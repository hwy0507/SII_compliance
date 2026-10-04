"""Reconstruct registered random ESN matrices; no fitting, inference or physics.

This checks the existing context ESN checkpoint contract, including every
retained ridge candidate. It does not prove closed-loop stability, the echo
state property, teacher quality or task superiority. Neural controls are
explicitly excluded: their input/recurrent matrices are allowed to learn.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def fixed_arrays(seed, candidate, metadata):
    rng = np.random.default_rng(seed)
    recurrent = rng.normal(size=(128, 128)) * (rng.random((128, 128)) < .08)
    recurrent /= max(np.max(abs(np.linalg.eigvals(recurrent))), 1e-12)
    inputs = rng.normal(size=(128, 156))
    inputs[:, 12:] /= 3.
    assert candidate['rho'] in (.5, .8) and candidate['input_gain'] in (.08, .25, .6)
    result = dict(w=candidate['rho'] * recurrent, win=candidate['input_gain'] * inputs,
        leak=1-np.exp(-.04/np.repeat([.04, .12, .5, 2.], 32)),
        scale=np.array([8., 8., 8., 1., 1., 1.]))
    if metadata['contextual_leak_gate']:
        result['context_gate_w'] = np.random.default_rng(seed+40000).normal(0, 1, (128, 12))
        limits = metadata['gate_multiplier_limits']
        if limits != [.05, 2.]:
            result['context_gate_limits'] = np.array(limits)
    if metadata.get('state_context_readout', False):
        result['state_context_readout_w'] = np.random.default_rng(seed+50000).normal(
            0, 1/np.sqrt(12), (128, 12))
    return result


def verify_values(values, fixed, metadata, family):
    constants = dict(contract='proprio48_office_vmc_memory_esn_v1',
        absolute_inputs=True, context_inputs=True, position_context=True,
        axis_separable=False, readout_activation='clipped_linear', output_gain=1.,
        reset_at_each_observation=family == 'memoryless')
    # Additional learned layers, thresholds or output gains must not silently
    # pass as a checkpoint with only the declared final readout trained.
    assert set(values) == set(fixed) | set(constants) | {'weights'}, 'Undeclared checkpoint fields'
    for key, value in constants.items():
        assert np.asarray(values[key]).shape == () and values[key].item() == value, key
    for key, expected in fixed.items():
        np.testing.assert_array_equal(values[key], expected, err_msg=key)
    expected_features = 424 + (128 if metadata.get('state_context_readout', False) else 0)
    weights = values['weights']
    assert weights.shape == (expected_features, 7) and np.isfinite(weights).all()
    np.testing.assert_array_equal(weights[-12:], np.zeros((12, 7)))
    assert metadata['trainable_readout_coefficients'] == (expected_features-12)*7
    assert metadata['reservoir_width'] == 128 and metadata['learned_hidden_readout_width'] == 0
    assert metadata['readout_activation'] == constants['readout_activation']
    assert metadata['reset_at_each_observation'] == constants['reset_at_each_observation']
    assert metadata.get('state_context_projection_trainable', False) is False


def audit_learning(path):
    state = read(path/'execution.json'); spec = read(path/'SPECIFICATION.json')
    assert state['status'] == 'complete' and state['specification_sha256'] == sha(path/'SPECIFICATION.json')
    jobs = {j['name']: j for j in spec['jobs']}
    assert {r['name'] for r in state['rows']} == set(jobs)
    rows = []; excluded = []
    for record in state['rows']:
        job = jobs[record['name']]
        if job['family'] not in ('esn', 'memoryless'):
            excluded.append(dict(name=job['name'], family=job['family']))
            continue
        base = path/job['name']; meta = read(base/'TRAINING_COMPLETE.json')
        assert sha(base/'TRAINING_COMPLETE.json') == record['training_metadata_sha256']
        assert sha(base/'checkpoint.npz') == record['checkpoint_sha256'] == meta['checkpoint_sha256']
        assert meta['seed'] == job['seed'] and meta['training_data_sha256'] == spec['data_sha256']
        assert all(sha(path/'source'/name) == digest for name, digest in meta['source_sha256'].items())
        expected_candidates = {f'rho{rho}_gain{gain}_ridge{ridge}'
            for rho in (.5, .8) for gain in (.08, .25, .6) for ridge in (.001, .1)}
        assert len(meta['candidates']) == 12
        assert {c['name'] for c in meta['candidates']} == expected_candidates
        assert meta['selected'] in meta['candidates']
        assert meta['selected']['checkpoint_sha256'] == meta['checkpoint_sha256']
        checked = []; negative = None
        for candidate in meta['candidates']:
            checkpoint = base/(candidate['name']+'.npz')
            assert checkpoint.parent == base and sha(checkpoint) == candidate['checkpoint_sha256']
            fixed = fixed_arrays(job['seed'], candidate, meta)
            with np.load(checkpoint, allow_pickle=False) as z:
                values = {key: z[key].copy() for key in z.files}
            verify_values(values, fixed, meta, job['family'])
            if negative is None:
                # Disposable in-memory controls. Never write altered weights as
                # candidate files or attach them to any development spec.
                changed = dict(values, w=values['w'].copy())
                changed['w'][0, 0] += .01
                try:
                    verify_values(changed, fixed, meta, job['family'])
                except AssertionError:
                    pass
                else:
                    raise AssertionError('Learned/modified recurrent matrix was not rejected')
                changed = dict(values, hidden_w=np.zeros((128, 424)))
                try:
                    verify_values(changed, fixed, meta, job['family'])
                except AssertionError:
                    pass
                else:
                    raise AssertionError('Undeclared learned layer was not rejected')
                negative = dict(modified_recurrent_rejected=True, undeclared_hidden_layer_rejected=True,
                                writes=0, fitting=0)
            checked.append(dict(name=candidate['name'], checkpoint_sha256=sha(checkpoint),
                exact_fixed_array_names=sorted(fixed)))
        rows.append(dict(name=job['name'], family=job['family'], seed=job['seed'],
            checkpoint_sha256=meta['checkpoint_sha256'], training_metadata_sha256=sha(base/'TRAINING_COMPLETE.json'),
            selected=meta['selected']['name'], readout_coefficients=meta['trainable_readout_coefficients'],
            candidates=checked, negative_controls=negative, fixed_arrays_exact=True,
            validation_selection_not_recomputed=True))
    return dict(path=str(path), execution_sha256=sha(path/'execution.json'),
        specification_sha256=sha(path/'SPECIFICATION.json'), protocol_sha256=spec['protocol_sha256'],
        data_sha256=spec['data_sha256'], rows=rows, excluded_learned_matrix_controls=excluded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--learning', type=Path, nargs='+', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    assert all(os.environ.get(k) == '1' for k in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'))
    cgroup = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cgroup/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    sources = {str(Path(__file__).resolve()): sha(__file__)}
    phases = [audit_learning(path.resolve()) for path in args.learning]
    assert len({p['protocol_sha256'] for p in phases}) == 1
    result = dict(status='complete', completed_utc=datetime.now(timezone.utc).isoformat(),
        command=sys.argv, source_sha256=sources, host=platform.node(), python=sys.executable,
        numpy=np.__version__, memory_max=memory, phases=phases,
        physics_steps=0, inference_steps=0, training_updates=0, candidate_fits=0,
        sealed_condition_contents_read=False,
        limitation='Initialization reconstructed in the fitting NumPy runtime. Exact fixed matrices and declared readout-only checkpoint schema do not prove echo-state contraction, closed-loop safety, generalization, or superior outcomes. Ridge/readout values and offline selection remain those of original immutable training records.')
    assert all(sha(path) == digest for path, digest in sources.items())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output),
        policies=sum(len(p['rows']) for p in phases),
        retained_candidates=sum(len(r['candidates']) for p in phases for r in p['rows']),
        physics_steps=0, training_updates=0)))


if __name__ == '__main__':
    main()
