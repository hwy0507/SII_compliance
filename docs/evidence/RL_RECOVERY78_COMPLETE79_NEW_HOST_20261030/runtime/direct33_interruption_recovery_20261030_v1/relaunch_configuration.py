from pathlib import Path
import json,os,subprocess,time,hashlib,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runs/serl_take33_frozen_remaining2_20261030_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v2'
def read(p):return json.loads(p.read_text())
def put(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
# Failed preflight attempts must have no physics or successful restore receipts.
for p in OLD.glob('shard*'):
 if p.is_dir():assert not list(p.rglob('actor_intervals.jsonl')) and not (p/'FULL_STATE_RESTORE.json').exists()
for j in read(OLD/'LAUNCH.json')['jobs']+[read(OLD/'REPLAY_LAUNCH.json')]:
 p=Path(f'/proc/{j["pid"]}/stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split();assert s[19]!=j['start'] or s[0]=='Z'
O.mkdir(exist_ok=False);(O/'PLAN.json').write_bytes((OLD/'PLAN.json').read_bytes())
env_overrides=dict(CUDA_VISIBLE_DEVICES='0',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XLA_PYTHON_CLIENT_PREALLOCATE='false');env=dict(os.environ,**env_overrides)
put(O/'CONFIGURATION_REPAIR.json',dict(time=time.time(),prior=str(OLD),prior_failures=[ref(OLD/x) for x in ['shard0.log','shard1.log','saved28_replay.log','COMBINED_REVIEW_FAILURE.json']],reason='Initial attempts exited before physics: missing one-GPU visibility, and mistaken taskset argument replacement. Preserve all originals. Same evaluator and registered physics; only GPU environment and executable-index selection corrected.',prior_new_physics=0,environment=env_overrides,source=ref(Path(__file__))))
jobs=read(OLD/'COMMANDS.json')['jobs']
for i,j in enumerate(jobs):
 cmd=j['command'];j['output']=str(O/f'shard{i}');cmd[cmd.index('--output')+1]=j['output']
put(O/'COMMANDS.json',dict(jobs=jobs))
def launch(cmd,log):
 with log.open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=env)
 return dict(pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),command=cmd)
for i,j in enumerate(jobs):j.update(launch(j['command'],O/f'shard{i}.log'))
put(O/'LAUNCH.json',dict(time=time.time(),jobs=jobs,environment=env_overrides))
cmd=list(jobs[0]['command']);oldscript=str(B/'runtime/serl_take33_frozen_full30_20261029_v1/evaluate_serl33_frozen_20261029.py');assert cmd[4]==oldscript;cmd[4]=str(D/'replay_runtime/evaluate_replay28.py');cmd[cmd.index('--output')+1]=str(O/'saved28_replay');cmd+=['--check-only']
put(O/'REPLAY_LAUNCH.json',launch(cmd,O/'saved28_replay.log'))
s=(D/'review_combined.py').read_text().replace('serl_take33_frozen_remaining2_20261030_v1','serl_take33_frozen_remaining2_20261030_v2');ast.parse(s);script=D/'review_combined_v2.py';script.write_text(s)
plan=read(OLD/'COMBINED_REVIEW_PLAN.json');plan['time']=time.time();plan['sources'][0]=ref(script);plan['inputs']=[ref(O/x) for x in ['PLAN.json','LAUNCH.json','REPLAY_LAUNCH.json']];put(O/'COMBINED_REVIEW_PLAN.json',plan)
put(O/'COMBINED_REVIEW_LAUNCH.json',launch([str(B/'env/bin/python'),str(script)],O/'combined_review.log'))
print(json.dumps(dict(output=str(O),jobs=jobs,replay=read(O/'REPLAY_LAUNCH.json')),indent=2))
