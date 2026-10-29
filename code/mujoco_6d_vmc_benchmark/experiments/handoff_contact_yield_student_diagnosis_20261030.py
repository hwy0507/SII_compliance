"""One finite owner waits for audited new fits, then runs fixed27 diagnosis."""
import argparse
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,sha,write
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
PARENT=ROOT/'outputs/contact_yield_scrape_training_handoff_20261030_v1'
COLLECTION=ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
TARGET=ROOT/'outputs/contact_yield_student_development_20261030_v1'
UNIT='sii-contact-yield-scrape-training-handoff-20261030.service'


def decision(state,active):
 if active in ('active','activating','deactivating','reloading'):return 'wait'
 if state['status']=='complete_nine_fits_pending_closed_loop_review' and active=='inactive':return 'ready'
 return 'parent_stopped_or_failed_no_dispatch'


def prepare(root):
 assert not root.exists() and not TARGET.exists()
 state=read(PARENT/'execution.json');assert state['status'] in ('waiting_for_collection','independent_review','fair_training','fit_audit')
 reg=read(PARENT/'REGISTRATION.json');assert reg['schema']=='sii-contact-yield-scrape-training-handoff-v1'
 sources=dict(reg['source_sha256'])
 for name in ('handoff_contact_yield_student_diagnosis_20261030.py','diagnose_contact_yield_students_20261030.py'):
  p=ROOT/'experiments'/name;sources[str(p.relative_to(ROOT))]=sha(p)
 for name,digest in sources.items():assert sha(ROOT/name)==digest,name
 root.mkdir();write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-fixed27-handoff-v1',registered_utc=now(),parent=str(PARENT),parent_unit=UNIT,parent_registration_sha256=sha(PARENT/'REGISTRATION.json'),target=str(TARGET),source_sha256=sources,maximum_wait_seconds=86400,no_final_test=True,no_reselection=True,no_retry=True,resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0)))


def run(root):
 check_resources();reg=read(root/'REGISTRATION.json');assert not (root/'execution.json').exists()
 state=dict(status='waiting_for_audited_fits',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),dispatch_attempted=False);write(root/'execution.json',state)
 def check():
  assert sha(root/'REGISTRATION.json')==state['registration_sha256']
  assert sha(PARENT/'REGISTRATION.json')==reg['parent_registration_sha256']
  assert reg['target']==str(TARGET) and reg['parent']==str(PARENT) and reg['parent_unit']==UNIT
  for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 deadline=time.monotonic()+reg['maximum_wait_seconds']
 try:
  while True:
   check();choice=decision(read(PARENT/'execution.json'),properties(UNIT)['ActiveState'])
   if choice!='wait':break
   if (root/'STOP_REQUESTED').exists():choice='stopped_before_dispatch';break
   if time.monotonic()>deadline:choice='finite_wait_timeout_no_dispatch';break
   time.sleep(20)
  if choice!='ready':
   state.update(status=choice,ended_utc=now());write(root/'execution.json',state);return
  assert not TARGET.exists();check()
  with (root/'diagnosis.log').open('x') as log:
   for mode in ('prepare','run','review'):
    check();state.update(status='diagnosis_'+mode,dispatch_attempted=mode!='prepare');write(root/'execution.json',state)
    args=[sys.executable,str(ROOT/'experiments/diagnose_contact_yield_students_20261030.py'),mode,'--root',str(TARGET)]
    if mode=='review':args.extend(['--output',str(TARGET/'REVIEW.json')])
    subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
  report=read(TARGET/'REVIEW.json');assert report['status']=='verified_fixed27_development_diagnosis'
  state.update(status='fixed27_verified_pending_final_registration' if not report['failed_ids'] else 'fixed27_scientific_failures_preserved_require_repair',review_sha256=sha(TARGET/'REVIEW.json'),failed_ids=report['failed_ids'],ended_utc=now());write(root/'execution.json',state)
 except BaseException as exc:
  state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(root/'execution.json',state);raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 prepare(a.root.resolve()) if a.prepare else run(a.root.resolve())
