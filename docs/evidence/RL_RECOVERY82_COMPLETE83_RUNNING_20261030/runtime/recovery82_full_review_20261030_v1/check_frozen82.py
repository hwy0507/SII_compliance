from pathlib import Path
import json,time,hashlib,os,subprocess
B=Path(__file__).resolve().parents[2];O=B/'runs/parameter82_frozen_full30_20261030_v1';D=B/'runtime/parameter82_frozen_full30_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
os.sched_setaffinity(0,{3});plan=read(O/'PLAN.json');assert not (O/'CHECK_ONLY_LAUNCH.json').exists()
for n,h in plan['source_hashes'].items():assert sha(D/n)==h
for m in plan['controllers']:
 reg=read(O/m/'REGISTRATION.json');assert not (O/m/'EVALUATION.json').exists()
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1,2,3',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');ps=[];jobs=[]
for j in read(O/'COMMANDS.json')['jobs']:
 with (O/j['controller']/'check_only.log').open('x') as f:p=subprocess.Popen(j['command']+['--check-only'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 ps.append((j['controller'],p));jobs.append(dict(j,pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
put(O/'CHECK_ONLY_LAUNCH.json',dict(time=time.time(),jobs=jobs,plan_sha256=sha(O/'PLAN.json')))
start=time.monotonic()
while any(p.poll() is None for _,p in ps):
 assert time.monotonic()-start<600,'Observe original children; no automatic restart'
 time.sleep(2)
codes={m:p.returncode for m,p in ps};put(O/'CHECK_ONLY_EXIT_CODES.json',codes);assert all(x==0 for x in codes.values()),codes
for m in plan['controllers']:
 r=read(O/m/'CHECK_ONLY_REVIEW.json');assert r['passed'] and r['full_replay_restored_exact'] and r['validated_parent_cycle']==82
put(O/'CHECK_ONLY_COMPLETE.json',dict(time=time.time(),passed=True,plan_sha256=sha(O/'PLAN.json'),new_physics=0,new_optimizer_updates=0,automatic_evaluation=False));print('All3 actual82 frozen full learner/replay and external RNG checks passed')
