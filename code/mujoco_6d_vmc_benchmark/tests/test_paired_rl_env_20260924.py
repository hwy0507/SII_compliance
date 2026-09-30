"""No simulator: prove action boundary, reset, potential reward and journal data."""
import json
from pathlib import Path
import gymnasium as gym
import numpy as np
import pytest
from canonical48_paired_rl_env_20260924 import PairedControlEnv
from canonical48_potential_reward_20260924 import shaped_reward
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning

OPTIONS=dict(stiffness_6d=[100,120,140,20,22,24],damping_6d=[11,12,13,4,5,6])
SPEC={'command':{'environment':{'CORE_VMC_CONFIG':json.dumps(dict(stiffness_6d=[999]*6,damping_6d=[99]*6))}}}


class FakePotentialBackend(gym.Env):
    def __init__(self,root,horizon=3):
        self.output_root=Path(root);self.horizon=horizon;self.episode_index=0
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(48,),dtype=np.float32)
        self.action_space=gym.spaces.Box(np.array([0]+[-1]*6,dtype=np.float32),np.ones(7,dtype=np.float32))
        self.actions=[]
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed);self.phase=0;self.count=0;self.obs=np.zeros(48)
        self.obs[20]=.075123456789;self.obs[39:45]=np.arange(1,7)*1.234567890123
        (self.output_root/f'episode_{self.episode_index:05d}').mkdir(parents=True)
        self.episode_index+=1
        return self.obs.astype(np.float32),{}
    def step(self,action):
        self.actions.append(np.asarray(action).copy());before=self.obs.copy();self.count+=1
        done=self.count==self.horizon
        if not done:self.obs[20]*=.9;self.obs[39:45]*=.95
        reward,terms=shaped_reward(before,0,self.obs,0,terminal=done)
        return self.obs.astype(np.float32),reward,done,False,{'reward_terms':terms}
    def close(self):pass


def make(tmp_path,mode='parameter6',horizon=3):
    backend=FakePotentialBackend(tmp_path,horizon)
    return PairedControlEnv(SPEC,None,tmp_path,mode=mode,nominal_options=OPTIONS,backend=backend),backend


def test_parameter_uses_raw64_and_fixed_training_options(tmp_path):
    env,backend=make(tmp_path);observed,_=env.reset()
    expected=Canonical48VMCTuning(OPTIONS).act(backend.obs,np.zeros(6))
    rounded=Canonical48VMCTuning(OPTIONS).act(observed,np.zeros(6))
    assert not np.array_equal(expected,rounded)
    env.step(np.zeros(6));assert np.array_equal(backend.actions[-1],expected)
    env.close()
    contract=json.loads((tmp_path/'episode_00000/transition_contract.json').read_text())
    assert contract['adapter_train_nominal_options']==OPTIONS
    assert contract['runtime_core_config']['stiffness_6d']==[999]*6


@pytest.mark.parametrize('mode',['parameter6','direct7'])
def test_partial_last_next_and_actual_reward_persist_immediately(tmp_path,mode):
    env,backend=make(tmp_path,mode);env.reset();before=backend.obs.copy()
    _,reward,done,_,info=env.step(np.zeros(env.action_space.shape))
    row=json.loads((tmp_path/'episode_00000/transitions.jsonl').read_text())
    assert np.array_equal(row['observation'],before)
    assert np.array_equal(row['next_observation'],backend.obs)
    assert row['reward']==reward and row['reward_terms']==info['reward_terms']
    assert row['next_observation_valid'] and not done
    assert np.array_equal(row['execution_action'],backend.actions[-1])
    env.close();env.close()
    with np.load(tmp_path/'episode_00000/transitions.npz') as data:
        assert data['next_observation_valid'].tolist()==[True]
        assert np.array_equal(data['next_observation'][-1],backend.obs)
        assert not data['terminated'].any() and not data['truncated'].any()


def test_terminal_placeholder_and_reset_state_are_explicit(tmp_path):
    env,backend=make(tmp_path,horizon=1);env.reset()
    before=backend.obs.copy();_,_,terminated,_,info=env.step(np.ones(6))
    assert terminated and info['terminal_observation_is_placeholder']
    assert not info['next_observation_valid']
    with np.load(tmp_path/'episode_00000/transitions.npz') as data:
        assert np.array_equal(data['next_observation'][0],before)
        assert data['reward_term_potential_after'].tolist()==[0.]
    env.reset();assert not env.controller.log_scale.any()
    expected=Canonical48VMCTuning(OPTIONS).act(backend.obs,np.zeros(6))
    env.step(np.zeros(6));assert np.array_equal(backend.actions[-1],expected)
    env.close()


def test_partial_reset_and_zero_step_close_are_isolated(tmp_path):
    env,_=make(tmp_path);env.reset();env.step(np.ones(6));env.reset()
    assert env.controller.last_parameters is None and not env.controller.log_scale.any()
    env.close();env.close()
    assert json.loads((tmp_path/'episode_00000/transition_summary.json').read_text())['transitions']==1
    assert json.loads((tmp_path/'episode_00001/transition_summary.json').read_text())['transitions']==0


@pytest.mark.parametrize('mode',['parameter6','direct7'])
@pytest.mark.parametrize('kind',['shape','nan','inf'])
def test_invalid_request_does_not_mutate_controller_or_backend(tmp_path,mode,kind):
    env,backend=make(tmp_path,mode);env.reset()
    n=env.action_space.shape[0]
    bad=np.zeros(n+1) if kind=='shape' else np.full(n,np.nan if kind=='nan' else np.inf)
    with pytest.raises(ValueError):env.step(bad)
    assert env.controller.last_parameters is None and not env.controller.log_scale.any()
    assert not backend.actions
    assert (tmp_path/'episode_00000/transitions.jsonl').read_text()==''
    env.close()


@pytest.mark.parametrize('mode',['parameter6','direct7'])
def test_finite_out_of_bounds_clipped_and_recorded(tmp_path,mode):
    env,backend=make(tmp_path,mode);env.reset();request=np.full(env.action_space.shape,2.)
    env.step(request);env.close()
    with np.load(tmp_path/'episode_00000/transitions.npz') as data:
        assert np.array_equal(data['requested_action'][0],request)
        assert np.array_equal(data['policy_action'][0],np.ones(env.action_space.shape))
        assert np.array_equal(data['execution_action'][0],backend.actions[-1])
        assert data['parameter_control_active'].tolist()==[mode=='parameter6']
