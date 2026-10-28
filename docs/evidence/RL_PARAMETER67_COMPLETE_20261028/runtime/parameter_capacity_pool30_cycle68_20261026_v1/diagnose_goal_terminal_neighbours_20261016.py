"""Read-only proximity of terminal-window and earlier training transitions.

Nearest neighbours are a descriptive diagnostic, not exact state equivalence,
an independent Bellman target, a causal experiment, or final acceptance.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np


def terminal_neighbours(observation, action, reward, terminated, *, n_step, gamma, dt):
    obs=np.asarray(observation,dtype=np.float64)
    act=np.asarray(action,dtype=np.float64)
    rew=np.asarray(reward,dtype=np.float64)
    done=np.asarray(terminated)
    count=len(obs)
    if (obs.ndim!=2 or act.ndim!=2 or len(act)!=count or rew.shape!=(count,) or
            done.shape!=(count,) or count==0 or not done[-1] or
            not np.isin(done,[0,1]).all() or not all(np.isfinite(x).all() for x in (obs,act,rew))):
        raise ValueError('Require finite aligned replay ending at a true episode boundary')
    if not isinstance(n_step,int) or n_step<1 or not 0<gamma<=1 or dt<=0:
        raise ValueError('Invalid credit horizon')
    scale=np.maximum(obs.std(axis=0),1e-6)
    ends=np.flatnonzero(done)
    pairs=[]; skipped=[]; begin=0
    for episode,end in enumerate(ends):
        # Earlier controls must be at least2n transitions before the end; this
        # excludes merely adjacent samples and never crosses an episode boundary.
        controls=np.arange(begin,end-2*n_step+1)
        if len(controls)==0:
            skipped.append(dict(episode=episode,begin=begin,end=int(end),reason='too_short'))
            begin=int(end)+1;continue
        for query in range(max(begin,int(end)-n_step+1),int(end)+1):
            obs_mse=np.mean(((obs[controls]-obs[query])/scale)**2,axis=1)
            action_mse=np.mean((act[controls]-act[query])**2,axis=1)
            nearest=int(np.argmin(obs_mse+action_mse))
            control=int(controls[nearest])
            def window(i):
                stop=min(i+n_step,int(end)+1)
                return float(sum(gamma**k*rew[j] for k,j in enumerate(range(i,stop))))
            pairs.append(dict(episode=episode,episode_begin=begin,episode_end=int(end),
                terminal_window_index=query,earlier_index=control,
                query_to_end_steps=int(end)-query,earlier_to_end_steps=int(end)-control,
                gap_s=(query-control)*dt,
                standardized_observation_rms=float(np.sqrt(obs_mse[nearest])),
                raw_action_rms=float(np.sqrt(action_mse[nearest])),
                joint_rms=float(np.sqrt((obs_mse[nearest]+action_mse[nearest])/2)),
                raw_observation_max_abs=float(np.max(np.abs(obs[query]-obs[control]))),
                query_reward_n=window(query),earlier_reward_n=window(control),
                query_bootstrap_mask=0,earlier_bootstrap_mask=1))
        begin=int(end)+1
    def summary(key):
        values=np.array([row[key] for row in pairs])
        return dict(min=float(values.min()),median=float(np.median(values)),
                    mean=float(values.mean()),max=float(values.max())) if len(values) else None
    return dict(observation_scale=scale.tolist(),pair_count=len(pairs),skipped_episodes=skipped,
        summary={key:summary(key) for key in ('standardized_observation_rms','raw_action_rms',
            'joint_rms','raw_observation_max_abs','gap_s','query_reward_n','earlier_reward_n')},pairs=pairs)


def diagnose(cp):
    from rl_recovery_control_20261016 import verify_checkpoint, read, digest
    from diagnose_goal_carry_stall_20261016 import SUPPORTED_SOURCE
    checked=verify_checkpoint(cp);spec=read(cp.parent/'PROTOCOL.json');runner=read(cp/'office_runner.json')
    assert checked['step']==runner['step']<=100000, 'Finite diagnostic supports at most100k recorded transitions'
    assert spec['actor_input']=='unchanged canonical48'
    source=Path(spec['recovery_trainer_source']).parents[1]
    canonical='scripts/validate_office_apparatus_v5_20260917.py'
    assert digest(source/canonical)==SUPPORTED_SOURCE[canonical]
    with np.load(cp/'office_replay.npz',allow_pickle=False) as raw:
        assert raw['observation'].shape==(runner['step'],48)
        assert not raw['truncated'].any()
        result=terminal_neighbours(raw['observation'],raw['action'],raw['reward'],raw['terminated'],
            n_step=spec['agent_config']['n_step'],gamma=spec['agent_config']['gamma'],
            dt=spec['reward']['control_dt_s'])
    assert all(digest(cp/key)==value for key,value in checked['hashes'].items())
    return dict(checkpoint=str(cp),checkpoint_hashes=checked['hashes'],
        protocol_sha256=digest(cp.parent/'PROTOCOL.json'),canonical_source_sha256=SUPPORTED_SOURCE[canonical],
        controller=spec['controller'],n_step=spec['agent_config']['n_step'],
        checkpoint_hashes_unchanged=True,**result)


def main():
    from rl_recovery_control_20261016 import digest
    import platform
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint',type=Path,action='append',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    assert platform.node()=='airpig' and not args.output.exists()
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::')[1].lstrip('/')
    assert int((cg/'memory.max').read_text())<=1024**3 and (cg/'memory.swap.max').read_text().strip()=='0'
    result=dict(status='running',observed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=digest(Path(__file__)),simulation=False,gradient_updates=0,model_saved=False,
        metric='Minimize mean squared observation difference standardized by this whole replay std floored1e-6 plus mean squared raw action difference; equal group weights. Not the learned normalizer or a physical state equivalence criterion.',
        limitations='Finite train-only replay. Small distances do not prove hidden-time aliasing or learning impossibility; other hidden state, small observable differences and stochastic actions remain. Report n-step reward component and bootstrap mask, not full Bellman targets or trueQ. No actor input change or acceptance.')
    try:
        result.update(checkpoints=[diagnose(p.resolve()) for p in args.checkpoint],status='diagnosed')
    except BaseException as exc:
        result.update(status='failed_preserved',error=repr(exc));raise
    finally:
        result.update(peak_memory_bytes=int((cg/'memory.peak').read_text()),memory_events=(cg/'memory.events').read_text())
        with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps({r['controller']:r['summary'] for r in result['checkpoints']},indent=2))


if __name__=='__main__':main()
