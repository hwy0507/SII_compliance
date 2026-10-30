from pathlib import Path
import os,json,time,hashlib
os.sched_setaffinity(0,{3})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';F=B/'runs/serl_take33_frozen_full30_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
def read(p):return json.loads(p.read_text())
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
def live(j):
 p=Path('/proc')/str(j['pid'])/'stat'
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split()
 return s[19]==j['proc_start_ticks'] and s[0]!='Z'
parent=B/'runtime/direct33_frozen_operations_20261029_v1/OBSERVATION_PLAN.json';jobs=read(parent)['jobs'];assert len(jobs)==18
put(D/'OBSERVATION_PLAN.json',dict(time=time.time(),parent_path=str(parent),parent_sha256=hashlib.sha256(parent.read_bytes()).hexdigest(),jobs=jobs,samples=11,interval_seconds=30,new_physics=0,new_updates=0,expiry_does_not_restart_science=True))
rows=[];start=time.monotonic()
try:
 with (D/'OBSERVATIONS.jsonl').open('x') as f:
  for i in range(11):
   states=[dict(role=j['role'],pid=j['pid'],live=live(j)) for j in jobs]
   assert all(s['live'] for s in states),states
   for p in [P/'ARCHIVE_REVIEW_FAILURE.json',F/'REVIEW_FAILURE.json',G/'FAILURE.json']+list(P.glob('*/train/FAILURE.json')):assert not p.exists(),str(p)
   guard=read(G/'CONTROL.json');g=json.loads((G/'samples.jsonl').read_text().splitlines()[-1]);assert time.time()-g['time']<20
   progress={m:read(P/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};shards=[]
   for j in read(F/'LAUNCH.json')['jobs']:
    folder=Path(j['output']);assert not (folder/'FAILURE.json').exists();results=read(folder/'RESULTS.json') if (folder/'RESULTS.json').exists() else None
    cases={p.parent.name:read(p) for p in folder.glob('*/rollout.progress.json')}
    shards.append(dict(pid=j['pid'],completed=len(results['episodes']) if results else 0,case_progress=cases))
   row=dict(time=time.time(),states=states,parameter_progress=progress,frozen_shards=shards,guard=g);rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
   print(json.dumps(dict(sample=i,steps={m:v['steps'] for m,v in progress.items()},frozen_completed=sum(v['completed'] for v in shards),gpu=[x['utilization'] for x in g['gpus']])),flush=True)
   if i<10:time.sleep(max(0,start+30*(i+1)-time.monotonic()))
 put(D/'OBSERVATION_FINISHED.json',dict(time=time.time(),passed=True,samples=len(rows),elapsed=time.monotonic()-start,original_identities=len(jobs),all_original_identities_live=True,first=rows[0],last=rows[-1],scientific_restart=False))
except BaseException as e:
 put(D/'OBSERVATION_FAILURE.json',dict(time=time.time(),error=repr(e),scientific_restart=False));raise
