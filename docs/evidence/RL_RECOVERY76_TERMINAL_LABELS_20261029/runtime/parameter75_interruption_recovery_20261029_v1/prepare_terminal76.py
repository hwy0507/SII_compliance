from pathlib import Path
import json,time,hashlib,difflib,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
capture='''"""Read-only partial75 terminal baseline for recovery76; no physics or updates."""
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
audit=read(p['inputs']['partial_audit']['path']);assert audit['passed']
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
(OUT/'ANCHOR_REVIEW.json').write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''
review='''from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{53})
import numpy as np
p=Path(__file__).parent;plan=json.loads((p/'ANCHOR_PLAN.json').read_text());r=json.loads((p/'ANCHOR_REVIEW.json').read_text())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(p/'anchor_partial75.npz')==r['anchor_sha256']
with np.load(p/'anchor_partial75.npz',allow_pickle=False) as a,np.load(plan['inputs']['full74_anchor']['path'],allow_pickle=False) as old:
 assert a['features'].shape==(2244,57) and a['q_after'].shape==(5,2244)
 for k in ['indices','features','rewards','masks']:np.testing.assert_array_equal(a[k],old[k])
 assert np.isfinite(a['q_after']).all() and np.all(a['denominator']>=old['denominator'])
 sse=math.fsum(float(a['masks'][i,j])*(float(a['q_after'][i,j])-float(a['rewards'][j]))**2 for i in range(5) for j in range(2244));assert math.isclose(sse,r['groups']['all2244']['masked_sse_after'],rel_tol=1e-12,abs_tol=1e-12)
 out=dict(passed=True,time=time.time(),all2244_fixed_inputs_exact=True,independent_scalar_sse=sse,partial75_denominator=a['denominator'].tolist(),full74_denominator=old['denominator'].tolist(),anchor_sha256=sha(p/'anchor_partial75.npz'),source_sha256=sha(Path(__file__)),new_physics=0,optimizer_updates=0)
(p/'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out))
'''
for m in ['vmc','admittance']:
 old=B/f'runs/{m}75_terminal_anchor_followup_20261028_v1';out=B/f'runs/{m}_recovery76_terminal_followup_20261029_v1';out.mkdir(exist_ok=False)
 for name in ['track.py','review_values.py','wait.py']:
  s=(old/name).read_text();new=s.replace('complete75','complete76').replace('Complete75','Complete76').replace("ck['cycle']==75","ck['cycle']==76").replace('health75','health76').replace('follow75.png','follow76.png').replace('fixed74','partial75').replace('Complete74 masked','Partial75 masked')
  ast.parse(new);(out/name).write_text(new);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(old/name),tofile=str(out/name))))
 for name,s in [('capture_anchor.py',capture),('review_anchor.py',review)]:ast.parse(s);(out/name).write_text(s)
 inputs=dict(checkpoint=ref(B/f'runs/parameter75_interruption_recovery_20261029_v1/{m}/checkpoint_partial75.pt'),partial_audit=ref(B/f'runs/parameter75_interruption_recovery_20261029_v1/{m}/REVIEW.json'),registration=ref(RUN/m/'REGISTRATION.json'),full74_anchor=ref(old/'anchor74.npz'))
 p=dict(time=time.time(),method=m,inputs=inputs,helper_runtime=str(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'),sources={n:sha(out/n) for n in ['capture_anchor.py','review_anchor.py']},fixed_terminal_rows=2244,partial75_not_complete=True,new_physics=0,optimizer_updates=0)
 write(out/'ANCHOR_PLAN.json',p)
 write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),prior=ref(old/'PLAN.json'),adaptation='Tracker only cycle76, partial75 labels and plot filename; fixed2244+30, focus, arithmetic and two denominators unchanged. New anchor uses audited partial75 weights and full retained replay denominator.',sources={n:sha(out/n) for n in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']}))
print('Prepared both partial75 anchors and complete76 trackers')
