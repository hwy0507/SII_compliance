from pathlib import Path
import json,time,hashlib,os,subprocess
B=Path(__file__).resolve().parents[2];O=B/'runs/parameter82_frozen_full30_20261030_v1';D=B/'runtime/parameter82_frozen_full30_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert not (O/'LAUNCH.json').exists();plan=read(O/'PLAN.json');check=read(O/'CHECK_ONLY_COMPLETE.json');assert check['passed'] and check['plan_sha256']==sha(O/'PLAN.json')
assert all(c==0 for c in read(O/'CHECK_ONLY_EXIT_CODES.json').values())
assert all(not live(j) for j in read(O/'CHECK_ONLY_LAUNCH.json')['jobs'])
assert sha(O/'PRE_REGISTRATION.json')=='baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76'
assert plan['case_ids']==read(O/'PRE_REGISTRATION.json')['case_ids'] and plan['episodes']==90 and plan['maximum_actions']==123750 and plan['maximum_substeps']==99000000
for n,h in plan['source_hashes'].items():assert sha(D/n)==h
assert read(B/'runs/parameter_partial75_recovery_cycle82_review_20261029_v1/REVIEW.json')['passed']
assert read(B/'runs/parameter_recovery82_loss_20261029_v1/SAVED_REVIEW.json')['passed']
assert read(B/'runs/parameter_recovery82_loss_20261029_v1/PAIRED_GATE_REVIEW.json')['passed']
for p in Path('/proc').glob('[0-9]*/cmdline'):
 try:args=p.read_bytes().split(b'\0')
 except (FileNotFoundError,ProcessLookupError):continue
 assert str(D/'evaluate_parameter82_frozen_full30_20261030.py').encode() not in args,'Duplicate frozen82 evaluator'
alloc=[]
for j in read(B/'runs/parameter_partial75_recovery_cycle83_20261029_v1/LAUNCH.json')['jobs']:
 assert live(j);cpus=os.sched_getaffinity(j['pid']);assert not cpus.intersection({0,1,2,3});alloc.append(dict(pid=j['pid'],cpus=sorted(cpus)))
assert live(dict(pid=97370,proc_start_ticks='570509460'))
resources=subprocess.check_output(['nvidia-smi','--query-gpu=index,uuid,utilization.gpu,memory.used,memory.free','--format=csv,noheader'],text=True)
assert int(resources.splitlines()[0].split(',')[-1].strip().split()[0])>12000
mem={l.split(':')[0]:int(l.split()[1]) for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemAvailable:','SwapTotal:'))};assert mem['MemAvailable']>24*1024*1024
commands=read(O/'COMMANDS.json')['jobs'];assert len(commands)==3
for j in commands:
 reg=read(O/j['controller']/'REGISTRATION.json');r=read(O/j['controller']/'CHECK_ONLY_REVIEW.json')
 assert r['passed'] and r['full_learner_state_unchanged'] and r['full_replay_restored_exact'] and r['native_vs_external_three_actions_exact'] and r['same_seed_exact'] and r['different_seed_changes_raw_action'] and r['negative_seed_guards']==2
 assert reg['parent_cycle']==82 and reg['cpu']==plan['cpu_mapping'][j['controller']] and reg['device']=='cuda:0' and reg['action_seed']==2026102638 and reg['case_ids']==plan['case_ids']
 assert sha(reg['checkpoint'])==reg['checkpoint_sha256']==r['checkpoint_sha256']
put(O/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),parent_cycle=82,plan=ref(O/'PLAN.json'),check_only=ref(O/'CHECK_ONLY_COMPLETE.json'),sources=ref(D/'SOURCE_REVIEW.json'),no_duplicate_evaluator=True,training83_allocations=alloc,resources=resources,memory_kib=mem,maximum_episodes=90,optimizer_updates=0,automatic_extension=False))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0,1,2,3',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=[]
for j in commands:
 with (O/j['controller']/'driver.log').open('x') as f:p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
 jobs.append(dict(j,pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time()))
 put(O/(j['controller']+'_LAUNCH.json'),jobs[-1])
put(O/'LAUNCH.json',dict(time=time.time(),jobs=jobs,all_spawned=True))
script=D/'review_parameter82_frozen_full30_20261030.py';put(O/'REVIEW_REGISTRATION.json',dict(evaluators=jobs,source_sha256=sha(script),plan_sha256=sha(O/'PLAN.json'),time=time.time(),maximum_wait_seconds=21600))
with (O/'review.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(script),'--root',str(O)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True)
put(O/'REVIEW_LAUNCH.json',dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time()))
print('Frozen82 finite90 evaluators and full reviewer launched',[(j['controller'],j['pid']) for j in jobs])
