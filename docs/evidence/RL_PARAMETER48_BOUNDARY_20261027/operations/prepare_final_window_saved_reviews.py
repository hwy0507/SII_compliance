from pathlib import Path
import json,time,hashlib,ast,subprocess,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
def launch(out,source):
 out.mkdir();ast.parse(source);(out/'review_saved.py').write_text(source)
 cmd=[str(B/'env/bin/python'),str(out/'review_saved.py')]
 with (out/'driver.log').open('x') as log:p=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
 (out/'LAUNCH.json').write_text(json.dumps(dict(time=time.time(),pid=p.pid,command=cmd,source_sha256=hashlib.sha256(source.encode()).hexdigest(),wait_seconds=7200,automatic_training=False),indent=2)+'\n');return p.pid
s=(B/'runs/parameter43_45_stability_saved_review_20261027_v1/review_saved.py').read_text().replace('43_45','46_48').replace('[43,44,45]','[46,47,48]').replace('==43+j','==46+j').replace('2026102745','2026102747').replace('paired43_to45','paired46_to48').replace('monotonic()+1800','monotonic()+7200')
parameter=launch(B/'runs/parameter46_48_stability_saved_review_20261027_v1',s)
s='''from pathlib import Path
import json,time,hashlib,math,os
O=Path(__file__).parent;B=O.parents[1];P=B/'runs/serl_take27_29_reward_stability_20261027_v1';os.sched_setaffinity(0,{54});os.nice(15)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text())
try:
 limit=time.monotonic()+7200
 while not (P/'REVIEW.json').exists():
  assert time.monotonic()<limit and not list(P.glob('*FAILURE.json'))
  time.sleep(3)
 r=read(P/'REVIEW.json');reg=read(P/'REGISTRATION.json');plan=read(P/'PLAN.json');assert r['passed'] and r['registration_sha256']==sha(P/'REGISTRATION.json')
 assert reg['cycles']==plan['cycles']==[26,27,28,29] and reg['stability_window']==plan['stability_window']==r['stability_window']==[27,28,29]
 assert reg['bootstrap_seed']==plan['bootstrap_seed']==2026102746 and reg['bootstrap_replicates']==5000 and reg['relative_change_limit']==.05 and reg['near_zero_guard']==1
 assert reg['source_sha256']==plan['source_sha256']==sha(P/'audit_serl_take27_29_reward_stability_20261027.py')
 for refs in reg['inputs'].values():
  for ref in refs.values():assert sha(ref['path'])==ref['sha256']
 rows=r['paired_conditions'];assert len(rows)==30 and len({x['condition'] for x in rows})==30
 means=[sum(x['rewards'][j] for x in rows)/30 for j in range(4)]
 for j,c in enumerate(r['cycles']):assert c['cycle']==26+j and abs(c['reward_mean']-means[j])<1e-10 and c['finite_logs']
 last=means[1:];near=any(abs(v)<1 for v in last);assert near==r['near_zero_mean_guard_triggered']
 if near:
  assert r['adjacent_relative_mean_changes'] is None and r['last3_endpoint_relative_change'] is None and not r['descriptive_five_percent_check']
 else:
  adjacent=[abs(last[j+1]-last[j])/abs(last[j]) for j in range(2)];endpoint=abs(last[-1]-last[0])/abs(last[0])
  assert all(abs(a-b)<1e-10 for a,b in zip(adjacent,r['adjacent_relative_mean_changes'])) and abs(endpoint-r['last3_endpoint_relative_change'])<1e-10
  assert r['descriptive_five_percent_check']==(max(adjacent+[endpoint])<=.05)
 deltas=[x['rewards'][-1]-x['rewards'][0] for x in rows]
 for x,d in zip(rows,deltas):assert abs(x['baseline26_to29_delta']-d)<1e-10
 assert abs(sum(deltas)/30-r['baseline26_to29_mean_delta'])<1e-10 and abs((last[-1]-last[0])/2-r['last3_mean_slope'])<1e-10
 assert sum(x>0 for x in deltas)==r['improved_conditions'] and sum(x<0 for x in deltas)==r['worsened_conditions']
 for key in ['bootstrap_condition_sensitivity95_delta','bootstrap_condition_sensitivity95_slope']:
  bounds=r[key];assert len(bounds)==2 and all(math.isfinite(v) for v in bounds) and bounds[0]<=bounds[1]
 assert sha(P/'reward_stability.png')==r['plot_sha256']
 result=dict(passed=True,time=time.time(),means=means,near_zero_guard=near,five_percent=r['descriptive_five_percent_check'],endpoint=r['last3_endpoint_relative_change'],last3_mean_slope=r['last3_mean_slope'],first1000_losses=[c['critic_loss_first1000'] for c in r['cycles']],last1000_losses=[c['critic_loss_last1000'] for c in r['cycles']],review_sha256=sha(P/'REVIEW.json'),registration_sha256=sha(P/'REGISTRATION.json'),all_input_hashes_verified=True,bootstrap_rerun=False,new_physics=0,optimizer_updates=0,convergence_claim=False)
 (O/'REVIEW.json').write_text(json.dumps(result,indent=2)+'\\n');print(json.dumps(result,indent=2),flush=True)
except BaseException as e:
 (O/'FAILURE.json').write_text(json.dumps(dict(time=time.time(),error=repr(e)))+'\\n');raise
'''
direct=launch(B/'runs/serl27_29_stability_saved_review_20261027_v1',s)
print(dict(parameter46_48_saved=parameter,serl27_29_saved=direct))
