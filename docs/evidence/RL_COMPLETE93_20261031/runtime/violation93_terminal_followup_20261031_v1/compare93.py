"""Compare all fixed92 terminals against complete93, preserving all masks and failures."""
from pathlib import Path
import gc,hashlib,json,math,os,sys,time,traceback
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def validate_architecture93(ck,reg):
 from persisted_history_critic import KEY as HK,marker as hm
 from persisted_violation_critic import KEY as VK,marker as vm
 from parameter_replay_capacity_20261026 import MARKER as CAP2
 from parameter_replay_capacity4m_20261027 import MARKER as CAP4
 h=reg['history_critic_amendment'];v=reg['violation_critic_amendment'];st=reg['post_interruption_continuation'];m=st['controller']
 assert h['first_cycle']==88 and v['first_cycle']==90 and v['binding']['history_binding']==h['binding']
 assert ck['history_critic_amendment']==h and ck['violation_critic_amendment']==v
 assert ck['controller']==m==v['binding']['method'] and ck['seed']==20261025 and ck['cycle']==93
 assert sha(st['cycle_review']['path'])==st['cycle_review']['sha256'];parent=read(st['cycle_review']['path'])['methods'][m]
 assert parent['checkpoint_sha256']==st['checkpoint']['sha256'] and parent['steps']<ck['steps']<=parent['steps']+41250
 assert sha(st['parent_registration']['path'])==st['parent_registration']['sha256']
 previous=read(st['parent_registration']['path']);old=read(previous['post_interruption_continuation']['cycle_review']['path'])['methods'][m];assert old['steps']+parent['new_transitions']==parent['steps']
 assert (st['parent_cycle'],st['new_cycle'],st['new_cycles'],st['maximum_new_actions'],st['automatic_followup'],st['optimizer_settings_changed'])==(92,93,1,41250,False,False)
 assert ck['protocol_sha256']==sha(B/'runs/parameter_violation_cycle93_20261031_v1'/m/'REGISTRATION.json')
 assert ck['recovery_continuation']==st and ck['interruption_recovery']==reg['interrupted_episode_recovery'] and ck['environment_state_saved'] is False
 for key in ['learner','replay']:assert ck[key][HK]==hm(h['binding']) and ck[key][VK]==vm(v['binding'])
 replay=ck['replay'];assert replay['size']==replay['cursor']==ck['steps'] and replay['capacity']==4000000 and replay['replay_capacity_extension']==CAP2 and replay['replay_capacity_followup']==CAP4
 for key in ['observations','next_observations']:assert replay['arrays'][key].shape==(ck['steps'],52)
 assert not any(c['cycle']==75 for c in ck['cycles'])
def validate_complete93(ck,reg):
 validate_architecture93(ck,reg);assert ck['boundary']=='complete_condition_cycle' and ck['cycles'][-1]['cycle']==93
def inputs(plan):
 for n,h in plan['source_hashes'].items():assert sha(D/n)==h,n
 for p,h in plan['dependencies'].items():assert sha(p)==h,p
 for item in plan['inputs']:assert sha(item['path'])==item['sha256']
def stats(pred,reward,mask):
 import numpy as np
 error=(pred.astype(np.float64)-reward.astype(np.float64)[:,None])**2;weighted=error*mask
 return dict(masked_sse=[math.fsum(weighted[:,j]) for j in range(5)],all_row_sse=[math.fsum(error[:,j]) for j in range(5)],mask_counts=mask.sum(0).tolist(),total_masked_sse=math.fsum(weighted.reshape(-1)))
def complete(plan):
 v=Path(plan['complete_review']);full=read(v/'REVIEW.json');finish=read(v/'FINISHED.json');loss=read(v/'loss/REVIEW.json');health=read(v/'health/DIAGNOSIS.json')
 assert full['passed'] and finish['completed'] and loss['passed'] and health['cycle']==93 and health['optimizer_updates_performed']==0
 for m in plan['methods']:
  x=full['methods'][m];assert x['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256'] and 0<x['new_transitions']<=41250 and x['new_transitions']==loss['methods'][m]['rows']
 return full
def baseline(entry):
 import numpy as np
 with np.load(entry['baseline_values']) as z:old={k:z[k].copy() for k in ['indices','observations','actions','rewards','masks','predictions']}
 assert len(old['indices'])==entry['terminal_rows'] and old['observations'].shape==(entry['terminal_rows'],52)
 report=read(entry['baseline_review']);s=stats(old['predictions'],old['rewards'],old['masks']);np.testing.assert_allclose(s['masked_sse'],report['groups']['all']['per_critic_masked_sse'],rtol=1e-12,atol=1e-8);np.testing.assert_allclose(s['all_row_sse'],report['groups']['all']['all_row_sse'],rtol=1e-12,atol=1e-8)
 return old,s
def preflight(plan):
 inputs(plan);results={}
 for m,e in plan['methods'].items():
  old,s=baseline(e);results[m]=dict(terminal_rows=len(old['indices']),saved92_arithmetic_checked=True,all_masks_and_failed_rows_retained=True,stats=s)
 try:complete(plan)
 except FileNotFoundError:missing=True
 else:raise AssertionError('Expected actual incomplete93 at preregistration')
 put(O/'PREFLIGHT_REVIEW.json',dict(passed=True,time=time.time(),methods=results,actual_missing_complete93_rejected=missing,new_physics=0,optimizer_updates=0,neural_forwards=0))
def run(plan):
 inputs(plan);full=complete(plan);os.sched_setaffinity(0,{11});sys.path[:0]=[plan['restore_runtime'],str(B/'runtime/source_train17_clock/source/tools')]
 import numpy as np
 import torch
 from violation_consumers import restore_learner
 from frozen_helpers import capture_rng
 from validate_published_finite_check_20261025 import digest
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 torch.set_num_threads(1);started=time.monotonic();fig,axes=plt.subplots(3,2,figsize=(14,11),constrained_layout=True);results={}
 for row,(m,e) in enumerate(plan['methods'].items()):
  assert time.monotonic()-started<plan['analysis_budget_seconds'];cp=Path(e['checkpoint']);expected=full['methods'][m]['checkpoint_sha256'];assert sha(cp)==expected
  ck=torch.load(cp,map_location='cpu',weights_only=False);reg=read(e['registration']);validate_complete93(ck,reg);old,s92=baseline(e);idx=old['indices'];arr=ck['replay']['arrays'];assert np.array_equal(idx,np.flatnonzero(arr['dones'][:e['parent_steps'],0]==1))
  for name in ['observations','actions','masks']:np.testing.assert_array_equal(arr[name][idx],old[name])
  np.testing.assert_array_equal(arr['rewards'][idx,0],old['rewards'])
  learner=restore_learner(ck['learner'],reg['violation_critic_amendment']['binding'],B/'runtime/source_train17_clock',plan['device'],ck['seed']);initial=digest(ck['learner']);rd=digest(ck['replay']);assert digest(learner.state_dict())==initial;rng=digest(capture_rng(learner))
  obs=torch.as_tensor(old['observations'],device=learner.device);act=torch.as_tensor(old['actions'],device=learner.device)
  with torch.no_grad():pred=torch.stack([q(obs,act).reshape(-1) for q in learner.learner.agent.ensemble],1).cpu().numpy()
  assert np.isfinite(pred).all() and digest(learner.state_dict())==initial and digest(capture_rng(learner))==rng and digest(ck['replay'])==rd and sha(cp)==expected
  s93=stats(pred,old['rewards'],old['masks']);out=O/(m+'_values.npz');np.savez_compressed(out,indices=idx,observations=old['observations'],actions=old['actions'],rewards=old['rewards'],masks=old['masks'],complete92=old['predictions'],complete93=pred)
  perrow92=(((old['predictions'].astype(float)-old['rewards'][:,None])**2)*old['masks']).sum(1);perrow93=(((pred.astype(float)-old['rewards'][:,None])**2)*old['masks']).sum(1);known=[]
  for abort in e['known_aborts']:
   where=np.flatnonzero(idx==abort['replay_index']);assert len(where)==1;j=int(where[0]);known.append(dict(cycle=abort['cycle'],replay_index=abort['replay_index'],mask=old['masks'][j].tolist(),reward=float(old['rewards'][j]),q92=old['predictions'][j].tolist(),q93=pred[j].tolist(),masked_sse92=float(perrow92[j]),masked_sse93=float(perrow93[j])))
  for col,key in enumerate(['masked_sse','all_row_sse']):
   ax=axes[row,col];ax.bar(np.arange(5)-.18,s92[key],width=.36,label='full92');ax.bar(np.arange(5)+.18,s93[key],width=.36,label='full93');ax.set_title(m+' fixed92 '+key);ax.set_xlabel('Zero-based critic');ax.legend();ax.grid(alpha=.2)
  result=dict(terminal_rows=len(idx),stats=dict(complete92=s92,complete93=s93),known_aborts=known,checkpoint_sha256=expected,values_sha256=sha(out),all92_terminal_inputs_exact=True,full_learner_optimizer_replay_rng_unchanged=True,optimizer_updates=0,new_physics=0);results[m]=result;put(O/(m+'_REVIEW.json'),result)
  del ck,arr,learner,obs,act;gc.collect();torch.cuda.empty_cache()
 fig.suptitle('Fixed all8263 seen92 terminals, original masks/all five critics; zero updates\nAll regressions retained; not policy safety or an extra convergence gate');fig.savefig(O/'fixed92_terminal_92_93.png',dpi=150);plt.close(fig)
 put(O/'REVIEW.json',dict(passed=True,time=time.time(),methods=results,elapsed_s=time.monotonic()-started,plot_sha256=sha(O/'fixed92_terminal_92_93.png'),actual_plot_inspection_pending=True,new_physics=0,optimizer_updates=0,convergence_claim=False))
if __name__=='__main__':
 plan=read(O/'PLAN.json')
 try:
  if '--preflight' in sys.argv:preflight(plan)
  else:run(plan)
 except BaseException as e:put(O/('FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
