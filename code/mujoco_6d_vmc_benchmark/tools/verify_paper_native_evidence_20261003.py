"""Twice hash a completed native study in place; preserve true compute paths.

The integrity manifest is separate from the study being hashed. This is not a
move, a copy of data, or a claim that native simulations ran on the local PC.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import platform


def sha(path):
    value=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):value.update(block)
    return value.hexdigest()


def entries(root):
    result={}
    for path in sorted(root.rglob('*')):
        relative=path.relative_to(root)
        if '__pycache__' in relative.parts or path.suffix=='.pyc':continue
        if path.is_symlink():raise ValueError('Unexpected symlink: '+str(relative))
        if path.is_file():
            if path.suffix=='.tmp':raise ValueError('Unfinished write: '+str(relative))
            result[relative.as_posix()]=path
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    assert root!=out and root not in out.parents and out not in root.parents
    assert root.name=='paper_esn_12h_rl_20261002_141136' and root.is_dir()
    out.mkdir(parents=True,exist_ok=False)
    sources=entries(root);files={};executions=[]
    for relative,path in sources.items():
        if path.name=='execution.json':
            state=json.loads(path.read_text())
            if state.get('status')=='running':raise ValueError('Running execution: '+relative)
            executions.append(dict(path=relative,status=state.get('status'),host=state.get('host'),python=state.get('python')))
        before=path.stat();digest=sha(path);after=path.stat()
        assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns)
        files[relative]=dict(size=after.st_size,sha256=digest)
    again=entries(root);assert set(again)==set(files)
    for relative,path in again.items():
        assert path.stat().st_size==files[relative]['size'] and sha(path)==files[relative]['sha256']
    result=dict(verified_utc=datetime.now(timezone.utc).isoformat(),verification_host=platform.node(),
                native_study_root=str(root),source_sha256=sha(Path(__file__)),files=files,executions=executions,
                historical_execution_paths_preserved=True,raw_data_moved=False,independent_hash_passes=2,
                exclusions=['**/__pycache__/**','*.pyc'],
                limitation='File integrity and completed-status audit; actual compute hosts remain in each execution record. Does not replace scientific checks.')
    manifest=out/'NATIVE_INTEGRITY.json'
    with manifest.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    receipt=dict(verified_utc=result['verified_utc'],verification_host=platform.node(),native_study_root=str(root),
                 files_verified=len(files),total_bytes=sum(v['size'] for v in files.values()),
                 manifest_sha256=sha(manifest),independent_hash_passes=2)
    with (out/'RECEIPT.json').open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
