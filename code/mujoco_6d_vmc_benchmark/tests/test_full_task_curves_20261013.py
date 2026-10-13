import numpy as np

from plot_full_task_curves_20261013 import trailing_rms


def test_causal_weighted_window_initial_and_trailing_samples():
    duration = np.array([.1, .1, .1, .1])
    squared = np.array([1., 9., 25., 49.])
    actual = trailing_rms(squared*duration, duration, 2)
    np.testing.assert_allclose(actual, np.sqrt([1., 5., 17., 37.]))


def test_partial_final_display_bin_keeps_exact_raw_sample_window():
    # Reporting at samples3,6,7 (last display bin short) must still use4 raw
    # samples at the final point, rather than only the last2 display bins.
    duration = np.full(7, .05)
    squared = np.arange(1., 8.)**2
    actual = trailing_rms(squared*duration, duration, 4, np.array([3,6,7]))
    np.testing.assert_allclose(actual, np.sqrt([14/3, 86/4, 126/4]))
