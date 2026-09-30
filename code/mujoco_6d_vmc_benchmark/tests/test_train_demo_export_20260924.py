import importlib.util
from pathlib import Path
import numpy as np
import pytest

spec=importlib.util.spec_from_file_location('demo_export',Path(__file__).resolve().parents[1]/'tools/export_train_demo_20260924.py')
exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)


def transitions():
    obs=np.zeros((600,48));obs[:,20]=np.arange(600)/1000.
    action=np.zeros((600,7));action[:,0]=np.linspace(0,1,600);action[:,1:]=.123456789
    done=np.zeros(600,dtype=bool);done[-1]=True
    return dict(observation=obs,next_observation=np.concatenate([obs[1:],obs[-1:]]),
        execution_action=action,policy_action=np.zeros((600,6)),parameter_request=np.zeros((600,6)),log_scale=np.zeros((600,6)),
        reward=np.linspace(-1,1,600),terminated=done,truncated=np.zeros(600,dtype=bool),next_observation_valid=~done)


def test_action7_scaling_and_all_actual_rewards_are_preserved():
    original=transitions();converted,_=exporter.convert_transitions(original)
    assert converted['observations'].dtype==np.float32
    assert converted['actions_sac'][0,0]==-1 and converted['actions_sac'][-1,0]==1
    original32=original['execution_action'][:,1:].astype(np.float32)
    np.testing.assert_array_equal(converted['actions_sac'][:,1:],2.*((original32+np.float32(1.))/np.float32(2.))-np.float32(1.))
    np.testing.assert_array_equal(converted['rewards'][:,0],original['reward'].astype(np.float32))
    assert converted['dones'].sum()==1 and not converted['timeouts'].any()
    assert not converted['next_observation_valid'][-1,0]


def test_all_axes_match_real_sb3_scale_action_including_small_yields():
    from types import SimpleNamespace
    import gymnasium as gym
    from stable_baselines3.common.policies import BasePolicy
    data=transitions()
    data['execution_action'][:,1:]=[1.e-8,-1.e-8,1.e-7,-1.e-7,.123456789,-.123456789]
    converted,_=exporter.convert_transitions(data)
    policy=SimpleNamespace(action_space=gym.spaces.Box(
        np.array([0]+[-1]*6,dtype=np.float32),np.ones(7,dtype=np.float32)))
    expected=BasePolicy.scale_action(policy,converted['actions_execution'])
    assert expected.dtype==converted['actions_sac'].dtype==np.float32
    np.testing.assert_array_equal(converted['actions_sac'],expected)
    assert np.any(expected[:,1:]!=converted['actions_execution'][:,1:])


@pytest.mark.parametrize('error',['zero6_as_action','timeout','missing_terminal','false_next_mask','nonfinite','out_of_bounds','not_zero_parameter'])
def test_reject_invalid_demo_contract(error):
    data=transitions()
    if error=='zero6_as_action':data['execution_action']=data['policy_action']
    elif error=='timeout':data['truncated'][-1]=True
    elif error=='missing_terminal':data['terminated'][-1]=False
    elif error=='false_next_mask':data['next_observation_valid'][-1]=True
    elif error=='nonfinite':data['reward'][3]=np.nan
    elif error=='out_of_bounds':data['execution_action'][0,0]=-.1
    elif error=='not_zero_parameter':data['policy_action'][0,0]=.2
    with pytest.raises(ValueError):exporter.convert_transitions(data)
