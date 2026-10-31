from pathlib import Path
import os,json,math,hashlib,time
os.sched_setaffinity(0,{52})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter_census_cycle95_20261031_v1';O=D/'prefix5000';O.mkdir()
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
full=read(B/'runs/parameter_census_cycle94_review_20261031_v1/REVIEW.json');previous=read(B/'runs/parameter_census_cycle94_review_20261031_v1/loss/REVIEW.json');assert full['passed'] and previous['passed']
methods={};fig,axes=plt.subplots(3,3,figsize=(18,11),constrained_layout=True)
for i,m in enumerate(['impedance','admittance','vmc']):
 source=R/m/'train/optimizer.jsonl'
 with source.open('rb') as f:raw=b''.join(next(f) for _ in range(5000))
 assert raw.endswith(b'\n');target=O/(m+'_optimizer_first5000.jsonl');target.write_bytes(raw)
 rows=[json.loads(l) for l in target.read_bytes().splitlines()];n=full['methods'][m]['steps'];assert len(rows)==5000 and [r['step'] for r in rows]==list(range(n+1,n+5001)) and all(r['update_index']==0 for r in rows)
 keys=sorted(set().union(*(r.keys() for r in rows))-{'step','update_index'});assert all(all(math.isfinite(r[k]) for k in keys) for r in rows)
 vals={k:np.array([r[k] for r in rows],np.float64) for k in keys};assert (vals['agent_train/original_sampled_q_loss']>=0).all();assert np.array_equal(vals['agent_train/q_loss'],vals['agent_train/conditional_terminal_q_loss'])
 np.savez_compressed(O/(m+'_values.npz'),steps=np.array([r['step'] for r in rows]),**vals)
 stats={}
 with np.load(O/(m+'_values.npz')) as saved:
  for k,v in vals.items():
   assert np.array_equal(saved[k],v);s=saved[k];stats[k]=dict(first1000=math.fsum(map(float,s[:1000]))/1000,last1000=math.fsum(map(float,s[-1000:]))/1000,mean=math.fsum(map(float,s))/5000,minimum=min(map(float,s)),maximum=max(map(float,s)))
   assert abs(stats[k]['mean']-float(v.mean()))<1e-10
 for col,key in enumerate(['agent_train/original_sampled_q_loss','agent_train/conditional_terminal_q_loss','agent_train/actor_loss']):
  a=vals[key];ax=axes[i,col];ax.plot(np.arange(1,5001),a,alpha=.45,lw=.35);ax.plot(np.arange(250,5001),np.convolve(a,np.ones(250)/250,'valid'),lw=1,label='250-update mean');ax.set_title(m+' '+key.split('/')[-1]);ax.set_xlabel('First 5000 actual cycle95 updates');ax.grid(alpha=.2);ax.legend()
 with source.open('rb') as f:assert b''.join(next(f) for _ in range(5000))==raw
 methods[m]=dict(rows=5000,parent_steps=n,first_step=n+1,last_step=n+5000,original_prefix_sha256=sha(target),saved_values_sha256=sha(O/(m+'_values.npz')),all_metrics_finite=True,stats=stats,complete94_last1000=previous['methods'][m]['stats'])
fig.suptitle('Cycle95 fixed early prefix; partial training, no convergence claim');fig.savefig(O/'prefix5000.png',dpi=150);plt.close(fig)
(O/'REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),methods=methods,plot_sha256=sha(O/'prefix5000.png'),plot_viewed=False,source_prefix_exact=True,independent_saved_scalar_arithmetic=True,physical_steps=0,optimizer_updates=0,convergence_claim=False,limits='All methods fixed first5000 actual updates, selected before reading loss values; no complete episode reward or full-cycle claim. Complete94 losses retained separately; 95 uses conditional-terminal estimator; original_sampled_q_loss is the original health metric. Partial prefix does not establish full-cycle reward stability or causal improvement.'),indent=2)+'\n')
print(json.dumps({m:v['stats']['agent_train/original_sampled_q_loss'] for m,v in methods.items()},indent=2))
