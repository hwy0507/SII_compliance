# 四路跨周期回报迁移诊断与GPU资源调整（2026-10-26）

用户再次要求提高GPU利用率以避免集群自动关机。开工四正式learner仍运行，瞬时GPU为5/8/7/6%，不能沿用历史辅助任务的高利用率作为当前数值。

保留 source_train17_clock 原四正式任务、原登记与物理。新增独立有限诊断：clock_temporal_return_transfer_v1，每卡一任务（PID375116/375119/375120/375122）。每方法parent/fresh两个初始化、每臂20000次更新、batch8192，四方法共160000次辅助critic更新；没有新物理回合，没有actor更新，不保存或推广辅助权重，不自动延期。

## 科学问题与限制

用cycle0的全部30条件拟合记录的无熵折扣行为回报，评估cycle1同30条件的实际记录回报。parent初始化严格来自cycle0，而不是读到后续数据的cycle1网络；cycle1 checkpoint仅提供已核验的累积replay。fresh初始化用登记seed。两臂用相同采样种子，配对初始化顺序交错。

此前clock_cycle00_return_capacity_v1在同一周期按条件留出；本次关注跨周期行为变化下回报预测能否迁移。回放prefix精确比对，按cycle/condition分60个完整或提前终止回合；保留Impedance cycle1提前结束的回合及真实终端奖励。标签为实际行为序列的无熵折扣和，既不是SAC软Q目标，也不是固定策略真实价值或未见条件泛化。batch8192与此前2048不同，不将两次loss曲线作同预算算法优劣比较。

每臂都只拟合cycle0；cycle1仅记录指标，不用于梯度、早停或checkpoint选择。有限预算用来检验跨周期表示/优化迁移，不能说明正式策略收敛、任务成功或替代最终ESN比较。

## 资源执行

首次按原辅助方案固定CPU52/53/54、nice10，D/I被已有nice0物理评估抢占。尝试将辅助nice调回0遭操作系统PermissionError，未发生优先级修改，失败写入RESOURCE_BALANCE.json。随后四任务及已有CUDA host线程统一共享CPU52–54，仍nice10、数值线程1。原A/V固定评估协调器、evaluator和物理子进程降为nice19继续运行；没有重启、没有增加评估条件。其执行速度可能下降。正式训练CPU0–51、四learner及其sampler均未改。

启动和调整后一分钟GPU窗口分别保存GPU_WINDOW_STARTUP.json及GPU_WINDOW_BALANCED.json，属于正式训练加辅助工作的混合利用率；不保证后续每秒均超过阈值，也不将其说成正式RL吞吐提升。该诊断结束后不得为了维持占用原样重复运行。

## 代码与产物

- 代码：code/mujoco_6d_vmc_benchmark/tools/probe_temporal_return_transfer_20261026.py。
- 冻结副本：/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/clock_temporal_return_transfer_v1/。
- 登记/日志/收据/结果：/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/clock_temporal_return_transfer_v1/。
- 原正式run：/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/cheq_clock_online_seed20261025_v1/。

GitHub已fetch/read main ce467b1773adeddfdfb82b8ccc424b97af23240b、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。新main仅新增另一主机25/55示范指标审计，不是当前四路RL或指定ESN结果；已安全合并，保留双方日志。前轮Impedance固定评估及完整恢复报告提交a91cf98；合并提交de7ac97。

持续Goal仍未完成：正式四路收敛、完整固定策略评估、指定ESN配对和最终完整集合SPT仍待完成。

## 已完成核验

四方法总328939条回放、240回合（含Impedance提前结束）全部按独立scipy.signal.lfilter计算无熵折扣标签，与训练脚本逐值hash完全一致；父cycle0及数据cycle1 checkpoint hash核验通过。启动核验时四路均已发生实际更新，正式任务未重启。语法编译与git diff检查通过；首seed诊断现已完整结束，8臂共16万更新、648点曲线完整且数值有限，actor未变/权重未推广收据与父文件hash通过；图已目视核对。

调整后一分钟60样本混合GPU均值61.733/53.283/48.350/46.683%，最低30/18/26/18%；均高于15%是该已测窗口事实，不能保证未来不中断。后两卡均值未达50%。启动窗口均值14.000/10.183/37.467/35.400%明确保留，不隐去启动不足。

## 首seed完成与两个独立seed复核

parent/fresh最终迁移MAE分别为Direct0.562/0.748、Impedance6.572/7.931、Admittance7.592/7.496、VMC5.872/5.579。周期内拟合误差下降，而后续周期误差明显更高；不能单凭此归因于critic发散，因为策略/轨迹分布也改变。完整数值见JSON。

原四任务均已结束，勿重启。其结束后的GPU_WINDOW_STEADY窗口真实包含利用率回落：均值54.583/58.917/32.867/29.033%，各卡均出现0%瞬时样本，不能只引用先前高利用率。

为检验上述迁移差距对初始化和采样seed的敏感性，另登记clock_temporal_return_replications_v1：seed20261027/20261028，八进程602548/602550/602552/602553/602556/602558/602560/602562，每卡2路，每臂20000更新，共新增32万辅助critic更新；含原seed三组总48万，不自动扩展。父数据、两周期目标与独立验证的首seed完全一致；八任务启动核验通过、均实际更新。仍只用52–54/nice10，正式0–51不改。该组正在运行，尚无完整跨seed结论。

八路复核运行的一分钟窗口均值49.867/61.133/56.900/56.933%，整体56.208%，各卡最低31/40/41/36%；GPU0均值略低于50%，不能说四卡均超过50%。该窗口四卡均超过15%，没有修改集群关机策略，也无法保证未来任务结束后仍维持同样利用率。
