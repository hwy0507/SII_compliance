"""Four finite, frozen-source queues for predeclared new development comparisons.

Models/candidates and conditions are explicit. No final-test unlocking here.
Only the supervising researcher selects subsequent stages, from development data.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from run_all_methods_formal_20261003 import V6,PARAMETER,MENAGERIE,active_workers
from run_paper_final_validation_20261003 import ENV


def read(p):return json.loads(p.read_text())


def validate(root,spec):
    protocol=read(root/'PROTOCOL.json')
    assert spec['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    conditions={c['id']:c for c in read(root/'CONDITIONS.json')['conditions']}
    assert 1<=len(spec['candidates'])<=48
    assert len({c['name'] for c in spec['candidates']})==len(spec['candidates'])
    assert len(set(spec['conditions']))==len(spec['conditions']) and spec['conditions']
    assert all(conditions[c]['role']=='development' for c in spec['conditions'])
    for c in spec['candidates']:
        assert re.fullmatch('[a-zA-Z0-9_.-]+',c['name']) and c['name'] not in ('.','..')
        assert sum(bool(c.get(k)) for k in ('checkpoint','controller','rl_case','adapted_rl'))<=1
        if c.get('checkpoint'):assert sha(Path(c['checkpoint']))==c['checkpoint_sha256']
        if c.get('adapted_rl'):
            assert sha(Path(c['adapted_rl']['manifest']))==c['adapted_rl']['manifest_sha256']
    assert len(spec['conditions'])*len(spec['candidates'])<=384
    return protocol


def queue(root,phase,index):
    spec=read(phase/'SPECIFICATION.json');protocol=validate(root,spec)
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    output=phase/f'queue_{index}';output.mkdir(exist_ok=False)
    source=output/'source'
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,source/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    manifest=[(c,condition) for condition in spec['conditions'] for c in spec['candidates']][index::4]
    state=dict(status='running',started_utc=now(),specification_sha256=sha(phase/'SPECIFICATION.json'),
        protocol_sha256=sha(root/'PROTOCOL.json'),rows=[])
    write(output/'execution.json',state)
    env={**os.environ,**ENV,'SII_SOURCE_BASE_COMMIT':os.environ.get('SII_SOURCE_BASE_COMMIT',protocol['source_base_commit']),
        'MUJOCO_MENAGERIE_PATH':str(MENAGERIE)}
    try:
        for c,condition in manifest:
            if datetime.now(timezone.utc)>=deadline:state['status']='deadline_no_new_dispatch';break
            name=c['name']+'__'+condition;run=output/name;config=output/(name+'.config.json');write(config,c.get('config',{}))
            kind='adapted_rl' if c.get('adapted_rl') else 'rl' if c.get('rl_case') else 'classical' if c.get('controller') else 'office'
            command=[sys.executable,str(source/'tools/research72_worker_20261003.py'),'--worker-kind',kind,
                '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',sha(root/'PROTOCOL.json'),
                '--research-condition',condition,'--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
                '--config',str(config),'--output',str(run),'--physics-dt',str(protocol['physics_dt_s']),'--contact-audit']
            if c.get('checkpoint'):command+=['--checkpoint',c['checkpoint']]
            if c.get('controller'):command+=['--controller',c['controller'],'--parameter-source',str(PARAMETER)]
            if c.get('rl_case'):command+=['--case',c['rl_case'],'--bridge',str(V6/'source/bridge_frozen.py')]
            if c.get('adapted_rl'):
                adapted=c['adapted_rl'];command+=['--agent-checkpoint',adapted['checkpoint'],'--checkpoint-manifest',adapted['manifest'],
                    '--parameter-source',str(PARAMETER)]
                if adapted.get('controller'):command+=['--controller',adapted['controller']]
            row=dict(name=name,candidate=c['name'],condition_id=condition,category=c['category'],started_utc=now(),command=command)
            state['rows'].append(row);write(output/'execution.json',state)
            with (output/(name+'.log')).open('x') as log:
                rc=subprocess.run(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
            row.update(returncode=rc,ended_utc=now());write(output/'execution.json',state)
            if rc:raise RuntimeError(name+' failed; preserved without automatic retry')
            row.update(audit=read(run/'AUDIT.json'),audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
            write(output/'execution.json',state)
        else:state['status']='complete'
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(output/'execution.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--specification',type=Path)
    p.add_argument('--queue',type=int,choices=range(4));a=p.parse_args();root=a.root.resolve();phase=a.output.resolve()
    if a.queue is not None:queue(root,phase,a.queue);return
    assert a.specification is not None
    spec=read(a.specification);protocol=validate(root,spec)
    assert not active_workers(), 'Existing physics; wait without duplicate dispatch'
    for proc in Path('/proc').glob('[0-9]*/cmdline'):
        try:names={Path(x.decode(errors='replace')).name for x in proc.read_bytes().split(b'\0')}
        except OSError:continue
        assert 'research72_worker_20261003.py' not in names,'Another research simulation active'
    phase.mkdir(parents=True,exist_ok=False);shutil.copy2(a.specification,phase/'SPECIFICATION.json')
    assert re.fullmatch('[a-zA-Z0-9_-]+',phase.name)
    with (phase/'coordinator.lock').open('x') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=dict(status='running',started_utc=now(),specification_sha256=sha(phase/'SPECIFICATION.json'),queues=[])
        write(phase/'execution.json',state)
        def launch(i):
            cmd=['systemd-run','--user','--wait','--pipe','--collect','--unit=sii-r72-'+phase.name.replace('_','-')+'-'+str(i),
                '--property=MemoryMax=3G','--property=MemorySwapMax=0']
            env={**ENV,'SII_SOURCE_BASE_COMMIT':os.environ.get('SII_SOURCE_BASE_COMMIT',protocol['source_base_commit'])}
            cmd+=['--setenv='+k+'='+v for k,v in env.items()]
            cmd+=[sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--output',str(phase),'--queue',str(i)]
            with (phase/f'queue_{i}.log').open('x') as log:rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
            return dict(queue=i,command=cmd,returncode=rc)
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:state['queues']=list(pool.map(launch,range(4)))
            assert all(q['returncode']==0 for q in state['queues'])
            rows=[]
            for i in range(4):
                q=phase/f'queue_{i}';cmd=[sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),
                    '--phase',str(q),'--output',str(phase/f'queue_{i}_analysis'),'--model-sha256',protocol['formal_model_sha256']]
                with (phase/f'audit_{i}.log').open('x') as log:subprocess.run(cmd,check=True,env={**os.environ,**ENV},stdout=log,stderr=subprocess.STDOUT)
                rows.extend(dict(r,run=str(q/r['name'])) for r in read(q/'execution.json')['rows'])
            write(phase/'SUMMARY.json',dict(completed_utc=now(),rows=rows,expected=len(spec['candidates'])*len(spec['conditions']),
                completed=len(rows),task=sum(r['audit']['task_success'] for r in rows),strict=sum(r['audit']['strict_success'] for r in rows)))
            state['status']='complete' if len(rows)==len(spec['candidates'])*len(spec['conditions']) else 'deadline_no_new_dispatch'
        except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
        finally:state['ended_utc']=now();write(phase/'execution.json',state)


if __name__=='__main__':main()
