"""Read every complete condition; audit all shortened/aborted journals without fixed failure selection."""
from pathlib import Path
import argparse,json,hashlib,math,time
p=argparse.ArgumentParser();p.add_argument('--cycle',type=int,required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
read=lambda p:json.loads(p.read_text())
def ref(p):return dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
full=read(a.review/'REVIEW.json');assert full['passed'] and read(a.review/'FINISHED.json')['completed'];a.output.mkdir();methods={};sources=[ref(a.review/'REVIEW.json'),ref(a.review/'FINISHED.json')]
for m,review in full['methods'].items():
 reg=read(a.run/m/'REGISTRATION.json');train=a.run/m/'train';eps=[json.loads(l) for l in (train/'episodes.jsonl').read_text().splitlines()];eps=[e for e in eps if e['cycle']==a.cycle];episodes={e['condition']:e for e in eps};cases=[c['id'] for c in reg['conditions']];assert len(eps)==len(episodes)==len(cases)==30 and set(episodes)==set(cases)
 assert sum(e['steps'] for e in eps)==review['new_transitions'];aborted=[];conditions=[]
 for c in cases:
  folder=train/f'cycle_{a.cycle:05d}'/c;x=read(folder/'rollout.json');term=read(folder/'TERMINAL.json');e=episodes[c];n=e['steps']
  assert n==x['baseline_policy']['actions'] and 0<n<=1375
  for k in ['task_success','strict_success','abort_reason','full_task_horizon_completed','physical_valid','final_task_stage']:assert x[k]==term['result'][k]
  assert x['abort_reason']==e['abort_reason'];assert x['model_sha256']==term['model_sha256']==e['model_sha256'];assert math.isclose(term['terminal_time_s'],n*.04,abs_tol=1e-7)
  if x['full_task_horizon_completed']:assert n==1375
  conditions.append(dict(condition=c,actions=n,terminal_time_s=term['terminal_time_s'],full_horizon=x['full_task_horizon_completed'],abort=x['abort_reason'],task=x['task_success'],strict=x['strict_success'],global_peak_mm=x['stats']['max_penetration_m']*1000,external_peak_mm=x['stats']['max_external_penetration_m']*1000,model_sha256=x['model_sha256']))
  sources.extend([ref(folder/'rollout.json'),ref(folder/'TERMINAL.json')])
  if x['abort_reason'] or not x['full_task_horizon_completed']:aborted.append(c)
 rows={c:[] for c in aborted}
 if rows:
  with (train/'transitions.jsonl').open() as f:
   for line in f:
    assert line.endswith('\n');r=json.loads(line)
    if r['cycle']==a.cycle and r['condition'] in rows:rows[r['condition']].append(r)
 failures=[]
 for c in aborted:
  folder=train/f'cycle_{a.cycle:05d}'/c;x=read(folder/'rollout.json');term=read(folder/'TERMINAL.json');e=episodes[c];rs=rows[c];intervals=[json.loads(s) for s in (folder/'actor_intervals.jsonl').read_text().splitlines()]
  assert len(rs)==len(intervals)==e['steps'];assert sum(r['done'] for r in rs)==1 and rs[-1]['done'];assert math.isclose(math.fsum(r['reward'] for r in rs),e['reward'],abs_tol=1e-10)
  current=intervals[-1]['interval']['external_penetration_peak_m'];nxt=term['interval']['external_penetration_peak_m'];out=a.output/(m+'_'+c+'_transitions.json');put(out,dict(episode=e,rows=rs,source=str(train/'transitions.jsonl')));sources.extend([ref(out),ref(folder/'actor_intervals.jsonl')])
  failures.append(dict(condition=c,actions=len(rs),reward=e['reward'],terminal_time_s=term['terminal_time_s'],abort=x['abort_reason'],task=x['task_success'],strict=x['strict_success'],global_peak_mm=x['stats']['max_penetration_m']*1000,external_peak_mm=x['stats']['max_external_penetration_m']*1000,worst_global_pair=x['stats']['worst_pair'],last_current_terminal_external_bits=[int(current>.0002),int(nxt>.0002)]))
 assert sum(x['full_horizon'] for x in conditions)==review['full_horizon_count'];assert sum(x['task'] for x in conditions)==review['task'] and sum(x['strict'] for x in conditions)==review['strict']
 methods[m]=dict(conditions=conditions,shortened_or_aborted=failures,new_transitions=sum(e['steps'] for e in eps));sources.extend([ref(a.run/m/'REGISTRATION.json'),ref(train/'episodes.jsonl')])
put(a.output/'REVIEW.json',dict(passed=True,time=time.time(),cycle=a.cycle,methods=methods,sources=sources,source=ref(Path(__file__)),optimizer_updates=0,new_physics=0,scope='All90 saved condition outcomes and durations; all actual shortened/aborted journals audited. No independent dynamics replay or new checkpoint replay assertion.'))
print(json.dumps({m:v['shortened_or_aborted'] for m,v in methods.items()},indent=2))
