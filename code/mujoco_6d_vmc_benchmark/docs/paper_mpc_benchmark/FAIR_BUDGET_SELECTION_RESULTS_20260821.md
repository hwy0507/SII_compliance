# ESN–VMC 共享预算验证选择与独立测试（服务器，2026-08-21）

## 可汇报结论

在双方都可从同一组残差预算中选择、并将选择与最终测试严格分开的协议下，ESN-303
与 VMC（`k=1.5`）均达到 **50/50 成功**。独立测试集的总体抓取误差分别为
`9.229 ± 2.737 mm`（ESN）和 `9.357 ± 2.999 mm`（VMC）；按五个测试 seed 做配对
平均，ESN−VMC 为 `−0.128 mm`，95% t 区间为 `[−0.715, +0.460] mm`。

因此，当前证据只支持“二者在此基准上成功率相同、总体误差没有可分辨的差异”，**不支持
ESN 已经总体战胜 VMC**。ESN 在 ball/board 子场景误差较低，但在 rod 子场景较高，不能用
总体均值的极小差异作优越性结论。

这是对先前“场景调参 VMC”的补充和更严格替代：VMC 不再按 rod/ball/board 单独使用预算，
而是与 ESN 一样先在 validation 集上选择一个全局配置，再一次性评估未参与选择的 test 集。

## 目的与预先固定的协议

目标是检验“若不固定 3% 预算，ESN 是否仍能与解析 VMC 公平比较”。在运行 held-out test 前，
以下规则已由 [`run_fair_budget_selection.py`](../../scripts/run_fair_budget_selection.py) 固定：

| 项目 | 设置 |
|---|---|
| validation seeds | `20260819, 20260820, 20260821, 20260822, 20260823` |
| held-out test seeds | `20260824, 20260825, 20260826, 20260827, 20260828` |
| 每个 seed 的工况 | 4 rod + 4 ball + 2 board，共 10 条 rollout |
| 匹配随机化 | `rod_stroke ±0.0020 m`，`rod_height ±0.0015 m`，`rod_start_time ±0.0150 s`；同一 seed/场景对两方法完全相同 |
| ESN candidates | 已冻结的 `esn_final_{101,202,303}.npz` × budget `{2%, 3%, 5%, 8%}` |
| VMC candidates | `k ∈ {1.5, 2.2, 3.2, 4.6}` × 相同 budget `{2%, 3%, 5%, 8%}` |
| 选择规则 | 先最大化 validation success rate；同成功率时最小化 validation mean at-grasp error |
| 测试规则 | 每一方法只用其选中配置跑一次完整 held-out test；不根据其结果重选 seed、预算或刚度 |

所有 rollout 均在服务器 `arm1@192.168.31.70` 的 MuJoCo 运行时完成：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
Python: /home/arm1/vmc_mujoco_runtime/.venv/bin/python
MuJoCo menagerie: /home/arm1/vmc_mujoco_runtime/mujoco_menagerie
raw result: /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_fair_selection_20260821/fair_selection_results.json
run log: /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_fair_selection_20260821/fair_selection.log
```

## Validation 选择结果

表中格式为 `success/50；mean at-grasp error (mm)`。该表仅用于选择，不能当作最终性能
报告。

| 方法候选 | 2% | 3% | 5% | 8% |
|---|---:|---:|---:|---:|
| ESN-101 | 50/50；9.328 | 50/50；10.034 | 22/50；11.250 | 0/50；132.783 |
| ESN-202 | 50/50；10.295 | 50/50；9.792 | 31/50；9.917 | 2/50；246.601 |
| ESN-303 | 50/50；9.226 | **50/50；9.174** | 10/50；124.793 | 0/50；293.420 |
| VMC k=1.5 | 50/50；17.123 | **50/50；9.278** | 23/50；13.590 | 17/50；16.804 |
| VMC k=2.2 | 50/50；29.036 | 46/50；19.510 | 35/50；20.370 | 18/50；25.837 |
| VMC k=3.2 | 50/50；39.188 | 38/50；31.729 | 27/50；203.313 | 0/50；202.121 |
| VMC k=4.6 | 50/50；43.988 | 34/50；42.708 | 0/50；303.973 | 0/50；384.924 |

故完全由 validation 规则选中：

| 家族 | 选中配置 | validation 成功率 | validation 抓取误差 | 平均障碍接触力 |
|---|---|---:|---:|---:|
| Proposed ESN | ESN-303，budget 3% | 50/50 | 9.174 mm | 70.592 N |
| 解析基线 VMC | `k=1.5`，budget 3% | 50/50 | 9.278 mm | 64.931 N |

## 独立测试结果

下表的 `±` 是 50 条（或子场景条数）rollout 的样本标准差，仅描述该测试集的离散度；
显著性判断使用随后给出的按 seed 配对分析。`obstacle force` 是机器人与 rod/board 的峰值
法向接触力，每个 rollout 取峰值、再聚合；它未参与模型选择。

| 场景 | ESN-303（3%）成功 | ESN 抓取误差 (mm) | ESN 接触力 (N) | VMC k=1.5（3%）成功 | VMC 抓取误差 (mm) | VMC 接触力 (N) |
|---|---:|---:|---:|---:|---:|---:|
| rod | 20/20 | 11.701 ± 2.678 | 39.312 ± 15.168 | 20/20 | 9.312 ± 1.452 | 41.365 ± 14.284 |
| ball | 20/20 | 7.557 ± 1.192 | 104.650 ± 13.019 | 20/20 | 9.845 ± 4.519 | 105.502 ± 12.904 |
| board | 10/10 | 7.630 ± 0.000 | 65.571 ± 0.000 | 10/10 | 8.470 ± 0.000 | 32.853 ± 0.000 |
| 全部 | **50/50** | 9.229 ± 2.737 | 70.699 ± 32.139 | **50/50** | 9.357 ± 2.999 | 65.317 ± 35.384 |

### 配对解释（ESN − VMC）

每个测试 seed 先在其 10 条 rollout 内求均值，再计算 ESN−VMC；这样比较使用的是完全匹配的
fixture 随机化。五个 seed 的总体误差差分别为 `−0.095, −0.615, −0.026, −0.491,
+0.589 mm`，均值 `−0.128 mm`，seed-level SD `0.473 mm`，two-sided 95% t interval
`[−0.715, +0.460] mm`（`n=5`）。区间跨过零，不能拒绝“总体误差相同”的解释。

分场景的 seed-level 平均差为：

| 场景 | ESN − VMC 抓取误差 | 95% t interval | 正确解读 |
|---|---:|---:|---|
| rod | +2.389 mm | [+1.966, +2.812] | VMC 更小 |
| ball | −2.287 mm | [−3.534, −1.041] | ESN 更小 |
| board | −0.840 mm | [−0.840, −0.840] | 本次固定 board 情形下 ESN 更小，但木板未随机化，不能将 5 个确定性重复当作 5 个独立物理样本 |
| 全部 | −0.128 mm | [−0.715, +0.460] | 无可分辨总体差异 |

力的总体差为 ESN−VMC `+5.381 N`，95% t interval `[+4.957, +5.806] N`。这主要来自固定
木板场景（ESN 比 VMC 高 `32.718 N`）；因此不应以“总体误差接近”掩盖 ESN 在这一接触力指标上的
劣势。

## 信息、公平性与边界

- 两方法共享 PaperMPC 名义速度控制、相同 FR3 MuJoCo 场景、相同 7 维残差力矩限幅，以及
  对每个 seed/scenario 完全相同的 fixture 参数。
- ESN 的输入契约保持冻结：`q`、`qdot`、`nominal_twist`、`pose_error`、`wbc_twist_error`。
  它没有获得 contact force、impactor 位姿/速度、future release time 或其他接触真值。
- VMC 以其解析控制律固有的当前末端 Jacobian 将笛卡尔弹簧力转换为关节力矩；这不是添加给 ESN
  的信息，也不能声称二者具有完全相同的内部模型。此比较回答的是：在相同外部任务和同样的
  残差预算候选集下，学习的本体感受 ESN 与模型驱动 VMC 的端到端控制表现如何。
- `budget` 是相对硬件力矩限位的残差比例，所有候选均满足相同的硬限幅；本实验不再人为规定
  3% 必须最优。恰好两类方法都由 validation 选择到 3%，是结果而非前提。
- 测试 seed 对本次 budget/model selection 未使用，但 ESN 架构、训练数据和三个 reservoir seed
  来自先前开发。故它是**对配置选择的 held-out test**，不是对整个研究开发流程的全新 blind test。
- 该证据仅覆盖 FR3 MuJoCo 的单次冲击、当前轨迹和指定的 fixture 扰动范围；不构成真实机器人、
  多次冲击或未建模接触条件下的性能保证。

## 建议的论文表述

可使用：

> Under a shared residual-budget search and validation-only configuration selection protocol, the proposed ESN and the analytic VMC baseline both achieved 100% success on 50 held-out randomized MuJoCo rollouts. Their overall grasping errors were statistically indistinguishable at the five-seed level (9.229 versus 9.357 mm); ESN was better on ball impacts but worse on rod impacts. We therefore claim competitive, configuration-stable performance rather than a universal superiority over VMC.

不要使用：“ESN 全面超过 / 显著战胜 VMC”。

## 复现命令

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
export MUJOCO_GL=osmesa

python run_fair_budget_selection.py \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --esn-101 /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/esn_final_101.npz \
  --esn-202 /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/esn_final_202.npz \
  --esn-303 /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench/esn_final_303.npz \
  --validation-seeds 20260819,20260820,20260821,20260822,20260823 \
  --test-seeds 20260824,20260825,20260826,20260827,20260828 \
  --budgets 0.02,0.03,0.05,0.08 \
  --vmc-k-values 1.5,2.2,3.2,4.6 \
  --stroke-jitter-m 0.002 --height-jitter-m 0.0015 --start-jitter-s 0.015 \
  --out /home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_fair_selection_20260821/fair_selection_results.json
```

运行脚本的 schema v2 会把 `selection_rule` 和 `validation_candidates` 摘要随结果 JSON 一同写出；
2026-08-21 已完成的原始输出为早先的 schema v1，完整 candidate 记录保存在同目录的
`fair_selection.log`，数值已逐项转录到本报告。
