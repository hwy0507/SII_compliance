"""Continuous supplementary validation, predeclared before primary tests.

All development-qualified frozen models receive every registered condition.
Primary/finer-step outcomes never determine eligibility. No fitting occurs.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from run_paper_final_validation_20261003 import ENV
from paper_office_worker_20261002 import SENSITIVITY_SHA,V6_SHA


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--conditions',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();assert sha(a.conditions)==SENSITIVITY_SHA
    protocol=json.loads(a.conditions.read_text());conditions=protocol['conditions']
    expected=np.round(np.random.default_rng(2026100312).uniform(protocol['lower_bounds'],protocol['upper_bounds'],size=(8,5)),6)
    actual=np.array([[c[k] for k in protocol['parameter_order']] for c in conditions])
    np.testing.assert_array_equal(actual,expected)
    assert all(c['rod_start']-c['person_start']-7>=1 for c in conditions)
    out=root/'sensitivity_coordinator';out.mkdir(exist_ok=False);shutil.copy2(a.conditions,out/'conditions.json')
    state=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=sha(Path(__file__)),
               conditions_sha256=SENSITIVITY_SHA,rows=[]);write(out/'execution.json',state)
    def save():write(out/'execution.json',state)
    try:
        while True:
            parent=json.loads((root/'final_validation_coordinator/execution.json').read_text())
            if parent['status']!='running':break
            if datetime.now(timezone.utc)>=datetime(2026,10,2,23,0,tzinfo=timezone.utc):
                raise RuntimeError('Primary queue not finished by conservative supplementary start cutoff')
            time.sleep(15)
        assert parent['status']=='complete', 'Do not bypass failed or incomplete primary audit'
        lock=root/'final_model_lock/VALIDATION_LOCK.json';model_lock=json.loads(lock.read_text())
        formal=json.loads((root/'final_model_lock/formal_manifest.json').read_text())
        eligible=[e['name'] for e in model_lock['development_evidence'] if e['strict_success']]
        assert [c['name'] for c in formal['candidates']]==eligible
        manifest=out/'manifest.json';write(manifest,dict(candidates=formal['candidates'],
            eligibility='Unchanged development strict gate, fixed before all primary/formal outcomes',validation_lock_sha256=sha(lock)))
        state.update(eligible_names=eligible,validation_lock_sha256=sha(lock),parent_execution_sha256=sha(root/'final_validation_coordinator/execution.json'));save()
        for start in (0,4):
            active=[]
            for path in Path('/proc').glob('[0-9]*'):
                try:
                    args=(path/'cmdline').read_bytes().split(b'\0');status=(path/'status').read_text()
                except (FileNotFoundError,PermissionError,ProcessLookupError):continue
                if any(line.startswith('State:') and ('T (stopped)' in line or 't (tracing stop)' in line) for line in status.splitlines()):continue
                names={Path(v.decode(errors='replace')).name for v in args[1:]}
                if names.intersection({'paper_office_worker_20261002.py','paper_classical_worker_20261002.py',
                                       'paper_rl_worker_20261002.py','validate_office_apparatus_v5_20260917.py'}):active.append(path.name)
            assert not active, 'Existing simulators; preserve concurrency cap: '+str(active)
            running=[]
            for condition in conditions[start:start+4]:
                name='random_'+condition['id'];runtime=root/(name+'_runtime');runtime.mkdir(exist_ok=False)
                for folder in ('scripts','tools','assets'):
                    shutil.copytree(ROOT/folder,runtime/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
                argv=['systemd-run','--user','--wait','--pipe','--collect',
                      '--unit=sii-paper-sensitivity-'+condition['id']+'-20261003',
                      '--property=MemoryMax=3G','--property=MemorySwapMax=0','--working-directory='+str(runtime)]
                argv+=['--setenv='+k+'='+v for k,v in ENV.items()]
                argv+=[sys.executable,str(runtime/'tools/run_paper_batch_20261002.py'),
                       '--manifest',str(manifest),'--output',str(root/name),
                       '--v6-input','/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002',
                       '--parameter-source','/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02',
                       '--rl-bridge','/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002/source/bridge_frozen.py',
                       '--menagerie','/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie',
                       '--validation-lock',str(lock),'--condition-file',str(out/'conditions.json'),
                       '--condition-id',condition['id'],'--dispatch-until',protocol['dispatch_deadline_utc']]
                log=(out/(name+'.log')).open('x');entry=dict(phase=name,command=argv,started_utc=now())
                state['rows'].append(entry);save()
                running.append((subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT),log,entry))
            while any(p.poll() is None for p,_,_ in running):time.sleep(5)
            for process,log,entry in running:
                log.close();entry.update(returncode=process.returncode,ended_utc=now())
            save();assert all(p.returncode==0 for p,_,_ in running), 'Failed queue retained without retry'
            for _,_,entry in running:
                name=entry['phase'];phase=root/name;record=json.loads((phase/'execution.json').read_text())
                assert record['status']=='complete' and [r['name'] for r in record['rows']]==eligible
                commands=[[sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),'--phase',str(phase),
                           '--output',str(root/(name+'_analysis')),'--model-sha256',V6_SHA],
                          [sys.executable,str(ROOT/'tools/audit_paper_common_cohort_20261003.py'),'--phases',str(phase),
                           '--output',str(out/(name+'_COMMON_COHORT.json'))]]
                entry['audit_commands']=commands;save()
                for index,command in enumerate(commands):
                    with (out/(name+f'_audit{index}.log')).open('x') as log:
                        subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
                entry['independent_audit_sha256']=sha(root/(name+'_analysis')/'INDEPENDENT_AUDIT.json');save()
        state['status']='complete'
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();save()


if __name__=='__main__':main()
