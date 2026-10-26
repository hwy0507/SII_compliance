from pathlib import Path
import os,sys,json,time,hashlib
os.sched_setaffinity(0,{52})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent
sys.path.insert(0,str(B/'runtime/serl_state_adapter_20261026_v1'))
from serl_state_adapter_20261026 import SerlStateLearner, OBSERVATION_SCALE
from validate_serl_state_20261026 import digest
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
evalroot=OUT/'evaluation'
e=json.loads((evalroot/'EVALUATION.json').read_text())
cp=evalroot/'checkpoint_frozen.pt'
assert sha(cp)==e['checkpoint_sha256']=='6b4c64daa94ab1c73096a15d34131d1ae2538db104a55071161ec71bebb0896e'
x=torch.load(cp,map_location='cpu',weights_only=False)
a=SerlStateLearner(B/'runtime/source_train17_clock',upstream=B/'runtime/serl_upstream_1fa2af7',upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=x['seed'],device='cuda:0')
a.load_state_dict(x['learner'])
before=digest(a.state_dict())
reg=json.loads((B/'runs/serl_batch32768_cycle02_20261026_v1/REGISTRATION.json').read_text())
conditions={c['id']:c for c in reg['conditions']}
reports=[]
for case in e['case_ids']:
    folder=evalroot/case
    if not (folder/'actor_intervals.jsonl').exists():continue
    with (folder/'actor_intervals.jsonl').open() as f:
        rows=[json.loads(line) for line in f if line.endswith('\n')]
    assert sha(folder/'rollout.mjb')==conditions[case]['model_sha256']
    maxerr=0.
    for r in rows:
        obs=np.asarray(r['observation'],np.float32)
        assert obs.shape==(48,) and np.isfinite(obs).all()
        normalized=obs/OBSERVATION_SCALE
        raw=np.asarray(a.agent.sample_actions(normalized,argmax=True))
        expected=raw.copy();expected[0]=(expected[0]+1.)*.5
        error=float(np.max(np.abs(expected-np.asarray(r['action']))));maxerr=max(maxerr,error)
        np.testing.assert_allclose(expected,r['action'],rtol=0,atol=1e-6)
        np.testing.assert_array_equal(r['executed_action'],r['action'])
        if r['interval'] is not None:
            assert r['interval']['substeps']==800
            assert abs(r['interval']['elapsed_s']-.04)<1e-10
    reports.append(dict(condition=case,actions=len(rows),max_action_error=maxerr,mjb_verified=True,canonical48=True,interval_substeps=800,physical_dt=5e-5))
assert reports and digest(a.state_dict())==before
report=dict(time=time.time(),checkpoint_sha256=sha(cp),episodes=reports,passed=True,new_physics=0,new_optimizer_updates=0,full_learner_state_unchanged=True,scope='All complete action journal rows available at this check; remaining episodes are not claimed verified',convergence_claim=False)
(OUT/'ACTION_REPLAY_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
