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
from teacher_bank_rollout_20260930 import audit, audit_exposure_physics_binding, audit_observation_alignment
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
                        applied_action=action, neuron_qpos=action, qpos=action, qvel=action,
                        neuron_time=np.arange(count)*.04, time=(np.arange(count)+1)*.04)
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
        exposure.record(i * .004, .004, 1. if i in (250, 251) else 0.,
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


def binding_arrays():
    physics=dict(time=(np.arange(8)+1)*.001, dt=np.full(8,.001))
    exposure=dict(time=np.array([0.,.004]), interval_end=np.array([.004,.008]),
        dt=np.full(2,.004), terminal_time_s=np.array(.008), schema=np.array(2),
        person_physics=np.c_[np.arange(8)*.001, np.full(8,.001), np.zeros((8,4))])
    return exposure,physics


def test_exposure_must_cover_whole_physics_not_only_valid_early_prefix():
    exposure,physics=binding_arrays()
    config=dict(category='active_long',apparatus='person')
    assert audit_exposure_physics_binding(exposure,physics,config)['person_every_physical_step_verified']
    for name in ('time','interval_end','dt'):
        exposure[name]=exposure[name][:1]
    exposure['terminal_time_s']=np.array(.004)
    exposure['person_physics']=exposure['person_physics'][:4]
    with pytest.raises(AssertionError):
        audit_exposure_physics_binding(exposure,physics,config)


def test_schema2_person_cannot_replace_physical_samples_with_coarse_samples():
    exposure,physics=binding_arrays()
    exposure['person_physics']=np.c_[np.array([0.,.004]), np.full(2,.004), np.zeros((2,4))]
    with pytest.raises(AssertionError, match='raw count'):
        audit_exposure_physics_binding(exposure,physics,dict(category='active_long',apparatus='person'))


def test_encoder_observation_and_actor_time_must_match_saved_states():
    count=4
    pre=np.arange(count*7,dtype=float).reshape(count,7)*.001
    post=np.vstack([pre[1:],pre[-1]])
    post_velocity=post*.01
    obs=np.zeros((count,48));obs[:,:7]=pre;obs[1:,7:14]=post_velocity[:-1]
    data=dict(observation=obs,neuron_qpos=pre,qpos=post,qvel=post_velocity,
              neuron_time=np.arange(count)*.04,time=(np.arange(count)+1)*.04)
    assert audit_observation_alignment(data)['max_abs']==0.
    for name,index in [('observation',(1,7)),('neuron_qpos',(2,0)),('neuron_time',2)]:
        corrupted={k:v.copy() for k,v in data.items()}
        corrupted[name][index]+=.001
        with pytest.raises(AssertionError):
            audit_observation_alignment(corrupted)
