# Fixture 2/3 teacher coverage + 随机化训练实验（2026-08-17，v2 多 seed 统计版）

## 目的

执行 HANDOFF.md 优先级 1/2/3：

1. 补强 fixture 2/3 强碰撞区域的 teacher coverage；
2. 建立真正的随机化训练分布；
3. 按正式 selection gate 判定候选模型并做多 seed 统计。

v2 修订：v1 报告中「seed 251 DAgger iter2 通过 gate」来自对 9 个 (seed, iteration) 组合做
held-out fx3 扫描后挑最优，属于测试集选择偏差，**不能作为正式结果**。本版改用统一协议：
iteration 只用 train fixtures 选择，fx3 只报告。结论因此修正。

## 方法

### 代码改动

- `scripts/run_direct_esn_mujoco.py`：`--rod-stroke-m / --rod-height-m / --rod-start-time-s /
  --grasp-time-s` fixture override；summary 记录 `override_fixture`。
- `scripts/run_direct_esn_dagger.py`：`--dagger-fixtures`（`stroke,height,start;...`）自定义随机化
  rod pool；summary 记录 `dagger_fixture_pool`，archive 记录 `rollout_fixture`。

### Reference 稳定边界

deterministic reference（formal multifixture seed_20260907 iteration_03）：stroke ≤ 0.176 全部
task success（timing 1.062–1.108、height 0.5395–0.5435），stroke ≥ 0.178 task fail。
fixture 3（0.175）在稳定边界内侧。

### Expert trace 网格（19 rod + 1 no-rod，全部 task success）

fixture 2 邻域：stroke {0.170,0.172,0.174,0.176} × start {1.062,1.085,1.108}（height 0.541，12 条）
+ height 变化 4 条 + default f0/f1/f2 3 条；impulse 覆盖 0.90–3.11 N·s。
无任何组合等于 held-out fixture 3 (0.175, 0.542, 1.100)。

### 训练管线（8 个 reservoir seeds：13, 42, 71, 137, 251, 307, 512, 1009）

1. Bootstrap：stable-reference coverage BC（`washout 3 / rod-repeat 4 / neutral-repeat 4`）。
2. DAgger：8-fixture 随机化 pool（default f0/f1/f2 + 0.176/0.541/1.085、0.176/0.5395/1.062、
   0.176/0.5425/1.108、0.174/0.541/1.096、0.172/0.5435/1.070），counterfactual h24 /
   nonzero-repeat 8 / dilation 0 / prior 100，3 iterations。
3. 统一选择协议：iteration 仅用 train fixtures 0/1/2 的平均 ΔRMSE 选择；fx3 与 no-rod 只评估报告。

## 结果

### Bootstrap-stage must gate

8/8 seeds 通过（no-rod task success、无 hard torque、mean yield < 0.005 m/s、全部 fixture
task success + stable rejoin）。

### 统一协议 8-seed 统计（Fixed WBC → ESN）

Post-contact ΔRMSE（mm，mean±std；负为改善）：

| 模型 | fx0 (train) | fx1 (train) | fx2 (train) | fx3 (held-out) |
|---|---:|---:|---:|---:|
| **Bootstrap BC-only（n=8）** | −0.982±0.011 | −2.600±0.011 | −3.313±0.015 | **−2.207±0.034** |
| DAgger iter1（train-selected，n=8） | −0.678±0.074 | −1.850±0.071 | −1.892±0.078 | **+1.146±0.390** |
| deterministic reference（单模型） | −1.041 | −2.650 | −3.506 | −2.397 |

Rejoin latency（s）与 recovery jerk（m/s³）：

| 模型 | fx0 | fx1 | fx2 | fx3 |
|---|---:|---:|---:|---:|
| BC-only rejoin | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| BC-only recjerk | 10±1 | 64±5 | 133±4 | 127±3 |
| reference rejoin | 0.80 | 0.60 | 0.48 | 0.64 |
| reference recjerk | 11 | 86 | 136 | 119 |

No-rod：BC-only mean yielding twist 0.001057±0.000064 m/s（8/8；v2 报告中的 0.00100±0.00000
为聚合脚本显示精度 bug，已修正）；DAgger iter1 同为
0.00100 量级（0.00053–0.00068）。

### Selection gate 判定

- **Bootstrap BC-only：8/8 seeds 通过完整 gate（must 项 + held-out RMSE 优先项）**，
  seed 间方差 ±0.034 mm，是正式的随机化 proposed 方法。
- DAgger（随机 pool counterfactual）：8/8 seeds 在 held-out fx3 恶化（+0.55 ~ +1.59 mm，
  mean +1.146±0.390），train-only 协议下全部违反「RMSE 不高于 Fixed WBC」优先项 →
  **记录为负结果（见失败方向 F）**。
- v1 的 seed251-it2（fx3 −3.214）为 held-out 扫描选择偏差产物，仅作探索性参考，不进入正式结果。

## 结论

1. **随机 reservoir robustness 的解 = stable-reference coverage BC**：19+1 条覆盖
   stroke/timing/height 的 expert traces 让 8 个独立 reservoir 全部以极小方差复现
   reference 水平（held-out −2.207±0.034 mm vs reference −2.397 mm）。
2. **随机 pool counterfactual DAgger 在此设置下是净负贡献**：iteration 1 即把 held-out
   ΔRMSE 从 −2.2 拉到 +1.1，且随 iteration 单调劣化（train fixtures 上亦然）。
   机理推测：pool 中 5/8 为强碰撞 fixture，counterfactual nonzero 标签（repeat=8 加权）
   把 readout 拉向过强 yield，破坏 BC 学到的与 teacher 参数化一致的低误差行为；
   proximal prior 100 不足以约束。若要复活 DAgger，需要标签权重按碰撞强度归一、或
   pool 强度分布匹配 default fixtures，或仅对 student 明显偏离 teacher 的状态打标。
3. 论文建议叙事：proposed = Direct ESN coverage BC（8-seed 统计），deterministic
   reference 作为单 reservoir 上界对照，DAgger 负结果写入 ablation。

## OOD 泛化扫描（v3 增补）

### 强度 OOD（stroke 0.178–0.190，reference 失败区；fixture 2 timing/height）

结果：**该区域为任务物理不可行区——Fixed WBC 也全部 task fail**（被撞后无人能完成 grasp）。
因此「BC 在 reference 失败区仍成功」的强泛化主张不成立；正确表述是退化行为分层：

- 8 个 BC seeds 的 post-contact RMSE 相对 Fixed WBC（24.3 → 31.6 mm）分三档：
  - bc_71 全程优于 Fixed WBC（0.190 时 27.2 vs 31.6 mm）；bc_251 / bc_512 在 stroke ≥ 0.182–0.186 后仍持平或略优；
  - bc_42 / bc_137 / bc_1009 温和退化（0.190 时 38–45 mm）；
  - bc_13 / bc_307 与 deterministic reference 一样剧烈退化（reference 0.190 时 55.1 mm，
    bc_13/307 peak deviation 130–164 mm）。
- 数据源：`ood_stroke_scan/ood_scan_summary.json`（9 models × 7 strokes）。

### 几何 OOD（可行域内未见 timing/height；stroke 0.172）

4 个 OOD 点：start 1.130 / 1.150（训练上限 1.108）、height 0.545（训练上限 0.5425）、
角点 (0.176, 0.5425, 1.130)。结果（8 BC seeds，Fixed WBC 对照全程 task success）：

| OOD 点 | ΔRMSE（8-seed 范围） | rejoin ESN vs FW |
|---|---|---|
| start 1.130 | −2.913 ~ −2.993 mm | 0.56 vs 0.96 s |
| start 1.150 | −1.905 ~ −2.262 mm | 0.60 vs 0.96 s |
| height 0.545 | −2.351 ~ −2.492 mm | 0.60 vs 0.96 s |
| 角点 (0.176, 0.5425, 1.130) | −1.695 ~ −2.012 mm | 0.68 vs 1.00 s |

**8/8 seeds 在全部 4 个 OOD 点 task success、无 hard torque、RMSE 大幅优于 Fixed WBC，
表现与 in-distribution 几乎无衰减，seed 方差极小**；deterministic reference 同点 −2.14 ~ −3.14 mm，
水平相当。数据源：`ood_geometry_scan/ood_geometry_summary.json`（evaluate 脚本新增
`--rod-stroke-m/--rod-height-m/--rod-start-time-s/--grasp-time-s` override 后跑出）。

### 泛化结论

1. **几何维度（impact timing / height）泛化强**：超出训练网格的未见组合上 8/8 seeds 保持
   全部 gate 指标，可直接作为论文泛化主张。
2. **强度维度泛化边界 = 训练覆盖的物理可行域（stroke ≤ 0.176）**：超出后任务本身不可行，
   各控制器只剩退化行为比较；方法不提供 task-level 强度外推。
3. 论文建议：报告 generalization boundary 分析（可行域内几何 OOD 阳性 + 强度不可行区
   分层退化），而不是笼统的「OOD 鲁棒」。

## 论文主实验表（v4 增补）

`paper_tables/`（服务器与本地 docs 同步）：

- `paper_main_tables.md`：Table 1 matched benchmark 全指标（RMSE/IAE/peak deviation/
  actual- 与 scheduled-release rejoin/impulse/peak force/peak torque/recovery jerk，
  Fixed WBC vs BC 8-seed vs reference）；Table 2 no-rod neutrality；Table 3 geometry OOD；
  Table 4 strength OOD 边界。
- `paper_main_statistics.csv`：BC 8-seed 各指标 mean/std（机器可读）。
- `paper_main_figure.png`：三面板图（RMSE、rejoin latency、geometry OOD ΔRMSE with
  per-seed scatter）。

主表要点：BC 8-seed 在全部 fixture 上 RMSE/IAE/peak deviation/rejoin 全面优于 Fixed WBC
（held-out fx3：RMSE 17.901 → 15.694±0.034 mm，rejoin 1.00 → 0.68 s）；impulse / peak
force / peak torque 与 Fixed WBC 完全一致（碰撞瞬时由 rod 运动学主导，ESN 响应在接触后）；
recovery jerk 是唯一劣于 Fixed WBC 的指标（126.8±2.9 vs 15.0 m/s³ @fx3，与 reference
119.2 同量级）。no-rod mean yielding twist 0.001057±0.000064 m/s（远低于 0.005 上限）。

## Twist 层 VMC baseline（v5 增补，核心对比方法）

按「VMC 必须进同一 WBC 环境当 baseline」的实验设计，新增
`scripts/vmc_compliance_baseline.py`：

- **控制律**：六维饱和弹簧阻尼偏移动力学（继承 v4 VMC benchmark 的参数化），
  `M ẍ + D ẋ + σtanh(Kx/σ) = σtanh(K_e·dead(e)/σ) + D_e·dead(ė)`，在 twist 层执行，
  输出与 Direct ESN 完全相同的 7-D action（同 safety adapter、同 env）。
- **信息集与 ESN 对齐**：只读 WBC pose/twist tracking error（本体感受），不读接触力；
  死区按 no-rod WBC 底噪 p95 定标（pos 8 mm / ori 32 mrad / lin 30 mm/s / ang 100 mrad/s），
  非调优参数。
- **调优协议对称**：κ/ζ/drive 网格（36 配置）只在 train fixtures 0-2 上选择
  （best：κ_t 1.0、κ_r 2.0、ζ 0.8、drive 2.0），fx3 held-out 只评。
- 单元测试 `tests/test_vmc_compliance_baseline.py`（8 项：零误差静止、死区、有界性、
  回归、gated 软化、npz 往返）。

结果（`paper_tables/paper_main_tables_v2_vmc.md`，四方法同表）：

| 维度 | VMC (tuned) | Direct ESN BC (8 seeds) | 胜者 |
|---|---|---|---|
| fx0/1/2 ΔRMSE | −0.21 / −0.53 / −2.23 | **−0.98 / −2.60 / −3.31** | ESN |
| fx3 (held-out) ΔRMSE | **−6.67** | −2.21 | VMC（含窗口效应，见下） |
| fx3 whole-episode peak dev | **25.1 mm** | 27.0 mm | VMC（小幅） |
| Rejoin latency (fx0-3) | 0.96/1.16/1.36/1.20 s（全慢于 FW） | **0.80/0.64/0.52/0.68 s**（全快于 FW） | ESN |
| Recovery jerk (fx0-2) | **13–18** | 64–133 | VMC |
| Contact impulse vs FW | +2~3%（接触延长） | **±0.0%（一致）** | ESN |
| No-rod yield | 0.00179 m/s ✓ | 0.001057±0.000064 ✓ | 均过 gate |

关键发现：

1. **评价协议注意事项**：VMC 让步慢导致 rod 接触延长（fx3 release 1.56 vs 1.36 s），
   post-contact 窗口起点后移，其 fx3 RMSE 优势部分来自窗口效应；表中已补
   whole-episode peak deviation 作为窗口鲁棒指标（VMC 仍小幅更好）。
2. **ESN 的隐性优势**：快速 yield 使接触尽快结束，impulse 与 Fixed WBC 完全一致；
   VMC 接触延长使 impulse 增加 2–3%。
3. 诚实结论：这是 Pareto 对比而非全面碾压——ESN 胜在恢复速度（1.5–2.5×）、
   train fixture 误差、接触快速终止；VMC 胜在光滑性与最强碰撞下的偏离控制。
   ESN 的 recovery jerk 短板（vs FW）对手工 VMC 律仍然成立，是后续工作。

## Spring-carriage VMC 忠实复刻与 EMA 消融（v6 增补）

### 忠实复刻（替换 v5 的简化 admittance 版）

`vmc_compliance_baseline.py` 重写为 **spring-carriage 双弹簧-质量结构**，完整复刻
v4 冻结控制器（`run_benchmark.py::SixDVirtualCarriage`）：

- virtual carriage（mass 1.25 kg / inertia 0.08，drive 弹簧 75/7，ζ 1.15）跟踪 WBC nominal；
- EE 六维饱和弹簧（base 220/18 × 冻结 KAPPA_6D，饱和 24 N/3 Nm，ζ 1.05）；
- 执行映射：WBC 速度环取代 `J^⊤w` 力矩通路，输出 yield_twist = carriage 速度，同一
  7-D action 接口与 safety adapter；**全部物理参数冻结零调优**；
- 两变体：`proprioceptive`（EE 耦合反作用由 WBC 跟踪误差估计，信息集与 ESN 完全对齐）
  与 `force_feedback`（测量 rod-on-hand 世界系 wrench 驱动，经相同通道饱和 + carriage
  自限项——信息集上界，读取 ESN 合同禁止的信号）。
- 已记录的 twist 层适配（非隐藏差异）：WBC 底噪死区（v4 力矩层 proxy 误差 0.3 mm 不需要）。

实现过程中修复并单测覆盖的三个问题：子步内外力更新缺失导致 ±速度限幅振荡；force
变体原始接触力直推 1.25 kg carriage（v4 carriage 只受饱和 EE 弹簧力）；force 变体缺
carriage 自限回归项（稳态 24 N/75 N·m⁻¹ ≈ 0.32 m 漂移）。wrench 世界系符号经 fixture-2
碰撞事件实证校准（`wbc_velocity_residual_env._rod_hand_wrench_world`）。

### 主表 v3（`paper_main_tables_v3_spring_carriage.md`）

| 方法 | fx0-3 ΔRMSE | rejoin (fx2/fx3) | recjerk (fx0-3) | impulse |
|---|---|---|---|---|
| Fixed WBC | 基线 | 0.96 / 1.00 s | 6/10/2.5/15 | 基线 |
| SC-VMC proprio（冻结） | +0.1/+1.0/+1.7/+1.9 | **0.60 / 0.52 s** | 32/31/118/116 | 略低 |
| SC-VMC force（冻结） | +0.1/+0.4/+1.0/+0.7 | 1.00 / 1.04 s | **6/11/3/15（≈FW）** | 略低 |
| ESN BC 8-seed | **−1.0/−2.6/−3.3/−2.2** | 0.52 / 0.68 s | 10/64/133/127 | 一致 |

结论：零调优忠实 SC-VMC 在 RMSE 上不优于 Fixed WBC（+0.1~+1.9 mm），proprio 变体
rejoin 显著快、force 变体 jerk 与 FW 无差别——**ESN 的 RMSE/rejoin 优势在最强 VMC
baseline 下保持**；SC-VMC force 的 jerk 上界说明 ESN 的 jerk 短板不是柔顺控制的必然
代价，仍属未解决问题。v5 的调优 admittance 简化版（t08）降级为中间产物（附录参考），
主表以冻结参数版本为准。

### ESN yield EMA 消融（负结果）

部署端一阶低通（`yield_smoothing_alpha`）在 seed 251 上呈现理想 trade-off
（α=0.25：fx1 jerk 75→33、fx2 135→82，RMSE 损 ~16%），但 8-seed 全量验证暴露
**train/held-out 不对称**：held-out fx3 ΔRMSE 从 −2.207 退到 −0.86（α=0.4）/−0.64
（α=0.25），且 fx3 jerk 无改善（116–122 vs 127）。EMA 降 train jerk 是靠延迟响应，
强碰撞 held-out 场景响应延迟直接伤精度。**结论：部署端平滑不是 recovery jerk 的解**，
默认 alpha=1.0（关闭），扫描数据保留为 ablation（`ema_scan/`、`ema_full/`）。



## 论文对照与恒力牵引变体（v7 增补）

### Baseline 与两篇 Forni 组论文的对应关系

复刻的直接依据是仓库冻结实现（`run_benchmark.py::SixDVirtualCarriage` + `VMCConfig` +
`KAPPA_6D`）；经论文原文核对，仓库实现与论文的对应为：

| 元素 | 论文出处 | 仓库/本实现 | 一致性 |
|---|---|---|---|
| Spring-carriage 机构（EE 弹簧连 virtual cart + 机器人反作用 w） | Zhang, Larby, Iida, Forni (IROS 2024) Eq (5a,5b), Fig 1d | `SixDVirtualCarriage` + twist 层 `SpringCarriageVMC` | 结构忠实 |
| 饱和弹簧 `f = σtanh(k·z/σ)` | Zhang, Iida, Forni (rock-chop) Eq (2) | `saturated_spring`（逐字等价） | 公式级一致 |
| 力矩映射 τ = ΣJᵢᵀfᵢ | 两文 Eq (1) | 仓库保留；twist 层换为 WBC 速度环 | 仓库层一致，twist 层适配 |
| Cart 驱动：恒力 f_C + 粘性摩擦 b | IROS 2024 Eq (5b) | 仓库改为 drive 弹簧拉向 nominal（= 同文 Fig 1c moving-target 思想）；本版补恒力变体 | 见下 |
| 3D→6D、κ 六维、KAPPA_6D 调优 | —（论文为 3D 平移） | 仓库扩展 | 任务适配 |
| 切换机构（switched references）、能量罐 | rock-chop / passivity 引用 | 仓库 vmc_gated/energy；未进 twist 层 baseline | 未复刻 |
| force-feedback 变体 | —（两文均无；论文 w 是模型内反作用） | 本项目构造（信息集上界） | 非论文方法 |

### 恒力牵引变体（Eq 5b 原味）结果

`carriage_drive="constant_force"`：恒幅值切向牵引（仅平移，静止段为零的任务适配）+
粘性摩擦作用于绝对 carriage 速度 + EE 耦合反作用，无位置恢复项。单测验证稳态
（pull/摩擦/弹簧反作用三方平衡，carriage 与 nominal 同速、亚毫米偏移）。

| 牵引 | fx0-2 ΔRMSE | fx2 rejoin | held-out fx3 |
|---|---|---|---|
| 0.5 / 1.0 / 2.0 N | +0.07/+1.07/+1.8（与 spring 版相当） | 0.56–0.60 s | **task fail（三档全失败，ΔRMSE ≈ +3.4）** |

结论：论文原始恒力驱动在 train 碰撞上与 drive 弹簧版等价，但**无位置恢复项使 carriage
在 held-out 强碰撞后无法精确回归完成抓取**——drive 弹簧（Fig 1c moving-target 思想）是
本任务的必要适配，而非任意改动。恒力变体进主表 v4 作为「论文原味驱动」对照行
（`paper_main_tables_v4_constant_pull.md`，含 v3 全表）。

论文建议表述：*VMC baseline implementing the spring–carriage architecture of Zhang et al.
(IROS 2024) with the saturating virtual springs of Zhang et al. (rock-chop), extended to six
dimensions and executed in the WBC twist layer; the paper's original constant-pull drive is
included and shown to require the moving-target adaptation for grasp recovery.*

## 最强 baseline 调优协议（v8 增补）

为消除"baseline 未调至最强"的质疑，对两个 spring-carriage 变体施加与 ESN 对称的
train-only 调优（27 网格：EE 弹簧整体缩放 {0.5,1,2} × drive 弹簧缩放 {0.5,1,2} ×
ζ_ee {0.8,1.05,1.4}；score = mean dRMSE − 0.5×rejoin 惩罚 − 0.005×mean jerk；
死区不参与调优——底噪定标，调它即作弊；held-out fx3 与 OOD 只评一次）。

最优配置与完整矩阵（`paper_main_tables_v5_tuned.md`、`tuned_full_eval.json`）：

| | ΔRMSE fx0-3 | rejoin | recjerk | OOD 4 点 |
|---|---|---|---|---|
| SC-VMC proprio (tuned: κ×0.5, drive×1.0, ζ0.8) | +0.07/+0.68/+1.53/+1.83 | 0.88/0.84/0.64/0.56（后两快于 FW） | 43/46/96/100 | 3/4 success（corner fail +3.65） |
| SC-VMC force (tuned: κ×2.0, drive×2.0, ζ0.8) | **+0.01/+0.11/+0.24/+0.29** | ≈FW | **6/12/3/14（=FW）** | 4/4 ≈FW（+0.17~+0.30） |
| ESN BC 8-seed | **−0.98/−2.60/−3.31/−2.21** | 快于 FW | 64/133/127 | 4/4 大幅改善（−1.7~−3.0） |

最终结论（最强 baseline 协议下）：调优后的 force-VMC 收敛为「透明柔顺」——
处处与 Fixed WBC 持平（RMSE ±0.3 mm 内、jerk 相同），不改善精度；proprio-VMC
以精度换 rejoin；**ESN 集成仍是唯一在全部 fixture 上 RMSE 优于 Fixed WBC 且
rejoin 更快的方法**。冻结参数版（v3）与论文原味恒力驱动（v4）保留为对照行。

## 服务器路径

- 输出根目录：`/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/`
  - `expert_traces/`（19 rod + no-rod + manifest.json）
  - `bootstrap/`（8 seeds）、`bootstrap_gate/gate_summary.json`
  - `spring_carriage/`（v6：两变体 checkpoints + eval + spring_carriage_eval.json）
  - `ema_scan/`、`ema_full/`（v6：EMA 消融数据）
  - `dagger_seed_{13,42,71,137,251,307,512,1009}/`
  - `iter_train_select/selection_summary.json`（train-only iteration 选择）
  - `iter1_holdout/iter1_holdout_summary.json`（DAgger iter1 held-out）
  - `multiseed_statistics.json`（本表数据源；no-rod yield 统计 v3 已重算）
  - `ood_stroke_scan/`、`ood_geometry_scan/`（v3 泛化扫描）
  - `paper_tables/`（v4 主表 csv/png；v5 `paper_main_tables_v2_vmc.md`；v6 主表 `paper_main_tables_v3_spring_carriage.md`）
  - `vmc_baseline/`（v5：baseline checkpoints、tune 网格、smoke 与 eval 产物）
- **正式随机化候选 checkpoints**：`bootstrap/bootstrap_seed_{13,42,71,137,251,307,512,1009}.npz`
  （8 个独立 reservoir，全部通过 gate）
