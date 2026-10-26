from pathlib import Path
import os,sys,json,time,hashlib
os.sched_setaffinity(0,{54})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent
sys.path.insert(0,str(B/'runtime/serl_cycle10_fixed_representatives_20261026_v1'))
from serl_multistep_state_adapter_20261026 import SerlMultistepLearner as SerlStateLearner
from serl_state_adapter_20261026 import OBSERVATION_SCALE
from validate_serl_state_20261026 import digest
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
evalroot=OUT/'evaluation'
e=json.loads((evalroot/'EVALUATION.json').read_text())
cp=evalroot/'checkpoint_frozen.pt'
assert sha(cp)==e['checkpoint_sha256']=='ed5790843b1fef76efb371a4ac12ceb4b9b47093fbdb73d603a0372f18f9dc54'
x=torch.load(cp,map_location='cpu',weights_only=False)
a=SerlStateLearner(B/'runtime/source_train17_clock',upstream=B/'runtime/serl_upstream_1fa2af7',upstream_manifest=B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=x['seed'],device='cuda:0')
a.load_state_dict(x['learner'])
before=digest(a.state_dict())
reg=json.loads((B/'runs/serl_multistep_cycle10_20261026_v1/REGISTRATION.json').read_text())
conditions={c['id']:c for c in reg['conditions']}
assert json.loads((OUT/'PHYSICAL_AUDITS_COMPLETE.json').read_text())['episodes']==3
assert json.loads((evalroot/'RESULTS.json').read_text())['finished']
assert json.loads((evalroot/'POLICY_UNCHANGED.json').read_text())['full_learner_state_unchanged']
reports=[]
for case in e['case_ids']:
    folder=evalroot/case
    assert (folder/'actor_intervals.jsonl').exists()
    with (folder/'actor_intervals.jsonl').open() as f:
        rows=[json.loads(line) for line in f if line.endswith('\n')]
    assert sha(folder/'rollout.mjb')==conditions[case]['model_sha256']
    maxerr=0.
    for action_index,r in enumerate(rows):
        obs=np.asarray(r['observation'],np.float32)
        assert obs.shape==(48,) and np.isfinite(obs).all()
        normalized=obs/OBSERVATION_SCALE
        raw=np.asarray(a.agent.sample_actions(dict(state=np.ascontiguousarray(normalized),clock=np.array([(1375-action_index)/1375],np.float32)),argmax=True))
        expected=raw.copy();expected[0]=(expected[0]+1.)*.5
        error=float(np.max(np.abs(expected-np.asarray(r['action']))));maxerr=max(maxerr,error)
        np.testing.assert_allclose(expected,r['action'],rtol=0,atol=1e-6)
        np.testing.assert_array_equal(r['executed_action'],r['action'])
        if r['interval'] is not None:
            assert 0<r['interval']['substeps']<=800
            assert abs(r['interval']['elapsed_s']-r['interval']['substeps']*5e-5)<1e-10
    physical=json.loads((folder/'PHYSICS_REVIEW.json').read_text())
    filtered=json.loads((folder/'FILTER_REVIEW.json').read_text())
    torque=json.loads((folder/'TORQUE_REVIEW.json').read_text())
    assert 0<physical['samples']<=1100000 and filtered['passed'] and torque['passed']
    result=next(v for v in json.loads((evalroot/'RESULTS.json').read_text())['episodes'] if v['condition']==case)
    assert len(rows)==result['actions'] and 0<len(rows)<=1375
    if result['result']['full_task_horizon_completed']:assert physical['samples']==1100000 and len(rows)==1375
    else:assert result['result']['abort_reason'] and physical['samples']<1100000
    for name,h in physical['evidence_sha256'].items():assert sha(folder/name)==h
    for name,h in filtered.get('evidence_sha256',{}).items():assert sha(folder/name)==h
    for name,h in torque.get('evidence_sha256',{}).items():assert sha(folder/name)==h
    action_array=np.asarray([r['action'] for r in rows])
    reports.append(dict(physical=physical,filter=filtered,torque=torque,mean_slowdown=float(action_array[:,0].mean()),final_10s_slowdown=float(action_array[-250:,0].mean()),condition=case,actions=len(rows),max_action_error=maxerr,mjb_verified=True,canonical48=True,interval_substeps=800,physical_dt=5e-5))
assert len(reports)==3 and digest(a.state_dict())==before
report=dict(time=time.time(),checkpoint_sha256=sha(cp),episodes=reports,passed=True,new_physics=0,new_optimizer_updates=0,full_learner_state_unchanged=True,scope='All three preselected deterministic cases, including early aborts if any; actual substeps/actions reported per case; not full30 or final convergence comparison',convergence_claim=False)
(OUT/'FINAL_SCIENTIFIC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
