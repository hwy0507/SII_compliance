"""Finite same-state/draw control for an actor-only entropy coefficient floor.

Two arms start from identical complete formal15 learner/optimizer/replay/RNG.
Both retain32-step critic targets and current actor states. Only the actor entropy
coefficient differs: original learned value versus max(learned,0.1). No physics or
candidate checkpoint is produced; formal learners are separate processes.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['arms'] == ['learned_alpha', 'actor_floor01']
    assert reg['outer_updates_per_arm'] == 2000 and reg['batch_size'] == 65536
    assert reg['record_every'] == 200 and reg['seed'] == 2026102622
    for key in ['checkpoint', 'cycle_review', 'health_review', 'training_registration', 'implementation_gate', 'gate_decision']:
        assert sha(reg[key]['path']) == reg[key]['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    gate = json.loads(Path(reg['implementation_gate']['path']).read_text())
    decision = json.loads(Path(reg['gate_decision']['path']).read_text())
    assert decision['permit_finite_offline_probe'] and not decision['permit_formal_deployment']
    assert decision['implementation_gate'] == reg['implementation_gate']
    assert gate['passed'] and gate['native_alias_complete8to1_update_exact']
    assert gate['default_numerical_comparison']['exact'] and gate['default_metrics_comparison']['exact']
    for component in ['critic', 'temperature']:
        assert gate['isolation'][component]['full_state_and_metrics_exact']
    assert gate['isolation']['actor']['only_actor_params_and_optimizer_differ']
    assert gate['checkpoint'] == reg['checkpoint'] and gate['full_original_state_and_replay_unchanged']
    protocol = json.loads(Path(reg['training_registration']['path']).read_text())
    root = Path(protocol['runtime'])
    sys.path[:0] = [str(Path(__file__).parent), reg['adapter_runtime'], str(root/'source/tools')]
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    from serl_actor_entropy_floor_candidate_20261026 import convert_agent
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 15 and ck['boundary'] == 'complete_condition_cycle'
    assert ck['protocol_sha256'] == reg['training_registration']['sha256']
    arrays, extra = ck['replay']['arrays'], ck['replay']['multistep_target_extension']
    assert not extra['pending']
    ready = np.asarray(extra['ready'], np.int64)
    assert np.array_equal(np.sort(ready), np.arange(ck['replay']['size']))
    initial_rows = np.flatnonzero(arrays['observations'][:, 48] == 1)
    terminal = np.flatnonzero(arrays['dones'][:, 0])
    assert len(initial_rows) == len(terminal) == 480
    ids = np.random.default_rng(reg['seed']).choice(len(ready), 4096, replace=False)
    parent_digest, replay_digest = digest(ck['learner']), digest(ck['replay'])

    def select(rows, arm):
        assert arm in reg['arms']
        values = {k: v[rows] for k, v in arrays.items() if k not in ('rewards', 'next_observations')}
        values.update(rewards=extra['target_rewards'][rows, None],
            next_observations=arrays['next_observations'][extra['target_endpoints'][rows]],
            _bootstrap=extra['target_bootstrap'][rows])
        return values

    first_rng = np.random.default_rng()
    first_rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
    first_rows = ready[first_rng.integers(len(ready), size=65536)]
    assert hashlib.sha256(first_rows.tobytes()).hexdigest() == gate['batch_rows_sha256']
    replay = optimized_class(replay_class(Replay))(7, 49, ck['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    first = select(first_rows, 'learned_alpha')
    assert digest(first) == digest(replay.sample(65536))
    assert digest(first_rng.bit_generator.state) == digest(replay.rng.bit_generator.state)
    del replay, first
    cls = transfer_class(SerlMultistepLearner)
    results = []
    for arm in reg['arms']:
        learner = cls(root, upstream=Path(reg['upstream']), upstream_manifest=Path(reg['upstream_manifest']),
            dimension=7, direct=True, seed=ck['seed'], device='cuda:0')
        learner.load_state_dict(copy.deepcopy(ck['learner']))
        learner.agent = convert_agent(learner.agent, 0.0 if arm == 'learned_alpha' else 0.1)
        assert digest(learner.state_dict()) == parent_digest
        jax = learner.jax
        assert jax.config.jax_default_matmul_precision is None, 'Keep original formal precision'
        rng = np.random.default_rng()
        rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
        draws = hashlib.sha256()
        points, durations, losses = [], [], []

        def diagnose():
            before = digest(learner.state_dict())
            agent = learner.agent
            key, sample_key, pair_key = jax.random.split(jax.random.PRNGKey(reg['seed']), 3)
            tb = learner.batch(select(terminal, arm))
            tq = np.asarray(agent.forward_critic(tb['observations'], tb['actions'], rng=key))
            error = np.abs(tq-np.asarray(arrays['rewards'][terminal, 0])[None])
            result = dict(temperature=float(agent.raw_temperature()), effective_actor_temperature=float(agent.forward_temperature()),
                terminal_mae=float(error.mean()), terminal_max=float(error.max()))
            b = learner.batch(select(ids, arm))
            q = agent.forward_critic(b['observations'], b['actions'], rng=key)
            act, _ = agent._compute_next_actions(b, sample_key)
            target_q = agent.forward_target_critic(b['next_observations'], act, rng=key)
            pair = jax.random.randint(pair_key, (2,), 0, 10)
            target = b['rewards']+.9995*b['masks']*target_q[pair].min(axis=0)
            result.update(q_mean=float(np.asarray(q).mean()), td32_mae=float(np.abs(np.asarray(q-target[None])).mean()))
            def obs(value):
                return dict(state=np.ascontiguousarray(value[:, :48]), clock=np.ascontiguousarray(value[:, 48:49]))
            states = dict(current=arrays['observations'][ids], raw_next1=arrays['next_observations'][ids],
                derived_next32=arrays['next_observations'][extra['target_endpoints'][ids]],
                initial=arrays['observations'][initial_rows])
            for name, value in states.items():
                distribution = agent.forward_policy(obs(value), rng=key)
                _, log_prob = distribution.sample_and_log_prob(seed=sample_key)
                result[name+'_entropy'] = float(np.asarray(-log_prob).mean())
                if name == 'initial':
                    mode = np.asarray(distribution.mode())
                    result['initial_public0_mode_mean'] = float(((mode[:, 0]+1)*.5).mean())
                    result['initial_residual_mode_abs_mean'] = float(np.abs(mode[:, 1:]).mean())
                    result['initial_pre_tanh_std_mean'] = np.asarray(distribution.distribution.stddev()).mean(axis=0).tolist()
                    result['initial_raw_mode_mean'] = mode.mean(axis=0).tolist()
            assert digest(learner.state_dict()) == before
            return result

        initial = diagnose()
        if results:
            assert {k:v for k,v in initial.items() if k != 'effective_actor_temperature'} == {k:v for k,v in results[0]['initial'].items() if k != 'effective_actor_temperature'}, 'Initial network diagnostics must match exactly'
        for step in range(1, 2001):
            rows = ready[rng.integers(len(ready), size=65536)]
            draws.update(rows.tobytes())
            start = time.perf_counter()
            metrics = learner.update(select(rows, arm))
            durations.append(time.perf_counter()-start)
            losses.append(float(metrics['serl/critic/critic_loss']))
            if step % 200 == 0:
                point = dict(outer_updates=step, critic_updates=step*8, **diagnose(),
                    last200_critic_loss=float(np.mean(losses[-200:])),
                    last200_outer_seconds=float(np.mean(durations[-200:])))
                points.append(point)
                write(args.output/(arm+'_PROGRESS.json'), dict(initial=initial, points=points))
                print(arm, step, 'alpha', point['temperature'], 'initial_H', point['initial_entropy'],
                    'terminal_MAE', point['terminal_mae'], flush=True)
        final = learner.state_dict()
        assert final['outer_updates']-ck['learner']['outer_updates'] == 2000
        assert final['num_gradient_steps']-ck['learner']['num_gradient_steps'] == 16000
        assert int(final['agent']['step'])-int(ck['learner']['agent']['step']) == 18000
        assert digest(ck['learner']) == parent_digest and digest(ck['replay']) == replay_digest
        result = dict(arm=arm, initial=initial, initial_learner_digest=parent_digest,
            initial_replay_digest=replay_digest, sampled_rows_sha256=draws.hexdigest(),
            final_sample_rng_digest=digest(rng.bit_generator.state),
            final_agent_rng_digest=digest(final['agent']['rng']),
            final_learner_digest=digest(final), outer_updates=2000, critic_updates=16000,
            actor_updates=2000, temperature_updates=2000, points=points,
            first_outer_seconds=durations[0], mean_outer_seconds_excluding_first=float(np.mean(durations[1:])),
            weights_saved=False)
        results.append(result)
        write(args.output/(arm+'_RESULT.json'), result)
        del learner, final
    for key in ['initial_learner_digest', 'initial_replay_digest', 'sampled_rows_sha256',
        'final_sample_rng_digest', 'final_agent_rng_digest']:
        assert results[0][key] == results[1][key], key
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    write(args.output/'REVIEW.json', dict(time=time.time(), passed=True, checkpoint=reg['checkpoint'],
        implementation_gate=reg['implementation_gate'], gate_decision=reg['gate_decision'], results=results,
        total_critic_updates=32000, total_actor_updates=4000, total_temperature_updates=4000,
        new_physics=0, original_checkpoint_and_replay_unchanged=True, weights_saved=False,
        formal_deployment=False, formal_default_matmul_precision=True, convergence_claim=False,
        limitation='Two fixed2000-outer arms from identical formal15 full state with identical65536 row draws and all RNG streams. Critic32-step targets and current actor states are unchanged; only effective actor entropy coefficient differs. Original learned temperature and its optimizer remain; actor floor does not constrain the dual loss. A prespecified0.1 floor is a stress test, not an optimized or formally deployed value. Finite offline optimization, no new physical interaction or task-success evaluation, and no auxiliary checkpoint/weight promotion.'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args)
    except BaseException as error:
        write(args.output/'FAILURE.json', dict(time=time.time(), error=repr(error)))
        raise
