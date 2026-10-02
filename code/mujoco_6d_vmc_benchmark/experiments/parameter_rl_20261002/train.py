"""Official SimbaV2 on four frozen video-derived source fixtures, online RL."""
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/frozen_adapter01/simba_reward_20260930')))
from official_parameter_agent import OfficialParameterAgent,BATCH_SIZE
from rewards import RewardConfig,OfficeReward,IntervalMetrics
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
SCENES=['ball','push','corner','table_corner']

def dump(p,v):
 tmp=Path(str(p)+'.tmp');tmp.write_text(json.dumps(v,indent=2,allow_nan=False));tmp.replace(p)
class Replay:
 def __init__(self,capacity,seed,action_dimension):
  self.rng=np.random.default_rng(seed);self.count=np.zeros(4,int);self.capacity=capacity//4
  self.data={k:np.empty((4,self.capacity)+shape,np.float32) for k,shape in dict(observation=(48,),action=(action_dimension,),reward=(),terminated=(),truncated=(),next_observation=(48,)).items()}
 def add(self,scene,**values):
  i=self.count[scene]%self.capacity
  for k,v in values.items():self.data[k][scene,i]=v
  self.count[scene]+=1
 def sample(self,n):
  present=np.flatnonzero(self.count);ss=self.rng.choice(present,n);ii=np.array([self.rng.integers(min(self.count[s],self.capacity)) for s in ss]);return {k:v[ss,ii] for k,v in self.data.items()}
 def save(self,p):
  values={f'{s}_{k}':v[s,:min(self.count[s],self.capacity)] for k,v in self.data.items() for s in range(4)};np.savez(p,**values)
  return dict(count=self.count.tolist(),capacity_per_scene=self.capacity,rng=self.rng.bit_generator.state)
class Episode:
 def __init__(self,request):
  self.out=Path(request['output']);self.out.parent.mkdir(parents=True,exist_ok=True);req=self.out.parent/(self.out.name+'_request.json');dump(req,request)
  env=dict(os.environ,JAX_PLATFORMS='cpu');self.err=open(self.out.parent/(self.out.name+'_stderr.log'),'w')
  self.p=subprocess.Popen([sys.executable,str(HERE/'worker.py'),'--request',str(req)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1,env=env)
 def read(self):
  while True:
   line=self.p.stdout.readline()
   if not line:raise RuntimeError(f'worker exited {self.p.poll()} before terminal: {self.out}')
   try:value=json.loads(line)
   except json.JSONDecodeError:continue
   if value.get('kind')=='error':raise RuntimeError(value['error'])
   if value.get('kind') in ('observation','terminal'):return value
 def step(self,a):
  self.p.stdin.write(json.dumps({'action':np.asarray(a).tolist()})+'\n');self.p.stdin.flush();return self.read()
 def close(self):
  self.p.stdin.close();rc=self.p.wait(timeout=60);self.err.close()
  if rc:raise RuntimeError(f'worker exit {rc}: {self.out}')

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--reward',choices=['office_task','metric'],required=True);p.add_argument('--seed',type=int,required=True);p.add_argument('--steps',type=int,default=100000);p.add_argument('--deadline',type=float,required=True);p.add_argument('--warmup',type=int,default=5000);p.add_argument('--controller',choices=['admittance','impedance','vmc'],required=True);a=p.parse_args()
 out=a.output;out.mkdir(parents=True,exist_ok=False);fixtures=json.loads((ROOT/'FIXTURES.json').read_text());train={s:[f for f in fixtures if f['split']=='train' and f['scene']==s] for s in SCENES}
 prior=json.loads((HERE/'PRIORS.json').read_text())['methods'][a.controller];action_dimension=prior['action_dimension']
 agent=OfficialParameterAgent(a.seed,a.steps,utd=2,gamma=.9995,entropy_coef=-2.,initial_temperature=.0001,action_dimension=action_dimension)
 replay=Replay(max(100000,a.steps),a.seed+53,action_dimension);rng=np.random.default_rng(a.seed+71);stop=False;step=0;ep=0;started=time.monotonic();pending=None;episode=None
 def handler(*_):
  nonlocal stop
  stop=True
 signal.signal(signal.SIGUSR1,handler);signal.signal(signal.SIGTERM,handler)
 protocol=dict(controller=a.controller,parameter_prior=prior,energy_safety="Positive local storage-change budget, not global passivity proof",reward_smoothing="executed action7 after parameter controller; impedance action7 zero, torque metrics still evaluated",seed=a.seed,reward=a.reward,steps=a.steps,deadline_epoch=a.deadline,agent=agent.config,warmup_steps=a.warmup,warmup_std=.02,scene_sampling='round-robin episodes, deterministic shuffled fixture permutations per scene',replay_sampling='uniform scene then uniform transition within scene',actor_uses_teacher=False,unused_legacy_teacher_may_run=True,bc=False,upstream='86899c277cdc697b2b02d827243de1ea93f20a1d',fixed_scene_source=str(ROOT/'source_scene_20260918'),fixtures_sha256=hashlib.sha256((ROOT/'FIXTURES.json').read_bytes()).hexdigest(),source_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')},success='original primitive task success; legacy thick table requires measured lift, placement and release; all require <=0.2mm external penetration for terminal +20',limitations=['Video-derived old source fixtures are not new final environment.', 'Different source fixtures retain original dt/task supervisor/safety limits.', 'Ball legacy task gate uses contact truth; this is shared task logic, absent from actor.', 'Bounded metric and task potential are adaptations, not original-paper task reward.'])
 dump(out/'PROTOCOL.json',protocol)
 permutations={s:np.random.default_rng(a.seed+100+i).permutation(len(train[s])).tolist() for i,s in enumerate(SCENES)}
 def checkpoint(name):
  cp=out/name;agent.save(cp);r=replay.save(cp/'replay.npz');dump(cp/'runner.json',dict(step=step,episode=ep,replay=r,exploration_rng=rng.bit_generator.state,pending_transition=pending,mid_episode=episode is not None,exact_resume_supported=False))
 def status():dump(out/'STATE.json',dict(step=step,episode=ep,wall_s=time.monotonic()-started,steps_per_s=step/max(time.monotonic()-started,1),scene_transitions=replay.count.tolist(),diagnostics=agent.diagnostics(),stop_requested=stop))
 summary=open(out/'episodes.jsonl','w');audit=open(out/'training.jsonl','w')
 try:
  while step<a.steps and time.time()<a.deadline and not stop:
   si=ep%4;s=SCENES[si];idx=permutations[s][(ep//4)%len(train[s])];f=train[s][idx];horizon=float(f['flags'].get('duration',f['flags'].get('simulation_time',13)))
   rewarder=OfficeReward(RewardConfig(mode=a.reward,error_transform='bounded',horizon_s=horizon,gamma=.9995))
   episode=Episode(dict(fixture=f,method='rl',parameter_method=a.controller,output=str(out/'episodes'/f'{ep:06d}_{s}'),save_substeps=False))
   try:event=episode.read()
   except RuntimeError as exc:
    if 'Initial robot/obstacle overlap' not in str(exc) and 'Randomized initial state overlaps' not in str(exc):raise
    episode.p.wait(timeout=60);episode.err.close();episode=None
    summary.write(json.dumps(dict(episode=ep,step=step,fixture_id=f['id'],scene=s,status='initial_state_rejected',error=str(exc)))+'\n');summary.flush();ep+=1;continue
   obs=np.asarray(event['observation'],np.float32);phi=event['potential'];epret=0;epsteps=0;termsum={}
   while True:
    act=agent.sample_action(obs,previous_transition=pending,training=True);pending=None
    if step<a.warmup:act=np.clip(rng.normal(0,.02,action_dimension),-1,1).astype(np.float32)
    event=episode.step(act);done=event['kind']=='terminal';iv=event['interval'];nobs=np.asarray(event['observation'],np.float32);nphi=iv['potential'];result=event.get('result');success=bool(done and result['task_success'] and result['physical_valid'])
    interval=IntervalMetrics(elapsed_s=iv['elapsed_s'],error_cost=iv['error_integral']/(horizon*.12**2),bounded_error_cost=iv['bounded_error_integral']/horizon,peak_torque_ratio=iv['peak_torque_ratio'],peak_torque_nm_per_joint=iv['peak_torque_nm_per_joint'],max_position_error_m=iv['max_position_error_m'],substeps=iv['substeps'])
    reward,terms=rewarder(interval,iv["executed_action"],current_potential=phi,next_potential=nphi,terminated=done,success=success,failure=done and not success,terminal_reason=('success' if success else 'finite_horizon_or_existing_abort') if done else None)
    replay.add(si,observation=obs,action=act,reward=reward,terminated=float(done),truncated=0.,next_observation=nobs);pending=dict(reward=reward,terminated=done,truncated=False);obs=nobs;phi=nphi;step+=1;epsteps+=1;epret+=reward
    for k in ['task','progress','error','peak_torque','time','smooth','failure_continuation']:termsum[k]=termsum.get(k,0)+terms[k]
    if step>=a.warmup:
     for _ in range(2):last=agent.update(replay.sample(BATCH_SIZE))
    if step%250==0:
     status();audit.write(json.dumps(dict(step=step,episode=ep,scene=s,reward=reward,action_rms=float(np.sqrt(np.mean(act*act))),potential=phi,diagnostics=agent.diagnostics()))+'\n');audit.flush()
    if step%10000==0:checkpoint(f'checkpoint_{step:07d}')
    if done:
     episode.close();episode=None;summary.write(json.dumps(dict(episode=ep,step=step,episode_steps=epsteps,return_value=epret,terms=termsum,**result))+'\n');summary.flush();ep+=1;status();break
    if (stop or time.time()>=a.deadline or step>=a.steps):
     # Finish a single existing finite episode before stopping, preserving raw result.
     stop=True
   if step>=a.steps or time.time()>=a.deadline or stop:break
  if pending:agent.consume_transition(**pending);pending=None
  checkpoint('checkpoint_final');status();dump(out/'COMPLETE.json',dict(step=step,episodes=ep,wall_s=time.monotonic()-started,deadline_reached=time.time()>=a.deadline))
 finally:
  summary.close();audit.close()
  if episode is not None and episode.p.poll() is None:
   episode.p.terminate();episode.p.wait(timeout=60)
if __name__=='__main__':main()
