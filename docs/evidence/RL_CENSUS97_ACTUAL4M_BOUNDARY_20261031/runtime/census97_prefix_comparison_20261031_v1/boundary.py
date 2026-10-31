"""One finite read-only audit of actual97 replay crossing4m; never trains or resets."""
from pathlib import Path
import os,sys,time,json,hashlib,shutil,gc,traceback,math
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/census97_capacity_boundary_20261031_v1';R=B/'runs/parameter_census_cycle97_20261031_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def identity(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['proc_start_ticks']
def audit_arrays(arr,old,n,ts):
 import numpy as np
 if set(arr)!=set(old):raise ValueError('Replay schema changed')
 parent=len(old['dones'])
 for key,v in old.items():
  if arr[key].shape!=(n,v.shape[1]) or arr[key].dtype!=v.dtype:raise ValueError('Replay shape/dtype changed')
  for lo in range(0,parent,65536):
   hi=min(parent,lo+65536)
   if not np.array_equal(v[lo:hi],arr[key][lo:hi]):raise ValueError('Old replay row changed: '+key)
  if not np.isfinite(arr[key][parent:]).all():raise ValueError('Nonfinite new replay')
 if [t['step'] for t in ts]!=list(range(parent+1,n+1)):raise ValueError('New journal not contiguous')
 np.testing.assert_array_equal(arr['rewards'][parent:,0],np.asarray([t['reward'] for t in ts],np.float32))
 np.testing.assert_array_equal(arr['dones'][parent:,0],np.asarray([t['done'] for t in ts],np.float32))
 if not np.all((arr['masks'][parent:]==0)|(arr['masks'][parent:]==1)):raise ValueError('Nonbinary masks')
 return parent

def main():
 import numpy as np,torch
 from collections import defaultdict
 p=read(O/'PLAN.json');assert sha(__file__)==p['source_sha256'];os.sched_setaffinity(0,{12});torch.set_num_threads(1);sys.path.insert(0,p['runtime'])
 from driver import validate_checkpoint
 from parameter_replay_capacity6m import KEY,MARKER
 from parameter_replay_capacity_20261026 import MARKER as CAP2
 from parameter_replay_capacity4m_20261027 import MARKER as CAP4
 from persisted_history_critic import feature
 for name,h in p['runtime_sources'].items():assert sha(Path(p['runtime'])/name)==h
 methods={}
 for m,e in p['methods'].items():
  run=R/m/'train';cp=run/'checkpoint_latest.pt'
  while True:
   assert time.time()<p['deadline_unix']
   if (run/'FAILURE.json').exists() or (run.parent/'DRIVER_FAILURE.json').exists():raise RuntimeError('Scientific job failed: '+m)
   if cp.exists() and read(run/'PROGRESS.json')['steps']>p['boundary']+1000:
    ck=torch.load(cp,map_location='cpu',weights_only=False,mmap=True);n=ck['steps'];del ck
    if n>p['boundary']:break
   if (run/'FINISHED.json').exists():raise RuntimeError('Finished without reaching4m: '+m)
   identity(e['process']);time.sleep(15)
  out=O/m;out.mkdir();snap=out/'boundary.pt'
  with cp.open('rb') as src,snap.open('xb') as dst:shutil.copyfileobj(src,dst)
  ck=torch.load(snap,map_location='cpu',weights_only=False,mmap=True);reg=read(e['registration']['path']);assert sha(e['registration']['path'])==e['registration']['sha256'];validate_checkpoint(ck,reg,complete=False);n=ck['steps'];assert n>p['boundary'] and ck['replay']['capacity']==6000000 and ck['replay'][KEY]==MARKER and ck['replay']['replay_capacity_extension']==CAP2 and ck['replay']['replay_capacity_followup']==CAP4
  parent=e['parent_checkpoint'];assert sha(parent['path'])==parent['sha256'];old=torch.load(parent['path'],map_location='cpu',weights_only=False,mmap=True);assert old['steps']==e['parent_steps'];arr=ck['replay']['arrays'];ts=[];raw=[]
  with (run/'transitions.jsonl').open('rb') as f:
   for line in f:
    t=json.loads(line)
    if t['step']>n:break
    raw.append(line);ts.append(t)
  before=audit_arrays(arr,old['replay']['arrays'],n,ts);by=defaultdict(list)
  for t in ts:by[t['condition']].append(t)
  selected={i for i in range(p['boundary']-2,min(n,p['boundary']+3))};records=[]
  for condition,rows in by.items():
   targets=[(i,t) for i,t in enumerate(rows) if t['step']-1 in selected]
   if not targets:continue
   journal=run/'cycle_00097'/condition/'actor_intervals.jsonl';js=[]
   with journal.open() as f:
    for k,line in enumerate(f):
     js.append(json.loads(line))
     if k>=max(i for i,t in targets)+1:break
   for i,t in targets:
    k=t['step']-1;j,nxt=js[i],js[i+1];scale=ck['learner']['observation_scale'];np.testing.assert_array_equal(arr['observations'][k,:48],np.asarray(j['observation'],np.float32)/scale);np.testing.assert_array_equal(arr['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32))
    np.testing.assert_array_equal(arr['next_observations'][k,:48],np.asarray(nxt['observation'],np.float32)/scale)
    assert arr['observations'][k,48]==np.float32(t['context']) and arr['observations'][k,49]==np.float32((1375-i)/1375) and arr['next_observations'][k,49]==np.float32((1374-i)/1375)
    for item,key in [(j,'observations'),(nxt,'next_observations')]:
     peak=0. if item['interval'] is None else item['interval']['external_penetration_peak_m'];assert arr[key][k,50]==feature(peak) and arr[key][k,51]==float(peak>.0002)
    records.append(dict(replay_index=k,step=t['step'],condition=condition,condition_action_index=i,done=t['done'],reward=t['reward']))
  assert {x['replay_index'] for x in records}==selected
  assert sha(parent['path'])==parent['sha256'];result=dict(passed=True,time=time.time(),snapshot=dict(path=str(snap),sha256=sha(snap)),steps=n,parent_steps=before,rows_beyond4m=n-p['boundary'],all_old_rows_all_fields_exact=True,new_journal_rewards_dones_exact=True,boundary_current_next52_and_mixed_action_exact=True,boundary_rows=sorted(records,key=lambda x:x['replay_index']),new_journal_prefix_sha256=hashlib.sha256(b''.join(raw)).hexdigest(),third_capacity_marker=MARKER,physics_steps=0,optimizer_updates=0,full97_claim=ck['boundary']=='complete_condition_cycle')
  put(out/'REVIEW.json',result);methods[m]=result;print(m,n,'actual4m crossing retained',flush=True);del ck,old,arr,ts,raw;gc.collect()
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=methods,physics_steps=0,optimizer_updates=0,scope='One actual boundary snapshot per method. Entire complete96 prefix/all fields exact; all new reward/done journal and five boundary rows tied to original actor intervals. Not full97 health/convergence or independent dynamics replay.'))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
