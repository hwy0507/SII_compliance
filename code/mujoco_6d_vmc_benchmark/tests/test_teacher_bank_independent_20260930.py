"""Independent teacher-bank integrity tests; no MuJoCo rollouts are launched.

Synthetic files exercise the acceptance boundary, rather than assert successful
physics. In particular, the raw metrics and exported distillation labels must
not be trusted merely because the evaluator's JSON says strict_success=True.
"""
import json
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))
from teacher_bank_rollout_20260930 import audit
from wbc_velocity_residual_core import (
    VelocityResidualActionFilter,
    VelocityResidualSafetyConfig,
)


def test_reachable_filtered_action_labels_reproduce_filter_outputs():
    """Label replay must use an independent reset filter, including reversals."""
    safety = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    raw_filter = VelocityResidualActionFilter(safety)
    label_filter = VelocityResidualActionFilter(safety)
    limits = np.array([safety.maximum_linear_yield_mps] * 3
                      + [safety.maximum_angular_yield_radps] * 3)
    actions = np.random.default_rng(620).uniform(-1, 1, (256, 7))
    actions[30:60] = 1
    actions[60:90] = -1
    for request in actions:
        out = raw_filter.filter(request, .04)
        label = np.r_[(1 - out.wbc_scale) / (1 - safety.minimum_wbc_scale),
                      out.cartesian_yield_twist / limits]
        replay = label_filter.filter(label, .04)
        np.testing.assert_allclose(replay.cartesian_yield_twist,
                                   out.cartesian_yield_twist, atol=1e-14)
        assert replay.wbc_scale == pytest.approx(out.wbc_scale, abs=1e-14)


def synthetic_evidence(folder, *, corrupt_label=False, nonfinite_state=False,
                       substeps=550000, count=1375):
    """A self-consistent zero-load transcript sufficient to audit data integrity."""
    folder.mkdir()
    action = np.zeros((count, 7))
    six = np.zeros((count, 6))
    internal_offset = six.copy()
    if nonfinite_state:
        internal_offset[100, 0] = np.nan
    labels = action.copy()
    if corrupt_label:
        labels[100, 3] = .75
    np.savez_compressed(folder / "rollout.npz", observation=np.zeros((count, 48)),
                        applied_action=action)
    np.savez_compressed(folder / "teacher_internal.npz", request=action,
                        wrench=six, offset=internal_offset, velocity=six, filtered_wrench=six)
    np.savez_compressed(folder / "execution_chain.npz", request=action,
                        filtered_action=labels, yield_twist=six,
                        wbc_scale=np.ones(count), filter_dt=np.full(count, .04))
    metrics = folder / "rollout_metrics"
    metrics.mkdir()
    np.savez_compressed(metrics / "substep_metrics.npz",
                        dt=np.full(substeps, .0001),
                        time=(np.arange(substeps) + 1) * .0001,
                        error=np.zeros((substeps, 3), dtype=np.float32),
                        qfrc_actuator=np.zeros((substeps, 7), dtype=np.float32),
                        twist=np.zeros((substeps, 6), dtype=np.float32))
    full = count == 1375
    result = dict(task_success=full, strict_success=full, contact_coverage_valid=True,
                  abort_reason=None if full else 'global_penetration_exceeded_2mm',
                  execution_complete=full, full_task_horizon_completed=full,
                  task_events=[dict(stage="retreat", time_s=1.)],
                  stats=dict(events={"office_v5_corner_face": dict(duration_s=1.)},
                             contact_diagnostics=dict(corner_target_by_stage={}),
                             max_external_penetration_m=0.),
                  metrics=dict(position_rmse_3d_m=0.,
                               generalized_actuator_torque_peak_nm=0.,
                               linear_speed_peak_mps=0.))
    (folder / "rollout.json").write_text(json.dumps(result))
    (folder / "rollout.mjb").write_bytes(b"integrity-test-not-a-physical-model")
    request = dict(teacher={}, fixture=dict(category="passive_corner", split="train",
                                           id="synthetic_integrity_test"))
    # Synthetic observer calls construct schema-valid exposure; no physics claim.
    from teacher_bank_exposure_20260930 import TrainingExposure
    exposure = TrainingExposure(request['fixture'])
    for i in range(count * 10):
        exposure.record(.0001 + i * .004, .004, 1. if i in (250, 251) else 0.,
                        [0., 0., .0002 * i], 3)
    exposure.save(folder)
    return request


def test_consistent_synthetic_evidence_reaches_acceptance_boundary(tmp_path):
    """Negative cases below must fail for corruption, not missing fixtures."""
    folder = tmp_path / "consistent-evidence"
    request = synthetic_evidence(folder)
    result = audit(tmp_path, request, folder)
    assert result['eligible']
    assert result['substeps'] == 550000
    assert result['replay_max_abs'] == 0.


def test_audit_rejects_corrupted_exported_distillation_label(tmp_path):
    folder = tmp_path / "corrupt-label"
    request = synthetic_evidence(folder, corrupt_label=True)
    with pytest.raises((AssertionError, ValueError, RuntimeError)):
        audit(tmp_path, request, folder)


def test_audit_rejects_incomplete_physical_substep_evidence(tmp_path):
    folder = tmp_path / "incomplete-physics"
    request = synthetic_evidence(folder, substeps=2)
    with pytest.raises((AssertionError, ValueError, RuntimeError)):
        audit(tmp_path, request, folder)


def test_audit_rejects_nan_in_recorded_teacher_state(tmp_path):
    folder = tmp_path / "nonfinite-state"
    request = synthetic_evidence(folder, nonfinite_state=True)
    with pytest.raises((AssertionError, ValueError, RuntimeError)):
        audit(tmp_path, request, folder)


def test_expected_physical_abort_is_retained_as_failure_not_pipeline_crash(tmp_path):
    """Unsafe candidates are data, whereas corrupt evidence is an audit error."""
    folder = tmp_path / "physical-abort"
    request = synthetic_evidence(folder, count=50, substeps=20000)
    result = audit(tmp_path, request, folder)
    assert not result['eligible']
    assert 'incomplete_horizon' in result['failure_reasons']
    assert 'physics_abort:global_penetration_exceeded_2mm' in result['failure_reasons']
    assert result['substeps'] == 20000
