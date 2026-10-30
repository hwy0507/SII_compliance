"""Capture complete78 terminal anchor from reviewed saved Q; no network forward or training."""
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
assert ck['cycle']==78 and ck['boundary']=='complete_condition_cycle' and ck['controller']==p['method']
a=ck['replay']['arrays'];idx=np.flatnonzero(a['dones'][:,0]==1);assert len(idx)==2334
features=np.concatenate([a['observations'][idx],a['actions'][idx]],axis=1);rewards=a['rewards'][idx,0];masks=a['masks'][idx].T
with np.load(p['inputs']['prior_values']['path'],allow_pickle=False) as old:
 for k,v in [('indices',idx),('rewards',rewards),('masks',masks)]:np.testing.assert_array_equal(v,old[k])
 q=old['q_after'].copy();den=old['denominator'].copy()
np.testing.assert_array_equal(den,a['masks'].sum(axis=0,dtype=float)+127*masks.sum(axis=1,dtype=float))
assert features.shape==(2334,57) and q.shape==(5,2334) and np.isfinite(q).all()
assert ck['replay']['capacity']==4000000 and ck['learner']['terminal_loss_weight']==128
sse=math.fsum(float(masks[i,j])*(float(q[i,j])-float(rewards[j]))**2 for i in range(5) for j in range(2334))
contribution=math.fsum(128*float(masks[i,j])*(float(q[i,j])-float(rewards[j]))**2/float(den[i]) for i in range(5) for j in range(2334))
assert math.isclose(contribution,prior['all_terminal_contribution'],rel_tol=1e-12,abs_tol=1e-12)
assert not (OUT/'anchor78.npz').exists()
np.savez_compressed(OUT/'anchor78.npz',indices=idx,features=features,rewards=rewards,masks=masks,q_after=q,denominator=den)
for x in p['inputs'].values():assert sha(x['path'])==x['sha256']
r=dict(passed=True,time=time.time(),method=p['method'],terminal_rows=2334,features_shape=[2334,57],groups=dict(all2334=dict(masked_sse_after=sse)),all_terminal_contribution=contribution,anchor_sha256=sha(OUT/'anchor78.npz'),checkpoint=p['inputs']['checkpoint'],source_sha256=sha(Path(__file__)),new_network_forward=0,new_physics=0,optimizer_updates=0,replay_writes=0,limitation='Reuse complete78 independently audited Q and denominator for all2334 terminals; features read from exact complete78 checkpoint, including its30 new terminals. Historical partial75 remains interrupted.')
(OUT/'ANCHOR_REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
