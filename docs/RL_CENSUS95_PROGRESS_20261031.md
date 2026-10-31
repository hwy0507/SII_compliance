# 第95轮十分钟实际进度观察

本轮为verified wait：当前原第95轮仍运行，先逐PID/start确认101个身份真实存活，随后有限观察600秒，未重启训练或重复派发分析。Goal active，未收敛。

实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`、共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`、解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际query/fetch/read main `44654f59c4ae3234add55102b68251f795570588`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；仓库sii-research-sync流程及非RL并行工作保持。

## 实际进展

原101身份连续600.525s/61样本保持，三方法新增{'impedance': 5382, 'admittance': 5434, 'vmc': 5303}；保存steps{'impedance': 3923565, 'admittance': 3927109, 'vmc': 3927258}，已完成条件{'impedance': 0, 'admittance': 0, 'vmc': 0}。全部三训练、90sampler、archive、原固定8443终端/全90比较两个等待器、5个GPU守护身份均核对；未发现新DRIVER/训练/archive/终端或比较失败。观察源与计划、逐次steps及最终保存快照位于 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_progress_20261031_v1`。

原正式运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle95_20261031_v1`，完整归档与review仍待。原固定终端 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census95_fixed94_terminal_20261031_v1`、全条件比较 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_comparison_20261031_v1` 两个唯一消费者仍在原截止内等待。输入组完整性核验已完成的94不能替代完整95/96；原94–96窗口5%/nearzero1/5000bootstrap/seed2026102861保持。

## 接续路径

等原完整95 FINISHED/review/health/loss和两个消费者结束后，实际查看原loss/health及比较图，核验保存算术；运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census95_comparison_20261031_v1/check_terminal_population.py --complete` 检查全部95日志和回放done、旧8443终端indices/masks及新30终端/方法。前5000没有新终端不能代替增长证明，在线逐分层tensor没有日志。

依据完整95再决定有限96，没有自动96或Direct34。96可容纳4m，97须单独容量决策，不覆盖旧回放。完整94三组映射在census95_window_inputs目录，最终统计仍须原binder检查全部三轮九组真实输入。

现有I原loss尖峰/actor漂移、A94 short0200丢失成功、原90–92失败和全部历史退化保持。Direct33数值验收与冻结Task/Strict0/0、旧28证据限制及指定ESN缺失保持。若意外中断，保存最新95 partial learner/Adam/RNG/replay/journal并另登记census-aware恢复，不回退94重跑95；MuJoCo物理state未保存。

## GPU及保存

守护 `/tmp/sii_gpu_util_guard_20261031_recovery_v1` 持续运行，科学结束仍保留，不创建STOP，不是主机重启服务。此窗口121样本/609.212s，最低[74, 70, 69, 70]%、低于50[0, 0, 0, 0]、末值[78, 96, 91, 91]%；含synthetic负载，与实际训练吞吐分列，不声明每瞬时下限或掩盖旧主机切换0%。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_PROGRESS_20261031/SMALL_EVIDENCE.tar.gz`，20成员/20303字节，SHA256 `50ce72cbee9ae7b2d088b45ecea177fb1f06612d142f40f161cf9c41f2fae71f`，逐成员字节/AST/JSON通过。发布收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS95_PROGRESS_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD LATEST原地保持254字节，仅交接指针，大checkpoint/raw/replay继续共享SSD，非HDD/arm1全备份。
