"""Isolated v4 recovery trainer: honor registered UTD and require hard cgroup limits.

Copied from train_baseline_repair_rl_20261008.py on 2026-10-16 to avoid
changing source hashes of concurrently running historical trainers.
Finite, auditable SimbaV2 training on repair-campaign train identities.

Same canonical48 input and raw-action replay. Capture every optimizer diagnostic
and per-step reward decomposition. Metric smoothness now uses actual actuator
torque slew for ALL methods, including native impedance's zero action7 path.
No demonstrations/BC/privileged actor inputs in these pure-RL rows.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now, V6, MENAGERIE
from run_paper_final_validation_20261003 import ENV
from research72_train_rl_20261003 import Replay, REWARDS
from research72_probe_online_20261003 import read_event
from research72_checkpoint_20261003 import checkpoint_hashes
from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
from baseline_repair_reward_clock_20261009 import TIME_BASE, SERVO_DT, remaining_slew_bound
from goal_tracking_reward_20261016 import validate_guidance, check_reward_resume, tracking_terms


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--parameter-source',type=Path,required=True)
    p.add_argument('--controller',choices=('vmc','admittance','impedance'))
    p.add_argument('--reward',choices=('metric','office_task'),required=True)
    p.add_argument('--reward-variant',choices=('original','task_safety','payload_shaping'),default='original')
    p.add_argument('--seed',type=int,required=True)
    p.add_argument('--steps',type=int,default=200000)
    p.add_argument('--stop-at-step',type=int)
    p.add_argument('--resume-checkpoint',type=Path)
    p.add_argument('--continuation-registration',type=Path,
                   help='New local continuation authority; preserves original scientific protocol hash')
    p.add_argument('--goal-registration',type=Path,
                   help='Explicit finite stage under the user-authorized persistent RL goal')
    p.add_argument('--hyperparameter-id', default='historical',
                   help='Registered exploration configuration; never selected using final outcomes')
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve();parameter=a.parameter_source.resolve()
    protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json')
    stop_file = Path(protocol['cooperative_stop_file']) if protocol.get('cooperative_stop_file') else None
    if stop_file is not None and not stop_file.is_absolute():
        stop_file = root / stop_file.name
    assert a.reward_variant in protocol.get('reward_variants',['original'])
    # A registered task_safety comparison retains the chosen base objective,
    # including metric/slew terms for online parameter controllers. Only the
    # terminal Task/Strict coupling and explicit safety cost differ.
    assert a.seed in protocol['budgets']['training_seeds']
    assert 1375<=a.steps<=protocol['budgets']['rl_steps_per_family_seed']
    limit=a.stop_at_step or a.steps
    assert 1375<=limit<=a.steps
    deadline=datetime.fromisoformat(protocol['training_dispatch_deadline_utc'])
    continuation = None
    goal_job = None
    if a.goal_registration:
        assert not a.continuation_registration
        from rl_goal_stage_20261016 import validate_training_job
        goal, goal_job = validate_training_job(a, protocol, pdigest)
        deadline=datetime.fromisoformat(goal['dispatch_deadline_utc'])
        stop_file=Path(goal['stop_file'])
    if a.continuation_registration:
        continuation=read(a.continuation_registration)
        assert continuation['schema']=='sii-local-rl-convergence-v2'
        assert continuation['parent_protocol_sha256']==pdigest
        assert continuation['parent_root']==str(root)
        assert continuation['host']==platform.node()=='airpig'
        assert continuation['resources']['server_compute'] is False
        assert a.resume_checkpoint and out.is_relative_to(Path(continuation['run_root']))
        assert limit in continuation['training_limits']
        assert a.steps==continuation['optimizer_schedule_steps']==500000
        assert a.seed==continuation['seed'] and a.reward_variant=='original'
        assert any(j['controller']==a.controller and j['reward']==a.reward and
                   j['hp']==a.hyperparameter_id for j in continuation['jobs'])
        deadline=datetime.fromisoformat(continuation['dispatch_deadline_utc'])
        if continuation.get('cooperative_stop_file'):
            stop_file=Path(continuation['cooperative_stop_file'])
    guidance = validate_guidance(goal_job, controller=a.controller, reward=a.reward,
                                 reward_variant=a.reward_variant)
    if a.resume_checkpoint:
        # Reject objective changes before allocating replay or creating output.
        check_reward_resume(read(a.resume_checkpoint.resolve().parent/'PROTOCOL.json'),
                            dict(tracking_guidance=guidance))
    assert datetime.now(timezone.utc)<deadline
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    conditions=[c for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='train']
    assert len(conditions)==32
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3, 'Recovery requires hard MemoryMax<=3GiB'
    assert (cg/'memory.swap.max').read_text().strip() == '0', 'Recovery requires MemorySwapMax=0'
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    out.mkdir(parents=True,exist_ok=False)
    sys.path[:0]=[str(parameter),str(REWARDS)]
    from official_parameter_agent import OfficialParameterAgent,BATCH_SIZE
    from rewards import RewardConfig,OfficeReward,IntervalMetrics
    prior=read(parameter/'PRIORS.json')['methods'][a.controller] if a.controller else None
    dimension=prior['action_dimension'] if prior else 7
    hyperparameters = protocol.get('rl_hyperparameters', {
        'historical': dict(entropy_coef=-2., initial_temperature=.0001)})
    if a.hyperparameter_id not in hyperparameters:
        raise ValueError('Unregistered RL hyperparameters')
    hp = hyperparameters[a.hyperparameter_id]
    if set(hp) != {'entropy_coef', 'initial_temperature'}:
        raise ValueError('Only registered entropy/temperature changes supported')
    # The default UTD=2 is retained for the registered baseline.  A lower
    # registered UTD arm can be selected for long CPU-only recovery runs so
    # that live MuJoCo interaction remains the bottleneck instead of two JAX
    # updates per transition exhausting the workstation memory budget.
    utd = int(os.environ.get('SII_RL_UTD', '2'))
    assert utd in (1, 2), 'Only registered UTD arms 1 and 2 are allowed'
    agent=OfficialParameterAgent(seed=a.seed,total_steps=a.steps,utd=utd,gamma=.9995,
        entropy_coef=hp['entropy_coef'],initial_temperature=hp['initial_temperature'],action_dimension=dimension)
    if agent.config['n_step']==1:replay=Replay(a.steps,dimension,a.seed+53)
    else:
        from multistep_rl_replay_20261009 import MultiStepReplay
        replay=MultiStepReplay(a.steps,dimension,a.seed+53,n_step=agent.config['n_step'],gamma=agent.config['gamma'])
    rng=np.random.default_rng(a.seed+71)
    order=np.random.default_rng(a.seed+100).permutation(len(conditions))
    source=Path(__file__).resolve().parents[1]
    source_hashes={str(f):sha(f) for folder in (parameter,REWARDS,source/'tools')
        for f in folder.rglob('*') if f.is_file() and f.suffix in ('.py','.json')}
    cfg=RewardConfig(mode=a.reward,error_transform='bounded',horizon_s=55,gamma=.9995,smooth_weight=0.)
    specification=dict(schema='sii-repair-rl-v1',registered_utc=now(),protocol_sha256=pdigest,
        seed=a.seed,controller=a.controller,agent_config=agent.config,utd=utd,reward=cfg.to_dict(),
        torque_slew_weight=1. if a.reward=='metric' else 0.,
        torque_slew_initial_sample='excluded; no artificial zero-to-gravity jump',
        torque_slew_time_base=TIME_BASE, torque_slew_control_dt_s=SERVO_DT,
        torque_slew_failure_continuation='At premature failure, charge 7*ceil(remaining_seconds/servo_dt)*servo_dt/55; conservative servo-update bound.',
        initialization='from scratch' if not a.resume_checkpoint else 'same repaired cohort exact episode-boundary resume',
        teacher_labels_used=False,bc=False,actor_input='unchanged canonical48',
        warmup_steps=5000,warmup_behavior='AR(1) rho=.9, stationary std=.10; pure exploration, no teacher',
        training_conditions=[conditions[int(i)]['id'] for i in order],maximum_steps=a.steps,segment_limit=limit,
        prior_file_sha256=sha(parameter/'PRIORS.json'),parameter_source=str(parameter),
        source_sha256=source_hashes,deadline_utc=deadline.isoformat(),
        optimizer_diagnostics='Every update returned metrics retained in optimizer.jsonl; includes actor/critic losses, Q and temperature when exposed upstream',
        checkpoints='Every completed episode boundary; all retained; no acceptance before all families finish')
    specification['utd'] = utd
    specification['recovery_implementation'] = '20261016: range(utd), hard cgroup memory/swap required; inherited v4 checkpoints were trained with actual UTD=2'
    specification['recovery_trainer_source'] = str(Path(__file__).resolve())
    specification['hyperparameter_id'] = a.hyperparameter_id
    if continuation:
        specification['continuation_registration_sha256']=sha(a.continuation_registration)
        specification['continuation_registration']=str(a.continuation_registration.resolve())
    specification['reward_variant'] = a.reward_variant
    if guidance is not None:
        assert guidance['gamma'] == cfg.gamma and guidance['horizon_s'] == cfg.horizon_s
        specification['tracking_guidance'] = guidance
        specification['tracking_guidance_definition'] = 'Train-only -4 times existing bounded physical tracking integral; discounted worst-case remaining tracking cost at early failure. Task/Strict labels and gates unchanged. Different objective: do not pool with original task_safety.'
    if goal_job is not None:
        specification['goal_registration_sha256']=sha(a.goal_registration)
        specification['goal_registration']=str(a.goal_registration.resolve())
        specification['credit_horizon_migration']=goal_job.get('credit_migration',False)
        specification['credit_horizon_caveat']='25-step off-policy returns introduce behavior-policy bias; finite registered experiment, not guaranteed improvement'
    if a.reward_variant=='task_safety':
        specification['task_safety_definition']='Original Task terminal +20/-20, plus20*increments of excess/(1+excess); excess=max(0,external_peak/.0002-1). Early failure charges unused worst-case safety peak budget. Original Strict evaluation unchanged.'
    if a.reward_variant=='payload_shaping':
        specification['payload_shaping_definition']='Only replace reference-progress potential with measured approach/lift/payload-goal potential, equal thirds; same weight5/gamma/terminal cancellation. Original Task AND Strict reward and all metric costs unchanged. Reward-only physical fields never enter actor48.'
    write(out/'PROTOCOL.json',specification)
    step=episode=last_checkpoint=0;pending=None;colored=np.zeros(dimension);stop=False;process=None
    state=dict(status='running',started_utc=now(),host=platform.node(),python=sys.executable,
               memory_max=memory,rows=[],checkpoint_rows=[],steps=0,episodes=0)
    if a.resume_checkpoint:
        cp=a.resume_checkpoint.resolve();parent=read(cp.parent/'PROTOCOL.json')
        assert parent.get('reward_variant','original')==a.reward_variant,'Reward changes require explicit replay rebuild'
        for k in ('protocol_sha256','seed','controller','reward','prior_file_sha256'):
            assert parent[k]==specification[k],k
        migration = bool(goal_job and goal_job.get('credit_migration'))
        if migration:
            from goal_rl_credit_adapter_20261016 import check_credit_migration
            check_credit_migration(parent['agent_config'],specification['agent_config'])
        else:
            assert parent['agent_config']==specification['agent_config'],'agent_config'
        if a.reward=='metric':
            assert parent.get('torque_slew_initial_sample')==specification['torque_slew_initial_sample'], 'Reward boundary correction requires explicit replay rebuild'
            assert parent.get('torque_slew_time_base')==TIME_BASE, 'Servo-time reward correction requires explicit replay rebuild'
        runner=read(cp/'office_runner.json');old=read(cp.parent/'execution.json')
        entry=next(r for r in old['checkpoint_rows'] if r['path']==str(cp))
        assert checkpoint_hashes(cp)==entry['hashes'] and runner['episode_boundary']
        agent.load(cp)
        replay_metadata=runner['replay']
        if migration:
            from goal_rl_credit_adapter_20261016 import migrated_replay_metadata
            replay_metadata=migrated_replay_metadata(replay_metadata,runner['step'],agent.config['gamma'])
        replay.restore(cp/'office_replay.npz',replay_metadata)
        step=runner['step'];episode=runner['episode'];last_checkpoint=step
        rng.bit_generator.state=runner['exploration_rng'];colored=np.asarray(runner['colored_noise'])
        assert step==replay.count==agent.interactions==agent.reward_samples
        state['resumed_from']=dict(checkpoint=str(cp),inherited_steps=step,inherited_episodes=episode,
            parent_execution_sha256=sha(cp.parent/'execution.json'),hashes=entry['hashes'])
    def request_stop(*_):
        nonlocal stop
        stop=True
    signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGUSR1,request_stop)
    def save():
        state.update(steps=step,episodes=episode,updates=agent.updates,diagnostics=agent.diagnostics(),stop_requested=stop)
        write(out/'execution.json',state)
    def checkpoint():
        nonlocal last_checkpoint
        cp=out/f'checkpoint_{step:07d}'
        if cp.exists():return
        assert pending is None and replay.count==step==agent.interactions==agent.reward_samples
        agent.save(cp);rp=replay.save(cp/'office_replay.npz')
        write(cp/'office_runner.json',dict(step=step,episode=episode,replay=rp,
            exploration_rng=rng.bit_generator.state,colored_noise=colored.tolist(),condition_order=order.tolist(),
            episode_boundary=True,pending_transition=None))
        state['checkpoint_rows'].append(dict(path=str(cp),step=step,episode=episode,hashes=checkpoint_hashes(cp)))
        last_checkpoint=step;save()
    save()
    try:
        with (out/'training.jsonl').open('x') as log,(out/'optimizer.jsonl').open('x') as optlog:
            while step+1375<=limit and datetime.now(timezone.utc)<deadline and not stop:
                # A marker requests episode-boundary shutdown without sending
                # a signal to the simulator child or killing its terminal data.
                if stop_file and stop_file.exists():
                    stop=True
                    state['resource_stop_reason']='cooperative_stop_file'
                    break
                if protocol.get('min_free_disk_bytes'):
                    import shutil
                    if shutil.disk_usage(out).free < protocol['min_free_disk_bytes']:
                        stop=True
                        state['resource_stop_reason']='disk_reserve'
                        break
                if continuation:
                    import shutil
                    if shutil.disk_usage(out).free < continuation['min_free_disk_bytes']:
                        stop=True
                        state['resource_stop_reason']='disk_reserve'
                        break
                c=conditions[int(order[episode%len(order)])];run=out/f'episode_{episode:05d}_{c["id"]}'
                command=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
                    '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',pdigest,
                    '--research-condition',c['id'],'--phase','train','--worker-kind','online',
                    '--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
                    '--config',str(root/'teacher.json'),'--output',str(run),'--physics-dt','.00005',
                    '--contact-audit','--parameter-source',str(parameter)]
                if a.controller:command+=['--controller',a.controller]
                row=dict(episode=episode,condition_id=c['id'],run=str(run),command=command,
                         started_utc=now(),step_before=step);state['rows'].append(row);save()
                environment={**os.environ,**ENV,'JAX_PLATFORMS':'cpu','MUJOCO_MENAGERIE_PATH':str(MENAGERIE),
                    'SII_SOURCE_BASE_COMMIT':protocol['source_base_commit']}
                rewarder=OfficeReward(cfg);total=0.;count=0
                if a.reward_variant=='task_safety':
                    from decoupled_task_safety_reward_20261009 import TaskSafetyPenalty
                    safety_penalty=TaskSafetyPenalty()
                with (out/(run.name+'.stderr.log')).open('x') as err:
                    process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,
                                             text=True,bufsize=1,env=environment)
                    event=read_event(process.stdout);assert event['kind']=='observation' and event['interval'] is None
                    obs=np.asarray(event['observation'],np.float32)
                    potential_key='payload_potential' if a.reward_variant=='payload_shaping' else 'potential'
                    phi=event[potential_key]
                    while True:
                        action=agent.sample_action(obs,previous_transition=pending,training=True);pending=None
                        if step<5000:
                            colored=.9*colored+np.sqrt(1-.9**2)*rng.normal(0,.10,dimension)
                            action=np.clip(colored,-1,1).astype(np.float32)
                        process.stdin.write(json.dumps(dict(action=action.tolist()))+'\n');process.stdin.flush()
                        event=read_event(process.stdout);done=event['kind']=='terminal';iv=event['interval']
                        next_obs=np.asarray(event['observation'],np.float32);next_phi=iv[potential_key]
                        success=bool(done and event['result']['task_success'] and
                            (a.reward_variant=='task_safety' or event['result']['strict_success']))
                        interval=IntervalMetrics(elapsed_s=iv['elapsed_s'],error_cost=iv['error_integral']/(55*.12**2),
                            bounded_error_cost=iv['bounded_error_integral']/55,peak_torque_ratio=iv['peak_torque_ratio'],
                            peak_torque_nm_per_joint=iv['peak_torque_nm_per_joint'],max_position_error_m=iv['max_position_error_m'],substeps=iv['substeps'])
                        reward,terms=rewarder(interval,iv['executed_action'],current_potential=phi,next_potential=next_phi,
                            terminated=done,success=success,failure=done and not success,
                            terminal_reason=(('original_task_success' if a.reward_variant=='task_safety' else 'original_strict_success') if success else 'original_horizon_or_abort') if done else None)
                        physical_smooth=specification['torque_slew_weight']*iv['torque_slew_cost']
                        remaining=remaining_slew_bound(rewarder.elapsed_s) if done and not success and a.reward=='metric' else 0.
                        reward-=physical_smooth+remaining
                        terms.update(physical_slew=-physical_smooth,physical_slew_failure_continuation=-remaining,final_reward=reward)
                        if a.reward_variant=='task_safety':
                            penalty,safety_terms=safety_penalty(iv['external_penetration_peak_m'],
                                terminated=done,elapsed_s=rewarder.elapsed_s)
                            reward-=penalty
                            terms.update(**safety_terms,final_reward=reward,
                                terminal_task_success=bool(done and event['result']['task_success']),
                                terminal_strict_success=bool(done and event['result']['strict_success']))
                        if guidance is not None:
                            guidance_terms = tracking_terms(interval.bounded_error_cost,
                                interval.elapsed_s, rewarder.elapsed_s,
                                terminated=done, success=success, config=guidance)
                            reward += sum(guidance_terms.values())
                            terms.update(**guidance_terms, final_reward=reward)
                        assert np.isfinite(reward)
                        replay.add(observation=obs,action=action,reward=reward,terminated=float(done),truncated=0.,next_observation=next_obs)
                        pending=dict(reward=reward,terminated=done,truncated=False);obs=next_obs;phi=next_phi
                        step+=1;count+=1;total+=reward
                        if step>=5000:
                            for _ in range(utd):
                                info=agent.update(replay.sample(BATCH_SIZE))
                                info=flatten_metrics(info)
                                assert all(np.isfinite(v) for v in info.values()),'Nonfinite optimizer diagnostic'
                                optlog.write(json.dumps(dict(step=step,update=agent.updates,metrics=info))+'\n')
                        log.write(json.dumps(dict(step=step,episode=episode,terms=terms))+'\n')
                        if step%250==0:save();log.flush();optlog.flush()
                        if done:
                            process.stdin.close();assert process.wait(timeout=60)==0;process=None
                            agent.consume_transition(**pending);pending=None
                            row.update(ended_utc=now(),return_value=total,steps=count,step_after=step,
                                result=event['result'],audit_sha256=sha(run/'AUDIT.json'),trace_sha256=sha(run/'rollout.npz'))
                            episode+=1;save();break
                # Persist each full/early-terminal episode so a later IPC or
                # launch-container failure cannot discard several closed episodes.
                log.flush();optlog.flush();checkpoint()
            checkpoint()
            assert all(sha(k)==v for k,v in source_hashes.items())
            state.update(status='complete',stop_reason='requested' if stop else 'deadline' if datetime.now(timezone.utc)>=deadline else 'step_budget')
            state['training_complete'] = state['stop_reason']=='step_budget' and limit==a.steps
            state['ready_for_acceptance'] = False  # Requires all four families and a separate lock.
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        if process is not None and process.poll() is None:
            process.stdin.close()
            try:process.wait(timeout=60)
            except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=60)
        state['ended_utc']=now();save()


if __name__=='__main__':main()
