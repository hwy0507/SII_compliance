import numpy as np
import pytest

from canonical48_potential_reward_20260924 import GAMMA, potential, shaped_reward


def obs(error):
    value = np.zeros(48)
    value[20] = error
    return value


@pytest.mark.parametrize('length',[2,64,600])
@pytest.mark.parametrize('outcome',['success','ordinary_failure','invalid'])
def test_discounted_shaping_cannot_reward_waiting_or_stage_changes(length,outcome):
    rng = np.random.default_rng(210)
    states = [obs(.06)]+[obs(x) for x in rng.uniform(0,.5,length)]
    stages = np.sort(rng.integers(0,4,length+1))
    stages[0] = 0
    values = []
    for i in range(length):
        terminal = i == length-1
        value,_ = shaped_reward(states[i],int(stages[i]),states[i+1],int(stages[i+1]),
            terminal=terminal,gate_success=terminal and outcome=='success',
            invalid_or_upstream=terminal and outcome=='invalid')
        values.append(value)
    base = 5 if outcome=='success' else -5 if outcome=='invalid' else 0
    expected = GAMMA**(length-1)*base-potential(states[0],0)
    assert np.dot(GAMMA**np.arange(length),values) == pytest.approx(expected,abs=1e-13)


def test_terminal_does_not_read_private_or_missing_final_observation():
    reward,terms = shaped_reward(obs(.06),2,None,None,terminal=True,gate_success=True)
    assert terms['potential_after']==0
    assert reward==pytest.approx(5-potential(obs(.06),2))


def test_reject_incompatible_stage_and_early_outcome_labels():
    with pytest.raises(ValueError,match='four-stage'):
        potential(obs(0),4)
    with pytest.raises(ValueError,match='before termination'):
        shaped_reward(obs(0),0,obs(0),0,gate_success=True)
