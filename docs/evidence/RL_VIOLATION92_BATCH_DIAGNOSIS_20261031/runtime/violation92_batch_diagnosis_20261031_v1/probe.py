"""Frozen full92 native65536 critic batches, stopped before zero_grad/backward/step."""
from pathlib import Path
import argparse,copy,gc,hashlib,json,marshal,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_frozen_batch_diagnosis_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
class BeforeOptimization(Exception):pass

def main(method):
 plan=read(O/'PLAN.json');entry=plan['methods'][method];out=O/method;out.mkdir();(out/'raw').mkdir();started=time.monotonic();os.sched_setaffinity(0,{entry['cpu']})
 assert sha(__file__)==plan['source_sha256']
 for p,h in plan['dependencies'].items():assert sha(p)==h,p
 for ref in plan['inputs']:assert sha(ref['path'])==ref['sha256']
 sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/violation92_continuation_20261030_v1'),str(B/'runtime/source_train17_clock/source/tools'),str(B/'runtime/violation92_terminal_followup_20261030_v1')]
 import numpy as np
 import torch
 from violation_consumers import restore_learner
 from violation_pipeline import classes
 from compare92 import validate_recovery92
 from published_exact_pipeline_20261026 import cache_class,accepted
 from published_replay_device_cache_20261025 import DeviceReplayCache
 from frozen_helpers import capture_rng,restore_rng
 from validate_published_finite_check_20261025 import digest
 torch.set_num_threads(1)
 cp=Path(entry['checkpoint']);assert sha(cp)==entry['checkpoint_sha256'];ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration']);validate_recovery92(ck,reg);assert ck['steps']==entry['steps']
 binding=reg['violation_critic_amendment']['binding'];learner=restore_learner(ck['learner'],binding,B/'runtime/source_train17_clock',entry['device'],ck['seed']);_,replay_cls=classes(reg);replay=replay_cls(binding['action_dimension'],52,20261078);replay.load_state_dict(ck['replay'])
 initial=learner.state_dict();initial_digest=digest(initial);replay_digest=digest(ck['replay']);assert initial_digest==digest(ck['learner']) and digest(replay.state_dict())==replay_digest
 native=learner.learner;original_rng=capture_rng(learner);original_replay_rng=copy.deepcopy(replay.rng.bit_generator.state);cache=cache_class(DeviceReplayCache)(replay,entry['device']);captured=[]
 def stop_before_zero(*args,**kwargs):
  frame=sys._getframe(1);loc=frame.f_locals
  assert loc['self'] is native and {'data','q_a_values','next_q_value','q_losses','q_loss','indices'}<=set(loc)
  captured.append(dict(q=np.column_stack([x.detach().cpu().numpy() for x in loc['q_a_values']]),target=loc['next_q_value'].detach().cpu().numpy().copy(),native_losses=np.array([float(x) for x in loc['q_losses']],dtype=np.float64),native_loss=float(loc['q_loss']),pair=np.asarray(loc['indices']).copy()))
  raise BeforeOptimization()
 def forbid(*a,**kw):raise AssertionError('Unexpected optimizer/target write attempted')
 replacements=[(native.q_optimizer,'zero_grad',stop_before_zero),(native.q_optimizer,'step',forbid),(native.actor_optimizer,'step',forbid),(native.a_optimizer,'step',forbid),(native,'update_target_networks',forbid)]
 originals=[(obj,key,getattr(obj,key)) for obj,key,_ in replacements]
 for obj,key,value in replacements:setattr(obj,key,value)
 def batch():
  witness=np.random.default_rng();witness.bit_generator.state=copy.deepcopy(replay.rng.bit_generator.state)
  while True:
   indices=witness.integers(replay.size,size=plan['batch_size'])
   if accepted(replay.arrays['masks'],indices):break
  values=cache.sample(plan['batch_size']);assert witness.bit_generator.state==replay.rng.bit_generator.state
  for key,value in values.items():np.testing.assert_array_equal(value.cpu().numpy(),replay.arrays[key][indices])
  captured.clear()
  try:
   with torch.no_grad():learner.update(values)
  except BeforeOptimization:pass
  else:raise AssertionError('Native loss did not stop before optimizer')
  assert len(captured)==1
  return indices,captured.pop()
 records=[];manifest=[];first=None
 try:
  for n in range(plan['batches']):
   assert time.monotonic()-started<plan['budget_seconds']
   idx,c=batch();q=c['q'];target=c['target'];arr=replay.arrays;done=arr['dones'][idx,0].astype(np.uint8);mask=arr['masks'][idx].astype(np.uint8);reward=arr['rewards'][idx,0];bits=arr['observations'][idx,51].astype(np.uint8)
   assert q.shape==(plan['batch_size'],5) and target.shape==(plan['batch_size'],) and np.isfinite(q).all() and np.isfinite(target).all()
   np.testing.assert_array_equal(target[done==1],reward[done==1])
   err=q.astype(np.float64)-target.astype(np.float64)[:,None];weight=mask.astype(np.float64)*(1+127*done.astype(np.float64))[:,None];den=weight.sum(0);contribution=err**2*weight/den;percritic=contribution.sum(0)
   np.testing.assert_allclose(percritic,c['native_losses'],rtol=3e-6,atol=1e-6);assert abs(percritic.sum()-c['native_loss'])<=max(1e-6,3e-6*abs(c['native_loss']))
   perrow=contribution.sum(1);order=np.argsort(-perrow)[:20];groups={}
   for name,sel in [('terminal',done==1),('nonterminal',done==0),('old',idx<entry['parent_steps']),('new92',idx>=entry['parent_steps']),('bit0',bits==0),('bit1',bits==1)]:groups[name]=dict(count=int(sel.sum()),loss=float(perrow[sel].sum()),per_critic=contribution[sel].sum(0).tolist())
   raw=out/'raw'/f'batch_{n:03d}.npz';np.savez_compressed(raw,indices=idx.astype(np.uint32),q=q,target=target,rewards=reward,masks=mask,dones=done,bits=bits,pair=c['pair'],native_losses=c['native_losses'],native_loss=np.asarray(c['native_loss']))
   record=dict(batch=n,native_loss=c['native_loss'],native_losses=c['native_losses'].tolist(),reconstructed_loss=float(perrow.sum()),pair=c['pair'].tolist(),denominators=den.tolist(),groups=groups,top20=[dict(replay_index=int(idx[j]),contribution=float(perrow[j]),terminal=bool(done[j]),violation_bit=int(bits[j]),reward=float(reward[j]),target=float(target[j]),q=q[j].tolist(),mask=mask[j].tolist()) for j in order])
   records.append(record);manifest.append(dict(path=str(raw),bytes=raw.stat().st_size,sha256=sha(raw)))
   if n==0:first=(idx.copy(),{k:copy.deepcopy(v) for k,v in c.items()})
   (out/'PROGRESS.json').write_text(json.dumps(dict(batch=n+1,total=plan['batches'],time=time.time(),native_loss=c['native_loss']))+'\n')
  restore_rng(learner,original_rng);replay.rng.bit_generator.state=copy.deepcopy(original_replay_rng);idx,repeated=batch();np.testing.assert_array_equal(idx,first[0])
  for key,value in first[1].items():np.testing.assert_array_equal(repeated[key],value)
 finally:
  for obj,key,value in originals:setattr(obj,key,value)
  restore_rng(learner,original_rng);replay.rng.bit_generator.state=copy.deepcopy(original_replay_rng)
 assert digest(learner.state_dict())==initial_digest and digest(capture_rng(learner))==digest(original_rng) and digest(replay.state_dict())==replay_digest and digest(ck['replay'])==replay_digest and sha(cp)==entry['checkpoint_sha256']
 losses=np.array([r['native_loss'] for r in records]);summary=dict(mean=float(losses.mean()),minimum=float(losses.min()),maximum=float(losses.max()),std=float(losses.std()),quantiles=np.quantile(losses,[.5,.9,.95,.99]).tolist(),mean_terminal_loss=float(np.mean([r['groups']['terminal']['loss'] for r in records])),mean_nonterminal_loss=float(np.mean([r['groups']['nonterminal']['loss'] for r in records])),target_pairs=sorted({tuple(sorted(r['pair'])) for r in records}),maximum_batch=int(losses.argmax()))
 put(out/'RAW_MANIFEST.json',dict(files=manifest));put(out/'REVIEW.json',dict(passed=True,time=time.time(),method=method,checkpoint_sha256=entry['checkpoint_sha256'],batches=plan['batches'],batch_size=plan['batch_size'],records=records,summary=summary,native_code_sha256=hashlib.sha256(marshal.dumps(native.train.__func__.__code__)).hexdigest(),first_batch_exact_repeat=True,full_learner_optimizer_replay_rng_restored=True,optimizer_updates=0,backward_calls=0,new_physics=0,native_stop_point='before q_optimizer.zero_grad',elapsed_s=time.monotonic()-started,limitation=plan['limitation']))
 print(method,json.dumps(summary))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--method',required=True,choices=['impedance','admittance','vmc']);args=parser.parse_args()
 try:main(args.method)
 except BaseException as e:
  put(O/(args.method+'_FAILURE.json'),dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
