from pathlib import Path
import json,time,hashlib,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;O=B/'runs/serl_take33_frozen_full30_20261029_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat');f=q.read_text().rsplit(')',1)[1].split() if q.exists() else None
 return f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert not (O/'LAUNCH.json').exists() and not (O/'PRELAUNCH_REVIEW.json').exists()
assert not live(read(O/'CHECK_ONLY_LAUNCH.json'))
reg=read(O/'REGISTRATION.json');plan=read(O/'PLAN.json');check=read(O/'check_only/CHECK_ONLY_REVIEW.json');state=read(O/'check_only/FULL_STATE_RESTORE.json');gate=read(O/'check_only/EXTERNAL_ACTION_RNG_GATE.json')
for x in list(reg['inputs'].values())+list(reg['sources'].values()):assert sha(x['path'])==x['sha256']
assert read(O/'STATIC_REVIEW.json')['passed'] and read(O/'WRONG_CYCLE_REJECTION.json')['passed']
assert plan['cycle']==33 and plan['action_seed']==2026102626 and plan['noise_schedule']=='independent' and plan['maximum_episodes']==30 and plan['maximum_actions']==41250 and plan['maximum_physical_substeps']==33000000
assert check['passed'] and check['cycle']==33 and check['full_learner_state_exact'] and check['full_replay_state_exact'] and check['external_action_rng_gate']
assert state['passed'] and state['checkpoint_sha256']==reg['inputs']['checkpoint']['sha256']==sha(O/'check_only/checkpoint_frozen.pt')==check['checkpoint_sha256']
assert state['replay_capacity']==2000000 and state['replay_size']==1369290 and state['historical_capacity_entry']==23
assert check['recovery_state']==state['recovery_state'];rec=state['recovery_state'];assert rec['quarantined_pending']==930 and rec['original_pending_exact'] and rec['original_pending_raw_derived_exact'] and rec['pending_not_mature_or_sampleable'] and not rec['complete25_invented'] and rec['complete_cycles_after_recovery']==list(range(26,34))
for x in [check,state]:assert all(x[k]==0 for k in ['optimizer_updates','new_physics','replay_writes'])
assert gate['passed'] and gate['same_seed_actions_exact'] and gate['different_seed_changes_actions'] and gate['temporal_sampling_gate_passed'] and gate['full_state_unchanged']
parent=read(reg['inputs']['training_registration']['path']);assert parent['conditions']==plan['conditions']
for c in plan['conditions']:
 assert sha(c['path'])==c['sha256'];assert sha(Path(c['preflight'])/'rollout.mjb')==c['model_sha256']
for j in read(B/'runs/parameter_partial75_recovery_cycle78_20261029_v1/LAUNCH.json')['jobs']:
 assert live(j);assert not os.sched_getaffinity(j['pid']).intersection({0,1,2,3})
for p in Path('/proc').iterdir():
 if not p.name.isdigit() or int(p.name)==os.getpid():continue
 try:
  cmd=(p/'cmdline').read_bytes();aff=os.sched_getaffinity(int(p.name))
  assert not (b'python' in cmd and len(aff)<20 and aff.intersection({0,1,2,3})),('CPU0-3 already occupied',p.name)
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
write(O/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),check=ref(O/'check_only/CHECK_ONLY_REVIEW.json'),restore=ref(O/'check_only/FULL_STATE_RESTORE.json'),external_rng=ref(O/'check_only/EXTERNAL_ACTION_RNG_GATE.json'),process_naturally_exited=True,exit_code_observed=False,new_physics=0,optimizer_updates=0,automatic_evaluation=False))
write(O/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),cycle=33,evidence={n:ref(O/n) for n in ['PLAN.json','SOURCE_FREEZE.json','REGISTRATION.json','STATIC_REVIEW.json','WRONG_CYCLE_REJECTION.json','CHECK_ONLY_COMPLETE.json']},launcher=ref(Path(__file__)),reason='Execute one registered full30 frozen validation for latest complete33 retained at accepted Direct numerical stage. Keep original29 paired cohort/action seed and all failure denominators. Post-training checkpoint selection disclosed. No update, no replay write, noDirect34, no held-out or finalESN claim. Original33 fullstate and original930 quarantined rows verified; parameter78 and guard remain unchanged.',automatic_training=False))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1');jobs=[]
for i,job in enumerate(read(O/'COMMANDS.json')['jobs']):
 assert not Path(job['output']).exists()
 with (O/f'shard{i}.log').open('x') as f:p=subprocess.Popen(job['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(**job,pid=p.pid,start=start,proc_start_ticks=start,time=time.time()))
write(O/'LAUNCH.json',dict(time=time.time(),jobs=jobs,prelaunch=ref(O/'PRELAUNCH_REVIEW.json'),finite_episodes=30,automatic_training=False))
rt=Path(reg['evaluation_runtime']);cmd=[str(B/'env/bin/python'),str(rt/'review_serl33_frozen_matrix_20261029.py'),'--root',str(O)]
with (O/'review.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'REVIEW_LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),command=cmd));print(dict(evaluators=[j['pid'] for j in jobs],review=p.pid))
