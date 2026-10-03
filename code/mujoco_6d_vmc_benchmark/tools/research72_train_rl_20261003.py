"""Official SimbaV2 adaptation on registered office-v6 training identities.

Training reward is the baseline's existing bounded metric/office-task reward.
This is a separate from-scratch office cohort, never relabeled primitive transfer.
One physics process; complete episodes; bounded steps and deadline; no test data.
"""
import argparse
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
from run_all_methods_formal_20261003 import V6,PARAMETER,MENAGERIE
from run_paper_final_validation_20261003 import ENV
from research72_probe_online_20261003 import read_event

REWARDS=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/frozen_adapter01/simba_reward_20260930')


class Replay:
    def __init__(self,capacity,dimension,seed):
        self.capacity=capacity;self.count=0;self.rng=np.random.default_rng(seed)
        self.data={k:np.empty((capacity,*shape),np.float32) for k,shape in dict(observation=(48,),action=(dimension,),
            reward=(),terminated=(),truncated=(),next_observation=(48,)).items()}
    def add(self,**values):
        for k,value in values.items():self.data[k][self.count%self.capacity]=value
        self.count+=1
    def sample(self,n):
        ids=self.rng.integers(min(self.count,self.capacity),size=n)
        return {k:value[ids] for k,value in self.data.items()}
    def save(self,path):
        np.savez_compressed(path,**{k:v[:min(self.count,self.capacity)] for k,v in self.data.items()})
        return dict(count=self.count,capacity=self.capacity,rng_state=self.rng.bit_generator.state,sha256=sha(path))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--controller',choices=('admittance','impedance','vmc'))
    p.add_argument('--reward',choices=('metric','office_task'),required=True)
    p.add_argument('--seed',type=int,required=True);p.add_argument('--steps',type=int,default=80000)
    p.add_argument('--probe-receipt',type=Path,required=True)
    p.add_argument('--parameter-source',type=Path,default=PARAMETER,
        help='Independently archived baseline law/priors; allows declared office-development prior initialization')
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    parameter=a.parameter_source.resolve()
    protocol=json.loads((root/'PROTOCOL.json').read_text());pdigest=sha(root/'PROTOCOL.json')
    assert a.seed in protocol['budget_caps']['training_seeds']
    assert 1375<=a.steps<=protocol['budget_caps']['rl_adaptation_steps_per_family_seed']
    assert json.loads(a.probe_receipt.read_text())['observations_and_physics_exact']
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    conditions=[c for c in json.loads((root/'CONDITIONS.json').read_text())['conditions'] if c['role']=='train']
    assert len(conditions)==32
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip();assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    deadline=min(datetime.fromisoformat(protocol['dispatch_deadline_utc']),datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48))
    assert datetime.now(timezone.utc)<deadline
    out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(parameter));sys.path.insert(0,str(REWARDS))
    from official_parameter_agent import OfficialParameterAgent,BATCH_SIZE
    from rewards import OfficeReward,RewardConfig,IntervalMetrics
    prior=json.loads((parameter/'PRIORS.json').read_text())['methods'][a.controller] if a.controller else None
    dimension=prior['action_dimension'] if prior else 7
    agent=OfficialParameterAgent(seed=a.seed,total_steps=a.steps,utd=2,gamma=.9995,entropy_coef=-2.,
        initial_temperature=.0001,action_dimension=dimension)
    replay=Replay(a.steps,dimension,a.seed+53);rng=np.random.default_rng(a.seed+71)
    order=np.random.default_rng(a.seed+100).permutation(len(conditions))
    sources={str(f):sha(f) for folder in (parameter,REWARDS) for f in folder.rglob('*') if f.is_file() and f.suffix in ('.py','.json')}
    sources.update({str(f):sha(f) for f in (ROOT/'tools').glob('research72_*.py')})
    reward_config=RewardConfig(mode=a.reward,error_transform='bounded',horizon_s=55,gamma=.9995)
    registered=dict(registered_utc=now(),protocol_sha256=pdigest,seed=a.seed,controller=a.controller,reward=reward_config.to_dict(),
        source_sha256=sources,agent_config=agent.config,utd=2,maximum_new_physics_steps=a.steps,
        warmup_steps=5000,warmup_std=.02,training_condition_ids=[conditions[int(i)]['id'] for i in order],
        checkpoint_selection='Common completed episode boundaries; never test-based. Later development choice budget registered separately.',
        stage_deadline_utc=deadline.isoformat(),bc=False,teacher_labels_used=False,actor_input='canonical48 only',
        privileged_reward_metadata='Reference stage/error potential and physical metric intervals, never concatenated to actor input',
        smoothness_action='Actual common filtered normalized action7; differs from legacy primitive prefilter smoothing and is disclosed.',
        prior=prior,parameter_source=str(parameter),prior_file_sha256=sha(parameter/'PRIORS.json'),
        probe_receipt=str(a.probe_receipt),probe_receipt_sha256=sha(a.probe_receipt),
        initialization='from scratch, same official upstream SimbaV2 configuration; no primitive checkpoint or replay',
        resume='Episode-boundary replay and RNG saved. Automatic optimizer/RNG exact-resume is not implemented; do not silently restart.',
        fixed_scope='Original full55s gate/physics/actuator. Budget stops before an episode if fewer than1375 steps remain; no overshoot.')
    write(out/'PROTOCOL.json',registered)
    state=dict(status='running',started_utc=now(),host=platform.node(),python=sys.executable,memory_max=memory,
        seed=a.seed,steps=0,episodes=0,updates=0,rows=[],checkpoint_rows=[])
    stop=False;process=None;step=episode=0;pending=None;last_checkpoint_step=0
    def request_stop(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGUSR1,request_stop)
    def save():
        state.update(steps=step,episodes=episode,updates=agent.updates,diagnostics=agent.diagnostics(),stop_requested=stop)
        write(out/'execution.json',state)
    def checkpoint():
        nonlocal last_checkpoint_step
        name=f'checkpoint_{step:07d}';cp=out/name
        if cp.exists():return
        agent.save(cp);replay_state=replay.save(cp/'office_replay.npz')
        write(cp/'office_runner.json',dict(step=step,episode=episode,replay=replay_state,exploration_rng=rng.bit_generator.state,
            condition_order=order.tolist(),pending_transition=None,episode_boundary=True,automatic_exact_resume_supported=False))
        state['checkpoint_rows'].append(dict(path=str(cp),step=step,episode=episode,
            hashes={f.name:sha(f) for f in cp.iterdir() if f.is_file()}));last_checkpoint_step=step;save()
    save()
    try:
        with (out/'training.jsonl').open('x') as training_log:
            while step+1375<=a.steps and datetime.now(timezone.utc)<deadline and not stop:
                c=conditions[int(order[episode%len(order)])];run=out/f'episode_{episode:05d}_{c["id"]}'
                cmd=[sys.executable,str(ROOT/'tools/research72_worker_20261003.py'),'--worker-kind','online',
                    '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',pdigest,'--research-condition',c['id'],
                    '--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
                    '--config',str(root/'teacher.json'),'--output',str(run),'--physics-dt','.00005','--contact-audit',
                    '--parameter-source',str(parameter)]
                if a.controller:cmd+=['--controller',a.controller]
                entry=dict(episode=episode,condition_id=c['id'],run=str(run),command=cmd,started_utc=now(),step_before=step)
                state['rows'].append(entry);save()
                env={**os.environ,**ENV,'JAX_PLATFORMS':'cpu','MUJOCO_MENAGERIE_PATH':str(MENAGERIE),
                    'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
                rewarder=OfficeReward(reward_config);total=0.;count=0
                with (out/(run.name+'.stderr.log')).open('x') as log:
                    process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1,env=env)
                    event=read_event(process.stdout);assert event['kind']=='observation' and event['interval'] is None
                    obs=np.asarray(event['observation'],np.float32);phi=event['potential']
                    while True:
                        action=agent.sample_action(obs,previous_transition=pending,training=True);pending=None
                        if step<5000:action=np.clip(rng.normal(0,.02,dimension),-1,1).astype(np.float32)
                        process.stdin.write(json.dumps(dict(action=action.tolist()))+'\n');process.stdin.flush()
                        event=read_event(process.stdout);done=event['kind']=='terminal';iv=event['interval']
                        next_obs=np.asarray(event['observation'],np.float32);next_phi=iv['potential']
                        success=bool(done and event['result']['task_success'] and event['result']['strict_success'])
                        interval=IntervalMetrics(elapsed_s=iv['elapsed_s'],error_cost=iv['error_integral']/(55*.12**2),
                            bounded_error_cost=iv['bounded_error_integral']/55,peak_torque_ratio=iv['peak_torque_ratio'],
                            peak_torque_nm_per_joint=iv['peak_torque_nm_per_joint'],max_position_error_m=iv['max_position_error_m'],substeps=iv['substeps'])
                        reward,terms=rewarder(interval,iv['executed_action'],current_potential=phi,next_potential=next_phi,
                            terminated=done,success=success,failure=done and not success,
                            terminal_reason=('original_strict_success' if success else 'original_horizon_or_abort') if done else None)
                        replay.add(observation=obs,action=action,reward=reward,terminated=float(done),truncated=0.,next_observation=next_obs)
                        pending=dict(reward=reward,terminated=done,truncated=False);obs=next_obs;phi=next_phi;step+=1;count+=1;total+=reward
                        if step>=5000:
                            for _ in range(2):agent.update(replay.sample(BATCH_SIZE))
                        if step%250==0:
                            save();training_log.write(json.dumps(dict(step=step,episode=episode,reward=reward,terms=terms,diagnostics=agent.diagnostics()))+'\n');training_log.flush()
                        if done:
                            process.stdin.close();assert process.wait(timeout=60)==0;process=None
                            agent.consume_transition(**pending);pending=None
                            entry.update(ended_utc=now(),return_value=total,steps=count,step_after=step,result=event['result'],
                                audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
                            episode+=1;save();break
                if step-last_checkpoint_step>=10000:checkpoint()
            checkpoint()
            assert all(sha(Path(k))==h for k,h in sources.items())
            state.update(status='complete',stop_reason='requested' if stop else 'development_deadline' if datetime.now(timezone.utc)>=deadline else 'remaining_budget_less_than_one_full_episode')
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        if process is not None and process.poll() is None:
            process.stdin.close()
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=60)
        state['ended_utc']=now();save()


if __name__=='__main__':main()
