# 假期研究进度：ESN 与 baseline 公平比较

核验时间：**2026-10-04 00:35 UTC / 北京时间10月4日08:35**。这是有时间戳的快照，不是实时监控。
历史与证据路径保留在 [UPDATE_LOG.md](UPDATE_LOG.md) 和 [联合研究进度](code/mujoco_6d_vmc_benchmark/docs/ESN_VMC_JOINT_PROGRESS_20260927.md)。

## 当前结论

**ESN已在多数初始开发回合完成放置，但还没有稳健通过安全门槛，也没有证明柔顺性全面优于baseline。**
尚未达到完整RAL投稿证据要求。新的最终24条件仍封存，未用于调模型。

初始33模型×8共同开发条件的264回合及独立阶段审计全部完成，261完整、3短失败。
以下各版本均为3个训练seed×8条件，是开发候选比较，不是最终选定模型的留出成功率：

| 初始方法/版本 | 放置成功 | strict成功 |
|---|---:|---:|
| 纯ESN，点损失 | 19/24 | 9/24 |
| 纯ESN，时序积分损失 | 11/24 | 4/24 |
| 无记忆，重新拟合 | 7/24 | 6/24 |
| 普通MLP，点损失 | 7/24 | 7/24 |
| 普通RNN，点损失 | 14/24 | 0/24 |

点版ESN三个seed的strict分别3/8、4/8、2/8；积分损失尚未改善闭环。
六个初始同特征RNN都选择了第0步ESN初始化，另有小学习率增强网络等待闭环，不能据初始组宣称充分优化RNN不如ESN。
点版ESN推杆暴露24/24，其P95力均值21.432N、力模积分36.733Ns；无记忆完整暴露23/23对应24.303N、33.242Ns。
暴露集合不同，峰力与累计负载存在权衡，不能当作全面柔顺领先。

[完整初始结果、全部seed/版本及局限](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_INITIAL_DEVELOPMENT_20261003.md)。
[上轮26方法单条件矩阵](code/mujoco_6d_vmc_benchmark/docs/evidence/all_methods_formal_20261003/report/MATRIX.md)另行保留，不与本轮分母混合。

## 已完成、运行中与未完成

| 工作 | 当前状态 |
|---|---|
| 条件/协议 | 32训练＋8离线验证＋8闭环开发；另24最终身份封存 |
| 初始teacher | 48回合及审计完成：44任务/28strict；训练32为29/18，验证8为7/6，开发8为8/4 |
| 真实示范 | 18合格训练＋6整身份验证，共33,000帧；所有拒绝/失败尝试仍计成本 |
| 初始学习组 | 33拟合及264闭环/独立审计完成 |
| teacher/经典参数 | 96筛选＋64确认及审计完成；teacher09为8/8task、7/8strict，其余选定adm03/imp02/vmc11 |
| 更强MLP/RNN | 48学习率复核拟合完成；服务先跑8条名义WBC，再跑21个模型的168开发回合 |
| 新ESN记忆机制及同机制对照 | 21拟合完成；168开发作业已接续、等共享租约。离线误差变差，不能先称优化成功 |
| 选定teacher再采集 | teacher09同32训练/8验证身份40回合采集中 |
| RL office适配 | 两队列实际训练、第三等租约；5方法×3seed，各最多80k累计交互，先5500步轮转再续训 |
| RL接口/恢复工程 | 55s物理接口及checkpoint/优化器/回放/RNG恢复工程通过；两真实训练队列峰约1.94GiB无OOM，尚在warm-up，梯度训练峰待检查 |
| 最终冻结/评估 | 未开始；计划38模型×24条件=912回合，包含全部RL、经典、神经和名义WBC |
| 最终审计/媒体/图表 | 工程入口准备完成；真实最终证据尚未产生 |

累计102个拟合模型均已完成本地训练、归档及字段/重放检查，不是102个最终模型。
纯ESN没有运行时teacher混合。新的固定本体×记忆读出只完成工程准备，**修订02未登记、未拟合**。
修订01下ESN每seed48候选已用满；追加工作须先登记共同预算并核定剩余时间。
不同家族的ridge次数、梯度更新、示范采集与RL交互分别报告，不称“等计算预算”。

## 下一步和判定依据

1. 64确认/独立审计已完成；保留teacher09的柱子/link6穿透.314mm失败，跟进新采集和后续作业、总并发≤4。
2. 核验真实RL首段内存、交互和续训边界；完成已登记增强组和teacher再采集。
3. 按实际容量决定是否登记新读出拟合，优先保留完整最终比较，不按失败删候选或方法。
4. 全方法冻结后才开封24条件，完成独立子步/动作审计、成对区间及固定首条件的全方法三机位媒体。

[容量核算](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CAPACITY_FORECAST_20261003.md)估计最终912回合纯物理约22–24小时，另需审计/报告。
最终同时报告任务、strict、失败阶段、接触暴露、P95/力模积分、恢复/删失和运动指标，不以加权总分挑胜者。
[分析方案](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_ANALYSIS_PLAN_20261003.md)、
[独立RL动作回放](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_ACTOR_REPLAY_20261004.md)和
[图表入口](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FIGURE_EXPORT_20261003.md)区分工程检查与实际结果。

## 时间和研究边界

本轮保守72小时窗口：**2026-10-03 11:30至10-06 11:30 UTC**（北京时间10月3日19:30至10月6日19:30）。
第48小时停止新开发，并提前预留最终评估/审计。无定时任务，不重启稳定作业，不为占满机器空转。
固定office-v6几何、目标、规划/WBC、输入、执行器和原task/strict门槛；dt=50μs、55s全程。
球2s，人手完全收回至少1s后才推杆；仅已登记小范围扰动，不称跨环境或真机泛化。
actor禁止接触真值、障碍状态、事件时间、任务阶段、视觉和距离；RL奖励诊断字段不拼入actor。
本地拟合/渲染优先，单模拟器、1–2线程、3GiB；Spark仿真≤4，保持已冻结原生物理运行库。

RMSE是到各回合当前阶段goal的子步误差，不是共同时间参考轨迹；停滞带来的低误差不算优势。
170条公开轨迹的首球撞峰值均先于首次可用碰后actor计算，不能归因于25Hz策略即时反馈，也不是硬件安全证明。
18条合格训练示范仅2条碰柱子，覆盖不足仍是限制。固定储备池/线性读出已有机器人先例；
[文献与方法定位](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_METHOD_POSITIONING_20261003.md)不构成首次性或稳定性证明。

[teacher/经典完整确认](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CONTROLLER_CONFIRMATION_20261004.md)：teacher从相同开发8/4改善至8/7，尚非ESN结果。
[短步长诊断](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_NUMERICAL_DIAGNOSTIC_20261003.md)：50→25μs球峰力差10.4%，积分差.5%，峰值未证明收敛。
最终入口的已知teacher 55s重放逐值一致；是工程验证，真实24保留条件仍封存。

## 服务器与Git复现入口

主机 `arm1@192.168.31.70`，本轮根 `/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
完整提交源码位于 `/home/arm1/sii_shared/SII_compliance/source/<完整SHA>/`；真正执行版本以各实验execution/source hash为准。

| 内容 | 本轮根下位置 |
|---|---|
| 初始teacher/示范 | `teacher_bank/`、`prepare_learning_v2/demonstrations/` |
| 初始开发/报告 | `learning_development_v1/`、`public_initial_report_v2/REPORT.json` |
| 参数筛选/确认 | `controller_screen_v1/`、`controller_confirmation_v1/`、`followup_v1/` |
| 初始/学习率/记忆组拟合 | `local_learning_archive_v1/`、`local_neural_refinement_archive_v1/`、`local_context_gate_archive_v1/` |
| 增强组/teacher新采集 | `additional_development_v1/`、`context_gate_development_v1/`、`teacher_refinement_v1/` |
| 活跃RL campaign | `rl_office_adaptation_v2/`；v1为零派发后保留的历史等待记录 |
| 短数值诊断/已知轨迹最终入口演练 | `public_numerical_probe_v1/`、`final_rehearsal_v1/`；不是实际最终测试 |

最近核验已推送main `92d1ea1290dc4b146520224fd86cce90777a9ffb`，完整3226文件已共享核验；
baseline为 `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`，未整分支合并。
大型原始产物留服务器，Git保存源码、协议、小型证据与hash；逐轮命令/运行库/归档收据见更新日志。
