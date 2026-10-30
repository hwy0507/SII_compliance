"""Read-only independent closure audit before constructing a shared dataset."""
import argparse
from collections import Counter
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,write,sha
from vertical_stage_scrape_teacher_20261030 import VerticalStageScrapeTeacher


def review(root, allow_partial=False):
 root=Path(root).resolve();reg=read(root/'REGISTRATION.json');state=read(root/'execution.json')
 assert reg['schema']=='sii-contact-yield-scrape-three-scenes-collection-v1'
 assert state['status'] in ('all30_qualified_pending_independent_dataset_review','complete_with_scientific_failures_preserved_no_dataset') or (allow_partial and state['status']=='running_fixed_teacher_collection')
 assert state['registration_sha256']==sha(root/'REGISTRATION.json')
 assert sha(ROOT/'experiments/collect_contact_yield_scrape_scenes_20261030.py')==reg['coordinator_sha256']
 assert sha(root/'teacher.json')==reg['teacher_config_sha256']
 for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
 assert len(reg['cases'])==30
 assert len(state['rows'])==30 or (allow_partial and 0<len(state['rows'])<30)
 assert len({r['id'] for r in state['rows']})==len(state['rows'])
 assert Counter((c['scene'],c['split']) for c in reg['cases'])==Counter({(s,p):n for s in ('rod','ball','corner') for p,n in [('train',8),('validation',2)]})
 rows=[]
 for case,row in zip(reg['cases'],state['rows']):
  assert case['id']==row['id'] and case['split']==row['split']
  folder=Path(row['folder']);ref=Path(case['reference'])
  expected=Path(case['reuse']) if case['reuse'] else root/case['id']/case['scene']
  assert folder==expected and row['reused']==bool(case['reuse'])
  assert sha(ref/'execution.json')==case['reference_execution_sha256']
  assert sha(ref/'DEMONSTRATION_QUALIFICATION.json')==case['reference_qualification_sha256']
  assert sha(folder/'HANDOFF_REVIEW.json')==row['review_sha256']
  assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==row['qualification_sha256']
  e=read(folder/'execution.json');h=read(folder/'HANDOFF_EXECUTION.json')
  q=read(folder/'DEMONSTRATION_QUALIFICATION.json');r=read(folder/'HANDOFF_REVIEW.json');a=read(folder/'INDEPENDENT_AUDIT.json')
  for record in (h,q,a):
   for name,digest in record['input_hashes'].items():assert sha(folder/name)==digest,(case['id'],name)
  assert e['scene']==case['scene'] and e['status']=='complete'
  assert e['model_sha256']==case['model_sha256']==read(ref/'execution.json')['model_sha256']
  assert e['physics_dt_s']==5e-5 and e['steps']==dict(rod=500,ball=750,corner=325)[case['scene']]
  assert e['substeps']==e['steps']*800 and e['filter_config']==read(ref/'execution.json')['filter_config']
  assert sha(folder/'teacher.json')==e['teacher_config_sha256']==reg['teacher_config_sha256']
  assert e['experiment_environment']['VMC_SCENE_SEED']==str(case['seed'])
  for name,value in case['parameters'].items():assert e['experiment_environment'][name]==str(value)
  assert h['source_stable'] and h['student_steps']==0 and h['executed_teacher_steps']==e['steps']==h['completed_steps']
  assert a['status']=='passed' and a['actor_replay_max_abs']==0 and a['filter_replay_max_abs']==0
  assert r['handoff_execution_sha256']==sha(folder/'HANDOFF_EXECUTION.json')
  assert r['independent_audit_sha256']==sha(folder/'INDEPENDENT_AUDIT.json')
  with np.load(folder/'trajectory.npz',allow_pickle=False) as z:obs=z['observation'].copy();act=z['action'].copy();times=z['time'].copy()
  assert obs.shape==(e['steps'],48) and act.shape==(e['steps'],7)
  assert np.isfinite(obs).all() and np.isfinite(act).all()
  np.testing.assert_allclose(times,np.arange(1,len(times)+1)*.04,rtol=0,atol=1e-8)
  with np.load(ref/'trajectory.npz',allow_pickle=False) as z:np.testing.assert_array_equal(obs[0],z['observation'][0])
  teacher=VerticalStageScrapeTeacher(read(folder/'teacher.json'));teacher.reset();actions=[]
  for o in obs:teacher.observe(o.copy());actions.append(teacher.act(o[39:45].copy(),.04))
  np.testing.assert_array_equal(np.asarray(actions),act)
  with np.load(folder/'handoff_actions.npz',allow_pickle=False) as z:
   np.testing.assert_array_equal(z['teacher'],act)
   assert z['physical_step_completed'].all() and z['teacher_loss_mask'].all()
   assert np.all(z['role']=='executed_teacher_suffix')
  assert r['qualified']==row['qualified']==(q['status']=='qualified')
  if case['scene']=='rod':
   b=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
   assert b['hashes']['trajectory.npz']==sha(folder/'trajectory.npz')
   assert (b['status']=='passed')==q['scene_contact_valid']
  rows.append(dict(id=case['id'],scene=case['scene'],split=case['split'],qualified=row['qualified'],task=q['task_success'],safety=q['safety_valid'],behavior=q['scene_contact_valid'],actor_replay=True,filter_replay=True,qualification_sha256=row['qualification_sha256'],trajectory_sha256=sha(folder/'trajectory.npz')))
 failures=[r['id'] for r in rows if not r['qualified']]
 if state['status']!='running_fixed_teacher_collection':
  assert state['status']==('all30_qualified_pending_independent_dataset_review' if not failures else 'complete_with_scientific_failures_preserved_no_dataset')
 return dict(schema='sii-contact-yield-scrape-collection-independent-review-v1',status=('verified_all30_qualified' if not failures else 'verified_scientific_failures_no_dataset') if len(rows)==30 else 'verified_completed_prefix_only',registration_sha256=sha(root/'REGISTRATION.json'),execution_sha256=sha(root/'execution.json'),reviewer_sha256=sha(Path(__file__)),qualified=sum(r['qualified'] for r in rows),failures=failures,rows=rows,scope='Development teacher collection only; no learning or unseen-test claim. Teacher tuning used development validation identities; not an independent heldout result.')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();write(a.output,review(a.root))
