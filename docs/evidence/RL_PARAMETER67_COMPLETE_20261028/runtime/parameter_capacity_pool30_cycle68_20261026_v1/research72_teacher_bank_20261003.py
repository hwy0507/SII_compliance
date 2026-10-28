"""Continuous finite teacher collection; checkpoint each completed episode.

Resume skips only hash-verified completed episodes. An interrupted episode is
never silently overwritten/retried. Four sequential queues, no recurring timer.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from run_all_methods_formal_20261003 import V6, MENAGERIE, active_workers
from run_paper_final_validation_20261003 import ENV


def read(path):
    return json.loads(path.read_text())


def run_queue(root, index):
    protocol = read(root/'PROTOCOL.json'); digest = sha(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json') == protocol['condition_file_sha256']
    assert sha(root/'teacher.json') == protocol['teacher_config_sha256']
    phase = root/'teacher_bank'/f'queue_{index}'
    phase.mkdir(parents=True, exist_ok=True)
    with (phase/'queue.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = phase/'source'
        if not source.exists():
            for folder in ('scripts','assets','tools'):
                shutil.copytree(ROOT/folder, source/folder, ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
            write(phase/'SOURCE_HASHES.json', {str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()})
        for name, expected in read(phase/'SOURCE_HASHES.json').items():
            assert sha(source/name) == expected
        conditions = read(root/'CONDITIONS.json')['conditions'][index::4]
        state = read(phase/'execution.json') if (phase/'execution.json').exists() else dict(
            status='running',started_utc=now(),protocol_sha256=digest,rows=[])
        assert state['protocol_sha256'] == digest
        if state['status'] == 'complete':
            assert len(state['rows']) == len(conditions)
        state['status'] = 'running'; write(phase/'execution.json',state)
        env = {**os.environ, **ENV, 'SII_SOURCE_BASE_COMMIT':protocol['source_base_commit'], 'MUJOCO_MENAGERIE_PATH':str(MENAGERIE)}
        try:
            for c in conditions:
                name = c['id']; run = phase/name
                old = next((r for r in state['rows'] if r['name']==name), None)
                if old is not None:
                    assert old.get('returncode') == 0, 'Incomplete execution preserved: '+name
                    assert read(run/'execution.json')['status'] == 'complete'
                    assert sha(run/'AUDIT.json') == old['audit_sha256']
                    assert sha(run/'rollout.npz') == old['trace_sha256']
                    continue
                if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['dispatch_deadline_utc']):
                    state['status']='deadline_no_new_dispatch';break
                assert not run.exists(), 'Unregistered output preserved'
                cmd=[sys.executable,str(source/'tools/research72_worker_20261003.py'),
                    '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',digest,'--research-condition',name,
                    '--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
                    '--config',str(root/'teacher.json'),'--output',str(run),'--contact-audit','--physics-dt',str(protocol['physics_dt_s'])]
                row=dict(name=name,role=c['role'],started_utc=now(),command=cmd);state['rows'].append(row)
                write(phase/'execution.json',state)
                with (phase/(name+'.log')).open('x') as log:
                    rc=subprocess.run(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
                row.update(returncode=rc,ended_utc=now());write(phase/'execution.json',state)
                if rc:raise RuntimeError(name+' failed infrastructure; no automatic retry')
                audit=read(run/'AUDIT.json')
                row.update(audit=audit,audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
                write(phase/'execution.json',state)
            else:state['status']='complete'
        except BaseException as exc:
            state.update(status='failed_preserved',error=repr(exc));raise
        finally:
            state['ended_utc']=now();write(phase/'execution.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--queue',type=int,choices=range(4));a=p.parse_args();root=a.root.resolve()
    if a.queue is not None:run_queue(root,a.queue);return
    root.joinpath('teacher_bank').mkdir(exist_ok=True)
    with (root/'teacher_bank/coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not active_workers(), 'Existing native simulation; no duplicate dispatch'
        # Include this wrapper (the historical checker predates it).
        for proc in Path('/proc').glob('[0-9]*/cmdline'):
            try:names={Path(v.decode(errors='replace')).name for v in proc.read_bytes().split(b'\0')}
            except (OSError,ProcessLookupError):continue
            assert 'research72_worker_20261003.py' not in names, 'Existing research worker'
        state=dict(status='running',started_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),queues=[])
        write(root/'teacher_bank/execution.json',state)
        def queue(i):
            unit='sii-r72-teacher-'+root.name.split('_')[-1]+'-'+str(i)
            cmd=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
                '--property=MemoryMax=3G','--property=MemorySwapMax=0']
            cmd += ['--setenv='+k+'='+v for k,v in ENV.items()]
            cmd += [sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--queue',str(i)]
            with (root/'teacher_bank'/f'queue_{i}.log').open('a') as log:
                rc=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT).returncode
            return dict(queue=i,returncode=rc,command=cmd)
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:state['queues']=list(pool.map(queue,range(4)))
            assert all(q['returncode']==0 for q in state['queues'])
            for i in range(4):
                phase=root/'teacher_bank'/f'queue_{i}';out=phase.with_name(phase.name+'_analysis')
                if out.exists():
                    assert read(out/'execution.json')['status']=='complete'
                    continue
                cmd=[sys.executable,str(ROOT/'tools/audit_paper_phase_20261003.py'),'--phase',str(phase),
                    '--output',str(out),'--model-sha256',read(root/'PROTOCOL.json')['formal_model_sha256']]
                with (root/'teacher_bank'/f'audit_{i}.log').open('x') as log:
                    subprocess.run(cmd,check=True,env={**os.environ,**ENV},stdout=log,stderr=subprocess.STDOUT)
            rows=[dict(r,run=str(root/'teacher_bank'/f'queue_{i}'/r['name']))
                  for i in range(4) for r in read(root/'teacher_bank'/f'queue_{i}'/'execution.json')['rows']]
            write(root/'teacher_bank/SUMMARY.json',dict(completed_utc=now(),rows=rows,
                count=len(rows),task=sum(r['audit']['task_success'] for r in rows),strict=sum(r['audit']['strict_success'] for r in rows),
                roles={role:dict(total=sum(r['role']==role for r in rows),qualified=sum(r['role']==role and r['audit']['strict_success'] and r['audit']['task_success'] for r in rows))
                       for role in ('train','imitation_validation','development')}))
            state['status']='complete'
        except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
        finally:state['ended_utc']=now();write(root/'teacher_bank/execution.json',state)


if __name__=='__main__':main()
