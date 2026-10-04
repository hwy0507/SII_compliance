"""One continuous dependency job for the already registered final matrix.

Waits for every declared predecessor, then invokes the existing selection,
freeze and final-batch programs in order. No scheduler, new search, retry,
fallback checkpoint, or condition access in this supervisor.
"""
import argparse
import ast
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

PREDECESSORS=('teacher_bank','learning_development_v1','followup_v1',
    'controller_confirmation_v1','additional_development_v1','context_gate_development_v1',
    'context_readout_refit_development_v1','teacher_refinement_v1',
    'rl_office_adaptation_v2','rl_final_boundary_v1','final_rehearsal_v1')


def read(path):return json.loads(Path(path).read_text())
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(path,value):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)


def predecessors(root):
    rows=[]
    for name in PREDECESSORS:
        path=root/name/'execution.json'
        assert path.is_file(), 'Missing registered predecessor: '+name
        raw=path.read_bytes();state=json.loads(raw);status=state['status']
        complete=status=='complete' or (name=='teacher_refinement_v1' and status=='complete_skipped_identical_teacher')
        waiting=status=='watching' or status=='running' or status.startswith(('running_','waiting_'))
        assert complete or waiting, 'Terminal predecessor requires researcher review: '+name+' '+status
        rows.append(dict(name=name,path=str(path),status=status,complete=complete,
                         snapshot_sha256=hashlib.sha256(raw).hexdigest()))
    return rows


def development_names(runtime):
    # Read the exact existing final batch's guard without importing its heavy
    # physics dependencies into this lightweight waiting service.
    tree=ast.parse((runtime/'tools/research72_final_batch_20261003.py').read_text())
    function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='no_development_processes')
    assignment=next(n for n in function.body if isinstance(n,ast.Assign) and
                    any(isinstance(t,ast.Name) and t.id=='names' for t in n.targets))
    names=ast.literal_eval(assignment.value)
    assert isinstance(names,set) and 'research72_train_rl_20261003.py' in names
    return names


def live_development(names):
    found=[]
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            status=(proc/'status').read_text()
            if any(line.startswith('State:') and ('T (stopped)' in line or 't (tracing stop)' in line)
                   for line in status.splitlines()):continue
            argv=[p.decode(errors='replace') for p in (proc/'cmdline').read_bytes().split(b'\0') if p]
            if names.intersection(Path(x).name for x in argv[1:]):found.append(dict(pid=int(proc.name),argv=argv))
        except (FileNotFoundError,ProcessLookupError):continue
        except PermissionError:
            # Do not turn unreadable process state into proof that training ended.
            if proc.stat().st_uid==os.getuid():raise
    return found


def commands(runtime,root,out,final_output,python):
    tools=runtime/'tools'
    return [
        ('learning_selection',[python,str(tools/'research72_select_learning_20261003.py'),
            '--root',str(root),'--output',str(out/'LEARNING_SELECTION.json')]),
        ('all_model_selection',[python,str(tools/'research72_finalize_selection_20261003.py'),
            '--root',str(root),'--learning-selection',str(out/'LEARNING_SELECTION.json'),
            '--output',str(out/'FINALISTS.json')]),
        ('model_lock',[python,str(tools/'research72_final_lock_20261003.py'),
            '--root',str(root),'--finalists',str(out/'FINALISTS.json'),'--output',str(out/'MODEL_LOCK.json')]),
        ('final_evaluation',[python,str(tools/'research72_final_batch_20261003.py'),
            '--root',str(root),'--output',str(final_output),'--model-lock',str(out/'MODEL_LOCK.json')])]


def transition(runtime,root,out,final_output,python,execute):
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists() and not final_output.exists()
    for label,command in commands(runtime,root,out,final_output,python):
        if label=='final_evaluation':
            lock=read(out/'MODEL_LOCK.json')
            assert lock['training_closed'] and lock['all_registered_finalists_included']
            assert len(lock['candidates'])==38
            command+=['--lock-sha256',sha(out/'MODEL_LOCK.json')]
        execute(label,command)
    evaluation=read(final_output/'execution.json')
    summary=read(final_output/'SUMMARY.json')
    assert evaluation['status']=='complete' and evaluation['expected']==912
    assert summary['completed']==summary['expected']==912
    return dict(final_execution_sha256=sha(final_output/'execution.json'),
        final_summary_sha256=sha(final_output/'SUMMARY.json'),model_lock_sha256=sha(out/'MODEL_LOCK.json'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','runtime','output','final-output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--source-commit',required=True);args=p.parse_args()
    root=args.root.resolve();runtime=args.runtime.resolve();out=args.output.resolve();final=args.final_output.resolve()
    assert re.fullmatch('[0-9a-f]{40}',args.source_commit)
    assert runtime.parents[1].name==args.source_commit, 'Use a verified immutable full-commit source archive'
    assert out.parent==final.parent==root and out!=final
    assert not out.exists() and not final.exists() and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text())<=1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    sys.path.insert(0,str(runtime/'tools'))
    from research72_final_lock_20261003 import runtime_hashes,amendment_hashes
    protocol=read(root/'PROTOCOL.json');deadline=datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    assert datetime.now(timezone.utc)<deadline
    source_hashes=runtime_hashes(runtime);amendments=amendment_hashes(root)
    protocol_digest=sha(root/'PROTOCOL.json');names=development_names(runtime)
    initial=predecessors(root)
    out.mkdir();handle=(out/'coordinator.lock').open('x');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    spec=dict(registered_utc=now(),source_sha256=sha(__file__),supervisor_source=str(Path(__file__).resolve()),
        runtime_source_commit=args.source_commit,
        runtime=str(runtime),runtime_source_sha256=source_hashes,protocol_sha256=protocol_digest,
        amendment_sha256=amendments,predecessors=list(PREDECESSORS),initial_predecessor_snapshots=initial,
        final_output=str(final),expected_models=38,expected_conditions=24,expected_episodes=912,
        dispatch_deadline_utc=protocol['dispatch_deadline_utc'],new_search_or_fitting=False,
        selection_rule='Invoke existing aggregate all-seed public selector and registered common RL boundary unchanged.',
        stop_rule='Any failed/incomplete terminal predecessor, changed source/protocol, existing final work or command error is preserved for review; never automatically retry.',
        condition_files_read_by_supervisor=False,scheduled_automation=False)
    write(out/'SPECIFICATION.json',spec)
    state=dict(status='waiting_for_predecessors',started_utc=now(),owner_pid=os.getpid(),
        argv=sys.argv,specification_sha256=sha(out/'SPECIFICATION.json'),steps=[],predecessors=initial)
    def save():write(out/'execution.json',state)
    def guards():
        assert sha(__file__)==spec['source_sha256']
        assert sha(root/'PROTOCOL.json')==protocol_digest and amendment_hashes(root)==amendments
        assert runtime_hashes(runtime)==source_hashes
        assert datetime.now(timezone.utc)<deadline, 'Authorization deadline reached before final dispatch'
        assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists() and not final.exists()
    save()
    try:
        while True:
            guards();rows=predecessors(root);active=live_development(names)
            state.update(predecessors=rows,live_development=active,last_checked_utc=now());save()
            if all(row['complete'] for row in rows) and not active:break
            time.sleep(30)
        def execute(label,command):
            guards()
            assert all(row['complete'] for row in predecessors(root)) and not live_development(names)
            state['status']='running_'+label
            # Each command receives its own bounded child cgroup. Final batch
            # retains its existing four separately limited simulation queues.
            launch=['systemd-run','--user','--wait','--pipe','--collect',
                '--unit=sii-r72-transition-'+out.name.replace('_','-')+'-'+label.replace('_','-'),
                '--property=MemoryMax=3G','--property=MemorySwapMax=0',
                '--property=WorkingDirectory='+str(runtime),
                '--setenv=OMP_NUM_THREADS=1','--setenv=OPENBLAS_NUM_THREADS=1','--setenv=MKL_NUM_THREADS=1',
                '--setenv=SII_SOURCE_BASE_COMMIT='+args.source_commit,*command]
            row=dict(label=label,command=launch,started_utc=now());state['steps'].append(row);save()
            with (out/(label+'.log')).open('x') as log:
                rc=subprocess.run(launch,cwd=runtime,stdout=log,stderr=subprocess.STDOUT).returncode
            row.update(returncode=rc,ended_utc=now());save()
            assert rc==0, label+' failed; original evidence preserved without retry'
        result=transition(runtime,root,out,final,sys.executable,execute)
        state.update(status='complete',**result,
            completion_scope='Registered final physics and batch independent audits finished; RL actor replay, full statistics, media and manuscript still require completion.')
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();save();handle.close()


if __name__=='__main__':main()
