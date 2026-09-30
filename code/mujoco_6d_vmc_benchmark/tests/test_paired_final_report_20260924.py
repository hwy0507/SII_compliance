import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec=importlib.util.spec_from_file_location('final_report',Path(__file__).resolve().parents[1]/'tools/report_paired_final_audit_20260924.py')
report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)


def trace(n,invalid=False):
    raw=dict(observation=np.zeros((n,48)),time=.04*np.arange(1,n+1),
        position=np.repeat(np.arange(n)[:,None],3,axis=1)*.001,target=np.zeros((n,3)))
    return raw,dict(invalid_physics=invalid,duration_s=.04*n),dict(complete=True,transitions=n)


@pytest.mark.parametrize('n,invalid',[(600,False),(399,True),(3,True)])
def test_safe_failure_is_preserved_with_actual_duration_and_available_endpoint_window(n,invalid):
    raw,result,audit=trace(n,invalid);timing,endpoint=report.validate_evaluation_trace(raw,result,audit)
    assert timing['safety_early_termination']==(n<600) and timing['duration_s']==.04*n
    assert timing['endpoint_window_frames']==min(10,n)
    assert endpoint==float(np.mean(np.linalg.norm(raw['position'][-min(10,n):],axis=1)))


@pytest.mark.parametrize('error',['not_invalid','not_terminal','wrong_duration','wrong_count'])
def test_incomplete_or_inconsistent_evaluation_cannot_be_marked_terminal(error):
    raw,result,audit=trace(399,True)
    if error=='not_invalid':result['invalid_physics']=False
    elif error=='not_terminal':audit['complete']=False
    elif error=='wrong_duration':result['duration_s']+=.04
    else:audit['transitions']+=1
    with pytest.raises(ValueError):report.validate_evaluation_trace(raw,result,audit)


@pytest.mark.parametrize('seed',[20260923,20260924,20260925])
def test_saved_model_seed_must_match_each_declared_seed(seed):
    manifest={'training':{'seed':seed}}
    assert report.validate_model_seed({'seed':seed},manifest,{'seed':seed})==seed
    # Original COMPLETE predates its explicit seed field; zip still must have it.
    assert report.validate_model_seed({'seed':seed},manifest,{})==seed
    with pytest.raises(ValueError,match='Final model seed metadata mismatch'):
        report.validate_model_seed({'seed':seed+1},manifest,{'seed':seed})


@pytest.mark.parametrize('model,error',[({},'missing'),({'seed':None},'mismatch')])
def test_missing_or_null_saved_model_seed_cannot_default_to_manifest(model,error):
    with pytest.raises(ValueError,match='Final model seed metadata '+error):
        report.validate_model_seed(model,{'training':{'seed':20260924}},{'seed':20260924})


def test_complete_seed_cannot_disagree_with_model_and_manifest():
    with pytest.raises(ValueError,match='COMPLETE seed metadata mismatch'):
        report.validate_model_seed({'seed':20260925},{'training':{'seed':20260925}},{'seed':20260924})
