# 第93轮持续推进与GPU保活复核（2026-10-31）

用户要求即使全部科学工作完成仍保持四卡利用率≥50%。原GPU保活正常运行，目标70%、最低duty .7；独立于训练完成标记，未设置STOP。此次没有重启训练、等待器或guard，没有更改科学协议。

## 2026-10-31 — 第93轮继续；科学完成后仍保持四卡GPU保活

- [交接](RL_VIOLATION93_GUARD_PROGRESS_20261031.md)。用户再次要求全部完成后仍保持GPU≥50%；原独立guard源码与SSD持久副本逐字相符，原5进程正常，训练结束不触发退出。不是重启服务，不承诺每瞬时利用率。
- 原101身份连续180.068s/19样本保持，三路steps增长{'impedance': 1996, 'admittance': 1964, 'vmc': 1985}，保存steps{'impedance': 3840691, 'admittance': 3843982, 'vmc': 3845017}。原93/archive/两个只读等待器继续，完整93/健康稳定/两项比较仍待，无新训练或自动94/Direct34，未收敛。原冻结90完成勿重启；所有历史失败、Direct原结论、指定ESN缺失保持。
- GPU41样本min[76, 69, 68, 71]%、低于50[0, 0, 0, 0]，含synthetic guard、不等于科学吞吐。SSD33成员/SHAafa66ac6核验，HDD仅254字节指针、非全备份；main10b1fb69/baselinef6e8f8c2实际query/fetch/read，正常发布见收据。Goal active，无子agent。


实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`。共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮依据仓库sii-research-sync实际query/fetch/read main `10b1fb693e6ac653466646fa8e2e5a8714cf3dd6` 与 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，相关科学协议无新变化。运行证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_guard_progress_20261031_v1`；原训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle93_20261031_v1`。原checkpoint、seed、环境和MJB hash、启动登记见本次复制的REGISTRATION/EXECUTION及前交接 `RL_VIOLATION93_COMPARE_READY_20261031.md`。

原learner729494/729495/729496、90sampler、archive729497、固定92终端等待1461907、全90比较等待2089103、guard97370/97399–97402均按PID/start ticks连续核验。19样本/180.068秒的三路实际steps增量为 `{'impedance': 1996, 'admittance': 1964, 'vmc': 1985}`。保存时完整93尚未出现，两等待器仍沿原截止1793422944.4276955；不能把存活称为已有最终结果。当前无自动94/Direct34。

GPU保活源码与 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/recovery86_history_progress_20261030_v1/gpu_guard_v7.py.txt` 逐字核验，SHA256 `5600eb0cfe76c2eb2f88d2341a77878b8021b70de0efaaadb2094cd7382a8db0`。观测41样本/203.273秒，最低[76, 69, 68, 71]%、低于50次数[0, 0, 0, 0]、末值[80, 92, 70, 93]%。采样与合成负载不等于每瞬时保证或训练吞吐；原历史低谷保持。当前guard独立于对话和科学完成运行，但位于/tmp、不是重启服务，不能据此宣称系统镜像或重启恢复已验证。

下一步读取完整93的归档/review/health/loss，并实际查看结果图；固定全部8263终端/all5/masks比较及全90训练92→93比较结束后独立核算和查看图，保留任何新abort或退化。依据证据再决定后续，不盲目续94。原90–92 I/A稳定性失败、V仅reward通过；原93前5000的I尖峰和actor上移、A中段抬升、V末段均值上升保持，当前不能宣布reward与loss联合收敛。

冻结90全90/98391200子步审查及raw/88→90比较已完成，Task/Strict I17/16、A15/15、V17/16，I long0000安全中止及I/V short0600违规保留；原完成进程不重启。Direct33原数值验收、冻结全30 Task/Strict0/0、旧28缺最终内存证明与恢复2完全不变保持；不把任务成功追加为数值收敛条件。指定ESN仍缺，不替换其他主机模型。

保持critic/replay52、actor49/canonical48、clock49/history50/bit51、已学history/violation及Adam/RNG/双marker、append-only4m及23/47历史标记、terminal128/batch65536/UTD1/原LR reward masks、冻结physics/MJB/Task/Strict/filter/执行器/dt5e−5，每方法本轮最多41250新增。保留partial75、不可评74–76、79/90/92中止、halfstd拒绝和全部失败窗口/软件失败。

共享SSD归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_GUARD_PROGRESS_20261031/SMALL_EVIDENCE.tar.gz`，33成员/107292字节，SHA256 `afa66ac6f643618f588864ccbfc11ddb520b2c9b95536effd9fc654a8a45fca8`；逐成员字节/Python AST核验。manifest在 `docs/evidence/RL_VIOLATION93_GUARD_PROGRESS_20261031/MANIFEST.json`。提交字节核验和实际push远端收据位于 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_GUARD_PROGRESS_20261031/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。HDD配额满，仅现有LATEST254字节原地更新回读；大checkpoint/replay/raw仍在SSD，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
