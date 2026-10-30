"""Archive a consistent receipted prefix, including all scientific failures.

The coordinator may stay live. Copy its execution bytes once, include only
episodes already listed in that snapshot, and verify every immutable source
before/after packing. Never label a prefix a complete campaign or final test.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

from archive_special_completed_fits_20261028 import digest, require, sha
from collect_special_scene_actions_20261028 import read, write
from review_v9_common_eligibility_20261030 import validate_structure as validate_three
from review_v9_full_grid_eligibility_20261030 import validate_structure as validate_twelve


def inventory(root, snapshot, reg):
    cap=reg['candidate_limit_per_family_seed']
    require(cap in (3,12),'Unsupported selection protocol')
    (validate_three if cap==3 else validate_twelve)(reg,snapshot,final=False)
    require(snapshot['registration_sha256']==sha(root/'REGISTRATION.json'),'Registration mismatch')
    allowed=[root,Path(reg['parent'])]
    if cap==12:allowed.append(Path(reg['previous_selection']))
    files={};cases=[];seen=set()
    for group in snapshot['groups']:
        for trial in group['trials']:
            candidate=trial['candidate']
            require(sha(Path(candidate['checkpoint']))==candidate['checkpoint_sha256'],'Checkpoint changed')
            require(sha(Path(candidate['metadata']))==candidate['metadata_sha256'],'Metadata changed')
            for receipt in trial['cases']:
                folder=Path(receipt['folder']).resolve()
                require(any(p in folder.parents for p in allowed),'Unknown episode origin')
                require(not folder.is_symlink(),'Symlink episode')
                key=(candidate['checkpoint_sha256'],receipt['identity'])
                require(key not in seen,'Duplicate episode identity');seen.add(key)
                q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
                require(sha(folder/'DEMONSTRATION_QUALIFICATION.json')==receipt['qualification_sha256'],'Stale qualification')
                for name,h in q['input_hashes'].items():
                    require(sha(folder/name)==h,'Qualification input changed: '+name)
                e=read(folder/'execution.json')
                require(e['status']=='complete','Unfinished raw episode')
                require(sha(folder/'student_checkpoint.npz')==candidate['checkpoint_sha256'],'Wrong saved actor')
                require(receipt['development_qualified']==(q['status']=='qualified'),'Qualification mismatch')
                prefix='episodes/'+str(len(cases)).zfill(3)
                for p in sorted(folder.parent.rglob('*')):
                    require(not p.is_symlink(),'No symlink payload')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
                        require(p.suffix!='.tmp','Incomplete payload')
                        files[prefix+'/'+p.relative_to(folder.parent).as_posix()]=p
                metadata_name=prefix+'/TRAINING_METADATA.json'
                require(metadata_name not in files,'Metadata collision')
                files[metadata_name]=Path(candidate['metadata'])
                cases.append(dict(family=group['family'],seed=group['seed'],rank=candidate['validation_rank'],
                    identity=receipt['identity'],source_folder=str(folder),archive_prefix=prefix,
                    qualified=receipt['development_qualified'],reused=receipt['reused_parent_episode'],
                    qualification_sha256=receipt['qualification_sha256'],checkpoint_sha256=candidate['checkpoint_sha256']))
    require(cases,'No completed receipts')
    return files,cases


def main(root,output):
    require(not output.exists() and root not in output.parents,'Use a new separate archive directory')
    execution_bytes=(root/'execution.json').read_bytes()
    registration_bytes=(root/'REGISTRATION.json').read_bytes()
    snapshot=json.loads(execution_bytes);reg=json.loads(registration_bytes)
    files,cases=inventory(root,snapshot,reg)
    files['archive_tool.py']=Path(__file__).resolve()
    for name in ('archive_special_completed_fits_20261028.py','review_v9_common_eligibility_20261030.py',
                 'review_v9_full_grid_eligibility_20261030.py'):
        files['archive_helpers/'+name]=Path(__file__).with_name(name)
    manifest={}
    for name,p in files.items():
        before=p.stat();h=sha(p);after=p.stat()
        require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Mutating source')
        manifest[name]=dict(bytes=after.st_size,sha256=h)
    index=dict(scope='Receipted prefix of development eligibility. Includes all successes/failures/raw for these cases only; not the in-flight episode, completed campaign or final unseen matrix.',
        source_root=str(root),execution_snapshot_sha256=hashlib.sha256(execution_bytes).hexdigest(),
        registration_sha256=hashlib.sha256(registration_bytes).hexdigest(),
        completed_cases=len(cases),failed_cases=sum(not c['qualified'] for c in cases),cases=cases,files=manifest)
    content={'execution.snapshot.json':execution_bytes,'REGISTRATION.json':registration_bytes,
             'MANIFEST.json':(json.dumps(index,indent=2)+'\n').encode()}
    expected={**manifest,**{n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in content.items()}}
    output.mkdir(parents=True)
    partial=output/'COMPLETED_PREFIX.tar.gz.partial'
    with tarfile.open(partial,'w:gz',compresslevel=1) as archive:
        for name,p in files.items():archive.add(p,arcname=name,recursive=False)
        for name,data in content.items():
            info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
    seen=set()
    with tarfile.open(partial) as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in seen,'Unexpected payload')
            wanted=expected[member.name]
            require(member.size==wanted['bytes'] and digest(archive.extractfile(member))==wanted['sha256'],'Payload mismatch')
            seen.add(member.name)
    require(seen==set(expected),'Missing payload')
    for name,p in files.items():
        require(sha(p)==manifest[name]['sha256'] and p.stat().st_size==manifest[name]['bytes'],'Completed source changed')
    require((root/'REGISTRATION.json').read_bytes()==registration_bytes,'Registration changed')
    final=output/'COMPLETED_PREFIX.tar.gz';partial.rename(final)
    receipt=dict(status='local_verified_development_prefix_not_yet_shared',archive=str(final),
        bytes=final.stat().st_size,sha256=sha(final),completed_cases=len(cases),
        failed_cases=index['failed_cases'],payload_files=len(files),
        execution_snapshot_sha256=index['execution_snapshot_sha256'],
        registration_sha256=index['registration_sha256'],manifest_sha256=expected['MANIFEST.json']['sha256'],
        source_before_after_verified=True,all_archive_members_verified=True,
        includes_inflight_episode=False,final_test_performed=False)
    write(output/'LOCAL_RECEIPT.json',receipt)
    write(output/'CASE_INDEX.json',dict(cases=cases,execution_snapshot_sha256=index['execution_snapshot_sha256']))
    print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.root.resolve(),a.output.resolve())
