from pathlib import Path
import json,math,time,hashlib
p=Path(__file__).parent
def read(x):return json.loads(x.read_text())
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
f=read(p/'FINISHED.json');assert f['completed'] and not f['science_restarted']
s=list(map(json.loads,(p/'SAMPLES.jsonl').read_text().splitlines()));assert len(s)==f['samples'] and [x['index'] for x in s]==list(range(len(s)))
assert all(a['time']<b['time'] for a,b in zip(s,s[1:]));assert all(all(v['live'] and not v['failure'] and v['finished'] is None for v in x['learners']) for x in s)
assert all(all(v['live'] for v in x['watchers'].values()) for x in s)
assert all(a['learners'][i]['progress']['steps']<b['learners'][i]['progress']['steps'] for a,b in zip(s,s[1:]) for i in range(3))
guard=[]
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as source:
 for line in source:
  x=json.loads(line)
  if s[0]['time']<=x['time']<=s[-1]['time']:guard.append(x)
assert len(guard)>1
(p/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in guard));g={}
for i in range(4):
 values=[next(v['utilization'] for v in x['gpus'] if v['gpu']==i) for x in guard];assert all(math.isfinite(x) for x in values)
 g[str(i)]=dict(minimum=min(values),mean=math.fsum(values)/len(values),below50=sum(v<50 for v in values))
gr=dict(samples=len(guard),first_time=guard[0]['time'],last_time=guard[-1]['time'],max_gap_seconds=max(b['time']-a['time'] for a,b in zip(guard,guard[1:])),gpus=g,synthetic_guard_included=True,per_instant_guarantee=False)
(p/'GUARD_REVIEW.json').write_text(json.dumps(gr,indent=2)+'\n')
r=dict(time=time.time(),passed=True,samples=len(s),first_time=s[0]['time'],last_time=s[-1]['time'],first_steps=[v['progress']['steps'] for v in s[0]['learners']],last_steps=[v['progress']['steps'] for v in s[-1]['learners']],all_original_identities_live=True,all_steps_strictly_increased=True,no_finished_or_failure=True,observer_finished=True,scientific_completion=False,science_restarted=False,source_sha256=sha(Path(__file__)),samples_sha256=sha(p/'SAMPLES.jsonl'))
(p/'REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(observer=r,guard=gr),indent=2))
