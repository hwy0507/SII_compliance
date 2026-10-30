"""Fair 75-fit ESN/RNN/MLP refit on the qualified early-rod dataset."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
from collect_contact_yield_scrape_scenes_20261030 import read,sha,write
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties

RECOVERY=ROOT/'outputs/contact_yield_mlp_rod_early_recovery_20261030_v1'
DATA=ROOT/'outputs/contact_yield_recovery_retrain_20261030_v6'
BASE=ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
TARGET=ROOT/'outputs/contact_yield_recovery_training_handoff_20261030_v7'
BLOCKING=('sii-contact-yield-recovery-20261030.service','sii-contact-yield-recovery-student-handoff-v1-20261030.service',
          'sii-contact-yield-student-diagnosis-handoff-20261030.service','sii-contact-yield-final108-handoff-20261030.service')
SOURCES=(Path(__file__).resolve(),ROOT/'experiments/build_contact_yield_mlp_rod_early_dataset_20261030.py',
         ROOT/'tools/train_contact_yield_recovery_models_20261030.py',ROOT/'tools/train_contact_yield_recovery_neural_20261030.py',
         ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py')
def now():return datetime.now(timezone.utc).isoformat()

def require_idle():
    for unit in BLOCKING:
        state=properties(unit);assert state['ActiveState']=='inactive' and state['MainPID']=='0',(unit,state)
    for unit in ('sii-contact-yield-targeted-refit-v4-20261030.scope','sii-contact-yield-targeted-diagnosis-v2-20261030.scope',
                 'sii-contact-yield-mlp-rod-early-recovery-20261030.scope'):
        state=properties(unit);assert state['ActiveState']=='inactive' and state.get('MainPID','0') in ('','0'),(unit,state)

def prepare(root=TARGET):
    root=Path(root).resolve();assert root==TARGET.resolve() and not root.exists();require_idle()
    recovery=read(RECOVERY/'execution.json');assert recovery['status']=='complete_four_recovery_probes_pending_shared_data_decision'
    assert recovery['registration_sha256']==sha(RECOVERY/'REGISTRATION.json') and len(recovery['rows'])==4
    assert [r['id'] for r in recovery['rows'] if r['qualified']]==['rod_mlp01_early_4p48s','rod_mlp01_early_4p60s']
    assert len([r for r in recovery['rows'] if not r['qualified']])==2
    meta=read(DATA/'data/DATA_COMPLETE.json');dataset=DATA/'data/training_data.npz'
    assert read(DATA/'execution.json')['status']=='dataset_complete' and sha(dataset)==meta['training_data_sha256']
    assert meta['schema']=='sii-vmc-special-scenes-recovery-augmented-v3' and meta['augmentation_round']==3
    assert meta['episodes']==38 and meta['qualified_episodes']==30 and meta['frames']==20500 and meta['augmented_recovery_episodes']==8
    assert meta['zero_weight_warmup_frames']==1707 and meta['teacher_supervised_recovery_frames']==3043
    assert read(BASE/'execution.json')['status']=='complete' and read(BASE/'MODEL_LOCK.json')['status']=='frozen'
    final=read(ROOT/'outputs/contact_yield_final108_handoff_20261030_v1/execution.json')
    assert final['dispatch_attempted'] is False and not (ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1').exists()
    root.mkdir(parents=True)
    write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-mlp-rod-early-refit-handoff-v3',registered_utc=now(),
        recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),recovery_execution_sha256=sha(RECOVERY/'execution.json'),
        parent_data=str(BASE),parent_model_lock_sha256=sha(BASE/'MODEL_LOCK.json'),training_data=str(DATA),dataset_sha256=sha(dataset),
        metadata_sha256=sha(DATA/'data/DATA_COMPLETE.json'),data_registration_sha256=sha(DATA/'REGISTRATION.json'),
        source_sha256={str(p.relative_to(ROOT)):sha(p) for p in SOURCES},maximum_fit_jobs=75,candidates_per_family_seed=12,
        seeds=[2026102801,2026102802,2026102803],neural_updates=32000,validation_scope='same six pure-teacher identities',
        dataset_contract=dict(schema='sii-vmc-special-scenes-recovery-augmented-v3',augmentation_round=3,episodes=38,train_episodes=32,validation_episodes=6,frames=20500,zero_weight_prefix_frames=1707,positive_weight_frames=18793),
        prior_failed_attempts=[
            dict(run_id='contact_yield_recovery_training_handoff_20261030_v5',status='failed_preserved_no_retry',reason='Trainer rejected v3 dataset schema before first fit.'),
            dict(run_id='contact_yield_recovery_training_handoff_20261030_v6',status='failed_preserved_no_retry',reason='Missing numpy alias in dataset contract check; no fit jobs started.'),
        ],
        no_test_selection=True,no_automatic_retry=True,resources=dict(cpu=6,threads=1,memory_max_bytes=3221225472,swap_bytes=0)))

def check(reg):
    require_idle();assert reg['schema']=='sii-contact-yield-mlp-rod-early-refit-handoff-v3'
    assert reg['recovery_registration_sha256']==sha(RECOVERY/'REGISTRATION.json') and reg['recovery_execution_sha256']==sha(RECOVERY/'execution.json')
    assert reg['dataset_sha256']==sha(DATA/'data/training_data.npz') and reg['metadata_sha256']==sha(DATA/'data/DATA_COMPLETE.json')
    assert reg['data_registration_sha256']==sha(DATA/'REGISTRATION.json')
    for n,h in reg['source_sha256'].items():assert sha(ROOT/n)==h,n

def run(root=TARGET):
    root=Path(root).resolve();check_resources();reg=read(root/'REGISTRATION.json');check(reg);state_path=root/'execution.json';assert not state_path.exists()
    state=dict(status='fair_refit_75_candidates',started_utc=now(),dispatch_attempted=True,registration_sha256=sha(root/'REGISTRATION.json'),dataset_sha256=reg['dataset_sha256']);write(state_path,state)
    def command(args):
        assert sha(root/'REGISTRATION.json')==state['registration_sha256']
        for n,h in reg['source_sha256'].items():assert sha(ROOT/n)==h,n
        with (root/'training.log').open('a') as stream:subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
    try:
        command([ROOT/'tools/train_contact_yield_recovery_models_20261030.py','--root',DATA,'--run'])
        state.update(status='independent_fit_audit');write(state_path,state)
        command([ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py','--root',DATA,'--physics-source',ROOT,'--output',DATA/'FIT_AUDIT.json'])
        audit=read(DATA/'FIT_AUDIT.json');lock=read(DATA/'MODEL_LOCK.json')
        assert audit['status']=='passed' and len(audit['candidate_jobs'])==75 and len(audit['frozen_actor_replays'])==9
        state.update(status='complete_nine_refits_pending_fixed27_development_review',model_lock_sha256=sha(DATA/'MODEL_LOCK.json'),audit_sha256=sha(DATA/'FIT_AUDIT.json'),ended_utc=now());write(state_path,state)
    except BaseException as exc:
        state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(state_path,state);raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=('prepare','run'));parser.add_argument('--root',type=Path,default=TARGET);args=parser.parse_args()
    (prepare if args.mode=='prepare' else run)(args.root.resolve())
