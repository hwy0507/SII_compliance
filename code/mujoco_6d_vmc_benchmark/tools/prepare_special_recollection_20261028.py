"""Register a full replacement collection only after a qualified finite probe.

Inherit every original physical condition, seed and split verbatim. In
particular, do not recenter the domain on a successful probe condition.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

from collect_special_scene_actions_20261028 import read, sha, validate
from review_special_collection_probe_20261028 import evidence


def prepare(original, probe, review, output):
    if output.exists():
        raise FileExistsError(output)
    plan = validate(original / 'COLLECTION_PLAN.json')
    progress = read(original / 'COLLECTION_PROGRESS.json')
    if progress['status'] not in ('qualified_complete', 'finished_with_nonqualified_demonstrations') or len(progress['episodes']) != 30:
        raise ValueError('Original collection must be fully finished')
    registration = read(probe / 'REGISTRATION.json')
    state = read(probe / 'execution.json')
    reviewed = read(review)
    count = registration['maximum_episodes']
    if state['status'] != 'complete' or len(state['episodes']) != len(registration['cases']) or len(state['episodes']) != count:
        raise ValueError('Require all registered probe cases completed')
    if not reviewed['probe'].get('all_cases_qualified', reviewed['probe'].get('all4_qualified', False)):
        raise ValueError('Probe did not qualify; no formal recollection')
    if registration['collection_plan_sha256'] != sha(original / 'COLLECTION_PLAN.json'):
        raise ValueError('Wrong original plan')
    assert reviewed['plan_sha256'] == registration['collection_plan_sha256']
    assert reviewed['probe']['registration_sha256'] == sha(probe / 'REGISTRATION.json')
    assert state['registration_sha256'] == sha(probe / 'REGISTRATION.json')
    teacher = Path(registration['candidate'])
    assert sha(teacher) == registration['candidate_file_sha256']
    references = {}
    for entry, receipt, pair in zip(registration['cases'], state['episodes'], reviewed['probe']['pairs']):
        assert entry['id'] == receipt['id'] == pair['id']
        folder = probe / entry['id'] / entry['scene']
        current = evidence(folder)
        assert current == pair['candidate']
        if current['status'] != 'qualified':
            raise ValueError(f'Failed probe: {entry["id"]}')
        assert current['teacher_sha256'] == registration['candidate_config_sha256']
        assert current['model_sha256'] == entry['expected_model_sha256']
        references.setdefault(entry['scene'], dict(folder=str(folder), qualification_sha256=current['qualification_sha256']))
    assert set(references) == {'rod', 'ball', 'corner'}
    successor = copy.deepcopy(plan)
    successor.update(registered_utc=datetime.now(timezone.utc).isoformat(),
                     teacher_config=str(teacher), teacher_file_sha256=sha(teacher),
                     teacher_config_sha256=registration['candidate_config_sha256'],
                     development_references=references,
                     supersedes=dict(original_plan=str(original / 'COLLECTION_PLAN.json'),
                                     original_plan_sha256=sha(original / 'COLLECTION_PLAN.json'),
                                     probe_registration_sha256=sha(probe / 'REGISTRATION.json'),
                                     reviewed_evidence=str(review), reviewed_evidence_sha256=sha(review),
                                     rule='All original 30 conditions, seeds and partitions unchanged; all failures retained; all30 collected again under one teacher. No test-based selection.'))
    for old, new in zip(plan['episodes'], successor['episodes']):
        new['folder'] = str(output / new['id'] / new['scene'])
        assert {k: v for k, v in old.items() if k != 'folder'} == {k: v for k, v in new.items() if k != 'folder'}
    output.mkdir(parents=True)
    destination = output / 'COLLECTION_PLAN.json'
    destination.write_text(json.dumps(successor, indent=2, allow_nan=False) + '\n')
    validate(destination)
    print(json.dumps(dict(plan=str(destination), sha256=sha(destination), episodes=30)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('original', 'probe', 'review', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    prepare(*(getattr(args, k).resolve() for k in ('original', 'probe', 'review', 'output')))
