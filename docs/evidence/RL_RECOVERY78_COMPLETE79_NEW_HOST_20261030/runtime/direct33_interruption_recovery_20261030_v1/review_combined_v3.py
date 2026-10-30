from pathlib import Path
import json,time,hashlib,os,sys
os.sched_setaffinity(0,{3})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;F=B/'runs/serl_take33_frozen_full30_20261029_v1';O=B/'runs/serl_take33_frozen_combined_review_20261030_v3'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,j):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['start'] and s[0]!='Z'
try:
 plan=read(O/'PLAN.json');registration=read(F/'REGISTRATION.json');source_plan=read(O/'COMBINED_REVIEW_PLAN.json')
 for x in source_plan['sources']+source_plan['inputs']:assert sha(x['path'])==x['sha256']
 deadline=time.monotonic()+21600;jobs=read(O/'LAUNCH.json')['jobs'];replayjob=read(O/'REPLAY_LAUNCH.json')
 targets=[(Path(j['output'])/'POLICY_UNCHANGED.json',j,Path(j['output'])/'FAILURE.json') for j in jobs]+[(O/'saved28_replay/CHECK_ONLY_REVIEW.json',replayjob,O/'saved28_replay/FAILURE.json')]
 for target,job,failure in targets:
  while not target.exists():
   assert not failure.exists(),str(failure);assert live(job),'Original recovery process missing before completion';assert time.monotonic()<deadline,'Observation expired; no automatic science restart';time.sleep(5)
 rp=read(O/'saved28_replay/SAVED28_ACTION_REPLAY.json');assert rp['passed'] and rp['all_saved_actions_exact'] and rp['replay_learner_state_unchanged'];assert len(rp['episodes'])==28
 replaymap={x['case']:x for x in rp['episodes']};check=read(F/'check_only/FULL_STATE_RESTORE.json');assert read(O/'saved28_replay/FULL_STATE_RESTORE.json')==check
 for x in list(registration['inputs'].values())+list(registration['sources'].values()):assert sha(x['path'])==x['sha256']
 protocol=read(registration['inputs']['training_registration']['path']);conditions={x['id']:x for x in protocol['conditions']};sys.path[:0]=[registration['evaluation_runtime'],str(Path(protocol['runtime'])/'source/tools')]
 from summarize_published_episode_audit_20261025 import summarize
 from replay_published_filter_audit_20261025 import audit as filter_audit
 from replay_published_torque_audit_20261025 import audit as torque_audit
 shards=[]
 for old in plan['original_shards']:
  folder=Path(old['original_job']['output']);assert read(folder/'FULL_STATE_RESTORE.json')==check;assert sha(old['results']['path'])==old['results']['sha256'];result=read(folder/'RESULTS.json');assert len(result['episodes'])==14;shards.append((folder,result,False))
 for job in jobs:
  folder=Path(job['output']);restore=read(folder/'FULL_STATE_RESTORE.json');assert restore==check;state=read(folder/'POLICY_UNCHANGED.json');gate=read(folder/'EXTERNAL_ACTION_RNG_GATE.json');assert state['full_learner_state_unchanged'] and state['full_replay_state_unchanged'] and state['new_optimizer_updates']==state['replay_writes']==0;assert state['initial_state_digest']==state['final_state_digest']==check['learner_digest'];assert state['replay_digest']==check['replay_digest'] and state['history_digest']==check['history_digest'];assert gate['passed'] and gate['full_state_unchanged'];result=read(folder/'RESULTS.json');assert result['finished'] and len(result['episodes'])==1;assert result['evaluation']['case_ids']==job['case_ids'];shards.append((folder,result,True))
 rows=[];seen=set()
 for folder,result,new in shards:
  evaluation=result['evaluation'];assert evaluation['checkpoint_sha256']==check['checkpoint_sha256'] and evaluation['action_seed']==2026102626 and evaluation['noise_schedule']=='independent' and not evaluation['deterministic'] and evaluation['audit_substeps'];assert sha(folder/'checkpoint_frozen.pt')==check['checkpoint_sha256'];assert evaluation['registration_sha256']==registration['inputs']['training_registration']['sha256']
  for episode in result['episodes']:
   case=episode['condition'];assert case in conditions and case not in seen;seen.add(case);path=folder/case
   if not new:assert sha(path/'actor_intervals.jsonl')==replaymap[case]['journal_sha256'] and episode['actions']==replaymap[case]['actions']
   assert sha(path/'rollout.mjb')==conditions[case]['model_sha256'];physical=summarize(path,'direct33_interruption_recovered_frozen',case);filtered=filter_audit(path);torque=torque_audit(path);assert filtered['passed'] and torque['passed'];assert 0<physical['samples']<=1100000 and physical['row']['elapsed_s']<=55.000001
   audit=O/'combined_audits'/case/'FROZEN_PHYSICAL_REVIEW.json';put(audit,dict(physical=physical,filter=filtered,torque=torque,source_episode=str(path),original_complete=not new))
   rows.append(dict(case=case,category=conditions[case]['category'],actions=episode['actions'],samples=physical['samples'],row=physical['row'],audit=ref(audit)))
   (O/'COMBINED_REVIEW_PROGRESS.json').write_text(json.dumps(dict(time=time.time(),reviewed=len(rows),maximum=30))+'\n')
 assert len(rows)==30 and seen==conditions.keys();assert sum(x['actions'] for x in rows)<=41250 and sum(x['samples'] for x in rows)<=33000000
 for x in plan['original_shards']:
  for key in ['results','partial_journal','partial_raw_audit']:assert sha(x[key]['path'])==x[key]['sha256']
 report=dict(passed=True,time=time.time(),episodes=rows,physical_samples=sum(x['samples'] for x in rows),task=sum(x['row']['task_success'] for x in rows),strict=sum(x['row']['strict_success'] for x in rows),full_horizon=sum(x['row']['full_horizon'] for x in rows),machine_violations=sum(x['row']['machine_safety_violation'] for x in rows),checkpoint_sha256=check['checkpoint_sha256'],full_training_cohort=True,independent_training_seeds=1,external_action_seeds=1,optimizer_updates=0,replay_writes=0,formal_state_unchanged=False,original_final_inmemory_state_unavailable=True,all28_original_saved_actions_reproduced_exactly=True,new2_full_state_unchanged=True,action_replay=ref(O/'saved28_replay/SAVED28_ACTION_REPLAY.json'),original_completed=28,recovered_completed=2,additional_interrupted_prefix_actions=sum(x['partial_actor_rows'] for x in plan['original_shards']),convergence_claim=False,limitation='All30 training conditions composed of28 original completed episodes and2 restarted incomplete episodes after container loss. Original final in-memory invariant unavailable; all28 saved actions independently reproduced exactly from frozen33. New2 final fullstate invariants passed. Original partial prefixes preserved as additional exposure, not completed denominators. No finalSPT reference or ESN comparison; saved-substep arithmetic/filter/torque audit is not independent dynamics integration.')
 put(O/'REVIEW.json',report);print('Combined30 reviewed; original missing state invariant explicitly retained',flush=True)
except BaseException as e:put(O/'COMBINED_REVIEW_FAILURE.json',dict(time=time.time(),error=repr(e)));raise
