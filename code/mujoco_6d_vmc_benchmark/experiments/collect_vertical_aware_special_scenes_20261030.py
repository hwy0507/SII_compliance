"""Collect the same 30 development identities with one verified fixed teacher.

Reuse the three exact completed nominal probes; run the other 27 once. No
unseen conditions, new fitting, threshold edits or automatic retries. Two
qualified mixed recovery histories remain separately registered augmentation
candidates; a later audited builder must preserve warmup/loss masks.
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
PARENT=ROOT/'outputs/vertical_aware_cross_track_development_20261030_v3'
ORIGINAL=ROOT/'outputs/special_scene_direction_collection_20261029_v9'
UNIT='sii-vertical-aware-cross-track-development-20261030.service'
REVIEW=ROOT.parents[1]/'docs/evidence/nonrl_v9_candidate_catalogue_20261029/VERTICAL_AWARE_COMPLETE_REVIEW_20261030.json'
REVIEWER=ROOT/'tools/review_vertical_aware_cross_track_campaign_20261030.py'

def prerequisites():
 p=properties(UNIT);assert p['ActiveState']=='inactive' and p['MainPID']=='0'
 s=read(PARENT/'execution.json');assert s['status']=='complete_five_probes_pending_independent_campaign_review'
 assert len(s['rows'])==5 and all(r['qualified'] for r in s['rows'])
 r=read(REVIEW);assert r['status']=='verified_complete_five_development_probes' and r['qualified_cases']==5
 assert r['execution_snapshot_sha256']==sha(PARENT/'execution.json')
 assert r['registration_sha256']==sha(PARENT/'REGISTRATION.json')
 assert r['reviewer_sha256']==sha(REVIEWER)
 assert not (ROOT/'outputs/nonrl_v9_isolated_unseen_108_20261030_v1').exists()

def prepare(root):
 assert not root.exists();prerequisites()
 old=read(ORIGINAL/'COLLECTION_PLAN.json');pr=read(PARENT/'REGISTRATION.json')
 assert len(old['episodes'])==30
 cfg=read(PARENT/'teacher.json');assert cfg['cross_track_recovery']['version']=='bounded_cross_track_recovery_v3'
 cases=[]
 for item in old['episodes']:
  ref=Path(item['folder']);q=verify_qualification(ref,sha(ref/'DEMONSTRATION_QUALIFICATION.json'));assert q['status']=='qualified'
  e=read(ref/'execution.json')
  reuse=PARENT/(item['scene']+'_prefix0')/item['scene'] if item['id'].endswith('_00') else None
  cases.append(dict(id=item['id'],scene=item['scene'],split=item['split'],seed=item['seed'],parameters=item['scene_parameters'],reference=str(ref),reference_execution_sha256=sha(ref/'execution.json'),reference_qualification_sha256=sha(ref/'DEMONSTRATION_QUALIFICATION.json'),model_sha256=e['model_sha256'],reuse=str(reuse) if reuse else None,reuse_review_sha256=sha(reuse/'HANDOFF_REVIEW.json') if reuse else None,reuse_qualification_sha256=sha(reuse/'DEMONSTRATION_QUALIFICATION.json') if reuse else None))
 assert {(s,p):sum(c['scene']==s and c['split']==p for c in cases) for s in ('rod','ball','corner') for p in ('train','validation')}=={(s,p):n for s in ('rod','ball','corner') for p,n in [('train',8),('validation',2)]}
 candidate=pr['cases'][0]['candidate']
 root.mkdir(parents=True);write(root/'teacher.json',cfg)
 augment=[]
 parent_reg=read(PARENT/'REGISTRATION.json')
 prefixes=[c['student_steps'] for c in parent_reg['cases'] if c['scene']=='rod' and c['student_steps']>0]
 assert len(prefixes)==2 and len(set(prefixes))==2
 for prefix in prefixes:
  f=PARENT/('rod_prefix'+str(prefix))/'rod';h=read(f/'HANDOFF_EXECUTION.json')
  assert h['student_steps']==prefix and h['source_stable'] and read(f/'HANDOFF_REVIEW.json')['qualified']
  augment.append(dict(folder=str(f),split='train',source_identity='rod_00',teacher_steps=500-prefix,student_prefix_steps=prefix,qualification_sha256=sha(f/'DEMONSTRATION_QUALIFICATION.json'),review_sha256=sha(f/'HANDOFF_REVIEW.json'),mask_note='Prefix importance=0/warmup only, actual teacher suffix only. Pending independent dataset builder; no automatic fitting.'))
 write(root/'REGISTRATION.json',dict(schema='sii-vertical-aware-three-scenes-collection-v1',registered_utc=now(),parent_directory=str(PARENT),parent_unit=UNIT,parent_review=str(REVIEW),parent_reviewer=str(REVIEWER),cases=cases,maximum_new_physical_episodes=27,maximum_pure_episodes=30,seeds=[2026102801,2026102802,2026102803],intended_common_candidates_per_family_seed=12,teacher_config_sha256=sha(root/'teacher.json'),candidate=candidate,parent_review_sha256=sha(REVIEW),parent_execution_sha256=sha(PARENT/'execution.json'),original_plan_sha256=sha(ORIGINAL/'COLLECTION_PLAN.json'),source_sha256={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')},coordinator_sha256=sha(Path(__file__)),augmentation_candidates=augment,resources=dict(cpu=6,simulators=1,threads=1,memory_max_bytes=3221225472,swap_bytes=0),no_unseen_or_fitting=True))

def check(root,reg):
 assert str(PARENT)==reg['parent_directory'] and UNIT==reg['parent_unit'] and str(REVIEW)==reg['parent_review'] and str(REVIEWER)==reg['parent_reviewer']
 assert sha(Path(__file__))==reg['coordinator_sha256']
 assert sha(root/'teacher.json')==reg['teacher_config_sha256']
 assert sha(REVIEW)==reg['parent_review_sha256'] and sha(PARENT/'execution.json')==reg['parent_execution_sha256']
 assert sha(ORIGINAL/'COLLECTION_PLAN.json')==reg['original_plan_sha256']
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
     subprocess.run([sys.executable,str(ROOT/'tools/run_vertical_aware_cross_track_probe_20261030.py'),'--output',str(out),'--scene',case['scene'],'--student-steps','0'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
     subprocess.run([sys.executable,str(ROOT/'tools/audit_vertical_aware_cross_track_probe_20261030.py'),str(folder)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
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
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');p.add_argument('--parent',type=Path,required=True);p.add_argument('--parent-unit',required=True);p.add_argument('--review',type=Path,required=True);p.add_argument('--reviewer',type=Path,required=True);a=p.parse_args()
 PARENT=a.parent.resolve();UNIT=a.parent_unit;REVIEW=a.review.resolve();REVIEWER=a.reviewer.resolve()
 if a.prepare:prepare(a.root.resolve())
 else:run(a.root.resolve())
