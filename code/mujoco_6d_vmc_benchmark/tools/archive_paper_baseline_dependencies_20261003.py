"""Copy exact native baseline dependencies into a new evidence directory.

Uses completed execution provenance and the existing checkpoint hashes. It
does not rewrite the running bridge, checkpoint paths, priors or environment.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import platform
import shutil
import sys
from optimize_tool_contact_20261002 import sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve();wanted={}
    def add(path,digest=None):
        path=Path(path).resolve();assert str(path).startswith('/home/arm1/') and path.is_file()
        actual=sha(path);assert digest is None or actual==digest
        assert str(path) not in wanted or wanted[str(path)]==actual
        wanted[str(path)]=actual
    phase=root/'evaluations_native';state=json.loads((phase/'execution.json').read_text());assert state['status']=='complete'
    for row in state['rows']:
        run=phase/row['name'];record=json.loads((run/'execution.json').read_text());provenance=record['runtime_provenance']
        for path,digest in provenance['policy_source_sha256'].items():add(path,digest)
        case=provenance['case']
        for name,digest in case['checkpoint_hashes'].items():add(Path(case['checkpoint'])/name,digest)
    v6=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
    add(v6/'source/bridge_frozen.py',provenance['bridge_sha256'])
    for name in ('PROTOCOL.json','construction/rollout.mjb','esn_original_v2/rollout.json'):add(v6/name)
    out.mkdir(parents=True,exist_ok=False);files=[]
    for original,digest in sorted(wanted.items()):
        source=Path(original);relative=Path('files')/source.relative_to('/')
        target=out/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        assert sha(source)==sha(target)==digest
        files.append(dict(original=original,archive_relative=str(relative),sha256=digest,size=target.stat().st_size))
    packages=sorted([dict(name=d.metadata['Name'],version=d.version) for d in importlib.metadata.distributions()],key=lambda x:x['name'].lower())
    write(out/'DEPENDENCY_INDEX.json',dict(created_utc=now(),copy_host=platform.node(),python=sys.executable,
        platform=platform.platform(),source_sha256=sha(Path(__file__)),files=files,installed_package_versions=packages,
        menagerie_required='/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie',
        limitation='Verified code/config/checkpoint copies from completed native RL evidence, plus exact v6 model/reference. Does not bundle Python binaries, CUDA libraries or the already-shared menagerie. Historical execution paths are unchanged.'))
    print(json.dumps(dict(files=len(files),bytes=sum(r['size'] for r in files),index_sha256=sha(out/'DEPENDENCY_INDEX.json'))))


if __name__=='__main__':main()
