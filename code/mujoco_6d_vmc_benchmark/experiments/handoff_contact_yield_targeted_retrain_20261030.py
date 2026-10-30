"""Run a common 75-candidate ESN/RNN/MLP refit on the qualified v4 dataset."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from collect_contact_yield_scrape_scenes_20261030 import read, sha, write
from select_v9_closed_loop_candidates_v3_20261029 import check_resources, properties

RECOVERY = ROOT/'outputs/contact_yield_targeted_recovery_20261030_v1'
DATA = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
BASE = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
TARGET = ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v4'
BLOCKING_UNITS = (
    'sii-contact-yield-recovery-20261030.service',
    'sii-contact-yield-recovery-student-handoff-v1-20261030.service',
    'sii-contact-yield-student-diagnosis-handoff-20261030.service',
    'sii-contact-yield-final108-handoff-20261030.service',
)
SOURCES = (
    Path(__file__).resolve(),
    ROOT/'experiments/build_contact_yield_targeted_dataset_20261030.py',
    ROOT/'tools/train_contact_yield_recovery_models_20261030.py',
    ROOT/'tools/train_contact_yield_recovery_neural_20261030.py',
    ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py',
)


def now():
    return datetime.now(timezone.utc).isoformat()


def require_idle():
    for unit in BLOCKING_UNITS:
        state = properties(unit)
        assert state['ActiveState'] == 'inactive' and state['MainPID'] == '0', (unit, state)
    current = properties('sii-contact-yield-targeted-run-20261030.scope')
    assert current['ActiveState'] == 'inactive'
    assert current.get('MainPID', '0') in ('', '0'), current


def prepare(root=TARGET):
    root = Path(root).resolve()
    assert root == TARGET.resolve() and not root.exists()
    require_idle()
    recovery = read(RECOVERY/'execution.json')
    assert recovery['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    assert recovery['registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert len(recovery['rows']) == 4
    selected = [row for row in recovery['rows'] if row['qualified']]
    rejected = [row for row in recovery['rows'] if not row['qualified']]
    assert [row['id'] for row in selected] == [
        'rod_mlp01_post_yield_5p2s', 'rod_mlp01_late_yield_7s']
    assert len(rejected) == 2
    data_execution = read(DATA/'execution.json')
    metadata = read(DATA/'data/DATA_COMPLETE.json')
    dataset = DATA/'data/training_data.npz'
    assert data_execution['status'] == 'dataset_complete'
    assert data_execution['dataset_sha256'] == sha(dataset) == metadata['training_data_sha256']
    assert metadata['episodes'] == 36 and metadata['frames'] == 19500
    assert metadata['augmented_recovery_episodes'] == 6
    assert metadata['zero_weight_warmup_frames'] == 1480
    assert metadata['teacher_supervised_recovery_frames'] == 2270
    assert read(BASE/'execution.json')['status'] == 'complete'
    assert read(BASE/'MODEL_LOCK.json')['status'] == 'frozen'
    assert read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')[
        'dispatch_attempted'] is False
    assert not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json', dict(
        schema='sii-contact-yield-targeted-fair-refit-handoff-v1', registered_utc=now(),
        recovery=str(RECOVERY), recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        recovery_execution_sha256=sha(RECOVERY/'execution.json'),
        parent_fit=str(BASE), parent_model_lock_sha256=sha(BASE/'MODEL_LOCK.json'),
        training_data=str(DATA), dataset_sha256=sha(dataset),
        metadata_sha256=sha(DATA/'data/DATA_COMPLETE.json'),
        registration_sha256=sha(DATA/'REGISTRATION.json'),
        source_sha256={str(path.relative_to(ROOT)): sha(path) for path in SOURCES},
        maximum_fit_jobs=75, candidates_per_family_seed=12, seeds=[2026102801, 2026102802, 2026102803],
        neural_updates=32000, validation_scope='same six pure-teacher development identities',
        no_test_selection=True, no_automatic_retry=True,
        resources=dict(cpu=6, threads=1, memory_max_bytes=3221225472, swap_bytes=0)))


def check(reg):
    require_idle()
    assert reg['schema'] == 'sii-contact-yield-targeted-fair-refit-handoff-v1'
    assert reg['recovery_execution_sha256'] == sha(RECOVERY/'execution.json')
    assert reg['recovery_registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert reg['dataset_sha256'] == sha(DATA/'data/training_data.npz')
    assert reg['metadata_sha256'] == sha(DATA/'data/DATA_COMPLETE.json')
    assert reg['registration_sha256'] == sha(DATA/'REGISTRATION.json')
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name


def run(root=TARGET):
    root = Path(root).resolve()
    check_resources()
    reg = read(root/'REGISTRATION.json')
    check(reg)
    state_path = root/'execution.json'
    assert not state_path.exists()
    state = dict(status='registered_not_dispatched', started_utc=now(),
                 registration_sha256=sha(root/'REGISTRATION.json'),
                 dataset_sha256=reg['dataset_sha256'], dispatch_attempted=False)
    write(state_path, state)

    def command(args):
        assert sha(root/'REGISTRATION.json') == state['registration_sha256']
        for name, digest in reg['source_sha256'].items():
            assert sha(ROOT/name) == digest, name
        with (root/'training.log').open('a') as stream:
            subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                           stdout=stream, stderr=subprocess.STDOUT, check=True)

    try:
        state.update(status='fair_refit_75_candidates', dispatch_attempted=True)
        state['dispatch_utc'] = now()
        write(state_path, state)
        command([ROOT/'tools/train_contact_yield_recovery_models_20261030.py',
                 '--root', DATA, '--run'])
        state.update(status='independent_fit_audit')
        write(state_path, state)
        command([ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py',
                 '--root', DATA, '--physics-source', ROOT, '--output', DATA/'FIT_AUDIT.json'])
        audit = read(DATA/'FIT_AUDIT.json')
        assert audit['status'] == 'passed' and len(audit['candidate_jobs']) == 75
        model_lock = read(DATA/'MODEL_LOCK.json')
        assert model_lock['status'] == 'frozen' and len(model_lock['models']) == 9
        state.update(status='complete_nine_refits_pending_fixed27_development_review',
                     model_lock_sha256=sha(DATA/'MODEL_LOCK.json'),
                     audit_sha256=sha(DATA/'FIT_AUDIT.json'), ended_utc=now())
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
