"""Audit all archived learned candidates at the deployed actor input boundary.

Uses one already public training identity, no fitting or physics. This does not
certify upstream observer realism, task-reference generation, RL input usage,
or closed-loop stability. No final condition or outcome is read.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import sys
import numpy as np
from research72_inference_profile_20261003 import ROOT, read, sha
from current_student_policy_20260921 import load_current

ALLOWED = np.r_[14:17, 20:23, 26:29, 39:48]
PERTURBED = np.setdiff1d(np.arange(48), ALLOWED)
SEED = 2026100343


def audit(checkpoint, observations, expected):
    assert observations.ndim == 2 and observations.shape[1] == 48
    assert expected.shape == (len(observations), 7)
    original = load_current(checkpoint)
    changed = load_current(checkpoint)
    mutated = observations.copy()
    mutated[:, PERTURBED] = np.random.default_rng(SEED).uniform(-1000, 1000,
        (len(observations), len(PERTURBED)))
    original.reset(); changed.reset()
    replay_error = 0.
    state_checks = 0
    for obs, altered, reference in zip(observations, mutated, expected):
        # Fail if an actor modifies the supplied observation in place.
        obs.setflags(write=False); altered.setflags(write=False)
        left, right = original.act(obs), changed.act(altered)
        np.testing.assert_array_equal(left, right)
        assert left.shape == (7,) and np.isfinite(left).all()
        assert 0 <= left[0] <= 1 and np.all(abs(left[1:]) <= 1)
        replay_error = max(replay_error, float(np.max(abs(left-reference))))
        if hasattr(original, 'state'):
            np.testing.assert_array_equal(original.state, changed.state)
            assert np.isfinite(original.state).all()
            state_checks += 1
    assert replay_error < 1e-11
    return dict(samples=len(observations), action_difference_max_abs=0.,
        exported_replay_max_abs=replay_error, hidden_state_checks=state_checks,
        hidden_state_difference_max_abs=0. if state_checks else None,
        supplied_observation_not_modified=True, bounded_finite_requested_actions=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('data', 'metadata', 'output'):
        p.add_argument('--'+name, type=Path, required=True)
    p.add_argument('--learning', nargs='+', type=Path, required=True)
    a = p.parse_args()
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    limit = int((cg/'memory.max').read_text()); assert limit <= 3*1024**3
    metadata = read(a.metadata)
    assert metadata['lineage'][0]['data_role'] == 'train' and metadata['all_real_execution']
    assert sha(a.data) == metadata['training_data_sha256']
    with np.load(a.data) as z:
        indices = np.flatnonzero(z['episode'] == 0)
        observations = z['observation'][indices].copy()
    assert observations.shape == (1375, 48)
    rows = []; sources = [Path(__file__), ROOT/'tools/research72_inference_profile_20261003.py']
    sources += [ROOT/'scripts'/name for name in ('current_student_policy_20260921.py',
        'office_vmc_memory_esn_20260927.py', 'office_context_network_20261003.py', 'office_mlp_rnn_20261002.py')]
    for folder in a.learning:
        state, spec = read(folder/'execution.json'), read(folder/'SPECIFICATION.json')
        assert state['status'] == 'complete' and spec['data_sha256'] == sha(a.data)
        receipts = {row['name']: row for row in state['rows']}
        assert set(receipts) == {job['name'] for job in spec['jobs']}
        for job in spec['jobs']:
            model = folder/job['name']; cp = model/'checkpoint.npz'; record = receipts[job['name']]
            assert record['returncode'] == 0 and sha(cp) == record['checkpoint_sha256']
            assert sha(model/'TRAINING_COMPLETE.json') == record['training_metadata_sha256']
            with np.load(model/'exported_replay.npz') as z:
                expected = z['prediction'][indices].copy()
            checks = audit(cp, observations, expected)
            assert sha(cp) == record['checkpoint_sha256']
            rows.append(dict(name=job['name'], family=job['family'], training_seed=job['seed'],
                checkpoint=str(cp.resolve()), checkpoint_sha256=sha(cp),
                specification_sha256=sha(folder/'SPECIFICATION.json'), **checks))
    assert len({row['name'] for row in rows}) == len(rows)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), host=platform.node(),
        python=sys.executable, numpy=np.__version__, memory_max=limit,
        data_sha256=sha(a.data), data_metadata_sha256=sha(a.metadata),
        input_identity=metadata['lineage'][0]['condition_id'], perturbation_seed=SEED,
        permitted_fields=ALLOWED.tolist(), perturbed_fields=PERTURBED.tolist(),
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in sources}, rows=rows,
        physics_steps=0, training_updates=0, final_conditions_read=False,
        scope='All provided fitted ESN/memoryless/MLP/RNN candidates; no success eligibility filtering.',
        limitations=['Observed invariance for one known1375-step training sequence, not proof on all possible inputs.',
            'The other30 canonical fields are not themselves privileged truth; this tests the declared18-field learned-actor subset.',
            'Reference-relative motion and estimated wrench are permitted; no audit of upstream sensor accuracy or simulator independence.',
            'Does not cover RL or classical actors, contact handling, task success or closed-loop stability.'])
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(models=len(rows), output_sha256=sha(a.output),
        samples=sum(row['samples'] for row in rows), maximum_replay_error=max(row['exported_replay_max_abs'] for row in rows))))


if __name__ == '__main__':
    main()
