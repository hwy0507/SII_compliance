"""Finite read-only action preference diagnosis on a reviewed SERL checkpoint.

Candidate actions are evaluated only by the critic, never executed or added to
replay. Q preferences are not evidence of causal physical improvement.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(args):
    os.sched_setaffinity(0, {54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg = json.loads(args.registration.read_text())
    assert sha(args.checkpoint) == reg['checkpoint_sha256']
    assert sha(__file__) == reg['source_sha256']
    for name, expected in reg['adapter_hashes'].items():
        assert sha(args.adapter/name) == expected
    sys.path.insert(0, str(args.adapter))
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    x = torch.load(args.checkpoint, map_location='cpu', weights_only=False)
    assert x['cycle'] == 11 and x['boundary'] == 'complete_condition_cycle'
    learner = SerlMultistepLearner(args.runtime, upstream=args.upstream,
        upstream_manifest=args.upstream_manifest, dimension=7, direct=True,
        seed=x['seed'], device='cuda:0')
    learner.load_state_dict(x['learner'])
    before = digest(learner.state_dict())
    assert before == digest(x['learner'])
    arrays = x['replay']['arrays']
    recent_start = reg['recent_start']
    assert recent_start == 442032 and x['replay']['size'] == 483282
    rng = np.random.default_rng(reg['seed'])
    ids = np.sort(rng.choice(np.arange(recent_start, x['replay']['size']), size=reg['states'], replace=False))
    assert reg['states'] == 1024
    obs = arrays['observations'][ids]
    observations = learner.jax.device_put(dict(state=np.ascontiguousarray(obs[:,:48]), clock=np.ascontiguousarray(obs[:,48:49])))
    jax = learner.jax
    mode = np.asarray(learner.agent.sample_actions(observations, argmax=True))
    candidates = dict(replay=arrays['actions'][ids], mode=mode)
    neutral = np.zeros_like(mode); neutral[:,0] = -1
    candidates['public_zero'] = neutral
    first_only = mode.copy(); first_only[:,0] = -1
    candidates['mode_public0_zero'] = first_only
    residual_only = np.zeros_like(mode); residual_only[:,0] = mode[:,0]
    candidates['mode_residuals_zero'] = residual_only
    for index in range(4):
        candidates[f'stochastic_{index}'] = np.asarray(learner.agent.sample_actions(observations, seed=jax.random.PRNGKey(reg['seed']+index)))
    def stats(values):
        values = np.asarray(values)
        assert np.isfinite(values).all()
        return dict(count=int(values.size), mean=float(values.mean()), p05=float(np.percentile(values,5)), p50=float(np.median(values)), p95=float(np.percentile(values,95)), maximum=float(values.max()))
    qs = {}
    reports = {}
    for label, actions in candidates.items():
        q = np.asarray(learner.agent.forward_critic(observations, learner.jax.device_put(actions), rng=jax.random.PRNGKey(412)))
        assert q.shape == (10,1024)
        qs[label] = q
        reports[label] = dict(q_ensemble_mean=stats(q.mean(axis=0)), q_ensemble_std=stats(q.std(axis=0)),
            public0=stats((actions[:,0]+1)*.5), residual_abs=stats(np.abs(actions[:,1:])), residual_saturation_fraction=float((np.abs(actions[:,1:])>.95).mean()))
    for label,q in qs.items():
        diff = q.mean(axis=0)-qs['mode'].mean(axis=0)
        reports[label].update(q_advantage_over_mode=stats(diff), preferred_over_mode_fraction=float((diff>0).mean()),
            all_critics_prefer_over_mode_fraction=float(((q-qs['mode'])>0).all(axis=0).mean()))
    def objective(actions):
        return learner.agent.forward_critic(observations,actions,rng=jax.random.PRNGKey(412)).mean(axis=0).sum()
    gradients = np.asarray(jax.grad(objective)(jax.numpy.asarray(mode)))
    assert gradients.shape == mode.shape and np.isfinite(gradients).all()
    after = digest(learner.state_dict())
    assert before == after
    assert sha(args.checkpoint) == reg['checkpoint_sha256']
    report = dict(passed=True,time=time.time(),checkpoint_sha256=reg['checkpoint_sha256'],source_sha256=sha(__file__),
        sampled_indices_sha256=hashlib.sha256(ids.tobytes()).hexdigest(),sampled_rows=ids.tolist(),
        candidates=reports,mean_abs_q_gradient_per_raw_channel=np.abs(gradients).mean(axis=0).tolist(),
        network_optimizer_rng_unchanged=True,new_optimizer_updates=0,new_physics=0,weights_saved=False,
        interpretation='Official SERL actor uses the mean of all10 critics plus entropy; this audit compares same-state Q predictions only. public0=0 is raw0=-1. Candidate ablations are not physical runs, causal gains, demonstrations, or proposed formal action mixing. Replay has evolving behavior and states; current stochastic policy differs from its deterministic mode.',
        convergence_claim=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,preferences={k:v['q_advantage_over_mode']['mean'] for k,v in reports.items()},gradients=report['mean_abs_q_gradient_per_raw_channel'])),flush=True)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['registration','checkpoint','runtime','adapter','upstream','upstream-manifest','output']:
        p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
