# Office-v7：全部 16 方法 × 同一 24 综合条件

本轮按用户 2026-10-08 的要求重新运行 **384 个物理回合**。这不是将旧 office-v6 的
结果换名，也不是将 office-v7 单条件 pilot 的结果复制 24 次。当前为运行中的实验登记；
最终结果以服务器 `report_final/REPORT.md` 和逐回合收据为准，文件生成前没有最终成功率。

## 场景、模型与统计口径

- 每个方法使用固定的一个模型，分别执行完全相同的 `office_v7_24_000`–`023`；
  模型取旧 uniform24 主表中已锁定的首个 family 模型，学习方法 seed 为 `2026100301`。
  这与较早 v7 单条件 pilot 使用的旧模型集合不同，不能将二者当作同模型配对结果。
- 同一冻结几何/MJB、55 s、正式物理步长 `5e-5 s`，相同初态 seed `2026091751`，
  原 task/strict gate、执行器幅值/变化率限制、actor 输入接口不变；本轮不训练或选择模型。
- 新条件在任何本轮结果产生前生成，抽样 seed `2026100824`，按六个参数做分层覆盖。
  被动障碍仍是柱子/厚桌角；主动短期为 2 s 发射的球；主动长期为先人手、后棍子。
  这是固定布局下的扰动参数泛化测试，不是 24 种不同几何布局，也不是重新开启旧封存条件。
- 球速 `1.305–1.595 m/s`，人手开始 `4–5 s`、行程 `0.18–0.22 m`；棍开始
  `13.5–14.5 s`、行程 `0.2115–0.2585 m`、保持 `4.5–5.5 s`。
  人手按原 2/3/2 s 推进/保持/撤回；棍按原 1.5/可变/2 s。生成的最小指令间隔为
  `1.965655 s`；实际接触及恢复仍从各回合轨迹统计，不能用指令间隔冒充完全恢复。
- 完成一个方法的全部 24 回合后，Task/Strict 才显示 `/24` 和百分比。物理失败、早停均保留
  在分母；基础设施失败显示未完成并保留日志，不能填成零分，也不能删掉后只报成功回合。
- Task 沿用 planned-hand-corner 放置判据：跑完完整任务时长，抬升超过 0.1 m，释放后的
  物块在目标 XY 25 mm/Z 15 mm 区域内受到支撑，线速度小于 15 mm/s、角速度小于
  0.15 rad/s，并在结尾连续稳定至少 0.5 s。Strict 为 Task 加物理有效及外部/未知桌角
  穿透均不超过 0.2 mm。接触覆盖另列，不能把“没有碰到障碍”解释为柔顺优势。
- 表中的 RMSE 为全观测物理时间加权值；峰矩/峰速先每回合取峰值再跨回合取平均，最大
  穿透取跨回合最坏值。短回合数单列，避免将早停造成的低指标当作优势。

|方法 family|固定模型名|
|---|---|
|ESN|readout_refit_esn_2026100301|
|Matched RNN|readout_refit_matched_rnn_2026100301|
|Matched MLP|gated_matched_mlp_2026100301_point|
|Ordinary RNN|readout_refit_ordinary_rnn_2026100301|
|Ordinary MLP|ordinary_mlp_2026100301_point_lr0001|
|Memoryless|gated_memoryless_2026100301|
|Classical VMC|vmc_11|
|Classical admittance|admittance_03|
|Classical impedance|impedance_02|
|RL parameter VMC|office_rl_parameter_vmc_2026100301|
|RL parameter admittance|office_rl_parameter_admittance_2026100301|
|RL parameter impedance|office_rl_parameter_impedance_2026100301|
|RL direct metric|office_rl_direct_metric_2026100301|
|RL direct task|office_rl_direct_office_task_2026100301|
|Enhanced teacher|teacher_09|
|Nominal zero|nominal_zero|

Enhanced teacher 是参考行，其手工结构/信息使用不能与纯本体学习策略混为一种设计。
相同测试条件不意味着历史训练成本、数据和模型设计完全相同；本轮不声称等训练预算。

## RL 修复及验证

较早 v7 pilot 的五个 RL 行在进入物理仿真前因 JAX/Orbax CUDA sharding 恢复失败。
已在新 dispatcher 中恢复归档评测器的原运行环境：`JAX_PLATFORMS=cuda`、正确 CUDA 库路径、
关闭预分配并限制显存比例；没有重写 checkpoint、更新归一化或做梯度训练。
旧 pilot runner 的本地源码也补齐相同设置，服务器历史失败目录保持不变。

本轮锁定的五个 RL checkpoint 都通过载入预检：各自对已有轨迹的 1,375 个动作精确重放，
最大差 `0`，归一化、训练计数和输入未变；预检自身新增物理步数和梯度更新数均为 `0`。
这是新矩阵模型的运行验证，不是宣称旧 pilot 中另一套 checkpoint 已重新完成评测。

启动后前三种参数 RL 及 direct-metric 已完成第 000 条件的正式 55 s 仿真和独立审计；
参数 RL 停在 `carry`，direct-metric 停在 `approach`，均未完成放置。
这些是保留的物理失败，说明“修复可运行”不等于“修复任务表现”。尚不能从单条件推断 `/24` 成功率。

## 执行与证据位置

计算主机：`arm1@192.168.31.70`。沿用该机冻结解释器、MuJoCo 3.11.0 和 CUDA checkpoint
依赖，避免迁移改变运行环境。并发最多四路，每路一线程、MemoryMax=3GiB、MemorySwapMax=0。
稳定作业不重启；每回合完成后从原始物理子步独立重算 RMSE、峰矩和峰速，并核对配置及模型。

主根目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`

- `PROTOCOL.json`、`CONDITIONS.json`、`MODEL_MANIFEST.json`：预注册协议、条件及模型。
- `source/`、`SOURCE_HASHES.json`：真实运行源码及逐文件哈希。源自历史
  `research72_20261003_1149/final_evaluation_v1/queue_0/source` 加本轮 wrapper/dispatcher；
  `source_base_commit=bebb633...` 是本轮仓库起点，不能把混合冻结快照冒充该 commit 的纯净 checkout。
- `preflight/*.json`、`PREFLIGHT_COMPLETE.json`：五类 RL 的载入、不可变动作重放证据。
- `episodes/<family>__<condition>/`：execution、AUDIT、rollout、物理子步、接触通道；
  同层 `.execution.json` 是调度/独立审计收据，`.log` 保留完整成功或失败记录。
- `analysis/`：逐回合独立物理/接触/恢复统计。
- `report_final/REPORT.json`、`REPORT.md`：有限 campaign 结束后独立统计工具生成；
  生成前为未完成产物，不可引用为已取得结果。

协调服务：`sii-office-v7-uniform24-20261008.service`，启动时间 `2026-10-08 05:52:40 UTC`。
这是有限批处理，不是定时任务；不会因同一对话重入重复派发。
独立报告服务 `sii-office-v7-uniform24-report-20261008.service` 已启动，只等待该批次结束，
不占用仿真名额、不重启作业。报告源码在同根 `reporting_source/`，SHA256
`a06bf5ba1ae13f7b244225710e2f7acd3030eae896d8b1c3cdccd452d80a7ba7` 已与本地核对。

|证据|SHA256|
|---|---|
|正式 MJB|d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3|
|PROTOCOL.json|9eae482be714b1d62ae58634d66a21b4ba9fcefe8303540ac07480663e66c3ec|
|CONDITIONS.json|5b10a6328f7c7b1c70b1a6c95b8d64a2740491b7ec0acf06a58d7b86559190ed|
|MODEL_MANIFEST.json|02980c636bb5fddabdf1bc16a669c7e093bc5be0a3bf5e027114b6849bc316d8|
|SOURCE_HASHES.json|008a6d817e5db113906708c91e26214f2ca905fc6031594ae0296fa3e22e3c71|
|PREFLIGHT_COMPLETE.json|87c95a137c03dc708c60c08a10c8d0533adf1c4f9fbf8d84bb0d75445b3c5073|

仓库小型登记证据：`outputs/office_v7_uniform24_20261008/registration/`。
原始大文件仍在服务器，不提交 Git；小型证据已从服务器下载并核对哈希。

## 状态

已完成：24 条件/16 固定模型登记、五类 RL 预检、首批真实 RL 回合、统一报告工具及边界检查。
14:05 CST 快照为 7/384 个审计回合；新增 ESN/matched RNN/matched MLP 在首条件均
Task/Strict 通过。这不是跨条件优势证据，完整统计尚待其他条件完成。
14:18 CST 复查为 16/384 个审计回合，另四路运行，没有基础设施失败；五类 RL 均已
至少完整执行一个真实回合，动作 exact replay、归一化冻结通过，首条件任务均失败。
运行中：384 回合有限评测及逐回合独立审计。
未完成：每方法 24 回合的最终成功率、完整跨方法差异及最终汇总。
没有改变 gate、丢弃物理失败、用历史 v6 结果代替本轮回合，也没有声称 ESN 已领先。

已发布代码/登记提交 `808d9dc24f00e16ae472a1b2c5f9e72a2fc44909` 的完整 Git 源码归档在
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/808d9dc24f00e16ae472a1b2c5f9e72a2fc44909/source.tar`，
SHA256 `133e57594eb5940105002df967c4788d25ea0525d7443f1759897beff48eacc6` 已于传输结束后核验。
后续交付只清理两个脚本文末空行并补充进度，实际运行仍以不可变 run/source 清单为准。

开工读取的远端分支：main `bebb6331707228f7bf84fd4925611243cf2c442e`；baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。baseline 最新为接触条件指标的探索性后处理，
没有改冻结环境/checkpoint。本轮不合并其分支，不读取或修改其他 agent 未提交的工作。
