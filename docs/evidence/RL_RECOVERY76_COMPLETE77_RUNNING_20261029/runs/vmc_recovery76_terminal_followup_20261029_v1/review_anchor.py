from pathlib import Path
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
(p/'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
