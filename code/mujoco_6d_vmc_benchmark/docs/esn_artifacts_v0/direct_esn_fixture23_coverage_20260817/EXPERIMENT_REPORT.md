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

## 服务器路径

- 输出根目录：`/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/`
  - `expert_traces/`（19 rod + no-rod + manifest.json）
  - `bootstrap/`（8 seeds）、`bootstrap_gate/gate_summary.json`
  - `dagger_seed_{13,42,71,137,251,307,512,1009}/`
  - `iter_train_select/selection_summary.json`（train-only iteration 选择）
  - `iter1_holdout/iter1_holdout_summary.json`（DAgger iter1 held-out）
  - `multiseed_statistics.json`（本表数据源；no-rod yield 统计 v3 已重算）
  - `ood_stroke_scan/`、`ood_geometry_scan/`（v3 泛化扫描）
  - `paper_tables/`（v4 论文主表：markdown / csv / png；v5 增补 `paper_main_tables_v2_vmc.md`）
  - `vmc_baseline/`（v5：baseline checkpoints、tune 网格、smoke 与 eval 产物）
- **正式随机化候选 checkpoints**：`bootstrap/bootstrap_seed_{13,42,71,137,251,307,512,1009}.npz`
  （8 个独立 reservoir，全部通过 gate）
