"""Fixed original87 terminal inputs, original masks, all five critics:87/88/89."""
from pathlib import Path
import os,sys,json,time,hashlib,math,traceback,gc
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/history89_fixed87_terminal_followup_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stats(pred,reward,mask):
 import numpy as np
 e=(pred.astype(np.float64)-reward.astype(np.float64))**2;w=mask.astype(np.float64)
 sse=[math.fsum(float(a)*float(b) for a,b in zip(e[:,j],w[:,j])) for j in range(5)];np.testing.assert_allclose(sse,(e*w).sum(0),rtol=1e-12,atol=1e-8)
 return dict(masked_sse=sse,masked_mse=(np.array(sse)/w.sum(0)).tolist(),all_row_sse=e.sum(0).tolist(),mask_counts=w.sum(0).tolist())
def inputs(plan):
 for name,h in plan['source_hashes'].items():assert sha(D/name)==h
 for name,h in plan['restore_sources'].items():assert sha(Path(plan['restore_runtime'])/name)==h
 for item in plan['inputs']:assert sha(item['path'])==item['sha256']
 return True
def complete(plan):
 folder=Path(plan['complete_review'])
 reports={name:read(folder/name) for name in ['REVIEW.json','FINISHED.json','loss/REVIEW.json','health/DIAGNOSIS.json']}
 for name in ['REVIEW.json','FINISHED.json','loss/REVIEW.json']:assert reports[name].get('passed',reports[name].get('completed',False))
 for m in plan['methods']:
  assert reports['REVIEW.json']['methods'][m]['checkpoint_sha256']==reports['health/DIAGNOSIS.json']['methods'][m]['checkpoint_sha256']
 return reports['REVIEW.json']
def preflight(plan):
 import numpy as np
 inputs(plan);old=read(Path(plan['previous_followup'])/'REVIEW.json');result={}
 for m,entry in plan['methods'].items():
  with np.load(entry['baseline_values']) as saved:
   assert len(saved['indices'])==entry['terminal_rows'] and saved['observations51'].shape==(entry['terminal_rows'],51)
   for name in ['initial_control','complete88']:
    actual=stats(saved[name],saved['rewards'],saved['masks']);assert actual==old['methods'][m]['stats'][name]
  result[m]=dict(terminal_rows=entry['terminal_rows'],original87_and_complete88_saved_arithmetic_exact=True)
 try:complete(plan)
 except FileNotFoundError:missing_rejected=True
 else:raise AssertionError('Expected incomplete89 before registration; inspect state')
 put(O/'PREFLIGHT_REVIEW.json',dict(passed=True,time=time.time(),methods=result,actual_missing_complete89_rejected=missing_rejected,physical_steps=0,optimizer_updates=0,neural_forwards=0))
def run(plan):
 inputs(plan);full=complete(plan);os.sched_setaffinity(0,{11});sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
 import numpy as np
 import torch
 from history_consumers import restore_learner
 from validate_published_finite_check_20261025 import digest
 from frozen_helpers import capture_rng
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 torch.set_num_threads(1);started=time.monotonic();fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True);results={}
 for i,(m,entry) in enumerate(plan['methods'].items()):
  assert time.monotonic()-started<plan['analysis_budget_seconds'];cp=Path(entry['checkpoint']);expected=full['methods'][m]['checkpoint_sha256'];assert sha(cp)==expected
  ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(entry['registration']);binding=reg['history_critic_amendment']['binding'];assert binding==entry['binding']
  assert ck['cycle']==89 and ck['boundary']=='complete_condition_cycle' and ck['steps']==binding['rows']+82500 and ck['protocol_sha256']==sha(entry['registration']) and ck['recovery_continuation']==reg['post_interruption_continuation']
  with np.load(entry['baseline_values']) as saved:old={k:saved[k].copy() for k in ['indices','feature','observations','observations51','actions','rewards','masks','initial_control','complete88']}
  idx=old['indices'];arr=ck['replay']['arrays'];assert len(idx)==entry['terminal_rows'] and np.array_equal(idx,np.flatnonzero(arr['dones'][:binding['rows'],0]==1))
  np.testing.assert_array_equal(arr['observations'][idx],old['observations51'])
  for k in ['actions','rewards','masks']:np.testing.assert_array_equal(arr[k][idx],old[k])
  learner=restore_learner(ck['learner'],binding,B/'runtime/source_train17_clock',plan['device'],ck['seed']);initial=digest(ck['learner']);assert digest(learner.state_dict())==initial;rng=digest(capture_rng(learner))
  obs=torch.as_tensor(old['observations51'],device=learner.device);actions=torch.as_tensor(old['actions'],device=learner.device)
  with torch.no_grad():pred=torch.stack([q(obs,actions).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
  assert np.isfinite(pred).all() and digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng
  output=O/(m+'_values.npz');np.savez_compressed(output,**old,complete89=pred);statistics={}
  with np.load(output) as saved:
   for label in ['initial_control','complete88','complete89']:statistics[label]=stats(saved[label],saved['rewards'],saved['masks'])
  for col,key in enumerate(['masked_mse','all_row_sse']):
   ax=axes[i,col]
   for shift,label in [(-.24,'initial_control'),(0,'complete88'),(.24,'complete89')]:ax.bar(np.arange(5)+shift,statistics[label][key],width=.24,label=label)
   ax.set_title(m+' '+key);ax.set_xticks(range(5));ax.set_xlabel('Critic');ax.legend(fontsize=8)
  result=dict(terminal_rows=len(idx),stats=statistics,complete89_minus88_masked_sse=(np.array(statistics['complete89']['masked_sse'])-statistics['complete88']['masked_sse']).tolist(),complete89_minus87_masked_sse=(np.array(statistics['complete89']['masked_sse'])-statistics['initial_control']['masked_sse']).tolist(),checkpoint_sha256=expected,values_sha256=sha(output),original87_terminal_inputs_exact=True,full_learner_and_rng_unchanged=True)
  results[m]=result;put(O/(m+'_REVIEW.json'),result);assert sha(cp)==expected;del ck,arr,learner,obs,actions;gc.collect();torch.cuda.empty_cache()
 fig.savefig(O/'fixed87_terminal_87_88_89.png',dpi=150);plt.close(fig)
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,elapsed_s=time.monotonic()-started,plot_sha256=sha(O/'fixed87_terminal_87_88_89.png'),plot_viewed=False,physical_steps=0,optimizer_updates=0,limits=plan['limits']))
if __name__=='__main__':
 plan=read(O/'PLAN.json')
 try:
  if '--preflight' in sys.argv:preflight(plan)
  else:run(plan)
 except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
