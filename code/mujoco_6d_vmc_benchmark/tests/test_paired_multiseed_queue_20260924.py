"""No simulator or policy training; test paired queue failure boundary."""
import importlib.util
from pathlib import Path
import sys
import threading
import json
from types import SimpleNamespace
import pytest

TOOLS=Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
spec=importlib.util.spec_from_file_location('multiseed_queue',TOOLS/'run_paired_multiseed_queue_20260924.py')
queue=importlib.util.module_from_spec(spec);spec.loader.exec_module(queue)

def jobs():
    return [dict(seed=s,mode=m) for s in queue.entry.SEEDS for m in ('parameter6','direct7')]

def test_failed_first_seed_keeps_started_peer_and_never_starts_second_seed():
    stop=threading.Event();both_started=threading.Barrier(2);failed=threading.Event();records=[]
    def worker(job):
        both_started.wait(timeout=5)
        if job['mode']=='parameter6':
            stop.set();records.append(dict(job,execution_error='synthetic execution error'));failed.set()
        else:
            assert failed.wait(timeout=5)
            records.append(dict(job,complete=True,original_artifacts_retained=True))
    with pytest.raises(ValueError,match='later seed not started'):
        queue.run_seed_pairs(jobs(),worker,stop)
    assert len(records)==2
    assert {r['seed'] for r in records}=={20260924}
    assert next(r for r in records if r['mode']=='direct7')['original_artifacts_retained']

def test_second_seed_starts_only_after_entire_first_pair_finishes():
    stop=threading.Event();lock=threading.Lock();finished=[]
    def worker(job):
        with lock:
            if job['seed']==20260925:
                assert sum(s==20260924 for s,m in finished)==2
            finished.append((job['seed'],job['mode']))
    queue.run_seed_pairs(jobs(),worker,stop)
    assert set(finished)=={(s,m) for s in queue.entry.SEEDS for m in ('parameter6','direct7')}

def test_owned_cleanup_is_bounded_and_does_not_target_peer(monkeypatch):
    signals=[]
    monkeypatch.setattr(queue.os,'killpg',lambda pid,sig:signals.append((pid,sig)))
    class FakeProcess:
        pid=12345
        calls=0
        def poll(self):return None
        def wait(self,timeout):
            assert timeout==15
            self.calls+=1
            if self.calls==1:raise queue.subprocess.TimeoutExpired('fake',timeout)
            return -9
    process=FakeProcess();queue.terminate_owned(process)
    assert signals==[(12345,queue.signal.SIGTERM),(12345,queue.signal.SIGKILL)]
    assert process.calls==2

def test_parent_status_failure_after_popen_reaps_owned_child(tmp_path,monkeypatch):
    """Exercise production worker finally after a parent-side write failure."""
    original_dump=queue.dump;injected=[];children=[];signals=[]
    def failing_dump(path,value):
        if path.name=='status.json' and value.get('active') and not injected:
            injected.append(True)
            raise OSError('synthetic parent status write failure')
        original_dump(path,value)
    class FakeProcess:
        def __init__(self,*args,**kwargs):
            assert kwargs['start_new_session'] is True
            self.pid=15000+len(children);self.alive=True;children.append(self)
        def poll(self):return None if self.alive else -15
        def wait(self,timeout):self.alive=False;return -15
    monkeypatch.setattr(queue,'dump',failing_dump)
    monkeypatch.setattr(queue,'source_manifest',lambda:{})
    monkeypatch.setattr(queue.base,'asset_hashes',lambda _: {})
    monkeypatch.setattr(queue.base,'resource_check',lambda:None)
    monkeypatch.setattr(queue.subprocess,'Popen',FakeProcess)
    monkeypatch.setattr(queue.os,'killpg',lambda pid,sig:signals.append((pid,sig)))
    preflight=tmp_path/'PREFLIGHT.json';preflight.write_text('{}')
    items=[dict(j,output=str(tmp_path/'training'/str(j['seed'])/j['mode']),command=['fake']) for j in jobs()]
    plan=dict(status='prepared_not_started',max_workers=2,global_cap=4,jobs=items,source_sha256={},
        menagerie=str(tmp_path),asset_hashes={},preflight_sha256=queue.sha(preflight),proof_reuse={},job_timeout_s=7200)
    path=tmp_path/'PLAN.json';path.write_text(json.dumps(plan))
    args=SimpleNamespace(root=tmp_path,expected_plan_sha256=queue.sha(path),available_worker_slots=2,proof_root=tmp_path)
    with pytest.raises(ValueError,match='later seed not started'):
        queue.execute(args)
    assert injected and children and all(not p.alive for p in children)
    assert (children[0].pid,queue.signal.SIGTERM) in signals
    rows=json.loads((tmp_path/'results.json').read_text())['rows']
    assert {r['seed'] for r in rows}=={20260924}
    assert any('synthetic parent status write failure' in r.get('execution_error','') for r in rows)
    assert (tmp_path/'FAILED.json').exists()
