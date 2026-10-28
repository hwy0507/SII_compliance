from pathlib import Path
import json,os,time,hashlib
os.sched_setaffinity(0,{54})
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');out=Path(__file__).parent
fig,axes=plt.subplots(3,2,figsize=(12,10),constrained_layout=True);result={}
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for row,m in enumerate(['impedance','admittance','vmc']):
 root=B/f'runs/parameter_capacity_pool30_cycle65_20261026_v1/{m}/train';assert json.loads((root/'FINISHED.json').read_text())['status']=='stopped_at_complete_cycle'
 logs=[json.loads(l) for l in (root/'optimizer.jsonl').read_text().splitlines()];eps=[json.loads(l) for l in (root/'episodes.jsonl').read_text().splitlines()];assert len(eps)==30 and len({e['condition'] for e in eps})==30;assert len(logs)==sum(e['steps'] for e in eps) and 0<len(logs)<=41250;assert [r['step'] for r in logs]==list(range(logs[0]['step'],logs[-1]['step']+1))
 stats={}
 for col,k in enumerate(['agent_train/q_loss','agent_train/actor_loss']):
  v=np.array([r[k] for r in logs]);assert np.isfinite(v).all();stats[k]=dict(count=len(v),first1000=float(v[:1000].mean()),last1000=float(v[-1000:].mean()),mean=float(v.mean()),maximum=float(v.max()),minimum=float(v.min()),nonfinite=0)
  ax=axes[row,col];ax.plot(np.arange(len(v)),v,alpha=.2,lw=.3);ax.plot(np.arange(999,len(v)),np.convolve(v,np.ones(1000)/1000,mode='valid'));ax.set_title(m+' '+k);ax.grid(alpha=.2)
 means=[]
 for cycle in [49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65]:
  p=B/f'runs/parameter_capacity_pool30_cycle{cycle}_20261026_v1/{m}/train/episodes.jsonl';es=[json.loads(l) for l in p.read_text().splitlines()];assert len(es)==30;means.append(dict(cycle=cycle,reward_mean=float(np.mean([e['reward'] for e in es])),task=sum(e['task_success'] for e in es),strict=sum(e['strict_success'] for e in es)))
 result[m]=dict(loss=stats,reward_history=means,aborts=[e for e in eps if e['abort_reason']],full_horizon=sum(e['full_task_horizon_completed'] for e in eps),inputs={n:dict(path=str(root/n),sha256=sha(root/n)) for n in ['FINISHED.json','optimizer.jsonl','episodes.jsonl']})
fig.savefig(out/'loss.png',dpi=120);report=dict(time=time.time(),methods=result,new_physics=0,optimizer_updates=0,convergence_claim=False,plot_sha256=sha(out/'loss.png'),limitation='Complete65 optimizer and episode statistics; exact replay/checkpoint review handled separately. Reward49-65 is descriptive, not an outcome-selected replacement of the original53-55 preregistered window.')
(out/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({m:dict(critic=r['loss']['agent_train/q_loss'],reward=r['reward_history'][-1]) for m,r in result.items()},indent=2))
