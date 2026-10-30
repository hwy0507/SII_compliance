"""Read-only partial75 terminal baseline for recovery76; no physics or updates."""
from pathlib import Path
import hashlib,json,time,os,sys
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
OUT=Path(__file__).resolve().parent
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read(OUT/'ANCHOR_PLAN.json')
for n,h in p['sources'].items():assert sha(OUT/n)==h
for x in p['inputs'].values():assert sha(x['path'])==x['sha256']
reg=read(p['inputs']['registration']['path']);runtime=Path(reg['runtime']);helper=Path(p['helper_runtime'])
assert sha(runtime/'RUNTIME.json')==reg['runtime_sha256']
for n,h in read(runtime/'SOURCE_HASHES.json').items():assert sha(runtime/'source'/n)==h
for n,h in reg['batch_size_stage']['dependency_hashes'].items():assert sha(helper/n)==h
sys.path[:0]=[str(helper),str(runtime/'source/tools')]
from published_compliance_learner_20261025 import PublishedLearner
from validate_published_finite_check_20261025 import digest
ck=torch.load(p['inputs']['checkpoint']['path'],map_location='cpu',weights_only=False)
audit=read(p['inputs']['partial_audit']['path']);overall=read(p['inputs']['aggregate_audit']['path']);assert overall['passed'] and overall['methods'][p['method']]==audit
assert ck['cycle']==75 and ck['boundary']=='partial_episode_valid_replay_reset_environment_on_resume' and ck['controller']==p['method']
assert sha(p['inputs']['checkpoint']['path'])==audit['checkpoint_sha256']
a=ck['replay']['arrays'];state=ck['learner'];idx=np.flatnonzero(a['dones'][:,0]==1);assert len(idx)==2244
features=np.concatenate([a['observations'][idx],a['actions'][idx]],axis=1);rewards=a['rewards'][idx,0];masks=a['masks'][idx].T
with np.load(p['inputs']['full74_anchor']['path'],allow_pickle=False) as old:
 for k,v in [('indices',idx),('features',features),('rewards',rewards),('masks',masks)]:np.testing.assert_array_equal(v,old[k])
assert features.shape==(2244,57) and ck['replay']['capacity']==4000000 and state['terminal_loss_weight']==128
learner=PublishedLearner(runtime,dimension=7,direct=False,seed=42,device='cpu',algorithm=state['algorithm'],**{k:state[k] for k in ['critic_layer_norm','numerical_amendments','critic_clock']})
agent=learner.learner.agent;agent.load_state_dict(state['agent']);before=digest(agent.state_dict());assert before==digest(state['agent']);rng=torch.get_rng_state().clone()
with torch.no_grad():
 obs=torch.as_tensor(a['observations'][idx]);action=torch.as_tensor(a['actions'][idx]);q=torch.stack([agent.get_q_value(obs,action,i,target=False).reshape(-1) for i in range(5)]).numpy()
assert q.shape==(5,2244) and np.isfinite(q).all() and digest(agent.state_dict())==before and torch.equal(rng,torch.get_rng_state())
den=a['masks'].sum(axis=0,dtype=float)+127*masks.sum(axis=1,dtype=float)
sse=float((masks*(q.astype(float)-rewards.astype(float)[None])**2).sum())
assert not (OUT/'anchor_partial75.npz').exists()
np.savez_compressed(OUT/'anchor_partial75.npz',indices=idx,features=features,rewards=rewards,masks=masks,q_after=q,denominator=den)
for x in p['inputs'].values():assert sha(x['path'])==x['sha256']
r=dict(passed=True,time=time.time(),method=p['method'],terminal_rows=2244,features_shape=[2244,57],groups=dict(all2244=dict(masked_sse_after=sse)),anchor_sha256=sha(OUT/'anchor_partial75.npz'),checkpoint=p['inputs']['checkpoint'],source_sha256=sha(Path(__file__)),old74_inputs_exact=True,weights_and_forward_rng_unchanged=True,new_network_forward=5,new_physics=0,optimizer_updates=0,replay_writes=0,limitation='Q recomputed from audited saved partial75 weights; denominator includes all retained partial75 rows. Not complete75.')
(OUT/'ANCHOR_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
