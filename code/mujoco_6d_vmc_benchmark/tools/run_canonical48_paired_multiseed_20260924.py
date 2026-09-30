"""Fixed additional seeds, preserving all original paired simulation/control bytes."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
import time
import traceback
os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
import run_canonical48_paired_ppo_20260924 as base

SEEDS = (20260924, 20260925)
PROTOCOL = 'docs/RL_PAIRED_MULTISEED_PROTOCOL_20260924.md'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_proofs(proof_root, manifest):
    proofs = {}
    for mode in ('parameter6', 'direct7'):
        folder = proof_root/mode
        require(not (folder/'FAILED.json').exists(), 'Original proof has FAILED marker')
        complete = json.loads((folder/'COMPLETE.json').read_text())
        parity = json.loads((folder/'PARITY.json').read_text())
        original = json.loads((folder/'manifest.json').read_text())
        require(complete['status'] == 'proof_passed' and parity['passed'] and not (folder/'FAILED.json').exists(), 'Incomplete original proof')
        require(all(x['mode'] == mode for x in (complete, parity, original)), 'Wrong proof mode')
        require(base.sha(folder/'PARITY.json') == complete['parity_sha256'], 'Proof parity drift')
        require(parity['source_hashes'] == original['source_hashes'], 'Proof source mismatch')
        for name, digest in original['source_hashes'].items():
            require(manifest['source_hashes'].get(name) == digest, 'Original execution bytes changed: '+name)
        for key in ('fixture_specs', 'asset_hashes', 'runtime', 'device', 'nominal_options'):
            require(original[key] == manifest[key], 'Original proof environment drift: '+key)
        require(parity['nominal_options'] == manifest['nominal_options'], 'Proof nominal options differ')
        require(original['protocol_sha256'] == manifest['base_protocol_sha256'], 'Original protocol drift')
        proofs[mode] = dict(manifest_sha256=base.sha(folder/'manifest.json'),
                            parity_sha256=base.sha(folder/'PARITY.json'),
                            complete_sha256=base.sha(folder/'COMPLETE.json'),
                            original_source_files=len(original['source_hashes']))
    return proofs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('parameter6', 'direct7'), required=True)
    parser.add_argument('--seed', type=int, choices=SEEDS, required=True)
    for name in ('output', 'assets', 'menagerie', 'proof-root'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--cpu-offset', type=int, required=True)
    args = parser.parse_args()
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.time()
    normalized = callback = None
    try:
        base.torch.set_num_threads(1)
        base.torch.set_num_interop_threads(1)
        cpus = sorted(os.sched_getaffinity(0))
        require(0 <= args.cpu_offset < len(cpus), 'Invalid CPU affinity index')
        os.sched_setaffinity(0, [cpus[args.cpu_offset]])
        base.resource_check()
        require(base.torch.cuda.is_available(), 'DGX CUDA required, no automatic device fallback')
        base.torch.cuda.set_per_process_memory_fraction(.15)
        specs, intersections = base.load_fixture_specs(args.assets)
        nominal = json.loads(specs['train']['command']['environment']['CORE_VMC_CONFIG'])
        manifest = dict(mode=args.mode, pid=os.getpid(), started_unix=started, argv=sys.argv,
            source_hashes=base.source_hashes(), fixture_specs=specs, split_intersections=intersections,
            nominal_options=nominal, nominal_rule='training options for all adapter episodes; runtime specs unchanged',
            reward=base.reward_protocol(), adapter=base.Canonical48VMCTuning.protocol(),
            actor_observation_dim=48, critic_observation_dim=48,
            policy_action_dim=6 if args.mode=='parameter6' else 7, execution_action_dim=7,
            actor_privileged_fields=[], critic_privileged_fields=[],
            training=dict(steps=8192, seed=args.seed, n_steps=64, batch_size=64, n_epochs=3,
                gamma=.995, gae_lambda=.95, learning_rate=3e-4, net_arch=[128,128],
                log_std_init=-2., selection='fixed final8192'),
            device='cuda', runtime=dict(python=sys.version, mujoco=base.mujoco.__version__,
                numpy=base.np.__version__, torch=base.torch.__version__, sb3=base.sb3.__version__,
                cuda_available=True, cuda_runtime=base.torch.version.cuda, gpu=base.torch.cuda.get_device_name()),
            asset_hashes=base.asset_hashes(args.menagerie),
            protocol_sha256=base.sha(ROOT/PROTOCOL),
            base_protocol_sha256=base.sha(ROOT/'docs/RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md'),
            cpu_affinity=sorted(os.sched_getaffinity(0)), threads=1, simulator_environments=1,
            control_class_limitations='Different output dimensions, VMC hidden memory/priors and executable action sets',
            transition_logging='Original paired journal plus original actual SB3 float32 reward callback',
            original_seed=20260923, additional_predeclared_seeds=list(SEEDS),
            source_rule='All original proof source bytes unchanged; new runner/protocol are separately hashed additions')
        manifest['proof_reuse'] = validate_proofs(args.proof_root, manifest)
        base.save_json(args.output/'manifest.json', manifest)
        env = base.PairedControlEnv(specs['train'], args.menagerie, args.output/'train',
                                   mode=args.mode, nominal_options=nominal)
        normalized = base.VecNormalize(base.DummyVecEnv([lambda:env]), norm_obs=True, norm_reward=False, clip_obs=12.)
        model = base.sb3.PPO('MlpPolicy', normalized, learning_rate=3e-4, n_steps=64, batch_size=64,
            n_epochs=3, gamma=.995, gae_lambda=.95, seed=args.seed, device='cuda',
            policy_kwargs=dict(net_arch=[128,128], log_std_init=-2.), verbose=0)
        callback = base.PairedProgress(args.output, started)
        base.save_json(args.output/'model_architecture.json', dict(mode=args.mode,
            policy_class=type(model.policy).__name__,
            trainable_parameter_count=sum(p.numel() for p in model.policy.parameters() if p.requires_grad),
            parameter_shapes={name:list(p.shape) for name,p in model.policy.named_parameters()},
            observation_dim=48, policy_action_dim=manifest['policy_action_dim'], execution_action_dim=7))
        model.learn(8192, callback=callback)
        model.save(args.output/'ppo_final.zip')
        normalized.save(args.output/'vecnormalize_train_only.pkl')
        normalized.training=False
        normalized.close()
        model=base.sb3.PPO.load(args.output/'ppo_final.zip', device='cuda')
        require(model.num_timesteps==8192, 'Wrong final interaction budget')
        before=(normalized.obs_rms.mean.copy(), normalized.obs_rms.var.copy(), normalized.obs_rms.count)
        results={}
        for split in ('train','validation'):
            for kind in ('zero','ppo'):
                base.save_json(args.output/'progress.json',dict(status='evaluation',mode=args.mode,
                    seed=args.seed,split=split,kind=kind,pid=os.getpid()))
                results[f'{split}/{kind}']=base.evaluate(specs[split],args.menagerie,args.output/'eval'/split/kind,
                    args.mode,nominal,model if kind=='ppo' else None,normalized)
                base.save_json(args.output/'evaluation.json',results)
        require(base.np.array_equal(before[0],normalized.obs_rms.mean) and
                base.np.array_equal(before[1],normalized.obs_rms.var) and before[2]==normalized.obs_rms.count,
                'Evaluation changed normalization')
        require(base.source_hashes()==manifest['source_hashes'], 'Frozen source drift')
        require(base.asset_hashes(args.menagerie)==manifest['asset_hashes'], 'Assets drift')
        require(base.sha(ROOT/PROTOCOL)==manifest['protocol_sha256'], 'Protocol drift')
        count=0
        for file in (args.output/'train').rglob('transitions.npz'):
            with base.np.load(file,allow_pickle=False) as data:
                count+=len(data['reward'])
        require(count==8192, 'Missing training transitions')
        base.save_json(args.output/'COMPLETE.json',dict(status='complete',mode=args.mode,seed=args.seed,
            training_steps=8192,recorded_transitions=count,updates=model._n_updates,normalization_frozen=True,
            results=results,checkpoint_sha256=base.sha(args.output/'ppo_final.zip'),
            normalizer_sha256=base.sha(args.output/'vecnormalize_train_only.pkl'),
            elapsed_s=time.time()-started,source_unchanged=True,publication_ready=False))
        base.save_json(args.output/'progress.json',dict(status='complete',mode=args.mode,seed=args.seed,pid=os.getpid()))
    except BaseException as error:
        base.save_json(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),pid=os.getpid()))
        raise
    finally:
        if normalized is not None:
            normalized.close()
        if callback is not None and not callback.reward_log.closed:
            callback.reward_log.close()


if __name__=='__main__':
    main()
