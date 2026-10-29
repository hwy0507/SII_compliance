from pathlib import Path
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
(p/'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
