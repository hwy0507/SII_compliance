"""Finite original-v6 damping control, retaining its static readout gain.

Normalization reduced both transient and steady compliance and failed office.
Test one translational damping change instead; no new recovery mechanism,
no scene-specific switching, and no validation/test imitation labels.
"""
import argparse
import copy
from pathlib import Path
import shutil

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run
from intent_recovery_teacher_20261029 import make_teacher
from review_special_teacher_midpoint_20261028 import inactive


def checks(original, candidate):
    old, new = make_teacher(original), make_teacher(candidate)
    poles = []
    h = .04/20
    for actor in (old, new):
        row = []
        for mass, damping, stiffness in zip(actor.mass, actor.b, actor.k):
            # Exact local Jacobian of the implemented semi-implicit update.
            matrix = np.array([[1-h*h*stiffness/mass, h*(1-h*damping/mass)],
                               [-h*stiffness/mass, 1-h*damping/mass]])
            radius = float(np.abs(np.linalg.eigvals(matrix)).max())
            assert radius < 1
            row.append(radius)
        poles.append(row)
    rng = np.random.default_rng(2026102906)
    maximum = 0.
    for _ in range(400):
        obs = rng.normal(0, .004, 48)
        obs[45:48] = [1, 0, 0]
        obs[14] = .02
        obs[39:45] = rng.normal(0, 1, 6)
        wrench = obs[39:45]
        effective = (wrench+new.previous_wrench)*.5
        filtered = new.filtered+(1-np.exp(-.04/new.filter_tau))*(effective-new.filtered)
        force = new.R6.T@filtered
        force = np.sign(force)*np.maximum(np.abs(force)-new.deadband, 0)
        force = new.sigma*np.tanh(force/new.sigma)
        position, velocity = new.offset.copy(), new.velocity.copy()
        for _ in range(20):
            acceleration = (force-new.b*velocity-new.sigma*np.tanh(new.k*position/new.sigma))/new.mass
            velocity = np.clip(velocity+acceleration*h, -new.vmax, new.vmax)
            position = np.clip(position+velocity*h, -new.xmax, new.xmax)
        new.observe(obs)
        new.act(wrench)
        np.testing.assert_array_equal(new.filtered, filtered)
        for actual, expected in ((new.offset, position), (new.velocity, velocity)):
            maximum = max(maximum, float(np.max(np.abs(actual-expected))))
            np.testing.assert_allclose(actual, expected, rtol=0, atol=1e-15)
    # A constant small wrench checks unchanged nonlinear static compliance.
    # No commanded horizontal direction => recovery is inactive in this check.
    old.reset(); new.reset()
    steady = []
    for actor in (old, new):
        for _ in range(1000):
            action = actor.act(np.array([1., -1., 1., .1, -.1, .1]))
        steady.append(action)
    np.testing.assert_allclose(steady[0], steady[1], rtol=0, atol=1e-12)
    return dict(status='passed', independent_integration_steps=400*20,
                independent_state_max_abs=maximum, local_substep_spectral_radii=poles,
                static_action_max_abs=float(np.max(np.abs(steady[0]-steady[1]))),
                original_static_action=steady[0].tolist(), candidate_static_action=steady[1].tolist(),
                interpretation='Both isolated virtual linearizations are stable. This excludes that local integration defect, not coupled robot/contact instability. Damping preserves the static mapping and changes transients; no closed-loop success guarantee.')


def prepare(root):
    assert not root.exists()
    parent = ROOT/'outputs/special_teacher_legacy_units_20261029_v1'
    reg, state, review = [read(parent/n) for n in ('REGISTRATION.json', 'execution.json', 'REVIEW.json')]
    inactive(reg['service'])
    assert state['status'] == 'complete_pending_review' and len(state['episodes']) == 6
    assert review['execution_sha256'] == sha(parent/'execution.json')
    assert not review['all_six_qualified'] and not review['rows'][-1]['task']
    original_path = Path(reg['reference_v6_config'])
    assert sha(original_path) == reg['reference_v6_config_sha256']
    original = read(original_path)
    assert original['velocity_weight'] == 1 and original['pair_average'] is True
    assert 'options' not in original and 'teacher_mechanism' not in original
    candidate = copy.deepcopy(original)
    candidate['options'] = dict(damping_6d=[56., 56., 110., 2.8, 2.4, 3.])
    actor_check = checks(original, candidate)
    visual = ROOT/'outputs/special_teacher_legacy_edge_states_20261029_v1/REVIEW.json'
    assert read(visual)['status'] == 'complete'
    root.mkdir(parents=True)
    write(root/'ACTOR_CHECKS.json', actor_check)
    teacher = root/'teacher_damping.json'
    write(teacher, candidate)
    source = root/'source'
    shutil.copytree(parent/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    source_copy = {str(p.relative_to(parent/'source')): sha(p) for p in (parent/'source').rglob('*')
                   if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
    assert all(sha(source/n) == digest for n, digest in source_copy.items())
    write(root/'SOURCE_COPY_REVIEW.json', dict(parent=str(parent/'source'), files=source_copy, all_identical=True))
    cases = copy.deepcopy(reg['cases'])
    for case in cases:
        case.update(config=str(teacher), id='damping_'+case.get('identity', 'office000'))
        if case['kind'] == 'office':
            case['command'][1] = str(source/'tools/legacy_teacher_office_driver_20261029.py')
    successor = copy.deepcopy(reg)
    successor.update(schema='sii-teacher-original-static-gain-damping-control-v1', registered_utc=now(),
        service='sii-special-teacher-damping-v1-20261029.service', cases=cases,
        config_sha256={str(teacher):sha(teacher)}, parent_review_sha256=sha(parent/'REVIEW.json'),
        parent_execution_sha256=sha(parent/'execution.json'), interpretation=__doc__,
        changed_parameter=dict(relative_to='original v6 config', name='options.damping_6d',
            before=[28.,28.,55.,2.8,2.4,3.], after=candidate['options']['damping_6d']),
        changes_from_immediate_parent=['Restore original teacher readout normalization', 'Double translational virtual damping'],
        actor_checks_sha256=sha(root/'ACTOR_CHECKS.json'),
        source_copy_review_sha256=sha(root/'SOURCE_COPY_REVIEW.json'), diagnosis_sha256=sha(visual),
        selection_rule='One damping candidate fixed before physics. Original five train identities plus inspected office000, all six original qualifications required before any new30. No sweep or automatic fitting. Office is development regression, never imitation labels.')
    successor['source_sha256'] = {n:sha(ROOT/n) for n in reg['source_sha256'] if not n.startswith('outputs/')}
    successor['source_sha256']['tools/'+Path(__file__).name] = sha(Path(__file__))
    successor['source_sha256'].update({str(p.relative_to(ROOT)):sha(p) for p in source.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'})
    write(root/'REGISTRATION.json', successor)
    print(root, sha(root/'REGISTRATION.json'), actor_check)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    (run if args.run else prepare)(args.root.resolve())
