"""Snapshot completed review evidence outside immutable simulation directories."""
import argparse
from pathlib import Path
import shutil

from teacher_bank_campaign_20260930 import REPO, archive
from teacher_bank_design_20260930 import sha, write


def snapshot(destination):
    if destination.exists():
        raise FileExistsError('Use a new immutable review checkpoint directory')
    destination.mkdir(parents=True)
    evidence = destination / 'evidence'
    evidence.mkdir()
    sources = []
    for directory, pattern in (
        ('outputs/teacher_bank_geometry_preflight_20260930', '*.json'),
        ('outputs/teacher_bank_reports_20260930', '*_final.*'),
        ('outputs/teacher_bank_three_domains_20260930_v8', 'pilot_summary.json'),
        ('outputs/teacher_bank_three_domains_20260930_v8', 'planned_phase_boundary_stop.json'),
        ('outputs/teacher_bank_three_domains_20260930_v8/paired_model_checks', '*.json'),
    ):
        sources.extend(sorted((REPO / directory).glob(pattern)))
    records = []
    for source in sources:
        relative = source.relative_to(REPO)
        target = evidence / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        before = sha(source)
        shutil.copy2(source, target)
        if sha(target) != before or sha(source) != before:
            raise RuntimeError('Source changed during review snapshot: ' + str(source))
        records.append(dict(source=str(source), snapshot=str(relative), sha256=before))
    write(evidence / 'review_sources.json', records)
    shutil.copy2(__file__, evidence / Path(__file__).name)
    return evidence


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--archive', action='store_true')
    args = parser.parse_args()
    destination = args.destination.resolve()
    snapshot(destination)
    if args.archive:
        path = archive(destination, 'evidence')
        write(destination / 'archive_receipt.json', dict(verified_path=path))
