"""All90 frozen55->82 paired summaries and plots from verified saved evidence."""
from pathlib import Path
import json,time,hashlib,math,os
D=Path(__file__).parent;B=D.parents[1];O=B/'runs/parameter82_frozen_full30_20261030_v1';C=O/'comparison55_82';A=B/'runs/parameter82_frozen_full_saved_audit_20261030_v1';P=B/'runs/parameter55_frozen_full30_20261028_v1'
os.sched_setaffinity(0,{12})
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def main():
 assert read(D/'WATCH_FINISHED.json')['all82_ready']
 full=read(O/'REVIEW.json');pair=read(C/'REVIEW.json');raw=read(A/'REVIEW.json');plan=read(O/'PLAN.json')
 for p in [O/'REVIEW.json',C/'REVIEW.json',C/'SAVED_REVIEW.json',A/'FINISHED.json',A/'REVIEW.json',A/'SAVED_REVIEW.json']:assert read(p)['passed']
 assert full['total_episodes']==raw['total_cases']==90 and raw['total_substeps']==99000000
 assert pair['all90_pairs_retained']
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,2,figsize=(15,11),constrained_layout=True)
 output={}
 for index,m in enumerate(['impedance','admittance','vmc']):
  rows=pair['methods'][m]['rows'];rawrows=raw['methods'][m];fr=full['methods'][m]
  assert len(rows)==len(rawrows)==len(fr['episodes'])==30
  assert [r['condition'] for r in rows]==[r['condition'] for r in rawrows]==plan['case_ids']
  for r,a,f in zip(rows,rawrows,fr['episodes']):
   assert r['after']==f and r['condition']==a['condition']
   for key,keyraw in [('task','task'),('strict','strict'),('reward','reward'),('actions','actions'),('substeps','physical_samples'),('penetration_mm','external_penetration_mm'),('machine_safety_violation','machine_violation')]:assert r['after'][key]==a[keyraw],(m,key)
   assert math.isclose(r['after']['human_contact_s'],a['human_contact_s'],rel_tol=0,abs_tol=1e-8)
   assert r['before']['reward']==a['prior55_reward'] and r['before']['task']==a['prior55_task'] and r['before']['strict']==a['prior55_strict']
   assert r['after']['actions']==1375 and r['after']['substeps']==1100000 and r['after']['full_horizon'] and not r['after']['abort_reason']
  fin=read(O/m/'FINISHED.json');assert fin['full_learner_state_unchanged'] and fin['full_replay_state_unchanged'] and fin['new_optimizer_updates']==0
  assert fin['initial_learner_digest']==fin['final_learner_digest']==fr['initial_and_final_learner_digest']
  endpoints={}
  for stage,root in [('before',P),('after',O)]:
   rewards=[r[stage]['reward'] for r in rows];contacts=math.fsum(r[stage]['human_contact_s'] for r in rows)
   below=math.fsum(read(root/m/f'{r["condition"]}_REVIEW.json')['physical']['row']['human_below_threshold_s'] for r in rows)
   assert 0<=below<=contacts+1e-8
   endpoints[stage]=dict(reward_mean=math.fsum(rewards)/30,reward_range=[min(rewards),max(rewards)],task=sum(r[stage]['task'] for r in rows),strict=sum(r[stage]['strict'] for r in rows),machine_violation_count=sum(r[stage]['machine_safety_violation'] for r in rows),full_horizon_count=sum(r[stage]['full_horizon'] for r in rows),contact_episodes=sum(r[stage]['human_contact_s']>0 for r in rows),human_contact_seconds=contacts,human_compliant_seconds=below,contact_weighted_compliance_ratio=below/contacts if contacts else None,maximum_external_penetration_mm=max(r[stage]['penetration_mm'] for r in rows))
  contributions=[dict(condition=r['condition'],reward55=r['before']['reward'],reward82=r['after']['reward'],reward_delta=r['reward_delta'],contribution_to_mean=r['reward_delta']/30,task55=r['before']['task'],task82=r['after']['task'],strict55=r['before']['strict'],strict82=r['after']['strict'],penetration55_mm=r['before']['penetration_mm'],penetration82_mm=r['after']['penetration_mm'],task_change=r['task_change'],strict_change=r['strict_change'],stage82=a['stage']) for r,a in zip(rows,rawrows)]
  mean_delta=math.fsum(x['contribution_to_mean'] for x in contributions)
  assert math.isclose(mean_delta,endpoints['after']['reward_mean']-endpoints['before']['reward_mean'],abs_tol=1e-12)
  assert math.isclose(mean_delta,pair['methods'][m]['mean_reward_delta'],abs_tol=1e-12)
  changed=[r for r in contributions if r['task_change'] or r['strict_change']];unchanged=[r for r in contributions if not (r['task_change'] or r['strict_change'])]
  pieces=dict(changed_label_conditions=len(changed),changed_label_mean_contribution=math.fsum(r['contribution_to_mean'] for r in changed),unchanged_label_mean_contribution=math.fsum(r['contribution_to_mean'] for r in unchanged))
  assert math.isclose(pieces['changed_label_mean_contribution']+pieces['unchanged_label_mean_contribution'],mean_delta,abs_tol=1e-12)
  output[m]=dict(endpoints=endpoints,mean_reward_delta=mean_delta,label_partition=pieces,changed=changed,all30=contributions,task_gained=[r['condition'] for r in rows if r['task_change']>0],task_lost=[r['condition'] for r in rows if r['task_change']<0],strict_gained=[r['condition'] for r in rows if r['strict_change']>0],strict_lost=[r['condition'] for r in rows if r['strict_change']<0],max_reward_reconstruction_error=max(r['reward_reconstruction_abs_error'] for r in rawrows),checkpoint82_sha256=fr['checkpoint_sha256'])
  xs=list(range(30));colors=['green' if r['strict_change']>0 else 'red' if r['strict_change']<0 else 'steelblue' for r in rows]
  axes[index,0].bar(xs,[r['reward_delta'] for r in rows],color=colors);axes[index,0].axhline(0,color='black',linewidth=.5);axes[index,0].set(title=f'{m}: return82 - return55 (all30)',ylabel='Episode return difference')
  axes[index,1].plot(xs,[r['before']['penetration_mm'] for r in rows],'o-',label='Frozen55',alpha=.75);axes[index,1].plot(xs,[r['after']['penetration_mm'] for r in rows],'x-',label='Frozen82',alpha=.75);axes[index,1].axhline(.2,color='red',linestyle='--',label='Original Strict0.2mm');axes[index,1].set(title=f'{m}: external penetration',ylabel='mm');axes[index,1].legend(fontsize=8)
  for axis in axes[index]:
   axis.set_xticks(xs,[r['condition'].replace('passive_corner_train_','p').replace('active_short_train_','s').replace('active_long_train_','l') for r in rows],rotation=90,fontsize=7);axis.grid(axis='y',alpha=.2)
 fig.suptitle('Frozen55 -> frozen82, same external action seed2026102638; development cases only\nReturn bars: Strict gained=green, lost=red, unchanged=blue')
 plot=D/'frozen55_82_all90_pairs.png';fig.savefig(plot,dpi=150);plt.close(fig)
 report=dict(passed=True,time=time.time(),methods=output,total_episodes=90,total_actions=123750,total_substeps=99000000,inputs=[ref(p) for p in [O/'REVIEW.json',C/'REVIEW.json',C/'SAVED_REVIEW.json',A/'REVIEW.json',A/'SAVED_REVIEW.json',A/'FINISHED.json']],plot=ref(plot),new_physics=0,new_optimizer_updates=0,new_network_forwards=0,convergence_claim=False,limitation='Independent saved scalar assembly and all90 paired figure. Label-group return partition is arithmetic, not stochasticity/learning causality. Same external action seed and development conditions only, not independent training replicates, generalization or final ESN ranking. Contact ratio uses actual contact durations; no-contact is null.')
 put(D/'INTERPRETATION.json',report);assert read(D/'INTERPRETATION.json')==report
 put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),all90_rows_preserved=True,all_scalar_endpoint_sums_and_raw_audit_cross_checked=True,review=ref(D/'INTERPRETATION.json'),source=ref(Path(__file__)),plot=ref(plot)))
 print(json.dumps({m:{k:v for k,v in x.items() if k not in ['all30','changed']} for m,x in output.items()},indent=2))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(D/'INTERPRETATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
