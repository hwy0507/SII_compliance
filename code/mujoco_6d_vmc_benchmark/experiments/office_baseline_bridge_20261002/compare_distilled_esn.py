"""Recompute archived ESN/RL office metrics without running or altering physics."""
import csv, hashlib, html, json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = Path("/home/arm1/SII_compliance_baseline")
ESN = Path("/home/arm1/sii_shared/SII_compliance/runs/main/vmc_esn_four_hour_20261002_090155/evidence")
RL = Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge")
OUT = Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/esn_rl_comparison_20261002")
MAIN = "14820fac7141fa8779aa56b5ae0ba595ee2ee0a5"
MODEL = "b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1"
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p, value): p.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n")
OUT.mkdir(parents=True, exist_ok=True)
esn_audit = read(ESN/"FINAL_AUDIT.json")
rl_summary = read(RL/"transfer_report01/SUMMARY.json")
reference = read(RL/"transfer01/parameter_impedance/rollout.json")
rl_execution = read(RL/"transfer01/parameter_impedance/EXECUTION.json")
ignore_args = {"output","esn_model","esn_mode","memory_ablation"}
common_sources = ["scripts/fixed_panda_wbc.py","scripts/paper_mpc_wbc.py","scripts/pink_wbc_adapter.py","scripts/planned_hand_corner_20261002.py","scripts/scene_gates.py","scripts/physics_substep_metrics_20260923.py","scripts/fr3_scene.py","scripts/office_complex_scene_v5_20260917.py"]
rows, verification = [], []
def process(run, identity, family, expected, execution, source_hashes):
    summary = read(run/"rollout.json")
    args = summary["arguments"]
    differing = {k:[args.get(k),reference["arguments"].get(k)] for k in set(args)|set(reference["arguments"]) if k not in ignore_args and args.get(k)!=reference["arguments"].get(k)}
    assert not differing, (identity,differing)
    assert summary["fixture"] == reference["fixture"]
    for k in common_sources:
        assert source_hashes[k] == rl_execution["upstream_source_sha256"][k], (identity,k)
    model = sha(run/"rollout.mjb")
    assert model == MODEL
    metric_file = run/"rollout_metrics/substep_metrics.npz"
    with np.load(metric_file) as z:
        dt = z["dt"].astype(float)
        error = z["error"].astype(float)
        torque = z["qfrc_actuator"].astype(float)
        twist = z["twist"].astype(float)
        assert all(np.isfinite(v).all() for v in [dt,error,torque,twist])
        assert len(dt)==550000 and np.allclose(dt,1e-4,atol=1e-12,rtol=0)
        metrics = dict(rmse_mm=float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum())*1000),peak_torque_nm=float(np.abs(torque).max()),peak_speed_mps=float(np.linalg.norm(twist[:,:3],axis=1).max()))
    errors={k:abs(v-expected[k]) for k,v in metrics.items()}
    assert errors["rmse_mm"]<1e-3 and errors["peak_torque_nm"]<1e-5 and errors["peak_speed_mps"]<1e-7, (identity,errors)
    checkpoint = run/"checkpoint.npz"
    checkpoint_hash = sha(checkpoint) if checkpoint.exists() else None
    if checkpoint_hash: assert checkpoint_hash == expected["checkpoint_sha256"]
    row=dict(id=identity,family=family,**metrics,task=expected.get("task",expected.get("task_success")),strict=expected.get("strict",expected.get("strict_success")),stage=expected["stage"],penetration_mm=expected.get("penetration_mm",expected.get("external_penetration_mm")),duration_s=float(dt.sum()),checkpoint_sha256=checkpoint_hash,source=str(run))
    assert row["task"] is False and row["strict"] is False
    rows.append(row)
    verification.append(dict(id=identity,model_sha256=model,raw_metrics_sha256=sha(metric_file),execution_sha256=sha(execution),rollout_summary_sha256=sha(run/"rollout.json"),checkpoint_sha256=checkpoint_hash,native_substeps=len(dt),common_arguments_equal=True,fixture_equal=True,common_source_hashes_verified=common_sources,absolute_metric_errors=errors))
for r in esn_audit["rows"]:
    if not r.get("checkpoint_sha256"): continue
    relative=r["run"].split("/tool_teacher_four_hour_20261002/",1)[1]
    run=ESN/relative
    exe=read(run/"execution.json")
    assert exe["mujoco"]=="3.11.0"
    assert exe["reference_sha256"] == rl_execution["reference_summary_sha256"]
    process(run,relative,"ESN",r,run/"execution.json",exe["source_sha256"])
for r in rl_summary["rows"]:
    if r["id"]=="source_esn_reference": continue
    run=Path(r["source"])
    exe=read(run/"EXECUTION.json")
    process(run,r["id"],"RL" if r["id"].startswith(("direct_","parameter_")) else "classical",r,run/"EXECUTION.json",exe["upstream_source_sha256"])
assert len(rows)==35 and len([r for r in rows if r["family"]=="ESN"])==24
byid={r["id"]:r for r in rows}
anchor=byid["esn_first_three/esn_original_v2"]
changes=[]
for r in rows:
    if r["family"]=="RL":
        changes.append(dict(id=r["id"],esn_original_v2_relative_change_percent={k:100*(anchor[k]/r[k]-1) for k in ["rmse_mm","peak_torque_nm","peak_speed_mps"]}))
limitations=[
"Single fixed office development condition, 55 s, dt=1e-4; not formal dt=5e-5 or an independent generalization test.",
"ESN was optimized on this office condition; RL weights were trained on four primitive scenes and transferred unchanged. Training exposure, optimization budgets and test familiarity are unequal.",
"ESN simulation host airpig (Python 3.11.15); RL host Spark (Python 3.12). MuJoCo 3.11.0 and archived MJB agree. This is a matched-configuration archival comparison, not a bitwise same-host rerun.",
"All 35 episodes fail task and strict. Low RMSE or low peak speed can coexist with stalled progress.",
"24 ESN evaluations are different candidates, calibrations and interventions, not 24 independent seeds; retain all instead of choosing a winner by a single metric.",
"original_v2 is the base VMC-distilled ESN in the latest batch, not the last trained checkpoint. dagger_drift is the later trained variant; final_gain and reset are subsequent interventions.",
"ESN architecture is a 128-unit reservoir plus 128-unit nonlinear readout and skip connection; it is not a classical linear-readout-only ESN.",
"RMSE uses the common evaluator's evolving nominal task reference. Policies can change task progress, so this is not error against an externally fixed time trajectory.",
"All peaks use all 550000 native substeps. Torque is actual qfrc_actuator maximum absolute value; speed is hand linear norm, not joint speed or action magnitude."
]
result=dict(created_utc=datetime.now(timezone.utc).isoformat(),main=MAIN,model_sha256=MODEL,rows=rows,esn_original_v2_vs_rl=changes,limitations=limitations,input_hashes={str(ESN/"FINAL_AUDIT.json"):sha(ESN/"FINAL_AUDIT.json"),str(RL/"transfer_report01/SUMMARY.json"):sha(RL/"transfer_report01/SUMMARY.json")})
save(OUT/"COMPARISON.json",result)
save(OUT/"VERIFICATION.json",dict(status="passed",new_simulations=0,total_episodes=35,total_native_substeps=35*550000,rows=verification))
with (OUT/"COMPARISON.csv").open("w") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
selected=[
("esn_first_three/esn_original_v2","ESN: base VMC distillation"),
("esn_context_pair/esn_reference_context","ESN: reference context"),
("esn_progress_pair/esn_integral41","ESN: integral41"),
("esn_dagger_pair/esn_dagger_drift","ESN: later DAgger drift"),
("parameter_admittance","RL: admittance parameters"),
("parameter_impedance","RL: impedance parameters"),
("parameter_vmc","RL: VMC parameters"),
("direct_metric_74001","Direct RL: metric / 74001"),
("direct_metric_74002","Direct RL: metric / 74002"),
("direct_office_task_74001","Direct RL: task / 74001"),
("direct_office_task_74002","Direct RL: task / 74002"),
("fixed_impedance","Fixed BO impedance"),
("zero","Zero compliance")]
fig,axes=plt.subplots(1,3,figsize=(14,7.4),sharey=True,layout="constrained")
for ax,key,title in zip(axes,["rmse_mm","peak_torque_nm","peak_speed_mps"],["Position RMSE (mm)","Peak actuator torque (Nm)","Peak hand speed (m/s)"]):
    for i,(ident,label) in enumerate(selected):
        r=byid[ident]; color={"ESN":"#326ca8","RL":"#c87a2e","classical":"#777777"}[r["family"]]
        ax.barh(i,r[key],color=color,height=.63)
        ax.text(r[key],i,f" {r[key]:.3f}",va="center",fontsize=8)
    ax.set_title(title);ax.set_xlim(0,max(byid[i][key] for i,_ in selected)*1.22);ax.grid(axis="x",alpha=.15);ax.set_axisbelow(True)
axes[0].set_yticks(range(len(selected)),[l for _,l in selected],fontsize=9);axes[0].invert_yaxis()
fig.suptitle("Archived matched office comparison | all task/strict failed\n55 s, dt=0.0001 s; ESN trained on office, RL transferred from primitive scenes",fontsize=12)
fig.savefig(OUT/"comparison.png",dpi=160);fig.savefig(OUT/"comparison.pdf");fig.savefig(OUT/"preview.jpg",dpi=105);plt.close(fig)
def table(rs):
    lines=["| Method | RMSE mm | Peak torque Nm | Peak hand speed m/s | Penetration mm | Final stage |","|---|---:|---:|---:|---:|---|"]
    for r in rs: lines.append(f"| {r['id']} | {r['rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.6f} | {r['penetration_mm']:.6f} | {r['stage']} |")
    return "\n".join(lines)
report=f"""# 最新蒸馏 ESN 与 RL：固定 office 三指标比较（2026-10-02）

GitHub main 核验提交：`{MAIN}`。没有一个被正式锁定为最终成功模型的新版 ESN；最新发布批次含13个有效学习模型及24条学生闭环候选/干预。全部失败。
本报告复用已保存的匹配配置回合，新增仿真0；独立重算35条完整回合、19,250,000个原生物理子步。

## 结论与版本身份

- 基础VMC蒸馏 `original_v2`：30.058 mm / 39.210 Nm / 0.370185 m/s，权重SHA256 `{anchor['checkpoint_sha256']}`。
- 它比四个直接动作RL的RMSE都低；峰矩/峰速并非全胜。对RL调导纳RMSE几乎相同；对RL调阻抗RMSE与峰矩较高、峰速略低；对RL调VMC三项均较低。
- context候选29.438 / 37.294 / .382850；推进较远的integral41为76.718 / 38.129 / .398990。
- 最后一组学习候选DAgger-drift为125.970 / 37.615 / .388723，不能把较早original_v2包装成最后训练模型，也不能认为后期优化必然更好。
- Zero及固定阻抗作为参照保留。全部task/strict=false；低指标不等于完成放置。

## 相同配置及核验

同一office-tool-contact-v5、seed2026091751、55s、dt1e-4、MuJoCo3.11.0、25Hz公共策略/4ms伺服。
MJB SHA256 `{MODEL}`。逐回合核对归档二进制模型、fixture、公共arguments和8个公共源码hash
（WBC、规划、场景、gate、指标），策略模式/权重/输出路径/记忆干预区别显式排除。
新ESN与RL运行使用同一参考summary hash；ESN权重逐文件复核，所有原始指标文件另存hash。
RMSE按三维位置误差平方的时间积分开方；峰值使用全部550000子步的真实qfrc_actuator绝对值和手部线速度范数。
从float32归档复算与原统计容差内一致，未用视频抽帧估计。
原ESN在airpig/Python3.11.15运行，RL在Spark/Python3.12运行；没有声称同机逐位复现。
两个host的zero统计30微米量级差异，不用于宣称微小优势。

## 主表：基础蒸馏与全部RL及经典对照

所有行task/strict=false，完整55s。
{table([anchor]+[r for r in rows if r['family']!='ESN'])}

## 最新发布的全部24条ESN评估

这是候选/干预表，不能当24个独立seed计算成功率。完整保留穿透超限与后期退化。
{table([r for r in rows if r['family']=='ESN'])}

## 比较边界

"""+"\n".join("- "+x for x in limitations)+f"""

## 复算与产物

实际分析在Spark，未改变任何checkpoint、场景或已有结果。
服务器：`arm1@192.168.31.70:{OUT}/`
包含COMPARISON.json/CSV、VERIFICATION.json、comparison.png/PDF及浏览页。
ESN原始数据：`{ESN}`；RL原始数据：`{RL}/transfer01`。
运行：`OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python code/mujoco_6d_vmc_benchmark/experiments/office_baseline_bridge_20261002/compare_distilled_esn.py`。
"""
(OUT/"REPORT.md").write_text(report)
(REPO/"code/mujoco_6d_vmc_benchmark/docs/DISTILLED_ESN_RL_COMPARISON_20261002.md").write_text(report)
(OUT/"index.html").write_text('<!doctype html><meta charset="utf-8"><title>Distilled ESN vs RL</title><style>body{font-family:system-ui;margin:32px;max-width:1500px}img{width:100%}pre{white-space:pre-wrap;line-height:1.5}</style><h1>最新蒸馏 ESN 与 RL 三指标对照</h1><p>固定55秒开发场景；全部task/strict失败；训练场景与预算不等同。</p><img src="comparison.png"><p><a href="COMPARISON.csv">CSV</a> · <a href="comparison.pdf">PDF</a> · <a href="VERIFICATION.json">原始数据复核</a></p><pre>'+html.escape(report)+'</pre>')
print(json.dumps(dict(output=str(OUT),verified_episodes=len(rows),changes=changes),ensure_ascii=False))


web = Path("/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/web_demo/primitive_baselines_20261002/esn_rl_comparison_20261002")
if not web.exists():
    web.symlink_to(OUT, target_is_directory=True)
else:
    assert web.resolve() == OUT.resolve()
