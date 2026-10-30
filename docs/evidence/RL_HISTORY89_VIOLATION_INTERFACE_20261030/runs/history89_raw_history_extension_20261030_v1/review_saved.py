"""Scalar independent journal/bit review plus full retained-prefix comparison."""
from pathlib import Path
import json,hashlib,time,collections,os
import numpy as np
D=Path(__file__).resolve().parent;os.sched_setaffinity(0,{11});read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
plan=read(D/'PLAN.json');assert sha(__file__)==plan['sources']['review_saved.py'];r=read(D/'REVIEW.json');assert r['passed'];out={}
for m,a in r['methods'].items():
 for x in [a['sidecar'],a['old_sidecar'],a['bits']]+a['inputs']:assert sha(x['path'])==x['sha256']
 side=np.load(a['sidecar']['path'],mmap_mode='r');old=np.load(a['old_sidecar']['path'],mmap_mode='r');bits=np.load(a['bits']['path'],mmap_mode='r');np.testing.assert_array_equal(side[:len(old)],old);assert side.shape==(a['total_rows'],2) and bits.shape==side.shape and bits.dtype==np.uint8
 np.testing.assert_array_equal(bits,np.greater(side,np.float64('0.0002')).astype(np.uint8));assert np.all(bits[:,1]>=bits[:,0])
 seen=set();bycycle={};stats=[]
 for e in a['episodes']:
  if e['cycle'] not in bycycle:
   groups=collections.defaultdict(list)
   for line in Path(e['transition_log']).read_text().splitlines():
    t=json.loads(line);groups[t['condition']].append(t)
   bycycle[e['cycle']]=groups
  ts=bycycle[e['cycle']][e['condition']];js=[json.loads(l) for l in Path(e['journal']).read_text().splitlines()];terminal=read(e['terminal']);prev=0.;nb=0;crossed=0
  for i,(t,j) in enumerate(zip(ts,js)):
   idx=t['step']-1;assert idx not in seen and len(old)<=idx<len(side);seen.add(idx)
   pre=0. if i==0 else float(j['interval']['external_penetration_peak_m']);nxt=float((terminal if t['done'] else js[i+1])['interval']['external_penetration_peak_m'])
   assert side[idx,0]==pre and side[idx,1]==nxt and pre>=prev and nxt>=pre
   assert int(bits[idx,0])==int(pre>0.0002) and int(bits[idx,1])==int(nxt>0.0002)
   prev=pre;nb+=pre>0.0002;crossed+=pre<=0.0002<nxt
  assert len(ts)==len(js)==1375 and nb==e['preaction_violation_rows'];stats.append(dict(cycle=e['cycle'],condition=e['condition'],preaction_violation_rows=nb,new_violation_transitions=crossed,terminal_pre_peak=pre,terminal_next_peak=nxt))
 assert len(seen)==82500 and min(seen)==len(old) and max(seen)==len(side)-1
 out[m]=dict(prefix_rows=len(old),appended_rows=len(seen),total_rows=len(side),prefix_exact=True,all_saved_appended_values_and_bits_match_scalar_journal=True,full_preaction_violation_rows=int(bits[:,0].sum()),full_next_violation_rows=int(bits[:,1].sum()),new_preaction_violation_rows=sum(x['preaction_violation_rows'] for x in stats),new_violation_transitions=sum(x['new_violation_transitions'] for x in stats),all60_episode_statistics=stats,sidecar_sha256=sha(a['sidecar']['path']),bits_sha256=sha(a['bits']['path']))
put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),methods=out,review_sha256=sha(D/'REVIEW.json'),source_sha256=sha(__file__),no_future_terminal_peak_broadcast=True,new_physics=0,new_network_forward=0,new_optimizer_updates=0))
put(D/'FINISHED.json',dict(passed=True,time=time.time(),saved_review_sha256=sha(D/'SAVED_REVIEW.json')));print('All original prefix and247500 appended rows/bits verified')
