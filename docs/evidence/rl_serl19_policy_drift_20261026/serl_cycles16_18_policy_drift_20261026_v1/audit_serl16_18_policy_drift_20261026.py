"""Compare frozen16-18 policies on identical retained16 inputs; no updates."""
from pathlib import Path
import argparse
import gc
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(root):
    os.sched_setaffinity(0, {52})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads((root/'REGISTRATION.json').read_text())
    assert reg['cycles'] == [16, 17, 18] and reg['seed'] == 2026102630
    assert reg['uniform_rows'] == 4096 and reg['initial_rows'] == 510
    assert sha(__file__) == reg['source_sha256']
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    sys.path[:0] = [reg['adapter_runtime'], str(Path(reg['runtime'])/'source/tools')]
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    frozen = json.loads(Path(reg['frozen16_review']['path']).read_text())
    assert sha(reg['frozen16_review']['path']) == reg['frozen16_review']['sha256']
    assert frozen['passed'] and frozen['formal_state_unchanged'] and len(frozen['episodes']) == 30
    reference = torch.load(reg['inputs']['16']['checkpoint']['path'], map_location='cpu', weights_only=False)
    arrays = reference['replay']['arrays']
    selected = dict(initial=np.flatnonzero(arrays['observations'][:, 48] == np.float32(1)),
                    uniform=np.random.default_rng(reg['seed']).choice(reference['replay']['size'], 4096, replace=False))
    assert len(selected['initial']) == 510
    all_rows = np.concatenate(list(selected.values()))
    retained = {k: v[all_rows].copy() for k, v in arrays.items()}
    inputs = {k: arrays['observations'][rows].copy() for k, rows in selected.items()}
    np.savez_compressed(root/'fixed_inputs.npz', **{k+'_rows': v for k, v in selected.items()},
                        **{k+'_observations': v for k, v in inputs.items()})
    del arrays, reference
    gc.collect()
    values, cycles = {}, {}

    def stats(v):
        v = np.asarray(v, np.float64)
        assert np.isfinite(v).all()
        return dict(mean=float(v.mean()), p95=float(np.percentile(v, 95)), maximum=float(v.max()))

    for cycle in reg['cycles']:
        refs = reg['inputs'][str(cycle)]
        ck = torch.load(refs['checkpoint']['path'], map_location='cpu', weights_only=False)
        review = json.loads(Path(refs['review']['path']).read_text())
        health = json.loads(Path(refs['health']['path']).read_text())
        assert ck['cycle'] == cycle and ck['boundary'] == 'complete_condition_cycle'
        assert ck['protocol_sha256'] == refs['protocol']['sha256']
        assert review['passed'] and health['network_optimizer_rng_unchanged']
        assert review['methods']['direct']['checkpoint_sha256'] == health['checkpoint_sha256'] == refs['checkpoint']['sha256']
        for k, v in retained.items():
            np.testing.assert_array_equal(ck['replay']['arrays'][k][all_rows], v)
        replay_before = digest(ck['replay'])
        learner = SerlMultistepLearner(Path(reg['runtime']), upstream=Path(reg['upstream']),
            upstream_manifest=Path(reg['upstream_manifest']), dimension=7, direct=True,
            seed=ck['seed'], device='cuda:0')
        learner.load_state_dict(ck['learner'])
        before = digest(learner.state_dict())
        assert before == digest(ck['learner'])
        jax = learner.jax
        assert jax.config.jax_default_matmul_precision is None
        cohorts = {}
        for i, (name, observations) in enumerate(inputs.items()):
            obs = jax.device_put(dict(state=observations[:, :48], clock=observations[:, 48:49]))
            policy_key, sample_key = jax.random.split(jax.random.PRNGKey(reg['seed']+i))
            distribution = learner.agent.forward_policy(obs, rng=policy_key)
            loc = np.asarray(distribution.distribution.mean())
            scale = np.asarray(distribution.distribution.stddev())
            mode = np.asarray(distribution.mode())
            sample, logp = distribution.sample_and_log_prob(seed=sample_key)
            sample, logp = np.asarray(sample), np.asarray(logp)
            assert loc.shape == scale.shape == mode.shape == sample.shape == (len(observations), 7)
            assert np.all(scale > 0)
            np.testing.assert_allclose(np.tanh(loc), mode, rtol=1e-6, atol=1e-6)
            for label, value in dict(loc=loc, scale=scale, mode=mode, sample=sample, logp=logp).items():
                assert np.isfinite(value).all()
                values[f'{cycle}_{name}_{label}'] = value
            cohorts[name] = dict(rows=len(observations), unique_observations=len(np.unique(observations, axis=0)),
                public0_mode_mean=float(((mode[:, 0]+1)*.5).mean()),
                residual_mode_abs_mean=float(np.abs(mode[:, 1:]).mean()),
                sampled_entropy_mean=float((-logp).mean()), latent_std_mean=scale.mean(axis=0).tolist())
        assert digest(learner.state_dict()) == before and digest(ck['replay']) == replay_before
        cycles[str(cycle)] = dict(full_learner_digest=before, replay_digest=replay_before,
            full_network_optimizer_rng_replay_unchanged=True, cohorts=cohorts)
        del learner, ck
        gc.collect()
    drifts = {}
    for first, last in [(16, 17), (17, 18), (16, 18)]:
        drifts[f'{first}_to_{last}'] = {}
        for name in inputs:
            a = {k: values[f'{first}_{name}_{k}'].astype(np.float64) for k in ['loc', 'scale', 'mode', 'sample']}
            z = {k: values[f'{last}_{name}_{k}'].astype(np.float64) for k in a}
            kl = np.sum(np.log(z['scale']/a['scale']) +
                (a['scale']**2+(a['loc']-z['loc'])**2)/(2*z['scale']**2)-.5, axis=1)
            assert (kl >= -1e-10).all()
            drifts[f'{first}_to_{last}'][name] = dict(
                raw_mode_abs_delta=stats(np.abs(z['mode']-a['mode'])),
                public0_mode_abs_delta=stats(np.abs(z['mode'][:, 0]-a['mode'][:, 0])*.5),
                coupled_sample_abs_delta=stats(np.abs(z['sample']-a['sample'])),
                latent_gaussian_kl_old_to_new=stats(kl))
    np.savez_compressed(root/'policy_values.npz', **values)
    for refs in reg['inputs'].values():
        for ref in refs.values():
            assert sha(ref['path']) == ref['sha256']
    result = dict(passed=True, time=time.time(), cycles=cycles, drifts=drifts,
        fixed_inputs_sha256=sha(root/'fixed_inputs.npz'), policy_values_sha256=sha(root/'policy_values.npz'),
        optimizer_updates=0, new_physics=0, replay_writes=0, weights_saved=False,
        default_formal_precision=True, convergence_claim=False,
        limitation='Same retained16 normalized inputs and fixed external noise draws across full16/17/18 states. Initial510 rows include repeated observations and uniform4096 is a fixed retained16 sample, not new-policy visitation. Mode is the API deterministic tanh(location), not a deterministic rollout. Latent diagonal-normal KL describes distributions, not task-effect causality or independent training seeds. No stationarity threshold or automatic stopping; small action differences alone do not establish convergence. All formal states remain untouched.')
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        (args.root/'FAILURE.json').write_text(json.dumps(dict(error=repr(error), time=time.time()))+'\n')
        raise
