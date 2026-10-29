"""Zero-physics lifecycle controls for the finite final108 handoff."""
import argparse
from pathlib import Path
import tempfile
from unittest.mock import patch
import handoff_contact_yield_final108_20261030 as runner


def check():
    ready = dict(status='fixed27_verified_pending_final_registration')
    for active in ('active', 'activating', 'deactivating', 'reloading'):
        assert runner.decision(ready, active) == 'wait'
    assert runner.decision(ready, 'inactive') == 'ready'
    assert runner.decision(ready, 'failed') != 'ready'
    statuses = ('fixed27_scientific_failures_preserved_require_repair',
                'failed_preserved_no_retry', 'waiting_for_audited_fits')
    for status in statuses:
        assert runner.decision(dict(status=status), 'inactive') != 'ready'
    checks = []
    for mode in ('success', 'scientific_failure', 'stop', 'timeout',
                 'register_error', 'run_error', 'review_error'):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            parent, target, root = (base/n for n in ('parent', 'target', 'handoff'))
            parent.mkdir(); root.mkdir()
            runner.write(parent/'REGISTRATION.json', {'synthetic': True})
            runner.write(parent/'execution.json', ready if mode != 'scientific_failure'
                         else dict(status=statuses[0]))
            runner.write(root/'REGISTRATION.json', dict(
                parent=str(parent), parent_unit=runner.UNIT, target=str(target),
                parent_registration_sha256=runner.sha(parent/'REGISTRATION.json'),
                source_sha256={}, maximum_wait_seconds=86400))
            if mode == 'stop':
                (root/'STOP_REQUESTED').touch()
            calls = []

            def command(args, **kwargs):
                phase = args[2]; calls.append(phase)
                if mode == phase+'_error':
                    raise RuntimeError('synthetic '+phase+' failure')
                if phase == 'register':
                    target.mkdir()
                if phase == 'review':
                    runner.write(target/'FINAL_REVIEW.json', dict(
                        status='verified_complete_isolated_unseen_matrix',
                        rows=[{}]*108, independent_replays=[{}]*108))

            active = 'active' if mode == 'timeout' else 'inactive'
            with patch.object(runner, 'PARENT', parent), patch.object(runner, 'TARGET', target), \
                 patch.object(runner, 'check_resources'), \
                 patch.object(runner, 'properties', return_value={'ActiveState': active}), \
                 patch.object(runner.subprocess, 'run', side_effect=command), \
                 patch.object(runner.time, 'monotonic', side_effect=[0, 100000]):
                try:
                    runner.run(root)
                except RuntimeError:
                    assert mode.endswith('_error')
                else:
                    assert not mode.endswith('_error')
            state = runner.read(root/'execution.json')
            if mode == 'success':
                assert calls == ['register', 'run', 'review']
                assert state['status'] == 'final108_verified_pending_delivery'
            elif mode.endswith('_error'):
                phase = mode.removesuffix('_error')
                assert calls == ['register', 'run', 'review'][:['register', 'run', 'review'].index(phase)+1]
                assert state['status'] == 'failed_preserved_no_retry'
            else:
                assert calls == [] and not state['dispatch_attempted'] and not target.exists()
            before = (root/'execution.json').read_bytes()
            with patch.object(runner, 'check_resources'):
                try:
                    runner.run(root)
                except AssertionError:
                    pass
                else:
                    raise AssertionError('duplicate run accepted')
            assert (root/'execution.json').read_bytes() == before
            checks.append(dict(case=mode, calls=calls, status=state['status']))
    return dict(status='passed_zero_physics_final108_handoff_controls',
                coordinator_sha256=runner.sha(Path(runner.__file__)),
                checker_sha256=runner.sha(Path(__file__)), cases=checks,
                no_final_conditions_read=True, physics_episodes=0,
                scope='Synthetic lifecycle and failure preservation only; no real final registration or results.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    runner.write(args.output, check())
    print('final108 finite handoff lifecycle controls passed; zero physics')
