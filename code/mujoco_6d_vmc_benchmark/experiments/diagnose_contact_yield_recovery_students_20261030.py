"""Run the fixed train-only 27-cell diagnosis with recovery-augmented models.

The physical runner and row reviewer are reused unchanged; all model and
dataset provenance is rebound to the separately audited recovery refit.
"""
import argparse
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
COLLECTION = ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
FIT_HANDOFF = ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v3'
FIT_UNIT = 'sii-contact-yield-recovery-fit-v3-20261030.service'
SCHEMA = 'sii-contact-yield-recovery-student-development-diagnosis-v1'

sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('contact_yield_base_diagnosis', BASE)
diagnosis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diagnosis
spec.loader.exec_module(diagnosis)
diagnosis.TRAINING = TRAINING
diagnosis.COLLECTION = COLLECTION
diagnosis.HANDOFF = FIT_HANDOFF
diagnosis.UNITS = (FIT_UNIT,)


def prerequisites():
    assert properties(FIT_UNIT)['ActiveState'] == 'inactive'
    parent = read(FIT_HANDOFF/'execution.json')
    assert parent['status'] == 'complete_nine_refits_pending_fixed_development_review'
    state = read(TRAINING/'execution.json')
    lock = read(TRAINING/'MODEL_LOCK.json')
    audit = read(TRAINING/'FIT_AUDIT.json')
    assert state['status'] == 'complete' and lock['status'] == 'frozen'
    assert state['model_lock_sha256'] == sha(TRAINING/'MODEL_LOCK.json')
    assert audit['status'] == 'passed'
    assert audit['model_lock_sha256'] == state['model_lock_sha256']
    assert audit['dataset_sha256'] == lock['training_data_sha256']
    assert sha(TRAINING/'data/training_data.npz') == lock['training_data_sha256']
    assert len(audit['candidate_jobs']) == 75
    assert len(audit['frozen_actor_replays']) == 9
    assert len(lock['models']) == 9
    assert read(COLLECTION/'COLLECTION_REVIEW.json')['status'] == 'verified_all30_qualified'
    return lock


diagnosis.prerequisites = prerequisites
_legacy_check = diagnosis.check


def check(reg):
    assert reg['schema'] == SCHEMA
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
    reg['schema'] = SCHEMA
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    reg['training_files'] = {
        name: sha(TRAINING/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')
    }
    write(path, reg)
    check(reg)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'review'))
    parser.add_argument('--root', type=Path, required=True)
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
