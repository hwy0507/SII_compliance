"""Fixed-budget standard SAC/direct7, with optional pinned train-only prefill."""
from __future__ import annotations

import argparse
import inspect
import json
import os
from pathlib import Path
import sys
import time
import traceback
import zipfile

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import numpy as np
import torch
import mujoco
import stable_baselines3 as sb3
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize
from stable_baselines3.common.off_policy_algorithm import OffPolicyAlgorithm
from stable_baselines3.common.buffers import ReplayBuffer
from stable_baselines3.sac.policies import SACPolicy
from canonical48_paired_rl_env_20260924 import PairedControlEnv
from canonical48_sac_audit_20260925 import AuditedReplayBuffer, OnlineEvidenceEnv, SACProgress, prefill, require, stats
from canonical48_rl_env_20260923 import load_fixture_specs, save_json, sha, resource_check
from canonical48_potential_reward_20260924 import protocol as reward_protocol
import run_canonical48_paired_ppo_20260924 as paired
import verify_train_demo_replay_20260924 as demo_protocol

STEPS = 8192
SEED = 20260923


def hyperparameters():
    return dict(learning_rate=3e-4, buffer_size=1_000_000, learning_starts=100, batch_size=256,
                tau=.005, gamma=.995, train_freq=1, gradient_steps=1, action_noise=None,
                optimize_memory_usage=False, n_steps=1, ent_coef='auto', target_entropy='auto',
                target_update_interval=1, use_sde=False, sde_sample_freq=-1,
                use_sde_at_warmup=False, seed=SEED, policy_kwargs=dict(net_arch=[256, 256]))


def verify_proofs(proof_root, manifest):
    evidence = {}
    for mode in ('parameter6', 'direct7'):
        folder = proof_root / mode
        require(not (folder / 'FAILED.json').exists(), 'Proof has FAILED marker')
        proof = json.loads((folder / 'manifest.json').read_text())
        complete = json.loads((folder / 'COMPLETE.json').read_text())
        parity = json.loads((folder / 'PARITY.json').read_text())
        require(complete['status'] == 'proof_passed' and parity['passed'], 'Proof incomplete')
        require(all(item['mode'] == mode for item in (proof, complete, parity)), 'Proof mode mismatch')
        for field in ('fixture_specs', 'asset_hashes', 'runtime', 'device', 'nominal_options'):
            require(proof[field] == manifest[field], 'SAC/proof environment drift: ' + field)
        require(proof['protocol_sha256'] == manifest['base_protocol_sha256'], 'Original protocol drift')
        require(proof['reward'] == manifest['reward'], 'Proof reward drift')
        require(all(manifest['source_hashes'].get(name) == digest for name, digest in proof['source_hashes'].items()),
                'Original execution source bytes changed')
        require(parity['source_hashes'] == proof['source_hashes'] and parity['nominal_options'] == manifest['nominal_options'],
                'Proof coverage mismatch')
        require(sha(folder / 'PARITY.json') == complete['parity_sha256'], 'Proof parity hash drift')
        evidence[mode] = {name: sha(folder / name) for name in ('manifest.json', 'COMPLETE.json', 'PARITY.json')}
    return evidence


def read_demo(path):
    require(sha(path / 'manifest.json') == demo_protocol.DEMO_MANIFEST, 'Only pinned r2 demonstration is permitted')
    manifest = json.loads((path / 'manifest.json').read_text())
    for name, digest in manifest['artifact_sha256'].items():
        require(sha(path / name) == digest, 'Demo artifact drift: ' + name)
    with np.load(path / 'demonstration.npz', allow_pickle=False) as archive:
        data = {key: archive[key] for key in archive.files}
    demo_protocol.validate(data)
    return data, dict(manifest_sha256=sha(path / 'manifest.json'), artifact_sha256=manifest['artifact_sha256'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--branch', choices=['online_only', 'demo_prefill'], required=True)
    for name in ('output', 'assets', 'menagerie', 'proof-root'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--demo', type=Path)
    parser.add_argument('--cpu-offset', type=int, default=0)
    args = parser.parse_args()
    require((args.branch == 'demo_prefill') == (args.demo is not None), 'Demo path required only for prefill branch')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    normalized = callback = model = None
    try:
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        allowed = sorted(os.sched_getaffinity(0))
        require(0 <= args.cpu_offset < len(allowed), 'Invalid CPU affinity offset')
        os.sched_setaffinity(0, [allowed[args.cpu_offset]])
        resource_check()
        require(sb3.__version__ == '2.9.0', 'SAC defaults were reviewed for SB3 2.9.0')
        require(torch.cuda.is_available(), 'DGX CUDA required; no device fallback')
        torch.cuda.set_per_process_memory_fraction(.15)
        specs, intersections = load_fixture_specs(args.assets)
        nominal = json.loads(specs['train']['command']['environment']['CORE_VMC_CONFIG'])
        training = dict(steps=STEPS, seed=SEED, **{key: value for key, value in hyperparameters().items() if key != 'seed'},
                        expected_updates=STEPS-100, selection='fixed final8192 after its final gradient update')
        manifest = dict(algorithm='standard SAC', mode='direct7', branch=args.branch, pid=os.getpid(), argv=sys.argv,
            started_unix=started, source_hashes=paired.source_hashes(), asset_hashes=paired.asset_hashes(args.menagerie),
            fixture_specs=specs, split_intersections=intersections, nominal_options=nominal,
            reward=reward_protocol(), training=training, device='cuda',
            runtime=dict(python=sys.version, mujoco=mujoco.__version__, numpy=np.__version__, torch=torch.__version__,
                         sb3=sb3.__version__, cuda_available=torch.cuda.is_available(), cuda_runtime=torch.version.cuda,
                         gpu=torch.cuda.get_device_name()),
            sb3_source_sha256={name: sha(Path(inspect.getfile(cls))) for name, cls in
                               [('SAC', sb3.SAC), ('SACPolicy', SACPolicy), ('OffPolicyAlgorithm', OffPolicyAlgorithm),
                                ('ReplayBuffer', ReplayBuffer), ('VecNormalize', VecNormalize)]},
            protocol_sha256=sha(ROOT / 'docs/CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md'),
            base_protocol_sha256=sha(ROOT / 'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md'),
            actor_observation_dim=48, critic_observation_dim=48, critic_action_dim=7, policy_action_dim=7,
            execution_action_dim=7, actor_privileged_fields=[], critic_privileged_fields=[],
            threads=1, simulator_environments=1, cpu_affinity=sorted(os.sched_getaffinity(0)),
            normalization=dict(norm_obs=True, norm_reward=False, clip_obs=12., clip_reward=10., gamma=.99,
                               epsilon=1e-8, training=True, source='Own online training reset/step only; no demo/PPO statistics'),
            data_budget=dict(online=8192, demo=600 if args.demo is not None else 0,
                             total=8792 if args.demo is not None else 8192, offline_updates=0),
            action_contract='Actual SAC buffer_actions logged before store; unscale equals environment request. Journal Gaussian wording belongs to original PPO.',
            limitations=['Standard SAC uniform replay; not RLPD or a paper reproduction',
                         'Different network/gradient budget from PPO; no equal-compute claim',
                         'Terminal next is masked placeholder; partial next remains real',
                         'No actual TD-target/loss/gradient-value numerical audit is claimed'])
        manifest['proof_sha256'] = verify_proofs(args.proof_root.resolve(), manifest)
        data = None
        if args.demo is not None:
            data, manifest['demo'] = read_demo(args.demo.resolve())
        else:
            manifest['demo'] = None
        save_json(args.output / 'manifest.json', manifest)
        env = OnlineEvidenceEnv(PairedControlEnv(specs['train'], args.menagerie, args.output / 'train',
                                                mode='direct7', nominal_options=nominal))
        normalized = VecNormalize(DummyVecEnv([lambda: env]), norm_obs=True, norm_reward=False, clip_obs=12.)
        model = sb3.SAC('MlpPolicy', normalized, **hyperparameters(), device='cuda',
                       replay_buffer_class=AuditedReplayBuffer,
                       replay_buffer_kwargs=dict(audit_directory=args.output / 'replay_audit',
                                                 expected_demo=manifest['data_budget']['demo'], handle_timeout_termination=True), verbose=0)
        model.replay_buffer.start_audit()
        initial_stats = stats(normalized)
        model.save(args.output / 'sac_initial.zip')
        normalized.save(args.output / 'vecnormalize_initial.pkl')
        manifest['initial_artifact_sha256'] = {name: sha(args.output / name) for name in
                                               ('sac_initial.zip', 'vecnormalize_initial.pkl')}
        manifest['actual_optimizer_defaults'] = {name: dict(class_name=type(optimizer).__name__, defaults=optimizer.defaults)
            for name, optimizer in [('actor', model.actor.optimizer), ('critic', model.critic.optimizer),
                                    ('entropy', model.ent_coef_optimizer)]}
        # Still before prefill, learn/reset, or any physical simulator step.
        save_json(args.output / 'manifest.json', manifest)
        save_json(args.output / 'model_architecture.json', dict(policy_class=type(model.policy).__name__,
            policy=str(model.policy), trainable_parameter_count=sum(p.numel() for p in model.policy.parameters() if p.requires_grad),
            parameter_shapes={name: list(value.shape) for name, value in model.policy.named_parameters()},
            target_entropy=model.target_entropy, initial_alpha=float(model.log_ent_coef.exp().detach().cpu()),
            initial_normalization=initial_stats))
        if data is not None:
            prefill(model.replay_buffer, data)
        require(stats(normalized) == initial_stats, 'Prefill fitted observation statistics')
        callback = SACProgress(args.output, started, resource_check)
        model.learn(STEPS, callback=callback)
        require(model.num_timesteps == STEPS and model._n_updates == STEPS-model.learning_starts,
                'Incomplete online or update budget')
        require(all(count == model._n_updates for count in callback.optimizer_steps.values()), 'Actual optimizer step count mismatch')
        require(model.replay_buffer.sample_calls == model._n_updates, 'Replay sample/update count mismatch')
        model.save(args.output / 'sac_final.zip')
        normalized.save(args.output / 'vecnormalize_train_only.pkl')
        replay_report = model.replay_buffer.export_valid(args.output / 'replay_valid.npz')
        save_json(args.output / 'replay_summary.json', replay_report)
        save_json(args.output / 'optimizer_summary.json', dict(actual_optimizer_steps=callback.optimizer_steps,
            actual_updates=model._n_updates, expected_updates=STEPS-100))
        normalized.training = False
        normalized.close()
        with zipfile.ZipFile(args.output / 'sac_final.zip') as archive:
            saved = json.loads(archive.read('data'))
        require(saved.get('seed') == SEED and saved['num_timesteps'] == STEPS and saved['_n_updates'] == model._n_updates,
                'Final saved metadata mismatch')
        evaluation_model = sb3.SAC.load(args.output / 'sac_final.zip', device='cuda')
        frozen_stats = stats(normalized)
        results = {}
        for split in ('train', 'validation'):
            for kind in ('zero', 'sac'):
                save_json(args.output / 'progress.json', dict(status='evaluation', split=split, kind=kind, pid=os.getpid()))
                results[f'{split}/{kind}'] = paired.evaluate(specs[split], args.menagerie,
                    args.output / 'eval' / split / kind, 'direct7', nominal,
                    evaluation_model if kind == 'sac' else None, normalized)
                save_json(args.output / 'evaluation.json', results)
        require(stats(normalized) == frozen_stats, 'Evaluation changed normalization')
        require(paired.source_hashes() == manifest['source_hashes'], 'Source drift during run')
        require(paired.asset_hashes(args.menagerie) == manifest['asset_hashes'], 'Model asset drift during run')
        require(sha(ROOT / 'docs/CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md') == manifest['protocol_sha256'],
                'SAC protocol drift during run')
        require(sha(ROOT / 'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md') == manifest['base_protocol_sha256'],
                'Base protocol drift during run')
        require(verify_proofs(args.proof_root.resolve(), manifest) == manifest['proof_sha256'], 'Proof artifact drift during run')
        for name, digest in manifest['initial_artifact_sha256'].items():
            require(sha(args.output / name) == digest, 'Initial model/normalizer artifact drift')
        if args.demo is not None:
            _, final_demo = read_demo(args.demo.resolve())
            require(final_demo == manifest['demo'], 'Demo provenance drift during run')
        transitions = 0
        for path in (args.output / 'train').rglob('transitions.npz'):
            with np.load(path, allow_pickle=False) as archive:
                transitions += len(archive['reward'])
        require(transitions == STEPS == model.replay_buffer.online_steps, 'Gym/replay training budget mismatch')
        save_json(args.output / 'COMPLETE.json', dict(status='complete', mode='direct7', branch=args.branch, seed=SEED,
            training_steps=STEPS, recorded_transitions=transitions, updates=model._n_updates,
            optimizer_steps=callback.optimizer_steps, normalization_frozen=True, results=results,
            checkpoint_sha256=sha(args.output / 'sac_final.zip'), normalizer_sha256=sha(args.output / 'vecnormalize_train_only.pkl'),
            replay_sha256=sha(args.output / 'replay_valid.npz'), elapsed_s=time.time()-started,
            source_unchanged=True, publication_ready=False))
        save_json(args.output / 'progress.json', dict(status='complete', branch=args.branch, pid=os.getpid()))
    except BaseException as error:
        save_json(args.output / 'FAILED.json', dict(error=repr(error), traceback=traceback.format_exc(), pid=os.getpid()))
        raise
    finally:
        if normalized is not None:
            normalized.close()
        if callback is not None:
            callback.close_logs()
        if model is not None:
            model.replay_buffer.close_logs()


if __name__ == '__main__':
    main()
