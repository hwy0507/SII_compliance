from pathlib import Path
import json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census96_completion_wait_20261031_v1';R=B/'runs/parameter_census_cycle96_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
jobs=read(R/'LAUNCH.json')['jobs'];completed={}
for j in jobs:
 m=j['controller'];run=R/m/'train';finished=read(run/'FINISHED.json');assert finished['status']=='stopped_at_complete_cycle'
 try:s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();live=s[0]!='Z' and s[19]==j['proc_start_ticks']
 except FileNotFoundError:live=False
 assert not live and not (run/'FAILURE.json').exists() and not (run.parent/'DRIVER_FAILURE.json').exists()
 archived=B/'runs/parameter_census_cycle96_archive_20261031_v1'/m/'cycle_00096.json';meta=read(archived);assert sha(Path(meta['path']))==meta['sha256']
 completed[m]=dict(finished=finished,archive=meta,learner_exited=True)
assert not (R/'ARCHIVE_REVIEW_FAILURE.json').exists()
put(O/'COMPLETION_REVIEW.json',dict(passed=True,time=time.time(),all_complete=True,methods=completed,scope='Actual complete-cycle FINISHED records, archived checkpoint hashes and original learner process exits; separate archive/health/comparison reviews still required.'))
original=O/'LIVE_TERMINAL_GROWTH_REVIEW.json';growth=read(original);assert growth['passed'];methods={}
for m,r in growth['methods'].items():
 x=dict(r)
 for key,name in [('optimizer','update'),('transition','transition')]:
  p=Path(r['optimizer_path'] if key=='optimizer' else r['transition_path']);n=r['prefix_update_bytes'] if key=='optimizer' else r['prefix_transition_bytes'];h=r[name+'_prefix_sha256']
  with p.open('rb') as f:data=f.read(n)
  assert len(data)==n and hashlib.sha256(data).hexdigest()==h
  x[key+'_prefix']=dict(path=str(p),bytes=n,sha256=h)
 methods[m]=x
put(D/'LIVE_TERMINAL_GROWTH_REVIEW.json',dict(growth,methods=methods,original_source=dict(path=str(original),sha256=sha(original))))
put(D/'LIVE_GROWTH_BINDING_REVIEW.json',dict(passed=True,time=time.time(),source=dict(path=str(original),sha256=sha(original)),all_prefixes_equal_final_logs=True,full96_replay_checked=False))
print('All three actual complete96 boundaries/exits and original live-prefix hashes verified')
