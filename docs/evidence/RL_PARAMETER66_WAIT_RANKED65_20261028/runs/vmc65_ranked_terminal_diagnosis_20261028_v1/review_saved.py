from pathlib import Path
import json,math,hashlib,os,time
os.sched_setaffinity(0,{53})
import numpy as np
OUT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def near(a,b):assert math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12),(a,b)
r=read(OUT/'REVIEW.json');assert r['passed']
for x in r['inputs'].values():assert sha(x['path'])==x['sha256']
with np.load(r['inputs']['values']['path'],allow_pickle=False) as v:
 assert len(v['indices'])==1974;pos={int(i):k for k,i in enumerate(v['indices'])};rows=r['all1974_ranked'];assert len(rows)==1974 and len({x['replay_index'] for x in rows})==1974
 assert [x['rank'] for x in rows]==list(range(1,1975));assert rows==sorted(rows,key=lambda x:(-x['masked_sse'],x['replay_index']))
 sums=[];cons=[]
 for x in rows:
  k=pos[x['replay_index']];parts=[float(v['masks'][h,k])*(float(v['q_after'][h,k])-float(v['rewards'][k]))**2 for h in range(5)];assert parts==x['per_head_sse'];near(math.fsum(parts),x['masked_sse']);assert x['terminal_reward']==float(v['rewards'][k]);sums.append(math.fsum(parts));con=math.fsum(128*parts[h]/float(v['denominator'][h]) for h in range(5));near(con,x['contribution']);cons.append(con)
  if k<1944:near(math.fsum(float(v['masks'][h,k])*(float(v['q_before'][h,k])-float(v['rewards'][k]))**2 for h in range(5)),x['sse64'])
  else:assert x['sse64'] is None
 for i,x in enumerate(r['top2']):
  assert x['replay_index']==rows[i]['replay_index'];k=pos[x['replay_index']];assert x['q64']==v['q_before'][:,k].tolist() and x['q65']==v['q_after'][:,k].tolist() and x['critic_head_masks']==v['masks'][:,k].tolist();near(x['sse_increment'],rows[i]['masked_sse']-rows[i]['sse64']);roll=read(x['rollout']['path']);assert sha(x['rollout']['path'])==x['rollout']['sha256'];assert roll['task_success']==x['task'] and roll['strict_success']==x['strict'] and roll['physical_valid']==x['physical_valid'];near(roll['stats']['max_external_penetration_m']*1000,x['penetration_mm'])
 near(math.fsum(sums),r['all1974_sse']);near(math.fsum(cons),r['all1974_contribution']);near(math.fsum(x['masked_sse'] for x in rows[:2])/math.fsum(sums),r['top2_share_of_full1974_sse']);near(math.fsum(x['sse_increment'] for x in r['top2']),r['top2_sse_increment']);near(r['remaining1942_sse_increment']+r['top2_sse_increment'],r['full1944_sse_increment'])
p=OUT/'SAVED_REVIEW.json';assert not p.exists();p.write_text(json.dumps(dict(time=time.time(),passed=True,all1974_independent_scalar_arithmetic=True,ranking_and_unique_indices_verified=True,top2_labels_and_original_arrays_verified=True,review_sha256=sha(OUT/'REVIEW.json'),reviewer_sha256=sha(Path(__file__)),new_physics=0,new_forward=0,optimizer_updates=0),indent=2)+'\n');print('All1974 scalar/ranking and top2 labels verified')
