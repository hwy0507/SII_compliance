"""Finite 0.5 readout probe after 0.6 collection revealed ball oscillation.

Keep all condition parameters/seed/MJB/hold time unchanged; five training
identities, no validation/test selection and no automatic student training.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from collect_special_scene_actions_20261028 import read, sha, write, validate
from probe_special_scene_readout_20261028 import run

ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / 'outputs/special_scene_vmc_collection_20261028_v4'


def prepare(root):
    if root.exists():
        raise FileExistsError(root)
    plan = validate(COLLECTION / 'COLLECTION_PLAN.json')
    progress = read(COLLECTION / 'COLLECTION_PROGRESS.json')
    assert progress['status'] == 'finished_with_nonqualified_demonstrations' and len(progress['episodes']) == 30
    assert [r['id'] for r in progress['episodes'] if r['status'] != 'qualified'] == ['ball_01']
    candidate = ROOT / 'configs/special_scene_vmc_readout05_20261028.json'
    original = read(Path(plan['teacher_config']))
    changed = read(candidate)
    assert original['velocity_weight'] == .6 and changed['velocity_weight'] == .5
    comparison = dict(changed)
    comparison['velocity_weight'] = .6
    assert comparison == original
    cases = []
    for name in ('rod_00', 'rod_04', 'ball_00', 'ball_01', 'corner_00'):
        entry = next(e for e in plan['episodes'] if e['id'] == name)
        assert entry['split'] == 'train'
        baseline = Path(entry['folder'])
        execution = read(baseline / 'execution.json')
        assert execution['status'] == 'complete'
        cases.append(dict(id=name, scene=entry['scene'], seed=entry['seed'], baseline=str(baseline),
                          baseline_execution_sha256=sha(baseline / 'execution.json'),
                          expected_model_sha256=execution['model_sha256'],
                          scene_parameters=entry['scene_parameters']))
    tools = ('run_video_reference_vmc_20261028.py', 'audit_video_reference_vmc_20261028.py',
             'audit_rod_yield_rejoin_v3_20261028.py', 'qualify_special_scene_demo_20261028.py',
             'collect_special_scene_actions_20261028.py', 'probe_special_scene_readout_20261028.py',
             'probe_special_scene_readout05_20261028.py', 'review_special_collection_probe_20261028.py',
             'prepare_special_recollection_20261028.py', 'optimize_tool_contact_20261002.py')
    sources = {str(Path('tools') / name): sha(ROOT / 'tools' / name) for name in tools}
    sources.update({str(p.relative_to(ROOT)): sha(p) for p in (ROOT / 'scripts').glob('*.py')})
    registration = dict(schema='sii-special-scene-readout-probe-v1',
                        registered_utc=datetime.now(timezone.utc).isoformat(),
                        collection=str(COLLECTION), collection_service='sii-special-collection-v4-20261028.service',
                        collection_plan_sha256=sha(COLLECTION / 'COLLECTION_PLAN.json'),
                        candidate=str(candidate), candidate_file_sha256=sha(candidate),
                        candidate_config_sha256=hashlib.sha256((json.dumps(changed, indent=2) + '\n').encode()).hexdigest(),
                        cases=cases, source_hashes=sources, maximum_episodes=5,
                        motivation='Original0.6 ball_01 terminal object finite-difference speed0.033813 m/s exceeds unchanged0.02 gate; original0.3 was0.000181. Probe one intermediate0.5, not scene-dependent switching.',
                        selection='Training identities rod00/04 (previously fixed recovery checks), ball00/01 (including the actual new failure), corner00. No validation or test selection.',
                        disposition='Review all five. Preserve original30 failures. No automatic collection or fitting. Never extend hold/horizon or relax gates.')
    root.mkdir(parents=True)
    write(root / 'REGISTRATION.json', registration)
    print(json.dumps(dict(root=str(root), maximum_episodes=5, sha256=sha(root / 'REGISTRATION.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.run:
        run(args.root.resolve())
    else:
        prepare(args.root.resolve())
