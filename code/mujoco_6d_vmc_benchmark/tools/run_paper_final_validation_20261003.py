"""One-shot final validation after development finishes; never trains or tunes.

Each simulation queue has its own frozen source, lock and 3 GiB systemd unit.
The coordinator is a continuous foreground job, not a scheduled automation.
Existing outputs are never overwritten or automatically retried.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT, sha, write, now

ENV = {
    'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
    'MUJOCO_GL': 'egl', 'JAX_PLATFORMS': 'cuda',
    'XLA_PYTHON_CLIENT_PREALLOCATE': 'false', 'XLA_PYTHON_CLIENT_MEM_FRACTION': '0.02',
    'LD_LIBRARY_PATH': '/home/arm1/vmc_mujoco_runtime/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:/home/arm1/vmc_mujoco_runtime/.venv/lib/python3.12/site-packages/nvidia/nccl/lib:/usr/local/cuda/lib64',
    'SII_SOURCE_BASE_COMMIT': '282433d339feef66b0334f223f82a6eea96b040b',
}
FORMAL_HASH = 'd4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--specification', type=Path, required=True)
    p.add_argument('--conditions', type=Path, required=True)
    a = p.parse_args(); root = a.root.resolve()
    output = root/'final_validation_coordinator'; output.mkdir(exist_ok=False)
    spec = output/'selection_specification.json'; conditions = output/'conditions.json'
    shutil.copy2(a.specification, spec); shutil.copy2(a.conditions, conditions)
    assert sha(conditions) == 'e9890b9a97ab5f89618a57cf093cb82813e335a1fdfe705ca6ba96c706e322cf'
    state = dict(status='running', started_utc=now(), argv=sys.argv, source_sha256=sha(Path(__file__)),
                 specification_sha256=sha(spec), conditions_sha256=sha(conditions), steps=[])
    def save(): write(output/'execution.json', state)
    def command(argv, label):
        entry = dict(label=label, argv=argv, started_utc=now()); state['steps'].append(entry); save()
        with (output/(label+'.log')).open('x') as log:
            result = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT, env={**os.environ, **ENV})
        entry.update(returncode=result.returncode, ended_utc=now()); save()
        if result.returncode: raise RuntimeError(label+' failed; output preserved')
    def audit(phase, model_hash):
        target = root/(phase+'_analysis')
        if target.exists():
            assert json.loads((target/'execution.json').read_text())['status']=='complete'
            return
        command([sys.executable, str(ROOT/'tools/audit_paper_phase_20261003.py'),
                 '--phase', str(root/phase), '--output', str(target), '--model-sha256', model_hash], 'audit_'+phase)
    def active_simulators():
        result=[]
        for path in Path('/proc').glob('[0-9]*'):
            try:
                args=(path/'cmdline').read_bytes().split(b'\0')
                status=(path/'status').read_text()
            except (FileNotFoundError, PermissionError, ProcessLookupError): continue
            if any(line.startswith('State:') and ('T (stopped)' in line or 't (tracing stop)' in line) for line in status.splitlines()): continue
            names={Path(x.decode(errors='replace')).name for x in args[1:]}
            if names.intersection({'paper_office_worker_20261002.py','paper_classical_worker_20261002.py',
                                   'paper_rl_worker_20261002.py','validate_office_v5_20260918.py'}):
                result.append(dict(pid=int(path.name), argv=[x.decode(errors='replace') for x in args if x]))
        return result
    def run_wave(jobs):
        assert len(jobs)<=4 and not active_simulators(), 'Existing simulation job: do not duplicate or exceed concurrency'
        running=[]
        for name, manifest, extra in jobs:
            runtime=root/(name+'_runtime'); runtime.mkdir(exist_ok=False)
            for folder in ('scripts','assets','tools'):
                shutil.copytree(ROOT/folder,runtime/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
            argv=['systemd-run','--user','--wait','--pipe','--collect',
                  '--unit=sii-paper-final-'+name.replace('_','-')+'-20261003',
                  '--property=MemoryMax=3G','--property=MemorySwapMax=0',
                  '--working-directory='+str(runtime)]
            argv += ['--setenv='+k+'='+v for k,v in ENV.items()]
            argv += [sys.executable,str(runtime/'tools/run_paper_batch_20261002.py'),
                     '--manifest',str(manifest),'--output',str(root/name),
                     '--v6-input','/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002',
                     '--parameter-source','/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02',
                     '--rl-bridge','/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002/source/bridge_frozen.py',
                     '--menagerie','/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie',
                     '--validation-lock',str(root/'final_model_lock/VALIDATION_LOCK.json'),
                     '--dispatch-until','2026-10-03T01:00:00+00:00',*extra]
            log=(output/(name+'.log')).open('x')
            entry=dict(label=name,argv=argv,started_utc=now()); state['steps'].append(entry); save()
            process=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT)
            running.append((process,log,entry,name))
        while any(process.poll() is None for process,_,_,_ in running): time.sleep(5)
        failures=[]
        for process,log,entry,name in running:
            log.close(); entry.update(returncode=process.returncode,ended_utc=now())
            if process.returncode: failures.append(name)
        save()
        if failures: raise RuntimeError('Preserved failed validation queues: '+repr(failures))
        for _,_,_,name in running:
            assert json.loads((root/name/'execution.json').read_text())['status']=='complete', 'Incomplete final denominator'
    save()
    try:
        # Stable development queue is allowed to finish untouched.
        while True:
            development=json.loads((root/'classical_native/execution.json').read_text())
            if development['status']!='running': break
            if datetime.now(timezone.utc)>=datetime(2026,10,2,22,11,36,tzinfo=timezone.utc):
                raise RuntimeError('Development still active at cutoff; no final dispatch')
            time.sleep(15)
        assert development['status']=='complete'
        audit('classical_native','173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11')
        audit('feature_matched_seed2_native','173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11')
        command([sys.executable,str(ROOT/'tools/freeze_paper_final_models_20261003.py'),
                 '--root',str(root),'--specification',str(spec),'--output',str(root/'final_model_lock')],'freeze_models')
        lock=root/'final_model_lock'; state['validation_lock_sha256']=sha(lock/'VALIDATION_LOCK.json'); save()
        jobs=[('heldout_'+c['id'],lock/'manifest.json',['--condition-file',str(conditions),'--condition-id',c['id']])
              for c in json.loads(conditions.read_text())['conditions']]
        run_wave(jobs)
        for name,_,_ in jobs:
            audit(name,'173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11')
            command([sys.executable,str(ROOT/'tools/audit_paper_common_cohort_20261003.py'),
                     '--phases',str(root/name),'--output',str(output/(name+'_COMMON_COHORT.json'))],'cohort_'+name)
        formal=json.loads((lock/'formal_manifest.json').read_text())['candidates']; width=min(4,len(formal))
        # Consecutive disjoint slices; every eligible model runs exactly once.
        q,r=divmod(len(formal),width);start=0;jobs=[]
        for i in range(width):
            count=q+int(i<r)
            jobs.append(('formal_'+str(i+1),lock/'formal_manifest.json',
                         ['--physics-dt','0.00005','--start-index',str(start),'--count',str(count)]))
            start+=count
        run_wave(jobs)
        for name,_,_ in jobs: audit(name,FORMAL_HASH)
        command([sys.executable,str(ROOT/'tools/audit_paper_common_cohort_20261003.py'),
                 '--phases',*[str(root/name) for name,_,_ in jobs],
                 '--output',str(output/'formal_COMMON_COHORT.json')],'cohort_formal')
        assert sha(spec)==state['specification_sha256'] and sha(conditions)==state['conditions_sha256']
        state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc)); raise
    finally:
        state['ended_utc']=now();save()


if __name__=='__main__':main()
