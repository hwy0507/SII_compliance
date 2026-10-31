"""Bound all90 new100 terminals to original journals and inspect failure mechanisms."""
from pathlib import Path
import json,hashlib,math,time,os,sys
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census100_new_terminal_diagnosis_20261031_v1'
os.sched_setaffinity(0,{53})
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def lines(p):
 with p.open() as f:return [json.loads(l) for l in f]
def main():
 r=read(O/'reference100/REVIEW.json');assert r['passed'];plan=read(O/'REFERENCE_PLAN.json');methods={};sources=[]
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,2,figsize=(15,12),constrained_layout=True)
 for row,m in enumerate(plan['methods']):
  e=plan['methods'][m];vp=O/'reference100'/(m+'_values.npz');assert sha(vp)==r['methods'][m]['values']['sha256']
  with np.load(vp) as z:a={k:z[k].copy() for k in z.files}
  new=np.flatnonzero(a['cycles']==100);assert len(new)==30
  train=B/f'runs/parameter_census_cycle100_20261031_v1/{m}/train';ts=lines(train/'transitions.jsonl');terminal={t['step']-1:t for t in ts if t['done']};episodes={x['condition']:x for x in lines(train/'episodes.jsonl')};assert len(terminal)==len(episodes)==30
  err=(a['initial_prediction'].astype(float)-a['rewards'].astype(float)[:,None])**2;weighted=err*a['masks'];rows=[]
  for j in new:
   idx=int(a['indices'][j]);t=terminal[idx];ep=episodes[t['condition']];assert t['condition']==a['conditions'][j] and np.float32(t['reward'])==a['rewards'][j] and ep['total_steps']==t['step']
   rollpath=train/'cycle_00100'/t['condition']/'rollout.json';roll=read(rollpath);assert roll['task_success']==ep['task_success'] and roll['strict_success']==ep['strict_success'];sources.append(ref(rollpath))
   q=a['initial_prediction'][j];mask=a['masks'][j];rw=float(a['rewards'][j]);scalar=[(float(v)-rw)**2*float(w) for v,w in zip(q,mask)];np.testing.assert_allclose(scalar,weighted[j],rtol=1e-13,atol=1e-10)
   rows.append(dict(replay_index=idx,step=t['step'],condition=t['condition'],terminal_reward=rw,reward_terms=t['reward_terms'],episode_reward=ep['reward'],task=ep['task_success'],strict=ep['strict_success'],stage=roll['final_task_stage'],q100=q.tolist(),original_mask=mask.tolist(),masked_sse=math.fsum(scalar),all5_sse=math.fsum(err[j]),terminal_observation_violation_bit=float(a['observations'][j,51]),rollout=ref(rollpath)))
  pairs={}
  for cycle in [99,100]:
   oldtrain=B/f'runs/parameter_census_cycle{cycle}_20261031_v1/{m}/train';rollpath=oldtrain/f'cycle_{cycle:05d}/active_short_train_0600/rollout.json';roll=read(rollpath);ep=next(x for x in lines(oldtrain/'episodes.jsonl') if x['condition']=='active_short_train_0600');trans=[t for t in lines(oldtrain/'transitions.jsonl') if t['condition']=='active_short_train_0600'];assert 0<len(trans)<=1375 and len(trans)==ep['steps'] and trans[-1]['done'] and trans[-1]['step']==ep['total_steps']
   np.testing.assert_allclose(math.fsum(t['reward'] for t in trans),ep['reward'],rtol=1e-12,atol=1e-10)
   terms={k:math.fsum(t['reward_terms'][k] for t in trans) for k in ['progress','occupancy','time','comfort_torque','contact_force','torque_slew','penetration','peak_torque','terminal','failure_tail','completion_efficiency']}
   peak=roll['stats']['max_external_penetration_m'];assert roll['physical_valid']==(peak<=.0002 and roll['initial_geometry_valid']);assert roll['strict_success']==(roll['task_success'] and roll['physical_valid'])
   pairs[str(cycle)]=dict(episode=ep,rollout=ref(rollpath),task_events=roll['task_events'],external_peak_m=peak,external_gate_m=.0002,external_margin_m=.0002-peak,physical_valid=roll['physical_valid'],object_final_position=roll['object_final_position'],terminal_transition=trans[-1],component_sums=terms);sources.extend([ref(oldtrain/'episodes.jsonl'),ref(oldtrain/'transitions.jsonl'),ref(rollpath)])
  total=math.fsum(weighted[new].reshape(-1));short=next(x for x in rows if x['condition']=='active_short_train_0600');largest=sorted(rows,key=lambda x:x['masked_sse'],reverse=True)
  # Log ordering supplies temporal association only; sampled indices were not retained.
  opt=lines(train/'optimizer.jsonl');worst=max(opt,key=lambda x:x['agent_train/original_sampled_q_loss']);spike_step=worst['step']
  result=dict(all30_new_terminal_rows=rows,total_new100_masked_sse=total,total_old_masked_sse=math.fsum(weighted[a['cycles']<=99].reshape(-1)),total_all8983_method_masked_sse=math.fsum(weighted.reshape(-1)),new100_masked_sse_by_critic=[math.fsum(weighted[new,j]) for j in range(5)],largest5=[{k:v for k,v in x.items() if k in ('condition','step','terminal_reward','masked_sse','q100','original_mask')} for x in largest[:5]],short0600=short,short0600_pair=pairs,largest_original_loss=worst,spike_step_minus_short0600_terminal_step=spike_step-short['step'],sampled_indices_available=False,causal_attribution=False)
  methods[m]=result;put(O/(m+'_DIAGNOSIS.json'),result)
  axes[row,0].bar(range(30),[x['masked_sse'] for x in rows]);axes[row,0].set_title(m+' new100 terminals: original masked SSE');axes[row,0].set_xlabel('Terminal order (all30)');axes[row,0].set_yscale('symlog',linthresh=1)
  axes[row,1].bar(range(5),result['new100_masked_sse_by_critic']);axes[row,1].set_title(m+' new100 all5 critics: original masked SSE');axes[row,1].set_xlabel('Critic index')
  for ax in axes[row]:ax.grid(alpha=.2)
 fig.suptitle('Complete100 predictions on all90 new100 training terminals / zero updates\nOriginal masks and failures retained; not held-out generalization or sampled-batch causality')
 plot=O/'new100_terminal_residuals.png';fig.savefig(plot,dpi=140);plt.close(fig)
 put(O/'DIAGNOSIS.json',dict(passed=True,time=time.time(),methods=methods,inputs=sources,reference_review=ref(O/'reference100/REVIEW.json'),plot=ref(plot),physics_steps=0,optimizer_updates=0,convergence_claim=False,causal_attribution=False))
 print(json.dumps({m:{k:v[k] for k in ['total_new100_masked_sse','largest5','spike_step_minus_short0600_terminal_step']} for m,v in methods.items()},indent=2))
if __name__=='__main__':main()
