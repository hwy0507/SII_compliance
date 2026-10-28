"""Reconstruct completed training rewards from physical substeps, read-only.

No simulation, gradients, checkpoint selection, or held-out reads. The frozen
reward reducer is replayed after independently reconstructing its inputs.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
import numpy as np
from rl_reward_diagnosis_audit_20261014 import read, write, sha
from datetime import datetime, timezone


def close(a, b, atol=1e-10):
    np.testing.assert_allclose(a, b, rtol=1e-8, atol=atol)


def inspect(training, episode, logs, campaign):
    spec=read(training/'PROTOCOL.json');row=episode;run=Path(row['run'])
    variant=spec['reward_variant'];cfg=spec['reward'];mode=cfg['mode']
    assert sha(run/'rollout.npz')==row['trace_sha256']
    assert sha(run/'AUDIT.json')==row['audit_sha256']
    audit=read(run/'AUDIT.json')
    assert sha(run/'rollout.mjb')==audit['model_sha256']==campaign['formal_model_sha256']
    research_path=run/'research_substeps.npz'
    assert sha(research_path)==read(run/'research_channels.json')['telemetry_sha256']
    ivs=read(run/'RL_INTERVALS.json');assert ivs[0] is None
    ivs=ivs[1:];assert len(ivs)==row['steps']==len(logs)
    assert [x['step'] for x in logs]==list(range(row['step_before']+1,row['step_after']+1))
    with np.load(run/'baseline_policy.npz') as policy,np.load(run/'rollout.npz') as trace,np.load(run/'execution_chain.npz') as chain:
        assert policy['observation'].shape==(len(ivs),48)
        np.testing.assert_array_equal(policy['observation'],trace['observation'])
        np.testing.assert_array_equal(policy['action'],trace['applied_action'])
        np.testing.assert_array_equal(policy['action'],chain['requested_action'])
        assert np.isfinite(policy['raw_action']).all()
        initial_qpos=trace['neuron_qpos'][0].copy()
        assert trace['neuron_time'][0]==0.
    assert audit['common_filter_replay_max_abs']==0
    # These constants are frozen in the source manifest, not fitted to traces.
    limits=np.array([87.,87.,87.,87.,12.,12.,12.])
    rates=np.array([700.,700.,700.,700.,160.,160.,160.])
    with np.load(run/'rollout_metrics/substep_metrics.npz') as data:
        dt=data['dt'].astype(float);tau=data['qfrc_actuator'].astype(float)
        err=data['error'].astype(float)
        speed=float(np.linalg.norm(data['twist'][:,:3].astype(float),axis=1).max())
    close(dt,campaign['physics_dt_s']);e2=np.sum(err*err,axis=1);del err
    with np.load(research_path) as data:
        penetration=data['external_penetration_m'].copy()
        counts=np.cumsum([i['substeps'] for i in ivs])
        # mj_step leaves live xpos at the final step's pre-integration state;
        # research telemetry explicitly forwards scratch post-integration FK.
        # Match the previous physical sample, not a relaxed numeric tolerance.
        assert min(i['substeps'] for i in ivs)>1
        ends=counts-2
        hand=data['hand_position'][ends].astype(float)
        payload=data['payload_position'][ends].astype(float)
    assert counts[-1]==len(dt)==len(tau)==len(penetration)
    goal=np.asarray(read(run/'rollout.plan.json')['destination'])
    # Independent vector expression; telemetry helper is not invoked here.
    measured_phi=(1/(1+np.linalg.norm(hand-payload,axis=1)/.04)
        +np.clip((payload[:,2]-.425)/.10,0,1)
        +1/(1+np.linalg.norm(payload-goal,axis=1)/.04))/3
    from rewards import OfficeReward,RewardConfig,IntervalMetrics
    from decoupled_task_safety_reward_20261009 import TaskSafetyPenalty
    rewarder=OfficeReward(RewardConfig(**cfg));safety=TaskSafetyPenalty()
    initial=logs[0]['terms']['current_potential'];phi=initial;offset=0
    if variant!='payload_shaping':
        close(initial,read(run/'RL_REWARD_METADATA.json')['initial_potential'])
    else:
        # Pure forward kinematics of the saved initial joint state, no mj_step
        # or environment reset. Both bodies are independent of mocap apparatus.
        import mujoco
        model=mujoco.MjModel.from_binary_path(str(run/'rollout.mjb'))
        data=mujoco.MjData(model);data.qpos[:]=initial_qpos
        mujoco.mj_kinematics(model,data)
        hand_id=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
        object_id=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'target_object')
        assert hand_id>0 and object_id>0
        for body in (hand_id,object_id):
            while body:
                assert model.body_mocapid[body]<0
                body=model.body_parentid[body]
        h0=data.xpos[hand_id];p0=data.xpos[object_id]
        reconstructed=(1/(1+np.linalg.norm(h0-p0)/.04)+np.clip((p0[2]-.425)/.10,0,1)
            +1/(1+np.linalg.norm(p0-goal)/.04))/3
        close(initial,reconstructed,atol=1e-7)
    discounted=undiscounted=progress=0.;maximum_residual=0.;peak=0.
    for index,(iv,record,end) in enumerate(zip(ivs,logs,counts,strict=True)):
        t=record['terms'];done=index==len(ivs)-1
        sl=slice(offset,end);d=dt[sl];torque=tau[sl]
        error_integral=float(d@e2[sl]);bounded=float(d@(e2[sl]/(.12**2+e2[sl])))
        maximum=float(penetration[sl].max())
        close(iv['error_integral'],error_integral);close(iv['bounded_error_integral'],bounded)
        close(iv['external_penetration_peak_m'],maximum)
        close(iv['payload_potential'],measured_phi[index],atol=1e-6)
        previous=tau[offset-1] if offset else torque[0]
        changes=np.diff(np.vstack((previous,torque)),axis=0)/(.004*rates)
        assert np.abs(changes).max()<=1+1e-5
        slew=float(np.sum(changes**2)*.004/55)
        close(slew,iv['torque_slew_cost'])
        metrics=IntervalMetrics(elapsed_s=float(d.sum()),error_cost=error_integral/(55*.12**2),
            bounded_error_cost=bounded/55,peak_torque_ratio=float(np.max(np.abs(torque)/limits)),
            peak_torque_nm_per_joint=np.abs(torque).max(0),max_position_error_m=float(np.sqrt(e2[sl].max())),substeps=len(d))
        next_phi=iv['payload_potential' if variant=='payload_shaping' else 'potential']
        success=bool(done and row['result']['task_success'] and
            (variant=='task_safety' or row['result']['strict_success']))
        reward,terms=rewarder(metrics,iv['executed_action'],current_potential=phi,next_potential=next_phi,
            terminated=done,success=success,failure=done and not success,
            terminal_reason=(('original_task_success' if variant=='task_safety' else 'original_strict_success')
                if success else 'original_horizon_or_abort') if done else None)
        remaining=max(0.,55-rewarder.elapsed_s)
        continuation=7*max(0,int(np.ceil(remaining/.004-1e-8)))*.004/55 if done and not success and mode=='metric' else 0.
        physical=slew if mode=='metric' else 0.
        reward-=physical+continuation
        close(t['physical_slew'],-physical);close(t['physical_slew_failure_continuation'],-continuation)
        if variant=='task_safety':
            cost,safety_terms=safety(maximum,terminated=done,elapsed_s=rewarder.elapsed_s)
            reward-=cost
            for key,value in safety_terms.items():close(t[key],value)
        for key in ('task','progress','error','peak_torque','time','smooth','failure_continuation','current_potential','next_potential'):
            close(t[key],terms[key])
        assert t['terminated']==done and t['success']==success
        close(t['final_reward'],reward)
        maximum_residual=max(maximum_residual,abs(t['final_reward']-reward))
        discounted+=cfg['gamma']**index*reward;undiscounted+=reward
        progress+=cfg['gamma']**index*t['progress'];phi=next_phi;offset=end;peak=max(peak,maximum)
    close(undiscounted,row['return_value'],atol=1e-8)
    close(progress,-cfg['progress_weight']*initial,atol=1e-8)
    rmse=1000*float(np.sqrt(dt@e2/dt.sum()));torque_peak=float(np.abs(tau).max())
    close([rmse,torque_peak,speed,peak*1000],[audit['rmse_mm'],audit['peak_torque_nm'],audit['peak_speed_mps'],audit['penetration_mm']],atol=1e-5)
    return dict(status='passed',episode=row['episode'],run=str(run),steps=len(ivs),variant=variant,
        task=row['result']['task_success'],strict=row['result']['strict_success'],stage=audit['stage'],
        reward_max_abs_error=maximum_residual,discounted_return=discounted,undiscounted_return=undiscounted,
        rmse_mm=rmse,peak_torque_nm=torque_peak,peak_speed_mps=speed,penetration_mm=peak*1000,
        actor_observation_dimension=48,common_filter_replay_max_abs=0,
        payload_reward_pose_semantics='live xpos pre-final-integration; aligned one physics substep before scratch post-integration telemetry',
        initial_payload_potential_independently_reconstructed=True if variant=='payload_shaping' else None,
        limitation='Base reward reducer replay is complemented by independent substep inputs, payload-pose potential reconstruction and shaping identity. This does not prove policy convergence or Markov sufficiency.',
        source_sha256=sha(run/'executed_online_worker.py.txt'),trace_sha256=row['trace_sha256'],
        research_sha256=sha(research_path),intervals_sha256=sha(run/'RL_INTERVALS.json'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--first-per-job',action='store_true')
    a=p.parse_args();assert not a.output.exists();campaign=read(a.root/'PROTOCOL.json')
    sys.path.insert(0,str(Path(campaign['runtime'])/'simba_reward_20260930'))
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),
        protocol_sha256=sha(a.root/'PROTOCOL.json'),new_simulation_steps=0,new_gradient_updates=0,
        selection='first completed episode per job' if a.first_per_job else 'all completed logged episodes at capture',episodes=[],pending=[])
    for job in campaign['jobs']:
        tr=a.root/(job['name']+'_train')
        if not (tr/'execution.json').exists():continue
        state=read(tr/'execution.json');completed=[r for r in state['rows'] if 'result' in r]
        if a.first_per_job:completed=completed[:1]
        logs=defaultdict(list);ids={r['episode'] for r in completed}
        with (tr/'training.jsonl').open() as f:
            for line in f:
                if not line.endswith('\n'):break
                row=json.loads(line)
                if row['episode'] in ids:logs[row['episode']].append(row)
        for row in completed:
            if len(logs[row['episode']])!=row['steps']:
                assert state['status']=='running'
                result['pending'].append(dict(job=job['name'],episode=row['episode'],reason='buffered log tail'));continue
            item=inspect(tr,row,logs[row['episode']],campaign);item['job']=job['name']
            result['episodes'].append(item);print(job['name'],row['episode'],'passed',flush=True)
    result['paired_warmup']=[]
    for pair in campaign['pairs']:
        paths=[a.root/(pair['id']+'_'+arm+'_train/execution.json') for arm in pair['arms']]
        if not all(path.exists() for path in paths):continue
        states=[read(path) for path in paths]
        rows=[{r['episode']:r for r in state['rows'] if 'result' in r and r['step_after']<=5000} for state in states]
        for ep in sorted(rows[0].keys() & rows[1].keys()):
            left,right=(r[ep] for r in rows)
            assert left['condition_id']==right['condition_id'] and left['steps']==right['steps']
            fields={'rollout.npz':['qpos','qvel','ctrl','observation','applied_action'],
                    'baseline_policy.npz':['raw_action','observation','action']}
            for file,keys in fields.items():
                with np.load(Path(left['run'])/file) as x,np.load(Path(right['run'])/file) as y:
                    for key in keys:np.testing.assert_array_equal(x[key],y[key])
            result['paired_warmup'].append(dict(pair=pair['id'],episode=ep,steps=left['steps'],
                condition=left['condition_id'],fields=fields,physics_and_actions_exact=True,
                traces_sha256=[left['trace_sha256'],right['trace_sha256']],
                learned_policy_result=False))
    result['status']='passed_for_captured_complete_episodes';write(a.output,result)


if __name__=='__main__':main()
