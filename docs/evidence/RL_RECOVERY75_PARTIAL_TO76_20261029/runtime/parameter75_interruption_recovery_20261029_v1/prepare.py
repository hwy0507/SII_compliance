from pathlib import Path
import json,time,hashlib,importlib.util,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1';AUD=B/'runs/parameter75_interruption_recovery_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';RT=B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
assert read(AUD/'REVIEW.json')['passed'];OUT.mkdir(exist_ok=False)
spec=importlib.util.spec_from_file_location('recovery',D/'resume_partial75.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
jobs=[]
for job in read(OLD/'LAUNCH.json')['jobs']:
 m=job['controller'];dest=OUT/m;dest.mkdir();p=read(OLD/m/'REGISTRATION.json');review=read(AUD/m/'REVIEW.json');trainer=OLD/m/'trainer_registered.py'
 p['interrupted_episode_recovery']=dict(version=1,parent_cycle=75,new_cycle=76,new_cycles=1,parent_steps=review['steps'],parent_registration=ref(OLD/m/'REGISTRATION.json'),checkpoint=ref(Path(review['checkpoint'])),partial_audit=ref(AUD/m/'REVIEW.json'),driver_sha256=sha(D/'resume_partial75.py'),original_runtime=str(RT),source_hashes=p['batch_size_stage']['dependency_hashes'],trainer_path=str(trainer),trainer_sha256=sha(trainer),patched_trainer_sha256=hashlib.sha256(module.transform(trainer.read_text()).encode()).hexdigest(),maximum_new_actions=41250,environment_state_saved=False,old_window_continuity_claim=False,automatic_followup=False,optimizer_settings_changed=False,physical_semantics='Start30 fresh physical episodes after exact full learner/replay restore. Interrupted75 retained as partial; no fabricated terminal, no rollback, no full75 reward. New complete76 is additional exposure.')
 write(dest/'REGISTRATION.json',p)
 cmd=list(job['command']);cmd[1]=str(D/'resume_partial75.py')
 for flag,val in [('--registration',dest/'REGISTRATION.json'),('--resume',Path(review['checkpoint'])),('--output',dest/'train')]:cmd[cmd.index(flag)+1]=str(val)
 jobs.append(dict(controller=m,command=cmd))
write(OUT/'COMMANDS.json',dict(time=time.time(),jobs=jobs,automatic_training=False))
status={};procs={};env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
for j in jobs:
 m=j['controller'];f=(OUT/m/'check_only.log').open('x');procs[m]=subprocess.Popen(j['command']+['--check-only'],stdout=f,stderr=subprocess.STDOUT,env=env);f.close()
for m,p in procs.items():status[m]=p.wait()
write(OUT/'CHECK_ONLY_EXIT_CODES.json',status);assert all(v==0 for v in status.values()),status
write(OUT/'CHECK_ONLY_COMPLETE.json',dict(passed=True,time=time.time(),optimizer_updates=0,new_physics=0));print('All exact partial75 restore checks passed',flush=True)
