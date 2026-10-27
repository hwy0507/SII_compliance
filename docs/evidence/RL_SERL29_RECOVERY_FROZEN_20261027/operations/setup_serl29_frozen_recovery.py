from pathlib import Path
import json,hashlib,shutil,time,ast,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';O=B/'runs/serl_take29_frozen_full30_20261027_v1';V=B/'runs/serl_recovery_frozen_preparation_20261027_v1';RT=B/'runtime'/V.name

def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
assert json.loads((V/'RESTORE_FINISHED.json').read_text())['passed']
check=json.loads((V/'restore27_v1/CHECK_ONLY_REVIEW.json').read_text());assert check['passed'] and check['cycle']==27 and check['recovery_state']['quarantined_pending']==930
plan=json.loads((O/'PLAN.json').read_text());assert plan['cycle']==29 and plan['action_seed']==2026102626
manifest=json.loads((V/'SOURCE_MANIFEST.json').read_text())
for name,expected in manifest.items():assert sha(RT/name)==expected
write(O/'SOURCE_FREEZE.json',dict(time=time.time(),plan=ref(O/'PLAN.json'),evaluation_runtime=str(RT),source_hashes=manifest,actual27_restore=ref(V/'RESTORE_FINISHED.json'),restore_review=ref(V/'restore27_v1/FULL_STATE_RESTORE.json'),rng_gate=ref(V/'restore27_v1/EXTERNAL_ACTION_RNG_GATE.json'),static_review=ref(V/'STATIC_REVIEW.json'),actual29_restore=False,preparation_wait_seconds=10800,automatic_evaluation=False))
PLAN_SHA=sha(O/'PLAN.json');FREEZE_SHA=sha(O/'SOURCE_FREEZE.json')
prepare='''from pathlib import Path
import json,hashlib,time,subprocess,os
O=Path(__file__).parent;B=O.parents[1];PLAN_SHA=__PLAN_SHA__;FREEZE_SHA=__FREEZE_SHA__
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\\n')
def main():
 os.sched_setaffinity(0,{52});assert sha(O/'PLAN.json')==PLAN_SHA and sha(O/'SOURCE_FREEZE.json')==FREEZE_SHA
 plan=json.loads((O/'PLAN.json').read_text());freeze=json.loads((O/'SOURCE_FREEZE.json').read_text());rt=Path(freeze['evaluation_runtime'])
 for name,expected in freeze['source_hashes'].items():assert sha(rt/name)==expected
 for key in ['actual27_restore','restore_review','rng_gate','static_review']:
  item=freeze[key];assert sha(item['path'])==item['sha256'] and json.loads(Path(item['path']).read_text())['passed']
 for key in ['comparison_frozen16_review','comparison_frozen16_registration','stability_window']:
  item=plan[key];assert sha(item['path'])==item['sha256']
 review=B/'runs/serl_take_cycle29_review_20261027_v1';deadline=time.monotonic()+freeze['preparation_wait_seconds']
 while not (review/'FINISHED.json').exists():
  assert time.monotonic()<deadline,'Bounded complete29 wait expired; no automatic retry/extension'
  assert not (B/'runs/serl_take_cycle29_20261027_v1/direct/FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((review/'FINISHED.json').read_text())['completed'];full=json.loads((review/'REVIEW.json').read_text());assert full['passed']
 parent=Path(plan['future_training_registration_path']);protocol=json.loads(parent.read_text());checkpoint=Path(plan['future_checkpoint_path'])
 assert protocol['conditions']==plan['conditions'] and protocol['recovery_continuation_stage']['new_cycle']==29
 assert protocol['interrupted_stream_recovery']==json.loads(Path(plan['current28_registration']['path']).read_text())['interrupted_stream_recovery']
 assert sha(checkpoint)==full['methods']['direct']['checkpoint_sha256']
 reg={k:plan[k] for k in ['cycle','action_seed','noise_schedule','maximum_episodes','maximum_physical_substeps','physics_cpus','learner_cpu','inference_gpu','optimizer_updates','replay_writes','training_conditions_only','convergence_claim']}
 reg.update(evaluation_runtime=str(rt),inputs=dict(plan=ref(O/'PLAN.json'),source_freeze=ref(O/'SOURCE_FREEZE.json'),training_registration=ref(parent),checkpoint=ref(checkpoint),cycle_review=ref(review/'REVIEW.json'),health_review=ref(review/'DIAGNOSIS.json'),finished=ref(review/'FINISHED.json')),sources={n:dict(path=str(rt/n),sha256=h) for n,h in freeze['source_hashes'].items()})
 write(O/'REGISTRATION.json',reg)
 common=[str(B/'serl_env/bin/python'),str(rt/'evaluate_serl_recovery_frozen_20261027.py'),'--runtime',protocol['runtime'],'--registration',str(parent),'--checkpoint',str(checkpoint),'--expected-cycle','29','--device','cuda:0','--learner-cpu','52','--serl-upstream',str(B/'runtime/serl_upstream_1fa2af7'),'--serl-manifest',str(B/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json'),'--sampler-python',str(B/'env/bin/python'),'--stochastic','--action-seed',str(plan['action_seed']),'--audit-substeps']
 jobs=[]
 for shard,cpu in enumerate(plan['physics_cpus']):
  cases=plan['case_ids'][shard::2];output=O/f'shard{shard}';cmd=['taskset','-c','52-54',*common,'--physics-cpu',str(cpu),'--output',str(output)]
  for case in cases:cmd+=['--case-id',case]
  jobs.append(dict(command=cmd,output=str(output),case_ids=cases))
 assert len(jobs[0]['case_ids'])==len(jobs[1]['case_ids'])==15
 assert set(jobs[0]['case_ids'])|set(jobs[1]['case_ids'])==set(plan['case_ids']) and not set(jobs[0]['case_ids'])&set(jobs[1]['case_ids'])
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 check=['taskset','-c','52-54',*common,'--physics-cpu','53','--output',str(O/'check_only'),'--check-only']
 with (O/'check_only.log').open('x') as log:subprocess.run(check,check=True,timeout=plan['check_only_timeout_seconds'],stdout=log,stderr=subprocess.STDOUT,env=env)
 result=json.loads((O/'check_only/CHECK_ONLY_REVIEW.json').read_text());assert result['passed'] and result['cycle']==29 and result['recovery_state']['quarantined_pending']==930
 write(O/'COMMANDS.json',dict(jobs=jobs));write(O/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),plan_sha256=PLAN_SHA,source_freeze_sha256=FREEZE_SHA,new_physics=0,optimizer_updates=0,automatic_evaluation=False));print('Actual29 recovery-aware restore passed; inspect before frozen physical launch.',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:write(O/'PREPARATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
'''.replace('__PLAN_SHA__',repr(PLAN_SHA)).replace('__FREEZE_SHA__',repr(FREEZE_SHA))
launcher='''from pathlib import Path
import json,hashlib,time,subprocess,os
O=Path(__file__).parent;B=O.parents[1];PLAN_SHA=__PLAN_SHA__;FREEZE_SHA=__FREEZE_SHA__
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\\n')
assert sha(O/'PLAN.json')==PLAN_SHA and sha(O/'SOURCE_FREEZE.json')==FREEZE_SHA
assert json.loads((O/'CHECK_ONLY_COMPLETE.json').read_text())['passed']
assert json.loads((O/'PRELAUNCH_REVIEW.json').read_text())['passed']
assert not (O/'LAUNCH.json').exists()
prior=B/'runs/parameter41_frozen_full30_20261027_v1'
assert json.loads((prior/'REVIEW.json').read_text())['passed']
for job in json.loads((prior/'LAUNCH.json').read_text())['jobs']:assert not Path(f"/proc/{job['pid']}").exists()
assert not Path(f"/proc/{json.loads((prior/'REVIEW_LAUNCH.json').read_text())['pid']}").exists()
freeze=json.loads((O/'SOURCE_FREEZE.json').read_text());rt=Path(freeze['evaluation_runtime'])
for n,h in freeze['source_hashes'].items():assert sha(rt/n)==h
reg=json.loads((O/'REGISTRATION.json').read_text())
for item in reg['inputs'].values():assert sha(item['path'])==item['sha256']
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
jobs=[]
for i,job in enumerate(json.loads((O/'COMMANDS.json').read_text())['jobs']):
 with (O/f'shard{i}.log').open('x') as log:p=subprocess.Popen(job['command'],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19];jobs.append(dict(**job,pid=p.pid,start=start,time=time.time()))
write(O/'LAUNCH.json',dict(jobs=jobs))
with (O/'review.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(rt/'review_serl29_recovery_frozen_matrix_20261027.py'),'--root',str(O)],stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True)
write(O/'REVIEW_LAUNCH.json',dict(pid=p.pid,time=time.time()));print(dict(evaluators=[j['pid'] for j in jobs],review=p.pid),flush=True)
'''.replace('__PLAN_SHA__',repr(PLAN_SHA)).replace('__FREEZE_SHA__',repr(FREEZE_SHA))
for name,s in [('prepare.py',prepare),('launch.py',launcher)]:ast.parse(s);(O/name).write_text(s)
# Publish the root-review source as well, keeping the frozen runtime bytes exact.
shutil.copyfile(RT/'review_serl29_recovery_frozen_matrix_20261027.py',R/'code/mujoco_6d_vmc_benchmark/tools/review_serl29_recovery_frozen_matrix_20261027.py')
write(O/'PREPARATION_STATIC_REVIEW.json',dict(passed=True,time=time.time(),plan_sha256=PLAN_SHA,source_freeze_sha256=FREEZE_SHA,actual27_restore=True,actual29_restore=False,complete29_only=True,original930_quarantine_required=True,physical_after_frozen41=True,full30_two_shards_of15=True,automatic_evaluation=False,preparation_source_sha256=sha(O/'prepare.py'),launcher_source_sha256=sha(O/'launch.py')))
with (O/'preparation.log').open('x') as log:p=subprocess.Popen([str(B/'env/bin/python'),str(O/'prepare.py')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
write(O/'PREPARATION_LAUNCH.json',dict(pid=p.pid,time=time.time(),command=[str(B/'env/bin/python'),str(O/'prepare.py')],wait_seconds=10800,check_only_timeout_seconds=600,automatic_evaluation=False));print('Frozen29 actual-check-only waiter',p.pid)
