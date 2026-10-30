from pathlib import Path
import json,hashlib,ast,time,math,os
D=Path(__file__).parent;B=D.parents[1];R=B/'runtime/parameter86_half_std_paired_20261030_v3';O=B/'runs'/R.name
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def pidstate(pid):
 x=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();return dict(state=x[0],start=x[19],affinity=sorted(os.sched_getaffinity(pid)))
old=B/'runtime/parameter86_frozen_switches_20261030_v1/evaluate_parameter86_frozen_switches_20261030.py';new=R/'evaluate_parameter86_half_std_20261030.py'
a=[n for n in ast.walk(ast.parse(old.read_text())) if isinstance(n,ast.While)];b=[n for n in ast.walk(ast.parse(new.read_text())) if isinstance(n,ast.While)];assert len(a)==len(b)==1
assert ast.dump(a[0])==ast.dump(b[0]),'Physics IPC/action loop changed'
plan=read(O/'PLAN.json');launch=read(O/'LAUNCH.json');rows={}
assert plan['time']<launch['time']
for job in launch['jobs']:
 g=job['group'];d=O/g;reg=read(d/'REGISTRATION.json');startup=read(d/'STARTUP_REVIEW.json');ev=read(d/'EVALUATION.json');progress=read(d/'PROGRESS.json');cur=read(d/'CURRENT_PHYSICS.json')
 probe=read(d/'STARTUP_PROBE.json');assert probe['passed'] and probe['pre_tanh_std_factor']==.5 and probe['sampling_distribution_intentionally_changed']
 assert startup['passed'] and startup['full_replay_restored_exact'] and startup['full_learner_state_unchanged']
 assert startup['full_learner_digest']==ev['full_learner_digest'] and startup['replay_digest']==ev['full_replay_digest']
 assert ev['registration_sha256']==sha(d/'REGISTRATION.json') and ev['checkpoint_sha256']==reg['checkpoint_sha256']
 assert ev['optimizer_updates']==0 and ev['expected_episodes']==4 and ev['maximum_actions']==5500
 assert progress['seed']==plan['action_seeds'][0] and progress['actions']>=100
 assert cur['seed']==progress['seed'] and cur['condition']==reg['case_ids'][0]
 st=pidstate(job['pid']);assert st['start']==job['start'] and st['state']!='Z' and st['affinity']==[reg['cpu']]
 child=pidstate(cur['pid']);assert child['state']!='Z' and child['affinity']==[reg['cpu']]
 protocol=read(reg['training_registration']);condition=next(c for c in protocol['conditions'] if c['id']==reg['case_ids'][0])
 folder=d/f'seed_{progress["seed"]}';assert sha(folder/'rollout.mjb')==condition['model_sha256']
 with (folder/'actor_intervals.jsonl').open('rb') as f:prefix=b''.join(next(f) for _ in range(100))
 parsed=[json.loads(line) for line in prefix.splitlines()]
 dim=5 if reg['controller']=='impedance' else 7
 for row in parsed:
  assert len(row['observation'])==48 and len(row['action'])==dim
  assert all(math.isfinite(x) for x in row['observation']+row['action'])
  assert all(-1<=x<=1 for x in row['action'])
 dest=d/'STARTUP_FIRST100.jsonl';dest.write_bytes(prefix);assert [json.loads(x) for x in dest.read_bytes().splitlines()]==parsed
 rows[g]=dict(learner=st,physics=child,physics_pid=cur['pid'],first_seed=progress['seed'],observed_actions=progress['actions'],prefix_rows=100,prefix_sha256=sha(dest),model_sha256=sha(folder/'rollout.mjb'),canonical_observation_dimension=48,action_dimension=dim,checkpoint_sha256=reg['checkpoint_sha256'],learner_digest=startup['full_learner_digest'],replay_digest=startup['replay_digest'])
for n in plan['groups']['impedance_short0600']['source_hashes']:
 if n not in [new.name,'half_std_probe.py','pair_review.py']:assert sha(R/n)==sha(B/'runtime/parameter86_frozen_switches_20261030_v1'/n),n
write(O/'STARTUP_SAVED_AUDIT.json',dict(passed=True,time=time.time(),groups=rows,physics_action_loop_ast_exact=True,sampler_intentionally_changed=True,old_evaluator_sha256=sha(old),new_evaluator_sha256=sha(new),all_unchanged_native_helpers_exact=all(sha(R/n)==sha(B/'runtime/parameter86_frozen_switches_20261030_v1'/n) for n in plan['groups']['impedance_short0600']['source_hashes'] if n not in [new.name,'half_std_probe.py','pair_review.py']),plan_written_before_dispatch=True,new_physics=0,new_optimizer_updates=0,final_full_state_invariance_pending=True))
print('FOUR ACTUAL STARTUPS AND400 SAVED ROWS PASSED')
