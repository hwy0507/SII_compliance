from pathlib import Path
import os,sys,json,hashlib,time
import numpy as np
import torch
out=Path(__file__).parent;reg=json.loads((out/'REGISTRATION.json').read_text());b=out.parents[2];m=reg['controller'];os.sched_setaffinity(0,{reg['cpu']});torch.set_num_threads(1)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rt=Path(reg['audit_runtime']);sys.path.insert(0,str(rt));sys.path.insert(0,str(Path(reg['runtime'])/'source/tools'))
from published_compliance_learner_20261025 import PublishedLearner
from published_projected_terminal_learner_20261026 import projected_class
from validate_published_finite_check_20261025 import digest
from summarize_published_episode_audit_20261025 import summarize
from replay_published_filter_audit_20261025 import audit as filter_audit
from replay_published_torque_audit_20261025 import audit as torque_audit
for n,h in reg['source_hashes'].items():assert sha(rt/n)==h
cp=out/'evaluation/checkpoint_frozen.pt';assert sha(cp)==reg['checkpoint_sha256']==sha(reg['checkpoint'])
ck=torch.load(cp,map_location='cpu',weights_only=False);v=ck['learner'];prior=read(Path(reg['runtime'])/'parameter/PRIORS.json')
a=projected_class(PublishedLearner)(Path(reg['runtime']),dimension=prior['methods'][m]['action_dimension'],direct=False,seed=ck['seed'],device=reg['device'],algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);a.load_state_dict(v);initial=digest(a.state_dict());assert initial==digest(v)
e=read(out/'evaluation/RESULTS.json');assert e['finished'] and len(e['episodes'])==3 and e['evaluation']['deterministic']
conditions={c['id']:c for c in read(reg['training_registration'])['conditions']};results=[]
for episode in e['episodes']:
 case=episode['condition'];folder=out/'evaluation'/case;assert sha(folder/'rollout.mjb')==conditions[case]['model_sha256']
 physical=summarize(folder,m,case);filtered=filter_audit(folder);torque=torque_audit(folder);assert filtered['passed'] and torque['passed']
 rows=[json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()];assert len(rows)==episode['actions'] and 0<len(rows)<=1375
 if episode['result']['full_task_horizon_completed']:assert len(rows)==1375 and physical['samples']==1100000
 else:assert episode['result']['abort_reason'] and physical['samples']<1100000
 a.reset_episode();error=0.
 for i,row in enumerate(rows):
  obs,raw,action,context=a.act(row['observation'],step=ck['steps'],deterministic=True)
  assert obs.shape==(50,) and obs[-1]==np.float32((1375-i)/1375)
  error=max(error,float(np.max(abs(action-np.asarray(row['action'])))));np.testing.assert_allclose(action,row['action'],rtol=0,atol=1e-7)
  executed=np.asarray(row['executed_action']);assert executed.shape==(7,) and np.isfinite(executed).all()
 results.append(dict(condition=case,physical=physical,filter=filtered,torque=torque,actions=len(rows),max_parameter_action_error=error,clock_verified=True,mjb_verified=True))
assert digest(a.state_dict())==initial
report=dict(passed=True,controller=m,checkpoint_sha256=sha(cp),registration_sha256=sha(out/'REGISTRATION.json'),episodes=results,total_actions=sum(r['actions'] for r in results),total_substeps=sum(r['physical']['samples'] for r in results),task=sum(r['physical']['row']['task_success'] for r in results),strict=sum(r['physical']['row']['strict_success'] for r in results),full_learner_state_unchanged=True,new_optimizer_updates=0,new_physics=0,scope='Independent replay and raw-substep audits of three preselected frozen-policy episodes; not full30 or final ranking',convergence_claim=False,time=time.time())
(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
