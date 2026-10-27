from pathlib import Path
import os,json,time,hashlib,math
O=Path(__file__).parent;B=O.parents[1];P=B/'runs/parameter_capacity43_45_reward_stability_20261027_v1';os.sched_setaffinity(0,{54});os.nice(15)
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
try:
 deadline=time.monotonic()+1800
 while not (P/'REVIEW.json').exists():
  assert time.monotonic()<deadline
  assert not list(P.glob('*FAILURE.json'))
  time.sleep(3)
 r=json.loads((P/'REVIEW.json').read_text());reg=json.loads((P/'REGISTRATION.json').read_text());plan=json.loads((P/'PLAN.json').read_text())
 assert r['passed'] and reg['cycles']==plan['cycles']==[43,44,45]
 assert reg['seed']==plan['bootstrap_seed']==2026102745 and reg['bootstrap_replicates']==5000
 assert reg['source_sha256']==plan['source_sha256']==sha(P/'audit_parameter43_45_reward_stability_20261027.py')
 for refs in reg['inputs'].values():
  for ref in refs.values():assert sha(Path(ref['path']))==ref['sha256']
 checked={}
 for method,data in r['methods'].items():
  rows=data['paired_conditions'];assert len(rows)==30 and len({x['condition'] for x in rows})==30
  means=[sum(x['rewards'][j] for x in rows)/30 for j in range(3)]
  for j,cycle in enumerate(data['cycles']):assert abs(means[j]-cycle['reward_mean'])<1e-10 and cycle['cycle']==43+j
  near=any(abs(x)<1 for x in means);assert near==data['near_zero_guard_triggered']
  diffs=[abs(means[j+1]-means[j]) for j in range(2)]
  assert all(abs(a-b)<1e-10 for a,b in zip(diffs,data['adjacent_absolute_mean_changes']))
  assert abs(max(means)-min(means)-data['absolute_range_of_cycle_means'])<1e-10
  if near:
   assert data['adjacent_relative_mean_changes'] is None and data['endpoint_relative_mean_change'] is None and not data['descriptive_five_percent_check']
  else:
   rel=[diffs[j]/abs(means[j]) for j in range(2)];end=abs(means[-1]-means[0])/abs(means[0])
   assert all(abs(a-b)<1e-10 for a,b in zip(rel,data['adjacent_relative_mean_changes'])) and abs(end-data['endpoint_relative_mean_change'])<1e-10
   assert data['descriptive_five_percent_check']==(max(rel+[end])<=.05)
  deltas=[x['rewards'][2]-x['rewards'][0] for x in rows]
  assert abs(sum(deltas)/30-data['paired43_to45_mean_delta'])<1e-10 and abs((means[-1]-means[0])/2-data['slope'])<1e-10
  assert sum(x>0 for x in deltas)==data['improved_conditions'] and sum(x<0 for x in deltas)==data['worsened_conditions']
  for key in ['bootstrap_condition_sensitivity95_delta','bootstrap_condition_sensitivity95_slope']:
   bounds=data[key];assert len(bounds)==2 and all(math.isfinite(x) for x in bounds) and bounds[0]<=bounds[1]
  checked[method]=dict(means=means,near_zero_guard=near,five_percent=data['descriptive_five_percent_check'],endpoint=data['endpoint_relative_mean_change'],first1000_losses=[x['q_loss_first1000'] for x in data['cycles']],last1000_losses=[x['q_loss_last1000'] for x in data['cycles']])
 assert sha(P/'reward_stability.png')==r['plot_sha256']
 (O/'REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),methods=checked,review_sha256=sha(P/'REVIEW.json'),registration_sha256=sha(P/'REGISTRATION.json'),plot_sha256=r['plot_sha256'],all_input_hashes_verified=True,bootstrap_rerun=False,new_physics=0,optimizer_updates=0,convergence_claim=False),indent=2)+'\n');print(json.dumps(checked,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\n');raise
