# 多接触 CEM-ESN 独立固定策略复现实验结果（2026-08-21）

## 结论先行

预注册的独立固定策略复现实验支持 CEM-improved multi-contact ESN 在所声明的 `positive_y + finite-mass hand_proxy` MuJoCo 接触分布内优于 validation-selected VMC。复现中没有重新训练 ESN、没有重新选择 budget/stiffness、没有调 CEM gain；只运行此前冻结的 ESN 5% 与 VMC `k=1.0, 2%`。

在 10 个新 seed × 4 fixture = 40 个 paired rollout 上：

| Method | Success | At-grasp error (mean ± SD) | Peak force | Peak torque | Contact bouts | Hard limit |
|---|---:|---:|---:|---:|---:|---:|
| Frozen multi-contact multi-scale CEM ESN, 5% | **39/40** | **15.778 ± 3.226 mm** | 100.376 ± 26.152 N | 33.805 ± 0.570 N·m | 2.475 | **0/40** |
| Frozen VMC k=1.0, 2% | 31/40 | 20.979 ± 6.548 mm | 100.815 ± 26.310 N | **32.856 ± 0.415 N·m** | **2.300** | 1/40 |

matched at-grasp error ESN−VMC=`−5.201 mm`，fixture-level 95% t CI `[-7.973,-2.429] mm`，按 seed 聚合的 95% t CI `[-8.494,-1.908] mm`。成功配对为 ESN-only `9`、VMC-only `1`、both-success `30`、both-fail `0`；在 10 个 discordant pairs 上的 exact two-sided paired binomial test 为 `p=0.0215`。因此，复现实验本身同时支持更高 success 和更低误差。

## 协议一致性与数据独立性

协议在运行前已写入 [ESN_MULTICONTACT_CEM_REPLICATION_PROTOCOL_20260821.md](ESN_MULTICONTACT_CEM_REPLICATION_PROTOCOL_20260821.md)，并在 commit `22e2609` 中推送。以下对象均在复现前冻结：

- CEM ESN checkpoint：multi-contact BC initialization + train-only CEM 的七个 bounded output-row gain；
- ESN budget：5%；
- VMC：`k=1.0`、2% budget，来自前一轮 validation selection；
- physical contact distribution、fixture generator、PaperMPC、FR3 torque limits 和 safety clamp。

replication seeds `20261431–20261440` 完全独立于 CEM train `20261401–04`、validation `20261411–15`、第一轮 held-out `20261416–20`，也未用于此前任何实验的 test。没有增加接触力、装置参数、障碍物状态/几何、方向标签、timing 或 future release 作为 ESN 的部署输入；观测仍是 32-D proprioceptive contract。

## 配对统计与安全维度

| Metric, ESN−VMC | Mean difference | Fixture-level 95% t CI | Seed-level 95% t CI |
|---|---:|---:|---:|
| At-grasp error | **−5.201 mm** | `[-7.973,-2.429] mm` | `[-8.494,-1.908] mm` |
| Peak post-impact error | **−45.371 mm** | `[-49.043,-41.699] mm` | `[-49.711,-41.031] mm` |
| Peak contact force | −0.439 N | `[-0.736,-0.143] N` | `[-0.759,-0.119] N` |
| Peak torque | +0.949 N·m | `[+0.668,+1.229] N·m` | `[+0.689,+1.209] N·m` |
| Contact bouts | +0.175 | `[+0.032,+0.318]` | `[-0.049,+0.399]` |

ESN 在误差、success 与 peak contact force 上占优或相当；但 VMC 的 peak torque 更低，ESN 的 contact bouts 点估计略多。因此不可宣称 ESN 在每个 safety dimension 都更好。更积极的是：本复现中 ESN 无 hard-limit，而 VMC 有 1/40；这项安全差异样本太少，应作为描述性结果而非显著性声明。

held-out fixture 实际物理范围：

| Parameter | Range |
|---|---:|
| Impactor mass | 0.191–0.498 kg |
| Slide damping | 0.601–3.943 N·s/m |
| Driver kp | 2.585–8.980 kN/m |
| Driver force limit | 180.9–299.7 N |
| Contact time constant | 8.45–24.40 ms |
| Stroke | 0.1607–0.1760 m |
| Height | 0.5391–0.5420 m |
| Start time | 0.900–1.027 s |
| Cycle period | 0.660–0.719 s |

## 与第一轮 held-out 的联合证据

第一轮 held-out test（20 fixture）已经给出同方向的点估计：ESN `19/20` vs VMC `17/20`、误差 `16.756` vs `19.979 mm`，但当时 error CI 跨零。复现实验是在此前配置已经冻结后进行的独立检验，结果更强。

若将两个独立测试 cohort 仅作为同一冻结策略的辅助 pooled descriptive summary，共有 60 paired fixture：

| Metric | Frozen CEM ESN | Frozen VMC | Paired ESN−VMC |
|---|---:|---:|---:|
| Success | 58/60 | 48/60 | 11 ESN-only vs 1 VMC-only; exact two-sided `p=0.00635` |
| At-grasp error difference | — | — | `−4.542 mm`, 95% t CI `[-6.821,-2.262] mm` |
| Peak force difference | — | — | `−0.428 N`, 95% t CI `[-0.643,-0.213] N` |
| Peak torque difference | — | — | `+1.046 N·m`, 95% t CI `[+0.804,+1.287] N·m` |
| Contact bouts difference | — | — | `+0.267`, 95% t CI `[+0.117,+0.416]` |

pooled 数字不替代单独的独立 replication，而是说明两个完全独立 test cohort 的方向一致；主证据仍应首先报告复现实验本身。

## 可汇报主张与边界

可以严谨地汇报：

> A multi-contact, multi-time-scale Direct ESN, initialized by behavior cloning and improved only through train-only MuJoCo CEM readout gains, outperformed a separately validation-selected VMC on an independent 40-fixture replication of the positive-y finite-mass hand-proxy condition: 39/40 versus 31/40 success, and a paired at-grasp-error reduction of 5.20 mm (95% CI 2.43–7.97 mm). The deployed policy used only the same 32-D proprioceptive observation and shared torque-safety contract.

必须同时保留以下限制：这是训练已覆盖的 `positive_y + hand_proxy` 接触分布内的 MuJoCo 结果；不能外推为对任意接触几何、未见操作方向、真实 FR3 或所有安全指标的普遍 superiority。第一轮 cross-contact OOD 失败仍然成立；在没有接触方向/几何训练覆盖时，冻结 CEM ESN 不能自动迁移。

replication seeds `20261431–20261440` 已消耗，不得据此修改 CEM gains、ESN checkpoint、budget、VMC k 或物理范围。真机前仍需要 system identification、外部力/力矩校验、碰撞停止逻辑与低速 dry-run。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_multicontact_cem_replication_20260821/replication_results.json`。

SHA-256：`a2cc788f021c295b8e9fcbf96e0affcc11e5147a10cf9d7b1b5526c2b2f7d3d2`。
