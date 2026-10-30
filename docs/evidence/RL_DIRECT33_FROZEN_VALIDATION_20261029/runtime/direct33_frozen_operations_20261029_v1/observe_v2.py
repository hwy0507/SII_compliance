from pathlib import Path
import json,time,hashlib,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;O=B/'runs/serl_take33_frozen_full30_20261029_v1';P=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return s is not None and s[19]==j['proc_start_ticks'] and s[0]!='Z'
os.sched_setaffinity(0,{3})
try:
 jobs=[]
 for j in read(P/'LAUNCH.json')['jobs']:jobs.append(dict(role='parameter78_'+j['controller'],pid=j['pid'],proc_start_ticks=j['proc_start_ticks']))
 for root,label,file in [(P,'archive78','MONITOR_LAUNCH.json'),(O,'frozen33_review','REVIEW_LAUNCH.json'),(O,'comparison29_33','COMPARISON_LAUNCH.json')]:jobs.append(dict(role=label,**read(root/file)))
 for name in ['parameter_recovery78_loss_20261029_v1','parameter_recovery78_task_labels_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:jobs.append(dict(role=name,**read(B/'runs'/name/'LAUNCH.json')))
 for i,j in enumerate(read(O/'LAUNCH.json')['jobs']):jobs.append(dict(role=f'frozen33_shard{i}',**j))
 gl=read(G/'LAUNCH.json')
 for pid in [gl['pid']]+list(gl['workers'].values()):jobs.append(dict(role='synthetic_guard',pid=pid,proc_start_ticks=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
 assert all(live(j) for j in jobs)
 check=read(O/'check_only/FULL_STATE_RESTORE.json');reg=read(O/'REGISTRATION.json');plan=read(O/'PLAN.json');startup=[]
 for j in read(O/'LAUNCH.json')['jobs']:
  folder=Path(j['output']);restore=read(folder/'FULL_STATE_RESTORE.json');assert restore==check
  gate=read(folder/'EXTERNAL_ACTION_RNG_GATE.json');assert gate['passed'] and gate['full_state_unchanged'];e=read(folder/'EVALUATION.json')
  assert e['checkpoint_sha256']==reg['inputs']['checkpoint']['sha256'] and e['case_ids']==j['case_ids'] and e['registration_sha256']==reg['inputs']['training_registration']['sha256'] and e['action_seed']==2026102626 and not e['deterministic'] and e['audit_substeps'] and e['optimizer_updates_during_evaluation']==0
  assert e['learner_cpu']==0 and e['physics_cpu'] in [1,2] and e['inference_device']=='cuda:0'
  case=folder/j['case_ids'][0];c=next(c for c in plan['conditions'] if c['id']==case.name);assert sha(case/'rollout.mjb')==c['model_sha256'];assert sha(case/'executed_evaluator.py.txt')==read(case/'ADAPTER.json')['executed_evaluator_function_sha256'];assert sha(case/'executed_evaluator.py.txt')==sha(B/'runs/serl_take29_frozen_full30_20261027_v1'/folder.name/case.name/'executed_evaluator.py.txt');assert sha(e['episode_entrypoint'])==e['episode_entrypoint_sha256']
  with (case/'actor_intervals.jsonl').open() as f:first=json.loads(f.readline())
  import math
  assert len(first['observation'])==48 and len(first['action'])==7 and all(math.isfinite(x) and abs(x)<=1.000001 for x in first['action']);assert first['action']==first['executed_action']
  children=[int(v) for v in Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()];assert len(children)==1 and os.sched_getaffinity(j['pid'])=={0} and os.sched_getaffinity(children[0])=={e['physics_cpu']}
  startup.append(dict(pid=j['pid'],restore=ref(folder/'FULL_STATE_RESTORE.json'),rng_gate=ref(folder/'EXTERNAL_ACTION_RNG_GATE.json'),evaluation=ref(folder/'EVALUATION.json'),first_model_exact=True,first_action_shape_bounds_and_execution_bridge_exact=True,physical_child=children[0]))
 write(D/'ACTUAL_FROZEN33_STARTUP_REVIEW.json',dict(passed=True,time=time.time(),shards=startup,full_actual_restores_equal_check_only=True,new_audit_physics=0,optimizer_updates=0,limitation='Startup restore/model/runtime/action bridge check; full30 physical/filter/torque and final policy invariance remain with original reviewer. Not a complete physics audit.'))
 write(D/'OBSERVATION_PLAN.json',dict(time=time.time(),jobs=jobs,samples=5,interval_seconds=30,observer_expiry_does_not_restart_science=True))
 started=time.monotonic();rows=[]
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  for i in range(5):
   states=[dict(role=j['role'],pid=j['pid'],live=live(j)) for j in jobs];assert all(x['live'] for x in states)
   assert not (O/'REVIEW_FAILURE.json').exists() and not (P/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (G/'FAILURE.json').exists()
   for m in ['impedance','admittance','vmc']:assert not (P/m/'train/FAILURE.json').exists()
   g=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   shards=[]
   for j in read(O/'LAUNCH.json')['jobs']:
    folder=Path(j['output']);assert not (folder/'FAILURE.json').exists();result=read(folder/'RESULTS.json') if (folder/'RESULTS.json').exists() else None
    shards.append(dict(pid=j['pid'],completed=len(result['episodes']) if result else 0,first_case_progress=read(folder/j['case_ids'][0]/'rollout.progress.json')))
   row=dict(time=time.time(),states=states,parameter_steps={m:read(P/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']},frozen_shards=shards,guard=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   if i<4:time.sleep(max(0,started+30*(i+1)-time.monotonic()))
 write(D/'OBSERVATION_FINISHED.json',dict(passed=True,time=time.time(),samples=len(rows),elapsed=time.monotonic()-started,identities=len(jobs),all_original_identities_live=True,first_parameter_steps=rows[0]['parameter_steps'],last_parameter_steps=rows[-1]['parameter_steps'],first_frozen_shards=rows[0]['frozen_shards'],last_frozen_shards=rows[-1]['frozen_shards'],scientific_restart=False));print('Actual startup and120-second original process observation passed')
except BaseException as e:write(D/'OBSERVATION_RETRY_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
