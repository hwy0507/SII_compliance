import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from panel_policy_ablations_20260923 import lowpass_025, no_x_yield


class CountingPolicy:
    kind = 'test_policy'
    slide = 1.5

    def __init__(self):
        self.calls = 0
        self.output = np.arange(7, dtype=float) / 7

    def act(self, *args, **kwargs):
        self.calls += 1
        return self.output

    def reset(self):
        self.calls = 0


def test_channel_intervention_calls_base_once_and_does_not_mutate_it():
    base = CountingPolicy()
    wrapped = no_x_yield(base)
    result = wrapped.act(np.zeros(48))
    assert base.calls == 1
    assert result[1] == 0
    np.testing.assert_array_equal(result[[0, 2, 3, 4, 5, 6]], base.output[[0, 2, 3, 4, 5, 6]])
    assert base.output[1] == 1 / 7


def test_lowpass_is_causal_and_forwards_teacher_arguments_and_attributes():
    base = CountingPolicy()
    wrapped = lowpass_025(base)
    assert wrapped.slide == base.slide
    first = wrapped.act(np.zeros(6), np.zeros(6), np.zeros(6), np.zeros(3), .04)
    np.testing.assert_allclose(first, .25 * base.output)
    second = wrapped.act(np.zeros(48))
    np.testing.assert_allclose(second, .4375 * base.output)
    assert base.calls == 2
    wrapped.reset()
    assert base.calls == 0
    np.testing.assert_allclose(wrapped.act(np.zeros(48)), first)
