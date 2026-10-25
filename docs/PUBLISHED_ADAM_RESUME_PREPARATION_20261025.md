# Adam计数器候选实际恢复入口验证 — 2026-10-25

`source_train15`已准备但未部署。当前四CHEQ仍在`source_train14`运行原登记10/11，两轮结束后才进行完整科学复核；四SAC09继续。此次准备解决恢复训练的计算开销，不构成critic健康或收敛改善证据。

## 改动

上一轮独立副本已验证：正式入口的CUDA map_location会把noncapturable Adam scalar step也加载到GPU，后续.item标量读取引入同步。此次只在CHEQ adapter的`load_state_dict`中，将actor、critic、alpha三个Adam的scalar step恢复为CPU；SAC分支不进入迁移。参数、Adam moments、计数器数值、网络、Bellman目标、学习率、随机状态及replay均保留。

实际候选由冻结source14复制而来，只有`published_compliance_learner_20261025.py`改动，增加`published_adam_step_device_20261025.py`；没有复制工作区的其他实验代码。对原/候选完整核验779/780份source、各24份parameter、150份上游CHEQ、128份机器人资产的文件hash。parameter/上游/robot manifests相同，dt5e-5、actor period0.04s、55s horizon不变，控制器、公共filter、执行器限制、actor信息和Task/Strict gate未改。

## 实际验证

使用当前all5在线阶段的四份不可变parent checkpoint，按正式入口`map_location=cuda:0`恢复。每方法执行原adapter与候选adapter各两次更新，并在更新之间保存、重新加载到CUDA，再恢复到对应adapter。批次包含120个非终端和8个终端transition。

- 原adapter保留59个CUDA step；候选每次加载后均恢复为59个CPU step。包括候选自身保存的checkpoint，再经CUDA重载后仍能正确迁移。
- 所有恢复/序列化过程数值状态精确相同；两次后续更新的完整learner state、metrics、网络参数梯度及`log_alpha.grad`均精确一致。状态包括网络、target、三个optimizer、alpha和各RNG。
- 四份原checkpoint与replay hash保持；共16次辅助更新、0新physics、不保存/导入辅助权重。验证进程2122767已结束，原运行任务未停止。
- 另读取一个真实SAC Direct完整cycle4 checkpoint，对原/候选实际adapter执行恢复；完整状态和counter device相同，证明该分支未被迁移。本项没有SAC更新或提速结论。

此前四helper单元测试及4096辅助更新的有限性能证据仍保留；本轮新增的是实际adapter恢复与保存入口覆盖，不重复性能试验，也不把共享负载的0.96–1.18倍波动计时写成正式吞吐改进。四GPU持续50%仍未证明。

## 状态和后续边界

候选`CANDIDATE_PROTOCOL.json`仅记录准备状态、当前阶段不变及未来部署前提，没有选择下一在线阶段或自动派发。用户已授权自主决策，无需为这些常规工作重新请求许可；需先完成当前阶段及科学复核，再登记下一阶段runtime、完整父状态和资源。任何新阶段不能导入本次辅助权重。

原10/11 auditor/reviewer继续等待完整归档；不能从部分reward窗口宣布收敛。最终仍需要充分训练与优化健康证据、完整训练集固定策略评估、统一最终SPT及指定ESN公平比较。当前缺少指定ESN checkpoint，未用历史版本替代。

## 位置

计算主机：`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`。集群SSD根目录：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。

- 候选runtime：`runtime/source_train15`，构建状态为prepared_only；并非当前训练runtime。
- 冻结验证工具：`runtime/adam_resume_preparation_v1`。
- 产物：`runs/adam_resume_preparation_v1/RESULT.json`、`CONTRACT_REVIEW.json`、`REGISTRATION.json`与`CANDIDATE_PROTOCOL.json`；小型结果及hash见同名JSON。
- GitHub main/baseline本轮fetch/read仍为a52dfba/f6e8f8c；没有远端新变更。推送状态以实际命令结果为准。
