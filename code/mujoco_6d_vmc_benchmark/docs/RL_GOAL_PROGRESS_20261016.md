# 持续Goal：四类RL训练与收敛修复

用户于2026-10-16 12:52 CST明确开启Goal，要求持续推进并自主修复训练问题。Goal active，
尚未完成；旧15小时run正常按原截止收尾，新授权以独立有限阶段继续，不回写旧协议的截止。
沿用sii-research-sync协作流程，训练与分析在airpig，服务器只归档。

## 旧恢复批次最终事实

`rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety`在12:41:42安全退出，
50,531步/84,189更新、累计37回合；本段新增6875步/6875更新、5个完整55秒回合，
Task/Strict均0/5。return依次−22.1773、−35.2090、−38.6078、−40.0133、−22.1345；
仅2/5 physical_valid，3条安全失败全部保留。最终checkpoint_0050531逐文件hash通过。
status=complete仅表示旧有限段已结束，training_complete=false，不代表训练完成或收敛。

## Stage01：检验长回合信用分配

历史在线2×2 n-step研究在第一组n01尚未完成时停止，n25没有在线结果。当前n1 checkpoint
多数terminal目标已拟合、非终止Q却与历史行为回报差异明显；这构成信用分配候选依据，
不是证明实现错误。采用已有上游SimbaV2的25步critic和已测的跨回合安全replay reducer。

这次只调整n_step=1→25，UTD保持1，reward/gamma/学习率/动作接口/物理均不变。
Direct从旧50,531步checkpoint迁移，保留网络/优化器/RNG/normalizer/原始单步replay；
只在采样时生成25步回报，遇terminal立即截断，无跨回合拼接，不伪造奖励或成功样本。
其余三类使用登记的payload reward从头训练，所有raw reward和失败轨迹保留。
25步未作离策略校正，存在行为策略偏差；本阶段没有匹配的从头1步对照，不能声明因果胜出。

|顺序|方法|起点|本阶段总步上限|新增交互上限|
|---|---|---:|---:|---:|
|1|Direct/task_safety|50,531|61,531|11,000|
|2|Impedance/payload|0|11,000|11,000|
|3|Admittance/payload|0|11,000|11,000|
|4|VMC/payload|0|11,000|11,000|

四类优化器总日程仍为1M交互，表中是有限阶段节点，不缩小持续Goal的完整训练目标。
完整回合边界限制可使实际交互小于上限。队列串行、每回合保存、worker硬限3GiB/swap0/
CPU1/数值线程1，协调器独立256MiB。进场要求可用内存≥3GiB+768MiB、磁盘余量≥50GiB，
同一派发锁及宿主机worker检查防重复。阶段派发保护截止2026-10-17T05:00:57.926303Z，
即10月17日13:00:57 CST；这是agent登记的有限保护，不是“到时算收敛”。

代码以独立source快照运行，允许后续Goal继续修复仓库而不改动活动worker的源码。
阶段没有acceptance入口，子作业错误会向上传播并保存失败，而不是让协调器假报成功。

## 可复核的收敛要求

在本阶段训练开始前登记：至少96个结束回合，最后两个32回合窗口均覆盖全部32个train身份，
两窗口return均值相对变化≤5%、末窗口return变异系数≤25%，且每个窗口Task AND Strict
同时成功率≥90%。所有失败均入分母；这只是训练收敛候选筛选，最终仍需四方法训练完成后的
统一acceptance与独立物理/动作重放/hash/指标审计。当前样本远未满足，不称已收敛。

## 启动前验证与当前入口

9项恢复/阶段约束测试、4项现有多步replay测试通过。真实50,531步checkpoint预检验证：
agent与上游critic确为n_step25；末25条transition的折扣奖励与独立求和一致，next_state均
止于真实terminal；恢复50,531条原始replay后一次优化更新指标有限，原checkpoint hash未变。
预检无新仿真、不保存模型，exit0、峰值1,161,908,224字节、OOM0。

本地阶段根：`outputs/rl_goal_20261016_stage01/`；登记SHA256
`661ffad196a667731bf34c9bb3855eb6ec81070bd5a6393b06a41f5b5443fcf1`。
协调器`sii-rl-goal-stage-3ced1757b345.service`，Direct worker
`sii-rl-goal-2dc62bfe00c9.service`已启动，接续状态见阶段execution与各方法execution。
其余三方法是明确队列任务，不把排队写成已经训练。停止使用本阶段STOP_REQUESTED，等待
在途回合/检查点保存，不停止仍有子模拟器的父容器或广播信号。

开工main `11809cb960cb4acdcb6ebe1a431d622979d2a3ec`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/读取，保留无关未跟踪文档。
13:11:34首个完整55秒回合结束：新增1375步/1375更新，到51,906步/85,564更新。
return−21.667945，physical_valid=true，Task/Strict均false；checkpoint_0051906全部hash
核验通过，agent与replay保存的n_step均25，第二回合已启动。这证明新训练/保存链路闭合，
不是收敛证据，不能将单个不同condition的return与上一段直接做因果比较。

新阶段源码快照/登记/预检/启动及13:07监视收据、旧恢复全部5个完整回合原始轨迹和
最终50,531 checkpoint已归档核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage01-20261016T0507/evidence.tar.gz`。
大小750,006,095字节，SHA256
`a65bf3966e17f1a38beb244cfa7983a40a7e9bb54f7f5b8f851ee3dda38ff13a`，本机/远端一致。
服务器只传输/归档/hash，没有训练或分析计算。新阶段51,906 checkpoint及新回合轨迹仍仅本地，
留待下一次安全边界归档；原始物理runtime/MJB仍依赖登记的既有路径，此包不是完整环境镜像。
