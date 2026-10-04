# 共同RL最终边界：前瞻登记与完整回合收尾

2026-10-04 03:24:43 UTC登记，24个最终条件仍封存，任何模型都尚未启动49,500阶段。
目的为在用户授权72小时内保留完整38模型×24条件最终矩阵；依据公开的串行队列容量，
不依据奖励、任务成功率或某个baseline表现。原80,000为交互上限，不代表已经训练完成。

## 固定规则

- 五个RL家族、各三个seed全部采用既有`cumulative_0049500`阶段的自然完成checkpoint。
  完整回合预留机制允许实际48,126–49,500步；短失败仍计入，不补写成49,500。
- 原优化器80,000步日程、奖励、训练身份、初始化、回放/RNG继承与环境/gate保持。
  没有因缩短采样而重新缩放学习率日程，须在论文中披露。
- 运行中的不可变队列仍会派发71,500与80,000两阶段。独立连续监护仅对这些阶段的精确
  learner发送SIGUSR1；原handler让在途回合结束后正常保存。每模型最多多出2×1375步。
  后续checkpoint不参与最终选择，额外数据/成本完整保留。不是硬杀进程或改写既有记录。
- 最终选择须核验三个队列自然关闭、15个目标边界及hash闭环；缺一个就不冻结，不能
  静默回退到更早checkpoint。原finalizer无修订时的行为保留。
- 此修订不增加ESN拟合预算，不解封测试身份，不删除baseline。修订02仍未登记。

## 机制与验证

新增`research72_rl_final_boundary_20261004.py`，登记原父进程PID/start ticks/完整argv及队列快照。
发送信号前核对模型、seed、root、output、原runtime、父进程/UID、SIGUSR1 handler；以pidfd绑定
进程并复查启动时间，避免PID复用。仅向本研究已经授权的后续冗余训练阶段发停止请求。

本机7项边界测试中6通过、1因本机Python无pidfd API跳过；Spark原生Python3.12实际7项全通过，
含可正常结束的一次性测试子进程。5项现有最终选择测试通过。新增关闭证据检查拒绝缺失产物、
源码hash变化、未结束监护及重复队列。测试不运行仿真、不触碰实际训练进程。

03:24 dry-run核验三个原队列、0信号/0物理/0封存读取。03:25启动一次性持续服务
`sii-r72-rl-final-boundary-v1`，PID2471052，MemoryMax512MiB、单线程、CPU上限1核；不是定时任务。
03:25:43核验仍watching、0信号。真正后续收尾尚未发生，不能据测试宣称已完成15模型训练。

## 证据与归档

服务器主机`arm1@192.168.31.70`，共同根：
`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。

| 相对共同根的原件 | SHA256 |
|---|---|
| `AMENDMENT_RL_FINAL_BOUNDARY.json` | `e2b74294410aa3a97aa9ded6623f8a621424048101b3b5c7c32fe3159a4a7779` |
| `rl_final_boundary_v1/REGISTRATION.json` | `89041159b0fa314bea94fcb317a96d1eb53727b555ea0e4fb469a4f2cde5c4b5` |
| `rl_final_boundary_v1/DRY_RUN.json` | `7690210f5f77719f2e6dd454bd38fcd1227b1a913d48f3629f2b4327473cc2d5` |
| `rl_final_boundary_source_v1/tools/research72_rl_final_boundary_20261004.py` | `00b7656a9ed03b69660b9e4d9db2befdf5fb27774eacf7dce005995aaceb13c7` |
| `EXPOSURE_SNAPSHOT_20261004_0327.json` | `b982abae1e0a9aefea175001ec03f3f45136399d7767419be5ffc83b6156fd7a` |

源码/测试两个文件已逐大小/内容/模式核验；tar SHA
`e5903f2beb8dc3460627d391fab404cf5d91c94eeb6292be83497f4ea12cc9a8`。
前三份登记证据在Git `docs/evidence/research72_20261003/`保留同字节副本。
原容量依据为已归档v4预测SHA`a1b04d8a8664bfab58bf0b1d51981a24d18319d2cc19bd931bbaab325ae0b2c4`。
真实队列等待、加载和不同并发下的耗时还需继续观察，不能把节省预算当成完成保证。

03:27成本快照：新teacher32/40（这32条全部为训练身份，task32/32、strict20/32）；
context16/168，增强学习率网络8/168；RL累计72,418交互/44,856更新，仍不是全部模型的最终预算。
当前没有新拟合。下一步等待采集、开发和RL完整边界，核验新teacher示范覆盖与真实剩余容量后再决定
是否有必要登记所有模仿学习家族共同的追加拟合。完整最终留出、审计和投稿结论仍未完成。
