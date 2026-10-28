"""Hash completed evidence, then verify/publish a new server directory.

Standard library only so the verification runs without the research runtime.
No deletion, overwrite of published evidence, or remote process management.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def included(path):
    parts=path.parts
    return '__pycache__' not in parts and path.suffix!='.pyc' and not any(
        parts[i:i+3]==('source','scripts','outputs') for i in range(len(parts)-2))

def entries(root):
    result=[]
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if not included(rel) or rel==Path('archive_manifest.json'):continue
        if p.is_symlink():raise ValueError('Unexpected symlink: '+str(rel))
        if p.is_file():
            if p.suffix=='.tmp':raise ValueError('Unfinished write: '+str(rel))
            result.append((p,rel.as_posix()))
    return result

def write_new(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

def make(root):
    files={}
    for path,relative in entries(root):
        if path.name=='execution.json':
            state=json.loads(path.read_text())
            if state.get('status')=='running' and not (path.parent/'RECOVERY_AUDIT.json').is_file():
                raise ValueError('Still-running execution: '+relative)
        before=path.stat();digest=sha(path);after=path.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):
            raise ValueError('File changed while hashing: '+relative)
        files[relative]=dict(sha256=digest,size=after.st_size)
    value=dict(created_utc=datetime.now(timezone.utc).isoformat(),local_execution_root=str(root.resolve()),
               exclusions=['**/source/scripts/outputs/**','**/__pycache__/**','*.pyc'],
               exclusion_reason='Unrelated old output copies accidentally included in first source snapshots; no campaign failure is excluded',files=files)
    write_new(root/'archive_manifest.json',value)
    print(json.dumps(dict(files=len(files),bytes=sum(x['size'] for x in files.values()),manifest_sha256=sha(root/'archive_manifest.json'))))

def verify(root,publish):
    manifest=root/'archive_manifest.json';value=json.loads(manifest.read_text());expected=value['files']
    actual=dict((relative,path) for path,relative in entries(root))
    if set(expected)!=set(actual):raise ValueError('Archived file set mismatch')
    for relative,row in expected.items():
        p=actual[relative]
        if p.stat().st_size!=row['size'] or sha(p)!=row['sha256']:
            raise ValueError('Size/hash mismatch: '+relative)
    receipt=dict(verified_utc=datetime.now(timezone.utc).isoformat(),files_verified=len(expected),
                 total_bytes=sum(x['size'] for x in expected.values()),manifest_sha256=sha(manifest),
                 actual_compute_host='airpig',local_execution_root=value['local_execution_root'],
                 published_evidence=str(publish),historical_execution_paths_preserved=True)
    if publish.name!='evidence' or publish.parent.exists():
        raise FileExistsError('Use evidence within a completely new run directory')
    publish.parent.mkdir(parents=False,exist_ok=False)
    root.rename(publish)
    write_new(publish.parent/'ARCHIVE_VERIFICATION.json',receipt)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--publish',type=Path);args=p.parse_args()
    if args.publish:verify(args.root,args.publish)
    else:make(args.root)
