# 固定多训练seed复验：实际启动记录

2026-09-25凌晨按预声明协议启动seed20260924/20260925各parameter6/direct7，共四run。仅改变训练seed；原奖励、模型、8192互动预算、物理fixture和final选择规则不变。20260924两分支先并行，各完整训练及四评估结束后，才启动20260925两分支；任一执行错误停止后续seed，保留已经启动的同seed peer。task/gate失败不影响入表、不触发换模型。

服务器根 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_multiseed_20260924_r1`。本机同名outputs目录保存冻结source/BUILD、真实PLAN/PREFLIGHT/EXECUTION、初始manifest及progress；当前不是四run完成归档。

## 已核证据

- 原训练source全部196文件按字节复制，只新增3文件，合计199；原163执行源码逐项保持原proof中的hash。所有source文件无写权限。134机器人资产、两fixture、runtime/CUDA、完整训练nominal options及两份600步proof来源均在真实DGX无物理preflight重核。未新跑证明仿真、未修改旧源或旧证明。
- reviewed训练入口SHA `56fd587fd95d3cbd9333c2e965bcf91a4649cd994bcc85f56081eb14640ec156`。
- 队列SHA `306450a286aaa4846bcc8d0a568b55c5f81fc43769af9425be5735f6430c49b1`；snapshot builder SHA `728767f98947fde3df13bc8bd4ff2d3f3fe00567282741d45d03d1d9d7e3ecd4`。
- 新协议SHA `453220211e13aa737fe620f77b55961fa41f37509c325f60cb76259aafb0df4a`；BUILD SHA `84c6c1ab7b03256bfeebd257401d798d174033b60d71b19c320dca72634738e5`。
- PLAN SHA `ce54a417388bf2a351fac3b59cbf500f9ea6b2f02eb43813fff8b0e09d126c09`；PREFLIGHT SHA `6e011847ab37173e009abba59cef8707527c0f323d47e437d8ff0662da2f765c`。四条完整命令、参数、seed、cpu、output均在PLAN中，队列EXECUTION记录实际argv和启动时间。
- 四项无物理测试通过：首seed错误后不启动下一seed、等待并保留已启动peer、同seed pair完整结束后才进入下seed、父侧status写失败后有界回收自己Popen的进程组。TERM等待15s，必要时KILL再等15s，不影响sibling。
- UTC2026-09-24 16:42:25启动前实查：原18条部署COMPLETE；全服无仿真worker，仅既有WebUI及检查进程；可用内存116.75GiB；新training/EXECUTION不存在。证据 `docs/evidence/paired_multiseed_20260924/prelaunch_resources.json`。

## 实际启动与资源

持久队列PID **549548**，默认2worker，确认空槽2，全服上限4。每run7200s超时、1CPU线程、原RSS保护7GiB及系统至少2.5GiB可用，CUDA保持原device。

| 训练seed | 分支 | Python PID / CPU | 首次真实进度 | 状态 |
|---|---|---|---|---|
| 20260924 | parameter6 | 549559 / 5 | 192步，32.71s，RSS2.29GiB | 运行中 |
| 20260924 | direct7 | 549560 / 6 | 224步，31.24s，RSS2.29GiB | 运行中 |
| 20260925 | parameter6 | 待自动队列启动 | 未开始 | 等待前一pair |
| 20260925 | direct7 | 待自动队列启动 | 未开始 | 等待前一pair |

以上PID需结合实际完整命令核对，不能因入口旧日期或本机断线重复启动。全局`status.json`在job启动/结束时更新；训练步数以各run的`progress.json`为准。日志`logs/<seed>_<mode>.log`，原始输出`training/<seed>/<mode>`；全部失败均保留。

后续按2048/4096/6144/8192核checkpoint真实步数与hash。各run完成后需完整归档、独立全部8192 transition和SB3 reward审计、对应zero原始轨迹/MJB等价、最终模型离线回放；通过后才具备后续六条件部署资格。当前不能将启动记录表述为新增两seed已完成，也不能把多seed复验表述为新算法或多物理训练场景。
