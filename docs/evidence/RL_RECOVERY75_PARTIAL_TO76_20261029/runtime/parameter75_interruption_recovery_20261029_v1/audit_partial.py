from pathlib import Path
import os,json,time,hashlib,shutil,sys,collections,math,socket
os.sched_setaffinity(0,{53})
import torch,numpy as np
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');RT=B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1';ROOT=B/'runtime/source_train17_clock';OLD=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1';OUT=B/'runs/parameter75_interruption_recovery_20261029_v1';OUT.mkdir(exist_ok=False)
sys.path[:0]=[str(RT),str(ROOT/'source/tools')]
from spt_rl_reward_20261025 import SPTReward
from validate_published_finite_check_20261025 import digest
import resume_cheq_capacity4m_pool30_20261027 as old_driver
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(x):
 if isinstance(x,dict):return all(finite(v) for v in x.values())
 if isinstance(x,(list,tuple)):return all(finite(v) for v in x)
 if torch.is_tensor(x):return bool(torch.isfinite(x).all())
 if isinstance(x,np.ndarray):return bool(np.isfinite(x).all())
 if isinstance(x,float):return math.isfinite(x)
 return True
def lines(p):
 return [json.loads(l) for l in p.read_bytes().splitlines(keepends=True) if l.endswith(b'\n')]
report=dict(time=time.time(),host=socket.gethostname(),passed=True,methods={},cycle75_complete=False,environment_state_saved=False,scientific_updates=0,original74_76_window_assessable=False)
for m in ['impedance','admittance','vmc']:
 o=OUT/m;o.mkdir();src=OLD/m/'train/checkpoint_latest.pt';h=sha(src);cp=o/'checkpoint_partial75.pt';shutil.copyfile(src,cp);assert sha(cp)==h==sha(src)
 regpath=OLD/m/'REGISTRATION.json';reg=read(regpath);old_driver.validate(reg['resume_parent_registration']['sha256'],reg,sha(regpath))
 x=torch.load(cp,map_location='cpu',weights_only=False);parent=Path(reg['batch_size_stage']['checkpoint']['path']);assert sha(parent)==reg['batch_size_stage']['checkpoint']['sha256'];prev=torch.load(parent,map_location='cpu',weights_only=False)
 assert x['cycle']==75 and x['boundary']=='partial_episode_valid_replay_reset_environment_on_resume' and x['controller']==m and not x['environment_state_saved'] and x['seed']==20261025
 assert x['protocol_sha256']==sha(regpath) and prev['cycle']==74 and prev['boundary']=='complete_condition_cycle'
 assert x['cycles']==prev['cycles'] and not any(c['cycle']==75 for c in x['cycles']) and finite(x['learner'])
 n=prev['steps'];size=x['steps'];a=x['replay']['arrays'];assert x['replay']['size']==x['replay']['cursor']==size and x['replay']['capacity']==4000000
 for k,v in prev['replay']['arrays'].items():np.testing.assert_array_equal(a[k][:n],v)
 for k,v in a.items():assert np.isfinite(v).all() and v.shape[0]==size
 assert np.all((a['masks']==0)|(a['masks']==1)) and not a['dones'][n:].any()
 for k in ['replay_capacity_extension','replay_capacity_followup']:assert x['replay'][k]==prev['replay'][k]
 s=x['learner'];assert s['num_gradient_steps']-prev['learner']['num_gradient_steps']==size-n
 for k in ['actor_optimizer','q_optimizer','alpha_optimizer']:assert s[k]['param_groups']==prev['learner'][k]['param_groups']
 ts=lines(OLD/m/'train/transitions.jsonl');retained=[t for t in ts if t['step']<=size];assert [t['step'] for t in retained]==list(range(n+1,size+1))
 opts=lines(OLD/m/'train/optimizer.jsonl');kept=[t for t in opts if t['step']<=size];assert [t['step'] for t in kept]==list(range(n+1,size+1)) and finite(kept)
 by=collections.defaultdict(list)
 for t in retained:by[t['condition']].append(t)
 err=0.;raw_counts={}
 for c,trs in by.items():
  folder=OLD/m/'train/cycle_00075'/c;js=lines(folder/'actor_intervals.jsonl');reward=SPTReward();raw_counts[c]=len(trs)
  cond=next(cn for cn in reg['conditions'] if cn['id']==c);assert sha(folder/'rollout.mjb')==cond['model_sha256']
  for i,t in enumerate(trs):
   j,z=js[i],js[i+1];k=t['step']-1;assert not t['done']
   value,_=reward(current_potential=j['payload_potential'],next_potential=z['payload_potential'],interval=z['interval'],terminated=False,task_success=False,strict_success=False);err=max(err,abs(value-t['reward']))
   np.testing.assert_array_equal(a['observations'][k,:48],np.asarray(j['observation'],np.float32)/s['observation_scale']);assert a['observations'][k,48]==np.float32(t['context']) and a['observations'][k,49]==np.float32((1375-i)/1375)
   np.testing.assert_array_equal(a['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32));np.testing.assert_array_equal(a['next_observations'][k,:48],np.asarray(z['observation'],np.float32)/s['observation_scale']);assert a['next_observations'][k,49]==np.float32((1374-i)/1375)
   assert a['rewards'][k,0]==np.float32(value)
 assert err<1e-10 and len(by)==30
 progress=read(OLD/m/'train/PROGRESS.json');assert progress['steps']>=size
 v=dict(checkpoint=str(cp),checkpoint_sha256=h,steps=size,parent74_steps=n,retained_partial75_updates=size-n,updates=s['num_gradient_steps'],protocol_sha256=sha(regpath),learner_digest=digest(s),replay_digest=digest(x['replay']),history_digest=digest(x['cycles']),old74_replay_exact=True,optimizer_network_and_all_replay_finite=True,all_partial_saved_rewards_actions_observations_exact=True,max_reward_error=err,all_retained_optimizer_rows_finite=True,last_progress=progress,progress_beyond_checkpoint=progress['steps']-size,transition_log_beyond_checkpoint=len(ts)-len(retained),optimizer_log_beyond_checkpoint=len(opts)-len(kept),new_terminal_count=0,raw_condition_transition_counts=raw_counts,source_checkpoint_unchanged=sha(src)==h)
 report['methods'][m]=v;(o/'REVIEW.json').write_text(json.dumps(v,indent=2)+'\n');print(m,size,size-n,'max_reward_error',err,flush=True)
 del x,prev,a,s
report['completed_at']=time.time();(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n');print('Full partial75 audit passed',flush=True)
