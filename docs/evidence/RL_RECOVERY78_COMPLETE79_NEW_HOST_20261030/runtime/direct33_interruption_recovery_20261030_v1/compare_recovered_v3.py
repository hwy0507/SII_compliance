"""Saved frozen29-to33 descriptive comparison, no physics/update or final SPT selection."""
from pathlib import Path
import json,hashlib,math,csv,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/serl_take33_frozen_combined_review_20261030_v3';OLD=B/'runs/serl_take29_frozen_full30_20261027_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2,allow_nan=False)+'\n')
plan=read(O/'COMPARISON_PLAN.json')
for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
assert sha(__file__)==plan['source_sha256'];assert not (O/'PAIRED29_33.json').exists()
old,new=read(OLD/'REVIEW.json'),read(O/'REVIEW.json');regold,regnew=read(OLD/'REGISTRATION.json'),read(B/'runs/serl_take33_frozen_full30_20261029_v1/REGISTRATION.json')
assert old['passed'] and new['passed']
assert regold['cycle']==29 and regnew['cycle']==33 and regold['action_seed']==regnew['action_seed']==2026102626 and regold['noise_schedule']==regnew['noise_schedule']=='independent'
pold,pnew=[read(x['inputs']['training_registration']['path']) for x in [regold,regnew]];assert pold['conditions']==pnew['conditions'];cases=[c['id'] for c in pnew['conditions']]
rows=[];summary={}
for cy,report,reg in [(29,old,regold),(33,new,regnew)]:
 assert report['checkpoint_sha256']==reg['inputs']['checkpoint']['sha256'] and report['optimizer_updates']==report['replay_writes']==0
 if cy==29:assert report['formal_state_unchanged']
 else:
  assert report['formal_state_unchanged'] is False and report['original_final_inmemory_state_unavailable'] is True
  assert report['all28_original_saved_actions_reproduced_exactly'] and report['new2_full_state_unchanged'] and report['original_completed']==28 and report['recovered_completed']==2
  replay_ref=report['action_replay'];assert sha(replay_ref['path'])==replay_ref['sha256'];rp=read(replay_ref['path']);assert rp['passed'] and rp['all_saved_actions_exact'] and rp['replay_learner_state_unchanged'] and len(rp['episodes'])==28
  assert len({x['case'] for x in rp['episodes']})==28 and all(x['maximum_error']==0 for x in rp['episodes'])
 mapped={x['case']:x for x in report['episodes']};assert len(mapped)==30 and set(mapped)==set(cases)
 for x in mapped.values():
  assert sha(x['audit']['path'])==x['audit']['sha256'];r=x['row'];assert r['torque_thresholds_nm']==[43.5]*4+[6.]*3
  assert len(r['peak_torque_nm_per_joint'])==7 and all(math.isfinite(v) and v>=0 for v in r['peak_torque_nm_per_joint'])
  assert 0<=r['human_below_threshold_s']<=r['human_contact_s']+1e-9
  if r['human_contact_s']==0:assert r['human_compliance_ratio'] is None
  else:assert math.isclose(r['human_compliance_ratio'],r['human_below_threshold_s']/r['human_contact_s'],rel_tol=1e-12,abs_tol=1e-12)
 totals={k:sum(bool(x['row'][field]) for x in mapped.values()) for k,field in [('task','task_success'),('strict','strict_success'),('full_horizon','full_horizon'),('machine_violations','machine_safety_violation')]}
 assert all(report[k]==v for k,v in totals.items());contact=math.fsum(x['row']['human_contact_s'] for x in mapped.values());below=math.fsum(x['row']['human_below_threshold_s'] for x in mapped.values())
 summary[str(cy)]=dict(**totals,failures_retained_in_denominator=30,contact_episodes=sum(x['row']['human_contact_s']>0 for x in mapped.values()),human_contact_s=contact,human_below_threshold_s=below,pooled_contact_compliance_ratio=below/contact if contact>0 else None,mean_episode_peak_torque_nm=math.fsum(max(x['row']['peak_torque_nm_per_joint']) for x in mapped.values())/30,maximum_joint_torque_nm=max(max(x['row']['peak_torque_nm_per_joint']) for x in mapped.values()),aborts=[c for c,x in mapped.items() if x['row']['abort_reason'] is not None],checkpoint=reg['inputs']['checkpoint'],review=ref(OLD/'REVIEW.json' if cy==29 else O/'REVIEW.json'))
 if cy==29:before=mapped
 else:after=mapped
for c in cases:
 a,z=before[c]['row'],after[c]['row'];record=dict(condition=c,category=before[c]['category'],task29=a['task_success'],task33=z['task_success'],strict29=a['strict_success'],strict33=z['strict_success'],full_horizon29=a['full_horizon'],full_horizon33=z['full_horizon'],peak29=max(a['peak_torque_nm_per_joint']),peak33=max(z['peak_torque_nm_per_joint']),peak_delta=max(z['peak_torque_nm_per_joint'])-max(a['peak_torque_nm_per_joint']),human_contact29=a['human_contact_s'],human_contact33=z['human_contact_s'],comfort29=a['human_compliance_ratio'],comfort33=z['human_compliance_ratio'],completion29=a['completion_time_s'],completion33=z['completion_time_s'],stage29=a['final_task_stage'],stage33=z['final_task_stage'],abort29=a['abort_reason'],abort33=z['abort_reason'],audit29=before[c]['audit'],audit33=after[c]['audit']);rows.append(record)
report=dict(passed=True,time=time.time(),summary=summary,paired_conditions=rows,plan=ref(O/'COMPARISON_PLAN.json'),original33_final_inmemory_state_unavailable=True,formal33_state_unchanged=False,recovered33_action_provenance_verified=True,additional_interrupted_prefix_actions=new['additional_interrupted_prefix_actions'],final_spt_reference=None,final_spt_selected=False,heldout=False,convergence_claim=False,causal_claim=False,new_physics=0,optimizer_updates=0,limitation=plan['limitation'])
write(O/'PAIRED29_33.json',report)
keys=[k for k in rows[0] if not k.startswith('audit')]
with (O/'PAIRED29_33.csv').open('x',newline='') as f:
 w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows({k:r[k] for k in keys} for r in rows)
# Independent saved arithmetic: reload records; count rates and peak deltas separately.
saved=read(O/'PAIRED29_33.json');records=saved['paired_conditions'];assert len(records)==30
for cy in [29,33]:
 s=saved['summary'][str(cy)];assert sum(int(x[f'task{cy}']) for x in records)==s['task'];assert sum(int(x[f'strict{cy}']) for x in records)==s['strict'];assert math.isclose(sum(x[f'peak{cy}'] for x in records)/30,s['mean_episode_peak_torque_nm'],rel_tol=1e-12,abs_tol=1e-12)
assert math.isclose(sum(x['peak_delta'] for x in records)/30,summary['33']['mean_episode_peak_torque_nm']-summary['29']['mean_episode_peak_torque_nm'],rel_tol=1e-12,abs_tol=1e-12)
write(O/'PAIRED_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all30_counts_means_deltas_verified=True,comparison=ref(O/'PAIRED29_33.json'),source=ref(Path(__file__)),new_physics=0,optimizer_updates=0))
print(json.dumps(summary,indent=2))
