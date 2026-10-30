# History critic有限88已实际启动；三路状态与数据核验通过

2026-10-30，Goal active。经过完整87准确迁移接口和本轮完整消费链预检，已明确登记并实际启动唯一有限history88模型修订。三路都在采集/更新，正式父均为完整87；当前完整88结果、reward稳定和最终loss健康仍未得到证明，不启动自动89或Direct34。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮query/fetch/read main `628bf1b824520e3f98cfe385c48f6225e163e32d`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，收尾没有远端新增；沿用sii-research-sync，无子agent。

## 有限科学修订与入口验证

登记和决定 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_online_20261030_v1/SCIENTIFIC_DECISION.json`、`AMENDMENT.json`。原85—87稳定性全失败、I/V末段loss上升和历史终端拟合漂移；原87匹配terminal拟合15个critic终点均偏向history，但只有in-sample证据。本次仅测试一个history信息修订，不采用统一half-std/entropy目标调整，不导入离线拟合权重。

critic/replay50→51，索引50为当前动作前累计外穿透 `p/(p+0.0002)`；actor仍49维、clock仍49索引，online/target新增权重和Adam矩初值0，原学习率/reward/masks、terminal128、pair reducer、原上界投影、canonical48/物理/MJB/gate/filter/dt5e−5保持。每方法30条件×最多55s、最多41250新transition，batch65536/UTD1，4m append-only和23/47历史容量标记保留。模型会通过critic不确定性影响CHEQ mixing，不把修改后学习称为始终相同策略。

三路真实完整87恢复、全旧状态及replay/新增history核验、实际65536 batch在可丢弃副本两次恢复重放通过，原生更新全state精确，初次共6次clone update。每方法22个协议/父边界拒绝，共66；真实87不能冒充完整88。完整冻结30 evaluator、三动作gate/native replay、实际health入口均接入；health实际消费原87迁移软件fixture，所有终端统计与原87精确相同，六栏实际图查看保留旧I/V loss上升。该fixture不是新物理评测，冻结88尚未派发。

## 保留的失败与修复

1. 初次复制依赖时旧prepare.py覆盖新同名准备脚本，因缺旧评测输入退出；发生在新run和物理派发之前。保留原log/旧脚本，改独立register88.py并排除旧调度文件复制。
2. 初次实际启动中导纳被新入口的严格浮点相等挡下：原LR `2.9999999999999997e-05`，计算预期 `3e-05`，差 `−3.3881317890172014e-21`。退出位置在训练目录/物理进程创建前，0新物理/正式更新；阻抗和VMC已经运行且未停止。独立v2恢复原有1e−12有限容差，并让check-only执行同一gate，5个错误学习率拒绝和额外2次clone update通过。只重试导纳，没有改学习率或扩大预算。
3. 只读startup/full-review生成器的连续数字替换把旧父cycle87误写成88，startup检查器退出，observer如实记录缺失PID。独立v3只读脚本修正父87/当前88，替换旧startup/archive consumers；三条正式learner未改未重启。修正后实际三路启动快照全部核验通过，所有失败收据保留。

## 当前运行与实际证据

唯一活动汇总入口 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_20261030_v2`。其中impedance/vmc为原v1方法目录的链接，PID保持3861085/3861087；admittance在v2独立目录，PID见LAUNCH.json。原v1导纳目录保留零物理失败，不能重启它。实际只读归档/检查运行代码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_review_20261030_v3`；活动只读身份在汇总run的 `REVIEW3_MONITOR_LAUNCH.json`、`REVIEW3_STARTUP_LAUNCH.json`，旧MONITOR/STARTUP收据保留但已替换。

|方法|保存时总steps|本轮新增steps|已审启动快照新增steps|已保存早期prefix q首→末1000均值|该prefix最大q loss|
|---|---:|---:|---:|---|---:|
|impedance|3615661|9213|5000|2.757372→1.962527|32.285168|
|admittance|3614141|5391|2000|1.343984→1.278980|7.902052|
|vmc|3619201|9451|6000|1.268404→1.064519|20.187889|

启动证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_20261030_v2/startup_v3/REVIEW.json`：旧replay每个原字段精确、新增历史列全核、原optimizer超参数/历史标记、30 MJB和sampler affinity、全部捕获的新transition canonical48/context/clock/history/raw-action混合映射及reward重构通过，各方法reward重构最大误差0。保存的只是部分周期，terminal_coverage=False；完整终端/Task/Strict/周期reward仍待结束。

固定早期prefix分别I5932/A2000/V6000条，原行副本和hash在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_review_20261030_v3`，全部有限但保留32.285/7.902/20.188尖峰；这些不同长度前缀只作运行观察，不作公平方法排序或收敛。随后120.042秒、13样本验证99个learner/sampler/monitor/guard身份保持，各路steps实际增加。

v3 archive88会在全部有限作业完成后保存完整88，运行全旧字段和新51维current-next/reward逐行review、完整health及全41250loss/独立标量保存复算和图。实际图仍需结束后查看；不把监控部署当完成。下一步先完成这轮完整科学审查，再决定是否继续训练。冻结88完整30入口已准备，须完整88及对应注册后再派发。

未来88–90稳定性在任何88启动之前登记于 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history88_90_reward_stability_20261030_v1`：同原近零guard1、相对限5%、5000 bootstrap、seed2026102861，强制三个周期相同history修订。只有方案和源码，没有自动89/90训练或统计结果。所有原失败窗口保留，新旧revision不混算稳定。

## 保存和GPU

本轮235次GPU采样最低 `[72, 67, 69, 65]`%、低于50次数 `[0, 0, 0, 0]`、末值 `[80, 94, 93, 94]`%。原v7 supervisor97370和四worker继续，科研结束也保载；包含合成占用，不冒充科学吞吐。历史v7预热0、v6 31/33/44低谷保留，采样不保证每瞬时，守护非重启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY88_ONLINE_20261030/SMALL_EVIDENCE.tar.gz`，278成员/1464084字节，SHA `b158a49e1cc554e40959f073bb2ed6d275b8a1d8d79b2eb4aea498742068ebe7`，逐tar成员/AST校验，Git index/commit另核，成功push再实际确认远端之后包外PUBLICATION。当前大checkpoint/新轨迹、软件fixture和启动快照均共享SSD，启动静态快照hash见收据；非HDD/arm1全备份。HDD原LATEST指针254字节原位更新。

Direct33数值阶段接受但冻结30 Task/Strict0/0，28中断缺最终内存证明；指定ESN仍不可用，不替换他主机模型、不重复追问。partial75、74—76不可判、79安全中止、85—87稳定性失败及全部历史结论继续保留。Goal最终仍需四方法reward平稳/loss健康、冻结评测及指定比较。

保存补充：原始 `.diff` 以及三份已冻结 `frozen_helpers.py` 的末尾额外空行保留原字节，不为格式检查改写已测源码。排除这些已明确列出的原件后，其他暂存内容的空白格式检查通过；全部证据仍逐大小/SHA及Git blob核验。
