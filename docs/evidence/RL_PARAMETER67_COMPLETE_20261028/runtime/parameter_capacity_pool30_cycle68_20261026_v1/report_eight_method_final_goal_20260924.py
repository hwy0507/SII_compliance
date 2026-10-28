"""Offline 48-episode final-goal and exposure audit; no simulator imports or steps.

Run from the benchmark directory. Only the two requested report outputs are written.
The final goal is constructed from archived task source and each command's panel
configuration, including for policies that never visited the final task stage.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np


METHODS = ("impedance_k900_z1.2", "admittance_k150_z0.7", "vmc", "mlp", "esn",
           "ppo8192", "zero", "ppo_potential8192")
SEEDS = range(9400, 9406)
BASE = Path("outputs/server_archive_20260923")
VALIDATION = BASE / "measured_campaign/fixed_budget/validation"
DENSE = Path("outputs/ppo_dgx_matched_archive_20260924_r1/evaluation")
POTENTIAL = Path("outputs/ppo_potential_dgx_archive_20260924_r1/evaluation")
SOURCE = BASE / "source_fixed_budget/scripts"
SOURCE_NAMES = ("primitive_contact_scene_v7_20260917.py",
                "run_primitive_teacher_v7_20260917.py", "run_panel_push_20260920.py")


def read(path):
    return json.loads(path.read_text())


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def compile_goal_constructor():
    """Execute only extracted pure task layout/initializer, never source modules."""
    layout_tree = ast.parse((SOURCE / SOURCE_NAMES[0]).read_text())
    task_tree = ast.parse((SOURCE / SOURCE_NAMES[1]).read_text())
    panel_tree = ast.parse((SOURCE / SOURCE_NAMES[2]).read_text())
    layout = next(n for n in layout_tree.body if isinstance(n, ast.FunctionDef) and n.name == "task_layout")
    task_class = next(n for n in task_tree.body if isinstance(n, ast.ClassDef) and n.name == "BlindTask")
    initializer = next(n for n in task_class.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    namespace = {"np": np}
    exec(compile(ast.Module(body=[layout, initializer], type_ignores=[]), "archived_pure_goal_constructor", "exec"), namespace)
    panel_assignments = {}
    for node in ast.walk(panel_tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = ast.unparse(node.targets[0])
            if target in ("task.goals[3][2]", "task.goals[3][0]"):
                require(target not in panel_assignments, "Ambiguous goal override")
                panel_assignments[target] = node.value
    require(set(panel_assignments) == {"task.goals[3][2]", "task.goals[3][0]"}, "Missing archived goal overrides")

    def construct(panel):
        initial, grasp = namespace["task_layout"](SimpleNamespace(kind="push"))
        task = SimpleNamespace(direction=lambda: np.array([0., 0., 1.]))
        namespace["__init__"](task, initial, grasp, np.eye(3), None, None, None, settle=False, extended=True)
        goals = np.asarray(task.goals[:4]).copy()
        for axis, target in ((2, "task.goals[3][2]"), (0, "task.goals[3][0]")):
            if axis == 0 and "lift_goal_x" not in panel:
                continue
            goals[3, axis] = eval(compile(ast.Expression(panel_assignments[target]), "archived_panel_goal", "eval"), {"PANEL": panel, "float": float})
        return goals
    return construct


def stage_at(times, events):
    stages = np.zeros(len(times), dtype=int)
    for event in events:
        stages[times >= event["t"] - 1e-8] = event["stage"]
    return stages


def distribution(values):
    a = np.asarray(values, dtype=float)
    return dict(values=a.tolist(), mean=float(a.mean()), std_population=float(a.std(ddof=0)),
                minimum=float(a.min()), median=float(np.median(a)), maximum=float(a.max()))


def audit():
    hashes = {}

    def record(path):
        value = sha(path)
        hashes[str(path)] = value
        return value

    original_path = Path("docs/PPO_POTENTIAL_DGX_RESULTS_20260924.json")
    original = read(original_path)
    record(original_path)
    old = {(r["method"], r["fixture"]["seed"]): r for r in original["rows"]}
    require(len(original["rows"]) == 48 and set(old) == {(m, s) for m in METHODS for s in SEEDS}, "Wrong 48-row matrix")
    source_hashes = {name: record(SOURCE / name) for name in SOURCE_NAMES}
    construct = compile_goal_constructor()
    rows, paired = [], {}
    for method in METHODS:
        root = POTENTIAL if method == "ppo_potential8192" else DENSE if method in ("ppo8192", "zero") else VALIDATION
        for seed in SEEDS:
            job = root / method / str(seed)
            command_path, result_path = job / "command.json", job / "rollout/rollout.json"
            command, result = read(command_path), read(result_path)
            frozen = old[(method, seed)]
            record(command_path)
            require(record(result_path) == frozen["result_sha256"], "Result hash differs from frozen report")
            model_hash = record(result_path.with_suffix(".mjb"))
            require(model_hash == frozen["model_mjb_sha256"], "Frozen model drift")
            for name, expected in source_hashes.items():
                require(result["source_sha256"][name] == expected, f"Goal source differs: {method}/{seed}/{name}")
            args = result["arguments"]
            require(args["scene"] == "push" and not args["settle_only"] and args["duration"] == 24., "Unexpected task")
            require(result["simulation_timestep_s"] == .00005, "Unexpected physical timestep")
            require(result["requested_event_stage"] == "loaded_lift" and result["requested_event_stage_index"] == 3, "Unexpected event stage")
            panel = json.loads(command["environment"]["PANEL_CONFIG"])
            goals = construct(panel)
            final_goal = goals[3]
            require(np.array_equal(final_goal, [.54, 0., .785]), "Final task goal contract differs")
            trace_path = result_path.with_suffix(".npz")
            record(trace_path)
            with np.load(trace_path, allow_pickle=False) as archive:
                trace = {key: archive[key] for key in ("time", "position", "target", "stage", "observation")}
            time, position, target, stage = (trace[k] for k in ("time", "position", "target", "stage"))
            require(time.shape == (600,) and position.shape == target.shape == (600, 3) and trace["observation"].shape == (600, 48), "Invalid trace shape")
            require(all(np.isfinite(a).all() for a in trace.values()), "Nonfinite trace")
            require(np.allclose(time, np.arange(1, 601) * .04, rtol=0, atol=1e-8), "Not the common 25 Hz grid")
            require(int(stage[-1]) == result["final_stage"], "Final stage mismatch")
            require(np.all([any(np.array_equal(t, g) for g in goals) for t in target]), "Unrecognized archived waypoint")
            if np.any(stage == 3):
                require(np.all(target[stage == 3] == final_goal), "Reached final-stage target inconsistent")
            task_signature = {k: args[k] for k in ("scene", "duration", "event_stage", "event_delay", "push_angle", "push_height", "push_force", "push_target_x", "push_target_y", "push_stroke", "push_press", "push_hold", "payload_mass", "nominal_speed")}
            signature = dict(model=model_hash, panel=panel, task=task_signature)
            if seed in paired:
                require(signature == paired[seed][0], "Per-fixture task/environment differs")
                require(np.array_equal(trace["observation"][0], paired[seed][1]), "Initial actor observation differs")
            else:
                paired[seed] = (signature, trace["observation"][0])
            mask = (time > 18. + 1e-8) & (time <= 24. + 1e-8)
            require(mask.sum() == 150, "Final-six-second window not complete")
            error = 1000. * (position[mask] - final_goal)
            rmses = dict(rmse_3d_mm=float(np.sqrt(np.mean(np.sum(error ** 2, axis=1)))),
                         rmse_xy_mm=float(np.sqrt(np.mean(np.sum(error[:, :2] ** 2, axis=1)))),
                         rmse_z_mm=float(np.sqrt(np.mean(error[:, 2] ** 2))))
            contacts = result["panel_audit"]["contacts"]
            contact_path = job / "rollout/contact_samples.npz"
            record(contact_path)
            with np.load(contact_path, allow_pickle=False) as archive:
                names, bins = archive["names"].tolist(), archive["samples"]
            require(bins.shape == (600, 1 + 2 * len(names)) and np.isfinite(bins).all(), "Invalid contact bins")
            require(np.allclose(bins[:, 0], time, atol=1e-8, rtol=0), "Contact bin time mismatch")
            for index, name in enumerate(names):
                require(abs(bins[:, 1 + index * 2].sum() - contacts[name]["duration_s"]) < 1e-7, "Contact duration mismatch")
            rod = contacts["push_rod_geom"]
            bin_stage = stage_at(time - .04 + 1e-8, result["events"])
            rod_durations = bins[:, 1 + 2 * names.index("push_rod_geom")]
            external = {n: c for n, c in contacts.items() if n != "target_object_geom" and c["duration_s"] > 0}
            primary = result["contact"]
            first_rod_stage = None if rod["first_s"] is None else int(stage_at(np.array([rod["first_s"]]), result["events"])[0])
            # Payload-held is recorded for the primary first contact, not every rod contact.
            same_first = rod["first_s"] is not None and primary["first_s"] is not None and abs(rod["first_s"] - primary["first_s"]) < 1e-8
            require(result["success"] == frozen["task_success"], "Task outcome drift")
            upstream_bodies = {f"fr3_link{i}" for i in range(5)}
            upstream = any(set(c["bodies"]) & upstream_bodies for n, c in contacts.items() if n != "target_object_geom")
            require(bool(result["accepted_panel_demo"] and not upstream) == frozen["strict_success"], "Strict gate drift")
            rows.append(dict(method=method, seed=seed, fixture=command["fixture"], final_goal_m=final_goal.tolist(),
                samples=150, final_stage=int(stage[-1]), stage_counts=dict(Counter(str(int(s)) for s in stage)),
                last6s_stage_counts=dict(Counter(str(int(s)) for s in stage[mask])), task_success=frozen["task_success"],
                strict_success=frozen["strict_success"], accepted_panel_demo=result["accepted_panel_demo"],
                original_substep_waypoint_rmse_mm=1000. * frozen["physical"]["position_rmse_3d_m"],
                **rmses, mean_distance_3d_mm=float(np.linalg.norm(error, axis=1).mean()),
                final_distance_3d_mm=float(np.linalg.norm(1000. * (position[-1] - final_goal))),
                final_position_m=position[-1].tolist(), final_current_waypoint_m=target[-1].tolist(),
                final_bilateral_grasp=result["panel_audit"]["final_bilateral_grasp"], lift_m=result["lift_m"],
                position_trajectory_array_sha256=hashlib.sha256(position.tobytes()).hexdigest(),
                fixture_triggered=result["fixture_triggered"], fixture_trigger_time_s=result["fixture_trigger_time_s"],
                rod_contact=rod["duration_s"] > 0, rod_first_contact_s=rod["first_s"], rod_first_stage=first_rod_stage,
                rod_first_payload_held=primary["first_payload_held"] if same_first else None,
                rod_duration_s=float(rod_durations.sum()), rod_duration_by_stage_s={str(s): float(rod_durations[bin_stage == s].sum()) for s in np.unique(bin_stage)},
                rod_peak_force_n=rod["peak_point_force_n"], rod_max_penetration_mm=1000. * rod["max_penetration_m"],
                rod_final_command_m=result["panel_audit"]["final_rod_command_m"],
                rod_final_position_m=result["panel_audit"]["final_rod_position_m"],
                primary_real_contact=result["real_contact"], primary_first_stage=primary["first_stage"],
                any_non_target_external_contact=bool(external), non_target_external_contacts=external,
                model_sha256=model_hash, input_directory=str(job)))
    history_path = Path("docs/CONTACT_MARGIN_HISTORY_DIAGNOSIS_20260924.json")
    history = read(history_path)
    record(history_path)
    previous = {(r["method"], r["seed"]): r["windows"]["last6s_absolute_window"] for r in history["common_windows"]}
    checked = 0
    for row in rows:
        if (row["method"], row["seed"]) in previous:
            reference = previous[(row["method"], row["seed"])]
            require(all(np.isclose(row[k], reference[k], rtol=0, atol=1e-9) for k in ("rmse_3d_mm", "rmse_xy_mm", "rmse_z_mm")), "Original five-method diagnostic regression")
            checked += 1
    require(checked == 30, "Missing previous-window comparison")
    summary = {}
    for method in METHODS:
        part = [r for r in rows if r["method"] == method]
        summary[method] = dict(episodes=6, task=sum(r["task_success"] for r in part), gate=sum(r["strict_success"] for r in part),
            final_stages=dict(Counter(str(r["final_stage"]) for r in part)), triggered=sum(r["fixture_triggered"] for r in part),
            rod_contact=sum(r["rod_contact"] for r in part), any_non_target_external_contact=sum(r["any_non_target_external_contact"] for r in part),
            rod_under_0p3s=sum(r["rod_duration_s"] < .3 for r in part),
            distributions={key: distribution([r[key] for r in part]) for key in ("rmse_3d_mm", "rmse_xy_mm", "rmse_z_mm", "original_substep_waypoint_rmse_mm", "rod_duration_s")})
    record(Path(__file__))
    return dict(scope="Post-hoc offline diagnostic; no simulation, selection, reward update or replacement of frozen metrics",
        samples_per_episode=150, window_s=[18., 24.], window="(18,24] at archived 25 Hz", final_goal_m=[.54, 0., .785],
        same_final_goal_all_48=True, source_hashes=source_hashes, identical_model_and_initial_observation_within_fixture=True,
        goal_evidence="Pure task_layout and BlindTask.__init__ extracted from archived AST, then archived panel z/x override expressions with each original PANEL_CONFIG; source hashes match all 48 rollout records",
        contact_semantics="Robot to obstacle point force norm >0.05 N; per-obstacle duration sums exact 50us contact steps. Different obstacle durations may overlap; do not sum them as union contact duration.",
        previous_five_method_rows_reproduced=checked, excluded="Potential deployment zero9400 parity replay is not an additional result",
        paired_fixtures={str(seed): data[0] for seed, data in paired.items()}, summary=summary, rows=rows, input_sha256=hashes)


def markdown(report):
    lines = ["# 八方法共同最终目标与真实扰动曝光：48条离线诊断", "",
        "只读取已有完整DGX归档，不运行仿真、不重新训练或选参。原冻结waypoint主指标、失败结果和验收门保持不变；本报告为事后辅助诊断，不作为reward或预声明论文指标。", "",
        "共同目标从冻结源码和每条原始PANEL_CONFIG独立恢复：push任务grasp位置为[0.54,0,0.425]，BlindTask构造loaded-lift，panel逻辑把最终Z设为0.785，未设置lift_goal_x覆盖。因此48条均使用既有最终手端目标 **[0.54,0,0.785]m**，包括从未进入stage3的策略。没有使用各策略最后访问的waypoint代替最终目标。三个目标相关源码SHA256与全部48条rollout记录一致；每个fixture的八方法MJB、任务配置和初始48D观测一致。", "",
        "统一取绝对时间(18,24]s的原始25Hz手端位置，每条150样本，全部失败保留。3D/XY/Z分别为sqrt(mean(dx²+dy²+dz²))、sqrt(mean(dx²+dy²))和sqrt(mean(dz²))，单位mm。它们表示距最终点的残差，不是连续参考轨迹跟踪误差。没有生成事后连续reference，也没有把25Hz统计宣称为物理子步统计。", "",
        "## 共同末6秒距离分布", "",
        "每项为六条件均值 ± 总体标准差；3D另列最小—最大。六条件是固定开发fixture，不是独立训练seed；标准差不代表算法统计显著性。", "",
        "| 方法 | 3D mm | 3D范围 mm | XY mm | Z mm | final stage分布 | task | strict gate |",
        "|---|---:|---:|---:|---:|---|---:|---:|"]
    for method, row in report["summary"].items():
        d = row["distributions"]
        fmt = lambda k: f"{d[k]['mean']:.3f} ± {d[k]['std_population']:.3f}"
        bounds = d["rmse_3d_mm"]
        lines.append(f"| {method} | {fmt('rmse_3d_mm')} | {bounds['minimum']:.3f}—{bounds['maximum']:.3f} | {fmt('rmse_xy_mm')} | {fmt('rmse_z_mm')} | {row['final_stages']} | {row['task']}/6 | {row['gate']}/6 |")
    lines += ["", "## 扰动触发和实际接触", "",
        "杆触发由task.index达到loaded_lift(stage3)驱动；未到stage3时不产生这次运动扰动。相同名义fixture因此不保证相同实际扰动曝光。杆本体仍是物理碰撞体，所以必须读取实际contact，不能用trigger=False推断没有碰撞。", "",
        "有力接触定义沿用原审计：机器人到障碍物接触点力向量模长>0.05N。累计时长用每40ms保存的物理子步时长增量复算，与原JSON逐障碍一致；原仿真步长50µs。任意非目标物外接触排除target_object_geom，但包含桌面、护板和推杆。", "",
        "| 方法 | 杆触发率 | 杆有力接触率 | 任意非目标物外接触率 | 杆接触时长范围 s | 杆接触<0.3s |",
        "|---|---:|---:|---:|---:|---:|"]
    for method, row in report["summary"].items():
        d = row["distributions"]["rod_duration_s"]
        lines.append(f"| {method} | {row['triggered']}/6 | {row['rod_contact']}/6 | {row['any_non_target_external_contact']}/6 | {d['minimum']:.6f}—{d['maximum']:.6f} | {row['rod_under_0p3s']}/6 |")
    potential = report["summary"]["ppo_potential8192"]["distributions"]
    lines += ["", f"潜势PPO原全程当前waypoint子步RMSE均值仅{potential['original_substep_waypoint_rmse_mm']['mean']:.3f}mm，但共同最终目标末6秒3D距离RMSE均值为{potential['rmse_3d_mm']['mean']:.3f}mm。六条均停stage1、task/gate均0/6；低waypoint误差不能解释为最好。没有触发杆、没有杆接触，也就没有检验loaded-lift扰动下的恢复能力。它仍与office_desk_top有右指接触；real_contact=False是原主审计口径，不代表所有物理外接触为零。", "",
        "dense PPO六条均停stage0并碰护板，末段手端距最终点74.531mm也不能解释为完成持物抬升：它没有经过抓取阶段，也没有承受杆扰动。zero六条均进入stage3并持续接触杆19.02–20.50s，但task/gate仍均0/6。下面完整逐条统计区分这些情况。杆接触时长不足0.3s沿用原任务接触门的解释尺度，不额外改写strict gate。阻抗低末段距离也必须连同4/6接触不足看待。", "",
        "潜势PPO六条保存的手端位置轨迹完全一致，最终目标距离标准差为零；这不表示对六种已实现扰动都稳健，而是没有进入扰动触发阶段。JSON保留位置数组hash，可检查重复轨迹而不重复计入额外zero复验。", "",
        "## 全48条距离和原始任务结果", "",
        "| 方法 | seed | 末6s 3D mm | XY mm | Z mm | trace末帧距离 mm | final stage | task | strict gate | 原waypoint子步RMSE mm |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|---:|"]
    for r in report["rows"]:
        lines.append(f"| {r['method']} | {r['seed']} | {r['rmse_3d_mm']:.6f} | {r['rmse_xy_mm']:.6f} | {r['rmse_z_mm']:.6f} | {r['final_distance_3d_mm']:.6f} | {r['final_stage']} | {r['task_success']} | {r['strict_success']} | {r['original_substep_waypoint_rmse_mm']:.6f} |")
    lines += ["", "## 全48条真实曝光", "",
        "杆首次阶段由原events时间恢复；首次持物只在杆首次接触与原主审计首次接触同一时刻时引用，否则留空，不推断。JSON额外保存各障碍的首次/末次、时长、力峰、参与body和按阶段杆接触时长；不同障碍时长可能重叠，不能相加当作总接触时长。", "",
        "| 方法 | seed | 杆触发 s | 杆首触 s | 首触stage/持物 | 杆时长 s | 杆力峰 N | 实际非目标外接触障碍及累计时长 s |",
        "|---|---:|---:|---:|---|---:|---:|---|"]
    for r in report["rows"]:
        fmt = lambda v: "—" if v is None else f"{v:.6f}"
        contacts = "; ".join(f"{n}: {c['duration_s']:.6f}" for n, c in r["non_target_external_contacts"].items()) or "无"
        lines.append(f"| {r['method']} | {r['seed']} | {fmt(r['fixture_trigger_time_s'])} | {fmt(r['rod_first_contact_s'])} | {r['rod_first_stage']}/{r['rod_first_payload_held']} | {r['rod_duration_s']:.6f} | {r['rod_peak_force_n']:.3f} | {contacts} |")
    lines += ["", "## 复核范围与限制", "",
        "原五方法30条末6秒3D/XY/Z结果逐条重现既有CONTACT_MARGIN_HISTORY_DIAGNOSIS报告，误差小于1e-9mm。48条完整24s、统一600帧时间网格、有限值、源代码/结果/模型hash、按fixture目标/环境/初始观测一致性、逐障碍接触累计时长均通过检查。潜势部署额外zero9400只用于此前配对复现，不作为第49条或第九种方法。", "",
        "位置严格沿用rollout.npz的position字段和原记录时间。原脚本在env.step后读取live d.xpos；它与另外重新求值的几何末端位置或JSON endpoint_error未必完全相同，因此末帧列只标作trace末帧距离，不据此重判任务。主waypoint子步指标引用已验证冻结报告，并保留该报告hash；本工具不把25Hz结果冒充重新恢复的子步位置。", "",
        "不同阶段和接触曝光意味着这不是等量扰动恢复能力排名。六条件结果也不能解决训练预算不一致：PPO是单训练seed/8192步pilot，学生来自教师模仿。经典基线为有限各向同性K/ζ搜索；导纳参考经过nominal-speed/WBC整形，不能从低峰值推导控制器本征优越性。报告没有改变任何训练或部署。", "",
        f"同名JSON保存48条完整精度数据、六条件全部取值分布和{len(report['input_sha256'])}个输入/工具SHA256。目标相关源码：", ""]
    lines += [f"- `{name}`：`{value}`" for name, value in report["source_hashes"].items()]
    lines += ["", "复核命令（benchmark目录，单CPU进程，无MuJoCo导入）：", "", "```bash",
        "OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python tools/report_eight_method_final_goal_20260924.py",
        "```", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/EIGHT_METHOD_FINAL_GOAL_EXPOSURE_20260924"))
    args = parser.parse_args()
    report = audit()
    args.output.with_suffix(".json").write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    args.output.with_suffix(".md").write_text(markdown(report))
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
