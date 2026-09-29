from types import SimpleNamespace
import mujoco
import numpy as np

from physics_substep_metrics_20260923 import EpisodeMetrics, Instrumentation


def fixture_env():
    bodies=''.join(f'<body pos="0 0 .1" name="body{i}"><joint name="j{i}" type="hinge" axis="0 1 0"/><geom type="sphere" size=".02" mass=".1"/>' for i in range(7))
    motors=''.join(f'<motor joint="j{i}"/>' for i in range(7))
    model=mujoco.MjModel.from_xml_string('<mujoco><option timestep=".001"/><worldbody>'+bodies+'</body>'*7+'</worldbody><actuator>'+motors+'</actuator></mujoco>')
    data=mujoco.MjData(model)
    data.qpos[:]=np.linspace(.01,.07,7);data.qvel[:]=np.linspace(.1,.7,7)
    data.ctrl[:]=np.linspace(.01,.07,7)
    mujoco.mj_forward(model,data)
    mujoco.mj_step(model,data)
    return SimpleNamespace(model=model,data=data,_hand_id=7,simulation_time_s=1.,
                           reference=SimpleNamespace(index=0,goals=[np.array([0.,0.,.9]),np.array([0.,0.,.8])],names=['first','second']))


def test_sampling_does_not_modify_live_state_and_matches_fresh_kinematics():
    env=fixture_env();data=env.data
    keys=('qpos','qvel','qacc','qacc_warmstart','ctrl','xpos','xmat','qfrc_actuator','actuator_force','cvel','qfrc_bias')
    before={key:getattr(data,key).copy() for key in keys};time=data.time
    audit=EpisodeMetrics(env);audit.sample()
    for key,value in before.items():np.testing.assert_array_equal(getattr(data,key),value)
    assert data.time==time
    independent=mujoco.MjData(env.model)
    independent.qpos[:]=data.qpos;independent.qvel[:]=data.qvel
    mujoco.mj_forward(env.model,independent)
    jp=np.zeros((3,env.model.nv));jr=np.zeros_like(jp)
    mujoco.mj_jacBody(env.model,independent,jp,jr,env._hand_id)
    expected=jp@data.qvel
    np.testing.assert_allclose(audit.arrays['twist'][0,:3],expected,rtol=1e-7,atol=1e-9)
    assert audit.speed_peak==float(np.linalg.norm(expected))
    np.testing.assert_array_equal(audit.qfrc_peak,np.abs(data.qfrc_actuator))


def test_stage_errors_and_sampling_count():
    env=fixture_env();audit=EpisodeMetrics(env);audit.sample()
    env.reference.index=1;mujoco.mj_step(env.model,env.data);audit.sample()
    # The canonical environment releases model/data references in close().
    env.model=None;env.data=None
    result=audit.summary()
    assert result['samples']==2
    assert result['stages']['0']['count']==1
    assert result['stages']['1']['count']==1
    for stage in (0,1):
        assert np.isclose(result['stages'][str(stage)]['position_rmse_3d_m'],np.linalg.norm(audit.arrays['error'][stage]))


def test_instrumentation_restores_hooks_on_error():
    import audited_velocity_env as velocity_env
    original_step=mujoco.mj_step
    original_physics=velocity_env.PandaWBCVelocityResidualEnv._physics_step
    try:
        with Instrumentation():
            assert mujoco.mj_step is not original_step
            raise RuntimeError('intentional test')
    except RuntimeError:
        pass
    assert mujoco.mj_step is original_step
    assert velocity_env.PandaWBCVelocityResidualEnv._physics_step is original_physics


def test_mixed_resolution_rmse_weights_elapsed_time_not_sample_count():
    env=fixture_env();audit=EpisodeMetrics(env,capacity=1024)
    # Fixed physical pose; change only reference/error and sample duration.
    target=env.data.xpos[env._hand_id].copy()
    env.reference.goals[0]=target+np.array([.1,0,0]);env.model.opt.timestep=.001
    audit.sample()
    env.reference.goals[0]=target+np.array([.3,0,0]);env.model.opt.timestep=.003
    audit.sample()
    raw=audit.arrays['error'][:2].astype(float)
    expected=np.sqrt(np.sum(np.array([.001,.003])*np.sum(raw**2,axis=1))/.004)
    result=audit.summary()
    assert result['timestep_s'] is None
    assert result['rmse_weighting']=='physical time integral'
    np.testing.assert_allclose(result['position_rmse_3d_m'],expected,atol=1e-8)
    assert result['timestep_sample_counts']=={'.001':1,'.003':1} or result['timestep_sample_counts']=={'0.001':1,'0.003':1}
