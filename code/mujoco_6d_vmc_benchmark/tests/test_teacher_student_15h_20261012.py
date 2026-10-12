import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from teacher_student_15h_20261012 import Campaign, predecessor_ready, pareto, qualified, write


def test_baseline_is_a_hard_precondition():
    assert not predecessor_ready(dict(status='running'))
    assert predecessor_ready(dict(status='complete_review_required', verified_rows=168, new_episodes_completed=64))
    for status in ('failed_preserved', 'stopped_at_deadline', 'success'):
        with pytest.raises(ValueError):
            predecessor_ready(dict(status=status))
    with pytest.raises(ValueError):
        predecessor_ready(dict(status='complete_review_required', verified_rows=167, new_episodes_completed=64))


def test_pareto_cannot_promote_fast_failure_or_unsafe_success():
    def row(name, rms, torque, n=2):
        return dict(name=name, rmse_mm=rms, peak_torque_nm=torque, qualified=n, expected=2)
    rows=[row('a',10,40), row('b',20,30), row('dominated',25,45), row('failed',1,1,0)]
    assert {r['name'] for r in pareto(rows)}=={'a','b'}
    assert not qualified(dict(full_horizon=True,task_success=True,strict_success=False))
    assert not qualified(dict(full_horizon=False,task_success=True,strict_success=True))


def test_deadline_and_stop_prevent_new_work(tmp_path):
    c=Campaign.__new__(Campaign); c.out=tmp_path
    c.deadline=datetime.now(timezone.utc)-timedelta(seconds=1)
    with pytest.raises(ValueError,match='deadline'):c.check()
    c.deadline=datetime.now(timezone.utc)+timedelta(hours=1)
    (tmp_path/'STOP_REQUESTED').touch()
    with pytest.raises(ValueError,match='Stop requested'):c.check()


def test_completed_job_is_not_repeated_and_changed_evidence_rejected(tmp_path):
    c=Campaign.__new__(Campaign);c.out=tmp_path;(tmp_path/'receipts').mkdir()
    from teacher_student_15h_20261012 import sha
    evidence=tmp_path/'artifact'; evidence.write_text('original')
    command=['not-a-real-command']
    write(tmp_path/'receipts/test.json',dict(status='complete',command=command,products={str(evidence):sha(evidence)}))
    c.job('test',command)  # Must not invoke a subprocess or resource check.
    evidence.write_text('changed')
    with pytest.raises(ValueError,match='product changed'):c.job('test',command)
    write(tmp_path/'receipts/test.json',dict(status='running',command=command))
    with pytest.raises(ValueError,match='preserved'):c.job('test',command)


def test_child_failure_propagates_and_preserves_receipt(tmp_path, monkeypatch):
    c=Campaign.__new__(Campaign);c.out=tmp_path;c.source=tmp_path;c.env={}
    c.state={};c.deadline=datetime.now(timezone.utc)+timedelta(hours=1)
    (tmp_path/'receipts').mkdir()
    from types import SimpleNamespace
    import teacher_student_15h_20261012 as module
    monkeypatch.setattr(module.shutil,'disk_usage',lambda p:SimpleNamespace(free=100*1024**3))
    original=Path.read_text
    monkeypatch.setattr(Path,'read_text',lambda p,*a,**k: 'MemAvailable: 10000000 kB\n' if str(p)=='/proc/meminfo' else original(p,*a,**k))
    monkeypatch.setattr(module.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=7))
    with pytest.raises(ValueError,match='Child failed'):c.job('bad',['false'])
    receipt=module.read(tmp_path/'receipts/bad.json')
    assert receipt['status']=='failed_preserved' and receipt['returncode']==7
    assert '--property=MemoryMax=3G' in receipt['managed_command']
    assert '--property=MemorySwapMax=0' in receipt['managed_command']


def test_condition_sampling_splits_and_temporal_clearance():
    from research72_protocol_20261003 import sample
    rows=sample(202610121528,[('train',66),('imitation_validation',16)])
    assert len(rows)==82
    assert len({tuple(sorted(c['overrides'].items())) for c in rows})==82
    assert all(c['overrides']['rod_start']>=c['overrides']['person_start']+8 for c in rows)
