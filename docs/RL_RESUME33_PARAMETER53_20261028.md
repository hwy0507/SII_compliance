# RL 恢复交接：Direct33／参数53与持续GPU守护（2026-10-28）

> 当前最新训练状态见[参数53完整、正式54启动](RL_PARAMETER53_COMPLETE_20261028.md)，旧三参数53已退出。本文保留恢复时快照。

> 后续更新：当前GPU守护为[v4](RL_GPU_GUARD_V4_20261028.md)，旧版已退出；下方v2占用与PID为原保存快照。早期loss与下一轮恢复准备见[补充交接](RL_EARLY33_PARAMETER53_20261028.md)。

当前 Goal **active，未完成**。本文件覆盖此前“Direct32／参数52仍运行”以及更旧的暂停状态。用户已再次授权续训，且明确要求训练/评测完成后仍保持GPU负载。没有子agent。

实际主机：`rltest-1025--a6ed2ff39b3c-hsje5ateny`。共享SSD根目录 B：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。仓库 R：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/SII_compliance`。本轮基于main `9a78d280e7b622ad1e96a8aeb5e4cacbbcebf3d5`，baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；已读两分支日志，安全快进合入非RL180最终审计，保留其成果。冻结训练runtime没有随Git合并变化。

## 已完成且保存

回到会话时，原四训练均已在完整周期退出，四卡0%/9MiB；不把此空档隐去。Direct32以及参数52的完整checkpoint已逐SHA256复制到独立archive，完整审查/健康诊断均结束。

| 方法 | 完整轮次 | steps | updates | mean reward | Task/Strict |
|---|---:|---:|---:|---:|---:|
| Direct | 32 | 1,328,040 | 10,584,328 | −30.907576405 | 0/0 |
| Impedance | 52 | 2,182,430 | 2,177,431 | −0.593691747 | 18/18 |
| Admittance | 52 | 2,182,250 | 2,177,251 | −11.924950471 | 13/12 |
| VMC | 52 | 2,183,250 | 2,178,251 | −2.806195247 | 17/17 |

每方法均30/30完整55秒、无abort；旧replay逐字段保留，新增奖励按已冻结interval journal重算误差0。Direct原930隔离尾部保留；不采样，不虚构完整25。此检查不等于独立重跑全部原始物理。

- Direct32：`B/runs/serl_take_cycle32_archive_20261027_v1/direct/cycle_00032.pt`，SHA256 `7f268d0bc354ded874d0536b22f59b37f8715a08be321279f65a0113c5486d09`。
- 参数52：`B/runs/parameter_capacity_pool30_cycle52_archive_20261026_v1/{impedance,admittance,vmc}/cycle_00052.pt`；hash见小证据parameter52_review.json。
- 完整审查：`B/runs/serl_take_cycle32_review_20261027_v1`、`B/runs/parameter_capacity_pool30_cycle52_review_20261026_v1`。
- 已复核Direct29冻结全30条件REVIEW：passed、33,000,000物理子步、Task/Strict0/0、机器违规0、网络/replay不变。不要重复此已完成物理评测；这仍是一训练seed、一动作seed、训练条件上的冻结验证，不是held-out或ESN最终对比。

## 稳定性与loss

原预登记49–51审计已从旧超时后恢复，旧WAIT_FAILURE完整保留。三方法原5% reward稳定性检查均未通过：I均值−0.586820→−2.375631→−5.871345，触发原near-zero1保护；A−10.310858→−15.368123→−10.339232，相邻49.05%/32.72%；V−4.523729→−4.604059→−2.780044，后相邻39.62%。没有事后替换原窗口。

完整32/52每方法41,250条optimizer记录的critic/actor loss均无非有限值。实际查看loss与健康图：Direct首/末1000 critic loss 0.008966→0.008772、max0.018171，平稳；I 2.450615→1.782739、max20.051586；A 1.335186→1.909094、max37.244198，末段抬升须跟踪；V 0.695057→0.716188、max13.597031，actor有小幅漂移。不能把有限值冒充全部健康收敛。Direct原27–29稳定通过的事实保持，Task0单列，不追加成功率门槛。

新固定53–55窗口在53训练启动之前登记，原5%/nearzero1/5000条件bootstrap不变，seed2026102852。`B/runs/parameter_capacity53_55_reward_stability_20261028_v1`；waiter PID514418，固定10800秒，不自动训练或自动停止。

## 当前正式训练

| 方法 | PID | cycle | 交互steps（保存时） | 更新次数 |
|---|---:|---:|---:|---:|
| direct | 259795 | 33 | 1,332,979 | 10,623,840 |
| impedance | 238630 | 53 | 2,192,520 | 2,187,521 |
| admittance | 238631 | 53 | 2,192,235 | 2,187,236 |
| vmc | 238632 | 53 | 2,194,259 | 2,189,260 |

Direct GPU0/CPU0–12、参数I/A/V GPU1/2/3及CPU13–25/26–38/39–51，每路30sampler。准确父checkpoint全state/下一batch/RNG check-only通过后才启动。新轮实际启动检查：Direct新增1000，旧1328040全prefix、135新成熟/865pending与旧930隔离保留；参数I/A/V新增2000/3000/5000，旧全部replay/history保留；四路新reward重算误差0、30MJB/动作/clock/CPU亲和核验通过。

Direct真实startup最终证据位于`B/runs/serl_take_cycle33_20261027_v1/startup_retry3/REVIEW.json`，复用retry2相同snapshot；最初启动审查因LAUNCH结构、第二次因helper残留cycle32断言失败，原脚本/日志保留。完整Direct32审查的首次条件计数迁移错误也保留失败日志；修正只涉及审查轮次/计数，训练与科学判据未改。

两个阶段均只登记一个有限周期。归档审查monitor PID259815（Direct33）/238633（参数53）已安装并验证存活，按LAUNCH进程起始ticks识别原进程，等FINISHED后核checkpoint、复制并hash，再执行完整review/health。当前**没有自动启动34/54**；下一次先读review/health/loss作续训决定，不把guard当自动训练。

## GPU持续负载

持续守护：`B/runtime/gpu_util_guard_20261028_v2/guard.py`，LAUNCH记录真实supervisor/worker PID，STOP文件控制退出。它是用户授权的**合成矩阵运算占用**，独立进程、无checkpoint读取写入、0训练更新，不是科研增益、训练进度或评测结果。

v1自适应过度退让，60采样四卡平均73.60/73.75/75.98/68.47%，各有5/9/8/11个低于50%样本，保留原证据。v2保持至少60%计算duty，第二次60采样实际80.23秒，四卡平均80.57/88.47/86.75/83.70%，最低37/25/43/27%，仍各有5/3/3/6个低于50%样本；所有正式learner身份存活并推进。**窗口均值达标，但不能声称每瞬时≥50%或保证平台不会关机。** 两窗口都包含合成守护，绝非纯训练利用率。v2窗口训练吞吐D/I/A/V约8.87/14.06/12.43/16.78steps/s；保底占用带来资源开销，不能说提速。

守护独立于Codex前台和训练生命周期：训练完整退出后仍运行，直到收到STOP或机器关机。它不是跨系统重启服务。当前v1已停止；只保留v2运行。若用户要停止保底：`touch B/runtime/gpu_util_guard_20261028_v2/STOP`（用上方实际B绝对路径）。不停止四正式训练。

## 下次继续

1. 先看`docs/evidence/RL_RESUME33_PARAMETER53_20261028/LIVE_STATUS.json`并核/proc起始ticks、PROGRESS/FINISHED，勿盲信旧PID或重复launch。
2. 正式run：`B/runs/serl_take_cycle33_20261027_v1`与`B/runs/parameter_capacity_pool30_cycle53_20261026_v1`；未完成则监测原任务，完成则核各自archive/review及ARCHIVE_REVIEW_FAILURE。
3. 固定53–55窗口继续，导纳末段loss要做实际时序诊断；使用完整optimizer/replay/RNG/history续接，不改物理、奖励、gate、学习率或引入辅助权重。Direct后续为平台延续证据，不否认已有27–29稳定性。
4. 检查v2 guard `CONTROL.json`、`samples.jsonl`、`worker*.json`与原PID，避免重复占用。保底混合占用与正式科学指标分开报告。

代码/小证据已保存在共享SSD与本仓库`docs/evidence/RL_RESUME33_PARAMETER53_20261028`，MANIFEST逐文件大小/SHA核验。执行源码保留`B/runtime/resume_sources_20261028_v1`；大型checkpoint/replay/raw继续留共享SSD。HDD配额满，不宣称HDD/arm1完整备份；仅尽力更新既有LATEST入口并回读。Git发布与小证据归档收据另记，不能仅依赖Git恢复大数据。

## 保存收据


本轮共享SSD小证据包已逐成员核验：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_RESUME33_PARAMETER53_20261028_033457/SMALL_EVIDENCE.tar.gz`，175成员、1,750,097字节、SHA256 `4ac8b8a17261b2d219eda3eae2e09e9eaa5b7a288c59aef9f9646a39d325e64f`。收据[RL_RESUME33_PARAMETER53_SAVE_20261028.json](RL_RESUME33_PARAMETER53_SAVE_20261028.json)。HDD全文更新遇Errno122配额满，现有LATEST已成功写为简短指针并回读验证；全文仍在共享SSD仓库，非HDD完整备份。
