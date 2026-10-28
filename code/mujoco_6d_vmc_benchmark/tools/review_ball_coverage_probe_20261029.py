"""Review all eight physical controls, including failed qualifications.

Checks measured canonical path directions and reached task targets, not merely
the requested environment variables. No fitting, dynamics, model selection or
change to the original qualification gates. A complete review can report a
failed repair; it is never a student or frozen-test success certificate.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import read, sha, write


def coverage(observation, time, stage, target, approach, carry):
    n = len(time)
    assert observation.shape == (n, 48) and target.shape == (n, 3)
    assert stage.shape == time.shape == (n,) and n > 0
    assert all(np.isfinite(a).all() for a in (observation, time, stage, target))
    np.testing.assert_allclose(time, .04 * np.arange(1, n + 1), rtol=0, atol=1e-8)
    assert np.all(stage == stage.astype(int)) and np.all(np.diff(stage) >= 0)
    assert np.all((stage >= 0) & (stage <= 5))
    assert np.asarray(approach).shape == np.asarray(carry).shape == (3,)
    assert np.linalg.norm(approach) > 0 and np.linalg.norm(carry) > 0
    directions = {0: approach / np.linalg.norm(approach),
                  4: carry / np.linalg.norm(carry),
                  5: -carry / np.linalg.norm(carry)}
    phases = []
    for s, expected in directions.items():
        mask = stage == s
        error = float(np.max(np.abs(observation[mask, 45:48] - expected))) if mask.any() else None
        phases.append(dict(stage=s, frames=int(mask.sum()), expected_direction=expected.tolist(),
                           max_direction_error=error,
                           reached_and_direction_matches=error is not None and error <= 1e-10))
    displacement = None
    if np.any(stage == 3) and np.any(stage == 4):
        displacement = target[stage == 4][0] - target[stage == 3][0]
    carry_matches = displacement is not None and np.allclose(displacement, carry, rtol=0, atol=1e-10)
    # Descriptive estimated-load threshold; not physical contact or a new gate.
    load = np.max(np.abs(observation[:, 39:45] / np.array([8., 8., 8., 1., 1., 1.])), axis=1)
    zero_load = load <= 1e-6
    return dict(phases=phases,
                actual_carry_displacement_m=None if displacement is None else displacement.tolist(),
                carry_displacement_matches=bool(carry_matches),
                physical_direction_coverage=all(p['reached_and_direction_matches'] for p in phases) and bool(carry_matches),
                estimated_zero_load_context_frames=int(np.sum(zero_load & (np.linalg.norm(observation[:, 45:48], axis=1) > .5))),
                estimated_zero_load_threshold=1e-6,
                path_min=observation[:, 45:48].min(0).tolist(),
                path_max=observation[:, 45:48].max(0).tolist())


def review(root, output):
    assert not output.exists(), 'Preserve previous review'
    reg = read(root / 'REGISTRATION.json')
    # Refuse unstarted/partial runs before creating any output.
    state = read(root / 'execution.json')
    assert state['status'] == 'complete_pending_review', 'All eight controls must terminate first'
    assert state['registration_sha256'] == sha(root / 'REGISTRATION.json')
    assert len(reg['cases']) == len(state['episodes']) == reg['maximum_episodes'] == 8
    assert len({c['id'] for c in reg['cases']}) == 8
    rows = []
    for case, receipt in zip(reg['cases'], state['episodes']):
        assert case['id'] == receipt['id'] and case['split'] == 'development_control'
        folder = root / case['id'] / 'ball'
        q = read(folder / 'DEMONSTRATION_QUALIFICATION.json')
        assert q == receipt['qualification']
        assert sha(folder / 'DEMONSTRATION_QUALIFICATION.json') == receipt['qualification_sha256']
        for name, digest in q['input_hashes'].items():
            assert sha(folder / name) == digest, name
        ex = read(folder / 'execution.json')
        assert ex['status'] == 'complete' and ex['controller_role'] == 'teacher'
        assert ex['teacher_config_sha256'] == reg['teacher_sha256']
        assert ex['physics_dt_s'] == .00005 and ex['actor_input'].startswith('canonical48')
        assert ex['actor_replay_max_abs'] == ex['filter_replay_max_abs'] == 0
        for key, value in case['parameters'].items():
            assert ex['experiment_environment'][key] == str(value), key
        assert ex['experiment_environment']['VMC_SCENE_SEED'] == str(case['seed'])
        for name, digest in read(folder / 'SOURCE_HASHES.json').items():
            assert reg['source_sha256'][name] == digest, name
        with np.load(folder / 'trajectory.npz', allow_pickle=False) as z:
            obs, time = z['observation'].copy(), z['time'].copy()
        with np.load(folder / 'legacy.npz', allow_pickle=False) as z:
            np.testing.assert_array_equal(z['time'], time)
            stage, target = z['stage'].copy(), z['target'].copy()
        params = case['parameters']
        initial = np.array([params['VMC_COVERAGE_INITIAL_' + axis + '_M'] for axis in 'XYZ'])
        carry = np.array([params['VMC_COVERAGE_CARRY_X_M'], params['VMC_COVERAGE_CARRY_Y_M'], 0.])
        # Original first goal minus original initial hand = (0,0,-.06)m.
        actual = coverage(obs, time, stage, target, np.array([0., 0., -.06]) - initial, carry)
        rows.append(dict(id=case['id'], qualification_status=q['status'],
                         task_success=q['task_success'], safety_valid=q['safety_valid'],
                         scene_contact_valid=q['scene_contact_valid'], coverage=actual,
                         qualification_sha256=receipt['qualification_sha256'],
                         legacy_trace_sha256=sha(folder / 'legacy.npz'),
                         metrics=q['metrics']))
    result = dict(status='complete_physical_coverage_review', created_utc=datetime.now(timezone.utc).isoformat(),
                  registration_sha256=sha(root / 'REGISTRATION.json'), execution_sha256=sha(root / 'execution.json'),
                  reviewer_sha256=sha(Path(__file__)), rows=rows,
                  qualified_episodes=sum(r['qualification_status'] == 'qualified' for r in rows),
                  qualified_with_actual_coverage=sum(r['qualification_status'] == 'qualified' and
                      r['coverage']['physical_direction_coverage'] for r in rows),
                  limitation='Development-only actual free-ball controls; all eight including failures retained. '
                  'Estimated zero-load counts are descriptive, not real-contact labels. No student fitting, '
                  'test success, three-scene dataset approval or proof that direction coverage fixes learning.')
    write(output, result)
    print(result['status'], result['qualified_with_actual_coverage'], '/8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    review(args.root.resolve(), args.output.resolve())
