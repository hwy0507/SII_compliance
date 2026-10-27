from pathlib import Path
import os,sys,json,time,hashlib,statistics,copy
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=Path(__file__).parent
os.sched_setaffinity(0,{52});os.nice(19)
import numpy as np,torch
torch.set_num_threads(1)
cp=B/'runs/serl_interrupted25_recovery26_20261027_v1/startup/direct.pt'
plan={'time':time.time(),'snapshot':str(cp),'repetitions':20,'batch_size':65536,'seed':2026102744,'cpu':52,'variants':['numpy_fancy_indexing','numpy_take_clip_validated_indices'],'new_physics':0,'optimizer_updates':0,'formal_deployment':False,'reason':'Direct stacks show CPU replay gathers; test exact gathered bytes and RNG on same saved replay with finite alternating paired timing. No saved weights or replay mutation.'}
(O/'GATHER_PLAN.json').write_text(json.dumps(plan,indent=2)+'\n')
x=torch.load(cp,map_location='cpu',weights_only=False);r=x['replay'];ex=r['multistep_target_extension'];ready=np.array(ex['ready'],dtype=np.int64);a=r['arrays'];rng=np.random.default_rng(plan['seed'])
rows=[]
for rep in range(20):
 ids=ready[rng.integers(len(ready),size=65536)];end=ex['target_endpoints'][ids]
 assert ids.min()>=0 and ids.max()<r['size'] and end.min()>=0 and end.max()<r['size']
 def base():
  v={k:val[ids] for k,val in a.items() if k not in ('rewards','next_observations')}
  v.update(rewards=ex['target_rewards'][ids,None],next_observations=a['next_observations'][end],_bootstrap=ex['target_bootstrap'][ids]);return v
 def candidate():
  v={k:np.take(val,ids,axis=0,mode='clip') for k,val in a.items() if k not in ('rewards','next_observations')}
  v.update(rewards=np.take(ex['target_rewards'],ids,mode='clip')[:,None],next_observations=np.take(a['next_observations'],end,axis=0,mode='clip'),_bootstrap=np.take(ex['target_bootstrap'],ids,mode='clip'));return v
 values={};elapsed={}
 for name,fun in ([('base',base),('candidate',candidate)] if rep%2==0 else [('candidate',candidate),('base',base)]):
  t=time.perf_counter();values[name]=fun();elapsed[name]=time.perf_counter()-t
 assert values['base'].keys()==values['candidate'].keys()
 for k,v in values['base'].items():assert v.dtype==values['candidate'][k].dtype and np.array_equal(v,values['candidate'][k]),k
 rows.append(elapsed)
report={'passed':True,'time':time.time(),'paired_timings_seconds':rows,'median_seconds':{k:statistics.median(r[k] for r in rows) for k in ['base','candidate']},'all20_batches_all_fields_bit_exact':True,'same_draw_indices':True,'rng_draws_unchanged':True,'new_physics':0,'optimizer_updates':0,'formal_deployment':False,'limitation':'CPU52 shares auxiliary frozen evaluation; wall timings noisy, not end-to-end GPU speedup. Candidate only, unchanged running source. Needs full wrapper/next-update and restore gates before any registered deployment.'}
with cp.open('rb') as f:report['checkpoint_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
(O/'GATHER_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='paired_timings_seconds'},indent=2))
