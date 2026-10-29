"""Finite no-retry handoff: complete collection -> independent review -> fair fits."""
import argparse
import fcntl
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]
from collect_special_scene_actions_20261028 import read,sha,write
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
COLLECTION=ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
TRAINING=ROOT/'outputs/contact_yield_scrape_retrain_20261030_v1'
UNIT='sii-contact-yield-scrape-collection-20261030.service'
SOURCES=['experiments/'+n for n in ('handoff_contact_yield_scrape_training_20261030.py','collect_contact_yield_scrape_scenes_20261030.py','review_contact_yield_scrape_collection_20261030.py','build_contact_yield_scrape_training_data_20261030.py')]+['tools/'+n for n in ('train_special_scene_models_20261028.py','audit_special_scene_fits_20261028.py')]


def decision(state,active):
 status=state['status']
 if active in ('active','activating','deactivating','reloading'):return 'wait'
 if status=='all30_qualified_pending_independent_dataset_review':
  assert len(state['rows'])==30 and len({r['id'] for r in state['rows']})==30
  assert all(r['qualified'] for r in state['rows'])
  return 'review_build_fit'
 if status=='complete_with_scientific_failures_preserved_no_dataset':return 'scientific_failure_preserved_no_fit'
 return 'incomplete_or_infrastructure_failure_no_fit'


def prepare(root):
 assert not root.exists() and not TRAINING.exists()
 reg=read(COLLECTION/'REGISTRATION.json');assert reg['schema']=='sii-contact-yield-scrape-three-scenes-collection-v1'
 assert read(COLLECTION/'execution.json')['status']=='running_fixed_teacher_collection'
 root.mkdir(parents=True)
 write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-scrape-training-handoff-v1',registered_utc=now(),collection=str(COLLECTION),training=str(TRAINING),collection_unit=UNIT,collection_registration_sha256=sha(COLLECTION/'REGISTRATION.json'),source_sha256={**reg['source_sha256'],**{n:sha(ROOT/n) for n in SOURCES}},maximum_wait_seconds=7200,maximum_fit_jobs=75,no_unseen_test=True,no_automatic_retry=True,resources=dict(cpu=6,simulators=0,threads=1,memory_max_bytes=3221225472,swap_bytes=0)))


def run(root):
 check_resources();reg=read(root/'REGISTRATION.json')
 assert not (root/'execution.json').exists()
 state=dict(status='waiting_for_collection',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),dispatch_attempted=False)
 write(root/'execution.json',state);start=time.monotonic()
 def check():
  assert sha(root/'REGISTRATION.json')==state['registration_sha256']
  assert sha(COLLECTION/'REGISTRATION.json')==reg['collection_registration_sha256']
  for n,d in reg['source_sha256'].items():assert sha(ROOT/n)==d,n
 try:
  while True:
   check();d=decision(read(COLLECTION/'execution.json'),properties(UNIT)['ActiveState'])
   if d!='wait':break
   if (root/'STOP_REQUESTED').exists():d='stopped_before_dispatch';break
   if time.monotonic()-start>reg['maximum_wait_seconds']:d='wait_timeout_no_dispatch';break
   time.sleep(20)
  if d!='review_build_fit':
   state.update(status=d,ended_utc=now());write(root/'execution.json',state);return
  assert not TRAINING.exists()
  check();state.update(status='independent_review',dispatch_attempted=True);write(root/'execution.json',state)
  with (root/'handoff.log').open('x') as log:
   def command(args):
    check();subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
   # The only shared compute lock is held by this builder and released before
   # the trainer independently acquires it. No physics runs in this handoff.
   with (ROOT/'outputs/.local-rl-compute.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    command([ROOT/'experiments/review_contact_yield_scrape_collection_20261030.py','--root',COLLECTION,'--output',COLLECTION/'COLLECTION_REVIEW.json'])
    assert read(COLLECTION/'COLLECTION_REVIEW.json')['status']=='verified_all30_qualified'
    command([ROOT/'experiments/build_contact_yield_scrape_training_data_20261030.py','--collection',COLLECTION,'--output',TRAINING])
   state.update(status='fair_training',dataset_sha256=sha(TRAINING/'data/training_data.npz'));write(root/'execution.json',state)
   command([ROOT/'tools/train_special_scene_models_20261028.py','--root',TRAINING,'--run'])
   state.update(status='fit_audit');write(root/'execution.json',state)
   command([ROOT/'tools/audit_special_scene_fits_20261028.py','--root',TRAINING,'--physics-source',ROOT,'--output',TRAINING/'FIT_AUDIT.json'])
  assert read(TRAINING/'execution.json')['status']=='complete' and read(TRAINING/'FIT_AUDIT.json')['status']=='passed'
  state.update(status='complete_nine_fits_pending_closed_loop_review',model_lock_sha256=sha(TRAINING/'MODEL_LOCK.json'),ended_utc=now());write(root/'execution.json',state)
 except BaseException as exc:
  state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(root/'execution.json',state);raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 prepare(a.root.resolve()) if a.prepare else run(a.root.resolve())
