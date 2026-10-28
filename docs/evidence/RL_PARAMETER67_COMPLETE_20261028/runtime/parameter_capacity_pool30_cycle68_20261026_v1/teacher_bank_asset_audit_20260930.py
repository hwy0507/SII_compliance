"""Audit actual FR3 + reused Panda assets and statically recompile saved XML.

Never steps a simulator, edits a frozen run, or replaces its existing manifest.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import resource
import sys
import xml.etree.ElementTree as ET


ROBOT_ROOTS = ('franka_fr3', 'franka_emika_panda')
ROBOT_MODELS = ('franka_fr3/fr3.xml', 'franka_emika_panda/panda.xml',
                'franka_emika_panda/hand.xml')


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):digest.update(block)
    return digest.hexdigest()


def referenced_files(xml_path):
    """Resolve file references using compiler mesh/texture/asset directory rules."""
    xml_path=Path(xml_path).resolve()
    tree=ET.parse(xml_path)
    compiler=tree.getroot().find('compiler')
    attrs={} if compiler is None else compiler.attrib
    files=[]
    for node in tree.iter():
        for key,value in node.attrib.items():
            if key!='file' and not (node.tag=='texture' and key in
                    ('fileback','filedown','filefront','fileleft','fileright','fileup')):
                continue
            filename=Path(value)
            if attrs.get('strippath','false').lower()=='true' and node.tag!='include':
                filename=Path(filename.name)
            kind='meshdir' if node.tag=='mesh' else 'texturedir' if node.tag=='texture' else 'assetdir'
            directory=attrs.get(kind,attrs.get('assetdir','')) if node.tag!='include' else ''
            path=(xml_path.parent/Path(directory)/filename).resolve()
            if not path.is_file():raise FileNotFoundError(f'{xml_path}: missing {node.tag} asset {path}')
            files.append(dict(tag=node.tag,name=node.get('name'),attribute=key,declared=value,
                resolved=str(path),sha256=sha(path),size_bytes=path.stat().st_size))
            if node.tag=='include':files.extend(referenced_files(path))
    return files


def collect_robot_assets(asset_root):
    """Require real generation models and referenced meshes before freezing."""
    asset_root=Path(asset_root).resolve()
    for name in ROBOT_MODELS:
        model=asset_root/name
        if not model.is_file():raise FileNotFoundError('Missing required robot model: '+str(model))
        referenced_files(model)
    manifest={str(p.relative_to(asset_root)):sha(p) for name in ROBOT_ROOTS
              for p in sorted((asset_root/name).rglob('*')) if p.is_file()}
    if any(not any(n.startswith(root+'/assets/') for n in manifest) for root in ROBOT_ROOTS):
        raise RuntimeError('Both FR3 and reused Panda mesh assets must be present')
    return manifest


def model_differences(a,b):
    import numpy as np
    differences={}
    for name in dir(a):
        if name.startswith('_'):continue
        left=getattr(a,name)
        if not isinstance(left,np.ndarray):continue
        right=getattr(b,name)
        if left.shape!=right.shape:
            differences[name]=dict(shape_original=list(left.shape),shape_recompiled=list(right.shape))
        elif not np.array_equal(left,right):
            differences[name]=dict(shape=list(left.shape),different_elements=int(np.count_nonzero(left!=right)),
                maximum_absolute_difference=float(np.max(np.abs(left.astype(float)-right.astype(float)))) if left.size else 0.)
    return differences


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--assets',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,assets,output=args.run.resolve(),args.assets.resolve(),args.output.resolve()
    if output.exists() or output==root or root in output.parents:
        raise ValueError('Require new output directory outside frozen campaign')
    manifest=collect_robot_assets(assets)
    old=json.loads((root/'source_inputs/robot_asset_manifest.json').read_text())
    if any(sha(assets/name)!=digest for name,digest in old.items()):
        raise AssertionError('Old manifested assets have changed')
    output.mkdir(parents=True)
    (output/'complete_robot_asset_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    import mujoco
    plan=json.loads((root/'plan.json').read_text())
    if mujoco.__version__!=plan['mujoco_version']:
        raise RuntimeError('Compilation requires original MuJoCo version')
    cases={}
    for category in ('passive_corner','active_short','active_long'):
        for anchor in (0,337,671):
            folder=root/f'search/{category}/vmc/c00/{anchor}'
            audit=json.loads((folder/'audit.json').read_text())
            receipt_path=root/'archive_receipts'/folder.relative_to(root)/'receipt.json'
            receipt=json.loads(receipt_path.read_text())
            if not receipt.get('verified_path'):raise AssertionError('No recorded archive receipt')
            for name in ('rollout.xml','rollout.mjb','request.json'):
                if sha(folder/name)!=audit['files_sha256'][name]:
                    raise AssertionError('Original archived evidence hash mismatch: '+name)
            references=referenced_files(folder/'rollout.xml')
            for ref in references:
                path=Path(ref['resolved'])
                if assets not in path.parents or manifest.get(str(path.relative_to(assets)))!=ref['sha256']:
                    raise AssertionError('XML references asset outside complete robot manifest')
            name=category+'_'+str(anchor)
            compiled=mujoco.MjModel.from_xml_path(str(folder/'rollout.xml'))
            dest=output/(name+'.mjb')
            mujoco.mj_saveModel(compiled,str(dest),None)
            original=mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'))
            original_hash,recompiled_hash=sha(folder/'rollout.mjb'),sha(dest)
            differences=model_differences(original,compiled) if original_hash!=recompiled_hash else {}
            cases[name]=dict(folder=str(folder),xml_sha256=sha(folder/'rollout.xml'),
                request_sha256=sha(folder/'request.json'),archive_receipt=receipt,
                referenced_files=references,original_mjb_sha256=original_hash,
                recompiled_mjb_sha256=recompiled_hash,byte_identical=original_hash==recompiled_hash,
                model_array_differences=differences,explicit_static_overrides=[],
                original_timestep=original.opt.timestep,recompiled_timestep=compiled.opt.timestep)
            print(json.dumps(dict(case=name,byte_identical=original_hash==recompiled_hash,
                                   differing_arrays=len(differences))),flush=True)
            del original,compiled
    report=dict(scope='Supplemental current-asset audit and no-step static compilation of nine archived training-anchor XMLs; old manifest is preserved and acknowledged incomplete. No validation read or dynamic simulation.',
        run=str(root),asset_root=str(assets),mujoco_version=mujoco.__version__,python=sys.executable,
        old_manifest_sha256=sha(root/'source_inputs/robot_asset_manifest.json'),old_manifest_files=len(old),
        old_manifest_roots=sorted({Path(name).parts[0] for name in old}),
        old_manifest_complete_for_fr3_and_panda=all(any(n.startswith(k+'/') for n in old) for k in ROBOT_ROOTS),
        complete_manifest_sha256=sha(output/'complete_robot_asset_manifest.json'),complete_asset_files=len(manifest),
        complete_asset_bytes=sum((assets/name).stat().st_size for name in manifest),
        complete_asset_counts_by_root=dict(Counter(Path(name).parts[0] for name in manifest)),
        current_unmanifested_files=sorted(set(manifest)-set(old)),
        all_nine_mjb_byte_identical=all(c['byte_identical'] for c in cases.values()),cases=cases,
        script_sha256=sha(Path(__file__)),peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps(dict(output=str(output),review_sha256=sha(output/'review.json'),
        byte_identical=report['all_nine_mjb_byte_identical'],peak_rss_kib=report['peak_rss_kib'])))


if __name__=='__main__':main()
