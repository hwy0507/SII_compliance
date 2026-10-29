"""Finite single-owner handoff from full development selection to unseen108.

No fallback on null, no duplicate run, no test-directed model revision.
Waiting is not physics; only registered final runner can dispatch after review.
"""
import argparse
import fcntl
from pathlib import Path
import time

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now
import run_v9_unseen_matrix_20261030 as final

SOURCE_NAMES = ('continue_v9_unseen_after_selection_20261030.py',
    'run_v9_unseen_matrix_20261030.py','review_v9_full_grid_eligibility_20261030.py',
    'audit_special_scene_metrics_v2_20261030.py','audit_special_scene_metrics_20261030.py',
    'special_scene_metrics_20261030.py','audit_special_terminal_trace_20261029.py')


def decision(state, active):
    if state is None:
        return 'wait'
    status=state['status']
    if status=='failed_preserved':
        return 'infrastructure_failed_no_dispatch'
    if status in ('selection_complete_pending_independent_audit','eligibility_exhausted_preserved'):
        if active=='active' or active=='deactivating':
            return 'wait'
        if active!='inactive':
            return 'service_not_inactive_no_dispatch'
        if status=='eligibility_exhausted_preserved' or len(state['selected_models'])!=9:
            return 'null_selection_requires_development_repair'
        return 'ready_for_independent_review_and_registration'
    return 'wait'


def wait_and_run(root,target,maximum_wait_s):
    final.check_resources()
    assert 0 < maximum_wait_s <= 21600
    assert root.parent==target.parent==ROOT/'outputs' and root!=target
    assert not root.exists() and not target.exists(), 'Never duplicate or overwrite a handoff/test'
    root.mkdir()
    with (ROOT/'outputs/.v9-unseen-handoff.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        pending={str((ROOT/'tools'/n).relative_to(ROOT)):sha(ROOT/'tools'/n) for n in SOURCE_NAMES}
        state=dict(status='waiting_for_complete_full_grid_selection',started_utc=now(),
            selection=str(final.SELECTION),selection_unit=final.UNITS[-1],target=str(target),
            maximum_wait_s=maximum_wait_s,pending_source_sha256=pending,
            conditions_sha256=final.CONDITIONS_SHA,dispatch_attempted=False)
        write(root/'HANDOFF.json',state)
        try:
            deadline=time.monotonic()+maximum_wait_s
            while time.monotonic()<deadline:
                assert all(sha(ROOT/n)==h for n,h in pending.items()), 'Pending execution source changed'
                assert sha(final.CONDITIONS)==final.CONDITIONS_SHA
                p=final.SELECTION/'execution.json'
                selection=read(p) if p.exists() else None
                active=final.properties(final.UNITS[-1])['ActiveState']
                choice=decision(selection,active)
                if choice=='ready_for_independent_review_and_registration':
                    break
                if choice!='wait':
                    state.update(status=choice,ended_utc=now())
                    return
                # A failed waiting parent with no execution must not look like
                # an indefinitely pending healthy selection.
                handoff=final.SELECTION/'HANDOFF.json'
                if handoff.exists() and read(handoff)['status']=='failed_preserved':
                    raise RuntimeError('Selection handoff failed before final model lock')
                if active=='failed':
                    raise RuntimeError('Selection service failed; inspect preserved evidence')
                time.sleep(20)
            else:
                raise TimeoutError('Finite final handoff wait expired; no dispatch')
            # register reruns the complete independent review if absent and
            # verifies all nine model identities, frozen conditions and sources.
            assert all(sha(ROOT/n)==h for n,h in pending.items())
            final.register(target)
            state.update(status='registered_unseen_test',registered_utc=now(),
                registration_sha256=sha(target/'REGISTRATION.json'))
            write(root/'HANDOFF.json',state)
            state.update(status='running_registered_unseen_test',dispatch_attempted=True)
            write(root/'HANDOFF.json',state)
            final.run(target)
            state.update(status='reviewing_complete_unseen_test')
            write(root/'HANDOFF.json',state)
            final.review(target,target/'FINAL_REVIEW.json')
            state.update(status='complete_unseen_test_independently_reviewed_pending_delivery',
                final_review_sha256=sha(target/'FINAL_REVIEW.json'),ended_utc=now())
        except BaseException as exc:
            state.update(status='failed_preserved',error=repr(exc),ended_utc=now())
            raise
        finally:
            write(root/'HANDOFF.json',state)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True)
    p.add_argument('--maximum-wait-s',type=int,default=21600)
    a=p.parse_args();wait_and_run(a.root.resolve(),a.target.resolve(),a.maximum_wait_s)
