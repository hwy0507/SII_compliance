from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_collection_audit_20260930 as collection
import teacher_bank_validation_audit_20260930 as validation


def tiny_plan():
    plan=dict(categories=['active_short'],train_per_category=2,methods=['vmc','admittance'],max_collection_attempts=4)
    fixtures=[dict(id=f'active_short_train_{i:04d}',category='active_short',split='train') for i in range(2)]
    return plan,fixtures


def test_terminal_gate_rejects_live_unstable_and_missing_deadline():
    good=dict(snapshot_kind='terminal_evidence',snapshot_consistency=dict(stable=True),
              terminal_basis=dict(explicit_marker=True,active_attempts_present=False))
    collection.terminal_contract(good)
    for field,value in [('stable',False),('explicit_marker',False),('active_attempts_present',True)]:
        bad=deepcopy(good)
        bad['snapshot_consistency' if field=='stable' else 'terminal_basis'][field]=value
        with pytest.raises(ValueError,match='terminal snapshot'):collection.terminal_contract(bad)


def test_preregistered_collection_refuses_validation_fixture_in_train_slot():
    plan,fixtures=tiny_plan()
    assert len(collection.registered_collection(plan,fixtures))==4
    fixtures[1]['split']='validation'
    with pytest.raises(ValueError,match='wrong-split'):collection.registered_collection(plan,fixtures)


def test_actual_attempts_reject_mixed_phase_duplicate_and_unregistered_case():
    plan,fixtures=tiny_plan();registered=collection.registered_collection(plan,fixtures)
    row=dict(folder='collection/active_short_train_0000/vmc',phase='collection',split='train',
             fixture_id='active_short_train_0000',category='active_short',method='vmc',execution_status='completed')
    assert len(collection.attempted_collection({'status':{'attempts':[row]}},registered))==1
    for changes in ({'phase':'validation'},{'split':'validation'},{'execution_status':'running'},
                    {'folder':'collection/active_short_train_9999/vmc'}):
        with pytest.raises(ValueError):
            collection.attempted_collection({'status':{'attempts':[dict(row,**changes)]}},registered)
    with pytest.raises(ValueError,match='Duplicate'):
        collection.attempted_collection({'status':{'attempts':[row,row]}},registered)


def test_unrun_definitions_are_never_counted_as_audited():
    rows=[dict(status=s) for s in ('audited','audited','invalid_initial_scene','incomplete','audit_failed')]
    result=collection.counts(rows,9000)
    assert result['actual_attempts']==5
    assert result['dynamic_audited']==2
    assert result['registered_not_attempted']==8995
    assert result['invalid_initial_scene']==result['incomplete']==result['audit_failed']==1


def test_shared_request_checker_refuses_phase_or_split_leakage_before_raw_reads(tmp_path):
    train=dict(split='train')
    with pytest.raises(ValueError,match='Fixture split'):
        validation.verify_request(tmp_path,{},None,train,'vmc',{},expected_phase='validation')
    with pytest.raises(ValueError,match='Fixture split'):
        validation.verify_request(tmp_path,{},None,dict(split='validation'),'vmc',{},expected_phase='collection')
    with pytest.raises(ValueError,match='request/phase mismatch'):
        validation.verify_request(tmp_path,dict(fixture=train,method='vmc',phase='validation'),
                                  {},train,'vmc',{},expected_phase='collection')
    with pytest.raises(ValueError,match='Unsupported'):
        validation.expected_split('search')


def test_truncated_abort_metrics_stay_outside_full_horizon_means():
    def row(full,duration,rmse):
        return dict(status='audited',category='active_long',method='vmc',eligible=False,
            full_task_horizon_completed=full,metrics=dict(actual_duration_s=duration,
            rmse_m=rmse,peak_torque_nm=30.,peak_speed_mps=.1))
    groups=collection.duration_groups([row(True,55.,.03),row(True,55.,.05),row(False,.08,9.)])
    full=next(g for g in groups if g['duration_stratum']=='full_task_horizon')
    abort=next(g for g in groups if g['duration_stratum']=='abort_or_truncated')
    assert full['count']==2 and full['mean_metrics']['rmse_m']==pytest.approx(.04)
    assert abort['count']==1 and abort['mean_metrics']['rmse_m']==9.
