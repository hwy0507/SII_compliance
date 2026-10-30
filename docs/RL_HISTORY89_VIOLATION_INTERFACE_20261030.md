# 完整89因果违规位持久化与全量回放初步迁移核验

2026-10-30 UTC，Goal active。承接[匹配违规位拟合](RL_HISTORY89_VIOLATION_BIT_FIT_20261030.md)的实际证据及准备决定，本轮重建完整89因果穿透历史，完成52维critic/replay初始持久化接口与三份完整父迁移核验。没有导入离线拟合权重，没有正式训练90/Direct34；完整回放磁盘/GPU cache、完整冻结轨迹消费者及trainer/eval调度接入仍须继续验证。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。原始历史扩展 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_raw_history_extension_20261030_v1`；新增源码与检查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_violation_interface_20261030_v2`。原冻结88与GPU v7继续，不重启已完成89或离线拟合。

## 原始历史与违规位

事前PLAN `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_raw_history_extension_20261030_v1/PLAN.json`、源/输入hash冻结，900秒预算；实际168.079秒完成。保留原87所有10,824,948行raw因果sidecar，原87回放的50维观测前缀和其余字段与完整89全部精确对齐。原88真实v2 registration（含I/V链接及A恢复重试）和89 registration解析真实train路径，按global step重建各30×1375的完整日志，新增共247500行、每行仅写一次。全11072448行current/next现有history51特征与raw归一化逐位一致；所有新增观测/动作混合映射/reward/done/clock/history也精确一致。

raw sidecar为float64双列（动作前/动作后累计外穿透），另存uint8双列违规位`raw>.0002`。独立复算逐条核验全部新增动作日志及前后顺序，原前缀精确保留，全量bits重新比较；不把终局最大值提前广播到此前动作，不从float32 history>.5反推真实门。现有checkpoint/replay只读，0physics/forward/update。

| 方法 | 全部保留行 | 原始终端数 | 动作前已违规行 | 动作后已违规行 | 首次跨门transition |
|---|---:|---:|---:|---:|---:|
| impedance | 3688948 | 2665 | 90635 | 90707 | 72 |
| admittance | 3691250 | 2664 | 77831 | 77893 | 62 |
| vmc | 3692250 | 2664 | 59503 | 59550 | 47 |

三路`<method>_causal_history.npy`与`<method>_causal_violation_bits.npy`仅在上述共享SSD目录，大小/hash见REVIEW；未把大数组塞入Git。历史partial75与所有短/失败原始数据保持。该核验是保存日志及回放一致性，不是独立重跑全部物理子步。

## 持久化接口与实际检查

新增 `persisted_violation_critic.py` 保留原history marker及已学第50列，新增独立bit marker绑定准确完整89 learner/replay/sidecar/bits/原history父。critic/replay52、actor49不变，clock49/history50/bit51。10个critic首层在索引51插入零列、原动作列右移，旧Adam全部值/step/group精确保留、新列矩0；不加载本轮之前的离线拟合权重。

actor hook在52维入口只取前49维，目标Q投影移除bit后调用原history投影（仍使用原clock）。每个stream复用原consume_interval因果顺序，动作前读取已累计raw，terminal使用最终完成interval；重复/缺失/递减interval拒绝，恢复时所有stream重置。replay同时保留原23/47容量marker及原history marker；拒绝缺marker/错父/hash/维度/非二值或与连续history矛盾的bit。在连续history恰好舍入为.5时允许0或1，以raw严格门为准。

初版v1失败及诊断完整保留：直接插入零列的dense首层在CUDA单行推理改变浮点归约，I首个动作后CHEQ混合权重差约2.82824e−5，下一raw action差约5.50561e−5；批量初始Q对照未捕获此差异，精确native守卫拒绝，0正式update/physics。v2用`PreservedHistoryLinear`保留原51+action点积布局，再加bit列贡献；未放宽任何动作/context/RNG判据。独立真实I首行batch1/64的old/dense/split比较，以及两动作维度×三batch的float64输出/梯度对照均通过；后者最大输出误差4.45e−16、最大梯度误差9.95e−14。其数学仿射模型与原52维相同，但训练后的浮点归约实现不同于此前dense离线诊断，不能声称逐位相同优化轨迹。v1仅随机fixture和部分I检查，完整三路以v2为准。

三份完整89全部learner反向删新增零列后逐字digest等同原父；全部旧回放字段与原history列精确保留，全部新bit逐行与raw一致；下一65536条原生采样索引、原字段、bit、RNG一致。learner写盘重载及replay内存roundtrip通过；三路native多stream动作/context/RNG与原51维完全一致。真实终端+均匀样本的online/target Q初始误差为 `{'impedance': {'ensemble': 0.0, 'ensemble_targets': 0.0}, 'admittance': {'ensemble': 0.0, 'ensemble_targets': 0.0}, 'vmc': {'ensemble': 0.0, 'ensemble_targets': 0.0}}`。

v2两动作维度5/7的随机fixture共12次原生update调用（连同保留的v1共24次辅助fixture调用，真实父仍0更新），更新/序列化恢复重放精确，新增bit列获得非零梯度，foreach target引用与actor49隔离通过。57个实际负例拒绝，完整父checkpoint hash与learner/replay digest保持；真实父0optimizer更新/0physics。这是迁移实现正确性的证据，不是训练健康或reward提升。

## 下一步与仍运行工作

下一步对准确迁移状态验证全量回放磁盘持久化、GPU DeviceReplayCache、可丢弃append，随后原1375动作+terminal的冻结消费者/RNG重放、health与trainer/eval恢复入口；这些完成后才单独决定/登记有限在线90和新的修订内统计窗口。当前`<method>_migrated_learner.pt`是迁移learner快照，不是新的物理训练checkpoint，也不是已经完整保存的52维replay。原88—90 A/V失败窗口不改，未运行全三轮bootstrap。

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1` 保存完成数 `{'impedance': 17, 'admittance': 17, 'vmc': 16}`；evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409与五guard原身份持续。接口观察170.196秒/18样本，检查任务正常完成；原冻结21600秒截止不扩展，最终全90/内存不变/raw审计/82→88配对仍待。

GPU v7 supervisor97370/worker97399–97402继续，科研任务结束也保载，阈值50%、目标70%。本轮148采样min `[68, 74, 67, 75]`%、低于50 `[0, 0, 0, 0]`，末值 `[73, 77, 75, 79]`%；含合成负载，非科研吞吐/每瞬时保证。历史v7预热0和v6 31/33/44低谷保持；非开机自启服务。

## 发布及原范围

开工实际query/fetch/read main5ebf8e08050e8d4a45c269a71b20a10397f31058、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，已ff保留另一主机非RL fixed27完成27/27、Strict24/27及三MLP穿透失败，不用其模型替代指定ESN。本机冻结runtime保持。沿用sii-research-sync，无子agent。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_VIOLATION_INTERFACE_20261030/SMALL_EVIDENCE.tar.gz`，81成员/135236字节，SHA256 `2be862f84884cfe676c2222c0ec968759ddb6867f9527cbe2525d9919a9347b4`；tar逐字/AST通过，index/commit核验及正常push/真实远端确认另见包外收据。HDD仅254字节原位LATEST，大checkpoint/raw/bits/learner快照仍SSD，非HDD/arm1全备份。

Direct33数值接受但冻结Task/Strict0/0，28中断缺最终内存不变证明；指定ESN仍缺失。partial75、74—76不可判、79安全中止、所有失败稳定性窗口、半std拒绝与软件失败保留。完整reward稳定、loss健康、最终冻结/ESN比较仍未证实，Goal active。
