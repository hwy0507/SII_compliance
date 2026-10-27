from pathlib import Path
import ast,hashlib,json,os,shutil,subprocess,sys,time
O=Path(__file__).parent;B=O.parents[1];R=B/'repository/SII_compliance'
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
try:
 review=B/'runs/serl_take_cycle29_review_20261027_v1';limit=time.monotonic()+7200
 while not (review/'FINISHED.json').exists():
  assert time.monotonic()<limit,'Bounded complete29 wait expired'
  assert not (B/'runs/serl_take_cycle29_20261027_v1/DRIVER_FAILURE.json').exists()
  time.sleep(5)
 assert json.loads((review/'FINISHED.json').read_text())['completed']
 assert json.loads((review/'REVIEW.json').read_text())['passed']
 assert not Path('/proc/241542').exists(),'Parent learner must exit before CPU0 restore check'
 parent=B/'runs/serl_take_cycle29_20261027_v1';reg=json.loads((parent/'REGISTRATION.json').read_text())
 name='serl_take_cycle30_20261027_v1';out=B/'runs'/name;rt=B/'runtime'/name
 static=json.loads((O/'STATIC_REVIEW.json').read_text());driver='resume_serl_take_recovery_continuation_20261027.py';gather='serl_replay_take_gather_20261027.py'
 assert sha(R/'code/mujoco_6d_vmc_benchmark/tools'/driver)==static['driver_sha256']
 out.mkdir();shutil.copytree(Path(reg['recovery_continuation_stage']['runtime']),rt,ignore=shutil.ignore_patterns('__pycache__'))
 for n in [driver,gather]:shutil.copyfile(R/'code/mujoco_6d_vmc_benchmark/tools'/n,rt/n)
 gate=B/'runs/serl_take_gather_gate_20261027_v1';gp=json.loads((gate/'PLAN.json').read_text())
 checkpoint=B/'runs/serl_take_cycle29_archive_20261027_v1/direct/cycle_00029.pt'
 reg['recovery_continuation_stage']=dict(parent_cycle=29,new_cycle=30,new_cycles=1,maximum_new_actions=41250,maximum_physical_substeps=33000000,automatic_followup=False,auxiliary_weights_imported=False,optimizer_settings_changed=False,quarantined_pending=930,active_streams=list(range(30,60)),parent_registration=ref(parent/'REGISTRATION.json'),checkpoint=ref(checkpoint),cycle_review=ref(review/'REVIEW.json'),health_review=ref(review/'DIAGNOSIS.json'),gather_gate=ref(gate/'REVIEW.json'),gather_saved_review=ref(gate/'SAVED_REVIEW.json'),gather_sha256=sha(rt/gather),driver_sha256=sha(rt/driver),runtime=str(rt),sample_source_sha256=gp['sample_source_sha256'],patched_main_sha256=static['patched_main_sha256'],source_hashes={p.name:sha(p) for p in rt.glob('*.py')},reason='One finite complete29->30 with equivalent take gather; preserve all learner/replay/history and original interrupted25 quarantine; no changed algorithm or auxiliary weights.')
 write(out/'REGISTRATION.json',reg)
 cmd=json.loads((parent/'COMMAND.json').read_text())['command'];cmd[1]=str(rt/driver)
 for flag,value in [('--registration',out/'REGISTRATION.json'),('--resume',checkpoint),('--output',out/'direct')]:cmd[cmd.index(flag)+1]=str(value)
 write(out/'COMMAND.json',dict(command=cmd))
 env=dict(os.environ,CUDA_VISIBLE_DEVICES='0',JAX_PLATFORMS='cuda',XLA_PYTHON_CLIENT_PREALLOCATE='false',JAX_COMPILATION_CACHE_DIR=str(B/'runtime/jax_compilation_cache'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 with (out/'check_only.log').open('x') as f:result=subprocess.run(cmd+['--check-only'],stdout=f,stderr=subprocess.STDOUT,env=env,timeout=900)
 write(O/'CHECK_ONLY_EXIT.json',dict(time=time.time(),returncode=result.returncode,automatic_training=False))
 assert result.returncode==0
 write(O/'FINISHED.json',dict(time=time.time(),prepared=True,formal_deployment=False,automatic_training=False))
except BaseException as e:
 write(O/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
