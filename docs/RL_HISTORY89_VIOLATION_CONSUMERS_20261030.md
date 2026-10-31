# 完整89违规位52维全量保存、GPU缓存与冻结消费者核验

2026-10-30 UTC，Goal active。本轮承接[持久化初始接口](RL_HISTORY89_VIOLATION_INTERFACE_20261030.md)，完成三份完整89的全量52维learner/replay磁盘快照、实际GPU cache和完整记录轨迹消费者验证。0正式optimizer更新、0新物理步；无在线90/Direct34派发，不能视为reward改善或收敛。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮源码、登记和检查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_violation_consumers_20261030_v1`；完整迁移快照 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_violation_interface_snapshots_20261030_v1`。每个snapshot标记 `interface_only_no_online_approval`，不是cycle90科学checkpoint。

## 全量保存与真实缓存

CACHE_PLAN在运行前绑定源码、恢复依赖、实际完整89 checkpoint、原始历史/bit sidecar、v2迁移learner及审查hash，CPU11/cuda:2/1800秒上限。实际289.743秒完成；独立删除索引51恢复10个critic和所有Adam矩后，全部原learner字段/RNG逐digest精确；删除replay新增bit及新marker后，原51维所有字段和原history/23/47标记精确。全部11072448旧行保留。

三份full snapshot实际写盘、重新加载、完整digest核验；真实4m×52 GPU DeviceReplayCache下一65536条采样及RNG与CPU一致。每方法仅在可丢弃副本追加1条合成transition，精确核验原Bernoulli mask draw、GPU行刷新、全部旧prefix，随后恢复原状态；未向科学回放添加合成数据。另有mask拒绝与fallback两调用fixture。对所有终端和4096均匀行的raw bit作独立标量检查；原checkpoint hash保持。

| 方法 | 保留行 | 完整快照字节 | SHA256 |
|---|---:|---:|---|
| impedance | 3688948 | 2464107595 | `779fc51ae2f749d2f62b33e1b20cf6c862b644cded6983cf547931abd5e09783` |
| admittance | 3691250 | 2525725047 | `06476a18b948ca81fdefe121cc202524142c19aad552ea0a5b6e230ef51f68a0` |
| vmc | 3692250 | 2481206403 | `249931303247ed6d75dd84be3f5ba61d440444b3dbd9445472ccca30dcd6eb84` |

## 1375动作与terminal消费者

新增 `violation_consumers.py` 显式要求原history与新bit双marker，恢复构造为history51上再包violation52。观测事件先消费刚完成interval一次，再动作；terminal仅消费最后interval。actor49、clock49、history50、bit51及原projection保持。候选使用v2 `PreservedHistoryLinear`，保留原51+action点积后加bit项；初版dense单行CUDA归约失败不删除，未放宽精度。

CONSUMER_PLAN在运行前绑定全部快照与三条完整89 `active_short_train_0600` journal/TERMINAL哈希，seed2026102638、CPU12/cuda:1/1800秒上限。三例均实际跨raw穿透.0002门。原history51和新52都消费全部1375 interval并使用相同外部动作RNG；前51观测、raw/mixed动作、CHEQ context、clock、terminal观测和外部RNG序列逐位完全一致。完整learner/host及GPU RNG均保持；新full replay和原89 checkpoint hash保持。原始记录的输入被重放给当前完整89模型，这不是重新执行物理轨迹，也不是新policy性能结果。

每方法额外原生/外部RNG三动作gate、不同seed变化及2种非法seed拒绝通过；新consumer每方法缺history或bit marker的两种实际恢复拒绝也通过。全部7993个真实终端的5个online和5个target Q与原51模型精确一致；bit移除后的clock projection与原50入口精确一致。实际consumer检查214.418秒。

| 方法 | 记录动作 | 动作前bit=1行数 | 首次bit=1动作索引（0起） | 终端health行 |
|---|---:|---:|---:|---:|
| impedance | 1375 | 1280 | 95 | 2665 |
| admittance | 1375 | 1279 | 96 | 2664 |
| vmc | 1375 | 1279 | 96 | 2664 |

## 正在运行和下一步

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1` 完成数 `{'impedance': 20, 'admittance': 19, 'vmc': 19}`；原三evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409身份保持，仍按原21600秒截止。最终全90、全state不变、raw子步及82→88全90配对待；不要重复启动。

本轮cache/consumer有界supervisor观察均成功，合计103次原进程身份核验。初次shell后台尝试未留下进程/启动收据且空log，随后唯一显式有界supervisor实际运行，记录见BACKGROUND_LAUNCH_OBSERVATION，未重复计算。GPU guard原97370/97399–97402持续，用户再次明确要求科学全部结束也继续保载。阈值50%、目标70%，本轮129样本min `[68, 73, 67, 75]`%、低于50 `[0, 0, 0, 0]`，末值 `[71, 77, 70, 79]`%；含合成占用，非科研吞吐/每瞬时保证；历史预热与低谷保留，非重启服务。

下一步接入完整trainer、正式evaluation和health调度，验证52维状态/全replay与新采集current-next观测、双marker、旧历史保留及原生更新的准确恢复，再依据完整89退化及离线对照证据单独决定/登记有限在线90。未把本轮接口通过当成科学接受或自动授权90。需要新的修订内稳定性窗口，原88—90 A/V失败窗口保持，不将不同revision混合宣称收敛。

原协议30条件×55秒、每方法每周期41250新transition、append-only4m、terminal128、batch65536/UTD1、原LR/reward/masks、物理/MJB/gates/filter/dt5e-5保持。Direct33数值阶段接受但冻结30条件Task/Strict0/0，Direct28缺最终内存证明仍披露；指定ESN缺失，不替换成另一主机模型。partial75、不可判74–76、79安全中止、半std拒绝及全部历史失败保留。Goal active，完整reward稳定/loss健康与最终对比仍未达到。

## 归档和发布

开工真实query main72d318a5，随后fetch/read maincea807d8与baselinef6e8f8c，已fast-forward保留另一主机非RL final108登记/资源受阻记录；无更改本机冻结runtime，无子agent。使用仓库sii-research-sync技能。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_VIOLATION_CONSUMERS_20261030/SMALL_EVIDENCE.tar.gz`，50成员/42791字节/SHA256 `c2f52675805fe71941a1a83a9374006c533c0401fe06cc345adf57293a014c41`，逐tar成员及Python AST核验。Git index/commit逐字节与正常push/真实ls-remote核验见包外PUBLICATION。HDD配额满，仅原位更新254字节LATEST；三份大快照及raw sidecars仍共享SSD，非HDD/arm1全备份。
