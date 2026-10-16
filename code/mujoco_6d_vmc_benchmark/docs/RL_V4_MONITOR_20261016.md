# v4 宿主机核验与恢复交接（2026-10-16 10:33 CST）

## 11:06 CST 复查补充

远端main `f6522a0e5abdb93741e74ce4554914ac31c0ec97`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询、fetch并读取日志。宿主机v4/恢复进程为空，
47,448步/84,898更新和Task/Strict各0/34均无变化；其余三方法未启动。
43,656步checkpoint全部登记hash再次匹配；最近1000步reward −0.001225和temperature
0.00032924（最近1000次更新）仍为历史样本。MemAvailable约3072MiB仅等于worker上限，
无余量，swap已用2047MiB；旧v3b模拟器PID2311744/2312815仍活动，未干预。共享cgroup
memory.current=6,846,820,352字节、swap.current=191,475,712字节、两项max均无限额，
oom/oom_kill=0；不将共享指标当作v4独立资源证明。GPU41°C、481/16303MiB、4%。
本轮不启动恢复、不发信号、不改冻结条件、不验收；原派发截止12:33:19 CST不变。

独立归档收据：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0306/MONITOR.json`，
SHA256 `9e773054d6b809532dbc9445475c61e2622ace277b4aa2960f734b779d9496f8`。

## 10:46 CST 复查补充

本轮宿主机检查未发现v4或恢复trainer；原execution仍显示running，但实际已中断，没有新
训练交互。持久化47,448步/84,898更新、34已结束回合及Task/Strict各0/34不变，其余三方法
未启动。checkpoint_0043656的所有登记hash再次匹配；历史reward/temperature指标没有新样本。
MemAvailable=3035MiB、swap已用2047MiB，仍不足单worker3072MiB上限，更未包含余量。
旧v3b模拟器PID2309032/2309783仍运行，未发信号或干预；共享app cgroup的oom/oom_kill=0，
memory.max与swap.max均为max，不能当作已退出v4的独立资源收据。GPU42°C、517MiB、4%。
本轮没有恢复、没有验收、没有改源码/冻结配置；派发截止仍12:33:19 CST。

远端已查询/fetch/读取：main `f8cbb9b71f481ef614729b59c98abdc8dc7d3371`，baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。本轮独立监视收据：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0246/MONITOR.json`，
SHA256 `5b766ad9f15d5edb23e29cc1f1c6ca0ca5613f128fc14a9154007e28c67c7796`。
下文保留10:33检查与中断处置的原始说明。

本轮未达到收敛或验收。实际计算主机为 airpig，冻结物理/MJB、dt=5e-5、canonical48、公共
filter、执行器限制和最终 gate 未改；未使用服务器计算。开工源码 `7be409d`。

| 方法 | 本轮可核实的状态 | 训练 Task / Strict |
|---|---|---|
| direct_task_safety | 至少 47,448 live steps、84,898 updates；停止操作后中断 | 各 0/34 已结束回合 |
| impedance_payload | 未启动 | 未评估 |
| admittance_payload | 未启动 | 未评估 |
| vmc_payload | 未启动 | 未评估 |

34 个已结束回合中 33 个达到 55 秒，24 个 physical_valid；1 个早停原因是
`global_penetration_exceeded_2mm`。其余 9 个完整但 physical_invalid 回合没有 abort_reason，
不能因此视为物理通过。零基索引 34 的在途回合未完成，保留原始 running 收据。

最初 10 个回合 return 均值 −25.3785，最近 10 个均值 −29.8091、标准差 7.8914；不支持改善或
收敛。最近 1,000 单步 reward 均值 −0.001225 不含完整的回合级信息，不能冒充成功。
最近 1,000 optimizer 行 temperature 均值 0.00032924、entropy −6.6922、critic loss 6.8138。
连续分布的微分熵可以为负，单凭负 entropy 不能断言探索完全塌缩。

## 实现与资源异常

- 登记、环境 `SII_RL_UTD`、agent 配置均选择 1，但旧 trainer 第 269 行 `range(2)` 每步执行
  两次 optimizer update。实测 `84,898 = 2 × (47,448 − 4,999)`。既有数据必须标为实际 UTD=2。
- v4 trainer 2223028 / simulator 2306337 同处 Codex app 共享 cgroup，`memory.max=max`、
  `memory.swap.max=max`；不能把 execution 声明的 3 GiB 当成内核硬限。该 cgroup 的
  oom/oom_kill=0，但不是独立 worker 指标。采样时两进程 VmSwap=0，不能证明禁 swap。
- trainer RSS 1,198,564 KiB、8 个运行时线程；simulator RSS 710,516 KiB、1 个线程。
  数值线程环境变量均为 1，CPU affinity=1。RSS 监控仅检查 `_job` 包装进程，不能覆盖子树。
- 旧 v3b direct/impedance 模拟器仍分别在 CPU1/6 执行；v4 内只有一个模拟器，但全机并非
  单路。未停止这些其他 run。历史 `sii-rl-full-campaign-v2.service` 已不存在。
- 采样系统 swap 已用 2047 MiB；GPU 42°C、496/16303 MiB、利用率 5%。这不是 v4 GPU 训练。

## 停止操作的实际结果与修复

本轮验证 PID/命令后，先向 v4 coordinator 2223021 单独发送 SIGTERM 防止后续派发，再向
trainer 2223028 发送其已有 SIGUSR1 回合边界停止请求；没有向模拟器或进程组发信号。
但之后整个 v4 进程树消失，未产生预期的终止收据或新 checkpoint。因此本轮操作**没有实现
安全回合末退出**；疑似启动容器生命周期连带退出，原因尚未独立验证。这个未完成回合是
监视操作之后发生的中断，不能描述成自然结束、资源 OOM 或训练成功。

最后可恢复 checkpoint 为 `checkpoint_0043656`，全部登记 hash 已核验。至少 3,792 步后续
交互没有成为可恢复 checkpoint；日志保留，不删除、不改写历史 execution。

新增独立 `tools/train_v4_recovery_rl_20261016.py`：使用 `range(utd)`，启动时强制核验
MemoryMax≤3 GiB 和 MemorySwapMax=0，并把相对停止标记解析到 run 根目录。旧 trainer
及其他在途训练的已有源码不变，避免破坏它们结束时的 source hash 校验。该恢复实现已通过
语法检查和实际更新循环的 UTD=1/2 stub 验证；尚未执行真实仿真或 checkpoint 恢复。

恢复条件：重新核验无 v4 进程；建立独立登记输出、记录继承历史实际 UTD=2；使用独立
systemd unit 硬限承载 trainer 和 simulator；从上述 hash 通过的 checkpoint 恢复。停止时先
请求 trainer 收完回合并确认 checkpoint，再处置上级生命周期。停止后的 MemAvailable
仅 2931 MiB，低于一个 3072 MiB worker 上限（尚未加余量），因此本轮没有启动恢复。
不要以已修代码等同已恢复运行，也不要盲目重启旧 coordinator 或旧输出。

真正登记的派发截止是 **2026-10-16T04:33:19Z / 12:33:19 CST**；此前日志中“08:00 后
不再新派发”既早于截止也未实际执行，本轮更正。root execution 还混有早期路径失败状态，
以方法收据和本轮中断说明共同判读。四方法均未完成，统一 acceptance 和独立最终审计未运行。

## 共享与可追溯性

实测远端 `main=32d027966797647ab16496e8b35d05bca498f4d8`、
`baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，已 fetch 并读取两分支日志。
远端 main 最新仍为上一轮 RL 监视；baseline 为既有探索分析，不自动合并。

归档已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0229/receipt-checkpoint.tar.gz`
SHA256 `aaed7b35c6fe1da01bb63f6153bf99730a0e3fa05724cf779ec54c8b75479b2c`。
包含 43,656 步完整 checkpoint、协议/版本、初始监视收据及 episode33 的 AUDIT/execution；
初始收据记录请求停止，须结合后续中断说明，不能单独当作正常收尾证明。
全部原始轨迹尚未全量同步，仍在本机输出目录保存；不得声称上述归档覆盖全部失败轨迹。

同一远端独立目录另有已核验 `recovery-interruption.tar.gz`，SHA256
`0766f2e260481c73bb724cbef1da17308c5f2a3df0d3aa6011b08f34d7bd148b`，包含中断说明、
原始未完成 execution、恢复源码及本报告当时快照。恢复代码的硬内存/禁swap检查也已用
允许和拒绝用例验证；真实仿真仍未执行。
