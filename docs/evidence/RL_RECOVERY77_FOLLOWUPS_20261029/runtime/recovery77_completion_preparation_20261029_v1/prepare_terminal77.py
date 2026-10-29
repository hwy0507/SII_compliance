from pathlib import Path
import json,time,hashlib,difflib,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
capture='''"""Capture complete76 terminal anchor from reviewed saved Q; no network forward or training."""
from pathlib import Path
import hashlib,json,time,os,math
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
prior=read(p['inputs']['prior_review']['path']);binding=read(p['inputs']['prior_binding']['path']);assert prior['passed'] and read(p['inputs']['prior_saved_review']['path'])['passed']
assert binding['checkpoint']==p['inputs']['checkpoint'] and prior['values_sha256']==p['inputs']['prior_values']['sha256']
assert read(p['inputs']['complete_review']['path'])['passed']
ck=torch.load(p['inputs']['checkpoint']['path'],map_location='cpu',weights_only=False)
assert ck['cycle']==76 and ck['boundary']=='complete_condition_cycle' and ck['controller']==p['method']
a=ck['replay']['arrays'];idx=np.flatnonzero(a['dones'][:,0]==1);assert len(idx)==2274
features=np.concatenate([a['observations'][idx],a['actions'][idx]],axis=1);rewards=a['rewards'][idx,0];masks=a['masks'][idx].T
with np.load(p['inputs']['prior_values']['path'],allow_pickle=False) as old:
 for k,v in [('indices',idx),('rewards',rewards),('masks',masks)]:np.testing.assert_array_equal(v,old[k])
 q=old['q_after'].copy();den=old['denominator'].copy()
np.testing.assert_array_equal(den,a['masks'].sum(axis=0,dtype=float)+127*masks.sum(axis=1,dtype=float))
assert features.shape==(2274,57) and q.shape==(5,2274) and np.isfinite(q).all()
assert ck['replay']['capacity']==4000000 and ck['learner']['terminal_loss_weight']==128
sse=math.fsum(float(masks[i,j])*(float(q[i,j])-float(rewards[j]))**2 for i in range(5) for j in range(2274))
contribution=math.fsum(128*float(masks[i,j])*(float(q[i,j])-float(rewards[j]))**2/float(den[i]) for i in range(5) for j in range(2274))
assert math.isclose(contribution,prior['all_terminal_contribution'],rel_tol=1e-12,abs_tol=1e-12)
assert not (OUT/'anchor76.npz').exists()
np.savez_compressed(OUT/'anchor76.npz',indices=idx,features=features,rewards=rewards,masks=masks,q_after=q,denominator=den)
for x in p['inputs'].values():assert sha(x['path'])==x['sha256']
r=dict(passed=True,time=time.time(),method=p['method'],terminal_rows=2274,features_shape=[2274,57],groups=dict(all2274=dict(masked_sse_after=sse)),all_terminal_contribution=contribution,anchor_sha256=sha(OUT/'anchor76.npz'),checkpoint=p['inputs']['checkpoint'],source_sha256=sha(Path(__file__)),new_network_forward=0,new_physics=0,optimizer_updates=0,replay_writes=0,limitation='Reuse complete76 independently audited Q and denominator for all2274 terminals; features read from exact complete76 checkpoint, including its30 new terminals. Historical partial75 remains interrupted.')
(OUT/'ANCHOR_REVIEW.json').write_text(json.dumps(r,indent=2)+'\\n');print(json.dumps(r))
'''
review='''from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{53})
import numpy as np
p=Path(__file__).parent;plan=json.loads((p/'ANCHOR_PLAN.json').read_text());r=json.loads((p/'ANCHOR_REVIEW.json').read_text())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(p/'anchor76.npz')==r['anchor_sha256']
with np.load(p/'anchor76.npz',allow_pickle=False) as a,np.load(plan['inputs']['prior_values']['path'],allow_pickle=False) as old:
 assert a['features'].shape==(2274,57) and a['q_after'].shape==(5,2274)
 for k in ['indices','rewards','masks','q_after','denominator']:np.testing.assert_array_equal(a[k],old[k])
 assert np.isfinite(a['q_after']).all() and np.isfinite(a['features']).all()
 sse=math.fsum(float(a['masks'][i,j])*(float(a['q_after'][i,j])-float(a['rewards'][j]))**2 for i in range(5) for j in range(2274));assert math.isclose(sse,r['groups']['all2274']['masked_sse_after'],rel_tol=1e-12,abs_tol=1e-12)
 out=dict(passed=True,time=time.time(),all2274_saved_values_exact=True,independent_scalar_sse=sse,complete76_denominator=a['denominator'].tolist(),anchor_sha256=sha(p/'anchor76.npz'),source_sha256=sha(Path(__file__)),new_physics=0,optimizer_updates=0)
(p/'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\\n');print(json.dumps(out))
'''
for m in ['vmc','admittance']:
 old=B/f'runs/{m}_recovery76_terminal_followup_20261029_v1';out=B/f'runs/{m}_recovery77_terminal_followup_20261029_v1';out.mkdir(exist_ok=False)
 for name in ['track.py','review_values.py','wait.py']:
  s=(old/name).read_text();new=s.replace('2274','__TOTAL__').replace('2244','2274').replace('__TOTAL__','2304').replace('complete76','complete77').replace('Complete76','Complete77').replace("ck['cycle']==76","ck['cycle']==77").replace('health76','health77').replace('follow76.png','follow77.png').replace('partial75','complete76').replace('Partial75','Complete76')
  # The original wait/forward/arithmetic remains unchanged except explicit cycle/count/labels.
  ast.parse(new);(out/name).write_text(new);(out/(name+'.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),new.splitlines(True),fromfile=str(old/name),tofile=str(out/name))))
 for name,s in [('capture_anchor.py',capture),('review_anchor.py',review)]:ast.parse(s);(out/name).write_text(s)
 inputs=dict(checkpoint=ref(B/f'runs/parameter_partial75_recovery_cycle76_archive_20261029_v1/{m}/cycle_00076.pt'),prior_review=ref(old/'REVIEW.json'),prior_saved_review=ref(old/'SAVED_VALUES_REVIEW.json'),prior_values=ref(old/'values.npz'),prior_binding=ref(old/'FINAL_BINDING.json'),complete_review=ref(B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1/REVIEW.json'))
 write(out/'ANCHOR_PLAN.json',dict(time=time.time(),method=m,inputs=inputs,sources={n:sha(out/n) for n in ['capture_anchor.py','review_anchor.py']},fixed_terminal_rows=2274,complete76=True,new_physics=0,optimizer_updates=0))
 write(out/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),prior=ref(old/'PLAN.json'),adaptation='Complete76 all2274 fixed terminals plus77 new30 expected2304; full population, historical focus and both denominators unchanged. Reuse audited complete76 Q; features exact checkpoint.',sources={n:sha(out/n) for n in ['capture_anchor.py','review_anchor.py','track.py','review_values.py','wait.py']}))
print('Prepared complete76 anchors and complete77 trackers; not launched yet')
