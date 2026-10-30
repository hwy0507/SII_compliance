"""Require full86 interpretation, completed original76–78/79–81 and unchanged prospective82–84; no automatic training."""
from pathlib import Path
import json,time,hashlib,argparse
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;PREP=B/'runtime/prepare_recovery87_20261030_v1';PARENT=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle87_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1';LOSS=B/'runs/parameter_recovery86_loss_20261029_v1';LABEL=B/'runs/parameter_recovery86_task_labels_20261029_v1';WINDOW=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def require_completed82_84(required):
 window=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1'
 assert sha(window/'PLAN.json')=='ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c'
 assert (window/'REVIEW.json').exists(),'Original82-84 complete result not ready'
 for key,name in [('result','REVIEW.json'),('saved','SAVED_ARITHMETIC_REVIEW.json'),('plot','PLOT_INSPECTION.json')]:required['completed82_84_'+key]=window/name
 assert read(required['completed82_84_result'])['passed'] and read(required['completed82_84_saved'])['passed']
 assert read(required['completed82_84_plot'])['actual_image_viewed']
 scalar=B/'runs/recovery82_84_bootstrap_scalar_review_20261030_v1'
 assert read(scalar/'FINISHED.json')['passed'] and read(scalar/'REVIEW.json')['passed']
 required['completed82_84_scalar']=scalar/'REVIEW.json';required['completed82_84_scalar_finished']=scalar/'FINISHED.json'
 follow=B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='6e9a91573eb88c6080eb885b9c6ece64d40e160c381297f9c2c648676dc7b66c'
 plan=read(follow/'PLAN.json');assert plan['fixed_rows']==2454 and plan['all_critics']==[0,1,2,3,4] and plan['checkpoint_cycles']==[82,83,84] and plan['registered_before_complete84']
 assert read(follow/'FINISHED.json')['passed'] and read(follow/'REVIEW.json')['passed'] and read(follow/'SAVED_REVIEW.json')['passed']
 for key,name in [('plan','PLAN.json'),('result','REVIEW.json'),('saved','SAVED_REVIEW.json'),('finished','FINISHED.json')]:required['fixed2454_82_84_'+key]=follow/name
 required['old83_population']=B/'runs/recovery82_83_old_terminal_population_20261030_v1/REVIEW.json'
 required['old83_population_saved']=B/'runs/recovery82_83_old_terminal_population_20261030_v1/SAVED_REVIEW.json'
 assert read(required['old83_population'])['passed'] and read(required['old83_population_saved'])['passed']
def require_input_followup85(required):
 follow=B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='7703cce3f9428f187fdd796df22e540eb945411b55108cf7e8d3aaee70306494'
 assert (follow/'FINISHED.json').exists(),'Complete85 fixed2514 input followup not ready'
 assert read(follow/'FINISHED.json')['passed'] and read(follow/'REVIEW.json')['passed'] and read(follow/'SAVED_REVIEW.json')['passed']
 p=read(follow/'PLAN.json');assert p['fixed_rows']==2514 and p['all_critics']==[0,1,2,3,4] and p['cycles']==[84,85] and p['registered_before_complete85']
 for n in ['PLAN.json','REVIEW.json','SAVED_REVIEW.json','FINISHED.json']:required['fixed2514_input85_'+n]=follow/n
 diag=B/'runs/recovery83_84_terminal_behavior_alignment_20261030_v1'
 for n in ['REVIEW.json','UPDATE_AVAILABILITY_REVIEW.json','INPUT_REVIEW.json','INPUT_SAVED_REVIEW.json','GRADIENT_REVIEW.json','GRADIENT_SAVED_REVIEW.json']:
  assert read(diag/n)['passed'];required['input_gradient84_'+n]=diag/n
 assert read(diag/'PLOT_INSPECTION.json')['actual_image_viewed'];required['input_gradient84_plot']=diag/'PLOT_INSPECTION.json'
 window=B/'runs/parameter_recovery85_87_reward_stability_20261030_v1'
 assert sha(window/'PLAN.json')=='6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e'
 p=read(window/'PLAN.json');assert p['cycles']==[85,86,87] and p['bootstrap_seed']==2026102858
 required['prospective85_87_plan']=window/'PLAN.json'
def require_fixed_followup86(required):
 follow=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1'
 assert sha(follow/'PLAN.json')=='2f7c719eb64c36ce20b8135ca5d18748c0683bb4bf45d6e44a2f953ce44e5041'
 assert (follow/'FINISHED.json').exists(),'Complete86 fixed2514 followup not ready'
 for n in ['FINISHED.json','REVIEW.json','SAVED_REVIEW.json']:
  assert read(follow/n)['passed'];required['fixed2514_84_86_'+n]=follow/n
 p=read(follow/'PLAN.json');assert p['fixed_rows']==2514 and p['all_critics']==[0,1,2,3,4] and p['checkpoint_cycles']==[84,85,86] and p['registered_before_complete86']
 required['fixed2514_84_86_plan']=follow/'PLAN.json'
 plot=follow/'PLOT_INSPECTION.json'
 assert plot.exists() and read(plot)['actual_image_viewed'],'Actual fixed2514 84-86 plot inspection required'
 required['fixed2514_84_86_plot']=plot
def collect():
 assert (PARENT/'ARCHIVE_REVIEW_FINISHED.json').exists(),'Complete86 archive/review not ready'
 assert read(PARENT/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(REV/'FINISHED.json')['completed'] and read(REV/'REVIEW.json')['passed']
 assert read(PREP/'FINISHED.json')['prepared'] and read(OUT/'CHECK_ONLY_COMPLETE.json')['passed']
 assert all(x==0 for x in read(OUT/'CHECK_ONLY_EXIT_CODES.json').values())
 evidence={};prior=B/'runtime/recovery86_completion_preparation_20261030_v1/DECISION86.json';old=read(prior);assert old['passed'] and old['parent_cycle']==85 and old['new_cycle']==86 and not old['configuration_changed'] and not old['automatic_followup'];evidence['prior86_decision']=ref(prior)
 for k,v in old['evidence'].items():assert sha(v['path'])==v['sha256'];evidence['prior86_'+k]=v
 required=dict(parent_review=REV/'REVIEW.json',health=REV/'health/DIAGNOSIS.json',health_plot=REV/'health/PLOT_INSPECTION.json',loss=LOSS/'REVIEW.json',paired_gate=LOSS/'PAIRED_GATE_REVIEW.json',saved_loss=LOSS/'SAVED_REVIEW.json',loss_plot=LOSS/'PLOT_INSPECTION.json',all_labels=LABEL/'COMPLETE85_86.json',all_labels_saved=LABEL/'COMPLETE85_86_SAVED_REVIEW.json',labels_finished=LABEL/'FINISHED.json',check_only=OUT/'CHECK_ONLY_COMPLETE.json',prepare_finished=PREP/'FINISHED.json',original_window76_78_plan=WINDOW/'PLAN.json',original_window76_78_result=WINDOW/'REVIEW.json',original_window76_78_saved=WINDOW/'SAVED_ARITHMETIC_REVIEW.json',original_window76_78_plot=WINDOW/'PLOT_INSPECTION.json',interrupted_window=B/'runtime/parameter75_interruption_recovery_20261029_v1/ORIGINAL_WINDOW_INTERRUPTED.json',launcher_sources=D/'LAUNCH_SOURCE_REVIEW.json')
 required['prospective79_81_plan']=B/'runs/parameter_recovery79_81_reward_stability_20261030_v1/PLAN.json'
 assert sha(required['prospective79_81_plan'])=='5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0' and read(required['prospective79_81_plan'])['cycles']==[79,80,81]
 for suffix,name in [('result','REVIEW.json'),('saved','SAVED_ARITHMETIC_REVIEW.json'),('plot','PLOT_INSPECTION.json')]:required['completed79_81_'+suffix]=required['prospective79_81_plan'].parent/name
 required['prospective82_84_plan']=B/'runs/parameter_recovery82_84_reward_stability_20261030_v1/PLAN.json'
 assert sha(required['prospective82_84_plan'])=='ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c' and read(required['prospective82_84_plan'])['cycles']==[82,83,84]
 assert read(required['completed79_81_result'])['passed'] and read(required['completed79_81_saved'])['passed'], 'Complete original79-81 arithmetic required'
 for m in ['impedance','admittance','vmc']:required['restore_'+m]=OUT/m/'CHECK_ONLY_REVIEW.json'
 for m in ['vmc','admittance']:
  p=B/f'runs/{m}_recovery86_terminal_followup_20261029_v1'
  for suffix,n in [('review','REVIEW.json'),('saved','SAVED_VALUES_REVIEW.json'),('plot','PLOT_INSPECTION.json'),('plan','PLAN.json'),('anchor','ANCHOR_SAVED_REVIEW.json')]:required[m+'_terminal_'+suffix]=p/n
  assert read(p/'FINISHED.json')['completed'] and read(p/'SAVED_VALUES_REVIEW.json')['passed']
  r=read(p/'REVIEW.json');assert r['passed'] and r['fixed_anchor_rows']==2544 and r['new_terminal_rows']==30
 required['original76_81_scalar_bootstrap']=B/'runs/recovery76_81_bootstrap_scalar_review_20261030_v1/REVIEW.json'
 assert read(required['original76_81_scalar_bootstrap'])['passed']
 required['frozen82_preregistration']=B/'runs/parameter82_frozen_full30_20261030_v1/PRE_REGISTRATION.json'
 assert sha(required['frozen82_preregistration'])=='baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76'
 require_completed82_84(required)
 require_input_followup85(required)
 require_fixed_followup86(required)
 for k,p in required.items():evidence[k]=ref(p)
 assert read(LOSS/'SAVED_REVIEW.json')['passed'] and read(LOSS/'PAIRED_GATE_REVIEW.json')['passed']
 assert read(LABEL/'FINISHED.json')['completed'] and read(LABEL/'COMPLETE85_86_SAVED_REVIEW.json')['passed']
 assert not read(required['interrupted_window'])['assessable']
 assert sha(WINDOW/'PLAN.json')=='57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85' and read(WINDOW/'PLAN.json')['cycles']==[76,77,78]
 assert read(WINDOW/'REVIEW.json')['passed'] and read(WINDOW/'SAVED_ARITHMETIC_REVIEW.json')['passed']
 for key in ['health_plot','loss_plot','vmc_terminal_plot','admittance_terminal_plot','original_window76_78_plot','completed79_81_plot']:assert read(required[key])['actual_image_viewed']
 full=read(REV/'REVIEW.json');health=read(REV/'health/DIAGNOSIS.json')
 for m,r in full['methods'].items():
  assert r['new_transitions']==41250 and r['retained_replay_all_fields_exact'] and r['max_reward_reconstruction_error']==0 and r['optimizer_and_network_finite']
  assert r['full_horizon_count']==30 and r['aborts']==[] and health['methods'][m]['network_state_unchanged']
  assert r['checkpoint_sha256']==health['methods'][m]['checkpoint_sha256']
  ck=read(OUT/m/'CHECK_ONLY_REVIEW.json');assert ck['passed'] and ck['full_learner_state_exact'] and ck['full_replay_and_next65536_exact'] and ck['negative_rejections']==9 and ck['checkpoint_sha256']==r['checkpoint_sha256']
  p=read(OUT/m/'REGISTRATION.json');assert p['post_interruption_continuation']['checkpoint']['sha256']==r['checkpoint_sha256']
 for j in read(PARENT/'LAUNCH.json')['jobs']:
  p=Path(f'/proc/{j["pid"]}/stat')
  if p.exists():
   f=p.read_text().rsplit(')',1)[1].split();assert f[19]!=j['proc_start_ticks'] or f[0]=='Z','Original86 still running'
 for x in read(D/'LAUNCH_SOURCE_REVIEW.json')['files']:assert sha(x['path'])==x['sha256']
 reason=D/'CONTINUATION_REASON.txt';assert reason.exists() and len(reason.read_text().strip())>100,'Actual full86, completed82–84 and fixed2514 input/gradient followup interpretation required'
 evidence['continuation_reason']=ref(reason)
 return evidence
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');a=parser.parse_args();evidence=collect()
 if a.write:
  decision=dict(time=time.time(),passed=True,parent_cycle=86,new_cycle=87,new_cycles=1,plot_inspected=True,convergence_claim=False,configuration_changed=False,automatic_followup=False,direct34=False,original76_78_window_completed_and_reviewed=True,original79_81_window_completed_and_reviewed=True,original82_84_window_completed_and_reviewed=True,fixed2454_critic_followup_reviewed=True,fixed2514_input_followup85_reviewed=True,fixed2514_84_86_reviewed=True,evidence=evidence,reason=(D/'CONTINUATION_REASON.txt').read_text().strip())
  with (D/'DECISION87.json').open('x') as f:f.write(json.dumps(decision,indent=2)+'\n')
 print('Full86, original76–78, completed79–81 and exact87 readiness checked; automatic training false')
