"""Fail-closed reclaimed-unit checks; never starts a physical episode."""
import argparse
import copy
import subprocess
from pathlib import Path
from unittest.mock import patch

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
import prepare_ball_coverage_reclaimed_20261029 as probe


def check(old_root, new_root, output):
    assert not output.exists()
    old, new = [read(p/'REGISTRATION.json') for p in (old_root, new_root)]
    for key in ('schema', 'maximum_episodes', 'cases', 'teacher_config', 'teacher_sha256',
                'parent_collection_plan_sha256', 'resources', 'interpretation',
                'prerequisite_matrix', 'prerequisite_service', 'prerequisite_pid',
                'prerequisite_start_ticks', 'prerequisite_preparation',
                'prerequisite_preparation_sha256', 'prerequisite_audit'):
        assert old[key] == new[key], key
    old_source = 'tools/prepare_ball_coverage_bounded_20261029.py'
    new_source = 'tools/prepare_ball_coverage_reclaimed_20261029.py'
    assert {k:v for k,v in old['source_sha256'].items() if k != old_source} == {
        k:v for k,v in new['source_sha256'].items() if k != new_source}
    for reg in (old, new):
        for name, digest in reg['source_sha256'].items():
            assert sha(ROOT/name) == digest, name
    absent = dict(LoadState='not-found', ActiveState='inactive', MainPID='0',
                  Result='success', InvocationID='', ControlGroup='',
                  ExecMainCode='0', ExecMainStatus='0')
    retained = dict(absent, LoadState='loaded', InvocationID=new['prerequisite_invocation_id'],
                    ControlGroup=new['prerequisite_cgroup'], ExecMainCode='1')
    positives = []
    for state, ticks, cg in [(retained, None, True), (absent, None, False),
                              (absent, 'different-reused-pid-start', False)]:
        positives.append(probe.require_finished_service(new, state, ticks, new['prerequisite_boot_id'], cg))
    assert positives[0]['service_exit_zero_verified'] is True
    assert all(p['service_exit_zero_verified'] is False for p in positives[1:])
    rejected = []
    cases = [
        ('active', dict(absent, ActiveState='active'), None, False, new['prerequisite_boot_id']),
        ('deactivating', dict(absent, ActiveState='deactivating'), None, False, new['prerequisite_boot_id']),
        ('remaining_pid', dict(absent, MainPID='1'), None, False, new['prerequisite_boot_id']),
        ('old_process_outside_unit', absent, new['prerequisite_start_ticks'], False, new['prerequisite_boot_id']),
        ('remaining_cgroup', absent, None, True, new['prerequisite_boot_id']),
        ('changed_boot', absent, None, False, 'different-boot'),
        ('other_invocation', dict(retained, InvocationID='0'*32), None, True, new['prerequisite_boot_id']),
        ('failed_exit', dict(retained, Result='exit-code', ExecMainStatus='1'), None, True, new['prerequisite_boot_id']),
        ('signal_exit', dict(retained, ExecMainCode='2'), None, True, new['prerequisite_boot_id']),
        ('ambiguous_load', dict(absent, LoadState='error'), None, False, new['prerequisite_boot_id']),
        ('missing_response_fields', {}, None, False, new['prerequisite_boot_id']),
        ('unreclaimed_invocation', dict(absent, InvocationID=new['prerequisite_invocation_id']), None, False, new['prerequisite_boot_id']),
    ]
    for label, state, ticks, cg, boot in cases:
        try:
            probe.require_finished_service(new, state, ticks, boot, cg)
        except (AssertionError, KeyError, ValueError):
            rejected.append(label)
        else:
            raise AssertionError('Unsafe handoff accepted: '+label)
    with patch.object(probe.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, ['systemctl'])):
        try:
            probe.service_state(new['prerequisite_service'])
        except subprocess.CalledProcessError:
            rejected.append('service_query_failed')
        else:
            raise AssertionError('Query failure accepted')
    live = probe.service_state(new['prerequisite_service'])
    assert live['LoadState'] == 'loaded' and live['ActiveState'] == 'active'
    assert live['MainPID'] == str(new['prerequisite_pid'])
    assert live['InvocationID'] == new['prerequisite_invocation_id']
    assert probe.process_identity(new['prerequisite_pid']) == new['prerequisite_start_ticks']
    # The actual registered original108 is still incomplete. Refusal must occur
    # before any new execution or physical subprocess, not through a mock state.
    try:
        probe.run(new_root)
    except AssertionError as error:
        assert str(error) == 'Original108 must finish first'
        rejected.append('real_original108_incomplete')
    else:
        raise AssertionError('Real incomplete original108 permitted')
    assert not (old_root/'execution.json').exists() and not (new_root/'execution.json').exists()
    write(output, dict(status='reclaimed_handoff_checks_passed_no_physics', positives=positives,
        rejected=rejected, original_live_service=live, original_process_identity_verified=True,
        old_registration_sha256=sha(old_root/'REGISTRATION.json'),
        new_registration_sha256=sha(new_root/'REGISTRATION.json'),
        old_bound_sources_unchanged=len(old['source_sha256']), new_bound_source_count=len(new['source_sha256']),
        source_sha256={p.name:sha(p) for p in (Path(__file__), Path(probe.__file__))},
        physical_steps=0, limitation='Synthetic terminal boundary tests and real incomplete-run refusal. '
        'No actual original108 terminal handoff or new eight-control physics yet.'))
    print('passed', len(positives), len(rejected), 'no physics')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old', type=Path, required=True)
    parser.add_argument('--new', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.old.resolve(), args.new.resolve(), args.output.resolve())
