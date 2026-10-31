# 第95轮全条件比较与终端增长检查准备

第95轮三路原在线训练继续，Goal active，尚未收敛。主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工实际query/fetch/read main `e98541b34f91918f5134d2dc4cbd68744cc2ad5a`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新增RL变更，并行非RL工作保持。应用仓库sii-research-sync流程。

## 已完成的输入与前缀核验

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_comparison_20261031_v1` 保存COMPARISON_PLAN/WAIT_PLAN以及源码和diff。全部完整94的90条rollout成功标签、abort、stage、模型hash、冻结条件、reward分项和均值/Task/Strict总数已独立复核；完整94 Task/Strict为18/17、15/14、17/17。95协议和94只允许post_interruption_continuation字段变化，conditional_terminal_amendment精确相同；原抽样健康loss均读取agent_train/original_sampled_q_loss，条件估计另列，actor亦单列。缺少真实完整95时前置检查按预期拒绝，不伪造结果。

check_terminal_population.py绑定完整94的全部8443终端indices/masks，来自 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1/reference94`；分路2815/2814/2814。实际95 first5000每步terminal_population与父总数加包含本步的done累计相等，原日志字节回读精确，三路无新终端。15个缺更新/错步/错总数/漏增长/错父总数损坏输入被拒绝。check_source_order.py核验29个锁定运行源码及实际trainer，确认add/cache同步在同step更新之前。此前缀没有真实新终端，不能作为增长证明。

## 正在等待的完整95分析

唯一全90条件比较等待器PID1569117/start197351143，沿原archive截止 `1793444841.1889687`，CPU10，每分析脚本600s上限。在原完整95 REVIEW/health/loss和FINISHED通过后，interpret95.py比较全部90个条件reward、分项、Task/Strict/abort及loss，changed_cases.py绑定所有标签变化的原两轮rollout、穿透和模型hash；保存汇总复算并产生图。实际图仍须查看。等待器的legacy输出键automatic95=False表示不派发训练；其源码没有任何95/96训练启动路径。两轮使用相同估计器，但此描述比较不是因果证明，也不替代固定94–96窗口。

原固定终端等待器PID1270332在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1`，仍等待完整95；其基准是完整94全部8443条、all5/original masks，保留old≤93/new94与历史79/90/92中止及93失败尖峰。两类消费者只有推理/分析，没有优化更新或物理推进。完整95完成后还需运行：

```bash
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_comparison_20261031_v1/check_terminal_population.py --complete
```

完整模式要求原FINISHED/review、严格完整95 checkpoint校验，全部新日志与全回放done精确，旧indices/masks保持，新30条件终端全部覆盖；报告存档32分层计数。在线逐分层tensor没有日志，不能把存档计数写成在线逐分层观察。**这些完整95结果尚未产生，完整模式尚未运行。**

## 实际持续训练与下一步

原101身份连续600.513s/61样本保持，三路新增{'impedance': 5422, 'admittance': 5408, 'vmc': 4999}；保存steps{'impedance': 3913890, 'admittance': 3917440, 'vmc': 3917574}，完成条件{'impedance': 0, 'admittance': 0, 'vmc': 0}。身份包含三learner、90sampler、原archive、两只读等待器与5个GPU守护进程。训练源码、学习率、reward、MJB、actor49/canonical48、critic/replay52和23/47容量标记保持，每方法本轮最多41250新transition。

下一步等待完整95归档，查看原loss/health和两类比较实际图，完成保存算术、全部新terminal增长与完整科学解释，再单独审查有限96。固定94–96统计5%/nearzero1/5000bootstrap/seed2026102861及原登记时序保持，尚无完整输入绑定或统计结果。96可容纳于4m回放；97需另行容量决策，不能覆盖回放。没有自动96或Direct34。

原95 first5000 I重复尖峰/actor上移保持；原94的A short0200成功丢失、原90–92失败及全部历史退化不因新程序抹除。Direct33原数值验收、冻结30例Task/Strict0/0、旧28证据限制和指定ESN缺失保持。数值收敛不能替代Task成功。若中断，保全最新95 partial的learner/Adam/RNG/replay/journal，另登记census-aware部分恢复，不回退94重跑95；MuJoCo物理状态未保存。

## GPU与持久交接

独立guard `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 持续运行，科学完成后仍保留，不创建STOP；它不是系统重启服务。当前窗口127样本/639.833s，最低[72, 69, 68, 70]%、低于50[0, 0, 0, 0]，末值[78, 91, 91, 92]%。占用包含synthetic guard，不等于科学吞吐，也不是每瞬时下限保证；旧主机切换0%历史保持。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_COMPARISON_20261031/SMALL_EVIDENCE.tar.gz`，46成员/48773字节，SHA256 `b30666292d498ae9eca45c2f1765b2a56788b7dc8966033d36813017752fe9e4`，逐成员字节与AST/JSON核验。提交字节与实际远端核验另存 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_COMPARISON_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，LATEST交接指针原地保持254字节，大checkpoint/replay/raw仍在共享SSD；这不是HDD/arm1完整备份。
