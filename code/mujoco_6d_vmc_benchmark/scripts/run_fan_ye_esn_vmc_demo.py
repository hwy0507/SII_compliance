#!/usr/bin/env python3
"""Run one WBC-aware physical validation fixture with Fan-Ye ESN-VMC.

The paired VMC-gated run shares exactly the same WBC, rod geometry, physics,
torque backend and task timing.  This is a development validation fixture, not
the frozen WBC-aware V4 final test.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from fan_ye_esn_policy import FanYeVMCPolicy
from run_benchmark import VMCConfig
from run_rod_perturbation_benchmark import run_episode
from screen_benchmark_v4_manifest import WARM_START_KAPPA


def _common(menagerie: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        VMCConfig(zeta=0.8),
        carriage_drive_k_translation=VMCConfig().carriage_drive_k_translation * 8.0,
        carriage_drive_k_rotation=VMCConfig().carriage_drive_k_rotation * 8.0,
    )
    return dict(
        menagerie=menagerie, kappa=np.asarray(WARM_START_KAPPA), output_dir=output_dir,
        render_gif=False, config=config, rod_stroke_m=0.170, contact_time_constant_s=0.015,
        recovery_kappa=np.asarray(WARM_START_KAPPA), recovery_ramp_s=0.08,
        recovery_drive_scale_factor=14.0 / 8.0, grasp_time_s=2.40, rod_start_time_s=0.955,
        explicit_translational_carriage=True, carriage_mass_kg=1.0, controller_mode="vmc_gated",
        rod_approach_side="negative_y", rod_height_m=0.540, rod_center_x_m=0.55, rod_center_y_m=0.0,
        remove_rod_when_disabled=True, recovery_gate_hold_s=0.28, recovery_gate_taper_s=0.04,
        reference_source="fixed_panda_wbc",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--model-npz", type=Path, required=True)
    parser.add_argument("--train-summary-json", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    baseline = run_episode(rod_enabled=True, **_common(args.menagerie, args.output_dir / "vmc_gated"))
    policy = FanYeVMCPolicy(args.model_npz, args.train_summary_json)
    esn = run_episode(
        rod_enabled=True, compliance_policy=policy, policy_update_hz=policy.config.update_hz,
        policy_contact_drive_scale=policy.config.contact_drive_scale,
        **_common(args.menagerie, args.output_dir / "fan_ye_esn_vmc"),
    )
    metrics = ("tracking", "motion", "torque", "rod_diagnostics", "phase_analysis", "task_validity")
    summary = {
        "stage": "WBC-aware ESN-VMC development validation fixture; not V4 final test",
        "fixture": {"rod_approach_side": "negative_y", "rod_start_time_s": 0.955, "rod_stroke_m": 0.170},
        "baseline_vmc_gated": {key: baseline[key] for key in metrics},
        "fan_ye_esn_vmc": {key: esn[key] for key in metrics},
        "policy_trace_contract": "trace records raw ESN action, bounded action, projected kappa and projected recovery drive; policy input remains q/qdot/wbc_task_twist only",
    }
    (args.output_dir / "fan_ye_esn_vmc_validation_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({
        "baseline_valid": baseline["task_validity"], "esn_valid": esn["task_validity"],
        "baseline_rejoin_s": baseline["phase_analysis"]["release_to_rejoin_latency_s"],
        "esn_rejoin_s": esn["phase_analysis"]["release_to_rejoin_latency_s"],
        "output_dir": str(args.output_dir),
    }, indent=2))


if __name__ == "__main__":
    main()
