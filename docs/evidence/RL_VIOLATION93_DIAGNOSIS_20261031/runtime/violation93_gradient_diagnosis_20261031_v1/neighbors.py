"""All fixed92 impedance input pairs; geometry does not establish irreducible ambiguity."""
from pathlib import Path
import os,time,json,hashlib,traceback
os.sched_setaffinity(0,{11})
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_gradient_diagnosis_20261031_v1';read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def main():
 plan=read(O/'PLAN.json');assert sha(__file__)==plan['sources']['neighbors.py'];p=Path(plan['fixed_values']);assert sha(p)==plan['fixed_values_sha256'];started=time.monotonic()
 with np.load(p) as z:obs=z['observations'].copy();act=z['actions'].copy();ids=z['indices'].copy();reward=z['rewards'].copy()
 x=np.concatenate([obs,act],1).astype(np.float64);assert x.shape==(2755,57) and np.isfinite(x).all() and np.isfinite(reward).all();assert np.all(reward!=0)
 unique,inv,count=np.unique(x,axis=0,return_inverse=True,return_counts=True);duplicates=[]
 for g in np.flatnonzero(count>1):
  ix=np.flatnonzero(inv==g);duplicates.append(dict(replay_indices=ids[ix].tolist(),rewards=reward[ix].tolist(),reward_range=float(np.ptp(reward[ix]))))
 std=x.std(axis=0);scale=np.where(std>1e-8,std,1.);metrics={};arrays=dict(indices=ids,observations=obs,actions=act,rewards=reward,scale=scale)
 for name,y in [('native_units',x),('unit_std',x/scale)]:
  nearest=[];opposite=[];distances=[];oppdist=[]
  for first in range(0,len(y),64):
   assert time.monotonic()-started<plan['neighbor_budget_seconds'];last=min(len(y),first+64);d=np.sqrt(np.square(y[first:last,None,:]-y[None,:,:]).sum(2));d[np.arange(last-first),np.arange(first,last)]=np.inf;ni=np.argmin(d,axis=1);nearest.extend(ni.tolist());distances.extend(d[np.arange(last-first),ni].tolist());d[np.sign(reward[first:last,None])==np.sign(reward[None,:])]=np.inf;oi=np.argmin(d,axis=1);assert np.isfinite(d[np.arange(last-first),oi]).all();opposite.extend(oi.tolist());oppdist.extend(d[np.arange(last-first),oi].tolist())
  nearest=np.array(nearest);opposite=np.array(opposite);distances=np.array(distances);oppdist=np.array(oppdist)
  np.testing.assert_allclose(distances,np.linalg.norm(y-y[nearest],axis=1),rtol=1e-12,atol=1e-12);np.testing.assert_allclose(oppdist,np.linalg.norm(y-y[opposite],axis=1),rtol=1e-12,atol=1e-12);assert np.all(np.sign(reward)!=np.sign(reward[opposite]))
  for key,value in [('nearest_positions',nearest),('opposite_positions',opposite),('nearest_distances',distances),('opposite_distances',oppdist)]:arrays[name+'_'+key]=value
  selected=[]
  for replay_index in plan['selected_indices']:
   loc=np.flatnonzero(ids==replay_index);assert len(loc)==1;i=int(loc[0]);pairs={}
   for label,j in [('nearest',int(nearest[i])),('nearest_opposite_sign',int(opposite[i]))]:
    delta=x[j]-x[i];scaled=delta/scale;order=np.argsort(np.abs(scaled))[-5:][::-1];pairs[label]=dict(replay_index=int(ids[j]),distance=float(np.linalg.norm(y[j]-y[i])),reward=float(reward[j]),reward_delta=float(reward[j])-float(reward[i]),exact_equal=bool(np.array_equal(x[j],x[i])),largest_standardized_differences=[dict(column=int(k),value_here=float(x[i,k]),value_neighbor=float(x[j,k]),scaled_difference=float(scaled[k])) for k in order],observations=obs[j].tolist(),actions=act[j].tolist())
   selected.append(dict(replay_index=int(ids[i]),reward=float(reward[i]),observations=obs[i].tolist(),actions=act[i].tolist(),pairs=pairs))
  metrics[name]=dict(nearest_distance_quantiles=np.quantile(distances,[0,.25,.5,.75,1]).tolist(),opposite_distance_quantiles=np.quantile(oppdist,[0,.25,.5,.75,1]).tolist(),nearest_opposite_sign_count=int(np.count_nonzero(np.sign(reward)!=np.sign(reward[nearest]))),selected=selected)
 file=O/'NEIGHBOR_VALUES.npz';np.savez_compressed(file,**arrays)
 put(O/'NEIGHBOR_REVIEW.json',dict(passed=True,time=time.time(),rows=len(x),joint_dimension=57,unique_inputs=len(unique),exact_duplicate_groups=duplicates,metrics=metrics,values=dict(path=str(file),bytes=file.stat().st_size,sha256=sha(file)),source_sha256=sha(__file__),optimizer_updates=0,new_physics=0,neural_forwards=0,scope='Exhaustive nearest input/action geometry on all fixed92 impedance terminal rows in native units and unit per-column standard deviation (std<=1e-8 uses1). Scale only for diagnostics, not training. Opposite reward sign is descriptive; near inputs do not prove missing information or irreducible labels. Selected rows fixed from preceding complete93 report; all2755 rows searched.'))
 print(json.dumps(dict(unique_inputs=len(unique),duplicate_groups=len(duplicates),metrics={k:{x:y for x,y in v.items() if x!='selected'} for k,v in metrics.items()}),indent=2))
if __name__=='__main__':
 try:main()
 except BaseException as e:put(O/'NEIGHBOR_FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
