from pathlib import Path
import json,time,hashlib,ast,difflib
D=Path(__file__).resolve().parent;B=D.parents[1];I=B/'runtime/history89_violation_interface_20261030_v2';H=B/'runs/history89_raw_history_extension_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read(I/'PLAN.json');h=read(H/'REVIEW.json');assert read(D/'CACHE_SAVED_REVIEW.json')['passed'] and read(D/'CACHE_OBSERVATION_REVIEW.json')['passed']
inputs=[D/'CACHE_PLAN.json',D/'CACHE_SAVED_REVIEW.json',D/'CACHE_OBSERVATION_REVIEW.json',H/'REVIEW.json',I/'REVIEW.json'];cases={m:'active_short_train_0600' for m in h['methods']}
for m,v in h['methods'].items():
 inputs += [I/(m+'_BINDING.json'),D/(m+'_CACHE_SAVED_REVIEW.json'),Path(v['checkpoint89']['path']),Path(read(D/(m+'_CACHE_SAVED_REVIEW.json'))['snapshot']['path'])]
 e=next(e for e in v['episodes'] if e['cycle']==89 and e['condition']==cases[m]);inputs += [Path(e['journal']),Path(e['terminal'])];assert e['preaction_violation_rows']>0
names=('persisted_violation_critic.py','violation_consumers.py','check_consumers.py','register_consumers.py','supervise.py')
for n in names:ast.parse((D/n).read_text())
plan=dict(time=time.time(),methods=list(cases),cases=cases,cpu=12,device='cuda:1',budget_seconds=1800,seed=2026102638,sources={n:sha(D/n) for n in names},restore_runtime=p['restore_runtime'],restore_sources=p['restore_sources'],inputs=[dict(path=str(f),sha256=sha(f)) for f in inputs],recorded_events_only=True,new_physics=0,optimizer_updates=0,training90=False)
with (D/'CONSUMER_PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print('REGISTERED',sha(D/'CONSUMER_PLAN.json'))
