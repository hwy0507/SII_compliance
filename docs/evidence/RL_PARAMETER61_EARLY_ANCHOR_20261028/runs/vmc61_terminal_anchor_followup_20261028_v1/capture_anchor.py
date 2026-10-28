"""Freeze complete60 terminal inputs for prospective complete61 comparison."""
from pathlib import Path
import hashlib,json,os,time
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).resolve().parent
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
cp=B/'runs/parameter_capacity_pool30_cycle60_archive_20261026_v1/vmc/cycle_00060.pt'
old=B/'runs/vmc60_terminal_anchor_followup_20261028_v1'
inputs={str(p):sha(p) for p in [cp,old/'values.npz',old/'REVIEW.json',old/'SAVED_VALUES_REVIEW.json']}
assert inputs[str(cp)]=='2c3ab84edc6bb4f9f49a8f7fbbe20a15453edeb8a2f477bdf72273b0ab60a1f6'
assert read(old/'REVIEW.json')['values_sha256']==inputs[str(old/'values.npz')]
assert read(old/'SAVED_VALUES_REVIEW.json')['passed']
ck=torch.load(cp,map_location='cpu',weights_only=False)
assert ck['cycle']==60 and ck['boundary']=='complete_condition_cycle' and ck['controller']=='vmc'
a=ck['replay']['arrays'];idx=np.flatnonzero(a['dones'][:,0]==1);assert len(idx)==1824
with np.load(old/'values.npz',allow_pickle=False) as saved:
    np.testing.assert_array_equal(idx,saved['indices'])
    np.testing.assert_array_equal(a['rewards'][idx,0],saved['rewards'])
    np.testing.assert_array_equal(a['masks'][idx].T,saved['masks'])
    q=saved['q_after'].copy();den=saved['denominator'].copy()
features=np.concatenate([a['observations'][idx],a['actions'][idx]],axis=1)
rewards=a['rewards'][idx,0];masks=a['masks'][idx].T
assert features.shape==(1824,57) and q.shape==(5,1824)
sse=float((masks*(q.astype(float)-rewards.astype(float)[None])**2).sum())
assert not (OUT/'anchor60.npz').exists()
np.savez_compressed(OUT/'anchor60.npz',indices=idx,features=features,rewards=rewards,masks=masks,q_after=q,denominator=den)
for p,h in inputs.items():assert sha(Path(p))==h
report=dict(passed=True,time=time.time(),inputs=inputs,source_sha256=sha(Path(__file__)),
    anchor_sha256=sha(OUT/'anchor60.npz'),terminal_rows=1824,features_shape=[1824,57],
    groups=dict(all1824=dict(masked_sse_after=sse)),exact_saved60_terminal_indices_rewards_masks=True,
    q_from_verified60_cpu_forward=True,new_network_forward=0,optimizer_updates=0,new_physics=0,
    limitation='Exact full60 archived checkpoint inputs plus previously independently audited60 Q values; no live checkpoint selection, no training mutation.')
(OUT/'ANCHOR_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
