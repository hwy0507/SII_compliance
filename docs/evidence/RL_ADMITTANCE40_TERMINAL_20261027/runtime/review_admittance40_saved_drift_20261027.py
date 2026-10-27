"""Describe all fixed1194 terminal-row changes from saved CPU predictions only."""
from pathlib import Path
import json,hashlib,time,os
import numpy as np
os.sched_setaffinity(0,{52})
r=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/admittance39_40_terminal_concentration_20261027_v1')
output=r/'SAVED_DRIFT_REVIEW.json';assert not output.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report=json.loads((r/'REVIEW.json').read_text());assert report['passed'];data=[]
for c,row in zip([39,40],report['cycles']):
 p=r/f'cycle{c}_terminal_values.npz';assert sha(p)==row['values_sha256']
 with np.load(p,allow_pickle=False) as a:data.append({k:a[k].copy() for k in a.files})
a,b=data;n=len(a['replay_indices']);assert n==1194
for key in ['replay_indices','rewards','features']:np.testing.assert_array_equal(a[key],b[key][:n])
np.testing.assert_array_equal(a['masks'],b['masks'][:,:n]);m=a['masks'];x=m*(a['q']-a['rewards'][None])**2;y=m*(b['q'][:,:n]-a['rewards'][None])**2
delta=y-x;percritic=[dict(critic=i,masked_sse_before=float(x[i].sum()),masked_sse_after=float(y[i].sum()),delta=float(delta[i].sum()),trained_terminal_cells=int(m[i].sum())) for i in range(5)]
rowdelta=delta.sum(axis=0);rows=dict(improved=int((rowdelta<0).sum()),worsened=int((rowdelta>0).sum()),unchanged=int((rowdelta==0).sum()))
assert sum(rows.values())==n
tracking=report['cycles'][1]['retained_terminal_tracking'];assert np.isclose(sum(v['delta'] for v in percritic),tracking['masked_sse_at40']-tracking['masked_sse_at39'],rtol=1e-13)
# Every fixed chronological quartile is reported; no selected subset.
quartiles=[]
for i,idx in enumerate(np.array_split(np.arange(n),4)):
 quartiles.append(dict(quartile=i+1,rows=len(idx),first_replay_index=int(a['replay_indices'][idx[0]]),last_replay_index=int(a['replay_indices'][idx[-1]]),sse_before=float(x[:,idx].sum()),sse_after=float(y[:,idx].sum()),improved=int((rowdelta[idx]<0).sum()),worsened=int((rowdelta[idx]>0).sum())))
out=dict(passed=True,time=time.time(),source_sha256=sha(Path(__file__)),input_report_sha256=sha(r/'REVIEW.json'),fixed_rows=n,per_critic=percritic,row_direction_counts=rows,chronological_quartiles=quartiles,new_physics=0,optimizer_updates=0,model_forward_calls=0,limitation='Descriptive saved-value drift for all retained terminal rows; not a causal decomposition of online loss or evidence for an LR/weight/feature change.')
output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps(out,indent=2))
