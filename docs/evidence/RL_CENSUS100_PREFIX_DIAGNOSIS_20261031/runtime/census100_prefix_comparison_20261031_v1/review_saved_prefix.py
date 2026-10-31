from pathlib import Path
import os,json,time,hashlib,math
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];P=D/'prefix5000';R=B/'runs/parameter_census_cycle100_20261031_v1';read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
os.sched_setaffinity(0,{52});plan=read(D/'PREFIX_PLAN.json');r=read(P/'REVIEW.json');assert r['passed'] and sha(D/'prefix100.py')==plan['source_sha256'];assert sha(P/'prefix5000.png')==r['plot_sha256']==read(D/'PLOT_INSPECTION.json')['sha256'];results={}
for m,e in r['methods'].items():
 cp=P/(m+'_optimizer_first5000.jsonl');npz=P/(m+'_values.npz');raw=cp.read_bytes();assert sha(cp)==e['original_prefix_sha256'] and sha(npz)==e['saved_values_sha256']
 with (R/m/'train/optimizer.jsonl').open('rb') as f:assert b''.join(next(f) for _ in range(5000))==raw
 rows=[json.loads(x) for x in raw.splitlines()];reg=read(R/m/'REGISTRATION.json');start=reg['post_interruption_continuation']['parent_steps'];assert [x['step'] for x in rows]==list(range(start+1,start+5001)) and all(x['update_index']==0 for x in rows)
 keys=set(rows[0])-{'step','update_index'};assert all(set(x)-{'step','update_index'}==keys for x in rows)
 with np.load(npz) as z:
  assert set(z.files)==keys|{'steps'};np.testing.assert_array_equal(z['steps'],[x['step'] for x in rows]);assert keys==set(e['stats'])
  for k in keys:
   v=np.array([x[k] for x in rows],np.float64);np.testing.assert_array_equal(z[k],v);assert np.isfinite(v).all();actual=dict(first1000=float(np.mean(v[:1000])),last1000=float(np.mean(v[-1000:])),mean=float(np.mean(v)),minimum=float(np.min(v)),maximum=float(np.max(v)))
   for label,value in actual.items():assert math.isclose(value,e['stats'][k][label],rel_tol=1e-12,abs_tol=1e-12)
  q=z['agent_train/original_sampled_q_loss'];assert (q>=0).all();np.testing.assert_array_equal(z['agent_train/q_loss'],z['agent_train/conditional_terminal_q_loss']);order=np.argsort(q)[-20:][::-1]
  results[m]=dict(rows=5000,metrics=len(keys),all_raw_and_saved_values_exact=True,all_scalar_stats_independently_recomputed=True,original_loss=e['stats']['agent_train/original_sampled_q_loss'],actor_loss=e['stats']['agent_train/actor_loss'],original_top20=[dict(step=int(z['steps'][i]),loss=float(q[i])) for i in order],largest_original_vs_conditional_difference=float(np.max(np.abs(q-z['agent_train/conditional_terminal_q_loss']))),raw_sha256=sha(cp),saved_sha256=sha(npz))
with (D/'PREFIX_SAVED_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),methods=results,source_sha256=sha(__file__),scope='Independent readback of every saved raw/NPZ value and all scalar statistics over fixed5000 per method. Does not establish full100 reward stability or loss health.',physics_steps=0,optimizer_updates=0),f,indent=2);f.write('\n')
print({m:(v['metrics'],v['largest_original_vs_conditional_difference']) for m,v in results.items()})
