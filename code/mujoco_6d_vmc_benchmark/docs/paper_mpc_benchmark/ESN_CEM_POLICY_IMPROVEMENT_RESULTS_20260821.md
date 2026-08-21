# ESN 读出策略改进结果（2026-08-21）

## 结论先行

在预先固定的 validation selection + 一次性 held-out test 协议下，CEM 改进 ESN 在全新测试集上优于被同一 validation 集调优的 VMC，且两者成功率均为 20/20、hard torque-limit 均为 0/20。ESN 的 at-grasp error 为 `8.887 ± 1.206 mm`，VMC 为 `9.634 ± 0.887 mm`（mean ± rollout sample SD）。匹配 fixture 的 ESN−VMC 差为 `−0.747 mm`，fixture-level 95% t CI `[-1.220, -0.274] mm`；先按 seed 聚合后为 `−0.747 mm`，seed-level 95% t CI `[-1.440, -0.054] mm`。在这个预先声明的 contact-apparatus MuJoCo 包络内，这一轮结果支持 ESN 的统计可分辨优势，但不能外推为普遍战胜所有 VMC 或真实机器人上的优势。

## 训练期开发结果（不作为测试声明）

CEM 使用 `20261001–20261004` train-only seeds 和 2 fixtures/seed，最终 checkpoint 在其选中的训练 rollout 上为 8/8 success，mean at-grasp error `8.337 mm`，mean peak force `41.723 N`，mean peak torque `33.129 N·m`，mean contact bouts `2.75`，hard limits `0`。该统计仅用于说明优化过程，不能与独立测试结果混用。

输出 gain factors（相对 BC parent）为：

```text
[0.8887569, 0.8811514, 1.0363167, 1.2497377,
 0.9928668, 1.3880309, 0.8440486]
```

## Validation selection

| family | candidate | budget | success | mean error | peak force | peak torque | contact bouts |
|---|---|---:|---:|---:|---:|---:|---:|
| ESN | BC parent | 5% | 20/20 | 9.934 mm | 42.455 N | 33.586 N·m | 3.75 |
| ESN | CEM improved | 5% | 20/20 | **9.154 mm** | 43.238 N | 32.971 N·m | 3.05 |
| VMC | k=2.2 | 5% | 20/20 | 9.746 mm | 43.120 N | 33.479 N·m | 3.55 |

ESN family 因而选择 CEM checkpoint；VMC family 选择 `k=2.2, 5%`。Validation 只用于选择，不是最终性能估计。

## Held-out test

| method | success | at-grasp error | peak contact force | contact bouts | peak torque | hard limit |
|---|---:|---:|---:|---:|---:|---:|
| CEM ESN-303, 5% | 20/20 | **8.887 ± 1.206 mm** | 41.883 ± 12.732 N | 3.10 | 32.993 ± 0.424 N·m | 0/20 |
| VMC k=2.2, 5% | 20/20 | 9.634 ± 0.887 mm | 41.734 ± 12.960 N | 2.90 | 33.469 ± 0.253 N·m | 0/20 |

误差差异按相同 seed 和 fixture 配对：

- fixture-level `n=20`：mean `−0.747 mm`，SD `1.012 mm`，95% t CI `[-1.220, -0.274] mm`；
- seed-level `n=5`（每 seed 4 fixture 先取均值）：mean `−0.747 mm`，SD `0.558 mm`，95% t CI `[-1.440, -0.054] mm`。

ESN 平均峰值接触力高 `0.149 N`，平均峰值 torque 低 `0.476 N·m`；contact-bout count 高 `0.20`。这些是描述性安全/机制指标，不能据此声称 ESN 在所有安全维度都更好。

## 可汇报表述与限制

> After behavior-cloning initialization, a frozen-observation ESN readout was improved using train-only MuJoCo CEM rollouts. On 20 previously untouched randomized finite-mass contact-apparatus realizations, the selected ESN and independently selected VMC both achieved 100% success; ESN reduced at-grasp error from 9.634 to 8.887 mm, with paired 95% CIs excluding zero at both fixture and seed aggregation levels. The result is limited to the declared MuJoCo contact envelope and does not establish sim-to-real superiority.

必须说明：这不是纯 BC，而是“BC 初始化 + 仿真期读出策略改进”；ESN 未获得接触力、装置参数、障碍物状态或未来脉冲信息；VMC 仍在同一 validation realization 上独立搜索 `k × budget`。CEM development、validation 和 held-out test 完全分开。测试 seed `20261016–20261020` 已消耗，禁止据此继续选择 ESN gain、budget、VMC k 或训练 checkpoint。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_contact_apparatus_esn_cem_fair_20260821/fair_results.json`；本地下载 JSON SHA-256：`a088437a9a6cb800f102e0c52610cb92c899b6841f6ec3aeccc317003d8dfaba`。
