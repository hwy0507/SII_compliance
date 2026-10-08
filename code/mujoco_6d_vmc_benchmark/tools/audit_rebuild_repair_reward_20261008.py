"""Audit physical reward intervals and rebuild an off-policy prefix after a boundary fix.

The first torque observation has no observed predecessor: exclude that one
derivative, rather than fabricate a jump from zero to gravity compensation.
All old physics/actions/failures remain intact. A rebuilt learner starts fresh
and consumes the identical recorded transitions with corrected rewards, making
this explicitly off-policy reuse, not an exact continuation of old weights.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from research72_train_rl_20261003 import Replay, REWARDS
from research72_checkpoint_20261003 import checkpoint_hashes
from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
from baseline_repair_reward_clock_20261009 import TIME_BASE, SERVO_DT, slew_cost_rows, remaining_slew_bound


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--rebuild',action='store_true')
    a=p.parse_args();cp=a.checkpoint.resolve();out=a.output.resolve()
    assert not out.exists();out.mkdir(parents=True)
    spec=read(cp.parent/'PROTOCOL.json');state=read(cp.parent/'execution.json')
    entry=next(r for r in state['checkpoint_rows'] if r['path']==str(cp))
    assert checkpoint_hashes(cp)==entry['hashes']
    segments=[];cursor=cp.parent
    while True:
        s=read(cursor/'execution.json');assert s['status']=='complete'
        segments.append((cursor,s))
        if 'resumed_from' not in s:break
        parent=Path(s['resumed_from']['checkpoint']).parent
        assert sha(parent/'execution.json')==s['resumed_from']['parent_execution_sha256']
        cursor=parent
    rows=[r for _,s in reversed(segments) for r in (s.get('source_episode_rows',[])+s['rows'])]
    sys.path[:0]=[spec['parameter_source'],str(REWARDS),str(Path(__file__).resolve().parents[1]/'scripts')]
    from rewards import RewardConfig,OfficeReward,IntervalMetrics
    # Materialize each compressed array once. NpzFile indexing in the update
    # loop would repeatedly decompress the full replay (quadratic IO).
    with np.load(cp/'office_replay.npz') as archive:saved={k:archive[k] for k in archive.files}
    runner=read(cp/'office_runner.json')
    assert runner['step']==len(saved['reward'])==sum(r['steps'] for r in rows)
    rewards=[];evidence=[];position=0
    for row in rows:
        run=Path(row['run']);assert sha(run/'rollout.npz')==row['trace_sha256']
        rates=np.asarray(read(run/'execution.json')['action_filter_config']['maximum_torque_rate_nmps'])
        ivs=read(run/'RL_INTERVALS.json');meta=read(run/'RL_REWARD_METADATA.json')
        assert ivs[0] is None and len(ivs)==row['steps']+1
        with np.load(run/'baseline_policy.npz') as policy,np.load(run/'execution_chain.npz') as chain:
            # Learner deliberately casts raw physical observations to float32.
            np.testing.assert_array_equal(policy['observation'].astype(np.float32),saved['observation'][position:position+row['steps']])
            np.testing.assert_array_equal(policy['raw_action'].astype(np.float32),saved['action'][position:position+row['steps']])
            filtered=chain['filtered_action'].copy()
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            dt=z['dt'].astype(float);tau=z['qfrc_actuator'].astype(float);error=z['error'].astype(float)
        costs=np.sum((np.diff(tau,axis=0)/(dt[1:,None]*rates[None,:]))**2,axis=1)*dt[1:]/55.
        costs=np.r_[0.,costs]
        servo_costs=slew_cost_rows(tau,rates)
        old_first=float(np.sum((tau[0]/(dt[0]*rates))**2)*dt[0]/55.)
        rewarder=OfficeReward(RewardConfig(mode=spec['reward']['mode'],error_transform='bounded',
            horizon_s=55,gamma=.9995,smooth_weight=0.))
        phi=meta['initial_potential'];offset=0;max_error=0.;old_total=new_total=0.
        logs=[]
        for j,iv in enumerate(ivs[1:]):
            n=iv['substeps'];end=offset+n
            physical_cost=float(costs[offset:end].sum())
            new_cost=float(servo_costs[offset:end].sum())
            excluded='first recorded sample excluded' in meta['torque_slew_definition']
            expected_old=(new_cost if meta.get('torque_slew_time_base')==TIME_BASE else physical_cost)+(old_first if offset==0 and not excluded else 0.)
            max_error=max(max_error,abs(expected_old-iv['torque_slew_cost']))
            np.testing.assert_allclose(expected_old,iv['torque_slew_cost'],rtol=1e-10,atol=1e-10)
            e2=np.sum(error[offset:end]**2,axis=1)
            np.testing.assert_allclose(dt[offset:end]@e2,iv['error_integral'],rtol=1e-10,atol=1e-12)
            np.testing.assert_allclose(dt[offset:end]@(e2/(.12**2+e2)),iv['bounded_error_integral'],rtol=1e-10,atol=1e-12)
            np.testing.assert_allclose(filtered[j],iv['executed_action'],rtol=0,atol=1e-7)
            done=j==len(ivs)-2
            success=bool(done and row['result']['task_success'] and row['result']['strict_success'])
            interval=IntervalMetrics(elapsed_s=iv['elapsed_s'],error_cost=iv['error_integral']/(55*.12**2),
                bounded_error_cost=iv['bounded_error_integral']/55,peak_torque_ratio=iv['peak_torque_ratio'],
                peak_torque_nm_per_joint=iv['peak_torque_nm_per_joint'],max_position_error_m=iv['max_position_error_m'],substeps=n)
            reward,terms=rewarder(interval,iv['executed_action'],current_potential=phi,next_potential=iv['potential'],
                terminated=done,success=success,failure=done and not success,
                terminal_reason=('original_strict_success' if success else 'original_horizon_or_abort') if done else None)
            weight=spec['torque_slew_weight']
            failed=done and not success and weight
            old_remaining=(remaining_slew_bound(rewarder.elapsed_s) if spec.get('torque_slew_time_base')==TIME_BASE else 7*max(0.,55-rewarder.elapsed_s)/55) if failed else 0.
            new_remaining=remaining_slew_bound(rewarder.elapsed_s) if failed else 0.
            checkpoint_cost=new_cost if spec.get('torque_slew_time_base')==TIME_BASE else physical_cost
            if offset==0 and not spec.get('torque_slew_initial_sample'):checkpoint_cost+=old_first
            old=reward-weight*checkpoint_cost-old_remaining;new=reward-weight*new_cost-new_remaining
            np.testing.assert_allclose(old,saved['reward'][position+j],rtol=2e-6,atol=2e-7)
            rewards.append(new);old_total+=old;new_total+=new
            logs.append(dict(step=position+j+1,old_reward=old,corrected_reward=new,corrected_slew_cost=new_cost))
            phi=iv['potential'];offset=end
        assert offset==len(dt)
        write(out/(run.name+'_reward_audit.json'),dict(steps=logs))
        evidence.append(dict(run=str(run),trace_sha256=sha(run/'rollout.npz'),substeps_sha256=sha(run/'rollout_metrics/substep_metrics.npz'),
            intervals_sha256=sha(run/'RL_INTERVALS.json'),old_return=old_total,corrected_return=new_total,
            artificial_first_cost=old_first,interval_reconstruction_max_abs=max_error))
        position+=row['steps']
    report=dict(status='passed',time_utc=now(),episodes=evidence,steps=position,physics_rerun=False,
        correction='Use actual4ms servo update period for executed torque changes, exclude first unobserved predecessor, ceil remaining servo updates for failure bound',
        note='Original physics/actions/failures retained; only reward and explicitly rebuilt learner change. No environment or gate change')
    write(out/'REWARD_AUDIT.json',report)
    if not a.rebuild:return
    # Large physical arrays are no longer needed during JAX reconstruction.
    del tau,error,dt,costs,servo_costs
    from official_parameter_agent import OfficialParameterAgent,BATCH_SIZE
    cfg=spec['agent_config'];seed=spec['seed']
    agent=OfficialParameterAgent(seed=seed,total_steps=spec['maximum_steps'],utd=spec['utd'],gamma=cfg['gamma'],
        entropy_coef=cfg['temp_target_entropy_coef'],initial_temperature=cfg['temp_initial_value'],action_dimension=cfg['action_dimension'])
    replay=Replay(spec['maximum_steps'],cfg['action_dimension'],seed+53);pending=None
    with (out/'optimizer.jsonl').open('x') as f:
        for i,reward in enumerate(rewards):
            agent.sample_action(saved['observation'][i],previous_transition=pending,training=True)
            pending=None
            values={k:saved[k][i] for k in saved};values['reward']=reward;replay.add(**values)
            pending=dict(reward=reward,terminated=bool(saved['terminated'][i]),truncated=bool(saved['truncated'][i]))
            if i+1>=5000:
                for _ in range(spec['utd']):
                    info=flatten_metrics(agent.update(replay.sample(BATCH_SIZE)))
                    f.write(json.dumps(dict(step=i+1,update=agent.updates,metrics=info))+'\n')
            if pending['terminated'] or pending['truncated']:
                agent.consume_transition(**pending);pending=None
    assert pending is None and agent.interactions==agent.reward_samples==position
    spec.update(torque_slew_initial_sample='excluded; no artificial zero-to-gravity jump',
        torque_slew_time_base=TIME_BASE,torque_slew_control_dt_s=SERVO_DT,
        torque_slew_failure_continuation='At premature failure, charge 7*ceil(remaining_seconds/servo_dt)*servo_dt/55; conservative servo-update bound.',
        initialization='Fresh agent consuming same retained off-policy transition prefix, corrected rewards; no new physics',
        reward_rebuild_source_sha256={str(p):sha(p) for p in [Path(__file__),Path(__file__).with_name('baseline_repair_reward_clock_20261009.py')]},
        rebuilt_from_checkpoint=str(cp),rebuilt_from_hashes=entry['hashes'],reward_audit_sha256=sha(out/'REWARD_AUDIT.json'))
    write(out/'PROTOCOL.json',spec)
    target=out/cp.name;agent.save(target);rp=replay.save(target/'office_replay.npz')
    runner.update(replay=rp,reward_rebuilt=True);write(target/'office_runner.json',runner)
    write(out/'execution.json',dict(status='complete',steps=position,episodes=runner['episode'],updates=agent.updates,
        rows=[],source_episode_rows=rows,physics_rerun=False,rebuilt_from=str(cp),diagnostics=agent.diagnostics(),
        checkpoint_rows=[dict(path=str(target),step=position,episode=runner['episode'],hashes=checkpoint_hashes(target))]))


if __name__=='__main__':main()
