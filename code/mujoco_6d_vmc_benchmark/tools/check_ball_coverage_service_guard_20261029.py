"""Check fail-closed service handoff without launching physical work."""
import argparse
from pathlib import Path
import subprocess
from unittest.mock import patch

from collect_special_scene_actions_20261028 import read, sha, write
import prepare_ball_coverage_probe_20261029 as probe


def check(old_root, new_root, output):
    assert not output.exists()
    old, new = [read(p/'REGISTRATION.json') for p in (old_root, new_root)]
    assert new['schema'] == 'sii-ball-coverage-development-eight-v2'
    for key in ('cases', 'maximum_episodes', 'teacher_config', 'teacher_sha256',
                'parent_collection_plan_sha256', 'resources', 'prerequisite_matrix',
                'prerequisite_service', 'prerequisite_audit', 'interpretation'):
        assert old[key] == new[key], key
    changed = [k for k,v in old['source_sha256'].items() if new['source_sha256'][k] != v]
    assert set(old['source_sha256']) == set(new['source_sha256'])
    assert changed == ['tools/prepare_ball_coverage_probe_20261029.py']
    current = dict(LoadState='loaded', ActiveState='inactive', Result='success', MainPID='0')
    positives = []
    for ticks in (None, 'different-reused-pid-start'):
        probe.require_finished_service(new, current, ticks)
        positives.append(ticks)
    failures = []
    cases = [('active', dict(ActiveState='active')),
             ('deactivating', dict(ActiveState='deactivating')),
             ('failed', dict(ActiveState='failed', Result='exit-code')),
             ('unsuccessful_inactive', dict(Result='exit-code')),
             ('missing_unit', dict(LoadState='not-found')),
             ('nonzero_pid', dict(MainPID=str(new['prerequisite_pid'])))]
    for label, delta in cases:
        try:
            probe.require_finished_service(new, dict(current, **delta), None)
        except AssertionError:
            failures.append(label)
        else:
            raise AssertionError(label)
    try:
        probe.require_finished_service(new, current, new['prerequisite_start_ticks'])
    except AssertionError:
        failures.append('original_process_outside_service')
    else:
        raise AssertionError('Original process must be absent')
    # A DBus/systemctl failure must propagate, never look like inactivity.
    with patch.object(probe.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, ['systemctl'])):
        try:
            probe.service_state(new['prerequisite_service'])
        except subprocess.CalledProcessError:
            failures.append('service_query_error')
        else:
            raise AssertionError('Service query failure accepted')
    with patch.object(probe.subprocess, 'check_output', return_value='ActiveState=inactive\n'):
        try:
            probe.require_finished_service(new, probe.service_state(new['prerequisite_service']), None)
        except KeyError:
            failures.append('incomplete_service_response')
        else:
            raise AssertionError('Missing service fields accepted')
    assert not (old_root/'execution.json').exists() and not (new_root/'execution.json').exists()
    write(output, dict(status='service_boundary_checks_passed_no_physics',
        positive_terminal_identities=positives, rejected=failures,
        unchanged_cases_and_teacher=True, changed_source=changed,
        old_registration_sha256=sha(old_root/'REGISTRATION.json'),
        new_registration_sha256=sha(new_root/'REGISTRATION.json'),
        checker_sha256=sha(Path(__file__)), launcher_sha256=sha(Path(probe.__file__)),
        physical_steps=0,
        limitation='Pure service-boundary checks and exact preparation comparison. '
                    'Real original108 is still running; complete positive dispatch has not occurred.'))
    print('service_boundary_checks_passed_no_physics', len(positives), len(failures))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.old.resolve(), args.new.resolve(), args.output.resolve())
