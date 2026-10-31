from pathlib import Path
import hashlib,json,math,time
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
plan=read(O/'PLAN.json');assert sha(__file__)==plan['source_hashes']['review_saved.py'];report=read(O/'REVIEW.json');assert report['passed'];results={}
for m,e in plan['methods'].items():
 r=report['methods'][m];p=O/(m+'_values.npz');assert sha(p)==r['values_sha256']
 with np.load(p) as z:data={k:z[k].copy() for k in z.files}
 with np.load(e['baseline_values']) as z:
  for k in ['indices','observations','actions','rewards','masks']:np.testing.assert_array_equal(data[k],z[k])
  np.testing.assert_array_equal(data['complete92'],z['predictions'])
 mask=data['masks'].astype(float);reward=data['rewards'].astype(float);statistics={}
 for label in ['complete92','complete93']:
  error=(data[label].astype(float)-reward[:,None])**2;weighted=error*mask
  s=dict(masked_sse=[math.fsum(weighted[:,i]) for i in range(5)],all_row_sse=[math.fsum(error[:,i]) for i in range(5)],mask_counts=mask.sum(0).tolist(),total_masked_sse=math.fsum(weighted.reshape(-1)))
  for k,v in s.items():np.testing.assert_allclose(v,r['stats'][label][k],rtol=1e-12,atol=1e-8)
  statistics[label]=s
 for abort in r['known_aborts']:
  loc=np.flatnonzero(data['indices']==abort['replay_index']);assert len(loc)==1;j=int(loc[0]);np.testing.assert_array_equal(mask[j],abort['mask']);assert reward[j]==abort['reward']
  for cycle in ['92','93']:
   np.testing.assert_array_equal(data['complete'+cycle][j],abort['q'+cycle]);np.testing.assert_allclose(math.fsum(((data['complete'+cycle][j].astype(float)-reward[j])**2)*mask[j]),abort['masked_sse'+cycle],rtol=1e-12,atol=1e-8)
 results[m]=dict(terminal_rows=len(reward),statistics=statistics,all_saved_fields_and_scalar_sse_checked=True,known_abort_rows_checked=len(r['known_aborts']),values_sha256=sha(p))
out=dict(passed=True,time=time.time(),methods=results,optimizer_updates=0,new_physics=0,convergence_claim=False,actual_plot_inspection_pending=True)
with (O/'SAVED_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print('All fixed92 saved inputs,92/93 predictions,masked/all-row SSE and known abort metrics checked.')
