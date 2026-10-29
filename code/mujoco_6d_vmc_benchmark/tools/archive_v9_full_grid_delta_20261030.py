"""Archive only new full-grid raw cases; reference exact existing top-three raw.

No simulation, fitting or deletion. Immutable source/member verification and
explicit dependency mapping preserve all99 cases without repacking old72.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile
from archive_v9_eligibility_prefix_20261030 import inventory
from archive_special_completed_fits_20261028 import digest, require, sha
from collect_special_scene_actions_20261028 import ROOT, read, write


def main(output):
    root=ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1'
    previous=ROOT/'outputs/nonrl_v9_complete_top3_raw_archive_20261030_v1'
    require(not output.exists(),'Never overwrite archive')
    eb=(root/'execution.json').read_bytes();rb=(root/'REGISTRATION.json').read_bytes()
    state=json.loads(eb);reg=json.loads(rb)
    require(state['status']=='eligibility_exhausted_preserved','Require terminal full-grid state')
    files,cases=inventory(root,state,reg)
    old_receipt=read(previous/'LOCAL_RECEIPT.json');old_index=read(previous/'CASE_INDEX.json')
    require(old_receipt['sha256']=='664252fbe018b9ba7d75dffb85cf855e9edb5010d1b63648e1b9f478e6211f80','Wrong prerequisite raw archive')
    old={(c['checkpoint_sha256'],c['identity']):c for c in old_index['cases']}
    new=[];dependencies=[]
    for case in cases:
        if case['reused']:
            origin=old[(case['checkpoint_sha256'],case['identity'])]
            for key in ('source_folder','qualification_sha256','qualified'):require(case[key]==origin[key],'Old raw mapping mismatch '+key)
            dependencies.append(dict(case=case,existing_archive_prefix=origin['archive_prefix']))
        else:new.append(case)
    require(len(cases)==99 and len(new)==27 and len(dependencies)==72,'Unexpected terminal coverage')
    prefixes={c['archive_prefix']+'/' for c in new}
    payload={name:p for name,p in files.items() if any(name.startswith(prefix) for prefix in prefixes)}
    for name in ('archive_v9_full_grid_delta_20261030.py','archive_v9_eligibility_prefix_20261030.py',
                 'archive_special_completed_fits_20261028.py','review_v9_common_eligibility_20261030.py','review_v9_full_grid_eligibility_20261030.py'):
        payload['archive_sources/'+name]=ROOT/'tools'/name
    manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for name,p in payload.items()}
    index=dict(scope='27 new complete full-grid development raw cases including all18 new failures; exact prerequisite archive holds other72. Together cover99 terminal cases/28 failures. Not final tests.',
        source_root=str(root),new_cases=new,reused_dependency_map=dependencies,
        prerequisite_archive='arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v9_complete_top3_raw_20261030_v1/COMPLETED_PREFIX.tar.gz',
        prerequisite_bytes=old_receipt['bytes'],prerequisite_sha256=old_receipt['sha256'],
        execution_sha256=hashlib.sha256(eb).hexdigest(),registration_sha256=hashlib.sha256(rb).hexdigest(),files=manifest)
    require(sum(not c['qualified'] for c in new)==18,'Failure count mismatch')
    content={'execution.snapshot.json':eb,'REGISTRATION.json':rb,'MANIFEST.json':(json.dumps(index,indent=2)+'\n').encode(),
        'prerequisite/LOCAL_RECEIPT.json':(previous/'LOCAL_RECEIPT.json').read_bytes(),
        'prerequisite/CASE_INDEX.json':(previous/'CASE_INDEX.json').read_bytes()}
    expected={**manifest,**{n:dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()) for n,b in content.items()}}
    output.mkdir(parents=True);partial=output/'NEW27_RAW.tar.gz.partial'
    with tarfile.open(partial,'w:gz',compresslevel=1) as archive:
        for name,p in payload.items():archive.add(p,arcname=name,recursive=False)
        for name,data in content.items():
            info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
    seen=set()
    with tarfile.open(partial) as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in seen,'Unexpected member')
            want=expected[member.name]
            require(member.size==want['bytes'] and digest(archive.extractfile(member))==want['sha256'],'Member mismatch')
            seen.add(member.name)
    require(seen==set(expected),'Missing member')
    for name,p in payload.items():require(p.stat().st_size==manifest[name]['bytes'] and sha(p)==manifest[name]['sha256'],'Source changed')
    require((root/'execution.json').read_bytes()==eb and (root/'REGISTRATION.json').read_bytes()==rb,'Terminal source changed')
    final=output/'NEW27_RAW.tar.gz';partial.rename(final)
    receipt=dict(status='local_verified_not_yet_shared',bytes=final.stat().st_size,sha256=sha(final),
        new_cases=27,new_failures=18,existing_cases=72,total_cases=99,total_failures=28,
        prerequisite_sha256=old_receipt['sha256'],execution_sha256=index['execution_sha256'],
        payload_members=len(payload),all_members_and_source_before_after_verified=True,final_test_performed=False)
    write(output/'LOCAL_RECEIPT.json',receipt);write(output/'CASE_INDEX.json',index)
    print(receipt)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output.resolve())
