"""Register a finite direction-coverage repair after all eight controls are reviewed.

Only qualified physical controls inform ball approach/carry direction and angle.
Original rod/corner configurations and teacher remain; all 30 are re-executed
under a new prospective plan. No student model or regression label is read.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from collect_special_scene_coverage_20261029 import (
    ROOT, COVERAGE_PARAMETERS, read, sha, validate, write,
)


def prepare(parent, probe, output):
    parent, probe, output = parent.resolve(), probe.resolve(), output.resolve()
    if output.exists():
        raise FileExistsError(output)
    review_path = probe / 'REVIEW.json'
    motion_path = probe / 'ACTUAL_MOTION.json'
    review, motion = read(review_path), read(motion_path)
    reg, state = read(probe / 'REGISTRATION.json'), read(probe / 'execution.json')
    if (review['status'] != 'complete_physical_coverage_review'
            or state['status'] != 'complete_pending_review'
            or len(review['rows']) != len(reg['cases']) or len(reg['cases']) != 8
            or review['registration_sha256'] != sha(probe / 'REGISTRATION.json')
            or review['execution_sha256'] != sha(probe / 'execution.json')):
        raise ValueError('Require complete matching eight-control review')
    if motion['status'] != 'complete_saved_ball_motion_description' or len(motion['rows']) != 8:
        raise ValueError('Require actual hand/object motion review of all eight')
    measured = {Path(row['folder']).resolve().parent.name: row for row in motion['rows']}
    if set(measured) != {case['id'] for case in reg['cases']}:
        raise ValueError('Actual motion identities differ')
    results = {row['id']: row for row in review['rows']}
    eligible = defaultdict(list)
    for case in reg['cases']:
        row, actual = results[case['id']], measured[case['id']]
        folder = probe / case['id'] / 'ball'
        for name, digest in actual['input_sha256'].items():
            if sha(folder / name) != digest:
                raise ValueError('Changed actual-motion evidence')
        if (row['qualification_status'] != 'qualified'
                or not row['coverage']['physical_direction_coverage']):
            continue
        phases = {p['name']: p for p in actual['phases']}
        # This checks the sign of observed displacement, not a new task gate.
        if not all(phases[n]['reached'] and
                   phases[n]['object_projection_on_goal_displacement_m'] > 0
                   for n in ('carry', 'recovery')):
            raise ValueError('Qualified control has no forward actual object motion')
        p = case['parameters']
        axis = 'x' if p['VMC_COVERAGE_INITIAL_X_M'] else 'y'
        sign = -1 if p['VMC_COVERAGE_INITIAL_' + axis.upper() + '_M'] < 0 else 1
        eligible[(axis, sign)].append(case)
    groups = [('x', -1), ('x', 1), ('y', -1), ('y', 1)]
    if any(not eligible[g] for g in groups):
        raise ValueError('At least one cardinal direction has no qualified physical control')

    plan = deepcopy(read(parent))
    if plan['teacher_file_sha256'] != reg['teacher_sha256']:
        raise ValueError('Teacher changed between original collection and controls')
    plan.update(schema='sii-three-real-scenes-collection-plan-v3',
        registered_utc=datetime.now(timezone.utc).isoformat(),
        coverage_probe_review=str(review_path), coverage_probe_review_sha256=sha(review_path),
        coverage_actual_motion=str(motion_path), coverage_actual_motion_sha256=sha(motion_path),
        parent_collection_plan=str(parent), parent_collection_plan_sha256=sha(parent),
        supersedes=str(parent.parent),
        repair_design=dict(
            purpose='Repair missing direction x load/stage coverage, not change the learning algorithm',
            training_ball='Two conditions per cardinal initial/carry direction; eligible angles in original registration order, cycle if only one is qualified',
            validation_ball='Original held-out speed/shift identities 08/09 assigned to negative/positive Y initial direction; use first/last eligible angle respectively',
            other_scenes='All original rod/corner physical parameters retained and re-executed; new root and prospective lineage',
            unchanged='One teacher; 24 train/6 validation; same canonical48/filter/action scale/physics gates; same fitting and selection rules',
            failures='All eight development controls retained, including nonqualified contact; no development trajectory is ingested',
            budget='Exactly 30 formal episodes; nonqualified demonstrations block dataset build; no automatic replacements'))
    assignments = [g for g in groups for _ in range(2)] + [('y', -1), ('y', 1)]
    balls = [e for e in plan['episodes'] if e['scene'] == 'ball']
    if len(balls) != 10 or [e['split'] for e in balls] != ['train'] * 8 + ['validation'] * 2:
        raise ValueError('Unexpected original ball identity order')
    selected = []
    for index, (entry, group) in enumerate(zip(balls, assignments)):
        choices = eligible[group]
        choice_index = index % 2 if index < 8 else (0 if index == 8 else len(choices) - 1)
        case = choices[choice_index % len(choices)]
        entry['scene_parameters'].update({k: case['parameters'][k] for k in COVERAGE_PARAMETERS})
        selected.append(dict(identity=entry['id'], development_basis=case['id'],
                             physical_parameters=entry['scene_parameters']))
    plan['repair_design']['ball_assignments'] = selected
    for entry in plan['episodes']:
        entry['folder'] = str(output / entry['id'] / entry['scene'])
    sources = set(plan['source_sha256'])
    sources.update('tools/' + n for n in (
        'collect_special_scene_coverage_20261029.py', 'run_registered_special_coverage_20261029.py',
        'qualify_registered_special_coverage_20261029.py', 'build_special_coverage_dataset_20261029.py',
        'review_ball_coverage_probe_20261029.py', 'describe_ball_actual_motion_20261029.py',
        Path(__file__).name))
    sources.update(str(p.relative_to(ROOT)) for p in (ROOT / 'scripts').glob('*.py'))
    plan['source_sha256'] = {name: sha(ROOT / name) for name in sorted(sources)}
    output.mkdir(parents=True)
    destination = output / 'COLLECTION_PLAN.json'
    write(destination, plan)
    validate(destination)
    print('registered_not_started', destination, sha(destination), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--probe', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.parent, args.probe, args.output)
