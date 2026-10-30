"""New-model provenance adapter for the unchanged frozen unseen108 evaluator.

Only register after nine frozen fits and all27 train-only closures pass.
The original physical dispatch, per-row metrics, replay and full108 review
remain unchanged. No final-test data is read until explicit registration.
"""
import argparse
from pathlib import Path
import os
import sys
import mujoco
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
import run_v9_unseen_matrix_20261030 as evaluator
import diagnose_contact_yield_students_20261030 as development
from collect_special_scene_actions_20261028 import read,sha,write
from diagnose_special_scene_regression_20261028 import now
DEVELOPMENT=ROOT/'outputs/contact_yield_student_development_20261030_v1'
TRAINING=development.TRAINING
COLLECTION=development.COLLECTION


def gate(report,models):
 assert report['status']=='verified_fixed27_development_diagnosis'
 assert report['no_model_reselection'] and report['no_final_test_performed']
 assert len(report['rows'])==len(report['independent_replays'])==27
 expected={(m['name'],s+'_00') for m in models for s in ('rod','ball','corner')}
 assert len(models)==9 and len(expected)==27
 assert {(r['method'],r['condition']) for r in report['rows']}==expected
 assert all(r['task_success'] and r['strict_success'] and r['machine_compliant'] for r in report['rows'])
 assert all(r['actor_replay_max_abs']==r['filter_replay_max_abs']==0 for r in report['independent_replays'])
 assert report['task_successes']==report['strict_successes']==27 and report['failed_ids']==[]


def prerequisite():
 lock=development.prerequisites()
 reg=read(DEVELOPMENT/'REGISTRATION.json');development.check(reg)
 assert reg['models']==lock['models']
 state=read(DEVELOPMENT/'execution.json');report=read(DEVELOPMENT/'REVIEW.json')
 assert state['status']=='complete_development_diagnosis_pending_review'
 assert report['registration_sha256']==sha(DEVELOPMENT/'REGISTRATION.json')
 assert report['execution_sha256']==sha(DEVELOPMENT/'execution.json')
 assert report['reviewer_sha256']==sha(Path(development.__file__))
 gate(report,lock['models'])
 return lock


def register(root):
 assert root.parent==ROOT/'outputs' and not root.exists()
 lock=prerequisite() # Refuse before opening the sealed condition file.
 assert sha(evaluator.CONDITIONS)==evaluator.CONDITIONS_SHA
 contract=read(evaluator.CONDITIONS)
 for name,digest in contract['frozen_sources'].items():assert sha(evaluator.REPO/name)==digest,name
 for model in lock['models']:
  for key in ('checkpoint','metadata'):assert sha(Path(model[key]))==model[key+'_sha256']
 cases=evaluator.make_cases(lock['models'],contract['conditions'])
 sources={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')}
 for path in (Path(__file__),Path(development.__file__)):sources[str(path.relative_to(ROOT))]=sha(path)
 reg=dict(schema='sii-contact-yield-frozen-unseen108-v1',registered_utc=now(),conditions_path=str(evaluator.CONDITIONS),conditions_sha256=evaluator.CONDITIONS_SHA,metric_contract=contract,models=lock['models'],cases=cases,maximum_episodes=108,teacher_config=str(COLLECTION/'teacher.json'),teacher_config_sha256=sha(COLLECTION/'teacher.json'),source_sha256=sources,recipe_config_sha256={n:sha(ROOT/n) for n in ('configs/ball_source_demo.json','configs/workstation_source_demo.json')},python=os.path.abspath(sys.executable),runtime_versions=dict(python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__),resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),development_files={n:sha(DEVELOPMENT/n) for n in ('REGISTRATION.json','execution.json','REVIEW.json')},training_files={n:sha(TRAINING/n) for n in ('MODEL_LOCK.json','FIT_AUDIT.json','execution.json','data/training_data.npz')},failure_policy='Run once; preserve all failed/incomplete cells. No test-based tuning or fallback models. Original Task/Strict, sampled hold, dual-pass SPT, torque, comfort NA/proxy and compliance unchanged.',scope='New-model adapter only; unchanged frozen 12 isolated conditions, 9 models and original full108 metrics/review.')
 root.mkdir();write(root/'REGISTRATION.json',reg)


def check(reg):
 lock=prerequisite()
 assert reg['schema']=='sii-contact-yield-frozen-unseen108-v1'
 assert reg['models']==lock['models']
 assert sha(evaluator.CONDITIONS)==reg['conditions_sha256']==evaluator.CONDITIONS_SHA
 assert read(evaluator.CONDITIONS)==reg['metric_contract']
 for name,digest in reg['metric_contract']['frozen_sources'].items():assert sha(evaluator.REPO/name)==digest,name
 assert reg['cases']==evaluator.make_cases(reg['models'],reg['metric_contract']['conditions']) and reg['maximum_episodes']==108
 assert reg['python']==os.path.abspath(sys.executable)
 assert reg['runtime_versions']==dict(python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__)
 assert reg['resources']==dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0)
 for base,key in ((DEVELOPMENT,'development_files'),(TRAINING,'training_files')):
  for name,digest in reg[key].items():assert sha(base/name)==digest,name
 for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 for name,digest in reg['recipe_config_sha256'].items():assert sha(ROOT/name)==digest,name
 assert reg['teacher_config']==str(COLLECTION/'teacher.json') and sha(Path(reg['teacher_config']))==reg['teacher_config_sha256']
 for model in reg['models']:
  for key in ('checkpoint','metadata'):assert sha(Path(model[key]))==model[key+'_sha256']


def run(root):
 # Explicit provenance substitution only. The reused evaluator functions use
 # their unchanged physical worker, metrics, pairing and failure handling.
 original=evaluator.check_registration;evaluator.check_registration=check
 try:evaluator.run(root)
 finally:evaluator.check_registration=original


def review(root,output):
 original=evaluator.check_registration;evaluator.check_registration=check
 try:evaluator.review(root,output)
 finally:evaluator.check_registration=original

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('register','run','review'));p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
 if a.mode=='register':register(a.root.resolve())
 elif a.mode=='run':run(a.root.resolve())
 else:
  assert a.output is not None;review(a.root.resolve(),a.output.resolve())
