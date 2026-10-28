from pathlib import Path
import json,hashlib,math,time,os
os.sched_setaffinity(0,{53})
import numpy as np
p=Path(__file__).parent;prior=p.parent/'vmc60_terminal_anchor_followup_20261028_v1';r=json.loads((p/'ANCHOR_REVIEW.json').read_text())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
assert sha(p/'anchor60.npz')==r['anchor_sha256']
with np.load(p/'anchor60.npz',allow_pickle=False) as a,np.load(prior/'values.npz',allow_pickle=False) as v:
 assert a['features'].shape==(1824,57)
 for k in ['indices','rewards','masks','q_after','denominator']:np.testing.assert_array_equal(a[k],v[k])
 sse=math.fsum(float(a['masks'][i,j])*(float(a['q_after'][i,j])-float(a['rewards'][j]))**2 for i in range(5) for j in range(1824));assert math.isclose(sse,r['groups']['all1824']['masked_sse_after'],rel_tol=1e-12,abs_tol=1e-12)
(p/'ANCHOR_SAVED_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),all1824_saved_arrays_exact=True,independent_scalar_sse=sse,anchor_sha256=sha(p/'anchor60.npz'),source_sha256=sha(Path(__file__)),new_network_forward=0,new_physics=0,optimizer_updates=0),indent=2)+'\n')
print('All1824 exact arrays/scalar SSE passed:',sse)
