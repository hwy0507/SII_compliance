"""Regression tests for the reservoir-timed slowdown-only ESN contract."""

import sys
from pathlib import Path

import numpy as np


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from current_student_policy_20260921 import load_current  # noqa: E402


def _checkpoint(path: Path) -> None:
    base_bias = np.zeros(7)
    base_bias[0] = -10.0
    np.savez_compressed(
        path,
        contract="proprio48_esn128_action7_hierarchical_margin_slowdown_pulsed_v1",
        mean=np.zeros(48), std=np.ones(48), win=np.zeros((128, 49)),
        w=np.zeros((128, 128)), leak=np.ones(128), input_mask=np.ones(48),
        alpha=np.array(1.0), output_gain=np.array(1.0),
        fmean=np.zeros(176), fstd=np.ones(176), w1=np.zeros((128, 176)), b1=np.zeros(128),
        base_yield_w2=np.zeros((7, 128)), base_yield_b2=base_bias,
        base_clearance_w2=np.zeros((7, 128)), base_clearance_b2=base_bias,
        base_gate_w1=np.zeros((16, 128)), base_gate_b1=np.zeros(16),
        base_gate_w2=np.zeros(16), base_gate_b2=np.array(-10.0),
        margin_w2=np.ones((7, 128)), margin_b2=np.ones(7),
        selector_w1=np.zeros((16, 128)), selector_b1=np.zeros(16),
        selector_w2=np.zeros(16), selector_b2=np.array(10.0),
        selector_confirm_steps=np.array(2), selector_pulse_steps=np.array(3),
        selector_slowdown_floor=np.array(0.75),
    )


def test_slowdown_pulse_keeps_base_yield_and_resets(tmp_path):
    checkpoint = tmp_path / "slowdown_pulse.npz"
    _checkpoint(checkpoint)
    policy = load_current(checkpoint)
    observation = np.zeros(48)
    actions = np.stack([policy.act(observation) for _ in range(5)])

    np.testing.assert_allclose(actions[:, 1:], 0.0)
    assert actions[0, 0] < 0.001
    np.testing.assert_allclose(actions[1:4, 0], 0.75)
    assert actions[4, 0] < 0.001

    policy.reset()
    assert policy.selector_positive_steps == 0
    assert policy.selector_pulse_remaining == 0
    assert not policy.selector_pulse_used
    np.testing.assert_array_equal(policy.act(observation), actions[0])


def test_vertical_pulse_changes_only_z_yield(tmp_path):
    source = tmp_path / "slowdown_pulse.npz"
    checkpoint = tmp_path / "vertical_pulse.npz"
    _checkpoint(source)
    with np.load(source, allow_pickle=False) as data:
        payload = {key: data[key].copy() for key in data.files
                   if key not in ("contract", "selector_slowdown_floor")}
    np.savez_compressed(
        checkpoint,
        **payload,
        contract="proprio48_esn128_action7_hierarchical_margin_vertical_pulsed_v1",
        selector_vertical_floor=np.array(0.65),
    )
    policy = load_current(checkpoint)
    observation = np.zeros(48)
    actions = np.stack([policy.act(observation) for _ in range(5)])

    assert actions[0, 3] == 0.0
    np.testing.assert_allclose(actions[1:4, 3], 0.65)
    assert actions[4, 3] == 0.0
    np.testing.assert_allclose(actions[:, [1, 2, 4, 5, 6]], 0.0)
    assert np.all(actions[:, 0] < 0.001)
