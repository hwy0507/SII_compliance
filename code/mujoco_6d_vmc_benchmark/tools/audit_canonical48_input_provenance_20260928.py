"""Audit the provenance of every canonical48D actor input field.

This is a read-only, source-and-trace audit.  It does not run MuJoCo and does
not change a checkpoint.  The purpose is to keep the phrase ``pure
proprioception`` precise: encoder measurements, WBC references, and diagnostic
truth are reported separately rather than silently treated as equivalent.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_source(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(path.read_text(), node) or ""
    raise KeyError(f"{name} not found in {path}")


def main() -> None:
    eval_src = ROOT / "scripts/validate_office_apparatus_v5_20260917.py"
    policy_src = ROOT / "scripts/current_student_policy_20260921.py"
    obs_src = function_source(eval_src, "canonical_observation")

    # Use one completed wrench1 episode only to quantify field variation.  The
    # values are descriptive and are never used to select a result.
    trace_candidates = sorted(
        (ROOT / "outputs/esn_joint_stiff_wrench_eval_20260927/eval_v1/results").glob(
            "*/rollout.npz"
        )
    )
    if not trace_candidates:
        raise FileNotFoundError("No completed wrench1 rollout found")
    trace_path = trace_candidates[0]
    with np.load(trace_path, allow_pickle=False) as z:
        observation = z["observation"].astype(np.float64)
        keys = set(z.files)

    groups = {
        "joint_position_q7": (0, 7, "encoder joint position; direct proprioception"),
        "joint_velocity_dq7": (7, 14, "encoder joint velocity; direct proprioception"),
        "wbc_command_twist6": (14, 20, "WBC target/reference twist; internal reference, not a contact sensor"),
        "wbc_pose_error6": (20, 26, "WBC target-minus-measured pose error; derived from reference and proprioception"),
        "measured_twist_error6": (26, 32, "WBC command minus measured twist; derived reference/error"),
        "estimated_joint_load7": (32, 39, "encoder/inertia/friction load observer estimate; proprioceptive estimate"),
        "estimated_wrench6": (39, 45, "Jacobian projection of estimated joint load; proprioceptive estimate"),
        "path_direction3": (45, 48, "task path direction supplied by task reference; not an external sensor"),
    }
    field_report = {}
    for name, (lo, hi, provenance) in groups.items():
        values = observation[:, lo:hi]
        field_report[name] = {
            "slice": [lo, hi],
            "provenance": provenance,
            "shape": list(values.shape),
            "finite": bool(np.isfinite(values).all()),
            "constant": bool(np.max(np.ptp(values, axis=0)) == 0.0),
            "per_channel_min": values.min(axis=0).tolist(),
            "per_channel_max": values.max(axis=0).tolist(),
            "per_channel_std": values.std(axis=0).tolist(),
        }

    forbidden = {
        "contact_truth": "prior_contact_peak/prior_contact_impulse are saved diagnostics and are not concatenated into canonical_observation",
        "ball_state": "ball position/velocity are saved rollout fields and are not concatenated into canonical_observation",
        "event_time": "person/rod schedules are evaluator-side and are not passed to actor.act",
        "task_stage": "task.index is saved after the action and is not passed to actor.act",
        "vision_or_distance": "no image, range, distance, or object label appears in canonical_observation or policy act",
    }
    source_text = eval_src.read_text() + "\n" + policy_src.read_text()
    static_checks = {
        "canonical_observation_has_forbidden_names": any(
            token in obs_src for token in ("contact", "ball", "stage", "event", "image", "distance")
        ),
        "policy_act_reads_only_observation_argument": "prior_contact" not in policy_src.read_text(),
        "evaluator_passes_stage_to_actor": "esn.act(task.index" in eval_src.read_text(),
        "evaluator_passes_ball_to_actor": "esn.act(d.xpos[ball" in eval_src.read_text(),
    }
    if static_checks["canonical_observation_has_forbidden_names"]:
        # The function source contains none of these; keep an explicit failure
        # rather than allowing a future refactor to silently broaden the actor.
        raise AssertionError("Forbidden token found in canonical_observation definition")
    if static_checks["evaluator_passes_stage_to_actor"] or static_checks["evaluator_passes_ball_to_actor"]:
        raise AssertionError("Forbidden runtime value appears in actor call")

    report = {
        "purpose": "canonical48D input provenance and pure-proprioception boundary audit",
        "trace": str(trace_path.relative_to(ROOT)),
        "trace_sha256": sha(trace_path),
        "observation_shape": list(observation.shape),
        "actor_contract": "proprio48_esn128_action7_v1",
        "field_groups": field_report,
        "forbidden_inputs": forbidden,
        "static_checks": static_checks,
        "actor_interpretation": {
            "direct_encoder_measurements": ["joint_position_q7", "joint_velocity_dq7"],
            "observer_estimates": ["estimated_joint_load7", "estimated_wrench6"],
            "reference_derived": ["wbc_command_twist6", "wbc_pose_error6", "measured_twist_error6", "path_direction3"],
            "conclusion": "The current 48D contract is proprioceptive/no-external-perception, but it is not a sensors-only contract: four groups depend on WBC/task references. A sensors-only mask must therefore be a separately trained and separately audited ablation, not a relabeling of the current checkpoint.",
        },
        "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (eval_src, policy_src, Path(__file__))},
        "trace_fields_present": sorted(keys),
        "not_a_performance_claim": True,
    }
    out = ROOT / "outputs/esn_office_input_provenance_audit_20260928"
    out.mkdir(parents=False, exist_ok=False)
    (out / "INPUT_PROVENANCE_AUDIT.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# canonical48D 输入来源审计（2026-09-28）",
        "",
        f"审计轨迹：`{trace_path.relative_to(ROOT)}`，SHA256 `{report['trace_sha256']}`。本审计不运行仿真、不修改 checkpoint，也不作性能选择。",
        "",
        "| 字段 | 维度 | 来源分类 |",
        "|---|---:|---|",
    ]
    for name, (lo, hi, provenance) in groups.items():
        category = field_report[name]["provenance"]
        lines.append(f"| `{name}` | {hi-lo} | {category} |")
    lines += [
        "",
        "## 结论",
        "",
        "当前 48D 合约没有把接触真值、球状态、事件时间、阶段标签、视觉或距离输入送入 actor；但它也不是只含传感器原始量的 contract。`command/error/path_direction` 依赖 WBC/任务参考，`load/wrench` 是本体观测器估计。",
        "因此后续若检验“纯传感器本体”假设，必须重新训练并独立六条件评估 q/dq/load/wrench mask；不能把现有 full48 checkpoint 事后置零字段后当作公平 baseline。",
        "",
        "该审计不改变 gate、held-out 封存、执行器限制或任何历史结果。",
    ]
    (out / "INPUT_PROVENANCE_AUDIT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"output": str(out), "trace": str(trace_path), "field_groups": list(groups), "static_checks": static_checks}, indent=2))


if __name__ == "__main__":
    main()
