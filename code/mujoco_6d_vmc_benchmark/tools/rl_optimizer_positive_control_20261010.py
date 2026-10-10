"""Pre-registered synthetic reward-learning check of the pinned RL stack.

Not a robot result or evidence that office tuning is sufficient. The target is
used ONLY inside the reward; actions/gradients are ordinary online RL. This
checks that this exact normalizer/actor/critic/replay can improve on an easy
continuous-action problem before committing another expensive physics budget.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import sys
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from research72_train_rl_20261003 import Replay
from research72_checkpoint_20261003 import checkpoint_hashes
from baseline_repair_rl_diagnostics_20261008 import flatten_metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, out = args.root.resolve(), args.output.resolve()
    assert platform.node() == 'airpig' and not out.exists()
    reg = read(root.parent/'REGISTRATION.json')['positive_control']
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 3*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    sys.path.insert(0, str(root/'parameter_fullrange'))
    from official_parameter_agent import OfficialParameterAgent, BATCH_SIZE
    out.mkdir()
    agent = OfficialParameterAgent(seed=reg['seed'], total_steps=reg['interactions'],
        utd=2, gamma=.9995, entropy_coef=-.5, initial_temperature=.01, action_dimension=7)
    assert agent.config['n_step'] == 1
    replay = Replay(reg['interactions'], 7, reg['seed']+53)
    rng = np.random.default_rng(reg['seed']+71)
    evaluation = np.random.default_rng(reg['evaluation_seed']).uniform(-1,1,(128,48)).astype(np.float32)
    target = np.asarray(reg['reward_optimum'],np.float32)
    def evaluate():
        before = agent.diagnostics()
        actions = np.asarray([agent.sample_action(o,training=False) for o in evaluation])
        assert before == agent.diagnostics()
        return actions, float(np.mean((actions-target)**2))
    initial_actions, initial_mse = evaluate()
    state = dict(status='running', started_utc=now(), specification=reg,
        source_sha256=sha(__file__), root_protocol_sha256=sha(root/'PROTOCOL.json'),
        host=platform.node(), python=sys.executable, agent_config=agent.config,
        initial_mse=initial_mse, new_robot_physics_steps=0, teacher_labels_used=False,
        limitation='Synthetic one-step reward optimizer check only; not a robot positive control or convergence evidence')
    write(out/'execution.json',state)
    try:
        with (out/'optimizer.jsonl').open('x') as log:
            for i in range(reg['interactions']):
                obs = rng.uniform(-1,1,48).astype(np.float32)
                action = agent.sample_action(obs,training=True)
                if i < 5000:
                    action = rng.uniform(-1,1,7).astype(np.float32)
                reward = -float(np.mean((action-target)**2))
                replay.add(observation=obs,action=action,reward=reward,terminated=1.,
                    truncated=0.,next_observation=np.zeros(48,np.float32))
                agent.consume_transition(reward=reward,terminated=True)
                if i+1 >= 5000:
                    for _ in range(2):
                        info = flatten_metrics(agent.update(replay.sample(BATCH_SIZE)))
                        assert all(np.isfinite(v) for v in info.values())
                        log.write(json.dumps(dict(step=i+1,update=agent.updates,metrics=info))+'\n')
                if (i+1)%500 == 0:
                    state.update(steps=i+1,updates=agent.updates,updated_utc=now())
                    write(out/'execution.json',state); log.flush()
        final_actions, final_mse = evaluate()
        assert replay.count == agent.interactions == agent.reward_samples == reg['interactions']
        replay_meta = replay.save(out/'raw_replay.npz')
        np.savez_compressed(out/'evaluation.npz',observation=evaluation,initial_actions=initial_actions,
            final_actions=final_actions,reward_optimum=target)
        agent.save(out/'checkpoint')
        passed = final_mse < reg['maximum_mse'] and final_mse <= reg['maximum_initial_ratio']*initial_mse
        state.update(status='complete',passed=passed,final_mse=final_mse,
            replay=replay_meta,checkpoint_hashes=checkpoint_hashes(out/'checkpoint'),
            evaluation_sha256=sha(out/'evaluation.npz'))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc)); raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)
    print(json.dumps(dict(passed=passed,initial_mse=initial_mse,final_mse=final_mse)))


if __name__ == '__main__':
    main()
