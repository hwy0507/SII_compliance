from pathlib import Path
import sys,os,time,json,copy,gc,traceback
D=Path(__file__).parent;B=D.parents[1]
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.sched_setaffinity(0,{53})
sys.path[:0]=[str(D),str(B/'runtime/parameter86_half_std_paired_20261030_v3'),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from persisted_history_critic import sha,feature
from history_consumers import restore_learner,frozen_event,terminal_health
from published_compliance_learner_20261025 import PublishedLearner
from published_pair_reduction_learner_20261026 import pair_class
from evaluate_parameter29_seeded_switch_20261026 import ExternalActions
from validate_published_finite_check_20261025 import digest
read=lambda p:json.loads(Path(p).read_text())
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
torch.set_num_threads(1);start=time.monotonic();plan=read(D/'CONSUMER_PLAN.json')
for n,h in plan['sources'].items():assert sha(D/n)==h
try:
 results={};hist=read(B/'runs/recovery87_history_extension_20261030_v1/REVIEW.json')
 for method,case in plan['cases'].items():
  assert time.monotonic()-start<plan['budget_seconds'];binding=read(D/(method+'_BINDING.json'));saved=read(D/(method+'_CACHE_SAVED_REVIEW.json'))['snapshot'];assert sha(saved['path'])==saved['sha256'];x=torch.load(saved['path'],map_location='cpu',weights_only=False);assert x['kind']=='interface_only_no_online_approval';before=digest(x['learner']);rd=digest(x['replay']);new=restore_learner(x['learner'],binding,B/'runtime/source_train17_clock','cuda:1');assert digest(new.state_dict())==before
  health=terminal_health(new,x['replay']['arrays']);assert digest(new.state_dict())==before
  meta=hist['methods'][method];oldck=torch.load(meta['checkpoint87']['path'],map_location='cpu',weights_only=False);old=pair_class(PublishedLearner,'minimum' if method=='impedance' else 'mean')(B/'runtime/source_train17_clock',dimension=binding['action_dimension'],direct=False,seed=20261025,device='cuda:1',algorithm='cheq',critic_layer_norm=True,numerical_amendments=True,critic_clock=True);old.load_state_dict(oldck['learner']);idx=health['indices'];a=oldck['replay']['arrays'];obs=torch.as_tensor(a['observations'][idx],device=old.device);act=torch.as_tensor(a['actions'][idx],device=old.device)
  with torch.no_grad():
   for name,key in [('ensemble','prediction'),('ensemble_targets','target_prediction')]:
    pred=torch.stack([q(obs,act).reshape(-1) for q in getattr(old.learner.agent,name)],1).cpu().numpy();assert np.array_equal(pred,health[key])
  episode=next(e for e in meta['episodes'] if e['cycle']==87 and e['condition']==case);journal=[json.loads(l) for l in Path(episode['journal']).read_text().splitlines()];terminal=read(episode['terminal']);assert len(journal)==1375
  out=[]
  for learner,state in [(old,oldck['learner']),(new,x['learner'])]:
   learner.load_state_dict(state);initial=digest(learner.state_dict());external=ExternalActions(learner,2026102633,case);external.call(learner.reset_episode);actions=[]
   for i,j in enumerate(journal):
    if learner is new:
     result=frozen_event(learner,external,dict(kind='observation',observation=j['observation'],interval=j['interval']),oldck['steps'])
     p=0. if j['interval'] is None else j['interval']['external_penetration_peak_m'];assert result[0][50]==np.float32(float(p)/(float(p)+.0002))
    else:result=external.call(learner.act,j['observation'],step=oldck['steps'],deterministic=False)
    assert result[0][49]==np.float32((1375-i)/1375);actions.append((result[0][:50],*result[1:]))
   if learner is new:
    assert frozen_event(learner,external,dict(kind='terminal',interval=terminal['interval']),oldck['steps']) is None
    assert learner.episode_actions=={0:1375} and learner.history_intervals=={0:1375}
    terminal_obs=learner.terminal_observation(result[0]);assert terminal_obs[49]==0 and terminal_obs[50]==feature(terminal['interval']['external_penetration_peak_m'])
   assert digest(learner.state_dict())==initial;out.append(actions)
  assert digest(out[0])==digest(out[1]);assert digest(x['replay'])==rd and sha(saved['path'])==saved['sha256'];result=dict(passed=True,case=case,recorded_observation_events=1375,terminal_events=1,actor_raw_mixed_context_clock_exact=True,history_scalar_checks=1376,native_external_rng_and_full_learner_unchanged=True,terminal_health_rows=len(idx),all5_online_and_target_health_exact=True,clock_projection_exact=True,full_replay_unchanged=True,new_physics=0,optimizer_updates=0,limits='Recorded observations, not a newly executed physical trajectory or policy evaluation result')
  results[method]=result;put(D/(method+'_CONSUMER_REVIEW.json'),result);print('CONSUMER',method,flush=True);del x,oldck,old,new,out,health,a;gc.collect();torch.cuda.empty_cache()
 put(D/'CONSUMER_REVIEW.json',dict(passed=True,methods=results,elapsed_s=time.monotonic()-start,new_physics=0,optimizer_updates=0,online_registration_or_launch=False))
except BaseException as e:put(D/('CONSUMER_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
