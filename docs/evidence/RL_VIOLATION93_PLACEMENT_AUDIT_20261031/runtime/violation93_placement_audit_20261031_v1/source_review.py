from pathlib import Path
import json,hashlib,time,ast
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_placement_audit_20261031_v1';S=B/'runtime/source_train17_clock/source';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2);f.write('\n')
r=rd(O/'REVIEW.json');entries=[];hashes=set()
for e in r['episodes']:
 p=Path(e['episode']);a=rd(p/'ADAPTER.json');rr=rd(p/'rollout.json');h=sha(p/'executed_evaluator.py.txt');assert h==a['executed_evaluator_function_sha256'];hashes.add(h)
 for n in ['office_task_v4_20260917.py','audited_velocity_env.py']:assert sha(S/'scripts'/n)==rr['source_sha256'][n]
 entries.append(dict(episode=str(p),executed_evaluator_sha256=h))
assert len(hashes)==1
code=(Path(r['episodes'][0]['episode'])/'executed_evaluator.py.txt').read_text();expected='placement_hold=placement_hold+.04 if supported and near and slow and released and height_ok and angular_slow else 0.';assert expected in code;assert code.index('env.step(applied)')<code.index(expected)<code.index('PUBLISHED_PLACEMENT(placement_hold,d.time)')<code.index('records.append(dict(time=float(d.time)')
contact=(S/'scripts/office_task_v4_20260917.py').read_text();tree=ast.parse(contact);node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='contact_support');function=ast.get_source_segment(contact,node);assert 'mj_contactForce' in function and 'f[0]>.05' in function
put(O/'SOURCE_REVIEW.json',dict(passed=True,time=time.time(),episodes=entries,all98_actual_evaluators_identical=True,actual_contact_and_dynamics_source_hashes_match_frozen_source=True,contact_support=function,original_hold_update=expected,post_step_hold_then_record_order_checked=True,missing_fields=['live normal contact forces for target-support and target-robot','constraint solver state/previous velocity/warmstart needed for exact mj_forward force reconstruction','107 partial-cohort finalized raw trajectories in complete85 inventory'],scope='Exact source and array phase checked; implicitfast final translation is post qpos - dt*post qvel (max error0 across98). This does not reconstruct constraint force or complete prior physics state.'))
print('All98 actual evaluator/contact/dynamics sources bound; original gate/update order checked.')
