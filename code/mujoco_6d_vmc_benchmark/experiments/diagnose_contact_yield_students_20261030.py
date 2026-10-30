"""Fixed nine-model, three-train-identity closure diagnosis; no reselection.

Uses the existing physical worker, per-episode metrics and independent replay.
Never reads unseen conditions. All 27 outcomes remain, including failures.
"""
import argparse
import copy
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import mujoco
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,write,sha
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
from audit_special_scene_metrics_v2_20261030 import episode
# Importing this module only defines paths/functions. Do not call its register,
# check_registration, run or review: those bind the historical selection/test.
from run_v9_unseen_matrix_20261030 import run_case,case_folder,replay,check_episode
COLLECTION=ROOT/'outputs/contact_yield_scrape_collection_20261030_v1'
TRAINING=ROOT/'outputs/contact_yield_scrape_retrain_20261030_v1'
HANDOFF=ROOT/'outputs/contact_yield_scrape_training_handoff_20261030_v1'
UNITS=('sii-contact-yield-scrape-collection-20261030.service',
       'sii-contact-yield-scrape-training-handoff-20261030.service')
FAMILIES=('esn_ridge','rnn_scratch','mlp_scratch')
SEEDS=(2026102801,2026102802,2026102803)


def make_cases(models,references):
 assert len(models)==9 and {(m['family'],m['seed']) for m in models}=={(f,s) for f in FAMILIES for s in SEEDS}
 assert len({m['name'] for m in models})==9
 assert len(references)==3 and {r['id'] for r in references}=={'rod_00','ball_00','corner_00'}
 assert all(r['split']=='train' and r['id']==r['scene']+'_00' for r in references)
 cases=[]
 for reference in references:
  for model in models:
   condition={k:copy.deepcopy(reference[k]) for k in ('id','scene','seed','parameters')}
   cases.append(dict(id=reference['id']+'__'+model['name'],condition=condition,model=copy.deepcopy(model),teacher_reference=copy.deepcopy(reference),expected_duration_s={'rod':20.,'ball':30.,'corner':13.}[reference['scene']]))
 assert len(cases)==27 and len({c['id'] for c in cases})==27
 return cases


def prerequisites():
 assert all(properties(u)['ActiveState']=='inactive' for u in UNITS)
 assert read(HANDOFF/'execution.json')['status']=='complete_nine_fits_pending_closed_loop_review'
 state=read(TRAINING/'execution.json');lock=read(TRAINING/'MODEL_LOCK.json');audit=read(TRAINING/'FIT_AUDIT.json')
 assert state['status']=='complete' and lock['status']=='frozen' and audit['status']=='passed'
 assert audit['model_lock_sha256']==state['model_lock_sha256']==sha(TRAINING/'MODEL_LOCK.json')
 assert audit['dataset_sha256']==lock['training_data_sha256']==sha(TRAINING/'data/training_data.npz')
 assert len(audit['candidate_jobs'])==75 and len(audit['frozen_actor_replays'])==9
 assert read(COLLECTION/'COLLECTION_REVIEW.json')['status']=='verified_all30_qualified'
 return lock


def prepare(root):
 assert not root.exists();lock=prerequisites()
 collection=read(COLLECTION/'REGISTRATION.json');state=read(COLLECTION/'execution.json')
 references=[]
 for scene in ('rod','ball','corner'):
  case=next(c for c in collection['cases'] if c['id']==scene+'_00')
  receipt=next(r for r in state['rows'] if r['id']==case['id']);assert receipt['qualified']
  folder=Path(receipt['folder'])
  references.append(dict(id=case['id'],scene=scene,split='train',seed=case['seed'],parameters=case['parameters'],folder=str(folder),hashes={n:sha(folder/n) for n in ('execution.json','trajectory.npz','DEMONSTRATION_QUALIFICATION.json')},model_sha256=read(folder/'execution.json')['model_sha256']))
 cases=make_cases(lock['models'],references)
 sources={str(p.relative_to(ROOT)):sha(p) for name in ('scripts','tools') for p in (ROOT/name).glob('*.py')}
 sources[str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
 root.mkdir(parents=True)
 write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-student-development-diagnosis-v1',registered_utc=now(),models=lock['models'],references=references,cases=cases,maximum_episodes=27,teacher_config=str(COLLECTION/'teacher.json'),teacher_config_sha256=collection['teacher_config_sha256'],training_files={n:sha(TRAINING/n) for n in ('execution.json','MODEL_LOCK.json','FIT_AUDIT.json','data/training_data.npz','data/DATA_COMPLETE.json')},collection_files={n:sha(COLLECTION/n) for n in ('REGISTRATION.json','execution.json','COLLECTION_REVIEW.json')},source_sha256=sources,python=os.path.abspath(sys.executable),runtime_versions=dict(python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__),resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),selection='Fixed nine validation-MSE models. This diagnosis never replaces/checkpoint-selects models. No unseen inputs or test-based tuning.',failure_policy='Preserve all readable scientific failures and run all 27. Infrastructure exception stops with current identity; no automatic retries. No SPT reference/ranking from development rows.'))


def check(reg):
 prerequisites()
 assert reg['schema']=='sii-contact-yield-student-development-diagnosis-v1'
 assert reg['cases']==make_cases(reg['models'],reg['references'])
 assert reg['models']==read(TRAINING/'MODEL_LOCK.json')['models']
 assert len(reg['cases'])==reg['maximum_episodes']==27
 assert reg['python']==os.path.abspath(sys.executable)
 assert reg['runtime_versions']==dict(python=sys.version,numpy=np.__version__,mujoco=mujoco.__version__)
 for base,key in ((TRAINING,'training_files'),(COLLECTION,'collection_files')):
  for name,digest in reg[key].items():assert sha(base/name)==digest,name
 for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 assert sha(Path(reg['teacher_config']))==reg['teacher_config_sha256']
 for model in reg['models']:
  for key in ('checkpoint','metadata'):assert sha(Path(model[key]))==model[key+'_sha256']
 for ref in reg['references']:
  for name,digest in ref['hashes'].items():assert sha(Path(ref['folder'])/name)==digest


def teacher_pairing(pairing,case):
 ref=case['teacher_reference'];folder=Path(ref['folder']);e=read(folder/'execution.json')
 assert pairing['model_sha256']==ref['model_sha256']
 assert pairing['filter_config']==e['filter_config']
 with np.load(folder/'trajectory.npz',allow_pickle=False) as z:np.testing.assert_array_equal(pairing['initial_observation'],z['observation'][0])


def run(root):
 check_resources();reg=read(root/'REGISTRATION.json');check(reg)
 assert not (root/'execution.json').exists(),'Preserve previous attempts'
 with (ROOT/'outputs/.contact-yield-student-diagnosis.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  with (ROOT/'outputs/.local-rl-compute.lock').open('a') as physics:fcntl.flock(physics,fcntl.LOCK_EX|fcntl.LOCK_NB)
  state=dict(status='running_fixed_student_development_diagnosis',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),rows=[]);write(root/'execution.json',state)
  try:
   for case in reg['cases']:
    check(reg);assert sha(root/'REGISTRATION.json')==state['registration_sha256']
    if (root/'STOP_REQUESTED').exists():
     state.update(status='stopped_at_episode_boundary',ended_utc=now());return
    state['current']=case['id'];write(root/'execution.json',state)
    result=run_case(root,case,reg);teacher_pairing(result['pairing'],case)
    state['rows'].append(result);write(root/'execution.json',state)
   state.update(status='complete_development_diagnosis_pending_review',ended_utc=now())
  except BaseException as exc:
   state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());raise
  finally:write(root/'execution.json',state)


def review(root,output):
 assert not output.exists();reg=read(root/'REGISTRATION.json');check(reg)
 before=(root/'execution.json').read_bytes();state=read(root/'execution.json')
 assert state['status']=='complete_development_diagnosis_pending_review'
 assert state['registration_sha256']==sha(root/'REGISTRATION.json')
 assert [r['id'] for r in state['rows']]==[c['id'] for c in reg['cases']]
 assert len(state['rows'])==27
 rows=[];replays=[]
 for case,receipt in zip(reg['cases'],state['rows']):
  folder=case_folder(root,case);assert receipt['folder']==str(folder)
  pairing=check_episode(folder,case,reg);assert pairing==receipt['pairing'];teacher_pairing(pairing,case)
  replays.append(dict(id=case['id'],**replay(folder)))
  row=episode(folder,case['model']['name'],case['condition']['id'],case['expected_duration_s'])
  assert sha(folder.parent/'METRICS.json')==receipt['metrics_sha256'] and row==read(folder.parent/'METRICS.json')
  rows.append(row)
 assert (root/'execution.json').read_bytes()==before;check(reg)
 write(output,dict(status='verified_fixed27_development_diagnosis',registration_sha256=sha(root/'REGISTRATION.json'),execution_sha256=sha(root/'execution.json'),reviewer_sha256=sha(Path(__file__)),rows=rows,independent_replays=replays,task_successes=sum(r['task_success'] for r in rows),strict_successes=sum(r['strict_success'] for r in rows),failed_ids=[state['rows'][i]['id'] for i,r in enumerate(rows) if not(r['task_success'] and r['strict_success'])],no_model_reselection=True,no_final_test_performed=True,scope='Three train00 identities only. No SPT, final ranking, or unseen-generalization claim. All scientific failures preserved.'))

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','run','review'));p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path);a=p.parse_args()
 if a.mode=='prepare':prepare(a.root.resolve())
 elif a.mode=='run':run(a.root.resolve())
 else:
  assert a.output is not None;review(a.root.resolve(),a.output.resolve())
