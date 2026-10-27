from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter32_41_frozen_comparison_20261027_v1';O.mkdir()
code='''from pathlib import Path
import json,time,hashlib,math,os,csv
O=Path(__file__).parent;B=O.parents[1];os.sched_setaffinity(0,{54});os.nice(10)
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,allow_nan=False)+'\\n')
try:
 plan=read(O/'PLAN.json');assert sha(__file__)==plan['source_sha256'];new=B/'runs/parameter41_frozen_full30_20261027_v1';old=B/'runs/parameter32_frozen_full30_20261026_v1';limit=time.monotonic()+1200
 while not (new/'REVIEW.json').exists():
  assert time.monotonic()<limit and not (new/'REVIEW_FAILURE.json').exists(),'Original root review pending or failed'
  p=Path(f"/proc/{plan['root_reviewer']['pid']}");st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==plan['root_reviewer']['start_ticks']
  time.sleep(3)
 plans=[read(root/'PLAN.json') for root in [old,new]];reports=[read(root/'REVIEW.json') for root in [old,new]]
 assert plans[1]['comparison_frozen32']==dict(path=str(old/'REVIEW.json'),sha256=sha(old/'REVIEW.json'))
 assert plans[0]['case_ids']==plans[1]['case_ids'] and plans[0]['conditions']==plans[1]['conditions'] and plans[0]['action_seed']==plans[1]['action_seed']==2026102638
 assert all(r['passed'] and r['total_episodes']==90 and r['total_actions']==123750 and r['total_substeps']==99000000 and r['new_optimizer_updates']==0 for r in reports)
 inputs={};methods={};flat=[]
 for m in ['impedance','admittance','vmc']:
  summaries=[];episode_sets=[];regs=[]
  for root,report in zip([old,new],reports):
   folder=root/m;reg=read(folder/'REGISTRATION.json');regs.append(reg);end=read(folder/'FINISHED.json');result=read(folder/'RESULTS.json');row=report['methods'][m]
   assert end['passed'] and end['full_learner_state_unchanged'] and end['full_replay_state_unchanged'] and end['new_optimizer_updates']==0 and end['initial_learner_digest']==end['final_learner_digest']==row['initial_and_final_learner_digest']
   assert sha(reg['checkpoint'])==reg['checkpoint_sha256']==row['checkpoint_sha256']
   assert sha(reg['training_registration'])==reg['training_registration_sha256']
   proto=read(Path(reg['training_registration']));assert proto['conditions']==plans[0]['conditions']
   assert result['completed']==result['expected']==len(result['episodes'])==30 and len(row['episodes'])==30
   assert [r['condition'] for r in row['episodes']]==reg['case_ids']==plans[0]['case_ids']
   for full,compact in zip(result['episodes'],row['episodes']):
    f=folder/(compact['condition']+'_REVIEW.json');assert read(f)==full and full['passed'];physical=full['physical']['row']
    assert full['condition']==compact['condition'] and full['reward']==compact['reward'] and full['action_seed']==compact['seed']==2026102638
    assert physical['task_success']==compact['task'] and physical['strict_success']==compact['strict'] and full['external_penetration_mm']==compact['penetration_mm']
    assert compact['actions']==1375 and compact['substeps']==1100000 and compact['full_horizon'] and compact['abort_reason'] is None
    assert full['full_learner_state_unchanged'] and full['new_optimizer_updates']==0 and full['native_stochastic_parameter_action_max_error']<=1e-7
    assert full['filter']['passed'] and full['torque']['passed'];inputs[str(f)]=sha(f)
   es=row['episodes'];mean=sum(r['reward'] for r in es)/30;assert abs(mean-row['mean_reward'])<1e-10 and sum(r['task'] for r in es)==row['task']==end['task'] and sum(r['strict'] for r in es)==row['strict']==end['strict']
   contact=[r for r in es if r['human_contact_s']>0];assert all(r['human_compliance_ratio'] is not None and 0<=r['human_compliance_ratio']<=1 for r in contact)
   seconds=sum(r['human_contact_s'] for r in contact);weighted=sum(r['human_contact_s']*r['human_compliance_ratio'] for r in contact)/seconds if seconds else None
   summaries.append(dict(cycle=reg['parent_cycle'],task=row['task'],strict=row['strict'],mean_reward=mean,machine_safety_violation_count=sum(r['machine_safety_violation'] for r in es),full_horizon_count=sum(r['full_horizon'] for r in es),maximum_external_penetration_mm=max(r['penetration_mm'] for r in es),maximum_torque_nm=max(max(r['peak_torque_nm_per_joint']) for r in es),human_contact_seconds=seconds,human_contact_episode_count=len(contact),time_weighted_human_compliance_ratio=weighted,checkpoint_sha256=reg['checkpoint_sha256']))
   episode_sets.append(es)
   for name in ['REGISTRATION.json','FINISHED.json','RESULTS.json']:inputs[str(folder/name)]=sha(folder/name)
  common=regs[0]['source_hashes'].keys()&regs[1]['source_hashes'].keys();assert len(common)==21
  for name in common:
   assert regs[0]['source_hashes'][name]==regs[1]['source_hashes'][name]
   for reg in regs:assert sha(Path(reg['audit_runtime'])/name)==reg['source_hashes'][name]
  paired=[]
  for a,b in zip(*episode_sets):
   assert a['condition']==b['condition'];change=(a['task'],a['strict'])!=(b['task'],b['strict'])
   r=dict(controller=m,condition=a['condition'],reward32=a['reward'],reward41=b['reward'],reward_delta=b['reward']-a['reward'],contribution_to_mean=(b['reward']-a['reward'])/30,task32=a['task'],task41=b['task'],strict32=a['strict'],strict41=b['strict'],penetration32_mm=a['penetration_mm'],penetration41_mm=b['penetration_mm'],completion32_s=a['completion_time_s'],completion41_s=b['completion_time_s'],success_changed=change);paired.append(r);flat.append(r)
  delta=sum(r['reward_delta'] for r in paired)/30;assert abs(delta-(summaries[1]['mean_reward']-summaries[0]['mean_reward']))<1e-10
  methods[m]=dict(summaries=summaries,paired_mean_reward_delta=delta,success_changed_contribution=sum(r['contribution_to_mean'] for r in paired if r['success_changed']),other_conditions_contribution=sum(r['contribution_to_mean'] for r in paired if not r['success_changed']),task_gained=sum(not r['task32'] and r['task41'] for r in paired),task_lost=sum(r['task32'] and not r['task41'] for r in paired),strict_gained=sum(not r['strict32'] and r['strict41'] for r in paired),strict_lost=sum(r['strict32'] and not r['strict41'] for r in paired),common_source_modules_identical=21,conditions=paired)
 for root in [old,new]:
  for n in ['PLAN.json','REVIEW.json']:inputs[str(root/n)]=sha(root/n)
 for p,h in inputs.items():assert sha(Path(p))==h
 with (O/'PAIRED.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axes=plt.subplots(3,2,figsize=(13,10),constrained_layout=True)
 for ax,(m,d) in zip(axes,methods.items()):
  rows=d['conditions'];xs=list(range(30));ax[0].plot(xs,[r['reward32'] for r in rows],'.-',label='Frozen32');ax[0].plot(xs,[r['reward41'] for r in rows],'.-',label='Frozen41');ax[0].set_title(m+' episode reward');ax[0].legend()
  ax[1].bar(xs,[r['reward_delta'] for r in rows]);ax[1].axhline(0,color='black',linewidth=.7);ax[1].set_title(m+' paired41 minus32 reward')
  for a in ax:a.set_xlabel('Registered condition index');a.grid(alpha=.2)
 fig.suptitle('Same30 training conditions and external action seed; descriptive frozen comparison')
 fig.savefig(O/'PAIRED.png',dpi=140);plt.close(fig)
 write(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=methods,inputs=inputs,plot_sha256=sha(O/'PAIRED.png'),csv_sha256=sha(O/'PAIRED.csv'),new_physics=0,new_optimizer_updates=0,neural_forward_passes=0,convergence_claim=False,limitation='Prospectively selected endpoints32/41, same training conditions and one external action seed; this saved comparison is descriptive, not independent training-seed inference, causal attribution, held-out generalization, or final SPT/ESN comparison. Human ratio is weighted by actual contact duration; no-contact episodes excluded from that ratio. No new bootstrap or physical rerun.'))
 print(json.dumps({m:{k:v for k,v in d.items() if k!='conditions'} for m,d in methods.items()},indent=2),flush=True)
except BaseException as e:
 write(O/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
'''
(O/'audit.py').write_text(code)
pid=316553;p=Path(f'/proc/{pid}');st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z'
plan=dict(time=time.time(),root_reviewer=dict(pid=pid,start_ticks=st[19]),wait_seconds=1200,source_sha256=hashlib.sha256(code.encode()).hexdigest(),cycles=[32,41],automatic_training=False,selection='Existing frozen41 PLAN comparison_frozen32 reference',all_conditions=True)
(O/'PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
cmd=[str(B/'env/bin/python'),str(O/'audit.py')];env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
with (O/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
(O/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,command=cmd),indent=2)+'\n');print(p.pid)
