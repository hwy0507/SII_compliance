"""Copy accepted training bytes plus new deployment files; no model/physics run."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ADDITIONS=('scripts/canonical48_paired_deployment_20260924.py','scripts/run_panel_paired_deployment_20260924.py',
    'tools/audit_paired_deployment_replay_20260924.py','tools/prepare_paired_six_fixture_deployment_20260924.py',
    'tools/run_paired_six_fixture_deployment_20260924.py','tools/prepare_paired_deployment_snapshot_20260924.py',
    'tests/test_paired_deployment_20260924.py','tests/test_paired_deployment_driver_20260924.py',
    'docs/RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md','docs/RL_PAIRED_DEPLOYMENT_DRIVER_20260924.md')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training-source',type=Path,required=True)
    p.add_argument('--proof-parity',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    args.training_source=args.training_source.resolve();args.output=args.output.resolve()
    parity=json.loads(args.proof_parity.read_text())
    if not parity['passed']:raise ValueError('Accepted proof required')
    for name,expected in parity['source_hashes'].items():
        source=(args.training_source/name).resolve()
        if not source.is_relative_to(args.training_source) or sha(source)!=expected:raise ValueError('Training snapshot drift: '+name)
    originals={str(path.relative_to(args.training_source)):sha(path) for path in args.training_source.rglob('*') if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc'}
    for name in ADDITIONS:
        if name in originals:raise ValueError('Only new file additions allowed: '+name)
    args.output.mkdir(parents=True,exist_ok=False)
    snapshot=args.output/'source'
    try:
        shutil.copytree(args.training_source,snapshot,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        # Only the fresh copy receives writable directories for new additions.
        for directory in [snapshot,*[p for p in snapshot.rglob('*') if p.is_dir()]]:directory.chmod(0o755)
        for name in ADDITIONS:
            target=snapshot/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,target)
        for name,expected in originals.items():
            if sha(snapshot/name)!=expected:raise ValueError('Original frozen bytes changed during copy: '+name)
        for path in snapshot.rglob('*.py'):compile(path.read_text(),str(path),'exec')
        code="""import sys,json,importlib,mujoco
from pathlib import Path
root=Path(sys.argv[1]);sys.path[:0]=[str(root/'tools'),str(root/'scripts')]
def prohibited(*a,**kw):raise AssertionError('No physics in static import check')
mujoco.mj_step=prohibited
names=['canonical48_paired_deployment_20260924','run_panel_paired_deployment_20260924','audit_paired_deployment_replay_20260924','prepare_paired_six_fixture_deployment_20260924','run_paired_six_fixture_deployment_20260924']
loaded={name:str(Path(importlib.import_module(name).__file__).resolve()) for name in names}
assert all(Path(path).is_relative_to(root) for path in loaded.values())
print(json.dumps({'passed':True,'modules':loaded,'physics_steps':0}))
"""
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        done=subprocess.run([sys.executable,'-c',code,str(snapshot)],env=env,capture_output=True,text=True,check=True)
        checked=json.loads(done.stdout)
        all_files={str(p.relative_to(snapshot)):sha(p) for p in snapshot.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        report=dict(status='prepared_no_models_no_simulation',original_training_source=str(args.training_source),
            proof_parity_sha256=sha(args.proof_parity),training_source_files=len(parity['source_hashes']),
            original_files_sha256=originals,all_original_bytes_preserved=True,added_files_sha256={n:sha(snapshot/n) for n in ADDITIONS},
            source_files_sha256=all_files,static_import_check=checked,builder_sha256=sha(Path(__file__)),
            limitation='No final model load, no real600-frame model parity, no18-job plan or simulation execution yet')
        (args.output/'BUILD.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        for path in snapshot.rglob('*'):
            if path.is_file():path.chmod(0o444)
        for directory in [p for p in snapshot.rglob('*') if p.is_dir()]:directory.chmod(0o555)
        snapshot.chmod(0o555)
        print(json.dumps(dict(status=report['status'],snapshot=str(snapshot),training_sources=len(parity['source_hashes']),added_files=len(ADDITIONS),static_import_check=True)))
    except BaseException as error:
        (args.output/'FAILED.json').write_text(json.dumps(dict(error=repr(error),simulations_started=0),indent=2)+'\n')
        raise


if __name__=='__main__':main()
