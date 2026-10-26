from pathlib import Path
import os,sys,json,time,hashlib
out=Path(__file__).parent;reg=json.loads((out/'REGISTRATION.json').read_text());os.sched_setaffinity(0,{reg['cpu']})
import numpy as np
import torch
torch.set_num_threads(1)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
rt=Path(reg['audit_runtime']);root=Path(reg['runtime']);b=out.parents[1]
sys.path.insert(0,str(root/'source/tools'));sys.path.insert(0,str(rt))
from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
from serl_state_adapter_20261026 import OBSERVATION_SCALE
from validate_serl_state_20261026 import digest
from summarize_published_episode_audit_20261025 import summarize
from replay_published_filter_audit_20261025 import audit as filter_audit
from replay_published_torque_audit_20261025 import audit as torque_audit
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus
for name,h in reg['source_hashes'].items():assert sha(rt/name)==h
folder=out/'evaluation';cp=folder/'checkpoint_frozen.pt';assert sha(cp)==reg['checkpoint_sha256']==sha(reg['checkpoint'])
x=torch.load(cp,map_location='cpu',weights_only=False);assert x['cycle']==12 and x['boundary']=='complete_condition_cycle'
a=SerlMultistepLearner(root,upstream=b/'runtime/serl_upstream_1fa2af7',upstream_manifest=b/'runtime/SERL_UPSTREAM_1fa2af7_HASHES.json',dimension=7,direct=True,seed=x['seed'],device='cuda:0');a.load_state_dict(x['learner']);before=digest(a.state_dict());assert before==digest(x['learner'])
baseline=Path(reg['baseline_run']);assert sha(reg['baseline_review']['path'])==reg['baseline_review']['sha256'];assert sha(reg['baseline_results']['path'])==reg['baseline_results']['sha256'];baseline_report=read(reg['baseline_review']['path']);baseline_episodes={e['condition']:e for e in baseline_report['episodes']};
results=read(folder/'RESULTS.json');assert results['evaluation']['noise_schedule']=='episode_constant';assert results['finished'] and not results['evaluation']['deterministic'] and results['evaluation']['action_seed']==reg['action_seed'];assert read(folder/'POLICY_UNCHANGED.json')['full_learner_state_unchanged'];assert read(folder/'EXTERNAL_ACTION_RNG_GATE.json')['passed']
conditions={c['id']:c for c in read(reg['training_registration'])['conditions']};reports=[];plot_data=[]
for episode in results['episodes']:
 case=episode['condition'];path=folder/case;assert sha(path/'rollout.mjb')==conditions[case]['model_sha256'];terminal=read(path/'TERMINAL.json');rows=[json.loads(line) for line in (path/'actor_intervals.jsonl').read_text().splitlines()]
 assert len(rows)==episode['actions'] and 0<len(rows)<=1375
 baseline_rows=[json.loads(line) for line in (baseline/'evaluation'/case/'actor_intervals.jsonl').read_text().splitlines()];np.testing.assert_array_equal(rows[0]['observation'],baseline_rows[0]['observation']);np.testing.assert_array_equal(rows[0]['action'],baseline_rows[0]['action'])
 seed=int.from_bytes(hashlib.sha256(f"{reg['action_seed']}:{case}".encode()).digest()[:4],'little');assert results['evaluation']['action_seed_by_case'][case]==seed
 key=a.jax.random.PRNGKey(seed);raw_actions=[];observations=[];rewards=[];error=0.;reward_fn=SPTReward()
 for i,row in enumerate(rows):
  normalized=np.asarray(row['observation'],np.float32)/OBSERVATION_SCALE;obs=dict(state=np.ascontiguousarray(normalized),clock=np.array([(1375-i)/1375],np.float32));unused_next_key,sample_key=a.jax.random.split(key)
  raw=np.asarray(a.agent.sample_actions(obs,seed=sample_key));public=raw.copy();public[0]=(public[0]+1)*.5;error=max(error,float(np.max(abs(public-np.asarray(row['action'])))));np.testing.assert_allclose(public,row['action'],atol=1e-6,rtol=0);np.testing.assert_array_equal(row['action'],row['executed_action'])
  nxt=terminal if i==len(rows)-1 else rows[i+1];done=i==len(rows)-1;labels=terminal['result'];value,_=reward_fn(current_potential=row['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=done,task_success=labels['task_success'] if done else False,strict_success=labels['strict_success'] if done else False)
  if done and labels['strict_success']:value+=completion_bonus(task_success=True,strict_success=True,completion_time_s=terminal['completion_time_s'])
  rewards.append(value);raw_actions.append(raw);observations.append(normalized)
 rewards=np.asarray(rewards,np.float64);returns=np.empty_like(rewards);carry=0.
 for i in range(len(rewards)-1,-1,-1):carry=rewards[i]+.9995*carry;returns[i]=carry
 obs=dict(state=np.asarray(observations,np.float32),clock=((1375-np.arange(len(rows),dtype=np.float32))/np.float32(1375))[:,None]);q=np.asarray(a.agent.forward_critic(a.jax.device_put(obs),a.jax.device_put(np.asarray(raw_actions,np.float32)),rng=a.jax.random.PRNGKey(261)));assert q.shape==(10,len(rows)) and np.isfinite(q).all()
 physical=summarize(path,'direct',case);filtered=filter_audit(path);torque=torque_audit(path);assert filtered['passed'] and torque['passed']
 if episode['result']['full_task_horizon_completed']:assert len(rows)==1375 and physical['samples']==1100000
 else:assert episode['result']['abort_reason'] and physical['samples']<1100000
 np.savez_compressed(out/(case+'_value_return.npz'),rewards=rewards,discounted_realized_returns=returns,q_predictions=q)
 comparison=dict(initial_q_mean=float(q[:,0].mean()),initial_realized_discounted_return=float(returns[0]),mean_prediction_minus_realized=float((q.mean(axis=0)-returns).mean()),mean_abs_prediction_minus_realized=float(np.abs(q.mean(axis=0)-returns).mean()),terminal_abs_error_mean=float(np.abs(q[:,-1]-rewards[-1]).mean()),undiscounted_reward=float(rewards.sum()),array_sha256=sha(out/(case+'_value_return.npz')))
 comparison['baseline_independent_noise']=baseline_episodes[case]['value_comparison'];comparison['baseline_physical_row']=baseline_episodes[case]['physical']['row'];comparison['first_observation_and_action_exact']=True
 reports.append(dict(condition=case,actions=len(rows),max_action_error=error,seed=seed,physical=physical,filter=filtered,torque=torque,value_comparison=comparison));plot_data.append((case,returns,q))
assert len(reports)==3 and {v['condition'] for v in reports}==set(reg['case_ids']);assert digest(a.state_dict())==before;assert sha(reg['checkpoint'])==reg['checkpoint_sha256']
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(3,1,figsize=(11,10),layout='constrained')
for ax,(case,returns,q) in zip(axes,plot_data):
 axis=np.arange(len(returns))*.04;ax.plot(axis,returns,label='constant-noise realized discounted return');ax.plot(axis,q.mean(axis=0),label='original independent-noise policy mean10 critic');ax.fill_between(axis,q.min(axis=0),q.max(axis=0),alpha=.2,label='critic min/max, not a confidence interval');ax.set_title(case);ax.set_xlabel('Simulation time (s)');ax.grid(alpha=.2);ax.legend()
fig.suptitle('Frozen SERL12 constant-noise behavior: original-policy Q is not this policy value')
fig.savefig(out/'value_vs_realized_return.png',dpi=150)
report=dict(passed=True,time=time.time(),checkpoint_sha256=reg['checkpoint_sha256'],episodes=reports,full_learner_optimizer_rng_unchanged=True,new_physics=0,new_optimizer_updates=0,scope='Independent seeded action replay, full physical/filter/torque audits, and discounted reward reconstruction. One constant-noise trajectory per condition versus original independent-noise trajectories with matched initial samples. Different continuation policy: original-policy critic versus realized returns is not a calibration error. Correlated states, no success-rate confidence intervals, no training deployment.',convergence_claim=False)
(out/'FINAL_SCIENTIFIC_REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
