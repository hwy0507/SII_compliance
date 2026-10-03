"""Run every prelocked finalist on every sealed identity at the frozen timestep.

No policy eligibility filter, fitting, outcome selection, or automatic retry.
This coordinator is only invoked after research development has been closed.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT,write,now
from research72_final_lock_20261003 import verify_lock,authorize_final_read,runtime_hashes,read,sha
from research72_slots_20261003 import simulation_slot
from run_all_methods_formal_20261003 import MENAGERIE
from run_paper_final_validation_20261003 import ENV


def no_development_processes():
    names={'research72_train_models_20261003.py','research72_train_rl_20261003.py',
        'research72_rl_campaign_20261003.py','research72_followup_20261003.py',
        'research72_additional_development_20261003.py','research72_batch_20261003.py',
        'research72_queued_development_20261003.py',
        'research72_refined_teacher_20261003.py',
        'research72_worker_20261003.py','train_paper_context_esn_20261003.py',
        'train_paper_feature_matched_network_20261003.py','train_office_mlp_rnn_20261002.py'}
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            status=(proc/'status').read_text()
            if any(line.startswith('State:') and ('T (stopped)' in line or 't (tracing stop)' in line)
                   for line in status.splitlines()):continue
            argv={Path(x.decode(errors='replace')).name for x in (proc/'cmdline').read_bytes().split(b'\0')[1:]}
            assert not argv.intersection(names), 'Development process still active: '+proc.name
        except (FileNotFoundError,ProcessLookupError,PermissionError):continue


def queue(root,output,lock_path,lock_sha,index):
    lock,protocol=authorize_final_read(root,lock_path,lock_sha,ROOT,output)
    conditions=read(root/'sealed/HELDOUT.json')['conditions']
    assert len(conditions)==24
    deadline=datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    phase=output/f'queue_{index}';phase.mkdir(exist_ok=False)
    source=phase/'source'
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    assert runtime_hashes(source)==lock['runtime_source_sha256']
    planned=[(c,d) for d in conditions for c in lock['candidates']][index::4]
    state=dict(status='waiting_for_lease',started_utc=now(),model_lock_sha256=lock_sha,
        expected=len(planned),planned=[dict(candidate=c['name'],condition=d['id']) for c,d in planned],rows=[])
    write(phase/'execution.json',state)
    try:
        with simulation_slot(root,deadline) as lease:
            state.update(status='running',simulation_lease=lease)
            write(phase/'execution.json',state)
            for c,d in planned:
                if datetime.now(timezone.utc)>=deadline:
                    state['status']='deadline_no_new_dispatch';break
                name=c['name']+'__'+d['id'];run=phase/name
                command=[sys.executable,str(source/'tools/research72_final_worker_20261003.py'),
                    '--root',str(root),'--model-lock',str(lock_path),'--lock-sha256',lock_sha,
                    '--candidate',c['name'],'--condition',d['id'],'--output',str(run)]
                row=dict(name=name,candidate=c['name'],category=c['category'],seed=c.get('seed'),
                    condition_id=d['id'],command=command,started_utc=now())
                state['rows'].append(row);write(phase/'execution.json',state)
                env={**os.environ,**ENV,'MUJOCO_MENAGERIE_PATH':str(MENAGERIE),
                    'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
                with (phase/(name+'.log')).open('x') as log:
                    rc=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
                row.update(returncode=rc,ended_utc=now());write(phase/'execution.json',state)
                assert rc==0, name+' engineering failure retained, no automatic retry'
                row.update(audit=read(run/'AUDIT.json'),audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
                write(phase/'execution.json',state)
            else:state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(phase/'execution.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--model-lock',type=Path,required=True)
    p.add_argument('--lock-sha256',required=True)
    p.add_argument('--queue',type=int,choices=range(4))
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve();lock_path=a.model_lock.resolve()
    lock,protocol=verify_lock(root,lock_path,a.lock_sha256)
    if a.queue is not None:
        queue(root,out,lock_path,a.lock_sha256,a.queue);return
    no_development_processes()
    assert datetime.now(timezone.utc)<datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    for evidence in lock['completion_receipts']:
        assert sha(evidence['path'])==evidence['sha256'] and read(evidence['path'])['status']=='complete'
    assert runtime_hashes(ROOT)==lock['runtime_source_sha256']
    out.mkdir(parents=True,exist_ok=False)
    receipt=dict(opened_utc=now(),model_lock_sha256=a.lock_sha256,
        protocol_sha256=sha(root/'PROTOCOL.json'),sealed_condition_sha256=protocol['sealed_condition_sha256'],
        source_sha256=sha(Path(__file__)),output=str(out),models=len(lock['candidates']),conditions=24,
        rule='Model freeze precedes this one-shot opening. No additional fitting or selection on final outcomes.')
    with (root/'FINAL_UNSEAL_RECEIPT.json').open('x') as f:
        json.dump(receipt,f,indent=2,allow_nan=False);f.write('\n')
    assert sha(root/'sealed/HELDOUT.json')==protocol['sealed_condition_sha256']
    conditions=read(root/'sealed/HELDOUT.json')['conditions']
    assert len(conditions)==24 and all(c['role']=='heldout' for c in conditions)
    state=dict(status='running',started_utc=now(),model_lock_sha256=a.lock_sha256,
        expected=len(lock['candidates'])*24,unseal_receipt_sha256=sha(root/'FINAL_UNSEAL_RECEIPT.json'),queues=[])
    write(out/'execution.json',state)
    def launch(index):
        command=['systemd-run','--user','--wait','--pipe','--collect',
            '--unit=sii-r72-final-'+out.name.replace('_','-')+'-'+str(index),
            '--property=MemoryMax=3G','--property=MemorySwapMax=0']
        env={**ENV,'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
        command+=['--setenv='+k+'='+v for k,v in env.items()]
        command+=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--output',str(out),
            '--model-lock',str(lock_path),'--lock-sha256',a.lock_sha256,'--queue',str(index)]
        with (out/f'queue_{index}.log').open('x') as log:
            rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
        return dict(queue=index,returncode=rc,command=command)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            state['queues']=list(pool.map(launch,range(4)))
        assert all(q['returncode']==0 for q in state['queues'])
        rows=[]
        for index in range(4):
            phase=out/f'queue_{index}'
            command=[sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),
                '--phase',str(phase),'--output',str(out/f'queue_{index}_analysis'),
                '--model-sha256',protocol['formal_model_sha256']]
            with (out/f'audit_{index}.log').open('x') as log:
                subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
            rows.extend(dict(r,run=str(phase/r['name'])) for r in read(phase/'execution.json')['rows'])
        write(out/'SUMMARY.json',dict(expected=state['expected'],completed=len(rows),rows=rows,
            task=sum(r['audit']['task_success'] for r in rows),strict=sum(r['audit']['strict_success'] for r in rows)))
        state['status']='complete' if len(rows)==state['expected'] else 'deadline_no_new_dispatch'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
