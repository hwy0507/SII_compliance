"""All full92 replay terminal fitting errors; no updates or environment steps."""
from pathlib import Path
import argparse,gc,hashlib,json,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_terminal_census_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def run(method):
 plan=read(O/'PLAN.json');entry=plan['methods'][method];started=time.monotonic();os.sched_setaffinity(0,{entry['cpu']})
 assert sha(__file__)==plan['source_sha256']
 for p,h in plan['dependencies'].items():assert sha(p)==h,p
 for x in plan['inputs']:assert sha(x['path'])==x['sha256']
 sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation92_terminal_followup_20261030_v1')]
 import numpy as np
 import torch
 from violation_consumers import restore_learner
 from compare92 import validate_recovery92
 from frozen_helpers import capture_rng
 from validate_published_finite_check_20261025 import digest
 torch.set_num_threads(1);cp=Path(entry['checkpoint']);assert sha(cp)==entry['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration']);validate_recovery92(ck,reg)
 assert ck['steps']==entry['steps'];arr=ck['replay']['arrays'];rd=digest(ck['replay']);initial=digest(ck['learner']);indices=np.flatnonzero(arr['dones'][:,0]==1);assert len(indices)==entry['terminal_count']
 learner=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',entry['device'],ck['seed']);assert digest(learner.state_dict())==initial;rng=digest(capture_rng(learner))
 obs=arr['observations'][indices];actions=arr['actions'][indices];rewards=arr['rewards'][indices,0];masks=arr['masks'][indices];assert obs.shape==(len(indices),52)
 with torch.no_grad():
  tx=torch.as_tensor(obs,device=learner.device);ta=torch.as_tensor(actions,device=learner.device);pred=torch.stack([q(tx,ta).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
 assert np.isfinite(pred).all();error=(pred.astype(np.float64)-rewards.astype(np.float64)[:,None])**2;weighted=error*masks;row_sse=weighted.sum(1);order=np.argsort(-row_sse,kind='stable')
 mask_total=arr['masks'].sum(0,dtype=np.float64);terminal_mask_total=masks.sum(0,dtype=np.float64);denom=mask_total+127*terminal_mask_total
 groups={}
 for name,sel in [('all',np.ones(len(indices),dtype=bool)),('before92',indices<entry['parent_steps']),('new92',indices>=entry['parent_steps']),('bit0',obs[:,51]==0),('bit1',obs[:,51]==1)]:
  groups[name]=dict(rows=int(sel.sum()),masked_sse=float(row_sse[sel].sum()),per_critic_masked_sse=weighted[sel].sum(0).tolist(),per_critic_mask_count=masks[sel].sum(0).tolist(),all_row_sse=error[sel].sum(0).tolist(),full_replay_weighted_terminal_contribution=float((128*weighted[sel].sum(0)/denom).sum()))
 top=[dict(replay_index=int(indices[j]),masked_sse=float(row_sse[j]),fraction=float(row_sse[j]/row_sse.sum()),reward=float(rewards[j]),q=pred[j].tolist(),mask=masks[j].tolist(),bit=int(obs[j,51]),clock=float(obs[j,49]),history=float(obs[j,50])) for j in order[:20]]
 known=[]
 for source in entry['known_aborts']:
  transition=source['transition'];i=int(transition['step'])-1;where=np.flatnonzero(indices==i);assert len(where)==1;j=int(where[0]);assert transition['done'] and transition['cycle']==source['cycle'];np.testing.assert_array_equal(rewards[j],np.float32(transition['reward']))
  known.append(dict(cycle=source['cycle'],replay_index=i,rank=int(np.flatnonzero(order==j)[0])+1,masked_sse=float(row_sse[j]),fraction=float(row_sse[j]/row_sse.sum()),reward=float(rewards[j]),q=pred[j].tolist(),mask=masks[j].tolist(),bit=int(obs[j,51]),clock=float(obs[j,49]),history=float(obs[j,50]),source=source))
 # Bind original fixed87 cohort, allowing only documented float32 kernel shape effects.
 with np.load(entry['fixed87_values']) as z:
  pos=np.searchsorted(indices,z['indices']);np.testing.assert_array_equal(indices[pos],z['indices']);np.testing.assert_array_equal(obs[pos],z['observations52']);np.testing.assert_array_equal(actions[pos],z['actions']);np.testing.assert_array_equal(rewards[pos],z['rewards'][:,0]);np.testing.assert_array_equal(masks[pos],z['masks']);diff=float(np.max(np.abs(pred[pos]-z['complete92'])));np.testing.assert_allclose(pred[pos],z['complete92'],rtol=3e-6,atol=1e-5)
 assert digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng and digest(ck['replay'])==rd and sha(cp)==entry['checkpoint_sha256']
 output=O/(method+'_values.npz');np.savez_compressed(output,indices=indices,observations=obs,actions=actions,rewards=rewards,masks=masks,predictions=pred,replay_mask_counts=mask_total,terminal_mask_counts=terminal_mask_total,weighted_replay_denominators=denom)
 assert time.monotonic()-started<plan['budget_seconds']
 put(O/(method+'_REVIEW.json'),dict(passed=True,time=time.time(),method=method,checkpoint_sha256=entry['checkpoint_sha256'],replay_rows=ck['steps'],terminal_rows=len(indices),groups=groups,top20=top,top_k_fractions={str(k):float(row_sse[order[:k]].sum()/row_sse.sum()) for k in [1,2,3,10,20,100]},known_aborts=known,original87_input_binding=True,fixed87_max_prediction_difference=diff,full_learner_optimizer_replay_rng_unchanged=True,values_sha256=sha(output),values_bytes=output.stat().st_size,optimizer_updates=0,new_physics=0,elapsed_s=time.monotonic()-started,scope=plan['scope']))
 print(json.dumps(dict(method=method,groups=groups,top3=top[:3],known_aborts=known,top_k_fractions={str(k):float(row_sse[order[:k]].sum()/row_sse.sum()) for k in [1,2,3,10,20,100]})),flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--method',required=True,choices=['impedance','admittance','vmc']);args=parser.parse_args()
 try:run(args.method)
 except BaseException as e:put(O/(args.method+'_FAILURE.json'),dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
