from pathlib import Path
import json,hashlib,time,difflib,ast
B=Path(__file__).resolve().parents[2]
D=B/'runtime/violation90_frozen_postprocess_20261030_v1';A=B/'runs/parameter90_violation_frozen_saved_audit_20261030_v1';R=B/'runs/parameter90_violation_frozen_full30_20261030_v1';P=B/'runs/parameter88_history_frozen_full30_20261030_v1'
oldD=B/'runtime/history88_frozen_postprocess_20261030_v1';oldA=B/'runs/parameter88_history_frozen_saved_audit_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def adapt(s):
 return s.replace('88','__NEW__').replace('82','88').replace('__NEW__','90').replace('parameter90_history','parameter90_violation').replace('parameter88_frozen','parameter88_history_frozen').replace('history90_frozen','violation90_frozen').replace('history51 critic amendment','violation52 critic amendment')
D.mkdir();A.mkdir()
for src,dest in [(oldD/'compare82_88.py',D/'compare88_90.py'),(oldD/'prepare_and_wait.py',D/'prepare_and_wait.py'),(oldA/'audit.py',A/'audit.py')]:
 old=src.read_text();s=adapt(old);ast.parse(s);dest.write_text(s);dest.with_suffix('.py.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(src),tofile=str(dest))))
pre=read(R/'PRE_REGISTRATION.json');cases=pre['methods']['impedance']['case_ids']
put(A/'PLAN.json',dict(time=time.time(),source=ref(A/'audit.py'),parent_source=ref(oldA/'audit.py'),preregistration=ref(R/'PRE_REGISTRATION.json'),case_ids=cases,prior_review=ref(P/'REVIEW.json'),physical_steps=0,optimizer_updates=0,scope='All90 registered frozen90 cases; raw substep/reward/torque and actual-contact audit, no physics rerun or convergence claim.'))
put(D/'PRE_REGISTRATION.json',dict(time=time.time(),source_sha256=sha(D/'compare88_90.py'),prior_review=ref(P/'REVIEW.json'),current_preregistration=ref(R/'PRE_REGISTRATION.json'),case_ids=cases,all90_pairs=True,includes_violation_architecture_change=True,physics_steps=0,optimizer_updates=0,scope='All90 same external action-seed comparison88 to90; includes online exposure and violation52 revision, no causal or final ranking.'))
put(D/'SOURCES.json',dict(time=time.time(),files={n:sha(D/n) for n in ['compare88_90.py','prepare_and_wait.py']},scope='Finite saved data postprocess; no dispatch before actual frozen90 collector.'))
# Check every prior/current frozen protocol before any new evaluation exists.
for m,reg in pre['methods'].items():
 old=read(P/m/'REGISTRATION.json');x=read(Path(old['training_registration']));y=read(Path(reg['training_registration']))
 assert reg['case_ids']==old['case_ids']==cases and reg['action_seed']==old['action_seed']==2026102638
 assert x['conditions']==y['conditions']
 for k in ['physics_dt_s','actor_period_s','horizon_s','reference_plan','reference_plan_sha256','torque_thresholds_nm','reward']:assert x[k]==y[k],k
 assert x['history_critic_amendment']==y['history_critic_amendment']
 assert 'violation_critic_amendment' not in x and y['violation_critic_amendment']['first_cycle']==90
put(D/'PROTOCOL_PAIR_REVIEW.json',dict(time=time.time(),passed=True,all90_current_prior_conditions_and_original_physics_reward_exact=True,prior_cycle=88,current_cycle=90,violation_architecture_diff_intentional=True,comparison_includes_additional_training=True,physics_steps=0,optimizer_updates=0,current90_outputs_still_pending=True))
print(D,A)
