"""Audit request -> common action filter -> physical actuator chain.

Read-only replay of the already completed wrench1 development episodes.  Contact
truth is used only to stratify archived samples and never enters an actor or a
new rollout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(actions: np.ndarray) -> dict[str, np.ndarray]:
    config = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    filt = VelocityResidualActionFilter(config)
    scale, twist, clipped, saturated, slew = [], [], [], [], []
    for action in actions:
        row = filt.filter(action, .04)
        scale.append(row.wbc_scale)
        twist.append(row.cartesian_yield_twist)
        clipped.append(row.raw_action_clipped)
        saturated.append(row.amplitude_saturated)
        slew.append(row.slew_limited)
    return {"wbc_scale": np.asarray(scale), "yield_twist": np.asarray(twist),
            "clipped": np.asarray(clipped), "amplitude_saturated": np.asarray(saturated),
            "slew_limited": np.asarray(slew)}


def summarize_mask(mask: np.ndarray, raw: np.ndarray, filtered: dict[str, np.ndarray]) -> dict:
    if not np.any(mask):
        return {"samples": 0}
    maximum = np.array([.32, .32, .32, .60, .60, .60])
    desired = np.clip(raw[:, 1:], -1., 1.) * maximum
    delta = filtered["yield_twist"] - desired
    return {
        "samples": int(mask.sum()),
        "duration_s": float(mask.sum() * .04),
        "raw_action_peak_abs": float(np.max(np.abs(raw[mask]))),
        "raw_action_rms": float(np.sqrt(np.mean(raw[mask] ** 2))),
        "filtered_yield_peak_linear_mps": float(np.max(np.linalg.norm(filtered["yield_twist"][mask, :3], axis=1))),
        "filtered_yield_peak_angular_radps": float(np.max(np.linalg.norm(filtered["yield_twist"][mask, 3:], axis=1))),
        "filtered_wbc_feedback_scale_min": float(np.min(filtered["wbc_scale"][mask])),
        "slew_limited_fraction": float(np.mean(filtered["slew_limited"][mask])),
        "amplitude_saturated_fraction": float(np.mean(filtered["amplitude_saturated"][mask])),
        "filtered_vs_desired_yield_rmse": float(np.sqrt(np.mean(delta[mask] ** 2))),
    }


def main() -> None:
    source = ROOT / "outputs/esn_joint_stiff_wrench_eval_20260927/eval_v1/results"
    out = ROOT / "outputs/esn_office_action_execution_chain_v2_20260928"
    if out.exists():
        raise FileExistsError(out)
    out.mkdir()
    rows = []
    for folder in sorted(source.iterdir()):
        if not (folder / "rollout.npz").exists():
            continue
        result = json.loads((folder / "rollout.json").read_text())
        with np.load(folder / "rollout.npz", allow_pickle=False) as z:
            raw = z["esn_action"].astype(np.float64)
            submitted = z["applied_action"].astype(np.float64)
            np.testing.assert_array_equal(raw, submitted)
            contact = z["prior_contact_peak"].astype(np.float64)
            times = z["neuron_time"].astype(np.float64)
            wrench_observation = z["observation"][:, 39:45].astype(np.float64)
        filtered = replay(raw)
        with np.load(folder / "rollout_metrics/substep_metrics.npz", allow_pickle=False) as z:
            torque_peak = float(np.max(np.abs(z["qfrc_actuator"])))
            speed_peak = float(np.max(np.linalg.norm(z["twist"][:, :3].astype(np.float64), axis=1)))
        # prior_contact_peak is diagnostic truth for the preceding physics
        # interval. It is used only in this offline report.
        external = np.any(contact[:, :3] > .05, axis=1)
        ball = contact[:, 0] > .05
        person = contact[:, 1] > .05
        rod = contact[:, 2] > .05
        row = {
            "case": folder.name,
            "task": result["task_success"],
            "strict": result["strict_success"],
            "external_penetration_mm": 1000 * result["stats"]["max_external_penetration_m"],
            "generalized_actuator_torque_peak_nm": torque_peak,
            "ee_linear_speed_peak_mps": speed_peak,
            "all": summarize_mask(np.ones(len(raw), dtype=bool), raw, filtered),
            "preceding_external_contact_interval": summarize_mask(external, raw, filtered),
            "preceding_ball_contact_interval": summarize_mask(ball, raw, filtered),
            "preceding_person_contact_interval": summarize_mask(person, raw, filtered),
            "preceding_rod_contact_interval": summarize_mask(rod, raw, filtered),
            "first_nonzero_wrench_observation_s": (float(times[np.flatnonzero(np.any(np.abs(wrench_observation) > 0, axis=1))[0]])
                                                   if np.any(np.abs(wrench_observation) > 0) else None),
            "hashes": {p.name: sha(p) for p in (folder / "rollout.json", folder / "rollout.npz",
                                                  folder / "rollout_metrics/substep_metrics.npz")},
        }
        rows.append(row)
    shifted = next(r for r in rows if r["case"].endswith("shift_plus"))
    report = {
        "purpose": "read-only action execution chain audit for the fixed wrench1 candidate",
        "actor_request": "saved esn_action; exactly equals evaluator submitted applied_action",
        "common_filter": "VelocityResidualActionFilter with office maximum_linear_yield_mps=.32 and unchanged angular/rate limits",
        "physical_execution": "independently recomputed generalized actuator torque and end-effector speed from physics substeps",
        "direct_esn_semantics": "filtered slowdown is consumed as next-step WBC feedback scaling; the composed command stores wbc_scale=1 to avoid double counting",
        "truth_used_by_actor": False,
        "contact_truth_used_for_offline_stratification_only": True,
        "rows": rows,
        "conclusions": [
            "No saved action exceeded the normalized amplitude bounds; amplitude saturation is zero in all six episodes.",
            "Whole-episode slew limiting affects at most 0.4% of 25 Hz decisions, so it is not the dominant rod-exposure bottleneck.",
            "The one archived 25 Hz interval following each ball-contact prefix is slew-limited; this is a post-contact response and cannot change the already completed sub-millisecond first impact.",
            f"In shifted-plus rod-contact-stratified samples the filter exactly reaches the requested yield (RMSE {shifted['preceding_rod_contact_interval']['filtered_vs_desired_yield_rmse']:.3g}); the weak peak raw request {shifted['preceding_rod_contact_interval']['raw_action_peak_abs']:.6f}, rather than common-filter clipping, is the actionable state-coverage/readout signal.",
        ],
        "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in
                          (Path(__file__), ROOT / "scripts/wbc_velocity_residual_core.py",
                           ROOT / "scripts/audited_velocity_env.py",
                           ROOT / "scripts/validate_office_apparatus_v5_20260917.py")},
        "limitations": [
            "The filter replay is exact for request clipping and slew state, but is not a counterfactual dynamics rollout.",
            "Generalized actuator torque is downstream of WBC, Jacobians, bias compensation, torque projection, and contact dynamics; it is not equal to action7.",
            "Contact-stratified rows are diagnostics and cannot be used by the deployed actor.",
        ],
    }
    (out / "ACTION_EXECUTION_CHAIN_AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = ["# wrench1 请求—过滤—物理执行链审计", "",
             "| 条件 | task/strict | slew-limited | action peak | filtered linear peak m/s | torque peak Nm | speed peak m/s |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for row in rows:
        all_ = row["all"]
        lines.append(f"| {row['case']} | {int(row['task'])}/{int(row['strict'])} | {all_['slew_limited_fraction']:.3f} | {all_['raw_action_peak_abs']:.3f} | {all_['filtered_yield_peak_linear_mps']:.4f} | {row['generalized_actuator_torque_peak_nm']:.3f} | {row['ee_linear_speed_peak_mps']:.6f} |")
    lines += ["", "`esn_action` 与提交给共同接口的 `applied_action` 逐元素完全一致；共同接口随后执行幅值和变化率限制。物理力矩来自子步 `qfrc_actuator`，不能与 action7 混称。", "",
              "六回合均无 action 幅值饱和，完整回合的 slew-limited 比例最高仅 0.4%。shifted-plus 的推杆接触分层中，过滤后 yield 与请求值 RMSE 为 0，而 raw action 峰值仅约 0.040：该曝光失败更指向访问状态/读出响应不足，不是共同接口削弱了一个强请求。球撞后的首个 25 Hz 响应区间均受变化率限制，但首次亚毫秒碰撞已在观测到来前结束，不能据此宣称调大 slew 会解决 hard 首峰。", ""]
    (out / "ACTION_EXECUTION_CHAIN_AUDIT.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
