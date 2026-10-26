"""Present the completed, independently audited new30 comparison; never fit or simulate."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


FAMILIES = ("esn", "rnn", "mlp")
METRICS = (
    ("task_success", "Task success", "%", 100),
    ("strict_success", "Task AND Strict success", "%", 100),
    ("spt_mean", "SPT (shared empirical reference)", "score", 1),
    ("peak_torque_mean_nm", "Mean episode peak torque", "Nm", 1),
    ("human_comfort_torque_compliance_contact_time_weighted",
     "Contact-time comfort compliance", "%", 100),
    ("machine_safety_violation_rate", "Machine safety violations", "%", 100),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def load_final(root, audit_path):
    """Reject partial results and audit receipts for a different report or run."""
    state = read(root / "execution.json")
    require(state["status"] == "complete", "Evaluation is not complete; no final presentation")
    report_path = root / "REPORT.json"
    report, audit = read(report_path), read(audit_path)
    require(report["status"] == "complete", "Incomplete report")
    require(audit["status"] == "final_audit_passed", "Full final audit required")
    require(Path(audit["root"]).resolve() == root.resolve(), "Audit refers to another run")
    require(state["report_sha256"] == audit["report_sha256"] == sha(report_path),
            "Report changed since execution or final audit")
    require(audit["model_lock_sha256"] == report["model_lock_sha256"] == sha(root / "MODEL_LOCK.json"),
            "Model lock changed")
    require(report["registration_sha256"] == sha(root / "REGISTRATION.json"), "Registration changed")
    require(audit["verified_physical_episodes"] == len(report["rows"]) == 108,
            "Full 108-episode matrix required")
    reg = read(root / "REGISTRATION.json")
    seeds = sorted(reg["seeds"])
    require(len(seeds) == len(set(seeds)) == 3 and set(reg["families"]) == set(FAMILIES),
            "Unexpected comparison families or seeds")
    models = {f"{family}_s{seed}" for family in FAMILIES for seed in seeds}
    conditions = {row["condition"] for row in report["rows"]}
    require(len(conditions) == 12 and {(r["method"], r["condition"]) for r in report["rows"]}
            == {(m, c) for m in models for c in conditions}, "Missing or duplicate evaluation cells")
    require(len(report["methods"]) == 9 and {m["method"] for m in report["methods"]} == models,
            "Missing method summary")
    require(all(not r["strict_success"] or r["task_success"] for r in report["rows"]),
            "Strict success without task success")
    require(set(report["family_summary"]) == set(FAMILIES), "Missing family summary")
    for family in FAMILIES:
        for key, _, _, _ in METRICS:
            stat = report["family_summary"][family][key]
            require(len(stat["per_seed"]) == 3, "Missing seed statistic")
            require(all(v is None or math.isfinite(v) for v in
                        [*stat["per_seed"], stat["mean"], stat["sample_sd"]]), "Nonfinite statistic")
    return report, audit, seeds


def formatted(stat, scale):
    if stat["mean"] is None:
        return "NA"
    return f"{stat['mean'] * scale:.3f} ± {stat['sample_sd'] * scale:.3f}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report, audit, seeds = load_final(args.root, args.audit)
    require(not args.output.exists(), "Never overwrite an existing presentation")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    args.output.mkdir(parents=True, exist_ok=False)
    fig, axes = plt.subplots(2, 3, figsize=(12, 7.2), layout="constrained")
    colors, markers = ("#246b9d", "#c46b17", "#4b8342"), ("o", "s", "^")
    for ax, (key, title, unit, scale) in zip(axes.flat, METRICS):
        upper = 1.0 if unit == "score" else 100.0 if unit == "%" else 0.0
        for i, family in enumerate(FAMILIES):
            stat = report["family_summary"][family][key]
            for j, value in enumerate(stat["per_seed"]):
                if value is not None:
                    ax.scatter(i + (j - 1) * .14, value * scale, color=colors[j], marker=markers[j],
                               s=42, zorder=3, label=f"seed {seeds[j]}" if i == 0 else None)
                    upper = max(upper, value * scale)
            if stat["mean"] is not None:
                mean, sd = stat["mean"] * scale, stat["sample_sd"] * scale
                ax.errorbar(i, mean, yerr=sd, fmt="D", color="#303030", ms=4, capsize=5,
                            lw=1.2, zorder=4, label="mean ± sample SD" if i == 0 else None)
                upper = max(upper, mean + sd)
                ax.annotate(f"{mean:.3f}" if unit == "score" else f"{mean:.1f}",
                            (i, mean + sd), xytext=(0, 9), textcoords="offset points",
                            ha="center", fontsize=9)
            else:
                ax.text(i, .94, "mean NA", transform=ax.get_xaxis_transform(), ha="center", fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.set_xticks(range(3), [f.upper() for f in FAMILIES])
        ax.set_ylabel(unit)
        # Symmetric SD is descriptive; do not clip it to the physical [0,1] domain.
        lower = min([0.] + [(s["mean"] - s["sample_sd"]) * scale
                            for s in [report["family_summary"][f][key] for f in FAMILIES]
                            if s["mean"] is not None])
        ax.set_ylim(lower - .03 * max(upper, 1), max(upper, 1) * 1.16)
        ax.set_xlim(-.5, 2.5)
        ax.grid(axis="y", alpha=.2)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=4, fontsize=9)
    ref = "NA" if report["t_ref_s"] is None else f"{report['t_ref_s']:.2f} s"
    fig.suptitle(f"New30 imitation learning | 3 seeds × 12 conditions per method | T_ref = {ref}", fontsize=12)
    fig.savefig(args.output / "final_metrics.png", dpi=170)
    fig.savefig(args.output / "final_metrics.pdf")
    plt.close(fig)

    headings = [f"{title} ({unit})" for _, title, unit, _ in METRICS]
    lines = ["# 新增30条示范：ESN、RNN、MLP最终对比", "",
             "全部108个闭环回合和最终独立审计完成。下表先按每个训练seed的12个条件汇总，再报告3个seed的均值 ± 样本标准差；不是置信区间。", "",
             "| 方法 | " + " | ".join(headings) + " |", "|---|" + "---:|" * len(METRICS)]
    for family in FAMILIES:
        lines.append("| " + family.upper() + " | " + " | ".join(
            formatted(report["family_summary"][family][key], scale) for key, _, _, scale in METRICS) + " |")
    lines += ["", f"共同后验参考时间 T_ref = {ref}。SPT仅对Task AND Strict双通过回合计分，其他为0；参考值不证明最优，也不宜跨不同矩阵直接比较。", "",
              "峰值力矩栏是回合峰值的均值，不是最坏峰值。舒适合规按实际人体接触时间加权、七关节同时满足阈值；无接触为NA。阈值[43.5,43.5,43.5,43.5,6,6,6] Nm是经验工程代理，不是人体舒适标定。", "",
              "## 逐模型结果", "", "| 模型 | Task | Task AND Strict | 最坏峰矩(Nm) | 总人体接触(s) | 机器违规回合 |", "|---|---:|---:|---:|---:|---:|"]
    for m in sorted(report["methods"], key=lambda m: m["method"]):
        lines.append(f"| {m['method']} | {m['task_success']}/12 | {m['strict_success']}/12 | {m['peak_torque_worst_nm']:.4f} | {m['human_contact_duration_s_total']:.4f} | {m['machine_safety_violation_episodes']}/12 |")
    lines += ["", "## 范围与失败", "",
              "只用新增30条、24train/6val、每方法每seed12候选、统一终态验证动作MSE选模。6条示范验证集用于选模，不能冒充未见测试；12个新扰动身份是锁模后的独立闭环评测，沿用既有范围和几何。", "",
              "ESN使用固定储备池＋解析ridge；RNN/MLP从头梯度学习。这是完整方法比较，特征处理/参数量/FLOPs不同，不是纯记忆机制消融。有限32000更新不自动证明收敛。低力矩或高舒适合规伴随任务失败不能称为整体更优。", ""]
    for family in FAMILIES:
        rows = [r for r in report["rows"] if r["method"].startswith(family + "_s")]
        reasons = Counter(reason for r in rows for reason in r["comfort"]["machine_safety_violation_reasons"])
        lines.append(f"- {family.upper()}：Task失败{sum(not r['task_success'] for r in rows)}/36；机器安全原因计数{dict(sorted(reasons.items()))}。原因可重叠，全部失败保留。")
    lines += ["", "独立审计核对训练/选模/验证动作重放、来源hash与已有actor/filter重放收据，并从保存的原始物理子步复算指标；没有独立重新仿真全部动力学。完整逐回合数据及接触峰力/冲量/超阈值时长/超额积分保留在原REPORT.json和最终审计中。", ""]
    (args.output / "FINAL_COMPARISON.md").write_text("\n".join(lines), encoding="utf-8")
    evidence = dict(created_utc=datetime.now(timezone.utc).isoformat(), root=str(args.root.resolve()),
                    report_sha256=sha(args.root / "REPORT.json"), audit_path=str(args.audit.resolve()),
                    audit_sha256=sha(args.audit), script_sha256=sha(Path(__file__)),
                    model_lock_sha256=report["model_lock_sha256"], t_ref_s=report["t_ref_s"],
                    family_summary=report["family_summary"], seed_order=seeds,
                    verified_physical_episodes=audit["verified_physical_episodes"],
                    artifacts={p.name: sha(p) for p in sorted(args.output.iterdir())})
    (args.output / "PRESENTATION_EVIDENCE.json").write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "artifacts": evidence["artifacts"]}))


if __name__ == "__main__":
    main()
