# ESN 读出平滑与泛化开发结果（2026-10-07）

## 目的与冻结边界

本轮只改变固定 128 单元 ESN 的线性 readout 拟合，不改变 office-v6 几何、任务/strict gate、48D/action7 本体输入、执行器幅值/变化率限制、公共 filtering 或正式物理步长。训练数据为
`outputs/research72_20261003_1149/demonstrations_refined_v1/training_data.npz`，固定 20/5 identity split；最终 24 条 sealed 条件未读取。

父 checkpoint SHA256：`acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7`。

训练数据 SHA256：`7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0`。

## 读出机制

- action-increment 正则：惩罚相邻读出特征对应的动作变化；
- action magnitude 正则：抑制动作能量，作为峰值力矩的离线代理；
- 可选本体观测噪声一致性：只在训练拟合中使用，部署仍接收原始 48D 本体字段；
- 禁止接触真值、球/物块状态、事件时间、任务阶段、视觉或距离输入。

网格为 `ridge ∈ {0.01, 0.1, 1.0}`、`smooth_weight ∈ {0, 0.01, 0.05, 0.1}`、`action_weight ∈ {0, 0.001, 0.005}`，共 36 个候选；选择只看 5 个 validation identities 的预注册组合目标。

## 离线 identity-holdout 结果

| 模型 | checkpoint SHA256 | 验证 action MSE | 验证 action delta energy | 验证 action energy | 最大单步 action 跳变 |
|---|---|---:|---:|---:|---:|
| 父 ESN | `acd3b27e…2ec7` | 0.000242 | 0.014357 | 0.012396 | 1.566 |
| 平滑网格候选 | `69ecee9d…46e4` | 0.000612 | 0.009489 | 0.009701 | 1.366 |
| 平滑+噪声候选 | `c327ee61…ab6e` | 0.000548 | 0.010215 | 0.010058 | 1.412 |

相对父 ESN，平滑网格候选的验证 action delta energy 降低约 33.9%，action energy 降低约 21.7%，最大单步跳变降低约 12.7%；代价是 action MSE 增加约 153%。加入小幅本体噪声后 MSE 和平滑度折中，但仍不如纯平滑网格候选的预注册目标分数。完整逐身份结果和数据 hash 见：

本地：`outputs/esn_torque_generalization_20261007_grid/REPLAY_COMPARISON.json`；服务器归档：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/REPLAY_COMPARISON.json`

训练网格收据：

`outputs/esn_torque_generalization_20261007_grid/TRAINING_COMPLETE.json`

提交源码快照已核验至：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/fa64f33b59794a0f88d53f667b8517e87a6737eb/source.tar`

源码 tar SHA256：`871cd8fb426a6171217f84bc0cd5810fd5b295a66fdca172d49aeecc62b544be`。

## 物理闭环状态

### v2 anchored `.03` development 闭环（2026-10-07）

同一 frozen `development_000`、正式 `dt=5e-5` 的 v2 anchored 候选已经完成真实闭环：
`task_success=true`、`strict_success=true`、RMSE `33.303 mm`、峰值力矩 `51.595 Nm`、峰值速度
`0.3655 m/s`、最大穿透 `0.1626 mm`（边缘 `0.0867 mm`）。动作、储备池和公共 filter replay
的最大绝对差均为 `0`。这证明修正后的 v2 机制可以保持单条件任务通过，但真实峰值力矩高于父 ESN
开发锚点的 `49.981 Nm`，因此没有把它升级为新冻结模型。完整回合证据见本地
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s003_dev000.json`，服务器原始审计位于
`arm1:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/v2_s003_dev000/AUDIT.json`。

随后已按相同 worker、相同资源限制启动更弱平滑候选 `ridge=0.1, smooth_weight=0.01,
action_weight=0.0001, parent_trust=100`（服务器 checkpoint SHA256
`da281fbe03e122f0d36bb6e5e65183f9fd480b2f5acfd6a939404888075f5d59`）。该回合正在运行，结果产生前不作
任务或降矩结论。

该 `.01` 候选随后在同一 `development_000` 完成：task/strict 均通过，RMSE `30.823 mm`、峰值力矩
`49.663 Nm`、峰值速度 `0.3659 m/s`、最大穿透 `0.1636 mm`（边缘 `0.0855 mm`）。相对父 ESN
开发锚点 `49.981 Nm`，峰值力矩下降约 `0.318 Nm`（`0.64%`）；相对 `.03` 候选，RMSE 和峰值力矩
同时改善。该结果仍只有一个 development identity，不能称为跨条件泛化；原始审计和 provenance 保存在
服务器 `v2_s004_dev000_r3/AUDIT.json`，本地摘要为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s004_dev000.json`。为避免把启动故障
混入物理结果，`v2_s004_dev000`、`v2_s004_dev000_r1`、`v2_s004_dev000_r2` 中的工作目录、线程环境和
Menagerie 路径失败均保留，并单独标记为 infrastructure failures。

同一 checkpoint 在登记的 `development_001` 也完成 task/strict：RMSE `28.338 mm`、峰值力矩
`49.909 Nm`、峰值速度 `0.3657 m/s`、最大穿透 `0.1484 mm`（边缘 `0.0881 mm`），动作和储备池
replay 仍为零差。两个 development identity 的峰值力矩均低于父 ESN 锚点，但改善幅度分别为
`0.64%` 和 `0.14%`，因此当前证据支持“轻度稳定降矩候选”，还不足以声称显著或全面优势。
本回合摘要为 `outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s004_dev001.json`，服务器
原始审计位于 `.../v2_s004_dev001/AUDIT.json`。

同一候选在 `development_002` 失败：task/strict 均为 false，RMSE `30.678 mm`、峰值力矩
`51.860 Nm`、峰值速度 `0.3625 m/s`、最大穿透 `0.1738 mm`，但完整 55 s horizon 执行且无 abort。
该失败回合保留在服务器 `v2_s004_dev002/AUDIT.json`，本地摘要为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s004_dev002.json`。因此目前 `.01` 只在
`2/3` development identities 通过，降矩与泛化不能升级为总体结论；下一步先对同一 `development_002`
跑父 ESN 配对，区分 readout 修改造成的退化与条件本身难度。

配对父 ESN 在 `development_002` 于 `24.32 s` 因 `global_penetration_exceeded_2mm` 中止，最大穿透
`2.602 mm`，RMSE `63.803 mm`，峰值力矩 `51.885 Nm`；对应 `.01` 候选虽然 task/strict 仍失败，
但完成 55 s 且最大穿透仅 `0.174 mm`。这表明该 readout 在这个困难条件上改善了穿透/完整 horizon，
但没有把最终放置 gate 做成成功，不能用“柔顺”替代 task/strict 结论。父配对摘要为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_parent_dev002.json`。

在 `development_003`，`.01` 候选完整执行 55 s、最大穿透 `0.1395 mm`，但 task/strict 均失败；
RMSE `35.209 mm`、峰值力矩 `38.311 Nm`、峰值速度 `0.3495 m/s`。这进一步说明降矩和低穿透
可以与放置成功脱钩，不能挑选该回合来宣称柔顺性优势。四个已测 development identity 中，`.01`
候选 task/strict 为 `2/4`，而两个失败回合仍分别显示“完整 horizon 低穿透”和“低峰矩但放置失败”
的不同失效模式；摘要见 `outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s004_dev003.json`。

`development_004` 恢复为 task/strict 通过：RMSE `31.076 mm`、峰值力矩 `49.682 Nm`、峰值速度
`0.3643 m/s`、最大穿透 `0.1521 mm`。截至目前 `.01` 在五个已测 development identities 中
`3/5` task、`3/5` strict 通过；三个通过回合的峰值力矩均为 `49.663–49.909 Nm`，低于父 ESN
开发锚点 `49.981 Nm`，但两个失败条件说明跨条件泛化尚未成立。回合摘要见
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s004_dev004.json`。

继续完成剩余登记条件后，`development_005` 为 task 通过但 strict 失败（穿透 `0.4859 mm`），
RMSE `28.361 mm`、峰值力矩 `52.153 Nm`；`development_006` task/strict 均失败但完整执行，
RMSE `29.789 mm`、峰值力矩 `41.185 Nm`、穿透 `0.1598 mm`；`development_007` task/strict 通过，
RMSE `36.499 mm`、峰值力矩 `48.836 Nm`、穿透 `0.1397 mm`。因此八个已测 development identities
的 `.01` 候选为 task `5/8`、strict `4/8`；严格通过回合的峰值力矩范围为 `48.836–49.909 Nm`，
而失败回合同时展示了穿透失败或放置失败，不能按低峰矩挑选。三个新增摘要为
`closed_loop_v2_s004_dev005.json`、`closed_loop_v2_s004_dev006.json`、
`closed_loop_v2_s004_dev007.json`；其中 `dev005` 的首次 worker 目录为
`v2_s004_dev005_r1`，其启动目录错误尝试单独保留。

本轮没有把新 checkpoint 放入正式 `/24` 矩阵，也没有声称峰值力矩下降或泛化成功。默认解释器曾因缺少 Pillow/SciPy 失败；随后找到兼容解释器并在 arm1 恢复了显式 cgroup worker。此前本机受限容器无法连接 user bus，故物理闭环统一转到 arm1；当前新增回合仍属于 development，不解封 sealed 条件。因此正式 `/24` 物理矩阵没有改变。

- 新增物理回合：v2 `.03` 在 development_000 通过，v2 `.01` 在 development_000/001/004 通过、002/003 失败，父 ESN 在 development_002 因穿透中止；所有回合均为正式 `dt=5e-5`、1线程、`MemoryMax=3GiB`。
- sealed 条件：未读取，正式 `/24` 主表不变。
- 基础设施失败：早期回合的工作目录、线程环境、Git provenance 和 Menagerie 路径问题均保留在服务器独立目录，未将其计入物理 task/strict 分母。

独立审计已完成：arm1 上的只读 `paper_metrics_20261002.py` 从保存的
`rollout_metrics/substep_metrics.npz` 与 `research_substeps.npz` 重算 RMSE、峰值力矩、峰值速度、穿透、
完整 horizon 和接触/恢复诊断；九个回合与原始 `AUDIT.json` 的核心数值一致（浮点舍入范围内），动作、
储备池和公共 filter replay 均为零差。汇总见
`outputs/esn_torque_v2_corrected_20261007/INDEPENDENT_AUDIT_SUMMARY.json`，服务器每个回合的
`INDEPENDENT_PAPER_METRICS.json` 也保留在 campaign 根目录。

本轮 Git commit `95f437f507911ed035a9503ba183c41589415951` 的源码快照已归档到
`arm1:/home/arm1/sii_shared/SII_compliance/source/95f437f507911ed035a9503ba183c41589415951/source.tar.gz`，SHA256
为 `cf6fd24b89051de457ebe0035e2d6ad40287e5b02cf9b062d760bdbdd4bea388`。

下一步应在依赖完整且资源受限的既有 worker 上，用未参与选择的 8 个 development identities 评估父 ESN、平滑候选和噪声候选；只有闭环 task/strict 与物理峰值结果完成后，才决定是否进入新的冻结模型锁。

## 2026-10-07：v2 anchored `.003` 八条件闭环与独立审计

预注册候选 `ridge=0.1, smooth_weight=0.003, action_weight=0.0001, parent_trust=100` 使用 checkpoint
`5b043942da39ff6ee280c56a95b8198a30609ba9fcfde16580fe7fe6e6166dad` 完成八个登记 development 条件的正式
`dt=5e-5` 闭环。`development_001` 首次启动因预创建输出目录产生 `FileExistsError`，原失败目录和日志保留；
`v2_s005_dev001_r1` 是同条件的唯一物理重跑。

| 条件 | Task | Strict | RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm |
|---|---:|---:|---:|---:|---:|---:|
| development_000 | 通过 | 失败 | 32.215 | 49.853 | 0.3661 | 0.581 |
| development_001 | 通过 | 通过 | 29.634 | 49.907 | 0.3657 | 0.184 |
| development_002 | 通过 | 通过 | 30.554 | 50.485 | 0.3627 | 0.174 |
| development_003 | 失败 | 失败 | 37.075 | 48.590 | 0.3494 | 0.140 |
| development_004 | 失败 | 失败 | 34.231 | 50.684 | 0.3646 | 0.153 |
| development_005 | 失败 | 失败 | 29.099 | 40.169 | 0.3675 | 0.150 |
| development_006 | 失败 | 失败 | 31.413 | 51.612 | 0.3585 | 0.160 |
| development_007 | 通过 | 通过 | 34.438 | 50.430 | 0.3488 | 0.140 |

该候选的 task/strict 为 `4/8` 和 `3/8`。四个严格通过回合的峰矩为 `49.907–50.485 Nm`；失败回合中有低至
`40.169 Nm` 的放置失败，不能挑选低峰矩回合宣称柔顺优势。所有回合完整执行且动作、储备池、公共 filter replay
最大绝对差均为 `0`。arm1 上的 `paper_metrics_20261002.py` 对八个保存的 substep/research 轨迹独立重算，
核心指标与 worker 审计在浮点舍入范围内一致。小型可审计账本见
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s005_summary.json`；原始审计和独立 JSON 位于
`arm1:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/v2_s005_dev*/`。

相对 `.01` 候选的八条件结果 `5/8` task、`4/8` strict，本候选没有提升跨条件成功率，因此不升级为正式模型。
它在部分条件保持低峰矩/低穿透，但失败模式仍包括放置错误；sealed 条件、环境、gate、actor 输入和正式 `/24`
矩阵均未改变。

## 2026-10-08：本体噪声一致性候选负结果

预注册 noise consistency checkpoint `c327ee61c583beb5a392b3752496f6e8eabc136e181551408d4471ded7acab6e`
在同一八个 development 条件上完成正式 `dt=5e-5` 闭环。八回合均完整执行，动作/储备池/公共 filter replay
均为零差，但 task/strict 为 `0/8`、`0/8`。RMSE 范围 `27.721–31.180 mm`，峰矩范围 `39.309–48.710 Nm`，
峰速 `0.354–0.385 m/s`，最大穿透 `0.138–0.178 mm`。低峰矩和低穿透没有转化为放置成功，因此该候选不升级。
独立 `paper_metrics_20261002.py` 审计已完成；证据账本为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_noise_summary.json`，原始服务器回合位于
`arm1:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/noise_dev*/`。
