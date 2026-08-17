#!/usr/bin/env python3
"""Run a frozen Direct ESN inside the fixed-WBC MuJoCo environment."""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from direct_esn_compliance import DirectESNController
from vmc_compliance_baseline import VMCComplianceAdapter, load_controller
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture, default_velocity_residual_fixtures


def resolve_override_fixture(
    rod_stroke_m: float | None,
    rod_height_m: float | None,
    rod_start_time_s: float | None,
    grasp_time_s: float | None,
    fixture_index: int,
    rod_approach_side: str | None = None,
    rod_cycles: int | None = None,
    cycle_period_s: float | None = None,
) -> tuple[tuple[VelocityResidualFixture, ...], int]:
    """Build a single-fixture pool when any physical rod override is supplied.

    Overrides start from the indexed default fixture so that unspecified
    fields keep that fixture's values; this keeps generated expert traces
    reproducible while the held-out evaluation fixtures stay untouched.
    """

    provided = {
        "rod_stroke_m": rod_stroke_m, "rod_height_m": rod_height_m,
        "rod_start_time_s": rod_start_time_s, "grasp_time_s": grasp_time_s,
        "rod_approach_side": rod_approach_side, "rod_cycles": rod_cycles,
        "cycle_period_s": cycle_period_s,
    }
    if all(value is None for value in provided.values()):
        return default_velocity_residual_fixtures(), fixture_index
    base = default_velocity_residual_fixtures()[fixture_index]
    overrides = {key: value for key, value in provided.items() if value is not None}
    fixture = replace(base, **overrides)
    if fixture.rod_cycles < 1:
        raise ValueError("rod_cycles must be at least one")
    return (fixture,), 0


def run_episode(controller_path: Path | None, *, menagerie: Path, fan_ye_model: Path | None, fan_ye_summary: Path | None, fixture_index: int, rod_enabled: bool, seed: int, fixed_wbc: bool = False, enable_rejoin_fade: bool = False, rejoin_fade_maximum: float = 0.85, override_fixture: VelocityResidualFixture | None = None, yield_smoothing_alpha: float = 1.0, mirror_gate: bool = False, mirror_gate_channels: str = "y") -> tuple[dict, list[dict]]:
    controller = None if fixed_wbc else load_controller(controller_path)  # type: ignore[arg-type]
    if isinstance(controller, VMCComplianceAdapter) and enable_rejoin_fade:
        raise ValueError("rejoin fade is a Direct-ESN-only ablation; the VMC baseline has no fade knob")
    if controller is not None and not isinstance(controller, VMCComplianceAdapter) and enable_rejoin_fade:
        controller.config = replace(
            controller.config, rejoin_fade_enabled=True, rejoin_fade_maximum=rejoin_fade_maximum,
        )
    if controller is not None and not isinstance(controller, VMCComplianceAdapter) and yield_smoothing_alpha != 1.0:
        controller.config = replace(controller.config, yield_smoothing_alpha=yield_smoothing_alpha)
    if controller is not None and not isinstance(controller, VMCComplianceAdapter) and mirror_gate:
        controller.config = replace(controller.config, mirror_gate_enabled=True, mirror_gate_channels=mirror_gate_channels)
    fixtures = None if override_fixture is None else (override_fixture,)
    env = PandaWBCVelocityResidualEnv(
        menagerie=menagerie, fan_ye_model_npz=fan_ye_model,
        fan_ye_train_summary_json=fan_ye_summary, observation_mode="direct_esn",
        rod_enabled=rod_enabled, seed=seed, fixtures=fixtures,
    )
    if isinstance(controller, VMCComplianceAdapter):
        controller.set_yield_limits(
            env.safety_config.maximum_linear_yield_mps,
            env.safety_config.maximum_angular_yield_radps,
        )
    try:
        env.reset(seed=seed, options={"fixture_index": fixture_index})
        if controller is not None:
            controller.reset()
        trace = []
        terminated = False
        info = {}
        while not terminated:
            diagnostic = env.diagnostics()
            impulse_before = float(env.contact_impulse)
            contact_wrench = getattr(env, "last_action_contact_wrench_world", None)
            # Only the force-feedback VMC variant may read the measured wrench;
            # the proprioceptive variant and the ESN never receive it.
            vmc_wrench = None
            if isinstance(controller, VMCComplianceAdapter) and controller.baseline.config.drive_source == "force_feedback":
                vmc_wrench = None if contact_wrench is None else np.asarray(contact_wrench).copy()
            if controller is None:
                action_vector = np.zeros(7, dtype=float)
                wbc_scale = 1.0
                yielding_twist = np.zeros(6, dtype=float)
                raw_readout = np.zeros(7, dtype=float)
            elif isinstance(controller, VMCComplianceAdapter):
                action = controller.act(
                    diagnostic["joint_position"], diagnostic["joint_velocity"], diagnostic["nominal_twist"],
                    pose_error=diagnostic["wbc_pose_error"], twist_error=diagnostic["wbc_twist_error"],
                    contact_wrench_world=vmc_wrench,
                )
                action_vector = action.bounded_filter_action
                wbc_scale = action.wbc_scale
                yielding_twist = action.yielding_twist
                raw_readout = action.raw_readout
            else:
                action = controller.act(
                    diagnostic["joint_position"], diagnostic["joint_velocity"], diagnostic["nominal_twist"],
                    pose_error=diagnostic["wbc_pose_error"], twist_error=diagnostic["wbc_twist_error"],
                )
                action_vector = action.bounded_filter_action
                wbc_scale = action.wbc_scale
                yielding_twist = action.yielding_twist
                raw_readout = action.raw_readout
            _, _, terminated, _, info = env.step(action_vector)
            trace.append({
                "time_s": diagnostic["time_s"], "wbc_scale": wbc_scale,
                "yielding_twist": np.asarray(yielding_twist).copy(), "raw_readout": np.asarray(raw_readout).copy(),
                "bounded_action": np.asarray(action_vector).copy(),
                "joint_position": diagnostic["joint_position"].copy(),
                "joint_velocity": diagnostic["joint_velocity"].copy(),
                "wbc_task_twist": diagnostic["nominal_twist"].copy(),
                "pose_error": diagnostic["wbc_pose_error"].copy(),
                "wbc_twist_error": diagnostic["wbc_twist_error"].copy(),
                "ee_position": diagnostic["ee_position"].copy(), "nominal_position": diagnostic["nominal_position"].copy(),
                "wbc_pose_error": diagnostic["wbc_pose_error"].copy(), "wbc_twist_error": diagnostic["wbc_twist_error"].copy(),
                # These diagnostics are written only to the offline trace;
                # they are never passed to the Direct ESN observation.
                "contact_force": float(env.last_action_contact_force),
                "contact_seen": bool(env.last_action_contact_seen),
                "contact_penetration_m": float(env.last_action_contact_penetration),
                "contact_impulse_delta_ns": float(env.contact_impulse - impulse_before),
            })
        return info, trace
    finally:
        env.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--controller", type=Path, default=None)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--fan-ye-model", type=Path, default=None)
    parser.add_argument("--fan-ye-summary", type=Path, default=None)
    parser.add_argument("--fixture-index", type=int, default=0)
    parser.add_argument("--seed", type=int, default=20260817)
    parser.add_argument("--no-rod", action="store_true")
    parser.add_argument("--fixed-wbc", action="store_true", help="record a zero-action fixed-WBC neutral trace")
    parser.add_argument("--rod-stroke-m", type=float, default=None, help="override the indexed fixture rod stroke")
    parser.add_argument("--rod-height-m", type=float, default=None, help="override the indexed fixture rod contact height")
    parser.add_argument("--rod-start-time-s", type=float, default=None, help="override the indexed fixture rod start time")
    parser.add_argument("--rod-approach-side", type=str, default=None,
                        choices=("negative_x", "positive_x", "negative_y", "positive_y", "negative_z", "positive_z"))
    parser.add_argument("--rod-cycles", type=int, default=None)
    parser.add_argument("--cycle-period-s", type=float, default=None)
    parser.add_argument("--grasp-time-s", type=float, default=None, help="override the indexed fixture grasp time")
    parser.add_argument("--enable-rejoin-fade", action="store_true")
    parser.add_argument("--mirror-gate", action="store_true", help="enable the mirror-equivariant action gate")
    parser.add_argument("--mirror-gate-channels", type=str, default="y", choices=("y", "full"))
    parser.add_argument("--yield-smoothing-alpha", type=float, default=1.0,
                        help="first-order low-pass on the ESN yielding twist (1.0 disables)")
    parser.add_argument("--rejoin-fade-maximum", type=float, default=0.85)
    parser.add_argument("--output-summary", type=Path, required=True)
    parser.add_argument("--output-trace", type=Path, required=True)
    args = parser.parse_args()
    fixtures, resolved_index = resolve_override_fixture(
        args.rod_stroke_m, args.rod_height_m, args.rod_start_time_s, args.grasp_time_s, args.fixture_index,
        rod_approach_side=args.rod_approach_side, rod_cycles=args.rod_cycles,
        cycle_period_s=args.cycle_period_s,
    )
    override_fixture = None if len(fixtures) > 1 else fixtures[0]
    info, trace = run_episode(
        args.controller, menagerie=args.menagerie, fan_ye_model=args.fan_ye_model,
        fan_ye_summary=args.fan_ye_summary, fixture_index=resolved_index,
        rod_enabled=not args.no_rod, seed=args.seed, fixed_wbc=args.fixed_wbc,
        enable_rejoin_fade=args.enable_rejoin_fade, rejoin_fade_maximum=args.rejoin_fade_maximum,
        override_fixture=override_fixture, yield_smoothing_alpha=args.yield_smoothing_alpha,
        mirror_gate=args.mirror_gate, mirror_gate_channels=args.mirror_gate_channels,
    )
    if override_fixture is not None:
        info = dict(info)
        info["override_fixture"] = {
            "base_fixture_index": args.fixture_index,
            "rod_stroke_m": override_fixture.rod_stroke_m,
            "rod_height_m": override_fixture.rod_height_m,
            "rod_start_time_s": override_fixture.rod_start_time_s,
            "grasp_time_s": override_fixture.grasp_time_s,
        }
    args.output_summary.parent.mkdir(parents=True, exist_ok=True)
    args.output_trace.parent.mkdir(parents=True, exist_ok=True)
    args.output_summary.write_text(json.dumps(info, indent=2, default=lambda value: value.tolist() if isinstance(value, np.ndarray) else value) + "\n")
    np.savez_compressed(
        args.output_trace,
        time_s=np.asarray([item["time_s"] for item in trace]),
        wbc_scale=np.asarray([item["wbc_scale"] for item in trace]),
        yielding_twist=np.asarray([item["yielding_twist"] for item in trace]),
        raw_readout=np.asarray([item["raw_readout"] for item in trace]),
        bounded_action=np.asarray([item["bounded_action"] for item in trace]),
        joint_position=np.asarray([item["joint_position"] for item in trace]),
        joint_velocity=np.asarray([item["joint_velocity"] for item in trace]),
        wbc_task_twist=np.asarray([item["wbc_task_twist"] for item in trace]),
        pose_error=np.asarray([item["pose_error"] for item in trace]),
        # The rollout adapter intentionally does not expose contact force to
        # the student. These values are label-side diagnostics for offline
        # phase analysis only.
        contact_force=np.asarray([item["contact_force"] for item in trace]),
        contact_seen=np.asarray([item["contact_seen"] for item in trace], dtype=bool),
        contact_penetration_m=np.asarray([item["contact_penetration_m"] for item in trace]),
        contact_impulse_delta_ns=np.asarray([item["contact_impulse_delta_ns"] for item in trace]),
        contact_normal=np.tile(np.array([0.0, 1.0, 0.0]), (len(trace), 1)),
        contact_duration_s=np.zeros(len(trace)),
        signed_distance_m=np.full(len(trace), 0.02),
        ee_position=np.asarray([item["ee_position"] for item in trace]),
        nominal_position=np.asarray([item["nominal_position"] for item in trace]),
        wbc_pose_error=np.asarray([item["wbc_pose_error"] for item in trace]),
        wbc_twist_error=np.asarray([item["wbc_twist_error"] for item in trace]),
    )
    print(json.dumps(info, indent=2, default=lambda value: value.tolist() if isinstance(value, np.ndarray) else value))


if __name__ == "__main__":
    main()
