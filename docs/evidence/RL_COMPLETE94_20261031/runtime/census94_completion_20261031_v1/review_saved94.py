"""Independent full94 original log -> saved arrays -> scalar loss arithmetic review."""
from pathlib import Path
import os,json,hashlib,math,time
os.sched_setaffinity(0,{52});D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle94_20261031_v1';V=B/'runs/parameter_census_cycle94_review_20261031_v1';L=V/'loss'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
import numpy as np
assert read(V/'FINISHED.json')['completed'];review=read(L/'REVIEW.json');full=read(V/'REVIEW.json');assert review['passed'] and full['passed'];results={}
for m in ['impedance','admittance','vmc']:
 p=R/m/'train/optimizer.jsonl';r=review['methods'][m];assert sha(p)==r['optimizer_log_sha256'];records=[json.loads(l) for l in p.read_text().splitlines()];values=L/(m+'_all_losses.npz');assert sha(values)==r['all_saved_losses_sha256'];n=full['methods'][m]['new_transitions'];assert len(records)==n==r['rows'] and all(x['update_index']==0 for x in records)
 with np.load(values) as z:
  assert len(z['steps'])==n;np.testing.assert_array_equal(z['steps'],[x['step'] for x in records]);keys=set().union(*(x.keys() for x in records))-{'step','update_index'};assert set(z.files)==keys|{'steps'}
  for k in keys:np.testing.assert_array_equal(z[k],[x[k] for x in records]);assert np.isfinite(z[k]).all()
  np.testing.assert_array_equal(z['agent_train/q_loss'],z['agent_train/conditional_terminal_q_loss']);stats={}
  for k in ['agent_train/original_sampled_q_loss','agent_train/conditional_terminal_q_loss','agent_train/actor_loss']:
   a=list(map(float,z[k]));s=dict(mean=math.fsum(a)/n,first1000_mean=math.fsum(a[:1000])/min(1000,n),last1000_mean=math.fsum(a[-1000:])/min(1000,n),minimum=min(a),maximum=max(a));assert s==r['stats'][k];stats[k]=s
  q=z['agent_train/original_sampled_q_loss'];top=np.argsort(q)[-20:][::-1];largest=[dict(step=int(z['steps'][i]),original_sampled_loss=float(q[i]),conditional_loss=float(z['agent_train/conditional_terminal_q_loss'][i]),actor_loss=float(z['agent_train/actor_loss'][i]),terminal_population=int(z['agent_train/terminal_population'][i]),sampled_terminal_rows=int(z['agent_train/sampled_terminal_rows'][i])) for i in top]
 results[m]=dict(rows=n,all_saved_arrays_exact_to_original_log=True,all_saved_scalar_stats_exact=True,stats=stats,largest20_original_sampled_losses=largest,source_sha256=sha(p),values_sha256=sha(values))
assert sha(L/'loss94.png')==review['plot_sha256']
result=dict(passed=True,time=time.time(),methods=results,plot_sha256=review['plot_sha256'],source_sha256=sha(__file__),actual_plot_inspection_pending=True,optimizer_updates=0,physics_steps=0,convergence_claim=False,scope='All complete94 update rows, all saved metrics exact to original JSONL; independent scalar means/extrema and all top20 original losses retained. No spike-cause or health-pass inference.')
with (D/'FULL_LOSS_SAVED_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({m:r['stats']['agent_train/original_sampled_q_loss'] for m,r in results.items()},indent=2))
