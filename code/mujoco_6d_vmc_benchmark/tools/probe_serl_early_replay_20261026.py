"""Finite early-replay candidate against the already completed warm13 control.

No control rerun. Every odd row is replaced by a uniform draw from the first32
steps of existing episodes, identified by the saved critic clock. No new physics,
demonstrations, reward changes, checkpoints, or auxiliary-weight promotion.
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
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def write(path, data):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert reg['horizons'] == [32] and reg['batch_size'] == 65536
    assert reg['early_steps'] == 32 and reg['early_fraction'] == .5
    for ref in [reg['completed_control'],reg['control_review'],reg['completed_control_report']]:assert sha(ref['path']) == ref['sha256']
    control = json.loads(Path(reg['completed_control']['path']).read_text())
    control_review = json.loads(Path(reg['control_review']['path']).read_text())
    assert control_review['passed'] and control['horizon'] == 32 and control['outer_updates'] == 2000
    assert control_review['checkpoint'] == reg['checkpoint']
    assert control_review['report_sha256'] == reg['completed_control_report']['sha256']
    control_report = json.loads(Path(reg['completed_control_report']['path']).read_text())
    assert control == control_report['results'][0] and control_report['passed']
    assert control_review['final']['32'] == control['points'][-1]
    assert reg['outer_updates_per_arm'] == 2000 and reg['record_every'] == 100
    assert reg['auxiliary_weights_promoted'] is False
    for ref in [reg['checkpoint'], reg['cycle_review'], reg['health_review']]:
        assert sha(ref['path']) == ref['sha256']
    for name, h in reg['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == h
    sys.path.insert(0, reg['adapter_runtime'])
    for name, h in reg['adapter_hashes'].items():
        assert sha(Path(reg['adapter_runtime'])/name) == h
    sys.path.insert(0, reg['base_adapter_runtime'])
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner, replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    ck = torch.load(reg['checkpoint']['path'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 13 and ck['boundary'] == 'complete_condition_cycle'
    review = json.loads(Path(reg['cycle_review']['path']).read_text())
    health = json.loads(Path(reg['health_review']['path']).read_text())
    assert review['passed'] and health['network_optimizer_rng_unchanged']
    assert review['methods']['direct']['checkpoint_sha256'] == health['checkpoint_sha256'] == reg['checkpoint']['sha256']
    parent_digest = digest(ck['learner']); replay_digest = digest(ck['replay'])
    arrays = ck['replay']['arrays']; extra = ck['replay']['multistep_target_extension']
    assert not extra['pending']
    ready = np.asarray(extra['ready'], np.int64)
    assert len(ready) == ck['replay']['size'] and np.array_equal(np.sort(ready), np.arange(len(ready)))
    terminal = np.flatnonzero(arrays['dones'][:, 0]); assert len(terminal) == 420
    early_rows = np.flatnonzero(arrays['observations'][:,48] >= np.float32((1375-31)/1375))
    assert 1000 < len(early_rows) < .05*len(ready)
    early_ids = np.random.default_rng(reg['early_seed']).choice(early_rows,1024,replace=False)
    ids = np.random.default_rng(reg['seed']).choice(ck['replay']['size'], 4096, replace=False)

    def select(rows, horizon):
        assert horizon in (1, 32)
        values = {k: v[rows] for k, v in arrays.items() if k not in ('rewards', 'next_observations')}
        if horizon == 32:
            values.update(rewards=extra['target_rewards'][rows, None], next_observations=arrays['next_observations'][extra['target_endpoints'][rows]], _bootstrap=extra['target_bootstrap'][rows])
        else:
            values.update(rewards=arrays['rewards'][rows], next_observations=arrays['next_observations'][rows], _bootstrap=1.-arrays['dones'][rows, 0])
        return values

    # Verify the control arm's first entire batch and RNG against the actual
    # deployed sampler before any optimization. One-step terminal rows coincide.
    replay = optimized_class(replay_class(Replay))(7, 49, reg['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']))
    rng = np.random.default_rng(); rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
    first_rows = ready[rng.integers(len(ready), size=65536)]
    assert digest(select(first_rows, 32)) == digest(replay.sample(65536))
    assert digest(rng.bit_generator.state) == digest(replay.rng.bit_generator.state)
    assert digest(select(terminal, 1)) == digest(select(terminal, 32))
    del replay
    cls = transfer_class(SerlMultistepLearner); results = []
    for horizon in reg['horizons']:
        learner = cls(Path(reg['runtime']), upstream=Path(reg['upstream']), upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True, seed=20261026, device='cuda:0')
        learner.load_state_dict(copy.deepcopy(ck['learner']))
        assert digest(learner.state_dict()) == parent_digest
        rng = np.random.default_rng(); rng.bit_generator.state = copy.deepcopy(ck['replay']['rng'])
        draws_hash = hashlib.sha256(); uniform_draws_hash = hashlib.sha256()
        early_rng = np.random.default_rng(reg['early_seed'])

        def diagnose():
            before = digest(learner.state_dict()); jax = learner.jax
            key, actionkey = jax.random.split(jax.random.PRNGKey(262))
            t = learner.batch(select(terminal, 1))
            tq = np.asarray(learner.agent.forward_critic(t['observations'], t['actions'], rng=key))
            error = np.abs(tq - np.asarray(t['rewards'])[None])
            result = dict(terminal_mae=float(error.mean()), terminal_max=float(error.max()), temperature=float(learner.agent.forward_temperature()))
            for h in (1, 32):
                tb = learner.batch(select(ids, h))
                pred = learner.agent.forward_critic(tb['observations'], tb['actions'], rng=key)
                acts, _ = learner.agent._compute_next_actions(tb, actionkey)
                targetq = learner.agent.forward_target_critic(tb['next_observations'], acts, rng=key)
                _, pairkey = jax.random.split(key); pair = jax.random.randint(pairkey, (2,), 0, 10)
                target = tb['rewards'] + .9995*tb['masks']*targetq[pair].min(axis=0)
                result[f'td{h}_mae'] = float(np.abs(np.asarray(pred-target[None])).mean())
            result['q_mean'] = float(np.asarray(pred).mean())
            obs = jax.tree_util.tree_map(lambda x: x[:1024], tb['observations'])
            mode = learner.agent.sample_actions(obs, argmax=True)
            def objective(actions):
                return learner.agent.forward_critic(obs, actions, rng=key).mean(axis=0).sum()
            gradients = np.asarray(jax.grad(objective)(mode))
            assert np.isfinite(gradients).all()
            result['mode_q_gradient_abs_mean'] = np.abs(gradients).mean(axis=0).tolist()
            result['mode_public0_mean'] = float(np.asarray((mode[:, 0]+1)*.5).mean())
            result['mode_residual_abs_mean'] = float(np.abs(np.asarray(mode[:, 1:])).mean())
            early = learner.batch(select(early_ids,32))
            eo = early['observations']; em = learner.agent.sample_actions(eo,argmax=True)
            def early_objective(actions):
                return learner.agent.forward_critic(eo,actions,rng=key).mean(axis=0).sum()
            eg = np.asarray(jax.grad(early_objective)(em))
            result['early_mode_public0_mean'] = float(np.asarray((em[:,0]+1)*.5).mean())
            result['early_mode_residual_abs_mean'] = float(np.abs(np.asarray(em[:,1:])).mean())
            result['early_mode_q_gradient_abs_mean'] = np.abs(eg).mean(axis=0).tolist()
            ep = learner.agent.forward_critic(eo,early['actions'],rng=key)
            ea,_ = learner.agent._compute_next_actions(early,actionkey)
            et = learner.agent.forward_target_critic(early['next_observations'],ea,rng=key)
            target = early['rewards']+.9995*early['masks']*et[pair].min(axis=0)
            result['early_td32_mae'] = float(np.abs(np.asarray(ep-target[None])).mean())
            assert digest(learner.state_dict()) == before
            return result

        initial = diagnose(); points = []; durations = []; losses = []
        assert all(initial[k] == v for k,v in control['initial'].items())
        assert parent_digest == control['initial_learner_digest'] and replay_digest == control['initial_replay_digest']
        for step in range(1, 2001):
            rows = ready[rng.integers(len(ready), size=65536)]
            uniform_draws_hash.update(rows.tobytes())
            rows[1::2] = early_rows[early_rng.integers(len(early_rows),size=32768)]
            draws_hash.update(rows.tobytes())
            start = time.perf_counter(); metrics = learner.update(select(rows, horizon))
            durations.append(time.perf_counter()-start); losses.append(float(metrics['serl/critic/critic_loss']))
            if step % 100 == 0:
                point = dict(outer_updates=step, critic_updates=step*8, **diagnose(), last100_critic_loss=float(np.mean(losses[-100:])), last100_outer_seconds=float(np.mean(durations[-100:])))
                points.append(point)
                write(args.output/f'horizon{horizon}_PROGRESS.json', dict(initial=initial, points=points))
                print(horizon, step, point['terminal_mae'], point['td1_mae'], point['td32_mae'], flush=True)
        final = learner.state_dict()
        assert final['num_gradient_steps'] - ck['learner']['num_gradient_steps'] == 16000
        assert digest(ck['learner']) == parent_digest and digest(ck['replay']) == replay_digest
        result = dict(horizon=horizon, early_steps=32, early_fraction=.5, early_rows=len(early_rows), uniform_draws_sha256=uniform_draws_hash.hexdigest(), initial=initial, initial_learner_digest=parent_digest, initial_replay_digest=replay_digest, sampled_rows_sha256=draws_hash.hexdigest(), final_sample_rng_digest=digest(rng.bit_generator.state), outer_updates=2000, critic_updates=16000, actor_updates=2000, sampled_rows=65536*2000, points=points, first_outer_seconds=durations[0], mean_outer_seconds_excluding_first=float(np.mean(durations[1:])), weights_saved=False)
        results.append(result); write(args.output/f'horizon{horizon}_RESULT.json', result)
        del learner
    result = results[0]
    assert result['uniform_draws_sha256'] == control['sampled_rows_sha256']
    assert result['final_sample_rng_digest'] == control['final_sample_rng_digest']
    assert result['sampled_rows_sha256'] != control['sampled_rows_sha256']
    assert sha(reg['checkpoint']['path']) == reg['checkpoint']['sha256']
    write(args.output/'REVIEW.json',dict(passed=True,checkpoint=reg['checkpoint'],completed_control=reg['completed_control'],candidate=result,control_final=control['points'][-1],total_critic_updates=16000,total_actor_updates=2000,new_physics=0,weights_saved=False,formal_state_unchanged=True,control_rerun=False,convergence_claim=False,limitation='Uniform control reused from completed warm13 probe, with identical initial state, update/row budget and underlying uniform draws. Candidate replaces every odd row with an existing first32-step row. No correction for changed replay distribution, no physical task-improvement claim, and no saved candidate weights. Early diagnostics have only candidate before/after values; control early metrics were not recorded.'))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
