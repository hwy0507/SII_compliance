"""Meaningful servo clock tests: integration refinement must not change reward."""
import numpy as np
from baseline_repair_reward_clock_20261009 import slew_cost_rows, remaining_slew_bound


def main():
    rates = np.array([700.,700.,700.,700.,160.,160.,160.])
    levels = np.arange(20.)[:,None]*rates[None,:]*.004
    coarse = np.repeat(levels, 40, axis=0)
    fine = np.repeat(levels, 80, axis=0)
    expected = 19*7*.004/55
    for trace in (coarse, fine):
        value = slew_cost_rows(trace, rates)
        np.testing.assert_allclose(value.sum(), expected, rtol=1e-14)
        cut = len(trace)//2
        np.testing.assert_allclose(value.sum(), slew_cost_rows(trace[:cut], rates).sum()+
            slew_cost_rows(trace[cut:], rates, trace[cut-1]).sum(), rtol=1e-14)
        assert slew_cost_rows(np.repeat(levels[10:11], 80, axis=0), rates).sum() == 0.
    assert remaining_slew_bound(55.) == 0.
    assert remaining_slew_bound(54.99995) == 7*.004/55
    assert remaining_slew_bound(0.) == 7.
    try: slew_cost_rows(np.vstack((np.zeros(7), 1.01*rates*.004)), rates)
    except AssertionError: pass
    else: raise AssertionError('An out-of-bound servo jump was silently accepted')
    print('PASS: physics refinement invariant, interval-additive, no initial jump, partial-update bound, violation rejected')


if __name__ == '__main__': main()
