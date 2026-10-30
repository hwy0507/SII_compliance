"""Fixed original87 seen terminals/all5/masks across87/88/89/90; no training."""
from pathlib import Path
import os,sys,json,time,hashlib,math,traceback,gc
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation90_fixed87_terminal_followup_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stats(pred,reward,mask):
 import numpy as np
 e=(pred.astype(np.float64)-reward.astype(np.float64))**2;w=mask.astype(np.float64)
 sse=[math.fsum(float(a)*float(b) for a,b in zip(e[:,j],w[:,j])) for j in range(5)];np.testing.assert_allclose(sse,(e*w).sum(0),rtol=1e-12,atol=1e-8)
 return dict(masked_sse=sse,masked_mse=(np.array(sse)/w.sum(0)).tolist(),all_row_sse=e.sum(0).tolist(),mask_counts=w.sum(0).tolist())
def inputs(plan):
 for n,h in plan['source_hashes'].items():assert sha(D/n)==h
 for n,h in plan['restore_sources'].items():assert sha(Path(plan['restore_runtime'])/n)==h
 for item in plan['inputs']:assert sha(item['path'])==item['sha256']
def complete(plan):
 folder=Path(plan['complete_review']);reports={n:read(folder/n) for n in ['REVIEW.json','FINISHED.json','loss/REVIEW.json','health/DIAGNOSIS.json']}
 for n in ['REVIEW.json','FINISHED.json','loss/REVIEW.json']:assert reports[n].get('passed',reports[n].get('completed',False))
 assert reports['health/DIAGNOSIS.json']['cycle']==90 and reports['health/DIAGNOSIS.json']['optimizer_updates_performed']==0
 for m in plan['methods']:
  r=reports['REVIEW.json']['methods'][m];assert r['checkpoint_sha256']==reports['health/DIAGNOSIS.json']['methods'][m]['checkpoint_sha256']
  assert 0<r['new_transitions']<=41250 and reports['loss/REVIEW.json']['methods'][m]['rows']==r['new_transitions']
 return reports['REVIEW.json']
def baseline(entry):
 import numpy as np
 with np.load(entry['baseline_values']) as saved:old={k:saved[k].copy() for k in ['indices','feature','observations','observations51','actions','rewards','masks','initial_control','complete88','complete89']}
 idx=old['indices'];v=entry['violation_binding'];peaks=np.load(entry['sidecar']['path'],mmap_mode='r');bits=np.load(entry['bits']['path'],mmap_mode='r')
 assert peaks.shape==bits.shape==(v['rows'],2) and len(idx)==entry['terminal_rows'] and old['observations51'].shape==(len(idx),51)
 raw=peaks[idx,0];bit=bits[idx,0];np.testing.assert_array_equal(bit,(raw>.0002).astype(bit.dtype))
 h=(raw/(raw+.0002)).astype(np.float32);np.testing.assert_array_equal(h,old['observations51'][:,50])
 old['observations52']=np.column_stack((old['observations51'],bit.astype(np.float32)));assert old['observations52'].shape==(len(idx),52)
 return old
def preflight(plan):
 import numpy as np
 inputs(plan);prior=read(Path(plan['previous_followup'])/'REVIEW.json');result={}
 for m,entry in plan['methods'].items():
  old=baseline(entry)
  for name in ['initial_control','complete88','complete89']:assert stats(old[name],old['rewards'],old['masks'])==prior['methods'][m]['stats'][name]
  result[m]=dict(terminal_rows=entry['terminal_rows'],original87_88_89_saved_arithmetic_exact=True,all52_inputs_bound_to_original51_and_raw_bits=True,bit_counts={str(int(v)):int((old['observations52'][:,51]==v).sum()) for v in np.unique(old['observations52'][:,51])})
 try:complete(plan)
 except FileNotFoundError:missing=True
 else:raise AssertionError('Expected incomplete90 before this followup; inspect state')
 put(O/'PREFLIGHT_REVIEW.json',dict(passed=True,time=time.time(),methods=result,actual_missing_complete90_rejected=missing,physical_steps=0,optimizer_updates=0,neural_forwards=0))
def run(plan):
 inputs(plan);full=complete(plan);os.sched_setaffinity(0,{11});sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
 import numpy as np
 import torch
 from violation_consumers import restore_learner
 from evaluate_violation90 import validate_recovery
 from validate_published_finite_check_20261025 import digest
 from frozen_helpers import capture_rng
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 torch.set_num_threads(1);started=time.monotonic();fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True);results={}
 for i,(m,entry) in enumerate(plan['methods'].items()):
  assert time.monotonic()-started<plan['analysis_budget_seconds'];cp=Path(entry['checkpoint']);expected=full['methods'][m]['checkpoint_sha256'];assert sha(cp)==expected
  ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration']);binding=reg['violation_critic_amendment']['binding'];assert binding==entry['violation_binding'] and binding['history_binding']==entry['history_binding'];validate_recovery(ck,reg,90)
  assert ck['protocol_sha256']==sha(entry['registration']) and ck['steps']==binding['rows']+full['methods'][m]['new_transitions']
  old=baseline(entry);idx=old['indices'];arr=ck['replay']['arrays'];assert np.array_equal(idx,np.flatnonzero(arr['dones'][:entry['history_binding']['rows'],0]==1))
  np.testing.assert_array_equal(arr['observations'][idx],old['observations52'])
  for k in ['actions','rewards','masks']:np.testing.assert_array_equal(arr[k][idx],old[k])
  learner=restore_learner(ck['learner'],binding,B/'runtime/source_train17_clock',plan['device'],ck['seed']);initial=digest(ck['learner']);rd=digest(ck['replay']);assert digest(learner.state_dict())==initial;rng=digest(capture_rng(learner))
  obs=torch.as_tensor(old['observations52'],device=learner.device);actions=torch.as_tensor(old['actions'],device=learner.device)
  with torch.no_grad():pred=torch.stack([q(obs,actions).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
  assert np.isfinite(pred).all() and digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng and digest(ck['replay'])==rd
  output=O/(m+'_values.npz');np.savez_compressed(output,**old,complete90=pred);statistics={}
  with np.load(output) as saved:
   for label in ['initial_control','complete88','complete89','complete90']:statistics[label]=stats(saved[label],saved['rewards'],saved['masks'])
  for col,key in enumerate(['masked_mse','all_row_sse']):
   ax=axes[i,col]
   for shift,label in [(-.30,'initial_control'),(-.10,'complete88'),(.10,'complete89'),(.30,'complete90')]:ax.bar(np.arange(5)+shift,statistics[label][key],width=.20,label=label)
   ax.set_title(m+' '+key);ax.set_xticks(range(5));ax.set_xlabel('Critic');ax.legend(fontsize=8)
  result=dict(terminal_rows=len(idx),stats=statistics,complete90_minus89_masked_sse=(np.array(statistics['complete90']['masked_sse'])-statistics['complete89']['masked_sse']).tolist(),complete90_minus87_masked_sse=(np.array(statistics['complete90']['masked_sse'])-statistics['initial_control']['masked_sse']).tolist(),checkpoint_sha256=expected,values_sha256=sha(output),original87_terminal_inputs_and_raw_bits_exact=True,full_learner_replay_rng_unchanged=True)
  results[m]=result;put(O/(m+'_REVIEW.json'),result);assert sha(cp)==expected;del ck,arr,learner,obs,actions;gc.collect();torch.cuda.empty_cache()
 fig.savefig(O/'fixed87_terminal_87_88_89_90.png',dpi=150);plt.close(fig)
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,elapsed_s=time.monotonic()-started,plot_sha256=sha(O/'fixed87_terminal_87_88_89_90.png'),plot_viewed=False,physical_steps=0,optimizer_updates=0,limits=plan['limits']))
if __name__=='__main__':
 plan=read(O/'PLAN.json')
 try:
  if '--preflight' in sys.argv:preflight(plan)
  else:run(plan)
 except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
