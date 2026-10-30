"""Run the fixed train-only 27-cell review against the audited v7 model lock."""
import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
COLLECTION = ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
HANDOFF = ROOT/'outputs/contact_yield_v6_mlp_rod_refit_handoff_20261030_v3'
TARGET = ROOT/'outputs/contact_yield_recovery_student_development_20261030_v6'
FIT_UNIT = 'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope'

sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from collect_contact_yield_scrape_scenes_20261030 import properties

spec = importlib.util.spec_from_file_location('contact_yield_v7_base_diagnosis', BASE)
diagnosis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diagnosis
spec.loader.exec_module(diagnosis)
diagnosis.TRAINING = TRAINING
diagnosis.COLLECTION = COLLECTION
diagnosis.HANDOFF = HANDOFF
diagnosis.TARGET = TARGET
diagnosis.UNITS = (FIT_UNIT,)


def prerequisites():
    fit_unit = properties(FIT_UNIT)
    assert fit_unit['ActiveState'] == 'inactive' and fit_unit.get('MainPID', '0') in ('0', '')
    fit_handoff = read(HANDOFF/'execution.json')
    fit_state = read(TRAINING/'execution.json')
    lock = read(TRAINING/'MODEL_LOCK.json')
    audit = read(TRAINING/'FIT_AUDIT.json')
    data = read(TRAINING/'data/DATA_COMPLETE.json')
    assert fit_handoff['status'] == 'complete_nine_refits_pending_fixed27_review'
    assert fit_state['status'] == 'complete' and lock['status'] == 'frozen'
    assert fit_state['model_lock_sha256'] == sha(TRAINING/'MODEL_LOCK.json')
    assert audit['status'] == 'passed'
    assert audit['model_lock_sha256'] == fit_state['model_lock_sha256']
    assert audit['dataset_sha256'] == lock['training_data_sha256'] == data['training_data_sha256']
    assert data['episodes'] == 40 and data['frames'] == 21500
    assert len(audit['candidate_jobs']) == 75
    assert len(audit['frozen_actor_replays']) == len(lock['models']) == 9
    assert len(fit_state['fits']) == 75 and all(item['status'] == 'complete' for item in fit_state['fits'])
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False
    return lock


diagnosis.prerequisites = prerequisites
_legacy_check = diagnosis.check


def check(reg):
    assert reg['schema'] == 'sii-contact-yield-recovery-v7-fixed27-diagnosis-v1'
    compatible = dict(reg)
    compatible['schema'] = 'sii-contact-yield-student-development-diagnosis-v1'
    _legacy_check(compatible)
    assert reg['training_files'] == {
        name: sha(TRAINING/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
    assert reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] == sha(Path(__file__))


diagnosis.check = check


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    prerequisites()
    diagnosis.prepare(root)
    path = root/'REGISTRATION.json'
    reg = read(path)
    reg['schema'] = 'sii-contact-yield-recovery-v7-fixed27-diagnosis-v1'
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
    reg['training_files'] = {
        name: sha(TRAINING/name) for name in (
            'execution.json', 'MODEL_LOCK.json', 'FIT_AUDIT.json',
            'data/training_data.npz', 'data/DATA_COMPLETE.json')}
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
