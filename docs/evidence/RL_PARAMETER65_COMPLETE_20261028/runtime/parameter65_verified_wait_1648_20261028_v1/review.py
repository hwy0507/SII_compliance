from pathlib import Path
import json,time,math,hashlib
p=Path(__file__).parent
def read(p):return json.loads(p.read_text())
s=list(map(json.loads,(p/'SAMPLES.jsonl').read_text().splitlines()));assert read(p/'OBSERVATION_READY.json')['all_required_paths_present'];assert len(s)==29 and [x['index'] for x in s]==list(range(len(s)))
assert all(not x['failures'] for x in s)
assert all(v['live'] or v['finished']['status']=='stopped_at_complete_cycle' for x in s for v in x['learners'])
assert all(all(v['live'] for k,v in x['watchers'].items() if k.startswith('guard')) for x in s)
assert all(a['learners'][i]['progress']['steps']<=b['learners'][i]['progress']['steps'] for a,b in zip(s,s[1:]) for i in range(3));assert all(not x['live'] for x in s[-1]['learners']) and not s[-1]['missing']
g=[]
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as f:
 for line in f:
  x=json.loads(line)
  if s[0]['time']<=x['time']<=s[-1]['time']:g.append(x)
(p/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in g))
a={}
for i in range(4):
 v=[next(t['utilization'] for t in x['gpus'] if t['gpu']==i) for x in g];a[str(i)]=dict(minimum=min(v),mean=math.fsum(v)/len(v),below50=sum(t<50 for t in v))
gr=dict(samples=len(g),first_time=g[0]['time'],last_time=g[-1]['time'],maxgap=max(y['time']-x['time'] for x,y in zip(g,g[1:])),gpus=a,synthetic_guard_included=True,per_instant_guarantee=False);(p/'GUARD_REVIEW.json').write_text(json.dumps(gr,indent=2)+'\n')
r=dict(passed=True,time=time.time(),samples=len(s),first_time=s[0]['time'],last_time=s[-1]['time'],natural_original_learner_completion=True,all_required_paths_present=True,all_guard_identities_live=True,science_restarted=False,first_steps=[x['progress']['steps'] for x in s[0]['learners']],last_steps=[x['progress']['steps'] for x in s[-1]['learners']],scientific_reviews_separate=True);(p/'REVIEW.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(observer=r,guard=gr),indent=2))
