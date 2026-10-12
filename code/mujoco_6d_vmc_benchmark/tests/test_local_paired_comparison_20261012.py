import fcntl
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from compare_local_baselines_20261012 import ready, same_conditions, summarise, wait_for_predecessor


def conditions():
    return [dict(id=f'dev_{i}', role='development', overrides={'seed': 1}) for i in range(8)]


def test_reject_same_names_different_physics():
    a=conditions(); b=conditions(); b[0]['overrides']['seed']=2
    with pytest.raises(ValueError, match='Different conditions'):same_conditions(a,b)


def test_reject_heldout_and_duplicate():
    a=conditions(); a[0]['role']='final'
    with pytest.raises(ValueError, match='Development only'):same_conditions(a,a)
    b=conditions(); b[0]=b[1]
    with pytest.raises(ValueError, match='Duplicate'):same_conditions(b,b)


@pytest.mark.parametrize('status',['failed_preserved','stopped_requested','stopped_at_deadline'])
def test_predecessor_failure_not_success(status):
    with pytest.raises(ValueError, match='failed/stopped'):ready(status)


def test_wait_releases_lock_to_predecessor(tmp_path):
    # Real flock contention check guards the previous overnight lock regression.
    path=tmp_path/'execution.json';path.write_text(json.dumps({'status':'running'}))
    calls=[]
    def finish(_seconds):
        with (tmp_path/'compute.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            calls.append('predecessor can finish')
            path.write_text(json.dumps({'status':'complete_review_required'}))
    with patch('compare_local_baselines_20261012.time.sleep',side_effect=finish):
        wait_for_predecessor(tmp_path,lambda:calls.append('budget checked'),lambda:None)
    assert calls==['budget checked','predecessor can finish']


def test_missing_is_pending_short_failure_stays_in_denominator():
    rows=[dict(method='esn',condition=f'dev_{i}',metrics=dict(task_success=False,
        strict_success=False,full_horizon=i!=0,rmse_mm=1.,peak_torque_nm=2.,peak_speed_mps=3.)) for i in range(8)]
    summaries=summarise(rows,['esn','rl'],{f'dev_{i}' for i in range(8)})
    assert summaries[0]['complete'] and summaries[0]['task']==0 and summaries[0]['short']==1
    assert summaries[1]['task'] is None and summaries[1]['means'] is None
    with pytest.raises(ValueError,match='Duplicate'):summarise(rows+[rows[0]],['esn'],{f'dev_{i}' for i in range(8)})
