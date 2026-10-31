"""Full-cycle loss evidence, with independent saved scalar recomputation."""
from pathlib import Path
import json,math,hashlib,os,time
os.sched_setaffinity(0,{52})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'runs/parameter_census_cycle97_20261031_v1';O=B/'runs/parameter_census_cycle97_review_20261031_v1/loss';O.mkdir()
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
fig,axes=plt.subplots(3,3,figsize=(18,11));methods={}
for i,m in enumerate(['impedance','admittance','vmc']):
 p=R/m/'train/optimizer.jsonl';rows=[json.loads(l) for l in p.read_text().splitlines()];reg=read(R/m/'REGISTRATION.json');n=read(Path(reg['post_interruption_continuation']['cycle_review']['path']))['methods'][m]['steps'];count=len(rows);assert 0<count<=41250 and count==read(O.parent/(m+'_REVIEW.json'))['new_transitions'] and [r['step'] for r in rows]==list(range(n+1,n+count+1)) and all(r['update_index']==0 for r in rows)
 keys=sorted(set().union(*(r.keys() for r in rows))-{'step','update_index'});assert all(all(np.isfinite(r[k]) for k in keys) for r in rows)
 values={k:np.array([r[k] for r in rows],dtype=np.float64) for k in keys};q=values['agent_train/original_sampled_q_loss'];assert np.array_equal(values['agent_train/q_loss'],values['agent_train/conditional_terminal_q_loss']);actor=values['agent_train/actor_loss'];assert np.all(q>=0)
 np.savez_compressed(O/(m+'_all_losses.npz'),steps=np.array([r['step'] for r in rows]),**values)
 with np.load(O/(m+'_all_losses.npz')) as saved:
  for k in keys:assert np.array_equal(saved[k],values[k])
  stats={}
  for key in ['agent_train/original_sampled_q_loss','agent_train/conditional_terminal_q_loss','agent_train/actor_loss']:
   a=saved[key];stats[key]=dict(first1000_mean=math.fsum(map(float,a[:1000]))/min(1000,len(a)),last1000_mean=math.fsum(map(float,a[-1000:]))/min(1000,len(a)),mean=math.fsum(map(float,a))/len(a),maximum=max(map(float,a)),minimum=min(map(float,a)))
   assert abs(stats[key]['mean']-float(a.mean()))<1e-10
 for col,key in enumerate(['agent_train/original_sampled_q_loss','agent_train/conditional_terminal_q_loss','agent_train/actor_loss']):
  a=values[key];ax=axes[i,col];ax.plot(np.arange(len(a)),a,lw=.3,alpha=.5);ax.plot(np.arange(min(500,len(a))-1,len(a)),np.convolve(a,np.ones(min(500,len(a)))/min(500,len(a)),'valid'),lw=1);ax.set_title(m+' '+key.split('/')[-1]);ax.set_xlabel('New census97 updates');ax.grid(alpha=.2)
 methods[m]=dict(rows=len(rows),endpoint_window_count=min(1000,len(rows)),optimizer_log_sha256=sha(p),all_saved_losses_sha256=sha(O/(m+'_all_losses.npz')),all_finite=True,stats=stats)
fig.tight_layout();fig.savefig(O/'loss97.png',dpi=150);plt.close(fig)
(O/'REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),methods=methods,independent_saved_scalar_means_checked=True,plot_sha256=sha(O/'loss97.png'),plot_viewed=False,convergence_claim=False,health_metric='agent_train/original_sampled_q_loss',update_metric='agent_train/conditional_terminal_q_loss',scope='All actual contiguous updates per method (max41250); abort lengths retained; prior revision failures retained; no cross-revision stability claim'),indent=2)+'\n')
