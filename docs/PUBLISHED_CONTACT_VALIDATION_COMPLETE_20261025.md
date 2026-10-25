# 接触读取候选12项完整验证与组合runtime准备 — 2026-10-25

原`contact_candidate_validation_v2`已自然完成全部12项完整55秒轨迹对照，协调器2530701与最后的VMC长期worker2249466均退出。已核对FINISHED、注册及冻结validator源码hash、12条件集合和各项完整比较收据，并独立重读原始字节一致文件核验hash。不是仅凭PROGRESS或进程退出宣布通过。

## 验证范围与结果

四接口Direct/Impedance/Admittance/VMC × 被动/主动短期/主动长期三个0000代表条件，共12条归档动作轨迹，累计13,200,000物理子步。首次v1验证中已经完成的Direct被动轨迹复用，v2实际新增11条、12,100,000子步；早期比较器误拒robot_parts集合顺序的失败和修正均保留。

每项原validator覆盖：

- 1375个actor周期中的canonical观测、interval奖励遥测及payload potential精确一致，执行固定原始action tape。
- 完整MJB、actor journal、终端记录和audit_substeps原始字节/hash一致；本轮完成复核又核对这些原始文件。
- rollout、filter、torque数组键/形状/dtype/逐字节数值精确一致。
- 完整rollout结果一致，仅规范预登记的源码hash、输出目录前缀以及明确为集合的robot_parts列表顺序。没有忽略任务事件序列或数值差异。
- 每例110万子步完整，原Task/Strict结果原样保留；这些是旧策略action tape，不是当前all5策略的新性能评估。

原RESULTS和PROGRESS保留其写入时状态（最后进度completed_cases可能仍为11）；最终证据是FINISHED中12项完整结果。`COMPLETED_REVIEW.json`记录收据与原始hash核验。未重跑已完成仿真或导入任何辅助权重。

## 后续性能候选

将已验证的三个接触读取源文件纳入仓库，并从source_train15准备独立`source_train16`。改动只把每个接触对象的逐条Python包装读取改为同一MuJoCo字段数组索引，接触遍历顺序、距离、frame、force调用及数值计算保持；同时更新episode动态插入代码的匹配位置。

组合前确认这三个文件在原source07、当前source14和source15中完全相同。组合后780份source hash通过：相对source15只变三个接触文件，内容与完成12项验证的候选逐字节相同；learner/Adam helper/trainer/Bellman文件与已完成实际恢复验证的source15完全一致。parameter、上游CHEQ、机器人资产manifests与当前source14相同。dt5e-5、actor period0.04s、55s horizon不变。

四项接触候选比较器/保护测试通过，三个采用文件语法检查通过。本次组合没有新physics、优化更新或部署；这是独立已验证组件的组合，尚未宣称在线吞吐改善。当前source14的原10/11和四SAC09继续，不打断，不选择下一阶段超参数。组合候选仍须在当前完整阶段科学复核后正式登记才能用于后续训练。

## 正式负载观察

本轮在没有辅助学习的窗口采样60次GPU，实际墙钟77.19秒，包含原固定VMC9策略推理。四卡均值35.13/39.40/30.07/33.97%，最低均0，仍未实现持续50%目标。八learner PID/start ticks前后核验一致；CHEQ新增步1186/1621/1289/1232，SAC573/344/300/529。不可把该观察当source16的性能证据，因source16尚未部署。

原四CHEQ继续第10轮收尾；SAC Direct已完整归档cycle5并进入6，其他SAC继续3。这仅说明真实推进，没有新增收敛结论。固定VMC9的被动条件完整55秒仍在carry失败，其余条件与后处理审计继续；原参数矩阵仍6/9已审计。最终完整训练集、SPT、接触舒适性和指定ESN公平比较未完成。

## 证据位置

主机：`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`；集群SSD根目录：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

- `runs/contact_candidate_validation_v2/results/FINISHED.json`与`COMPLETED_REVIEW.json`：12项最终比较、原始证据核验。
- `runtime/source_train16`：prepared_only组合候选，未部署。
- `runs/combined_performance_preparation_v1/CONTRACT_REVIEW.json`与`CANDIDATE_PROTOCOL.json`：精确组件来源和未来阶段前提。
- `runs/bellman_minimum_online_seed20261025_v1/GPU_60S_02.json`：原始60样本、前后进度与进程身份。
- 同名JSON提交小型结果和hash；大型MJB/轨迹/子步留在原集群目录，不提交Git。

本轮fetch/read main a52dfba、baseline f6e8f8c未变。工作沿用用户自主推进授权；不因候选尚未部署而重新索要许可。physics/MJB、gate、actor输入、公共filter和执行器限制未改变，下一阶段还需完整科学复核与登记。
