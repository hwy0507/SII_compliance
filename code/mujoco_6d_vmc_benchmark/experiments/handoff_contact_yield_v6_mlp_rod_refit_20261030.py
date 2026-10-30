"""Register and run the shared 75-candidate v6 rod-handoff refit."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties

RECOVERY = ROOT/'outputs/contact_yield_v6_mlp_rod_handoff_20261030_v1'
BASE = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v6'
TRAINING = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v7'
TARGET = ROOT/'outputs/contact_yield_v6_mlp_rod_refit_handoff_20261030_v3'
SCOPE = 'sii-contact-yield-v6-mlp-rod-refit-v3-20261030.scope'
BLOCKING = (
    'sii-contact-yield-scrape-collection-20261030.service',
    'sii-contact-yield-scrape-training-handoff-20261030.service',
    'sii-contact-yield-student-diagnosis-handoff-20261030.service',
    'sii-contact-yield-final108-handoff-20261030.service',
    'sii-contact-yield-recovery-student-handoff-v1-20261030.service',
    'sii-contact-yield-v6-mlp-rod-handoff-20261030.scope', SCOPE)
BUILDER = ROOT/'experiments/build_contact_yield_v6_mlp_rod_dataset_20261030.py'
TRAINER = ROOT/'tools/train_contact_yield_recovery_models_v2_20261030.py'
AUDITOR = ROOT/'tools/audit_contact_yield_recovery_fits_v2_20261030.py'
SOURCES = (Path(__file__).resolve(), BUILDER, TRAINER, AUDITOR,
           ROOT/'tools/train_contact_yield_recovery_neural_20261030.py',
           ROOT/'tools/train_paper_context_esn_20261003.py',
           ROOT/'tools/train_office_mlp_rnn_20261002.py',
           ROOT/'tools/optimize_tool_contact_20261002.py')


def now():
    return datetime.now(timezone.utc).isoformat()


def require_idle(inside_scope=False):
    for unit in BLOCKING:
        if inside_scope and unit == SCOPE:
            continue
        state = properties(unit)
        assert state['ActiveState'] == 'inactive' and state.get('MainPID', '0') in ('0', ''), (unit, state)


def prepare(root=TARGET):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    require_idle()
    recovery = read(RECOVERY/'execution.json')
    assert recovery['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    assert recovery['registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert [row['id'] for row in recovery['rows']] == [
        'v6_rod_mlp01_handoff_4p48s', 'v6_rod_mlp01_handoff_4p60s',
        'v6_rod_mlp03_handoff_4p48s', 'v6_rod_mlp03_handoff_4p60s']
    assert [row['qualified'] for row in recovery['rows']] == [True, True, False, False]
    assert read(BASE/'execution.json')['status'] == 'complete'
    assert read(BASE/'MODEL_LOCK.json')['status'] == 'frozen'
    assert read(BASE/'FIT_AUDIT.json')['status'] == 'passed'
    assert read(TRAINING/'execution.json')['status'] == 'dataset_complete'
    data_meta = read(TRAINING/'data/DATA_COMPLETE.json')
    assert data_meta['schema'] == 'sii-vmc-special-scenes-recovery-augmented-v4'
    assert data_meta['training_data_sha256'] == sha(TRAINING/'data/training_data.npz')
    assert data_meta['episodes'] == 40 and data_meta['frames'] == 21500
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-v6-rod-handoff-fit-handoff-v1', registered_utc=now(),
        recovery=str(RECOVERY), recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        recovery_execution_sha256=sha(RECOVERY/'execution.json'),
        parent_training=str(BASE), parent_model_lock_sha256=sha(BASE/'MODEL_LOCK.json'),
        training=str(TRAINING), dataset_sha256=sha(TRAINING/'data/training_data.npz'),
        metadata_sha256=sha(TRAINING/'data/DATA_COMPLETE.json'),
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in SOURCES},
        maximum_fit_jobs=75, candidates_per_family_seed=12, neural_updates=32000,
        validation_scope='Same six pure-teacher validation identities; no recovery row used for selection.',
        no_test_selection=True, no_automatic_retry=True,
        resources=dict(cpu=6, threads=1, memory_max_bytes=3221225472, swap_bytes=0)))


def check(reg, inside_scope=False):
    require_idle(inside_scope=inside_scope)
    assert reg['schema'] == 'sii-contact-yield-v6-rod-handoff-fit-handoff-v1'
    assert reg['recovery_registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert reg['recovery_execution_sha256'] == sha(RECOVERY/'execution.json')
    assert reg['parent_model_lock_sha256'] == sha(BASE/'MODEL_LOCK.json')
    assert reg['dataset_sha256'] == sha(TRAINING/'data/training_data.npz')
    assert reg['metadata_sha256'] == sha(TRAINING/'data/DATA_COMPLETE.json')
    assert read(RECOVERY/'execution.json')['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    final = read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False


def run(root=TARGET):
    root = Path(root).resolve()
    check_resources()
    reg = read(root/'REGISTRATION.json')
    check(reg, inside_scope=True)
    state_path = root/'execution.json'
    assert not state_path.exists()
    state = dict(status='build_verified_recovery_dataset', started_utc=now(),
                 dispatch_attempted=False, registration_sha256=sha(root/'REGISTRATION.json'))
    write(state_path, state)

    def command(args):
        assert sha(root/'REGISTRATION.json') == state['registration_sha256']
        for name, digest in reg['source_sha256'].items():
            assert sha(ROOT/name) == digest, name
        with (root/'training.log').open('a') as log:
            subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)

    try:
        data = read(TRAINING/'data/DATA_COMPLETE.json')
        assert read(TRAINING/'execution.json')['status'] == 'dataset_complete'
        assert sha(TRAINING/'data/training_data.npz') == reg['dataset_sha256']
        assert sha(TRAINING/'data/DATA_COMPLETE.json') == reg['metadata_sha256']
        state.update(status='dataset_verified_fit_ready', dispatch_attempted=False,
                     dataset_sha256=sha(TRAINING/'data/training_data.npz'),
                     metadata_sha256=sha(TRAINING/'data/DATA_COMPLETE.json'))
        write(state_path, state)
        assert data['schema'] == 'sii-vmc-special-scenes-recovery-augmented-v4'
        assert data['episodes'] == 40 and data['frames'] == 21500
        assert data['zero_weight_warmup_frames'] == 1934
        assert data['training_data_sha256'] == state['dataset_sha256']
        state.update(status='fair_refit_75_candidates', dispatch_attempted=True)
        write(state_path, state)
        command([TRAINER, '--root', TRAINING, '--run'])
        state.update(status='independent_fit_audit')
        write(state_path, state)
        command([AUDITOR, '--root', TRAINING, '--physics-source', ROOT,
                 '--output', TRAINING/'FIT_AUDIT.json'])
        audit = read(TRAINING/'FIT_AUDIT.json')
        assert audit['status'] == 'passed' and len(audit['candidate_jobs']) == 75
        assert len(audit['frozen_actor_replays']) == 9
        lock = read(TRAINING/'MODEL_LOCK.json')
        state.update(status='complete_nine_refits_pending_fixed27_review',
                     model_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),
                     audit_sha256=sha(TRAINING/'FIT_AUDIT.json'), ended_utc=now())
        write(state_path, state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry', error=repr(exc), ended_utc=now())
        write(state_path, state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run'))
    parser.add_argument('--root', type=Path, default=TARGET)
    args = parser.parse_args()
    (prepare if args.mode == 'prepare' else run)(args.root.resolve())
