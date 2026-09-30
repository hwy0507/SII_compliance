import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from analyze_measured_policy_ablations_20260923 import analyze_job, decision


def test_short_smoke_never_becomes_performance_result(tmp_path):
    job=tmp_path/'esn_lowpass_025'/'9301'
    (job/'rollout').mkdir(parents=True)
    (job/'metrics').mkdir()
    (job/'command.json').write_text('{}')
    (job/'rollout/rollout.json').write_text(json.dumps({'arguments':{'duration':.4}}))
    np.savez(job/'rollout/rollout.npz',observation=np.zeros((10,48)),action=np.zeros((10,7)),
             time=np.arange(1,11)*.04,position=np.zeros((10,3)),target=np.zeros((10,3)))
    (job/'metrics/audit_manifest.json').write_text(json.dumps({'enabled':True,'error':None,
        'episodes':[{'samples':8000,'timestep_s':.00005}]}))
    result=analyze_job(tmp_path,'esn_lowpass_025',9301,{})
    assert result['status']=='short_or_incomplete_not_performance'
    assert 'task_success' not in result


def test_no_expansion_until_all_full_paired_controls_arrive():
    rows=[{'method':'esn_lowpass_025','status':'complete','strict_success':True}]
    assert decision(rows)[0]=='WAIT_FULL_PAIRED_RESULTS'
