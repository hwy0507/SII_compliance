"""Independent full-row arithmetic from transition reward telemetry, not extraction journals."""
from pathlib import Path
import os,sys,json,time,hashlib,collections,traceback,math
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1'
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_potential_audit_20261031_v1';rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def seq(phi):
 low=collections.deque();high=collections.deque();out=np.empty((len(phi),3))
 for i,x in enumerate(phi):
  while low and low[0]<i-13:low.popleft()
  while high and high[0]<i-13:high.popleft()
  while low and phi[low[-1]]>=x:low.pop()
  while high and phi[high[-1]]<=x:high.pop()
  low.append(i);high.append(i);out[i]=[x,0. if i==0 else (x-phi[i-1])/.04,phi[high[0]]-phi[low[0]]]
 return out
def main(m):
 start=time.monotonic();plan=rd(O/'PLAN.json');e=plan['methods'][m];os.sched_setaffinity(0,{e['cpu']+3});r=rd(O/(m+'_REVIEW.json'));assert r['passed'];assert sha(r['sidecar']['path'])==r['sidecar']['sha256'];side=np.load(r['sidecar']['path'],mmap_mode='r');assert side.shape==(e['rows'],6);seen=np.zeros(len(side),bool);terminal=[];cycles=[];conditions=[]
 for root in e['roots']:
  assert time.monotonic()-start<3600;groups=collections.defaultdict(list);p=Path(root['transitions']['path']);h=hashlib.sha256()
  with p.open('rb') as f:
   for line in f:
    h.update(line);t=json.loads(line)
    if root['selected_first_step']<=t['step']<=root['selected_last_step']:groups[t['cycle'],t['condition']].append(t)
  assert h.hexdigest()==root['transitions']['sha256']
  for (cycle,condition),ts in groups.items():
   idx=np.array([x['step']-1 for x in ts],np.int64);assert not seen[idx].any();phi=[x['reward_terms']['current_potential'] for x in ts];done=bool(ts[-1]['done'])
   if not done:phi.append(ts[-1]['reward_terms']['next_potential'])
   independent=seq(phi);np.testing.assert_array_equal(side[idx,:3],independent[:len(ts)])
   expect=np.empty((len(ts),3))
   for i,t in enumerate(ts):expect[i]=independent[i] if t['done'] else independent[i+1]
   np.testing.assert_array_equal(side[idx,3:],expect);seen[idx]=True
   if done:terminal.append(int(idx[-1]));cycles.append(cycle);conditions.append(condition)
 assert seen.all();values=np.load(r['terminal_values']['path']);order=np.argsort(terminal);np.testing.assert_array_equal(values['indices'],np.array(terminal)[order]);np.testing.assert_array_equal(values['cycles'],np.array(cycles)[order]);np.testing.assert_array_equal(values['conditions'],np.array(conditions)[order]);np.testing.assert_array_equal(values['features'],side[values['indices'],:3])
 baseline=np.load(B/'runs/violation93_fixed92_terminal_followup_20261031_v1'/(m+'_values.npz'));old=len(baseline['indices'])
 for key in ['indices','observations','actions','rewards','masks']:np.testing.assert_array_equal(values[key][:old],baseline[key])
 assert len(values['indices'])==old+30;assert sha(r['sidecar']['path'])==r['sidecar']['sha256'] and sha(r['terminal_values']['path'])==r['terminal_values']['sha256']
 put(O/(m+'_SAVED_REVIEW.json'),dict(passed=True,time=time.time(),rows=len(side),all6_saved_columns_exact_from_independent_reward_potential_deque_reconstruction=True,all_rows_checked_once=True,terminal_rows=len(terminal),old92_terminal_inputs_exact=True,sidecar_sha256=r['sidecar']['sha256'],elapsed_s=time.monotonic()-start,new_physics=0,optimizer_updates=0))
 print(json.dumps(dict(method=m,passed=True,rows=len(side),elapsed=time.monotonic()-start)),flush=True)
if __name__=='__main__':
 m=sys.argv[1]
 try:main(m)
 except BaseException:put(O/(m+'_SAVED_FAILURE.json'),dict(time=time.time(),traceback=traceback.format_exc()));raise
