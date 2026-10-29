"""Algebraic controls only; no dynamic recovery/safety claim."""
import copy
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]/'code/mujoco_6d_vmc_benchmark';sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,write,sha
from cross_track_recovery_teacher_20261030 import CrossTrackRecoveryTeacher,VERSION
from optimize_tool_contact_20261002 import ParameterTeacher
base=read(ROOT/'outputs/special_scene_direction_collection_20261029_v9/rod_00/rod/teacher.json')
cfg=copy.deepcopy(base);cfg['cross_track_recovery']=dict(version=VERSION,gain_per_s=1.5,maximum_speed_mps=.02,load_scale_n=1.)
obs=np.zeros(48);obs[45]=1.;obs[14]=.02;obs[21]=.01
actor=CrossTrackRecoveryTeacher(cfg);actor.observe(obs);a=actor.act(np.zeros(6));v=actor.last_cross_track_velocity.copy()
assert v[1]>0 and abs(v[0])<1e-15 and np.linalg.norm(v)<=.02
actor.reset();negative=obs.copy();negative[21]=-.01;actor.observe(negative);actor.act(np.zeros(6));np.testing.assert_allclose(actor.last_cross_track_velocity,-v,atol=0,rtol=0)
actor.reset();actor.observe(obs);actor.act(np.array([0.,10.,0.,0.,0.,0.]));assert np.linalg.norm(actor.last_cross_track_velocity)<np.linalg.norm(v)/100
# With no cross-track error the original actual teacher action is unchanged.
legacy=ParameterTeacher(base);new=CrossTrackRecoveryTeacher(cfg)
for _ in range(100):
 o=obs.copy();o[21]=0.;o[39:45]=[.3,.4,.5,.01,.02,.03]
 legacy.observe(o);new.observe(o);np.testing.assert_array_equal(legacy.act(o[39:45]),new.act(o[39:45]))
# Direction-free horizontal command cannot create a restore term.
new.reset();o=obs.copy();o[45:48]=[0.,0.,1.];new.observe(o);new.act(np.zeros(6));np.testing.assert_array_equal(new.last_cross_track_velocity,np.zeros(2))
rng=np.random.default_rng(20261030);max_speed=0.
for _ in range(2000):
 new.reset();o=obs.copy();o[20:22]=rng.normal(size=2);o[45:47]=rng.normal(size=2)
 wrench=rng.normal(0,5,6);new.observe(o);a=new.act(wrench);vel=new.last_cross_track_velocity
 assert np.isfinite(a).all() and np.max(np.abs(a))<=1 and np.linalg.norm(vel)<=.02+1e-15
 direction=o[45:47]/np.linalg.norm(o[45:47]);assert abs(float(direction@vel))<1e-14
 assert float(vel@o[20:22])>=-1e-15
 max_speed=max(max_speed,float(np.linalg.norm(vel)))
output=Path(__file__).with_name('CROSS_TRACK_TEACHER_ALGEBRAIC_CONTROLS_20261030.json')
write(output,dict(status='passed_algebraic_only',configuration=cfg,random_samples=2000,maximum_restore_speed_mps=max_speed,
 controls=['restore sign/symmetry','smooth load suppression','100-step original equality at zero cross-track error','zero horizontal path disables term','random bounded/orthogonal/error-reducing restore'],source_sha256=sha(ROOT/'tools/cross_track_recovery_teacher_20261030.py'),physical_executions=0,no_training_performed=True,limitations='No physical safety, successful recovery or qualified demonstration established. Must register finite matched-scene probes.'))
print('Algebraic controls passed; zero new physics.')
