"""Continuation skips only preserved initial-geometry failures; no dynamics in tests."""
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_continuation_20260930 as driver


def failed(folder, rc=1, exception=None):
    folder.mkdir(parents=True,exist_ok=True)
    driver.write(folder/'execution.json',dict(status='failed',returncode=rc))
    text=exception or 'ValueError: Initial rigid body intersections: [{"pair":["rod","robot"],"depth_mm":60.0}]'
    (folder/'run.log').write_text('Traceback (most recent call last):\n  File "office_task_v4_20260917.py", line 70, in audit_initial\n'+text+'\n')


def test_exact_initial_geometry_is_classified_without_mutation(tmp_path):
    failed(tmp_path)
    before={p.name:driver.sha(p) for p in tmp_path.iterdir()}
    evidence=driver.classify_geometry(tmp_path)
    assert evidence['classification']=='invalid_initial_scene'
    assert evidence['metrics'] is None and evidence['success'] is None
    assert not evidence['retried']
    assert before=={p.name:driver.sha(p) for p in tmp_path.iterdir()}


@pytest.mark.parametrize('artifact',['audit.json','rollout.npz','rollout.progress.json','rollout_metrics','teacher_internal.npz'])
def test_any_rollout_product_prohibits_geometry_skip(tmp_path,artifact):
    failed(tmp_path);(tmp_path/artifact).write_text('partial')
    with pytest.raises(RuntimeError,match='artifacts exist'):driver.classify_geometry(tmp_path)


@pytest.mark.parametrize('rc,exception',[(2,None),(1,'RuntimeError: out of memory'),(1,'ValueError: Initial rigid body intersections: []')])
def test_unknown_or_malformed_failures_stop(tmp_path,rc,exception):
    failed(tmp_path,rc,exception)
    with pytest.raises(RuntimeError):driver.classify_geometry(tmp_path)


def test_geometry_text_without_initial_audit_frame_stops(tmp_path):
    failed(tmp_path)
    log=tmp_path/'run.log';log.write_text(log.read_text().replace('in audit_initial','in step'))
    with pytest.raises(RuntimeError,match='exact audit_initial'):driver.classify_geometry(tmp_path)


def test_search_review_requires_162_complete_anchors():
    group=dict(candidates=[dict(complete=True,anchors=[dict(complete=True)]*3) for _ in range(6)])
    review=dict(closeout=dict(reconstructed_groups={str(i):copy.deepcopy(group) for i in range(9)}))
    driver.verify_search(review)
    review['closeout']['reconstructed_groups']['8']['candidates'][5]['anchors'][0]['complete']=False
    with pytest.raises(RuntimeError,match='162'):driver.verify_search(review)


def test_registered_order_is_category_index_method_for_validation_and_index_category_method_for_train():
    plan=dict(categories=['a','b'],methods=['vmc','admittance','impedance'],validation_indices=[0,2],train_per_category=2)
    fixtures=[dict(category=c,split=s,id=f'{c}_{s}_{i:04d}') for c in plan['categories'] for s in ('train','validation') for i in range(3)]
    validation=list(driver.schedule(plan,fixtures,'validation'))
    assert [x[0] for x in validation[:4]]==['validation/a_validation_0000/vmc','validation/a_validation_0000/admittance','validation/a_validation_0000/impedance','validation/a_validation_0002/vmc']
    train=list(driver.schedule(plan,fixtures,'collection'))
    assert train[3][0]=='collection/b_train_0000/vmc'
    assert train[6][0]=='collection/a_train_0001/vmc'


def test_completed_calls_original_attempt_and_unknown_failure_never_retries(tmp_path):
    driver.write(tmp_path/'plan.json',{})
    calls=[]
    campaign=SimpleNamespace(controller_config=lambda x,m:dict(x=x),
        attempt=lambda *args:(calls.append(args) or dict(eligible=True)))
    row=driver.dispatch(campaign,tmp_path,'validation/example/vmc',dict(id='example'), 'vmc',[.5],'validation')
    assert row['classification']=='completed' and len(calls)==1
    folder=tmp_path/'validation/example/vmc'
    failed(folder,1,'RuntimeError: unrelated')
    driver.write(folder/'request.json',dict(fixture={'id':'example'},method='vmc',teacher={'x':[.5]},x=[.5],phase='validation',plan_sha256=driver.sha(tmp_path/'plan.json')))
    execution=driver.read(folder/'execution.json')
    execution['command']=[sys.executable,str(tmp_path/'source/tools/teacher_bank_rollout_20260930.py'),'--root',str(tmp_path),'--request',str(folder/'request.json')]
    driver.write(folder/'execution.json',execution)
    campaign.stale_execution_evidence=lambda *args:None
    with pytest.raises(RuntimeError):driver.dispatch(campaign,tmp_path,'validation/example/vmc',dict(id='example'),'vmc',[.5],'validation')
    assert len(calls)==1


def test_deadline_system_exit_from_original_attempt_propagates_without_new_dispatch(tmp_path):
    driver.write(tmp_path/'plan.json',{})
    calls=[]
    def deadline(*args):calls.append(args);raise SystemExit('10-hour deadline reached; no new simulation dispatched')
    campaign=SimpleNamespace(controller_config=lambda x,m:dict(x=x),attempt=deadline)
    with pytest.raises(SystemExit,match='deadline'):
        driver.dispatch(campaign,tmp_path,'collection/example/vmc',{'id':'example'},'vmc',[.5],'collection')
    assert len(calls)==1


def test_implicit_start_is_blocked(tmp_path):
    with pytest.raises(RuntimeError,match='Explicit --start'):driver.run(tmp_path)


def test_deadline_requires_exact_exit_and_matching_frozen_marker(tmp_path):
    driver.write(tmp_path/'deadline_reached.json',dict(stopped_dispatch=True,time=driver.DEADLINE+1,next_attempt='collection/x/vmc'))
    exact=SystemExit('10-hour deadline reached; no new simulation dispatched')
    assert driver.original_deadline_exit(exact,tmp_path,'collection/x/vmc',driver.DEADLINE+2)
    assert not driver.original_deadline_exit(SystemExit('unexpected'),tmp_path,'collection/x/vmc',driver.DEADLINE+2)
    assert not driver.original_deadline_exit(exact,tmp_path,'collection/other/vmc',driver.DEADLINE+2)


def test_recovered_partial_pair_is_upgraded_after_all_methods_are_accounted(tmp_path):
    methods=('vmc','admittance','impedance');calls=[]
    driver.write(tmp_path/'fixture_model_identity.json',{'f':{'model_sha256':'model'}})
    marker=tmp_path/'paired_model_checks/collection/f.json'
    driver.write(marker,[dict(fixture_id='f',methods=['vmc'],model_sha256='model',complete=False)])
    campaign=SimpleNamespace(METHODS=methods,check_paired_models=lambda *args:calls.append(args))
    rows=[dict(classification='completed',audit=dict(fixture_id='f',method=m,model_sha256='model')) for m in methods]
    result=driver.check_finished_pair(campaign,tmp_path,'collection','f',rows)
    assert result['complete'] and len(calls)==1 and len(calls[0][-1])==3


def test_all_invalid_scene_pair_is_not_reported_complete_or_success(tmp_path):
    campaign=SimpleNamespace()
    result=driver.check_finished_pair(campaign,tmp_path,'collection','f',[{'classification':'invalid_initial_scene'}]*3)
    assert result['all_invalid_initial_scene'] and not result['complete'] and result['methods']==[]


@pytest.mark.parametrize('cpu', [None,'100000 100000'])
def test_memory_and_thread_guards_with_optional_cpu_controller(tmp_path,monkeypatch,cpu):
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        monkeypatch.setenv(key,'1')
    (tmp_path/'memory.max').write_text(str(3*1024**3))
    (tmp_path/'memory.swap.max').write_text('0')
    if cpu:(tmp_path/'cpu.max').write_text(cpu)
    actual=driver.check_resources(tmp_path)
    assert actual['cpu_controller_available']==(cpu is not None)
    assert actual['quota_enforced']==(cpu is not None)
    assert actual['memory_max_bytes']==3*1024**3 and actual['memory_swap_max_bytes']==0
    if cpu is None:assert 'unavailable' in actual['reason']


def test_available_cpu_controller_with_unbounded_quota_still_rejected(tmp_path,monkeypatch):
    for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        monkeypatch.setenv(key,'1')
    (tmp_path/'memory.max').write_text(str(3*1024**3));(tmp_path/'memory.swap.max').write_text('0')
    (tmp_path/'cpu.max').write_text('max 100000')
    with pytest.raises(RuntimeError,match='CPUQuota'):driver.check_resources(tmp_path)
