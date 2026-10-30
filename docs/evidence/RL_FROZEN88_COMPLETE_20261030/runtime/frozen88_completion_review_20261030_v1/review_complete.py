"""Review completed original frozen88 artifacts, with no physics or learning."""
from pathlib import Path
import hashlib,json,math,time,os
D=Path(__file__).resolve().parent; B=D.parents[1]
O=B/'runs/parameter88_history_frozen_full30_20261030_v1'
A=B/'runs/parameter88_history_frozen_saved_audit_20261030_v1'
P=B/'runtime/history88_frozen_postprocess_20261030_v1'
def read(p):return json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h,bytes=p.stat().st_size)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
os.sched_setaffinity(0,{3})
assert read(P/'FINISHED.json')['passed']
assert not list(P.glob('FAILURE*')) and not (O/'REVIEW_FAILURE.json').exists()
r=read(O/'REVIEW.json');a=read(A/'REVIEW.json');c=read(O/'comparison82_88/REVIEW.json')
assert r['passed'] and a['passed'] and c['passed']
assert r['total_episodes']==a['total_cases']==90
assert r['total_substeps']==a['total_substeps']<=99000000
assert r['total_actions']<=123750
for p in (A/'SAVED_REVIEW.json',A/'FINISHED.json',O/'comparison82_88/SAVED_REVIEW.json'):assert read(p)['passed']
methods={}; inputs=[]
for m in ('impedance','admittance','vmc'):
 f=read(O/m/'FINISHED.json');assert f['passed'] and f['full_learner_state_unchanged'] and f['full_replay_state_unchanged'] and f['new_optimizer_updates']==0
 assert f['initial_learner_digest']==f['final_learner_digest'];assert not (O/m/'FAILURE.json').exists()
 rs=r['methods'][m];ars=a['methods'][m];cs=c['methods'][m]
 assert len(rs['episodes'])==len(ars)==len(cs['rows'])==30
 for x,y,z in zip(rs['episodes'],ars,cs['rows']):
  assert x['condition']==y['condition']==z['condition'];assert z['after']==x
  for k in ('task','strict','reward','actions','peak_torque_nm_per_joint'):assert x[k]==y[k],(m,k)
  assert math.isclose(x['human_contact_s'],y['human_contact_s'],abs_tol=1e-8)
  if x['human_compliance_ratio'] is None:assert y['human_compliance_ratio'] is None
  else:assert math.isclose(x['human_compliance_ratio'],y['human_compliance_ratio'],abs_tol=1e-12)
  assert x['machine_safety_violation']==y['machine_violation']
  assert x['penetration_mm']==y['external_penetration_mm']
 contact=math.fsum(x['human_contact_s'] for x in ars);compliant=math.fsum(x['human_compliant_s'] for x in ars)
 assert math.isclose(rs['mean_reward'],math.fsum(x['reward'] for x in ars)/30,abs_tol=1e-12)
 methods[m]={k:v for k,v in rs.items() if k!='episodes'}
 methods[m].update(contact_seconds=contact,compliant_contact_seconds=compliant,pooled_contact_compliance=(compliant/contact if contact else None),no_contact_cases=[x['condition'] for x in ars if not x['human_contact_s']],peak_torque_nm_per_joint=[max(x['peak_torque_nm_per_joint'][j] for x in ars) for j in range(7)],max_reward_reconstruction_abs_error=max(x['reward_reconstruction_abs_error'] for x in ars),task_failed=[x['condition'] for x in ars if not x['task']],strict_failed=[x['condition'] for x in ars if not x['strict']],machine_failed=[x['condition'] for x in ars if x['machine_violation']],comparison82_88={k:v for k,v in cs.items() if k!='rows'})
 inputs.append(ref(O/m/'FINISHED.json'))
for p in (O/'REVIEW.json',A/'REVIEW.json',A/'SAVED_REVIEW.json',A/'FINISHED.json',O/'comparison82_88/REVIEW.json',O/'comparison82_88/SAVED_REVIEW.json',P/'FINISHED.json',O/'frozen_full30_results.png'):inputs.append(ref(p))
put(D/'REVIEW.json',dict(passed=True,time=time.time(),methods=methods,inputs=inputs,total_episodes=90,total_actions=r['total_actions'],total_substeps=r['total_substeps'],new_physics=0,new_optimizer_updates=0,convergence_claim=False,limitation='Original training cohort and one fixed external action seed; 82 to 88 includes added training and a critic architecture change, without causal attribution or held-out generalization. No-contact comfort stays NA; pooled ratio uses actual contact duration. Specified ESN and final comparison remain pending.'))
print(json.dumps(methods,indent=2))
