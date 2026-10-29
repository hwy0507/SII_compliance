"""Small synthetic boundary checks plus real previously audited episodes."""
import argparse
from copy import deepcopy
from pathlib import Path
import tempfile

import numpy as np

import audit_special_condition_streaming_20261029 as streaming
from collect_special_scene_actions_20261028 import read, sha, write


def check(previous, output):
    assert not output.exists()
    resources = streaming.require_resources()
    rng = np.random.default_rng(2026102904)
    n = 10001
    metrics = dict(dt=np.full(n, .00005), qfrc_actuator=rng.normal(0, 10, (n, 7)).astype('f4'),
                   error=rng.normal(0, .1, (n, 3)).astype('f4'), twist=rng.normal(0, .1, (n, 6)).astype('f4'))
    research = dict(contact_force_sum=rng.uniform(0, .1, (n, 6)).astype('f4'),
                    external_penetration_m=rng.uniform(0, .0003, n), edge_penetration_m=np.zeros(n))
    dt, torque, error, twist = [metrics[k].astype(float) for k in ('dt', 'qfrc_actuator', 'error', 'twist')]
    torque = abs(torque); force = research['contact_force_sum'][:, 2].astype(float)
    contact = force > .05; within = np.all(torque <= np.array([43.5]*4+[6.]*3)*(1+1e-6), axis=1)
    expected = dict(substeps=n, duration=float(dt.sum()), contact=float(dt[contact].sum()),
        comfort=float(dt[contact & within].sum()/dt[contact].sum()),
        rmse=float(1000*np.sqrt(np.sum(np.sum(error**2, axis=1)*dt)/dt.sum())),
        impulse=float(np.sum(force[contact]*dt[contact])), exceed=float(dt[contact & ~within].sum()),
        torque=float(torque.max()), penetration=float((1000*np.maximum(research['external_penetration_m'], research['edge_penetration_m'])).max()),
        speed=float(np.linalg.norm(twist[:, :3], axis=1).max()), force=float(force.max()),
        ratio=float((torque/np.array([87.]*4+[12.]*3)).max()))
    rejected = []
    with tempfile.TemporaryDirectory(prefix='sii-streaming-software-check-') as temp:
        root = Path(temp); (root/'rollout_metrics').mkdir()
        def save(m, r):
            np.savez_compressed(root/'rollout_metrics/substep_metrics.npz', **m)
            np.savez_compressed(root/'research_substeps.npz', **r)
        save(metrics, research)
        for chunk in (257, 4096, 12000):
            actual = streaming.arithmetic(root, chunk)
            for key in expected:
                streaming.original.equal(actual[key], expected[key], 'Synthetic arithmetic: '+key)
        for label in ('nan', 'wrong_dt', 'unaligned', 'wrong_shape', 'truncated'):
            m, r = deepcopy(metrics), deepcopy(research)
            if label == 'nan': m['error'][7000, 0] = np.nan
            elif label == 'wrong_dt': m['dt'][7000] = .0001
            elif label == 'unaligned': r['edge_penetration_m'] = r['edge_penetration_m'][:-1]
            elif label == 'wrong_shape': m['twist'] = m['twist'][:, :3]
            save(m, r)
            if label == 'truncated':
                with (root/'research_substeps.npz').open('r+b') as stream:
                    stream.truncate(200)
            try: streaming.arithmetic(root)
            except (ValueError, streaming.zipfile.BadZipFile): rejected.append(label)
            else: raise AssertionError(label+' accepted')
    assert sha(previous) == 'aa1ead018cbbc25384a6804a51bb291a5cd32b007a01dc6cd2dee1231ba6e4d2'
    old = read(previous); preparation = Path(old['preparation']); plan = read(preparation/'REGISTRATION.json')
    root = Path(plan['evaluation']); parent_root = Path(plan['source_run'])
    models = {m['name']: m for m in read(root/'INPUT_MODEL_LOCK.json')['models']}
    conditions = {c['id']: c for c in read(parent_root/'CONDITIONS.json')['conditions']}
    parent = read(parent_root/'REGISTRATION.json')
    parent['formal_model_sha256'] = read(parent_root/'PROTOCOL.json')['formal_model_sha256']
    verify = streaming.verifier(); verified = set(); results = []
    for index in (0, 2, 4, 6):
        row, expected = old['rows'][index], old['checks'][index]
        actual = verify(row, models[row['method']], conditions[row['condition']], root, root/'source', parent, verified)
        errors = {}
        for key, value in actual.items():
            if isinstance(value, (int, float)):
                streaming.original.equal(value, expected[key], 'Original audit equivalence: '+key)
                errors[key] = abs(value-expected[key])
            else: assert value == expected[key], key
        results.append(dict(method=row['method'], max_abs_errors=errors))
    write(output, dict(status='streaming_checks_passed', resources=resources,
        memory_peak_bytes=int((Path(resources['cgroup'])/'memory.peak').read_text()),
        checker_sha256=sha(Path(__file__)), streaming_auditor_sha256=sha(Path(streaming.__file__)),
        original_auditor_sha256=streaming.ORIGINAL_SHA, previous_audit_sha256=sha(previous),
        synthetic_rows=n, synthetic_chunk_sizes=[257, 4096, 12000], synthetic_rejected=rejected,
        real_original_audit_comparisons=results, physical_steps=0,
        limitation='Synthetic fixtures only test software; real comparisons use four previously audited original episodes including abort, no contact, zero comfort and full comfort. No new dynamics or training.'))
    print('streaming_checks_passed', len(results), 'real episodes')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.previous.resolve(), args.output.resolve())
