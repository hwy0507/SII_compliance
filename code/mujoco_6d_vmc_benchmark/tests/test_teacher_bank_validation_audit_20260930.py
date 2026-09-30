import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_validation_audit_20260930 as audit


def test_running_case_reads_no_request_audit_or_raw_trace(tmp_path,monkeypatch):
    (tmp_path/'execution.json').write_text(json.dumps(dict(status='running',returncode=None)))
    original=audit.read
    def guarded(path):
        assert Path(path).name=='execution.json'
        return original(path)
    monkeypatch.setattr(audit,'read',guarded)
    result=audit.audit_case(tmp_path,tmp_path,{},'vmc',{},None,None)
    assert result['status']=='skipped'


def test_independent_physical_metrics_use_actual_torque_and_vector_error(tmp_path):
    path=tmp_path/'physical.npz'
    dt=np.array([.0001]*3)
    error=np.array([[3.,4.,0.],[0.,0.,0.],[0.,0.,5.]],np.float32)
    torque=np.zeros((3,7),np.float32);torque[1,4]=-17.
    twist=np.zeros((3,6),np.float32);twist[2,:3]=[.3,.4,0.]
    np.savez_compressed(path,time=np.cumsum(dt),dt=dt,error=error,qfrc_actuator=torque,twist=twist)
    measured,_=audit.physical_metrics(path,{'dt':.0001})
    assert measured['rmse_m']==pytest.approx(np.sqrt(50/3))
    assert measured['peak_torque_nm']==17.
    assert measured['peak_speed_mps']==pytest.approx(.5)
    assert measured['actual_duration_s']==pytest.approx(.0003)


def test_nonmonotone_physical_time_is_rejected(tmp_path):
    path=tmp_path/'physical.npz'
    np.savez_compressed(path,time=[.0001,.0001],dt=[.0001,.0001],error=np.zeros((2,3)),
                        qfrc_actuator=np.zeros((2,7)),twist=np.zeros((2,6)))
    with pytest.raises(AssertionError):audit.physical_metrics(path,{'dt':.0001})


def test_paired_failed_cases_retained_but_different_models_rejected():
    rows=[dict(status='audited',fixture_id='f',method=m,model_sha256='a'*64,eligible=False)
          for m in ('vmc','admittance','impedance')]
    assert audit.paired_groups(rows,('vmc','admittance','impedance'))[0]['complete']
    rows[-1]['model_sha256']='b'*64
    with pytest.raises(ValueError,match='models differ'):
        audit.paired_groups(rows,('vmc','admittance','impedance'))


def test_lock_requires_explicit_hash_complete_history_and_exact_selection(tmp_path):
    plan=dict(categories=['active_short'],methods=['vmc'],search_candidates_per_category=2,anchor_indices=[0,1,2])
    row=dict(index=0,x=[.3],total=3)
    bank={'active_short/vmc':[dict(row,anchor_feasible=True)]}
    (tmp_path/'teacher_bank.json').write_text(json.dumps(bank))
    (tmp_path/'plan.json').write_text(json.dumps(plan))
    digest=audit.sha(tmp_path/'teacher_bank.json')
    with pytest.raises(ValueError,match='marker absent'):audit.verify_lock(tmp_path,digest)
    (tmp_path/'anchor_feasibility.json').write_text('{}')
    history=tmp_path/'search/active_short/vmc/history.json';history.parent.mkdir(parents=True)
    history.write_text(json.dumps([row]))
    with pytest.raises(ValueError,match='history incomplete'):audit.verify_lock(tmp_path,digest)
    history.write_text(json.dumps([row,dict(index=1,x=[.4],total=3)]))
    assert audit.verify_lock(tmp_path,digest)[1]==bank
    with pytest.raises(ValueError,match='hash mismatch'):audit.verify_lock(tmp_path,'wrong')


def test_frozen_policy_boundary_abort_is_retained_without_full_horizon_claim():
    result=audit.audit_duration(2,.08,55.,'global_penetration_exceeded_2mm')
    assert not result['full_task_horizon_completed']
    assert not result['physical_horizon_duration_recorded']
    # A failure at the final boundary still is not evaluator horizon success.
    result=audit.audit_duration(1375,55.,55.,'global_penetration_exceeded_2mm')
    assert result['physical_horizon_duration_recorded']
    assert not result['full_task_horizon_completed']


def test_half_policy_abort_is_not_legal_completed_evidence_in_frozen_v10():
    # Frozen env.step never breaks its servo/substep loops. Such a trace is
    # partial/infrastructure evidence, not a completed evaluator abort episode.
    with pytest.raises(AssertionError,match='whole policy steps'):
        audit.audit_duration(2,.06,55.,'global_penetration_exceeded_2mm')
    with pytest.raises(ValueError,match='Unexplained truncated'):
        audit.audit_duration(2,.08,55.,None)
