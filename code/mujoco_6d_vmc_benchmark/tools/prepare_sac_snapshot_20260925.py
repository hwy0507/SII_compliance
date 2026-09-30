"""Freeze original paired bytes plus reviewed SAC additions and pinned r2 demo."""
import argparse
import inspect
import json
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
import run_canonical48_sac_20260925 as entry
from prepare_sac_two_branch_plan_20260925 import implementation_hashes

ADDITIONS=('scripts/canonical48_sac_audit_20260925.py','tools/run_canonical48_sac_20260925.py',
    'tools/verify_train_demo_replay_20260924.py','tools/prepare_sac_two_branch_plan_20260925.py',
    'docs/CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original-source','proof-root','demo','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    for name in ('original_source','proof_root','demo','output'):setattr(a,name,getattr(a,name).resolve())
    entry.require(not a.output.exists(),'Fresh SAC snapshot root required')
    proofs=[json.loads((a.proof_root/m/'manifest.json').read_text()) for m in ('parameter6','direct7')]
    original=proofs[0]['source_hashes']
    entry.require(len(original)==163 and original==proofs[1]['source_hashes'],'Original163 proof execution source mismatch')
    for name,digest in original.items():entry.require(entry.sha(a.original_source/name)==digest,'Original source drift: '+name)
    for name in ADDITIONS:entry.require(not (a.original_source/name).exists(),'Would overwrite original source: '+name)
    _,demo=entry.read_demo(a.demo)
    files=[f for f in sorted(a.original_source.rglob('*')) if f.is_file() and '__pycache__' not in f.parts]
    entry.require(not any(f.is_symlink() for f in files),'Source symlinks need explicit review')
    a.output.mkdir(parents=True,exist_ok=False)
    source=a.output/'source'
    for src in files:
        target=source/src.relative_to(a.original_source);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
    for name in ADDITIONS:
        target=source/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target)
    demo_files={}
    for src in sorted(a.demo.rglob('*')):
        if not src.is_file():continue
        entry.require(not src.is_symlink(),'Demo symlinks need explicit review')
        name=str(src.relative_to(a.demo));target=a.output/'demo'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
        demo_files[name]=entry.sha(target)
    hashes={str(f.relative_to(source)):entry.sha(f) for f in sorted(source.rglob('*')) if f.is_file()}
    for src in files:entry.require(hashes[str(src.relative_to(a.original_source))]==entry.sha(src),'Copied original file mismatch')
    for name,digest in original.items():entry.require(hashes[name]==digest,'Copied163 source mismatch')
    entry.require(entry.sha(a.output/'demo/manifest.json')==demo['manifest_sha256'],'Copied demo manifest mismatch')
    record=dict(builder_sha256=entry.sha(__file__),original_source=str(a.original_source),original_files=len(files),
        original_execution_files=len(original),source_sha256=hashes,additions={name:hashes[name] for name in ADDITIONS},
        reviewed_sb3_source_sha256=implementation_hashes(),reviewed_test_sha256=entry.sha(ROOT/'tests/test_sac_audit_20260925.py'),
        demo_manifest_sha256=demo['manifest_sha256'],demo_files_sha256=demo_files,simulator_steps=0,gradient_updates=0)
    entry.save_json(a.output/'BUILD.json',record)
    for folder in (source,a.output/'demo'):
        for path in sorted(folder.rglob('*'),reverse=True):path.chmod(0o555 if path.is_dir() else 0o444)
        folder.chmod(0o555)
    print(json.dumps(dict(source=str(source),source_files=len(hashes),original_execution_files=len(original),
        build_sha256=entry.sha(a.output/'BUILD.json'),simulator_steps=0,gradient_updates=0)))

if __name__=='__main__':main()
