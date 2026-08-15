# WBC-aware ESN 训练/验证 fixture：物理筛选结果

## 结论

已创建一个与冻结 V2/V3/V4 不混用的、WBC-aware 的 ESN train/validation fixture pool。它含 **22 个有效的物理碰撞 fixture**：train 11 个、validation 11 个。两者都使用 `fixed_panda_wbc` reference，WBC 本身不读取 rod/contact/force/future release 信息。

这不是 ESN 训练结果，更不是对 VMC 的性能主张；它是允许后续拟合 ESN readout 和选择 ESN 超参数的唯一数据池。冻结的 WBC-aware V4 ladder 继续作为未来的一次性 test，不可在本 pool 选择阶段读取。

## 运行版本与入口

| 项目 | 取值 |
|---|---|
| simulator runtime | MuJoCo 3.11.0 / NumPy 2.5.2（服务器） |
| reference source | `fixed_panda_wbc` |
| screening selector | frozen 6D `vmc_gated`，仅用于 fixture validity |
| collision gate | peak contact force ≥ 15 N；contact impulse ≥ 0.45 N·s |
| task/safety gate | finite、rod–hand contact、stable 5 mm/80 ms rejoin、lift、hold、no hard torque limit、matched no-rod task valid |
| selected artifact | [esn_wbc_train_validation_fixture_pool.json](esn_wbc_train_validation_fixture_pool.json) |

## 结果

| split | 有效 fixture | x 轴 | y 轴 | z 轴 | 方向构成 |
|---|---:|---:|---:|---:|---|
| train | 11 | 5 | 4 | 2 | `-x` 2，`+x` 3，`-y` 2，`+y` 2，`-z` 2 |
| validation | 11 | 5 | 4 | 2 | `-x` 2，`+x` 3，`-y` 2，`+y` 2，`-z` 2 |

首轮 20 个候选中，18 个通过；`+x` 的两个晚时机（train 1.180 s、validation 1.205 s）分别出现了 `missing_rod_hand_contact / below_effective_force / below_effective_impulse / no_stable_rejoin`，故不进入任何 split。为保证 `+x` 不只含单个时机，追加了 4 个**新时机**的 `+x` pre-screen，均通过，得到最终 22 个 fixture。

筛选证据完整保留：

- [首轮 manifest](esn_wbc_train_validation_manifest.json)：20 个 candidates，含两条未通过记录；
- [`+x` 补筛 manifest](esn_wbc_positive_x_early_probe_manifest.json)：4 个 candidates；
- [合并 pool](esn_wbc_train_validation_fixture_pool.json)：每条记录保留 `source_manifest` 和 `source_fixture_id`，避免不同筛选轮次的同名临时 ID 混淆。

## 已验证的 ESN 部署边界

服务器还完成了 `scripts/esn_compliance.py` 的无 MuJoCo contract smoke check：20-D student input、ESN reset 的确定性、ridge readout、7-D action projection 与正值/slew-limited stiffness/drive bounds 均通过。

student 输入严格为：

\[
[q\;(7), \dot q\;(7), \dot x^{WBC}\;(6)].
\]

rod contact、rod force、rod displacement、obstacle pose/geometry、collision normal、future release 和 fixture ID 只能被 teacher/offline evaluator 使用，不能进入 deployed ESN。

## 局限与下一步

- 只覆盖五个轴对齐物理 rod approach；`+z` 尚未通过 rejoin validity，不能称 six-side 或 arbitrary 3-D coverage。
- fixture selector 是 VMC-gated，不是 teacher policy；筛选通过也不预设 ESN 应当模仿 VMC-gated。
- 下一步应先定义 teacher label 的目标（例如局部 Pareto-optimal 7-D bounded action），用 train 拟合 readout、用 validation 选择 reservoir/ridge/safety envelope；选择冻结后才能运行 V4 WBC-aware final test。
