from pathlib import Path
import json,hashlib,time,os
os.environ['OPENBLAS_NUM_THREADS']='1'
import numpy as np
os.sched_setaffinity(0,{53});D=Path(__file__).parent;B=D.parents[1]
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(r):
 p=Path(r['path']);assert sha(p)==r['sha256'];assert p.stat().st_size==r['bytes']
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(D/'FINISHED.json')['passed'];review=read(D/'REVIEW.json');assert review['passed'];verify(review['plan']);inv=read(B/'runs/recovery85_history_lineage_inventory_20261030_v1/REVIEW.json');old=read(B/'runs/recovery84_causal_history_audit_20261030_v1/REVIEW.json');results={}
for m,r in review['methods'].items():
 verify(r['sidecar']);verify(r['episode_review']);a=np.load(r['sidecar']['path'],mmap_mode='r',allow_pickle=False);assert a.dtype==np.float64 and a.shape==(r['retained_rows'],2)
 eps=[json.loads(l) for l in Path(r['episode_review']['path']).read_text().splitlines()];assert len(eps)==r['episode_cohorts']==2580
 totals=dict(rows=0,pre=0,next=0,term=0,partial=0,unknown=0,bad_episodes=0);seen=np.zeros(a.shape[0],np.uint8);old_cases={x['condition']:x for x in old['methods'][m]['cases']};matched84=0;checks84=[];perroot={};max_peak=0.
 for e in eps:
  # Global replay rows of parallel episodes are interleaved. Obtain their exact indices from the already inventoried immutable transition logs.
  key=(e['train'],e['cycle'],e['condition']);perroot.setdefault(e['train'],{})[(e['cycle'],e['condition'])]=e
 for root in inv['methods'][m]['roots']:
  p=Path(root['transitions']['path']);assert sha(p)==root['transitions']['sha256'];groups={}
  with p.open() as f:
   for line in f:
    t=json.loads(line)
    if root['selected_first_step']<=t['step']<=root['selected_last_step']:groups.setdefault((t['cycle'],t['condition']),[]).append(t['step']-1)
  assert set(groups)==set(perroot[str(root['train'])])
  for key,idx in groups.items():
   e=perroot[str(root['train'])][key];v=a[idx];n=len(idx);assert n==e['retained_transitions'] and idx[0]+1==e['first_global_step'] and idx[-1]+1==e['last_global_step'];assert not seen[idx].any();seen[idx]=1
   assert np.isfinite(v).all() and np.all(v>=0) and np.all(v[:,1]>=v[:,0]) and np.all(np.diff(v[:,0])>=0);assert v[0,0]==0 and np.array_equal(v[:-1,1],v[1:,0]);max_peak=max(max_peak,float(v.max()))
   bad=[i for i,pair in enumerate(v) if float(pair[0])>.0002];nb=len(bad);nn=sum(float(pair[1])>.0002 for pair in v)
   assert nb==e['preaction_violation_rows'] and nn==e['next_violation_rows'] and (bad[0] if bad else None)==e['first_bad_preaction_index']
   assert float(v[-1,0])==e['last_preaction_peak'] and float(v[-1,1])==e['last_next_peak'] and float(v[0,0])==e['first_preaction_peak']
   totals['rows']+=n;totals['pre']+=nb;totals['next']+=nn;totals['term']+=int(e['terminal_retained']);totals['partial']+=int(not e['terminal_retained']);totals['unknown']+=e['unknown_next_context_rows'];totals['bad_episodes']+=int(nb>0)
   if e['train']==str(B/f'runs/parameter_partial75_recovery_cycle84_20261029_v1/{m}/train'):
    c=old_cases[e['condition']];assert c['actions']==n and c['preactions_after_violation']==nb and c['last_preaction_peak_m']==float(v[-1,0]) and c['final_peak_m']==float(v[-1,1]) and c['first_bad_preaction_index']==e['first_bad_preaction_index']
    verify(c['derived'])
    with np.load(c['derived']['path'],allow_pickle=False) as z:
     np.testing.assert_array_equal(v[:,0],z['preaction_peak_m']);np.testing.assert_array_equal(v[:,1],z['next_observation_peak_m'])
    checks84.append(dict(condition=e['condition'],rows=n,prior_scalar_metrics_exact=True,prior84_arrays_exact=True));matched84+=1
 assert seen.all() and totals['rows']==r['retained_rows'] and totals['pre']==r['preaction_violation_rows'] and totals['next']==r['next_violation_rows'] and totals['term']==r['retained_terminal_rows'] and totals['partial']==r['retained_partial_episode_cohorts'] and totals['unknown']==r['next_context_unavailable_rows'] and totals['bad_episodes']==r['episodes_with_preaction_violation'] and matched84==30
 assert r['next_context_checked_rows']+totals['unknown']==totals['rows'];verify(r['sidecar']);verify(r['episode_review'])
 results[m]=dict(passed=True,totals=totals,sidecar_maximum_peak_m=max_peak,prior84_all30_scalar_metrics_exact=True,prior84_checks=checks84,sidecar_sha256=r['sidecar']['sha256'],all_replay_indices_once=True,all_within_episode_next_to_pre_exact=True)
 print(m,totals,flush=True)
put(D/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),methods=results,source_review_sha256=sha(D/'REVIEW.json'),total_rows=sum(x['totals']['rows'] for x in results.values()),limitation='Independent saved scalar/sidecar/index/hash checks and all90 earlier84 scalar comparisons. Does not re-execute raw physics or independently recheck all50 checkpoint fields.',new_physics=0,new_network_forward=0,optimizer_updates=0))
