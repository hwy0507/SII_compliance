"""Run fixed27 development checks for the targeted-recovery v4 model lock."""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
COLLECTION = ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
HANDOFF = ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v4'
TARGET = ROOT/'outputs/contact_yield_targeted_student_development_20261030_v2'
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('targeted_recovery_base_diagnosis', BASE)
diagnosis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diagnosis
spec.loader.exec_module(diagnosis)
diagnosis.TRAINING = TRAINING
diagnosis.COLLECTION = COLLECTION
diagnosis.HANDOFF = HANDOFF
diagnosis.UNITS = ()


def prerequisites():
    scope = properties('sii-contact-yield-targeted-refit-v4-20261030.scope')
    assert scope['ActiveState'] == 'inactive'
    fit_state = read(TRAINING/'execution.json')
    lock = read(TRAINING/'MODEL_LOCK.json')
    audit = read(TRAINING/'FIT_AUDIT.json')
    handoff = read(HANDOFF/'execution.json')
    assert fit_state['status'] == 'complete' and lock['status'] == 'frozen'
    assert audit['status'] == 'passed'
    assert audit['model_lock_sha256'] == fit_state['model_lock_sha256'] == sha(TRAINING/'MODEL_LOCK.json')
    assert audit['dataset_sha256'] == lock['training_data_sha256'] == sha(TRAINING/'data/training_data.npz')
    assert len(audit['candidate_jobs']) == 75 and len(audit['frozen_actor_replays']) == 9
    assert handoff['status'] == 'failed_preserved_no_retry'
    assert read(COLLECTION/'COLLECTION_REVIEW.json')['status'] == 'verified_all30_qualified'
    return lock


diagnosis.prerequisites = prerequisites
_legacy_check = diagnosis.check


def check(reg):
    compatible = dict(reg)
    compatible['schema'] = 'sii-contact-yield-student-development-diagnosis-v1'
    _legacy_check(compatible)


diagnosis.check = check


def prepare(root):
    assert not root.exists()
    prerequisites()
    diagnosis.prepare(root)
    path = root/'REGISTRATION.json'
    reg = read(path)
    reg['schema'] = 'sii-contact-yield-targeted-student-development-v1'
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    reg['training_files'] = {name: sha(TRAINING/name) for name in (
        'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
        'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    reg['fit_handoff_failure_sha256'] = sha(HANDOFF/'execution.json')
    from collect_contact_yield_scrape_scenes_20261030 import write
    write(path, reg)
    check(reg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'review'))
    parser.add_argument('--root', type=Path, default=TARGET)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    if args.mode == 'prepare':
        prepare(root)
    elif args.mode == 'run':
        diagnosis.run(root)
    else:
        assert args.output is not None
        diagnosis.review(root, args.output.resolve())


if __name__ == '__main__':
    main()
