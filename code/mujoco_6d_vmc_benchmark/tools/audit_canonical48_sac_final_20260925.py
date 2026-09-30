"""Offline final SAC audit; never import a simulator or select a checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import pickle
import types
import zipfile

import numpy as np
import torch

STEPS = 8192
SEED = 20260923
UPDATES = 8092
DEMO_SHA = '9f9092c03abcbf80cbf3e036552fbd9d6a214cdd21af8dded5eed1c402eb0a56'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    with Path(path).open() as stream:
        return [json.loads(line) for line in stream]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def exact(actual, expected, label):
    a, b = np.asarray(actual), np.asarray(expected)
    require(a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
            and np.array_equal(a, b), 'Exact mismatch: ' + label)


def normalizer_state(normalizer):
    return dict(mean=np.asarray(normalizer.obs_rms.mean), var=np.asarray(normalizer.obs_rms.var),
                count=float(normalizer.obs_rms.count), clip_obs=float(normalizer.clip_obs),
                epsilon=float(normalizer.epsilon), norm_obs=bool(normalizer.norm_obs),
                norm_reward=bool(normalizer.norm_reward))


def same_stats(actual, expected, label):
    require(set(actual) == set(expected), 'Normalizer fields: ' + label)
    for key in actual:
        exact(actual[key], expected[key], label + '/' + key)


def update_stats(state, observation):
    """Independent single-env parallel-moments formula, using raw float32 input."""
    array = np.asarray(observation, np.float32).reshape(1, 48)
    mean, var, count = state['mean'], state['var'], state['count']
    batch_mean, batch_var = np.mean(array, axis=0), np.var(array, axis=0)
    delta = batch_mean - mean
    total = count + 1
    result = dict(state)
    result.update(mean=mean + delta * 1 / total,
                  var=(var * count + batch_var * 1 + np.square(delta) * count * 1 / (count + 1)) / (count + 1),
                  count=1 + count)
    return result


def normalize(raw, state):
    return np.clip((np.asarray(raw, np.float32) - state['mean']) / np.sqrt(state['var'] + state['epsilon']),
                   -state['clip_obs'], state['clip_obs']).astype(np.float32)


def terminal_roundtrip(raw, state):
    return (normalize(raw, state) * np.sqrt(state['var'] + state['epsilon']) + state['mean']).astype(np.float32)


def reconstruct_statistics(gym_rows, initial, final_old_obs):
    expected_initial = dict(mean=np.zeros(48), var=np.ones(48), count=.0001,
                            clip_obs=12., epsilon=1e-8, norm_obs=True, norm_reward=False)
    same_stats(initial, expected_initial, 'fresh initial statistics')
    require(gym_rows, 'Empty online training')
    current = update_stats(initial, gym_rows[0]['observation'])  # first VecNormalize.reset
    states = []
    last_reset_from_pickle = False
    for index, row in enumerate(gym_rows):
        if row['terminated']:
            if index + 1 < len(gym_rows):
                next_obs = gym_rows[index+1]['observation']
                require(gym_rows[index+1]['step_index'] == 0, 'Terminal did not lead to next episode reset')
            else:
                # No following action/journal row exists in this special case.
                # Bind to saved VecNormalize.old_obs, not to a made-up terminal state.
                next_obs = np.asarray(final_old_obs).reshape(48)
                last_reset_from_pickle = True
        else:
            next_obs = row['next_observation']
        current = update_stats(current, next_obs)
        states.append(current)
    return states, last_reset_from_pickle


def audit_insertions(replay, inserted, gym_rows, gym_directories, states, demo=None):
    prefill = 0 if demo is None else 600
    total = prefill + len(gym_rows)
    require(len(inserted) == total, 'Insertion count mismatch')
    shapes = dict(observations=(total, 1, 48), next_observations=(total, 1, 48), actions=(total, 1, 7),
                  rewards=(total, 1), dones=(total, 1), timeouts=(total, 1),
                  is_demo=(total,), next_observation_valid=(total,))
    require(set(replay) == set(shapes), 'Replay export schema mismatch')
    for key, shape in shapes.items():
        require(replay[key].shape == shape and np.isfinite(replay[key]).all(), 'Replay shape/finite: ' + key)
        require(replay[key].dtype == (np.bool_ if key in ('is_demo', 'next_observation_valid') else np.float32), 'Replay dtype: ' + key)
    exact(replay['is_demo'], np.arange(total) < prefill, 'source prefix')
    exact(replay['timeouts'], np.zeros((total, 1), np.float32), 'no timeout')
    exact(replay['dones'].reshape(-1), (~replay['next_observation_valid']).astype(np.float32), 'terminal mask')
    require(np.all(np.abs(replay['actions']) <= 1.), 'SAC replay action outside normalized bounds')
    terminal_count = 0
    for index, entry in enumerate(inserted):
        require(entry['index'] == index, 'Insertion index gap/duplicate')
        stored, evidence = entry['stored'], entry['evidence']
        require(set(stored) == {'observations', 'next_observations', 'actions', 'rewards', 'dones', 'timeouts'}, 'Stored slot schema')
        for key in stored:
            exact(stored[key], replay[key][index], 'actual post-add vs final slot ' + key)
        if index < prefill:
            require(evidence['source'] == 'demo' and evidence['demo_index'] == index, 'Demo source/index mismatch')
            source = dict(observation=demo['observations'][index], next_observation=demo['next_observations'][index],
                          reward=float(demo['rewards'][index, 0]), terminated=bool(demo['dones'][index, 0]),
                          next_observation_valid=bool(demo['next_observation_valid'][index, 0]))
            exact(replay['actions'][index, 0], demo['actions_sac'][index], 'pinned demo action')
        else:
            online = index - prefill
            source = gym_rows[online]
            require(evidence['source'] == 'online' and evidence['online_step'] == online+1, 'Online source/index mismatch')
            require(evidence['episode_step'] == source['step_index'], 'Gym episode step mismatch')
            require(Path(evidence['episode_directory']).parts[-2:] == gym_directories[online].parts[-2:], 'Gym episode directory mismatch')
            action = replay['actions'][index, 0]
            low = np.asarray([0., -1., -1., -1., -1., -1., -1.], np.float32)
            high = np.ones(7, np.float32)
            executed = low + (.5 * (action + 1.) * (high - low))
            exact(executed, evidence['environment_action'], 'real SAC unscale action')
            exact(executed.astype(np.float64), source['requested_action'], 'Gym action request')
            exact(executed.astype(np.float64), source['execution_action'], 'Gym actual action')
        for key in ('observation', 'next_observation'):
            exact(evidence[key], source[key], 'independent source ' + key)
        require(evidence['reward'] == source['reward'] and evidence['done'] == source['terminated']
                and evidence['next_observation_valid'] == source['next_observation_valid'], 'Gym/demo labels mismatch')
        exact(evidence['buffer_action'], replay['actions'][index, 0], 'original logged buffer_actions')
        exact(replay['observations'][index, 0], np.asarray(source['observation'], np.float32), 'raw observation stored')
        exact(replay['rewards'][index], np.asarray([source['reward']], np.float32), 'float32 reward stored')
        exact(replay['dones'][index], np.asarray([source['terminated']], np.float32), 'done stored')
        if index >= prefill and source['terminated']:
            terminal_count += 1
            expected_next = terminal_roundtrip(source['next_observation'], states[index-prefill])
        else:
            expected_next = np.asarray(source['next_observation'], np.float32)
        exact(replay['next_observations'][index, 0], expected_next, 'actual valid next or explicitly masked terminal roundtrip')
    return dict(insertions=total, online=len(gym_rows), demo=prefill,
                online_terminal_placeholders=terminal_count, all_actual_slots_bound=True,
                all_online_unscaled_actions_exact=True, partial_final_next_valid=bool(gym_rows[-1]['next_observation_valid']))


def audit_samples(samples, replay, states, prefill, warmup=100, batch_size=256):
    require(len(samples) == len(states)-warmup, 'Sample/update count mismatch')
    demo_total = online_total = 0
    for index, row in enumerate(samples):
        step = warmup + index + 1
        require(row['call'] == index+1 and row['online_steps'] == step, 'Sample update order mismatch')
        same_stats(row['normalization'], states[step-1], 'online-only statistics at sample ' + str(index+1))
        indices = np.asarray(row['indices'])
        require(indices.shape == (batch_size,) and indices.dtype.kind in 'iu'
                and np.all(indices >= 0) and np.all(indices < prefill+step), 'Sampled missing/future transition')
        demo_count = int(np.count_nonzero(indices < prefill))
        require(row['demo_count'] == demo_count and row['online_count'] == batch_size-demo_count, 'Sample source counts mismatch')
        require(row['actual_sample_arrays_verified'] is True, 'Runtime sample verification absent')
        # Tensor bytes were checked by the hashed runtime logger but were not
        # themselves archived. Reconstruct their contract without overstating it.
        for name in ('observations', 'next_observations'):
            require(np.isfinite(normalize(replay[name][indices, 0], states[step-1])).all(), 'Nonfinite normalized sample')
        exact(1.-replay['dones'][indices, 0], replay['next_observation_valid'][indices].astype(np.float32), 'sampled bootstrap mask')
        demo_total += demo_count
        online_total += batch_size-demo_count
    return dict(calls=len(samples), sampled_demo=demo_total, sampled_online=online_total,
                logged_statistics_reconstructed_from_online_only=True, all_sample_indices_in_available_prefix=True,
                tensor_evidence='Actual returned arrays verified by hashed runtime assertion; bytes not independently archived')


def audit_optimizer_logs(rows, updates, warmup=100):
    require(len(rows) == updates*3, 'Optimizer hook count mismatch')
    for update in range(updates):
        for offset, name in enumerate(('entropy', 'critic', 'actor')):
            row = rows[update*3+offset]
            require(row == dict(optimizer=name, completed_steps=update+1, online_step=warmup+update+1),
                    'Actual optimizer event order/count mismatch')
    return {key: updates for key in ('actor', 'critic', 'entropy')}


def checkpoint(path, steps, updates):
    with zipfile.ZipFile(path) as archive:
        data = json.loads(archive.read('data'))
        require('seed' in data and data['seed'] == SEED, 'Explicit SAC checkpoint seed missing/wrong')
        require(data['num_timesteps'] == steps and data['_n_updates'] == updates, 'Not fixed-final SAC update boundary')
        for key, expected in dict(gamma=.995, learning_starts=100, batch_size=256,
                                  gradient_steps=1, buffer_size=1_000_000, n_steps=1,
                                  learning_rate=3e-4, tau=.005, target_entropy=-7.,
                                  target_update_interval=1, use_sde=False, ent_coef='auto', action_noise=None).items():
            require(data[key] == expected, 'Saved SAC learning parameter mismatch: ' + key)
        require(data['policy_kwargs']['net_arch'] == [256, 256], 'Saved SAC architecture differs from protocol')
        optimizer_parameters = {}
        for name, entry in [('actor', 'actor.optimizer.pth'), ('critic', 'critic.optimizer.pth'), ('entropy', 'ent_coef_optimizer.pth')]:
            state = torch.load(io.BytesIO(archive.read(entry)), map_location='cpu', weights_only=True)['state']
            require(bool(state) == bool(updates), 'Unexpected empty/nonempty Adam state')
            for parameter in state.values():
                require(float(parameter['step']) == updates, 'Saved Adam step differs from runtime hooks')
            optimizer_parameters[name] = len(state)
    return dict(seed=SEED, steps=steps, updates=updates, adam_parameters_with_matching_step=optimizer_parameters)


def audit_run(run, snapshot, demo_path=None):
    run, snapshot = Path(run).resolve(), Path(snapshot).resolve()
    manifest, complete = read(run/'manifest.json'), read(run/'COMPLETE.json')
    require(complete['status'] == 'complete' and not (run/'FAILED.json').exists(), 'Successful final marker required')
    require(manifest['algorithm'] == 'standard SAC' and manifest['mode'] == 'direct7', 'Only declared SAC/direct7 covered')
    require(manifest['branch'] in ('online_only', 'demo_prefill') and complete['branch'] == manifest['branch'], 'Branch mismatch')
    require(manifest['training']['steps'] == complete['training_steps'] == complete['recorded_transitions'] == STEPS, 'Wrong online budget')
    require(manifest['training']['seed'] == complete['seed'] == SEED and complete['updates'] == UPDATES, 'Wrong seed/update budget')
    require(complete['normalization_frozen'], 'Final normalization not frozen')
    prefill_count = 600 if manifest['branch'] == 'demo_prefill' else 0
    require(manifest['data_budget'] == dict(online=STEPS, demo=prefill_count, total=STEPS+prefill_count, offline_updates=0), 'Hidden/missing demo budget')
    require((demo_path is not None) == bool(prefill_count), 'Pinned demo must be supplied for prefill audit only')
    for name, field in [('sac_final.zip', 'checkpoint_sha256'), ('vecnormalize_train_only.pkl', 'normalizer_sha256'), ('replay_valid.npz', 'replay_sha256')]:
        require(sha(run/name) == complete[field], 'Final artifact hash drift: ' + name)
    require(set(manifest['initial_artifact_sha256']) == {'sac_initial.zip', 'vecnormalize_initial.pkl'}, 'Missing initial provenance')
    for name, digest in manifest['initial_artifact_sha256'].items():
        require(sha(run/name) == digest, 'Initial artifact hash drift: ' + name)
    require(sha(snapshot/'docs/CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md') == manifest['protocol_sha256'], 'SAC protocol drift')
    require(sha(snapshot/'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md') == manifest['base_protocol_sha256'], 'Base protocol drift')
    frozen = snapshot/'tools/audit_paired_transitions_20260924.py'
    require(sha(frozen) == manifest['source_hashes']['tools/audit_paired_transitions_20260924.py'], 'Original reward auditor drift')
    module = types.ModuleType('frozen_sac_reward_auditor')
    module.__file__ = str(frozen)
    exec(compile(frozen.read_text(), str(frozen), 'exec'), module.__dict__)
    gym_audit = module.audit_run(run, snapshot)
    require(gym_audit['training_transitions'] == STEPS and gym_audit['sb3_received_rewards']['all_float32_conversions_exact'], 'Incomplete actual Gym/reward audit')
    gym_rows, directories = [], []
    for path in sorted((run/'train').rglob('transitions.jsonl')):
        entries = lines(path)
        gym_rows.extend(entries)
        directories.extend([path.parent]*len(entries))
    with (run/'vecnormalize_initial.pkl').open('rb') as stream:
        initial_norm = pickle.load(stream)
    with (run/'vecnormalize_train_only.pkl').open('rb') as stream:
        final_norm = pickle.load(stream)
    states, last_reset = reconstruct_statistics(gym_rows, normalizer_state(initial_norm), final_norm.old_obs)
    same_stats(normalizer_state(final_norm), states[-1], 'final saved online-only normalization')
    demo = None
    if demo_path is not None:
        demo_path = Path(demo_path)
        require(sha(demo_path/'manifest.json') == manifest['demo']['manifest_sha256'] == DEMO_SHA, 'Not pinned r2 demo')
        declared = read(demo_path/'manifest.json')
        require(declared['artifact_sha256'] == manifest['demo']['artifact_sha256'], 'Demo manifest binding mismatch')
        for name, digest in declared['artifact_sha256'].items():
            require(sha(demo_path/name) == digest, 'Demo bytes changed')
        with np.load(demo_path/'demonstration.npz', allow_pickle=False) as archive:
            demo = {key: archive[key] for key in archive.files}
    else:
        require(manifest['demo'] is None, 'Online-only run contains demo metadata')
    with np.load(run/'replay_valid.npz', allow_pickle=False) as archive:
        replay = {key: archive[key] for key in archive.files}
    insertions = audit_insertions(replay, lines(run/'replay_audit/replay_insertions.jsonl'), gym_rows, directories, states, demo)
    samples = audit_samples(lines(run/'replay_audit/replay_samples.jsonl'), replay, states, prefill_count)
    expected_replay_summary = dict(size=STEPS+prefill_count, pos=STEPS+prefill_count, full=False, online_steps=STEPS,
        demo_transitions=prefill_count, sample_calls=UPDATES, sampled_demo=samples['sampled_demo'], sampled_online=samples['sampled_online'])
    require(read(run/'replay_summary.json') == expected_replay_summary, 'Replay summary not supported by complete logs')
    optimizer_steps = audit_optimizer_logs(lines(run/'optimizer_steps.jsonl'), UPDATES)
    require(complete['optimizer_steps'] == optimizer_steps, 'COMPLETE optimizer count mismatch')
    require(read(run/'optimizer_summary.json') == dict(actual_optimizer_steps=optimizer_steps, actual_updates=UPDATES, expected_updates=UPDATES), 'Optimizer summary mismatch')
    initial_checkpoint = checkpoint(run/'sac_initial.zip', 0, 0)
    final_checkpoint = checkpoint(run/'sac_final.zip', STEPS, UPDATES)
    evaluations = read(run/'evaluation.json')
    require(evaluations == complete['results'] and set(evaluations) == {'train/zero', 'train/sac', 'validation/zero', 'validation/sac'}, 'Four fixed final evaluations required')
    ns = module.load_frozen(snapshot, manifest)
    evaluation_rows = []
    for condition in ('train/zero', 'train/sac', 'validation/zero', 'validation/sac'):
        split, kind = condition.split('/')
        folder = run/'eval'/split/kind/'episode_00000'
        result = read(folder/'rollout.json')
        recomputed = ns['evaluation_summary'](result, manifest['fixture_specs'][split])
        require(all(evaluations[condition][key] == value for key, value in recomputed.items()), 'Final evaluation recomputation mismatch')
        matching = [row for row in gym_audit['episodes'] if Path(row['directory']).resolve() == folder]
        require(len(matching) == 1 and matching[0]['complete'], 'Evaluation terminal not independently audited')
        with np.load(folder/'rollout.npz', allow_pickle=False) as raw:
            count = len(raw['observation'])
            require(1 <= count <= 600 and count == matching[0]['transitions'], 'Invalid evaluation length')
            require(count == 600 or result['invalid_physics'], 'Unexplained safety early termination')
            require(np.allclose(raw['time'], .04*np.arange(1, count+1), rtol=0., atol=1e-6), 'Evaluation timing mismatch')
            require(abs(result['duration_s']-raw['time'][-1]) < 1e-6, 'Evaluation duration mismatch')
            endpoint = float(np.mean(np.linalg.norm(raw['position'][-min(10, count):]-raw['target'][-min(10, count):], axis=1)))
            require(abs(endpoint-recomputed['endpoint_error_m']) < 1e-12, 'Evaluation endpoint mismatch')
        evaluation_rows.append(dict(condition=condition, **recomputed, action_steps=count, duration_s=result['duration_s'],
                                    lift_m=result['lift_m'], safety_early_termination=count < 600))
    artifacts = ('manifest.json', 'COMPLETE.json', 'sac_initial.zip', 'sac_final.zip', 'vecnormalize_initial.pkl',
                 'vecnormalize_train_only.pkl', 'replay_valid.npz', 'replay_summary.json', 'optimizer_steps.jsonl',
                 'optimizer_summary.json', 'sb3_received_rewards.jsonl', 'evaluation.json', 'model_architecture.json',
                 'replay_audit/replay_insertions.jsonl', 'replay_audit/replay_samples.jsonl')
    return dict(passed=True, algorithm='standard SAC', branch=manifest['branch'], seed=SEED,
                gym_transition_audit=gym_audit, insertions=insertions, samples=samples, optimizer_steps=optimizer_steps,
                initial_checkpoint=initial_checkpoint, final_checkpoint=final_checkpoint, evaluations=evaluation_rows,
                initial_normalizer_count=normalizer_state(initial_norm)['count'], final_normalizer_count=states[-1]['count'],
                final_terminal_reset_from_saved_old_obs=last_reset,
                artifacts={name: dict(path=str(run/name), sha256=sha(run/name)) for name in artifacts}, tool_sha256=sha(__file__),
                limitations=['No simulation, training, checkpoint selection or changes to frozen sources.',
                    'Sample tensor values were checked in hashed runtime instrumentation; archived indices/statistics/slots are independently reconstructed, not unrecorded tensor bytes.',
                    'Actual TD targets, losses and gradient tensor values were not logged and are not numerically audited.',
                    'Terminal placeholder values may change under normalize/unnormalize but done=1 and timeout=0 forbid bootstrap; final partial done=0 preserves its real next.',
                    'If the online budget ends exactly at a terminal, the final auto-reset observation comes from the bound saved normalizer old_obs because no next action journal row exists.',
                    'Current-stage endpoint is not common final-goal accuracy; single training seed and fixed fixture do not establish convergence or paper reproduction.'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'snapshot', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--demo', type=Path)
    args = parser.parse_args()
    require(not args.output.exists() and not args.output.with_suffix('.md').exists(), 'Fresh audit outputs required')
    result = audit_run(args.run, args.snapshot, args.demo)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    text = ['# SAC固定最终8192步：独立审计', '',
        f"分支 `{result['branch']}`，seed20260923；全8192在线Gym/reward、实际replay槽、全部8092次sample索引/online统计及actor/critic/entropy实际8092步已核。固定最终SAC模型与初始模型/normalizer来源绑定，非PPO384更新规则。", '',
        '| 条件 | task/gate | stage | 当前阶段endpoint mm | lift mm | 步数/实际s |', '|---|---|---:|---:|---:|---|']
    for row in result['evaluations']:
        text.append(f"| {row['condition']} | {row['task_success']}/{row['development_gate']} | {row['final_stage']} | {1000*row['endpoint_error_m']:.3f} | {1000*row['lift_m']:.3f} | {row['action_steps']}/{row['duration_s']:.2f} |")
    text += ['', '示范额外预算与实际采样数量、全部产物hash见同名JSON。失败和安全早停全部保留，不跨阶段平均endpoint。', '',
        'sample实际返回张量由冻结runtime中的逐值断言核对，本离线审计核归档槽位、索引和当时仅online统计，并不声称未保存的sample张量、TD target、loss或梯度数值被独立重放。终态next仅为mask=0的占位；预算partial保留真next。', '',
        '单seed、单训练fixture与小预算结果不代表收敛、泛化或论文复现；没有把低频训练日志当作50µs物理子步主表。']
    if result['final_terminal_reset_from_saved_old_obs']:
        text += ['', '本run的在线预算恰在terminal结束。该唯一最后一次auto-reset输入取自hash绑定的最终normalizer.old_obs，用于核对末次RMS更新；它没有后继Gym action/journal的独立见证，不是由终态占位推造的物理观测。']
    args.output.with_suffix('.md').write_text('\n'.join(text)+'\n')
    print(json.dumps(dict(passed=True, output=str(args.output), branch=result['branch'],
                          insertions=result['insertions'], samples=result['samples'])))


if __name__ == '__main__':
    main()
