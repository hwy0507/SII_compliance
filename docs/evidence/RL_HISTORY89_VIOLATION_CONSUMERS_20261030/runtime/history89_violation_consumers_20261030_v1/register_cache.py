from pathlib import Path
import json,time,hashlib,ast
D=Path(__file__).resolve().parent;B=D.parents[1];I=B/'runtime/history89_violation_interface_20261030_v2';H=B/'runs/history89_raw_history_extension_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read(I/'PLAN.json');assert read(I/'REVIEW.json')['passed'];h=read(H/'REVIEW.json')
inputs=[I/n for n in ('PLAN.json','REVIEW.json','AFFINE_REVIEW.json','LAYOUT_DIAGNOSIS.json')]+[H/'REVIEW.json',H/'SAVED_REVIEW.json']
for m,v in h['methods'].items():
 inputs += [I/(m+'_BINDING.json'),I/(m+'_migrated_learner.pt')]+[Path(v[n]['path']) for n in ('checkpoint89','sidecar','bits')]
names=('persisted_violation_critic.py','check_cache_and_saved.py','register_cache.py')
for n in names:ast.parse((D/n).read_text())
plan=dict(time=time.time(),methods=list(h['methods']),cpu=11,device='cuda:2',budget_seconds=1800,sources={n:sha(D/n) for n in names},restore_runtime=p['restore_runtime'],restore_sources=p['restore_sources'],inputs=[dict(path=str(f),sha256=sha(f)) for f in inputs],actual_parent_updates=0,physics=0,synthetic_replay_appends=3,full_snapshot_role='interface_only_no_online_approval',training90=False)
with (D/'CACHE_PLAN.json').open('x') as f:json.dump(plan,f,indent=2);f.write('\n')
print('REGISTERED',sha(D/'CACHE_PLAN.json'))
