"""Zero-physics integration checks: saved-history pure actor oracle + worker mocks."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import numpy as np
ROOT=Path(__file__).resolve().parents[3]/'code/mujoco_6d_vmc_benchmark'
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,sha,write
from development_teacher_handoff_20261030 import DevelopmentTeacherHandoff
from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher
from audit_vertical_aware_cross_track_probe_20261030 import expected
import run_vertical_aware_cross_track_probe_20261030 as worker
from run_vertical_aware_cross_track_campaign_20261030 import prepare, check
reg=read(ROOT/'outputs/nonrl_v9_full_grid_eligibility_20261030_v1/REGISTRATION.json')
candidate=next(g for g in reg['catalogue']['groups'] if g['family']=='mlp_scratch' and g['seed']==2026102802)['ordered_candidates'][0]
ref=next(r for r in reg['references'] if r['identity']=='rod_00')
config=read(Path(ref['folder'])/'teacher.json');cp=Path(candidate['checkpoint'])
config['cross_track_recovery']=dict(version='bounded_cross_track_recovery_v3',gain_per_s=1.5,maximum_speed_mps=.02,load_scale_n=1.)
check_sources={str(p):sha(p) for p in [cp,Path(ref['folder'])/'teacher.json']}
with np.load(Path(ref['folder'])/'trajectory.npz',allow_pickle=False) as z:observations=z['observation'].copy()
controls=[]
# Actual saved-history regression: post-pass path is vertical, not zero.
regression=VerticalAwareCrossTrackTeacher(config)
probe=np.zeros(48);probe[47]=1.;probe[21]=.01
regression.observe(probe);regression.act(np.zeros(6))
np.testing.assert_allclose(regression.last_cross_track_velocity,[0.,.015],atol=1e-15)
probe[45:48]=0.;regression.observe(probe);regression.act(np.zeros(6))
np.testing.assert_array_equal(regression.last_cross_track_velocity,np.zeros(2))
probe[45]=1.;regression.observe(probe);regression.act(np.zeros(6))
np.testing.assert_allclose(regression.last_cross_track_velocity,[0.,.015],atol=1e-15)
regression.reset();assert not regression.last_cross_track_velocity.any()
controls.append(dict(vertical_regulates_horizontal_reference=True,full_zero_disables=True,horizontal_transverse_preserved=True,reset_clears=True))
for prefix in (175,275):
 folder=ROOT/'outputs/cross_track_teacher_development_20261030_v1'/('rod_prefix'+str(prefix))/'rod'
 with np.load(folder/'trajectory.npz') as z:hist=z['observation'].copy();times=z['time'].copy()
 actor=VerticalAwareCrossTrackTeacher(config);vel=[]
 for obs in hist:actor.observe(obs);actor.act(obs[39:45]);vel.append(actor.last_cross_track_velocity.copy())
 vel=np.asarray(vel);window=(times>=12.)&(times<12.8)
 assert window.any();np.testing.assert_array_equal(hist[window,45:48],np.tile([0.,0.,1.],(int(window.sum()),1)))
 assert np.max(np.abs(vel[window,1]))>0
 assert np.all(np.sum(vel[window]*hist[window,20:22],axis=1)>=0)
 assert np.max(np.linalg.norm(vel,axis=1))<=.02000000000001
 controls.append(dict(actual_saved_prefix=prefix,vertical_window_samples=int(window.sum()),nonzero_return_max_mps=float(np.max(np.abs(vel[window,1]))),bounded_and_error_aligned=True,trajectory_sha256=sha(folder/'trajectory.npz')))
for prefix in [0,175,275]:
 t,s,behavior,mask=expected(config,cp,observations,prefix)
 actor=DevelopmentTeacherHandoff(config,cp,prefix)
 actor.teacher=VerticalAwareCrossTrackTeacher(config);actor.reset()
 actual=[]
 for obs in observations:
  actor.observe(obs);actual.append(actor.act(obs[39:45]))
 np.testing.assert_array_equal(actual,behavior)
 controls.append(dict(prefix=prefix,saved_history_independent_pure_controller_replay=True))
# Exercise the actual worker glue, both complete and physics-exception paths.
# Mock only the physical worker and cgroup guard, not source/labels/receipts.
original_worker=worker.physical.worker;original_guard=worker.check_resources
old_env=dict(os.environ)
worker.check_resources=lambda:None
os.environ['VMC_STUDENT_CHECKPOINT']=str(cp);os.environ.pop('VMC_COLLECTION_PLAN',None)
try:
 for fail in [False,True]:
  def fake(out,scene):
   folder=out/scene;folder.mkdir();write(folder/'teacher.json',config)
   import shutil
   shutil.copyfile(cp,folder/'student_checkpoint.npz')
   actor=worker.physical.make_actor(config,folder/'student_checkpoint.npz')
   actions=[]
   for obs in observations[:(4 if fail else 500)]:actor.observe(obs);actions.append(actor.act(obs[39:45]))
   n=3 if fail else 500
   np.savez_compressed(folder/'trajectory.npz',observation=observations[:n],action=np.asarray(actions[:n]))
   write(folder/'execution.json',dict(status='failed_preserved' if fail else 'complete',steps=n))
   if fail:raise RuntimeError('injected physical failure, fourth action not completed')
   replay=worker.physical.make_actor(config,folder/'student_checkpoint.npz')
   for obs in observations:replay.observe(obs);replay.act(obs[39:45])
  worker.physical.worker=fake
  with tempfile.TemporaryDirectory(prefix='handoff-glue-') as tmp:
   output=Path(tmp)/'probe'
   try:worker.worker(output,175,'rod')
   except RuntimeError as exc:assert fail and 'injected' in str(exc)
   else:assert not fail
   receipt=read(output/'rod/HANDOFF_EXECUTION.json')
   assert receipt['status']==('failed_preserved' if fail else 'complete_pending_independent_review')
   assert receipt['completed_steps']==(3 if fail else 500)
   assert receipt['attempted_actions']==(4 if fail else 500)
   assert receipt['labels_eligible_for_training'] is False
   with np.load(output/'rod/handoff_actions.npz') as z:
    assert int(z['physical_step_completed'].sum())==(3 if fail else 500)
    assert int(z['teacher_loss_mask'].sum())==(0 if fail else 325)
   controls.append(dict(injected_physical_failure=fail,worker_receipt_and_masks_correct=True))
finally:worker.physical.worker=original_worker;worker.check_resources=original_guard;os.environ.clear();os.environ.update(old_env)
with tempfile.TemporaryDirectory(prefix='handoff-prepare-') as tmp:
 root=Path(tmp)/'pending';prepare(root);pending=read(root/'REGISTRATION.json');check(root,pending)
 assert pending['maximum_episodes']==5 and [c['student_steps'] for c in pending['cases']]==[0,0,0,175,275]
 assert not (root/'execution.json').exists()
 try:prepare(root)
 except AssertionError:pass
 else:raise AssertionError('Duplicate preparation accepted')
 controls.append(dict(real_prepare_no_physics_and_duplicate_refusal=True))
for p,d in check_sources.items():assert sha(Path(p))==d
sources=[ROOT/'tools'/n for n in ['run_vertical_aware_cross_track_probe_20261030.py','audit_vertical_aware_cross_track_probe_20261030.py','run_vertical_aware_cross_track_campaign_20261030.py']]
write(Path(__file__).with_name('VERTICAL_AWARE_CROSS_TRACK_INTEGRATION_CONTROLS_20261030.json'),dict(status='passed_zero_physics',controls=controls,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in sources},real_input_hashes=check_sources,limitations='Saved-history replay and injected worker errors, not new physical recovery evidence.'))
print('Passed: independent saved-history behavior; complete/failure worker glue; real preparation and duplicate refusal. Zero physics.')
