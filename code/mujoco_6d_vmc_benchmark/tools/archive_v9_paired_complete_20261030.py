"""Preserve all 18 completed paired trajectories, including failed students."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tarfile

from archive_special_completed_fits_20261028 import digest, read, require, sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,output=args.root.resolve(),args.output.resolve()
    require(not output.exists() and root not in output.parents,'New separate archive directory required')
    state,review=read(root/'execution.json'),read(root/'REVIEW.json')
    require(state['status']=='complete_pending_review' and len(state['rows'])==len(review['rows'])==18,'Complete reviewed18 required')
    require(review['status']=='complete_development_review' and review['execution_sha256']==sha(root/'execution.json'),'Stale review')
    require(review['registration_sha256']==sha(root/'REGISTRATION.json'),'Stale registration')
    files={}
    for p in sorted(root.rglob('*')):
        require(not p.is_symlink(),'No symlink payload')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
            require(p.suffix!='.tmp','Incomplete temporary file')
            files['paired18/'+p.relative_to(root).as_posix()]=p
    files['archive_tool.py']=Path(__file__).resolve()
    files['archive_helpers.py']=Path(__file__).with_name('archive_special_completed_fits_20261028.py').resolve()
    manifest={}
    for name,p in files.items():
        before=p.stat();h=sha(p);after=p.stat()
        require((before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),'Mutating source')
        manifest[name]=dict(bytes=after.st_size,sha256=h)
    data=(json.dumps(dict(scope='Complete18 paired development runs, all successes/failures/raw/checkpoints/source/qualification/review; not final unseen test.',files=manifest),indent=2)+'\n').encode()
    output.mkdir(parents=True)
    partial=output/'COMPLETE_PAIRED18.tar.gz.partial'
    with tarfile.open(partial,'w:gz',compresslevel=1) as archive:
        for name,p in files.items():archive.add(p,arcname=name,recursive=False)
        info=tarfile.TarInfo('MANIFEST.json');info.size=len(data);archive.addfile(info,io.BytesIO(data))
    expected={**manifest,'MANIFEST.json':dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())}
    seen=set()
    with tarfile.open(partial) as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in seen,'Unexpected member')
            target=expected[member.name]
            require(member.size==target['bytes'] and digest(archive.extractfile(member))==target['sha256'],'Payload mismatch')
            seen.add(member.name)
    require(seen==set(expected),'Missing payload')
    for name,p in files.items():require(sha(p)==manifest[name]['sha256'] and p.stat().st_size==manifest[name]['bytes'],'Source changed')
    final=output/'COMPLETE_PAIRED18.tar.gz';partial.rename(final)
    result=dict(status='local_complete_paired18_verified_not_yet_shared',archive=str(final),bytes=final.stat().st_size,sha256=sha(final),payload_files=len(files),manifest_sha256=expected['MANIFEST.json']['sha256'],source_and_payload_match=True)
    (output/'LOCAL_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
