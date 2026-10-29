"""Validate prospective ingestion boundaries, without physics or training.

Mock lineage examples are software checks only, never scientific receipts.
Real v4 registration and original108 bindings are checked separately.
"""
import argparse
import ast
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import collect_special_scene_coverage_20261029 as collector
from prepare_special_frozen_test_20261028 import validate as validate_frozen

ROOT = collector.ROOT


def rejected(call):
    try:
        call()
    except (ValueError, KeyError, FileNotFoundError, TypeError):
        return
    raise AssertionError('Invalid input accepted')


def check(probe, output, successor=None):
    assert not output.exists()
    resources = collector.require_resources()
    if resources['cpu_max'] is None:
        with patch.object(collector.os, 'sched_getaffinity', return_value={1, 2}):
            rejected(collector.require_resources)
    with patch.dict(collector.os.environ, {'OMP_NUM_THREADS': '2'}):
        rejected(collector.require_resources)
    reg = collector.read(probe/'REGISTRATION.json')
    names = ['collect_special_scene_coverage_20261029.py',
             'run_registered_special_coverage_20261029.py',
             'qualify_registered_special_coverage_20261029.py',
             'build_special_coverage_dataset_20261029.py']
    for name in names:
        ast.parse((ROOT/'tools'/name).read_text())
    accepted = []
    for case in reg['cases']:
        entry = dict(id=case['id'], scene='ball', scene_parameters=case['parameters'])
        collector.validate_override(entry)
        accepted.append(case['id'])
    assert len(accepted) == 8
    entry = dict(id='software_check_only', scene='ball',
                 scene_parameters=deepcopy(reg['cases'][0]['parameters']))
    bad_parameters = []
    for key in sorted(collector.COVERAGE_PARAMETERS):
        bad = deepcopy(entry)
        del bad['scene_parameters'][key]
        rejected(lambda: collector.validate_override(bad))
        bad_parameters.append('missing_'+key)
    for key, value in [('VMC_BALL_EVENT_STAGE', 'carry'),
                       ('VMC_COVERAGE_INITIAL_X_M', .09),
                       ('VMC_COVERAGE_INITIAL_Z_M', float('nan')),
                       ('VMC_COVERAGE_CARRY_X_M', .11),
                       ('VMC_COVERAGE_CARRY_Y_M', float('inf')),
                       ('VMC_BALL_ANGLE_RAD', 2), ('UNKNOWN_PARAMETER', 0)]:
        bad = deepcopy(entry)
        bad['scene_parameters'][key] = value
        rejected(lambda: collector.validate_override(bad))
        bad_parameters.append('invalid_'+key)
    for scene in ('rod', 'corner'):
        collector.validate_override(dict(id='software_check_only', scene=scene, scene_parameters={}))

    wrapper_old = (ROOT/'tools/run_video_reference_coverage_20261029.py').read_text()
    wrapper_new = (ROOT/'tools/run_registered_special_coverage_20261029.py').read_text()
    restored = wrapper_new.replace(
        'Registered coverage collection variant; existing wrappers and runs stay unchanged.',
        'Development coverage variant; original wrapper and in-flight runs stay unchanged.')
    restored = restored.replace(
        "    if not os.environ.get('VMC_COLLECTION_PLAN'):\n"
        "        raise ValueError('Formal coverage requires its prospective collection plan')\n", '')
    restored = restored.replace('collect_special_scene_coverage_20261029',
                                'collect_special_scene_actions_20261028')
    assert restored == wrapper_old, 'Unexpected changes to physics/teacher/filter wrapper'
    qualifier_old = (ROOT/'tools/qualify_special_scene_demo_20261028.py').read_text()
    qualifier_new = (ROOT/'tools/qualify_registered_special_coverage_20261029.py').read_text()
    assert qualifier_new.replace('tools/run_registered_special_coverage_20261029.py',
        'tools/run_video_reference_vmc_20261028.py') == qualifier_old
    builder_old = (ROOT/'tools/build_special_scene_dataset_v2_20261028.py').read_text()
    builder_new = (ROOT/'tools/build_special_coverage_dataset_20261029.py').read_text()
    restored = builder_new.replace('Build registered coverage v3 real-special-scene identities (24+6).',
                                  'Build only registered, audited real-special-scene identities (24+6).')
    restored = restored.replace('    from collect_special_scene_coverage_20261029 import validate\n', '')
    restored = restored.replace('plan_path=plan_path.resolve();plan=validate(plan_path)',
                                'plan_path=plan_path.resolve();plan=read(plan_path)')
    restored = restored.replace('sii-three-real-scenes-collection-plan-v3',
                                'sii-three-real-scenes-collection-plan-v2')
    assert restored == builder_old, 'Dataset arrays, qualification or budgets changed'

    # Explicit in-memory synthetic fixtures: never saved as a real REVIEW.
    root = Path('/synthetic-software-check-only')
    ids = ['synthetic_'+str(i) for i in range(8)]
    registration = dict(maximum_episodes=8, cases=[dict(id=i) for i in ids])
    state = dict(status='complete_pending_review', registration_sha256='reg',
                 episodes=[dict(id=i, qualification_sha256='q') for i in ids])
    review = dict(status='complete_physical_coverage_review', registration_sha256='reg',
                  execution_sha256='execution', reviewer_sha256='reviewer',
                  created_utc='2026-10-29T00:00:00+00:00',
                  rows=[dict(id=i, qualification_sha256='q') for i in ids])
    plan = dict(coverage_probe_review=str(root/'REVIEW.json'), coverage_probe_review_sha256='review',
                registered_utc='2026-10-29T00:01:00+00:00')

    def exercise(p, r, s, registration_value):
        values = {'REVIEW.json': r, 'execution.json': s, 'REGISTRATION.json': registration_value}
        hashes = {'REVIEW.json': 'review', 'execution.json': 'execution',
                  'REGISTRATION.json': 'reg', 'DEMONSTRATION_QUALIFICATION.json': 'q',
                  'review_ball_coverage_probe_20261029.py': 'reviewer'}
        with patch.object(collector, 'read', side_effect=lambda path: values[path.name]), \
             patch.object(collector, 'sha', side_effect=lambda path: hashes[path.name]):
            return collector.require_complete_probe_review(p)

    assert exercise(plan, review, state, registration) == review
    negative_lineage = []
    variants = [('plan', 'coverage_probe_review', 'relative/REVIEW.json'),
                ('plan', 'coverage_probe_review_sha256', 'changed'),
                ('plan', 'registered_utc', '2026-10-29T00:00:00+00:00'),
                ('review', 'status', 'partial'), ('state', 'status', 'running'),
                ('review', 'registration_sha256', 'changed'),
                ('state', 'registration_sha256', 'changed'),
                ('review', 'execution_sha256', 'changed'),
                ('review', 'reviewer_sha256', 'changed'),
                ('review', 'rows', review['rows'][:-1]),
                ('review', 'rows', [review['rows'][0]]*8),
                ('state', 'episodes', list(reversed(state['episodes']))),
                ('state', 'episodes', [dict(id=i, qualification_sha256='changed') for i in ids]),
                ('registration', 'cases', registration['cases']+[dict(id=ids[0])])]
    for owner, key, value in variants:
        fixtures = dict(plan=deepcopy(plan), review=deepcopy(review), state=deepcopy(state),
                        registration=deepcopy(registration))
        fixtures[owner][key] = value
        rejected(lambda: exercise(fixtures['plan'], fixtures['review'], fixtures['state'],
                                  fixtures['registration']))
        negative_lineage.append(owner+'.'+key)

    # Real missing review refuses before source validation, output, or dispatch.
    assert not (probe/'REVIEW.json').exists() and not (probe/'execution.json').exists()
    rejected(lambda: collector.require_complete_probe_review(dict(
        coverage_probe_review=str(probe/'REVIEW.json'), coverage_probe_review_sha256='not_available')))
    for name, digest in reg['source_sha256'].items():
        assert collector.sha(ROOT/name) == digest, name
    validate_frozen(ROOT/'outputs/special_scene_frozen108_preparation_20261029_v8')
    successor_checks = None
    if successor is not None:
        new = collector.read(successor/'REGISTRATION.json')
        assert new['schema'] == 'sii-ball-coverage-development-eight-v3'
        for key in ('cases', 'maximum_episodes', 'teacher_config', 'teacher_sha256',
                    'parent_collection_plan_sha256', 'prerequisite_matrix', 'prerequisite_service',
                    'prerequisite_pid', 'prerequisite_start_ticks', 'prerequisite_preparation',
                    'prerequisite_preparation_sha256', 'prerequisite_audit', 'interpretation'):
            assert new[key] == reg[key], key
        for name, digest in new['source_sha256'].items():
            assert collector.sha(ROOT/name) == digest, name
        old_names, new_names = set(reg['source_sha256']), set(new['source_sha256'])
        assert old_names-new_names == {'tools/prepare_ball_coverage_probe_20261029.py'}
        assert new_names-old_names == {'tools/prepare_ball_coverage_bounded_20261029.py',
                                      'tools/collect_special_scene_coverage_20261029.py'}
        assert all(reg['source_sha256'][k] == new['source_sha256'][k] for k in old_names & new_names)
        refused = subprocess.run([sys.executable, str(ROOT/'tools/prepare_ball_coverage_bounded_20261029.py'),
                                  '--root', str(successor), '--run'], capture_output=True, text=True)
        assert refused.returncode != 0 and 'Original108 must finish first' in refused.stderr
        assert not (successor/'execution.json').exists()
        successor_checks = dict(registration_sha256=collector.sha(successor/'REGISTRATION.json'),
            cases_teacher_and_prerequisite_identity_exact=True, source_count=len(new_names),
            original_sources_unchanged=True, actual_inflight_refusal=refused.stderr,
            physical_steps=0)
    result = dict(status='ingestion_software_checks_passed_physical_validation_pending',
        created_utc=datetime.now(timezone.utc).isoformat(), checker_sha256=collector.sha(Path(__file__)),
        sources={name:collector.sha(ROOT/'tools'/name) for name in names},
        resources=resources, actual_resource_check_passed=True, accepted_registered_ball_overrides=accepted,
        rejected_parameters=bad_parameters, wrapper_inverse_exact=True, qualification_inverse_exact=True,
        dataset_arrays_and_budgets_inverse_exact=True, synthetic_positive_lineage_checks=1,
        synthetic_negative_lineage_checks=negative_lineage, actual_missing_review_rejected=True,
        probe_registration_sha256=collector.sha(probe/'REGISTRATION.json'),
        successor=successor_checks, non_single_thread_rejected=True,
        unbounded_affinity_rejected_when_cpu_controller_absent=resources['cpu_max'] is None,
        unchanged_probe_sources=len(reg['source_sha256']), original108_bindings_unchanged=True,
        physical_steps=0, formal_plan_created=False, fitting_runs=0,
        limitation='Software boundary checks only. In-memory synthetic lineage is not physical evidence. '
                   'Eight real controls, formal30, fair retraining and regression remain pending.')
    collector.write(output, result)
    print(result['status'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--successor', type=Path)
    args = parser.parse_args()
    check(args.probe.resolve(), args.output.resolve(), args.successor.resolve() if args.successor else None)
