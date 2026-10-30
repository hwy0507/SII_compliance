"""Read-only full27 review using the registered wide-MLP deployment loader."""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'experiments/diagnose_contact_yield_mlp384_fixed27_20261031_v4.py'
spec = importlib.util.spec_from_file_location('wide_fixed27_registered_review', SOURCE)
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--prefix-check', action='store_true')
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists(), 'Preserve earlier review evidence'
    root = campaign.TARGET
    registration = campaign.read(root/'REGISTRATION.json')
    campaign.check(registration)
    import current_student_policy_20260921 as legacy
    from current_student_policy_mlp384_20261031 import load_current
    original = legacy.load_current
    legacy.load_current = load_current
    try:
        if args.prefix_check:
            before = (root/'execution.json').read_bytes()
            state = campaign.read(root/'execution.json')
            rows = []
            cases = {c['id']: c for c in registration['cases']}
            for receipt in state['rows']:
                folder = campaign.diagnosis.case_folder(root, cases[receipt['id']])
                rows.append(dict(id=receipt['id'], **campaign.diagnosis.replay(folder)))
            campaign.write(output, dict(status='passed_completed_prefix_replay',
                execution_snapshot_sha256=__import__('hashlib').sha256(before).hexdigest(),
                reviewer_sha256=campaign.sha(Path(__file__)), rows=rows,
                scope='Saved completed prefix only; no full27 completion or safety claim.'))
        else:
            campaign.diagnosis.review(root, output)
            result = campaign.read(output)
            result['wide_loader_sha256'] = campaign.sha(ROOT/'scripts/current_student_policy_mlp384_20261031.py')
            result['wide_review_wrapper_sha256'] = campaign.sha(Path(__file__))
            campaign.write(output, result)
    finally:
        legacy.load_current = original


if __name__ == '__main__':
    main()
