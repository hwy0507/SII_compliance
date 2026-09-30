"""No dynamics integration: inject synthetic live contacts and state readers."""
import copy
from types import SimpleNamespace
import json
import sys
import numpy as np
import pytest
import contact_substep_sidecar_20260924 as module


def fake_env(monkeypatch):
    model=SimpleNamespace(opt=SimpleNamespace(timestep=5e-5,integrator=3),ngeom=3,
        geom_bodyid=np.array([0,1,2]),nq=2,nv=2,nu=1,na=0,nbody=3,nmocap=0,nuserdata=0)
    data=SimpleNamespace(time=0.,contact=[],ncon=0,qpos=np.array([1.,2.]),qvel=np.array([3.,4.]),
        qacc=np.array([5.,6.]),qfrc_constraint=np.array([7.,8.]),ctrl=np.array([9.]),
        solver_niter=np.array([0]),solver=[],geom_xpos=np.zeros((3,3)),geom_xmat=np.tile(np.eye(3).ravel(),(3,1)))
    monkeypatch.setattr(module.mujoco,'mj_stateSize',lambda m,s:6)
    def get_state(m,d,state,s):state[:]=np.r_[d.time,d.qpos,d.qvel,d.ctrl]
    monkeypatch.setattr(module.mujoco,'mj_getState',get_state)
    monkeypatch.setattr(module.mujoco,'mj_id2name',lambda m,t,i:('rod','hand','target')[i])
    def force(m,d,i,w):w[:]=[d.contact[i].force,0,0,0,0,0]
    monkeypatch.setattr(module.mujoco,'mj_contactForce',force)
    return SimpleNamespace(model=model,data=data,audit_obstacles={0:'rod',2:'target_object_geom'},
        _push_audit_robot_geom_ids={1},reference=SimpleNamespace(index=3,names=('a','b','c','lift')))


def contact(depth,force=2.,geom2=1):
    return SimpleNamespace(geom1=0,geom2=geom2,dist=-depth,force=force,pos=np.zeros(3),frame=np.eye(3).ravel(),
        efc_address=0,solref=np.array([.0015,1.]),solimp=np.array([.95,.995,.0002,.5,2.]))


def sample(episode,depth):
    episode.before_step();episode.data.time+=episode.dt
    episode.data.contact=[contact(depth)];episode.data.ncon=1
    before=copy.deepcopy(vars(episode.data));episode.after_step()
    for key in ('qpos','qvel','qacc','qfrc_constraint','ctrl','geom_xpos','geom_xmat'):
        np.testing.assert_array_equal(getattr(episode.data,key),before[key])
    assert episode.data.time==before['time'] and episode.data.contact[0].dist==before['contact'][0].dist


def test_threshold_equality_and_contiguous_runs():
    runs=module.ThresholdRuns(1)
    for depth in (.0002,.0002,0.,.00021):runs.update([depth])
    np.testing.assert_array_equal(runs.count,[[3,3,3,1]])
    np.testing.assert_array_equal(runs.longest,[[2,2,2,1]])


def test_read_only_live_capture_chunks_and_pre_post_state(monkeypatch,tmp_path):
    env=fake_env(monkeypatch);episode=module.ContactEpisode(env,tmp_path/'audit',chunk_size=2,event_chunk_size=2)
    for depth in (.00019,.0002,0.,.00021):sample(episode,depth)
    result=episode.save()
    assert result['samples']==4 and result['event_count']==3
    assert result['obstacle_names']==['rod']
    assert result['thresholds']['steps_at_or_above']==[[3,3,2,1]]
    assert result['thresholds']['longest_consecutive_steps']==[[2,2,1,1]]
    assert result['peak_records'][0]['sample_index']==3
    assert result['peak_records'][0]['geom1']==0 and result['peak_records'][0]['geom2']==1
    raw=np.load(tmp_path/'audit/contacts_0000.npz')
    np.testing.assert_array_equal(raw['depth_m'][:,0],[.00019,.0002])
    event=np.load(tmp_path/'audit/events_0000.npz')
    np.testing.assert_allclose(event['post_state'][:,0]-event['pre_state'][:,0],5e-5,rtol=0,atol=1e-15)
    np.testing.assert_array_equal(event['pre_state'][:,1:],event['post_state'][:,1:])
    assert len(json.loads((tmp_path/'audit/events_0000.json').read_text()))==2


def test_deepest_pair_and_no_target_contact(monkeypatch,tmp_path):
    env=fake_env(monkeypatch);episode=module.ContactEpisode(env,tmp_path/'audit')
    episode.before_step();env.data.time=5e-5
    env.data.contact=[contact(.0001,3),contact(.00021,7),contact(.001,100,geom2=2)];env.data.ncon=3
    episode.after_step();result=episode.save()
    raw=np.load(tmp_path/'audit/contacts_0000.npz')
    assert raw['contact_count'][0,0]==2
    assert raw['peak_pair_normal_force_n'][0,0]==7
    assert result['max_depth_m']==[.00021]


def test_reject_unbracketed_and_wrong_step(monkeypatch,tmp_path):
    episode=module.ContactEpisode(fake_env(monkeypatch),tmp_path/'audit')
    with pytest.raises(ValueError,match='exactly one'):episode.after_step()
    episode.before_step();episode.data.time=.01
    with pytest.raises(ValueError,match='exactly one'):episode.after_step()


def test_hooks_restore_on_failure_without_simulation(monkeypatch,tmp_path):
    class Env:
        def _physics_step(self):pass
    monkeypatch.setitem(sys.modules,'audited_velocity_env',SimpleNamespace(PandaWBCVelocityResidualEnv=Env))
    original_physics=Env._physics_step;original_step=module.mujoco.mj_step
    with pytest.raises(RuntimeError,match='intentional'):
        with module.ContactInstrumentation(tmp_path):
            assert Env._physics_step is not original_physics
            assert module.mujoco.mj_step is not original_step
            raise RuntimeError('intentional')
    assert Env._physics_step is original_physics and module.mujoco.mj_step is original_step
