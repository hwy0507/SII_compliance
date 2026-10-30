"""Evaluate the capacity-selected MLPs on fixed train00 identities only."""
import argparse
import copy
import importlib.util
import os
import sys
from pathlib import Path
import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'experiments/diagnose_contact_yield_students_20261030.py'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
CAPACITY = ROOT/'outputs/contact_yield_mlp_capacity_20261031_v1'
COLLECTION = ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
FIT_HANDOFF = ROOT/'outputs/contact_yield_v6_mlp_rod_refit_handoff_20261030_v3'
FIT_UNIT = 'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope'
TARGET = ROOT/'outputs/contact_yield_mlp384_fixed27_20261031_v1'

sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import properties

spec = importlib.util.spec_from_file_location('contact_yield_mlp384_fixed27_base', BASE)
diagnosis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = diagnosis
spec.loader.exec_module(diagnosis)
diagnosis.TRAINING = TRAINING
diagnosis.COLLECTION = COLLECTION
diagnosis.UNITS = (FIT_UNIT,)

def selected_models():
    old_lock = read(TRAINING/'MODEL_LOCK.json')
    capacity_lock = read(CAPACITY/'MODEL_LOCK.json')
    capacity = {row['seed']: row for row in capacity_lock['models']}
    result = []
    for old in old_lock['models']:
        model = copy.deepcopy(old)
        if old['family'] == 'mlp_scratch':
            selected = capacity[old['seed']]
            metadata = CAPACITY/'learning'/selected['selected_trial']/'TRAINING_COMPLETE.json'
            model.update(
                name='special_mlp_scratch_s%d_w384' % old['seed'],
                selected_trial=selected['selected_trial'],
                checkpoint=selected['checkpoint'],
                checkpoint_sha256=selected['checkpoint_sha256'],
                metadata=str(metadata), metadata_sha256=sha(metadata),
                validation_mse=selected['validation_mse'], trainable_parameters=16512,
                hidden_width=384, capacity_model_lock_sha256=sha(CAPACITY/'MODEL_LOCK.json'))
        result.append(model)
    assert len(result) == 9 and len({m['name'] for m in result}) == 9
    assert sum(m.get('hidden_width') == 384 for m in result) == 3
    return result


def prerequisites():
    assert properties(FIT_UNIT)['ActiveState'] == 'inactive'
    fit_handoff = read(FIT_HANDOFF/'execution.json')
    fit_state = read(TRAINING/'execution.json')
    old_lock = read(TRAINING/'MODEL_LOCK.json')
    old_audit = read(TRAINING/'FIT_AUDIT.json')
    capacity_state = read(CAPACITY/'execution.json')
    capacity_audit = read(CAPACITY/'FIT_AUDIT.json')
    capacity_lock = read(CAPACITY/'MODEL_LOCK.json')
    data = read(TRAINING/'data/DATA_COMPLETE.json')
    assert fit_handoff['status'] == 'complete_nine_refits_pending_fixed27_review'
    assert fit_state['status'] == 'complete' and len(fit_state['fits']) == 75
    assert all(row['status'] == 'complete' for row in fit_state['fits'])
    assert old_lock['status'] == 'frozen' and old_audit['status'] == 'passed'
    assert old_audit['model_lock_sha256'] == fit_state['model_lock_sha256'] == sha(TRAINING/'MODEL_LOCK.json')
    assert old_audit['dataset_sha256'] == old_lock['training_data_sha256'] == data['training_data_sha256']
    assert len(old_audit['candidate_jobs']) == 75 and len(old_audit['frozen_actor_replays']) == 9
    assert capacity_state['status'] == 'complete' and len(capacity_state['fits']) == 36
    assert all(row['status'] == 'complete' and row['updates'] == 32000 for row in capacity_state['fits'])
    assert capacity_audit['status'] == 'passed' and capacity_audit['candidates'] == 36
    assert capacity_audit['dataset_sha256'] == data['training_data_sha256']
    assert capacity_lock['status'] == 'frozen' and len(capacity_lock['models']) == 3
    assert all(row['width'] == 384 for row in capacity_lock['models'])
    assert read(COLLECTION/'COLLECTION_REVIEW.json')['status'] == 'verified_all30_qualified'
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False
    return dict(models=selected_models(), old_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),
                old_audit_sha256=sha(TRAINING/'FIT_AUDIT.json'),
                capacity_lock_sha256=sha(CAPACITY/'MODEL_LOCK.json'),
                capacity_audit_sha256=sha(CAPACITY/'FIT_AUDIT.json'))


def check(reg):
    inputs = prerequisites()
    assert reg['schema'] == 'sii-contact-yield-mlp384-fixed27-diagnosis-v1'
    assert reg['models'] == inputs['models']
    assert reg['parent_hashes'] == {k: v for k, v in inputs.items() if k != 'models'}
    assert reg['cases'] == diagnosis.make_cases(reg['models'], reg['references'])
    assert len(reg['cases']) == reg['maximum_episodes'] == 27
    assert reg['python'] == os.path.abspath(sys.executable)
    assert reg['runtime_versions'] == dict(python=sys.version, numpy=np.__version__, mujoco=mujoco.__version__)
    for base, key in ((TRAINING, 'training_files'), (COLLECTION, 'collection_files')):
        for name, digest in reg[key].items():
            assert sha(base/name) == digest, name
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    assert sha(Path(reg['teacher_config'])) == reg['teacher_config_sha256']
    for model in reg['models']:
        for key in ('checkpoint', 'metadata'):
            assert sha(Path(model[key])) == model[key+'_sha256']
    for ref in reg['references']:
        for name, digest in ref['hashes'].items():
            assert sha(Path(ref['folder'])/name) == digest


diagnosis.prerequisites = lambda: prerequisites()
diagnosis.check = check


def prepare(root):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    inputs = prerequisites()
    diagnosis.prepare(root)
    path = root/'REGISTRATION.json'
    reg = read(path)
    reg['schema'] = 'sii-contact-yield-mlp384-fixed27-diagnosis-v1'
    reg['parent_hashes'] = {k: v for k, v in inputs.items() if k != 'models'}
    reg['models'] = inputs['models']
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))] = sha(Path(__file__))
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
