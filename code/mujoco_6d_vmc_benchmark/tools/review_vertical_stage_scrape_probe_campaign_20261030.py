"""Independent summary verification for the registered scrape repair probes."""
import json
from pathlib import Path

from collect_special_scene_actions_20261028 import sha


def review(root):
    root = Path(root).resolve(); reg = json.loads((root / 'REGISTRATION.json').read_text())
    state = json.loads((root / 'execution.json').read_text())
    assert sha(root / 'REGISTRATION.json') == state['registration_sha256']
    assert state['status'] in ('three_probes_qualified_pending_independent_review', 'complete_with_failures_preserved_no_collection')
    assert len(reg['cases']) == len(state['rows']) == 3
    assert [x['id'] for x in reg['cases']] == ['rod_09', 'rod_04', 'rod_01']
    assert [x['id'] for x in state['rows']] == [x['id'] for x in reg['cases']]
    for name, digest in reg['source_sha256'].items():
        assert sha(Path(__file__).resolve().parents[1] / name) == digest, name
    for case, row in zip(reg['cases'], state['rows']):
        folder = Path(row['folder'])
        q = json.loads((folder / 'DEMONSTRATION_QUALIFICATION.json').read_text())
        b = json.loads((folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json').read_text())
        h = json.loads((folder / 'HANDOFF_EXECUTION.json').read_text())
        r = json.loads((folder / 'HANDOFF_REVIEW.json').read_text())
        assert sha(folder / 'HANDOFF_REVIEW.json') == row['review_sha256']
        assert sha(folder / 'DEMONSTRATION_QUALIFICATION.json') == row['qualification_sha256']
        assert sha(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json') == row['behavior_sha256']
        assert h['source_stable'] and h['student_steps'] == 0 and h['executed_teacher_steps'] == 500
        assert sha(folder / 'teacher.json') == reg['teacher_config_sha256']
        assert r['qualified'] == row['qualified'] == (q['status'] == 'qualified')
        assert b['checks']['persistent_rejoin_before_withdrawal'] == row['qualified']
        assert q['task_success'] and q['safety_valid'] and q['checks']['actor_filter_replay'] is True
        assert b['hashes']['trajectory.npz'] == sha(folder / 'trajectory.npz')
    failures = [row['id'] for row in state['rows'] if not row['qualified']]
    assert state['status'] == ('three_probes_qualified_pending_independent_review' if not failures
                               else 'complete_with_failures_preserved_no_collection')
    return dict(status='independently_verified', identities=len(state['rows']),
                qualified=sum(x['qualified'] for x in state['rows']), failures=failures)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', type=Path, required=True)
    print(json.dumps(review(p.parse_args().root), indent=2))
