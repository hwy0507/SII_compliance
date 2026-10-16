# 更新日志

## 2026-10-16 14:01 CST — 定位Direct训练奖励的任务区分不足，保留完整证据

- 开工查询/fetch/read main `ea271110dc9ef16da2047e2df8fa374eefa8cc28`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS及Goal进度。上一轮为证据归档进展；
  本轮新增闭合训练奖励分解工具与3项针对性测试，实际五回合全部通过一致性检查。
- 五回合每个1375步仅末步有Task奖励−20，n25直接含终止奖励的窗口占1.818%；折扣势函数
  和均为−0.62499941，抵消残差<1e-15，未发现这部分公式错误。安全罚分为0/−12.5152/
  −17.7245/0/−13.9713。两个零安全罚分回合的有界跟踪cost为0.89025/0.07205，但折扣
  总奖励相同，说明当前task_safety目标对安全失败间的跟踪质量缺少持续区分。
  这不是n25无效或已证实根因的结论；下阶段应检验密集跟踪项，而非把失败平台当收敛。
- 新工具严格校验奖励组件、gamma、终止语义和日志连续性，区分Task成功/Strict失败的训练
  标签；拒绝多行/错位日志，活动末尾缓冲显式pending。完整execution/protocol/log快照随收据
  保存，可复算。无新仿真、模型更新、最终acceptance或独立最终物理审计。
- 同一worker/协调器持续推进至58,781步/92,439更新，新增8250/8250；6个完整回合Task/Strict
  0/6、physical_valid2/6，第6return−22.475132，第7在途，其他三族排队。58,781 checkpoint
  hash通过。OOM0/swap0，memory.max事件1162；继续观察回收压力，不改冻结源码/限制。
- 工具/测试/五回合完整诊断快照已核验归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-reward-signal-20261016T0600/evidence.tar.gz`，
  1,225,327字节，SHA256 `30a9b7c1c8e615098a3d7d2596684e03e5a865e236fa7c74400f34e43e4db9c6`。
  服务器只归档/hash；第五回合之后大型轨迹/checkpoint仍本机待同步。Goal保持active。

## 2026-10-16 13:55 CST — Goal持续运行，失败轨迹与checkpoint补齐归档

- 实时查询/fetch/read main `436552af7c5417c9033ffd87dfb26ce8e5707559`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/专题进度；Goal仍active。
  同一协调器2329290/Direct trainer2329294保持运行，没有重复启动。
- Direct持久化57,750步/91,408更新，相对阶段起点新增7219/7219。5个完整55秒回合，
  Task/Strict联合0/5、physical_valid2/5；第5个return−35.653907，仍停在approach，
  原生训练AUDIT记录RMSE803.36mm、物体目标XY误差192.09mm、max_lift0。
  57,406步checkpoint实际hash核验通过，第6回合在途，另外三方法尚未派发。
  条件不同，不把回合顺序当调参因果证据；当前没有收敛或最终验收成功。
- worker内存3,151,167,488/3,221,225,472字节，memory.events max434、OOM/kill0、swap0；
  已发生硬限缓存回收压力，继续观察，不能仅以占用上升断言内存泄漏或移除限制。
- episode38–40原始失败轨迹、53,281/54,656/56,031 checkpoint、协议和05:46Z完整监视快照
  已上传并核验大小/hash，发布至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-episodes38-40-20261016T0545/evidence.tar.gz`，
  835,219,332字节，SHA256 `77b7fca926a438e8c83a96ae2e01a0c1f075420aae69e1340916112dc61860e4`。
  服务器仅传输/归档/hash；episode41及之后产物仍本机待同步。冻结输入、活动源码未修改，
  未运行最终acceptance或独立最终审计。下一步核对该有限阶段的完整结果和自动接续。

## 2026-10-16 13:39 CST — 落实训练收敛统计，拒绝失败平台与累计计数冒充成功

- 查询/fetch/read main `dee4c4ba65b5866d1e31fe0d15122c34da47d384`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/Goal进度。同一stage/worker保持active；
  optimizer55,804步/89,462更新，54,656 checkpoint hash核验通过，第四回合在途。
- 3个完整回合return−21.667945/−34.277519/−39.487075，均值−31.810846、标准差7.480807，
  Task/Strict联合0/3、physical_valid1/3。temperature约0.00058627，不将早期样本判作收敛。
- 新增训练收敛统计工具：按原登记96回合/两32回合窗口/全条件覆盖/各窗联合成功≥90%/
  mean漂移≤5%/CV≤25%检查。只合并hash绑定精确接续的自有rows，旧n1回合不混入n25；
  保留所有失败/在途记录，拒绝重复、缺失、非有限值及不同reward/配置混合。快照与hash可复核。
  8项针对性测试通过，实际Direct与未启动的其余三类均未满足判据；不执行最终验收。
- worker内存2,913,398,784字节、上限3GiB，约0.92GB为file缓存，OOM0/worker swap0。
  持续Goal和训练继续，物理/gate/输入/执行器与活动源码保持。
- 源码/测试/完整统计快照已归档核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-screen-20261016T0539/evidence.tar.gz`，
  41,304字节，SHA256 `45442e7ee148cdc6cd734afe9594700778551612fd30f9837809b2b14f7ca311`。
  服务器只归档/hash；第二个新回合之后的大型轨迹/checkpoint仍本机待同步。

## 2026-10-16 13:31 CST — 补齐四类RL精确接续与逐方法恢复预检

- 查询/fetch/read main `24fd0bd0dc6fda266053bcee6b7ddf7dd23dcd1b`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/Goal进度；同一训练服务真实active，
  54,500步/88,158更新，新增3969/3969。两结束回合Task/Strict0/2，第三回合在途，其他三类排队。
- 阶段工具新增prepare-next，要求四族上一阶段全部闭合，逐一核对各自最终checkpoint、
  trainer/协调器状态和父execution hash；保留各自网络/优化器/RNG/raw replay，单族仍新增
  11k/总日程1M。沿用上一冻结trainer/worker/物理/parameter，只更新协调器与预检脚本。
  四方法真实预检各自通过并封存hash后才允许新阶段launch；当前没有建立stage02或重复派发。
- 15项相关测试通过。当前running stage真实提前接续被拒绝且无新目录；真实53,281步n25
  checkpoint/replay恢复、采样RNG重复性及一次丢弃更新通过，原文件hash未改。探针exit0、
  峰值1,128,882,176字节、OOM0；不包含新仿真或模型保存，不冒充其余三方法真实预检通过。
- 13:31训练worker内存2,604,490,752字节、峰值2,685,267,968，硬限3GiB/swap0、OOM0。
  Goal继续，四方法收敛/最终acceptance和独立审计均未完成；新阶段启动仍需本阶段完成证据。
- 本轮源码/测试/恢复探针与运行检查脚本/收据归档核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-continuation-20261016T0530/evidence.tar.gz`，
  14,259字节，SHA256 `bcde86e186923ad2679e97160ee328eb8018216cb0a5d405928c4f0c0b466ea9`。
  服务器只归档/hash，53,281及之后checkpoint/原始轨迹仍本机待同步。

## 2026-10-16 13:22 CST — RL真实推进，补齐只读Bellman目标和动作外推诊断

- 开工查询/fetch/read main `02053647aba71bc623b0c53fe65d60fc002a8f5b`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS/Goal进度。上一轮为实质进展；
  本轮核对同一协调器和worker真实活跃，未重复派发；新增诊断工具/数学测试与真实证据。
- Stage01 Direct已完成2个完整55秒回合，到53,281步/86,939更新，新增2750/2750；
  return−21.667945、−34.277519，Task/Strict0/2、physical_valid1/2，第三回合继续。
  训练worker峰值2,351,804,416字节、硬限3GiB/swap0、OOM0；其余三方法仍排队。
- 固定51,906 checkpoint上取1948条训练replay（含末端增采样），独立复算分布Bellman期望。
  裁剪概率质量均值0.006649%；末25步历史动作绝对TD误差均值0.1884，而当前动作Q比历史
  动作高2.5416；最新回合子样本误差1.1743。支持继续查动作外推和新回合学习，未证明实现bug，
  不把历史行为MC当当前soft-Q真值或n25优越证明。两项数学测试通过，真实诊断exit0、峰值
  924,012,544字节、OOM0，模型hash/RNG/统计计数未改；无仿真、无更新、无测试集输入。
- 新工具`diagnose_goal_rl_credit_20261016.py`、测试、结果与进度均保留。当前阶段继续，
  后续调整在新有限阶段登记；Goal active，四方法收敛与最终统一验收/独立审计均未完成。
- 本轮诊断源码/测试/结果/监视快照、首个完整新回合原始轨迹和51,906 checkpoint已归档核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-20261016T0518/evidence.tar.gz`，
  264,505,895字节，SHA256 `f4a47b6801fae4d367caebb92dc2e0fd48765e9117feae4ac45d7ff2f1bec7dd`。
  服务器只归档/hash；第二回合及之后新轨迹/checkpoint仍本地待同步，未宣称全量共享。

## 2026-10-16 13:07 CST — 持续Goal启用，四类RL有限阶段已启动

- 用户明确开启持续Goal，允许自主排查/修复与有记录的训练调参；旧15小时run不回写，后续
  按独立有限阶段推进。开工查询/fetch/read main `11809cb960cb4acdcb6ebe1a431d622979d2a3ec`、
  baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS；保留无关未跟踪文档。
- 旧恢复最终50,531步/84,189更新，本段新增6875交互/6875更新、5个完整55秒回合，
  Task/Strict各0/5、physical_valid2/5；最终checkpoint逐文件hash通过。正常截止结束不等于
  training_complete，更不是收敛。所有失败保留。
- 新增有限阶段协调器、严格n1→n25 checkpoint/replay迁移与真实checkpoint预检，扩展恢复
  trainer识别Goal阶段授权。Stage01四方法串行各新增最多11k，Direct续50,531至61,531；
  其余三类从零至11k，优化器日程仍为各1M。只改回报信用窗口，reward/物理/gate/接口不变。
  25步离策略偏差及继承/从零曝光差异明确记录，不宣称优于1步；未来阶段须另登记接续。
- 9项恢复/阶段测试、4项多步replay测试通过。真实50,531 checkpoint预检：25步terminal回报
  独立求和一致、未跨回合bootstrap、一次更新有限、原文件hash未变；峰值1,161,908,224字节。
- `outputs/rl_goal_20261016_stage01/`协调器与Direct worker真实active；13:07读到51,250步/
  84,908更新，即新增719/719，UTD1；worker内存1,971,478,528字节、硬限3GiB、swap0、OOM0。
  当前尚无新完整回合，其他三方法排队。独立冻结源码快照，单模拟器；阶段截止10月17日13:00
  CST用于有限派发保护，Goal仍active。新收敛筛选要求两32回合窗口覆盖训练条件并同时满足
  reward稳定及Task AND Strict≥90%；不足样本不判成功，最终统一acceptance/独立审计未运行。
- 详细入口、局限与后续计划见`code/mujoco_6d_vmc_benchmark/docs/RL_GOAL_PROGRESS_20261016.md`。
  13:11补充：首个完整55秒回合新增1375/1375，到51,906步/85,564更新，新checkpoint hash
  通过、保存n_step25；return−21.667945、physical_valid=true、Task/Strict0/1，第二回合继续。
- 新源码快照/登记/预检/启动/13:07监视收据，以及旧恢复5回合原始数据与最终50,531 checkpoint，
  已归档核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage01-20261016T0507/evidence.tar.gz`，
  750,006,095字节，SHA256 `a65bf3966e17f1a38beb244cfa7983a40a7e9bb54f7f5b8f851ee3dda38ff13a`。
  服务器仅归档/hash；新阶段51,906 checkpoint及新回合仍仅本地，既有物理runtime依赖未全量打包。

## 2026-10-16 12:12 CST — 用户授权清理旧作业，修复版RL真实恢复并完成首回合

- 开工核对远端main `ce516ca45beac86d0e86d2fb2e1bde4a7fb0ce98`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read日志、AGENTS。用户明确授权后，
  先保持旧协调器存活但停止派发，再请求v3b trainer回合末退出；无模拟器的v2保存死锁中断。
  v2 partial checkpoint与失败保留；v3b阻抗112,750步/Direct73,365步新checkpoint hash通过，
  两者末尾历史源码一致性失败均保留。子进程退出后才结束旧协调器，未广播停止模拟器。
- 独立`sii-rl-v4-recovery-recovery-20261016-1140b.service`从43,656步恢复：首个完整55秒
  回合新增1375步/1375更新，到45,031步/78,689更新，新checkpoint hash通过，证明真实UTD1。
  cgroup硬限3GiB/禁swap生效，首回合峰值2,432,258,048字节、OOM0；source/config hash一致。
  首回合return−22.1773、Task/Strict均false；12:11已推进至46,000步/79,658更新。
- 只读critic诊断（无仿真、无更新）显示行为Q与历史行为回报差异，多数terminal目标已拟合；
  作为信用分配线索，不据此断言实现bug、收敛或成功。正常闭环/保存恢复不等于策略学会。
  当前仅Direct运行，其他三方法未启动，统一acceptance未运行，原派发截止12:33:19不延长。
- 更新RL进度、监视入口与`docs/RL_V4_REPAIR_20261016.md`。后续读取
  `outputs/rl_tuned_20261015_v4/RECOVERY_CURRENT.json`及`recovery_20261016_1140b/`，
  不以旧execution的running重复启动。当前源代码仍为ce516ca，本次仅提交报告/交接。
- 修复source/测试、登记、两套checkpoint、首个完整回合原始数据、资源与诊断收据已归档核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-recovery-20261016T0353/evidence.tar.gz`，
  431,405,754字节，SHA256 `cc93180c70721b0ceae8cafc25392d1bfb430cf87af004b22abd317af8f0d63a`。
  服务器仅归档/hash；后续在途轨迹及旧批次全量失败轨迹仍保留本机，不宣称已全量共享。

## 2026-10-16 11:32 CST — 实查训练bug、完成恢复入口与真实checkpoint诊断

- 用户要求修复后，核对远端main `a6f45496fdd6be40fbfdce1469aa0cdf18e66e43`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与运行证据。定位v2在11,000步
  保存卡住约21小时、无子模拟器仍占约1.1GiB；v3b两路实际仍在训练，早期退出记录不准确。
- 完善独立恢复trainer：真实UTD循环、每结束回合保存、拒绝无硬限cgroup、标明训练是否完成。
  新恢复控制器使用独立systemd service，3GiB/禁swap/单CPU，派发前核验进程、内存余量、
  原截止与checkpoint/source/config hash，防重复并禁止自动acceptance。旧在途源码不改。
- 5项回归测试通过；真实43,656步checkpoint恢复action一致、单次梯度确实更新actor，重复
  重载+更新结果一致且指标有限。只读历史replay诊断，无模拟器，无新交互，不写回checkpoint；
  峰值1,557,102,592字节、OOM0、exit0。首轮诊断metrics展开错误及修复后成功收据均保留。
- 恢复登记和命令已准备于`outputs/rl_tuned_20261015_v4/recovery_20261016_1140b/`，但未启动。
  旧进程处理请求被自动审批拒绝（可能干扰共享训练，需明确授权）；未绕过或执行信号操作。
  当前仍未收敛或验收，详情见`docs/RL_V4_REPAIR_20261016.md`；原派发截止12:33:19不延长。
- 修复/测试/诊断及登记证据已归档核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-repair-20261016T0332/repair-evidence.tar.gz`，
  SHA256 `945072b9fb82c88e3132903fd01a68ce4f456aa5ef28bc29d5cf165cb5ca8027`。

## 2026-10-16 11:06 CST — v4 无新交互，继续等待恢复资源

- 已实测/fetch远端main `f6522a0e5abdb93741e74ce4554914ac31c0ec97`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志、AGENTS及v4进度。
- 宿主机v4/恢复进程仍为空，旧running收据不代表运行；日志保持47,448步/84,898更新。
  34已结束回合中33完整、24 physical_valid，Task/Strict各0/34，1次穿透超过2mm早停；
  索引34回合仍为未完成历史收据。其余三方法未启动，43,656步checkpoint全部登记hash通过。
- 历史最近1000步reward均值−0.001225、最近1000更新temperature均值0.00032924，无新样本。
  MemAvailable约3072MiB仅等于worker上限、无余量，swap已用2047MiB；旧v3b两路仍活动。
  共享cgroup无限额、oom/oom_kill=0，不作为v4独立证明；GPU41°C、481MiB、4%。
- 本轮不启动、不发信号、不改源码或冻结条件，修复版本未实际恢复；未验收、未收敛，
  截止仍12:33:19 CST。更新RL进度，保留全部失败/未完成收据。
- 收据归档核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0306/MONITOR.json`，
  SHA256 `9e773054d6b809532dbc9445475c61e2622ace277b4aa2960f734b779d9496f8`。
  服务器仅作归档；全量原始轨迹仍仅本地、待同步。

## 2026-10-16 10:46 CST — v4 中断后复查，资源准入仍不足

- 已查询并 fetch 远端 main `f8cbb9b71f481ef614729b59c98abdc8dc7d3371`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两分支日志、AGENTS 和 v4 交接报告。
- 宿主机 v4/恢复进程为空；原 execution 的 running 是中断前陈旧状态，不代表推进。
  持久化日志仍为47,448步/84,898更新，34已结束回合中33完整、24 physical_valid，
  Task/Strict各0/34；索引34回合未完成。其余三方法未启动，未执行验收。
- 43,656步checkpoint全部登记hash再次通过；历史最近1000步reward均值−0.001225、
  temperature最近1000更新均值0.00032924，没有新样本。既有UTD修复版本尚未真实恢复。
- MemAvailable=3035MiB，仍低于3072MiB worker上限（尚未加余量），系统swap已用2047MiB；
  旧v3b两路仍活动，未干预。共享app cgroup无限额、oom/oom_kill=0，不能当成v4独立指标。
  GPU42°C、517/16303MiB、4%。本轮不启动、不发信号、不改冻结条件，截止仍12:33:19 CST。
- 更新RL进度和交接报告；本轮收据归档至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0246/MONITOR.json`，
  SHA256 `5b766ad9f15d5edb23e29cc1f1c6ca0ca5613f128fc14a9154007e28c67c7796`。
  服务器仅归档/hash核验，全部原始轨迹仍未全量同步。

## 2026-10-16 10:33 CST — v4 真实UTD/资源异常、停止中断与隔离修复

- 实测并 fetch 远端 main `32d027966797647ab16496e8b35d05bca498f4d8`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两分支日志及 AGENTS；保留无关未跟踪文件。
- Direct 至少47,448步/84,898更新，已结束34回合（33个完整55s、24个physical_valid），
  Task/Strict各0/34；最近10回合return均值−29.81，未收敛，其他三路未启动，未进行验收。
- 定位旧trainer写死`range(2)`导致实际UTD2；v4进程继承无限额共享cgroup，并无独立3GiB/
  禁swap硬限。旧v3b两路仍在运行，未改动。登记截止实际为12:33:19 CST，纠正早前末期表述。
- 本轮向v4协调器TERM、trainer USR1请求阻止派发并安全收尾后，整个v4进程树消失，未生成
  最终收据/checkpoint；这是停止操作后的中断，不能称安全边界完成。原始running/失败收据保留。
- 新增独立`tools/train_v4_recovery_rl_20261016.py`，修复UTD循环并要求内核内存/swap硬限，
  不修改其他在途run的旧trainer。语法与实际循环UTD1/2测试通过；尚未真实恢复，停止后可用
  内存2931MiB不足新worker预算。恢复须独立登记、原截止、已核验43,656步checkpoint。
- 更新RL进度和`docs/RL_V4_MONITOR_20261016.md`；checkpoint/协议/部分收据已归档核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-v4-monitor-20261016T0229/receipt-checkpoint.tar.gz`，
  SHA256 `aaed7b35c6fe1da01bb63f6153bf99730a0e3fa05724cf779ec54c8b75479b2c`。
  全部原始轨迹仍仅本地、待同步；服务器只传输/归档/hash核验。无新增训练、未改冻结科学条件。
- 同目录补充归档`recovery-interruption.tar.gz`已核验，SHA256
  `0766f2e260481c73bb724cbef1da17308c5f2a3df0d3aa6011b08f34d7bd148b`，含中断收据、
  恢复源码与报告快照。硬内存/禁swap guard的允许/拒绝用例通过，实际恢复仍待资源准入。

## 2026-10-16 10:06 CST — v4 Direct 46.0k 末期监视

- `direct_task_safety` 第 32 回合已结束于 `45,031` 步，`physical_valid=true` 但
  `task_success=false`、`strict_success=false`；第 33 回合在途，当前约 `46,036` live steps、
  `82,074` optimizer updates。checkpoint 仍为 `checkpoint_0043656`，不再新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.00133`，温度约 `0.000236`，critic loss 约 `7.29`，actor
  entropy 约 `-4.45`。Task/Strict 仍无成功，尚未收敛或开始 acceptance；系统 swap 仍占满
  2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 09:46 CST — v4 Direct 44.9k 末期监视

- `direct_task_safety` 第 32 回合仍在途，当前约 `44,858` live steps、`79,718` optimizer
  updates；最近已登记安全 checkpoint 为 `checkpoint_0043656`，不再新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.00111`，温度约 `0.000188`，critic loss 约 `7.33`，actor
  entropy 约 `-3.75`。此前所有完整回合 Task/Strict 均未同时成功，仍不满足收敛或 acceptance
  判据；系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 09:26 CST — v4 Direct 43.7k 末期监视

- `direct_task_safety` 第 31 回合已结束于 `43,656` 步，但 `task_success=false`、
  `strict_success=false`、`physical_valid=false`；按安全边界生成 checkpoint `checkpoint_0043656`。
  第 32 回合在途，当前约 `43,686` live steps、`77,380` optimizer updates；失败收据保留，
  不再新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.02060`，温度约 `0.000192`，critic loss 约 `7.40`，actor
  entropy 约 `-4.02`。Task/Strict 仍没有成功，尚未收敛或开始 acceptance；系统 swap 仍占满
  2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 09:06 CST — v4 Direct 42.5k 末期监视

- `direct_task_safety` 已完成第 30 回合至 `42,281` 步，`physical_valid=true` 但
  `task_success=false`、`strict_success=false`；第 31 回合在途，当前约 `42,524` live steps、
  `75,056` optimizer updates。checkpoint 仍为 `checkpoint_0033000`，收据保留；窗口末期不再
  新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.02129`，温度约 `0.000178`，critic loss 约 `7.49`，actor
  entropy 约 `-3.90`。没有 Task/Strict 成功，不能称收敛或开始 acceptance；系统 swap 仍占满
  2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 08:46 CST — v4 Direct 41.3k 末期监视

- `direct_task_safety` 已完成第 29 回合至 `40,906` 步，`physical_valid=true` 但
  `task_success=false`、`strict_success=false`；第 30 回合在途，当前约 `41,340` live steps、
  `72,682` optimizer updates。checkpoint 仍为 `checkpoint_0033000`，所有失败/未通过收据保留；
  窗口末期不再新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.02315`，温度约 `0.000159`，critic loss 约 `7.54`，actor
  entropy 约 `-3.28`。没有 Task/Strict 成功，仍不能称收敛或开始 acceptance；系统 swap 仍
  占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 08:26 CST — v4 Direct 40.3k 末期监视

- `direct_task_safety` 已完成第 28 回合至 `39,531` 步，但 `task_success=false`、
  `strict_success=false`、`physical_valid=false`（未给出 abort_reason）；第 29 回合在途，
  当前约 `40,286` live steps、`70,574` optimizer updates。最新 checkpoint 仍为
  `checkpoint_0033000`，失败收据保留；窗口末期不再新派发其余三路。
- 最近 1,000 步 reward 均值约 `-0.02072`，温度约 `0.000166`，critic loss 约 `7.58`，actor
  entropy 约 `-3.02`。Task/Strict 仍没有成功，不能称收敛或开始 acceptance；系统 swap 仍占满
  2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 08:06 CST — v4 Direct 39.1k 末期监视

- `direct_task_safety` 仍在途，约 `39,108` live steps，第 28 回合进行中，`68,218`
  optimizer updates；最新 checkpoint 为 `checkpoint_0033000`。第 26 回合在 `36,781` 步因
  `global_penetration_exceeded_2mm` 提前失败（Task/Strict=false、physical_valid=false）；第 27
  回合完整跑完但 Task/Strict 仍 false，失败收据均保留。其余三路没有 execution.json，不再新派发。
- 最近 1,000 步 reward 均值约 `-0.02372`，温度约 `0.000176`，critic loss 约 `7.62`，actor
  entropy 约 `-2.87`。没有 held-out Task/Strict 成功，不能称收敛或开始 acceptance；系统 swap
  仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 07:46 CST — v4 Direct 38.0k 监视

- `direct_task_safety` 仍连续写入，约 `37,972` live steps，第 27 回合在途，`65,934`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0033000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `+0.00099`，温度约 `0.000158`，critic loss 约 `7.60`，actor
  entropy 约 `-3.22`。短窗口回到零附近但策略仍塌缩、Task/Strict 仍 `0/0`，不满足稳定收敛
  判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 07:26 CST — v4 Direct 36.8k 监视

- `direct_task_safety` 仍连续写入，约 `36,822` live steps，第 27 回合在途，`63,646`
  optimizer updates；最新安全 checkpoint 为 `checkpoint_0033000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02407`，温度约 `0.000155`，critic loss 约 `7.63`，actor
  entropy 约 `-3.60`。负回报平台与策略塌缩继续，Task/Strict 仍 `0/0`，不满足收敛判据；未做
  acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 07:06 CST — v4 Direct 35.8k 监视

- `direct_task_safety` 仍连续写入，约 `35,762` live steps，第 26 回合在途，`61,520`
  optimizer updates；最新安全 checkpoint 为 `checkpoint_0033000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02284`，温度约 `0.000177`，critic loss 约 `7.64`，actor
  entropy 约 `-3.05`。负回报平台、策略塌缩和 Task/Strict `0/0` 持续，未满足收敛判据；未做
  acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 06:46 CST — v4 Direct 34.7k 监视

- `direct_task_safety` 仍连续写入，约 `34,680` live steps，第 25 回合在途，`59,362`
  optimizer updates；最新安全 checkpoint 为 `checkpoint_0033000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02201`，温度约 `0.000196`，critic loss 约 `7.66`，actor
  entropy 约 `-3.68`。负回报平台和策略塌缩持续，Task/Strict 仍 `0/0`，未满足收敛判据；
  未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 06:26 CST — v4 Direct 33.6k 监视

- `direct_task_safety` 仍连续写入，约 `33,578` live steps，第 24 回合在途，`57,164`
  optimizer updates；已生成安全 checkpoint `checkpoint_0033000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02176`，温度约 `0.000218`，critic loss 约 `7.68`，actor
  entropy 约 `-2.92`。checkpoint 增加但负回报平台、策略塌缩和 Task/Strict `0/0` 未改善，仍
  不满足收敛判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 06:06 CST — v4 Direct 32.4k 监视

- `direct_task_safety` 仍连续写入，约 `32,394` live steps，第 23 回合在途，`54,790`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02187`，温度约 `0.000233`，critic loss 约 `7.71`，actor
  entropy 约 `-3.62`。负回报平台和塌缩策略持续，Task/Strict 仍 `0/0`，不能判定收敛；未做
  acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 05:46 CST — v4 Direct 31.2k 监视

- `direct_task_safety` 仍连续写入，约 `31,210` live steps，第 22 回合在途，`52,416`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02163`，温度约 `0.000276`，critic loss 约 `7.74`，actor
  entropy 约 `-2.68`。回合 reward 仍为负平台、Task/Strict 仍 `0/0`，策略未恢复探索，不能
  判定收敛；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 05:26 CST — v4 Direct 30.1k 监视

- `direct_task_safety` 仍连续写入，约 `30,054` live steps，第 21 回合在途，`50,110`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.000646`，温度约 `0.000346`，critic loss 约 `7.81`，actor
  entropy 约 `-3.01`。零附近短平台仍没有 Task/Strict 成功（`0/0`），策略分布塌缩，未满足
  收敛判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 05:06 CST — v4 Direct 28.9k 监视

- `direct_task_safety` 仍连续写入，约 `28,858` live steps，第 20 回合在途，`47,718`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.00102`，温度约 `0.000408`，critic loss 约 `7.92`，actor
  entropy 约 `-3.97`。回报仍只是零附近短平台，策略分布塌缩且 Task/Strict 仍 `0/0`，不满足
  收敛判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 04:46 CST — v4 Direct 27.7k 监视

- `direct_task_safety` 仍连续写入，约 `27,710` live steps，第 20 回合在途，`45,416`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02070`，温度约 `0.000342`，critic loss 约 `8.10`，actor
  entropy 约 `-3.51`。温度/熵已塌缩且回报和 Task/Strict 未改善（`0/0`），仍不满足收敛判据；
  未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 04:26 CST — v4 Direct 26.5k 监视

- `direct_task_safety` 仍连续写入，约 `26,518` live steps，第 19 回合在途，`43,038`
  optimizer updates；最新安全 checkpoint 仍为 `checkpoint_0022000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02133`，温度约 `0.000280`，critic loss 约 `8.19`，actor
  entropy 约 `-4.59`。策略分布进一步塌缩，回报与 Task/Strict 仍未改善（`0/0`），明确不满足
  收敛判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 04:07 CST — v4 Direct 25.4k 监视

- `direct_task_safety` 已产生新的安全 checkpoint `checkpoint_0022000`；当前约 `25,394` live
  steps，第 18 回合在途，`40,790` optimizer updates。第 17 回合完整跑完但
  `task_success=false`、`strict_success=false`、`physical_valid=false`，失败收据保留；当前
  worker 仍在写入，未见 OOM 或重复进程。其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02129`，温度约 `0.000294`，critic loss 约 `8.18`，actor
  entropy 约 `-2.18`。探索已塌缩且没有任务成功，仍不满足收敛判据；未做 acceptance。系统
  swap 仍占满 2 GiB，worker 登记保持禁 swap。

## 2026-10-16 04:06 CST — v4 Direct 25.3k 监视

- `direct_task_safety` 仍连续写入，约 `25,322` live steps，第 18 回合在途，`40,646`
  optimizer updates；仍只有 `checkpoint_0011000`。无 OOM 或重复 worker，其他三路仍无
  execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02135`，温度约 `0.000296`，critic loss 约 `8.17`，actor
  entropy 记录约 `-2.24`，显示探索已完全塌缩。Task/Strict 仍 `0/0`，回报未改善，不满足
  收敛判据；未做 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 03:46 CST — v4 Direct 24.1k 监视

- `direct_task_safety` 仍连续写入，约 `24,138` live steps，第 17 回合在途，`38,272`
  optimizer updates；最近 checkpoint 仍为 `checkpoint_0011000`。无 OOM 或重复 worker，其他三
  路仍未创建 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02188`，温度约 `0.000340`，critic loss 约 `8.17`，actor
  entropy 仅约 `0.017`。探索几乎完全塌缩且回报/Task/Strict 未改善（`0/0`），明确不满足收敛
  判据；未做 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 03:26 CST — v4 Direct 22.9k 监视

- `direct_task_safety` 仍连续写入，约 `22,942` live steps，第 16 回合在途，`35,880`
  optimizer updates；最近安全 checkpoint 仍为 `checkpoint_0011000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动派发。
- 最近 1,000 步 reward 均值约 `-0.02160`，温度约 `0.000413`，critic loss 约 `8.17`，actor
  entropy 约 `1.14`。熵显著下降而回合 reward/Task/Strict 未改善（`0/0`），表现为探索塌缩而非
  收敛；未做 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 03:06 CST — v4 Direct 21.7k 监视

- `direct_task_safety` 仍连续写入，当前约 `21,756` live steps，第 15 回合在途，`33,520`
  optimizer updates；最近 checkpoint 仍为 `checkpoint_0011000`。无 OOM 或重复 worker，其他三路
  仍未创建 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.00090`，温度约 `0.000498`，critic loss 约 `8.13`，actor
  entropy 约 `2.56`。短窗口仍在零附近，但没有 Task/Strict 成功（`0/0`），不能判定收敛；
  未做 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 02:46 CST — v4 Direct 20.5k 监视

- `direct_task_safety` 仍在真实写入，约 `20,560` live steps，第 14 回合仍在途，`31,128`
  optimizer updates；安全 checkpoint 仍为 `checkpoint_0011000`。无 OOM 或重复 worker，其他三
  路仍未创建 execution.json，未手动派发。
- 最近 1,000 步 reward 均值约 `-0.00111`，温度约 `0.000614`，critic loss 约 `8.12`，actor
  entropy 约 `3.16`。短窗口回到零附近但没有任何 Task/Strict 成功（仍 `0/0`），不足以判定
  收敛，未执行 acceptance。系统 swap 仍占满 2 GiB；worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 02:26 CST — v4 Direct 19k 监视

- `direct_task_safety` 仍在真实写入，当前约 `19,370` live steps，第 14 回合在途，`28,736`
  optimizer updates；最近安全 checkpoint 仍为 `checkpoint_0011000`。无 OOM 或重复 worker，
  其余三路仍无 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02149`，温度约 `0.000756`，critic loss 约 `8.07`，actor
  entropy 约 `3.34`。温度/熵继续下降但回合回报和 Task/Strict 未改善（`0/0`），不满足收敛
  判据；未执行 acceptance。系统 swap 仍占满 2 GiB，worker 登记保持禁 swap，未见 OOM 收据。

## 2026-10-16 02:06 CST — v4 Direct 18k 监视

- `direct_task_safety` 仍连续写入，当前约 `18,180` live steps，第 13 回合在途，`26,362`
  optimizer updates；尚只有 `checkpoint_0011000`。已完成回合仍无 Task/Strict 成功，无 OOM 或
  重复 worker；其余三路仍未生成 execution.json，未手动接续。
- 最近 1,000 步 reward 均值约 `-0.02126`，温度约 `0.000932`，critic loss 约 `8.09`，actor
  entropy 约 `3.74`。温度/熵继续下降但回合回报未改善，Task/Strict=0/0，仍不满足收敛判据，
  未进行 acceptance。系统 swap 仍占满 2 GiB；worker 登记保持 `swap_max_bytes=0`，未见 OOM 收据。

## 2026-10-16 01:46 CST — v4 Direct 17k 监视

- `direct_task_safety` 仍在连续写入，当前约 `16,990` live steps，第 12 回合在途，`23,988`
  optimizer updates；仍仅有 `checkpoint_0011000`，无 OOM 或重复 worker。`impedance_payload`、
  `admittance_payload`、`vmc_payload` 尚未生成 execution.json，未手动派发。
- 最近 1,000 步 reward 均值约 `-0.02161`，温度约 `0.00115`，critic loss 约 `8.10`，actor
  entropy 约 `4.10`；Task/Strict 仍 `0/0`。该回合级负平台和零成功不满足收敛判据，未进行
  acceptance。系统 swap 仍全占用 2 GiB，worker 登记仍为禁 swap，未见 worker OOM 收据。

## 2026-10-16 01:26 CST — v4 Direct 15.8k 监视

- `direct_task_safety` 仍在真实写入：`15,816` live steps，11 个完整回合，第 12 个回合在途，
  `21,628` optimizer updates；最近完整 checkpoint 仍为 `checkpoint_0011000`。已完成回合均为
  `task_success=false`、`strict_success=false`，无 OOM 或重复 worker；其余三路仍未创建
  execution.json，未手动接续。
- 最近 1,000 个单步 reward 均值约 `-0.02136`（含回合边界大负值），温度约 `0.00142`，critic
  loss 约 `8.11`，actor entropy 约 `4.29`。回合级 return 仍约 `-21.85`，Task/Strict=0/0，
  不满足收敛判据。系统 swap 仍为已占满的 2 GiB；v4 worker 登记为 `swap_max_bytes=0`，未见
  worker OOM 收据，继续保留该资源限制并不进行 acceptance。

## 2026-10-16 01:13 CST — v4 Direct 持续监视

- `direct_task_safety` 文件仍在连续写入，当前约 `15,078` live steps、10 个完整回合、约
  `20,164` 次 optimizer updates；最近 checkpoint 仍为 `checkpoint_0011000`。未发现新的 OOM、swap
  或重复 worker；其余 `impedance_payload`、`admittance_payload`、`vmc_payload` 仍未创建
  execution.json，尚未接续。
- 最近 1,000 个单步 reward 均值约 `-0.00111`（范围约 `-0.0583` 至 `0.0458`），温度约
  `0.00161`，critic loss 约 `8.08`，Task/Strict 仍为 `0/0`。该零附近短窗口和回合周期波动
  不满足稳定 reward 加 held-out Task/Strict 成功的收敛判据；未执行 acceptance。

## 2026-10-16 01:04 CST — v4 Direct 14.5k 监视

- `direct_task_safety` 当前 `14,500` live steps、10 个完整回合、`19,002` 次更新，仍在运行；
  最近完整 checkpoint 仍为 `checkpoint_0011000`，无 OOM。
- 12k–14k reward 均值约 `-0.0211`、`-0.0215`，14k 后短窗口约 `-0.0011`，温度约 `0.00175`。
  该模式仍是回合重置造成的周期性波动，Task/Strict 为 `0/0`，尚未收敛或接续其余方法。

## 2026-10-16 00:43 CST — v4 Direct 13.25k 监视

- `direct_task_safety` 已推进至约 `13,250` live steps、9 个完整回合、`16,502` 次更新，仍为
  running；当前最近完整 checkpoint 仍为 `checkpoint_0011000`，未见 OOM。
- 11k–13k reward 均值约 `-0.0214`、`-0.0211`，13k 后短窗口约 `-0.0015`；温度约 `0.00217`。
  这仍是回合间波动而非稳定收敛，Task/Strict 为 `0/0`，其余三路未接续。

## 2026-10-16 00:22 CST — v4 Direct 12k checkpoint

- `direct_task_safety` 当前约 `12,000` live steps、8 个完整回合、`14,002` 次更新；最近安全
  checkpoint 为 `checkpoint_0011000`，worker 仍在运行，未见 OOM。
- 11k–12k reward 均值约 `-0.0214`，当前 12k 后短窗口约 `-0.00074`，温度约 `0.00268`；
  回合间变化仍明显。Task/Strict 仍为 `0/0`，尚未接续其余三类或开始 acceptance。

## 2026-10-16 00:06 CST — v4 Direct 11k 监视

- `direct_task_safety` 已推进至 `11,000` live steps、8 个完整回合、`12,002` 次更新，仍为
  running；未发现 OOM 或重复进程。
- 10k–11k 窗口 reward 均值约 `-0.00114`，当前回合尾段短样本约 `-0.476`；温度约 `0.00333`。
  回合级波动仍大，Task/Strict 尚为 `0/0`，不能判定收敛；其余三方法仍未接续。

## 2026-10-15 23:45 CST — v4 Direct 9.75k 监视

- `direct_task_safety` 当前约 `9,750` live steps、7 个完整回合、`9,502` 次更新，仍为 running；
  没有 OOM 或重复启动。
- 8k–9k、9k–9.75k reward 均值约 `-0.0217`、`-0.0244`，温度约 `0.00411`，短平台继续
  下滑且回合间波动明显；Task/Strict 仍为 `0/0`，尚未收敛或接续其余方法。

## 2026-10-15 23:24 CST — v4 Direct 8.5k 监视

- `direct_task_safety` 当前 `8,500` live steps、6 个完整回合、`7,002` 次更新，仍为 running；
  未检测到 OOM，未创建重复 worker。
- 7k–8k 单步 reward 均值约 `-0.00082`，8k–8.67k 受回合终止影响均值约 `-0.0317`；温度约
  `0.00509`，因此此前短平台不稳定，不能判为收敛。Task/Strict 仍为 `0/0`，其余三路未接续。

## 2026-10-15 23:03 CST — v4 reward窗口监视

- `direct_task_safety` 继续真实推进至约 `7,250` live steps、5 个完整回合、`4,502` 次更新，
  未请求停止，未见新的 OOM 收据。
- 7,000–7,500 步的单步 reward 均值暂约 `-0.0010`，温度约 `0.00630`、actor entropy 约
  `4.6`；这是短窗口平台迹象，仍没有 held-out Task/Strict 成功，不能判为收敛。
- 其余三路仍未接续；继续按单路安全边界和 v4 协议观察。

## 2026-10-15 22:46 CST — v4 Direct 持续推进

- 已确认 v4 现有 Direct worker 未重复启动，`direct_task_safety` 当前约 `6,250` live steps、
  4 个完整回合、`2,502` 次更新，`status=running`。
- 单路 CPU/UTD=1 资源约束仍满足；当前温度和 reward 仍处于探索早期，Task/Strict 尚为 0/0，
  未开始后续三类，也未做 acceptance。继续保留失败收据并等待安全 checkpoint。

## 2026-10-15 22:27 CST — v4 单路 Direct 监视

- 已再次核对远端缓存 `main=32d027966797647ab16496e8b35d05bca498f4d8`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 AGENTS；GitHub 网络仍不可达。
- v4 `direct_task_safety` 真实完成 3 个回合，约 5,000 live steps、2 次 optimizer update；
  5k–10k 窗口当前 reward 均值约 `-0.0023`，温度约 `0.00975`，探索尚未塌缩。
- Task/Strict 仍为 0，Impedance/Admittance/VMC 尚未接续；当前没有收敛或 acceptance 证据。
  单路 CPU、1线程、3GiB、禁 swap 继续生效，所有旧失败收据保留。

## 2026-10-15 21:58 CST — v3b异常退出与v4单路探索恢复

- 继续核对远端缓存：`main=32d027966797647ab16496e8b35d05bca498f4d8`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；本轮网络仍不可达，未冒称已取得新的 GitHub 日志。
- v3b 的 Direct/Impedance 进程在约 43,250/40,750 live steps 后返回码 1；其
  `execution.json` 曾停留在 running，已保留原始收据。Direct 从
  `checkpoint_0033000` 的单路恢复也在 34,090 steps、25 回合处失败；因此双路内存竞争
  不是唯一故障来源，不能把这两批称作收敛。
- 新增源码提交 `f9705f7`：登记 UTD=1 的内存安全臂和单路调度入口，仍冻结 MuJoCo/MJB、
  gate、canonical48 actor 输入、公共动作滤波、执行器限制和 dt=5e-5。
- 新 run `outputs/rl_tuned_20261015_v4` 已登记独立协议 SHA
  `61d379a9e514d99f59fb5f5262b9e7b0770ee0c8baabb3b413f4d93a746fa9db`：单路 CPU、1线程、
  3GiB、UTD=1；Direct 使用 task-safety，Impedance/Admittance/VMC 使用 payload shaping，
  探索温度 0.01，payload telemetry 只用于 reward，不进入 canonical48。首次相对路径启动
  失败已保留，随后已用绝对路径重新启动。
- v4 当前 Direct task-safety 正在真实推进，最新约 750 live steps、0 完整回合；其余三类
  尚未接续。尚无 reward 收敛、Task/Strict 成功或 acceptance 证据；按安全回合继续收据。

## 2026-10-15 13:40 CST — v2 调参失败保留与 v3b 百万步批次

- 核对开工时本地缓存远端 SHA：`main=32d027966797647ab16496e8b35d05bca498f4d8`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；本轮 GitHub 网络不可达，未宣称
  已取得最新远端日志。
- v2 `outputs/rl_tuned_20261015_v2` 保留为失败收据：Direct 仅 2,250 live steps、
  0 updates；Impedance 在首个观测因 `payload_shaping` 读取缺失的
  `payload_potential` 抛出 `TypeError(NoneType)`；Admittance/VMC 为 0 steps。该失败是
  reward 接口兼容性/调度问题，不能作为 RL 不适用结论。
- 新批次 `outputs/rl_tuned_20261015_v3b` 独立登记，协议 SHA
  `9fbeae9535bea093e98fdcb782e97673544f44f0ce69173eb5f78ed7f0561c03`，四方法各
  `1,000,000` live MuJoCo interactions，reward 全部使用兼容的 `original`，只调已登记的
  熵/温度臂：Direct `direct_balanced`，Impedance/Admittance `parameter_balanced`，VMC
  `parameter_explore`。物理、gate、canonical48、动作滤波、执行器限制和 dt=5e-5 均冻结；
  本机 CPU、两路并行、每路单线程/3 GiB/禁 swap，服务器不计算。
- 四路 1,375 步 smoke 均完成完整回合和 checkpoint hash；Task/Strict 均 0/0，属于 smoke
  预检，不是成功或收敛证据。CPU Orbax 保存器在 smoke 初版卡在临时目录，保留失败目录；
  v3b 的 parameter agent 改用同一网络状态的便携 Flax msgpack，保持 actor/critic/
  target_critic/temperature/obs_norm/rew_norm 目录契约，独立保存/加载验证通过。
- v3b 长训练已从绝对路径启动，Direct/Impedance 当前均真实推进但仍在 warmup（约
  1,500/4,250 steps、0 updates、未到 5,000 warmup）；尚未完成四方法，未做 acceptance，
  不声称 reward 收敛或成功。正式调度收据与所有失败/未完成产物均保留。
- 后续监视已确认两路越过 warmup：最新 Direct 约 11,500 steps/13,002 updates、
  Impedance 约 12,375 steps/14,752 updates；已完成回合仍为 Task/Strict 全 0，return
  只在失败平台附近波动。Admittance/VMC 尚待第一对完成后按协议接续，四方法 acceptance
  尚未开始；本机 CPU 吞吐显示该百万步预算是多日级，不能把早期曲线称作收敛。

## 2026-10-15 11:25 CST — 启动 RL 调参百万步批次

- 针对上一批 reward 平台化且探索温度快速塌缩的问题，登记本机 run
  `code/mujoco_6d_vmc_benchmark/outputs/rl_tuned_20261015_v1`：四个策略各
  `1,000,000` 次 live MuJoCo interaction，最多两路并行、每路单线程/3 GiB/禁 swap，服务器不计算。
- 只改变登记的 RL 学习信号和探索超参数：direct 使用 `task_safety + direct_balanced`，
  impedance/admittance 使用 `payload_shaping + parameter_balanced`，VMC 使用
  `payload_shaping + parameter_explore`；不改物理、gate、actor 输入、动作滤波或执行器限制。
- 修正 `rl_full_retrain_campaign_20261014.py`，使 worker 从 `PROTOCOL.json` 读取实际步数、
  reward variant 和 hyperparameter arm；源码提交为 `9bba6f997a863d0dc9036cae8d7b83526f6d86fc`。
- 本批次只在回报窗口稳定且测试回合同时出现 Task 与 Strict 成功时判定收敛；保留每个 arm 的
  checkpoint、原始 reward/optimizer 日志和失败收据，不按 best-of-test 选点。

## 2026-10-15 10:08 CST — RL 15小时窗口收尾

- 窗口于 `2026-10-15T01:59:34Z` 到期，已在
  `code/mujoco_6d_vmc_benchmark/outputs/rl_full_retrain_20261014_v2/STOP_REQUESTED`
  写入 cooperative stop 收据；两路当前回合均在安全边界完成，之后未继续派发训练。
- `direct_original` 最终为 `status=complete`、196 个完整回合、267404 steps、524810 updates；
  `impedance_original` 为 166 个完整回合、228250 steps、446502 updates。两路
  `Task=0`、`Strict=0`；direct 有 156/196 回合 physical_valid，impedance 有 165/166，
  这不等同于任务成功。
- `admittance_original` 和 `vmc_original` 仅创建了零步初始 checkpoint，均为
  `steps=0, episodes=0, updates=0, stop_requested=true`，没有真实训练交互，不能计为完成。
- 协调器根收据为 `complete_review_required`；四路 acceptance 收据均为
  `failed_preserved`，日志显示冻结测试二进制路径缺失（`.../rl_online_convergence_20261014_v7/construction/rollout.mjb`）。
  未据此宣称成功；本轮没有统一 acceptance 通过，也没有独立物理子步、action/filter replay、
  source/config/checkpoint hash、RMSE、峰值力矩、峰值速度或穿透审计结论。
- 本机两路均保持 3 GiB、禁 swap、单线程，未使用服务器计算；保留全部失败和未完成收据。
  远端网络在本轮仍不可达，不能重新核验 GitHub 最新 SHA；已知缓存为
  `main=32d027966797647ab16496e8b35d05bca498f4d8`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。

## 2026-10-15 09:40 CST — RL监视回合：窗口即将结束

- 已重新核对 `AGENTS.md`、远端 `main=32d027966797647ab16496e8b35d05bca498f4d8` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未新增派发、未改冻结条件。
- campaign、direct、impedance 仍 active。direct 已完成191回合、第192回合在途，最新
  `step=260946`；impedance 已完成162回合、第163回合在途，最新 `step=223264`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 仍不存在，未手动派发。两路继续3GiB上限、禁swap、单线程，无OOM；GPU约43°C、
  2329MiB/16303MiB、利用率约6%。窗口结束时仅收当前回合并停止新派发，保留所有未完成收据；
  不进行统一 acceptance 或独立审计。

## 2026-10-15 09:20 CST — RL监视回合：窗口最后阶段继续收尾

- 已重新核对 `AGENTS.md`、远端 `main=822ef1206e2b3a462b30bb0f45b0b3305dbf9e1f` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未新增派发或修改冻结协议。
- campaign、direct、impedance 仍 active。direct 已完成186回合、第187回合在途，最新
  `step=255028`；impedance 已完成159回合、第160回合在途，最新 `step=218710`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 仍未启动，未手动派发。两路维持3GiB上限、禁swap、单线程，无OOM；GPU约42°C、
  2330MiB/16303MiB、利用率约2%。窗口结束后只收当前在途回合，保留未完成收据，不进行统一
  acceptance或独立审计。

## 2026-10-15 09:00 CST — RL监视回合：最后窗口阶段

- 已重新核对 `AGENTS.md`、远端 `main=bb783688d02d5bd62cfa723f430577a106206d85` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未新增派发、未修改冻结配置。
- campaign、direct、impedance 仍 active。direct 已完成182回合、第183回合在途，最新
  `step=249528`；impedance 已完成155回合、第156回合在途，最新 `step=214348`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 仍未启动，未手动派发。两路仍为3GiB上限、禁swap、单线程，无OOM；GPU约43°C、
  2330MiB/16303MiB、利用率约6%。按窗口协议继续只收当前在途回合，不进行 acceptance 或审计。

## 2026-10-15 08:40 CST — RL监视回合：窗口末期仍有在途回合

- 已重新核对 `AGENTS.md`、远端 `main=d2d55e92739d50f7014d68cc3acb5a43f7810d67` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未启动重复进程或修改冻结条件。
- campaign、direct、impedance 均 active。direct 已完成178回合、第179回合在途，最新
  `step=243625`；impedance 已完成152回合、第153回合在途，最新 `step=209876`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 仍不存在，未手动启动。两路继续3GiB内存上限、禁swap、单线程，未见OOM；
  GPU约43°C、2325MiB/16303MiB、利用率约6%。窗口结束后只收完当前回合，不再新增训练，
  不会把当前训练统计当作 acceptance 成功。

## 2026-10-15 08:20 CST — RL监视回合：窗口末期继续收尾

- 已重新核对 `AGENTS.md`、远端 `main=6bf114c3a52c9e9b3ec884da44040675b1f3f1b5` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未新增派发或改变冻结协议。
- campaign、direct、impedance 均 active。direct 已完成174回合、第175回合在途，最新
  `step=238098`；impedance 已完成149回合、第150回合在途，最新 `step=205411`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 仍不存在，未手动启动。两路仍为3GiB内存上限、禁swap、单线程，未见OOM；
  GPU约43°C、2336MiB/16303MiB、利用率约6%。窗口结束只收完在途回合，不启动新训练；统一
  acceptance和独立审计未开始。

## 2026-10-15 08:00 CST — RL监视回合：窗口末期仍在训练

- 已重新核对 `AGENTS.md`、远端 `main=8ce679ba9fa1c9bea5cf69673b78d7f9210755cd` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未启动重复进程或修改冻结设置。
- campaign、direct、impedance 均 active。direct 已完成170回合、第171回合在途，最新
  `step=233028`；impedance 已完成146回合、第147回合在途，最新 `step=200904`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC 尚未按协调器接续，未手动派发。direct cgroup 已显示约3.0GiB、无可用 swap，
  impedance约2.7GiB；目前未见OOM，GPU约44°C、2338MiB/16303MiB、利用率约6%。窗口结束时
  只收完在途回合并停止新派发；统一 acceptance 和独立审计仍未开始。

## 2026-10-15 07:40 CST — RL监视回合：在途回合持续完成

- 已重新核对 `AGENTS.md`、远端 `main=212533a4caac6004cf1318eea0f452771974ae73` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未改冻结实验条件或启动重复进程。
- campaign、direct、impedance 均 active。direct 已完成167回合、第168回合在途，最新
  `step=228430`；impedance 已完成143回合、第144回合在途，最新 `step=196799`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC worker 仍不存在，未手动派发。两路仍为 `MemoryMax=3GiB`、禁swap、单线程；
  GPU约44°C、2329MiB/16303MiB、利用率约6%，未见OOM。统一 acceptance 与独立审计尚未开始。

## 2026-10-15 07:20 CST — RL监视回合：两路继续推进

- 已重新核对 `AGENTS.md`、远端 `main=f2d77c2c6da823e262ddf4439aa3d0f4885842c4` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未修改冻结环境、gate、actor输入或执行器限制。
- campaign、direct、impedance 均 active。direct 已完成163回合、第164回合在途，最新
  `step=223028`；impedance 已完成140回合、第141回合在途，最新 `step=192619`。已完成回合
  的 Task/Strict 成功数均为0。
- admittance/VMC worker 仍不存在，未手动派发。两路仍为 `MemoryMax=3GiB`、禁swap、单线程；
  direct 当前约2.9GiB、impedance约2.7GiB，未见OOM；GPU约44°C、2329MiB/16303MiB、利用率约2%。
  尚未开始统一 acceptance 或独立物理/action-filter/hash审计。

## 2026-10-15 07:00 CST — RL监视回合：训练仍在安全推进

- 已重新核对 `AGENTS.md` 与远端日志；当前远端为 `main=65890b610d8b98f8a7a3e1f02e060fd767e0f540`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。没有修改冻结环境、gate、actor输入或执行器限制。
- campaign、direct、impedance 均 active，direct 已完成159回合、第160回合在途，最新日志
  `step=217640`；impedance 已完成136回合、第137回合在途，最新 `step=188292`。已完成回合
  的 Task/Strict 成功数仍均为0。
- admittance/VMC worker 仍未出现，未手动启动；两路继续使用 `MemoryMax=3GiB`、禁swap、单线程。
  GPU约44°C、2349MiB/16303MiB、利用率约6%，未见OOM。统一 acceptance、物理子步、action/filter
  replay、hash及RMSE/峰值审计仍未开始。

## 2026-10-15 06:40 CST — RL监视回合：两路继续推进

- 已重新读取 `AGENTS.md`、远端 `main=f7c5fa11f4d065bad50d6b9eeee57ce7cb8f958a` 和
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 的更新日志；未切换分支或修改冻结协议。
- 现有 campaign、direct、impedance 服务均 active。direct 已完成155回合、第156回合在途，
  最新训练日志 `step=212369`；impedance 已完成133回合、第134回合在途，最新
  `step=183710`。两路已完成回合 Task/Strict 成功数均为0。
- admittance/VMC user-systemd worker 仍不存在，未手动启动。两路维持 `MemoryMax=3GiB`、
  `MemorySwapMax=0`、单线程；GPU约44°C、2349MiB/16303MiB、利用率约10%，未见OOM。
  尚未进入统一 acceptance 或独立物理/action-filter/hash审计。

## 2026-10-15 06:22 CST — RL监视回合：两路仍在真实推进

- 重新读取 `AGENTS.md`；GitHub 本轮 fetch 仍因网络不可达，使用已缓存的
  `origin/main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `origin/baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未将缓存冒充实时远端。
- 宿主机只存在登记的 `sii-rl-full-campaign-v2` 及其 direct/impedance user-systemd worker，
  没有重复进程。direct 当前完成至 `episode=152` 后正在第153回合，训练日志约
  `207084` 物理步；impedance 完成至 `episode=130` 后正在第131回合，约 `179542` 物理步。
  两个最后收据仍为在途，尚不能计入完成回合或成功统计；admittance/VMC 目录和服务仍不存在。
- cgroup 仍为每路 `MemoryMax=3GiB`、`MemorySwapMax=0`、单线程；宿主机 GPU 恢复可见，约
  45°C、显存占用约2.3GiB，未见 OOM。未修改冻结环境、gate、actor输入或执行器限制。
- 当前尚无统一 frozen acceptance、独立物理子步/action-filter replay 审计或任何
  `Task=true && Strict=true` 结果；保留所有失败和在途收据，不把 reward/checkpoint 当成功。

## 2026-10-15 06:24 CST — RL监视回合：新回合仍在运行

- 宿主机核对显示登记的 campaign、direct、impedance 服务仍 active；没有 admittance/VMC
  worker，也没有重复启动。最新训练日志为 direct `step=208154`（第153回合在途）、
  impedance `step=180133`（第132回合在途）。此前已完成回合分别为 direct `152`、impedance
  `131`，两路已完成回合的 Task 成功数和 Strict 成功数均为 `0`。
- 资源保持每路 `MemoryMax=3GiB`、禁swap；GPU约45°C、2331MiB/16303MiB、利用率约6%，
  未见 OOM。窗口仍只收既有在途回合，不手动派发其余方法；统一 acceptance 和独立审计仍未开始。

## 2026-10-15 11:59 CST — RL监视回合：direct推进到195k

- 继续核对 v2 收据与 `AGENTS.md`，未新增派发、未重复启动、未修改冻结实验条件。
- direct 已推进至 `interactions=195904, updates=381810`，完成147回合；impedance 完成127回合，
  主状态为 `165000/320002`。Task/Strict均失败；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.92/2.83GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 11:59 CST — RL监视回合：完成回合继续收尾

- 继续核对 v2 收据和 `AGENTS.md`，未新增派发、未重复启动、未修改冻结实验条件。
- 主checkpoint仍为 direct `185904/361810`、impedance `165000/320002`，独立完成回合已增至
  direct 143、impedance 124；Task/Strict均失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.90/2.81GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 11:59 CST — RL监视回合：两路推进到新边界

- 继续核对在途收据和 `AGENTS.md`，未新增派发、未重复启动、未修改冻结实验条件。
- direct 已推进至 `interactions=185904, updates=361810`，完成138回合；impedance 至
  `interactions=165000, updates=320002`，完成121回合。Task/Strict均失败；admittance/VMC
  尚未接续。
- 两worker active/running，MemoryCurrent约2.87/2.79GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 11:39 CST — RL监视回合：在途回合继续完成

- 继续核对 v2 收据与 `AGENTS.md`，未新增派发、未重复启动、未修改冻结实验条件。
- 主checkpoint仍为 direct `175142/340286`、impedance `154000/298002`，独立完成回合已增至
  direct 134、impedance 118；Task/Strict均失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.89/2.69GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 10:39 CST — RL监视回合：两路继续到新边界

- 继续核对收据和 `AGENTS.md`，未新增派发、未重复启动、未修改冻结实验条件。
- direct 已推进至 `interactions=175142, updates=340286`，完成130回合；impedance 至
  `interactions=154000, updates=298002`，完成114回合。Task/Strict均失败；admittance/VMC
  尚未接续。
- 两worker active/running，MemoryCurrent约2.87/2.87GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；尚无统一acceptance或独立物理审计结果。

## 2026-10-15 10:19 CST — RL监视回合：在途回合继续完成

- 当前窗口仍在收尾阶段；继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- 主checkpoint仍为 direct `164142/318286`、impedance `143000/276002`，独立完成回合已增至
  direct 127、impedance 110；Task/Strict均失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.80/2.84GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 09:59 CST — RL监视回合：窗口末期两路仍在训练

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件；15小时窗口进入末期。
- direct 已推进至 `interactions=164142, updates=318286`，完成123回合；impedance 至
  `interactions=143000, updates=276002`，完成107回合。Task/Strict均失败：direct `0/123`、
  impedance `0/107`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.84/2.83GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启。尚无四方法完成、统一acceptance或最终成功结论；窗口结束后
  仅收完在途回合，不新增派发，保留所有失败与未完成收据。

## 2026-10-15 08:59 CST — RL监视回合：完成回合继续增加

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- 主checkpoint仍为 direct `153142/296286`、impedance `132000/254002`，但独立完成回合已增至
  direct 119、impedance 103；Task/Strict均失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.83/2.87GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 07:59 CST — RL监视回合：direct推进到153k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=153142, updates=296286`，完成115回合；impedance 完成100回合，
  主状态为 `132000/254002`。Task/Strict均失败：direct `0/115`、impedance `0/100`；
  admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.76/2.81GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 06:59 CST — RL监视回合：impedance推进到132k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成110回合，主状态为 `142142/274286`；impedance 推进至
  `interactions=132000, updates=254002`，完成97回合。Task/Strict均失败：direct `0/110`、
  impedance `0/97`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.75/2.73GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 05:59 CST — RL监视回合：direct推进到142k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=142142, updates=274286`，完成107回合；impedance 完成94回合，
  主状态为 `121000/232002`。Task/Strict均失败：direct `0/107`、impedance `0/94`；
  admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.72/2.45GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 04:59 CST — RL监视回合：完成回合继续增加

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- 主checkpoint仍为 direct `131142/252286`、impedance `121000/232002`，但独立完成回合已增至
  direct 103、impedance 91；Task/Strict均失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.95/2.79GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 03:59 CST — RL监视回合：impedance推进到121k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成100回合，主状态为 `131142/252286`；impedance 推进至
  `interactions=121000, updates=232002`，完成88回合。Task/Strict均失败：direct `0/100`、
  impedance `0/88`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.74/2.95GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 02:59 CST — RL监视回合：direct接近内存上限

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=131142, updates=252286`，完成96回合；impedance 完成85回合，
  主状态为 `110000/210002`。Task/Strict均失败：direct `0/96`、impedance `0/85`；
  admittance/VMC 尚未接续。
- 两worker active/running；direct MemoryCurrent约3.220GiB、impedance约2.73GiB，均配置
  MemoryMax=3GiB、MemorySwapMax=0，暂未见OOM。direct已接近硬上限，继续观察并保留回合边界，
  不强行重启。GPU查询仍无法连接驱动；统一acceptance和物理审计未开始。

## 2026-10-15 02:39 CST — RL监视回合：impedance推进到110k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成93回合，主状态为 `120142/230286`；impedance 推进至
  `interactions=110000, updates=210002`，完成81回合。Task/Strict均失败：direct `0/93`、
  impedance `0/81`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.76/2.74GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 01:39 CST — RL监视回合：direct推进到120k

- 继续核对 v2 收据和 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=120142, updates=230286`，完成89回合；impedance 完成77回合，
  主状态为 `99000/188002`。Task/Strict均失败：direct `0/89`、impedance `0/77`；
  admittance/VMC 尚未接续。
- 两worker active/running，direct/impedance MemoryCurrent约2.93/2.79GiB，MemoryMax=3GiB、
  禁swap且未见OOM。GPU查询仍无法连接驱动，未重启；统一acceptance与物理审计未开始。

## 2026-10-15 00:59 CST — RL监视回合：impedance推进到99k

- 继续核对 v2 收据和 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成86回合，主状态为 `109142/208286`；impedance 推进至
  `interactions=99000, updates=188002`，完成73回合。Task/Strict均失败：direct `0/86`、
  impedance `0/73`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.79/2.56GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 00:39 CST — RL监视回合：direct推进到109k

- 继续核对 v2 收据和 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=109142, updates=208286`，完成82回合；impedance 完成70回合，
  主状态仍为 `88000/166002`。Task/Strict均失败：direct `0/82`、impedance `0/70`；
  admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.81/2.80GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计未开始。

## 2026-10-15 00:19 CST — RL监视回合：回合收据继续写入

- 当前仍在15小时监视窗口内；核对 v2 收据和 `AGENTS.md`，未重复启动，冻结环境、gate、actor
  输入和执行器限制保持不变。
- 主状态尚未刷新（direct `98142/186286`、impedance `88000/166002`），但独立完成回合已增至
  direct 78、impedance 67；两类 Task/Strict 仍全部失败。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.95/2.87GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启；统一acceptance和独立物理审计尚未开始。

## 2026-10-14 23:39 CST — RL监视回合：两路持续推进

- 合并本时段两次心跳检查，继续核对 v2 收据与 `AGENTS.md`，未重复启动或修改冻结条件。
- direct 已推进至 `interactions=98142, updates=186286`，完成75回合；impedance 至
  `interactions=88000, updates=166002`，完成64回合。Task/Strict均失败：direct `0/75`、
  impedance `0/64`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.82/2.88GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未重启。尚无统一acceptance、最终成功或独立物理审计结论。

## 2026-10-14 22:59 CST — RL监视回合：impedance推进到77k

- 继续核对现有 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成68回合，主状态为 `87142/164286`；impedance 推进至
  `interactions=77000, updates=144002`，完成57回合。Task/Strict均失败：direct `0/68`、
  impedance `0/57`；admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.87/2.72GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未因此重启；统一acceptance与独立物理审计尚未开始。

## 2026-10-14 22:39 CST — RL监视回合：direct推进到87k

- 继续核对 v2 收据与 `AGENTS.md`，未重复启动，冻结实验条件保持不变。
- direct 已推进至 `interactions=87142, updates=164286`，完成65回合；impedance 完成53回合，
  主状态仍为 `66000/122002`。Task/Strict均失败：direct `0/65`、impedance `0/53`；
  admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.75/2.76GiB，MemoryMax=3GiB、禁swap，未见OOM。
  GPU查询仍无法连接驱动，未重启。统一acceptance与独立物理审计尚未开始。

## 2026-10-14 22:19 CST — RL监视回合：impedance推进到66k

- 继续核对 v2 收据和 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已完成61回合，主状态仍为 `76142/142286`；impedance 已推进至
  `interactions=66000, updates=122002`，完成50回合。Task/Strict均失败：direct `0/61`、
  impedance `0/50`。admittance/VMC 尚未生成目录或checkpoint。
- 两worker active/running，MemoryCurrent约2.87/2.79GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍无法连接驱动，未因此重启；统一acceptance与物理审计未开始。

## 2026-10-14 21:59 CST — RL监视回合：direct推进到76k

- 复核现有 v2 收据与 `AGENTS.md`，未重复启动或修改冻结实验条件。
- direct 已推进至 `interactions=76142, updates=142286`，完成57回合；impedance 完成45回合，
  状态为 `55000/100002`。已完成收据 Task/Strict 均失败：direct `0/57`、impedance `0/45`。
  admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.76/2.71GiB，MemoryMax=3GiB、禁swap，未见OOM。
  GPU查询仍无法连接驱动，未据此重启；统一acceptance及物理审计仍未开始。

## 2026-10-14 21:39 CST — RL监视回合：impedance推进到55k

- 继续核对 `AGENTS.md` 与现有 v2 收据；未重复启动，未修改冻结环境、gate、actor输入或执行器限制。
- direct 状态仍为 `65142/120286`，已完成54回合；impedance 推进至
  `interactions=55000, updates=100002`，已完成41回合。Task/Strict均未成功：direct `0/54`、
  impedance `0/41`。admittance/VMC 尚未接续。
- 两worker active/running，MemoryCurrent约2.83/2.88GiB，MemoryMax=3GiB、禁swap、未见OOM。
  GPU查询仍不可用，未重启。尚无冻结checkpoint后的统一acceptance或物理审计结果。

## 2026-10-14 21:19 CST — RL监视回合：direct推进到65k

- 复核远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`；未重复启动，冻结约束不变。
- direct 状态推进至 `interactions=65142, updates=120286`，已完成51回合；impedance 已完成37回合，
  状态仍为 `44000/78002`。已完成收据 Task/Strict 均失败：direct `0/51`、impedance `0/37`。
  admittance/VMC 仍无训练目录或checkpoint。
- 两worker active/running，MemoryCurrent约2.79/2.62GiB，MemoryMax=3GiB、禁swap且未见OOM。
  GPU查询仍不可用，未因此重启；统一acceptance和独立物理审计尚未开始。

## 2026-10-14 20:59 CST — RL监视回合：impedance推进到44k

- 复核远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`；未重复启动，冻结配置不变。
- direct 状态为 `interactions=54142, updates=98286`，已完成47回合；impedance 已推进至
  `interactions=44000, updates=78002`，已完成34回合。两类已完成回合 Task/Strict 均失败：
  direct `0/47`、impedance `0/34`。admittance/VMC 仍无目录或checkpoint。
- 两worker active/running，`MemoryMax=3GiB`、`MemorySwapMax=0`，当前内存约2.90/2.64GiB，
  未见OOM。GPU查询仍无法连接驱动，未重启作业；统一acceptance与独立物理审计未开始。

## 2026-10-14 20:39 CST — RL监视回合：direct继续推进，后两类仍未接续

- 复核远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`；未重复启动或修改任何
  冻结配置。
- direct checkpoint 已推进至 `interactions=54142, updates=98286`，已完成 43 个回合；
  impedance 已完成 30 个回合，主状态仍在 `33000/56002` 边界。两类已完成收据的
  Task/Strict 均为 direct `0/43`、impedance `0/30`。admittance/VMC 尚未派发。
- 两worker active/running，MemoryCurrent约2.77GiB/2.28GiB，MemoryMax=3GiB、禁swap，
  未见OOM。GPU查询仍无法连接驱动；资源读取不影响作业，未重启。统一acceptance、物理子步、
  action/filter replay、hash和正式指标审计仍未开始。

## 2026-10-14 20:19 CST — RL监视回合：训练回合继续写入

- 远端基线仍为 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；重新读取 `AGENTS.md`，未重复启动，
  未改冻结环境、gate、actor输入或执行器限制。
- `sii-rl-full-campaign-v2.service`、direct、impedance 均 active/running。虽然主状态文件仍
  停在 direct 43142/76286、impedance 33000/56002 边界，独立回合收据已推进到 direct 39、
  impedance 27 个完成回合；各有一个 `repair_train` 回合运行中，说明真实worker仍在采样。
- 已完成回合 Task/Strict 仍为 direct `0/39`、impedance `0/27`；admittance/VMC 尚未生成
  训练目录或checkpoint。两worker `MemoryMax=3GiB`、`MemorySwapMax=0`，当前内存约2.85/2.82GiB，
  服务正常且未见OOM。GPU查询仍暂不可用，未据此重启。统一acceptance和最终物理审计尚未开始。

## 2026-10-14 19:59 CST — RL监视回合：两路继续推进，尚未接续后两类

- 复核远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`；heartbeat窗口内未
  重复启动作业，冻结环境、gate、actor输入和执行器限制不变。
- 两个现有worker仍 active/running：direct `interactions=43142, updates=76286`，
  impedance `interactions=33000, updates=56002`。已完成收据 direct 35、impedance 24，
  两类均 `task_success=false` 与 `strict_success=false` 全部为 0；admittance/VMC 尚无
  目录、checkpoint或训练回合。
- 当前两路 cgroup `MemoryMax=3221225472`、`MemorySwapMax=0`，MemoryCurrent分别约
  2.90GiB 与 2.89GiB，服务仍在运行且未见 OOM。`nvidia-smi` 继续无法连接驱动，未据此
  重启；宿主swap已满但worker禁swap。尚未具备统一acceptance或最终成功结论。

## 2026-10-14 19:39 CST — RL监视回合：训练继续，GPU查询暂不可用

- 复核远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`；heartbeat
  `rl-full-acceptance-monitor-15h-20261014` 仍在窗口内，未重复启动或修改作业。
- `sii-rl-full-campaign-v2.service`、direct、impedance 均 active/running。direct 已有
  30 个完成训练收据，impedance 20 个；现有收据 `task_success=false`、
  `strict_success=false` 分别为 30/30 与 20/20。两路都有新的 `repair_train` 回合处于
  running，admittance/VMC 尚未派发，尚无冻结checkpoint或统一acceptance。
- 两个worker仍使用登记的单线程、3GiB、禁swap约束；本轮未见OOM或服务退出。宿主
  `nvidia-smi` 查询暂时报告无法与NVIDIA驱动通信，但不据此重启或宣称训练停止；以服务和
  回合收据为准继续监视。物理子步/action replay/hash审计和四方法统一测试仍未开始。

## 2026-10-14 19:19 CST — RL监视回合：两路worker真实推进

- 再次核对远端 `main=c62ff87823b594e31cca1cebf0c67ac9264a7ef2`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 与 `AGENTS.md`。heartbeat
  `rl-full-acceptance-monitor-15h-20261014` 继续生效，未重复启动任何作业。
- `sii-rl-full-campaign-v2.service`、direct 与 impedance 子服务均为 active/running；
  durable state 分别为 direct `interactions=32142, updates=54286`、impedance
  `interactions=22000, updates=34002`。两路当前训练回合分别为
  `repair_train_025` 与 `repair_train_011`，admittance/VMC 目录尚未生成。
- 已完成且可审计的训练收据为 direct 26 回合、impedance 18 回合；两者
  `task_success=false`、`strict_success=false` 均为 26/26 与 18/18。训练仍在进行，
  没有冻结checkpoint、统一acceptance或方法成功结论。
- 资源核对：direct cgroup `MemoryCurrent≈3.185GiB/3.0GiB`、impedance≈2.69GiB，
  两者 `MemorySwapMax=0`、`OOMKilled` 未见；GPU 43°C、显存约2.3GiB、利用率约6%。
  宿主交换空间已接近满载，但worker cgroup禁swap且仍在推进；继续监视，不强行重启或扩容。
- 本轮未改环境、gate、actor输入、执行器限制或训练预算；失败收据保留。统一四方法
  acceptance、物理子步/action replay/hash审计仍未开始，不能将当前结果写成最终对比。

## 2026-10-14 18:59 CST — 注册15小时RL全量监视

- 按用户授权创建 heartbeat `rl-full-acceptance-monitor-15h-20261014`，窗口至
  2026-10-15 09:59 CST；每20分钟检查 `outputs/rl_full_retrain_20261014_v2` 的四类RL训练、
  checkpoint、execution 收据、资源和失败原因。
- 开工核对：远端 `main=9b01f20f065f829f0bc2b801622b2ea776b9167a`、
  `baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；AGENTS约束已读取。工作区保留既有
  未跟踪 `docs/MEETING_FLOWCHART_IMAGE_PROMPTS.md`，未将其纳入本次变更。
- 当前 v2 仍为 `training`：direct/impedance 的 user-systemd worker 已登记为
  `MemoryMax=3GiB`、禁swap、单线程；admittance/VMC尚未派发，尚无冻结checkpoint、统一
  acceptance 或Task+Strict成功结论。只监视既有作业，不重复启动、不修改环境/gate/actor输入。
- 15小时结束时仅在四方法完成训练并通过同一正式 acceptance 及独立物理审计后报告结果；失败与
  未完成回合保留，不能把reward平台或早期回合写成成功。大产物继续按协议归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/` 独立目录。

## 2026-10-14 17:16 CST — v2 RL 训练已移交持久宿主服务

- v1 中断批次确认停在 direct 6,875 步/5 回合、impedance 6,500 步/4 回合，无 checkpoint；其残留子进程已终止并保留全部收据。
- 新批次 `outputs/rl_full_retrain_20261014_v2` 已由 `sii-rl-full-campaign-v2.service` 启动。direct 与 impedance 两个 worker 已在独立 user-systemd 单元中运行，均显示 `MemoryMax=3221225472`、`MemorySwapMax=0`，GPU 可见；admittance/VMC 将按 pair 接续。
- 当前仍是 from-scratch online 训练，尚无冻结 checkpoint、统一 acceptance 或成功结论。所有训练、环境、gate、输入和执行器限制保持登记协议不变。

## 2026-10-14 18:28 CST — v2 持续监视确认真实推进

- `sii-rl-full-campaign-v2.service`、direct 和 impedance 两个子服务均 active；最近核对 direct 18,250 步/13 回合、impedance 13,250 步/9 回合，均为真实 MuJoCo online 交互和梯度更新。
- 两路 cgroup 仍为 `MemoryMax=3GiB`、`MemorySwapMax=0`，GPU 显存约2.5GiB、温度47°C，无 OOM；尚未达到训练边界，admittance/VMC 尚未派发。

## 2026-10-14 17:10 CST — 训练进程中断，保留并重建宿主机服务

- 检查确认 `rl_full_retrain_20261014_v1` 并非持续运行：direct 在 6,875 步/5 回合、impedance 在 6,500 步/4 回合时随 Codex 沙箱子进程退出，均无 checkpoint，admittance/VMC 尚未开始；两路训练回合 Task/Strict 均为0，不能作为收敛或成功证据。
- 中断批次完整保留为失败收据；没有把未保存的网络状态当作可恢复 checkpoint。GPU 查询显示宿主 RTX 5080 可见，但原服务被沙箱隔离且配置为 CPU，故利用率低。
- 修正 `rl_full_retrain_campaign_20261014.py` 的宿主训练环境为 JAX CUDA；下一批将由 user-systemd 独立服务托管，显式 `MemoryMax=3G`、`MemorySwapMax=0`、单线程，避免对话结束回收训练进程。环境、gate、actor 输入和执行器限制不变。
- 未完成：新的四方法 from-scratch 训练、checkpoint 冻结、统一 acceptance、物理审计和归档。当前不报告任何方法成功。

## 2026-10-14 16:24 CST — 四类 RL 从头在线重训已启动

- 按用户要求登记并启动新的 `outputs/rl_full_retrain_20261014_v1` 批次，四个冻结接口分别为 direct action、impedance parameter、admittance parameter、VMC parameter；每个方法从头在真实 MuJoCo train 条件在线采样和更新，不导入 teacher/BC/离线 replay。
- 固定 formal dt=5e-5、office-v5 几何与摩擦、canonical48 本体输入、原 Task/Strict gate、共用 action filter、执行器幅值/变化率限制；每个方法 500000 交互步上限，完成后才进入同一 `repair_acceptance_000` 测试，Task 与 Strict 同时通过才计成功。
- 已完成并保存 1375 步真实 MuJoCo 预检收据；当前 direct 和 impedance 两路已进入正式 from-scratch 训练，分别使用 CPU1/6、单线程，admittance/VMC 在前两路完成后接续。当前尚无任何方法完成训练或 acceptance，不能报告成功。
- 桌面 Codex 进程继承只读 cgroup（`memory.max=max`），无法冒称 systemd `MemoryMax=3GiB`；新增显式 3 GiB RSS 监视模式，若 cgroup 可写仍强制硬上限，超限请求回合边界停止。服务器不计算。
- 旧 smoke 预检在继承 cgroup 断言处失败并保留为 `failed_preserved`；不计入训练结果。远端 main/baseline 本轮开工核对因 GitHub 网络不可达，使用缓存 main `fffab0a`、baseline `f6e8f8c…`，待网络恢复后同步。
- 新增 `code/mujoco_6d_vmc_benchmark/tools/rl_full_retrain_campaign_20261014.py`；未完成：四方法训练、冻结 checkpoint、统一 acceptance、独立物理子步审计、服务器归档和远端 push。

## 2026-10-14 15:56 CST — online reward平台通过，冻结测试失败

- direct原奖励从22k边界checkpoint真实续训至32633步，新增8个完整回合；最后两个四回合reward窗口均值-21.7636/-21.8681，相对变化0.48%、最后窗口CV0.63%，通过预注册平台门槛。
- 冻结checkpoint在未参与训练的`repair_acceptance_000`完成55秒测试：Task0/Strict0，align阶段，RMSE1003.24mm、峰矩50.719Nm、峰速0.30580m/s、外穿透0.06673mm；actor/公共filter重放0。
- 真实online reward可以达到有限平台稳定，但该平台未产生可用放置策略；不声称RL普遍不适用。

## 2026-10-14 11:32 CST — 首组成对22k开发结果完成，登记旧数据四格补评

- 直接动作原/解耦奖励各22000交互、34002更新；最后checkpoint固定开发Task均0/4、
  Strict均0/4，八回合独立物理指标及actor重放通过。参数阻抗原/物块势函数训练运行中。
  不能把终奖解耦无改进写成RL普遍不适用；完整训练奖励重算正在进行。
- 新增旧离线四格闭环评估工具：同11000步纯RL数据、12002更新，原/新奖励×1/25步回报，
  条件性补评最多16开发回合、0新训练；等待主实验结束，不延长12小时授权。
  与新在线数据/seed分开报告，保留多步离策略偏差限制；编译通过。
- 补评方案7文件/121987字节已hash核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_credit_setup_20261014_v1/evidence/`；
  manifest `a39212c1697e0c7a9405f625cc74df68ec1e45f75b58538dd47421d243909990`。
  首组22k原始数据仍待归档，11k前缀已共享；后续对照/最终归因未完成。
  开工main/baseline SHA见本日首条，未改环境/actor/gate，服务器仅存储。
- 直接动作22k成对快照（32训练回合、八条开发回合）均通过逐步奖励/物理审计，
  2059文件/6446255276字节已发布到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_reward_diagnosis_direct_022k_20261014_v1/evidence/`，
  manifest `9b3fb49a365cdd7f928223dc0de32c627bee6261b8a6096cad537a8e4a2e8910`。
  参数阻抗两臂仍在优化，未提前封存或排名。

## 2026-10-14 14:17 CST — 登记 online 收敛后测试协议

- 根据用户重申，direct/parameter RL 后续必须先在真实 MuJoCo 交互中学习并达到预注册
  reward 平台，再冻结 checkpoint 进入测试；固定22k诊断不满足此条件，保留为机制证据。
- 新增 `code/mujoco_6d_vmc_benchmark/tools/rl_online_convergence_campaign_20261014.py`，
  登记 `outputs/rl_online_convergence_20261014_v1/CONTINUATION_REGISTRATION.json`：从已审计
  22k边界checkpoint纯在线续训，33k–88k分段延长；两臂最近两个四回合窗口均值变化≤5%、
  变异系数≤25%且至少8回合才解锁 acceptance `repair_acceptance_000`。
- 当前协调器等待在途admittance回合自然结束，不重复启动模拟器；未达到收敛不测试、
  不报告模型胜负。服务器仍只存储，未改环境、actor、gate或执行器限制。

## 2026-10-14 15:10 CST — online续训迁移修正，direct有效交互已启动

- v1–v6 continuation启动收据均判定为基础设施兼容失败：没有MuJoCo物理步、梯度更新或
  策略结果；保留失败，不算RL失败。修正了历史根目录、资源字段、`hp`注册、冻结runtime
  路径与磁盘保留字段后，v7 direct原奖励从22k episode-boundary checkpoint合法恢复。
- v7当前真实online交互约30.5k总步、51,002更新、22个完整回合，目标33k边界；每回合都
  在MuJoCo采样并即时更新。reward窗口尚未达到/判定，acceptance仍锁定。
- 旧task_safety checkpoint不能被训练器合法恢复，v7对应启动失败保留；不将其混入原奖励
  收敛结论。后续以合法online链路完成“收敛→冻结→测试”。

## 2026-10-14 10:52 CST — 成对11k原始数据与权重已共享，训练继续

- 两臂共同11000步边界各8完整回合，均Task1/8、Strict0/8，唯一Task成功来自随机预热；
  尚无学习后成功或固定开发评估结论。当前原/新奖励继续向各22000步终点推进。
- 已捕获12条新回合的独立物理子步/奖励重放通过，三个成对预热回合状态/动作完全一致。
  新增仅复制已关闭回合/checkpoint的快照工具，不重启训练、不改写原始执行路径。
- 共同边界16回合、两套checkpoint、源与运行库版本1219文件/2696560250字节已核验共享：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_reward_diagnosis_direct_011k_20261014_v1/evidence/`；
  manifest `c06d9e6a60145f1952b93a4f254e873a9f00c524b2176dc9b278b1da25917bc7`。
  归档hash通过不代替所有回合独立物理审计；余下审计随完整成对实验进行。
- 审计补充初始物块势函数的纯前向运动学核对入口；编译通过，待参数奖励回合实测。
  main/baseline开工SHA与12小时截止不变，未改actor/模型/门槛，服务器仅存储。

## 2026-10-14 10:06 CST — 首个成对预热回合奖励重放通过

- 原/新奖励首回合物理轨迹与actor48/原始动作完全一致，均Task通过/Strict失败；
  折扣回报−11.4082与+2.2892，逐步重算误差均0。仍是随机预热，不是已学习策略的比较。
- 新增只读物理子步/奖励审计和历史优化器/参数局部敏感性探针；保留审计采样对齐错误，
  按live位置与scratch位置相差一个物理子步的实际语义修正，未改训练源。
- 9文件审计检查点已核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_reward_diagnosis_audit_checkpoint_20261014_0206/evidence/`；
  manifest `dd8bcae1ad9d02fc02638ba4e1f325a361ed2decb0ed68ae049e674aef4fd16f`。
  原始新轨迹仍本机运行中、待完整边界归档。两路成对训练继续，未有新闭环排名。
  本轮开工分支SHA及预算见下条；相关源/方案已在main `92dfd88`，baseline未合并。

## 2026-10-14 — 12小时本机RL奖励/在线参数诊断，先发布方案与历史审计

- 开工核对远端main `a08bc203eeee7dfd7a1faffd2409026d1d0f4d69`、baseline
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；本地既有两提交保留，未合并baseline。
- 已完成867条历史训练回合审计：直接动作任务奖励122回合Task7/Strict2；三种在线参数
  各120回合Task0，但均无穿透超限，不能把参数失败归因于Strict阻断终奖。
  参数确实每40ms变化；完整失败回合势函数折扣消项是数学性质，不是公式错误。
- 新增有限诊断工具、物块进度奖励专用遥测和预登记成对实验；两套5项测试通过。
  当前新训练运行中，未有完整成对开发结果，不宣称收敛或RL普遍不适用。
  起止2026-10-14 09:27:15–21:27:15 CST；12小时截止含启动故障，不顺延。
  v1/v2启动失败、v3未训练替代记录保留；v4冻结actor48/物理/执行器/Task/Strict。
- 方案/冻结源码/历史审计629文件已核验共享：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_reward_diagnosis_setup_20261014_v1/evidence/`，
  archive manifest SHA256 `4302bd2ff8a166601b2f3d4ed5df8c6c9dd3a701878c4d20f8338fd55b06ae9d`。
  新训练原始轨迹/checkpoint仍在本机运行，待完成边界归档；服务器未计算。
- 详见 [RL诊断协议与结果](code/mujoco_6d_vmc_benchmark/docs/RL_REWARD_DIAGNOSIS_20261014.md)。
  未完成：成对闭环评估、新轨迹独立奖励/动作/物理审计、最终结论。

## 2026-10-13T22:02:24.287399+00:00 — 公平比较并行调度 parallel_v4_final

- 状态 `complete_review_required`，已评 288/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T21:24:19.225579+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_007

- 状态 `prospective_evaluation`，已评 288/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T19:44:50.831143+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_006

- 状态 `prospective_evaluation`，已评 252/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `pending`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T18:06:10.234058+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_005

- 状态 `prospective_evaluation`，已评 216/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T16:29:16.354323+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_004

- 状态 `prospective_evaluation`，已评 180/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T14:50:05.843925+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_003

- 状态 `prospective_evaluation`，已评 144/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 原版ESN/MLP/RNN三指标统一平滑与实际接触时段

- 按用户要求仅绘制 `esn__original/ordinary_mlp__original/ordinary_rnn__original`，原8开发条件×3方法全部保留。新增benchmark `tools/plot_original_students_smoothed_20261013.py`、报告 `docs/ORIGINAL_THREE_SMOOTHED_CURVES_20261013.md`、首编号PNG及小型来源审计；没有混入matched、新训练模型或棍推修复候选。
- 使用统一居中高斯σ0.20s/截断±0.60s，边缘按可用样本归一化；局部RMSE先平滑20ms误差平方均值再开方，力矩/速度平滑20ms实际物理峰值包络。8张PNG、8页PDF、首图PDF、HTML、接触时刻CSV、未经平滑的指标CSV及原/平滑数值均已保存。平滑压低短时峰值，仅供趋势展示，不替代原始峰值或反应延迟测量。
- 第一编号球接触共同包络2.063–2.225s、人手5.575–10.529s、棍15.650–21.803s；下部逐方法分别标出实际首末跨度及未知凸边/柱子，明确跨度内部有间断、不是累计接触时长。原失败/Task/Strict不变，不把平滑视觉改善当新性能。
- 24/24原始子步/AUDIT/checkpoint hash通过，三指标与原审计一致；有限值/时间间隔/事件边界/常量边缘保持/核对称性检查通过；首末编号PNG目视核对、系统pdfinfo确认8页。Python缺pypdf、打包pdfinfo不兼容GLIBC，已用`/usr/bin/pdfinfo`完成验证。本机1线程/1GiB/禁swap分析5.4s，未启动仿真。
- 已核验服务器源码和全产物：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_three_smoothed_20261013_v1/evidence/`，19文件34610827字节，manifest `b28c07f829e3b2c90459629d55494c6cc04b5d48dc805e81b3e549f4c42d8b7b`，2026-10-13T13:24:56Z发布，父目录含ARCHIVE_VERIFICATION.json。该目录内含绘图脚本/source_curves.json/REPORT.md/execution.json，原物理轨迹仍在既有归档中。
- 使用sii-research-sync核对main `d34cddf67402d43b1e9e7935641a983494dd12a9`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；main最近修复候选未通过，baseline无本轮更新，均未混入本图。已完成本轮绘图/校验/共享；原公平v4服务和worker运行中未重启；未新增训练或公平结论。保留其他agent会议prompt文件。

## 2026-10-13 — 棍推对抗专项：编码器摩擦候选失败，明确物块接触与反向读出

- 新增benchmark电机补偿/运行/测试/比较/读出方向/姿态几何/媒体工具，报告 `docs/ORIGINAL_ESN_ROD_OPPOSITION_20261013.md`。原ESN `acd3b27e…`、旧MJB `586dd7f2…`、输入公式/参数/过滤/事件/gate/执行器/55秒冻结；保留同拍反馈和continuous reference，仅测试实际编码器速度的模型摩擦补偿，系数来自原模型/观测器，没有搜索。
- 原基准近期棍接触采样中名义x−11.813mm/s、过滤ESN+8.152mm/s，存在抵消。冻结策略精确重放显示接触跨度82帧中53帧估计Fx>0、其中10帧原始vx<0；13.72秒记忆及记忆×上下文合计−0.32043，产生−72.991mm/s请求。这些请求并非适配翻号；估计力和瞬时符号不是被动性证明，未排除其他执行因素。
- 唯一新候选55秒Task/Strict=false、仍carry。14.76秒进入carry较基准17.28秒早，RMSE30.846mm、峰矩45.207Nm、峰速0.101871m/s、穿透0.159115mm，但缺失棍—机器人接触，不能以较低x波动宣称修复。没有调整棍时序/位置或采用为默认。
- 纠正中间“提前离开棍子扫掠位置”的推断：25Hz保存姿态有185帧棍—物块接触，首末10.48–16.64秒、采样几何穿透最大0.034866mm。缺失robot接触不等于没有任何rod接触；几何重建不替代物理子步力/时长，未实现末端受推后蹭开的要求。
- 2项补偿方向/边界测试通过；1375步动作/状态/过滤精确重放，1,224,000物理子步三指标/独立穿透、13,750伺服补偿/安全投影/幅值与变化率审计，源码tar/hash核验。完整55s三视角MP4全帧解码及14秒/末帧/曲线目视核对；MP4 `3f0152c6be49c5a35669e58f88bed688cf7d5e8b2b51ebf6240479a3f271773f`。小证据在benchmark `docs/evidence/ORIGINAL_ESN_ROD_OPPOSITION_20261013_{COMPARISON,DIRECTION,GEOMETRY,MEDIA}.json`。
- 已核验服务器：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_rod_opposition_20261013_v1/evidence/`，62文件197480808字节，manifest `bed61d3943697e3ab2a89479be47d9d3f7d2028dd287b7707dc3b01f98dfd4d5`，2026-10-13T13:07:52Z发布。含原始失败/基准输入/源码/命令/模型/协议/审计/媒体，父目录ARCHIVE_VERIFICATION.json，历史执行路径保留。
- 使用sii-research-sync；开工main `021f35fdbaaaad07d40a13d891bb89f95319f03b`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。收工fetch main已由公平协调器推进至 `ee7c6f24d742e66c7dbe17b802d9a3688a0d3c6b`，baseline不变，保留其108/288进度提交与他人会议prompt。本机单线程1.5GiB/渲染1GiB、禁swap，服务器仅存储；lease12:57:39 UTC已thaw，公平作业未重启。
- 已完成本轮有限候选/诊断/共享；运行中原公平比较；未完成旧布局合格棍推和放置。本轮候选不采用、不并入论文结果。若探索重训须另建版本保留旧权重，用独立训练/验收，不能在当前测试回合反复调参冒充泛化。

## 2026-10-13T13:04:09.469771+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_002

- 状态 `prospective_evaluation`，已评 108/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 聚焦棍推：修正反馈系数错拍，但完整任务仍未恢复

- 新增benchmark `tools/feedback_tick_contract_20261013.py`及run/pair/test/analyze/render工具，报告 `docs/ORIGINAL_ESN_ROD_TICK_REPAIR_20261013.md`。冻结原ESN checkpoint `acd3b27e…`、旧场景MJB `586dd7f2…`、输入公式/参数/事件时间/gate/执行器/55秒不变；沿用continuous reference，仅测试公共WBC反馈系数和当前残差同拍。没有储备池重置、摩擦前馈、teacher或新增滤波。
- 发现原direct_esn执行中反馈系数滞后当前残差40ms，13,750伺服步错拍率78.98%、最大差0.16。A记录版与此前完整回合time/qpos/qvel/观测/动作/状态逐值一致；B同步版错拍率与误差归零、合成scale=1保留。原生运行也有该路由，不能称其为迁移独有原因。
- A/B均Task=false、Strict=false。B的12–18秒实际x速度相邻变化RMS15.419→13.638mm/s，但原请求翻转72→115、棍峰力61.774→95.162N；棍后2–6秒局部较平稳，完整任务反而慢，55秒仍carry（A为load_transfer）。B峰矩43.180Nm、峰速0.102859m/s、穿透0.161005mm。没有采用为默认修复或更新公平矩阵。
- A首次棍接触前2秒已47次x请求翻转；离线相同观测的零状态重放最终动作/状态差约1e-8，不支持永久储备池损坏，但不证明闭环重置有效。原生成功002的棍峰力282.148N来自不同路径/姿态，不能直接因果比较。保留负结果，未继续按这一个回合调ESN。
- 一个时序/不重复缩放测试及两次完整集成回合通过审计；每回合1375策略步精确动作/状态/过滤重放、1,224,000物理子步独立指标及穿透审计、13,750真实消费记录、源tar/hash核验。普通/棍近景两份55秒三视角MP4全帧解码通过，另有明确标记的8–23秒原速剪辑；关键帧及曲线目视核对。小证据位于benchmark `docs/evidence/ORIGINAL_ESN_ROD_TICK_REPAIR_20261013_{ANALYSIS,MEDIA}.json`。
- 已核验服务器：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_rod_tick_20261013_v1/evidence/`，84文件375235511字节，manifest `d6ac65a06350c947b81dfa5dbddd161b44eeee0fcbe9b2501eda1dcbc3ce5d6a`，2026-10-13T12:35:53Z发布。包含失败原始回合/源码tar/source工具快照/checkpoint/场景/对照输入/审计/视频；父目录ARCHIVE_VERIFICATION.json，不改历史执行路径。
- 使用sii-research-sync；开工及收工fetch核对main `2b4461a6f746952c45fe86f1a1e6b34104738b9b`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。本机串行单线程1.5GiB仿真/1GiB渲染、禁swap；服务器只存储。派发lease12:29:38 UTC已thaw，原公平作业未重启，保留他人会议prompt。
- 已完成本轮时序修正候选及完整审计/共享；运行中原公平比较；未完成冻结原ESN在旧布局中顺滑、按时的放置。后续公共执行改变须全方法一致重评，不将本轮局部改善宣传为完整修复。

## 2026-10-13 — 固定ESN继续修复杯口/棍推：有限执行层对照未通过，不采用失败方案

- 新增benchmark `tools/`中的payload路径/servo衔接/摩擦前馈独立入口、配套测试/分析/视频工具及 `docs/ORIGINAL_ESN_CUP_ROD_REPAIR_20261013.md`。保持原checkpoint `acd3b27e…`、MJB `586dd7f2…`、actor公式/参数、环境/时序、gate、执行器限制、55秒与正式dt5e-5不变；没有训练或运行时teacher，也没改原公平矩阵。
- 原杯口与物块确有接触：25Hz保存姿态重建162帧，27.68–41.24秒首末跨度13.56秒，不是累计接触时间。复用初始已知地图A*，计入物块半尺寸＋原12mm容差＋2mm间隙；相同起终点延后下降。A（仅路径）、有效B（路径＋40ms内10伺服步衔接）均没有采样物块—杯壁接触，但55秒仍carry、Task/Strict=false。规划避杯不是ESN杯接触柔顺证据。
- A→B的12–18秒实测x速度变化RMS12.566→11.078mm/s，仅改善11.8%；棍峰力60.728→228.149N、结束进度更慢，不能认定整体更好。新增插值首版误读direct_esn中性关节合成scale=1，972/1375反馈终值不符，被审计拦截；完整错误B `path_bridge/episode`保持failed_preserved。修正版从_last_policy_wbc_scale读取反馈系数且不双重缩放，补针对性测试后只重跑一次。
- A30–55秒名义y31.651mm/s、ESN修正+0.222mm/s、反馈系数1，实际仅4.123mm/s，定位公共伺服摩擦/跟踪不足而非ESN相抵。另登记且仅运行一次C：相同路径/衔接，加固定机器人摩擦前馈到原力矩安全投影前。C21.72秒完成搬运，但放置响应失稳，Task/Strict=false、峰矩59.957Nm、峰速0.48770m/s、穿透0.214980mm、杯倾倒、棍接触仅0.2059秒。未采用此方案，没有按失败再调ESN或放宽gate；也不把新前馈称为恢复历史代码。
- 5项测试通过；有效A/B/C均完成1375步动作/储备池/过滤精确重放、1,224,000物理子步与独立穿透审计；B/C记录13,750伺服动作并验证限幅/限速/缩放，C另逐步重放力矩分解与安全投影。四回合源码tar/hash均核对，错误B只保留不计入有效对照。三份完整55s/25fps/1375帧三视角MP4全帧解码和定点目视核对完成；小证据在benchmark `docs/evidence/ORIGINAL_ESN_CUP_ROD_REPAIR_20261013_{COMPARISON,BUNDLE_AUDIT,MEDIA}.json`。
- 已核验服务器：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_payload_bridge_20261013_v1/evidence/`，135文件489128317字节，manifest `d53e6369b434920b9e227d81d65f3e9c1f2097033991ca4044f25e713185cc43`，2026-10-13T12:00:16Z核验发布；父目录ARCHIVE_VERIFICATION.json。含四回合全部原始/失败数据、checkpoint/MJB/源tar与source/tools快照、协议、报告、三份视频；不改历史执行路径。
- 使用sii-research-sync：开工与收工fetch核对main `77dccc20dd06483f5bdb979a0cf0b2b79c02f353`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。本机1线程/1.5GiB串行仿真、1GiB渲染/禁swap，服务器仅存储。两次协调器lease已thaw，原公平服务active/running、未重启。在途worker及他人会议prompt均保留。
- 已完成：本轮有限修复候选、失败归因、审计/完整视频/共享归档。运行中：原公平比较。未完成：冻结原ESN在旧反向搬运布局中顺滑、及时且安全的完整放置；不能称已修好或把本轮候选并入论文胜出结果。

## 2026-10-13 — 固定ESN继续修复：公共位置/速度参考，搬运完成但55秒未释放

- 应用户要求继续修复并解释原好版本为何迁移变差。新增benchmark `tools/continuous_old_office_reference_20261013.py`、run/test工具、`analyze_reference_repair_20261013.py`及 `docs/ORIGINAL_ESN_CONTINUOUS_REFERENCE_20261013.md`。统一生成carry弧长位置与速度前馈，保留原直线路径；60mm/s、12mm、80mm和0.12rad来自既有名义/到点规则，不按回合调ESN。此为新公共参考设计，不假称历史遗漏分支；不改权重/输入公式/增益/过滤/执行器/场景时序/gate，原公平矩阵不采用此实验。
- 原成功002与当前迁移checkpoint相同 `acd3b27e…`；成功002是手侧桌角、−35°姿态/负y路线（carry255.75mm），当前旧杯柱布局是向下姿态/正y路线（425mm）。原27,500训练帧路径y最大0、正y占比0；ESN实际使用该方向×负载特征。是训练覆盖外证据，不证明单一原因；旧8条Task7/8、Strict2/8不改写，也不冒充本轮重跑。
- 预登记1个55秒回合完成：53.68s进入load_transfer，55秒未释放，Task=false/Strict=false。上轮55秒仍carry，本轮走完搬运；原远终点迁移Task=true仍保留，未完全恢复。11.48–16.68s x请求饱和62.31%（原）/3.08%（上轮）/0%（本轮）；实际x速度变化RMS21.54/19.13/14.36mm/s。翻转82次仍存在，30–55s波动较上轮增加，不能称全程消振。20–30s实际y速度2.597→9.811mm/s；峰矩40.351Nm、峰速0.12180m/s、外穿透0.171547mm。RMSE36.240mm仅本轮参考口径，不直接排名。棍累计接触1.4854s，柱/link6接触14.05ms；杯有效，任务未过。
- 两项进度/速度一致性及终端gate测试通过；1375步动作/储备池/过滤精确重放，1,224,000子步指标/独立穿透和真实参考增速/前馈审计通过。原MJB `586dd7f2…`未变。完整55s三视角MP4全帧解码、13秒/末帧目视核验通过；MP4 SHA256 `8e0d08351bb5f2029b84bd38e730c40bf8a986e9bf77d728a557c9a319139824`，小证据在benchmark `docs/evidence/ORIGINAL_ESN_CONTINUOUS_REFERENCE_20261013_{AUDIT,ANALYSIS}.json`。
- 已核验共享：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_continuous_reference_20261013_v1/evidence/`，38文件126190764字节，manifest `3cac99b9a07e4495c40b8a21d65c3692f66a7fc25d857fffe8bbabb62561ba3a`，2026-10-13T11:08:36Z发布；父目录ARCHIVE_VERIFICATION.json。含完整失败轨迹/原始模型与checkpoint/命令与源码tar/source独立文件/协议/审计/视频，未改写本机执行历史。
- 按sii-research-sync核对远端main `06480dd72d2f6ae578cfc7e6d9371b4aca00dcae`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志/AGENTS。本机1线程/仿真1.5GiB/渲染1GiB/禁swap，经内存准入等既有worker自然结束；协调器lease已恢复，原公平服务active/running未重启；服务器只存储，保留他人会议prompt。
- 已完成本轮结构修正、单次验证、审计/视频/归档；运行中原公平比较；未完成旧布局按时放置与全程平稳性。剩余问题不能直接认定实现bug，不用成功筛选/ESN调参/延长时限掩盖。未来公共参考对照须所有方法一致使用。

## 2026-10-13 — 冻结ESN修复公共参考，完整MP4与两次失败保留

- 用户授权修复迁移适配并给MP4，禁止改ESN具体参数。新增benchmark `tools/old_office_waypoint_reference_20261013.py`、执行/对照/测试工具和 `docs/ORIGINAL_ESN_REFERENCE_FIX_20261013.md`；只将旧搬运直线细分为公共局部路点，最终版补齐原部署已有的forward-plane/lateral<80mm回归分支。WBC和actor共用参考，无actor独有输入缩放，无训练/改权重/改增益/改过滤/改环境时序/改gate。
- v1/v2均完整55秒、Task=false/Strict=false，最终v2在carry、cursor18/43。原直达终点Task=true，本次任务退步明确保留。11.48–16.68s x请求饱和62.31%→3.08%，正负翻转100→54；原请求相邻变化RMS降约80.6%，实际x速度变化RMS仅降约11.2%，不称振荡已解决。峰矩42.197Nm、峰速0.24710m/s、外穿透0.171547mm；杯/柱尚未接触，不能据此声称更柔顺。局部目标RMSE34.671mm与原阶段终点RMSE不同口径，不直接排名。
- 两项参考推进/原阶段与释放门槛测试通过；1375步原始动作/储备池/过滤精确重放，1,224,000物理子步三指标复算和独立穿透审计通过。原checkpoint `acd3b27e…`、MJB `586dd7f2…`不变。完整55秒/1375帧/25fps三视角MP4全帧解码通过、13秒/末帧目视核验；最终MP4 SHA256 `fd50e0d80c6553a882c9c0f0c17f3578400211e2185adcc365b138047c7cdb8a`。小证据位于benchmark `docs/evidence/ORIGINAL_ESN_REFERENCE_FIX_20261013_{AUDIT,COMPARISON}.json`。
- 已核验服务器v1：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_reference_fix_20261013_v1/evidence/`，35文件128507071字节，manifest `734979f9f36de33b97b94b5607ef0b7dd5e8029eaa882ed2ec4e714a28cbbc86`；v2同根 `original_esn_reference_fix_20261013_v2/evidence/`，36文件127315143字节，manifest `82ec6761fcdf98e571c88f37a90ba1c04174c0d3c765951b90ca9983fce60368`，2026-10-13T10:40:46Z核验。两者父目录均有ARCHIVE_VERIFICATION.json，含完整失败轨迹/协议/源码快照/视频；v2源码另在evidence/source/，不冒充干净Git快照。
- 按sii-research-sync开工核对main `13b963aa9376f05cd254ca0debf162c536c4a9f7`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志/AGENTS，收工远端仍相同。本机单线程仿真1.5GiB、渲染1GiB、禁swap；服务器仅存储。两次有时限派发lease均已恢复，独立worker未停，原公平服务active/running未重启。保留他人会议prompt。
- 已完成：公共参考修复、两次完整对照/审计/视频/归档。运行中：原公平比较；未完成：旧布局残余波动和按时放置，不能称整体修复成功。不把新参考回合混入原公平矩阵；后续各方法必须共用相同参考协议。

## 2026-10-13T10:06:54.344118+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_001

- 状态 `prospective_evaluation`，已评 72/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 旧场景抽动诊断与冻结ESN迁移契约核查

- 用户要求不改ESN具体参数，排查迁移/适配结构。本轮只读分析，checkpoint `acd3b27e…`、归一化、储备池、读出、输出增益、过滤参数、环境与gate全部未变，无新物理仿真。新增两份报告 `code/mujoco_6d_vmc_benchmark/docs/ORIGINAL_ESN_OLD_OFFICE_CHATTER_20261013.md` 与 `ORIGINAL_ESN_TRANSFER_CONTRACT_20261013.md`，对应tools脚本和docs/evidence小证据。
- 11.48–16.68s中ESN x请求100次正负翻转、62.3%达到±0.32m/s，25Hz序列主要两步交替；89.1%相邻过滤动作达到48mm/s变化率边界。13s名义x约−4mm/s，ESN请求连续+320/−320/+320mm/s。16.72–22.68s五类扰动接触均零，动作仍有56次反向；不能解释成纯粹被棍子顶动。精确代数读出分解将主要放大环节定位到负载×y位置误差项，不将各相关项当独立因果份额。
- 确认迁移参考层不一致：wrapper关闭planned_hand_corner而选择旧PickPlaceTask远阶段终点，原配套PlannedCornerTask使用局部路点。原训练数据SHA `7bb2f7ba…`核验通过，训练y误差最大16.608mm、验证16.327mm，原8条部署最大15.613–16.730mm；旧棍推窗口均值437.677mm，error/.08的y特征100%截断到+4。字段排列一致但参考范围不一致，上一轮只核对48D接口/MJB还不充分；未证明其解释全部振荡，保持权重的参考对照未运行。
- 公共执行/观测器/WBC/动作核心hash和action_filter_config一致，前7关节索引与执行器相关参数逐值一致，25Hz相同。adapter差异仅增加其他contract分发；当前ESN仍走同一路径。Jacobain重建未出现秩切换；其与live缓存wrench最大差0.0003632，首版过严精确重建断言失败已保留，不伪称这部分逐位重放一致。
- 已核验服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_old_office_chatter_20261013_v1/evidence/`（14文件1824405字节，manifest `adbf15d0a6b3f4f6230b27b43514663d8c98f849b79f2f567f03fd508c67f13c`），含图/数值/失败与源码；以及同根 `original_esn_transfer_contract_20261013_v1/evidence/`（4文件19385字节，manifest `03daee8ee4301536115ff711d7e1f041f7f1c073dfe50b60afd14dbf74d04f25`），含契约审计/源码/报告/adapter差异。均有父目录ARCHIVE_VERIFICATION.json。
- 已完成：时序/读出/训练范围/接口审计；运行中：原公平比较服务未重启；未完成：公共参考对齐实现和冻结权重因果对照。后续不得偷偷压缩actor误差或只给ESN添加滤波来改善这条结果；若恢复共同参考，须所有方法一致、新旧实验单列。使用sii-research-sync，本机1线程/1GiB/禁swap，服务器仅文件存储；开工main `74fcd826741bc0b40bd0f031932f2e1880f26665`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留他人会议prompt。

## 2026-10-13 — 当前原ESN跨布局测试：水杯／高柱旧综合环境

- 应用户要求，将当前原checkpoint `acd3b27e…` 直接接入9月28日原MJB `586dd7f2…`；55秒单回合，未训练/调权重/改环境/改gate。当前评估器与名义控制代码，不冒充9月28日整个软件运行时复现，也不混入当前公平矩阵。
- Task=true、Strict=false；43.32s释放、44.32s撤离。阶段目标距离RMSE217.945mm、峰矩49.842Nm、峰速0.39397m/s。旧任务RMSE包含到阶段终点的搬运距离，不能与新版规划路点RMSE直接排名。Strict三项失败：外穿透0.277821mm>0.2mm；杯倾倒92.048°/位移142.798mm；棍累计接触0.02985s不足0.4s。
- 完成1375步动作/储备池/过滤精确重放、1,224,000物理子步三指标复算与独立穿透核对、运行源码tar/checkpoint/model hash审计。首个尝试在物理开始前XML导出初始化失败；完整回合后审计因旧JSON缺字段失败，均保留。只补做audit-only，`AUDIT_RECOVERY.json`绑定原failed execution与新审计源码，没有重跑物理或改写历史失败。
- 完整55s/1375帧/25fps三视角MP4全帧解码通过，24s/55s目视核对；MP4 SHA256 `1f6e4cfc1c943755c3f30c83305f4ccaea1600d5e818391b037354eac205f8d1`。报告 `code/mujoco_6d_vmc_benchmark/docs/ORIGINAL_ESN_OLD_OFFICE_TRANSFER_20261013.md`，小证据在同级 `evidence/ORIGINAL_ESN_OLD_OFFICE_TRANSFER_20261013.json`。
- 已逐文件核验并发布至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_old_office_transfer_20261013_v1/evidence/`，核验时间08:36:08 UTC。manifest `9c736257a15b5be44551dbf85f2a19ecddc4b0892199824d3e3853ad8b47eaf7`，45文件226138489字节，含两次失败/恢复、完整轨迹、原场景、视频与源码；父目录保留 `ARCHIVE_VERIFICATION.json`。
- 使用sii-research-sync；开工main `5a63bd74e94b2a21b4db08160e4eb474eac3ec7b`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；运行时base main已由公平作业正常推进至 `02e3e289b02a561f1e6c0ac5abddb143612369e0`。本机单线程/1.5GiB仿真、1GiB分析渲染、禁swap，服务器仅存储。为安全准入短暂冻结协调器派发的两次lease均已thaw；独立在途worker未停止，原公平服务active/running且未重启。保留他人会议prompt。
- 已完成：此次冻结权重单回合、审计恢复、视频、共享归档核验；运行中：原公平比较；未完成：跨布局统计成功率及接触质量改进。本次不声称ESN全面泛化或优于baseline。

## 2026-10-13T07:55:05.248843+00:00 — 公平比较并行调度 parallel_v4_parallel_condition_prospective_20261013_acceptance_000

- 状态 `prospective_evaluation`，已评 36/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 原ESN残差链路诊断与002完整视频

- 用户要求先检查根本问题、观察另一条件，暂不修改算法。新增 `code/mujoco_6d_vmc_benchmark/docs/ORIGINAL_ESN_ALGORITHM_REVIEW_20261013.md` 和只读诊断脚本 `tools/review_original_esn_residual_20261013.py`（benchmark内）。全部8条原ESN轨迹的动作/128维状态/公共过滤器精确重放一致，输入与源码hash核对，零负载从reset输出为零、未读取字段扰动不改变输出。相同实现重放不是独立控制理论证明。
- 001的25.48–30.20s窗口：上抬请求/过滤后均值均31.720mm/s，z过滤差<2e-15mm/s，最大请求仅为320mm/s上限的17.162%；名义比例仍94.376%。不支持“残差硬上限太小”，也不据此贸然扩大动作。003有22.56s同路点驻留并最终任务失败，说明脱困局限不只存在于成功案例。保留全部Task7/8、Strict2/8及安全失败。
- 按编号顺延选择002（查看成绩前确定），相同冻结几何、不同扰动；完整55s/1375帧/25fps三视角MP4，保存MJB和状态重渲染，无新物理仿真。34.80s开始释放、35.32s撤离；Task=true/Strict=false，RMSE28.050mm/峰矩51.253Nm/峰速0.36975m/s，柱/link7最大穿透0.550130mm。顶部穿透是整回合最大值。全帧解码、18s/35s目视验证通过。
- 按sii-research-sync归档并逐文件核验18文件：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_algorithm_review_20261013_v1/`，含analysis/REVIEW.json/execution.json、media、诊断/渲染源码与四个冻结重放源码。REVIEW SHA256 `27d156bcf128c0daa89b59fff48445a340a508cf539eada3ac025b8298cc7f3f`；MP4 `3e0c6c5eed564b81b1e046cdf65e2f8e277e8445bf9f9f7f7f53b67af5cf7b30`；报告 `79e812818abdd95b27318c9580cad2e7f1544e7ea6a02f1bcac99c03dd830fdc`。
- 开工核对main `3ef9208c0325da2aba70067cdf0c75f182314106`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志/AGENTS。完成静态检查/历史重放/视频/归档；原公平比较服务PID1775739保持运行，未重启；闭环稳定性/恢复改进消融/新公平矩阵未完成。只本机计算，渲染1线程/1GiB/禁swap；服务器仅存储；保留他人会议prompt。

## 2026-10-13 — 原 ESN 完成任务但 Strict 未通过的三视角视频

- 用户请求观看执行MP4；取当前8条件中编号最前的Task成功/Strict失败原ESN回合 `repair_development_001`，用于说明两种判据的区别，并非随机抽样或整体成功率证据。原checkpoint `acd3b27e…`；Task=true、Strict=false，最大外穿透0.380594mm（柱/link7），49.08s释放、49.88s撤离；原门槛不变。
- 本地复用已保存qpos/qvel/ctrl/mocap和MJB，只做mj_forward渲染，无重新物理积分/策略执行。使用现有 `tools/render_office_threeview_20260929.py`，stride1/fps25/gif-stride5；原速55秒、1375帧、1920×560、overview/end-effector/pillar-corner三视角。单线程库/编码器、CPUQuota100%/MemoryMax1GiB/Swap0，服务正常结束，原公平比较未重启。
- 验证：源轨迹 `81a8efb51968b131f5db64aa409bd41d208c85d44696374f6c26b62bc1c5d3e5`、MJB `d4c28e40…`、原模型hash一致；视频全帧解码及55秒/1375帧检查通过；18s棍推和55s末帧三视角目视核对；输入hash未变。顶部穿透数值为整回合最大值，不是当前帧穿透。
- 已核验服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_media_20261013_001/`，含MP4/GIF、两帧、manifest及实际renderer源码，6文件hash与本地一致；MP4 SHA256 `138db2a77c791732dc25aebdd02c7dbd6f8cc0d4c8a69039a2ab04a518a3f638`，manifest `1e0347ffb36dab9d480d7093031ebaad4d88872b32d4dc4400e1c7e2fe2f2d0b`。本地播放缓存为benchmark下 `outputs/original_esn_media_20261013_001/replay_threeview.mp4`。
- 开工核对main `d703f57bf487fbe7cb67f20cacfcf3649b7e496e`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两分支日志，按sii-research-sync/AGENTS发布；保留他人会议prompt。完成视频与归档，原ESN安全约束不足仍保留，新公平比较仍未完成。

## 2026-10-13 — 原 ESN 组会汇报稿与训练谱系核验

- 新增 `code/mujoco_6d_vmc_benchmark/docs/ORIGINAL_ESN_GROUP_MEETING_20261013.md`：八页讲述提纲、两分钟口述稿、teacher来源/资格筛选、真实训练配置、全过程曲线讲解及全部21旧配置表。历史24条留出与当前8条开发复测分开，新ESN/新RNN仅作明确标注的进展对照。
- 锁定原ESN `readout_refit_esn_2026100301`，checkpoint `acd3b27e…`；真实数据20训练/5验证、27,500/6,875帧，仅训练3,780个线性读出系数。监督标签是实际执行历史中的原始teacher请求，不是执行力矩；无contextual leak gate、无时序损失项。明确增强teacher的人工恢复先验，以及旧MLP/无记忆家族选中模型数据版本不同。
- 当前原ESN Task7/8、Strict2/8，人手冲量相对同数据普通RNN低57.5%；matched RNN接触表现相近且Strict更高。保留柱/link6、link7穿透失败与峰矩不全面领先，不把历史24条件的20/24、16/24同当前结果混合。
- 验证：21行三指标/Task/Strict/早停与已审计report逐值核对，5行接触表核对，文档链接/模型与数据hash/训练字段检查通过；服务器模型、训练metadata、数据和历史24条报告hash重新确认。无训练或新仿真。
- 已核验服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/original_esn_group_meeting_20261013_1458/`，报告及3个小证据文件SHA一致；报告SHA256 `e09771ae9d3d3bf4ebcdeb9c63c779bc382d757706b3d2348277e0125915a26a`。实际训练源码快照仍在报告列出的原模型目录，未修改实验。
- 完成：汇报整理/核验/归档。运行中：本机既有 `sii-fair-parallel-20261013-v4.service`，14:54快照21/288，未重启；未完成：该批全矩阵与最终审计。本轮不取其局部成绩作排名。开工main `7e1a384379af82a45ecd3300f192bb36793ceb21`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按sii-research-sync/AGENTS发布，保留他人会议流程图prompt。

## 2026-10-13 14:27 CST — 26配置全过程曲线已完成并共享

- 按用户请求，用已审计208条轨迹绘制所有原/新学生、经典6配置、RL7配置及参考的全过程RMSE/实际力矩/末端速度。8条件×4组共32页PDF及32张PNG；交互HTML可选方法/条件/时间范围/误差定义，完整CSV.gz保留全部失败。原/新版本不混合，不使用未完成前瞻性结果。
- 原始子步hash、回合审计hash、208条整回合三指标复算和累计RMSE末点核验通过；2项数值测试通过，3组PNG目视/PDF32页/浏览器方法切换与缩放验证。滚动窗口0.20秒；力矩/速度每20ms保留子步峰值；8条早停不补零。
- 已核验服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/full_task_curves_20261013_v2/evidence/`，43文件183820146字节，manifest `6dcfcb90e1822b4c1ad8183786a4800c232af090b1ac8e4161eda1501e9b5aae`，含实际绘图源码。报告 `code/mujoco_6d_vmc_benchmark/docs/FULL_TASK_CURVES_20261013.md`，Git保留4张第一编号预览，大图册/数值留服务器。
- 只读分析在本机1线程/1GiB内完成，没有新仿真或修改环境。首版对无接触事件字段的兼容失败已修复并保留收据；本轮不将曲线形状等同柔顺性排名。
- 完成：全部曲线、数值核验、浏览器检查与服务器归档。运行中：原公平批次14/288（14:26观察），未重启，在途阻抗/MLP两路；未完成：该批完整矩阵/最终审计。默认预览条件000恰为新RNN失败条件，明确公开其全8条件7/8仍高于新ESN5/8，避免单图误导。

- 开工核对main `cbcf37400985d7dced58c5836d5f392178d6b600`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两分支日志/AGENTS；使用sii-research-sync归档发布和browser技能验交互页。保留他人会议prompt。

## 2026-10-13 13:45 CST — 已核实两路独立评估同时运行

- 已完成39/39拟合、36个模型/配置锁定、3/288回合及逐回合审计；两路实际在途为导纳boundary_07与ESN-gradient seed2026101303，分别CPU1/6，实测99.9%/99.7%单核CPU。不是仅登记并行上限。
- 完整导纳回合内核峰值1,024,077,824字节，按预登记规则后续同类上限2GiB；神经worker2.25GiB。两路均禁swap，内存超限/oom/oom_kill计数0；仍按剩余硬上限预留增长空间并保留0.75GiB。最多4路是上限，当前只证实2路；完整吞吐加速倍数尚未测得。
- 运行中：本机一次性`dispatch_v4`服务推进原288回合，固定环境/原门槛/模型/源/seed/dt5e-5不变；服务器不计算。未完成：完整统一矩阵、最终独立审计与配对统计，不提前作方法排名。
- 两路实测证据已核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/fair_parallel_resource_20261013_054540/FAIR_PARALLEL_RESOURCE_20261013.json`，SHA256 `d90a1893e6ca6538398cd84ebb559a21902f062e72df89432b1df7b2d472e990`；仓库小证据在`docs/evidence/FAIR_PARALLEL_RESOURCE_20261013.json`（benchmark内）。
- 全部训练与冻结源/调度器快照已核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/fair_comparison_20261013_v2_parallel_v4_models_locked/evidence/`，967文件220706579字节，manifest `bf11f955fc69c2c6cdafb2ee9b6fb5e129413728166319c42e73f40923fc8465`。该快照含前2条结果，后续轨迹仍由运行服务分阶段归档。

- 本轮开工main `06ac5565a33bbffc2c6d742e6876e025a339ee74`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；收工前再次核对远端main `b3813d0b2d5f46fadf8fd144f6f34c77271250b8`、baseline未变，读取最新日志与AGENTS。资源代码10项测试通过；未改动他人会议prompt。

## 2026-10-13T05:38:48.661112+00:00 — 公平比较并行调度 parallel_v4_models_locked

- 状态 `models_locked`，已评 2/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13T05:38:02.855602+00:00 — 公平比较并行调度 parallel_final

- 状态 `failed_preserved`，已评 2/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 完整回合内存实测后细化并发档位

- 39/39拟合已完成、36模型锁定；新调度器/模型快照已经服务器核验，`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/fair_comparison_20261013_v2_parallel_models_locked/evidence/`，956文件220632399字节，manifest `e8af933b29e2698f5569346dc3812d630402a5a8b6627d600fa4ed626c78eb59`。
- 第一个原计划完整回合的内核峰值1159131136字节；粗分档导致2倍峰值需要2.16GiB却分配3GiB，实际无法开第二路。新增dispatch_v4采用0.25GiB档位、神经worker2.25GiB，仍保留2倍峰值和所有在途硬限剩余空间/0.75GiB余量。
- 其他类别初始3GiB，完整回合后依类别最大已测峰值同规则调整；短回合不降低上限。旧在途回合正常完成再交接，所有39拟合/已完成回合/pilot复用。保持实验/模型/原截止、只本机计算；不是按成功率调整资源。10项测试再次通过。
- 已完成代码、内存实测、模型锁定与服务器核验；v4等待边界交接/后续并行评估，最终288行和独立审计未完成。不能把注册4路上限写成已实测4路吞吐。

## 2026-10-13T05:22:05.556660+00:00 — 公平比较并行调度 parallel_models_locked

- 状态 `models_locked`，已评 0/288；资源调整不改实验/模型/门槛，旧封存集未读。
- 归档 `verified`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。


## 2026-10-13 — 按用户授权加速公平比较，复用31拟合并引入动态并行

- 开工核对main `06ac5565a33bbffc2c6d742e6876e025a339ee74`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两分支日志/AGENTS；本机24核、16GiB RAM，可用约4.6GiB（有一个训练进程），swap已满。GPU约6%，主要瓶颈是单核MuJoCo及可用RAM。
- 已实现并启用资源调度补充，最多4核/4独立回合；完整回合内核内存峰值决定神经worker1.5/2/3GiB硬限，经典/RL3GiB；保留运行作业的未来内存增长和0.75GiB余量，禁swap。只本机计算，服务器仅归档。
- 原协调器在子作业边界停止并归档，31个已完成拟合复用，新协调器已接续第32拟合；这不是重训或更换实验。原source/39拟合/288回合/模型选择/门槛/条件/截止时间不变。原服务的预期Stop异常保留，不能误读为物理失败。
- 新脚本 `code/mujoco_6d_vmc_benchmark/tools/parallel_fair_comparison_20261013.py`、资源边界测试和协议补充；10项测试通过，实际systemd退出后内存峰值记录验证通过。
- 当前运行中：剩余拟合、首个内存测量回合、之后多路评估；实际可同时开几路等待内存实测。已完成训练未丢弃；最终表/审计未完成。服务器最新核验入口由FAIR_COMPARISON_LIVE记录，不把调度上限冒充实测加速倍数。

## 2026-10-13T05:15:46.986128+00:00 — 公平性修正 final

- 状态 `failed_preserved`，新条件已评 0/288；39拟合/3seed，旧封存集未读。
- 归档 `verified`，详情 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。失败保留；不能在完整审计前宣称胜出或所有baseline充分收敛。


## 2026-10-13T04:51:08.632476+00:00 — 公平性修正 setup

- 状态 `training`，新条件已评 0/288；39拟合/3seed，旧封存集未读。
- 归档 `verified`，详情 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。失败保留；不能在完整审计前宣称胜出或所有baseline充分收敛。


## 2026-10-13 — 公平性修正：共同训练机制与前瞻性全方法验收

- 核对远端main `0fffa8560d45be84ab7da036d1eb7c976ba3dfca`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；读AGENTS/sync skill。本机与服务器无重复研究作业，旧15小时任务不延长。
- 新训练器统一ESN/RNN/MLP的真实数据、特征/时间尺度/读出、随机初始化、Adam损失/预算/选择机会；解析ESN和从其微调RNN单列，保留update0并报告实际权重更新。6项测试通过：梯度/实际参数更新、导出重放、字段隔离、零负载、身份切分、全seed选择。
- 固定39拟合、3seed；冻结全部模型后在原范围8个新身份统一重评新学生120回合与全部旧21配置168回合。保留经典6候选和RL7配置，不换环境/gate、不解封旧保留集、不用服务器算力。
- 协议 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_PROTOCOL_20261013.md`；本机run `outputs/fair_comparison_20261013_v2/`，服务器状态另由实时报告记载。v1仅准备未执行，保留说明。
- 已完成代码/测试/预登记；新训练、288闭环与审计待完成。相同神经元不等于相同可训练参数，RL训练来源不同；不宣称已消除一切差异、ESN必胜或所有baseline充分收敛。

## 2026-10-13 12:27 CST — 持续监视至结果、审计、归档全部完成

- 本轮实际查询/fetch main `e82ba274bbe86928b25484596cd577381c8bd3d7` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读更新日志/AGENTS和sync skill；监视未重启仿真。12:06学生40/40与独立审计完成，12:25:44最终归档核验通过，自动报告push `c9efbae3c524224cccb42d8b7445619c0e0cf4e4`。
- 既有baseline168行及新增学生40行全部审计passed；新增26配置统一表 `code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_COMPLETE_COMPARISON_20261013.md`，逐行与两份审计锁定报告hash/数值核对，不混选新旧最优值。未动他人会议prompt。
- 新ESN Task5/8、Strict3/8、RMSE33.973mm/平均回合峰矩49.684Nm/平均回合峰速.3745m/s；ordinary RNN7/8、5/8、35.278/51.403/.3675。ESN部分接触指标较低，但成功率不领先，不能声称全面优于RNN。matched RNN均选回update0父ESN，闭环完全相同，不能充当独立训练有效的RNN对照。
- 数据44train/11validation、75625实际帧，teacher mixture；旧ESN7/8、2/8到新5/8、3/8并非单因素数据量消融。三seed离线，首预登记seed闭环，仅8开发身份；最终盲测泛化/所有baseline收敛/ESN全面优越均未完成或未获支持。
- 已核验服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_student_15h_20261012_v3_final/evidence/`，3994文件15416918386字节，manifest `4f7ce4dca8d98b3a713616aca0d418da5cfba5eb7c05bc0d606b65700ab3aec4`。baseline原始168条另在同根 `teacher_student_15h_20261012_v3_baseline_complete/evidence/`，6118文件24535685543字节。
- 所有本批仿真/学习/审计已结束，无追加训练或服务器计算；统一表补入GitHub，过夜窗口不延长。

## 2026-10-13T04:25:46.077489+00:00 — 15小时teacher/student接续：final

- 实际状态 `complete_review_required`；baseline审计：True。
- 归档状态 `verified`；详情见 `code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_LIVE_20261012.md`。
- 单模拟器/1线程/3GiB，只本机计算；不改环境/gate、不解封保留条件，失败均保留。

## 2026-10-13T00:01:28.831803+00:00 — 15小时teacher/student接续：teacher_data_complete

- 实际状态 `collecting`；baseline审计：True。
- 归档状态 `verified`；详情见 `code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_LIVE_20261012.md`。
- 单模拟器/1线程/3GiB，只本机计算；不改环境/gate、不解封保留条件，失败均保留。

## 2026-10-12T18:17:49.874143+00:00 — 15小时teacher/student接续：baseline_complete

- 实际状态 `baseline_final_audit`；baseline审计：True。
- 归档状态 `verified`；详情见 `code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_LIVE_20261012.md`。
- 单模拟器/1线程/3GiB，只本机计算；不改环境/gate、不解封保留条件，失败均保留。

## 2026-10-12 21:45 CST — 启动先baseline后teacher/student的15小时一次性任务

- 开工核对远端main `e6d63c84eb84e0b326597131e1ab4f9ebfe9684e`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读两分支日志/AGENTS/sii-research-sync。保留他人会议prompt，服务器只存储、不训练、不改显示。
- 原统一baseline继续，启动时123/168已复算。新增`tools/teacher_student_15h_20261012.py`一次性服务，真实waiting_for_baseline、零新仿真/拟合；检查PID1676275只持自己的单例锁，原PID1649757仍持全局锁。168完整行与独立审计passed是teacher采集硬前置。
- 15小时从用户授权21:28算至明日12:28；6teacher候选×2训练身份、最多80新采集，07:58截止采集以留4.5小时重训/比较。原环境/gate/本体输入/执行限制不变，不读封存条件；失败和未派发身份记账，数量上限不冒充采集完成。
- 现有合格refined数据20train/5validation。本轮新数据与历史真实轨迹统一供三seed ESN、ordinary/matched MLP/RNN学习，固定首seed五族各8开发身份闭环。记录可训练参数/固定存储与不等训练成本；不预设ESN优势、不以拟合MSE冒充任务成功。新旧teacher不同则披露混合，非纯样本量消融。
- v1准备缺历史conditions缓存，v2导入发现仿真环境无torch；两者0仿真/拟合保留。v3使用hash核对的历史公共条件、单独现有PyTorch拟合解释器；16项回归与冻结导入通过。运行worker1线程/3GiB/禁swap，协调器1GiB，非定时任务、不自动盲重启。
- 设置/源码/历史数据603文件、24327306字节已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_student_setup_20261012_v3/evidence/`，manifest `6b95404ace71424690d410c73cab63e17df518c4ee7d66b7d4f3c3b404cf7748`。不含尚未产生的新结果；之后baseline/data/final边界归档并核验，自动更新报告/日志安全push，失败标pending。
- 详见`code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_20261012.md`。已完成登记/测试/服务启动/设置归档；运行中baseline及等待协调器；未完成新采集、训练和闭环，不称投稿级公平性或泛化验收。

## 2026-10-12 19:50 CST — 七组RL开发评估闭合，统一比较开始ESN实测

- 开工核对远端main `4007ea3d5ccd867c7949f5b7bdf6d563f3a22bbd`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两分支日志/AGENTS；用户要求持续盯至出结果。保留原稳定作业，只本机计算，无新训练预算、定时任务或服务器实验。
- 最后历史熵RL调阻抗18:54:41训练按165000步预算结束（320002更新），19:45:29完成八条件审计；Task/Strict0/8，全部55秒，均值23.795402mm/37.541461Nm/.379347m/s。七组共56条均任务失败；实际步数与早停保留，不称收敛。
- 配对队列正常取得释放后的全局锁，19:48:29已从原始子步复算全部104条经典/RL轨迹；已启动ESN第000条件。21配置×8条件完整表尚未完成，未混入旧24条件或CPU探针。
- 新增独立收尾工具`tools/audit_local_paired_comparison_20261012.py`，检查完整方法/条件网格、冻结源码和checkpoint、原始子步/动作链hash、动作/状态重放以及报告聚合；它不运行物理、不读封存条件、不修改执行中的冻结源码。新增3项检查与已有7项回归共10项通过，最终168条审计仍待批次完成。
- 原设置归档仍为`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paired_baseline_setup_20261012_v2/evidence/`；服务器仅检查存储空间，未使用算力。新结果/收尾工具当前仅本地，完整批次结束后单独核验归档，不能把旧设置包说成新结果备份。
- 已完成：七组RL和104条复算；运行中：64条冻结参考模型闭环；待完成：全表、独立收尾审计、结果归档及后续最终泛化验证。任务失败不是实现错误的充分证据，也不是ESN已优于所有baseline的证据。

## 2026-10-12 晚 — 接续baseline，登记与proposed的同八条件比较

- 开工实际fetch/读取main `55c53fb871c26ae8717d4b730aa22fded31bcd1b`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS。沙箱网络/systemd受限后在宿主机核对正常，不再把沙箱不可见当服务器/GPU故障。仅本机计算，未动服务器显示/训练，保留其他agent未跟踪会议prompt。
- 18:12 CST历史熵RL调阻抗已155000步/300002更新/112回合、checkpoint152625；原训练/监视/汇总保持运行。已有六配置仍各Task/Strict0/8，最后节点尚待165k及8条件审计，没有追加训练预算或伪称收敛。
- 新 `tools/compare_local_baselines_20261012.py` 冻结同一八development条件，复用7RL×8与经典三类各两候选×8，补跑ESN、matched/ordinary RNN/MLP、memoryless、teacher、zero共64新回合；总168行、21配置覆盖原16方法族及附组。旧24测试分数不拼入新8条件表，封存条件不读。
- 一次性服务 `sii-paired-baseline-comparison-20261012-v2` 18:12:52实际active，当前waiting_for_rl、新增物理0。等旧任务成功闭合后再拿全局锁，前置失败则停止；单模拟器/单线程/3GiB/禁swap、子任务30分钟上限，14小时有限派发保护。v1仅prepare未派发，保留；原环境/gate/actor/执行器限制不变。
- 7项回归通过（条件身份/前置失败/真实flock交接/pending/早停），冻结副本导入和六学生48D→7D重置推理通过。已有完整RL轨迹110万子步及接触指标复算通过。新表另报告接触P95/冲量/恢复及删失，保留所有失败，不为低指标挑回合。
- 设置与冻结源码/权重606文件、6423779字节已核验到`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paired_baseline_setup_20261012_v2/evidence/`，manifest `3440a74deb080156a558814913904d5760b10e51f81d6921a58a45eb4da2546c`。代码在`source/`，权重在`checkpoints/`；大轨迹未包含，未来结果未提前宣称已上传。
- 新增 `docs/BASELINE_PAIRED_DEVELOPMENT_20261012.md`，同步联合进度和周报。已完成登记/预检/服务启动；运行中旧RL与新等待队列；待完成64闭环、统一独立复算与之后最终24条件比较。当前不是完整最终矩阵或可投稿验收结论。

## 2026-10-12 — 补齐RL最后一个165k节点，保留CPU兼容性探针与诊断纠正

- 14:09:42首条新CUDA训练回合完整55秒落盘，已99000步/188002次更新，新增2750条有限优化器记录；110万物理子步独立复算、模型/轨迹/动作一致性通过，Task/Strict失败保留，已进入下一回合。首回合小包已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_completion_first_episode_20261012/evidence/`，3文件15390字节，manifest `3d2cee03550fa967471b0a856319db6c86245d72936fd0afd93fcdf30c7c7e59`。这是实训恢复证据，不是新的冻结策略开发成功率。

- 已在宿主机fetch并读main `8de2df9d5c5b23a7803d0b7f375f3d1427de4abc`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`和AGENTS。用户授权继续；只在本机计算，不动服务器显示或算力，不建定时任务，保留未跟踪会议prompt。
- 上轮六个完整CUDA节点已各8条件审计Task/Strict 0/8；最后一组历史熵调阻抗在截止后保存97625步。前五组完整55秒，直接RL历史熵配置八条均穿透早停，不能把其低峰速当优势；原failed_preserved收据保留。
- 本轮曾把沙箱GPU不可见误判为驱动故障，宿主机实查RTX5080正常，现予纠正。CPU兼容恢复后的97625步八条件试跑完整55秒，Task/Strict0/8，均值22.819469mm/36.279807Nm/.378260m/s，880万物理子步复算通过；只作为兼容探针，不冒称165k或并入CUDA主表。初期bus/加载/cgroup/相对路径失败均未进入物理仿真，收据缺陷如实披露。
- CPU恢复改动两份源码已单独快照，原runtime随后按全清单恢复；CUDA对保存观测重放最大差7.1032e-6，归一化hash和checkpoint不变，不声称跨设备闭环等价。新增CPU物理审计/跨设备动作审计工具与独立单节点接续工具。
- 新`completion_20261012_v1`在14:02:50启动，14:05已实训98000步/186002次更新；单模拟器1线程/3GiB/禁swap，从97625接165k后自动八条件审计及七配置汇总，原六组不重跑。12小时安全派发截止至10月13日02:01:42；运行中，尚无新165k开发成绩。3项新协调器、8项监视/汇总、6项停止规则检查通过，源副本独立import通过。
- 已核验小包 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_completion_setup_20261012/evidence/`，609文件5340373字节，manifest `160425ee4230959cd901d21500cec61cbbdf0db42bb93a3bf5f39639e23fecd5`。含冻结source、注册、六组旧审计、CPU探针源码/审计/重放与runtime恢复证明；大型raw/checkpoint仍本地。详情见`code/mujoco_6d_vmc_benchmark/docs/RL_NODE_COMPLETION_20261012.md`。


## 2026-10-11 晚 — 保留在途两路，启动一次性过夜结果汇总与节点归档

- 按sii-research-sync核对/fetch并读main `6c6c83413d3076b3e3e5206cb77bf44f06ea1ab2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`和AGENTS。用户要求过夜长时任务；原稳定worker不重启，不建定时任务、不使用服务器计算。无关未跟踪会议prompt文档保留未提交。
- 直接动作163927、RL阻抗165000均已完整8条件审计，Task/Strict各0/8；三指标均值分别20.088mm/40.531Nm/.3447m/s和21.352mm/50.136Nm/.3752m/s。19:30导纳90750/VMC82500训练中，其余三配置待接续，不能写成0/0失败或最终全方法矩阵。
- 新report_rl_longrun工具和4项回归通过（篡改/条件/pending/早停分母）；19:30一次性服务sii-longrun-report-20261011-v1实际active。60秒汇总真实训练与已审计节点，原30秒监视保留；节点审计hash/完整8身份/计数/checkpoint逐文件核验后，按节点增量存储小包。
- 监视ALERT或超过5分钟不更新会请求当前回合结束后保存停机，不自动重启、不杀训练。原24小时安全截止仍明天12:01:50 CST；本轮没有修改已加载协议/模型/gate/actor/执行器限制，不承诺明早七配置全完成。保留失败与未完成，详情见docs/RL_LONGRUN_20261011.md。
- 首轮四个已审计节点/权重核验通过；小包已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_longrun_report_20261011_v1_001/evidence/`，8文件178372字节，manifest `039c5ba20d3f73b074d0bc6899e355f33568456dc739012b44fb41dc55d07d48`；含汇总源码/登记/审计/表，不含大轨迹/权重实体。未来归档在节点完成时单独核验，不提前声称存在。

## 2026-10-11 — 修复RL父子锁交接，恢复两路实训并连续监视

- 12:10 CST两路各1条完整55秒新回合已完成并继续下一回合。直接动作110000步/210002更新、调阻抗106000步/202002更新；新优化器记录3084/3000条且均有限。两条各1100000物理子步独立指标复算、模型/轨迹/执行链hash和训练动作/filter一致性通过，Task/Strict均失败保留；不冒充开发成绩或新checkpoint。首回合审计小包已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_recovery_first_episodes_20261011/evidence/`，3文件13813字节，manifest `bb75e8ae1e2542d4e184010f23e7131122a7476435da2981b27fb37d73f3e4f6`。连续监视器无ALERT。

- 开工实查/fetch并读取main `8a4be097ad861c54d20efbbc7fbc35f1292b119a`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`日志与AGENTS。用户新授权继续本机RL，经典90回合和昨夜失败收据保留，服务器不计算。
- 外层使用独立协调锁，调用RL前释放仿真锁；子进程重新独占/预检，子失败抛出且非零退出，预检/准备异常亦落盘，拒绝覆盖execution。真实父子锁交接/子退出23、截止不派发、证据不替换、监视误报success/停滞等15项检查通过。
- 新run `baseline_local_rl_20261009/recovery_20261011_v1` 12:01:50 CST启动。旧两checkpoint各8开发轨迹重新独立审计、与原rows完全一致，省去重复仿真后两路直接接续165k。12:05直接动作109000步/208002更新、调阻抗105000步/200002更新，证明实际学习推进；尚无新完整开发结果。
- 两路各模拟器1/线程1/3GiB/禁swap，沿用正式冻结模型/门槛/actor/执行器限制和无teacher标签。一路失败时STOP_REQUESTED让另一训练路回合边界落盘。独立连续监视器30秒记录真实训练与评估进度，故障/20分钟停滞写ALERT并失败退出，不自动重启；不是定时任务或永久agent在线承诺。
- 新24小时派发安全边界至10月12日12:01:50 CST，明确是本次继续授权下agent选择的保护，不是旧15h延长或收敛条件。保留原有限节点与失败平台复查，不能把启动成功当实验完成。
- 已核验设置包 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_recovery_setup_20261011/evidence/`，594文件5251685字节，manifest `30434c95ad548ad349877b380f882402eb1a99d986ddb968ca94b849b113f05f`。含实际冻结source、外层/监视tools、登记、测试和重审；训练新轨迹仍本地，不冒称已全部上传。
- 新增RL_RECOVERY报告，更新联合进度、周报和接续报告；已完成修复/验证/实际恢复，运行中两路训练与连续监视，待完成新checkpoint/开发评估与最终公平验收。

## 2026-10-11 — 经典90回合完成；如实记录RL整夜未启动的调度故障

- 开工实查/fetch并读main `6023800c9632c8de6a043338f6fa6b544481aede`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`两日志/AGENTS。当前用户请求核查状态，本轮无新训练、仿真、算法或环境修改。
- 经典54筛选＋36确认全部完成；11:53 CST只读重新核验90条条件/seed/参数/模型/路线/轨迹hash及独立审计收据，通过。每类top2各8开发条件Task/Strict均0/8；90条全部完整55秒，无安全早停。不能将参数试验次数当作最终选定策略成功率，未读final。
- RL于昨夜22:03启动即失败：外层协调器持全局锁调用同样需要锁的子进程，子进程BlockingIOError退出1；父脚本却返回0，使systemd错误显示success。这是我们的调度实现与监测缺陷，不是RL算法失败。原failure及源码保留，新run无execution/checkpoint，昨夜新增训练0。当前无运行服务、15小时窗口已结束，没有擅自重启。
- 新增 `docs/BASELINE_OVERNIGHT_CLOSEOUT_20261011.md`，完整列出六组候选8条件指标、RL实际旧checkpoint与故障定位；更新经典验收、联合进度、周报。锁交接/退出码/集成测试修复及最终统一重评尚未完成，不宣称已收敛或全baseline可投稿验收通过。
- 小包已核验发布至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_closeout_20261011/evidence/`，5文件218613字节，manifest `4215d0701bb622c53039117a6c32b6d3ccb6fdfdb31f93caf8e98187f8703624`；含故障源码、失败收据、CLOSE、完整选择及新复核。90条大型原始轨迹仍在本机，不冒称全部已共享。服务器仅传输/核验，没有实验计算。

## 2026-10-10 — 登记15小时过夜baseline接续：经典先收口，随后RL checkpoint接续

- 按同步skill核对并fetch main `fe695ec7e9a1a7810e0ae61689062eda36f9a68e`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两日志/AGENTS。用户授权一次性15小时；不创建定时任务，不使用服务器计算。
- 经典两路搜索检查时已完成64/90，vmc boundary_05 的 development_006/007在运行，服务和监视器正常。保留原90回合、环境、参数、seed、gate、worker和失败记录。
- RL历史`continuation_v2`有中断/失败保留收据，`extension_v1`的旧running字样没有活动服务；未覆盖或伪装这些收据。
- 新增`overnight_baseline_coordinator_20261010.py`及3项回归。协调器不持有全局锁等待经典完成；经典失败即停止。完成后检查活动RL和可用内存≥7GiB，调用已有RL接续工具从不可变checkpoint建立新`overnight_15h_20261010`，每路1线程/3GiB/禁swap，最终测试读取0。
- 20:43 CST一次性服务`sii-overnight-baseline-20261010.service`实际active，内存512MiB/禁swap，15小时deadline至2026-10-11 03:43 UTC；当前`waiting_for_classical`、经典64/90，未启动RL，不影响在途经典worker。
- 已完成：过夜协议、资源门槛、失败保留和服务登记。运行中：经典90回合、只读监视、过夜协调器。待完成：经典收口、RL checkpoint接续与审计、统一公平比较。不能提前称baseline调参充分或RL收敛/proposed优越。
## 2026-10-10 — 本机经典搜索在安全边界从串行提升至两路

- 18:07首批两路已完成：导纳boundary_03/04均完整55秒，分别耗时362.176/361.000秒，shield/动态重放通过。约6分钟完成2回合，原串行约6分钟1回合；是首批吞吐观察，不是同参数配对测速。累计14/90且全量证据复核通过，boundary_05/06已自动接续；两新增Task/Strict失败照常保留。剩余约3.8小时，最终调参仍未完成。

- 按同步skill实查/fetch main `ebecda7a0a5a8151061bf72c06537648f4c47aee`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两日志/AGENTS。用户指出本机利用不足；实测24逻辑核仅一核满载、约7GiB可用内存，原调度偏保守。
- 原第12条完整回合及审计后通过STOP_REQUESTED自然收口，未终止在途worker。旧execution/CHAIN/停止请求保留，12条结果逐项相同，原登记SHA `44e1094a88d86130aa7ec2d22dea99acd63d6fab1ad3e6ec6a584f6ccfe7035e`未变。
- 新增parallel_classical_search工具，18:00:58本机v2服务实际启动，原全局锁、两路各单线程/3GiB/禁swap、CPU1/6；首次可用内存≥7GiB，第二路准入≥4GiB，无第三路。资源登记SHA `9e3a17005cdb3329910fd7a3e8e11302ff280c7fc7442418bd5cce89cffc1726`。原54筛选+36确认/worker/参数/seed/模型/门槛不变，不重复旧回合，基础设施异常停止新派发并排空另一在途回合。
- 监视器支持两路active_jobs和资源登记核验，旧v1自然退出后启动v2；原CHAIN为串行收口，当前读execution及v2服务。7项回归通过（内存准入/防重复/失败保留/证据完整性），真实12条收据重验通过。18:02两个worker分别在CPU1/6约100%，各RSS约0.66GiB、可用6.4GiB、内存PSI为0。
- 已核验小包`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_parallel_setup_20261010/evidence/`，11文件/318902字节，manifest `d47aed02df06a3a83795c7020d74124042f6e9f5cdf0190bd3b1ea3302b0051c`；含源码/原登记/资源补充/安全交接/12条启动快照。实时轨迹仍本地，服务器只存储未计算。
- AGENTS、经典报告、联合进度、周报同步。运行中：两路经典搜索及只读监视；RL仍暂停。首批并行完整回合和吞吐检查见本节顶部；全部调参与最终重评尚未完成。剩余时间仅为估计，不是最终加速比。

## 2026-10-10 — 连续监视经典有限搜索，保留合法失败与完整证据

- 17:12 CST监视器已自动核验新完成的第4条，累计4/90，第5条VMC候选boundary_04正在运行；coordinator与monitor均active，无ALERT，证明进度持续更新而非仅保存启动快照。

- 实查/fetch并读取main `c1a7374fb05943da79a1af319045367021b16b55`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与同步skill。保持原冻结环境/参数范围/90回合预算和在途worker，不恢复RL，不启动服务器实验。
- 17:11 CST完成3条VMC开发候选，同一development_000均完整55秒Task/Strict失败；第四候选运行中。RMSE26.508/26.368/27.961mm、峰矩39.074/39.761/38.071Nm、峰速0.369934/0.373336/0.381502m/s。是参数敏感性试验，不是选定策略跨条件0/3成绩。
- 新增`monitor_classical_search_20261010.py`，读已完成回合并验证条件/seed/步长/冻结模型/路线/参数/轨迹hash与独立审计；选模后重算登记排序与确认条件，终局重验全部轨迹。不修改/重启/派发实验，零新物理步、零final读取。缺失候选记pending，不计零成功。
- 4项测试通过：篡改轨迹、缺失独立审计拒绝；完整卡住与合法物理早停均保留。真实3条证据核验通过；一次性连续服务`sii-classical-monitor-20261010-v1`已active，512MiB/禁swap，每60秒记录，原worker3GiB/禁swap生效。结束产出CLOSE，异常产出ALERT，不自动重启。无定时任务。
- 已核验共享`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_monitor_setup_20261010/evidence/`，5文件/151713字节，manifest `936c58e6febbc85024a1024409a54eca0006311b7238a432554d8090f2c2e57d`；START_SNAPSHOT仅是启动快照，实时结果仍本地，不冒称全部轨迹已归档。
- 更新经典验收报告、联合进度和周报，明确验收不要求解卡，不继续以完整接触恢复为baseline必达条件。运行中：原有限搜索/只读监视/既有归档。未完成：54筛选+36确认收口、调参充分性审阅、最终统一重评；当前吞吐估计剩余约8.8小时，不延长预算。

## 2026-10-10 — 明确baseline验收目标，核实RL暂停与经典搜索运行状态

- 用户再次明确：baseline允许卡住，重点是实现正确、调参扎实、条件公平；不以必须解卡为验收目标。写入AGENTS，现有有限搜索协议、环境、gate、算法和运行快照未改。
- 实查并fetch远端main `8576fa4ab29bdf8aecfe17660345148deeb95cc9`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，阅读两日志与同步skill；无分支合并。
- 本机RL coordinator/worker均inactive，execution为`stopped_at_safe_boundary`：上一轮优先经典控制器时主动安全暂停，新四格RL第一格checkpoint为5500交互；不是风扇停转导致训练退出。本轮仅查状态，未恢复RL或重复派发。
- 经典有限调参服务active，检查时推进至`vmc_boundary_02__repair_development_000`，worker约占一个CPU核、RSS约723MiB。GPU两次采样45–46°C、28–30W，利用率8%/42%波动；未测风扇RPM，不能据此诊断风扇硬件。名称含RL的归档服务不计作训练。
- 已完成：目标澄清和实际服务/进程/收据交叉核对。运行中：原54筛选+36确认经典搜索及原归档。未完成：搜索收口与统一比较，不能提前称调参充分。本轮无新仿真/产物，原服务器已核验诊断路径见下一节；新文档通过GitHub共享，不冒称旧服务器快照已更新。

## 2026-10-10 — 优先补强经典baseline：四组基础搬运验收通过，有限接触归因与调参连续执行

- 六条接触归因已完整完成并独立审计：active_only三类Task/Strict通过（阻抗未碰棍）；edge_only三类均完整55秒失败/carry，VMC/导纳/阻抗目标XY误差79.198/44.146/85.735mm，桌沿穿透均<0.1mm，非安全早停。10条诊断的路线、组内模型、登记与轨迹hash重新核验通过，零新分析物理步/零final访问。连续服务已进入原冻结综合环境的54筛选+36确认搜索；尚无扩展搜索结论。

- 接触覆盖核查：active_only阻抗没有实际碰棍，不能算棍推恢复通过；VMC/导纳棍接触为5.720/0.367s，不能忽略覆盖直接按冲量判优。
- 修复归档收尾的cwd依赖：systemd默认cwd与rsync原工作目录不同，rsync又会进入源目录；前两收尾检查在传输前置核验退出，原传输/仿真未受影响。使用精确发送进程cwd/源参数匹配，保持目的路径、pid身份和全文件hash核验；7项回归通过，v3已实际waiting_for_transfer。GitHub当前helper比已封存小包版本更新，未覆盖封存包。

- 16:52 CST已核验10诊断结果/独立控制器审计/最新helper源码小包：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_diagnostics_close_20261010/evidence/`，16文件/136639字节，manifest `e6f1fa8fc85c222b51d7850fe5066b3e5cf05d7ea62900fa99d4981c2e20823e`。大轨迹包仍在原传输中；没有宣称全部原始数据已共享。首个原综合场景VMC中心复现已完成/审计通过，boundary_01参数候选已实际执行，搜索仍未完成。

- 按`sii-research-sync`查询/fetch并读main `c705c652181dc255b5ac03a5942718f9c8070677`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS。用户改为优先VMC/导纳/阻抗；RL在完整第4回合/5500交互处安全保存暂停，75个checkpoint文件hash核验，不向进程组发信号。
- 修正验收缺口：此前关推力仍保留静态障碍。新增独立clear诊断，在原模型规划后仅屏蔽登记非支撑障碍，原路线/姿态/目标/负载/支撑/任务与安全限制不变；原综合基准未修改。名义、VMC、导纳、阻抗均完整55秒并Task/Strict通过，放置XY误差6.826/9.875/12.342/20.695mm。不得把诊断成功并入最终比较。
- VMC/导纳1375步动态状态/动作重放最大误差0/6.95e-15；三参数shield重放通过，13750条阻抗伺服限制通过。五项场景隔离/预算/选模回归及原控制器单位/投影/执行约束测试通过。未发现新的已证实控制律错误，不以纯重命名伪装修复。
- 旧development_000同所选参数/同路线诊断显示物块与未知桌沿接触停滞（末尾10快照VMC10/导纳8/阻抗10），原始trace hash核验。新增六条active_only/edge_only因果诊断现已全部完成，结果见本节顶部。
- 一次性本机服务`sii-classical-strengthen-20261010-v1`16:14启动：接触归因后，在原冻结综合环境每类中心+8参数边界候选×同2开发筛选，top2补其余6条件，共最多90回合；参数合法范围/actor/gate/执行限制不变，单模拟器/1线程/3GiB/禁swap，服务器不计算。登记SHA `44e1094a88d86130aa7ec2d22dea99acd63d6fab1ad3e6ec6a584f6ccfe7035e`。物理失败保留计数，审计/基础设施异常停止排查；不自动解封final、不宣称充分调参或ESN优越已成立。
- 已核验共享小包：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/classical_local_setup_20261010/evidence/`，26文件/454548字节，manifest `64d881b45f24b2b3023524ecc67f07a18822c0a303ddbacd106f8b1def695930`。`tools/`为新源码入口，`registration/`为登记，`clear_audits/`为已完成审计。749877105字节完整基础轨迹包正传入独立incoming，尚未核验；收尾服务负责原传输的逐文件核验，未启动服务器实验。
- 新增`CLASSICAL_BASELINE_READINESS_20261010.md`与执行/诊断/测试工具，更新联合进度和周报；扩展调参、完整恢复与最终公平重评尚未完成。仿真前npair过严断言的v1失败保留；未派发的归因v1另记superseded，不计作算法失败。

## 2026-10-10 — 启动无示范RL证据研究：奖励×信用分配的本机四格实验

- 15:34首回合完整55秒/1375交互，filter重放误差0、Task/Strict失败；这是随机预热，不是训练后成绩。只读FIRST_TRAINING_MONITOR核验累计2000交互/1完整预热回合，第二回合运行中；新增物理分析0。新开发节点尚未到达。
- 设置/源码/合成控制完整包793文件/151667090字节已封存，manifest SHA `e21d2b1a5d93e31b7dc7152c1cb1bd7fedec4134d5c4d43f29177888d4dfdd78`；正传至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/incoming/rl_evidence_phase1_setup_20261010/`，尚未核验发布。新增通用独立run归档收尾工具与一次性本机服务，等待当前rsync后逐文件核验；状态见运行根SETUP_ARCHIVE_TRANSFER.json。旧大包传输继续，不重复启动；新机器人轨迹仍本地。归档名称正常/四种越界输入检查通过。

- 15:25先行合成控制通过：12000交互/14002更新，固定128样本动作MSE0.159934→0.020626（约-87.1%），满足事前<0.05且≤初始50%；不是机器人任务成功。首组n01_original已开始物理训练，15:27累计250交互、单模拟器/约1.6GB、3GiB/禁swap生效。四cell源逐文件一致，全部历史scripts字节未改，12个声明tools叠加；尚无完整新开发结果。

- 实查main `b7844023bad24ecd6c4f3b9e4969a84351f97037`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取两日志/AGENTS/sii-research-sync，无合并。用户授权本机继续研究，不预设RL必须失败；服务器不计算。
- 新增`rl_evidence_campaign_20261010.py`及合成奖励学习正控制入口/完整性测试。先检验同一官方学习栈能否学会简单连续动作奖励，再跑原/Task安全拆分奖励×1/25步四格，全部从零、同seed2026101011、同训练顺序与环境。每格11k/55k同八development，最多220k训练交互＋64评估回合，单模拟器/1线程/3GiB/禁swap；48小时派发安全保护，完成收口不无限加步。
- trainer新增STOP_REQUESTED回合边界停机与磁盘余量保护；不再向unit广播SIGUSR1。冻结物理/模型/dt5e-5/actor/Task/Strict/执行约束不变，奖励遥测不输入actor。旧运行与中断文件不改写。
- 12项回归通过。15:23 CST一次性连续服务`sii-evidence-phase1-20261010`已active，当前先行控制检查运行中；登记SHA `b7430fc8771c427facb9df03e6ac3079e45dab8d6a531c32b3c134db36480610`。当前新产物仅本地，归档核验另记。
- 新报告`RL_EVIDENCE_STUDY_20261010.md`列明证据边界：这是单算法/单seed机制诊断；多算法、带记忆RL、机器人正控制、≥5训练seed、充分搜索/预算平台与新最终比较仍未完成。成功结果同样保留，不能以未完成或零成功推出RL普遍不适合。

## 2026-10-10 15:05 CST — 完整110k开发零成功，停止盲目续步并记录停止事故

- 用户澄清直接动作RL的对照目的就是“无teacher示范、从交互探索”的完整学习方案；RL调传统控制器是保留结构先验的独立类别。接受此研究问题，不要求给直接RL补示范；将结果限定于所评估算法/任务/预算，ESN结构效应仍由同teacher的MLP/RNN支撑。澄清写入续训报告，服务器小包为此前快照，最新解释以本提交为准。

- 15:09 CST已核验6文件/133192字节的小型审计与事故包：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_development_stop_20261010/evidence/`，manifest SHA `a00cc324bcf2736d6711c27f3b701fb3c2fe850564e04534e6189007274cb648`。包含两完整开发审计、协调器/训练段原始收据及报告快照；不冒充所有原始轨迹已归档。JSON与服务journal交叉核验、文档diff检查通过；本轮无算法改动/新训练测试。

- 按sii-research-sync实查/fetch main `3aa0f4445ef20f24ebde5574f99a6621789fc3d4`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两日志/AGENTS；不合并baseline，不改环境/gate/actor/限制。
- direct108458步、Task/Strict 0/8、8 carry；阻抗104500步、0/8、6 retreat/2 carry。16条均55秒、dt5e-5、独立审计passed，未读final。不能据此断言所有RL不适合、单seed调参充分或数学收敛。
- 用户提出方法论质疑后，agent停止自动续训（非用户明确停机指令）。遗漏仅向main发SIGUSR1，误中断两在途仿真，trainer均报Worker closed before terminal。direct119168步无本段checkpoint；阻抗115739步有115500 checkpoint记录。旧108458/104500 checkpoint及完整评估保留；中断不算算法失败、不声称未落盘梯度已保存。
- 三计算unit均inactive；原大包归档收尾active、waiting_for_transfer。新开发大产物/中断轨迹仅本地，服务器不计算。本轮只核对与记录，更新续训报告、研究面板、联合进度与周报；后续先诊断信息增益，不自动追加预算。

## 2026-10-10 — 重新授权仅本机RL训练至可用策略，连续接续已启动

- 实查远端main `6e31e394617b92ad067aab798e3037b930a6bfe9`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取两分支日志/AGENTS与`sii-research-sync`。前轮网络/SSH失败来自沙箱限制，本轮宿主机正常连通；新授权覆盖旧15小时收口后的等待状态，不再要求用户重复给小时数。
- 新增`launch_rl_convergence_20261010.py`及五个停止条件回归，trainer增加显式接续登记校验。旧协议/hash不改，完整恢复两110k及其余五55k checkpoint；保持原reward/n-step=1、500k优化器日程和所有冻结物理/actor/gate/执行限制。新source快照与旧worker字节一致，入口/审计叠加单独hash。
- 13:14 CST本机`sii-convergence-20261010-v2.service`实际active、两开发worker已开始物理推进。先评两个已存110k节点，随后两路接续165k；剩余五配置在lane空闲后补至165k，后续220k/330k/499125共同节点。每次八development与原始物理/动作/参数/身份/模型hash审计，不解封final、不用teacher或BC、不在Spark计算。
- 单lane3GiB/禁swap/数值线程1，协调器1GiB，启动可用内存≥7GiB；同全局计算锁、防旧活跃unit重复派发。新登记72h有限安全边界至10月13日13:13:46 CST，属于agent运行保护而非用户时间上限或收敛定义。连续失败平台触发机制复查，稳定成功需独立seed确认，500k不能自动称收敛。
- 注册SHA `56542a1a43c30d6a1cbc7e1fda6d003e45740eda94536c4f53397aee91a433bc`；五个新回归、七个原接续回归、语法/diff通过。新增`RL_CONVERGENCE_CONTINUATION_20261010.md`并更新研究面板、联合进度、周报。当前两110k开发运行中，新的训练步与开发结果尚未完成；新产物暂本地，服务器归档核验另记。
- 13:17 CST续训源码/登记/测试589文件、5192187字节已逐文件核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_convergence_v2_setup_20261010/evidence/`，manifest SHA `15d66fbf101fd50303e79c3eae4aef181778d541c2e1f0e96c4667a0be868486`；不冒充运行中轨迹已完整共享。两worker各约1.8GiB，均保持3GiB/禁swap。
- 13:28 CST：两方法前2个development均完整55秒、Task/Strict 0/2、worker动作重放误差0；其余继续，暂无完整8条件结果。新审计入口已通过旧55k阻抗8条真实轨迹复算（0新物理）；SHA `a07f3653c93901bc4666195beb4fd8ef0f90e9840f067e761e0c2e7c9eff955b`。
- 旧两110k训练段3096文件/13504141567字节正限速上传至服务器`incoming/rl_closed110k_20261010/`，manifest SHA `f91bab36baf92a82eff7f0d08532a204d740386172a1ecca4306568286021588`，尚未核验发布。新增一次性归档收尾工具/本机服务，等当前rsync结束后再全量hash核验；无定时任务/服务器训练。源码与启动记录已push `76d89d7`，此前未推送的`f24729a`一并补发。

## 2026-10-10 12:53 CST — 110k RL 收口状态监看与只读审计

- 按 `sii-research-sync` 核对本地缓存的 main `6e31e394617b92ad067aab798e3037b930a6bfe9`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS 和 15 小时收口报告；本轮尝试联网刷新远端失败，未把缓存 SHA 宣称为新的远端检查。工作区开工时干净。
- 确认本机无 `sii-local-rl`/MuJoCo/validate/overnight 进程；没有启动新训练、仿真或服务器计算。两个外层扩展收据的旧 `running` 字样与实际子目录冲突，子目录 `execution.json` 已为 `complete` 并有结束时间，保留历史文件不改写。
- 运行只读 `inspect_local_rl_progress_20261009.py --training-suffix extended110000`：新增物理步 0、held-out/final 读取 0。direct 110k 为 108458 步/40 训练回合/6 Task/2 Strict；impedance 110k 为 104500 步/36 回合/0 Task/0 Strict。审计 SHA `8ad74de12c28a5182f68a6626587b86eca08e8bf8cf6d2b1801843711af2fafd`。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/BASELINE_MONITOR_20261010.md`，明确训练身份指标、development 尚未重评、服务器大型轨迹仍主要本地及下一步预算边界；不以训练回合结果替代公平 baseline 成绩。
- 已完成：进程/收据核对、110k 原始轨迹与 hash 只读审计。运行中：无作业。尚未完成：固定 8 条 development 重评、独立 seed、统一 final 矩阵；新计算需新的明确预算登记。

## 2026-10-09 21:33 CST — 新15小时本机baseline修正窗口与奖励诊断

- 10月10日12:28 CST收口：预算guard在12:21冻结调度器并让已有worker完成回合，12:25退出；无110k后新派发。direct110k实际108458步/40训练回合/6 Task/2 Strict，impedance110k 104500步/36回合/0 Task/0 Strict；未做development重评，不能作为最终成功率。新收口报告`BASELINE_15H_CLOSE_20261010.md`。
- 四格离线信用试验均12002 updates/0 physics，不能替代闭环baseline。可用RL策略、经典恢复、development重评、多seed和统一最终公平矩阵仍未完成；旧384结果保留。
- 收口小型证据包已核验发布至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_15h_close_20261010/evidence/`，8文件/60847字节，manifest SHA `f14b4e029cea7bf9ab4b452c2f7f2a81ec52279fd55ca7d6be51f93c8ef8d77a`。新110k大型轨迹/checkpoint仍留本机，未冒充已归档。

- 10月10日11:30 CST：55k接续已完成全部七配置；直接office_task进入110k接续训练，训练身份新增回合出现6/27 Task、2/27 Strict，尚未完成development；阻抗110k接续仍0/24训练回合。预算guard仍active，截止12:21 CST。
- 固定四格信用分配试验（原奖励/任务安全分开 × n-step 1/25）全部完成，每格12002 updates、0 new physics、无heldout/final reads；`CREDIT_ASSIGNMENT_REPORT.json`只记录学习机制证据，不是闭环baseline。新增n-step和task-safety实现/测试仍需收工发布。
- 11:46 CST：旧55k诊断快照3091文件/12,856,965,783字节已完成服务器核验发布：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage5/evidence/`，manifest SHA `3f5465d4ee035771f03c8ec70f06ab08f80344a741eb1916f7e97676e921298d`。新110k原始训练仍只在本机。

- 21:40补充：首组55k开发8/8完整独立审计，Task/Strict仍0/8（7carry/1load_transfer），调导纳已接续。12个本轮源/注册/审计文件已核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_15h_setup_20261009/evidence/`，79752字节，清单SHA `f1c219037bfe41ad8a8483b92a48a239ae6c954521d7b3f4faccf031e0d835ca`。旧诊断剩余五配置12.86GB快照正在传输，新55k原始数据待归档；不冒充全量已共享。

- 按`sii-research-sync`核对main `935f8cb2242dd7a9e6c637644359ef8673e9fcdd`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS，无分支合并。用户再授15小时，登记21:21至次日12:21 CST；全部计算仍仅本机两lane，服务器仅归档，无定时任务。
- 原七配置56/56开发独立审计完成，Task/Strict全0；原接续18:20开始。直接office_task已54146交互/98294更新，新增33训练失败；首6开发审计通过但均未成功，调阻抗约51k仍训练。更晚状态见15小时报告，不以部分开发或步数称收敛。
- 新增精确进程身份/pidfd保护的一次性预算guard，不改冻结执行源、不重启健康worker；到点阻止旧协调器继续派发，使用trainer既有SIGUSR1处理器完成当前回合/checkpoint。独立预算侧收据保留旧日志。自有虚拟进程身份/信号测试通过，实际guard已启动。
- 修正未来extension判定：55k登记节点与实际完整回合步数分别记录，避免54146被遗漏为未达到第一节点；七项回归通过。运行副本未改，后续独立判断使用修正语义。
- 新增train-only奖励信息消融：Task终奖与连续安全超标成本分开；原八训练回报标准差约0，离线重计9.09。三个单元检查及真实原始子步/hash核验通过，零新物理/梯度，不是新模型成绩，未更改当前训练、gate或actor输入。
- 新报告`BASELINE_OVERNIGHT_15H_20261009.md`；本轮新产物目前仅本地待归档，旧extension设置已核验地址仍为`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/local_rl_extension_setup_20261009/evidence/`。强RL策略、经典恢复、多seed与最终公平比较仍未完成。

## 2026-10-09 — 授权延长RL训练，等可用策略再比较

- 核对远端main `32fd4eeee1878a71be5a1a7e813d0b2d9e9a22ea`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志/AGENTS，无合并。用户要求继续至可用策略，11k不得当充分训练；按`sii-research-sync`保留原队列、冻结环境和本机计算限制。
- 新增`extend_local_rl_training_20261009.py`，原诊断七配置及独立审计全部完成后才接管同一计算锁，精确恢复checkpoint/optimizer/replay/随机状态到累计55k/110k/220k/499125节点；沿用500k学习率日程、原reward/actor/gate/参数限制。每节点同八development评估/原始子步与动作审计，无final访问；接续声明将原77k诊断上限显式扩为有限分段学习，不覆盖原协议与失败。
- 预先登记连续三节点Task≥7/8、Strict≥6/8及稳定性作为开发可用筛查，仅触发独立seed确认，不称统计收敛。所有七配置连续两个≥55k节点仍Task零成功时转科学修正；预算/安全截止/存储不足不算收敛。至少三seed和最终比较仍未完成、未自动派发。新报告`RL_EXTENDED_TRAINING_20261009.md`说明预算、上限和边界。
- 15:56 CST接续服务`sii-local-rl-extension-v1-20261009.service`实际active，状态`waiting_for_parent`，约14MiB，未占第三仿真lane。原队列综合指标直接动作与历史熵对照继续；已完成四配置×八开发全部Task/Strict零成功。接续保持本机两lane/各3GiB/禁swap/单线程，服务器只存档；新55k训练尚未开始，未获得可用新策略。
- 六个回归检查通过：零成功平台、单次好结果、安全失败、未完成开发/训练不能误作可用或收敛；新后缀审计接口在32条完整真实开发轨迹上通过。源码编译/diff检查通过。更新README、研究面板、联合进度、周报和本地报告。
- 已核验接续源码/登记/真实审计包：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/local_rl_extension_setup_20261009/evidence/`，416文件/3188786字节，清单SHA `012bfc5d808b519a295289a5d3a9d4d5e1a3447eb0d9396fa9e26e28ca61ee17`。登记SHA `f07ff9423284e06cc1260d1bff226611d0e2bd66301e1eef75a514c45f36dd2c`；该包不冒充尚未生成的新checkpoint/轨迹。

## 2026-10-09 — 搬运卡住的完整三视角GIF/MP4

- 按`sii-research-sync`核对远端main `93caa3989d5704feb1bf9f082e54cee8d84a9981`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，无合并。选已完成RL调阻抗11k的首个开发身份dev000解释失败，不改实验/训练队列。
- 本地原MuJoCo3.11.0保存状态回放，三视角全55秒GIF/MP4放入用户下载目录；4.56秒进入搬运，10.588秒至结束持续桌沿接触，最终XY误差86.415mm，Task/Strict false。新报告`docs/RL_CARRY_STALL_MEDIA_20261009.md`记录解释/源与媒体hash，未把11k诊断当充分训练结果。
- 仅渲染、无新物理步/动作选择，MemoryMax1GiB/禁swap/单线程；原冻结环境与训练依赖不变。MP4完整解码、GIF276帧/55.2秒读取及12秒/最终画面目视检查通过，下载副本hash一致。
- 已核验服务器媒体与源码：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_impedance_carry_media_20261009/evidence/`，6文件/10968041字节，清单SHA `ba0c4e2f27362f8dd4306657bbd2b9c600a9c9d47c35c468150dd847904a3ae9`。原回合仍在stage4归档；服务器只存储/校验。完整RL队列和审计继续，本次没有新增算法结果。

## 2026-10-09 — 本机RL监看：两组同八开发完成、奖励信息审计与原始轨迹归档

- 延续本轮已授权监看；再次核对远端main `6caa74831135bccb8961b524c145646c291f638c`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志，无合并。全部训练/仿真/分析仍在本机，两lane各3GiB/禁swap/数值单线程；服务器仅存档，显示配置未动。
- direct office_task、RL调阻抗各11000交互/12002更新，均完成同八development条件，Task/Strict各0/8。16条完整55秒正式dt子步/动作/身份/checkpoint独立审计通过；分别停approach/carry。均值RMSE/峰矩/峰速为205.018mm/41.929Nm/0.34735m/s及23.327mm/36.510Nm/0.37383m/s；不以不同失败阶段的低指标宣称柔顺优势。
- 新增只读`--objective-audit`，逐项核对折扣与未折扣原始奖励及势函数抵消。直接组观察到的八条完整Strict失败回报几乎完全相同，包含两次Task已完成的预热；这是当前奖励信息的局限，不是实现重建错误、唯一因果证明或所有策略等价。未改变运行奖励/权重，后续奖励消融须独立登记。阻抗metric回报仍有差异；全八训练＋八开发接触停滞诊断完成，不声称经典无解。
- 14:23 CST调导纳8000交互/6002更新、调VMC2750交互/仍预热，服务正常、OOM计数0；剩余直接metric与两个历史熵对照待运行。只读一次性监看进程持续审计已完成组，有限队列结束即停止等待研究审查，不创建定时任务。训练充分性、多seed、经典脱困和新统一final仍未完成，旧384最终比较未被替换。
- 逐文件核验共享：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage3/evidence/`，210文件/1040156441字节，清单SHA `70afb7ed548d2b888702f00035f7535770e5a641b2532be302fce6de5ad3ca23`，含direct八开发原始轨迹和奖励诊断源；`.../baseline_local_rl_20261009_stage4/evidence/`，292文件/1198991995字节，SHA `168f920b8509531b43e29fee6a589630dc1267a895cb84fafb3e1a02961a022b`，含阻抗八开发原始轨迹、完整成对审计和停滞诊断。所有失败保留，checkpoint/训练在stage2、基础源/继承smoke在stage1；不覆盖旧归档。
- 前次已发布源码/报告小包也已核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage2/review_6caa748.tar.gz`，354665字节，SHA `4a748dc9875cb7f9e6b5cbdf2c070ad4d07cc900cf116b662bcc40606ca2a2a8`。本次同步README、进度面板、联合进度、周报及小型证据；奖励实数据重建、源码语法与diff检查通过。

## 2026-10-09 — 本机RL持续监看：首段完成、开发资源路径修复、独立学习诊断

- 开工及本轮远端核对main `c745da382a45ed7d8ef59f6915cc3464ef2a8ea2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，不合并。按`sii-research-sync`持续本地计算，服务器仅归档，不触碰已恢复显示。
- direct office_task、parameter impedance各11000交互/12002更新完成；前者继承1375步smoke，未重复计算。两组完整物理奖励/原始replay核验及八个阻抗参数回合重放通过。直接组纯学习四回合停approach、阻抗仍卡carry；不能把随机预热Task成功当学习成功，更不能称11k已收敛。
- 首个开发评估在物理开始前因漏传`MUJOCO_MENAGERIE_PATH`失败，原收据/源/日志保留。同checkpoint、条件和正式模型在独立`_assets_retry_v2`完成55秒重跑，Task/Strict失败但actor/filter重放误差0、归一化未更新。只修资源路径，不修改环境/奖励/gate；新恢复入口仅接受这一可核验资源错误，不因物理失败自动重跑。
- 13:16旧健康阻抗段结束后，独立v3协调器核对源/hash/内存并复用已有checkpoint接续原七配置队列；状态为`parallel_v2.execution.json`，旧失败状态仍保留。13:30直接4/8、阻抗2/8开发已完成且全失败，六回合原始子步/动作/条件/checkpoint独立审计通过，其余在进行。新增随机/混合/学习分组检查与一次性只读观察器；后者v2补进度原地写入竞态防护，未重启实验、未创建定时任务。
- 固定checkpoint价值诊断补充categorical目标上界概率及熵尺度敏感度，温度/归一化/权重均不变。两组终止价值残差仍大；熵因素待原登记低熵对照验证，不把soft Q减历史behavior return称纯高估。CPU读取GPU分片诊断失败后用原本地GPU恢复通过，未改checkpoint。
- 阻抗八训练＋两开发均接触意外桌沿约44秒；两个开发末10秒原4cm弹簧误差边界持续触发，但执行命令限幅未改请求、力矩scale和参数能量scale均1，实际速度约0.13–0.14mm/s。新增只读停滞诊断，将持续接触平衡与安全层完全阻断区分；不声称因此证明经典无解，不改约束或actor字段。
- README、进度面板、联合进度与周报同步；源码语法/diff及真实恢复/审计链检查通过。已逐文件核验归档 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage2/evidence/`：717文件、2736212640字节，清单SHA `65e69ae7f36b1f063913b0996258f90bbbd03857c06d578174a2a31b7266a632`。包括两个完整训练段/checkpoint、首开发重跑和原失败；smoke/基础源仍在stage1包，其余正在增加的开发数据未包括在此快照。全部7×8、低熵对照、充分训练/多seed、经典补强和新最终公平比较未完成。

## 2026-10-09 — RL补强转为本机两路，服务器仅存档

- 开工及发布前核对main `694a94d6907d6624e615b9a9cccfe2242502bd2e`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志；无分支合并。按用户最新要求，AGENTS登记禁止服务器计算，保护已恢复显示，不恢复旧Spark队列。使用`sii-research-sync`完成分支核验、归档和发布。
- 新增本地有限RL入口/两路续跑调度，显式本地运行时目录，取消本机子进程继承Spark CUDA路径；官方SimbaV2固定原commit，历史环境二进制和正式dt=5e-5模型hash一致。全范围参数映射保留原rate/tank约束；参数轨迹独立审计精确检查字符串版本标签并补齐适配器hash。五RL族+两探索强度对照，原32train/8development身份、每配置11k诊断上限/共77k，不读封存final、不声称充分训练。
- 完成5D/7D GPU真实梯度更新、归一化计数、checkpoint预测精确恢复与全范围约束测试；物理奖励时钟测试通过。首个55秒/1375交互smoke完整，Task=true/Strict=false，RMSE28.4595mm、峰矩49.0145Nm、峰速0.364766m/s、外穿透0.273794mm（柱—link6）；这是随机预热、0梯度，不能称学习成功。子步奖励重建、replay原始观测/动作和共同filter一致性通过，失败及完整checkpoint保留。
- 12:21 CST本机RTX 5080两路开始：direct office_task精确接续smoke、parameter impedance metric从零训练；各3GiB/禁swap/数值单线程，最大合计6GiB，启动可用RAM8.84GiB。原单回合5分30秒，无OOM；新队列状态在`parallel.execution.json`。语法/diff检查通过，无定时任务；多seed、收敛诊断及新统一最终比较仍未完成。README/进度面板/周报/联合进度同步。
- 两路随后各完成首个完整回合并继续：direct接续Task=true/Strict=false，调阻抗Task/Strict=false且仍卡carry；都未过5000步随机预热，不是方法成绩。调阻抗1375参数更新及13750伺服行独立审计通过，命令幅值/加速度/力矩变化率限制保持；新审计小文件入Git，新增原始回合尚在本地、待后续边界归档。
- 已核验共享归档 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage1/stage1_verified_snapshot.tar.gz`（190281186字节，SHA `ffdad404d6713fceda5e9824b2969b160379f1adecfc3a6dfb3af8b43bdeec12`），含冻结执行源、参数源、首回合原始轨迹/checkpoint与审计。运行中两目录不在此阶段快照，待后续归档；未在服务器启动训练/仿真/分析。详见`BASELINE_LOCAL_RL_20261009.md`，小型证据入Git。

## 2026-10-09 — 显示已恢复，持久保留自动识别并加入协作保护约定

- 开工核对main `4e710fbccb6673bca6ab57276e59de4b23874a7f`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志，无合并。用户确认画面已恢复，要求保持当前配置。
- 11:57 CST远端确认原`/etc/X11/xorg.conf`不再生效，备份hash仍为`794ba039ae3fd03aef2097cf7b5015da9b74f292c23c7042d3f93ee694490b33`；实际显示为USB-C-1、2560×1440/59.95Hz，HDMI断开。纠正此前只查HDMI的局限；自动探测恢复真实USB-C输出，不需要再硬编码分辨率。
- `AGENTS.md`新增用户明确要求的显示保护约定，禁止研究任务恢复旧headless配置或修改系统显示设置；故障报告顶部更新恢复证据。未再改变显示、重启桌面/机器或启动实验；磁盘配置已持久化，但未额外做重启测试。
- 新版共享说明归档至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/display_recovery_20261009/DISPLAY_CONFIGURATION_PRESERVED_1157.md`，按本轮传输核验；旧故障记录保留。baseline补强的中断与未完成状态不变。

## 2026-10-09 — baseline补强启动后被主机重启打断；优先处理显示无信号

- 开工实查main `0a1080709b85a9918aa0a1975f4401836ee48f30`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无分支合并。新增full-range参数RL映射，保留原rate/tank/执行器限制；三类端点、随机状态和旧映射兼容验证通过。新增登记式探索配置入口、有限开发队列；编译/diff检查通过。
- 本地18个同20train/5validation、三seed神经checkpoint的数据/父模型/hash/梯度曝光及字段隔离审计通过；不称同参数量或同总历史预算。经典登记40候选×8条件×3类，180历史组合可复用，780待补跑；RL探索初段不是训练充分性证明。
- 服务器独立run `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_strengthening_20261009_0334/` 已登记并通过映射测试；11:39启动后被主机重启打断，新job/config/log有0字节文件。11:44/11:46本轮服务与进程均不存在，尚无可核验新完整回合，不相信旧running状态、不自动重启。协议SHA `9b3b7235c13ac2af6f35f8c416d0dbd7ed006b16d44c80a06b380f30ca66819b`；原15小时最终报告和执行收据SHA仍匹配。
- 用户报告NVIDIA启动画面后无信号但风扇仍转；SSH/GDM仍正常，HDMI底层disconnected/EDID零字节，7月27日旧Xorg强制headless/1600×900。临时1024×768切换执行成功但用户确认未恢复。无明确故障归因，不把显示报错直接当训练引发的硬件损坏。
- `repair_spark_display_20261009.sh`已上传并核验至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/display_recovery_20261009/`，SHA `4f1a100cb6076fb08397725a71e00642298016a0a6383bbd3c9d588b2d223a86`，bash语法和远端只读check通过。脚本限定主机/原配置hash，备份后停用强制配置并重启GDM，可rollback；sudo需要用户在终端认证，尚未应用系统修改或验证物理画面恢复。
- 联合进度/周报及两份专题记录更新。当前研究受基础设施故障中断，剩余baseline调参充分性、RL收敛与新统一对比均未完成。无定时任务、无新环境/gate修改。

## 2026-10-09 — 15小时修复最终交付：384全完成，ESN未全面胜出

- 前一已核验main `fa4a891428dd03c14131a51267178fa836d0560a`，baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，不合并。新增`BASELINE_REPAIR_FINAL_RESULTS_20261009.md`及全16柔顺/任务表；新384回合全为55秒，422400000物理子步核验、144控制器审计和最终预算/614回合势函数检查通过，所有本批计算服务已结束。
- ESN21/24 Task、15/24 Strict；matched RNN24/16、matched MLP13/9、ordinary RNN14/9、ordinary MLP18/15、memoryless12/10、enhanced teacher24/17；三经典/五RL及nominal全零。ESN人手负载与跟踪有优势，但共同Strict时棍P95更高、球冲量更大；不能挑指标宣称全面最好，也不能称baseline已充分训练或性能问题全部解决。
- 384完成后协调器因冻结快照漏带报告模块而退出，原FAILURE和v1停止收据保留；独立`delivery_continuation_source_v2/`补原版本报告模块，五入口预检及完整后处理通过，无物理重跑/源覆盖/门槛改动。未来prepare补依赖，evaluate提前导入；`finish_repair_delivery`新增严格限定该缺报告错误的恢复入口。语法/diff及实际全链验证通过。
- 服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；真实物理源`source_v9/`、控制器`parameter_v2/`、384原始数据`final_evaluation/episodes/`、最终审计/表`final_delivery_v2/`。最终执行SHA `267aaeb2b3dc6db07c23ffd258ce9a76de0ce308e6cc5d36ddeecca633794f27`，比较表SHA `16c5345874b4912797d9062419caef8147e0eb3dc1ac4f5fd88a7f3b6ea49dd0`；审阅报告与阶段二十归档发布前核验，小型证据入Git，大轨迹/模型留服务器。
- 十组RL实际875183物理交互/684训练回合、1753254次记录优化，含102868次废弃/替代成本；每模型预算和历史teacher差异明确披露。已完成有限修复与重评；未完成强RL学习、经典恢复、同数据多seed因果比较和真实硬件泛化，当前不支持“ESN全面优于强baseline”的RAL结论。

## 2026-10-09 — 15小时修复阶段十九：最终评估过半，未发布局部排名

- 前一已远端核验main `c12c656f53ff8989e7eb0f35773339528e2b9243`，baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。00:54:53 UTC快照202/384完成、10运行，各方法完成12或13条件，无基础设施/逐回合审计失败；完成不是任务成功，未用部分结果改模型或排名。
- 冻结源与模型清单hash复核不变，全部10个活动worker的OOM/oom_kill均0，每路3GiB/禁swap保持。无算法、环境、门槛或预算修改，无重启、新训练或定时任务；仍执行原有限长任务。
- 小型`FINAL_MIDPOINT_20261009.json`同步到`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`，精确计数和资源保留。README/面板/周报/联合进度更新；本阶段快照与独立归档发布前核验。
- 运行中最终评估；尚未完成384完整矩阵和全量独立审计，后处理服务仅等待且checks为空。不将训练稳定、实现检查通过或部分结果称作baseline性能问题全部解决。

## 2026-10-09 — 15小时修复阶段十八：80开发完成，16模型冻结，384正式评估启动

- 前一发布main `951b4e492cfdc03cd905a36ca3649c191b57876e`已远端核验；baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，不合并。80开发回合Task/Strict全零，78完整/2提前失败，无基础设施失败；全部失败和落选seed保留。
- 原协调器于22:51:51锁定16方法，22:51:52开始384最终评估，原预算/环境/gate不变。VMC参数选seed11、导纳12、阻抗11、两个direct均11；选模依据登记排序，不使用最终结果，不能解释为seed平均表现。
- 新只读`audit_repair_model_lock_20261009.py`复算全部80开发分数、核验排序/实际物块末位置、16模型与源码hash、参考未换、冻结先于最终派发；在锁核验后检查最终条件身份/完整参数元组不重复，通过。没有训练/仿真或修改运行中源码。
- 服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`：工具`model_lock_audit_source_v1/`，`MODEL_LOCK_AUDIT.json` SHA `9168776c68c2d82eb2e0e9266d139998b72729005253e53192e7ce3e1b446f06`，模型锁SHA `943fafa86ef309fd9de87a62797039c5c430a81c326cd3a2498abe520750213e`；小型证据入库，阶段十八归档发布前核验。README/进度/周报同步，最终384与全量审计仍未完成，不发布局部最终排名。

## 2026-10-09 — 15小时修复阶段十七：训练结束，80开发评估开始

- 22:13 UTC实查远端main `6f72a5ba0c307a00aaef66cd0f17068e18bd658d`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无并行新提交。训练按22:00收口，22:05:32十组全部在回合边界保存，十execution/hash与末checkpoint核对；参数60500–63250步、直接85285–164621步，逐seed真实预算入15小时记录，未声称均20万或收敛。
- 80开发回合由原continuation_v3运行，新final24仍封存，最终384和全量审计尚未完成。最后训练诊断现行段仍无Task/Strict成功，失败与旧预热Task记录全部保留；没有新增训练或改测试门槛。
- 修正checkpoint诊断入口漏cuDNN路径及子诊断失败仍退出0的问题；显式复用冻结ENV并记录，失败非零退出。首轮十个失败日志/收据保留在`checkpoint_panel_final/`，v2使用逐项相同十checkpoint全部通过可复现性检查；这不是baseline算法修复或收敛证明，未重训或改权重。
- 服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`已核验：`TRAINING_DRAINED.json` SHA `3937fc8b84747d328b14b15edbe4b4ddaea804583b8c8a9d06c18dca5aa249c8`、`TRAINING_DIAGNOSTIC_FINAL.json` SHA `435ebe688b3c0aa5e982c909212da163824e0aedddd65b7ed68bc098561a946a`、`checkpoint_panel_final_v2/execution.json` SHA `8b44f1680262b21906a431f9d1c98a9f75df0bfe423fbe2546ed6ca0b02c9725`；工具位于`checkpoint_panel_source_v2/`。README/面板/联合进度/周报同步；阶段十七交付归档发布前核验。

## 2026-10-09 — 15小时修复阶段十六：解封前明确判据与统计假设

- 前一发布main `ba9897e8d2e3d68e06731d434c900101bacd03f7`已远端核验，baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。新增`BASELINE_REPAIR_EVALUATION_NOTES_20261009.md`，逐代码说明当前放置Task、Strict穿透判据、25Hz保持检测、完整/短回合指标，以及原生阻抗命令限制与实际速度的区别。
- 登记采样实际是六参数逐列分层抽样后乱序组合（Latin-hypercube式），不是独立同分布的24次简单抽样。Wilson/McNemar与逐条件bootstrap按其参考假设解释，不能声称对该单组分层设计或真实硬件精确；这不修改数值/指标/模型/gate。范围只覆盖固定几何和登记扰动，球时间仍2s，不能外推到任意新布局/碰撞方向。
- 已核验服务器同一run的`EVALUATION_NOTES_20261009.md` SHA `00633e0d4272b2a398264bda7ae5af0495add2d642c3323296ed08e970bbdf3b`。README/执行记录链接到说明；修正执行记录开头区分原23:23训练上限与第三阶段已登记的实际22:00收口，不是新增预算变更。
- 十组训练稳定、后处理只等待，final24仍未读；本阶段没有仿真/学习/奖励修改。最终比较尚未生成，成稿须一起引用该解释边界。

## 2026-10-09 — 15小时修复阶段十五：有限最终审计接续

- 21:02 UTC重新核对main `a73dcfd50a07a54477ff1eaca3a9a02e8714df0c`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无并行新提交。十组训练保留；20:58快照参数4.85–5.1万、direct最高14.6万，当前段仍无Task/Strict成功。
- 新`finish_repair_delivery_20261009.py`以一次性`sii-r15-final-delivery-v1.service`接续：等待现有384和协调器报告完成，才顺序运行最终轨迹/统计核验、144经典/参数控制器审计、全16比较表、最终计算账本与势奖励审计。独立锁防重复、预核全部工具hash、失败保留；不创建定时任务，不运行训练/仿真，不替代人工审阅与Git发布。
- 实际状态`waiting_existing_final_evaluation`，所有checks为空；MemoryMax=3221225472、swap=0、单数值线程/CPUQuota100%。目前只验证启动/资源/登记和语法；完整链尚未执行，不能写成最终审计已通过。原总截止后不新开审计阶段，已开始的阶段允许完成；不延长训练或开新物理回合。
- 已核验服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；源码`delivery_continuation_source_v1/finish_repair_delivery_20261009.py` SHA `10dbf7ca1a32519acc6170b14c5a990f5a029f396ebde2926aa148d475d2defd`，输出`final_delivery_v1/`，登记SHA `edd7b7c79fb6d76c5799217ea44e082c6d4c824534565f126d3b0763861d0730`。阶段十五交付归档发布前核验。
- 已完成有限接续入口；运行中十组训练和一个仅等待的后处理服务；尚未完成开发选模/模型锁、新384及最终审计。训练22:00 UTC收口、04:23:12 UTC总截止不变，final24仍封存。

## 2026-10-09 — 15小时修复阶段十四：04:01 CST训练复查

- 前一发布main `12e7bfe7929864f961c8e8ca548484dd929d2a3d`已远端核验，baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。十组稳定训练；参数约3.8–4万交互，direct metric10.8/6.35万、task12.775/5.775万，原06:00 CST收口不变。
- 新训练诊断05：优化数值有限、十组OOM/oom_kill均0（3GiB回收事件仍存在）；当前训练段Task/Strict均0，导纳seed2一条到release、阻抗seed2六条到retreat也没有放置成功。direct当前段短失败3/12/22/12条均保留。不是整个历史从未有过预热放置，也不是学习收敛结论。
- 势函数审计02核对401个完整回合全部通过，无待flush回合；上次direct metric seed1第81回合末三条已齐，1375条完整抵消误差3.55e-15。计算账本04保留历史预热成功（Strict失败）和废弃/重建梯度成本，不把复用数据重复算物理交互。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；`TRAINING_DIAGNOSTIC_05.json` SHA `155420a797f0dd7e5b63fd6056ac136b80fa62503d3dedeedee94c92c368e20d`，`POTENTIAL_OBJECTIVE_AUDIT_02.json` SHA `e8010cce9594e499b1bbac14ca30fed23d8fdd63803229b27d99caa5efc64d34`，`COMPUTE_LEDGER_04.json` SHA `3f5ea2716d110368dc54154cf5956ef56d61ef59d34be8d1d9b221769576d099`。本阶段归档发布前核验；README/进度面板已更新。
- 本阶段未改算法、奖励、环境或门槛，没有训练重启；final24仍封存。开发选模、最终全16×24及最终审计未完成，继续同一有限长任务。

## 2026-10-09 — 15小时修复阶段十三：势函数奖励排查与完整/短回合分表

- 延续已核验main `1ddcbf3cde1e83c454c4002edf48086575934687`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，不改source_v9或稳定训练。19:42 UTC参数约3.45–3.625万步，direct最高12.125万；十组仍运行，原截止不变，新final24未读。
- 排查“空手推进是否骗取阶段奖励”：实际势函数确实取机械臂参考进度，但逐日志核对372个完整训练回合的折扣势奖励均等于负的初始势（最大残差1.56e-14），终止时势归零、失败仍扣任务罚分，没有证据表明该项存在净阶段刷分漏洞。一个新结束回合仅落盘1372/1375条，明确待日志flush，不补造末三条。该恒等式不是学习充分性或部分可观测问题的解决证明。
- 上游SimbaV2实际工作树干净、HEAD仍`86899c277cdc697b2b02d827243de1ea93f20a1d`。新增只读`audit_repair_potential_objective_20261009.py`及结果；不更换奖励或重启模型。
- 新`render_repair_comparison_20261009.py`仅在384结果和144控制器审计都完成后生成全16方法表。成功率保留所有失败；完整55秒/提前终止指标分开，接触覆盖、事件与全时域受力、恢复删失、全部15项配对对照同时列出。合成检查验证短失败不会降低完整回合均值、无接触/无完整回合写NA；尚未生成最终比较。
- 已核验服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；两工具在`analysis_stage13_source/`，结果`POTENTIAL_OBJECTIVE_AUDIT_01.json` SHA `81b7c0f0c9ad76554acd39b9cfbf0c7fc81f1f2fa39071f2cc64ee3e7e58594b`。最初仅含事件表的renderer保留在`comparison_renderer_source_v1/`，未运行最终；最终将用含全时域补充的stage13版本。新模型冻结、最终384与全部审计仍未完成。

## 2026-10-09 — 15小时修复阶段十二：最终控制器审计预检

- 19:24 UTC重新核对远端main `dc62e246cc2dc2c235efa94c3c394e787415a766`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；两个分支无并行新提交。唯一continuation_v3仍训练十组，参数3.125–3.3万交互、direct metric9.975/5.15万、task11.525/5.05万；保留稳定作业和原22:00 UTC收口时间。
- 增加完整最终控制器审计入口：仅在全部384回合结束及16模型锁定后，对144经典/参数RL回合做参数shield重放，其中96条VMC/导纳完整动态状态与动作重放、48条原生阻抗伺服限制审计。最终条件仍封存，批处理尚未执行，不写成已通过。
- 三个既有开发轨迹预检通过：VMC09共1375步零误差；导纳17共1375步完整动作误差5.85e-15；阻抗00共13750条伺服记录满足命令速度、加速度、力矩slew和40mm弹簧界。没有新物理仿真、参数修改或阈值放宽；不是完整机器人动力学重放或无源性证明。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；工具`final_controller_audit_source_v1/audit_repair_final_controllers_20261009.py` SHA `4f54d0f4026161a2bb33adc25e39ec988f4337424bd100b1ffc7ffe8473b43db`。三个`FINAL_AUDIT_PREFLIGHT_*.json`小型收据入库，原始数据留服务器，阶段十二交付归档发布前核验。
- 已完成审计入口与开发预检；运行中十组训练；未完成开发选模/冻结、新16×24评估、最终全量审计与比较。统一测试是系统对比，历史teacher数据/训练预算差异单列，不承诺ESN胜出。

## 2026-10-09 — 15小时修复阶段十一：新增训练回合与第二轮checkpoint检查

- 前一发布main `47f9b3b17a66522994d2b3e1848497b02d6cd25d`，baseline仍为`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。19:03 UTC十组稳定运行，参数2.725–2.875万步、direct metric约9.275/4.425万、task10.75/4.475万；当前训练段Task/Strict仍均零，旧预热成功记录不抹去。
- `TRAINING_DIAGNOSTIC_04.json`对新增完整回合/优化日志核验通过，全部数值有限、十组cgroup OOM=0；触及3GiB的事件存在，但抽查主要有可回收文件缓存且近期内存等待压力接近0，不因此重启。VMC/导纳多停carry；阻抗虽部分到retreat，物块仍未放好；直接动作多停approach/align。只列真实失败，不视为方法性能上限。
- `checkpoint_panel_02/`对十个新增完整checkpoint再次只读检查通过。六组参数均26125步，direct metric89194/37613，task101654/43448；checkpoint/归一化保持不变。terminal价值残差仍明显，两个panel的采样数据和归一化不同，不以原始残差升降作无偏学习曲线或收敛结论。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；诊断04 SHA `be674049ba0d99e2954bda6d13dafd103fd0a77db0a90e9b8b3a9f95f6e2bf00`，`COMPUTE_LEDGER_03.json` SHA `34e773e958b01260fb958e6a9213845e4209a4ea55816054d50964c42faad19e`，panel02执行摘要 SHA `4987a92e605adf14f02a8b0aa2cd81119a778929cf4cf7156e7f6df5c2de4d1f`。大产物留服务器，阶段十一交付归档发布前核验。
- 本阶段是新增学习证据审计，没有更改算法/奖励/环境/门槛，没有新模拟器或训练重启。训练按22:00 UTC收口，final24仍封存；开发冻结、新384评测与最终比较尚未完成。

## 2026-10-09 — 15小时修复阶段十：十组冻结critic诊断与参考模型训练来源

- 上一发布main `40a7dd9a159c5333928e0cacf80482af5e0e016a`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；继续同一长任务。18:05 UTC十组训练仍运行，参数约1.675–1.7875万交互、direct metric7.407/2.6万、task8.725/3.075万，没有新最终成绩。
- 新只读panel在看诊断前登记十个最新完整checkpoint，按单进程/3GiB顺序加载相同GPU拓扑，不仿真或训练。十组模型/归一化未变，检查全通过；终止状态最小双Q减归一化奖励的均值约0.398–2.845，尚无收敛证据，不把历史行为return差当当前策略价值偏差。全部十组继续按原预算训练。
- 六个神经参考模型checkpoint及训练metadata/data登记hash通过：选定ESN/matched RNN/ordinary RNN来自20train/5validation的新teacher数据，matched MLP/ordinary MLP/memoryless来自18train/6validation旧teacher数据。历史都曾获得新数据拟合候选机会，但开发选择出的版本不同；最终统一评测是系统比较，不是六者同数据/同预算结构消融，宽度128亦不代表参数相等。本批不据此倒推换模型。
- 来源审计首版对ordinary MLP的旧`data_sha256`字段不兼容，保留失败，v2记录真实字段后通过；没有修改历史模型/metadata。新增工具`audit_repair_checkpoint_panel_20261009.py`、`audit_repair_reference_provenance_20261009.py`，详情见15小时记录第十阶段。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；`checkpoint_panel_01/execution.json` SHA `1e58c6ceea00791e7a39db3ce81223bb0f325f6c5494e025de9b3ac0964a34d5`，`REFERENCE_PROVENANCE_02.json` SHA `03326d03d8b8815c730c47c4d00fc11b9ff3539c0c77fc3a60702f889425ed46`。源码与失败版本分目录保留，阶段十归档发布前核验。训练收口、开发选模、全16模型冻结与新384矩阵仍未完成，final24未读。

## 2026-10-09 — 15小时修复阶段九：两个seed的学习后动态动作/状态审计

- 17:53 UTC实时核对main `82c9443427bcdf101236d07ba2058985f64fc8d3`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；两分支无并行新更新，未合并baseline。十组训练稳定继续，参数组约1.45–1.575万交互，direct metric约7.025/2.225万、task约8.325/2.825万；这是运行快照，不是收敛或最终成绩。
- 新`replay_repair_dynamic_controllers_20261009.py`重建非零学习后参数动作：两个seed各1375步VMC动作/虚拟状态零误差，导纳完整共享WBC动作最大误差5.52e-15/4.31e-15；原生阻抗两组shield及各13750次250Hz伺服限幅/变化率检查通过。没有修改训练代码、gate、世界或actor。
- 导纳审计入口先后误用joint映射、通用WBC配置及默认名义速度；最终按归档Cartesian映射、pre-integration运动学和fixture速度.06恢复，原1e-10阈值内通过。全部失败尝试及部分状态审计保留，明确是审计入口错误，不列作baseline缺陷。未独立重放完整机器人动力学或证明无源性。
- 已核验服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；工具`dynamic_replay_v5/` SHA `d677c7d5d86073af2c2d9ae3fbba29ad500d6470683088168e2a97045e178f5c`，证据索引`DYNAMIC_REPLAY_RESOLUTION_20261009.json` SHA `5be4407cc6872e15630a803503f7d7357638836850aa36980bd641dda8d3a78a`。小型证据入库，原始数据仍在服务器；阶段九交付归档发布前核验。
- 已完成所述两个seed动作/状态/限制检查；运行中十组训练；未完成充分学习验证、开发选模/全16模型冻结和新16×24矩阵。仍按22:00 UTC训练收口、次日04:23:12 UTC总截止执行同一有限长任务。

## 2026-10-09 — 15小时修复阶段八：全部奖励重建接续、预算账本与最终核验工具

- main上一发布`f6cc500ceecc3abde688eb26fb72eb73a3996b61`已远端核验，baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。17:09:58 UTC八组metric全部重建/恢复；唯一continuation_v3接续十组实际梯度训练，旧v1/v2不重启，原训练/总截止保持。
- 独立奖励检查已覆盖八组15条修复后完整回合，全部通过；证据`LIVE_SERVO_REWARD_AUDIT_02.json` SHA `451f8b40b3a8bc97ec68cff82059590452c42b654bb9d5fbd501c891db749bea`。十组optimizer有限、OOM均0；两组较早task服务有3GiB内存回收压力，不把systemd摘要误作真实内存。
- 新`report_repair_compute_20261009.py`按实际物理行和日志更新数统计，排除继承/复用数据的重复仿真计数，重建计算是总计算子集，废弃/替换梯度另列。`COMPUTE_LEDGER_02.json` SHA `feb74bb69afe59a7e3674fd8fedf0f2e0ec6c1f4d1fbbc6d67a2c800e4742908`；快照不是最终预算。初始两个direct同seed预热曾Task成功但Strict失败（穿透0.98245mm），不能当成梯度学习或两项独立成功证据。
- `verify_repair_final_20261009.py`已通过配对概率/Holm/无接触NA检查；将在完整384后核验模型锁、原始数据hash、动作/储备池及RL归一化，再输出全部15项ESN配对对照，成功检验分别Holm校正，条件接触指标与总表失败分开。未运行最终核验，未打开final24，不按结果选指标或改模型。
- 已核验服务器主根仍`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；新工具`analysis_stage08_source/`，训练`source_v9/`不变，登记`RL_JOBS_CORRECTED.json`、进度`continuation_v3/execution.json`。阶段交付`delivery_stage08.tar.gz`发布前核验；尚未完成RL收口、开发选择/冻结及16×24新矩阵，继续原长任务。

## 2026-10-09 — 15小时修复阶段六/七：奖励时钟纠错与原始转移重建

- 01:01 CST重新核对远端main `9ff915d2830eee2e699dce20539b1bda9b13b607`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；未合并baseline。经典144筛选及48确认全完成，Task/Strict均0，选择VMC09/导纳17/阻抗00；不把运行正确当成性能合格。
- 独立实际伺服对照证实新平滑奖励把4ms更新期错作0.05ms物理步长，首阻抗回合成本0.366185应为0.00457731（约80倍），旧失败剩余上界也不再成立。新增伺服时钟函数及测试，修复在线成本、上界、奖励重建/接续；未改世界、gate、actor、执行器或失败。原始物理数据没有重跑。
- 八组metric在回合边界保存后由不可变source_v9重建：七组已恢复实际梯度，第八组direct metric seed1的55932步前缀重建中；两组task奖励不受影响继续训练。旧梯度与重建梯度分账，不冒称exact resume或相等训练预算；原v2协调器留存superseded说明，完成后接续有限v3，22:00 UTC训练收口与次日04:23总截止不延长。
- 新独立在线奖励审计对七组已恢复训练的8个完整回合通过：实际物理力矩增量、每区间成本、训练负奖励和失败续算一致，原生阻抗还对照独立250Hz记录。非收敛或最终成功证明；第八组尚未有修复后回合。旧奖励critic只读诊断及CPU拓扑加载失败保留，不能用旧诊断评价新权重。
- 已核验服务器根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；`SERVO_CLOCK_DIAGNOSTIC.json` SHA `9d07b467746a73ca60067e7e8777c49e4ec1f525fe34c95236be70d30d44e7ad`，`LIVE_SERVO_REWARD_AUDIT_01.json` SHA `b1bc1b0a6e148336973a63b085264611670db22edf15ef9fb3c758bcf6b40f61`；实际运行源码及清单`source_v9/`、`SOURCE_V9_HASHES.json`，重建收据`servo_reward_repair_v1/`。本次交付归档`delivery_stage07.tar.gz`发布前核验，GitHub仅小型证据。
- 更正当前enhanced teacher的输入口径：实际是同一canonical48/估计负载及共享名义指令上的手工恢复VMC，不能因名称自动归作特权actor并排除。仍纳入全部16方法。final24仍封存；完整新矩阵、RL充分训练及泛化结论尚未完成，继续同一长任务。

## 2026-10-08 — 15小时修复阶段五：筛选完成、RL失败定位与原生伺服审计

- 核对远端main `0e8e2bd9aff78ad936e5ef670a0ecf81f94ffeae`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。经典144/144筛选完成，无基础设施失败，Task/Strict均0；前两名各8条件确认正在运行，两组direct RL稳定，不重复启动。
- 新只读训练诊断验证完成回合的48D/原始action/控制器action/过滤action与hash；快照metric/task约36500/37250交互，本段26/36回合均失败，6/14次原2mm穿透早停，多停approach。optimizer未见非有限值、cgroup无OOM；运行稳定和高过滤频率均不等于收敛或算法正确性结论。
- 三类参数shield各1375步重放误差0；阻抗02完整13750次伺服记录符合40mm弹簧界、1.25rad/s等效命令界、8rad/s²变化率和原力矩slew。更正：原生日志对应250Hz伺服，不是20kHz物理子步；磁盘存储是预防调整，未证实旧原生日志导致OOM。实际物理速度/力矩仍需独立子步审计。
- 新工具`inspect_repair_training_20261008.py`、`audit_repair_parameter_trace_20261008.py`及证据位于服务器主根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`：`TRAINING_DIAGNOSTIC_01.json`、`NATIVE_PARAMETER_AUDIT_01.json`、`VMC_PARAMETER_AUDIT_01.json`、`ADMITTANCE_PARAMETER_AUDIT_01.json`。未改训练源/环境/gate/actor，final24仍封存；阶段五归档发布前核验。
- 未完成经典确认、其余8组RL与原生参数RL实际内存验收、开发选择及最终16×24矩阵。继续原15小时长任务，无定时任务，不要求ESN获胜。

## 2026-10-08 — 15小时修复阶段四：3GiB内存预检与无损日志存储

- 前一阶段main已推送`bc68921`，baseline未改。实读两个RL cgroup发现达到3GiB并触发内存回收，oom/oom_kill均0；不使用systemd摘要中的512KiB假工作集。原生阻抗后续与RL组合前，将两个伺服回调Python数组历史改成磁盘顺序float64记录，完整NPZ不变，不增大限额。
- 本地/Spark10000行NPZ逐位一致及原控制律/限制契约通过。只停止尚未派发新物理任务的continuation_v1，记录superseded和原因；已有经典筛选/两个direct RL未重启。新`continuation_v2`/`source_v8`服务等待既有筛选，后续流程和15小时截止保持。
- 15:24 UTC：screen116/144完成，两个direct RL约28000/29000步，尚无训练Task成功；短回合和失败保留。参数RL完整物理内存验收、开发选择和最终16×24仍未完成。
- README与RESEARCH_STATUS更新到真实当前批次，明确旧弱baseline结果不能支撑ESN全面优势。服务器主根不变，新增`CONTINUATION_MEMORY_PREFLIGHT.json`、`STREAMED_TELEMETRY_CONTRACT_SPARK.json`与`continuation_v2/SCHEDULE.json`；阶段归档`delivery_stage04.tar.gz`（发布前核验），大轨迹仍在原run。

## 2026-10-08 — 15小时修复阶段三：有限接续进程、物块进度筛选与状态重放

- 核对main `bc86e561f03e9366d45ba70840489829e55a3492`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。新有限`continue_baseline_repair_campaign_20261008.py`按已有筛选→确认→10组RL→8开发条件→冻结→16×24执行，没有定时任务；训练拟于22:00 UTC提前收口以预留评测时间，原15小时截止不延长。
- 开发诊断显示空手retreat不能代表物块进度，新增物块实际3D放置距离优先于arm-stage的排序补充；原排序和失败保留，未改task/strict或actor，final24仍封存。该排序明确标注为开发诊断后的修正，不冒称最初预注册。
- 5维RL真实梯度/恢复探针通过；VMC1375步动作、offset/velocity、参数/能量全部重放误差0；六个验收物理子步指标独立重算一致。VMC审计入口曾误用panel单位和漏设导入路径，失败日志保留，实际控制器未重跑。
- 服务`sii-r15-continuation.service`使用不可变`source_v7`，当前等已有144筛选；两个direct RL保持运行。其余参数RL/第二seed、开发选择和最终新矩阵仍未完成；两seed开发选择后得到的是固定模型评估，不是训练seed均值。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`，新证据`RL_DIM5_CONTRACT.json`、`actor_replay_v1/VMC_ACCEPTANCE_V3.json`、`acceptance_independent_audit/SUMMARY.json`及`continuation_v1/SCHEDULE.json`。阶段工具/报告归档`delivery_stage03.tar.gz`（发布前核验），详见15小时记录。

## 2026-10-08 — 15小时修复阶段二：独立奖励重算与阻抗滑移定位

- 前一阶段已推送main `17517dcceec6f00726ef8fcad0125bbb0eaf9c9a`，baseline仍为`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。持续执行同一15小时任务，无新增定时任务，不改环境/gate/actor/执行器。
- 两个direct RL到5500步/4回合/1002次梯度，训练链可运行。独立原始子步审计找出新平滑奖励首样本的人工零→重力跳变，source_v5排除无前驱的首差分；metric用原5500条off-policy转移重建学习器/归一化/重放及梯度，无物理重跑，旧权重与失败保留。task奖励权重0不受影响，原checkpoint直接接续。实际梯度计算包含废弃诊断更新，不冒称exact resume或预算完全相等。
- 本地单线程3GiB运动学重建：两项高刚度阻抗在约9.80/8.92s出现相对夹爪>20mm滑移，接触厚桌角后丢物；低RMSE/低外部穿透不能代替放置成功。几何重建不是接触力重放，最大时间戳运动学差0.0124/0.0127mm已披露。
- 新增奖励审计/重建、滑移诊断和最终评测锁定工具；最终16×24尚未运行。当前经典144筛选及两组RL继续运行，未完成参数RL多seed、冻结/新对比或收敛证明。
- 服务器主根仍为`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`；训练源`source_v5`、奖励证据在各`rl/direct_*_2026100811/reward_boundary_audit_rebuild_v2/`，本阶段小型证据和工具归档`delivery_stage02.tar.gz`（发布前核验）。详见`docs/BASELINE_REPAIR_15H_20261008.md`。

## 2026-10-08 — 用户授权15小时baseline修复/重评，第一阶段启动

- 14:10 UTC阶段核对：验收重试6/6完成、Task/Strict均0/6；高刚度阻抗进入retreat但物块掉落，不能算成功。经典筛选18/144完成。两组direct RL在4125步安全保存后，用source_v4接续至5500步；独立真实优化器探针通过，修正的是嵌套optimizer日志兼容性，尚无学习性能结论。新证据`RL_CONTRACT_TEST_V2.json`、`RL_LOGGER_TYPE_FIX.json`与source_v4存同一服务器主根。
- 开工实时核对main `d5627f49a94651962bdb3f0c5a75c4b503c325ab`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。新长任务窗口13:23:12 UTC至次日04:23:12 UTC，前10小时开发/训练、后5小时冻结/评测/审计；无定时任务。保留旧384回合、旧源码及四个历史暂停RL进程。
- VMC单位修复、投影式阻抗参考、受限名义/等效命令、摩擦前馈/零空间姿态项保存到独立parameter_v1；本地/Spark数值契约通过，尚不等于任务成功。新增RL逐次optimizer日志、每步奖励和实际物理力矩平滑成本，修复参数阻抗action7恒零导致平滑项不可见，并保存初始potential用于完整奖励重放。
- 新32训练/8开发/24封存条件，同一冻结MJB/目标/规划/actor/gate/执行器限制，formal dt5e-5。经典各24候选×2筛选＋前2×8确认；纯RL各族两seed，上限每seed20万且受截止控制，实际预算如实报告，不冒称收敛或相等历史训练。
- Spark登记10路上限、单线程/每worker3GiB，8共享经典物理租约＋2direct RL烟测；本机保守单模拟器。运行中：六个验收重试、经典筛选、两个5500步RL烟测。首验收`events=none`在55s后报告KeyError，原失败保留、无Task分数；新版本映射既有`settle`关闭主动扰动模式，正式all-events场景不改。
- 已核验服务器主根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`，PROTOCOL SHA256 `ff4e3830fbbaaa40efee2d277c57b3859d19162e6ef286c971cbe22a3a44de71`，source_v1/v2/v3和parameter_v1各自留存；详见 `docs/BASELINE_REPAIR_15H_20261008.md`。尚未完成完整验收、RL收敛、最终模型冻结或新比较表。不会为了ESN优势保留弱baseline。

## 2026-10-08 — 经典/RL 实现公平性审计：限制旧表的算法优劣结论

- 按用户要求审查实际冻结代码，开工核对 main `f135ac021aed4bb2af75d5d118a56d1a374cf555`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。本轮仅诊断，不修控制器、不训练、不改场景/gate/checkpoint；384旧回合及全部失败保留。
- 已复现VMC物理读出与action单位不一致：编码平移单位`.16/.16/.20`，实际解码`.32/.32/.32`，未饱和时读出变为2/2/1.6倍。不能据此断言它单独导致0/24；修复还需检查共享teacher路径。
- 阻抗4cm参考边界会抑制切向积分；首预注册条件中固定/调参阻抗末5秒弹簧误差100%达到边界。原生力矩adapter未使用上游受限joint_velocity_command，虽保留力矩幅值/变化率限制，不能称完全相同执行通道；参数阻抗action7恒零还使基于它的平滑奖励失效。上述是已确认实现特征，闭环因果和修复效果尚未验证。
- 五个选定RL模型确实从头在office训练，约4.9万交互/8.8–8.9万更新/36–38回合，但训练Task/Strict全零；update返回的loss/Q等优化诊断没有保留，收敛无充分证据。未发现官方SimbaV2核心更新明显符号错误；导纳本轮未发现明确单位/符号错误。不能把这些0/24直接当作完善经典控制或充分训练RL的性能上限。
- 新增 `docs/BASELINE_IMPLEMENTATION_FAIRNESS_AUDIT_20261008.md`、只读审计脚本及两个V2小型证据；更新最终结果页/联合进度/周报。已核验服务器归档：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_implementation_audit_20261008/v2/`，完整JSON SHA256 `39ec3c982408ec9c3e6c9410c244f7986497094c8e59234cb4031093f84c6d65`；本轮文档存同run的 `delivery/`。历史384回合目录不改。
- 已完成源码/执行配置核对、代数复现、阻抗轨迹和RL训练链审计；本轮无运行中作业。未完成修正后验收、因果闭环、RL收敛与新公平矩阵。后续不以确保ESN胜出为目标，须在独立开发条件修复后冻结，并用新保留条件评测。

## 2026-10-08 — office-v7 384回合最终闭合与交付

- 20:45:50 CST，本批16方法×24条件全部完成，384/384个55秒回合，无基础设施失败；八路评估与最终报告服务均正常退出。ESN Task/Strict为20/24、16/24，matched RNN17/24、14/24，matched MLP15/24、12/24；enhanced teacher24/24、20/24。经典三类、参数RL三类、直接RL两类和nominal zero均0/24真实任务成功。ESN相对matched RNN的RMSE/峰速低4.61%/2.53%，峰矩高2.55%；最坏穿透0.696mm，仍未全部安全通过。配对精确McNemar p(Task/Strict)=0.5078/0.7744，不声称显著全面优势。
- 复核 main `68f9c21c8de4fde9885bf368863d5ada2dcac4cd`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未更改冻结场景、gate、模型、actor输入或执行器限制，没有新训练/重复仿真/定时任务。
- 新增 `docs/OFFICE_V7_UNIFORM24_FINAL_20261008.md`、只读核验脚本和小型 `final/VERIFIED_SUMMARY.json`；同步联合进度、周报和登记入口。最终报告重建逐字段一致、384身份唯一、各24条件齐全，收据/AUDIT/metrics哈希一致；120条RL exact replay及归一化冻结通过。
- 已核验服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`；完整结果 `report_final/REPORT.json` SHA256 `aa84f38750aeafabcf4d5e4586a2f379068b175ccc611535d3cf84d44b5a8203`，原始源/轨迹/审计不移动。`final_delivery_20261008/` 归档本轮报告、核验摘要和核验源码；GitHub只提交小型证据。
- 已完成本批评估/最终报告/审计；运行中无本批作业。未完成baseline性能修复、ESN全部安全通过和更广泛泛化。24个固定布局扰动条件不等于24种布局，相同评测不等于相等历史训练预算。禁止重启旧协调器或用本轮评测反向选权重。

## 2026-10-08 — 经典/RL 停滞诊断与实际八路加速

- 开工核对 main `c81233d1cfcf3afbbb75a182986831f259e53fc4`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。用户再次要求充分利用算力，本轮将本批剩余评测从4路提高到8路，每路仍单线程/3GiB/禁swap，并限定高性能CPU核5–9、15–19；未改物理、gate、策略、条件或演员输入。增加独立回合并发本身不等于破坏公平性，先前将4路说成硬件极限的解释不准确。
- 只暂停旧派发器，四个既有物理回合全部正常结束后补审计，`physics_rerun=false`；保留旧源码和原收据，原协议不覆盖，新增 `DRAIN_V2.json/DISPATCH_V2.json` 记录资源变更。八路新协调器与最终报告服务于18:00 CST启动。18:08快照为174/384完成、8运行，无基础设施失败；其中首批8个新增回合约6–7分钟完成。实测整机CPU约40%，可用内存约93GiB。
- 166个完成回合的只读诊断：经典VMC/调参VMC末5秒误差均值15.52/15.07mm、速度0.43/0.32mm/s；首预注册条件末段仍有未知桌角约6.00/5.13N接触。经典阻抗停lift、末段误差27.83mm，首条件没有外部障碍接触，需核查带载静差/参考/伺服。直接动作RL的变化率限制触发比例为95.4%/93.4%，误差大，尚未学会可靠到位；这些是描述性机制证据，不是参数因果归因或“所有经典/RL都不可能成功”的结论。
- 新增两个工具及 `docs/OFFICE_V7_STALL_AND_DISPATCH_20261008.md`，更新AGENTS中的本批八路例外、联合进度与周报；不以当前测试结果选新权重。诊断使用正确的 `audit.stage` 字段，修正一次查询用 `final_stage` 导致的空输出。
- 服务器证据根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。新调度脚本在 `dispatch_v2/`，SHA256 `67d01dd3492a9966c2ac4f98dd35e5058cff9d984e9bd63429a52c079e24dd32`；`dispatch_v2/STALL_DIAGNOSTIC_CONTACT_V2.json` SHA256 `4a3eae098f1110c268ec960d2d5f41d39f649041ad4c4f0d86a97dc4f0c288a5`，已下载核验。大轨迹不迁移、不删除、不重复运行。
- 已完成：资源预检/亲和性验证、回合边界接续、四回合补审计、八路首批验证、只读机制诊断、源码及证据hash核验。运行中：`sii-office-v7-uniform24-v2-20261008.service` 和 `sii-office-v7-uniform24-report-v2-20261008.service`。未完成：384全部回合、最终每方法24条件对比，以及真正提高baseline性能的独立开发消融；不要恢复旧协调器。

## 2026-10-08 — uniform24 中间结果快照（批次仍运行）

- 15:48 CST 读取服务器批次：`77/384` 回合已完成、4 回合正在运行，其余未派发；评测服务和自动报告服务均为 active。没有基础设施失败或重复启动。
- 当前完成数/Task/Strict：ESN `5/5/4`，matched RNN `5/4/3`，matched MLP `5/3/2`，ordinary RNN `4/2/1`，ordinary MLP `5/4/4`，memoryless `5/2/2`；enhanced teacher `4/4/3`。经典控制器、RL 和 nominal zero 当前已完成的回合均未 Task 成功。以上是前 4–6 个条件的中间计数，不是每方法 `/24` 成功率。
- 当前完成回合的均值指标显示 ESN RMSE `28.89 mm`、峰矩 `51.49 Nm`、峰速 `0.362 m/s`、最坏穿透 `0.375 mm`；matched RNN `29.86/49.80/0.363/0.474`；matched MLP `44.17/47.67/0.373/0.297`。RL direct metric/task 当前 RMSE `77.38/159.20 mm`，但都为任务失败；不能用低峰矩或低 RMSE 取代成功率与安全门槛。
- 失败阶段保留：经典/RL parameter 多停在 `carry`，RL direct metric 停在 `approach`，direct task 停在 `lift`；这些结果不能外推到尚未完成的条件。
- 中间报告已在服务器独立目录 `.../office_v7_uniform24_20261008/report_progress_current/` 生成；`report_final/` 仍等待 384 回合完成。原始回合、物理子步、RL replay 和哈希均保留。

## 2026-10-08 — uniform24 首批闭环核对与源码归档

- 14:18 CST 复查新批次：16/384 个物理回合已完成独立审计，另四路运行，未发现基础设施失败；评测及最终报告服务均为 active。五种 RL 均已至少完成一个真实 55 s 回合，动作 exact replay、归一化冻结通过，但首条件均未完成放置；ESN/matched RNN/matched MLP 首条件均 Task/Strict 通过。尚无完整 `/24` 成功率。
- 已发布代码/协议提交 `808d9dc24f00e16ae472a1b2c5f9e72a2fc44909`。该提交完整源码归档已上传并在传输结束后核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/808d9dc24f00e16ae472a1b2c5f9e72a2fc44909/source.tar`，SHA256 `133e57594eb5940105002df967c4788d25ea0525d7443f1759897beff48eacc6`。大文件传输期间短连接曾超时，传输结束后 SSH 与两项服务状态均重新核实；没有重启仿真。
- 修正两个新脚本的文末空行，复查 `git diff HEAD~1 --check` 与语法通过；这是交付格式清理，服务器实际运行的不可变源及哈希保持原样。对 9 个已完成回合生成的部分报告验证了 384 个预期身份齐全、未完成率为 null、五类 RL 实际回放/归一化检查通过。
- 未完成：余下评测和最终统一成功率表。独立报告服务会在本次有限评测结束后生成服务器 `report_final/REPORT.md`、`REPORT.json`；若批次异常中止则保留未完成状态，不用物理零分掩盖基础设施错误。

## 2026-10-08 — 新 office-v7 统一 24 条件启动与 RL 运行修复

- 实时 fetch/read main `bebb6331707228f7bf84fd4925611243cf2c442e`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；baseline 最新仅为探索性接触指标后处理，不修改冻结模型或环境。检查现有进程后，在独立 run 启动有限批处理，没有定时任务或重复训练。
- 用户要求每方法 24 个新综合场景。本轮登记同一 24 条扰动参数条件 × 16 个固定 family 模型，共 384 个新物理回合；沿用旧 uniform24 的首个冻结模型，而非旧 v7 单条件 pilot 的较早模型。球、人手/棍、柱/厚桌角覆盖三类障碍；几何固定，时序/幅度抽样 seed `2026100824`，实际初态 seed `2026091751`，55 s、formal `dt=5e-5`。不复用旧 office-v6 结果冒充本轮成功率。
- 修复缺失的原 CUDA/JAX/Orbax 运行设置。五个本轮 RL checkpoint 均加载成功，各自 1,375 动作 exact replay，归一化/计数不变；不是重新训练或声称性能已改善。首条件三种参数 RL 均停在 carry、direct-metric 停在 approach；这些真实失败保留。
- 14:05 CST 检查快照：7/384 回合已完成独立审计，四路运行，无基础设施失败；ESN/matched RNN/matched MLP 在首条件均 Task/Strict 通过。尚未取得任何方法完整 `/24`，不报告最终百分比。每回合保留 raw trace、物理子步、动作重放、source/config/model hash 和失败原因。
- 新增 `office_v7_uniform24_20261008.py`、RL preflight、独立报告工具，补齐旧 pilot runner 的环境设置；协议及小型预检证据归档到 `outputs/office_v7_uniform24_20261008/registration/`。验证包括编译、24 条件唯一性/时序、五类 RL replay、首回合真实报告、Wilson 区间边界及 `git diff --check`。
- 已核验服务器主根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。实际 `source/`、`SOURCE_HASHES.json`、协议/模型/条件、原始回合和独立审计已存在；SHA 详见 `code/mujoco_6d_vmc_benchmark/docs/OFFICE_V7_UNIFORM24_20261008.md`。报告程序独立存 `reporting_source/`，SHA256 `a06bf5ba1ae13f7b244225710e2f7acd3030eae896d8b1c3cdccd452d80a7ba7`，与本地一致。
- 运行中：`sii-office-v7-uniform24-20261008.service` 四路评测，每路一线程/3GiB；`sii-office-v7-uniform24-report-20261008.service` 仅等待该有限批次结束，然后生成 `report_final/REPORT.md` 与 JSON。未完成：384 全部回合、最终成功率与跨方法结论。原 gate、actor 输入、执行器限制、历史失败和封存数据未改。

## 2026-10-08 — office-v7 三类障碍统一方法统计

- 开工核对：本地 `main=a518ed45ffa2fd2aab84bdc29bba9243ebdaf9d1`；GitHub fetch 当时不可达，使用已缓存 main/baseline 日志，未把缓存冒充最新远端。服务器 SSH 后恢复可用；未发现已有 office-v7 作业后才启动独立 run。
- 新增并上传 runner 修复：`office_v7_campaign_20261008.py` 使用完整 40 位 Git SHA，且通过冻结 evaluator 允许的 `legacy` parser 注册新时序；场景设置仍写入独立 `PROTOCOL.json/CONDITIONS.json`，没有改写 office-v6 历史目录、gate、actor 输入、MJB 或执行器限制。源码 SHA256 `b19d414801ce6694693525887e361995a07a49e7cce59509d041d0aa51e7842f`，服务器路径为 `arm1:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_three_obstacle_20261008/source/tools/office_v7_campaign_20261008.py`。
- `run_001`（短 SHA）和 `run_002`（未注册 schedule 标签）均为基础设施失败并完整保留。`run_003` 正式 `dt=5e-5`、55 s、17 方法注册，12 个物理回合完成，task `4/12`、strict `3/12`；参数/RL 五行在 checkpoint JAX/Orbax sharding 载入前失败，表中保留为 `not run`，没有计为物理零分。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/OFFICE_V7_ALL_METHODS_20261008.md`，并更新联合进度与 baseline 周报。完整 raw rollout、AUDIT、substep/contact channels、失败日志和 model/source hashes 位于服务器 run-003。限制：单一 development 条件，不能替代 sealed office-v6 矩阵或声称跨条件泛化；RL rows 需要匹配 checkpoint runtime 后另行补跑。

## 2026-10-08 — noise consistency ESN 负结果闭环

- 使用预注册 noise checkpoint `c327ee61c583beb5a392b3752496f6e8eabc136e181551408d4471ded7acab6e`，在相同 office-v6、canonical48D/action7、原 gate、执行器限制和正式 `dt=5e-5` 下完成八个 development 条件；task/strict `0/8`、`0/8`。
- 八回合全部完整执行，RMSE `27.721–31.180 mm`、峰矩 `39.309–48.710 Nm`、峰速 `0.354–0.385 m/s`、穿透 `0.138–0.178 mm`；动作、储备池和公共 filter replay 最大差 `0`。
- arm1 独立 `paper_metrics_20261002.py` 审计完成，原始回合保留在 `arm1:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/noise_dev*/`；新增本地账本 `code/mujoco_6d_vmc_benchmark/outputs/esn_torque_v2_corrected_20261007/closed_loop_noise_summary.json`。
- 结论：noise readout 可压低部分峰矩，但八个条件均未完成放置，不升级候选；未修改环境、gate、actor 输入或正式 `/24` 矩阵。

## 2026-10-08 — 父 ESN 八条件因果配对

- 父 checkpoint `acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7` 在同八个 development 条件补齐，task/strict `7/8`、`6/8`；`development_002` 因 `2.602 mm` 穿透中止，`development_004` 完整但 strict 因 `0.657 mm` 穿透失败。
- 独立 paper metrics 核对 RMSE、峰矩、峰速和 horizon，worker 接触审计提供穿透；replay 最大差均为 `0`。新增 `code/mujoco_6d_vmc_benchmark/outputs/esn_torque_v2_corrected_20261007/parent_paired_summary.json`。
- 配对结果修正模型解释：`.003` 在 development_001 峰矩 `49.907 Nm` 高于父 `49.126 Nm`，development_003 父通过而 `.003` 失败；development_002 `.003` 低穿透而父早停。readout 改动是条件依赖的 trade-off，不是统一峰矩或泛化优势。

## 2026-10-08 — state-delta v4 正式 smoke 负结果

- 已训练的纯 ESN state-delta/abs-state-delta readout v4（checkpoint `7e10362d32a666b0e1d2cc7cad4bbed7c3280d6dc081058873751b57a413345f`）在 development_000、正式 `dt=5e-5` 上 task 通过但 strict 失败：RMSE `30.459 mm`、峰矩 `53.107 Nm`、峰速 `0.3647 m/s`、穿透 `0.5795 mm`，replay 最大差 `0`。
- 独立 paper metrics 完成；首条件相对父 ESN 和已测 readout 候选均不利，因此停止该候选后续派发，保留服务器原始回合和哈希。未改环境、gate、actor 输入或正式 `/24` 矩阵。

## 2026-10-07 — v2 `.003` ESN 八条件闭环与独立审计

- 固定 office-v6、canonical48D/action7、原 task/strict gate、执行器限制和正式 `dt=5e-5`，只评估 ESN readout 候选 `ridge=0.1, smooth_weight=0.003, action_weight=0.0001, parent_trust=100`；checkpoint SHA256 `5b043942da39ff6ee280c56a95b8198a30609ba9fcfde16580fe7fe6e6166dad`。
- 八个 development 条件完成正式闭环：task `4/8`、strict `3/8`。三个 strict 通过回合 RMSE `29.634–34.438 mm`、峰矩 `49.907–50.485 Nm`、峰速 `0.349–0.366 m/s`、穿透 `0.140–0.184 mm`；最低峰矩失败回合 `40.169 Nm`，说明低峰矩不能替代放置成功。
- 所有回合完整保存；动作、储备池、公共 filter replay 最大差均为 `0`。arm1 独立 `paper_metrics_20261002.py` 重算与 worker 审计在浮点舍入范围内一致。首次 dev001 输出目录错误作为基础设施失败保留并排除物理分母。
- 新增 `code/mujoco_6d_vmc_benchmark/outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s005_summary.json`，更新 `docs/ESN_TORQUE_GENERALIZATION_20261007.md`、`docs/ESN_STAGE_REPORT_20261007.md` 和 `docs/ESN_VMC_JOINT_PROGRESS_20260927.md`。原始服务器证据位于 `arm1:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/v2_s005_dev*/`。
- 限制：该候选没有超过 `.01` 的 `5/8` task、`4/8` strict，不升级正式 `/24` 模型；sealed 条件、环境、gate、actor 输入均未改变。

## 2026-10-07 — ESN 读出平滑与泛化开发（本轮）

- 开工核对：工作区 `main` 为 `26cf8a2e028c4c332a0c22fce05ad9106abdd3eb`；缓存的 baseline 为 `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`。本轮 `git fetch`/GitHub 访问因网络不可达失败，不能声称已读取最新远端；服务器 SSH 也不可达。
- 新增 `code/mujoco_6d_vmc_benchmark/tools/train_esn_torque_generalization_20261007.py`：固定 128 单元 reservoir，只训练 readout；加入 action increment、action magnitude 和可选本体噪声一致性正则。修复 float32 checkpoint 的合理部署 parity 容差，并修复噪声特征重复归一化变量错误。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/ESN_TORQUE_GENERALIZATION_20261007.md` 与更新 `ESN_STAGE_REPORT_20261007.md`。36 候选预注册网格在 20/5 identity split 上选择 `ridge=1.0, smooth=0.1, action=0.005`；平滑候选 checkpoint SHA256 `69ecee9d57f34d67be5bec47a4be621d58b9957cc066b1fad0cac7bf588146e4`。
- 离线验证：相对父 ESN，5 个 validation identity 的 action delta energy `0.014357→0.009489`，action energy `0.012396→0.009701`，最大单步 action 跳变 `1.566→1.366`；action MSE `0.000242→0.000612`。这只是峰矩代理/输出平滑证据，不是真实峰值力矩或任务成功结果。
- 训练/回放和 source/config/hash 收据已从本地 `code/mujoco_6d_vmc_benchmark/outputs/esn_torque_generalization_20261007_grid/` 同步到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/`；`REPLAY_COMPARISON.json` SHA256 `082da4d47cf3c5bf60d2be3be9618114e8e1c8330ef85d969aae1af6372d0abb`，checkpoint SHA256 `69ecee9d57f34d67be5bec47a4be621d58b9957cc066b1fad0cac7bf588146e4`。提交源码快照已核验到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/fa64f33b59794a0f88d53f667b8517e87a6737eb/source.tar`，SHA256 `871cd8fb426a6171217f84bc0cd5810fd5b295a66fdca172d49aeecc62b544be`。
- 已完成：编译、单候选测试、36 候选网格、噪声候选、部署 replay parity、离线 identity-holdout 审计和文档更新。未完成：arm1 development 闭环、真实峰值力矩/RMSE/速度、跨条件确认、服务器归档和远端 push。
- 失败原因保留：默认本机解释器闭环启动被 `ModuleNotFoundError: PIL` 阻止；已找到兼容 `.venv-canonical-rl`，但 worker 的 cgroup `MemoryMax≤3G` 审计因 `systemd-run --user` bus 不可用而阻止执行；SSH `192.168.31.70:22` 当前不可达。没有修改环境、gate、actor 输入、执行器限制，也没有读取 sealed 条件。

## 2026-10-07 — 全部 16 个方法的 ESN 重点指标表

- 按用户指定的 16 个方法生成统一展示表，选择 Task/Strict、RMSE、峰值速度、人手/棍子接触力 P95，并同时列出恢复率和最大穿透作为约束列。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_ESN_SELECTED_METRICS_ALL_METHODS_20261007.md`；所有行仍是同一 24 条件、单固定模型，不把低 RMSE/低速度的任务失败回合解释成柔顺成功。
- ESN 在学习方法之间的 Task、Strict、RMSE、峰速和人手接触 P95 均较好；Enhanced teacher 任务成功率更高但其他柔顺指标并非全面领先，经典/RL 的恢复优势也与任务失败一起保留。

## 2026-10-07 — 从统一回合重算接触与恢复柔顺性指标

- 从同一 `/24` 固定模型 cohort 的逐回合 `REPORT.json` 重算球/人手/棍子的接触 P95、冲量、接触时长、恢复成功率与条件恢复时间，并加入最大穿透、单位时间力矩总变差和机械功。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_COMPLIANCE_METRICS_20261007.md` 和后处理工具 `code/mujoco_6d_vmc_benchmark/tools/build_uniform24_compliance_metrics_20261007.py`。未把右删失恢复回合当作零，也未把未接触回合当作零力。
- 主要结果：ESN 人手接触 P95 `19.6 N`、棍子 P95 `13.4 N`，人手/棍子恢复分别 `3/24`、`2/24`；matched RNN 为 `20.4 N`、`13.8 N`，恢复 `1/24`、`1/24`。柔顺接触力优势不能脱离 ESN `16/24 strict`、穿透和恢复率解释。
- 统计 JSON 已独立归档到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/uniform24_compliance_20261007/UNIFORM24_COMPLIANCE_METRICS.json`，SHA256 `c82c7d839d6ec9ef9704fce57299804713fe61afc07fe4e59ecfbca310fb91d0`。

## 2026-10-07 — 修正为完全统一的 24 条件单模型矩阵

- 用户指出原表混用 `/72` 神经/RL 多 seed 与 `/24` 经典单模型分母。本轮从同一服务器 `REPORT.json` 的 912 条原始回合重聚合，没有新仿真或结果筛选。
- 论文主表现在固定每个 family 的一个模型，在完全相同的 `heldout_000`–`heldout_023` 条件上比较，所有行统一 `/24`；神经网络/RL 使用模型锁中首个 seed `2026100301`，经典控制器/teacher/zero 使用其唯一模型。
- 新增 `code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_UNIFORM24_MATRIX_20261007.md` 和可复核工具 `code/mujoco_6d_vmc_benchmark/tools/build_uniform24_matrix_20261007.py`；原 `/72` 全 seed 结果保留为敏感性附录。
- 独立重算得到 ESN `20/24 task, 16/24 strict`，matched RNN `16/24, 15/24`，matched MLP `12/24, 11/24`；所有经典/RL 行同为 `/24`，失败分母保留。
- 本轮源码快照已核验至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/3d565c1/source.tar`，SHA256 `c5b51fc92920ac7276e25208f4983c7bd91a69639d135e2fc194fc5c855aaa84`，93,235,200 bytes。

## 2026-10-07 — 统一 office-v6 ESN/RNN/MLP 与服务器 baseline 矩阵复核

- 本轮重新核对远端 `main=510589794be317e20ea300eb022f86616dab5b12`、`baseline=ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`，并检查服务器进程；没有重复启动仿真或训练。
- 复用并核验服务器最终收据：38 个冻结模型 × 24 个 held-out 条件 = 912/912 回合，`SUMMARY.json` SHA256 `e6d29024bf0e80df16554325193f7a94c6ba8e1193cc31f168a08c9da7346660`，统一 `REPORT.json` SHA256 `100341d7cd42cac944fb5f28849c6028890faf160adfdd27201b0ed4d3fb8d45`；15 个 RL 模型另有 360/360 独立 actor replay。
- 同场景最终表已整理在 `code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FINAL_RESULTS_20261007.md`，覆盖 ESN、matched RNN/MLP、普通 RNN/MLP、memoryless、经典 VMC/导纳/阻抗、参数 RL 和直接动作 RL；保留失败、short 回合和完整分母。
- 最新 ESN v4 目前只有训练/离线 replay 收据，没有 office-v6 闭环收据，故不放入正式矩阵，也不把 v3 开发锚点冒充 v4 正式结果。当前表中的 ESN 是已完成统一闭环的 readout-refit 版本；结论是 ESN task 60/72，但 strict 43/72，matched RNN strict 44/72，不能声称 ESN 全指标领先。
- 服务器原始证据根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。本轮未修改 gate、环境、actor 输入或执行器限制。
- 当前源码快照已归档至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/ad4a98c/source.tar`，远端 SHA256 `0634bf59f7e63cea1f67d01f1685b6bb92937fbc5aa8b96afd90881c7264bf12`（93,224,960 bytes）。

## 2026-10-07 — 因果储备池状态变化读出实验

- 开工读取了本地 AGENTS、联合进度与 baseline 周报；本次 `git ls-remote` 因当前网络不可达失败，不能把缓存 SHA 当作最新远端日志。未发现本机 validate/train/overnight 进程，也未重启既有作业。
- 新增 `tools/audit_esn_causal_memory_20261007.py`：固定 20/5 身份留出，比较完整时间顺序与逐观测清空储备池的动作回放，并分解瞬态/安静窗口；新增报告 `docs/ESN_CAUSAL_STATE_DELTA_EXPERIMENT_20261007.md`。
- proposed ESN 仅加入因果储备池状态变化 `Δh`、`|Δh|` residual，阈值2.0、gain0.25；统一父模型 `clipped_linear` 解码后新候选 checkpoint SHA `7e10362d32a666b0e1d2cc7cad4bbed7c3280d6dc081058873751b57a413345f`，训练数据 SHA `7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0`。旧 v3 候选保留，但不再作为部署候选。
- 离线 held-out MSE：修正解码后的因果 ESN `0.000228972`、matched RNN `0.000234517`；memory gap：`0.006588982` 对 `0.006481536`。该证据支持历史利用增强，但瞬态窗口仍不如 RNN，不能声称全面胜出。
- 已核验的 office-v6 开发锚点记录属于解码修正前的 v3：gain=0.25 ESN task/strict 通过，RMSE `29.400 mm`、峰矩 `49.032 Nm`、峰速 `0.3461 m/s`；matched RNN 为 `29.938 mm`、`54.435 Nm`、`0.3863 m/s`。该结果来自前一轮服务器归档 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_state_delta_gate_dev_20261007_v3_gain025/`，本轮 SSH 不可达，未宣称重新上传；不能直接当作 v4 闭环结果。
- 本地 office-v5 兼容 smoke（修正解码候选）完整55 s但 task/strict=false/false，RMSE `456.748 mm`、峰矩 `68.982 Nm`、峰速 `0.361326 m/s`、最大外穿透 `0.196223 mm`；已放在 v4 候选目录 `v5_smoke_dev_anchor/`，明确不纳入 office-v6 公平矩阵。
- 已完成：机制实现、输入/部署 parity、离线因果记忆审计、兼容 smoke、进度/周报/报告更新。运行中：无。尚未完成：同一 frozen office-v6 worker 的多条件闭环复核、服务器本轮归档、formal dt=5e-5 解封；不得据单锚点解封或改变 gate。
- 本轮本地提交为 `a75c691`；GitHub `main` 的 fetch/push 因网络不可达失败，恢复后需先核对远端 SHA 再正常推送，当前不能声称已发布。

## 2026-10-07 — 最终 912 回合公平矩阵与独立 RL 回放闭合

- 开工复核 main f89e040、baseline ebb0e1e、AGENTS；原开发/最终监督已自然完成，未重启或修改 gate/actor 输入/环境。
- 最终模型锁定后 38×24=912/912 held-out 物理回合完成，task 284、strict 218；最终 `SUMMARY.json` SHA e6d29024bf0e80df16554325193f7a94c6ba8e1193cc31f168a08c9da7346660，统一 `REPORT.json` SHA 100341d7cd42cac944fb5f28849c6028890faf160adfdd27201b0ed4d3fb8d45。
- 最终 ESN 60/72 task、43/72 strict、RMSE 33.780 mm、峰矩49.734 Nm、峰速0.372 m/s；matched RNN 58/72、44/72、33.500 mm、49.729 Nm、0.378 m/s；matched MLP 28/72、26/72。ESN task/速度/RMSE 权衡较好，但 strict 略低于 RNN，不宣称全面优势。
- final delivery `complete`，15 个 RL 模型 360/360 回合独立 actor replay，缺失0；服务器本轮根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/final_evaluation_v1/` 与 `final_delivery_v1/` 保留逐回合轨迹、审计、图和344个媒体文件。
- 新增 `docs/RESEARCH72_FINAL_RESULTS_20261007.md`，明确 task/strict、RMSE、峰矩、峰速、work、short 分母和局限；最终结果已达到可投稿表格基础，但仍需论文作者目视检查媒体并按局限写摘要。
- 本次提交 `1e2cb5bb2e28caa54f43f6d1f8471cbbb41925ab` 已推送 `main`；未压缩源码归档 SHA256 `b7a1c595fcfb61c80fbb695efaad01a0f190f3a776c61f01ceaafd39e228f8f1`，经服务器验证脚本核对 3319 个文件后发布至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/1e2cb5bb2e28caa54f43f6d1f8471cbbb41925ab/`。

## 2026-10-04 — 两个seed303新完成RL续训段独立核验

- 前轮为已核验等待；本轮查询/fetch/read main48d09de、baseline ebb0e1e与AGENTS，确认两段已自然complete，原监督真实存活、final未启动，不重复计算既有审计。
- 冻结371264a三工具检查VMC参数303和直接task303父缓存前缀/新增43991转移/32回合/35192800子步，43959奖励精确一致，32首项因初始potential缺失排除。
- VMC实际累计27500步/45002更新；task实际27159步/44320更新，保留train009于54.64秒穿透失败，两组各16条task/strict false是在线训练记录，非冻结策略最终0/16或ESN优势。
- Spark单线程1GiB只读服务20.644秒正常结束，0新物理/actor/梯度。四结果327499字节位于arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_completed_continuation_audit_v4/，Git前缀RL_CONTINUATION_V4_同字节，hash见RL_REWARD_AND_CONTINUATION报告。
- 进度/周报/状态同步累计240回合审计范围；原训练开发继续、最终912与投稿结论未完成。源码48d09de981cef794948579b26167a2c7130a49d4完整3314文件已核验服务器source/同SHA，tar c8c29a1152d159ac7c2bb4228ed0ada15f9828c28bdef43c1950d4ef8b71b8fd。

## 2026-10-04 — 10:42公开进度与最终阶段容量复核

- 前数轮为具体PID已核验等待；本轮重新查询/fetch/read main fbc11302、baseline ebb0e1e及AGENTS，保留原作业。
- 新快照10:42:08.769010UTC：120拟合完成，RL370053交互/590136更新；三开发37/168、42/168、21/144，含5短失败。队列0/2已自然进入49500最终阶段，全部15模型边界仍未闭合、最终24未开封。
- 原预测器optional0，剩余开发理想17.598–18.432h；最终912物理22.824–23.942h/2h收尾后余量4.424–6.376h。额外等待/加载未全计，不扩搜索；P90最晚final启动仍10月5日09:33UTC。
- 两证据已与Git逐SHA核验同字节，服务器arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下EXPOSURE_SNAPSHOT_20261004_1042.json、BUDGET_FORECAST_20261004_1042.json；具体hash见RESEARCH72_CAPACITY_FORECAST。338ms元数据服务，0新仿真/学习/选模。
- 状态/进度/周报更新，RL审计总范围同步208回合，最终912与投稿结论未完成。前次完整源码fbc11302ab1b203f026d4a4d49f5a7ebfc75ede5已核验3312文件共享至source/同SHA，tar b3ec5a2da8e5a0fd7f94a54d9fae92952d3de7c30d49c953811dc0bec1d94305。

## 2026-10-04 — 补充直接动作RL task301真实续训审计

- 上轮属于已核验等待；本轮发现09:17自然完成的新段并审计。开工main7d66262、baseline ebb0e1e；一次fetch TLS中断后重查/fetch成功，两分支未变，AGENTS已重读。
- 冻结371264a三工具核验5500父缓存前缀、新增21246转移/16回合/16996800子步及21230奖励，16首奖励继续排除；实际累计26746步/43494更新。一条24.84秒global_penetration_exceeded_2mm失败保留，不当最终策略0/16或ESN优势。
- Spark单线程1GiB只读审计10.631秒，0新增仿真/actor/学习；既有队列与最终监督保持运行，最终条件未开封。研究报告/状态/进度/周报同步，最终912和投稿结论仍未完成。
- 三结果163793字节在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_completed_continuation_audit_v3/，Git证据RL_CONTINUATION_V3_*逐SHA同字节；具体hash见RL_REWARD_AND_CONTINUATION报告。
- 前次源码7d662627117d61c76f793db60f50aa7774ed4fa2已核验3309文件共享至source/同SHA，tar d1d3fd6ff083899dc08646409b94b49a286206cc7f7f30ab6e38bf62a4f7e152。

## 2026-10-04 — 09:44公开快照与剩余容量复核

- 开工fetch/read main256bd75、baseline ebb0e1e；具体监督/训练/开发PID持续存活，未重启或解封。上一轮为已核验等待，本轮保存新成本与容量证据。
- 新不可变快照实际09:44:06.133167UTC：120拟合完成，RL331644交互/513318更新，neural-LR32/168、context38/168、readout19/144，含3短回合；未闭合开发指标不是独立子步审计或最终胜负。
- 原预测器optional=0，剩余开发理想18.624–19.506h；912物理22.824–23.942h，保留2h收尾后余量4.317–6.317h。最长固定RL队列P90理想15.179h；仍不含全部等待/冷加载，不能据正余量追加搜索，P90最晚final启动10月5日09:33UTC。
- 两文件已核验Git同字节，服务器根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下EXPOSURE_SNAPSHOT_20261004_0944.json（SHA8f79b10a75e88464ac122674c6fd378620cc4c6d74d37489b8856cacd139d5f8）、BUDGET_FORECAST_20261004_0944.json（SHA62c6ee8d152e438fd906704bb16d05138700594956ed97493bf50b038f1cd876）。
- RESEARCH_STATUS同步当前计数并合并新旧RL奖励审计范围；容量报告/联合进度/周报同步。0新物理/训练/选模，最终912和投稿结论仍未完成。源码256bd75完整3307文件已核验共享，tar SHA811c4c9fbec1e3995ab58691a4a0c3e4e22705702c5d8f7ee46582d2d7e57a18。

## 2026-10-04 — 公布120次已完成拟合的实际成本对照

- 实时fetch/read main52ae14c、baseline ebb0e1e及AGENTS；原监督与开发仍为真实存活进程，最终未开封。最近两轮为已核验等待，本轮整理完整拟合成本，不增加搜索。
- 新RESEARCH72_TRAINING_COST_TABLE_20261004.md从08:45:42UTC不可变快照逐行核算：120作业、288ridge、384000梯度更新、146480736次非padding样本访问，进程耗时合计1742.801748秒；与四批totals交叉一致，作业名不重复。
- 明确ESN60ridge/seed、无记忆36、普通MLP/RNN各7拟合/seed、同特征各9；披露参数范围、54个父权重初始化、验证选第0步仍花4000更新、80次共享teacher采集与额外8开发、四控制器160调参回合。不同单位/共享成本不混成同预算或零成本。
- 不把重复样本访问当新增物理数据，不把拟合进程之和当端到端训练/日历时间；新refit ESN推理慢于普通小网络的既有证据一并链接。RL完整成本、最终逐模型谱系及性能仍待闭合，未改模型/场景/选择规则。
- 引用已核验服务器根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/EXPOSURE_SNAPSHOT_20261004_0850.json，SHAc708837a1b011d7b623ffbf88c8fd7aac346e72eb88c115727902c24f477df67；0新仿真/训练/计时。源码52ae14c已完整3306文件核验，tar SHAefcb274212cf57d4c5a5443ed9a9424d70a5bb7933afcc50c7b3dffb47772d81。

## 2026-10-04 — 独立核验六个新完成RL续训段及38个短失败

- 开工查询/fetch main371264a、baseline ebb0e1e并读日志/AGENTS；原final transition2513613和delivery2550310实际active，未开封、重启或新增训练。上一轮属于实际进展，本轮使用等待时间补真实数据证据。
- 原冻结工具审计六个新完成27500阶段：130回合/129707转移/103765600物理子步；5500父回放前缀和新增观测/原始动作/终止逐值核验。129577可核验奖励精确一致，130首奖励仍因初始potential缺失而排除。
- 物理区间独立重算最大误差积分差5.55e-17，其余力矩/时长/最大位置误差及过滤动作差0。direct task302保留26个短失败、metric302保留12个，原原因global_penetration_exceeded_2mm；不是冻结策略的最终失败率，不宣称ESN优势。
- Spark单线程1GiB/Swap0/CPUQuota100%，服务67.019秒、0新物理/actor/梯度。原训练/开发继续；全部共同边界、912正式、最终独立actor和投稿结论仍未完成。
- 共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下`rl_completed_continuation_audit_v2/`八文件1203070字节完整核验；清单SHA0b16e4a2f7a25de575b7b701113d60b206a00de001e661adc424d1aa3db550c3。两审计/清单Git同字节，详见RESEARCH72_RL_REWARD_AND_CONTINUATION_20261004.md。
- 实际工具源码371264a完整3303文件归档已核验，服务器source/371264a8131effa0d593ad585c4ecc60f83ee7f6，tar SHA9cc0dd6f38c4034e453c443251654a472c1e64229a4f40f45fcbe362767423d6。

## 2026-10-04 — 接通最终评测后的独立RL回放、矩阵与媒体

- 开工实时查询/fetch main de89c451ca33f56aee9e66ca06dac398417b5f04、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读AGENTS/两分支日志；原最终监督PID2513613仍等待前置，未开封/重启。
- 新 `research72_final_delivery_20261004.py` 等最终批次终止后顺序调用原冻结a3 runtime：全部15模型独立RL回放→统一38×24矩阵/统计→图→全部38模型同条件三视角视频。无新增物理/学习/选模，不改变gate或环境；失败/短回合/缺失保留，不自动重试。
- 本机与Spark各9项合成编排检查通过；实际依赖和内置ffmpeg可用。合成测试不等于真实RL回放，缺失报告不伪装完整。论文解释/媒体目视核验仍由研究者完成。
- 09:04:53UTC实际服务 `sii-r72-final-delivery-v1` active，PID2550310，MemoryMax3GiB/Swap0/单线程/CPUQuota100%，`waiting_for_final`、steps空；没有定时任务。
- 已核验共享根 arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：`final_delivery_source_v1` 两源码文件，tar SHA ff113e8896f4b1f6dd0fdb4df8c34cc6fd2fd55078bb735f8c1203f029a25174；`final_delivery_v1/SPECIFICATION.json` SHA348925fe49141896477d3f7433e032949991c71f0f343716137f5d03075d2134，Git同字节。
- 已完成：后处理连续衔接/工程验证；运行中：原开发/RL和两等待监督；未完成：最终912、真实独立RL回放、统计、视频、论文结果。报告见 `RESEARCH72_FINAL_DELIVERY_20261004.md`，未宣称ESN获胜或投稿就绪。

## 2026-10-04 — 核验成本账本、真实OOM计数和报告证据范围

- 本轮承接并已fetch main edf63e5、baseline ebb0e1e，后续本任务main7282022；遵循AGENTS/同步skill，未修改活跃runtime。上一轮属已核验等待，本轮补可复查证据。
- 复用冻结a3b8c97的exposure/forecast工具生成新文件0850，内部真实时间08:45:42UTC：120拟合完成、RL287566交互/425162更新；neural-LR29/168（task10/strict8/短1）、context34/168（18/10/短1）、refit16/144（5/3/短0）。
  快照SHAc708837a1b011d7b623ffbf88c8fd7aac346e72eb88c115727902c24f477df67，预测SHAb694b6e3864288380256bb6b7b955bd6342e85eca246ca4ab1678c387cb45ec4，Git与服务器字节一致。
- 剩余开发理想19.736–20.669h、完整912和2h收尾后余量4.127–6.178h；原有等待/冷加载限制仍适用，不据此加搜索。共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，文件EXPOSURE_SNAPSHOT_20261004_0850.json与BUDGET_FORECAST_20261004_0850.json。
- 七相关服务真实MainPID/ActiveState和cgroup memory.events核对：oom/oom_kill/oom_group_kill均0；开发与RL的max计数非零，说明触及内存限制，不能把MemoryPeak≤MemoryMax本身当OOM检查。前轮较强资源表述本轮补足实际证据。
- 修正DEVELOPMENT_AUDIT：旧表仅worker已有指标重新汇总，不是独立物理子步审计；complete可能是短回合。保留历史数据并关联新79条账本，不扩大成功/机制结论。状态页合并密集轮询文字，旧记录仍在本日志/进度历史中，补更正周报0717实际时间。
- 7282022共享源码已对Git原tar逐文件内容/大小/模式/完整集合核验3297文件通过（原tar SHA28229ff680f7aece49edeab47b8513d4a067ccbaa202815584f3787a3fcd148e）。第一次验证导入产生1个pyc缓存导致集合检查拒绝；仅删除本次自动生成缓存后以python -B通过，没有源码或实验修改。
- 最终24封存，全部开发/RL/912正式/独立actor/统计/媒体仍未完成。本轮0新物理/训练/选模；不以不平衡开发结果宣称ESN领先。

## 2026-10-04 — 08:36UTC队列进度

- arm1 收据更新：neural-LR 29/168、context gate 34/168、context readout refit 15/144；RL adaptation、boundary watcher、final transition 仍 active/waiting，模型锁和正式评估仍不存在。
- 没有重启、解封或追加搜索，失败回合继续保留。

## 2026-10-04 — 08:26UTC队列进度

- arm1 收据更新：neural-LR 28/168、context gate 34/168、context readout refit 14/144；RL adaptation、boundary watcher、final transition 仍 active/waiting，最终评估和模型锁仍缺失。
- 未重启、未解封、未新增搜索，失败回合继续保留。

## 2026-10-04 — 08:17UTC队列进度

- arm1 收据更新：context gate 34/168、neural-LR 27/168、context readout refit 13/144；RL adaptation、boundary watcher、final transition 仍 active/waiting，尚未生成模型锁或正式评估。
- 未重启、未解封、未新增搜索，失败回合继续保留。

## 2026-10-04 — 08:07UTC队列进度

- arm1 收据更新：neural-LR 27/168、context gate 33/168、context readout refit 13/144；RL boundary watcher 与 final transition 仍正常刷新，模型锁和正式评估不存在。
- 未重启或新增队列，失败回合和固定分母保持不变。

## 2026-10-04 — 08:00UTC队列进度

- arm1 收据更新：context gate 33/168、context readout refit 13/144、neural-LR 26/168；RL adaptation、boundary watcher 和 final transition 仍 active/waiting，正式评估与模型锁仍不存在。
- 只读轮询未发现终止失败；没有重启、解封或追加搜索。

## 2026-10-04 — 开发回合独立只读审计

- 新增 `RESEARCH72_DEVELOPMENT_AUDIT_20261004.md`，从 arm1 三个开发目录的已完成 `execution.json` 独立汇总 70 条带 audit 回合：neural-LR 26 条（task 9、strict 7、最大穿透0.9309 mm）、context gate 32 条（17、9、2.4684 mm）、readout refit 12 条（4、2、0.5069 mm）。
- 报告明确不平衡开发曝光不能替代 38×24 正式留出，也不把动作重放误差或单个成功回合当作安全结论；未读取封存条件、未修改 gate、未启动新物理。

## 2026-10-04 — 07:49UTC队列进展

- arm1 收据更新为 neural-LR 26/168、context gate 32/168、context readout refit 12/144；RL adaptation、boundary watcher 和 final transition 仍 active/waiting，`final_evaluation_v1` 及模型锁仍缺失。
- 本轮仅观察与记录，没有重启、追加搜索或解封条件；失败回合继续计入分母。

## 2026-10-04 — 07:37UTC队列继续审计

- arm1 收据更新：context readout refit 11/144、context gate 32/168；neural-LR 保持25/168但其 worker/supervisor仍存活，RL boundary watcher 与 final transition 收据持续刷新。
- `final_evaluation_v1`、模型锁和开封收据仍不存在；没有终止失败、重启或新增派发，正式912回合尚未开始。

## 2026-10-04 — 07:31UTC队列进度

- arm1 收据新增完成回合：neural-LR 25/168、context gate 32/168、context readout refit 10/144；RL adaptation 和 boundary watcher 仍 active，final transition 仍 `waiting_for_predecessors`，最终评估尚未创建。
- 只读观察，无重启、无新派发、无解封；失败分母和固定协议不变。

## 2026-10-04 — 07:22UTC服务与资源审计

- arm1 `systemd --user` 只读核对：additional neural-LR 24/168、context gate 31/168、context readout refit 10/144；RL adaptation、RL boundary watcher 和 final transition 均 active，final transition 仍等待前置，最终评估目录不存在。
- final supervisor 当前约10 MiB、MemoryMax 512 MiB；开发/RL服务 MemoryMax 3 GiB，观测峰值未超过上限，未发现 OOM/kill。没有重启、暂停、解封或新增队列。

## 2026-10-04 — 07:08UTC队列核对

- 只读复核 arm1 既有收据：增强网络仍23/168、context gate 31/168、context readout refit 已9/144；RL adaptation 仍运行，RL final boundary `watching`（最近检查07:07UTC）。连续衔接仍 `waiting_for_predecessors`，`final_evaluation_v1` 缺失。
- 无新增派发、无重启、无条件解封；最终正式结果仍未产生，失败继续保留在分母中。

## 2026-10-04 — 核对服务器队列继续推进，未重复派发

- 06:50UTC通过 `arm1@192.168.31.70` 读取既有 `execution.json` 和进程：`additional_development_v1=running_neural_lr`（nominal已完成，neural-LR已完成22条开发回合）、`context_gate_development_v1=running`（30条完成）、`context_readout_refit_development_v1=running`（8条完成）、`rl_office_adaptation_v2=running`、`rl_final_boundary_v1=watching`；`final_transition_v1=waiting_for_predecessors`，`final_evaluation_v1` 和 `FINAL_UNSEAL_RECEIPT.json` 仍不存在。
- 未重启、暂停或新增任何队列。最终24条件继续封存，失败和短回合继续保留；当前不能报告最终912回合或方法胜负。
- 本次提交 `c65a6c265752a02e8de95ba37f28dfbc8791578d` 已由 GitHub `main` 接收；提交归档到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/c65a6c265752a02e8de95ba37f28dfbc8791578d/`，tar SHA256 `14803649f6d037209fcb11a100107bcbfc7937e2b46bbbd5fde70c48466ace1f`，文件数3296。

## 2026-10-04 — 修正公开快照时间标签并复核最终衔接守卫

- 更正 `EXPOSURE_SNAPSHOT_20261004_0717.json` 的说明：文件名中的 `0717` 仅为运行标识，JSON 内部 `created_utc` 为 `2026-10-04T06:18:25.398327+00:00`；同步修正 `RESEARCH_STATUS.md`、联合进度和最终衔接报告，未改原始 JSON 或 SHA。
- 本地用 Python `unittest` 运行最终衔接、最终锁定和 exposure ledger 的 17 项回归，全部通过；未启动物理、训练或选择流程。
- 开工时远端 GitHub 与 arm1 SSH 均因网络不可达，无法刷新远端 SHA、读取服务器 `execution.json` 或 push；本地基线仍为 `main=9c66ea6`、`baseline=ebb0e1e` 缓存引用。网络恢复后先核对远端并继续既有衔接服务，不重复派发。
- 研究状态仍为：最终 24 条件封存，连续衔接待前置队列；912 回合、独立 RL actor 审计、统计、媒体和 RAL 结论均未完成，失败保留。

## 2026-10-04 — 开发队列继续推进，连续衔接保持等待

- 06:16UTC实时查询/fetch并读main eea104e06fb86ef5b358ab273e51badef9967882、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；连续服务PID2513613仍存活，未重复派发。
- 文件名`EXPOSURE_SNAPSHOT_20261004_0717.json`对应的公开快照内部实际时间为06:18:25UTC（0717仅运行标识）：全部120拟合完成，RL177603交互/206734更新；增强网络19/168、context29/168、新refit6/144，直接/参数RL的失败和短回合仍在分母中。
  25个开发/训练相关进程仍有真实PID；三队列均保留既有租约和共同边界监护，final_transition仍waiting_for_predecessors，最终24封存且final_evaluation_v1未创建。
- 新预测理想剩余开发22.511–23.573h、完整912物理22.824–23.942h，保留2h收尾后余量5.857–3.678h；额外等待/冷加载未计，不追加搜索或改变预算。
  快照SHA74fca49834e4136decb3cd5be3418f05dd7e3fd45b1e49104e6a03fd40cbff89，预测SHAd7f72cc2f9337f3154a02d2f105aa37cfc8ff2e039b2b5fb3ee24fa0ba20295，Git同字节。
  本轮无新物理/拟合代码改动；完整共同边界、正式评估、独立RL actor回放、统计/媒体和投稿报告仍未完成，目标active。

## 2026-10-04 — 一次性连续衔接全部开发与912最终评估

- 05:59UTC实时查询/fetch并读main a3b8c97fa027f4bf9bb55149e45cac4f664be562、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志，依既有AGENTS/skill继续；工作区干净，原七个队列/监护PID仍存活。
  main a3完整3289文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a3b8c97fa027f4bf9bb55149e45cac4f664be562/，tar SHA0fd1ecbcdcff983818ec7c2ddf29108699f356295189a980b1c50dddd011a781。
- 新research72_final_transition是一次性连续依赖进程，全部前置/监护关闭且无活跃开发后，调用已有公开选模→38模型汇总→冻结→912最终批次；规则/门槛/场景/预算不改。
  缺前置、终止失败、源码变化、已有最终输出或命令错误均保留并停止，不自动重试；8项合成回归通过，包括37模型、911回合与已开封拒绝。没有实际选模或物理测试。
- 06:09实际服务sii-r72-final-transition-v1/PID2513613已核验存活，512MiB/Swap0/单线程/CPUQuota30%；waiting_for_predecessors、steps空，最终24未开封。
  五项仍待完成：增强网络、context、新refit、RL、RL共同边界监护；原稳定服务不重启。后续先检查该监督状态，禁止重复手工派发final矩阵。
  supervisor独立两源final_transition_source_v1核验，tar SHA7cfeb2dee5e9eef397a5d07be925adbd74760812b86e76a520d19931be3cb953；实际子流程使用固定a3 runtime。
- 本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；final_transition_v1/SPECIFICATION.json SHA665883fca7dc5dab7b3d80d64fcccd9b6ec1028fa9dbc271bcb4950edd8a9fe5，Git同字节。
  05:59快照RL165754交互/191536更新、context28/168、增强19/168、refit4/144；新容量预测含912/2h收尾余量3.673–5.867h，仍非保证，不追加搜索。
  BUDGET_FORECAST_20261004_0559.json SHAfb3dabe4a21ee43d898778b35a21eda77b3ade9120a5f62d4e6bf817a0e66b51，Git同字节；新增FINAL_TRANSITION报告，更新状态/进度/周报/容量。
  完整最终比较、独立RL actor、统计/媒体/论文结论仍未完成，目标active；即监督最终complete也不等于投稿完成。

## 2026-10-04 — RL物理奖励输入独立复算与短失败保留

- 05:41UTC实时查询/fetch并读main19a11c21f6aef4be2801a1e3c192146182a23bad、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS，工作区干净；前轮属实质进展，本轮实际PID/服务继续存活。
  main19a完整3284文件核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/19a11c21f6aef4be2801a1e3c192146182a23bad/，tar SHA1f170330481b8121489168602eeefc2e850742edac17cc00fe5ac2c8a30ca431。
- 新research72_reward_intervals从物理/actor时间戳独立划区间，重算dt/error/实际力矩积分与峰值并核对公共过滤action；五家族六完整训练段的62回合82004区间/65603200物理子步通过，4短失败保留。
  时长、峰力矩/误差、动作差值0，积分最大8.33e-17；六项边界/篡改回归通过。Spark1线程/1GiB/CPUQuota100%，约33s完成，无新物理/actor/拟合。
  只补物理日志归约，不独立重算任务potential/初始potential、终止观测或接触真实性，不把这些训练记录当最终策略测试。
- direct_metric301自然完成27336步/22回合/44674更新，5500父前缀及新增21836真实转移核验；新18回合含39.76/1.04/7.64s三个穿透超限短失败。
  新21818奖励精确核验、18首奖励排除；与原五段合计81942已核验奖励/62未知首项，与82004物理区间对应。不补写步数、不丢失败、不称已收敛。
- 两源reward_intervals_source_v1核验，tar SHAfc4fdbb7145ba401f15a7aa479c3641160904d48b289c5d57b503e0190039f37；结果reward_intervals_audit_v1三文件276836字节独立核验，清单SHAddf8c0bea89c62cf4455e01966687002ad7493b178aba07beebe26307477a140。
  共同根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，Git保留物理区间/新奖励/清单同字节；更新原RL奖励报告、状态、进度、周报。
  稳定开发与RL队列继续，未追加搜索/更改环境或gate；全部共同训练边界和38×24最终比较未完成，最终条件封存、目标active。

## 2026-10-04 — 最终RL共同边界的完整账本检查

- 05:26UTC重新实时查询/fetch并读main2000768、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS；承接前轮12文件审计，正常提交/push为9ccabddd8095166c4b535d6b108631327e5af33e。
  完整3284文件已逐内容/大小/模式核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9ccabddd8095166c4b535d6b108631327e5af33e/，tar SHA4afd43694094e5acbfb4ca15e4b3eb230bdb1d3a8049f46a8123abfa31ddcce9。
- 最终38模型汇总原5项回归补至8项：真实final_policy/selected_boundary/main串联15个合成RL模型，包含49336与49500实际步数差异，必须选择登记边界而非后续收尾权重；1375额外步保留计成本。
  缺一个登记阶段不回退，监护关闭证据篡改拒绝，真实新teacher完成与旧相同teacher跳过路径均覆盖。本机8项通过；仅checkpoint字节检查在合成测试中mock，实际13存档另经真实verify_candidates核验。
  无实际最终选择/冻结/开封，无新物理/训练；不修改运行中源码、队列或研究选择规则。
- 只读加载核查：当时13个已完成RL存档964文件/1,836,571,406字节，两遍真实完整校验约1.988/0.914s；550个runtime文件约.030/.030s。
  这是当前存档在现有缓存状态的粗计时，不代表完整15个最终checkpoint冷加载、JAX推理初始化或912回合完成耗时，原预算预测不据此缩减。
- 05:35公开快照：RL151254实际交互/171034更新，旧context26/168、增强网络18/168、新refit3/144；全部120拟合已完成，原作业继续。
  服务器本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，EXPOSURE_SNAPSHOT_20261004_0535.json SHA2809fa0829b508af25ede9c933cbca54b9a804441589cca64ed59c786ebe83a9。
  新refit仍只完成三个开发样本，不做胜负推断；最终24封存，完整912比较、独立最终审计和投稿证据未完成，目标active。

## 2026-10-04 — RL完整续训闭合与五家族奖励缓存核验

- 05:05UTC实时查询/fetch并读main2000768fbd0b4dd2edef709854e6b444b98335a0、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS；工作区原干净，只有root agent。
  main2000768完整3276文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/2000768fbd0b4dd2edef709854e6b444b98335a0/，tar SHA700aa4acb9d6fad89a8464d59e1719718e83daca19fda1427190ca71675ac5fe。
- 导纳301/VMC301自然完成27500步/20回合/45002更新；复用冻结审计工具核对75/74存档文件、44源、原轨迹引用，并验证5500父前缀和新增22000真实转移。
  与旧16500中途快照区分；未逐梯度重算或把训练结束当最终策略成功，15模型49500共同边界继续等待。
- 新research72_reward_replay_audit按原协议SHA加载冻结rewards.py，从保存区间/实际过滤action核验回放奖励，四项边界/篡改回归通过。
  五家族代表段60124奖励逐值一致，包括office_task303原41.72s短失败；其终止task−20、负成本补偿−.2224180869保留。
  因初始potential未保存，44个首奖励明确未核验；未从子步独立重算区间、未重算梯度/终止观测，0物理/actor/学习，不称全15模型审计。
- reward_replay_source_v1两源核验，tar SHA4d304639183d6c490899961a8393ca4e264bd738a0d77ec137ec9c5ae6a6625e。
  rl_completed_continuation_audit_v1五完成结果315828字节逐hash/大小核验，清单SHA33014cf06562a26ac02b4528e9ab6ac45bae1b857b386e70a70f79d78aa3c397；存档/奖励/清单Git同字节，长前缀原件服务器保留。
  共同根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；详见新RESEARCH72_RL_REWARD_AND_CONTINUATION，同步状态/进度/周报。
- 05:19真实成本RL140438交互/154400更新、context25/168、增强网络17/168、新refit2/144；三RL及评估实际PID存活，三memory.events的oom/oom_kill均0。
  新预测保留完整912和2h收尾后理想余量3.632–5.857h，非完成保证；BUDGET_FORECAST_20261004_0520.json SHA7c4709023889cf34387cd711025f2137bc6d492ce65167fe22025b8a123ad795，Git原字节。
  本轮未加训练/物理、未重启稳定队列、未改环境/奖励/gate；最终24仍封存，全部正式比较与论文结论未完成，目标active。

## 2026-10-04 — 新读出实际推理成本和更强RNN对照

- 承接main a09926105598ef04b8f77982fa119d67556088fb，baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；本轮已实时核对分支及AGENTS。
  最新main3275文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a09926105598ef04b8f77982fa119d67556088fb/，tar SHA70a971f64d6d78415cd4bb989657089725ee4fabd6eca648c72738b445f7b563。
- 复用既有inference_profile入口，本机单线程3GiB测量新18模型/同公开1375帧训练序列，固定打乱顺序、每模型3遍，共74250计时；warm导出重放误差0，0物理/拟合/封存读取。
  ESN3780可训练系数，actor中位32.205–32.800μs；普通MLP5504系数/7.847–7.910μs，RNN21888系数/9.885–10.104μs。不称ESN推理更快，不以actor延迟证明端到端实时。
  新matched RNN三个seed选择更新4000/3600/3600、验证MSE均优于ESN父模型；其三seed均值.000230356 vs ESN.000232886。保留更强对照，离线代理不是闭环成功。
- 六文件源码/原始计时/PROFILE已完整核验共享本轮根refit_inference_archive_v1，tar SHAf6f6a71315f7a8146ac0ed1f0b50c78ded5cf451fdad2fab9fd5b371a7277939；PROFILE SHA674c80045d0e22e1962430d8f1e4bfd3deba47780621ea791cad1826adb8ad8b，Git同字节。
  本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；更新READOUT_REFIT_RESULTS、方法定位、联合进度和周报。
- 同时检查Spark空间余2.7TiB，运行目录93GiB；三RL服务正常、swap0，原队列不重启。开发144及旧增强组/RL运行中，最终24封存，目标active。

## 2026-10-04 — 最终选择的真实路径兼容修复与新读出首回合

- 承接已推送main9e7fa92dedd121a79e838a49fa48cd1c27921444，baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；本轮前已实时核对两分支和AGENTS，无其他工作区改动。
  main9e完整3274文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9e7fa92dedd121a79e838a49fa48cd1c27921444/，tar SHA49f18477cffb2f15561761f9d96645a90d6dd09a05b9395e8eb09192fd8f80a2。
- 在后续最终学习选择器发现同类JSON路径字符串/hash接口错误，规范化为Path。新增完整72候选合成账本测试，经真实load_phase/main验证18模型输出，全部失败仍入选、teacher证据篡改拒绝、refit缺1回合拒绝。
  本机3项通过、原38模型汇总5项通过；Spark同3项通过，零实际选模/物理/拟合/封存读取。不修改运行中冻结源，真实最终选模必须用本修复后的入口。
  本轮根selection_guard_source_v1两文件内容/大小/模式全核验，tar SHAff30db5889c35883933aef23daf173f181ad957c3ff9ac5c2040ae8547771411。
- 04:51:49UTC新refit首条development000/seed301完整55s结束，worker审计task/strict通过，RMSE30.699mm、峰力矩49.981Nm、峰速度.349058m/s，外穿透.143599mm。
  请求/公共filter/储备池重放误差0；raw trace SHA5c43b9cd6b48c015ff5b9e314d001d23b8b0b5438de23e7139c13766f66ef26c。
  仅单条公共开发、整阶段独立审计未完成，不据它改候选、gate或声称泛化；固定144队列继续。
- 04:52UTC旧context24/168、增强网络15/168、新refit1/144；三RL队列持真实租约、共同边界监护watching。24最终仍封存，目标active。
  共同产物根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；进度/周报同步，无新搜索或重启。

## 2026-10-04 — 共享新teacher重训完成，纯ESN交互读出进入144条开发比较

- 04:28UTC实时核对/fetch并读main8c1633e5b643b68c26008047c1fb5f4a1cf25010、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS，承接已登记研究的未提交源码/证据。
  main8c完整3259源文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/8c1633e5b643b68c26008047c1fb5f4a1cf25010/，tar SHA5473d1fcee18f0607afce2c56ec94558441a096076b06a48678aec1c689b4ede。
- teacher40/40完整采集完成：task40、strict25；新20训练＋5验证34,375帧，真实请求/过滤重放已核验。验证8配对审计task7→8、strict6→5，合格柱接触0/5，明确不是全面改善。
  validation审计20文件1,056,265字节全核验，清单SHAaedb6501a93be5825b97b8d0bce4fe0e228753f874d05bf4011563a76ada6382，SUMMARY Git同字节。
- 修订02于04:20:58拟合前登记，保留原条件/gate/最终38×24，核验三RL真实租约与容量。纯128ESN新增固定本体×记忆读出，只训练3780线性系数。
  全六模仿家族共享新数据、固定学习率；本机1线程3GiB于04:22–04:26完成18拟合，6固定模型72候选精确重建，18actor共24,750帧隔离/导出重放误差0。
  新数据＋结构不能当单因素机制证明；累计ESN60、无记忆36候选/seed，ordinary+matched MLP/RNN各16，不称等计算。
- 763文件核验共享本轮根local_context_readout_refit_archive_v1，tar SHA07d887b4c98426a3a97441e0d1568a8020b2581b494e9b9268e2c2a9b987034b。
  登记JSON路径字符串错误在写出spec前修复，原拟合未重跑；18模型×8开发全部登记，单队列PID2490149已运行，仍共享四仿真槽。
  修订/登记/储备池/输入审计等Git原字节证据，实际源/seed/hash/限制详见RESEARCH72_READOUT_REFIT_RESULTS，更新状态/进度/周报/英文方法。
- RL导纳301/VMC301各16,500步真实存档保留5500回放前缀精确一致，新增11000转移关联实际8回合；未重算梯度/奖励/终止帧下一观测，不称最终任务审计。
  prefix源两文件核验，tar SHAfd4cf8c6e74e65015a6a28884e1cd7554b464a3ae8b8478ac12a54261763f988；两实际结果Git同字节。
  q1自然得槽在一次性让槽工具之前，真实events=[]，未向研究进程发暂停/恢复信号；工具仅自身一次性测试子进程的信号检查通过，不重复调用。
- 成本工具从登记起计144条、未来optional=0避免重计；新refit_dispatch_source_v1三文件核验，tar SHAccbf38b89d0f15ba9410adeb8fff760e122fa7dcfd563e1b1153bbc1701f91f0。
  04:36:18快照120拟合完成、RL106418交互/102858更新、旧context23/168、增强网络14/168、新refit0/144；含912最终和2h收尾理想余量3.48–5.74h，非完成保证。
  本轮6登记＋8容量＋2曝光＋3回放回归通过；首审计漏systemd工作目录在模型加载前失败，补全后独立审计通过。未改环境/输入/执行器/门槛。
- 上述本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  运行中稳定作业保留，24最终条件仍封存；开发/全RL共同边界/最终冻结/912评估和论文证据仍未完成，目标active。

## 2026-10-04 — 新旧teacher训练示范的配对质量审计

- 03:40UTC实时核对/fetch并读取main6c0cbb6e2edd8fa75a0b1762166ce4bb51f1584f、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS，工作区干净。
  main6c0cbb6完整3256文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/6c0cbb6e2edd8fa75a0b1762166ce4bb51f1584f/，tar SHAd1ddb7352859f63204e34882899ac7be69d7efee458aecf007856c26ecce581d。
- 新research72_teacher_data_comparison只读审计同32训练身份初始/选定teacher共64完整回合、70,400,000已保存子步；使用原v4指标，0物理/拟合/封存读取。
  逐协议/config/MJB/trace/chain/native/telemetry及原三指标核验通过；Spark单线程3GiB服务正常结束。新teacher任务29→32、strict18→20，8改善6退化；柱子合格示范仍只有2条。
  推杆P95力降低，但桌角接触时长4.112→8.583s、力模积分8.169→22.369Ns；不能称全面柔顺改善。人手两身份位移变化单列，负载指标保持，不以均值相同冒充所有字段相同。
- 本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  teacher_data_audit_source_v1单源文件核验，tar SHA83dd9acfc784111c72218cac63b7b179c3993a06e6373d8bfd9f29f005a9bd19；teacher_data_train_comparison_v1共68文件/1,677,577字节全核验，清单SHA3105de87e10c5254b4d2f0e020c095401f36e8d374675e5ed58cd8aaa8f31287。
  SUMMARY SHAd59f26e76abc0e0c69b412edc2130cc2dd270546eea4380671440492ccd41cc3，Git同字节；新增TEACHER_DATA_QUALITY报告，同步状态/联合进度/周报。
- 03:51采集37/40、context18/168、增强网络10/168，原RL/预算监护运行中。等待8验证完整导出；未新拟合/登记修订02/解封24最终条件，目标active。

## 2026-10-04 — 共同边界后的保守成本复算

- 承接已发布7d9fcd8ca3b17bbd0580b0b63e7c7f58c917c3a7；其3255源码文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7d9fcd8ca3b17bbd0580b0b63e7c7f58c917c3a7/，tar SHA dbde88e74d2cd1f1835bc7808465f938a7f411dd7e558b13fdc1f13d2c6ae226。
  本轮main/baseline实时核对如上一条；baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，无并行文件修改。
- 容量工具核验登记修订后，计入所有15模型49,500＋最大2750后续收尾步，原80k协议/优化器不改；新增算术回归共7通过。
  03:27实际快照下剩余开发理想21.91–22.94h，最终912物理22.82–23.94h，加2h收尾预计余量7.18–9.32h；额外等待/冷加载仍未计，未登记追加ESN拟合。
- 两源文件已核验共享本轮根budget_forecast_source_v5，tar SHA6e9833187cc81b4601a181bceb0ddce83bb512324dfe129a9cf9b801e06f6940。
  BUDGET_FORECAST_20261004_0327.json SHA8c962f7e502653c3bde882ba6f969b024d3d387563a1bd2f13bf2c351da5b44d，Git同字节；共同根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  只做只读成本算术，0物理/拟合；更新状态、容量、联合进度、周报，原训练继续、最终条件封存，目标active。

## 2026-10-04 — 全部RL共同最终边界前瞻登记

- 03:12UTC左右重新实时查询/fetch并读取main271a937444de7577d3432d627d2eeba1cb7efee3、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志/AGENTS，承接三个未提交源文件。
  main271a937的3249文件已核验归档arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/271a937444de7577d3432d627d2eeba1cb7efee3/，tar SHA28cdd9b55ff2c97683593ecbc53872f523f77137b84e7d7e67e11a8889d95bf9。
- 03:24:43UTC在全部模型均未进入49,500阶段时登记统一最终边界：5RL家族×3seed均选该自然完成checkpoint，实际48,126–49,500步；原80k优化器/奖励/runtime保持。
  依据已归档串行队列容量保护完整912回合，不使用奖励或任务成败。不可变队列后续两阶段精确SIGUSR1温和结束，最多2750额外步/模型全部保留/计成本，权重不参与选择。
- 新research72_rl_final_boundary以PID/start ticks/argv/父进程/UID/handler/pidfd核对目标；finalize_selection要求全部15边界与关闭hash证据，无缺失回退。
  本机边界6通过1跳过（缺pidfd），Spark7全通过含真实一次性测试子进程；原finalizer5通过。dry-run三个队列零信号，持续监护服务PID2471052已运行，尚未发训练信号，不创建定时任务。
- 本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  rl_final_boundary_source_v1两文件完整核验，源tar SHAe5903f2beb8dc3460627d391fab404cf5d91c94eeb6292be83497f4ea12cc9a8。
  AMENDMENT SHAe2b74294410aa3a97aa9ded6623f8a621424048101b3b5c7c32fe3159a4a7779；登记/DRY_RUN同字节Git证据，详见RESEARCH72_RL_FINAL_BOUNDARY。
- 更新状态、容量、分析方案、英文方法草稿、联合进度、周报。03:27快照teacher32/40（32训练task全过、20strict）、context16/168、增强网络8/168，RL72418交互/44856更新。
  新teacher尚未用于学生拟合，未登记修订02、未解封最终24条件；ESN泛化/全baseline最终比较/投稿证据仍未完成。稳定作业继续，目标active。

## 2026-10-04 — 真实RL续训首动作验证与队列容量修正

- 02:30UTC实时查询/fetch并读main1066bcad0142c706cd93d2c84382e0c18500885c、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS约定，原工作区干净。
  main1066的3244文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/1066bcad0142c706cd93d2c84382e0c18500885c/，tar SHA c50e57a1f5ac3fbef09cd0284959461be716eaef3783d4be8d465dc4a1a520e8。
- 新research72_rl_resume_audit在原生Spark分别独立加载VMC301/导纳301父checkpoint，以真实续训首观测重放随机动作，精确一致；
  每审计仅1次actor调用、0梯度/物理，保存运行中child execution原字节快照hash、不修改原件。六回归通过，非全段优化器/最终策略核验。
  rl_resume_action_audit_v1三源文件已核验；两结果SHA分别ab492d2cae78ea7721a0b39913de9ad99da4752470a05af17ed8235d06aa9ef7、
  4add155e9f0c35426a247e17499bbe5c692608a3371ed2a099b0cbb188387bda，Git同字节。源tar SHA ff9a4cdc27de1b18d2e225e320d21690977421aecd5dd42a20b9e43167154039。
- 新增VMC303/任务奖励303首段存档核验通过，后者train031因穿透2.560352mm在carry中止，真实5168步/338更新保留，未补成5500。
  rl_saved_state_audit_v3/AUDIT.json SHA a094a55f2627298175f4f0609ecd41aafb23e1595992273c443874427e0d5828，Git同字节；十首段不是全部15模型训练完成。
- 容量预测新增实际串行RL最长队列，6回归通过。02:43实际快照预测全80k开发31.28–32.70h、最终22.82–23.94h，含2h收尾余量+0.67至−1.88h且未计等待；
  不再只用总量除以四。budget_forecast_archive_v4四文件核验，tar SHA bd92cfac326de98edb7abafeae1c3cc4221792bb2d434601c5e893d8b8eb723e，详见CAPACITY_FORECAST。
- 上述产物根均arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  更新状态/联合进度/周报：teacher26/40、context13/168、增强网络4/168，q0/q2真实续训、q1等租约。未改冻结环境/gate、未发停止信号/改预算，24最终封存。
  下一步须据真实稳态明确共同预算边界以保护完整比较；不因某方法失败删回合，目标active。

## 2026-10-04 — 英文方法正文草稿与首任务奖励RL真实存档

- 02:17UTC实时查询/fetch并读main f6d22ffffa74e33e1e28dc8e49695cd22c3a7262、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS，工作区原干净。
  前者3242文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f6d22ffffa74e33e1e28dc8e49695cd22c3a7262/，
  tar SHA6187c1f6b96da35d5f42549a7351d88d6b929468b5c87c402b54cae312a1be36。
- 新RESEARCH72_MANUSCRIPT_METHODS英文稿按实际actor/trainer/evaluator/selection与统计方案逐项核对：给出储备池公式、
  精确task/strict口径、对照差异、912回合计划和推断边界。未选最终变体、未填最终结果或虚构新颖性/ESN优势，不改环境或gate。
  正文SHA b7d2feabb5c2477ce56943f0fd1c83bdabc9f50cec06cdc2576c3313ddd2b5c3；共享methods_draft_v1/docs/，单文件内容/大小/模式核验，
  tar SHA bf66c8495fda765fceeaab3afee10e84c710bb1dd4977375fd6acde1f8d1c41e。
- 新增直接任务奖励302/阻抗303两个首段存档独立复核（75/74文件、7/5维）：各5500步/4回合/1002更新，完整hash/回放/计数/边界/RNG/源核验通过。
  复用v1已归档源码，零动作/更新/物理/封存读取；rl_saved_state_audit_v2/AUDIT.json SHA a23428d103a1f393f98c269f837bffa786a99355185d11b28f7f9406a9b6f53f，
  Git同字节证据，详见RL_MEMORY_PREFLIGHT；不把存档核验当实际续训或任务成功。
- 上述本轮产物根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  02:22快照teacher21/40、context10/168、增强网络2/168；RL八首段完成/累计46875交互，q1等租约、OOM0。
  四实际仿真原作业保留，无新搜索/派发/预算修改。更新状态/联合进度/周报；最终公平矩阵、实际续训和最终论文证据仍未完成，目标active。

## 2026-10-04 — 首5D真实RL存档与名义控制完整开发结果

- 01:49UTC实时查询/fetch并读main66c72b90fdbcd7355b2fad2029f482ef24a555b4、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS。
  main66完整3238文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/66c72b90fdbcd7355b2fad2029f482ef24a555b4/，
  tar SHAded8abdba4cea715edc88cd627aa0750e90a34aab932faf3c73a9de774bea152。
- 六模型各5500步/4回合/1002更新已保存，包括5D阻抗302。新增独立零JAX/动作/物理审计核对完整存档、回放维度、
  计数/episode边界/RNG/条件顺序/44源与prior及24条原轨迹hash，全部通过；不是实际续训或最终策略评估。
  本轮服务器根rl_saved_state_audit_v1源/结果已核验，结果SHAbb3120147ee90a4c2e90447b373ad44818a39dcc84015380e4d495514a3b4d35，
  源包SHA717b32450b5902a52426740d1871ccb6302277aee4c1bbef422eecbbdd227261；Git同字节审计及首5D原manifest，详见RL_MEMORY_PREFLIGHT。
- 名义规划＋WBC开发8/8完整与独立审计完成：task/strict0/8，均carry；RMSE26.697mm、峰力矩均值37.532Nm、峰速度均值.36838m/s。
  SUMMARY SHA6c2c6ec9784bcdbedcf0a742e607a46f874873279eef6ed2fce8142806062718，Git同字节；原件additional_development_v1/nominal_development/。
  低误差不抵消任务停滞，非最终留出结果；见CONTROLLER_CONFIRMATION新增名义参考，不混旧64确认分母。
- 实际01:54成本快照：既有剩余开发理想31.569–33.038h，最终22.824–23.942h；不新增回合也只有总余量+1.199至−1.387h（含2h收尾）。
  budget_forecast_archive_v3全4文件核验，tar SHA5a48ce61fa3d6f0c725380dc6ead5c86f0ced0b2483588b3a9f5b3f24f9d909f。
  不绕过开发闭环替换新teacher重训权重，不登记修订02、不减最终baseline；原稳定作业与封存条件保持。
- 上述本轮根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  更新状态/联合进度/周报，真实续训、更强学习组、teacher40与最终比较未完成；保持研究目标active。

## 2026-10-04 — 实际物理装置核验与论文结论范围

- 01:30UTC实时查询/fetch并读main58fcf97d6e90d08f6feba94b7740365609815f20、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志和AGENTS，工作区干净。
  main58完整3235文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/58fcf97d6e90d08f6feba94b7740365609815f20/，
  tar SHA9281c6b48f7c11579835f1b4b7724b9b4e6b2ddfb3b22a91c8b29c92df81b163。
- 新零积分只读审计核对公开train000精确MJB、七个实际源码hash、1375帧旧mocap位置：球1kg/r60mm、物块80g自由体，
  无payload weld；实际人/杆为有限质量驱动机构，但模型仍有场外旧mocap。保留审计早期粗假设被拒绝的记录，未修改模型来通过。
  解释14/80N驱动力不等于接触力上限、2s前球被固定、柱为特定低摩擦小几何；不冒充人体安全、广泛环境或硬件验证。
- 本机1线程/3GiB成功审计.219s；全部3文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/apparatus_audit_v1/，
  结果SHAcb30b726a8acc310d2607bd38a44785730aae02e6b5c527c9f01d23f10e38648、tar SHAd5c178a5316e26436f16f5672569df115ada885a19db4b1a9e41fe4eda568321；
  与服务器原execution/model/trace再次关联，Git同字节小证据。详见RESEARCH72_APPARATUS_SCOPE，更新方法定位/状态/联合进度/周报。
- 01:44UTC新teacher14/40、名义7/8、context7/168；四RL模型首段各5500/1002，后续两模型4750步；第三队列等租约。
  两queue memory.max事件447/685、OOM0，稳定作业不重启。无新候选、环境/gate/预算修改或封存读取；最终公平矩阵仍未完成。

## 2026-10-04 — 纯ESN固定矩阵独立重建与实际归档关联

- 01:10UTC实时查询/fetch并读取main5b50c0cd87fab8cb711979ef1d15069ecf2fd762、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志，工作区干净。
  main5b50完整3233文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/5b50c0cd87fab8cb711979ef1d15069ecf2fd762/，
  tar SHAa6f923d6d9b9a864c02470c6aad5b1018db0438a26ba1dc9e977a171457d5409。
- 新零训练/零推理/零物理审计从seed独立重建12个ESN＋6个无记忆拟合的全部216保留候选固定矩阵、时间尺度、gate及字段合同，
  全部精确一致；每拟合两项内存负对照拒绝修改循环矩阵/额外隐藏层。原权重不改，MLP/RNN不纳入固定矩阵断言。
  本机1线程/3GiB完成1.183s，再与Spark模型/metadata/候选逐hash关联通过；不证明稳定、泛化或ESN优势。
- 全2文件（实际源/结果）已核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/fixed_reservoir_audit_v1/，
  tar SHA2b6ea4ba8a0db3bdde62b10dffea7f2ebb0257b46bcf2288b12d525fe11717bd；结果SHAb01441975949630d46b0b579b36e25bf40fdc52fd043390810c6155af3d4fdcc。
  Git同字节结果，完整方法/源码hash见RESEARCH72_INPUT_AND_MEDIA_AUDIT，更新方法定位/状态/联合进度/周报。
- RL第二模型梯度开始后两queue峰触及3GiB、max事件169/148，OOM仍0，anon约1.83/1.87GB、file约1.25/1.26GB；
  保留页缓存回收的真实观察，不沿用旧max0断言，不增加限制或重启作业。实际新ESN开发和teacher采集继续，最终24未开封。

## 2026-10-04 — 首批真实RL存档通过与最终评估容量复核

- 延续实时核验main759ba7b1d847b660af201ddb51e528ebf9b465b9、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  main759完整3231文件已核验归档arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/759ba7b1d847b660af201ddb51e528ebf9b465b9/，
  tar SHAc2d498bb33101a0bef38f966f80061135f27ef8897e7ab2bb938fdd475971b60。
- 00:56UTC导纳301/VMC301各5500真实交互、4完整回合、1002梯度更新并保存。独立零积分/零更新检查每个75存档文件、
  原始manifest、回放形状/终止计数、runner/agent/奖励计数、RNG可加载、源/prior不变，通过；未将其当真实续训或最终成功。
  两queue累计峰2.67/2.66GiB，max/oom事件0；已轮转下一模型，第三RL等租约，不重启稳定作业。
  Git含两个同字节初始manifest，权重/回放位于本轮根rl_office_adaptation_v2，hash/精确路径见RESEARCH72_RL_MEMORY_PREFLIGHT。
- 00:44UTC新的公开成本快照：既有剩余开发理想32.697–34.220h，最终912回合理想22.824–23.942h；
  再追加144开发会相对总窗口欠2.370–5.186h（含2h收尾假设）。暂不登记修订02，保持全部baseline和最终分母；真实并行/启动成本仍须核对。
  本机零物理预测与源/测试全4文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/budget_forecast_archive_v2/，
  tar SHA8412d5cc484555c83d09365e5bb48bf5f8cdb32d2a21f7b4938d8765dfe93cf6；详见RESEARCH72_CAPACITY_FORECAST。
- 本轮只有核验/文档/小证据更新，未改训练或环境；最终24封存，未完成最终公平矩阵，不宣称RL收敛或ESN最终优势。

## 2026-10-04 — Teacher完整确认、数值敏感性与真实RL启动

- 00:32UTC实时查询/fetch并读main `92d1ea1290dc4b146520224fd86cce90777a9ffb`、baseline `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`日志及AGENTS；无新协作改动。
  main92完整3226文件已共享核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/92d1ea1290dc4b146520224fd86cce90777a9ffb/，
  tar SHA53195da043f6dc2919af8112d8ebff88b7395f7a11afa61515c053770331133c。
- 64/64 teacher/经典开发确认及四队列独立审计完成。预登记选择teacher09、adm03、imp02、vmc11；teacher8task/7strict，
  相同原teacher8/4；development006柱子/link6外穿透.313866810mm失败保留。所有经典确认0/8task，有限搜索不能解释为其普遍上限。
  新报告RESEARCH72_CONTROLLER_CONFIRMATION_20261004给出全部候选与hash，Git同字节选择/汇总；不是ESN/最终保留集结果。
- 三步长3秒球撞诊断完成：50→25μs峰力−10.437%、力模积分+.504%；50μs前缀精确重放。正式步长不改，峰力仍有数值敏感性。
  已知teacher通过最终入口55s逐值重放及独立审计；不代表真实24条件或全部38方法通过。
- 00:35UTC四物理进程：teacher采集、名义WBC、两个真实RL训练；第三RL等租约，新context队列已接续。
  两RL实际子服务峰1.93/1.94GiB、OOM/max事件0；首回合完整，warm-up更新0，真实梯度/保存峰值仍待查。稳定作业不重启。
- 官方SimbaV2 HEAD86899c277cdc697b2b02d827243de1ea93f20a1d完整225文件源码归档并与live逐hash匹配；
  上游归档不包括运行库/权重。独立RL报告额外核对每回合checkpoint manifest，并展示失败阶段、恢复删失；14项相关合成测试通过。
- 本轮产物共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，
  对应followup_v1、controller_confirmation_v1、public_numerical_probe_v1、final_rehearsal_v1、upstream_simbav2_source_v1；精确hash见专题报告/Git证据。
  更新精简RESEARCH_STATUS、联合进度及周报；最终24仍封存，学习修订02未登记，尚无最终ESN优势或可投稿结论。

## 2026-10-03 — 独立RL actor回放准备与缺失证据保留

- 实时核验/fetch main c5343841a29987bc1468c9143ecfcfda4ce48399、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6并读两日志。
  main c534完整3223文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/c5343841a29987bc1468c9143ecfcfda4ce48399/，
  tar SHA0d249b49abe926daa5dace405429578a06ed8e40dc18b1ff27dbf182649aeca3。
- 新独立进程从冻结官方RL权重重算raw actor，核对canonical48、normalizer/计数、checkpoint/训练源；覆盖失败/短回合，0新物理/拟合。
  汇总器显式记录回放覆盖；缺失不删物理结果。1线程/3GiB下14项合成测试通过，真实RL尚未运行此审计，不混称baseline完成。
- 源码核对RL奖励metadata未拼入actor；调参7/5/7维语义保留。现有物理/过滤器审计继续覆盖本入口未重建的控制律与伺服。
- 共享根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_actor_replay_engineering_v1/evidence/，
  5文件/52,258字节，manifest SHA f4db3b3e57967170bcc97f12419e5546eda59817b61c176f87a9fda52d816472，
  tar SHA a6a4251a6ffe93842e9074d1cf070bfbca237c63771f007b80620d23423a261d，已逐hash核验；完整说明见RESEARCH72_RL_ACTOR_REPLAY_20261004。
- 23:47UTC确认42/64，四稳定仿真未改；增强组/RL/teacher新采集待前序。24最终仍封存，学习修订02未登记，尚无最终优势结论。

## 2026-10-03 — 全方法与五类接触图导出工程核验

- 23:27UTC实时核验并fetch main4b72e83c422d9fbd42896b208e8f8028ae88d3b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两日志和AGENTS；无新远端改动。
- 最终图入口只消费已有审计统计，不选模型/重算CI；16方法固定顺序，保留缺失、seed、无配对NA、全部五类接触。
  成功子集的P95/力模积分仅条件诊断，图注不作总体/因果优势；三项合成测试及三图目视检查通过，0物理/拟合/封存读取。
- 已核验arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/figure_engineering_archive_v4/evidence/
  10文件/2,056,068字节，manifest SHA7fce50cef55ca5a05c2f1c8132746af0726a996dcbdde54ffe999e6f9613754f，
  tar SHAf4ee52a04dbeb355b4df1bdd606bea4f0767f9a8215fdc628ff5ab377f4bf479；源/合成输入/六图hash见RESEARCH72_FIGURE_EXPORT。
- Git保留v2和v4真实合成manifest，说明仅版式数据；v3本地试排未伪作服务器归档。teacher/经典确认继续，RL等前序；最终比较未完成。

## 2026-10-03 — RAL机器人储备池作者稿及近年先例核对

- 延续实时核验main4b72e83c422d9fbd42896b208e8f8028ae88d3b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  main4b源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/4b72e83c422d9fbd42896b208e8f8028ae88d3b7/
  全3218文件核验，tar SHAaf0f17eeba547949e5b5ec11eba394b3bc426062fd8c446d15dcf6aefea98018。
- 阅读Shen等arXiv2409.06961v2的完整HTML正文/公式/表/参考文献，对应DOI10.1109/LRA.2024.3523229；图未独立渲染、未复现实验。
  其ESN/物理储备池、T-S分组读出和200Hz软体硬件控制已有明确先例；人工抗扰施于计算储备池，不当本项目机械臂避让证据。
  补查ICRA2025 RC+FORCE及2026 SSRN纯运动学ESN力估计，前者仅元数据/摘要、后者是预印本且未读全文；不夸大阅读范围或方法首次性。
- 更新RESEARCH72_METHOD_POSITIONING及进度/周报：论文贡献仍须靠同数据机制消融与公平闭环结果，未引入新baseline/预算或改环境/gate。
  23:06UTC参数确认16/64、四稳定仿真，其余等前序，真正24最终未开。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/related_work_review_v2/全8文件核验；
  tar SHA2e68435b5e3ea6ca8f79efb0e698b8782d7c05cb500506b1e2477cd1f9cb3406；HTML SHA61f4a5baada4835aabbddaf505d83c19c16e3e648e212e5ae8fa25790dbf9a46；
  阅读记录SHA84f7682a953d784ee260e6c846f815b25f9747904846ce4404b3d82db165b77b。保留广搜不相关命中，OpenAlex两次429未伪作已读文献。

## 2026-10-03 — RL组合内存有限预检与RMSE解释

- 本轮延续核验main558947de4d9aef526768f6af86c0f94dd331b3a0、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  main558源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/558947de4d9aef526768f6af86c0f94dd331b3a0/
  全3215文件核验；tar SHA484d74b444652d2053523998cc09f63e4514bc436efd04ef0da62eae926b5a13。
- 22:53:57–22:55:16UTC实际learner依赖＋80k Replay＋1,086,394,368B物理队列等量压力，CUDA单线程3GiB/无swap，
  4周期/8工程更新峰值2,844,037,120B，余359.715MiB，oom/max事件0。原工程7D73文件集合/hash不变；8更新丢弃，不计训练或候选。
  这是零物理静态压力，不是三learner+真实仿真/存档峰值保证。真实5500步仍须核验，不改运行资源与训练源码。
- 共享根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_memory_probe_v1/execution.json
  SHA26885a47d096fd3bcce484544bbb86ca7812b746524d540538d7dc7b83193297；相邻rl_memory_probe_source_v1实际脚本
  SHA9be4dc23c1ae0e0fc8a880d08ea241eb249e570509abd9cc67aa77aef36b2593，两端核验。Git含同字节原执行记录，语法/有限真实运行通过。
- 核对EpisodeMetrics.sample：RMSE是物理子步末端到当前任务阶段goal距离，各控制器切换时间不同。
  最终报告明确Stage-goal RMSE与解释边界；不改任何计算、排序或gate，不把低误差但停滞称柔顺优势。
- 更新分析方案、联合进度、周报、RESEARCH_STATUS及RESEARCH72_RL_MEMORY_PREFLIGHT。teacher/经典确认运行中，
  新组/RL等待，24最终仍封存，修订02未登记，无ESN最终优势结论。

## 2026-10-03 — 初始264回合完成与全部候选的描述报告

- 开工实时核验main94fdf073be3c03c437d88b656ea5e6903f3c0796、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，fetch并读两日志/AGENTS。
  既有main94源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/94fdf073be3c03c437d88b656ea5e6903f3c0796/
  3211文件已核验，tar SHA a9004df3d23c08d85e126e2726f2834f118c5d2fd0bf6d69228a0d948eee1e3f。
- 22:40:59UTC初始33模型×8条件264回合及四队列独立审计完成：261完整/3短回合，105task/51strict是全部候选账本，不作最终方法率。
  ESN点版19/24task、9/24strict，积分11/24、4/24；六matchedRNN均selected_update0继承ESN，不能据此宣称充分优化RNN不如ESN。
- 新零物理报告逐hash关联264独立审计/接触指标和33训练记录；保留各seed/variant、短失败、暴露NA/恢复删失。
  点版ESN推杆P95均值21.432N较无记忆24.303低，但力模积分36.733Ns较33.242高，暴露集合不同，不作全面优势结论。
  原事件指标为v2，最终须用v4独立复算；没有改门槛/指标、拟合或开封最终条件。
- 服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/public_initial_report_v2/REPORT.json
  SHA adb7ff8e71117d09a612796e6a56ca02b17b430054ca707f51832112194d7b4d；报告脚本SHA8c78f2f0b78228b89e790826c38dda11fd1de02ea350e1b17a07b37cecca8d32，
  selector依赖SHA6b1785c55c183982c7040293276987c3a9e87ef70914934bf598b649db530354均两端核验。Git含279518字节同字节报告。
  v1只读汇总因str/Path类型失败，源保留；v2在独立目录修复后141ms完成，无仿真重跑。3聚合边界检查及真实全批对接通过。
- 更新RESEARCH_STATUS、联合进度、周报和RESEARCH72_INITIAL_DEVELOPMENT。64回合teacher/经典确认开始、四仿真内；
  新teacher采集/增强网络与ESN/RL适配仍待前序。24最终封存，修订02未登记；不以初始开发结果声称可投稿或ESN独占优势。

## 2026-10-03 — 首撞短步长诊断登记与诊断成本分母

- 本轮延续实时核验main f40b1ad05d43373c380d71b06807b7ee9785a8b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；稳定仿真保留。
  f40源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f40b1ad05d43373c380d71b06807b7ee9785a8b7/
  已核验3206文件，tar SHA4139bca72fd41b21393b8294f016e3028958ae69402c8dc7bc4c9abd565f3844。
- 22:02:45UTC登记原teacher/train_000三条3s前缀，dt100/50/25μs，最多9模拟秒/210000子步。
  只改诊断MJB timestep并验证还原整个二进制hash；50μs前缀须与已有轨迹精确重放。正式55s/50μs/原gate及输入不变。
  独立runtime的525旧文件与f40逐hash一致，仅新增诊断和测试；未对运行源热改。
- 有限服务sii-r72-numerical-probe-v1/PID2403221，1线程/3GiB/CPUQuota100%，等followup完成后取一共享租约。
  当前waiting_for_predecessor/0派发；worker拒绝无存活租约owner的启动。无定时任务、无新增模型或学习预算修订02。
- 原生最终版本3模型/角色测试、本地4预算＋2账本检查通过；均0积分。诊断attempted/completed/耗时保留，
  但已知重放成功和短探针false不混任务成功/失败分母；预测对新增短探针保守计完整回合成本。
- 服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下public_numerical_probe_v1/SPECIFICATION.json
  SHA234712686ed7ee00571a0ec3886c3f134ae33c91631d87024111cdb67ca892a2；Git同字节证据。
  相邻_numerical_runtime_v1实际脚本SHA86a8d8907b93464d9a2c42ef46431534f1cd2697e486e1a04951f8a91b445a36；
  incoming/research72-numerical-overlay-v2.tar.gz SHAc722b43ba619c67d5588a4f8df33f837850e56c980028f7f8058a5a13c567e60两端核验。
- 22:05UTC初始246/264，第七完整身份ESN/matchedRNN各4/6task、1/6strict；matchedMLP2/6strict、memoryless1/3、普通MLP1/6、RNN0/6。
  全264整阶段审计/teacher确认/增强组/RL尚未完成，24最终仍封存。诊断边界及准确共享路径见RESEARCH72_NUMERICAL_DIAGNOSTIC。

## 2026-10-03 — 全102学习actor字段审计与本地完整三机位工程验证

- 延续核对main c84a7cd8aea0ab1874d7c3682773e772445c2cc5、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；运行快照不改。
  c84源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/c84a7cd8aea0ab1874d7c3682773e772445c2cc5/
  核验3201文件，tar SHA20595252d883a0ff09b4c084544561ad45416e0f6eab6b9664d497a9752d253b。
- 本机21:23:55–21:24:06UTC对全部102模型回放train_000：140250时刻请求与导出最大差0，扰动未声明30字段动作逐值不变，
  82500状态检查不变。只读输入、有限幅值和checkpoint身份通过；3负对照涵盖隐藏状态偷用字段/输入原位改写。
  是声明18字段的序列边界检查，不证明上游传感器真实、不覆盖RL、不是任务通过；0拟合/0物理。
- 21:30:42–21:31:02UTC本地已知teacher完整55s三视角：18.771s渲染＋1.692s全帧解码，1375帧/25fps，峰值691216384B。
  输入状态/模型不变，仅mj_forward；6时刻三视图拼图目视核对。不是ESN或新最终成功，最终38模型仍按固定首条件全展示。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  actor_field_audit_archive_v1全3文件核验，结果SHA7aaba52990beb7423b707ae243434c8420f4f38ef51723d52a3ebb4dec9fc5d6；Git含同字节全102行。
  media_rehearsal_archive_v1/evidence全10文件/18244126字节核验；execution SHA464dbe742f17fa3e65c247cbf30fe8d9f4f637b323a9ec72f6b14266ad113f5f；
  MP4 SHA d6a009c7240eeb8877f4ce853331044c349787083fe4227a9c1b68d07ed11b0b；tar SHA2a8e5a140687976644095e88c189a544b0610f5afa7c63215ddbf8131366659d。
  实际本地路径/命令保留，脚本混合源及边界见RESEARCH72_INPUT_AND_MEDIA_AUDIT。
- 最新物理检查220/264，四队列稳定；24最终封存，修订02未登记，不因媒体变快削减审计预留。teacher/增强组/RL与最终比较未完成。

## 2026-10-03 — 第六开发条件失败与剩余容量核算

- 本轮实时核对main792316711f11e43a12e06bfeb389f87b015fe040、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两日志/AGENTS。
  main792源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/792316711f11e43a12e06bfeb389f87b015fe040/
  核验3198文件，tar SHAdfae85ee383bb48c1044cfa6c22b3afbe4ef98b26543e07532cc27a4ee2fdb55。
- 21:09:42UTC只读成本快照209/264，206个完整回合中位351.820s/P90378.758s。完整失败计时保留，短回合计成本但不压低完整预测。
  15RL全80k上限＋已有待执行组理想还需35.253–37.829h；新增144回合加3.518–3.788h会挤占最终912回合。
  当前不登记修订02/不新拟合。理想容量不是实际排队保证，2h收尾只是规划假设；真实RL争用/物理续跑待验证。
- 第六开发身份33候选完整：ESN/matchedRNN各4task/0strict（n6）；matchedMLP2/2、memoryless1/1、ordinaryMLP2/1、ordinaryRNN2/0。
  ESN已放置四条柱子/link7穿透0.223096–0.593794mm；303temporal RMSE247.992mm停carry。未改gate/未删失败，阶段独立复核待全264结束。
- 新纯标准库预测工具3项检查通过：累计RL去重、缺失阶段拒绝、短回合不压低全程耗时。本机0物理/拟合，源与预测共3文件已hash核验共享。
  服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  EXPOSURE_SNAPSHOT_20261003_2120.json SHA97c4dfbba35b60a1f606bc83490106c0e28539a8f27ebe9d7bd157fe5d0cdd55；
  budget_forecast_archive_v1/research72-budget-20261003-2120.json SHAeaa9c54e7f9cab6fdd40fc3e9fc04e2994c27189b2e1e1b9e31eed8fd1b802d5。
  文件名2120不是实际生成时间；完整口径/命令/源hash见RESEARCH72_CAPACITY_FORECAST。
- 四稳定物理队列保留；teacher确认/再采集、增强组及RL仍等前序，24最终封存，尚无完整投稿结论。

## 2026-10-03 — 官方RL GPU有限吞吐与剩余预算依据

- 延续核验main788d6814d0ed3ac2cc5bb5a7cacafa367a66e539、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  788源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/788d6814d0ed3ac2cc5bb5a7cacafa367a66e539/
  已核验3195文件，tar SHA04457028dd9328893be595a922833daa507e552e65666416df1d6a0f292d7b53。
- GPU0空闲/96GiB可用后进行有限吞吐探针：官方actor128/critic512、batch256、UTD2、同80k计划；
  每维度1冷＋8预热＋32计时共82更新，总164工程更新，0物理/0候选，权重全部丢弃。同步等待JAX参数树完成。
  5D动作0.773ms＋两更新17.449ms；7D0.839＋18.568ms；冷周期71.160/16.000s，同进程缓存复用，不作速度胜者比较。
  20:47:22–20:49:03UTC，单线程3GiB，峰值2,220,003,328B。组合物理内存和3learner争用仍未验证。
- 原工程检查点5D/7D各74/73文件在实际探针后经独立递归hash核对完整集合/字节精确不变；
  语法检查及实际有限运行通过。不能把这些工程更新给baseline计入真实训练步或宣称已收敛。
  实際执行脚本SHA0ed30caf396db249c1b304767344a84ae546979a9bfe39f576bade140a9293c9；
  本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_throughput_probe_v1/execution.json
  SHA687fdaf8d61f842bdd3c7572891e2064ab11e364d1895cc8cc3b9a38153a9861，已两端核验，Git保存小型同字节证据。
- 两条件teacher筛选中领先09/07均不同于原配置，需要为40条实际采集留预算；八条件确认前不选teacher。
  可选共享ESN交互读出再拟合若数据改变须144开发回合，目前修订02仍未登记。
  20:56UTC初始198/264、第六条件32/33，四仿真持续；RL v2/teacher确认/新组仍等待，24最终条件未读。

## 2026-10-03 — 170公开轨迹首撞时序核对与柔顺性归因边界

- 延续实时核验main be473ca6d6c38a71182032504b8d5194ce235ac7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  be473ca源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/be473ca6d6c38a71182032504b8d5194ce235ac7/
  核验3189文件，tar SHA f0306577208e5612ff08a225fe9b850ba444f5215892eb65d538b05c1bf07312。
- 前五完整开发身份33初始学习候选＋原teacher共170条全部纳入，4时序回归通过。只读Spark原生20:29:31–20:30:04UTC，
  单线程3GiB、CPU23.299s，无新物理或拟合。球首段接触0.45–0.50ms，至下次真实actor计算9.20–32.20ms；
  170/170球窗峰值和首段接触结束都先于那次计算，已保守考虑50μs采样余量。
- 峰值5485.92–7407.39N不能当已标定人体安全受力，也不能证明25Hz策略已即时抑制首次碰撞。
  碰前姿态/动作、公共4ms WBC和被动物理仍有作用。所有峰值继续报告，不改gate/actor时钟；结合后续恢复/持续接触解释柔顺性。
  此为公开开发事后诊断，不是最终盲测、ESN胜者或RL已验证。全部失败/短回合均保留。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下：
  public_impact_timing_v1/IMPACT_TIMING.json SHA cd8a9ec1f707fdb1be008eceb5331d83ce17e2a4f1ee7d9a929616aa141686e8；
  SPECIFICATION SHA166648074e86fc909ddbed9dd1bc183878f36c6cace5035025eef0c04f1ffe33；
  EXECUTION_RECEIPT SHAa1c9d99d50f02a6cae2f075308954314b81f41cf76f45e311e698a9a612c0eea明确是基于日志补写的事后说明。
  实际诊断脚本SHA2a7db52731480f3dae1bed9c0c47df4c62cbb8c7352898a5a86523e179a19fa5；精确入口见RESEARCH72_IMPACT_TIMING。
- 本地单线程3GiB绘图已目视核验；服务器impact_timing_plot_archive_v1全4文件核验，tar SHA
  fc1c842de54cac4a87d1f25ccd076f9b09db3ebb9feed393cb1dddf6d632bfd3；PNG SHA c9cab76a261e3f6b567776da6a5e1efd8b63ac2f8e8c78f3b44e2c291eb94a8a。
  Git含小型全部结果和图；不改历史路径。初始20:37UTC184/264、4稳定仿真，teacher确认/新组/RL v2仍等待。
  最终24封存；学习预算修订02尚未登记，无最终可投稿结果。

## 2026-10-03 — RL首次开训前轮转登记、第五共同条件与统计区间解释

- 19:55UTC实时核对main2da38895ce8a91eb9cc7b47d94a72e53ff615166、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  读取两日志、同步skill和AGENTS，四稳定仿真保留，未读真正24封存条件。
- 初始20:15UTC169/264，五身份各33完整。第五身份ESN/matchedRNN各4/6task、1/6strict；
  matchedMLP2/2、memoryless1/1、ordinaryMLP1/1、ordinaryRNN3/0。三条已放置ESN因pillar/link7
  穿透0.209686/0.279906/0.573083mm失败，303temporal RMSE250.986mm仍carry。原gate不改、失败保留。
- RL原逐模型80k顺序存在晚排方法零checkpoint风险。首次office训练前登记累计边界5500/27500/49500/71500/80000的轮转，
  同15任务、80k总计划、奖励/模型/训练身份/截止/3租约；完整恢复优化器/回放/RNG。先保证所有组有初段。
  有限队列完成不冒充全80k或收敛，实际步数/截止另存最终候选；更多启动可能增加编译成本。
- 16调度/模型汇总/冻结工程回归通过，包含真实队列入口25个模拟分段父checkpoint和新增步核算；实际物理续跑未验证。
  精确核验旧等待器PID2332615、零队列后仅停止该等待器，旧execution字节不变；新v2 PID2384702等待同followup。
  独立runtime_v4仅两调度文件不同，trainer及其余源逐hash一致，无物理中断。主动选择器/成本快照识别登记的活跃v2。
- 主机arm1@192.168.31.70，本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  AMENDMENT_RL_ROUND_ROBIN.json SHA3ff1ae22f310825de701344df84d8f74c1c18b27e7719c448a5b563c009a7d46；
  rl_dispatch_change_v1/execution.json SHAb99f9aa0601b553e67258bfc4529d0b0498856ad9c6653fdd505c34159c5d1ee；
  活跃rl_office_adaptation_v2，旧v1仅历史登记。相邻research72_20261003_1149_rl_runtime_v4保存真实混合源链。
  incoming/sii-r72-rl-dispatch-overlay-20261003-2045.tar.gz已两端核验SHAfa888c0e518ac15b2681ba0ebaafc0e3c597a683e5a346acac884af4a8d45509；
  文件名2045是标识，实际20:13:54执行。完整报告RESEARCH72_RL_DISPATCH_20261003.md。
- 统计报告区分观测恒定/重抽恒定/点区间，避免将[1,1]当新条件的确定保证；原10000重抽和数值区间不变，18项回归通过。
  本轮无新ESN拟合、无学习预算修订02；teacher确认和新组仍未完成，尚无最终投稿结论。

## 2026-10-03 — 本机99轨迹覆盖诊断与第四共同条件完整

- 延续main a5ed961ef2216033e2311f964ba4617dc80f0de5、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6实时核验。
  main a5ed源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a5ed961ef2216033e2311f964ba4617dc80f0de5/核验3178文件，
  tar SHAd3bcddf8c1b8756a8daf64f7461cb690cae7594dfef0ec42f570cd96f8ea5eaa；未改运行快照。
- 新本体覆盖诊断固定前三完整开发身份全部33候选共99轨迹；18D已有actor字段、固定物理尺度与clip。
  校准排除整个自身teacher训练身份，18身份24750帧的近邻P95=0.308898；不用验证/开发校准，不含储备池状态。
  ESN303temporal/condition001超参照72.7%、RMSE124.44mm；302temporal成功仍46.9%、95.20mm。
  clip约0–0.3%，不能只改裁剪或把距离当失败原因/校准OOD概率。所有失败和短回合保存，图无胜者筛选。
- 本机airpig/NumPy2.4.6/SciPy1.17.1，单线程3GiB，4.163秒；2合成检查通过；Spark只读提取核验所有trace/AUDIT/model。
  0新物理、0拟合。诊断说明RESEARCH72_PROPRIO_SUPPORT及Git内174KiB图，PNG SHA c7d4a4f4397148972371da7c91a435749f478a8e6acdda77754097e10c9d20ea。
  初图标签拥挤仅修排版后目视核验v2，未改数据；代码/数据注册时钟与真实执行命令记录在EXECUTION_RECEIPT。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下：
  public_proprio_export_v1；proprio_support_archive_v1核验5文件/tar SHAdc07c9d45036ecda010dd2124208f1d421ff6628f04d3490211eaa608363f6b4；
  proprio_support_plot_archive_v2核验4文件/tar SHA78f681f29e7f14bfb46810f484a2ef45057e7dc2a9d4a72297cbefa1bc931fad。
- 19:37UTC143/264，第四共同身份ESN/matchedRNN各5/6task、4/6strict；matchedMLP2/6strict、memoryless1/3、
  ordinaryMLP1/6、ordinaryRNN0/6。初始候选不是最终方法统计；RL/新组/teacher确认等待，4仿真稳定，无其他活跃agent。
  真正24条件封存，修订02未登记；当前没有完整投稿结论。

## 2026-10-03 — 选定teacher共享读出再拟合入口准备，尚未启动新预算

- 延续实时核对main ad957af96444b418c0bceb8063bd0e72031bd8fc与baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；重读AGENTS收尾。
  ad957af源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/ad957af96444b418c0bceb8063bd0e72031bd8fc/核验3175文件，
  tar SHA58f3b23608d8c012db9159c0284fcef932aa24567964138134a3cbbb6b795dca。
- 新refit-data-receipt要求teacher选择/执行/config/数据hash和合格账本一致，未完成采集、标签非真实或最终已开封均拒绝。
  同teacher验证0新采集；不同teacher要求40真实身份导出。只用train/imitation_validation，保留拒绝账本。
- 可选context-readout-refit沿用12组ESN ridge和128储备池，加已验证固定G交互，只训练读出；同特征MLP/RNN获得相同特征。
  网络沿用此前跨3seed验证选好的point学习率/4000更新。数据相同则不重复训练/评估普通网络，新增12模型；数据变则18模型。
  服务器权重引用保留真实路径，不能在本机伪造挂载；登记时在服务器核验复用权重，最后模型选择支持声明的不同数据谱系。
- 14项合成登记/数据来源/跨seed选择/全38模型入口回归通过；没有实际拟合或物理重放。
  RESEARCH72_READOUT_REFIT_PREPARATION明确拟议cap60、额外96或144回合及成本，但AMENDMENT_02尚不存在，当前有效cap仍48。
  必须等teacher确认和剩余预算核定后才能正式登记/拟合；不让额外ESN搜索挤掉已登记baseline或最后24小时评估。
- 19:19UTC初始131/264，第四条件32/33；4稳定仿真、无新增物理；真正24条件仍封存。
  已完成工程，未完成新结构学习/完整跨条件比较/投稿证据。新代码将在本提交对应source目录核验，不改运行快照。

## 2026-10-03 — 补齐放置阶段接触负载、保留原事件统计及全失败安全审计

- 18:53UTC实时核对main2bd499594f45fce1888e34128bdaa67d260dc23a、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；读取AGENTS和两日志。
  main2bd源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/2bd499594f45fce1888e34128bdaa67d260dc23a/核验3173文件，
  tar SHA966cc1894a3c16e39ea745d1e0ea8a9b88bda61a31cec823e23c52332030f8f8。
- development_001的全6ESN与teacher曲线暴露晚期人体接触。新增metrics v4全实际时长/原事件窗外负载，
  保留原窗口、恢复与所有gate；补充属公开开发观察后、最终开封前登记，不宣称最初预注册。
  final report将短失败、完整失败、缺字段和无接触分开；安全表包含短回合外穿透/edge及执行器幅值/变化率审计。
  external不含payload而edge含robot或payload，不把重叠列相加；补充表不作配对优越性推断。
- 本地14项测试通过；初次入口缺PYTHONPATH导入失败已纠正。Spark原生7条完整55s只读回归：所有旧数值/结果精确不变，
  ESN302point窗外人体力模积分1.430966Ns/接触0.29505s，原teacher0.167416Ns/0.02675s；不是安全/优越性结论。
  0新物理、0拟合。服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下
  supplemental_contact_regression_v1/results/REGRESSION.json SHA29ee8fff3ccd85bc50746341814d8278f64fd526aae9c92e099220ef29075c04，7产物hash核验。
  public_condition1_esn_curves_v1/保留全6候选+teacher图；精确源/图hash见RESEARCH72_SUPPLEMENTAL_CONTACT_20261003.md。
- 18:59UTC初始学习开发115/264，前三条件各33完整；第三条件总11task/5strict，ESN/matchedRNN各3/6task、1/6strict，
  matchedMLP2/6strict、memoryless1/3strict、ordinaryMLP/RNN0strict。含损失候选，非最终模型统计。
  4稳定物理队列未重启，RL/确认teacher/新组等待；真正最终24封存。尚无最终胜者或可投稿结论。

## 2026-10-03 — 38模型冻结前汇总、相同teacher无重复采集与方法定位

- 本阶段基于已实时核对main9d996dde19adf4bb816cc403b51bc5025f527f32及baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；收尾重读AGENTS。
  main9d源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9d996dde19adf4bb816cc403b51bc5025f527f32/
  核验3170文件，tar SHA586c79474bf49dd7d05cca9d679b130014472e4374956fa11f6cdbf4f48d4bee。
- 新research72_finalize_selection仅汇总公开选择：6学习族×3seed、5RL族×3seed、teacher/三经典/nominal共5确定性方法，合计38。
  缺任何family/seed或混用跨seed variant则阻止冻结，不以开发成功资格筛模型。RL按最新完成训练边界选checkpoint，
  不读reward/任务结果来挑权重；保留实际累计步和stop_reason，共同cap不冒充每族步数严格相同。
- 发现再采集在teacher相同时记录complete_skipped_identical_teacher，而最终锁只接受complete工作收据：
  新汇总器核验原teacher/config/选择hash完全相同且新增物理0，再写明确的零操作closure；不改原执行状态或伪造40条新示范。
  五项合成检查通过，包含38模型全失败仍保留、缺失seed/族、混variant拒绝及真实文件/manifest衔接的skip分支。
  checkpoint字节仍由已有final-lock验证；本次并未执行真实最终模型汇总、锁定或开封。
- 文献原始元数据4篇已核验；已读Gauthier等(2021)NG-RC出版商HTML正文Introduction至Methods，未读补充材料。
  新RESEARCH72_METHOD_POSITIONING说明固定非线性特征+线性读出及leaky ESN不是本项目首创，
  本体信息调制记忆的有效性仍待同数据消融与完整闭环结果；状态有界不当echo-state收缩、无源或机器人安全证明。
  其余3篇仅核验元数据，不声称完成系统综述或忠实复现；一次429和首次303页面未冒充有效全文。
- 已核验共享归档主机arm1@192.168.31.70，本轮根
  /home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/related_work_review_v1/：
  5文件，tar SHA3c7b08994ab1e09d1daf0efed5f845843482a63d7f59ff0e98f9586fbfad961c，
  HTML SHAb03455ff17545082d796162b922d3741a79df55b438e6c62160c20d84fcc8231。
  初始4元数据归档related_work_metadata_archive_v1独立保留，tar SHA5ea2cfc9dd0888f0bb50e25c4b5e54ed645ac99fe359708b81fc5f0e063c7347。
- 18:36UTC初始开发100/264（33/33/32/2分布），仍4稳定物理队列；第三条件尚未齐备，不提前汇总其胜负。
  本机约10.6GiB可用；没有活跃subagent或新增仿真。teacher确认、RL与再采集仍等待前序，真正24条件封存。
  无新拟合、无预算修订02、无最终结论；下一轮学生拟合必须等真实数据与可用预算核定。

## 2026-10-03 — 最终矩阵/媒体入口、工程中断保留与第二条件完整结果

- 延续本轮实时核对main e4366a7a941da64b443db1278ce36af4eae72ebb与baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，AGENTS已重读。
  e436源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/e4366a7a941da64b443db1278ce36af4eae72ebb/核验3165文件，
  tar SHA068bec9321ced62a1b3fa8780a8e68d6bd18b1dbb535306d686ca257a1eddd88。
- 第二共同开发身份development_001全部33候选：ESN6回合3task/3strict，matchedRNN同3/3；ordinaryMLP1/1、
  ordinaryRNN1/0、matchedMLP0/0（分母均6），memoryless0/0（分母3）；总8task/7strict。
  分母都是真实已跑次数，不是未评估。含损失候选，不是最后模型的泛化成功率；增强baseline仍待执行。
- ESN303点版XY13.192mm、外穿透0.149mm，但直到53.44s才load_transfer、54.76s才release，任务仍失败；
  积分版XY7.520mm、外穿透0.187mm，54.24s才load_transfer，亦失败。原55s任务要求不修改。
  两者RMSE102.724/124.436mm；需要改善恢复推进而非单看末端XY。另seed301积分版柱子穿透0.687mm失败。
- 全33模型只读诊断主机arm1@192.168.31.70，本轮根
  /home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/public_contact_diagnostics_condition1_v1/，
  DIAGNOSTICS SHA5c90db239476de8dff03d8382f8af903f047d48afa0f0cb85e881ffac773cb26，
  source SHA9afb61d840dc0c93b32f93d0262c188a48d2178a7e94c4521e58b660fa04cc9a。零新物理回合或拟合，反事实查询不当训练标签。
- 新research72_comparison_report汇总全部锁定方法/seed/24计划身份，验证原始audit/独立复算/metrics/锁关联，
  未审计保持缺失及分母上下界；短回合单列、无接触NA、恢复右删失，严格成功为主、接触条件子集明确披露。
  输出Markdown与逐回合JSON和交叉bootstrap，不排序制造ESN第一；8项合成回归含证据链接入/篡改拒绝通过。
- 修复未来最终batch一队列报错会跳过全部peer独立审计的问题：先保存完整PLANNED，保留失败且继续审计已完成peer；
  audit_paper_phase新增显式allow-partial，审计完成不等于物理全完成。2项合成队列故障测试通过，无自动重试。
  当前运行runtime没有热改；最终入口预演只覆盖worker，完整多队列真实最终链路仍未执行。
- 新最终媒体入口避免沿用旧12小时硬编码截止；选择首个共同最终ID、全部锁定方法/seed，三机位25fps全程，
  失败不剔除、短回合不补帧、缺失不冒充0成功。选择回归通过；未制作或读取最终视频/条件。
- 已完成工程和第二条件诊断；运行仍为初始4队列；RL、确认teacher再采集等仍等待前序。
  真正最终24身份封存；最终矩阵/媒体及新结构训练均未完成，不宣称RAL可投稿或ESN领先。

## 2026-10-03 — 当前本体调制读出工程验证与最终入口预演登记

- 17:42UTC实时核对main65b3dd64868010d9579c565842abeb9a04ac9ca4、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两分支日志和AGENTS。
  65b源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/65b3dd64868010d9579c565842abeb9a04ac9ca4/核验3158文件；
  tar SHA f646a5b44ada140f03712fb0e7d0a74087df108d61cf09804065a9458d6a4bb3。
- 公开完整首条件诊断v3保留全部33模型。ESN积分303在41.72s的z请求+0.3368中，当前signed load项-0.4708，
  signed state项+1.4374，另有absolute state等抵消。是相关特征的代数分解，不是隔离因果结论或实际teacher执行标签。
  DIAGNOSTICS SHA66b833eb6d2ce68f35156ffe16c5fbf5d3926bd21087a24ad8752f64e8394d38；真实执行脚本SHA89c57a43ed28a29e8b6767b957c39fde49525946093c0621af88dd2d3949966e。
- 新可选固定交互特征r*tanh(G*c)，仍128储备池、相同本体输入，只训练线性读出；没有混合teacher。
  扩展特征后不是单独对r/c线性和，训练系数2884→3780，固定G另1536系数，不能称等参数/FLOP。
  给同特征MLP/RNN同一固定变换；未拟合任何新候选，原ESN48/seed cap仍用满，无修订02。
- 本地单线程3GiB，4随机系数组合NumPy/Torch最大差5.61e-15，真实loader导出精确；
  零状态零负载平衡、禁用字段隔离、固定G无梯度通过。旧102模型在已知train_000完整1375帧动作重放全部误差0。
  ENGINEERING_ONLY权重不列候选，不是物理结果。原运行runtime保持不变。
- 本轮共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  public_contact_diagnostics_v3/；context_readout_engineering_archive_v1/已核验14文件，
  tar SHA ff52bdeb2fecdafc2ebc9f3791f152b0b86491f7e60524b5c7d29f22e1926c82。
  PARITY SHAfa1bef3e4193bfc188b9307b138aee2391438762bd7ea47dc2a62aa69e674b3e，
  backward PROFILE SHA3b7d7c7491783de56853edf256e8da570bc7b343b504f3d45e9889d707b047fb。
- 最终入口预演服务已登记，等待followup完成后使用1受管理槽位重放已知train_000的原teacher。
  独立合成协议/锁/receipt不读写真正封存区或FINAL_UNSEAL_RECEIPT。spec SHA92dc8c61a5e41e63bf5a29b4ed5d154583322cd92b563263b9bd4fd47a37f712。
  相邻research72_20261003_1149_final_rehearsal_runtime_v1核验499文件，tar SHA1179c10aaf2631970fdf261ff9811df37a5096f4329c7dc4fc9e800f337ac8d2。
  最终batch拒绝预演活动时启动，曝光账本将预演单列；预演尚未物理执行，不能宣称最终链路全部验证。
- 17:46UTC初始开发60/264完成，4队列稳定；RL/teacher再采集/预演等待前序。真正最终24条件仍封存。
  已完成工程验证，尚未完成新结构学习、全部baseline适配或最终统计；不宣称ESN优化有效或论文可投稿。

## 2026-10-03 — 首开发条件完整对照与柱子失败动作诊断

- 继续核对main415501369e4b26ecdca60f65a9a6761115ffb6e8、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  4155源码已在server source/<完整SHA>/核验3157文件，tar SHA1efd2cb93ccd463121bf6811ba67a902330e6714b689ac52cc9196a450a22d5a。
- 首个公开development_000的33模型全部完成：14任务/10严格；ESN6回合4任务/3严格，
  matchedRNN6回合4/3、matchedMLP6回合2/2、memoryless3回合1/1、ordinaryMLP6回合1/1、ordinaryRNN6回合2/0。
  这些含两个损失版本，不是选定方法跨条件成功率；后续学习率/机制复核仍未运行，不以欠优化网络宣称ESN领先。
- 扩展现有teacher接触诊断工具，要求同一公开身份全部登记模型齐备且完成才诊断；拒绝封存角色，检查协议/公开身份hash。
  所有33回合一同分析，没有选掉失败；truth仅用于离线诊断，不进入actor/训练标签。
- seed303点/积分ESN最差穿透均为柱子-link7。点版首次接触41.4745s，最差41.8659s，延后0.3914s；
  积分版首次25.75275s，最差41.729s，延后15.97625s。不应一概归咎于首次碰撞太快或25Hz来不及反应。
- 在完整真实学生观测上重放原teacher内部状态作反事实查询：积分版41.72s学生z请求+0.3368，
  原teacher建议-0.2049；点版41.84s分别+0.1298/-0.0036。是同观测历史下动作偏差，不能证明换teacher就物理成功。
  请求、实际过滤动作和查询均分开保留，明确actual_execution=false、used_as_training_labels=false。
  未用这些开发历史重新拟合学生或扩充示范，现有ESN48候选cap未再扩展。
- 已核验共享产物主机arm1@192.168.31.70，本轮根public_contact_diagnostics_v1/和v2/：
  v2 DIAGNOSTICS SHA6dc2185a2ba9d2134f0fab897b2a76b62cba4936ccfe83e2a3020cbd6e9933a7，
  实际脚本副本SHA1fb72edb429a314ed8941b3b578b2e8caaa004bbde44609a49b0dc486926574f。
  两次均为单线程3GiB离线分析、0新物理回合，原v1保留；Git同步v2小证据。
- 17:08UTC开发37/264完成，实际均值343s/回合；912最终回合按4并发仅物理约21.72小时，还需预留审计/工程开销。
  不再盲目堆叠开发候选。优先完成当前整批与选定teacher真实再采集，之后若有新拟合须先登记共享数据/预算且保证最终时间。
  最终24条件仍封存，RL等待前序，没有提前结束持续任务或宣布论文完成。

## 2026-10-03 — 成对统计、短回合删失修正与实际推理成本

- 继续已核对的main9855fa8a78c9ea87bd3cf0a63f0fbd345483a296/baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  9855源码tar SHA ed40d4b2980729b8f4eef998e76fcced5636448cd5e401f9b4281902df733719已在server source/<完整SHA>/核验3151文件。
- 新成对统计模块按条件与训练seed交叉bootstrap，确定性经典对照不伪造3seed；缺失回合保留分母上下界，
  无接触/短回合/失败不进入“双方严格成功且接触”的条件子集；该子集不取代完整成功率。8项合成回归通过，
  包含首seed失败不能抹掉后续seed与确定性对照的有效配对。尚未处理最终24身份。
- 模型锁加入所有AMENDMENT文件内容与集合，7项保护回归通过。完整冻结前后预算修订必须一致，真实封存仍未打开。
- 修复paper_metrics早停回合恢复观察窗可能超过实际最后采样时间的问题；v3增加计划截止并保留右删失。
  3项完整提取器合成回归通过；一个真实55s ESN回合全部数值与v2精确相同，只增加计划截止及变更版本/源时间。
  原runtime和历史v2证据不覆盖；主机arm1@192.168.31.70，本轮根metrics_censor_regression_v1/full_esn_point.json
  SHA7aece33d1cc89609f3dac3a1571433901327eab5e80ae9e6608dc4d909194d65，Git含同一小证据。
- 按服务器PRIORS与controllers重新核对，纠正文档“全部参数RL5D”：导纳7参数、阻抗5、VMC7。
  阻抗公共残余动作虽记录为7D零，真实执行仍是其独立底层力矩律。实际训练代码一直使用各prior维度，未更改控制律。
- 本地1线程3GiB零仿真核验全部102已保存拟合，已知train_000完整1375帧动作重放误差全0；
  每模型3次序列推理、保留原始ns。ESN/memoryless2884可训练系数；ordinaryMLP5504、RNN21888；
  matchedMLP22852、RNN39236。各模型中位数再取族中位数：ESN32.15us、普通MLP7.98us、普通RNN10.00us。
  ESN系数少不意味着推理更快，固定特征有开销；actor-only耗时不当整个控制器实时保证。
- 服务器本轮根inference_profile_archive_v1/inference_profile_v1/完整6文件逐内容/大小/模式核验，
  tar SHA4f826b6a90e2ce22925b223d6b6ddbdb99693202c6f70c0842ef72ee64912eaa，PROFILE SHA91431277af003439608cb5677a53cdd1fd6328bfcc737272f02712d29f60ffa2。
  Git INFERENCE_PROFILE_RECEIPT.json含精确命令、成本、归档与局限；初次systemd缺工作目录退出2、脚本未打开，修正工作目录后完成，不是物理重试。
- 16:50UTC公开开发24/264完成。首条件ESN全部3seed×2损失已齐：3/6 strict；
  seed303点/积分外穿透0.551/0.476mm超过0.2mm，点版任务成功仍strict失败；积分版任务也失败。
  待完整开发审计，不从单条件选择模型或改gate。后续RL/teacher再采集等仍等待前序，未重复启动。

## 2026-10-03 — 控制器筛选完成、真实teacher再采集入口与首轮学习闭环

- 16:27UTC重新核对main 8bdade7fbd15f76f725c985514bde6e0c94a0253、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6并读取两分支日志/AGENTS；无远端新变更。
  main8bd源码在服务器source/<完整SHA>/核验3144文件，tar SHA ead3221294e2cfd2565679acaa8b71713381afd64a84217700f6a8fe0919b612。
- 参数筛选96/96完整55s并独立审计：增强teacher21task/13strict（24回合），导纳/阻抗/VMC各0/24。
  这只是12候选×2开发条件；按原规则各取2个继续8条件确认，尚未确定最终参数。
- 初始33模型×8开发条件正在实跑。第一个条件development_000/seed2026100301：
  ESN点版task/strict均通过，RMSE29.399mm、峰矩50.386Nm、峰速0.373926m/s、放置XY24.774mm，距离25mm门槛很近；
  ESN积分版XY26.381mm而失败。无记忆及初始matchedMLP均成功，RMSE37.050mm、XY20.283mm。不是最终盲测或跨条件结论。
- 首4回合离线接触诊断：ESN点版推杆P95力14.313N、力模积分43.724Ns、接触4.945s、保持期最大脱离仅0.0013s；
  无记忆分别25.297N、28.817Ns、2.666s、2.191s。低P95与低RMSE并未同时带来更快脱离和更低累计负载。
  ESN未触柱子，该项显示NA；无记忆有柱子接触。球接触峰力约5.9–6.8kN，属于刚性碰撞仿真瞬态，不能称人体安全力或25Hz策略反应。
  全部恢复诊断右删失，不能写成0秒恢复；完整队列独立审计仍待完成。
- 新增有限refined-teacher服务：等待8条件选择后，在原32train/8validation身份真实执行选中teacher；若配置相同则跳过。
  原48轨迹不覆盖，无开发历史作标签。只采集/审计/导出，不偷偷增加学生训练；任何新拟合须先登记预算。
  导出器默认路径原生回归仍得到相同24示范/33000帧和同一数据SHA b97acf4c61d9d3ba4d5fcb4817ac449b460e65a4821be632c5f61a5a1bba67c6。
- 新学习选择器只接受完整独立审计的三组开发结果，跨全部3seed/8条件统一选variant，失败族也保留；3项合成回归通过。
  54合格权重来自75实跑权重；未对尚未完成的真实数据执行选择。最终入口补充等待refined-teacher，成本账本纳入再采集。
  分析方案注明参数动作与公共7D接口不同；16:45核对原prior后更正为导纳7D/阻抗5D/VMC7D，阻抗另有底层力矩律；
  独立选出的ESN/memoryless不同loss/gate不冒充隔离记忆消融。
- 服务器根 arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  controller_screen_v1/SUMMARY.json、early_learning_metrics_v1/、teacher_export_regression_v1/、teacher_refinement_v1/SPECIFICATION.json。
  context21权重原生1375帧重放最大误差1.66e-14；CONTEXT_GATE_NATIVE_REPLAY.json与以上小证据已纳入Git。
  新采集实际源码相邻research72_20261003_1149_teacher_refinement_runtime_v1，tar SHA4bb4d0bbb27b4a95fa8406bd8b4ce6c0f8b7c75acb829a84a4e51a8e56fbfb51（8bd加本批修改）。
- 已完成：筛选/初步诊断/导出回归/选择器工程；运行：四学习仿真；等待：参数确认、RL适配、同机制/小LR评估、新teacher采集。
  24最终身份仍封存。未取得ESN最优或RAL投稿完成结论。

## 2026-10-03 — 记忆表达缺口诊断、预算修订01与同机制ESN/MLP/RNN

- 延续本轮核对main e32f02ddc16e1b65511b5a9f9cfbd316042b43ef、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  e32源码归档SHA8f007a3f8333ee5fff0da721b0a36f8456dac01d4d98093621fd440433e2edf0在服务器source/<该SHA>/全3133文件核验。
- 代码和零仿真输入干预发现：原ESN的context只乘当前load，直接context读出被约束为0；load归零后，
  相同历史无法区分后续卡住/前进/意图消失。3seed两loss的10秒合成探针状态仅保留约0.78%，
  卡住时teacher恢复记忆仍0.99976、z动作约0.37491；该人工输入序列不保证物理可实现，不当任务失败证据。
- 真实18训练＋6验证完整teacher动作复现最大误差1.11e-16；估计线性负载<0.5N且恢复记忆>0.5的片段
  分别3.24秒/16身份、1.08秒/6身份。<0.05N的验证片段为0；真实覆盖远少于人工10秒探针，不能过度解释机制。
- 15:23UTC在新拟合前将AMENDMENT_01_CONTEXT_MEMORY.json归档服务器，SHA5b6e9c22751b0045e7da980f24480338ab03164c6cd7fc29a05fbab68ac27a6a。
  各学习族每seed上限显式24→48；实际ESN48、memoryless24、普通+同特征MLP/RNN各14。72h/48h截止、数据、环境/gate/actor/执行器均不变。
- 使用既有固定随机本体context→leak调制（0.05..2），仍128固定储备池、受约束线性读出、无运行teacher；
  相同固定gate提供给重训memoryless及matchedMLP/RNN，后者沿之前3seed平均验证选定LR，各4000更新，全部原组保留。
  NumPy/Torch含gate及无gate最大差3.83e-15，零平衡/禁用字段隔离通过，gate不是可训练参数。
- 本地单CPU/3GiB完成21模型（另108ridge和48000梯度更新），完整动作导出回放与输入审计通过。
  gate打破合成输入不可区分性，但未获得teacher长时间保持；ESN点/积分验证误差普遍高于原版，未宣称机制或任务改进。
  全21模型登记同8开发身份168回合，四仿真既有筛选74/96正常；新有限服务等待原followup，之后每回合共享释放槽位。
- 服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `local_context_gate_archive_v1/`包SHA c206c4e98102bff46d0dc97a8915e5018ddfbb9369914f08ce5b2e5b1c0b2ea6，21模型元数据/权重/原拟合源全核验。
  `memory_mechanism_archive_v1/`原探针/一致性包SHA2bdd45803e510475fdc40221ca0a7c30c6c2cb3fe377e852390911e921ed96d8，两端及解包数组hash一致。
  `CONTEXT_GATE_DEVELOPMENT_SPECIFICATION.json` SHA19347931867d439ca2951a934c5b9bde636681fe785eed1c934db920993b6cbf。
  有限服务`sii-r72-context-gate-development-v1`已核验仅等待；相邻`research72_20261003_1149_context_runtime_v1/`源码tar
  SHA516ed7e308b8911c355b6397217db32d963d5de6306888fd2e083ae8d293d641，base e32＋本批修改，旧runtime不改。
- 完成：工程/机制/拟合/归档；运行：开发筛选；等待：全部学习闭环和RL。最终24身份仍封存，新的物理改进与投稿证据未完成。

## 2026-10-03 — 最终评估冻结保护与训练成本账本

- 15:00UTC实时核对远端main389e9e53bc016a03a250fe5f053a5a6513331023、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，
  两分支无新修改；读取AGENTS/同步skill。389源码包SHA77790e550cdfd516b2ef69701ae2a5339222bede0ea8addc28933ab164a33219
  已在`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/389e9e53bc016a03a250fe5f053a5a6513331023/`核验3126文件。
- 新增最终模型锁、独立最终worker和有限4槽队列。锁要求全部16类别、全部3seed与开发证据，
  不按strict资格删方法；checkpoint/RL嵌套文件、精确源码及资产集合核验。直接调用子队列也必须先有同锁/同输出开封收据。
  6项合成数据回归通过，含改权重、加源码、改资产、改收据/条件hash、缺收据拒绝；未读真实封存条件，未启动最终评估。
  真实端到端最终执行仍未验证。新增代码本批提交前仅本地，不热改已有稳定runtime。
- 新只读曝光账本分开统计teacher失败、ridge候选、神经梯度、开发仿真和RL累计新交互；恢复段不重复累加继承步数。
  15:08UTC快照teacher48完整44task/28strict；筛选56/96完成17task/11strict，其余仍在运行，非最终结果。
  初始33模型108ridge/96000梯度更新，复核48模型192000梯度更新；RL等待前序，当前新交互0。
- 本轮服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `EXPOSURE_SNAPSHOT_20261003_1520.json`（实际时间见created_utc）SHA579bf27e5ee931f9c00d036b59c35a911e8583e83072eb49d181f3d48e5cd369，
  已下载逐SHA核对并保留Git证据。实际脚本在服务器incoming/research72_exposure_ledger_20261003_1520.py，
  SHA2812aaf433ef13005e9f7f966781ea6f7c1f16418cde2036af6c721aa317c85e两端一致；后续已提交源码以source/<commit>为准。
- 新分析方案先登记成对条件/seed交叉bootstrap、接触覆盖与双方成功子集局限、恢复删失和成本披露；
  不把72回合视为72独立环境，不把无接触当柔顺零力，不以多指标事后加权制造赢家。环境/gate/actor/执行器均未改变。
  四仿真稳定运行；33+21学习模型闭环、RL适配、最终24条件及投稿证据仍未完成。

## 2026-10-03 — 加强神经baseline与累计动作偏差诊断

- 开工沿用已核验main d08dc8f23a0b5e9bbff2bed66e489620333d9052、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  d08完整Git归档SHA03945be24408f486f792d36d460a05f4de434c5ca69467906f41ded057f56cf2已传Spark，source/<SHA>/3117文件内容/大小/模式核验。
- 原同特征网络验证均选初始化，不能据此断言ESN结构优势。先登记再本地运行48个小学习率拟合（单CPU/3GiB）：
  matched取1e-6/1e-5，ordinary取1e-4/3e-4；每个4千更新，数据/宽度/损失和3seed不变。
  原始＋新增合计每普通/同特征子族每seed6候选，合并MLP/RNN仍仅12≤cap24；ESN候选预算未扩大。
- 按跨3seed平均整身份验证动作MSE择一个共同学习率，保留全部seed，不看闭环/最终条件。
  ordinary MLP点/积分误差下降23.91%/24.59%，ordinary RNN下降36.42%/27.41%；matched RNN下降1.62%/.94%。
  matched MLP积分组继续用原学习率；其余7组共21新模型登记8开发身份168回合，未把这些离线改进当任务成功。
- 新独立回放诊断完整重现教师动作filter和实际记录，覆盖33模型×6验证身份。ESN点/积分版本的
  残余速度差累积末值范数均值约98.0/87.8mm；是固定teacher观测下的开放回放代理，不是真实位置误差或物理结果。
  当前仍须等待闭环结果再确定下一步ESN机制，不把该代理当论文主结果。
- 新增零让位参考接口：相同规划/反馈WBC、7D零动作、同世界与gate；不是开环机械臂。已编译，尚待物理执行。
  `sii-r72-additional-development-v1`等待原统一开发/经典确认结束，然后8个名义参考＋168个神经复核回合。
  与3条RL训练共享4个flock槽位；评估每回合释放，允许ESN后续开发插入。原稳定四队列未修改或重启。
- 服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `local_neural_refinement_archive_v1/`含全部48拟合/源码及`replay_drift_v1`；包两端SHA
  97a39b953bfbe4b90f7aab28d82b4f98c14b4f8934c0827c5d3846d2f84c04fa，逐权重/训练记录/实际源码/数据hash核验。
  选择文件`NEURAL_LR_SELECTION.json` SHA dc5af909d1918f41a9b60e98dd39d0f3c0a26ac30cbd3ec9d9e46827359bcd34。
  后续源码相邻`research72_20261003_1149_development_runtime_v4/`，RLruntime_v3加新overlay
  1399f47d891ef90b2d6e777e4119fe8c0a5fc9319b8106a2c014a296c18d7b5d两端一致；base d08dc8f＋本批改动。
- 新增初始SOURCE标签澄清：teacher队列ENV继承了旧282433d标签，与协议base33f4380不同；
  实际源以已核验runtime tar及每回合source hashes为准，四独立审计已通过。澄清同时存Git和本轮根，未篡改原日志。
- 全部新脚本编译/diff检查通过；本轮拟合和离线诊断完成，闭环队列运行/等待中。24最终条件仍封存，未获得新最终优越性结论。

## 2026-10-03 — RL嵌套checkpoint修复、边界续跑与有限训练登记

- main45662c03ca40269f08e183fa6e814a900f026aca已推送核对，baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  已提交源码在`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/45662c03ca40269f08e183fa6e814a900f026aca/`，
  Git归档SHA b8eed5e8612ddfdf1e0569c9b71080d929aff11e6d724a6c6918276b33ef44d2，3111文件内容/大小/模式核验通过。
- 新RL适配开训前发现hash清单遗漏嵌套模型/优化器文件；修为递归完整清单，拒绝缺组件和symlink，评估要求精确文件集合。
  原生Spark无物理回归通过：5D与7D分别比较112个状态数组，保存/恢复后三次动作及优化更新逐值一致，
  replay内容/采样RNG一致。每模型71个原agent文件均覆盖；不将该工程权重当训练baseline，0新增物理步。
- 新增显式完整回合边界续跑，恢复优化器/归一化/actor RNG、replay/RNG、探索RNG、条件顺序与累计计数。
  只恢复已完整结束的段到新目录，不自动覆盖或重试中断回合。实际物理分段端到端验证尚待首个训练段。
- 登记15模型（RL导纳/阻抗/VMC、direct metric/office_task，各3seed），各最多80000累计步。
  初始5500步段不改变总学习率计划；续跑不清回放、不重复计曝光。参数中心沿事先规则从经典开发确认中选择，方程/范围不变。
  `sii-r72-rl-office-adaptation-v1`正在等待统一开发与经典确认，未开始RL物理训练，不创建定时任务。
- 新共享4槽位flock，6个竞争进程工程验证峰值4且全部释放；新RL限3队列、每队列3GiB/CPUQuota100%，
  为ESN后续开发留容量。检测到未使用锁的旧仿真时等待，不终止或热改稳定作业。现有筛选20/96完成（非最终统计）。
- 本轮根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `rl_checkpoint_probe_v2/`、`rl_office_adaptation_v1/SPECIFICATION.json`及对应Git小证据可核验。
  源在相邻`research72_20261003_1149_rl_runtime_v3/`，由已归档development_v3加三层overlay组成，
  SHA依次a7b674ba3e640aa512e59bb618efcb02ceb79204bc96559c7d18981c460b753b、
  c5b697572199b6895a80e07b5c3422ebcdcafbed8d3706776d50250824a70f42、
  685ad0d2bae2f002f56646ef013b2d36a0104c5ec27088107107e421e60ae0a1，两端均核验；base45662c0＋未提交改动，非干净commit运行。
- 编译/diff检查通过。24最终条件仍封存；RL学习效果、全部模型闭环对比、最终审计和投稿结果仍未完成。

## 2026-10-03 — 真实数据与33模型拟合完成，启动统一开发比较

- 本轮开工实时核对main fb484272f42e2e89fc54bfbec839f9d1b7d50900、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  短暂GitHub延迟后再次fetch/ls-remote成功，无新分支更新。原72小时协议和最终封存不变。
- 48个teacher全部完成并独立审计，44 task/28 strict；训练32为29/18，离线验证8为7/6，开发8为8/4。
  导出18训练＋6验证实际示范、33000帧，记录请求/过滤/执行量及原始source/seed/hash。全部失败在账本中。
- 训练身份诊断发现18个strict示范仅2个柱接触；12个穿透失败的最差对是pillar/link7。
  这是数据覆盖和接触速度关联，未证明失败不可避免；不将接触真值送actor或伪造示范。
- 本地1线程/3GiB完成33模型：3seed，128宽度纯ESN点/积分读出、重训无记忆、普通/同特征MLP/RNN两损失。
  同特征网络均选择初始权重，验证未获梯度收益；保留此结果继续诊断。离线误差不当闭环成功。
  全部模型登记8开发条件264回合，不按拟合优劣筛掉方法；按跨seed汇总选择损失，禁止择幸运seed。
- RL在线接口已知train_000完整1375步/55秒重放：观测/状态/动作/全部物理子步数组和task/strict/三指标精确相同。
  这是接口工程核验，未开始新RL训练。新增RL prior文件与训练配置hash核对，调参控制律不改；新增先验路径尚待训练验证。
- 增强teacher、导纳、阻抗、VMC各12候选于13:44UTC启动96回合筛选；采样与排序事先登记。
  有限串行服务等待此批完成，依次执行264学习回合及8候选×8条件确认；最多4仿真，各1线程3GiB。
  未创建定时任务；不重启稳定作业，不改环境/gate/执行器/actor契约，最终24条件未读取。
- 服务器根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
  模型归档 `local_learning_archive_v1/learning_v1/`：tar两端SHA 197bc0a5f7c363832a78ddb93dbd73cad7ff793c625eb2e6e19054795360f95d，
  全33权重/训练记录/实际source/数据谱系核验。保留真实本地计算路径，不冒充服务器训练。
  运行源在相邻`research72_20261003_1149_development_runtime_v2/`及`..._v3/`，base fb48427＋本批overlay；
  v2包SHA 850606455d85b9265c518f9408d88d3b02ce8764435410f0d56691f4798a4752，v3新增脚本包SHA
  7cbaaf0da92f23180e8e2e9de5be094c55ceb2e5ef83083a978eeaf5e6254f75，两端一致；不是干净commit执行。
- 新增登记/选择/训练接触诊断/有限后续脚本；编译、diff检查和实际登记核验通过。小证据在
  `code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/`。已完成数据/拟合/接口；运行中开发；未完成新RL、留出、最终论文比较。

## 2026-10-03 — 同真实数据学习机制与办公RL适配接口准备

- 72小时窗口继续，最近已核验teacher28/48完整，25 task、15 strict。四稳定队列保持运行，
  不按中间结果重采样；最终封存24条件未读取。main已发布659672d，baseline仍ebb0e1e，未合并分支。
- 新增真实示范导出器：逐身份原task/strict/55s资格、完整失败账本、训练/离线验证分割，
  逐项核验请求/过滤/执行action链及source/trace。开发与最终历史不能进入训练数据。
  修正旧训练脚本把episode<48一律叫合成轨迹的统计假设，新增显式physical_execution掩码，旧默认兼容。
- 纯ESN新增受约束线性读出的误差差分/16步积分目标，保持固定储备池、零负载平衡和相同本体字段。
  MLP/RNN同时获得积分损失选择；新增覆盖3seed、合计33模型的顺序训练计划（含记忆清空重新训练、普通与同特征网络），
  宽度128但实际参数/成本不同明确披露。尚未在新数据开训，不把离线fit当任务成功。
- 本地单线程3GiB旧训练数据工程回归完成，12个新读出候选/导出回放/输入隔离/零平衡通过；
  该回归只验证实现，非新闭环实验或新盲测。checkpoint SHA dd040d112eb1b53663546aa0bca602264ef54a64710ae5640118d627d8f01936。
  原生执行本机airpig，归档到本轮服务器根`engineering_local_v1/outputs/research72_engineering_20261003/temporal_readout/`；
  tar两端SHA 1c68737d7eb98afdd4b231cc17e8f0c8eb03b0343f231ceeaaf95694bce3df77，解包checkpoint hash一致。
- 已实现同v6原生RL IPC、原官方SimbaV2办公从零训练、冻结归一化评估、有限开发队列和依赖准备服务。
  baseline奖励原公式沿用，平滑项显式改用共同filter之后action；训练专用potential不进入actor。
  这些新增物理接口尚待实际完全重放验证；不宣称RL已开训或通过。
- 新准备源在 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149_learning_runtime_v2/`，
  base659672d＋本轮overlay；tar两端SHA deb7e5c546cab79d0776d1102e9205d1ff2f2c39b4df6889c9e6d881dca5e7d3。
  `sii-r72-prepare-learning-20261003-v2`等待collector完成后导出数据和单回合RL重放，不提前增加仿真并发。
  v1仅空闲等待器因原生环境无torch而替换；不安装额外框架、不动稳定物理作业，保留版本与替换记录。
- 上次已提交完整源码source/659672d9b463b98b3290d461f7bfe6b8901ea572逐文件核验3085项通过。
  本批编译/diff检查、33任务依赖顺序检查通过；最终学习/公平比较/新留出/论文证据仍未完成。

## 2026-10-03 — 新72小时研究登记与真实teacher采集启动

- 用户授权假期3–4天持续自主研究，保守窗口10-03 11:30至10-06 11:30UTC，含准备时间；
  不沿用旧截止、不建定时任务。新增固定GitHub入口 `RESEARCH_STATUS.md`，root README链接。
  开工实时核对main `33f438075649508ceb8f84479880d5d622f4eb4f`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`；工作树干净、无活动仿真，历史停止作业未动。
- 新协议先登记32训练/8离线验证/8开发身份，同原扰动范围、同v6几何与gate、正式dt5e-5；
  另生成24最终身份并封存，仅记录hash。旧最终条件不作为新盲测或训练轨迹。
  新增3脚本：protocol/role-aware worker/可恢复teacher队列，源码编译与diff检查通过。
- 11:49UTC实际启动48回合增强35mm VMC采集：4顺序队列、各1线程/MemoryMax3GiB/Swap0。
  原worker执行和审计不改；保存角色、协议hash、action全链、原始物理与失败。
  所有完整task/strict合格历史供ESN/MLP/RNN共享；失败留在采集账本，不冒充示范。
- 服务器原生共享根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`；
  实际源在相邻`research72_20261003_1149_runtime/`，base33f4380＋3新脚本，运行时各queue另存hash清单。
  初始源tar两端SHA一致 `0c43441298a6a68dac2d25f1578d3ee87ebd49c2c88cd0282a033e78aea4353d`；
  协议SHA `5457d85726e2a88067e153464b7e50dbc9fcd173b89a9fc5da2da096c0891732`，公开副本在
  `code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/`，未下载封存条件。
- 已完成协议/启动核验；运行中真实teacher；未完成新学习、经典/RL适配、新留出与论文证据。
  预算上限和逐阶段登记不等于已执行或各方法成本相同；不预设ESN获胜，不承诺真机/录用。

## 2026-10-03 — 26模型同一正式测试场景全部实际重跑完成

- 用户质疑0/0与是否统一测试后，新授权有限26模型×1固定v6锚点、正式dt5e-5实际重跑；
  旧0/0仅为两个成功计数（各分母4），不是未测试。原12小时预算/结果不改，新协议于10:48:23UTC登记。
  开工核对main c2bbc79de083564b6107fbe200ab2ecf10bb3207、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
- 26/26完整55秒，无重训、无换权重、无环境/gate更改、无开发资格筛选、无自动重试。
  5模型task/strict均通过：增强VMC teacher、普通RNN两seed、同特征RNN seed1、无记忆重训。
  两ESN均失败：seed1掉块；seed2最终XY28.19mm超原25mm。三RL调参停carry、四RL action停approach。
  21失败末态13 carry/4 approach/4 retreat；不能把阶段名当放置成功。明确任务/严格两列是/否。
- 各queue独立子步三指标、执行器、action/filter、源/权重审计及共同世界/初态核验通过；
  26条最终放置独立重建、全任务接触覆盖和失败征象汇总完成。7条旧formal重测的轨迹hash与三指标完全相同。
  每模型1条已知锚点，不是成功率/泛化估计；RL训练曝光不同，失败不推广为RL算法族不适用。
- 新增有限执行/报告脚本 `tools/run_all_methods_formal_20261003.py`、`tools/report_all_methods_formal_20261003.py`；
  归档校验工具允许显式指定研究目录名，默认原研究不变。源码编译、diff检查和实际全量执行审计通过。
  入口 `code/mujoco_6d_vmc_benchmark/docs/evidence/all_methods_formal_20261003/report/MATRIX.md`，
  同目录JSON含全26回合；上级有协议、共同配置、4批审计、放置审计与双遍核验收据。
- 服务器原生执行/共享根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/all_methods_formal_20261003_104728/`。
  基础源码c2bbc79＋两个新脚本快照在相邻`all_methods_formal_20261003_104728_runtime/`及各queue/source。
  最多4并发、1线程、各3GiB/Swap0。11:28:35UTC双遍核验2787文件/3826668265字节；
  清单在相邻`all_methods_formal_20261003_104728_integrity/NATIVE_INTEGRITY.json`，SHA
  `e0869790eb167394cb88a7ba5bc2953d5c830a6fe012141e3b37ef1ae8adaa7f`；174下载证据逐项hash一致。
  本轮无运行中仿真；不修改旧数据，不把新增结果混入原四条件或随机组。
- 用户随后授权约3–4天自主持续研究、定期GitHub更新，目标公平RAL级证据；按72小时新窗口规划，
  先解决ESN放置稳定性并补强同训练条件baseline，另设新模型冻结和留出验证，不预设ESN必胜。

## 2026-10-03 — 全部26方法统一柔顺性矩阵（含RL调参与RL action）

- 应用户要求，对既有冻结v6四条件104个完整55秒回合统一制表；未重训、重跑、改环境或gate。
  开工实时核对main `965be4b04f157eeece21f182ce2fab62fe0ef128`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`及双方日志/AGENTS；三个原研究协调服务inactive。
- 26行包括2纯ESN、teacher、全部MLP/RNN/无记忆、3个RL调参、4个RL action、7经典及zero。
  全回合（包括失败）中位数统一列RMSE/峰矩/峰速、球峰力、人手/杆/桌角P95力；补充积分、时长、
  恢复观察/删失、全任务再接触。显式接触分母，无接触NA；JSON保存范围和全部104条来源/失败记录。
- ESN主组task为1/4、3/4，strict1/4、2/4；七RL均task0/4。ESN并非各项力最低：RL调导纳
  人手/杆P95为14.5/7.2N，ESN为22.1/19.2及18.7/22.4N。RL与ESN无共同strict回合，
  不能将全回合描述性差异解释成同等完成任务时的柔顺优势；历史训练曝光不等。正式步长ESN失败仍保留。
- 新增标准库复算脚本 `code/mujoco_6d_vmc_benchmark/tools/build_unified_compliance_matrix_20261003.py`；
  入口 `code/mujoco_6d_vmc_benchmark/docs/evidence/unified_compliance_20261003/MATRIX.md`，
  同目录MATRIX.json与服务器核验收据。核对原报告/锁/窗口hash、26方法×4条件全覆盖、trace/接触字段，
  独立检查中位数与成功计数；编译/diff检查通过。本轮只做本地后处理，无运行中实验或新增训练。
- 已核验服务器共享根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unified_compliance_20261003_1034/`，
  内含tools脚本及docs/evidence同路径矩阵；3文件内容/大小/权限核验通过，归档SHA256
  `2eda7f13b25e409eae53900c353fea1e65abb6aedc36cb357831a91b4e397a09`。
  MATRIX.json SHA `de918f795f65f9d06a254fb00303faa948186f78c92534e47792a5480f8251f0`。
  原物理归档不变；已提交源码按最终commit另存服务器source/<commit>，不覆盖运行快照。

## 2026-10-03 — 十二小时预算内同场景研究收尾：局部ESN优势，未证明全面最好

- 授权窗口2026-10-02 14:11:36至次日02:11:36UTC，连续任务，无定时任务。22:24UTC前实验、
  独立审计、媒体及服务器整体核验已完成；不为空耗剩余预算重新训练。采用baseline事前发布的
  office-validation-v6与其原生Spark运行库；几何/目标/gate/本体输入/执行器不变，未将旧v5混排。
- 26锁定模型×4条件104回合、7合格模型×8随机条件56回合、7 formal dt5e-5均完整55秒。
  主比较ESN两seed task/strict为1/1和3/2（分母4）；同特征RNN3/2、4/2，普通RNN4/2、2/1，
  同特征MLP2/2、无记忆3/2、增强teacher3/2。七经典及七冻结RL各task0/4，但历史训练曝光不等。
- 随机补充ESN6/4、5/4（分母8），同特征RNN6/1、3/2；teacher7/5、无记忆5/5、调参原VMC0/0。
  非合格方法未测，不能计失败。formal两个ESN均放置失败，teacher/无记忆/RNN seed1通过。
  同seed共同strict仅三个条件：ESN较快完成，但杆p95力均更高；不能换权重宣称柔顺全面最好。
- 全部193选定记录（包含26开发）独立复算接触覆盖；192完整回合末态重建通过，1条开发abort
  保留16.36秒。10学习模型53500输入精确回放、1375帧输入边界干预差0；全子步/动作/filter/
  幅值与变化率/source/config/checkpoint检查通过。新增七对步长分叉、失败征象及20ms完成时间
  插值勘误审计，不改变物理/门槛/成功标签。47完整三机位MP4/GIF＋2上下对比视频解码/hash通过。
- 开发本机82＋原生112回合，另7跨库兼容诊断，新增最终167回合；全部原始失败保留。
  主35mm数据只有2实际teacher历史、2反事实学生历史和48合成负载序列，不宣称3000成功场景。
  128宽度不等于相同容量/训练预算；无记忆成功不支持记忆必要性。持续杆推主动滑脱仍未证明。
- 新增纯固定储备池/受约束读出训练、同特征MLP/RNN控制、固定模型/候选队列、统一物理接触指标、
  原生复现、配置/动作/状态/末态审计、完整媒体和归档工具；保留默认旧契约行为。
  编译、diff检查与实际全量审计通过。结果/方法/协议、联合进度、周报、两处README和小型证据已更新。
- 开工及22:29UTC收尾核对远端main `282433d339feef66b0334f223f82a6eea96b040b`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`，均未前进；按sii-research-sync/AGENTS执行，
  未合并baseline分支，未动历史暂停进程。本任务无运行中训练/仿真/后处理；未实现稳定泛化/正式步长ESN。
- 已核验服务器主根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`。
  双遍hash **40094项/32802129515字节**，清单位于同父目录
  `paper_esn_12h_native_integrity_20261003_final/NATIVE_INTEGRITY.json`，SHA256
  `f2bd06e2a7a1b4e26c85eaaa0a6e96061da88b729232c8775a2a58317579b3e8`。本机606份下载/报告/视频
  对该清单复核，24份独立审计报告hash与终版汇总一致；大文件不提交Git。
  实际物理源在各批次source及overlay，后处理在`final_delivery_runtime/`；已提交整理源码
  另按完整提交SHA归档服务器`/home/arm1/sii_shared/SII_compliance/source/`，不覆盖历史run。
- 验收入口：`code/mujoco_6d_vmc_benchmark/docs/PAPER_ESN_12H_RESULTS_20261003.md`；
  小型完整结果、图表、视频索引、核验收据在相邻`docs/evidence/paper_esn_12h_20261003/`。

## 2026-10-03 — 十二小时同场景研究过程记录（最终状态以上节为准）

- 21:41UTC：104四设计条件和7 formal已全部完成、独立审计及同配置核验通过。ESN两seed
  主比较strict1/4、2/4，RNN/MLP/无记忆也有2/4，不支持ESN全面最好。formal两个ESN任务失败，
  teacher/无记忆/同特征RNN seed1通过；不改变门槛、模型或既定随机资格。56随机回合已开始。
  新结果报告记录真实释放/掉落失败与数值敏感性；其余设计条件14条完整三机位视频和一个短abort视频已核验。

- 21:09UTC：主验证81/104条已完成，稳定队列不重启。新增整批最终放置重建、接触覆盖审计与
  完整三机位交付流水线，等待已启动验证结束，不派发新训练/仿真。固定展示h1全部26模型与formal全部7模型，
  abort保持真实时长。开发图发现指令窗口后的人体系再接触，补充全任务/窗口外统计，原指标与gate不改。
  准确注明放置13个25Hz有效样本计.52s、时间戳跨度.48s，不冒称连续子步稳定证明。
  10模型各1375帧输入边界干预的动作/隐藏状态最大差0；原生112条开发全量目录已完成（另列本机82条及7条库兼容诊断）。
  源快照final_delivery_source_20261003_0505.tar.gz SHA 2d7ecfc244d0449722a1ba928900492d7487f7eca326580956ce22ba93738c21；
  已核验于主执行根。一次未完成源码传输的失败解包被单独保留，未用于运行；替代小型源码包先完成传输/hash核验再解包。
  20:29UTC复查远端main 282433d339feef66b0334f223f82a6eea96b040b、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6未变。

- 20:09UTC：38原生经典候选与独立审计完成，26最终模型正式锁定，lock SHA
  755974da1d4d5a3fb1aa24aa779cf91ede2e83768de2b9dd21089de863166701；四条件104回合开始。
  7个开发strict合格模型另做formal；在最终回合前登记8随机条件补充验证，不重训，不按最终结果改资格。
  10模型学习回放各53500输入精确一致；本机82回合审计索引、6完整开发视频和537项baseline依赖已核验共享。
  仍运行中，最终结果未定；服务器详细路径、manifest与源hash见联合进度20:09记录。

- 19:27UTC：同特征RNN两seed独立审计后均开发strict成功，原VMC04亦strict成功，不能宣称ESN独占。
  新训练已结束，新增最终选型规格/冻结工具及一次性连续验证协调器；先完成38条经典候选审计，
  再锁26模型×4共同条件，开发strict合格者另做正式步长。未根据测试结果调参，尚未启动最终条件。
  新增完整表格/锁定配置复核/成功矩阵报告工具及三机位全程媒体队列。学习证据69组/3710文件
  已共享核验至服务器runs/main/paper_esn_12h_learning_complete_20261002_141136/evidence，manifest
  f0229abc25df6042a339035671f6a65cf5e069974ba88b432a028b0e72645e90；经典本机剩余29条亦已归档。
  19:08UTC远端main/baseline SHA与开工相同，无合并baseline代码或改环境。

- 18:45UTC：35mm teacher组两个固定ESN seed均在原生v6锚点task/strict通过；普通MLP/RNN各0/2，
  无记忆重新训练亦成功，不能声称记忆必要。新增共享DAgger、长反传RNN、同特征MLP/RNN机制对照；
  DAgger ESN与长RNN的放置/穿透失败均保留。已完成成功回合真实松爪/桌面支撑重建与两段55秒
  三机位媒体核验。经典38候选全量原生复评中；最后四条件未解封，终版/正式步长与最终结论未完成。
  新增显式argv冻结离线队列，修正数据追加的context契约继承和视频场景标签，训练支持float64及
  可登记长反传，旧默认行为不变。完整学习证据服务器paper_esn_12h_learning_evidence_1815_20261002_141136/evidence
  已核验639文件/100781194字节，manifest f6a56266094c5fb7c89ff6adec32b10bad100ff82ef087ea1cd77a078f799b48。

- 17:56UTC进展：原baseline统一环境首条纯128固定储备池/线性读出ESN task/strict成功，
  41.476mm/50.136Nm/.357187m/s、外穿透.125753mm、终点XY7.929mm；目前只属开发单回合。
  同组条件漏率失败、可训练漏率放置成功但穿透超限，均保留。14历史方法逐数组精确复现与15条
  共同运行环境核验通过；恢复VMC六条中三条成功。新35mm数据组/同宽MLP/RNN继续。
  成功run在服务器paper_esn_12h_rl_20261002_141136/recovery05_learned_native/recovery05_esn_fixed；
  末态/完整接触审计、终版锁定及四条件仍未完成，不能宣称ESN最优。17:50UTC复核两远端SHA未变。

- 开工实时核对main282433d339feef66b0334f223f82a6eea96b040b、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  按sii-research-sync读取两分支日志/AGENTS。授权2026-10-02 14:11:36至次日02:11:36UTC，无定时任务。
- 锁定baseline既有office-validation-v6，原始VMC本机单条task/strict成功；128单元纯ESN积分训练版
  末帧放置到XY12.557mm，但保持仅.04s不足.5s，仍失败。新增统一接触/恢复/动作与原生子步审计，
  不改场景/gate/actor输入/执行器，不挑失败，不预设ESN最好。MLP/RNN同数据学习对照和经典固定预算继续。
- 纠正RL运行解释器：原GPU环境七条复跑与历史结果一致；先前不同JAX环境七条另存兼容性诊断。
  所有原生RL均失败；非RL锚点正在同解释器核验。首次新源码缺少outputs锁目录的预启动失败保留，
  只补运行目录后恢复，批处理代码增加目录创建。源码快照独立保存，无热改稳定作业。
- 已核验新增经典九条782文件/973560594字节：
  arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_classical_slice1_20261002_141136/evidence/，
  manifest SHA b04f3ec8db8e16e470a98e540c4d77d87c1ec1e7176f7326d943393613577d66。
  先前initial/phase2/paired_learned亦已归档；最新学习产物仍有仅本地待同步部分。
- 进行中：teacher恢复/平滑、学生读出学习、原环境统一锚点。未完成：最终模型锁定、正式步长、四条件
  配对泛化、最终媒体与完整共享审计。详细协议/状态见benchmark docs/PAPER_ESN_12H_PROTOCOL_20261002.md
  和ESN_VMC_JOINT_PROGRESS_20260927.md；收尾再更新最终结论并提交推送main。

## 2026-10-02 — 固定teacher数据下纯MLP/可训练RNN替换ESN

- 按用户新授权，完成两套既有teacher数据×MLP/Elman RNN×两个seed，共8模型、8条55秒开发
  回合；全部task/strict失败，未修改tool-contact-v5环境、b092662a模型、规划/WBC/gate/执行器。
  本轮是独立8模型协议，不延长已结束四小时预算，无定时任务。
- 原VMC组MLP/RNN两seed平均RMSE39.060/29.307mm、峰矩38.470/38.933Nm、峰速.404145/.386349m/s，
  均卡carry；原VMC MLP seed2外穿透.205319mm超限。恢复41组未显示稳定优势：RNN seed1最终
  XY101.545mm，seed2全程approach，较低RMSE/峰矩不能当作进步；MLP seed2最终XY59.899mm仍未放置。
- 新增office_mlp_rnn_20261002 actor、训练/固定8回合runner/独立模型审计；loader添加契约、
  evaluator仅允许RNN类型。128隐藏宽度、2400更新、同data/seed/序列曝光，RNN学习循环矩阵。
  四对RNN离线拟合更好但闭环均失败；参数量不相等，旧ESN另有128非线性读出，不声称结构优势。
- 8条550000子步指标、动作/filter、4条RNN状态、8份独立接触sidecar、执行器幅值/4ms变化率及
  source/data/config/checkpoint/trace hash审计通过；4组训练曝光完全一致。导出Torch/NumPy最大差≤3.76e-7。
  原始teacher失败标签/trace hash复核；两条55秒/1375帧/25fps三机位视频完整解码并目视检查。
- 初次资产路径缺失在物理启动前失败，记录保留、原MLP checkpoint核验复用，没有重训或丢弃回合。
  报告工具增加显式物理batch选择，避免把归档预启动协调记录当待完成物理回合；初次诊断仍保留。
  编译与diff检查通过。专题报告/协议、联合进度、周报、两处README和小型审计收据同步。
- 按sii-research-sync开工核对main `14820fac7141fa8779aa56b5ae0ba595ee2ee0a5`、baseline
  `133a0b4306f70dd703629bf1227961899d6abcfd`；收工main未前进，baseline更新至
  `d00b995711c68a2e42a2ffd4ec2813758849aff3`，历史ESN/RL对照更新已读，未合并分支或干预独立作业。
- 已核验680项、747,693,072字节证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/mlp_rnn_replacement_20261002_131535/evidence/`。
  manifest SHA256 `8a5209a9432138459175202d7a6452125bfc1c1bd7082aca0943256e5743931d`。
  运行源码在该根目录`evaluations/source/`、后处理源码`postprocess_source/`；本轮Git源码另外
  按完整发布commit SHA归档服务器`/home/arm1/sii_shared/SII_compliance/source/`。
  小型证据入口`code/mujoco_6d_vmc_benchmark/docs/evidence/mlp_rnn_replacement_20261002/`。
- 完整结果和视频索引：`code/mujoco_6d_vmc_benchmark/docs/MLP_RNN_REPLACEMENT_REPORT_20261002.md`。
  已完成本轮比较/审计/共享，无运行中实验；未完成成功teacher、放置/strict、formal步长与跨条件泛化。

## 2026-10-02 — 四小时固定环境teacher/纯ESN联合优化及完整失败审计

- 授权09:01:55–13:01:55UTC，连续前台任务，无定时任务。预登记48条teacher/名义候选、
  24条纯ESN回合均完成55秒，task/strict均0；额度用完后收尾，不为耗满时间空转。
  环境tool-contact-v5、MJB b092662a、规划/WBC/gate/公共输入与执行器限制均未改。
- 优化teacher弹簧/读出、负载耦合与相对参考恢复记忆；纯ESN增加多时间尺度、负载×运动/
  误差派生输入、context调制leak、失败学生历史反事实重标注及积分动作损失。
  仍无新成功teacher数据。原VMC蒸馏ESN30.058mm/39.210Nm/.370185m/s、穿透.111707mm，
  但卡carry；推进最远学生integral41为76.718mm/38.129Nm/.398990m/s、XY76.918mm，仍失败。
- teacher47最终XY49.157mm，但没有接触未知凸边，后段卡柱子，推杆连续受力8.8172秒，
  不能把更近的终点当作滑脱成功。DAgger漂移损失配对RMSE153.759→125.970mm、峰矩/峰速
  略升且均失败；零初态平衡不足以保证已有历史卸载，离线干预与物理清空记忆结果分别保存。
- 13个有效学习模型及1个拒绝部署的旧标签模型、8组读出和最后3条gain/记忆干预全部保留。
  本模型128储备池另加128非线性读出；没有MLP新实验，不声称严格参数/FLOP匹配或ESN优势。
  全72条三指标、动作/状态、公共filter、幅值/4ms指令变化率及源/配置/hash审计通过；
  33条独立接触sidecar复算一致，6条穿透超限保留，5组配对数据/seed/预算一致性核验通过。
- 新工具包括冻结批次runner、teacher worker、学习/物理/配对/记忆/视频审计和归档发布；
  teacher与学生checkpoint重放验证、编译与diff检查通过。三机位编码固定单线程，
  两条完整55秒1375帧MP4/GIF已生成并验证，视频明确标为失败。
- 按sii-research-sync开工读取main `7cd5f4b7ac0a3056df76ac62bc690ded0724b104`及baseline
  `e564e09a691293802ec76c237d717b202d592e85`；收工main未前进，baseline更新至
  `a788be958486b5b24bc546737d44f690763521ba`并已读日志。未改baseline作业/分支或独立FLASK环境。
- 已核验5050项、5,951,412,066字节原始数据及运行源码：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_esn_four_hour_20261002_090155/evidence/`。
  manifest SHA256 `20731dc23f9924cf2247a2c7d62db12a7f75602ddae8d8e7ae3a059f5f6de98f`。
  代码在其中各批次`source/`及逐回合/训练overlay，例如`final_intent/source/`与
  `esn_dagger_pair/source/`；base commit不冒充干净源码。本次发布源码另按完整commit SHA
  归档同一服务器`/home/arm1/sii_shared/SII_compliance/source/`，不覆盖旧运行。
- 完整结果/限制/媒体入口：`code/mujoco_6d_vmc_benchmark/docs/VMC_ESN_FOUR_HOUR_REPORT_20261002.md`；
  原预登记协议、联合进度、周报、两处README及小型归档收据已同步。
  已完成本轮预算内实验和审计共享，无运行中任务；未完成稳定放置/strict、成功teacher数据、
  formal dt=5e-5及跨条件泛化。

## 2026-10-02 — 当前环境及三机位完整交接，补充跨机器复跑入口

- 用户认可当前交互展示，要求先同步供其他agent接续；本轮未启动仿真/训练，未改变环境、
  机位、gate或权重。按sii-research-sync开工及收工核对远端main
  `03809257e72b612bdc760ada3113e8ddba32c098`、baseline
  `e564e09a691293802ec76c237d717b202d592e85`，未改baseline分支/独立作业。
- 新增`code/mujoco_6d_vmc_benchmark/docs/OFFICE_TOOL_CONTACT_HANDOFF_20261002.md`，
  固定office-tool-contact-v5的坐标/尺寸/时序、公共规划/成功定义/本体输入限制、三机位
  lookat/距离/方位/俯角、25fps原速完整视频和慢放区别、重渲染/复跑命令、共享资产与hash。
  README、接触修正报告、联合进度和周报均加入入口。
- `run_tool_contact_20261002.py`新增`--reference-dir`，可直接使用共享完整回合中的
  summary/checkpoint/TRAINING_COMPLETE；验证完整时长和权重hash，拒绝短探针参考。
  无仿真验证：共享参考与原p010权重及所有非覆盖参数一致，短球对照被拒绝。
- 已核验原物理源码：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/03809257e72b612bdc760ada3113e8ddba32c098/`。
  已核验原证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/`，
  manifest SHA256 `936b6af1988b65bfce16dcf6c4fa44b2b1bf8460913b59aff2accb6496c6221f`。
  本次提交源码另按完整SHA归档到同一服务器source目录，不覆盖历史产物。
- 已完成：环境与拍摄交接、可移植参考入口。运行中：本任务无新增作业。
  未完成：完整放置/strict、正式步长和跨条件验证；全程仍49.428mm/45.880Nm/.370425m/s、
  最大穿透.653202mm、task/strict=false，不把画面认可当成功。VMC新采集/ESN新学习待后续推进。

## 2026-10-02 — 球撞响应与棍推掌部修正；保持期滑脱已观察，整场仍失败

- 用户要求先修物理交互，暂缓ESN算法修复。本轮未重训、未改WBC/actor输入/权重/执行器限制。
  开工/收工核对main `b75ef8e177a6bd149786b74279704ea8caaa0b92`、baseline
  `e564e09a691293802ec76c237d717b202d592e85`；不影响baseline四特化场景运行。
- 独立tool-contact-v5：1kg/半径60mm球正撞掌部；棍升到.64m、改从对侧推掌部、缩短杆身，
  固定保持到23.5秒，消除新杆身与人体/物块接触。旧默认环境不变，新旧分数不得混算。
- 球零入射速度反事实确认13.845mm额外手部偏移。棍仅接触hand，在仍伸出时15.1201–19.1801秒
  已无受力接触；随后回碰，最长连续接触.1061秒，不能宣称平滑永久滑脱。前28秒穿透.111485mm。
- 55秒开发回合仍task/strict=false，后段原柱子/link7穿透.653202mm；
  RMSE49.428mm、峰矩45.880Nm、峰速.370425m/s。不移柱子/放宽门槛去掩盖失败。
  源码新增延迟球撞日志修复、逐子步接触对象/受力统计、200Hz状态、原速/慢放近景。
  ESN动作/储备池重放误差0；补日志前后28秒状态/动作逐元素一致，公共路径回归检查通过。
- 保留1条入口相交拒绝、3条候选诊断失败、完整v5、28秒遥测复核、3秒球对照。无运行中仿真。
  已核验142项服务器证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/`；
  manifest SHA256 `936b6af1988b65bfce16dcf6c4fa44b2b1bf8460913b59aff2accb6496c6221f`。
  接入/参数/全部失败和媒体见`code/mujoco_6d_vmc_benchmark/docs/TOOL_CONTACT_REPAIR_20261002.md`，
  README/联合进度/周报同步。未完成平滑不回碰、全场安全和最终放置。

## 2026-10-02 — 未建图凸边阻塞任务；统一修复路径接回，旧ESN/MLP尚未解决

- 按用户桌角视频新增独立物理凸边（20×90×70mm），从reset存在、只在先验地图中遗漏，
  不给actor增加感知。保持靠手桌角目标、放置门槛、顺序扰动与执行器限制。
  开工及收工前核对main `f3437ade3a44e52db4a118d5c112e6cabbb48d41`、baseline
  `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`，baseline分支未改。
- 发现并修复公共接回逻辑误把纵向前进计入80mm横向容差。相同虚拟绕行旧版卡14/27，
  修复后27/27并进入下一阶段，终点到达约束保留；几何/IK绕路审计不冒充物理成功。
- v1/v2共8条55秒开发回合完成，每组对应状态/动作数组重跑完全一致。
  名义无新凸边task/strict成功；名义有凸边11.3937–55秒持续接触并失败。
  原ESN/MLP仍在触及新凸边前停carry，均task/strict失败；三指标分别
  26.496mm/37.763Nm/.084326m/s、24.843mm/36.977Nm/.061384m/s。
  无重训；不能声称“加柔顺即可成功”、ESN优势或正式步长通过。
- 子步指标、动作/ESN状态重放、共同规划/阻塞MJB、55秒1375帧MP4/275帧GIF已核验。
  无运行中仿真。未完成：新参考下学生正常推进、接触恢复放置、多条件/正式验证。
- 已逐文件SHA256核验189项共享证据，含实际执行源码快照、权重、轨迹、审计和媒体：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unexpected_edge_contact_review_20261002_v2/evidence/`。
  `archive_manifest.json` hash：`91dc23cc9d20d8ab4815a2c07164db41d135521d5995774a5441ff9d45bb1544`。
  新报告`code/mujoco_6d_vmc_benchmark/docs/UNEXPECTED_EDGE_CONTACT_TASK_20261002.md`记录
  场景尺寸、命令/权重、成功定义、失败和baseline接入；README/进度/周报同步。

## 2026-10-02 — 靠手桌角新任务与静态路径规划；名义成功，旧ESN仍失败

- 用户授权新目标/成功定义：物块放到靠手桌角并松手稳定即task成功，接触覆盖改为诊断。
  新协议planned-hand-corner-v1，目标[.690,-.310,.545]m；旧协议/结果保留。
  开工main7674ed9、baseline699e317，baseline未改。新增静态A*扫掠规划与IK姿态搜索，
  原竖直姿态不可达，选择-35度；不向ESN加入环境真值，模型几何和执行器限制不改。
- 两条完整55秒/单线程3GiB开发验证完成：同一规划文件hash50f32f7e，零动作名义执行
  成功放置，XY误差10.797mm；原ESN仍停carry，不能把名义成功说成ESN成功。
  ESN三指标43.370mm/38.515Nm/.094228m/s，名义22.767mm/42.020Nm/.068210m/s。
  动作/状态/子步和独立末端放置审计通过；规划绕障与松手边界检查通过，完整GIF/MP4已保存。
- 已核验服务器独立归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/planned_hand_corner_pair_20261002_v1/`；
  evidence.tar.gz SHA256=`7b37f3512c95b3f3d5cd0dd0e8546171727e9faec5f8977ef7a8f88f62b4e73e`。
  新协议、旧strict区分、baseline复用与失败分析见
  `code/mujoco_6d_vmc_benchmark/docs/PLANNED_HAND_CORNER_TASK_20261002.md`。
  未完成：新参考下ESN可靠放置；本轮无重训/其他baseline/正式步长，所有作业结束。

## 2026-10-02 — 原ESN权重完成12秒推杆时序评估与全程媒体

- 按用户请求复用上次动图的p=.1 ESN（checkpoint9f4b5a81），只改变推杆时序，未训练。
  开工核对maind43f050、baseline699e317。本机单线程/3GiB、MuJoCo3.11.0完成55秒开发
  评估；task/strict仍false，停load_transfer；RMSE38.708mm、峰矩48.463Nm、峰速
  .094228m/s、外部穿透.122975mm。人手接触4.2813–8.8977秒；推杆/柱子未记录有效接触，
  不把时序分离或低指标冒充成功。动作/储备池重放误差0，550000子步物理指标独立复算通过。
- 全景/末端/柱桌角三视角GIF及MP4完整55秒原速，实测帧数275/1375，已目视核验。
  新单回合启动器保存原参数/源/模型/权重hash、执行和审计；所有作业完成，无新增campaign。
- 已核验服务器归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_sequential_r12_media_20261002_v1/`。
  evidence.tar.gz SHA256=`c6938228a27aeb7a6b08d33245d96325fb4ec0cd2274582cfb89cc9a268c1e31`。
  详细结果及源码/媒体地址见`code/mujoco_6d_vmc_benchmark/docs/ESN_SEQUENTIAL_R12_REPLAY_20261002.md`。

## 2026-10-02 — 顺序扰动修复：人手撤回后2秒启动推杆

- 用户授权将combined-v4推杆起点7→12秒，登记独立`sequential-r12-v1`；人手3–10秒、
  推杆12–21.5秒，球2秒及其他物理/任务/gate/actor/执行器设置不变。旧配置与结果保留。
  新共享配置和验证器启动检查拒绝误带旧时序。已有ESN/MLP/baseline权重和参数不需重训。
- 开工实时核对main5dc538b、baseline699e317；未改baseline分支、未重启旧campaign。
  3GiB/单线程的两个80ms检查成功：新旧MJB5eaee4aa及所有轨迹数组一致，权重hash未变；
  全55秒指令检查无重叠。新55秒实际接触/任务/strict尚未评估，不能报告效果改善。
- 已核验共享源码/配置/执行证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_sequential_r12_check_20261002_v1/`。
  evidence.tar.gz SHA256=`b2d10aa5d0f2d271c3bd514ebad3ad8e46f92d364b50ea744a0aa04811b0008b`。
  接入与未完成项见`code/mujoco_6d_vmc_benchmark/docs/OFFICE_SEQUENTIAL_R12_HANDOFF_20261002.md`。

## 2026-10-02 — current frozen combined-v4 full three-view media

- 按用户请求展示当前最终测试环境，开工核对main38d40c1、baseline699e317；场景未变。
  以最新p=.1 ESN已保存轨迹和MuJoCo3.11.0归档MJB生成全景/末端/柱桌角三视角，
  不重跑物理或训练。仍标注task=false/strict=false及load_transfer停滞，不伪装成功。
- 渲染工具支持显式fps与GIF抽帧，MP4保留1375帧/25fps/55秒原速，GIF275帧/5fps/55秒；
  GIF缩至960×280以限制内存。实测视频/GIF时长与帧数一致，已目视核验终帧。
  本地渲染使用3GiB服务和单线程。短碰撞应优先看25fps MP4，GIF不代表高频物理采样。
- 媒体和输入输出hash已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/current_office_v4_esn_media_20261002_v1/`。
  GIF SHA256=`0c8a370ac63a4d0011df0f646128db93b5be7d89c4c9f81f4b5c67e33a1e7067`；
  MP4=`e92115da80566fb5a3ed6984a1490caa8168c5760ea9b18c4fb0ec40e9227f49`；
  manifest=`9c98c016c435423fab0ee0b59f5373c78c535e286118e681069b1469207fbfdc`。
  对应原始输入仍为temporal_s52_latent_dropout_20261001_v1/p010_eval/esn_combined_v4，
  MJB5eaee4aa未改。自动研究任务保持暂停；本次仅完成媒体展示。

## 2026-10-01 — memory/dropout diagnostics audited; budget conflict closed out

- 开工实时核对main e0c963b、baseline699e317，未修改baseline。固定权重ESN逐次清空历史
  回合完成：task/strict=false，停align，25.213mm/34.820Nm/.076344m/s；没有抓起物块，
  不能把低指标解释成改善。动作与状态按实际reset语义独立重放，最大误差0。
- 同teacher九轨迹、7/2split、seed152/153、160epochs/1120更新与128+128单元预算下，
  完成p=0/.1整段128维特征dropout对照。ESN从lift到load_transfer但仍失败，
  三指标48.971mm/43.600Nm/.116950m/s→44.666mm/47.458Nm/.094228m/s；
  MLP两组task=true，p=.1为46.587mm/44.587Nm/.073259m/s；五条strict均false。
- 五条55s/550000子步/dt1e-4独立审计通过：checkpoint/MJB绑定、有限值、物理指标重算、
  动作/储备池精确重放。p=0权重及原始轨迹与原冻结参考逐字节一致。两dropout组教师身份、
  原始数据hash、seed/epoch/归一化/储备池不变；相同dropout概率不等于相同表征语义。
  全部使用冻结MuJoCo3.11.0/MJB5eaee4aa、真实cgroup3GiB/单线程，无新环境/gate。
- 纠正预算处理：自动化创建05:48:54.070UTC，按创建+8小时保守推算13:48:54.070，
  但前几轮误用唤醒日程16:20作派发授权。未找到独立起点证明延期，晚期诊断不得写作
  原八小时内完成。识别冲突后没有新campaign；已启动末回合15:40:30结束并审计。
  heartbeat已PAUSED、仿真为0；AGENTS新增预算依据规则，原配置/执行记录保持真实，
  新增明确标为事后的BUDGET_RECONCILIATION.json。继续实验需新的明确预算。
- 已核验归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_memory_dropout_20261001_v1/evidence.tar.gz`，
  232570508bytes，SHA256 `4ed503552bea79609578040aa4cff344a790bf75051313a183764b8e53820bf5`。
  运行前源码分别为服务器共享根下
  `source/078446e00aa5470ad1bb68caaa1932d35d802c00/repository.tar`（SHA
  `50b0a55ad2a8d2264f88e23733679e3f43101bf685445fc1a3ab72fe1557c84c`）及
  `source/f4422c9b56ef97d1889b774c8d843a1526d4905d/repository.tar`（SHA
  `10e042986438cddf1df85fd1d5679c70d72a9dbb567177a755f4761e1abccc3d`）。
- 完整报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MEMORY_DROPOUT_DIAGNOSTIC_20261001.md`，
  联合进度/周报/小证据同步。完成了诊断和归档，未完成ESN任务/strict、跨条件泛化和formal；
  不因阶段推进或回放MSE宣称ESN优势。

## 2026-10-01 — register paired sequence-consistent latent dropout

- seed52固定权重清空记忆回合已完成，task/strict=false，停align，未证明清空历史能修复；
  原始失败与精确动作/状态审计保留，结果报告稍后归档。
- 预提交固定p=0与p=.1两组：每组ESN/MLP均160epochs、1120优化步、相同7/2身份留出、
  seed152/153及锁定九条teacher。ESN的128维储备池特征与MLP第一隐藏层128维特征施加
  同概率、整段序列一致的inverted dropout，推理关闭；保留128+128神经元、原输入/gate。
  表征不同，因此不是严格等价结构消融，也不从测试回合挑概率。
- 新训练/评估监督器串行两组，MuJoCo3.11.0、真实3GiB/单线程；每阶段记录执行与hash，
  16:20UTC后不派发新阶段。补全teacher原始文件hash校验、训练运行时/config元数据；
  eval支持显式新checkpoint来源。当前仅注册，未声称已启动或提升。

## 2026-10-01 — register seed52 closed-loop memory intervention

- 开工实时读取main e0c963b与baseline699e317日志；本机/Spark同类评估均空闲。
- 注册一条固定ESN checkpoint的reset_each_observation闭环因果对照，权重、actor输入、
  冻结3.11.0/MJB、scene/gate/执行器限制、seed/55s/dt1e-4保持不变。复用刚完成的
  同条件ESN/MLP作为参考，不重复启动MLP。配置temporal_s52_memory_ablation_20261001.json。
- 守护启动器增加显式方法/记忆消融选项；独立审计按真实记录的记忆语义重放动作和状态。
  本条先提交再运行；这是诊断，不是部署时混合控制、已改进学习或任务成功结论。

## 2026-10-01 — frozen-runtime seed52 pair completed and audited

- 本轮开工核对main d29e504、baseline699e317；运行前注册提交5572a73后，本机服务
  sii-temporal-runtime-s52-20261001于15:12:17–15:15:39UTC串行完成两条，均rc0，
  真实cgroup memory.max=3221225472/单线程。当前无仿真运行，未改baseline或启动训练。
- 同seed52 checkpoint回到冻结MuJoCo3.11.0，两MJB精确匹配5eaee4aa。
  ESN task/strict=false，lift，RMSE/峰矩/峰速/穿透
  48.971mm/43.600Nm/.116950m/s/.131457mm；MLP task=true/strict=false，retreat，
  46.908mm/45.907Nm/.070165m/s/.151728mm。全部55s/550000子步/dt1e-4。
  ESN相对原3.14.0的RMSE降低23.252mm，但失败未解决，不能宣称算法提升。
- 新旧四条独立审计动作/储备池replay最大误差0，三指标复算、模型/checkpoint绑定、
  原参数和源码hash核对通过。错误运行时启动测试在建目录/仿真前拒绝3.14.0。
  初次报告工具Path类型错误已修正，仅重跑只读报告，没有重跑回合。
- ESN末10秒误差中位28.920mm、速度.000860m/s、ready=0；该窗口无输入>12截断、
  无储备池abs>.95饱和。相同输入离线重置历史改变动作RMS .157981，属于读出依赖诊断，
  不是闭环记忆消融成功。下一步聚焦历史状态与持续残差，不改gate或解锁formal。
- 证据已核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_frozen_runtime_s52_20261001_v1/evidence.tar.gz`，
  92494783bytes，SHA256 `0b51f23b479282e35343515918ede84e090fde4951259f77e5ac137af36e7c75`。
  运行源码快照：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/5572a733a2fbc97b78201ee586cba188c49d43a3/repository.tar`，
  SHA256 `f5ddd6459b3589404996eb55773a6b2b794d6df37639e378c9890b23d323d87a`。
- 报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MLP_FROZEN_RUNTIME_PAIR_20261001.md`，
  联合进度/周报/小证据同步。已完成运行时复核与归档；未完成ESN任务/strict稳健成功、
  跨条件泛化和正式步长验证，不把单checkpoint对照当泛化率。

## 2026-10-01 — register frozen-runtime seed52 verification

- 实时查询核对 main d29e504、baseline 699e317并读取对应日志；baseline暂停事项保持不动。
  当前本机/Spark没有运行中的同类评估，未启动重复作业。
- 注册两条串行复核：固定seed52 ESN/MLP checkpoint和原55s/dt1e-4参数，仅恢复冻结
  MuJoCo 3.11.0。启动器检查真实cgroup MemoryMax≤3GiB、单线程、manifest/checkpoint/
  源码hash，并在保存MJB之后、回合执行之前核对5eaee4aa模型hash，失败保留且不重试。
- 配置 temporal_frozen_runtime_diagnostic_20261001.json；工具
  verify_temporal_frozen_runtime_20261001.py。每条保存独立execution/原始轨迹/三指标及
  action/储备池审计；不训练、不改环境/gate/actor/限制，不解锁formal。此条提交在运行前，
  尚无新性能结论；运行记录和服务器归档地址在完成后补充。

## 2026-10-01 — temporal evidence integrity, runtime drift and synchronization repair

- 实时核对 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、baseline
  `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`；授权外部网络下 GitHub/Spark 均可达，
  先前失败至少部分为沙箱限制，不能继续称服务器不可达。未合并或操作 baseline 作业。
- 最新六条回合补强审计通过：checkpoint/模型元数据绑定、actor/状态/物理数值有限、
  550000 子步与三指标复算、精确 action/reservoir replay。ESN task 0/3、MLP 3/3，
  strict 各0/3；这些是不同开发配置，不是独立泛化成功率。没有新仿真或正式评估。
- 定位运行时偏移：旧冻结 MJB 仅被现有 MuJoCo 3.11.0 加载，近期 MJB 仅被3.14.0加载。
  最新六条模型hash一致；同版本两模型618个公开字段一致。禁止把跨版本结果作仅算法
  变化排名。后续冻结评估恢复 .venv-canonical-rl/3.11.0，先记录真实执行元数据和限制。
- seed42配置恢复到62f8c65原字节；seed52另存
  `configs/esn_mlp_temporal_consistency_narrow_rep_seed52_20261001.json`，历史命令不改。
  更正窄屏/seed52的“预提交注册”、独立execution.json及历史MemoryMax过强描述。
  本轮只读审计确实使用systemd MemoryMax=3G/单线程；不能反推历史已遵守。
- 原始temporal七组成对回合、训练记录、checkpoint、MJB/XML与新旧审计已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_integrity_20261001T1450Z/evidence.tar.gz`：
  652346695 bytes，SHA256 `0d30662ae0479b5594f8240eb4f019f7e2f9ee7b76ad974b80b8fdd6216bd460`。
  运行源码快照：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/434e46fbedfc88df11d7ff8c44f2b3d064ebd217/repository.tar`，
  SHA256 `d23b4c74298ff87b5079002f4e3bb246582f4db6447a97613eab7da1e88479b2`。
- 报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MLP_TEMPORAL_INTEGRITY_20261001.md`；
  同步联合进度、周报和小型JSON证据。已完成配置/审计/归档修复，当前无新实验运行；
  未完成同checkpoint冻结运行时复核、ESN任务/strict稳健成功及formal步长验证。

## 2026-10-01 — temporal-consistency delta=0.25 replication completed locally

- 开工再次核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；`git ls-remote` 仍因网络不可达
  失败，未把缓存当作最新远端，未修改 baseline；本机无运行中的 evaluator/training 进程。
- 预注册配置 `configs/esn_mlp_temporal_consistency_replication_20261001.json`，锁定 manifest
  SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 split、
  canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；只复现
  `delta_weight=0.25`，ESN seed=`2026100152`、MLP seed=`2026100153`。
- ESN task/strict=`0/1`,`0/1`，停在 lift，指标 `72.223 mm / 44.403 Nm / 0.125044 m/s /
  0.131457 mm`；MLP task/strict=`1/1`,`0/1`，完成 retreat，指标
  `46.980 mm / 45.918 Nm / 0.070165 m/s / 0.151728 mm`。两条均为开发 `dt=1e-4`、55 s、
  550000 子步，失败回合完整保留。
- 独立审计 action replay 最大误差为0、ESN reservoir replay 最大误差为0，三项物理指标
  重算一致。新增报告 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_REPLICATION_20261001.md`；
  结果否定首轮 `delta=0.25` ESN 的稳健改善，formal `dt=5e-5` 继续锁定。大产物仅本地，
  arm1/GitHub 网络仍不可达。

## 2026-10-01 — temporal-consistency narrow follow-up completed locally

- 开工核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；本轮
  `git ls-remote` 因网络不可达失败，未把缓存 SHA 当作最新远端，也未修改 baseline。
- 预注册配置 `code/mujoco_6d_vmc_benchmark/configs/esn_mlp_temporal_consistency_narrow_20261001.json`
  （SHA256 `4e6fd694756b73fd964f9f1fe1ab6e71eee98f4da165c06f5f79d48851eac886`），
  固定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、
  7/2 split、canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；
  只测试 temporal delta loss `0.25/0.75`。
- 四条开发闭环均 55 s/550000 子步。ESN task/strict=`0/2`,`0/2`，MLP
  task/strict=`2/2`,`0/2`。`delta=0.25` ESN 到 retreat、RMSE `52.502 mm`、峰矩
  `45.556 Nm`、峰速 `0.117007 m/s`、穿透 `0.146245 mm`、推杆最长接触 `0.7673 s`，
  但未完成 placement；`delta=0.75` ESN 停 carry。MLP 两条均 placement 完成，一条缺
  required contact coverage，另一条球反弹失败，均 strict=false。
- 新增独立审计脚本 `tools/audit_temporal_narrow_screen_20261001.py`（SHA256
  `c9639aecdcb26cce9bcfa394e471a1e2c953224456b77ab44dfec5c582e82c3f`），四条 action replay
  最大误差为0，ESN reservoir replay 最大误差为0，物理子步指标独立重算通过。新增专题报告
  `docs/ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md`；大产物和 raw rollout 仅本地，
  arm1/GitHub 网络仍不可达，待恢复后同步。formal `dt=5e-5` 继续锁定。

## 2026-10-01 — temporal-consistency candidate seed replication completed locally

- 对首轮 `delta_weight=1.0` ESN 候选预注册第二 seed `2026100142`（MLP `2026100143`），manifest、7/2 split、canonical48D/action7、combined-v4、gate、禁止输入和执行器限制均未变。
- 复现 ESN 在 carry 停止，task/strict=false，RMSE/峰矩/峰速/穿透=`257.986 mm/44.770 Nm/0.1423 m/s/0.1774 mm`；MLP task=true、strict=false，指标=`58.208/45.395/0.1178/0.1317`。两条均完成550000子步，独立 action/储备池/物理审计通过。
- 复现否定首轮 `delta_weight=1.0` ESN 的稳健泛化结论；formal `dt=5e-5` 仍锁定。复现原始证据保留在 `outputs/esn_mlp_temporal_consistency_20261001_rep_seed42/`，大产物仅本地待同步。

## 2026-10-01 — temporal-consistency ESN/MLP screen completed locally

- 注册并完成纯 ESN/MLP action-delta loss 屏幕，候选 `delta_weight=0/0.5/1.0`。锁定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 identity split、canonical48D/action7、128 宽度、combined-v4、原 gate、禁止输入和执行器限制；只改变训练目标中的相邻 action 增量损失。
- 六条均为开发 `dt=1e-4`、55 s、550000 子步。ESN task/strict=`0/3`,`0/3`，最终阶段 carry/carry/load_transfer；`delta_weight=1.0` ESN 最接近完成但仍未放置。MLP 的 `0.5/1.0` 完成 task，strict=`0/3`，required contact coverage 仍失败。六条指标和 checkpoint hash 见 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md`。
- 六条独立 action/储备池/物理子步审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，均为550000物理子步。没有 strict 候选，formal `dt=5e-5` 继续锁定；结果不支持 ESN 优势。
- 新增配置、训练器和专题报告。原始 rollout、checkpoint、MJB 和失败回合仅保留本地待同步；本轮 GitHub 与 arm1 网络仍不可达。

## 2026-10-01 — low-scale ESN/MLP weight-decay screen completed locally

- 完成预注册 `weight_decay=1e-5/1e-4/1e-3` 屏幕。锁定 teacher manifest SHA256=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`，固定 7/2 identity split、canonical48D/action7、ESN/MLP 宽度128、`input_scale=0.25`、combined-v4、原 gate、纯本体输入和执行器限制；仅改变 AdamW weight decay。
- 三组均为开发 `dt=1e-4`、55 s、550000 物理子步。ESN 三组 task/strict 均为 false，全部在 lift 停滞；MLP 三组 task=true、strict=false，均因 combined contact coverage（含柱子等要求）不足而失败。ESN 的 RMSE/峰矩/峰速/外部穿透分别为 `77.173/42.170/0.1106/0.1635`、`75.485/42.723/0.1078/0.0997`、`73.093/41.235/0.1134/0.0919`；MLP 分别为 `48.442/44.781/0.0662/0.1106`、`60.176/45.249/0.1172/0.1323`、`47.831/44.426/0.0702/0.1666`。
- 六条独立审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，物理子步与55 s时长一致。两次仿真前 setup failure（hash变量错误、teacher root错误）保留并不计实验回合。结果不支持 ESN 优势，formal `dt=5e-5` 仍锁定。
- 新增报告 `docs/ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md`、配置和训练器；修复审计器以支持无 reservoir 的 MLP。专题输出和 checkpoint 目前仅本地、待 arm1/GitHub 网络恢复，未声称远端归档；详见专题报告与联合进度。

## 2026-10-01 — low-input-scale pure ESN output-gain screen completed locally

- 在已登记的 `input_scale=0.25` ESN checkpoint 上只改变 `output_gain=0.80/0.90/0.95`；
  base SHA256=`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_gain_screen_20261001.json` SHA256=
  `3e7a79e32cf17ebbd7fc6a81ae9703d27f5c09ed8a69746ce82a5c5fb34fde67`。
- 固定 teacher manifest、7/2 split、canonical48D/action7、combined-v4、原 gate、禁止
  输入与执行器限制；三条均为开发 `dt=1e-4`、55 s/550000 子步，task/strict=`0/3`、`0/3`。
  `.80/.90/.95` 最终 lift/carry/lift，指标分别为
  `60.590/37.618/.1031/.1257`、`144.782/37.867/.1395/.1705`、
  `73.919/37.051/.1019/.1150`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）；柱子
  覆盖全部失败。
- 三条独立审计均通过：action/reservoir replay 最大误差为0，物理子步均550000；失败 raw
  rollout、MJB、checkpoint 和审计保留在 `outputs/esn_low_scale_gain_screen_20261001_v1/`。
  结果只说明增益单因素没有恢复严格任务，不支持 ESN 泛化或相对 MLP 优势。
- formal `dt=5e-5` 继续锁定；arm1 与 GitHub 网络不可达，产物仍仅本地待同步。

## 2026-10-01 — low-input-scale pure ESN alpha screen completed locally

- 开工读取了缓存 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline
  `4dad929b6550b167943becd271836f0c74a21a38` 的更新日志；本轮 fetch/SSH 在当前网络下
  失败，未把缓存冒充最新远端，也未修改 baseline。
- 在先前唯一一次 `input_scale=0.25` task-success 的 ESN checkpoint 上预注册并物化
  action-readout `alpha=0.25/0.50/0.75`。base checkpoint SHA256=
  `99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_alpha_screen_20261001.json` SHA256=
  `2f286923b0f1a701f42e463553b2f0399fc2b3eba797321536e247a408604f79`。
- 固定 teacher manifest、7/2 identity split、canonical48D/action7、128 ESN、combined-v4
  环境、原 gate、禁止输入和执行器限制；三条均为本地 `.venv-rl`、单线程、开发
  `dt=1e-4`、55 s/550000 子步。结果 task/strict 均 `0/3`：alpha .25 停 lift，
  `.50` 停 carry，`.75` 停 lift；柱子接触覆盖均失败。三项指标分别为
  `68.485/35.127/.1010/.1423`、`138.424/39.585/.1275/.1373`、
  `59.341/37.282/.1041/.1101`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）。
  `.50` 推杆最长连续接触 `.6642 s`，但没有转化为任务成功；`.75` 球反弹失败。
- 三个独立审计均通过：action replay 与 reservoir replay 最大误差均为 `0`，物理子步为
  `550000`，最长单回合 RSS 约 `667 MiB`。所有失败 raw rollout、MJB、checkpoint 和审计
  保留于 `code/mujoco_6d_vmc_benchmark/outputs/esn_low_scale_alpha_screen_20261001_v1/`。
  详细结果见 `docs/ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md` 和联合进度文档。
- 本轮无 strict 候选，formal `dt=5e-5` 继续锁定。arm1 归档尝试因 SSH 不可达未完成，
  产物明确标记为本地待同步；GitHub push 待网络恢复。

## 2026-10-01 — fixed-reservoir ESN readout-seed decomposition completed locally

- 固定 input-scale=`0.25` 和 reservoir seed=`2026100101`，仅改变 readout seeds `2026100121/22/23`，预注册配置 SHA=`c5f31edb3263fa16702229bfd14d74f7f6b584d0f9a8136f5c51d521385e4828`，训练脚本 SHA=`9e30fd12ed056bedcdafe80a32deb67786aa20e6f22b4612b8ebfecdccea5d2f`。
- ESN task/strict=`0/3`、`0/3`，停在 lift/carry/carry；MLP task/strict=`3/3`、`0/3`。所有回合 550000 子步，动作和 ESN 储备池 replay 最大误差为 0，物理审计通过。
- 独立 audit SHA=`d82652a366c6f2d5cd6b3562c9b483ae298563f5a130955cf41aad3a8f6a2cb3`，73 文件收据 SHA=`eda963478fa3362d7ed4078bb6d6e9eb1bd500126310670eed8b83bfcbe54af6`。固定 reservoir 仍未消除 ESN 对 readout seed 的敏感性，也没有 strict 候选。
- 未完成：formal `dt=5e-5`、arm1 归档和 GitHub push；网络仍不可达，产物标记为本地待同步。

## 2026-10-01 — pure ESN input-scale screen and replication completed locally

- 在冻结 teacher manifest、office-v5 combined-v4、gate、canonical48D/action7、禁止输入和执行器限制下，预注册输入权重尺度 `0.25/0.45/0.80` 屏幕；配置 SHA=`1197d1739ae0e2f1af9671cf4dbabbd1350bb4ab589ef7b951708fd5bd87deff`，训练器 SHA=`881d670a56f1723576534020ef4baebddd0ed29e5e0f7bb2f7a4ffc9e0db77c6`。
- `input_scale=0.25` 的单个 ESN seed 完成 task、strict=false，RMSE/峰矩/峰速/穿透=`68.471 mm / 48.004 Nm / 0.1164 m/s / 0.1499 mm`；0.45/0.80 ESN 分别在 carry/load_transfer 停止。MLP 对照全部 task=true、strict=false。
- 对唯一 task=true 候选预注册复现 seeds `2026100118/19/20`，ESN task/strict=`0/3`、`0/3`；复现 audit 与 73 文件收据 SHA=`688ae6b3556023d64eb1c68ba2d84cde0b6ca461892240cbe9f8a83666b484f2`。屏幕收据 SHA=`0fe9e346533fb27ba4ba306b49d9bc128dbe2bf584b1a168d1ae8dba934e42a2`。因此单 seed 成功不能称 ESN 泛化或优势。
- 所有回合均为开发 `dt=1e-4`/550000 子步，严格 gate 无一通过，未解锁 formal `dt=5e-5`。GitHub/arm1 仍不可达，产物仅本地待同步。

## 2026-10-01 — pure ESN spectral-radius screen completed locally

- 在同一 teacher manifest、场景、gate、actor 输入和执行器限制上完成预注册 spectral-radius 屏幕；只改变 128 单元 ESN reservoir 谱半径 `0.60/0.90/1.10`，每组配同宽度 MLP。配置 SHA=`e96a9880d607d77390b062542e25dab677880587a2483aeb3dcfc4e9b48f0c17`，训练脚本 SHA=`9381becd58ce6c750672e6184f4a452004990bec5e98dd989ba8eab97fab5e5c`。
- 三组 ESN task/strict 均失败：0.60 在 lift，0.90 在 lift 且外部穿透 `1.5602 mm`，1.10 在 carry。MLP 对照仅 0.90 完成 task、strict=false；所有行都是 55 s、`dt=1e-4`、550000 子步开发结果。
- 独立审计 `outputs/esn_mlp_spectral_screen_20261001/INDEPENDENT_AUDIT.json` 通过，六条动作 replay 最大误差为 0，ESN 储备池 replay 最大误差为 0。73 文件收据 SHA=`6505943bf8a8711fb03a2e48a86545cc1937e77b8f1e64c5e9459179a182ae0`。完整结果和失败原因见 `docs/ESN_SPECTRAL_SCREEN_20261001.md`。
- 未完成：ESN strict 泛化、formal `dt=5e-5`、arm1 归档与 GitHub push。网络仍不可达，产物明确标记为本地待同步。

## 2026-10-01 — pure ESN reservoir leak-time screen completed locally

- 开工核对 main 缓存 `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline 缓存 `4dad929b6550b167943becd271836f0c74a21a38`；再次 fetch 和 GitHub/arm1 SSH 均因网络限制失败，未把缓存当作最新远端，未修改 baseline。
- 预注册 `configs/esn_tau_screen_20261001.json`（SHA256=`cd21c44d4b0aa494f464d9aa450c9ff70b6d002361f924e19ae5c7a378d9a9d4`）并新增 `tools/train_esn_mlp_tau_screen_20261001.py`（SHA256=`510fd962ebcf96051f064e5a51bab6fa14a16af5afa9650babd52dd71be4fa09`）。只改变 128 单元 ESN 的 reservoir leak 时间尺度，保持 teacher manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、canonical48D/action7、7/2 identity split、估计负载训练权重、环境/gate/actor 输入/执行器限制不变；每个 profile 都训练同宽度 MLP 对照。
- fast/baseline/slow 三组均已完成 55 s、`dt=1e-4`、550000 子步闭环。ESN 依次在 lift/carry/lift 停止，task/strict 均为 false；MLP fast/baseline 为 task=true、strict=false，slow 为 task/strict=false。ESN 最佳 baseline 行的 RMSE/峰矩/峰速/穿透为 `86.080 mm / 40.585 Nm / 0.0862 m/s / 0.1540 mm`，但未完成 placement。
- 独立审计 `outputs/esn_mlp_tau_screen_20261001/INDEPENDENT_AUDIT.json` 通过；六条物理子步均为 550000，动作回放最大误差为 0，ESN 储备池回放最大误差为 0。汇总 70 文件收据 SHA=`361116939aee2ef4b6bedbcba828b215a516de3158434c00161e7e9c4694eea0`。完整结果和失败原因见 `docs/ESN_TAU_SCREEN_20261001.md` 与 `docs/ESN_VMC_JOINT_PROGRESS_20260927.md`。
- 未完成：strict 泛化成功、formal `dt=5e-5`、arm1 归档与远端 push。由于服务器不可达，本轮大产物仍标记为“本地、待同步”，没有声称服务器已核验。

## 2026-10-01 — paired ESN/MLP seed screen completed

- 完成预注册配置 `configs/esn_mlp_seed_screen_20261001.json` 的 seed
  `2026100106/07/08` 成对训练。三组均使用 manifest SHA256
  `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、固定 7/2
  identity split、估计负载训练权重、canonical48D/action7 和 128 宽度；环境、gate、
  actor 输入与执行器限制保持不变。
- 冻结 combined-v4 开发闭环均为 55 s、550000 子步、`dt=1e-4`。MLP 三组 task=true、
  strict=false；ESN 三组 task=false，seed106/107/108 分别停在 lift/load_transfer/lift。
  ESN/MLP 的 `RMSE mm / 峰矩 Nm / 峰速 m/s / 穿透 mm` 为：
  `874.772/55.664/0.1639/0.1089` vs `52.402/44.708/0.0730/0.1772`；
  `187.222/47.666/0.1601/0.1612` vs `33.860/44.542/0.0707/0.1530`；
  `37.743/38.843/0.0721/0.1714` vs `43.083/45.083/0.0724/0.1843`。
- 六条学生回合独立 action/状态/物理子步审计通过，ESN action/储备池 replay 与 MLP action
  replay 最大误差均为0；没有 strict 通过，未解锁 formal `dt=5e-5`。seed108 的 ESN
  数值指标接近成功但 placement gate 未完成，不能写成 task success或ESN优势。
- 训练峰值 RSS 约 832 MiB；初次错误的 `ulimit -v` 导致 PyTorch 库映射失败，相关失败日志
  保留并不计为实验回合。完整 output、checkpoint、raw rollout 和 audit 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_mlp_seed_screen_20261001_v1/`；
  evidence tar SHA256=`12ebe6d9529df5dd0bc967a45ed7a5ac77d1d0e4774d8fe10203ac5f158e5aa8`。
- 提交 `9888f6cc361004a70a24851e7915062ca5962a5f` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9888f6cc361004a70a24851e7915062ca5962a5f/repository.tar`，
  SHA256=`36563d9b960253ba1ec4a71ac3a4a1fea3966aa9afbdfe4727ad271e5ee9c589`。

## 2026-10-01 — pre-registered paired ESN/MLP seed screen

- 增加 `configs/esn_mlp_seed_screen_20261001.json`，预注册在锁定的 9 条 teacher manifest
  上使用 seed `2026100106/07/08` 成对训练 weighted ESN 与 MLP；仍为 canonical48D/action7、
  128 宽度、固定 7/2 身份留出和训练期估计负载权重。环境、gate、actor 输入和执行器限制不变。
- 先固定配置并提交，再按同一 combined-v4 冻结命令运行闭环；所有 seed、checkpoint、trace
  hash、失败原因和独立物理子步审计均保留。未运行前不解读结果。

## 2026-10-01 — pure ESN output-gain screen completed

- 完成预注册的纯 ESN `output_gain=0.80/0.90/0.95` 屏幕；只改变 v4 checkpoint 输出增益，
  不改 office-v5、gate、canonical48D actor 输入、执行器限制或 MLP。三条回合均为
  seed `2026091751`、55 s、550000 子步、开发 `dt=1e-4`。
- 结果：0.80 停在 carry，task/strict=false，RMSE/峰矩/峰速 `520.286 mm/41.950 Nm/
  0.1879 m/s`，穿透 `0.1688 mm`；0.90 停在 lift，`407.785/46.242/0.2134`，
  `0.1350 mm`；0.95 停在 lift，`454.745/44.605/0.2160`，`0.1243 mm`。三条均未完成放置，
  失败回合全部保留，没有候选解锁 formal `dt=5e-5`。
- 独立 audit `outputs/esn_gain_screen_20261001_v1/gain_{080,090,095}_audit.json` 全部通过：
  action replay 与储备池状态 replay 最大误差为 0，物理子步为 550000。配置 SHA256 为
  `1d0e8cb73db0a8effa142a3fcdbc2dd026edf70eaa4517231b72815895ce5c90`，基准 checkpoint
  SHA256 为 `bb0bd4df0f9467932c15999853f67fe662aaf5f34c06b79855d4d1ab9a4cf1b0`。
- 结果和审计保留在本地 `outputs/esn_gain_screen_20261001_v1/`，并已逐项核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_gain_screen_20261001_v1/`；
  文件收据 SHA256=`6ed5e73204de983d481200bcf5082a50e1259fbd55a281934aa33e7460dcff74`。
  预注册源码提交为 `9e9580a`，结果记录为 `0a611d4`，最终同步提交为 `7fa6a6e`。
- 对应 `7fa6a6e39459cf846f21400c7f5fa5d4301da1ca` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7fa6a6e39459cf846f21400c7f5fa5d4301da1ca/repository.tar`，
  SHA256=`1a79dd2583859e38ce785d2cd96bfb5efd1b0a2af436c4565224123c92277015`。
- GitHub `main` 已成功推送至 `7fa6a6e`；服务器归档与源码快照逐项核验通过。
- 已完成：三组闭环、三项物理指标重算、动作/状态重放审计和文档更新。未完成：服务器归档、
  formal `dt=5e-5`（门槛未满足）及 ESN 跨条件成功。

## 2026-10-01 — pre-registered ESN output-gain screen

- 注册第二个纯 ESN 算法屏幕，只改变 v4 checkpoint 的 `output_gain=0.80/0.90/0.95`；不
  组合 alpha、不改环境、gate、actor 输入、执行器限制或 MLP。计划见
  `configs/esn_gain_screen_20261001.json`，物化工具为
  `tools/materialize_esn_gain_screen_20261001.py`。
- 先提交预注册和固定 hash，再逐一运行 55 s/550000 子步开发闭环；未运行前不解读结果。

## 2026-10-01 — pre-registered ESN output-smoothing screen

- 在不修改 office-v5、gate、actor 输入、执行器限制或 MLP 的前提下，注册纯 ESN action
  readout `alpha` 屏幕，候选固定为 `0.25/0.50/0.75`；基准 checkpoint 为 v4 无权重
  ESN，完整命令和选择规则见 `configs/esn_alpha_screen_20261001.json`。
- 新增 `tools/materialize_esn_alpha_screen_20261001.py`，生成变体前固定 base/config
  hash；尚未运行闭环，结果不得提前解读。该预注册先提交，随后按单 MuJoCo/1线程/3GiB
  约束逐一运行，所有失败回合保留。

## 2026-10-01 — pure ESN alpha screen completed

- 按已推送的预注册计划，只改变 v4 ESN checkpoint 的 action-readout smoothing
  `alpha=0.25/0.50/0.75`；场景、gate、canonical48D 输入、执行器限制、MLP 和评测命令均不变。
- 三条开发回合均为 55 s/550000 子步、`dt=1e-4`，task/strict 全部 false：alpha 0.25
  停在 lift，RMSE/峰矩/峰速 `367.725 mm/50.319 Nm/0.2420 m/s`，穿透 `0.6467 mm`；
  alpha 0.50 为 `411.708/36.347/0.2306`，穿透 `0.1787 mm`；alpha 0.75 停在 carry，
  `95.040/41.629/0.0848`，穿透 `0.1276 mm`。alpha 0.25 推杆接触最长2.2952s，0.50为
  0.5018s，0.75为0.0038s；不能把接触时长换写成任务成功。
- 三条动作与储备池状态重放均为0，独立物理子步审计通过；未有候选解锁 formal `dt=5e-5`。
  原始回合、失败和审计保留在 `outputs/esn_alpha_screen_20261001_v1/`，并已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_alpha_screen_20261001_v1/`；
  38 文件收据 `FILE_SHA256_REL.txt` SHA256=`45dcf2d710a8ea12cd0f6ba0277669da76deb6af889347e6ec1f9e01575fbffa`，
  远端逐项校验通过。
- 最终提交 `afba210d2eb554b2e3fd7ca5c91363549cbacf2b` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/afba210d2eb554b2e3fd7ca5c91363549cbacf2b/repository.tar`；
  本地/远端 SHA256=`61b0284f613a13677b5c969be7c5dfca965b491c591efd34806cfb055dc9cb54`。

## 2026-10-01 — v3 teacher-label correction and frozen ESN/MLP rerun

- 开工按 `sii-research-sync` 核对本地 `origin/main` 缓存起点
  `3336864707c1e59a1015568a0aea1891e18b8980`；本轮网络受限，无法重新连接 GitHub 或
  `arm1@192.168.31.70`，因此未把缓存 SHA 冒充最新远端状态。远端没有可读的 `baseline`
  分支／更新日志；baseline 工作区未修改。
- 修正 `tools/train_vmc_teacher_esn_mlp_20261001.py` 和 weighted trainer：训练目标绑定
  `execution_chain.npz/filtered_action`，保留 raw `rollout.npz/applied_action`，逐条校验两者
  shape 与 rollout/chain hash；metadata 增加 execution-chain、ESN/MLP 推理源码 hash，并
  更正 trainable 参数量为 ESN 23,559、MLP 23,687。新增
  `tests/test_student_distillation_20261001.py` 的标签出口回归测试。
- 在冻结 manifest、combined-v4、canonical48D/action7、gate、actor 输入与执行器限制下，
  使用本地 `.venv-canonical-rl`、单线程完成 v3 训练（seed `2026100104`）与无初始细步的
  55 s/550000 子步开发闭环。结果：VMC teacher task/strict=true/false，ESN=false/false
  （carry，RMSE 406.806 mm，43.246 Nm，0.2404 m/s，穿透 0.1929 mm），MLP=true/false
  （retreat，43.333 mm，44.405 Nm，0.0753 m/s，穿透 0.1012 mm）。动作重放均为 0，ESN
  储备池重放为 0，独立物理子步审计通过；strict 未通过，不解锁 formal `dt=5e-5`。
- v3 输出、首轮带细步诊断及失败回合保留在
  `code/mujoco_6d_vmc_benchmark/outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/`；详见
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`、联合进度与周报。checkpoint：ESN
  `a5560ca073c3afed6d553c1ee7a37ac32d537f1245aa6369feabeb022dff40b4`，MLP
  `e27c4ed63cd5f604c5338c90aa87b09e61a90f401a2d92f674c1e69a501e45f0`。v3/v4 随后同步到
  新的 arm1 归档目录（见末项），已有 v1 归档未覆盖。
- 验证：`pytest -q tests/test_student_distillation_20261001.py tests/test_esn_compliance.py
  tests/test_direct_esn_env_contract.py tests/test_office_memory_esn_20260927.py` → 14 passed；
  `git diff --check` 与两训练脚本 `py_compile` 通过。已完成：标签修复、v3 训练、闭环和
  独立审计。运行中：无本机仿真。未完成：arm1 归档、正式 `dt=5e-5`（门槛未满足）及
  strict 泛化成功。
- 追加预注册无负载权重控制 v4（seed `2026100105`, emphasis=0）：ESN task/strict=false/false、
  lift、RMSE 526.818 mm、峰矩44.416 Nm、峰速0.2204 m/s、穿透0.1323 mm；MLP=true/false、
  retreat、RMSE38.832 mm、峰矩44.286 Nm、峰速0.0807 m/s、穿透0.1527 mm。仍为
  55 s/550000 子步开发回合；动作/储备池重放及独立审计通过。v3/v4 均未过 strict，
  不解锁 formal dt=5e-5；v4 也已进入同一新的 arm1 归档目录。
- 随后将 v3/v4 完整输出（68个文件，含 checkpoint、55 s 原始 rollout、MJB、日志和两份
  独立审计）归档到已核验的新目录
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`。
  相对路径收据 `FILE_SHA256_REL.txt` SHA256=`ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`，
  远端逐项 `sha256sum -c` 全部通过；未覆盖已有 v1 归档。
- 已将本轮提交 `a2a926b5b4deee3dea9476e1eaefd5dcf211f09a` 的源码快照归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a2a926b5b4deee3dea9476e1eaefd5dcf211f09a/repository.tar`，
  本地/远端 SHA256 均为 `4e6fd79dbf6281217fa7dc718d5b9719be6a667be6fcf13930d35e26d9c7dd70`。

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-10-01 — VMC teacher 标签上的 ESN/MLP 加权读出续实验

- 开工核对 origin：`main=3336864707c1e59a1015568a0aea1891e18b8980`，随后复核远端
  `baseline=4dad929b6550b167943becd271836f0c74a21a38`；baseline 正在独立运行奖励主批次，
  本轮未合并、停止或改写其冻结源/作业。
- 新增 `tools/train_vmc_teacher_esn_mlp_weighted_20261001.py`，在冻结
  canonical48D/action7、相同 128 单元预算下，只对估计力/负载本体通道采用训练期平滑
  权重；actor、环境、gate、执行器限制均未变。新增报告
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`，并同步联合进度、周报和 README。
- 新 weighted ESN/MLP checkpoint SHA 分别为
  `2723e218b474e4414bbbf199eeda0099eae5dfae6af9fbd3e40cbe6b389483c9`、
  `992a6dcd99685f278687fcf4cf25e1e6d61171dc4dde650489c679f082497cdc`。
  同一 combined-v4 开发场景：ESN task=false、lift停滞，RMSE 688.378 mm、峰矩
  62.020 Nm、峰速 0.1800 m/s；MLP task=true、placement complete、strict=false，
  RMSE 50.381 mm、峰矩 46.634 Nm、峰速 0.0823 m/s、柱最长接触 0.6056 s。
- `tools/audit_vmc_teacher_esn_mlp_20261001.py` 独立审计通过：三行均 55 s/550000
  子步，动作/储备池重放和 RMSE/力矩/速度复算通过。两学生 strict 均 false，未解锁
  formal `dt=5e-5`；失败回合保留。运行中仿真 0，服务器归档待 SSH 恢复。
- 验证：加权模型训练与闭环均在本地 `.venv-canonical-rl` 单线程运行；10项 ESN/环境
  合约测试通过，`git diff --check` 通过。完整 campaign 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v1/`；
  远端 file-list receipt SHA=`5dc78c054067e88e3b34922023d3bbe476e251008e01941bfa0bd43525a34d96`，
  checkpoint hash 与本地一致。大型 rollout/checkpoint 未提交 Git。
- 首次代码/文档提交为 `48358e8af6c2563209d52e8f8eeeb852d9be9dae`；对应完整 source tar
  已归档到服务器 `source/48358e8af6c2563209d52e8f8eeeb852d9be9dae/repository.tar`，
  SHA256=`951556d584689f520f13d64d3ad0a9130641c067aa02185602835e31e4c9411e`。

## 2026-09-30 — 十小时窗口收尾：215条记录、9个唯一teacher条件与公平经典对照

- 13:29 UTC读取实际远端日志，13:55/13:57复核fetch：main=
  `cd38ad943b1cf16442ca181e44eae64579720986`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，未合并baseline、未干扰其旧暂停作业。
- 10小时派发截止13:48:16；最后派发13:46:18.620425、动态结束13:48:22.954650、
  归档结束13:48:50，continuation v2 rc0退出，截止后派发0。终态162搜索＋27验证记账
  （24动态/3初态拒绝）＋26collection，共212完整动态/3初态失败；缺失最后long0002
  阻抗配对明确保留，未补跑。定义3300不等于已执行/合法示范。
- 验证有效8fixture：VMC/导纳/阻抗task7/8、0/8、7/8；strict4/8、0/8、6/8；
  全要求录取3/8、0/8、4/8。每方法另1个预注册初态无效条件。类别分别锁参，不称统一策略
  或VMC全面优势。追加采集共同8训练fixture录取5/8、0/8、5/8，失败参与指标汇总。
- 新collection独立审计26/26通过，全55s/550000子步，动作重放最大5.55e-17；9重复对
  57NPZ/612数组完全相同、不增样本。严格train-only锁参VMC清单9唯一（厚角4/短撞4/持续1），
  205排除/1隔离：隔离因部分配对缺模型绑定且原本接触失败，不是证明模型矛盾；不回写追认。
  validation全排除，无新ESN。每类1000合格、持续推碰可靠teacher和正式综合泛化未完成。
- 新collection审计入口/测试、shared validation helper显式phase/split绑定、完整验证及
  十小时报告；README、联合进度、周报、三类记录同步。65相关测试通过、diff check通过。
  原冻结v10源207项hash保持一致，环境/gate/actor/执行器限制未改，全部为开发dt=1e-4。
- 2120文件最终证据已逐项核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_final/evidence/`，
  含`tools/`审计代码、`outputs/teacher_bank_v10_terminal_review_20260930_1349/`完整metadata、
  `outputs/teacher_bank_v10_final_comparison_20260930_1350/`及raw/duplicate/strict manifest。
  终态review SHA=`6414365111679e1712ed169bc83c3022c7b8b6cf68b56fd7f27a4517b7b0deea`；
  manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`。
  逐条raw及动态源码仍在相邻`teacher_bank_three_domains_20260930_v10/`，215份凭据完整。
  归档后的文档地址补充以本提交为准，不冒称已在较早快照中。运行中仿真0，teacher-10已暂停。
- 汇报入口：[十小时结果](code/mujoco_6d_vmc_benchmark/docs/TEACHER_BANK_TEN_HOUR_REPORT_20260930.md)。
  限时工作已完成，数据数量和研究目标未完成；不能以少量合格轨迹宣称泛化或真实部署安全。

## 2026-09-30 — 严格训练标签出口、初态拒绝诊断与不改场景接续

- 12:21及12:49 UTC核对并读取main=`d39aed3f4800223e1aa1584f1dbcc9d45c13e13f`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，无上游新变化，未合并baseline。
- 新训练标签出口绑定原train manifest、锁参、源、实际MJB/NPZ/hash和服务器凭据；
  历史validation标签即使true也拒绝。1144快照仅6个唯一训练fixture（厚角2/短撞3/持续1），
  158排除、0隔离。重复不增样本，矛盾结果/模型隔离；未来runner标签增加train条件，
  冻结v10保留。旧collector/status已另筛train，没有证据表明实际训练数据混用。
- 12:27原作业在21完整validation后因棍推0001初态交叉最大60.09884mm退出；
  独立源码/堆栈/空曝光核查表明动态前拒绝，不能说控制器运动失败。三方法该场景均原样
  保留，无替换。新独立continuation复用全部已完成数据、原冻结attempt与截止，未知异常停机。
  v1资源检查未派发即失败（cpu.max未委派）；v2记录quota_enforced=false并强制单sim/1线程/
  MemoryMax3GiB/Swap0，12:46:27启动，最后验证运行中。此前CPUQuota配置请求不等于实际生效。
- 新增去重原始数组对比、严格标签出口、验证图、接续工具与初态诊断；独立验证审计支持
  无效初态单列null指标。五组相关70测试通过；未修改gate/环境/参数、未做新ESN或正式dt验证。
- 已逐文件核验共享至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1209/evidence/`厚角raw审计与source发布凭据；
  `_1237/evidence/`1791文件（完整名称前缀同上teacher_bank_review_checkpoint_20260930）；
  `_1242/evidence/`45文件初态核查/v1协议；`_1245/evidence/`41文件v2协议/源和首次启动失败。
  v2 driver SHA=`9215b66fefbd7a91082ddbf7c205c777122a59777f5827502d0042a06ed93077`。
  运行中state及本次补充文档未冒称已在此前快照中。原截止13:48:16 UTC不延长，继续验证/采集。

## 2026-09-30 — 162搜索锁参、首个人推独立通过与完整决策审计

- 11:52 UTC重新fetch并读main=`0a1e7972750114d2e0e1f5c1626004e1ed449d7a`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，上游无新增变化，未合并baseline。
- 11:42搜索162/162完成，27录取/135未录取；九组候选/排名、源与配对模型独立核对通过。
  bank SHA=`1cafd43556f754df0595027c6aa1a358520038bbd5a3f742b9ef3b2a2f287945`。
  锁定参数训练录取厚角VMC/导纳/阻抗2/3、0/3、2/3；短撞3/3、1/3、2/3；持续1/3、0/3、0/3。
  task/strict与曝光/录取分开，持续阻抗task/strict仍2/3；不称VMC三指标全面优势。
  27预注册验证运行，collection/新ESN未开始，仍只有2/3/1个唯一合格VMC训练fixture。
- 新增定义覆盖工具，3300定义在剔除未消费字段后仍全部唯一、train/val精确重合0，未宣称
  全量动态有效。全部27BO决策用当时训练前缀同实现精确重放，误差0，不当作收敛证明。
  短撞c05退化诊断区分两类任务失败，不调原score。首个人推c05原始550000子步/动作与
  独立连续段重算通过：1.2643s同段14.3532mm；但RMSE/峰力增加且仍碎接触，不称真实安全。
- 新增validation离线审计、human分段与图工具、相关专属报告，10项针对性测试通过。
  全162点图显示所有失败并修正长期图标签含paddle，已视觉核验。README/主记录/进度/周报同步。
- 均已逐项核验到服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1124/evidence/`56文件定义覆盖、短撞诊断及工具；
  `teacher_bank_review_checkpoint_20260930_1138/evidence/`49文件独立人推/图与全部BO审计；
  `teacher_bank_review_checkpoint_20260930_1150/evidence/`1609文件锁定元数据、公平表和162点图。
  锁定review SHA=`a2708301bdf41874c01dca8a31611c6a5fc1a09081fb50e6c41ea6c8afd32169`；
  人推review SHA=`dab55a4eba144668891332ff6c9a4dbd4415ae8a2c21e7cce7e3acb5725ba2a7`。
  归档后文档地址补充以本Git提交为准，不冒称已在旧快照中。稳定v10未重启，10小时任务继续。

## 2026-09-30 — 135回合检查点、完整资产复现更正与公平展示

- 11:10 UTC重新fetch并读取main=`2581451cc9c471b19c67286457bea8d3b8a4b2b7`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`日志。baseline奖励主实验和独立40k诊断均已收尾，
  仍存在无grasp的探索瓶颈；不合并、不混同其综合场景和本次训练域，也不声称算法本质失败。
- v10完整c00–c04共135回合23录取/112失败，c05继续，未重启。短撞VMC c04单参数3/3、
  c05为0/3；不改规则或丢失败。参数未锁定，validation/collection/新ESN未开始。
- 纠正资产清单遗漏FR3：完整133文件而非85；未来prepare校验两树与引用资源。原冻结
  plan/source/execution保留。本机真实冻结初始化零积分9/9逐字节复现；XML-only0/9因质量
  默认和运行时mask等差异失败。ARM首个source模型22数组有差异，动态补充采集阻断。
  新资产审计/静态复现工具与报告解释范围，不声称跨架构物理等价。
- 新公平展示器分列task/strict/曝光/录取与失败，锁定前不输出策略成绩；三方法指标采用
  同fixture共同完整证据集合，缺失或不匹配一项则共同排除指标聚合但保留任务统计与明细。
  最终11测试通过；资产6/选择6/Spark driver8通过。Spark采集driver仅准备，未启动态作业。
- 已逐文件核验服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_runtime_inputs_complete_20260930/menagerie/`完整133资产，manifest SHA
  `56b0e9d07c2b0e5636f38fb228dbd077980d2ea14c2ea26bc8987be11a304523`；
  `teacher_bank_review_checkpoint_20260930_1104/evidence/`含112文件，本机静态成功和XML失败
  证据、135状态及归档时工具版本；`teacher_bank_spark_static_source_20260930_v1/`为ARM阻断证据。
  归档后的展示器修正及本段文档以本次Git提交为准，未虚称已在1104快照中。
  10小时窗口继续至13:48:16 UTC；3300定义不等于示范，未达到每类1000条。

## 2026-09-30 — 短撞VMC同参数3/3与108回合公平检查点

- 09:42 UTC核对main=`e1d815c390d1221ee0bf80293e2b8179d2e1d3f8`，baseline已前进至
  `e47da59ebb665fb20764131bd56c7b639805f326`，已读新日志。其100k RL主实验已完成但任务失败，
  发现训练覆盖问题后正做独立补充诊断；不把该局限解释为算法本质，不混入本轮特化训练比较，
  未合并baseline或操作其Spark服务。
- 09:40 v10完整c00–c03共108条，17录取/91失败，全部逐条有核验归档凭据；c04运行。
  VMC短撞c03同一参数3/3，初始c00为2/3。六条配对550000子步的三指标独立重算、冻结
  VMC/filter/状态重放与source/参数/model/hash通过；球形RMSE64.667→37.662mm、峰矩
  47.935→45.004Nm，但峰力1793→2221N、穿透0.11744→0.18863mm。穿透仅元数据核验，
  不冒称独立物理重算、全面安全提升或泛化。新增短撞审计工具和报告，更新专题/进度/周报。
- 新终态收尾工具保存原始JSON快照、独立重建选参和锁定、核对后续参数一致性并指出截止
  汇总归档缺口；11项针对性测试通过，live验收正常。它不重新核验所有原始轨迹/远端receipt。
  原稳定仿真未重启，仍固定六候选；持续推碰三方法0/12，validation/collection/新ESN未开始。
- 以下均已逐文件核验至服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0913/evidence/`含964文件（短撞审计/六份重放、终态
  工具与live验收/JSON快照）；review SHA=`d135e2f4336583528e66be27e03b0e47b66201355fbc5d03b21212c7a1659c50`。
  `teacher_bank_review_checkpoint_20260930_0943/evidence/`含42文件（108回合status/公平图/报告），
  PNG已视觉核验，SHA=`fb7df489d653adfad53c1a2245d5eca8ef7b2aba7019c3c035ec92148d3f9f13`。
  10小时任务继续至原截止，不改gate、环境或执行器，不把3300定义当作已采满示范。

## 2026-09-30 — 初始81回合完成与首个BO决策复核

- 08:57 UTC再次核对main=`b1e14de2dade36eed6cc8d9ce448cd8b4a1565ad`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及日志，无新上游变化；未合并baseline。
- 08:40检查点的初始81回合10录取/71失败，VMC唯一合格fixture厚角2/短撞3/持续推碰0。
  不能把跨参数样本拼成单控制器成功率。实际BO已开始，首个VMC厚角c03录取1/3，低于c01
  的2/3；不称BO已改善。参数未锁定，validation/collection/新ESN未开始，固定预算继续。
- 新增首次BO只读审计及报告：前三候选训练证据独立汇总与history一致；读取九份真实MJB
  哈希，并核对peer audit记录的同模型hash，未冒称重读peer全部模型。冻结源与plan绑定；
  相同优化器实现、seed20260933重放差0。首次是可行性LCB，离散代理不是连续物理超限。
- 初始81条公平三指标图含所有失败，排除另计尚不完整BO尝试，PNG视觉核验通过。
  审计/图/status等44文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/`。
  review SHA=`979ea114c384ba23ced024f37601a35221ed3c27da9f9832ba97d6f14a6dc197`；
  PNG SHA=`31f933a44a09a1fea4eb0189130cc8bfd1ee29191219af9195efc6de8e0a8536`。
  更新三类记录/联合进度/周报。v10未重启，冻结测试、gate和执行器未改；十小时任务继续。

## 2026-09-30 — 54回合检查点与可复算的公平三指标图

- 07:18 UTC核对main=`24c5bac6f26bae935d2367b952ebe0f97bb6fc5b`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，未出现上游变化。稳定v10服务未重启。
- 07:35 UTC前两个初始候选54回合完成：8录取/46失败，全部已核验归档；第三组c02运行。
  VMC合格唯一fixture为厚角2/短撞3/持续推碰0，但短撞3条来自不同候选，不能拼成单策略3/3。
  银行未锁定，BO/独立验证/collection/新ESN尚未完成，截止与预算不变。
- 新增`plot_teacher_bank_search_20260930.py`和测试：只画共同完整候选前缀，核对每条audit SHA、
  fixture/MJB、方法/录取与anchor集合，保留所有失败，partial另计。stage-waypoint RMSE与
  峰矩/峰速分列展示，不当平滑全局路径误差，不挑最佳点，不冒称重新复算物理轨迹。
  5项证据/搬移/不覆盖校验通过；首轮27点PNG视觉检查通过。可选campaign-root映射服务器
  读取根，原执行路径保留，v3旧图不重写。联合进度/周报/主报告同步更新。
- 以下均已逐文件核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0717/evidence/`含42文件（首轮PNG/PDF/点JSON/来源status/绘图源）；
  `teacher_bank_review_checkpoint_20260930_0722/evidence/`含36文件（支持服务器映射的新版源码/测试）；
  `teacher_bank_review_checkpoint_20260930_0736/evidence/`含36文件（54回合配对状态）。
  PNG SHA=`bf088ec34ac28340a6c19535654dc1d4f4d80885c63926e22643f2e1c9072824`，完整点JSON的
  SHA=`507cae91f03b65b2335c0c4fde6b08d09295dd46e1b1a1a1816f4f919b514c8e`。未改冻结源码或gate。

## 2026-09-30 — 完整首轮27回合及人手子步独立重建

- 06:26 UTC核对main=`f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，均无新上游变更。v10相同服务稳定运行，未重启。
- 06:32 UTC第一轮c00三类×三方法×三anchor共27条全部完成，5录取/22失败并逐条归档；
  持续推碰三方法均0/3。status确认三个类别共同完整候选前缀[0]、模型hash与历史一致。
  进入c01；固定6候选搜索未完成、参数未锁定，collection=0、新ESN未启动。
- 新增`teacher_bank_person_anchor_review_20260930.py`及专题报告，原hash全匹配；每条550000
  物理子步独立重建schema2连续段，差≤1.22e-13。VMC1.2516s/9.09595mm，尚差0.90405mm；
  导纳宏观约27mm不能替代连续段要求；阻抗连宏观也不足1cm。力阈值间断不能当几何脱离。
  保留所有失败，不改gate/冻结环境或源。同步联合进度、周报和三类主报告。
- 新脚本/JSON/完整配对汇总38文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
  review SHA=`2f94c7999c3732582e38b69e005c75e257dda84f510b1f190842ac8e145c7835`。
- f3b42f5完整源码2623文件已核验发布到同一服务器
  `/home/arm1/sii_shared/SII_compliance/source/f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985/`；
  tar SHA=`274e159481c6f9545ce705b0bcfee90455f0c8caf7433aa7b8357d4a0f931b11`。10小时任务仍继续。

## 2026-09-30 — 首两条VMC合格搜索轨迹复核，完整保留接触峰力

- 06:16 UTC核对main=`5ded01a21ed07f57c28786c616507ade46974289`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及两分支日志，未合并baseline；Spark四个新worker运行，
  旧四个进程为T暂停态。本机v10稳定，未重启或新增仿真。
- 06:18 UTC v10完成21条搜索/5条录取/16条失败，另1条运行。共同c00配对：厚角VMC/导纳/阻抗
  0/3、0/3、2/3；短撞2/3、0/3、1/3。VMC持续推碰0/3，其余方法仍在运行；不提前作配对结论。
- 新增`teacher_bank_search_success_audit_20260930.py`及专题报告：VMC短撞337/671原hash与独立
  子步指标重算通过，冻结runner动作/状态重放通过。它们是初始参数搜索样本，不是BO改善，
  不代表独立验证。正式collection=0、参数银行未锁定，各类1000有效示范/新ESN未完成。
- VMC两条合格短撞接触峰力约1368/1350 N，阻抗合格短撞约2077 N；保留冲击风险局限，
  不用电机峰矩合规冒充低碰撞力/真实部署安全。未改变gate、模型或评分。
- status工具新增已完成rollout元数据哈希核验、接触载荷及原失败字段，不冒充独立物理复算。
  19项status测试通过；联合进度、周报及三类记录同步更新。
- 冻结源码输入审计：反馈控制器无直接外部真值字段，但共享task executive使用真实支撑/物块速度
  辅助松爪，并间接改变名义参考。专题文档明确该边界，不将当前系统称为端到端纯本体真实部署；
  本轮不修改共同协议或停止稳定作业。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`下：
  `teacher_bank_review_checkpoint_20260930_0603/evidence/`（40文件，首次VMC复核源码/JSON/报告）；
  `teacher_bank_review_checkpoint_20260930_0621/evidence/`（38文件，06:18状态及status源码/测试）。
  原始轨迹继续逐条归档到`teacher_bank_three_domains_20260930_v10/`。10小时任务继续，截止不变。

## 2026-09-30 — 首个公平配对与pilot失败归因，v10继续运行

- 05:36 UTC核对main=`7423d5ef94df05470ba14188a983f92fc51846b1`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`，已读日志，未合并baseline。
- 05:49 UTC，v10厚桌角c00完成三个方法各3个anchor、同模型hash配对，录取VMC0/3、导纳0/3、
  阻抗2/3。统计含失败，不称泛化；参数银行仍暂定，作业继续短撞类别，本机单环境/1线程/3GiB。
  VMC合格新教师仍0，全部搜索、独立验证、各类1000有效轨迹及ESN未完成。
- 新增`tools/teacher_bank_pilot_failure_causes_20260930.py`及同名专题报告（研究目录内）：
  九条v8原始文件hash全部匹配，子步三指标独立重算差≤6.94e-18m，力矩/速度差0。
  球撞VMC主要晚期释放后滑落；导纳放置漂移、阻抗收敛超时。145mm误差跳变主要来自
  waypoint切换，不能当作碰撞末端位移。人推VMC/导纳约27mm宏观位移横跨微接触间断，
  不能说完全不会让位，也不能追认连续接触/schema2成功。原gate/源/失败记录未改。
- 归因JSON SHA=`c6d3469bea9113edf7416697d31950921b7d2fbf44da3f5016c2c74d6d020986`。
  41个新证据文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`；
  内含归因脚本/报告/JSON、当前status源码和v10_0549预算汇总。新增review归档的显式include选项。
- 已提交源码7423d5e的2618文件经SHA/大小/权限及完整文件集合核对，共享到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7423d5ef94df05470ba14188a983f92fc51846b1/`。
  tar SHA=`47399ebcc9e6463d81f001a3112642ff362e45e9ee46f046efff37229b8cf13e`；初次tar compare
  仅因uid/gid不同而退出，之后独立核验内容通过才发布。新增源码归档核验工具，不改源内容。
- 更新联合进度、周报和三类专题。未重启稳定作业、未新增仿真槽位，10小时原截止不变。

## 2026-09-30 — 三类pilot审计完成，v10公平搜索启动（10小时任务继续）

- 05:19 UTC接续核对main=`8dec129deecf2b769e765c5d91a54a64140a22a7`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`并读日志。baseline的SimbaV2
  campaign_03在Spark四路训练，本任务本机单环境/1线程/3GiB，不修改其分支或作业。
- 已完成v6六条主动pilot、v8九条三类别pilot及服务器归档；v8仅阻抗厚桌角fixture0通过，
  RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s。接触18840段、其中一个5ms段以0.231mm上抬
  通过已注册曝光，不称平顺明显蹭过。VMC同场任务成功但上抬0.0866mm不足0.1mm，保留拒绝。
  当前合格新VMC轨迹为0，不把3300配置定义当成功示范。未启动新ESN。
- 新训练厚边缘移至掌翼上方，避开下降手掌；18项跨类初态预检通过。只改新增训练域，
  冻结综合测试/gate/actor/执行器不变。几何失败、旧corner曝光不足与v5失败全部保留。
- 修复人手曝光方向与施推时窗，schema2保存每个物理子步；旧schema1不追认为新筛选通过。
  修复搜索anchor的物体形状覆盖（0/337/671），独立验证固定0/1/11。候选成功anchor数量
  优先，之后比较失败标签代理及原评分；不把该离散代理称作连续物理超限。
- 每次dispatch核验实际Panda资产85文件，模型hash跨方法/候选/阶段一致；新增曝光-物理
  时间绑定、观察q/dq-前后状态绑定。九条旧pilot关联只读复核全通过，原audit未改写。
  搜索开始前73项测试通过。数值异常停机待分类，不吞异常或伪造BO指标。
- v8于05:23:21 UTC按预定阶段锁在pilot后停止，末尾BlockingIOError是计划内边界停止，
  不算物理失败。v9只准备未运行。v10于05:29:05 UTC实际启动固定6候选×3anchor搜索，
  首回合完成并归档，未通过接触筛选。服务`teacher-bank-search-v10-20260930.service`。
  计算窗口仍截止13:48:16 UTC；heartbeat保留到14:28只做最后归档审计，不扩展计算授权。
- 已核验服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`。
  其下`teacher_bank_three_domains_20260930_v10/`含源码210文件、metadata2文件、输入3文件，
  运行记录逐条发布。`teacher_bank_runtime_inputs_20260930/menagerie/`含实际Panda资产85文件；
  `teacher_bank_reaudit_v5_20260930/impedance/`为旧raw复审及源码；
  `teacher_bank_review_checkpoint_20260930_0527/evidence/`为34份新几何/pilot报告/计划停止证据。
  所有路径均已SHA256核验，未覆盖历史产物。
- 已更新README、联合进度、周报、三类专题及schema2/手掌阻塞诊断；新增独立审计测试和
  review归档工具。未完成：搜索、锁定参数验证、各类1000条合格teacher、ESN与正式泛化。
  `teacher_bank.json`搜索中只是暂定选择；截止partial block须单列，公平比较用共同完整预算。
- 搜索启动后另扩展只读status，独立核验decision/anchors/执行记录和模型hash、reuse/recovery、
  共同完整候选前缀、截止partial，以及完整搜索后才locked。该工具13项测试通过；没有改
  v10冻结源码或运行过程。实时PID核验需宿主上下文，沙箱生成报告可能看不到systemd进程。

## 2026-09-30 — 启动三类 teacher 数据与经典 baseline 的 10 小时任务

- 开工核对 main=`38caf3152282df4963435bb65c11c93a1e4fffa5`、
  baseline=`59342005b11b5892b18301fd9b52c6b07ad87f45`；开工时其日志仅有初始化，
  其工作区 `/home/arm1/SII_compliance_baseline` 不由本任务修改。
  04:15 UTC再次核对baseline已到`5bc21d8d19eaf60691f561f0ad9dd4409749e667`，已读新日志：
  SimbaV2奖励配对训练/GPU验证与布局合法性修正；不合并其分支，不占用Spark仿真槽位。
- 用户新增授权：三类各至少1000训练环境，VMC同时作teacher/model-based baseline，导纳/阻抗
  同场景同预算调参，多agent协作，持续10小时。窗口至2026-09-30 13:48:16 UTC。
- 新增 `tools/teacher_bank_{design,rollout,campaign,classical,exposure}_20260930.py`、相关测试和
  `docs/TEACHER_BANK_THREE_DOMAINS_20260930.md`、独立场景审查报告（路径相对研究目录）。
  生成3000训练+300验证配置，支持冻结源码、约束BO、原始/过滤动作、物理子步与接触曝光审计。
- 已完成34项新测试；动态pilot发现新训练桌角连接件初态与机器人相交，正确拒绝并归档，
  修正为绕手爪连接后42个初态预检通过。v4九条动态pilot已于04:16 UTC启动。
  v4完成一个有效物理回合但没有真实上抬碰face，不可入库；导纳adapter在仿真前失败已修。
  v5于04:30 UTC启动，VMC/导纳前两条均在align被训练face挡住，负结果保留，继续其他配对。
  尚无合格新teacher轨迹；未启动ESN、不改冻结综合测试或保留集。
- 已核验服务器源码/失败路径：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
  v4源码206文件/metadata2文件也已核验归档到同一父目录下
  `teacher_bank_three_domains_20260930_v4/`，动态轨迹完成后逐条归档。
  不覆盖失败记录。详细实时状态和限制见上述专题文档。
- 新增进程身份恢复：仅确认旧PID已退出才另开retry目录，旧文件逐字节保留，基础设施失败
  不进入BO；新增只读状态汇总器。53项测试通过。公共评分移除对力矩阻抗不公平的action7
  平滑罚，补配对MJB一致性和阻抗命令→实际物理力矩审计。
- v5源码209文件、metadata2文件已核验归档到同父目录`teacher_bank_three_domains_20260930_v5/`；
  几何诊断/初态成功及失败的7份JSON已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_archive_20260930/evidence/`。
- 重要纠正：旧corner task/strict成功不是“上抬碰face成功”证据。新曝光审计把桌面支撑与
  真实上抬碰边分开。十小时按98.3s首回合吞吐无法跑满9000次配对采集；搜索前预注册
  6候选×3anchors/方法/类、每类3个独立验证、之后剩余时间配对采集，3000有效数据目标未完成。
- v5阻抗完整仿真后审计触发3GiB限制，原因是NPZ逐行索引重复解压且保留整列view；已修为
  一次读列＋生成器，54项测试通过。旧raw独立复审4.39s成功，13750servo/550000子步实际力矩
  映射误差0；原failed execution不改写。该复审仅本地、待归档。
  v5现已停止；v6冻结源码的主动短撞/持续推碰六条pilot已启动，仍单环境/1线程/3GiB。

## 2026-09-30 — 协作 skill：双分支开工检查、本地计算与服务器归档

- 新增 `skills/sii-research-sync/SKILL.md` 与 `agents/openai.yaml`，安装至
  `/home/airpig/.codex/skills/sii-research-sync/`，允许自动选择。开工先 fetch/读取远端
  main、baseline 的 `UPDATE_LOG.md`；收工重新读取 `AGENTS.md`，记录并发布本轮进展。
  同步更新根目录 AGENTS 与 README，让未自动加载 skill 的后续 agent 也有入口。
- 本轮远端检查（2026-09-30，Asia/Shanghai）：main=`f098678ad1532f1b87c7e2ac803faa301c4c65ca`；截至本轮查询，
  远端没有 baseline 分支，因此无 baseline 更新日志可读。没有擅自创建分支或合并代码。
- 新默认偏好：尽量本地计算，服务器共享持久文件。共享目录为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`，源码按 commit 隔离，
  实验按 branch/run-id 隔离；先同步并校验，再把服务器绝对路径写入更新文档。
  本地缓存和实际执行来源保留，不改历史 execution.json，不覆盖别的 agent 或 runtime。
- 本轮归档的是已发布研究源码，服务器代码位置：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f098678ad1532f1b87c7e2ac803faa301c4c65ca/code/mujoco_6d_vmc_benchmark/`。
  此路径对应本轮开始时的研究代码；本轮 skill/文档更改以 GitHub 新提交为准。
  未全量迁移历史 outputs、原始大轨迹或 checkpoint，不声称它们已在新共享目录。
- 验证：仓库版与安装版 skill 均通过 skill-creator 的 quick_validate，目录内容一致；
  使用现有 `.venv-canonical-rl` 中的 PyYAML 完成校验，未安装新依赖。文档差异检查通过。
  本轮没有修改算法、环境或启动仿真。
- 已完成：skill 编写安装、双分支状态检查、共享目录创建与研究源码归档。2026-09-30
  03:10:53 UTC 逐文件校验服务器快照：2,592 个文件 SHA256 全部一致，无缺失或额外文件。
  本轮没有运行中的新实验；历史大文件仍在原位置，后续按实际任务逐批归档。

## 2026-09-30 — 积累成果同步与每轮自动提交约定

### 文件更新

- 新增根目录 `AGENTS.md`，落实用户“每次对话结束前 commit、push main、记录更新”的授权。
  新增本日志，README 增加当前状态与入口。此次同步的起点为 `2e37ddc`。
- 纳入 9 月 23 日至今未提交的研究代码、配置、测试、报告与小型证据：统一物理子步指标、
  经典控制器预算实验、canonical48D/action7 及参数动作 RL 对照、ESN 记忆消融、
  VMC＋ESN 联合优化、延迟球撞、综合环境的版本化开发、纯 ESN 与 MLP 比较和动作重放审计。
  各历史实验的冻结配置、失败原因与结论以各自报告为准，不合并为一个“全部成功”的结论。
- 纳入独立 teacher 修正实现 `scripts/vmc_teacher_stable_readout_20260930.py`、
  `tools/teacher_repair_campaign_20260930.py`、`tools/teacher_repair_followup_20260930.py`、
  `tools/audit_teacher_repair_20260930.py`，以及 `docs/TEACHER_REPAIR_20260930.md` 和进度、周报。
  上述路径均相对 `code/mujoco_6d_vmc_benchmark/`。
- 新增 `tools/export_publication_evidence_20260930.py`，导出 teacher 的小型审计 JSON、运行配置、
  源码快照及哈希索引到 `docs/evidence/publication_20260930/`。原始大文件不进入普通 Git：
  `results/` 下 NPZ/MJB、证据目录编译模型，以及原本已忽略的 outputs、视频等仍在原处。
  本次清单覆盖 results 大文件、证据 MJB 和三轮 teacher 输出，不覆盖所有历史 outputs 或服务器。
  小型 docs/evidence NPZ 仍纳入版本管理。没有删除原始数据；需要完整重放时还须取得清单中的本地产物。

### 已有实验结果（与本次发布检查分开）

- teacher 两轮完成 12 条有效 55 s、dt=1e-4 开发回合；动作、内部状态及过滤链独立重放误差为 0，
  每条 550,000 个物理子步复算指标。此前误用 MuJoCo 3.14 的四条诊断保留，不混入有效结果；
  有效实验固定 MuJoCo 3.11，并核对综合模型 SHA256。
- 当前候选 `velocity025_stiff2`：corner-placement 的 task/strict 均通过；综合单柱 v4
  task=true、strict=false（缺少要求的柱接触）。综合 waypoint RMSE 37.406 mm，峰值实际力矩
  48.127 Nm，峰值末端速度 0.070574 m/s，外部穿透 0.144922 mm。
  相对同模型原版，放置阶段动作差分 RMS 0.306187→0.042031，降低约 86.3%。
- 尚未完成：特化场景全协议与跨条件验证、综合 strict、正式 dt=5e-5，以及稳定 teacher 数据上的
  新纯 ESN 蒸馏。此次发布没有新训练，没有改冻结环境或 gate。
- README 中 9/29 的 delayed-ball 正式通过结果和早期 cup/pillar 综合失败属于不同版本；
  不可与当前单柱 teacher 开发回合互相替代，也不能据此声称 ESN 已全面优于 baseline。

### 发布验证

发布内容扫描：814 个 Python 文件（包含归档源码副本）语法通过，1,216 个 JSON 可解析；
已检查的私钥、GitHub token、AWS key 和含密码 URL 模式无命中。相关既有测试
`test_esn_load_gated_20260929`、`test_esn_impact_response_20260929`、
`test_office_canonical_audit_20260927`、`test_physics_substep_metrics_20260923`
共 9 项通过。发布集合约 60 MB，最大单文件约 7.6 MB，无超大单文件。
产物索引含 1,642 项、17,382,062,868 字节（含保留在本地的原始数据和已复制的小型证据）。
本次不重复运行已经完成的长仿真实验。
发布整理同时移除了八份历史 Markdown 的行尾空白或多余末尾空行，不修改实验内容。
`git diff --cached --check` 通过；推送前 fetch 确认远端 main 与此次同步起点一致。

## 2026-10-07 — ESN v2 anchored readout 真实降矩/泛化审计

- 仅修改纯 ESN readout；office-v6 场景、原 task/strict gate、48D/action7 本体输入、执行器约束和 sealed 条件保持不变。v2 候选为 `ridge=0.1, smooth_weight=0.01, action_weight=0.0001, parent_trust=100`，checkpoint SHA256 `da281fbe03e122f0d36bb6e5e65183f9fd480b2f5acfd6a939404888075f5d59`。
- 在正式 `dt=5e-5`、单线程、`MemoryMax=3GiB` worker 上，development_000/001/004 通过 task/strict，development_002/003 失败，分母为 `3/5`。通过回合 RMSE `28.338–31.076 mm`、峰值力矩 `49.663–49.909 Nm`，略低于父 ESN 锚点 `49.981 Nm`；失败回合和基础设施失败均保留。
- development_002 的父 ESN 配对在 `24.32 s` 因 `2.602 mm` 穿透中止，而 v2 候选完整跑完 55 s、穿透 `0.174 mm` 但仍未放置成功；development_003 v2 穿透 `0.139 mm`、峰矩 `38.311 Nm` 但 task/strict 失败。结论是有限的低峰矩/低穿透鲁棒性信号，不能称跨条件泛化或任务优势。
- 原始审计、trace/chain/metrics/source 哈希与失败目录归档在
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/`；本地摘要在 `code/mujoco_6d_vmc_benchmark/outputs/esn_torque_v2_corrected_20261007/`。
- 本轮提交 `95f437f507911ed035a9503ba183c41589415951` 的源码快照已归档到
  `arm1:/home/arm1/sii_shared/SII_compliance/source/95f437f507911ed035a9503ba183c41589415951/source.tar.gz`，SHA256 `cf6fd24b89051de457ebe0035e2d6ad40287e5b02cf9b062d760bdbdd4bea388`。
- 更新文档：`docs/ESN_TORQUE_GENERALIZATION_20261007.md`、`docs/ESN_STAGE_REPORT_20261007.md`、`docs/ESN_VMC_JOINT_PROGRESS_20260927.md`、`docs/BASELINE_WEEKLY_REPORT_20260923.md`。统一 `/24` 主表未改，sealed 条件未读取。

## 2026-10-13 — 绘制现有RL训练reward曲线

- 按用户要求读取本机 `code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/recovery_20261011_v1` 的既有 `training.jsonl`，绘制直接输出动作的两种 reward 标准，以及参数输出的 admittance/impedance/VMC/历史熵附组。
- 图中每点为一个 episode 的 `final_reward` 求和，横轴为该回合最后记录的训练步；同时保留原始点线和 15 回合移动平均。未重训、未仿真、未修改既有运行。
- 产物在 `code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013/`，含 PNG、PDF、说明；脚本为 `code/mujoco_6d_vmc_benchmark/tools/plot_reward_training_curves_20261013.py`。部分历史日志在 97,625 或 108,458 步封存，图中保留实际终点，不补齐。
- 这是训练目标回报曲线，不等同任务成功或安全收敛；远端 fetch 因网络不可达，本轮按本地缓存分支状态完成。

## 2026-10-13 — 重画RL reward收敛过程图

- 根据用户反馈，弃用只按回合数量且从中途开始的旧主图，改用真实训练步拼接后的完整 episode return；上图保留原始回报，下图为10回合移动平均趋势。
- 拼接 segment/55k extension/110k continuation/recovery 日志并按训练步去重，覆盖直接动作两种 reward 标准和参数输出 admittance、impedance、VMC、历史熵附组。
- 主图：`code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013/reward_convergence_episode_return.png`及同名PDF；脚本：`tools/plot_reward_convergence_episode_return_20261013.py`。transition-level辅助图仍保留。
- 观察：各方法大多在自身 reward 尺度上较早进入平台，直接动作两种标准的水平明显不同；这说明目标回报稳定化，但不等同任务成功率或安全收敛。

## 2026-10-13 — 重画RL reward收敛过程图

- 根据用户反馈，弃用只按回合数量且从中途开始的旧主图，改用真实训练步拼接后的完整 episode return；上图保留原始回报，下图为10回合移动平均趋势。
- 拼接 segment/55k extension/110k continuation/recovery 日志并按训练步去重，覆盖直接动作两种 reward 标准和参数输出 admittance、impedance、VMC、历史熵附组。
- 主图：`code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013/reward_convergence_episode_return.png`及同名PDF；脚本：`tools/plot_reward_convergence_episode_return_20261013.py`。transition-level辅助图仍保留。
- 观察：各方法大多在自身 reward 尺度上较早进入平台，直接动作两种标准的水平明显不同；这说明目标回报稳定化，但不等同任务成功率或安全收敛。

## 2026-10-14 — 夜间补充RL actor/critic loss收敛图

- 自动任务按已授权范围完成只读分析；未重训、未启动仿真、未影响在途作业。
- 从近期 `baseline_local_rl_20261009` 的 `optimizer.jsonl` 读取实际 `actor/loss`、`critic/loss`、`actor/entropy`、`temperature/value`；按真实训练步拼接 segment/extension/continuation/recovery，重复同一步优化记录先取均值，再按1000步分箱，粗线为约5000步移动平均。
- 主图：`code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013/loss_convergence_actor_critic.png/pdf`；辅助图：`loss_convergence_auxiliary.png/pdf`；说明：`LOSS_README.md`；脚本：`tools/plot_rl_loss_convergence_20261013.py`。
- 图上可见 actor/critic loss 在约5万–8万步附近出现明显下降后进入平台，随后部分方法缓慢回升；这只能说明优化器诊断量的阶段性稳定，不能单独证明策略任务成功或严格收敛。旧PPO/SAC pilot的monitor/TensorBoard已核对但因协议不同单独保留，未混图。

## 2026-10-14 — 夜间补充RL actor/critic loss收敛图

- 自动任务按已授权范围完成只读分析；未重训、未启动仿真、未影响在途作业。
- 从近期 `baseline_local_rl_20261009` 的 `optimizer.jsonl` 读取实际 `actor/loss`、`critic/loss`、`actor/entropy`、`temperature/value`；按真实训练步拼接 segment/extension/continuation/recovery，重复同一步优化记录先取均值，再按1000步分箱，粗线为约5000步移动平均。
- 主图：`code/mujoco_6d_vmc_benchmark/outputs/reward_training_curves_20261013/loss_convergence_actor_critic.png/pdf`；辅助图：`loss_convergence_auxiliary.png/pdf`；说明：`LOSS_README.md`；脚本：`tools/plot_rl_loss_convergence_20261013.py`。
- 图上可见 actor/critic loss 在约5万–8万步附近出现明显下降后进入平台，随后部分方法缓慢回升；这只能说明优化器诊断量的阶段性稳定，不能单独证明策略任务成功或严格收敛。旧PPO/SAC pilot的monitor/TensorBoard已核对但因协议不同单独保留，未混图。
