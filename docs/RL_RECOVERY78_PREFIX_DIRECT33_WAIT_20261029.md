# 恢复78前缀诊断与原Direct33连续观察

2026-10-29T08:41:58.001761+00:00，Goal active。承接[完整77/78续训](RL_RECOVERY77_COMPLETE78_RUNNING_20261029.md)和[Direct33冻结评测](RL_DIRECT33_FROZEN_VALIDATION_20261029.md)。本轮不启动或重启科学任务，原78与冻结33持续推进；无79或Direct34。

## 固定前5000次更新

三路各固定前5000条optimizer原字节、连续步号、所有数值有限、独立标量复算和源码逆变换全部通过。该描述性检查登记在训练与前缀可用之后，不冒充前瞻窗口，也不据局部均值宣布收敛。源自77已审工具，仅改变周期/路径/标题；完整78审查与原76–78 PLAN保持不变。

|方法|critic 首1000 → 末1000均值|critic 最大值|actor 首1000 → 末1000均值|
|---|---:|---:|---:|
|impedance|2.931915 → 2.734444|18.749109|25.242827 → 25.210080|
|admittance|1.192993 → 1.236785|6.321925|-9.111547 → -9.123858|
|vmc|1.448537 → 0.845574|185.416763|-12.665768 → -12.745974|

六栏loss图已实际查看：阻抗critic反复尖峰；导纳均值较平但有孤立尖峰；VMC早期大尖峰且actor仍向负值漂移。VMC第3198125步critic185.416763，随后55.847782、5.147417、3.592860；前后原始记录单独保存并独立核验。日志没有该时刻minibatch逐样本归因，不能据此编造终端样本原因。没有NaN/Inf不代表loss健康，原训练保持，完整78终端/health/loss和76–78 reward结果仍待。

前缀证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_recovery78_first5000_20261029_v1`；实际图/检查为PLOT_INSPECTION.json，尖峰原记录与算术为PEAK_CONTEXT.json和PEAK_CONTEXT_REVIEW.json。解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。未改变学习率、reward、masks、物理、gate、batch65536/UTD1/terminal128、4m replay及23/47历史markers。partial75继续作为不完整曝光保留，原74–76不可评定。

## 连续观察

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/recovery78_prefix_audit_20261029_v1` 的11样本/300.005秒观察完成，18个原PID/start_ticks身份全部持续live；观察器自然结束不触发科学重启。参数步号到 {'impedance': 3221641, 'admittance': 3222537, 'vmc': 3225962}，各30条件仍按原流程运行。Direct33完整runtime回合到8/30，尚未有完整30物理/filter/torque和最终policy不变审查结论；原root reviewer和29→33配对等待继续。该冻结比较仍是一个训练seed/动作seed、训练条件，不能替代指定ESN或最终SPT比较。

## GPU与保存

从上次最终收据之后取原guard全部144个5秒样本，四卡最低[76, 71, 69, 69]%，低于50次数[0, 0, 0, 0]，最新[79, 91, 92, 94]%。合成保活和科研吞吐分别记账；保活不依赖训练/评测结束状态，用户要求全部科学结束仍继续。原supervisor78710及workers78730–78733保持，历史停机和预热空闲未抹去；不是重启自启服务。

执行主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。本轮证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029/SMALL_EVIDENCE.tar.gz`，35成员/936009字节/SHA256 `81878110d6dee673b65ae33d4a6038418643ec8b98224a03f853ce4b6952bc25`，逐成员/hash/Python AST核验通过，[收据](RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029_SAVE.json)。大checkpoint/raw/replay仍SSD，非HDD或arm1全备份；HDD既有LATEST指针仅原位更新不增长。

本轮实际fetch/read main `69d656d67e60b66107f506400af0d36bc195b4d1` 和baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。远端非RL已完整108（Task1/108、Strict0/108）、八球完成并启动v9补采，和本RL不同任务。共享AGENTS/UPDATE_LOG的新增冲突逐段保留双方；其余14远端文件逐字相同。合并commit8d5319b5；没有改动对方实验。GitHub推送以最终实际收据为准，既有HTTPS认证缺失。

下一步等原78完成，检查全loss/health/标签、2304旧终端与新增30终端及实际图、原76–78统计后再决定有限下一阶段；不自动追加79。原冻结33完整后审查原物理及配对结果，不能用旧29代替。Goal保持active。
