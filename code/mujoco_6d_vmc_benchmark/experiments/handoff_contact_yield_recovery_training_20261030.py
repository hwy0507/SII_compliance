"""Build the fixed recovery-augmented dataset, fit 75 candidates, and audit."""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
from collect_contact_yield_scrape_scenes_20261030 import sha,read,write
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
RECOVERY=ROOT/'outputs/contact_yield_recovery_development_20261030_v1'
BASE=ROOT/'outputs/contact_yield_scrape_retrain_20261030_v1'
TRAINING=ROOT/'outputs/contact_yield_recovery_retrain_20261030_v3'
UNIT='sii-contact-yield-recovery-20261030.service'
SOURCES=[Path(__file__),ROOT/'experiments/build_contact_yield_recovery_dataset_20261030.py',
 ROOT/'tools/train_contact_yield_recovery_models_20261030.py',ROOT/'tools/train_contact_yield_recovery_neural_20261030.py',
 ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py']

def now():return datetime.now(timezone.utc).isoformat()

def prepare(root):
 assert not root.exists() and TRAINING.exists()
 assert read(RECOVERY/'execution.json')['status']=='complete_four_recovery_probes_pending_shared_data_decision'
 assert all(r['qualified'] for r in read(RECOVERY/'execution.json')['rows'])
 assert read(BASE/'execution.json')['status']=='complete' and read(BASE/'FIT_AUDIT.json')['status']=='passed'
 assert read(TRAINING/'execution.json')['status']=='dataset_complete'
 assert read(TRAINING/'execution.json')['dataset_sha256']==sha(TRAINING/'data/training_data.npz')
 assert all(properties(u)['ActiveState']=='inactive' and properties(u)['MainPID']=='0' for u in
   (UNIT,'sii-contact-yield-recovery-20261030.service','sii-contact-yield-student-diagnosis-handoff-20261030.service','sii-contact-yield-final108-handoff-20261030.service'))
 reg=read(RECOVERY/'REGISTRATION.json')
 for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 root.mkdir(parents=True)
 write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-recovery-training-handoff-v1',registered_utc=now(),
  recovery=str(RECOVERY),recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
  recovery_execution_sha256=sha(RECOVERY/'execution.json'),base=str(BASE),base_lock_sha256=sha(BASE/'MODEL_LOCK.json'),
  training=str(TRAINING),dataset_sha256=sha(TRAINING/'data/training_data.npz'),metadata_sha256=sha(TRAINING/'data/DATA_COMPLETE.json'),
  source_sha256={str(p.relative_to(ROOT)):sha(p) for p in SOURCES},maximum_fit_jobs=75,
  no_test_selection=True,no_automatic_retry=True,resources=dict(cpu=6,threads=1,memory_max_bytes=3221225472,swap_bytes=0)))

def run(root):
 check_resources();reg=read(root/'REGISTRATION.json');assert not (root/'execution.json').exists()
 assert sha(RECOVERY/'REGISTRATION.json')==reg['recovery_registration_sha256']
 assert sha(RECOVERY/'execution.json')==reg['recovery_execution_sha256']
 assert sha(BASE/'MODEL_LOCK.json')==reg['base_lock_sha256']
 for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 assert all(properties(u)['ActiveState']=='inactive' and properties(u)['MainPID']=='0' for u in
   ('sii-contact-yield-recovery-20261030.service','sii-contact-yield-student-diagnosis-handoff-20261030.service','sii-contact-yield-final108-handoff-20261030.service'))
 assert read(TRAINING/'execution.json')['status']=='dataset_complete'
 assert sha(TRAINING/'data/training_data.npz')==reg['dataset_sha256']
 assert sha(TRAINING/'data/DATA_COMPLETE.json')==reg['metadata_sha256']
 state=dict(status='recovery_dataset_verified',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),dispatch_attempted=False,dataset_sha256=reg['dataset_sha256'])
 state_path=root/'execution.json';write(state_path,state);log=root/'training.log'
 def command(args):
  assert sha(root/'REGISTRATION.json')==state['registration_sha256']
  for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
  with log.open('a') as stream:subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)
 try:
  # Builder is read-only with respect to physics but shares the global lock;
  # release it before the fitting coordinator acquires it itself.
  data=read(TRAINING/'data/DATA_COMPLETE.json')
  assert data['augmented_recovery_episodes']==4 and data['zero_weight_warmup_frames']==1175
  state.update(status='fair_refit_75_candidates',dispatch_attempted=True);write(state_path,state)
  command([ROOT/'tools/train_contact_yield_recovery_models_20261030.py','--root',TRAINING,'--run'])
  state.update(status='independent_fit_audit');write(state_path,state)
  command([ROOT/'tools/audit_contact_yield_recovery_fits_20261030.py','--root',TRAINING,'--physics-source',ROOT,'--output',TRAINING/'FIT_AUDIT.json'])
  audit=read(TRAINING/'FIT_AUDIT.json');assert audit['status']=='passed' and len(audit['candidate_jobs'])==75
  assert read(TRAINING/'execution.json')['status']=='complete'
  state.update(status='complete_nine_refits_pending_fixed_development_review',model_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),audit_sha256=sha(TRAINING/'FIT_AUDIT.json'),ended_utc=now());write(state_path,state)
 except BaseException as exc:
  state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(state_path,state);raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
 (prepare if a.mode=='prepare' else run)(a.root.resolve())
