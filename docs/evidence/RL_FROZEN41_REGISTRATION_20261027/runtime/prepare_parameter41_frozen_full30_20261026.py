from pathlib import Path
import json,hashlib,time,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=B/'runs/parameter41_frozen_full30_20261027_v1';RT=B/'runtime'/OUT.name
PLAN_SHA='a541276ae23af43ac253d0bc0d6a3736fd5a601d8ba6d00307f727e3379df83a'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def main():
 os.sched_setaffinity(0,{52})
 assert sha(OUT/'PLAN.json')==PLAN_SHA
 plan=json.loads((OUT/'PLAN.json').read_text())
 for n,h in plan['source_hashes'].items():assert sha(RT/n)==h
 review=B/'runs/parameter_capacity_pool30_cycle41_review_20261026_v1'
 deadline=time.monotonic()+7200
 while not (review/'FINISHED.json').exists():
  assert time.monotonic()<deadline, 'No complete41 within registered wait; retain failure, do not repeat automatically'
  for m in plan['controllers']:
   assert not (B/'runs/parameter_capacity_pool30_cycle41_20261026_v1'/m/'train/FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((review/'FINISHED.json').read_text())['completed']
 complete=json.loads((review/'REVIEW.json').read_text());assert complete['passed']
 commands=[]
 for m in plan['controllers']:
  parent=B/'runs/parameter_capacity_pool30_cycle41_20261026_v1'/m/'REGISTRATION.json';protocol=json.loads(parent.read_text());assert protocol['conditions']==plan['conditions'];assert protocol['replay_capacity_stage']['parent_cycle']==23
  cp=B/'runs/parameter_capacity_pool30_cycle41_archive_20261026_v1'/m/'cycle_00041.pt';assert sha(cp)==complete['methods'][m]['checkpoint_sha256']
  old=B/'runs/parameter29_seeded_short0600_20261026_v1'/m/'REGISTRATION.json';reg=json.loads(old.read_text());reg.pop('case_id');reg.pop('action_seeds')
  gatecase='active_short_train_0600';journal=parent.parent/'train/cycle_00041'/gatecase/'actor_intervals.jsonl'
  reg.update(parent_cycle=41,case_ids=plan['case_ids'],action_seed=plan['action_seed'],gate_case_id=gatecase,gate_observations=str(journal),gate_observations_sha256=sha(journal),audit_runtime=str(RT),checkpoint=str(cp),checkpoint_sha256=sha(cp),training_registration=str(parent),training_registration_sha256=sha(parent),required_review=str(review/'REVIEW.json'),required_review_sha256=sha(review/'REVIEW.json'),source_hashes=plan['source_hashes'])
  assert reg['runtime']==protocol['runtime'];assert reg['cpu']==plan['cpu_mapping'][m] and reg['device']==f"cuda:{plan['gpu_mapping'][m]}"
  dest=OUT/m;dest.mkdir();write(dest/'REGISTRATION.json',reg)
  commands.append(dict(controller=m,command=[str(B/'env/bin/python'),str(RT/'evaluate_parameter41_frozen_full30_20261026.py'),'--registration',str(dest/'REGISTRATION.json')]))
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1,2,3',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
 checks=[]
 for job in commands:
  with (OUT/job['controller']/'check_only.log').open('x') as log:p=subprocess.Popen(job['command']+['--check-only'],stdout=log,stderr=subprocess.STDOUT,env=env)
  checks.append((job['controller'],p))
 codes={m:p.wait() for m,p in checks};write(OUT/'CHECK_ONLY_EXIT_CODES.json',codes);assert all(v==0 for v in codes.values()),codes
 for m in plan['controllers']:assert json.loads((OUT/m/'CHECK_ONLY_REVIEW.json').read_text())['passed']
 write(OUT/'COMMANDS.json',dict(jobs=commands));write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),plan_sha256=PLAN_SHA,new_physics=0,new_optimizer_updates=0,automatic_evaluation=False))
 print('Complete41 frozen full30 preparation only; inspect check-only before launch.',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as e:
  write(OUT/'PREPARATION_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
