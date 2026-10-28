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
from research72_checkpoint_20261003 import checkpoint_hashes

REWARDS=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/frozen_adapter01/simba_reward_20260930')
if os.environ.get('SII_LOCAL_RUNTIME'):
    REWARDS = Path(os.environ['SII_LOCAL_RUNTIME']).resolve(strict=True)/'simba_reward_20260930'


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
    def restore(self,path,state):
        assert sha(path)==state['sha256'] and state['capacity']==self.capacity
        count=int(state['count']);assert 0<=count<=self.capacity
        with np.load(path,allow_pickle=False) as z:
            assert set(z.files)==set(self.data)
            for key,values in self.data.items():
                assert z[key].shape==(count,*values.shape[1:]) and z[key].dtype==values.dtype
                assert np.isfinite(z[key]).all()
                values[:count]=z[key]
        self.count=count;self.rng.bit_generator.state=state['rng_state']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--controller',choices=('admittance','impedance','vmc'))
    p.add_argument('--reward',choices=('metric','office_task'),required=True)
    p.add_argument('--seed',type=int,required=True);p.add_argument('--steps',type=int,default=80000)
    p.add_argument('--probe-receipt',type=Path,required=True)
    p.add_argument('--parameter-source',type=Path,default=PARAMETER,
        help='Independently archived baseline law/priors; allows declared office-development prior initialization')
    p.add_argument('--resume-checkpoint',type=Path,
        help='Verified complete episode boundary; resume into a new independent output directory')
    p.add_argument('--stop-at-step',type=int,
        help='Optional finite segment boundary; total optimizer schedule and exposure cap remain --steps')
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    parameter=a.parameter_source.resolve()
    protocol=json.loads((root/'PROTOCOL.json').read_text());pdigest=sha(root/'PROTOCOL.json')
    assert a.seed in protocol['budget_caps']['training_seeds']
    assert 1375<=a.steps<=protocol['budget_caps']['rl_adaptation_steps_per_family_seed']
    segment_limit=a.steps if a.stop_at_step is None else a.stop_at_step
    assert 1375<=segment_limit<=a.steps
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
        initialization=('verified same-cohort episode-boundary resume' if a.resume_checkpoint else
            'from scratch, same official upstream SimbaV2 configuration; no primitive checkpoint or replay'),
        resume='Explicit verified episode boundary only, into a new output directory. Incomplete episodes are preserved, never silently retried.',
        segment_step_limit=segment_limit,
        exposure_accounting='steps/episodes are cumulative across linked segments; rows contain only this segment. Never sum cumulative steps across segments.',
        fixed_scope='Original full55s gate/physics/actuator. Budget stops before an episode if fewer than1375 steps remain; no overshoot.')
    write(out/'PROTOCOL.json',registered)
    state=dict(status='running',started_utc=now(),host=platform.node(),python=sys.executable,memory_max=memory,
        seed=a.seed,steps=0,episodes=0,updates=0,rows=[],checkpoint_rows=[])
    stop=False;process=None;step=episode=0;pending=None;last_checkpoint_step=0
    if a.resume_checkpoint is not None:
        cp=a.resume_checkpoint.resolve();parent_out=cp.parent
        parent=json.loads((parent_out/'PROTOCOL.json').read_text())
        for key in ('protocol_sha256','seed','controller','reward','agent_config','utd','maximum_new_physics_steps','prior_file_sha256'):
            assert parent[key]==registered[key], 'Resume protocol mismatch: '+key
        previous=json.loads((parent_out/'execution.json').read_text())
        assert previous['status']=='complete', 'Resume only a completed finite segment'
        checkpoint_row=next(r for r in previous['checkpoint_rows'] if Path(r['path'])==cp)
        assert checkpoint_hashes(cp)==checkpoint_row['hashes']
        runner=json.loads((cp/'office_runner.json').read_text())
        assert runner['episode_boundary'] and runner['automatic_exact_resume_supported']
        assert runner['pending_transition'] is None
        step=int(runner['step']);episode=int(runner['episode'])
        assert step==checkpoint_row['step']==previous['steps'] and episode==previous['episodes']
        assert all('step_after' in r for r in previous['rows']), 'Incomplete parent physics cannot be silently replayed'
        assert step+1375<=segment_limit
        np.testing.assert_array_equal(order,runner['condition_order'])
        replay.restore(cp/'office_replay.npz',runner['replay'])
        assert replay.count==step
        rng.bit_generator.state=runner['exploration_rng'];agent.load(cp)
        assert agent.interactions==step and agent.reward_samples==step
        last_checkpoint_step=step
        state['resumed_from']=dict(checkpoint=str(cp),hashes=checkpoint_row['hashes'],
            training_protocol_sha256=sha(parent_out/'PROTOCOL.json'),
            parent_execution_sha256=sha(parent_out/'execution.json'),inherited_steps=step,inherited_episodes=episode)
    def request_stop(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGUSR1,request_stop)
    def save():
        inherited=state.get('resumed_from',{})
        state.update(steps=step,episodes=episode,updates=agent.updates,diagnostics=agent.diagnostics(),stop_requested=stop,
            new_segment_steps=step-inherited.get('inherited_steps',0),new_segment_episodes=episode-inherited.get('inherited_episodes',0))
        write(out/'execution.json',state)
    def checkpoint():
        nonlocal last_checkpoint_step
        name=f'checkpoint_{step:07d}';cp=out/name
        if cp.exists():return
        agent.save(cp);replay_state=replay.save(cp/'office_replay.npz')
        write(cp/'office_runner.json',dict(step=step,episode=episode,replay=replay_state,exploration_rng=rng.bit_generator.state,
            condition_order=order.tolist(),pending_transition=None,episode_boundary=True,automatic_exact_resume_supported=True))
        state['checkpoint_rows'].append(dict(path=str(cp),step=step,episode=episode,
            hashes=checkpoint_hashes(cp)));last_checkpoint_step=step;save()
    save()
    try:
        with (out/'training.jsonl').open('x') as training_log:
            while step+1375<=segment_limit and datetime.now(timezone.utc)<deadline and not stop:
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
