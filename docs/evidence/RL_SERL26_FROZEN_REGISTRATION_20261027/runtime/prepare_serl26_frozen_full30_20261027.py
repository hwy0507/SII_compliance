from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');OUT=B/'runs/serl_cycle26_frozen_full30_20261027_v1';RT=B/'runtime'/OUT.name
PLAN_SHA='72882a42d0a32a3414363e8f8163f1d7169bb92f10ec8254ffe59e3dd65bf896'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
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
