from pathlib import Path
import json,hashlib,os,time,math
os.sched_setaffinity(0,{54})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent

def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def readrows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def stats(v):
 a=np.asarray(v,dtype=float);return dict(n=len(a),nonfinite=int((~np.isfinite(a)).sum()),first1000=float(a[:1000].mean()),last1000=float(a[-1000:].mean()),mean=float(a.mean()),maximum=float(a.max()),minimum=float(a.min()))
report=dict(time=time.time(),prefix_rows=5000,retrospective_descriptive=True,new_physics=0,optimizer_updates=0,convergence_claim=False,methods={})
fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True)
for i,m in enumerate(['direct','impedance','admittance','vmc']):
 root=B/'runs/serl_take_cycle33_20261027_v1' if m=='direct' else B/'runs/parameter_capacity_pool30_cycle53_20261026_v1'
 run=root/'direct' if m=='direct' else root/m/'train';cp=out/(m+'_first5000.jsonl');lines=[]
 with (run/'optimizer.jsonl').open() as f:
  for line in f:
   if line.endswith('\n'):lines.append(line)
   if len(lines)==5000:break
 assert len(lines)==5000
 with cp.open('x') as f:f.writelines(lines)
 rows=readrows(cp);assert [r['step'] for r in rows]==list(range(rows[0]['step'],rows[0]['step']+5000))
 ck='serl/critic/critic_loss' if m=='direct' else 'agent_train/q_loss';ak='serl/actor/actor_loss' if m=='direct' else 'agent_train/actor_loss'
 numeric=[v for r in rows for v in r.values() if isinstance(v,(int,float))];assert all(math.isfinite(v) for v in numeric)
 v=np.array([r[ck] for r in rows]);a=np.array([r[ak] for r in rows]);report['methods'][m]=dict(first_step=rows[0]['step'],last_step=rows[-1]['step'],source=str(run/'optimizer.jsonl'),prefix_sha256=sha(cp),critic=stats(v),actor=stats(a),all_numeric_metrics_finite=True)
 ax=axes.flat[i];ax.plot(np.arange(5000),v,alpha=.25,lw=.5);ax.plot(np.arange(1000,5001),np.convolve(v,np.ones(1000)/1000,mode='valid'));ax.set_title(m+' first 5000 critic loss');ax.set_xlabel('within-stage update');ax.grid(alpha=.2)
old=B/'runs/parameter_capacity_pool30_cycle52_20261026_v1/admittance/train';rows=readrows(old/'optimizer.jsonl');eps=readrows(old/'episodes.jsonl');new=readrows(out/'admittance_first5000.jsonl')
steps=np.array([r['step'] for r in rows]);v=np.array([r['agent_train/q_loss'] for r in rows]);assert len(rows)==41250
report['admittance52_all_terminal_neighborhoods']=[]
for e in eps:
 index=int(np.searchsorted(steps,e['total_steps']));assert steps[index]==e['total_steps']
 before=v[max(0,index-1000):index];after=v[index:min(len(v),index+1000)]
 report['admittance52_all_terminal_neighborhoods'].append(dict(condition=e['condition'],step=e['total_steps'],task=e['task_success'],strict=e['strict_success'],reward=e['reward'],before_count=len(before),after_count=len(after),before_loss_mean=float(before.mean()) if len(before) else None,after_loss_mean=float(after.mean()) if len(after) else None))
allsteps=np.r_[steps,[r['step'] for r in new]];allv=np.r_[v,[r['agent_train/q_loss'] for r in new]]
ax=axes[2,0];ax.plot(allsteps,allv,alpha=.2,lw=.4);ax.plot(allsteps[999:],np.convolve(allv,np.ones(1000)/1000,mode='valid'));ax.axvline(steps[-1],color='red',ls='--',label='52/53 boundary');ax.set_title('Admittance full52 and fixed first5000 of53');ax.legend();ax.grid(alpha=.2)
ax=axes[2,1];ax.plot(allsteps[999:],np.convolve(allv,np.ones(1000)/1000,mode='valid'));ax.set_xlim(steps[-1]-5000,allsteps[-1]);ax.axvline(steps[-1],color='red',ls='--')
for e in eps:
 if e['total_steps']>=steps[-1]-5000:ax.axvline(e['total_steps'],alpha=.15,color='green' if e['strict_success'] else 'black')
ax.set_title('All late terminals marked; overlapping windows, no causal claim');ax.grid(alpha=.2)
peak=int(np.argmax(v));report['admittance52_peak']=dict(step=int(steps[peak]),loss=float(v[peak]))
report['inputs']={str(old/n):sha(old/n) for n in ['optimizer.jsonl','episodes.jsonl']};report['limitation']='Early5000 is a retrospective fixed prefix, not a preregistered convergence window. All30 terminal neighborhoods are retained; neighborhoods overlap and changing policy/replay sampling confound causality. No sampled replay-index trace is available, so temporal proximity does not prove which terminal caused a loss spike. Full-cycle reward53 still incomplete.'
fig.savefig(out/'loss.png',dpi=120);report['plot_sha256']=sha(out/'loss.png');(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({m:r['critic'] for m,r in report['methods'].items()},indent=2));print(report['admittance52_peak'])
