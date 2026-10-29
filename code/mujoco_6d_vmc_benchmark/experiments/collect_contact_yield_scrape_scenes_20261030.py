"""Collect 30 balanced identities with the contact-yield-gated scrape teacher.

Reuse exactly three qualified same-config rod probes; execute the remaining
27 once. Preserve every scientific failure and prohibit dataset construction
until all 30 pass. No test data or fitting in this coordinator.
"""
import argparse,fcntl,json,os,subprocess,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,write,sha
from diagnose_special_scene_regression_20261028 import now
from select_v9_closed_loop_candidates_v3_20261029 import check_resources,properties
from review_v9_paired_scene_closure_20261029 import verify_qualification
PARENT=ROOT/'outputs/vertical_stage_scrape_probe_20261030_v1'
ORIGINAL=ROOT/'outputs/special_scene_vertical_aware_collection_20261030_v2'
UNIT='sii-vertical-stage-scrape-probe-20261030.service'
REVIEW=ROOT.parents[1]/'docs/evidence/nonrl_v9_candidate_catalogue_20261029/VERTICAL_STAGE_SCRAPE_TEACHER_PROBES_20261030.json'
REVIEWER=ROOT/'tools/review_vertical_stage_scrape_probe_campaign_20261030.py'


def prerequisites():
 p=properties(UNIT);assert p['ActiveState']=='inactive' and p['MainPID']=='0'
 from review_vertical_stage_scrape_probe_campaign_20261030 import review
 r=review(PARENT);assert r['qualified']==3 and not r['failures']
 report=read(REVIEW)['contact_yield_gated_probe']
 assert report['registration_sha256']==sha(PARENT/'REGISTRATION.json')
 assert report['execution_sha256']==sha(PARENT/'execution.json')
 assert report['teacher_config_sha256']==sha(PARENT/'teacher.json')
 old=read(ORIGINAL/'execution.json')
 assert old['status']=='complete_with_scientific_failures_preserved_no_dataset'
 assert len(old['rows'])==30 and sum(x['qualified'] for x in old['rows'])==29
 assert not (ROOT/'outputs/nonrl_v9_isolated_unseen_108_20261030_v1').exists()


def prepare(root):
 assert not root.exists();prerequisites()
 old=read(ORIGINAL/'REGISTRATION.json');state=read(ORIGINAL/'execution.json')
 probes=read(PARENT/'execution.json');cfg=read(PARENT/'teacher.json')
 assert cfg['contact_yield_progress']['version']=='contact_yield_then_bounded_path_progress_v1'
 cases=[]
 for case,row in zip(old['cases'],state['rows']):
  assert case['id']==row['id']
  ref=Path(row['folder']);q=verify_qualification(ref,row['qualification_sha256'])
  assert (q['status']=='qualified')==row['qualified']
  reuse_row=next((r for r in probes['rows'] if r['id']==case['id']),None)
  reuse=Path(reuse_row['folder']) if reuse_row else None
  if reuse:
   pc=next(c for c in read(PARENT/'REGISTRATION.json')['cases'] if c['id']==case['id'])
   assert all(pc[k]==case[k] for k in ('scene','split','seed','parameters'))
   assert read(reuse/'HANDOFF_REVIEW.json')['qualified']
  cases.append(dict(id=case['id'],scene=case['scene'],split=case['split'],seed=case['seed'],parameters=case['parameters'],reference=str(ref),reference_execution_sha256=sha(ref/'execution.json'),reference_qualification_sha256=sha(ref/'DEMONSTRATION_QUALIFICATION.json'),model_sha256=read(ref/'execution.json')['model_sha256'],reuse=str(reuse) if reuse else None,reuse_review_sha256=sha(reuse/'HANDOFF_REVIEW.json') if reuse else None,reuse_qualification_sha256=sha(reuse/'DEMONSTRATION_QUALIFICATION.json') if reuse else None))
 assert len(cases)==30 and sum(bool(c['reuse']) for c in cases)==3
 assert {(s,p):sum(c['scene']==s and c['split']==p for c in cases) for s in ('rod','ball','corner') for p in ('train','validation')}=={(s,p):n for s in ('rod','ball','corner') for p,n in [('train',8),('validation',2)]}
 root.mkdir(parents=True);write(root/'teacher.json',cfg)
 write(root/'REGISTRATION.json',dict(schema='sii-contact-yield-scrape-three-scenes-collection-v1',registered_utc=now(),parent_directory=str(PARENT),parent_unit=UNIT,parent_review=str(REVIEW),parent_reviewer=str(REVIEWER),cases=cases,maximum_new_physical_episodes=27,maximum_pure_episodes=30,seeds=[2026102801,2026102802,2026102803],intended_common_candidates_per_family_seed=12,teacher_config_sha256=sha(root/'teacher.json'),candidate=old['candidate'],parent_review_sha256=sha(REVIEW),parent_execution_sha256=sha(PARENT/'execution.json'),original_registration_sha256=sha(ORIGINAL/'REGISTRATION.json'),original_execution_sha256=sha(ORIGINAL/'execution.json'),source_sha256={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')},coordinator_sha256=sha(Path(__file__)),augmentation_candidates=[],resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),no_unseen_or_fitting=True,selection_note='Teacher tuned on development identities, including validation rod09. These six identities are development validation only, not unbiased generalization evidence. Final unseen108 stays sealed.'))

def check(root,reg):
 assert str(PARENT)==reg['parent_directory'] and UNIT==reg['parent_unit'] and str(REVIEW)==reg['parent_review'] and str(REVIEWER)==reg['parent_reviewer']
 assert sha(Path(__file__))==reg['coordinator_sha256']
 assert sha(root/'teacher.json')==reg['teacher_config_sha256']
 assert sha(REVIEW)==reg['parent_review_sha256'] and sha(PARENT/'execution.json')==reg['parent_execution_sha256']
 assert sha(ORIGINAL/'REGISTRATION.json')==reg['original_registration_sha256']
 assert sha(ORIGINAL/'execution.json')==reg['original_execution_sha256']
 for n,d in reg['source_sha256'].items():assert sha(ROOT/n)==d,n
 c=reg['candidate'];assert sha(Path(c['checkpoint']))==c['checkpoint_sha256'] and sha(Path(c['metadata']))==c['metadata_sha256']
 for c in reg['cases']:
  f=Path(c['reference']);assert sha(f/'execution.json')==c['reference_execution_sha256'] and sha(f/'DEMONSTRATION_QUALIFICATION.json')==c['reference_qualification_sha256']
  if c['reuse']:
   f=Path(c['reuse']);assert sha(f/'HANDOFF_REVIEW.json')==c['reuse_review_sha256'] and sha(f/'DEMONSTRATION_QUALIFICATION.json')==c['reuse_qualification_sha256']
 for a in reg['augmentation_candidates']:
  f=Path(a['folder']);assert sha(f/'HANDOFF_REVIEW.json')==a['review_sha256'] and sha(f/'DEMONSTRATION_QUALIFICATION.json')==a['qualification_sha256']

def run(root):
 check_resources();prerequisites();reg=read(root/'REGISTRATION.json');check(root,reg)
 assert not (root/'execution.json').exists(),'Never repeat an existing/incomplete collection'
 lock=(ROOT/'outputs/.local-rl-compute.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 state=dict(status='running_fixed_teacher_collection',started_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),rows=[])
 write(root/'execution.json',state)
 try:
  for case in reg['cases']:
   check(root,reg);assert sha(root/'REGISTRATION.json')==state['registration_sha256']
   if (root/'STOP_REQUESTED').exists():
    state.update(status='stopped_at_episode_boundary',ended_utc=now());write(root/'execution.json',state);return
   state['current']=case['id'];write(root/'execution.json',state)
   if case['reuse']:folder=Path(case['reuse'])
   else:
    out=root/case['id'];folder=out/case['scene']
    env={k:v for k,v in os.environ.items() if k in {'PATH','HOME','USER','LANG','LD_LIBRARY_PATH','MUJOCO_GL','TMPDIR'}}
    env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONPATH=str(ROOT/'scripts')+':'+str(ROOT/'tools'),MUJOCO_MENAGERIE_PATH=str(ROOT/'outputs/baseline_local_rl_20261009/runtime/menagerie'),VMC_TEACHER_CONFIG=str(root/'teacher.json'),VMC_SCENE_SEED=str(case['seed']),VMC_STUDENT_CHECKPOINT=reg['candidate']['checkpoint'])
    env.update({k:str(v) for k,v in case['parameters'].items()})
    with (root/(case['id']+'.log')).open('x') as log:
     subprocess.run([sys.executable,str(ROOT/'tools/run_vertical_stage_scrape_probe_20261030.py'),'--output',str(out),'--scene',case['scene'],'--student-steps','0'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
     subprocess.run([sys.executable,str(ROOT/'tools/audit_vertical_stage_scrape_probe_20261030.py'),str(folder)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
   h=read(folder/'HANDOFF_EXECUTION.json');e=read(folder/'execution.json');r=read(folder/'HANDOFF_REVIEW.json')
   q=verify_qualification(folder,sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
   assert h['student_steps']==0 and h['source_stable'] and e['status']=='complete'
   assert e['steps']==dict(rod=500,ball=750,corner=325)[case['scene']] and e['substeps']==e['steps']*800
   assert sha(folder/'teacher.json')==reg['teacher_config_sha256'] and e['model_sha256']==case['model_sha256']
   assert e['filter_config']==read(Path(case['reference'])/'execution.json')['filter_config']
   with np.load(folder/'trajectory.npz') as z,np.load(Path(case['reference'])/'trajectory.npz') as old:np.testing.assert_array_equal(z['observation'][0],old['observation'][0])
   assert r['qualified']==(q['status']=='qualified')
   state['rows'].append(dict(id=case['id'],split=case['split'],folder=str(folder),reused=bool(case['reuse']),qualified=r['qualified'],review_sha256=sha(folder/'HANDOFF_REVIEW.json'),qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json')))
   write(root/'execution.json',state)
  state.update(status='all30_qualified_pending_independent_dataset_review' if all(r['qualified'] for r in state['rows']) else 'complete_with_scientific_failures_preserved_no_dataset',ended_utc=now())
  write(root/'execution.json',state)
 except BaseException as exc:
  state.update(status='failed_preserved_no_retry',error=repr(exc),ended_utc=now());write(root/'execution.json',state);raise

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 if a.prepare:prepare(a.root.resolve())
 else:run(a.root.resolve())
