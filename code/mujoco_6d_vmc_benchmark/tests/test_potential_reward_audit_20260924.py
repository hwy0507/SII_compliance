import importlib.util
from pathlib import Path
import numpy as np
import pytest

path=Path(__file__).resolve().parents[1]/'tools/audit_ppo_potential_reward_20260924.py'
spec=importlib.util.spec_from_file_location('potential_audit',path)
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def observations(n):
    obs=np.zeros((n,48));obs[:,20]=np.linspace(.08,.28,n)
    return obs


@pytest.mark.parametrize('base',[0.,5.,-5.])
def test_complete_n_observations_suffice_without_private_terminal(base):
    obs=observations(600);phase=np.minimum(np.arange(600)//150,3)
    result=audit.reconstruct(obs,phase,.995,terminal_base=base)
    assert result['known_rewards']==600
    assert result['unrecoverable_boundary_rewards']==0
    expected=.08/.30/3+.995**599*base
    assert result['known_discounted_return']==pytest.approx(expected,abs=1e-12)


def test_partial_keeps_boundary_potential_and_marks_last_reward_missing():
    result=audit.reconstruct(observations(392),np.full(392,3),.995)
    assert not result['terminal_applied']
    assert result['known_rewards']==391
    assert result['unrecoverable_boundary_rewards']==1
    assert result['discounted_shaping']==pytest.approx(
        -result['initial_potential']+.995**391*result['last_recorded_potential'],abs=1e-12)
    assert abs(result['discounted_shaping']+result['initial_potential'])>.01


@pytest.mark.parametrize('n',[0,1])
def test_empty_or_single_sample_partial_does_not_invent_reward(n):
    result=audit.reconstruct(observations(n),np.zeros(n),.995)
    assert result['known_rewards']==0
    assert result['terminal_base'] is None


def test_invalid_phases_fail_closed():
    with pytest.raises(ValueError,match='stage'):
        audit.reconstruct(observations(2),np.array([0,4]),.995)
