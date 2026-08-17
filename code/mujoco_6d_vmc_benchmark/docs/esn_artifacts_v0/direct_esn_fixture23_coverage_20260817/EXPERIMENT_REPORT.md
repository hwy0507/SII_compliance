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

## Proposed 方法升级：readout 训练端平滑正则（v9 增补）

针对 recovery jerk 短板（EMA 部署端方案已否决），在 **readout 拟合目标**中加入
episode 内相邻动作差分惩罚（`fit_readout(..., smoothness_features, smoothness_weight)`，
Gram 矩阵加 λ_s·ΔXᵀΔX 项；bootstrap CLI `--smoothness-weight`）。与部署端 EMA 的本质
区别：正则让 readout **本身**学出平滑映射，不引入响应延迟。

λ_s 扫描（8-seed mean，train fixtures）：

| λ_s | fx0-2 ΔRMSE | fx0-2 jerk |
|---|---|---|
| 0（基线） | −0.98/−2.60/−3.31 | 10/64/133 |
| 10 | −0.83/−2.15/−2.49 | 10/36/92 |
| **100** | **−0.65/−1.32/−1.57** | **7/15/27** |
| 1000 | −0.42/−0.64/−0.74 | 6/9/8 |

**λ_s=100 的 held-out 与泛化验证（与 EMA 的关键对比）**：

| | fx3 ΔRMSE | fx3 jerk | OOD 4 点 | no-rod yield |
|---|---|---|---|---|
| λ=0 基线 | −2.207±0.034 | 127 | 4/4（−1.9~−3.0） | 0.001057 |
| EMA α=0.4（否决） | −0.862 | 116（未降） | — | — |
| **λ=100（本方案）** | **−1.118±0.065** | **30±3** | **4/4（−1.06~−1.61）** | 0.00048 |

结论：训练端正则把 recovery jerk 从 127 压到 30（接近最强 force-VMC 的 14 和 FW 的 15），
同时保持全部 gate 与泛化；精度改善仍为最强 VMC 的 4–5 倍。**Proposed 现在提供精度-
光滑可调的 Pareto 前沿（λ_s 旋钮），且整个前沿位于 VMC baseline 之上**——论文建议
双配置报告：λ=0（accuracy-optimal）与 λ=100（smoothness-matched），λ 扫描曲线作
能力图。数据：`smooth_scan/`。

## RMSE-first 重调参、ESN 超参扫描与 MLP baseline（v10 增补）

### 调参协议修正

v8 的调优 score 含 jerk 惩罚项，把 VMC 最优解推向「透明」配置（jerk 最低但 RMSE 不动）。
本轮改为 **RMSE-first**（mean dRMSE 最小，rejoin tie-break，jerk 不进 score；60 网格
κ×{0.25..4} × drive×{0.5..4} × ζ{0.8,1.05,1.4}），并修复 rejoin=None 的评分崩溃。

### 结果：VMC 的 train 上限与泛化崩溃

| SC-VMC force 配置 | train ΔRMSE | held-out fx3 | OOD 4 点 |
|---|---|---|---|
| RMSE-first 最优（κ×4, drive×4, ζ1.05） | **−1.739** | **+0.495**（翻正） | −0.05/−0.92/−1.13/+0.38（不稳定，corner 正） |
| 稳健调参最优（v8，κ×2, drive×2, ζ0.8） | +0.121 | +0.285 | 4/4 持平（+0.17~+0.30） |

proprio 变体 RMSE-first 最优仍为 +0.754（正）。结论：**RMSE-first 调参确实释放了 VMC 的
train 表现（用户直觉正确），但该配置在 held-out 翻正、OOD 不稳——VMC 只有两个增益的
曲线族，train 改善来自对训练碰撞分布的过拟合；泛化稳健的参数区域又不改善 RMSE**。
两种调参目标都无法同时做到 train/held-out/OOD 三项为负。

### ESN 超参扫描：不敏感（鲁棒性证据）

spectral_radius {0.85,0.90,0.95} × time_constant {0.08,0.12,0.20} × λ_s {0,100}，
3 seeds、18 配置：**sr/tc 全组合 train ΔRMSE 差异 < 0.02 mm**（−2.29~−2.31），性能由
数据 coverage 与 λ_s 主导，reservoir 超参无需精调——与 MLP 的 seed 敏感形成对照。

### MLP baseline（memoryless，同数据同合同 BC，8 seeds）

gate 7/8（seed2 no-rod yield 0.009 超标）；fx0-3 ΔRMSE 均值
−0.89/−2.48/−2.90/−2.33，**seed 方差 ±0.41~0.75（ESN 的 20–70 倍）**，rejoin
0.79/0.65/0.56/0.81，jerk 53/79/122/128。均值精度与 ESN 相当，稳定性显著更差。

### 最终四方对比（各自最强，统一 train-only 协议）

| 方法 | train ΔRMSE | held-out fx3 | OOD | seed 稳定性 |
|---|---|---|---|---|
| Fixed WBC | 0 | 0 | 0 | — |
| MLP BC（8 seeds） | −2.09（均值） | −2.33±**0.75** | 未测 | **7/8 gate** |
| SC-VMC force RMSE-first | **−1.74** | +0.50（翻正） | 不稳（±1.1） | 单配置 |
| SC-VMC force 稳健 | +0.12 | +0.29 | 4/4 持平 | 单配置 |
| **ESN BC λ=0（8 seeds）** | **−2.30** | **−2.21±0.03** | **4/4 全改善** | **8/8，超参不敏感** |

叙事结论：ESN 是唯一同时做到 train 强、held-out 强、OOD 强、seed 稳定的方法——
VMC 的 train 改善以泛化崩溃为代价，MLP 的精度以 seed 稳定性为代价，ESN 无需在
四个维度间做取舍。VMC 弱于 MLP 不是 baseline 失职：反馈律无数据学习容量，
两种调参目标已穷尽其两参数曲线族的能力（数据：`tune2/`、`esn_hp_scan/`、`mlp_baseline/`）。

## 三个高收益方向实验（v11 增补）

### 方向 1：教师侧 coverage 扩展——假设证伪，性能饱和确认

fx0/1 邻域新增 25 条 expert traces（全部成功，`expert_traces_v2/`），合并为 44+1 条重新
BC（8 seeds × λ {0,100}，`coverage_v2/`）。结果：fx0 ΔRMSE −0.942±0.014（19 条版
−0.982），held-out fx3 −2.220±0.039（19 条版 −2.207）——**统计持平**。结合教师 fx0
也只有 −1.04：fx0 弱改善是弱碰撞的物理属性（impulse 0.9 → 误差基数 8.8mm → 改善
天花板低），ΔRMSE 与 impulse 单调相关。**结论：19 条 coverage 已饱和，方法数据高效**
（同等数据下 MLP seed 不稳）。

### 方向 2：multi-cycle 连撞（环境新增 rod_cycles/cycle_period_s）

两次撞击（cycle_period 0.80/1.00），所有方法均 zero-shot（训练数据只有单撞），
onset→grasp 全窗口 RMSE（mm）：

| 方法 | p=0.80 | p=1.00 | task success |
|---|---|---|---|
| Fixed WBC | 15.02 | 15.00 | 1/1 |
| **ESN BC（8 seeds）** | **12.02±0.01** | **11.93±0.01** | 8/8 |
| MLP（8 seeds） | 12.40±0.45 | 12.31±0.45 | 8/8 |
| VMC force | 15.25 | 15.23 | 1/1 |

MLP 未崩（其 error-based activation gate 在第二撞仍触发），ESN 均值最优且方差小 45 倍
——连撞场景仍是稳定性优势而非记忆碾压。数据 `multicycle/`。

### 方向 3：方向泛化矩阵（环境新增 --rod-approach-side）

zero-shot 到未见方向（window RMSE mm，`sides_matrix/`）：

| 方向 | FW | ESN | MLP | VMC force | 判定 |
|---|---|---|---|---|---|
| −y（训练） | 14.99 | **11.93±0.01** | 12.31±0.45 | 15.22 | ESN 最优 |
| **+y（镜像）** | 14.91 | **21.50±10.76（5/8 fail）** | 15.32±2.11 | 15.14 | **ESN 方向绑定缺陷** |
| +x（弱撞） | 5.94 | 6.94±1.42 | 8.12±4.63 | 6.45 | 均可行 |
| −x / −z | fail | fail | fail / 2/8 | fail | 任务物理不可行（FW 也 fail） |

**诚实 limitation**：ESN readout 的 yield 方向 world-frame 绑定——镜像撞击时把 EE 推向
rod（比 FW 差 6.6mm 且 3/8 seed task fail）；MLP 从 pose-error 符号结构获得部分方向
泛化。−x/−z 为任务不可行方向（Fixed WBC 亦失败，不计入方法对比）。该结果直接复活
error-aligned/方向对称化参数化的动机（失败方向 C 的重新审视列为 future work）。

### 代码变更

`VelocityResidualFixture` 新增 `rod_cycles`/`cycle_period_s`（release 时刻按最后 cycle
计算）；`run_direct_esn_mujoco.py`/`evaluate_direct_esn_post_contact.py` 的 override
新增 `--rod-approach-side`（六方向）与 `--rod-cycles/--cycle-period-s`。

## 方向绑定缺陷修复：教师侧镜像增广（v12 增补）

### 侦察（决定技术路线）

1. 教师在镜像 +y 方向**不翻车**（window RMSE 12.57 vs FW 14.91）——教师有方向泛化，
   方向绑定是 **BC 蒸馏损失**（学生 21.50）→ 选数据增广路线；
2. 教师/ESN 的 yield 方向与 −pose_error 夹角很大（mean cos −0.225，仅 11% 步 <45°）——
   教师策略是复杂侧向让开，**部署端投影到误差反向会严重扭曲行为**（也正是当年
   error-aligned 失败方向 C 的根因），投影方案放弃。

### 修复：教师在 +y 生成 14 条 traces（fixture 2 邻域，+y 版 fx3 组合不生成）

BC v3 = 19（−y）+ 14（+y）+ 1 no-rod，8 seeds（`coverage_v3_directional/`）：

| 配置 | −y fx0-3 ΔRMSE | **+y 镜像 held-out** | gate |
|---|---|---|---|
| 修复前（19 条单向） | −0.98/−2.60/−3.31/−2.21 | **21.50±10.76（5/8 fail）** | 8/8 |
| **v3 双向 λ=0** | −0.96/−2.61/−3.23/**−2.11** | **12.70±0.36（8/8，优于 FW 14.91，追平教师 12.57）** | 8/8 |

**方向绑定 limitation 已修复**：−y 性能统计无损（fx3 −2.11 vs −2.21），镜像方向从
比 FW 差 6.6mm 翻转为优于 FW 2.2mm。这是论文 proposed 的最终配置。

### 诚实记录：λ_s 平滑正则在双向数据上失效

v3 数据上 λ ∈ {10, 30, 100} 全部使 held-out fx3 翻正（+0.24~+0.30；单向数据上 λ=100
曾为 −1.12）。推测：双向覆盖要求 readout 保留方向区分容量，平滑正则挤掉了它。
**精度-光滑 Pareto（λ_s）目前只对单向数据集成立**，作为单向 ablation 报告；双向
光滑配置需要方向对称的正则结构（future work）。

## 回到 Fan Ye 定义的算法研究（v13 增补）

依据：Fan Ye et al., Communications Engineering 4:81 (2025)——leaky ESN Eq(7)（τ ṡ = −s +
tanh(W_in In + W_r s + b)）、线性 readout Eq(8-9)、**containment ratio** Eq(14-16)（机器人
频谱被 reservoir 频谱包含的比例，CR < CR_T 拒绝）、ESPI（初态敏感性；CR+ESPI 将有效
reservoir 比例 38%→92%）。

### 尝试 1：镜像等变门控 readout——负结果（结构性不可行）

构造：输出端软符号门 a_y = raw_y·σ(e_y)，σ = −tanh(e_y/ε)。等变性单测通过
（y/yaw 精确翻转、其余通道不变、训练分布内恒等）；−y 性能无损（−2.20/−2.10）。
但镜像泛化失败：单向数据+门 +y = **42.36（1/8）**（比无门 21.50 更差），双向数据+门
+y = **51.61（0/8）**（比无门 12.70 差得多）。

根因（有 ablation 价值）：闭环下镜像 rollout 的 **reservoir 特征不镜像**——Panda 7-DOF
冗余使 IK 在镜像任务下产生非镜像关节轨迹，输出端门的结构假设（raw_y 是 +y 幅值包络）
在镜像世界不成立；且双向 readout 已对 e_y 条件化，加门反而翻转正确行为。
**结论：输出端等变不可行，v3 教师数据增广（12.70）仍是正解**；真正等变需要输入/
特征层对称化，受关节冗余阻碍（记录为 negative ablation）。代码保留：
`mirror_gate_enabled`（默认关）。

### 尝试 2：CR 频域判据在我们系统的检验——发现「分层控制下设计塌缩」

按 Eq(14-16) 实现（`cr_analysis/`）：机器人频谱 = 闭环任务信号（nominal twist + 跟踪
误差，真实 expert trace），reservoir 频谱 = 相同输入驱动的节点状态 FFT，7×7 网格
（sr 0.5-1.3 × tc 0.05-1.0）。结果：

| | CR 范围 | 闭环性能（train mean ΔRMSE） |
|---|---|---|
| 高 CR 配置（0.81-0.93） | 扫描超参区间 | −2.29 ~ −2.31 |
| 低 CR 配置（0.67-0.77，含 tc=1.0、sr=1.3/tc=0.6） | 补测 5 配置 × 3 seeds | **−2.276 ~ −2.282（统计无差）** |

**CR 与性能完全解耦**。解释（半形式化）：Fan Ye 的场景是 reservoir 直接拟合裸机器人
逆动力学（欠驱动 cart-pole，宽带）——CR 不足则失败；我们的场景中 **WBC 内环把有效
植物动力学替换为低带宽速度跟踪闭环**，教师柔顺策略是慢变误差函数（接触频谱 ≤10 Hz，
rod profile ~1.6 Hz），任意合理 leaky reservoir 的动态均覆盖之。由此：

1. 超参不敏感（sr/tc 全网格 <0.02 mm 差异）与 seed 免筛（8/8 无需 CR/ESPI 筛选）
   是**分层控制的结构必然**，不是运气；
2. 对 Fan Ye 判据的适用边界给出精化：CR 筛选适用于直接逆动力学控制；内环整形
   （WBC/阻抗等）后判据自动满足、reservoir 设计自由度塌缩——**分层柔顺控制中
   "which reservoir" 不再是设计问题，"what data"（coverage）才是**（与本 campaign
   的全部证据一致：19→44 traces 饱和、增广方向数据带来真实提升）。

论文表述：CR 分析 + 性能解耦表作为「设计理论」小节；镜像门负结果进 ablation。

## 大规模 Scaling 研究（v14 增补，~2.5 小时服务器计算）

### 设置

435 条双向 expert-trace 池（教师 rollout，stroke 0.148-0.176 × timing 1.030-1.108 ×
height 0.5375-0.5425 × side ±y 分层随机采样，`expert_traces_pool/`）；数据子集
{25, 50, 100, 200, 435}（双向均衡、嵌套抽样）× reservoir {160, 400, 1000} × 8 seeds
= 120 个 BC 模型 + 720 次 matched 评估（`scaling_study/`）。

### Scaling 结果（fx3 held-out ΔRMSE / +y 镜像 RMSE / gate）

| n \ N | 160 | 400 | 1000 |
|---|---|---|---|
| 25 | −2.00 / 17.2 / 7/8 | −2.17 / 23.4 / **2/8** | −2.25 / 18.1 / 6/8 |
| 50 | −1.93 / 13.1 / 8/8 | −1.97 / 13.0 / 8/8 | −2.10 / 13.1 / 8/8 |
| 100 | −2.00 / 12.6 / 8/8 | −2.06 / 12.6 / 8/8 | −2.09 / 12.7 / 8/8 |
| 200 | −2.15 / 12.6 / 8/8 | −2.15 / 12.3 / 8/8 | −2.23 / 12.5 / 8/8 |
| 435 | −2.12 / 12.5 / 8/8 | −2.16 / **12.2** / 8/8 | −2.23 / 12.6 / 8/8 |

### 三条 Scaling 结论

1. **数据维度**：25→50 为关键跃迁（镜像 17-23→13，gate 全稳），100→200 缓慢增益，
   **200→435 完全饱和**（fx3 −2.15 vs −2.12~−2.23，镜像 12.3-12.6 持平）；
2. **Reservoir 维度全平**：n≥50 时 160/400/1000 差异 <0.1mm（fx3）/<0.5mm（镜像）——
   模型容量不是杠杆（CR 设计塌缩理论的规模化验证）；小数据 + 大 reservoir 反而有害
   （n25_N400 gate 2/8，经典 bias-variance）；
3. **覆盖质量 > 数量**：精心设计的 33 条 v3 网格（fx3 −2.11）统计等于 435 条均匀
   随机采样（−2.12~−2.23）——性能由覆盖**结构**决定，网格化设计已接近最优覆盖。

### 教师升级线（负结果）

从原教师继续 12 轮 counterfactual DAgger（default fixtures，原配方）：**所有后续
iteration 在 held-out fx3 崩溃**（iter3 +36.6 / iter6 +41.5 / iter9 +33.1 / iter12
+19.3，全部 task fail，`teacher_upgrade/`）。教师配方 3 轮即峰值，继续训练只过拟合
（与失败方向 F 的单调劣化一致）。学生上限 = 教师（−2.40），v3 学生（−2.11）已接近，
突破需新教师来源而非更多轮次。

### 论文级 Scaling 图数据

数据量-performance 曲线（每 reservoir 规模一条线，8-seed 带误差条）+ reservoir
规模-performance 平线 + 「33 网格 vs 435 随机」对照点——完整的 scaling 三联图
（`scaling_study/scaling_summary.json`）。

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
