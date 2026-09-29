import numpy as np
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from validate_office_apparatus_v5_20260917 import prepare_policy_state


def policy():
    p=OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
    rng=np.random.default_rng(123)
    p.w=.4*np.eye(128);p.win=rng.normal(0,.1,(128,6));p.leak=np.full(128,.2)
    p.scale=np.ones(6);p.weights=rng.normal(0,.01,(268,7));p.reset()
    return p


def test_exact_neutral_action_despite_unseen_pose_and_goal():
    p=policy();rng=np.random.default_rng(17)
    for _ in range(100):
        obs=rng.normal(0,10,48);obs[39:45]=0
        np.testing.assert_array_equal(p.act(obs),np.zeros(7))


def test_reservoir_retains_impulse_history_then_decays_and_resets():
    p=policy();obs=np.zeros(48);obs[39]=2;p.act(obs)
    obs[:]=0;p.act(obs)
    assert np.linalg.norm(p.state)>0
    magnitude=np.linalg.norm(p.state)
    for _ in range(200):p.act(obs)
    assert np.linalg.norm(p.state)<magnitude*1e-8
    p.reset();np.testing.assert_array_equal(p.act(obs),np.zeros(7))


def test_diagnostic_reset_erases_history_but_preserves_current_input_and_weights():
    live=policy();reset=policy();fresh=policy()
    impulse=np.zeros(48);impulse[39]=2
    live.act(impulse);reset.act(impulse)
    quiet=np.zeros(48)
    previous=prepare_policy_state(live,'none')
    np.testing.assert_array_equal(previous,live.state)
    assert np.linalg.norm(live.act(quiet))>0
    np.testing.assert_array_equal(prepare_policy_state(reset,'reset_each_observation'),np.zeros(128))
    np.testing.assert_array_equal(reset.act(quiet),np.zeros(7))
    prepare_policy_state(reset,'reset_each_observation')
    np.testing.assert_array_equal(reset.act(impulse),fresh.act(impulse))
    np.testing.assert_array_equal(reset.weights,fresh.weights)
