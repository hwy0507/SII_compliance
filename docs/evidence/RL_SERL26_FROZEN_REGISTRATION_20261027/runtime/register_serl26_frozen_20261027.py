from pathlib import Path
import json,time,hashlib,ast,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';RT=B/'runtime/serl_cycle26_frozen_full30_20261027_v1';OUT=B/'runs/serl_cycle26_frozen_full30_20261027_v1';OUT.mkdir(exist_ok=False)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
validation=B/'runs/serl26_frozen_capacity_validation_20261027_v1';reg=json.loads((validation/'REGISTRATION.json').read_text());gate=validation/'restore24_v4'
assert json.loads((gate/'CHECK_ONLY_REVIEW.json').read_text())['passed'];assert json.loads((gate/'EXTERNAL_ACTION_RNG_GATE.json').read_text())['passed']
assert sha(reg['checkpoint'])==reg['checkpoint_sha256'];assert sha(reg['training_registration'])==reg['training_registration_sha256']
assert not Path('/proc/3422452').exists()
write(validation/'VALIDATION_REVIEW.json',dict(passed=True,time=time.time(),actual_cycle=24,source_sha256=sha(RT/'evaluate_serl_capacity_frozen_20261027.py'),checkpoint_sha256=reg['checkpoint_sha256'],full_learner_replay_restore_exact=True,history_field='cycles',external_action_rng_gate_passed=True,source_helper_unchanged=True,optimizer_updates=0,new_physics=0,replay_writes=0,limitation='Actual24 validates new evaluator restore only; not actual26 restoration or physical evaluation. Failed CPU/v3 visibility attempts preserved; native singleGPU0 v4 passed.'))
proto=json.loads((B/'runs/serl_capacity_batch65536_cycle25_20261027_v1/REGISTRATION.json').read_text());old=B/'runs/serl_cycle16_frozen_full30_20261026_v1';oldreg=json.loads((old/'REGISTRATION.json').read_text());oldproto=json.loads(Path(oldreg['inputs']['training_registration']['path']).read_text());assert proto['conditions']==oldproto['conditions'];assert json.loads((old/'REVIEW.json').read_text())['passed']
sources={p.name:sha(p) for p in RT.glob('*.py')}
plan=dict(time=time.time(),cycle=26,selected_as='Prospective endpoint of original24-26 reward stability window;26 not yet launched',action_seed=2026102626,noise_schedule='independent',maximum_episodes=30,maximum_actions=41250,maximum_physical_substeps=33000000,conditions=proto['conditions'],case_ids=[c['id'] for c in proto['conditions']],physics_cpus=[53,54],learner_cpu=52,inference_gpu=0,optimizer_updates=0,replay_writes=0,training_conditions_only=True,convergence_claim=False,source_hashes=sources,capacity_entry_cycle=23,replay_capacity=2000000,capacity_restore_validation=ref(validation/'VALIDATION_REVIEW.json'),comparison_frozen16_review=ref(old/'REVIEW.json'),comparison_frozen16_registration=ref(old/'REGISTRATION.json'),preparation_wait_seconds=10800,check_only_timeout_seconds=600,evaluation_review_wait_seconds=21600,physical_launch_resource_gate='Wait until parameter41 frozen original evaluators and root review have completed; avoid concurrent physics on CPU53/54. Training0-51 continues.',automatic_evaluation=False,automatic_training=False,limitation='Single training seed and single external action seed on full training cohort; not held-out/generalization/final ESN or convergence claim. Capacity1m-to2m change disclosed for16-to26 comparison.')
assert not (B/'runs/serl_capacity_batch65536_cycle26_20261027_v1/LAUNCH.json').exists();write(OUT/'PLAN.json',plan);plan_sha=sha(OUT/'PLAN.json')
prepare='''from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=B/'runs/serl_cycle26_frozen_full30_20261027_v1';RT=B/'runtime'/OUT.name
PLAN_SHA=__PLAN_SHA__
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\\n')
def main():
 os.sched_setaffinity(0,{52});assert sha(OUT/'PLAN.json')==PLAN_SHA;plan=json.loads((OUT/'PLAN.json').read_text())
 for n,h in plan['source_hashes'].items():assert sha(RT/n)==h
 assert json.loads(Path(plan['capacity_restore_validation']['path']).read_text())['passed']
 for name in ['capacity_restore_validation','comparison_frozen16_review','comparison_frozen16_registration']:
  item=plan[name];assert sha(item['path'])==item['sha256']
 review=B/'runs/serl_capacity_batch65536_cycle26_review_20261027_v1';deadline=time.monotonic()+plan['preparation_wait_seconds']
 while not (review/'FINISHED.json').exists():
  assert time.monotonic()<deadline,'Complete26 wait expired; no automatic extension/retry'
  assert not (B/'runs/serl_capacity_batch65536_cycle26_20261027_v1/direct/FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((review/'FINISHED.json').read_text())['completed'];full=json.loads((review/'REVIEW.json').read_text());assert full['passed']
 parent=B/'runs/serl_capacity_batch65536_cycle26_20261027_v1/REGISTRATION.json';protocol=json.loads(parent.read_text());assert protocol['conditions']==plan['conditions'] and protocol['replay_capacity_stage']['parent_cycle']==23
 checkpoint=B/'runs/serl_capacity_batch65536_cycle26_archive_20261027_v1/direct/cycle_00026.pt';assert sha(checkpoint)==full['methods']['direct']['checkpoint_sha256']
 reg={k:plan[k] for k in ['cycle','action_seed','noise_schedule','maximum_episodes','maximum_physical_substeps','physics_cpus','learner_cpu','inference_gpu','optimizer_updates','replay_writes','training_conditions_only','convergence_claim']}
 reg.update(evaluation_runtime=str(RT),inputs=dict(training_registration=ref(parent),checkpoint=ref(checkpoint),cycle_review=ref(review/'REVIEW.json'),health_review=ref(review/'DIAGNOSIS.json'),finished=ref(review/'FINISHED.json')),sources={n:dict(path=str(RT/n),sha256=h) for n,h in plan['source_hashes'].items()})
 write(OUT/'REGISTRATION.json',reg)
 common=[str(B/'serl_env/bin/python'),str(RT/'evaluate_serl_capacity_frozen_20261027.py'),'--runtime',protocol['runtime'],'--registration',str(parent),'--checkpoint',str(checkpoint),'--expected-cycle','26','--device','cuda:0','--learner-cpu','52','--serl-upstream',str(B/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(B/'env/bin/python'),'--stochastic','--action-seed',str(plan['action_seed']),'--audit-substeps']
 jobs=[]
 for shard,cpu in enumerate(plan['physics_cpus']):
  cases=plan['case_ids'][shard::2];output=OUT/f'shard{shard}';cmd=['taskset','-c','52-54',*common,'--physics-cpu',str(cpu),'--output',str(output)]
  for case in cases:cmd+=['--case-id',case]
  jobs.append(dict(command=cmd,output=str(output),case_ids=cases))
 assert len(set(jobs[0]['case_ids'])|set(jobs[1]['case_ids']))==30 and not set(jobs[0]['case_ids'])&set(jobs[1]['case_ids'])
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 check=['taskset','-c','52-54',*common,'--physics-cpu','53','--output',str(OUT/'check_only'),'--check-only']
 with (OUT/'check_only.log').open('x') as log:subprocess.run(check,check=True,timeout=600,stdout=log,stderr=subprocess.STDOUT,env=env)
 assert json.loads((OUT/'check_only/CHECK_ONLY_REVIEW.json').read_text())['passed']
 write(OUT/'COMMANDS.json',dict(jobs=jobs));write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),plan_sha256=PLAN_SHA,new_physics=0,optimizer_updates=0,automatic_evaluation=False))
 print('Actual complete26 restored; inspect before fixed30 physical launch.',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as error:
  write(OUT/'PREPARATION_FAILURE.json',dict(error=repr(error),time=time.time()));raise
'''.replace('__PLAN_SHA__',repr(plan_sha))
launcher='''from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=B/'runs/serl_cycle26_frozen_full30_20261027_v1';RT=B/'runtime'/OUT.name
PLAN_SHA=__PLAN_SHA__
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\\n')
assert sha(OUT/'PLAN.json')==PLAN_SHA
assert json.loads((OUT/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert json.loads((OUT/'PRELAUNCH_REVIEW.json').read_text())['passed']
assert not (OUT/'LAUNCH.json').exists()
# Respect pre-registered CPU53/54 physical-resource ordering.
prior=B/'runs/parameter41_frozen_full30_20261027_v1'
assert json.loads((prior/'REVIEW.json').read_text())['passed']
for job in json.loads((prior/'LAUNCH.json').read_text())['jobs']:assert not Path(f"/proc/{job['pid']}").exists()
assert not Path(f"/proc/{json.loads((prior/'REVIEW_LAUNCH.json').read_text())['pid']}").exists()
plan=json.loads((OUT/'PLAN.json').read_text())
for n,h in plan['source_hashes'].items():assert sha(RT/n)==h
reg=json.loads((OUT/'REGISTRATION.json').read_text())
for item in reg['inputs'].values():assert sha(item['path'])==item['sha256']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
jobs=[]
for i,job in enumerate(json.loads((OUT/'COMMANDS.json').read_text())['jobs']):
 with (OUT/f'shard{i}.log').open('x') as log:p=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(**job,pid=p.pid,start=start,time=time.time()))
write(OUT/'LAUNCH.json',dict(jobs=jobs))
with (OUT/'review.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(RT/'review_serl26_frozen_matrix_20261027.py'),'--root',str(OUT)],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(OUT/'REVIEW_LAUNCH.json',dict(pid=p.pid,time=time.time()));print(dict(evaluators=[j['pid'] for j in jobs],review=p.pid),flush=True)
'''.replace('__PLAN_SHA__',repr(plan_sha))
for name,s in [('prepare_serl26_frozen_full30_20261027.py',prepare),('launch_serl26_frozen_full30_20261027.py',launcher)]:ast.parse(s);(B/'runtime'/name).write_text(s)
for name in ['evaluate_serl_capacity_frozen_20261027.py','review_serl26_frozen_matrix_20261027.py']:subprocess.run([str(B/'serl_env/bin/python'),str(RT/name),'--help'],check=True,stdout=subprocess.DEVNULL)
write(OUT/'STATIC_REVIEW.json',dict(passed=True,time=time.time(),plan_sha256=plan_sha,actual24_restore_only_validation=ref(validation/'VALIDATION_REVIEW.json'),all30_same_conditions_and_seed_as_frozen16=True,source_files=len(sources),learner_adapter_and_capacity_helpers_unchanged=True,exact26_and_historical_entry23=True,finite_budget_actions=41250,finite_budget_physical_substeps=33000000,physical_resources_ordered_after_frozen41=True,actual26_restore=False,physical_evaluation_launched=False))
with (OUT/'preparation.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(B/'runtime/prepare_serl26_frozen_full30_20261027.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
write(OUT/'PREPARATION_LAUNCH.json',dict(pid=p.pid,time=time.time(),source_sha256=sha(B/'runtime/prepare_serl26_frozen_full30_20261027.py'),plan_sha256=plan_sha,wait_seconds=10800,automatic_evaluation=False));print('Direct26 frozen preparation waiter',p.pid,'plan',plan_sha)
