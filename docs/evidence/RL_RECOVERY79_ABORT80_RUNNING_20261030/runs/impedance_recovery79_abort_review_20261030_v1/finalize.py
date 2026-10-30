from pathlib import Path
import json,hashlib,time,os
os.sched_setaffinity(0,{7})
import numpy as np
D=Path(__file__).parent;B=D.parents[1]
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
plan=read(D/'PLAN.json');geo=read(D/'REVIEW.json');servo=read(D/'SHIELD_SERVO_REVIEW.json')
for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
assert geo['passed'] and geo['new_mj_steps']==0 and geo['geometry_forward_calls']==1350
assert servo['status']=='passed' and servo['updates']==675 and servo['native_servo']['rows']==6750 and max(servo['shield_replay_max_abs'].values())==0
with np.load(D/'geometry_values.npz',allow_pickle=False) as a:
 for c in ['78','79']:
  x=geo['cycles'][c];assert len(a[c+'_time'])==675 and np.isfinite(a[c+'_penetration']).all()
  assert float(a[c+'_penetration'].max())==x['maximum_saved_frame_global_penetration_m']
  assert np.array_equal(a[c+'_object'][-1],x['last_saved_object_position'])
case=Path(plan['inputs']['79:TERMINAL.json']['path']).parent;terminal=read(case/'TERMINAL.json');train=case.parents[1]
ts=[json.loads(l) for l in (train/'transitions.jsonl').read_text().splitlines()];ts=[t for t in ts if t['condition']==case.name and t['cycle']==79]
e=[json.loads(l) for l in (train/'episodes.jsonl').read_text().splitlines() if json.loads(l)['condition']==case.name and json.loads(l)['cycle']==79][0]
assert len(ts)==675 and sum(t['done'] for t in ts)==1 and ts[-1]['done'] and ts[-1]['step']==3264119
assert abs(sum(t['reward'] for t in ts)-e['reward'])<1e-8
full=B/'runs/parameter_partial75_recovery_cycle79_review_20261029_v1/REVIEW.json';r=read(full)['methods']['impedance']
assert r['new_transitions']==40550 and r['full_horizon_count']==29 and r['aborts']==[e] and r['max_reward_reconstruction_error']==0 and r['retained_replay_all_fields_exact']
health=B/'runs/parameter_partial75_recovery_cycle79_review_20261029_v1/health/DIAGNOSIS.json';ep=next(x for x in read(health)['methods']['impedance']['episodes'] if x['condition']==case.name)
assert ep['reward_terms']['terminal']==-25 and ep['reward_terms']['failure_tail']<0
# Inspect actual log lines without treating words inside the final JSON metrics as warnings.
log=case/'evaluator.log';nonjson=[]
for i,line in enumerate(log.read_text(errors='replace').splitlines(),1):
 try:json.loads(line)
 except (ValueError,TypeError):
  if any(s in line.lower() for s in ['warning','unstable','nan','infinite']):nonjson.append(dict(line=i,text=line[:2000]))
evidence={k:ref(D/k) for k in ['PLAN.json','REVIEW.json','SHIELD_SERVO_REVIEW.json','PLOT_INSPECTION.json','geometry_values.npz','abort_geometry.png','audit_geometry.py']}
evidence.update(full79=ref(full),health79=ref(health),transitions=ref(train/'transitions.jsonl'),episodes=ref(train/'episodes.jsonl'),terminal=ref(case/'TERMINAL.json'),evaluator_log=ref(log),finalizer=ref(__file__))
out=dict(time=time.time(),passed=True,abort_preserved=True,physical_valid=False,root_cause_established=False,known_abort=e,actual_actions=675,actual_time_s=terminal['terminal_time_s'],actual_cycle_new_transitions=40550,full_horizon_count=29,terminal_transition_step=ts[-1]['step'],terminal_transition_reward=ts[-1]['reward'],exactly_one_done=True,reward_sum_reproduced=True,replay_done_reward_validated_by_bound_full79_review=True,terminal_penalty=ep['reward_terms']['terminal'],failure_tail=ep['reward_terms']['failure_tail'],non_json_warning_lines=nonjson,warning_scope='Only saved evaluator.log non-JSON lines; absence does not establish warning-free integration. No full substep trajectory available.',new_mj_steps=0,new_optimizer_updates=0,evidence=evidence,interpretation='Real simulated safety failure at27s; original2mm end-of-actor-iteration check terminated episode and original failure reward/done retained. Shield and logged servo checks pass, but do not prove global passivity or integration correctness. Saved25Hz geometry is insufficient to localize97.689mm inter-frame peak. No reclassification, replay deletion, retry, model/gate/reward change or claim of harmless spike.')
with (D/'FINAL_REVIEW.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='evidence'},indent=2))
