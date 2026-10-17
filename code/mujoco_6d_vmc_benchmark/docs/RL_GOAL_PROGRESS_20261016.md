# 持续Goal：四类RL训练与收敛修复

## 2026-10-17 11:24 CST — mixed continuation 已启动

- stage03 direct 在 `29,512` steps、24 个完整回合处因磁盘保留线安全停止；旧目录和全部失败
  收据保留。清理约 13.85 GiB 可再生成 pip 下载缓存后，磁盘可用空间约 62.6 GiB。
- 新建唯一 `outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1`，使用
  `tools/prepare_mixed_goal_stage_20261017.py` 记录逐族 lineage：direct 继承 stage03
  `checkpoint_0029512`，impedance/admittance/VMC 继承 stage02 各自 `checkpoint_0023375`；
  每族新增 11,000 interactions，CPU1/单线程/3 GiB/禁 swap/UTD=1。
- 四份 n25 checkpoint/replay preflight 均通过；coordinator
  `sii-rl-goal-stage-86934caed9a9.service` 已启动。direct worker
  `sii-rl-goal-d5c23cdd51d6` 已在安全预算边界完成 `40,512 steps / 35,513 updates`、32 个完整回合；
  最后四回合 return 为 `-22.103423267`, `-21.790978936`, `-21.714844084`, `-22.137743486`，
  均 physical_valid=true、Task/Strict=false/false，direct 没有收敛或成功证据。episode 24
  (`repair_train_020`) return `-38.757591452`、`physical_valid=false`、Task/Strict=false/false；
  episode 25 (`repair_train_025`) return `-21.788506946`、`physical_valid=true`、Task/Strict=false/false；
  episode 26 (`repair_train_003`) return `-27.024080870`、`physical_valid=false`、Task/Strict=false/false；
  episode 27 (`repair_train_026`) return `-22.112554771`、`physical_valid=true`、Task/Strict=false/false；
  episode 28 (`repair_train_016`) return `-22.103423267`、`physical_valid=true`、Task/Strict=false/false；
  episode 29 (`repair_train_005`) return `-21.790978936`、`physical_valid=true`、Task/Strict=false/false；
  episode 30 (`repair_train_004`) return `-21.714844084`、`physical_valid=true`、Task/Strict=false/false；
  episode 31 (`repair_train_009`) return `-22.137743486`、`physical_valid=true`、Task/Strict=false/false。
  direct 峰值达到 3.00 GiB hard limit，memory.max events=1542，但 OOM/oom_kill/swap=0。
  coordinator 已完成 impedance worker `sii-rl-goal-96859867545` 的 34,375 steps / 29,376 updates、
  25 个完整回合；最后四回合 return 为 `-24.782192822`, `-24.947542116`, `-25.430825464`,
  `-25.073407371`，均 physical_valid=true、Task/Strict=false/false，impedance 没有收敛或成功证据。
  其峰值约 3.14 GiB，OOM/oom_kill/swap=0。coordinator 已接续 admittance worker
  `sii-rl-goal-bc165dcc6cf0`，已推进至 24,750 steps / 19,751 updates；episode 17
  (`repair_train_011`) return `-25.600694688`、physical_valid=true、Task/Strict=false/false，
  episode 18 在途；其峰值约 2.40 GiB，OOM/max/swap=0。当前没有
  Task/Strict 成功证据。
- 该 mixed stage 不是收敛或最终成功结论。旧 stage03 execution 未覆盖；四族完成后再按统一
  acceptance 和独立物理/动作/filter/hash/RMSE/峰值/穿透审计，Task 与 Strict 同时通过才计成功。

## 2026-10-17 10:15 CST — stage03 CPU continuation 启动

- GPU 继承预检因驱动不可用保留失败收据；已登记显式本机 CUDA→CPU fallback，冻结物理、
  gate、canonical48、公共 filter、执行器限制及 dt=5e-5 不变。
- `rl_goal_selected_20261016_stage03_cpu_v1` 四份 systemd 3 GiB/禁 swap/单线程预检通过：
  direct 继承 21,262 条 raw replay，其余三族各 23,375，n-step=25、terminal window、
  checkpoint hash 与单次更新均通过。协调器已启动并串行推进四族；首个 direct 当前约
  21,500 steps/16,501 updates，第18回合在途，Task/Strict 尚无新成功证据。
- direct 第18回合随后安全结束于 step 22,637，新增 1,375 steps/updates，return
  `-21.855956642`，`physical_valid=true`，Task/Strict `false/false`，无 abort；第19回合
  已由同一协调器接续。该结果是失败收据，不是收敛证据。
- direct 第19回合在 step 24,012 安全结束，return `-33.479317074`，`physical_valid=false`，
  Task/Strict `false/false`；第20回合已接续。该失败收据保留，当前策略仍不稳定。
- direct 第20回合在 step 25,387 安全结束，return `-21.801052248`，`physical_valid=true`，
  Task/Strict `false/false`；第21回合已接续，仍无成功回合。
- direct 第21回合在 step 26,762 安全结束，return `-21.712710806`，`physical_valid=true`，
  Task/Strict `false/false`；第22回合已接续，仍无成功回合。
- direct 第22回合在 step 28,137 安全结束，return `-22.172865867`，`physical_valid=true`，
  Task/Strict `false/false`；第23回合已接续，direct 仍无成功回合。

## 2026-10-17 09:05 CST — occupancy二十四回合，仍在安全推进

本轮开工重新读取 AGENTS、远端分支日志和现有进度。GitHub fetch 受网络限制未能取得更新；本地
remote-tracking 的已核验 main 为 `e38bba9dd0705181182bcb6a8d4e003a286eda7a`，baseline 为
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未把缓存引用冒充本轮远端新状态。唯一活动 worker
仍是 `sii-rl-goal-af59b75d7cc5.service`，coordinator 仍登记 `impedance_occupancy`，没有重复派发。

实时 execution/training/optimizer 交叉核对到约 `34,000` steps、`29,001` updates、24 个完整回合，
第 25 回合随后在途；最近闭合回合 return 为 `-27.082338`、`-26.785106`，Task/Strict 仍为
`0/24`，physical_valid 均为 true，不能称收敛。worker 记录的峰值内存 `2,802,864,128` bytes、
硬限 `3,221,225,472`，memory.max/oom/oom_kill/swap 均为 0；GPU 38°C、空闲显存约 14,406 MiB，
磁盘余 `55,527,899,136` bytes，高于 50 GiB 保留线。

额外只读核验 episode 22 的 `parameter_trace.json`：raw action 五维标准差约 `[.575,.648,.648,.619,.662]`，
applied parameter 也有非零变化，energy scale 全为 1.0；因此当前失败不能归因于 actor 完全不输出或
参数 shield 把动作全部裁成零。`requested_action` 全零是阻抗执行动作字段的接口语义，不能代替 raw-action
replay。冻结 physics/MJB、Task/Strict gate、canonical48、公共 filter、执行器限制及 dt=5e-5 未改。

阶段仍按登记的 44k 安全边界继续；闭合后才归档最后回合、核对 treatment/control 匹配，再登记覆盖
admittance/VMC/direct 的有限阶段。当前不做 acceptance，不把 occupancy reward 平台或早期失败回合写成收敛。

## 2026-10-17 08:46 CST — occupancy二十二回合，继续失败但资源稳定

开工实查/fetch/read main `e38bba9dd0705181182bcb6a8d4e003a286eda7a`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份进度，收工重读AGENTS。
协调器2502213/worker2546313同一PID真实active，无重复派发、无活动配置或冻结source修改。

观察器00:31:41–00:42:41 UTC记录28000→30250步、23001→25251更新、20→22闭合回合，
目标边界归档后退出0；处理组44k预算完成约68.75%。22回合均1375步/55秒、physical_valid，
Task/Strict0/22；20carry/2retreat。新增ep20/21 return −27.168395055/−27.486226574。
全22回合return均值−27.457381962、标准差.522539051；纯学习ep4–21均值−27.463554388、
标准差.540630782；最近8回合均值−27.277365369、标准差.572251558，仍无Task/Strict成功。
这些是同一处理组不同训练条件的窗口，不能仅以reward平台宣称收敛。

末temperature .001102521、critic loss5.174789；worker峰2,802,864,128/max3,221,225,472，
OOM/max/swap0，归档时内存2,289,479,680；磁盘余55,601,889,280 bytes，高于50GiB。
本机GPU/CPU约束和dt5e-5保持，服务器只传输/存储/hash。归档助手7.953秒退出0。

本轮证据BENCH/outputs/rl_goal_stream_window_20261017T0900已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T0900/evidence.tar.gz`
13,203,008 bytes，SHA256 `02433528207c5ab0489b9a207c5bfed978c85a9b730c832fdd8443cae03dce90`。
此前ep16 carry失稳时间线归档仍保留。Goal active，继续处理组至44k；
完成后再做控制/处理匹配、有限后续调整和四族接续，最终acceptance尚未执行。



## 2026-10-17 08:31 CST — occupancy二十回合，首次retreat失稳时间线

开工实查/fetch/read main `10d8ce3fb24262cd56b290d4c004d0ede1cdf62e`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份进度，收工重读AGENTS。
协调器2502213/worker2546313持续active，无重复派发、无活动代码/参数/物理修改。

观察器00:16:45–00:28:15 UTC记录25250→27500步、20251→22501更新、18→20闭合回合，
目标边界归档后退出0；处理组44k预算完成62.5%。20回合均1375步/55秒、physical_valid，
Task/Strict0/20，18carry/2retreat；新增ep18/19 return −26.816303524/−27.118446107。
全20回合return均值−27.470389076、标准差.544026937；纯学习ep4–19均值−27.480584835、
标准差.568374653；最近8回合均值−27.214263405、标准差.593015047。窗口波动和阶段切换
不构成收敛，未比较控制/处理收益，未执行最终acceptance。末temperature .001394340、
critic loss5.198501。worker峰2,802,864,128/max3,221,225,472字节，OOM/max事件/swap0；
磁盘余55,124,811,776字节，高于50GiB；GPU实查41°C/1436MiB。归档助手CPU6/1GiB/swap0，
6.445秒退出0，服务器仅存储/传输/hash。

对ep16首次retreat做原生40ms时间线诊断：物块最高点51.16s、z=.578209m、XY误差99.125mm；
51.44s payload potential从.415322骤降至.263509，51.48s物块降至z=.444607m、XY误差
212.187mm并远离手；52.48s才进入place，53.20s进入release，最终XY误差223.214mm，
release_supported=false、placement_complete=false。故物块在carry阶段已经失稳，retreat阶段
不是成功放置后的误报。原生contact摘要记录carry阶段unexpected edge 40.467s、峰62.29N，
51.24295–51.33170s corner contact峰73.80N，最大穿透.121190mm；这些时间对齐和接触摘要
不能单独证明因果控制原因，未改冻结接触/环境或gate。动作/实际参数和energy_scale=1仍保留。
ep16 reward分解通过：terminal task=-20、payload_occupancy未折扣=-2.160844、
终点potential=.086133、shaping residual5.2e-15，Task/Strict仍明确false。

证据BENCH/outputs/rl_goal_stream_window_20261017T0835（12,321,386 bytes，
SHA256 `966301758715043e9d547740a3605677e6ab7d24ace362450da6798d80be0fe7`）已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T0835/evidence.tar.gz`。
retreat时间线证据也已独立核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-retreat-20261017T0830/evidence.tar.gz`
（2,315,441 bytes，SHA256 `04f88b51e61f50af3c7a3fd80042789e0a3f7a476545c9ea1a1a2d8c4f274180`）。
所有失败/未完成回合保留；Goal active，继续处理组至44k，再做匹配对照并按证据决定四族后续调整。



## 2026-10-17 08:17 CST — 已核验等待：occupancy十八回合及replay容量核对

开工实查/fetch/read main `8eb042664232ad9a0daacd1d4362f73e9c1d62ba`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份进度，
收工重读AGENTS并再次fetch核对分支未前进。上一轮新增动作覆盖诊断，本轮接续同一健康worker，
无研究源码或活动配置修改、无重复派发。协调器2502213/worker2546313真实active。

观察器00:02:34–00:14:04 UTC记录22500→24750步、17501→19751更新、16→18闭合回合，
目标边界归档后退出0，训练继续。execution批次刷新时另读optimizer末行24734/19735，
确认没有把记录间隔误当停滞。18回合均1375步/55秒、physical_valid，Task/Strict0/18；
17carry/1retreat。新增ep16/17 return −27.637977570/−26.699794802。
ep16首次进入retreat但物块最终XY误差223.214239mm、位置z .424996988m，仍任务失败；
阶段推进不能替代物块放置/最终gate，不推断掉落的具体因果。
全18回合return均值−27.526279550、标准差.543209955（含warmup/mixed）。
纯学习ep4–17均值−27.553900552、标准差.568276159；
最近8个ep10–17均值−27.475437173、标准差.652700227、范围[−28.537852285,−26.699794802]。
这些窗口含不同条件和演化中策略，不证明收敛或处理收益。

24750交互/19751更新连续有限，奖励分解、AUDIT/trace、cp24750成员hash与新增原始远端归档通过。
末temperature .001809536、critic loss5.557659。worker峰2,774,876,160/max3,221,225,472字节，
OOM/max事件/swap0；磁盘余55,849,672,704字节，高于50GiB；GPU实查43°C/1436MiB。
归档助手CPU6/1GiB/swap0，6.135秒退出0，本机计算/服务器仅归档保持。

另外只读cp22000的真实replay数组头和runner元数据，前后checkpoint hash一致：
capacity1000000/count22000，48+48观测、5动作及3标量，float32，每条416字节；
填充数组9,152,000字节，满容量原始数组416,000,000字节，余增量406,848,000字节。
这不是进程RSS上界或百万步在3GiB内可运行的证明，仍需逐有限阶段核对实际峰值。
本机CPU6/1GiB助手375ms退出0，无全容量分配、仿真、更新、replay修改或资源限额变更。

证据BENCH/outputs/rl_goal_stream_window_20261017T0820含WINDOW/TRAINING_SCREEN、闭合日志、
REPLAY_CAPACITY及检查脚本。已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T0820/evidence.tar.gz`，
11,454,139字节，SHA256
`67f2b170ec406a95e4b2c764a43f66dc5be3a79e93d2ac02f250593bb8c38ff5`。
按sii-research-sync更新三份进度、提交/push main，保留无关meeting文件。
Goal active，继续处理组44k，双方闭合后做匹配比较及四族接续；控制组0/32，
四方法均未证明收敛，最终acceptance/独立物理与filter重放未执行，全部失败保留。
冻结物理/MJB、最终gate、canonical48、公共filter、执行器限制及dt5e-5保持。



## 2026-10-17 08:02 CST — occupancy半程16回合，补充动作时间连续性诊断

开工实查/fetch/read main `997853bad6b3911cc35f65b05c2c7ba33388596b`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份RL进度；
收工重读AGENTS，发布前再次fetch核对未前进。上一轮是已发布接续修复；本轮核验现有等待并新增
原生训练诊断，没有修改研究源码、活动snapshot、奖励、物理/gate/actor输入/filter/执行器/dt5e-5。

协调器PID2502213/worker2546313真实active。观察器23:48:17–23:59:47 UTC记录
19750→22000交互、14751→17001更新、14→16闭合回合，目标边界归档后退出0；
训练继续，未重复启动。处理组44k预算完成50%，不是收敛或四方法训练完成。
16回合均1375步/55秒、physical_valid、carry，Task/Strict0/16；
新增ep14/15 return −28.537852285/−26.753927031，均无物理abort。
全16回合return均值−27.570953720、标准差.535251168（含warmup/mixed）。
连续22000条交互/17001更新有限，逐回合奖励分解、AUDIT/trace、cp22000成员hash、
新增原始远端归档复核通过。末temperature .002244723、critic loss6.321387。
worker峰2,748,755,968/max3,221,225,472字节，OOM/max事件/swap0；
磁盘余55,948,918,784字节，高于50GiB。GPU实查41°C/1436MiB。

对较晚学习回合ep12/13补充原生25Hz诊断：尾10秒各250采样仍在第20/28路径点，
无采样路径点推进，位置误差中位13.169110/12.909078mm，超过冻结12mm；
radius/rejoin readiness0，rotation/speed readiness250。动作及实际参数均变化，
每tick至少一维rate-limited，energy-limited0。不是策略断接或能量缩放阻断的证据。
尾10秒第一刚度请求p95为898.182/1308.093，实际p95仅215.712/257.148，
实际中位182.607/188.949；原始第一动作lag1相关.0452/.1668，
连续请求相对当前参数的方向相同占比.4538/.4096。
这说明偶发大请求未形成同等范围的持续执行；后续应核对探索的时间连续性，
不能仅凭原始动作方差认定实际参数探索充分。只是两个演化中策略回合的描述，
未证明IID、filter因果关系、提高刚度必然有效或新探索方案有益；既往高刚度失败也须保留。
当前配对未结束，未比较两臂、未登记新处理，不按该诊断放宽filter/gate。

两项本机CPU6/1GiB/swap0诊断正常退出0（359ms/99ms），第一项峰38,109,184字节；
核验原生输入hash、parameter trace与action文件一致并复制输入，未运行仿真/梯度更新/filter重放。
归档助手8.387秒退出0。证据BENCH/outputs/rl_goal_stream_window_20261017T0805含
LATE_CARRY、ACTION_PERSISTENCE、原生输入、两诊断脚本、WINDOW/TRAINING_SCREEN及闭合日志。
服务器仅存储/传输/hash；已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T0805/evidence.tar.gz`，
14,653,725字节，SHA256
`525e32b53b4aead0479810b058b0359e34a0f0e9abe3e07993f34e0f46907fbd`。

按sii-research-sync更新三份进度并提交/push main，保留无关meeting文件及全部失败收据。
Goal active，继续同一处理组至44k，再依据双方完整匹配条件/相同曝光结果决定调整和四族接续。
控制组0/32，四方法均未证明收敛，最终acceptance和独立物理/filter replay未执行。



## 2026-10-17 07:47 CST — 接续阶段继承存储保护，occupancy十四回合

开工查询/fetch/read main `f08ce92a44002cb57ed432cef9c731838c405020`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS和两份进度；
收工重读AGENTS，发布前复查远端未前进。本轮沿用已开启的Goal，不创建重复worker。

修复未来阶段的存储登记遗漏：原selected continuation只复制storage-aware trainer/helper，
从旧base选择stream策略时未继承working_set_policy；普通prepare_next继承policy字段却不生成
新STORAGE_POLICY，导致后续校验失败。现在新选定阶段从base/所选闭合来源保留精确策略与
CPU6/1GiB/swap0资源，核对已审阅trainer/helper hash，在最终登记写完后生成独立seal；
普通接续也生成新seal。非规范outputs/rl_goal_stream_*目标在创建前拒绝。
不复用父级seal或STORAGE_PREFLIGHT；新阶段仍须真实归档/恢复和四路replay预检。
活动snapshot、冻结物理、reward、actor输入/filter/执行器/dt5e-5均未修改。
这是续训资源正确性修复，不是不收敛根因或学习改善的证据。

首批23测试通过，补充旧checkpoint重新选择路径和共享调度器回归后37测试通过：
selected7、occupancy9、storage8、ordinary continuation5、stage4、regularized4。
覆盖新seal身份、缺失新存储预检仍拒绝、旧source/checkpoint不变、隔离snapshot导入、
奖励及44000→55000步历史保留、重新选择旧目标仍保留存储保护、非法目标不留目录。
本机受限测试1.482秒退出0，峰38,264,832字节/1GiB，OOM/swap0；两次记录均保留。
当前pair尚未结束，未实际选择下一训练阶段，也未启动额外仿真。

观察器23:34:48–23:45:18 UTC记录17250→19250步、12251→14251更新、12→14闭合回合，
新边界归档后退出0，协调器2502213/worker2546313继续active。
前14回合均1375步/55秒、physical_valid、carry，Task/Strict0/14；新增ep12/13 return
−27.390283956/−26.759521963。均值−27.560248586、标准差.461354462（含warmup），
不能把失败平台当收敛，也不比较不同奖励定义的总return。19250条交互、14251更新连续有限，
奖励分解、AUDIT/trace、cp19250成员hash和新增原始归档通过。
末temperature .002817736、critic loss6.692233。worker峰2,707,271,680/max3,221,225,472字节，
OOM/max事件/swap0；磁盘余56,055,189,504字节，高于50GiB。另查GPU42°C/1437MiB。
归档助手CPU6/1GiB/swap0，5.869秒退出0；服务器只存储/传输/hash，无服务器计算。

本轮代码前后副本、测试记录、WINDOW/TRAINING_SCREEN/连续日志位于
BENCH/outputs/rl_goal_stream_window_20261017T2350；已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2350/evidence.tar.gz`，
9,784,137字节，SHA256
`2b43deae7edca5efe6e6b8abe93da6fc39c7bce58bf01006fea0d231d88117e0`。
归档修复源码以内容hash标识，不冒充正在运行的冻结代码。按sii-research-sync同步三份进度、
提交/push main，保留无关meeting文件。Goal active；继续44k匹配试验，双方完成再比较。
控制组0/32，四方法均未验证收敛，最终acceptance未执行，所有失败/未完成收据保留。



## 2026-10-17 07:32 CST — 修复归档迁移后的接续误拒绝，occupancy十二回合

开工查询/fetch/read main `dec11ea216d26559ccffca456f6e862ee7b315ae`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份进度，收工重读AGENTS。
上一轮为已核验等待；本轮新增真实接续缺陷复现、修复和回归证据。
协调器2502213/worker2546313持续active，未重复派发或改活动source/参数/物理。
观察器23:20:46–23:30:46 UTC从14500/9501更新推进至16500/11501更新、
10→12闭合回合，边界归档后退出0；现有训练继续。

只读compatibility probe发现：原未启动的occupancy登记可与四方法base匹配，
当前stream登记却触发“Occupancy migration changed other frozen source”。
旧校验器未识别已登记的存储迁移新增helper和trainer边界hook，后续选择会被误拒绝；
不是正在运行worker的训练故障，也不是学习不收敛根因。
修改`tools/goal_selected_continuation_20261016.py`：先验证storage seal、前驱登记hash、
训练祖先和parameter manifest，再仅归一化已审阅且严格hash锁定的trainer/storage helper；
其他冻结source仍逐项一致。新选定阶段复制精确storage helper依赖，保留奖励身份和原checkpoint。
不将任意trainer变化泛化豁免为“存储”，不把策略来源、reward或replay混合。
实际stream登记修复后compatible通过，活动source/parameter manifest与登记hash保持。
当前pair仍运行，因此尚未实际选择/派发新训练；新阶段仍需独立存储登记和恢复预检。

新增两项回归覆盖stream选择→隔离snapshot导入→后续阶段、精确继承44000/55000步和奖励，
以及trainer/helper/physics source与祖先篡改拒绝。相关22项测试全部通过：
selected continuation7、occupancy continuation7、prospective storage8。
首次证据打包错误假定活动快照旧checker等于修复前仓库checker，1.034秒退出1；
此前真实兼容检查和22项测试已通过。失败脚本/收据保留，不重跑或重启训练。
随后从开工commit提取旧checker并核对与原probe hash一致，260ms完成证据打包，
峰29,294,592字节/1GiB、OOM/swap0；原误拒绝和打包失败均保留。

训练前12回合均1375步/55秒、physical_valid、carry，Task/Strict0/12。
新增ep10/repair_train_017、ep11/repair_train_012的return −27.879664331/−28.144475447，
物块最终XY误差92.242572/110.815609 mm，无物理abort。
前12回合return均值−27.641139524、标准差.431209532，含warmup；失败平台不是收敛。
16500交互/11501更新连续有限，奖励分解、AUDIT/trace、cp16500成员hash和新增原始远端归档通过。
末temperature .003555267、critic loss7.409366。worker峰2,676,830,208/max3,221,225,472字节，
OOM/max事件/swap0；磁盘余56,158,629,888字节，高于50GiB；GPU42°C/1439MiB。
归档助手CPU6/1GiB/swap0，5.685秒退出0，服务器只存储/传输/hash。

证据`BENCH/outputs/rl_goal_stream_window_20261017T2335`含修复前probe、22项测试、
修复前后源码/测试与登记快照、打包失败收据、WINDOW/TRAINING_SCREEN/日志。
独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2335/evidence.tar.gz`，
8,961,349字节，SHA256
`7e50e99e091289ef632f7a8246c5dba00fa5fe31ad1b3e300e97edae6b9a15a8`。
归档内本轮修复源码按内容hash标识，不冒充活动worker代码。

按sii-research-sync同步三份进度，提交/push源码、测试和文档；保留无关meeting文件。
Goal active，继续occupancy登记44k，双方结束再做匹配条件/相同暴露比较；
控制组0/32，四族均未证明收敛，最终acceptance未执行。
全部失败保留，冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，本机计算/服务器仅归档。


## 2026-10-17 07:18 CST — 已核验等待：occupancy十回合/13750步

开工查询/fetch/read main `5bd16b99e9d61bfbb5ddad0d24571ec2d2ae9386`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份RL进度；
收工重新读取AGENTS。上一轮完成动作/路径点诊断，本轮接续健康worker，
无研究源码、训练参数或活动snapshot修改，无重复派发。协调器2502213/worker2546313
真实active；观察器23:04:49–23:16:19 UTC记录11500→13750步、6501→8751更新、
8→10完整回合，边界归档后正常退出0。训练继续，观察器退出不是训练结束。

前10回合均1375步/55秒、physical_valid、carry，Task/Strict0/10；
新增ep8/repair_train_010与ep9/repair_train_027的return为−27.676733438/−27.002897844，
物块最终XY误差84.694987/86.905799 mm，无物理abort。
前10回合return均值−27.566953451、标准差.431974891，含warmup/mixed记录；
失败策略的低波动不是收敛。13750交互/8751更新连续有限，奖励分解、AUDIT/trace、
cp13750成员hash及新增两回合原始远端归档复核通过。
末temperature .004546261、critic loss8.121669。控制组44k/32回合0联合成功保持。

worker峰2,655,051,776/max3,221,225,472字节，OOM/max事件/swap0；
归档时磁盘余56,224,366,592字节，高于50GiB；GPU43°C/1435MiB。
核验归档助手CPU6/1GiB/swap0，5.463秒退出0。
证据`BENCH/outputs/rl_goal_stream_window_20261017T2320`含WINDOW、TRAINING_SCREEN、
连续闭合日志与边界收据。已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2320/evidence.tar.gz`，
7,947,323字节，SHA256
`e89e9c308135dedb839ad905f371bc5627228ffaed5f9574a1af0d78002a2fc4`。

按sii-research-sync同步三份进度、提交/push main，保留无关meeting文件。
Goal active，继续登记44k occupancy，双方完成后再比较匹配条件/相同暴露的任务指标；
不比较不同定义reward总分。四族仍未证明收敛，最终acceptance未执行。
全部失败保留；物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，本机计算、服务器仅归档。


## 2026-10-17 07:03 CST — occupancy八回合与原生动作/路径点诊断

开工查询/fetch/read远端main `bbf94039ec95e242117ccfbb88bb5a98f56e1383`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS和两份RL进度；
收工重新读取AGENTS。上一轮为已核验等待；本轮新增原生动作/路径点证据。
同一协调器2502213/worker2546313真实存活，观察器22:51:25–23:01:55 UTC记录
9000→11000步、4001→6001更新、6→8闭合，归档完成后退出0；未重启、重复派发或改活动snapshot。

occupancy前8回合均1375步/55秒、physical_valid，Task/Strict0/8、均carry。
新增ep6/repair_train_022、ep7/repair_train_000的return为−28.275457426/−27.978447800，
最终物块XY误差88.471501/95.549554 mm；前8回合return均值−27.623737904、
标准差.434456110。包含warmup，不构成收敛或奖励处理收益。
11000条交互/6001条更新连续有限，闭合奖励分解、AUDIT/trace与cp11000成员hash通过，
新增两回合原始远端归档复核通过；末temperature .005778676、critic loss8.609760。

新增诊断固定此前完整学习ep4/5：cp8250经验池的2750条原始动作与控制器记录逐元素一致，
reward与训练final_reward一致、terminal恰在两回合末；checkpoint读前后全部hash保持。
parameter_actions与parameter_trace一致，复制的原生输入逐文件hash一致。
复用冻结来源及前/后步时间对齐检查，两回合末10秒各250样本均停在carry waypoint20/28，
位置误差中位12.850325/12.572138 mm，半径门槛12 mm保持；位置/rejoin readiness0，
旋转和速度readiness均250/250。目标重建残差0、无观测cursor推进。
末段5维raw action标准差分别约[.494,.248,.448,.483,.583]、
[.420,.222,.166,.133,.547]，实际参数各维标准差也非零；并非动作完全恒定或未接入。
全回合每维abs(raw)>.95比例3.35%–7.93%；至少一维触发原生rate-limit的tick比例
100%/99.8545%，energy-limit0。末段第一维刚度中位180.577027/185.064195。
这些是原生25Hz描述，不能证明探索充分、filter导致失败或提高刚度必然有效；
不将低刚度观察外推全部条件。无仿真/梯度/独立物理子步/action-filter replay。
诊断工具577ms退出0，峰73,154,560字节/1GiB/swap0/OOM0。

训练worker峰2,639,867,904/max3,221,225,472字节，OOM/max事件/swap0；
归档时磁盘余56,316,026,880字节，高于50GiB，GPU42°C/1435MiB。
归档助手CPU6/1GiB/swap0，6.689秒退出0。证据目录
`BENCH/outputs/rl_goal_stream_window_20261017T2310`含OCCUPANCY_CARRY、原生输入、
实际诊断脚本、WINDOW/TRAINING_SCREEN和完整日志；服务器只存储/传输/hash。
已独立SSH核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2310/evidence.tar.gz`，
11,621,775字节，SHA256
`fda97147da8d430c82f8f59910ff851610a8ddb044240bf0bccaf00cee6e424e`。

按sii-research-sync更新三份进度并提交/push main，保留无关meeting文件。
Goal active，继续occupancy登记44k预算，双方完成后再做匹配条件/相同暴露比较；
不对不同定义reward总分排名。四族仍未证明收敛，控制组0/32不变，最终acceptance未执行。
全部失败保留；冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5及本机计算约束保持。


## 2026-10-17 06:49 CST — occupancy新增两个完整学习回合，8250步/3251更新

本轮接续已完成开工核查的同一任务：远端main
`2ad99d8f9fc4dcad1cd32146df947250e2ad57ce`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，已查询/fetch/read两分支日志、
AGENTS与RL进度；收工再次读取AGENTS。Goal保持active。
观察器22:37:03–22:48:03 UTC记录6250→8250步、1251→3251更新、4→6闭合回合，
边界归档完成后正常退出0。协调器2502213/worker2546313保持，未重复启动或改活动配置。

新增ep4/repair_train_002、ep5/repair_train_028均1375步/55秒、physical_valid，
全程处于学习阶段；return分别−27.650366084、−27.367207751，Task/Strict均false、
stage carry，最终物块XY误差89.382860/86.415408 mm，无物理abort。
前6回合Task/Strict0/6，return均值−27.455999668、标准差.363006601；
含3个warmup和1个混合回合，不能据此宣称收敛或奖励处理有效。
8250条交互/3251条更新连续有限，全部闭合奖励分解、AUDIT/trace与cp8250成员hash通过，
新增两回合原始远端归档复核通过。末temperature .007384279、critic loss8.767115。
控制组44k/32回合0联合成功保持；待occupancy同预算结束再运行匹配条件/暴露比较，
不比较不同奖励定义总分。四族均未证明收敛，未做最终acceptance/独立物理或action/filter replay。

worker峰2,604,429,312/max3,221,225,472字节，OOM/max事件/swap0；
归档时磁盘余56,173,322,240字节，高于50GiB；宿主GPU43°C/1436MiB。
核验归档助手CPU6/1GiB/swap0，5.960秒退出0，服务器只存储传输/hash。
本地证据`BENCH/outputs/rl_goal_stream_window_20261017T2250`含WINDOW、
TRAINING_SCREEN、连续日志与边界收据；独立SSH核验服务器归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2250/evidence.tar.gz`，
6,189,492字节，SHA256
`53d11314d4e2846ebe2aae52fbd2a883059b8e6c76bcaa2e4000839938ff42b8`。
按sii-research-sync同步三份文档并提交/push main，保留无关meeting文档。
下一步继续健康occupancy至登记44k边界，基于完整对照结果决定后续修复/调参阶段；
保持冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5及本机计算约束。


## 2026-10-17 06:35 CST — occupancy越过warmup，501次真实参数更新核验

开工查询/fetch/read main `c28638499c93a4c3020e9961c1b880cd895c5535`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份RL进度并收工重读。
上一轮新增首回合奖励公式证据；本轮从2250步/0更新观察同一worker2546313至
5500步/501更新，约18分钟，4回合归档后观察器正常退出0。协调器2502213保持，
无重复启动、重启或活动配置修改；5000步开始首次更新，符合登记UTD1。

occupancy前4回合均1375步/55s、physical_valid，Task/Strict0/4，均carry。
ep0..3条件repair_train_008/029/001/007，return分别
−27.520973245/−28.096028074/−27.086804364/−27.014618488；
平均−27.429606043、标准差.430753396。前三回合纯warmup，第四回合混合warmup/学习，
不足以评价收敛或处理收益，不与control不同定义reward总分比较。
5500交互与501条optimizer更新连续有限，reward分解、所有闭合AUDIT/trace及cp5500成员hash通过；
末temperature .009566467、critic loss8.979347。控制组0/32结果保持，四族均未证明收敛。

新增只读checkpoint参数检查：cp4125的saved updates=0，cp5500=501，配置完全相同，
全部checkpoint成员读前后hash核对。按Flax portable msgpack格式直接解码NumPy数组，
不导入JAX、不执行actor/optimizer或新增梯度；所有数值叶有限、参数shape/dtype一致。
actor/critic/target_critic/temperature均有参数变化；
最大绝对参数变化分别.032853909/.078507282/.043938220/.044424057。
actor/critic/temperature的内部update_step由0变501；
target_critic的update_step仍0，opt_state正常为None，其参数通过目标网络同步发生变化。
这证明实际参数更新，不证明更优动作、正确真实Q值、任务成功或收敛。
首次诊断把正常target opt_state=None当数值数组而失败，597ms退出1；
已保留PARAMETER_CHECKER_ATTEMPT1.json及原脚本快照，修正只读检查器后703ms退出0，
峰362,242,048字节/1GiB，swap/OOM0；不是训练故障，未改或重启worker。
整体证据助手CPU6/1GiB/swap0，6.215秒退出0。

worker峰2,590,826,496/max3,221,225,472字节，OOM/max事件/swap0，
归档时磁盘余56,238,043,136字节，高于50GiB保护；GPU43°C/1436MiB。
证据 `BENCH/outputs/rl_goal_stream_window_20261017T2235` 含参数更新报告、失败检查收据、
修正前后脚本、WINDOW/TRAINING_SCREEN、训练与更新日志及原始归档映射；
已上传且独立SSH复核
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2235/evidence.tar.gz`，
7,392,612字节，SHA `096d42f4ea0d7defb7bd850f1b5e29f970bfa874b03c825634e1cd50f3b01e3c`。
按sii-research-sync同步三份进度并提交/push main，保留无关meeting文件。
Goal active，继续同一occupancy worker完成登记44k预算，之后再做匹配条件比较；
物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，本机计算、服务器只归档，
全部失败保留，未做统一acceptance或独立物理/action/filter replay。


## 2026-10-17 06:13 CST — occupancy首完整回合：原生奖励公式逐区间核验

开工查询/fetch/read main `32d344e3a828c65d482c856ab268bca256287eaa`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份RL进度，收工重读。
上一轮已完成control预算及自动交接核验；本轮新增occupancy奖励链路证据。
协调器2502213/occupancy worker2546313保持active，未重启/重复启动/改活动snapshot。
只读观察器补充warmup空optimizer列表的明确表示（last_optimizer=null），先于4回合目标
检查首回合公式；不更改训练预算、warmup或优化器。观察器在首回合归档后正常退出。

ep0/repair_train_008完成1375步/55s，physical_valid，Task/Strict0/1，stage carry，
return−27.520973245；仍处于5000步warmup，optimizer更新0，无学习/收敛或处理收益结论。
全部1375交互连续，reward分解、AUDIT/trace及cp1375成员hash通过，全部失败保留。
对首回合原生25Hz手/物块位置重算approach/lift/payload-goal三项等权phi，
逐区间与RL_INTERVALS及训练日志next_potential核对，最大误差0。
独立按−4*(1−phi)*interval/55重算occupancy项，1375区间最大误差0，
occupancy总和−2.027561326，折扣总和−1.495285257；
首回合完整55s、remaining-tail=0，与日志一致。本证据未覆盖实际提前失败非零tail路径。
phi初始.112047706、最终/最高.530355179；最终reference potential .594671346，
核验使用实测物块phi，没有把参考进度冒充物块进度。潜能折扣望远镜残差3.55e−15。
输入文件读前后hash不变，匹配原始归档成员，原始远端归档复核通过。
这些是原生遥测/奖励算术核验，无仿真、梯度、独立物理子步或action/filter replay。
不同定义reward不相减/排名；待两组44k均完成后再比较匹配条件的原生任务结果。

奖励公式助手CPU6/1GiB/swap0，1.208秒退出0，峰32,407,552字节；
首回合整体核验/归档助手4.331秒退出0。
worker峰2,086,580,224/max3,221,225,472字节，OOM/max事件/swap0；
磁盘余56,455,733,248字节，高于50GiB保护；GPU43°C/1113MiB。
证据 `BENCH/outputs/rl_goal_stream_window_20261017T2215` 含
OCCUPANCY_REWARD_VERIFICATION、WINDOW、TRAINING_SCREEN、原生输入、检查器源码及原始归档映射；
已上传且独立SSH复核
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2215/evidence.tar.gz`，
2,736,274字节，SHA `9824f7cb848187994097a35940533f009c7ca6b658addb4cab2b62243b5fd23e`。
按sii-research-sync更新三份进度、提交/push main，保留无关meeting文件。
Goal active，下一步接续同一worker到4完整回合/5500步并核验warmup后真实更新；
四族均未证明收敛，控制组0/32结果不变，最终acceptance未执行。
物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，本机计算/服务器仅归档。


## 2026-10-17 06:08 CST — 控制组44k预算完成，occupancy奖励组自动接续

开工查询/fetch/read main `7e3abb95f099832fb8f047421330de3be078d260`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份RL进度，收工重读AGENTS。
上一轮为新增诊断与已验证等待；本轮完成control有限阶段证据核验并验证自动交接。
未重复启动训练、重启健康worker或修改活动源码/配置。仅新增临时只读完成观察器，
区分正常退出与异常，保留cgroup消失前的带时间戳资源观测；观察器正常退出0。

impedance_control从18:15:38.112110UTC训练至22:04:03.982761UTC，44,000步/39,001更新，
32个1375步/55s完整回合，全部physical_valid，Task/Strict0/32；27回合carry、5回合retreat。
mean return−25.530207948、std .659400224；新增ep30/31（repair_train_004/009）
return−25.153143068/−25.668938414，均carry失败。完整交互/更新连续有限、
全部闭合reward分解、AUDIT/trace及最终cp44000成员hash通过；
末temperature .001180375、critic loss6.666161。执行状态complete/stop_reason=step_budget，
但只是44k先导预算完成，training_complete=false，未达成1M目标、收敛或最终通过。

协调器PID2502213保留，核实首job退出0/32回合/44k及checkpoint后自动启动第二job；
原worker2502235已退出，occupancy worker为PID2546313、
`sii-rl-goal-af59b75d7cc5.service`，active、MemoryMax3GiB/MemorySwapMax0。
交接核验时execution250步/0更新，training.jsonl有362条连续完整交互；随后500步/0更新，
处于登记5000步warmup，不能称学习更新或收益已验证。
逐项比较两份实际PROTOCOL，唯一差异为registered_utc、payload_occupancy_guidance及其definition；
模型配置、seed、条件、warmup、源码hash、资源设置均一致；两组从零开始、无teacher/BC，
actor仍canonical48。未继承control回放；不同reward总分不直接比较。
本轮没有matched-arm收益结论，等待occupancy完成同一44k预算再比较原生任务结果。

control最后可读资源样本22:03:56.795985UTC：peak3,116,797,952/max3,221,225,472字节，
OOM/max事件/swap0；cgroup正常退出后已移除，所报peak是最后观测值，不冒充退出后的内核读数。
奖励组核验时current/peak1,670,729,728字节，OOM/max事件/swap0；后续GPU43°C/1127MiB。
归档时磁盘余56,739,905,536字节，高于50GiB保护线。
交接助手CPU6/1GiB，311ms退出0；完成核验归档助手同限额18.312秒退出0。
证据 `BENCH/outputs/rl_goal_stream_window_20261017T2205` 含
WINDOW、TRAINING_SCREEN、HANDOFF_VERIFICATION、两份协议/执行快照、检查器源码和失败原始归档映射。
已上传且独立SSH复核
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2205/evidence.tar.gz`，
17,021,373字节，SHA `38528b5a849d6404b76abf3e4fb2ef3696a382290e914cbd2a5408edcda09c43`。
为下轮准备只读`/tmp/sii_goal_occupancy_window_monitor.py`，绑定实际新PID/服务，
首次核验目标至少4回合以覆盖warmup结束；未启动额外训练进程。
按sii-research-sync更新三份进度并提交/push main，保留无关meeting文件。
Goal active，四族仍未证明收敛，继续奖励组；物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，
全部失败保留，服务器仅归档，未执行统一acceptance或独立物理/filter replay。


## 2026-10-17 05:50 CST — 第三条retreat失败诊断；控制组30回合/41,250步

开工查询/fetch/read main `853b605fadf205d7a4f4724c960ea91f1858e7bb`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/两份RL进度并收工重读。
上一轮为已验证等待；本轮新增原生失败诊断，并持续观察同一协调器2502213/worker2502235，
从39,250步/34,251更新推进至41,250步/36,251更新，30回合归档后观察器退出0。
未重启、重复派发、改活动snapshot或执行独立物理/filter replay。

ep27/repair_train_026的原生25Hz轨迹及接触/参数记录逐文件与原始归档成员hash核对一致，
读前后hash不变，原始远端归档重核通过。12.00s最高点(.590319,−.228441,.577239)m；
14.48s最接近目标XY仍差.115712m；15.04s物块z=.441679m，手物距离.237700m，
尚在carry。16.92/17.52/18.04s才进入stage5/6/7，此时物块已回到桌面；
最终XY误差.214070m，hold0，release_supported/placement_complete/Task/Strict均false。
payload-corner接触14.76910–14.90990s，峰54.079N；接触与掉落接近不证明因果。
与ep16/19不同，最高点前后±.4s的21个参数样本有13个energy_scale<.999999；
stiffness767.288–1248.098，中位1242.479，而14.88–15.12s掉落邻域energy_scale已为1。
冻结ParameterShield源码确认scale缩放log参数增量，并非全部力矩乘该比例。
故不支持统一“刚度过低”或“过滤器直接压低全部力矩导致掉落”，也无依据放宽filter。
冻结任务阶段按机器人位姿推进，实际payload支撑/位置/稳定时间由最终判据另外检查；
掉落后retreat不是成功统计bug，不改冻结规划/输入/gate。
参数过滤源码SHA `aa3374afdbf6a9c3333a2cb365299ac6e4d21c3e5fba97b335432cc3e0524e70`；
任务源码SHA `60fc1bc868a04e5a8e27c887b91a9ba4ffeaed6cd073379be589780d59fcabd5`。
诊断助手CPU6/1GiB/swap0，3.762秒退出0，峰29,974,528字节；没有仿真或梯度更新。
证据 `BENCH/outputs/rl_goal_retreat_third_20261017T2145`；
已独立SSH复核归档
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-retreat-third-20261017T2145/evidence.tar.gz`，
2,221,415字节，SHA `828a62ee22ce5d05b27a50ca8020be2c274c710b5dc135fe5dc74bc8996fc58f`。

控制组完成44k预算93.75%；30回合均1375步/55s、physical_valid，Task/Strict0/30。
新增ep28/29（repair_train_016/005）return−27.964723652/−26.205297268，均retreat失败，
最终XY误差.179658137/.286577530m；未据阶段标签断言成功或具体掉落机制。
全30回合mean return−25.538152428、std .677016974，四族均未证明收敛。
41,250交互/36,251更新连续有限，闭合reward分解、AUDIT/trace及cp41250成员hash通过；
temperature .001511186、critic loss6.664773。occupancy仍排队，尚无处理收益结论。
worker峰3,116,797,952/max3,221,225,472字节，OOM/max事件/swap0；
磁盘余57,282,682,880字节，高于50GiB保留线，GPU43°C/1438MiB。
CPU6/1GiB核验归档助手10.846秒退出0；证据 `BENCH/outputs/rl_goal_stream_window_20261017T2150`，
已独立SSH复核
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2150/evidence.tar.gz`，
15,977,224字节，SHA `7d8c915d8b00b73177c6373f40c32abd9c8abcaafb561066f0750e5b6f5de604`。
按sii-research-sync保存/同步两份独立证据及三份进度，提交/push main。
Goal active，继续control最后2回合并核对协调器自动接续occupancy；全部失败保留，
本机计算/服务器只归档，物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，最终acceptance未执行。


## 2026-10-17 05:39 CST — 已验证等待：控制组28完整回合，38,500步

本轮承接active Goal；查询/fetch/read远端main `71360524abc3f15988ebeb57712063c285bcb65e`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份RL进度，收工重读AGENTS。
同一协调器2502213/worker2502235保持active；观察从36,750步/31,751更新至
38,500步/33,501更新，28回合边界归档完成后观察器正常退出，约7.5分钟。
未重启、重复派发或修改活动配置。冻结协调器确认control完成、末checkpoint有效且
stop_reason=step_budget后才接续occupancy；处理组仍未开始。

控制组完成44k预算87.5%；28回合均1375步/55s、physical_valid，Task/Strict0/28。
新增ep26（repair_train_003）return −25.217369295，carry，最终放置XY误差.093071702m；
ep27（repair_train_026）return −26.596496000，retreat，最终XY误差.214070391m。
进入retreat不等于放置成功，本轮尚未诊断ep27具体掉落过程，不外推此前两条失败的因果解释。
28回合平均return −25.427662569、标准差.502685825，不能将失败平台称为收敛。
38,500交互与33,501更新连续且有限，闭合reward分解/总和、AUDIT/trace、cp38500成员hash通过；
末temperature .001441916、critic loss6.800612。无奖励处理收益结论，四族未证明收敛，
最终acceptance及独立物理/filter replay均未执行。

本机CPU1/单线程/CUDA0/UTD1保持；worker峰3,052,421,120/max3,221,225,472字节，
OOM/max事件/swap0；归档时磁盘余57,422,405,632字节，高于50GiB保护。
沙箱内nvidia-smi设备不可见，主机只读重查正常42°C/1437MiB，未修改驱动或训练。
CPU6/1GiB/swap0证据助手6.980秒退出0；本地证据
`BENCH/outputs/rl_goal_stream_window_20261017T2140`，全部失败及新增原始归档映射保留。
已上传且独立SSH复核大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2140/evidence.tar.gz`，
15,080,497字节，SHA `2313c3825e22e0d1cc93c38a4b04b90c9c897d3a1c29240984801b330466b8a4`。
本机缺jq，改用Python结构化读取证据统计；仅检查工具回退，无训练修改。
物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，服务器只存储/hash。
Goal active，继续登记44k×2对照；按sii-research-sync同步三份进度并提交/push main，
保留无关meeting文件。下一步观察control剩余4回合及协调器自动接续。


## 2026-10-17 05:27 CST — 已验证等待：控制组26完整回合，35,750步

按sii-research-sync开工查询/fetch/read main `dc821e27b9a7c42bd5c4866c5a872c311c17a5ac`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS及两份RL进度，收工重读AGENTS。
上一轮及本轮均为已验证等待；同一协调器2502213/worker2502235持续active，
本轮从33,500步/28,501更新观察至35,750步/30,751更新，约11.5分钟，
26回合闭合且归档后观察器正常退出，未重启、重复派发或改变活动配置。

控制组完成44k预算81.25%；26回合均1375步/55s且physical_valid，Task/Strict0/26。
新增ep24/25（repair_train_020/025）return −25.791228914/−25.978695063，均停carry。
全26回合平均return −25.390795640、标准差.465323370，仍不能认定收敛。
35,750条交互与30,751更新连续且有限，闭合reward分解/总和、AUDIT/trace、
cp35750成员hash通过；末temperature .001100571、critic loss6.502209。
occupancy组尚未启动，无奖励处理收益结论；四族未证明收敛，最终acceptance未执行。

本机CPU1/单线程/CUDA0/UTD1保持；worker峰3,040,776,192/max3,221,225,472字节，
OOM/max事件/swap0，磁盘余57,555,910,656字节，高于50GiB保护线。
收工仍active，current2,610,409,472字节，GPU42°C/1457MiB。
CPU6/1GiB/swap0核验归档助手7.062秒退出0，无新增模拟器或独立物理/filter审计。
本地证据 `BENCH/outputs/rl_goal_stream_window_20261017T2125`，保留全部失败和新增原始归档映射。
共享归档已上传并再次核验大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2125/evidence.tar.gz`，
14,342,104字节，SHA `602f417d2fa194e6822376e6e767ff1ed62a94017865ba50211d3b599174abb7`。
物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，服务器只存储/hash。
Goal active，继续44k×2登记对照；三份进度同步提交/push main，保留无关meeting文件。


## 2026-10-17 05:12 CST — 已验证等待：控制组24完整回合，33,000步

开工按sii-research-sync查询/fetch/read main `d9a4184ea2fcd1a56eddd037d9f9fb97e932bb4d`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份RL进度，收工重读AGENTS。
上一轮及本轮均为已验证等待；本轮同一协调器2502213/worker2502235从30,750步/25,751更新
推进至33,000步/28,001更新，观察约12.5分钟，24回合边界归档完成后观察器正常退出。
登记顺序仍为control44k后occupancy44k；冻结协调器源码确认须退出码0、complete、
末checkpoint验证及stop_reason=step_budget才继续下一job，未人工重复派发。

控制组完成预算75%；24回合均1375步/55s且physical_valid，Task/Strict0/24。
新增ep22/23（repair_train_024/014）return −24.970507415/−25.246474703，均carry失败。
24回合平均return −25.349615111、标准差.460208250；失败平台不是收敛或奖励处理收益。
33,000交互与28,001更新连续且有限，24回合reward分解/总和、AUDIT/trace、
cp33000成员hash通过；末temperature .000962008、critic loss6.474129。
occupancy仍未开始，四族均未证明收敛，最终acceptance未执行。

本机CPU1/单线程/CUDA0/UTD1保持；worker峰2,998,894,592/max3,221,225,472字节，
OOM/max事件/swap0；磁盘余57,687,056,384字节，高于50GiB保护线。
收工worker仍active，current2,562,818,048字节，GPU41°C/1438MiB。
CPU6/1GiB/swap0归档助手6.979秒正常退出，无新增模拟器或独立物理/filter审计。
证据 `BENCH/outputs/rl_goal_stream_window_20261017T2110`，含完整失败记录及新增原始归档映射；
共享归档已上传且再次远端核验大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2110/evidence.tar.gz`，
13,513,436字节，SHA `ac8f2e6cd3b58312646b482e9001eab88d0a06ff1fa5224d8bd0520adc9a6308`。
冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，全部失败保留，服务器仅存储/hash。
Goal active，继续44k×2登记对照；按同步流程更新三份进度并提交/push main，保留无关meeting文件。


## 2026-10-17 04:57 CST — 已验证等待：控制组22完整回合，30,250步

开工按sii-research-sync查询/fetch/read main `b8f48369b74cbf746609be217ea49c13370b7412`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS及RL进度，收工重读AGENTS。
上一轮增加接触/动作诊断；本轮为已验证等待，同一协调器2502213/worker2502235保持active，
从29,250步/24,251更新观察至30,250步/25,251更新，22回合归档完成后观察器正常退出。
初次只读状态查询误用不存在的checkpoints键，改按实际checkpoint_rows字段确认；不是训练故障，
未重启、重复派发或修改活动配置，后续完整checkpoint验证通过。

控制组完成44k预算68.75%；22回合均1375步/55s且physical_valid，Task/Strict均0/22。
新增ep20/21（repair_train_030/023）return −24.772889103/−24.742053888，均结束于carry。
全22回合平均return −25.371535479、标准差.472809185；不能将失败reward平台视为收敛。
30,250交互和25,251更新连续且有限，所有闭合reward分解/总和、AUDIT/trace及cp30250成员hash通过；
末temperature .001121098、critic loss6.756882。occupancy组仍排队，尚无处理收益结论。
本机CPU1/单线程/CUDA0/UTD1继续；worker峰2,962,739,200字节/max3,221,225,472，
OOM/max事件/swap0；磁盘余57,809,682,432字节，50GiB保护保持。
收工current2,529,439,744字节，其中anon1,570,299,904/file924,946,432；GPU42°C/1439MiB。

CPU6/1GiB/swap0核验归档助手7.057秒正常退出；没有新增模拟器、梯度诊断或独立物理/filter审计。
本地证据 `BENCH/outputs/rl_goal_stream_window_20261017T2055`；
共享归档已再次远端核验大小和SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2055/evidence.tar.gz`，
12,675,748字节，SHA `c7f2bafcc3410593230a600a2227e07def7da61c3f14e8a7187c3628fdea8627`。
新增两回合原始归档映射、hash及失败收据均在WINDOW证据中，逐一远端复核通过。
冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，全部失败保留，服务器只存储/hash。
继续登记44k×2对照，四族均未证明收敛，最终acceptance未执行，Goal active；
三份进度按同步流程提交/push main，保留无关meeting文件。


## 2026-10-17 04:50 CST — 搬运掉落附近的原生接触与控制参数

开工按sii-research-sync查询/fetch/read main `14e289888d25dcb5cbeece57ead4fcadff828e76`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS/两份进度并收工重读AGENTS。
上一轮定位相近掉落位置；本轮增加原生接触摘要与动作窗口证据。同一协调器2502213/
worker2502235保持active，实测28,965步/23,966更新，OOM/max事件/swap0，未重复启动或改配置。

固定control ep16/19；输入rollout.npz/json、execution、parameter_trace/actions与FULLRANGE
全部匹配既有归档成员大小/hash，原始远端归档重新核验，分析前后文件不变。
接触记录器源码hash与两个execution一致：
`76ed25f77c7c32452121382b1f5a766f1b553af62802a1afb7000b3bd029ebe0`。
参数trace与NPZ逐元素一致，1375条记录、canonical48形状、pre/post时间差.04s通过。

ep16/19凸边接触摘要last_s为47.138600/32.663750，全部发生于carry；
该摘要合并robot与payload接触，不能仅凭它分清接触对象，也不能把全回合peak移作掉落瞬时力。
物块—桌角接触carry窗口分别47.185250–47.274450s、32.712250–32.784050s，
峰78.127802/79.959737N，与掉落过程在时间上接近，但尚未证明因果或精确脱离时刻。
最高点前后按pre-interval时间±.4s，各21条记录：平移刚度范围
370.059–543.301（中位478.025）与156.696–185.296（中位171.325），
两个窗口energy_scale均未小于.999999。不能据此认定统一低刚度或能量缩放导致两次掉落。
五路prior_contact仅ball/person_hand/rod/cup/pillar，且属于前一物理区间；
不包含凸边/物块/指尖接触，因此五路零值不是无碰撞证据。无接触真值加入actor。

本机CPU6/1GiB/swap0助手3.924秒退出0，峰34,275,328字节、OOM/max事件/swap0。
仅分析既有训练摘要与25Hz控制记录，无仿真/梯度/filter重放/独立物理子步审计。
证据 `BENCH/outputs/rl_goal_drop_contacts_20261017T2050`，含输入/源码/脚本；
服务器仅归档/hash，上传后再次核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-drop-contacts-20261017T2050/evidence.tar.gz`，
4,071,245字节，SHA `1253ea4cf15bbca1ccee0f71f55be4bed61cacc3bb7b08e291503c85122ac5a7`。
本轮未证明可直接修补的实现缺陷；保留凸边—桌角区域接触为后续诊断方向，
先完成已登记44k×2奖励对照。全部失败保留，冻结约束保持，四族未证明收敛，
Goal active，最终验收未执行；三份进度同步提交/push main，保留无关meeting文件。


## 2026-10-17 04:45 CST — 第二次retreat失败：不同时间、相近位置的搬运掉落

开工按sii-research-sync查询/fetch/read main `4572db887cbfb4d72e022665304a76b0babb7ac0`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS和RL进度，收工重读AGENTS。
上一轮为已验证等待；本轮对control ep16/19两个已闭合失败作原生时间线诊断，
同一协调器2502213/worker2502235仍active，优化推进至28,286步/23,287更新，未重启或重复派发。

两回合rollout.npz/json、RL_INTERVALS、AUDIT、execution逐文件匹配既有原始归档成员大小/hash，
再次远端核验对应归档，分析前后hash不变；1375个40ms采样与neuron_time偏移.04秒通过。
ep19/repair_train_018在32.60s最高点(.599666,−.276229,.581138)m，XY误差.096440m；
32.92s仍carry，高度已降至.447965m、手—物块距离.234572m、XY误差.199780m。
post-interval时间上的stage5/6/7首个样本为34.00/34.80/35.32s，此时物块已在桌面；
因此同样不是仅在正常release后才失败。最终XY误差.181052m、hold0、
release_supported/placement_complete/Task/Strict均false。
ep16最高点47.08s在(.598111,−.271706,.578743)m，两次最高点空间距离约5mm，
但时点相差14.48s。提示后续应检查共同空间区域的原生接触/动作证据；不是接触原因或修复有效证明。
两回合训练条件不同，不作因果配对或策略改善结论。stage采样时间是post-interval时间，
与前轮引用的pre-interval边界相差40ms；不宣称精确接触脱离时刻，.45m只用于描述。

本机CPU6/1GiB/swap0助手5.028秒正常完成，峰28,712,960字节，OOM/max事件/swap0。
未运行仿真、梯度、action/filter重放或独立物理子步审计；活动配置及冻结约束保持。
证据 `BENCH/outputs/rl_goal_retreat_repeat_20261017T2045`，含两回合输入、报告和脚本；
共享归档已上传并再次核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-retreat-repeat-20261017T2045/evidence.tar.gz`，
3,420,374字节，SHA `031a8354e85fbad812785f3f857dd38bde8ea15a2d8f3b9fc2dad5cb1c5f8846`。
全部失败保留，服务器仅归档/hash。继续44k×2登记对照，四族仍未证明收敛，
Goal active，最终验收未执行；同步三份进度并提交/push main，保留无关meeting文件。


## 2026-10-17 04:42 CST — 已验证等待：控制组20完整回合，仍无Task/Strict成功

本轮按sii-research-sync查询/fetch/read main `f27b1bcb640afb646f927060946f2bd44165d2c9`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读AGENTS与两份RL进度，
收工重读AGENTS。上一轮完成诊断发布；本轮为同一活动进程的已验证等待。
协调器2502213与worker2502235持续active，无重复worker、重启或活动配置修改。
观察从26,750步/21,751更新至27,500步/22,501更新，20闭合回合及边界归档完成后观察器正常退出。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`完成44k预算62.5%。
20回合均1375步/55秒且physical_valid，Task/Strict均0/20；return均值−25.432941878、
标准差.452107735。新增ep18/19（repair_train_021/018）return分别−24.761643577/
−25.618699595，结束阶段carry/retreat；进入retreat不等于物块稳定放置成功。
27,500条交互与22,501次更新连续且有限，20回合reward分解/总和、AUDIT/trace、
checkpoint27500成员hash通过；末temperature .001423736、critic loss6.719837。
occupancy组仍未启动，不能推断奖励调整收益；四族均未证明收敛，最终acceptance未执行。

归档时worker峰值2,905,554,944字节、上限3,221,225,472，OOM/max事件/swap0；
磁盘剩余57,937,117,184字节，50GiB保护保持。收工GPU41°C/1438MiB。
CPU6/1GiB/swap0核验归档助手6.311秒正常退出，训练继续使用本机CPU1/单线程/CUDA0/UTD1。
冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，所有失败保留，服务器仅存储/hash。

本地证据 `BENCH/outputs/rl_goal_stream_window_20261017T2040`；
共享归档已再次核验大小与SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2040/evidence.tar.gz`，
11,802,356字节，SHA `4f485c207b277f5494f38fa1526247057430bce5eb8a13698ed7f44a3f82f7f2`。
含新增原始归档映射与完整失败收据。继续登记44k×2对照，Goal active；
三份进度同步并提交/push main，保留无关meeting文件。


## 2026-10-17 04:35 CST — retreat失败定位：物块在carry末段下落，奖励记录并未遗漏

上一轮增加18回合证据与retreat失败判据核查；本轮沿ep16的新失败现象诊断原生时间线。
开工查询/fetch/read main `6ddbe33b04f6c890ef660707c5ee6adb15448024`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
同一协调器2502213/worker2502235保持active，优化实测26,072步/21,073更新；未重启或重复派发。

固定诊断control ep16/repair_train_013，1375个40ms原生采样。输入rollout.npz/json、
RL_INTERVALS、AUDIT、execution逐个匹配已核验归档member大小/hash，诊断前后保持一致。
post-step time与pre-step neuron_time差.04s通过；使用已存手部/物块位置直接计算原有
approach/lift/goal三项标量，与1375个记录payload_potential最大绝对差0，
再与训练step22001–23375的next_potential逐点核对通过。没有模拟器、梯度、
action/filter重放或独立物理子步审计；只是训练原生状态与奖励一致性诊断。

结果显示本回合的下落早于放置/释放阶段：

- 47.08s仍carry，物块高度.578742695m、XY目标误差.099549426m，这是该回合
  最接近XY目标的采样，仍远大于25mm。手—物块距离.086835759m，payload phi=.530338833。
- 47.16s开始的采样显示物块远离目标并降低；47.44s仍carry，高度.440473234m，
  手—物块距离.251745420m、XY误差.225553099m，phi=.143480056。
  .45m阈值仅用于描述时间，不是新门槛；40ms采样不能定位精确脱离接触时刻或力学原因。
- 最大phi单步下降在47.40s，delta−.174050400、progress reward−.870710066；
  47.36s的progress为−.539510401，说明奖励已记录实际退步，并非只奖励手部推进。
- 进入load_transfer的48.36s之前物块已在约(.470675,−.265030,.424997)m；
  release/retreat发生于49.04/49.56s，不能将此次失败归为仅在正常放手后没放稳。
  55s参考进度.998572528，实际物块phi仅.085640495；训练使用后者。
  最终reward−20.428932097，包含任务失败及potential终局抵消；Task/Strict均false。

该证据把后续信用分配诊断定位到carry末段的真实物块退步；不证明接触原因、策略泛化、
最终验收或奖励处理有效。继续已登记44k×2 occupancy对照，不更改活动配置或冻结条件。
物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持，四族均未证明收敛，全部失败保留。

产物BENCH/outputs/rl_goal_retreat_payload_20261017T2035含TIMELINE、该回合训练日志、
资源与归档收据；脚本/tmp/sii_goal_retreat_payload_20261017T2035.py随输入一并归档。
本机CPU6/单线程/1GiB/swap0，峰38,301,696字节、OOM0，3.529秒正常完成。
共享证据已核验且再次远端读取大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-retreat-payload-20261017T2035/evidence.tar.gz`，
1,968,026字节，SHA `c50f52c4419357eddaf6f12afb31cfc570b54c0b2210c168fde05a6f35320822`。
服务器仅归档/hash；收工worker内存2,674,917,376字节、GPU42°C/1439MiB。
Goal active，最终acceptance尚未执行。按sii-research-sync更新三份进度、diff检查后提交/push main，
保留无关meeting文件；本轮没有修改研究源码或活动snapshot。


## 2026-10-17 04:30 CST — 控制组十八回合：出现retreat但物块未放置成功

上一轮为已验证等待；本轮同一PID2502235从22,500步/17,501更新推进至24,750步/
19,751更新，观察约11.5分钟，协调器2502213保持active。开工查询/fetch/read
main `175a00679d5a63348833cb2b524c598b8febd411`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
没有重启、重复派发或研究源码修改。观察器目标18回合并归档后正常结束，训练继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`已完成44k预算56.25%。
18回合均1375步/55秒、physical_valid18/18，Task/Strict0/18；平均return
−25.459916354、标准差.446578570。ep16/17（repair_train_013/011）回报
−25.510348452/−24.790855485，分别终止于retreat/carry。
24,750条交互、19,751次更新连续且指标有限，18回合reward分解/总和、AUDIT/trace hash、
cp24750成员hash通过。末temperature .001785144、critic loss7.017396。
occupancy组尚未启动，没有奖励处理收益或收敛结论。

ep16首次在本control闭合记录中进入retreat，需区分手部阶段与真实物块成功。
读取原生rollout与冻结判据：48.36秒进入load_transfer、49.04秒release、49.56秒retreat；
max_lift .153743m，但最终物块(.470675,−.265030,.424997)m，目标(.69,−.31,.545)m，
XY误差.223887940m，placement_hold_s=0、release_supported=false、placement_complete=false。
因此完整时长/物理有效并不满足稳定放置要求，Task/Strict失败与原生判据一致；
contact_coverage=false仅为诊断，不能拿它当本回合Task失败原因。未进行独立物理重放。
rollout.json SHA `9bf2355bb0afe52a515b8a69d748f8bc5381c4ed284902d5e953d9bc7180a277`、
AUDIT SHA `21ec2b7690e74e753c4f6cd12ef474a7352ac0e7e8e6d509a8c39d22bc943750`
均与已核验原始归档member大小/hash一致；冻结gate来源hash与原生记录一致。
不能将进入retreat当成功，也不据此断言掉落时点、原因或控制器修复已奏效。

归档时worker current2,433,253,376字节、peak2,888,511,488、max3,221,225,472；
memory.max事件/OOM/oom_kill/swap0，free58,046,984,192字节，50GiB保护保持。
收工worker仍active、current2,530,291,712，GPU43°C/1437MiB。
本机CPU1/单线程/CUDA0/.125/UTD1保持；CPU6/1GiB/swap0归档助手6.622秒正常退出。
服务器仅归档及hash，全部失败保留，冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5不变。

本轮证据独立归档并再次远端核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2015/evidence.tar.gz`，
10,992,222字节，SHA `0422d9f425663d07775b076a8c01eafe53c135c2a0401ab8c64ac936cc320cba`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T2015，含闭合日志、训练screen、观察/归档映射。
新增原始轨迹/checkpoint于同主机共同根 `/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-9a5268aec7cb8c6b635403a2/evidence.tar.gz`，272,023,530字节，
  SHA `e4d00bf98d46b2b696ffe613500cd1ec98b5883083648b337327470e0fdaa8a0`。
- `goal-stream-eb6481cac4f4201d9a6bc278/evidence.tar.gz`，271,401,316字节，
  SHA `833699740d082565804768ac77645f784450b2d722048ef0a5f16bcba7db3068`。

Goal active；继续44k×2对照并保留这类“手部推进但真实物块失败”的区别，四族均未证明收敛。
最终acceptance与独立物理/action-filter审计尚未执行。按sii-research-sync更新三份进度、
diff检查后提交/push main，保留无关meeting文件。


## 2026-10-17 04:14 CST — 已验证等待：控制组22k步，十六完整回合尚无成功

上一轮完成原生动作/停滞诊断；本轮确认同一协调器2502213/worker2502235存活后，
从20,250步/15,251更新观察至22,000步/17,001更新，约9.5分钟，无重启或重复派发。
开工查询/fetch/read main `c7400ac979497f4e0cb6035ebdf50c3f8de99bf2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`完成44k预算50%；
16回合均1375步/55秒且physical_valid，Task/Strict0/16，均未证明收敛。
新增ep14/15（repair_train_015/019）return −26.029092712/−24.977225453，carry失败；
全16平均−25.498580653、标准差.441282141。22,000交互与17,001更新连续且有限，
16回合reward分解/总和、AUDIT/trace hash、cp22000成员hash通过。
末temperature .002250975、critic loss7.500761、actor loss1.571514、entropy−.175552。
occupancy组尚未启动；控制失败reward平台不是成功或处理收益证据。

归档时worker current2,395,394,048字节、peak2,848,673,792、max3,221,225,472；
memory.max事件/OOM/oom_kill/swap0，free58,156,675,072字节，高于50GiB保护线。
收工同一worker active、current2,415,771,648，GPU42°C/1440MiB。
本机CPU1/单线程/CUDA0/.125/UTD1保持；CPU6/1GiB/swap0归档助手7.890秒正常完成。
观察器只在目标回合及归档完成后结束；训练继续第17回合。

证据已独立归档核验，并再次从服务器读取大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T2005/evidence.tar.gz`，
10,173,291字节，SHA `7318bd8ee255fd6d3c6731d43af589ee1a62df049e2e8a87d4954f140023a6f3`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T2005，保留WATCH、闭合日志、训练screen和映射。
新增原始轨迹/checkpoint重核于同主机共同根 `/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-a045808f4f18e5d556ca147e/evidence.tar.gz`，271,566,092字节，
  SHA `bfef83c999e7edcaea7f25f6de07f4ab44b64b354d44647dc242b0867b8e00e7`。
- `goal-stream-1c819d0c4484899952ec0176/evidence.tar.gz`，271,931,949字节，
  SHA `024838ba97582db37eb89e9fdc062ab206265edf3d4fbc936ff3741c85e28c00`。

服务器仅归档，活动代码f788fcb/登记d37b16975a6f…不变；冻结物理/MJB/gate/canonical48/
filter/执行器/dt5e-5保持。本轮属于已验证等待，无研究源码修改；四族仍未证明收敛，
最终acceptance及独立物理/action-filter重放未执行，全部失败保留。Goal active，
继续登记44k×2对照；三份进度diff检查后提交/push main，保留无关meeting文件。


## 2026-10-17 04:04 CST — 十四回合原生动作诊断：并非始终低刚度，停滞原因仍需对照验证

上一轮为已验证等待；本轮增加固定闭合前缀的原生动作/路径点诊断，避免将早期低刚度观察
外推成全部失败的原因。开工查询/fetch/read main `7dcf03ff5360664e5696a35e0b4bd6af3290951c`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
协调器2502213/worker2502235均真实active，实时优化已到20,072步/15,073更新；
本轮诊断固定ep0–13、19,250已闭合步，不把在途记录混入结果。

对14回合逐一验证AUDIT/rollout与执行记录hash、parameter_trace及parameter_actions原始动作/
实际参数逐元素一致，输入文件前后hash保持。全部5维数组有限；运行原有冻结来源匹配、
前后步时间对齐及路径点重构检查。只读25Hz训练原生记录，未运行新仿真/梯度/物理子步/
action-filter replay，没有修改活动checkpoint、reward或source。

新证据限定了下一步判断：

- ep8/9末10秒实际第一维刚度中位834.553681/1123.982370，明显不同于ep4/5的
  189.317379/178.694966；仍停在waypoint20。不能把所有失败归因于始终低刚度，
  也不能据此推断提升刚度必定无效：条件不同，策略持续变化，尚非因果对照。
- ep11末10秒cursor18→20，观测到两次前进；其他13回合末10秒cursor20不变。
  所有回合当前采样target的position/rejoin readiness为0，但planner先更新后采样，
  因此零readiness不能被解释为全程没有推进。该诊断明确保留时序语义。
- ep12/13末10秒位置误差中位12.775111/12.849531mm，当前冻结半径为12mm；
  对应刚度中位232.280391/322.356390。只说明这些尾段仍未跨越当前路径点条件。
- 完全学习回合ep4–13，各维|raw_action|>.95比例约2.11%–13.96%，并非整段动作
  恒定饱和。至少一维触发原生rate-limit记录的tick比例99.709%–100%，不能将
  任一维过滤比例误当每一维均失效或证明失败由filter造成。
- ep8/9/13出现能量缩放，tick比例5.1636%/1.2364%/.2182%；其他回合为0。
  之前ep0–5的零缩放观察仍成立，但不能外推到后续全部回合。

诊断根BENCH/outputs/rl_goal_stream_carry_20261017T2000；CARRY_ACTIONS包含完整逐回合输入hash、
参数统计、原生gate/path证据与限制，实际脚本/tmp/sii_goal_stream_carry_20261017T2000.py也归档。
本机CPU6/单线程/1GiB/swap0，峰60,559,360字节、OOM0，13.859秒正常完成。
已核验且再次远端读取大小/SHA的共享证据：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-carry-20261017T2000/evidence.tar.gz`，
28,537,644字节，SHA `372af0b6309ef71ca941db25ace8e45dd1189d495a2b260b1f6299dcab6eacdd`。
服务器仅存储/传输/hash。收工worker内存2,511,310,848字节，GPU43°C/1447MiB。

继续已登记44k×2 occupancy对照，不据上述观察擅改刚度边界/filter或额外混入其他处理。
活动代码f788fcb、登记d37b16975a6f…保持；四族训练收敛未证明，当前control仍0/14联合成功。
最终acceptance未执行；全部失败保留，Goal active。按sii-research-sync更新三份进度、diff检查、
提交/push main，保留无关meeting文件。


## 2026-10-17 04:00 CST — 已验证等待：控制组十四回合，连续更新与归档通过

上一轮完成12回合证据发布；本轮对真实存活PID2502235有界观察约9.5分钟，
从17,750步/12,751更新推进至19,250步/14,251更新，协调器2502213持续active。
按sii-research-sync查询/fetch/read main `57b9f4a1ad5a2967ad399ede6abb7d4d3131db90`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/进度，收工重读AGENTS。
无研究源码或训练配置改动，无重复训练；观察器达到14回合且归档完成后正常退出，worker继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`的14回合均1375步/55秒、
physical_valid14/14，Task/Strict0/14；平均return −25.497926591、标准差.427819936。
新增ep12/13（repair_train_006/031）return −24.775301155/−24.998685579，均carry失败。
ep12原生RMSE23.551309mm、峰矩35.941719Nm、峰速.388448807m/s、穿透.156059713mm、
放置XY误差.085631292m；只是训练原生记录，不是独立验收。回报变高不等于任务完成。
19,250交互及14,251更新序号连续且指标有限，14回合reward分解/总和、AUDIT/trace hash、
cp19250成员hash通过；末temperature .002821193、critic loss7.599995。
控制44k预算已完成43.75%；occupancy尚未启动，没有奖励处理收益结论。
已读冻结协调器逻辑：仅正常step_budget结束且checkpoint通过才接续另一组，异常保留失败。

归档时worker MemoryCurrent2,359,603,200字节、peak2,812,641,280、max3,221,225,472，
memory.max事件/OOM/oom_kill/swap均0；磁盘可用58,265,899,008字节，50GiB保护保持。
收工服务仍active，GPU40°C/1440MiB；CPU1/单线程/CUDA0/.125/UTD1保持。
归档助手本机CPU6/1GiB/swap0、9.652秒正常退出。服务器仅归档/大小/hash核验。

本轮证据已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1950/evidence.tar.gz`，
9,334,574字节，SHA `01a170160822793de10863b19f0c266ce17cac213350af2ab94bd2e1781e5f2f`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1950，含观察、闭合日志、训练screen、
实际脚本与归档映射。新增原始轨迹/checkpoint已重核，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-ecb2188a818f31ec636cf4d4/evidence.tar.gz`，270,561,939字节，
  SHA `862cd135df5f53b3e28c3ed2ad1e317f8370d7415585b41c74593723e42039b7`。
- `goal-stream-4fb246fb459d819256748ab1/evidence.tar.gz`，271,347,558字节，
  SHA `5f60956e721ad39b47d574b756353e1776fae91e42903f510c20c885b779e183`。

活动代码仍f788fcb，登记SHA d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6。
物理/MJB、最终gate、canonical48/filter/执行器/dt5e-5保持；全部失败保留。
本轮是已验证等待，四族尚未证明收敛，最终acceptance/独立物理与filter重放尚未执行。
Goal active；继续44k×2登记对照，之后按配对任务/原生指标选择调整，不将小预算pilot当最终完成。
仅提交三份进度，保留无关meeting文档；diff检查后正常push main。


## 2026-10-17 03:48 CST — 已验证等待：控制组十二回合，奖励对照继续

本轮承接同一PID2502235从14,500步推进至16,500步的观察与归档；协调器2502213保持active。
复核远端main `135e1c7349bf108ae40d59e3d293b7bdfdd40e18`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read两分支日志、AGENTS与两份进度。
沙箱fetch网络失败后宿主fetch成功；baseline没有新的RL变更。Goal保持active，没有重复派发或重启。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`已核验16,500连续交互、
11,501连续有限优化更新，44k控制预算完成37.5%；12回合均1375步/55秒、physical_valid，
Task/Strict均0/12，平均return −25.599748795、标准差.372667896。
新增ep10/11（repair_train_017/012）return −25.693374591/−26.003577436，均carry失败。
12回合reward分解与总和、AUDIT/trace hash、cp16500全部成员hash通过。
末次temperature .003578299、critic loss7.789541、actor loss.616567、entropy1.863455。
收工实时读取已达17,358步/12,359更新，第十三回合仍在途；不能与已归档闭合统计混算。
occupancy处理组尚未启动，不比较不同目标的总reward来宣称收益；四族均未证明收敛。

归档时worker内存2,313,179,136字节、峰2,769,199,104、硬限3,221,225,472，
memory.max事件/OOM/oom_kill/swap均0；磁盘可用58,362,855,424字节，50GiB保护保持。
宿主19:46UTC复核同一服务active、MemoryCurrent2,460,209,152、GPU43°C/1438MiB。
归档助手CPU6/1GiB/swap0，5.824秒正常结束；本机CPU1/线程1/CUDA0/.125/UTD1训练保持。
物理/MJB、最终gate、canonical48、filter、执行器与dt5e-5均未改。

本轮证据归档已核验并再次读取服务器大小/SHA：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1935/evidence.tar.gz`，
8,495,607字节，SHA `9f3694059aa9a0f1a2e5b80b3afc9e62495780796f1e2e145e8c025b1d151dca`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1935，含WINDOW、TRAINING_SCREEN、
闭合训练/优化日志、WATCH、归档收据和实际观察脚本。新增原始轨迹/checkpoint已核验于同主机
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-732f56334291d23283af4822/evidence.tar.gz`，268,897,079字节，
  SHA `7ca042aa49162a5f9090338455c0c8e1b005180b0e905093e66567d0f0f4386d`。
- `goal-stream-61f2565877a723e74fba984b/evidence.tar.gz`，269,570,697字节，
  SHA `70c3d5f0633ab36861ff41abf4f1e4a83d42b5a3f19cf0b8a7efd6d37facf81c`。

当前32训练条件均events=all，现有worker没有课程/state-reset入口；本轮未改变任务或引入teacher/replay。
活动研究代码仍f788fcb，登记SHA `d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。
先完成登记44k×2配对，再按相同条件/曝光的任务与原生指标决定下一调整；不将失败reward平台当收敛。
本轮仅更新三份进度，保留无关meeting文档及全部历史失败；未执行最终acceptance或独立物理/filter重放。
收工重读AGENTS，文档diff检查后提交并正常push main；Goal继续，不以观察器退出作为训练终止。


## 2026-10-17 03:29 CST — 已验证等待：同一worker闭合十回合，控制组继续运行

上一轮为固定样本critic诊断进展；本轮为对已确认存活的PID2502235的已验证等待，
从12,000步/7,001更新观察到13,750步/8,751更新，持续约10分钟，协调器2502213保持。
开工按sii-research-sync查询/fetch/read main `46a226438adf3edb8aa2717086e5536c83470876`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/两份进度，收工重读AGENTS。
没有重启、重复训练或修改活动snapshot；观察器达到十回合且归档完成后正常退出，训练继续。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`闭合10个1375步/55秒回合，
physical_valid10/10、Task/Strict0/10。新增repair_train_010/027 return
−25.759603751/−25.400400406，均停在carry；保留全部失败，不将回报平台视为收敛。
13,750交互序号与8,751优化序号连续且指标有限；10回合reward逐项/总和、AUDIT与trace hash、
cp13750全部成员hash通过。最后temperature .004527187、critic loss8.104725。
控制组44k预算完成31.25%，occupancy组仍排队；没有处理收益或四族完成结论。

worker峰2,731,810,816字节、3GiB硬限、memory.max/OOM/oom_kill/swap0；
记录时MemoryCurrent2,280,210,432字节，本机free58,428,452,864字节，50GiB保护保持。
沙箱nvidia-smi不能访问驱动，随后宿主复核43°C/1441MiB且优化持续，未误判为GPU故障。
服务器归档盘可用3,553,241,657,344字节，仅查询容量/传输/hash，未使用服务器计算。
新增两回合归档耗时41.446/38.407秒后同一worker继续；正常归档等待不算训练异常。
CPU1/线程1、CUDA0/.125/UTD1、冻结物理/MJB/gate/canonical48/filter/执行器/dt5e-5保持。

本轮闭合日志、训练screen、逐回合原生结果、监视轨迹、脚本与新增轨迹已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-window-20261017T1920/evidence.tar.gz`，
7,669,855字节，SHA `cb41442eedf21dd0a07792a7404ee5ee9a608adc4696014de5973eeffbb1f284`。
本地缓存BENCH/outputs/rl_goal_stream_window_20261017T1920；分析/归档本机CPU6/1GiB/swap0。
新增原始回合/checkpoint已重核服务器大小/hash，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-0aa94c08d05b7ead45da3481/evidence.tar.gz`，268,001,970字节，
  SHA `e3724b0c7cd8ce949600049b1420d660377dfb6afcc7ed17eda7cb5294c3655d`。
- `goal-stream-640d8cde1a6b99e95e5ee828/evidence.tar.gz`，269,075,243字节，
  SHA `f3c1658daf6dfc157a99eded7394063267e2d61173b629f245d935b8014b42ec`。

活动研究代码仍f788fcb、登记SHA d37b16975a6f…，本轮无研究源码修改；文档diff检查后提交/push main。
Goal active；继续control到登记边界，核对后续occupancy派发。四族均未证明收敛；
训练screen条件仍不满足，最终acceptance与独立物理/action/filter重放未执行，历史数据未删除。


## 2026-10-17 03:15 CST — 固定终局样本确认critic能学习罚分，策略泛化仍未解决

上一Goal轮有训练链路/失败定位进展；本轮开工查询/fetch/read main
`131615dc7414a03c8dafd3048ff2175ffdd0ac4c`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS/进度，收工重读AGENTS。
同一协调器2502213/worker2502235持续active。只读观察到第八回合及归档闭合，未重启或重复启动。

阻抗fresh control已闭合11,000步/6,001更新（44k预算的25%），8回合全1375步/55秒、
physical_valid8/8，Task/Strict0/8。新增repair_train_022/000回报−26.077511768/−25.892417060；
末10秒均250采样停在carry waypoint20/28，位置误差中位12.801975/12.738583mm，
radius/rejoin readiness0，rotation/speed均250/250。冻结12mm门槛未改。
11,000交互、6,001优化记录连续且有限，8回合reward逐项及总和、AUDIT/trace hash、
cp11000成员hash通过。occupancy组尚未启动，没有奖励处理收益结论。
收工live optimizer为11,342步/6,343更新；第九回合在途。

本轮先以cp9625的1,131个预定训练样本检查n25 categorical critic：
平均clipped mass1.55e-6、终局窗口0，未见显著support截断。较早6回合末25步TD残差均值
.0269027；刚闭合第七回合为3.6951479。这些新终局数据刚进入训练，不能凭此判定学习故障。

随后在cp9625与cp11000上固定全部前7回合的末25步，共175条完全相同历史样本：
经验池前9625条每字段字节hash一致，独立逐步折扣求和与n25回报一致；
没有bootstrap的终局窗口直接对比已保存尺度下的奖励目标，两个checkpoint均截断0。
第七回合25条TD绝对残差均值3.695133→.016740，normalizer分母6.278640→6.015730；
换回原reward尺度残差23.200407→.100701，说明新增1,375更新确实学到了这批失败罚分。
并非所有历史样本都改善：前6回合平均绝对残差.026902→.046366，后者最大2.903373。
不能将局部拟合改善等同于策略收敛。

cp11000当前actor动作Q比历史动作Q高：前6回合末段均值差2.898145、第七回合2.729928。
这是相同历史状态下critic估值的泛化/外推疑点，未执行替代动作的物理结果，不是已证实的
真实Q误差或失败因果关系。继续既定44k×2奖励对照；不因该疑点修改活动网络、扩大support、
放宽filter/gate或立刻同时叠加正则化。完整对照后再依据任务结果与估值证据决定下一实验。

两只读诊断本机CPU6/2GiB/swap0/CUDA0完成，峰1,291,501,568/1,280,163,840字节、
max/OOM均0；网络/RNG/归一化/checkpoint在各探针内均未改变，新增梯度/仿真0。
训练峰2,694,467,584字节、3GiB硬限、max/OOM/oom_kill/swap0；
收工MemoryCurrent2,293,448,704字节、GPU42°C/1439MiB。分析/归档CPU6/1GiB/swap0。
研究实现仍f788fcb，活动登记d37b16975a6f…及解释器/物理/MJB/48维/执行器/dt5e-5均保持。

报告、固定样本索引/逐样本估值/原数据hash、闭合日志、原生新轨迹和脚本已上传并重新核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-credit-followup-20261017/evidence.tar.gz`，
6,898,258字节，SHA `ec8e868bf6605583c85f40b8c7b34bbdb0fc775cd12d5441342e67aa291ba4de`。
本地缓存BENCH/outputs/rl_goal_stream_credit_followup_20261017；服务器只传输/归档/hash。
新增两回合完整原件/checkpoint独立归档重核如下，同主机共同根
`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-ff349b04467a9829252d900f/evidence.tar.gz`，267,262,273字节，
  SHA `0f9fe58a43b4ad034302d3b18e8ed10133e9f17529acc6103a5073d3c647b9f5`。
- `goal-stream-d929a5499e35e76fc29df4da/evidence.tar.gz`，267,502,587字节，
  SHA `fdc8c8246765cd2cefab96ecbdf626eadc87ec21b3b22f04df5b456c94a5022d`。

本轮无研究源码变更；诊断脚本和断言验证随证据保留。三进度文档diff检查后提交/push main。
全部失败/历史数据保留；四族均尚未收敛，最终acceptance和独立物理/filter重放未执行。
Goal保持active，继续健康control并核对occupancy自动接续。


## 2026-10-17 03:04 CST — 阻抗早期学习链路核验通过，完整回合仍停滞于carry

按sii-research-sync查询/fetch/read远端main `9f4b8747dfea25e66e1007941b32678d5e31d6de`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/进度；收工重读AGENTS。
Goal工具确认active。本轮观察同一worker PID2502235从6500推进至8250，协调器PID2502213保持；
观察器在两个全程学习回合闭合后正常退出，训练未停止。收工optimizer实测9228步/4229更新。
未重复派发、重启或修改活动source；occupancy处理组仍排队。

已封存分析覆盖8250条连续交互与3251条连续优化更新，全部优化指标有限。6个完整55秒
回合均physical_valid=true、Task/Strict0/6。前三回合warmup，第四混合，第五/六全程学习；
后两回合return −25.633716548/−25.106000635。六回合总体return均值−25.395017、
标准差.379481，仅为早期描述，失败平台不算收敛；不足96回合和两个完整32条件窗口。
step8250 temperature .007397509、actor loss−.3102534、critic loss8.802989。

本轮新增训练链路核验：checkpoint经验池action与控制器收到的5维raw_action逐项一致；
reward与final_reward在浮点精度内一致；terminal恰在6个闭合边界；parameter_actions与
parameter_trace一致；各回合reward分解/terminal/potential求和通过；cp6875/8250全部成员
hash通过。没有发现“优化更新但动作未连接”证据。这里是原生记录/文件一致性核对，
没有执行新的独立物理子步或action/filter重放，最终acceptance未运行。

两全程学习回合末10秒各250采样均处于carry waypoint20/28，无采样cursor变化。
重建目标残差0；radius/rejoin-plane readiness均0，rotation/speed readiness均250/250。
位置误差中位数12.769655/12.639503mm，冻结门槛12mm未改；该结果定位停滞，
不能独自证明根因或任务不可行。原生记录的rate-limit比例从warmup约.608–.623升至
两个学习回合均1.0，energy-limit均0；这不是因果结论，也不是放宽公共filter的依据。
两回合实际刚度均值约269.986/268.013、末段中位数189.317/178.695，合法范围150–1800，
无刚度硬上界导致不可行的证据。继续既定44k control/44k occupancy同seed对照；
处理组尚未训练，不跨奖励定义比较总return来宣称改善。

当前worker MemoryCurrent约2,351,947,776字节，峰2,656,804,864，硬限3GiB；
memory.max/OOM/oom_kill/swap均0，GPU43°C/1439MiB，磁盘余58,563,842,048字节。
CPU1/线程1、CUDA0/.125/UTD1、50GiB余量及全部冻结物理/gate/输入/执行器保持。
分析在airpig CPU6/1GiB/swap0完成；服务器仅归档/hash。训练源码仍f788fcb，
登记SHA `d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。

本轮报告、闭合日志、6回合原生诊断、观察与归档收据/脚本已独立归档，收工重新核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-early-learning-20261017/evidence.tar.gz`，
14,095,897字节，SHA `7888eaeb0accadfacce3b4f5f3d1ab7a6fc97fd72d18158ff12911786117283f`。
全部6个原始回合/checkpoint远端归档均在分析中重核大小/hash；新增ep4/5位于同主机、
共同根`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-8c0e92f011ff3f8c38099b4c/evidence.tar.gz`，266,364,943字节，
  SHA `1b60e738d486843d3073478c25413d53186dfb8a86c34b585a0185664f0dc4b4`。
- `goal-stream-92f5dd52122e58bc89788efb/evidence.tar.gz`，266,072,999字节，
  SHA `bcb1ce09417b792be0aafc5d9d3db368ff12fc8b55854ebd4c95e7f97f43ffda`。

本地报告缓存为BENCH/outputs/rl_goal_stream_early_learning_20261017。
两回合归档约35.5/37.4秒后原worker自动继续。历史数据未删除，全部失败收据保留。
本轮未改研究代码，不重复无关测试；文档diff检查后按约定提交/push main。
Direct/阻抗/导纳/VMC均尚无收敛证明；继续诊断和登记实验，Goal保持active。


## 2026-10-17 02:47 CST — 阻抗进入真实优化更新，旧checkpoint远端恢复验证通过

按sii-research-sync开工查询/fetch/read main `f788fcb9f74dfced22180ddd421184a5048249c8`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与Goal progress。
普通沙箱网络失败后宿主核验成功；收工再次fetch/查远端，两分支未前进，并重读AGENTS。
上一轮为真实启动/修复进展；本轮对已确认存活的同一PID2502235持续观察15分钟，
协调器PID2502213保持，未重启、重复派发或改活动源码/冻结协议。只读观察器已正常结束。

`rl_goal_stream_occupancy_20261017_v2/impedance_control`前四个回合已闭合到5500步/501更新：
repair_train_008/029/001/007均1375步/55秒、physical_valid=true、Task/Strict0/4。
return依次−25.493412/−26.067121/−25.072284/−24.997567；均值−25.407596、标准差.425116。
前三回合全部warmup，第四回合跨过5000步开始学习，不能把这些早期不同condition的return
或小方差当收敛/奖励改进。训练筛查为false：不足96个回合及两个完整32-condition窗口。
occupancy处理组仍排队，尚无本轮奖励对照结果；四类Goal均未证明收敛，最终acceptance未运行。

5500条交互按step1..5500连续、501条optimizer按step5000..5500/update1..501连续，
所有优化指标有限；四回合reward逐项/terminal/potential求和、AUDIT和checkpoint hash通过。
step5500的actor loss−.0813624、critic loss8.985741、temperature .00956446，均为训练诊断。
收工实测5750步/751更新，第五回合在途；worker峰2,621,403,136字节、3GiB硬限，
memory.max事件/OOM/oom_kill/swap均0，GPU43°C/1439MiB；free58,647,646,208字节。
CPU1/单线程、CUDA0/.125/UTD1、50GiB余量、44k×2预算和全部冻结输入/物理/gate保持。

真实第三/第四回合的工作副本管理已执行，最新cp4125/5500逐成员hash通过。
cp1375及2750的大本地工作副本在各自远端核验后释放；原始完整版本和失败收据保留远端。
实际下载cp1375所在包，在独立一次性/tmp目录重建其全部9个成员，再用原checkpoint
验证器检查episode_boundary、step及成员hash，全通过；没有重编译模型或写入活动训练目录。
验证后的重复下载/重建临时副本已清理，可由下述归档精确恢复。历史其他run未删除。
各回合归档耗时约26–43秒，成功后同一worker自动继续；这些文件核验不是独立物理/action重放。

本轮闭合日志、501次更新、reward分解、训练筛查、15分钟PID/steps观察、旧cp重建证据、
原始归档完整地址/hash索引和脚本已上传并核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-learning-start-20261017/evidence.tar.gz`，
1,095,611字节，SHA `2759b6956042f538b06ae924cfa04c050f2049222c7011321699968a4561cd88`。
新增ep1/2/3原始数据与各自checkpoint已由训练流程独立归档，并在本轮重核远端大小/SHA：
服务器主机`arm1@192.168.31.70`，共同根`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `goal-stream-fe6f4f3f05ceab4f6bb4c2cf/evidence.tar.gz`，193,801,251字节，
  SHA `2ee94fff6cefa084b816fb92b73cbb6422f551dfc3205e30418da6b059d294ef`。
- `goal-stream-0e675db8295f38c5685cc3b8/evidence.tar.gz`，194,069,554字节，
  SHA `662964169a614e6678b15c7d281b9fbb692ec431d897619c336252988883945d`。
- `goal-stream-43fd4f7a9d13c4e41b185c6a/evidence.tar.gz`，264,820,990字节，
  SHA `bc1650addd7572742cc81299614e6aced420584f6f804aeb461f3c9b6eb85afc`。

计算/重建/分析均在airpig，服务器仅文件/归档/hash。运行登记仍为d37b16975a6f…；
完整冻结source及Python依赖见上一轮归档，当前研究代码提交f788fcb未改动。
继续健康control到登记边界并核对处理组接续，再按完整数据决定四类下一阶段；Goal保持active。

## 2026-10-17 02:16 CST — Direct正则化对照关闭，新阻抗44k对照以预登记工作副本策略接续

开工查询/fetch并读取main `474f80d100c301b1c195716a6442f860de8e0a58`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS；普通沙箱fetch连接失败后，
宿主机fetch成功，两分支未前进。继续现有Goal，不重复创建或把阶段完成记成收敛。

Direct正则化组自然关闭32,262步/27,263更新，本段11,000次连续有限更新，8回合全部
1375步/55秒、physical_valid=true、Task/Strict0/8。return为−21.856347/−21.845347/
−21.867770/−21.850740/−21.849019/−21.782428/−21.832327/−21.775935，最终temperature
.006969546。峰值3GiB、memory.max505，OOM/oom_kill/swap0。全部8个checkpoint成员hash、
AUDIT、reward逐项复算通过。协调器2489803/worker2494519均自然退出，未重启健康进程。

控制组仍为30,984步/25,985更新，8尝试中7完整/6physical_valid、Task/Strict0/8。
严格相同condition和训练暴露的完整配对只有ep18/19：正则化reward分别低.016929/.159174；
RMSE分别59.631636→36.605086mm、486.685389→42.111425mm，穿透均略增。
从ep20开始，控制的97步提前失败使两组暴露不同，后续保留而不混作等预算配对。
全组物理有效率的差异是单seed训练观察，不能推出总体调参有效；两组都没有任务成功，
稳定的失败reward不是收敛。完整PAIR_REPORT及全部失败保留，最终acceptance未运行。

服务器独立归档已逐一核验大小/SHA，本机airpig计算，服务器仅文件传输/归档/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-regularized-close-20261017/evidence.tar.gz`，
1,893,048,841字节，SHA `87ab1ea077c1bbb9d48c2161aafaf3a2d646842bd44fd8677c11b5f592d1eeff`。
含正则化ep19–25原始轨迹/checkpoint（ep18已有上一轮独立归档）、完整11k日志、比较/筛查，
以及新存储源码快照、预检与失败记录。当前历史原始轨迹和checkpoint删除0。
仅在重核远端hash后释放3个/tmp重复tar，共4,183,705,513字节，CACHE_RELEASE收据保留恢复地址；
此前历史100文件删除拒绝未绕过。

新工具goal_prospective_storage_20261017仅接受全新rl_goal_stream_*目录，必须在任何job
输出/LAUNCH/execution出现前封存STORAGE_POLICY；旧run不可追认。每个完整或提前失败回合
先保存checkpoint，再用CPU6/1GiB/swap0辅助服务打包、逐成员核验、独立服务器目录发布并
核验最终hash，落盘恢复收据后才释放该新批次四个大临时文件。最新两个checkpoint留本地，
较早checkpoint也必须先核验各自远端副本才释放工作副本；小轨迹/日志/全部失败收据保留。
restore只写缺失的原始字节，拒绝覆盖不同文件，不重编译MJB。断网/hash不符/容量不足则
保留现有副本并在已保存checkpoint边界报告失败，不继续派发或创建重复进程。
该前瞻策略不授权删除历史数据，不修改活动旧训练源码。

109项Goal测试通过，其中8项新测试覆盖历史/在途/软链接拒绝、断网、篡改、释放中断恢复、
最近两checkpoint保留及精确恢复。全新合成文件完成真实服务器上传/下载/逐字节恢复，
不是仿真结果。首次CUDA预检因仅用AllowedCPUs而affinity检查不符，0更新失败保留在
rl_goal_stream_occupancy_20261017；改为显式taskset后使用独立_v2，不覆盖失败。
新CUDA预检2次丢弃更新通过、初始网络一致、reward normalizer和n25 terminal复算通过，
原cp hash未变；峰1,609,830,400字节、OOM0。

新批次本地根`outputs/rl_goal_stream_occupancy_20261017_v2`，登记SHA
`d37b16975a6f8e6408e951ec5bf69f14294b718dca7dc951ad56e9ba1c5e3aa6`。
保留已准备occupancy科学对照：两组fresh、同seed/配置/44,000步，差异仅
4*(1−measured payload phi)*dt/55训练附加成本；不把不同reward总值差当改进。
源码/预检重新冻结，单模拟器CPU1/单线程/3GiB/swap0、CUDA0/.125/UTD1、1M优化器日程、
物理/MJB/最终gate/canonical48/filter/执行器/dt5e-5保持。
根据原cp体积与工作副本上限，额外空间估计4,543,866,268字节（含2GiB余量）；
仍保留50GiB每回合保护。估计不是最坏情况保证。
18:15:32 UTC启动协调器`sii-rl-goal-stage-51973845a385.service`及control
`sii-rl-goal-03c22cf08c22.service`，实际PID2502213/2502235；第二组排队。
18:22:11 UTC首个repair_train_008闭合1375步/55秒，physical_valid=true、Task/Strict=false，
return−25.493412。仍是5000步warmup，更新0，不是学习有效性证据。1375条连续reward日志、
原生audit与cp1375全部hash通过。自动归档辅助服务28.924秒成功，四个新大工作副本释放后
第二回合接续；本地cp1375仍完整。首次真实原始归档为
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/goal-stream-a963f5309264e9830049c265/evidence.tar.gz`，
193,117,060字节，SHA `0cb14189dd735e55136ce8875431905b69ecc6c506d8e74110c52fde90b81709`。
另从服务器下载该包，核对全包及所有原始/模型成员hash一致，下载重复缓存核验后释放。
这只验证文件完整性和归档链路，不是独立物理重放；真实较早checkpoint释放仍待第3回合验证。
首回合运行证据/闭合日志/新工具和8项测试已独立归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stream-first-episode-20261017/evidence.tar.gz`，
340,777字节，SHA `0e4158cf7726e31f41f9ad032bb64ba62acafffb8a2679a1ddf68d41c14fb203`。
收工18:25 UTC观察1750步/0更新，第二回合在途；worker当前约1.89GB、峰1.98GB，
OOM/max/swap均0；GPU上次宿主观测40°C/1115MiB。本地free58,865,954,816字节。
按sii-research-sync收工重读AGENTS；两分支复核仍为开工SHA，保留无关未跟踪meeting文档。
四方法均未证明收敛，Goal保持active；没有统一acceptance或独立最终物理/action重放。

## 2026-10-17 01:43 CST — Direct控制组关闭，正则化组已接续并取得首个对应回合

开工实时查询/fetch/read main `6b069036afe2fcf2ab24e739a3465b8792c14cb4`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS；按sii-research-sync收工重读。
上一轮完成真实派发，本轮持续核对PID2489819直至正常退出，未中断健康worker或改活动源码/登记。
同一协调器2489803于17:35 UTC自动接续正则化worker2494519，无重复模拟器，Goal继续active。

Direct控制组有限段正常结束30,984步/25,985更新，新增9,722次连续有限更新。
八次尝试：7完整、6physical_valid、Task/Strict0/8；第三次ep20/repair_train_030为97步/3.88秒，
global_penetration_exceeded_2mm提前失败，return−41.398965；ep22/repair_train_024虽然完整，
physical_valid仍false，return−39.207510，原生训练收据RMSE560.324mm、穿透1.373658mm，阶段align。
其他六次return约−21.686至−21.865，仍是任务失败。余下预算不足容纳一个完整回合，
按既定边界停在30,984而非强行凑32,262；不是异常暂停。峰3GiB/max2190，OOM/oom_kill/swap0。
全8个checkpoint成员hash、AUDIT hash、reward逐步组件/求和与9,722条连续日志核验通过，
保留短回合与完整但物理失败回合。尚未完成两组比较，更不代表Direct收敛。

正则化组确认actor_bc_alpha=1、actor_regularization_migration=true，从同一原cp21262恢复，
其余agent/reward/seed/physics/48维/filter保持。首个1375步/55秒回合已闭合至cp22637，
对应控制组同一repair_train_021、同一21262→22637训练暴露，双方physical_valid=true、Task/Strict均false：
- reward：控制−21.839418，正则化−21.856347，差−.016929，没有提升。
- 原生训练RMSE：59.631636→36.605086mm；峰矩44.300316→37.913303Nm；
  峰速.346483→.334012m/s，穿透.134222→.135829mm，放置XY误差.259996→.183428m。
- 双方最终阶段仍approach。只是一对训练条件下的局部指标改善，不能推出整体调参有效、
  收敛或最终验收通过；策略在回合内继续更新。全部未对应、短回合与失败项仍在PAIR_REPORT中。

首个正则化回合1,375条连续有限更新、原checkpoint恢复hash、reward分项与新cp22637成员hash通过。
收工真实optimizer23,466步/18,467更新，temperature .002711194；
`sii-rl-goal-baf3c94bbf55.service` PID2494519 active，内存2,275,340,288字节，
max/OOM/swap0、GPU42°C/1438MiB。CPU1/单线程/3GiB/swap0/CUDA0/.125/UTD1不变。
第二回合在途，后续继续按原有限预算训练，不因单对局部改善提前选择策略或改协议。

本轮仅释放已重新核验服务器最终副本的/tmp阶段关闭重复tar，1,336,207,540字节；
原始轨迹/checkpoint删除0，CACHE_RELEASE.json保留精确恢复地址。历史100文件删除拒绝仍未绕过。
free61,909,770,240→63,245,971,456（释放时）；收工59,031,752,704字节，50GiB保护保持。

已核验服务器独立归档，本地/暂存/最终大小和SHA一致，服务器仅文件/hash：
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-control-close-20261016/evidence.tar.gz`，
  2,020,110,510字节，SHA `645294b33182491fe654a8c6a3991fe12964ab4c514c87e6213200c49ccb2983`。
  全控制组8尝试及cp、完整training/optimizer日志、原生失败收据、reward复算、
  pair/screen快照、缓存释放收据与本轮脚本。
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-first-pair-20261016T1742/evidence.tar.gz`，
  270,546,162字节，SHA `8b7dfe9bd2d352503724be6ff91a8a4bbbd9eada5fe8d7f01e3e9f402865d237`。
  正则化首个完整回合/cp22637/1375更新、首对比较、登记及脚本。之后新数据仅本地，待安全边界归档。

继续正则化组至登记边界，再依据全部证据比较两组。阻抗occupancy试验仍未派发、容量待解决。
四方法尚无可验证收敛，未进行统一acceptance或独立最终物理/action审计；Goal范围与完成标准不变。

## 2026-10-17 01:09 CST — 四族阶段关闭，Direct正则化在线对照已真实接续

开工实时查询/fetch/read main `f3b38923f05a2a318bb51805dae4fe9235934cec`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按sii-research-sync开工/收工重读AGENTS。
上一轮是归档进展；本轮持续核对同一VMC真实PID/步骤，直到协调器和worker均MainPID0/inactive，
再启动已准备的有限对照。没有重复训练、未修改活动/冻结源码或协议，Goal继续active。

VMC在17:03 UTC正常关闭23,375步/18,376更新；本段8回合全部1375步/55秒、physical_valid，
Task/Strict0/8。11,000条连续有限optimizer更新、逐回合reward求和、AUDIT与checkpoint成员hash通过。
八次return为−25.216931/−25.206806/−25.658431/−25.216424/−24.923777/−25.304485/−24.912112/−25.323514；
峰3GiB、memory.max2650为硬限回收事件，OOM/oom_kill/swap0。四族stage02_v2终态finite_stage_complete。
所选lineage的Direct/阻抗/导纳/VMC分别18/17/17/17闭合回合，联合Task AND Strict均0；
Direct完整14/physical13，另外三类各17完整/physical。均不足收敛所需回合和两个完整窗口，
不能把参数RL的稳定失败reward视为收敛，未运行最终acceptance。

新增只读VMC失败诊断覆盖捕获时前4个完整训练回合：末10秒均carry，
位置误差中位15.872/12.393/16.009/12.350mm，对应路径点17–18，仍高于12mm门槛；
参数速率限制tick占99.42%–100%、能量限制0。与其他参数方法的carry停滞表现相似，
不构成限速导致失败的因果证据，不放宽冻结限制；未做独立action/filter或物理重放。

本轮核验并释放5个明确/tmp重复传输tar，共2,613,878,367字节，服务器原包逐一重新核对大小/hash，
原始轨迹和checkpoint删除0。CACHE_RELEASE.json列出完整恢复地址；此前被拒绝的历史100文件操作未执行。
Direct容量估计使用最近10尝试平均1026.9步/尝试，预计两组22次尝试，包含剩余VMC、replay增长和2GiB余量：
free65,288,507,392，估计新增11,429,325,176，剩53,859,182,216字节，略高于50GiB保护。
这不是最坏情况保证；更短失败会增加checkpoint，逐回合磁盘检查不变。收工free62,677,520,384。

17:05:28 UTC按原登记启动Direct alpha0/1对照：
`sii-rl-goal-stage-210cab565c96.service` PID2489803，
控制组`sii-rl-goal-c05f012de695.service` PID2489819，正则化组尚排队。
准入可用内存7,941,910,528字节、GPU宿主核验36°C/15303MiB空闲，无旧RL worker；
单模拟器CPU1/单线程、3GiB/swap0、CUDA0/.125/UTD1保持。原cp21262、相同reward/seed，
每组最多新增11k至32262、1M优化日程，登记SHA `1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`不变。
启动证据核验21,590步/16,591更新、328次连续有限新更新，原checkpoint恢复hash一致；
收工optimizer已22,000步/17,001更新，max/OOM/swap0。尚无本轮完整回合收益结论，不能预称正则有效。

已核验共享（本地/暂存/最终大小与SHA一致，服务器仅存储/hash）：
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage02-close-20261016T1705/evidence.tar.gz`：
  1,336,207,540字节，SHA `3e5e76e408cc07d153282e95727aa546cd10e7539d04e7bf605eb821e4745775`。
  含VMC cp17875/19250/20625/22000/23375与对应5回合原始数据、完整11k日志、
  四族screen/终态、容量/缓存释放收据及前4回合诊断、全部本轮脚本。
- `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-actor-pair-launch-20261016T1708/evidence.tar.gz`：
  206,410字节，SHA `6655309c511f9111d9f4a42680ab511aa4f4ec0cda28e85f65b738798ec65af3`。
  含真实launch/恢复快照、登记和预检收据、328次连续新更新前缀及pair报告。后续训练原始数据仍本地，待闭合归档。

下一步继续真实Direct两组在线对照，按完整失败/成功与相同条件、训练暴露核对结果；
阻抗occupancy对照仍需容量，尚未派发。四方法最终收敛与统一测试仍未完成，不缩小Goal范围。

## 2026-10-17 00:38 CST — VMC真实推进与Direct在线对照接续核验

开工查询/fetch/read远端main `f9969c69a396b94c6663cd05c6a048a9cfc91b0b`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按sii-research-sync开工与收工重读AGENTS。
Goal工具确认active，承接原持续目标，不重复创建或启动worker。本轮无训练源码/协议修改。

当前协调器2447861/VMC2479454与其单个模拟器正常推进；核验期间optimizer从17,307/12,308推进到
17,858steps/12,859updates，temperature .003200021。execution快照17,750/12,751。
当前段已核验前三完整回合均1375步/55秒、physical_valid，Task/Strict0/3；
return依次−25.216931、−25.206806、−25.658431，不能据此声称reward收敛。
内存当前3,110,014,976、峰3,202,686,976字节，max/OOM/oom_kill/swap0，GPU39°C/1439MiB。
free62,989,017,088字节，50GiB保留线继续；不存在重复RL训练worker。

本机CPU6/1GiB/swap0归档helper核验cp16500、4125条连续有限更新和三个已结束回合reward求和、
AUDIT hash及checkpoint各成员hash。新增第3回合原始产物/cp16500、闭合日志前缀、现场快照、
登记与Direct既有预检记录核验共享至独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-progress-20261016T1640/evidence.tar.gz`，
269,013,117字节，SHA256 `475880a8c61e86cbf8f56819f79c778f76477fe0e476a30a3b5fb453205b00a6`。
本地/暂存/最终大小和hash一致；服务器仅存储/hash；16500之后数据待后续安全边界归档。
归档脚本随包保存，现场收据本地位于outputs/rl_goal_vmc_progress_20261016T1640。

已重新核验Direct alpha0/1有限在线对照登记、source/checkpoint和封存预检（未重复学习预检）；
登记SHA `1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`不变。
两组均从cp21262增加最多11k交互，尚无LAUNCH/execution。等待当前四族阶段全部闭合，
派发时仍须复核全局锁、磁盘/内存/GPU、截止；本次通过静态核验不等于派发准入或在线收益。
阻抗occupancy对照仍待存储容量，未移除历史原件、未绕过既有删除审批拒绝。
四方法均未证实收敛，未最终acceptance；Goal保持active，下一实质步骤为本段结束后的Direct在线对照。

## 2026-10-17 00:30 CST — 新奖励接续修复与真实CUDA保存恢复核验

开工实时查询/fetch/read main `40bc1546ae10ae2aa1ea02c1cad916c62f763049`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，依sii-research-sync开工/收工读AGENTS。
上一轮闭合导纳并找到错误放置失败类型，属于实际进展。当前协调器2447861/VMC2479454未重启；
归档快照15,500步/10,501更新，收工16,091步/11,092更新。已完成前2个新回合均1375步/55秒、
physical_valid、Task/Strict0/2，return−25.216931/−25.206806；cp13750/15125和2750条连续有限更新核验。
VMC约2.81GB/max/OOM/swap0、GPU39°C，free63,482,564,608字节，50GiB保护继续。

修复新reward已能独立试验但未完整接入四族选型/后续接续的缺口：
`goal_selected_continuation`识别occupancy双组，逐job核对并保留payload_occupancy_guidance，
记录原试验登记/hash来源，选回旧checkpoint时明确清除该job的新reward字段。
只按已登记trainer/helper的精确hash识别可选实现迁移，其余冻结源码仍须一致；
可与既有actor正则化实现共用同一冻结来源，不改active source或已准备pair。
`rl_goal_stage`保留后续来源和必要依赖，拒绝缺失来源/悄然删改reward；
`probe_goal_credit`在分配agent前核对checkpoint奖励定义，预检封存与再验证同时核对奖励身份。
新fresh pair准备清除上一段的occupancy来源，防止错误继承。

101项Goal unittest通过，新增5项覆盖选择后再接续、独立冻结入口、fresh历史计数、源码/奖励篡改、
活动pair拒绝、显式旧模型重选及预检封存；修改收据hash也不能绕过奖励身份检查。
合成48回合失败历史保持联合成功0，不因fixture阶段结束判为收敛。

真实本机CPU6/2GiB/swap0/CUDA0预检通过：使用1375条既有训练replay重算已登记reward，
丢弃一次更新后保存专用PROBE_ONLY检查点，再重载并核验4网络/优化器/RNG、归一化统计/计数、
raw replay与下一次抽样完全一致，重载后另一次丢弃更新有限；原cp23375及三份登记hash不变。
已登记四族/Direct正则化/occupancy源码兼容检查通过，删除或改reward权重被拒绝。
峰2,137,206,784字节、max/OOM0。该检查点只有replay诊断用途，不是候选策略、没有在线训练或新增仿真；
未来实际选中checkpoint仍必须完成四方法逐一预检，不能用本次fixture代替。

源码/新增测试、真实CUDA保存恢复收据及诊断检查点、VMC前2完整回合/cp与2750连续日志已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-continuation-20261016T1630/evidence.tar.gz`，
666,344,069字节，SHA256 `f47bb1fc7ca8626479b4f7d06c466ed2dc2eb7541a0d904ead5d8a2eab79836f`，
本地/暂存/最终大小和hash一致，VMC checkpoint成员hash核验通过。预检source保留当时4个新测试版本，
delivery/source另收录最终第5个封存检查测试；运行时代码未在预检之后变化。服务器仅文件/hash。
VMC cp16500及之后的新产物不在本包，待后续安全边界归档。

Goal保持active，四方法仍未证实收敛、未运行最终acceptance。继续VMC至已登记边界，再按现有协议和资源检查
推进Direct正则化对照；occupancy配对尚未派发。历史100原文件删除仍待明确授权，本轮未删除原件或checkpoint。

## 2026-10-17 00:15 CST — 导纳阶段关闭、VMC接续与错误放置诊断

开工实时查询/fetch/read main `fd1b5660c87a88477507b306941105a307525987`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按sii-research-sync开工/收工读AGENTS。
上一轮有实际工具修复/归档进展；本轮保留所有失败、原件和活动source，历史100文件移除仍未获明确批准，未执行。

导纳正常关闭23,375步/18,376更新，本段11,000条连续有限更新、8完整55秒physical_valid回合、Task/Strict0/8，
末return−25.351177、temperature .001980882；cp23375成员hash和逐回合reward求和核验。
协调器2447861自动接续VMC2479454（sii-rl-goal-f97f0a2da6b1），收工实测12,978步/7,979更新；
无重复worker。导纳最终峰3GiB/max2369、OOM/swap0；VMC当前约2.52GB/max/OOM/swap0、GPU38°C，
free64,913,981,440字节，50GiB保护保持。四方法当前选中lineage闭合回合数18/17/17/9、联合成功均0；
这是训练screen快照，未证实收敛、未最终acceptance，VMC本段首回合在途。

新增8阻抗/6导纳完整训练回合的动作和reward诊断：原始动作std约.51–.66，几乎每tick至少一维受参数速率限制，
能量限制0。不能据此判定零控制能力或放宽限速。7阻抗carry末段位置误差中位12.69–15.83mm，
6导纳为14.12–17.03mm；阻抗ep16却已进入release/retreat，物块目标XY误差258.172mm、release_supported=false。
首次carry-only诊断因此报错，原脚本/失败收据保留，修正适用范围后全量保留14回合，峰506,691,584字节/OOM0。
固定轨迹occupancy重算对该错误放置额外成本−3.097749，其他7个阻抗carry为−2.0065…−2.0506；
支持已登记在线候选的检验理由，不代表新策略收益。详见`RL_PARAMETER_FAILURE_DIAGNOSIS_20261017.md`。

诊断/源码/失败收据、导纳ep13–15和cp19250/20625/22000核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-parameter-diagnosis-20261016T1615/evidence.tar.gz`，
852,248,130字节，SHA `2e724776968fb1d0dd32a4a512a895892b20a51c71934430093cf0ce70a08dbb`。
导纳最终回合/cp23375、完整日志和四族screen补包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-close-20261016T1615/evidence.tar.gz`，
278,175,559字节，SHA `d2ebefcd27119b779e8cf6b8c3b9c35203f091f82d7d6eadaf3a57fee2a219e0`；
两包本地/暂存/最终一致，服务器仅文件/hash。VMC新数据仍仅本地、待安全回合边界归档。
Direct正则化/阻抗occupancy两组准备协议保持未派发；继续VMC，当前四族阶段闭合和资源准入后才开后续有限对照。
Goal active；本轮为真实训练推进和新失败类型证据，不把阶段结束或shadow成本当收敛。

## 2026-10-16 23:58 CST — 导纳持续推进、归档核验提速与存储保留审批

开工实时核对main `50af442b2b75ff6351eff48114aae54b6a11d7d2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及两分支日志，开工/收工重读AGENTS。
持续Goal保持active；协调器2447861和导纳2467890未重启。15:58 UTC execution为20,250步/15,251更新，
optimizer已到20,287步/15,288更新，temperature .002585187；真实推进。当前段5个结束回合均完整55秒、
physical_valid，Task/Strict0/5，return依次−25.493493、−25.264967、−25.422910、−25.312598、−25.247658；
第6回合在途，VMC尚待本段接续。导纳峰3GiB、memory.max483、OOM/oom_kill/swap0，GPU38°C；
本地free67,053,481,984字节，保持50GiB保护。Direct/阻抗仅有限段结束，四方法均未证实收敛，未最终acceptance。

离线归档核验helper改为一次顺序解压扫描，仍扫描全尾部并拒绝重复/链接/缺失/大小或hash不符成员；
10项既有保留/恢复unittest通过。只读盘点首次目录层级识别错误得到0候选，修正后重新核验25个已结束历史回合；
两份盘点收据均保留，未据错误结果删除数据。已生成25份逐回合计划，精确列出100文件共3,655,768,123字节及
原件inode/mtime/hash、服务器包/member/hash；另记915个checkpoint及其他文件的保留前hash。
自动审批拒绝批量本地移除：AGENTS规定“历史数据不自动迁移或删除”，本批缺少明确删除授权。
拒绝发生在进程创建之前，无evict服务、无RESULT/删除journal；随后100原件全部重新hash确认在本地。
`outputs/rl_goal_storage_20261016T1550_v2/OFFLINE_RETENTION/REVIEW.md`是可审阅方案，
READY.json链接精确清单，BLOCKED.json保留拒绝证据；等待用户批准，不能拆分或绕过拒绝。

不受阻的缓存清理已完成：重新核验服务器和本地hash/大小/身份后，仅释放16份重复/tmp传输包，
6,630,480,093字节，free61,298,081,792→67,928,477,696；原始轨迹/checkpoint删除0。
收据TRANSFER_CACHE_RELEASE_20261016T1555.json保存逐文件恢复地址；T1252缓存实际映射T1116归档，
查证后才释放。后续经批准的离线保留/恢复须先重新下载相应已移除缓存，不能跳过归档核验。

源码、测试、盘点/计划/拒绝/缓存收据和导纳ep11/12原始回合、cp16500/17875及截至17875的5500条连续有限更新
已核验到独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-storage-delivery-20261016T1600/evidence.tar.gz`，
548,097,492字节，SHA256 `4c5c1cdcd3d3232ac2017ff9e9fcc57432f65e1071e08f74d3980e42f9836d0a`，
本地/暂存/最终一致；逐回合reward和、checkpoint成员hash已验证。服务器仅文件/hash。
cp19250及其后新产物仍仅本地、待下一安全边界归档。已准备Direct正则化pair和阻抗occupancy pair均未派发；
继续现有导纳→VMC，四族阶段闭合并满足资源准入后才开展后续登记对照。预检不代表在线改善或收敛。

## 23:40 CST：occupancy对照已登记并通过真实预检，未派发

开工main `a63ff29a290ce36fd73f1c9954bf695c9610e4e8`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实时查询/fetch/read，开工/收工读AGENTS。
上一轮实际闭合阻抗并诊断奖励，属于进展。原协调器2447861/导纳2467890保持active；
归档快照15,500步/10,501更新，收工16,250步/11,251更新，新增ep9/10各完整55秒、physical_valid、Task/Strict失败。
return−25.4934929291/−25.2649668678，cp13750/15125和2750条训练/更新连续有限、逐回合回报和核验。
导纳峰3GiB、memory.max1、OOM/swap0；GPU38°C。没有重启健康worker、没有重复模拟器。

新根`outputs/rl_goal_impedance_occupancy_20261016`，登记
`b3cb37f91cb713f4878fc7a0e79ae506a846feef159236baa72dd74f557caf1d`；派发截止2026-10-17T15:34:37.666477Z。
原payload_shaping reward的fresh control与额外weight4 measured-payload occupancy成本的fresh处理组，
相同seed/初始化/超参数/物理/条件/学习日程，两组各44,000交互。完整回合情况下32条件循环/39,001次更新；
短失败保持并可能增加结束回合数，不能把预算当收敛。历史cp23375仅用于诊断replay预检，不被当作fresh对照初始模型。
本试验不替换当前四族lineage；Direct actor正则化pair原登记/hash保持，尚未运行。

trainer只有登记payload_occupancy_guidance才加入新reward，加入后再写raw replay和消费normalizer，
早失败补最坏剩余折扣成本。改变/去除该reward不能静默恢复旧checkpoint。公共物理/gate/48维/filter未改。
pilot验证双组仅reward项不同，44000预算只适用于本类型；从选型四族新建fresh pair时清掉旧selected_lineages，
避免将两组误当四族恢复。dispatch继续强制前置四方法闭合；报告验证实际处理配置，screen双组独立且four_family_scope=false。
96项Goal unittest通过，含独立快照入口/预算/seed/混合处理/缺失配置/分解测试；尚未补齐此新reward的跨source选型接续，
在实际训练结果支持采用时必须先明确核验该兼容链，不放宽现有source一致性检查。

CPU6/2GiB/swap0/CUDA0真实预检：1375条旧训练replay分别生成control与处理reward，
两组4网络/优化器初始化序列化hash一致，源checkpoint hash不变；agent初始计数为0，预检未保存模型/未仿真。
独立递推G和批量矩核验normalizer的count/mean/variance/G/G_r_max；control mean−1.35227406、variance .607512116，
处理mean−2.19579339、variance1.103416443，均1375 reward样本；这些是归一化统计，不是新策略回报。
末25步replay回报与独立折扣求和一致，两组各一次丢弃更新有限；峰1,516,871,680字节、max/OOM/swap0。
实际从冻结snapshot隔离导入验证两组trainer准入；提前launch被前置四族仍running拒绝，未创建LAUNCH或execution。
新pair report/screen都为not_started；预检通过不证明在线收益或任务成功。

服务器已核验`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-ready-20261016T1540/evidence.tar.gz`，
547,562,429字节，SHA `766cab7086f18f6305632f316daa1f06a0695491438d01b0d7ccdd25f62a2fc7`。
含完整新pair/source/parameter/登记/预检/报告、交付工具/测试、阻抗8回合reward完整收据、导纳ep9/10原始回合及cp；
训练在airpig，服务器仅文件存储和hash。本轮仍无最终acceptance，四方法均未证实收敛。

容量估算：每完整回合raw约160.9MB、cp约153.1MB，64回合约20,098,866,176字节，
仅是两个导纳样本的规划估计，不含checkpoint增长/短失败/缓存，不是派发许可。
当前空闲不足以同时容纳新对照及50GiB保护区，继续归档并使用已验证的可恢复离线保留流程后再派发。
已重新核验远端并移除三个明确重复传输tar（T1455 lineage/T1520 diagnosis/T1525 impedance-close），
释放2,164,485,381字节，free59,785,506,816→61,949,943,808；原始回合和checkpoint全部留本地。
释放收据`TRANSFER_CACHE_RELEASE_20261016T1540.json`单独同步同服务器目录，可按收据下载对应evidence.tar.gz恢复缓存。
下一步继续当前导纳→VMC、准备后续Direct在线对照及occupancy试验的存储余量；Goal active。

## 23:25 CST：阻抗闭合并交接导纳；局部误差加权假设修正

实时核对main `fe07aa91d57935765dd3bee0e6d45a9fe66f533f`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与两分支日志，开工/收工读AGENTS。Goal active。
stage02_v2阻抗于15:21:35Z结束23,375步/18,376更新，新增11,000条更新连续有限，逐回合reward和核验。
8个完整55秒回合、physical_valid8/8、Task且Strict0/8；return依次−25.729180/−27.340559/
−26.037487/−25.273970/−26.085219/−26.521273/−25.033403/−25.320493，末temperature .001968527。
峰值3GiB，memory.max3175、OOM/swap0。协调器2447861自动接续导纳2467890，
单模拟器/CPU1/thread1/3GiB/swap0/UTD1、学习CUDA0保持；已观测12,500步/7,501更新、GPU38°C。
导纳当前峰约2.55GB/max/OOM/swap0；VMC仍排队。主机已有swap约2GiB，不代表本批worker发生swap。

cp19250只读critic诊断1332个固定训练样本，较早/最新末端窗口signed TD均值.01290561/.31250385，
当前actorQ减历史动作Q .08137958/−.01916685，clipped mass近0；没有梯度、模型写入或仿真，checkpoint/RNG/normalizer不变。
最新末端训练曝光有限，不用critic估值充当真实Q。探针CPU6/2GiB，峰1,251,819,520字节、OOM0。

对ep9–13做reward/动作分解：末10秒位置误差中位12.6864/12.8307/15.8256/12.9607/13.2199mm，
均在冻结12mm推进门槛外，旋转/速度采样均在阈值内。但ep11游标18→19有推进，不写成全部停滞。
动作非零且变化、能量限制触发行0；误差成本−.1089…−.1185、峰矩成本−1.891…−3.955，任务−20/时间−1。
折扣potential shaping −.5602385287565恰等于−5×初始phi，是设计性质，不是bug。
99次路径点切换中97次局部误差成本上跳；原尺度.12/权重4的跳变中位.0644247，
旧权重40为.6442473，假设尺度.012/权重4为.9257038。它们是25Hz相邻采样成本，非实际物理积分reward。
因此暂不采用收紧局部误差尺度；这种修改可能更强地惩罚切换到下一个目标。

新增prospective helper `goal_payload_occupancy_reward_20261016.py`：
成本4×(1−已有reward-only measured payload phi)×dt/55，早失败补最坏折扣尾项；不新增actor输入或成功标签。
这是明确的训练目标变更，不是potential shaping。scope/配置/非有限值/早失败补偿/恢复拒绝测试通过，全部93项Goal测试通过。
同5条训练轨迹shadow额外成本−2.006519/−2.015082/−2.050623/−2.018314/−2.027786，
同99次切换采样成本变化中位−.0001302209、30次正跳变（物理phi仍可能波动），无局部目标重置项。
仅诊断：helper未接入trainer、未登记或部署处理、未修改replay/normalizer。phi包含手物距离项，真正任务成功时也不保证为1；
可能带来新的偏好，必须经过独立有限配对和奖励一致的fresh replay/normalizer或完整核验的迁移，不能直接加到当前worker。

服务器证据`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-payload-diagnosis-20261016T1520/evidence.tar.gz`，
1,088,411,543字节，SHA `dc7f72746fd2c72f8371dade4b5292b0fe9586846d9a09ee64f365a8e3e8fa31`，本地/暂存/最终hash一致。
含4份诊断、实际脚本/helper/tests快照、cp17875/19250/20625/22000及对应4原始回合，9625条累计连续更新。
最后cp23375/回合及完整11000条训练/更新的补包267,249,973字节，SHA
`0d6c9510a533779f87676215e7079e0c92d450b27f879ec69327cd095c043f86`，已核验同服务器runs/main下
`rl-goal-impedance-stage02-close-20261016T1525/evidence.tar.gz`，本地/暂存/最终大小及hash一致。
归档helper CPU6/1GiB，无新增仿真。未删除失败或传输缓存；free约61GB、保留50GiB。
继续原四族训练；Direct alpha0/1 pair仍未派发，须等待本阶段全部结束和新资源检查。
收工导纳13,250步/8,251更新、峰2,654,740,480字节，max/OOM/swap0；free60,999,487,488字节。
当前四方法均未收敛，不做最终acceptance，也不以此有限段结束或93项测试代替成功。

## 23:00 CST：分支可接续与统计隔离完成，阻抗仍在真实学习

开工main `e19fedae55647bc71bfad01df66d25b36a93104b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read；开工/收工读AGENTS，上一轮为实质进展。
原stage02_v2协调器2447861、阻抗2455377持续active。归档快照17,000交互/12,001更新，
收工18,250交互/13,251更新；新增4个完整55秒回合均physical_valid，但Task/Strict全失败。
return为−25.729180、−27.340559、−26.037487、−25.273970。前三个checkpoint13750/15125/16500
及4125条连续有限更新/逐回合reward和/hash已核验，第四个cp17875及其原始轨迹仍仅本地待归档。
最新峰值3GiB、memory.max事件287、OOM/swap0；没有重启或改动活动冻结source。

`goal_selected_continuation`现在支持已完成的actor正则化pair：必须两组均闭合，显式选型，
四方法来源各自绑定登记/执行/协议/checkpoint hash，参数实现跟随实际选中分支。
alpha1策略后续恢复使用普通严格加载，不重复alpha0→1迁移；`prepare_next`复制并验证方法专属参数快照。
迁移trainer必须等于原登记pair快照，归一化来源只用于核对这一已登记的迁移入口，其余物理和reward源码仍逐hash一致。
显式选择原alpha0来源时必须重写alpha元数据，避免沿用四族模板中的alpha1标记。
当前没有实际采用任何pair分支，pair和正在运行的stage快照完全未动。

配对报告支持新same-reward alpha0/1试验，只在完整回合身份及训练步窗口一致时比较指标和return；
要求实际reward完整定义/prior/config/恢复checkpoint匹配。短失败、不完整、无效或缺少对应回合全部保留。
收敛screen可查看两组但不会把两组Direct标成四族全部候选；选型后的统计跟随真实分支。
两组的前处理训练历史另存完整源execution及checkpoint hash，不混入试验起点后的固定配置窗口；
处理后的失败仍全部计入分母，试验前失败仍可追溯，恢复的optimizer和交互计数并未清零。
原96回合/两个32条件窗口/稳定回报且每窗Task AND Strict≥90%的筛选要求不变。

90项Goal unittest通过：合成闭合pair→四族alpha1选型→再接续、隔离snapshot导入、
错误alpha/参数/训练源码/reward拒绝、未结束pair不允许选型、改回原alpha0不保留旧标记、历史失败保留。
这不是实际alpha1后续回合验证；真实在线pair仍两组not_started，无LAUNCH/execution。
真实四族screen保留Direct18闭合/14完整/13物理有效/0joint；阻抗快照12闭合/12完整/0joint及1在途；
导纳与VMC各9历史闭合/0joint，本阶段仍排队。所有方法training_candidate=false，最终acceptance未运行。

本轮证据根`outputs/rl_goal_regularized_lineage_tools_20261016`包含pair未开始报告/screen、四族screen、
监视及前三个阻抗cp/完整原始回合证据。服务器已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-regularized-lineage-20261016T1455/`。
`evidence.tar.gz`808,823,865字节，SHA256 `1553ff87d7c62ad6f5c0e18e6b95eb905504debb36b9c1ebcdb7019602182122`。
打包后进一步收紧完整reward定义比较、补充回归测试；最终代码见同目录`source_final.tar.gz`，
21,964字节，SHA256 `d31acdcb7af0d0e0d53fa381b68b9288cf1cbad34939d8a95fc8333efa1bc98f`。
代码按未提交内容快照标识，不冒称原base commit已含新实现；本地/服务器最终hash一致，服务器只归档。

重复传输缓存`/tmp/rl-goal-direct-credit-regularization-20261016T1415.tar.gz`和
`/tmp/rl-goal-bc-online-ready-20261016T1440.tar.gz`经重新核验本地/远端大小/hash后移除，共2,479,027,859字节。
对应服务器包仍完整，原始回合和checkpoint未删除；下载各自服务器`evidence.tar.gz`可恢复缓存。
释放收据`TRANSFER_CACHE_RELEASE_20261016T1500.json`保留本地并同步服务器；free61.18→63.66GB，50GiB保护保持。
下一步继续当前阻抗→导纳→VMC，完成后重检磁盘和前置闭合状态再启动alpha0/1在线对照。
本轮没有修改奖励、actor输入、物理/gate或活动训练快照，没有重复worker；Goal active。

## 22:40 CST：Direct闭合，actor正则化在线接续已验证但尚未派发

开工实时查询/fetch/read main `610cdbc5a94369b6ac3c9e2ed8358dcf7212cef5`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，开工/收工读AGENTS。Goal继续active。
stage02_v2 Direct于14:29:45Z结束21,262交互/16,263更新，新增10,269次交互/更新连续有限。
本段10回合，7完整55秒、3因穿透>2mm短终止，physical_valid6/10，Task且Strict0/10。
episode12–17 return依次−21.670135、−21.675998、−21.702363、−21.742310、−41.427858、−21.657791；
其中episode16仅191步/7.64秒，其余完整。最后temperature .002418325；失败reward平台不是收敛。
Direct峰值3,221,225,472字节，memory.max事件1330、OOM/swap0。协调器2447861自动转至阻抗worker2455377，
观测14,000交互/9,001更新；首个新完整回合13750 checkpoint、return−25.729180、physical_valid=true、Task/Strict=false。
阻抗峰值2,309,435,392字节，max/OOM/swap0。导纳/VMC本阶段仍排队，已有历史cp12375不等于本阶段已训练。

新实验根`outputs/rl_goal_actor_regularization_online_20261016`，登记SHA
`1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`。
两组共享最新闭合Direct cp21262，原始模型/optimizer/replay/normalizer/RNG保留，训练seed及reward相同。
control alpha0、处理alpha1，仅使用上游SimbaV2已有actor replay-action正则项；各新增最多11000交互至32262，
1M优化日程保持。旧离线256更新探针来自cp12821；它只提供候选动机，不能当成cp21262在线效果。
处理组`parameter_bc1`独立快照，加载只允许指定路径和全部hash绑定的alpha0→1迁移；
后续alpha1保存模型走普通严格恢复。所有其他配置、物理、MJB、gate、48维/filter/执行器及dt5e-5不变。

86项Goal unittest通过，覆盖额外配置变更/错误cp或hash拒绝、alpha1普通重载、配对参数/证据篡改、
前置运行/错误登记禁止launch/run、独立快照导入。实际隔离导入和两组trainer准入也通过。
两组真实CUDA replay预检各一次丢弃更新，全部4个网络/优化器完整序列化hash与源相同；
归一化数组、计数、JAX RNG精确相同，21262原始replay恢复、末25步终止求和检查通过，源cp hash未变。
control/处理峰值1,328,312,320/1,564,688,384字节，CPU6/3GiB/swap0、OOM/max0。
额外处理组保存/重新加载无仿真/无更新探针通过，网络/优化器、normalizer、RNG/计数均保留，
峰值1,633,832,960字节/2GiB、OOM0。`disposable_roundtrip_model`仅测试产物，未部署、未替换正式cp。
实际提前launch被拒绝且没有LAUNCH/execution；两组已seal预检，必须等待前置四族阶段全闭合。
随后重新核算空间（目前free约62.93GB，保护50GiB）再派发，不用本阶段旧空间估算替代新pair预算。

尾6个Direct原始回合/cp15571/16946/18321/19696/19887/21262、完整连续日志、pair源码/测试/登记/
预检/roundtrip已打包，本地`/tmp/rl-goal-bc-online-ready-20261016T1440.tar.gz`，
1,611,100,590字节，SHA256 `da29a35e1835a90b48e7a684bb09f79da6e750a413a6844b55f4fc799533b806`。
已核验共享：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-bc-online-ready-20261016T1440/evidence.tar.gz`，
本地/服务器暂存/最终目录大小及hash一致，服务器仅文件归档。本轮未删除任何数据，传输缓存保留。
收工阻抗14,750步/9,751更新，服务持续active、OOM/swap0；新阻抗轨迹/cp仍仅本地待同步。
此轮完成可审计修复候选准备，不是正则化闭环收益证明。在线结果后若采用alpha1，需补齐选型接续与
分支收敛统计支持。四族均未证实收敛，最终acceptance仍未运行。

## 22:15 CST：Direct动作偏移证据与上游正则化候选对照

开工main `cc193663d626ad6e9f935fa54994ed45c78186ac`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read，开工/收工读AGENTS。
上一轮为实质进展。原stage02_v2协调器2447861、Direct2447875确认存活且持续推进：
归档快照16250交互/11251更新，新增5闭合（episode8–12），3完整、physical_valid2/5、Task且Strict0/5。
前4闭合cp11333/11446/12821/14196逐文件与tar成员hash核验；10994–14196的3203条新训练记录、
update5995–9197连续有限，逐回合reward和一致，含两个穿透短失败与一个完整物理失败，不删失败。
episode11/12 return−21.666452/−21.670135仍任务失败，不能称reward收敛；第5回合/cp15571仅本地待归档。

对cp12821运行已有只读`diagnose_goal_rl_credit`，固定1024均匀索引+各回合末25步去重1239样本，
无梯度/仿真/模型写回，normalizer、RNG和checkpoint不变。CPU6/2GiB/swap0，实测峰985,444,352字节。

|样本组|样本数|历史动作Q均值|投影目标均值|绝对TD残差均值|当前动作Q−历史动作Q|
|---|---:|---:|---:|---:|---:|
|较早回合末25步|250|−2.168825|−2.168796|.005644|.681024|
|最新回合末25步|25|.653371|−1.803346|2.456717|−.001081|
|距离末端至少25步|964|.066354|.094637|.044654|.030762|

较早末端当前/历史动作差绝对值均值.784079，当前饱和维比例17.94%、历史3.71%。
总体裁剪概率质量均值.0000248693（约.00249%），不支持支持集截断是主要解释。
最新末端窗口刚获得终止信息、更新曝光不足，不与较早窗口混成拟合结论；soft-Q不是历史MC或真实最优Q。
证据提示动作分布偏移及当前策略估值问题值得处理，并不单独证明学习代码bug。

新增有限探针`tools/probe_goal_actor_regularization_20261016.py`，根
`outputs/rl_goal_actor_regularization_probe_20261016/`含REGISTRATION、alpha_0/1、COMPARISON。
从同cp12821恢复完整模型/优化器/normalizer/RNG，实际使用上游SimbaV2已有
`actor_loss += alpha * stop_gradient(mean(abs(Q))) * mean((sampled_action-replay_action)^2)`。
只把内存actor_bc_alpha由0改为1；对照仍0，两组同seed/256×256训练索引和1024诊断索引。
未修改任何活动source/参数/reward、未保存探针模型、未启动模拟器，训练数据允许与诊断样本重叠。
运行前两个安全边界测试与全部81项Goal测试通过；实际两组均完成256次有限更新，cp hashes/normalizer计数不变。

|1024训练replay诊断样本，256更新后|alpha0|alpha1|
|---|---:|---:|
|策略与历史动作MSE|.557015|.230609|
|策略动作RMS|.589605|.247419|
|abs(action)>.95维度比例|4.8131%|.1116%|
|当前动作Q−历史动作Q|.036300|.024182|

两组初始诊断最大数值差2.81482935e-5，源checkpoint/计数/索引相同，但不同CUDA进程不声称逐位一致。
warmup和learned子组MSE差分别−.277936/−.358249。结果支持正则化确实限制动作偏移，但也可能
主要收缩随机动作幅度；没有闭环安全、推进或成功证据，不能直接当最终算法或验收结果。
两进程CPU6/2GiB/swap0/CUDA0/.125依次运行，峰值1,316,466,688/1,318,391,808字节，OOM/max0。
主训练持续CPU1单模拟器/thread1/3GiB/swap0/UTD1，峰值2,785,837,056、OOM/max0，没有重启或改变快照。

前4新增原始回合/4cp、完整边界学习日志、只读诊断、候选探针源码/测试/登记/全部结果已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-credit-regularization-20261016T1415/evidence.tar.gz`，
867,927,269字节，SHA256 `a2af18129ff12927befd61ee26f0f48c07ddd985051271d2175f2ad3f92dd2e8`。
本地重复传输缓存`/tmp/rl-goal-direct-credit-regularization-20261016T1415.tar.gz`本轮仍保留。
候选探针源SHA256 `f9a92fe5e2f21653fa616a3a8071d3c842e9aae8c2c21225f14ccd205ee3c99b`，
包内基于cc19366但尚未提交状态如实标注；服务器仅存储/hash。
下一步继续四族当前有限阶段，按完整证据登记在线正则化接续/对照并验证配置迁移，不更改运行中模型；
同步新增回合并复核50GiB保留线。Goal active，四族无可验证收敛，未统一acceptance或最终独立审计。

## 22:05 CST：完整Direct对照无成功，独立快照bug修复后四族实际接续

开工main `ce97607603593cae53e899c9b14ca6a5c5d9fedd`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，开工/收工读AGENTS。
Direct tracking11000步/6001连续有限更新、8完整、physical_valid7/8、Task且Strict0/8；
回报−23.647310/−23.654229/−23.824334/−24.231452/−24.633473/−25.232520/−39.191037/−24.135839。
最后4cp6875/8250/9625/11000及全部训练步序/更新序/回报和已核验。完整配对3热身/1混合/3学习；
学习RMSE中位差+241.535270mm、峰矩+4.074654Nm、峰速−.134038m/s、穿透−.015579mm、放置XY−2.261262mm。
control末短回合仍在报告，不能凑成第4个完整学习配对。双方都失败，额外tracking权重未证明收益。

本次选择保持未加tracking目标：Direct接fresh-n25 control cp10993（保留其短安全失败），参数三族
接既有GPU验证cp12375，不再fresh重置。每族新增11k，Direct限21993、其他限23375，优化日程1M。
第一准备目录`outputs/rl_goal_selected_20261016_stage02`运行时缺pilot校验模块，协调器failed、无trainer输出；
旧快照未改，新增DISPATCH_FAILURE_20261016T1400.json含journal。根因是base四族source不含pilot模块，
预检的sys.path同时留着checkout/tools，掩盖了依赖缺失。原测试夹具也错误地预装模块。
修复`goal_selected_continuation`复制pilot校验器，`probe_goal_credit`替换而非叠加入口目录；
真实缺依赖夹具与禁止checkout回退测试先出现2失败，再全79项Goal测试通过。

当前唯一训练根`outputs/rl_goal_selected_20261016_stage02_v2`，登记SHA
`2f7401d5ed96c7ab3f70f62890de078d95399fa0b6b6eea94a0ad3d89c0c3b18`。
独立Python -I导入/核验及四族实际CUDA replay末窗口/丢弃更新预检全部通过，原cp hash保持。
13:59:23Z新协调器`sii-rl-goal-stage-51b5e2c65202` PID2447861，Direct
`sii-rl-goal-2ea514600ebc` PID2447875；首实际新更新10994/5995，归档快照11333/6334，优化尾11369/6370。
CPU1/thread1/3GiB/swap0/UTD1、CUDA0/.125，物理/gate/actor48/filter/执行器/dt5e-5未改。
接续episode8/9分别340/113步（13.60/4.52秒），return−41.499027/−41.402112，均approach，
穿透2.120478/2.027631mm触发global_penetration_exceeded_2mm；cp11333/11446及原始数据仅本地待归档。
这些失败照常计入，后续episode10已派发；绝不能把工作流恢复当训练质量修复。

真实分支screen最初包含Direct8闭合+在途、三参数族各9历史闭合，全部joint0，均非training_candidate；
随后新短失败须继续累积。14:01资源快照peak2,441,695,232字节，max/oom/swap均0；持续查真实更新和失败趋势。
存储估算以32完整回合、最大161.69MB轨迹/152.09MB cp、每新增步4KiB增长余量、备用cp和2GiB暂存计算，
增量13,827,378,359字节，free68,724,199,424，估剩54,896,821,065，高于50GiB；短失败会增加cp数量，
不把估算当硬上界，继续逐回合磁盘保护和归档管理。已核验后移除1,014,664,550字节重复tar缓存，
原始数据和checkpoint留本地，服务器包完整可恢复。旧阻抗64文件离线保留状态不变。

已核验服务器主机arm1@192.168.31.70，根`/home/arm1/sii_shared/SII_compliance/runs/main/`：

- `rl-goal-direct-pair-selected-20261016T1350/evidence.tar.gz`：1,014,664,550字节，
  SHA256 `4926680f57691f57adb2845fcb33882f8dd0f9e0a2cd5648b1333ecbb4cb64c2`，tracking尾4原始回合/cp和完整配对。
- `rl-goal-selected-snapshot-fix-20261016T1400/evidence.tar.gz`：3,259,135字节，
  SHA256 `c471f8b7da9a223097010736e7db974ee2dd2d59225175ad3610f923d778d0df`，首次失败journal、修复源/测试、
  v2完整source/参数/登记/四预检/launch/真实推进/screen及缓存恢复地址。候选修复按内容hash标识。

服务器仅存储/hash。继续现有worker，完成Direct后核对三参数族顺序接续；下一轮优先归档新短失败并复核容量。
Goal active，四方法均未证明收敛，未做最终统一acceptance或独立最终审计。

## 21:35 CST：逐方法来源接续可用，tracking进入学习且首配对仍失败

开工main `ee494302b9eda843782204cc6d1f758477aa81fd`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，开工/收工读AGENTS；上一轮为进展。
原tracking worker2432993/协调器2424012继续推进，归档快照7000交互/2001更新，5完整55秒，Task/Strict0/5。
前4return−23.6473104406/−23.6542294571/−23.8243342856/−24.2314521733；cp2750/4125/5500逐文件
与tar成员hash通过，前5500交互序号/回合reward和一致，step5000–5500的501条更新连续有限，
actor/critic相对热身hash改变。首末critic loss9.23200989→8.95285416、temperature .010000→.009595596。
这些仅证明学习链路，非收敛。memory peak3GiB/max512、OOM0/swap0；原进程/活动source未改。

本轮补齐从有限pilot接续到四方法的实现：`tools/goal_selected_continuation_20261016.py`。
入口为`--base <已闭合四族root> --selection <选择JSON> --root <独立新root>`，默认每族新增11000；
可显式传`--interactions-per-family 22000|33000|44000`，仍每族累计≤1M/24小时派发保护/原资源。
选择JSON含decision以及methods：以四族base的job名为键，每项root、job、rationale；每族必须显式指定。
来源可以是已闭合四族stage或已闭合两臂pilot，但整个来源根必须finite_stage_complete且无active。
不能在Direct control已结束、tracking仍运行时提前接纳整个pair。检查最终cp与协调器/训练收据一致，
锁定实际reward/variant/hp/seed/controller/tracking配置，所有非派发/预检源码及完整parameter manifest相同。
运行主机/解释器/runtime/父协议/优化日程/资源/收敛标准必须一致；不会刷新物理/学习算法或重新初始化。
准备出的每个job从其自己的checkpoint恢复model/optimizer/replay/normalizer/RNG，四族仍须各自执行
现有丢弃更新预检并seal，然后正常锁与资源准入launch。下一普通prepare-next只沿新阶段末cp接续，
不把原selection指向的旧cp继续拿来用。不自动把pilot当四族完成，不按不同reward总值选优。

`screen_goal_rl_convergence_20261016.py`支持逐方法分支来源以及之后的正常stage：
只累积选中方法自身的连续episode/step历史，检查每段协议与执行hash、奖励fingerprint和实际resumed_from；
未选臂保留在其原收据但不混入返回窗口，选中历史中的失败不丢弃。96回合、双32条件窗口、
两窗≥90%Task且Strict和既定稳定性标准完全不变，screen仍不等同最终acceptance。
78项Goal unittest通过：新增6项接续测试和3项分支统计测试，覆盖复制快照在独立进程中import+verify、
实际trainer参数准入、四族独立cp/目标保持、拒绝running/缺族/跨族/篡改/源码不符/超预算、
下一阶段不重用旧cp、失败计数和不混奖励历史。未对正在运行的快照应用新代码。

真实兼容检查在CPU6/512MiB/swap0进行：GPU四族、阻抗pair、Direct pair的受保护源差异均为空，
资源与完整参数实现相同；GPU四cp和阻抗两cp均通过实际hash核验；Direct仍running，closed-source入口正确拒绝。
收据为`SELECTED_CONTINUATION_COMPATIBILITY_20261016T1330.json`。尚无真实选择文件/新stage/preflight/launch，
要等完整Direct结果后才能决定来源；存储容量仍须独立安排，不因代码支持44k就直接派发。

当前配对3热身/1混合/1全学习。热身原生指标完全一致；混合tracking−control RMSE+11.298344mm、
放置XY+71.680544mm。第1全学习RMSE+241.535270mm、峰矩+10.129753Nm、峰速−.134038m/s、
穿透−.015579mm、放置XY−2.261262mm，双方仍失败；单对非改善结论，也不等于长期无效证明。
完整早期失败仍在报告；不同定义reward总值不排名，control末回合安全失败不被删掉。

tracking第2–4原始回合/cp2750/4125/5500、前5500学习日志、配对/兼容收据、候选代码/测试已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-selection-20261016T1335/evidence.tar.gz`
648,113,768字节，SHA256 `9c2e566639765d54913205185058758431faaa1a450ced8536878259fef3d8d6`。
第5回合/cp6875仍本地待同步。包内候选代码以内容hash绑定，不冒充当前训练source或干净提交。
Goal active，继续tracking剩余回合和完整对照，再进行有依据的精确接续；四方法仍无可验证收敛，未最终验收。

## 21:15 CST：Direct control闭合且末回合安全失败，tracking奖励已实际写入replay

开工main `8eaccb4fc0762ced11b4e90f3537e2ddd73ff087`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，开工/收工读取AGENTS；上一轮为进展。
control于13:03:20Z正常结束有限预算，实际10993步/5994更新、8闭合但仅7完整55秒，
physical_valid7/8、Task/Strict0/8。末回合在54.72秒因柱体与fr3_link6碰撞穿透3.930900mm中止，
abort_reason=global_penetration_exceeded_2mm；step_budget表示余量不足再派完整回合，不表示任务成功。
最后4个全学习回合return−21.765686/−21.699330/−21.695607/−41.679094，均停在approach；
对应native RMSE382.939/285.229/480.001/721.447mm。前三个较高return不能覆盖末回合安全失败，
不同条件的跨回合数值不能作为因果对照。配对报告保留短回合，不能凑成4个完整学习配对。
5994条step5000–10993/update1–5994连续有限，10993交互序号/8回合reward求和正确；
cp6875/8250/9625/10993源与归档成员hash核验，最终cp保存实际10993交互/5994更新。

原协调器2424012自动接续tracking，13:03:26Z开始，worker2432993、unit sii-rl-goal-185982a6fdbe。
归档快照2250步/0更新，首回合1375步/55秒完整、return−23.6473104406、Task/Strict失败。
首回合每步奖励均满足实际final_reward=control−4*bounded_error_cost，新增累计−.388026116762；
五个非reward replay数组完全一致、实际replay.reward与记录一致，初始模型四组和obs_norm hash一致。
这是预热期奖励接入证据，不是学习效果或收敛证据；活动快照/奖励权重/物理/gate均保持登记值。
control最终memory peak3GiB/max1428，OOM0/swap0；tracking当前仍3GiB/swap0，未重复启动模拟器。

离线保留实质落地：已完成阻抗pair的16回合共64文件、2,294,939,982字节转为服务器持久保留。
范围只含此前工具允许的三个大型物理npz及rollout.mjb。9个独立最终归档包重新校验大小/hash，
全部tar成员字节与本地原件一致后才执行；先全目标预验证，再逐文件写持久日志后移除。
16个回合全部失败仍保留；144个checkpoint文件hash未变，动作/小收据/25与250Hz诊断留本地。
离线后重新report(old)的完整arms/comparison与PAIR_COMPLETE原报告完全一致；两最终cp11000再次通过。
原阻抗三个服务均确认inactive。处理后free72,665,419,776字节，此值早于本轮新归档包生成。
9个本轮新下载传输包经远端/本地复核后清理，不删除服务器包；恢复时显式传新的下载archive路径。
恢复索引为阻抗root的`OFFLINE_RETENTION_20261016T1300/`：REGISTRATION、READY、16个JSON计划、
逐回合removal.jsonl、RESULT和RESTORE.md。本目录也随本轮包上服务器；先恢复所需大文件再做物理审计。
不能把已离线原件当作永远不需恢复，也不能因缺失而跳过最终检查。

本轮Direct control最后4回合/4cp和完整日志、tracking首回合/cp1375、实际奖励检查、全部离线清单/脚本已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-control-close-retention-20261016T1310/evidence.tar.gz`
1,198,940,149字节，SHA256 `4d38896ac3492a6ddbf0993dab9482fd30172a08e21cf2b954afcc83297677eb`。
加此前分包已覆盖control全部8回合/cp；tracking第2及后续回合仍本地待闭合归档。
当前cp实测约148–151MB，单轨迹约146–159MB。44k每族32回合×4，仅按当前大小已约39GB，
尚不含replay增长/暂存包，超过当前50GiB保护线以上余量；需按安全分阶段保留安排，不能直接套用44k。
继续tracking既定完整对照，后续合并所选各族checkpoint须显式登记来源、训练目标和接续预检；
当前四族prepare-next不能直接把两个pilot当完整四族前序。Goal active，尚无收敛/最终acceptance结论。

## 20:55 CST：Direct越过热身真实更新，归档恢复实测通过

开工main `f29614ca5b75b525b067513339f1d6386cf003fe`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，开工/收工读取AGENTS。
原Direct trainer2424017/协调器2424012继续；12:52归档快照7000交互/2001更新，5完整55秒，
physical_valid5/5、Task/Strict0/5。前四return−23.2592843239/−23.2647493885/
−23.4519602502/−23.3572739030，第五−21.7656862410；不同训练条件，不能当作收敛趋势。
cp2750/4125/5500源与tar成员hash一致；5500条交互序号/回合reward求和正确，
cp5500保存501次step5000–5500连续有限更新，actor/critic相对热身文件hash改变。
首末critic loss9.23203087→8.94854164、temperature .010000→.009595258，仅证明学习链路。
快照memory current3,074,641,920/peak3,221,225,472、max383、OOM0/swap0；GPU44°C/1436MiB。
保持3GiB限制与50GiB磁盘保护，未重复启动或改活动快照。

新增`tools/offline_goal_episode_20261016.py`的plan/evict/restore：仅已完成训练臂的闭合Goal回合，
移除白名单为research_substeps.npz、independent_contacts.npz、rollout_metrics/substep_metrics.npz、
rollout.mjb；checkpoint/动作/25与250Hz轨迹/小收据留本地，失败与成功一视同仁。
plan记录原件inode/device/mtime/size/SHA和登记/执行/audit身份，核验服务器独立最终目录tar及各成员；
evict再次核验全部目标/远端后写fsync日志再逐文件移除；restore不用tar.extract，按白名单独占落盘，
原始MJB逐字节恢复、已有相同文件允许、不同内容拒绝覆盖，链接/重复成员/活跃臂等拒绝。
10项安全/恢复测试及全部69项Goal unittest通过。现有trainer接续只依赖checkpoint及冻结运行源，
未发现上述四个回合大文件的恢复依赖；独立审计使用前仍须恢复原始文件，不把缺失文件忽略掉。

真实演练选择已结束阻抗control的`episode_00004_repair_train_002`：
从服务器重新下载既有`rl-goal-pair-report-20261016T1116/evidence.tar.gz`，大小266,677,855，
SHA256 `6c16b1005c956b60e11604f29b1c7d8e9deb199096c2efa7a0fbb2709c193093`，再次核验远端。
4文件144,291,728字节先移除再恢复；33个回合文件全部hash一致、cp6875的9文件hash一致。
最终离线文件0，当前没有任何回合原始文件留在缺失状态。收据位于阻抗root：
`OFFLINE_ROUNDTRIP_PLAN_20261016T1252.json`、`OFFLINE_ROUNDTRIP_REMOVAL_20261016T1252.jsonl`、
`OFFLINE_ROUNDTRIP_RESULT_20261016T1252.json`。将来恢复使用工具restore模式并传对应receipt/archive；
本次restore可重复核对，但恢复后inode改变，不能复用旧plan再次evict，必须重新plan。
尚未登记/执行批量离线，不将这次零净释放演练说成长期空间问题已彻底解决。

本轮第2–4原始回合、cp2750/4125/5500、学习日志、工具/测试、实测恢复证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-learning-offline-20261016T1255/evidence.tar.gz`
647,988,847字节，SHA256 `7d96b43f7bc0b9edd606baef6d4297f1e7a5deec30872f9f871a850f7458adea`。
服务器仅存储/hash，第5回合/cp6875尚本地待同步。继续当前Direct control→tracking完整对照，
之后根据证据登记较长四族接续与保留方案；不因短pilot失败再反复重置学习。四族未证明收敛，未最终验收。

## 20:40 CST：Direct3250热身，较长接续预算实现与缓存回收

开工main `cda3106f8155620f7895894bc965f5fb14bbc215`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工读取；上一轮为进展。
Direct原trainer2424017/协调器2424012未重启，12:38:27Z3250步/0更新，符合5000热身；
两完整55秒return−23.2592843239/−23.2647493885，physical_valid2/2、Task/Strict0/2。
首cp1375源与tar成员hash核验，保存1375交互/0更新；前1375条日志序号/回报和一致。
当前current2,467,450,880/peak2,536,906,752字节、max/OOM0、swap0，第三回合在途。

后续阶段原固定11k预算已扩展为显式有限登记，prepare-next可传`--interactions-per-family`
11000/22000/33000/44000，默认不变；22k以上须finite_continuation_budget字段并匹配四族总量。
保留完整四族前序/独立cp恢复/1M总上限/24h派发保护/资源与奖励/优化日程，pilot和GPU预检不扩容。
测试检查旧source与各族cp保持、实际trainer准入、遗漏登记和超过1M等拒绝路径，59项Goal unittest通过。
当前活动Direct源hash仍匹配冻结登记，未应用新代码；没有准备或派发较长阶段，也未选择奖励胜者。
44k对应32个完整55秒回合的交互量；短回合/失败仍按真实记录，不据此推断条件覆盖或收敛。
待Direct完整对照后按结果和存储空间选择接续长度，避免反复fresh热身取代持续训练。

清理14个明确列出的重复/tmp传输包，check/apply均核验远端大小/SHA256，逐项校验本地
普通文件/所有者/单硬链接/inode/mtime/hash，先落日志后移除，逻辑回收5,461,537,291字节。
结果free73,903,075,328字节；只删除可由服务器完全恢复的传输缓存，原始实验/轨迹/cp/失败全部保留。
恢复scp命令见TRANSFER_CACHE_CHECK_20261016T1235.json，移除日志/结果同步保存。
历史归档服务器路径仍有效，但本次列出的14个旧/tmp tar缓存已不存在；勿按旧记录重复使用本地缓存。
50GiB保护线不变，长期四族各1M仍需要增量归档和明确离线保留，不把缓存回收称为完整存储方案。

首原始回合/cp、1375步日志、缓存核验/移除/恢复收据、新预算源码/测试及复现脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-first-storage-20261016T1240/evidence.tar.gz`
189,850,878字节，SHA256 `7c74a262eb65e4121a5ab0b5b4fcc0e663dd3af71d1e2689f858d7914b29b6ad`。
incoming及最终目录大小/hash通过，服务器仅存储/hash。第二回合/cp2750仍本地待同步。
Goal active，继续Direct既定control→tracking及后续四族接续；尚无收敛/最终验收证据。

## 20:28 CST：阻抗完整对照结束，Direct v2已实际推进

开工main `536e6c941d08c5a2a9841a3fd47687a42cf688b7`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工读取，上一轮为进展。
观察原tracker2413986/协调器2400799至12:23:40Z均inactive，根收据finite_stage_complete。
两组各11000交互/6001更新、8完整55秒、physical_valid8/8、Task/Strict0/8，training_complete=false。
tracking返回依次−26.512956/−27.083870/−26.077475/−26.004701/−26.520930/−26.288968/
−27.095333/−27.058253。6001条更新连续有限、最终cp9625/11000源和tar成员hash通过。

完整配对3热身/1混合/4全学习。全学习中位差tracking−control：RMSE−.100881mm、
峰矩+.296778Nm、峰速+.002600m/s、穿透+.006392mm、放置XY+2.718305mm。
后两配对改变此前仅2对的放置误差方向；没有任务成功，不能将奖励权重40当作已验证修复。
单seed短训练对照也不足以证明长期无效；不同定义return不作排名，未修改活动源码或最终gate。

确认active_workers为空、全局锁可获取之后，接续已登记且预检通过的Direct v2，未重复启动：
`outputs/rl_goal_direct_tracking_gpu_20261016_v2`，登记SHA
`109bf618dcc7f34e8d5d74d2940ab6704787bdabcf7a6c7c619890b53c9e4e06`。
协调器`sii-rl-goal-stage-bb18f8d17dfd`，control worker`sii-rl-goal-edf740b23fa9`/PID2424017；
实际协议from scratch、seed2026101421、task_safety/n25/UTD1/CUDA0，canonical48不变。
control及额外weight4处理组各11k预算，1M优化日程、5000热身。12:25:11Z真实250步，
12:27:21Z750步/0更新、首回合在途。后续处理组由此协调器接续；未启动额外模拟器。

tracking最后两原始回合/cp、全日志/配对、交接观察与源码、Direct登记/冻结源/实际协议已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-pair-close-direct-launch-20261016T1226/evidence.tar.gz`
540,752,690字节，SHA256 `77e18a30d230fd041a5042cc1165e996c6d3abf0b8567876ee30fa2f9d2ab436`。
incoming及最终路径大小/hash一致。tracking全部8回合和checkpoint连同此前独立包均已归档，本地仍保留。
只读登记摘要CLI误用可选字段强索引导致KeyError，改.get后读取成功；实际输入/预检已通过，失败记录在包内。
tracking最终peak3GiB、max1358、OOM0/swap0；Direct current约1.72GB、max/OOM0/swap0，
GPU最近45°C/1102MiB。继续Direct对照，再依据完整证据登记后续训练；有限pilot不能替代足量训练。
Goal active，四方法均未证明收敛，未运行统一acceptance或最终独立审计。

## 20:15 CST：两对全学习结果仍失败，继续处理组

开工main `619c3f8f2b94aa4a8a05b50d2f9558288356cf93`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工读取；上一轮为进展。
原trainer2413986与协调器2400799继续，观察服务核对同一live PID直到cp8250完成。
12:14:49Z已9000步/4001更新、6完整55秒，physical_valid6/6、Task/Strict0/6，第七回合在途。
新闭合return−26.5209300959/−26.2889681344。cp6875/8250源与tar成员hash、8250步日志完整性、
3251条更新序号及有限指标、逐回合reward和均通过；cp8250温度.00739581、critic loss8.77130。

配对warmup3/mixed1/learned2，两个learned的tracking−control中位差：RMSE−.100881mm，
放置XY−1.274364mm，峰矩+.296778Nm，峰速+.006372m/s，穿透+.015202mm。
表现发生变化但没有全面改善或任务通过；单seed在线训练有限pilot，不能称收敛或充分因果证据。
两个处理回合末10秒均carry20/28不变，位置误差分别12.706–12.822、12.552–12.615mm；
各250采样姿态/速度满足，参数变化且energy_scale1。

首个全学习回合的既有250Hz servo遥测只读诊断：末10秒tracking名义qdot范数中位.06707rad/s，
等效请求与限幅后范数中位均.32869rad/s，最大分量差1.63e-19；对应control .06652/.46008rad/s。
tracking弹簧wrench中位约[4.552,−.294,−9.008]N，control约[6.696,−.494,−12.513]N。
因此该段不是名义指令归零或等效速度限幅截断；不能据此排除其他限制/接触，或断言根因已修复。
该诊断不运行物理/动作重放或最终acceptance，不改活动快照、gate或控制接口。

两原始回合/cp6875/8250、截至8250训练/更新日志、配对/carry/servo诊断与复现源已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learned-20261016T1212/evidence.tar.gz`
534,465,416字节，SHA256 `aa19ceb33724a597a141fd8b10074635bb7da0af6d4fdfaeb0c741871188f5fb`。
incoming及最终目录大小/hash通过。首报告服务因systemd默认cwd导致找不到相对脚本exit2；
独立v2显式设置工作目录后通过，失败收据保留，未影响训练。
内存current3,190,861,824/peak3,221,225,472字节、max371、OOM0/swap0；GPU最近44°C/1443MiB。
继续剩余两回合、完整配对，再启动已预检Direct v2；Goal active，四方法尚无收敛证据。

## 20:05 CST：tracking学习链路核验通过，尚无有效改善证据

查询/fetch/read main `5633e19fc60307f28c7cc1e4e0ad02f9fa31a45d`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取AGENTS；Goal保持active。
同一trainer2413986/协调器2400799运行，12:03Z execution6500步/1501更新，第五回合在途。
首次GPU更新出现短暂编译等待后真实推进，未重启或重复启动模拟器。

cp2750/4125/5500逐文件与tar成员hash通过；cp5500保存5500交互/501更新。
actor/critic文件相较热身改变，optimizer step5000–5500/update1–501连续且全部有限；
5500条训练记录连续、逐回合reward求和一致。critic loss首末9.230323→8.983398，
temperature .010000→.00956565，actor entropy −12.029792→3.148023，仅作学习链路证据。
四个完整55秒return −26.512956/−27.083870/−26.077475/−26.004701，physical_valid4/4、Task/Strict0/4。

5500边界配对报告：warmup3对的原生指标完全一致；mixed1对的tracking−control
RMSE −0.00004431954mm，放置XY误差+0.00001767408m，峰矩/峰速/穿透差均0；learned0对。
当前差异极小，不证明处理改善，不比较不同奖励定义的return总分；保留失败/在途收据。
继续完成已登记11k处理组后再分析全学习配对，不改活动源码或提前运行最终acceptance。

第2–4原始回合、cp2750/4125/5500、5500步训练日志/501更新、登记/配对/核验及复现脚本已归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-20261016T1200/evidence.tar.gz`
653,909,672字节，SHA256 `9d26c72d6443420a51ffd36aaddf1b53c621e204de963b2bafc76633b0cf09ac`。
incoming与发布后的最终目录均核验hash/大小，服务器只存储/hash；本地原件未删除。
6500步资源快照current2,822,778,880/peak3,116,003,328字节，max/OOM0、swap0；
12:03 systemd current2,847,494,144字节，GPU44°C/1433MiB。冻结约束与3GiB保护不变。
后续回合仍本地待边界归档。Direct v2已预检但未派发，等待阻抗配对结束且全局锁释放。
四方法均尚无收敛证据；有限pilot结束不等于Goal完成。

## 19:43 CST：首次实际配对验证新增奖励已写入replay

开工main `40eb81b3cce1d5ae3dd65c06acb2ea816539225c`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工重读，上一轮为进展。
原trainer2413986持续推进，11:42:36Z tracking2500步/0更新（5000热身），第二回合在途；
首个repair_train_008完整55秒1375步、return−26.512955713、physical_valid=true、Task/Strict=false。

与control同条件首回合匹配，rollout SHA256均
`7370775a5d2ca67f55ff14b8adf73a046f7fbc2ace16fe47c3f006da77ba1f9e`，parameter_actions均
`de68f112eca4d2e413f77250a930ce76113c8b08b5e61166ed0436a5d788aa76`。
两组cp1375 hash核验通过，actor/critic/target_critic/temperature保存文件一致，updates均0。
1375个区间原有reward分项完全相同，独立按control bounded_error_cost计算新增−36成本，
与tracking记录逐项及总和匹配：总−1.019543795131，区间reward差最大误差3.423e-16，
完整回合的额外早停补偿0。没有直接把两个不同目标的return差当作策略优劣。

直接读取两组checkpoint replay：observation/action/terminated/truncated/next_observation
五数组完全一致；reward分别匹配对应训练日志，最大float32误差3.789e-7/7.922e-7，
二者reward差也匹配额外成本。该证据排除本首回合“只改配置而未将奖励送入replay”的问题；
仍属未学习热身，不证明学习更好、CPU/GPU学习等价或最终收敛。
奖励分解及配对报告通过，当前warmup1对、learned0对，Task/Strict均失败；没有新仿真或最终审计。

tracking首回合原始轨迹/cp1375、完整奖励快照/分解、配对及replay核验、复现脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-first-20261016T1142/evidence.tar.gz`
193,524,455字节，SHA256 `ebc3e5cb64c190426c45684c0b376d5939f5588080bde14d3ae6d39d9a3b6a03`。
cp源文件和tar成员hash通过，本机/远端整体hash/大小一致；control对应文件已有先前独立包。
当前tracking current/peak2,283,864,064字节、OOM/max0、swap0，GPU43°C/约1115MiB。
第二回合及后续checkpoint仍本地待闭合归档。继续tracking到11k及公平配对，随后Direct v2；
不修改活动源码、物理或gate。Goal active，四类尚未证明收敛，最终acceptance未运行。

## 19:35 CST：control完成11k，tracking由原协调器接续

开工main `de07e3e3d06a241fce2cf24a4c76367a2ac399b7`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工重读，上一轮为进展。
本轮观察服务每45秒核对原control PID2400811、协调器2400799和cgroup，最终11:31:29确认
control inactive、tracking active PID2413986，观察服务exit0。没有因触顶或观察等待而重启训练。

control正常完成11000步/6001更新，8个完整55秒回合，physical_valid8/8、Task/Strict0/8。
return依次−25.493411918、−26.067120701、−25.072283800、−24.997562068、−25.682297583、
−25.389612508、−26.209323906、−26.290249859。只是有限对照段结束，training_complete=false，
不是收敛；不得把失败reward窄幅波动当作完成Goal。6001条真实更新序号与steps完整连续、指标有限，
cp8250/9625/11000及tar成员hash通过，协调器收据的最终cp一致。

原协调器在11:30:45.516800Z启动impedance_tracking，服务`sii-rl-goal-7f55e47acca6.service`，
trainer2413986；实际命令无resume-checkpoint，实际协议from scratch，跟踪总权重4+36=40。
11:35:24Z已750步/0更新，仍处5000热身；同seed2026101421、原条件顺序/n25/UTD1/1M日程，
本段11000交互预算、3GiB/swap0/CUDA0/单模拟器不变。current/peak1,716,035,584字节、OOM0/swap0。
处理组首完整回合尚未结束，当前没有匹配的处理效果结论；不比较两个定义不同的reward总分。

control第五、第六回合末10秒只读定位：两者carry cursor20/28固定，250采样的姿态/速度都满足，
位置误差分别12.628–12.819mm、12.674–12.730mm，energy_scale=1且参数变化。
仍支持已登记跟踪成本对照，不能单凭路点停滞证明实现bug或权重修复成功。
control最终内存current2,566,287,360/peak3,221,225,472字节，max1828，OOM/oom_kill0、swap0。
触顶期间anon约1.69GB、file约1.48GB、inactive_file约1.30GB；保持保护后自然闭合。

末三回合原始轨迹/cp8250/9625/11000、完整training/optimizer日志、carry诊断、配对报告、
全部观察/交接收据及复现脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-control-close-20261016T1132/evidence.tar.gz`
803,419,415字节，SHA256 `16f0082c6802fa746cb1e2a83342746458166d65821add63bee32d3e8a8cf0ae`。
此前5回合分别见之前独立包，至此control8回合及全部checkpoint均已核验保全；未删除本地原件。
服务器只存储/hash。tracking新轨迹仍本地待完整边界归档，Direct v2未派发；Goal active、无最终验收。

## 19:16 CST：配对报告可用，control首个全学习回合仍失败

开工main `9456b51a798462f30328b93231dd1cab35b3caf9`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工重读，上一轮为进展。
原trainer2400811仍active，8000步/3001更新，五个完整回合physical_valid5/5、Task/Strict0/5。
第五回合repair_train_002从5500到6875，全程使用学习策略，return−25.682297583，末stage=carry；
原生审计RMSE23.28643mm、峰矩36.09985Nm、峰速.379328m/s、穿透.150319mm。不同条件不能
直接和热身回合作因果比较，当前仍未证明奖励改善或收敛。

新增`tools/report_goal_tracking_pair_20261016.py`，用于本次阻抗及后续Direct配对。
先核验登记/源/预检，执行协议须匹配注册hash、seed、奖励/指导项、UTD、n25、预算、热身与条件顺序。
对相同episode+condition、相同步数窗口的完整回合，列出原生物理指标差并按热身/混合/学习分组。
缺失、在途、损坏、短回合与失败均保留；失败完整回合仍入比较，Task AND Strict才计成功，
不对不同目标的reward总分求差/排名；不运行新仿真、不宣称收敛或最终acceptance。
6项测试覆盖错配、短/在途、失败分母、单Task成功、hash篡改、曝光/奖励错配与分组。
最初pytest命令不可用，按仓库使用unittest，6项通过且实际报告exit0。训练环境未安装/改动。
真实报告5个闭合、1个在途、0个无效闭合；tracking未启动、0个可比较配对，当前不作处理效果结论。

工具/测试/报告两版本、第五回合原始数据/cp6875、内存及复现/测试收据已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-pair-report-20261016T1116/evidence.tar.gz`
266,677,855字节，SHA256 `6c16b1005c956b60e11604f29b1c7d8e9deb199096c2efa7a0fbb2709c193093`。
cp文件/tar成员及远端整体hash均通过；服务器仅存储/hash，前四回合在之前独立包，第六回合仍本地。

内存11:13 anon1,617,608,704/file1,460,359,168/inactive_file966,529,024字节，包含较多文件缓存。
11:15后memory.events.max9→85，OOM/oom_kill仍0、swap0，实际到8000步仍正常推进。
最新MemoryCurrent3,220,987,904，保留3GiB保护，不调限/重启；max触顶并非OOM，但需继续跟踪。
当前control按11k预算继续，tracking随后fresh启动；Direct v2保持已预检未派发。Goal active。

## 19:07 CST：阻抗跨过热身，真实更新及5500 checkpoint核验通过

本轮main `1f59dbfc810e210fe39ae72bc6fd1310f8517859`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工重读。
上一轮为进展；原trainer2400811/协调器2400799继续，观察服务每30秒检查原PID active，
有600秒时限，不凭状态文件重新启动。5000步开始更新，5500边界11:04:24Z闭合，核验服务exit0。

cp4125/5500及归档tar内成员hash通过，前者updates0，后者interactions5500/updates501。
actor/critic保存文件hash均改变，优化日志501条step5000–5500/update1–501连续、指标全部有限；
critic loss首末9.23035→8.98545，temperature .01000→.00956482，actor entropy −12.02979→3.14322。
这些是早期更新观测，不能据此判定策略改善或收敛。5500条训练日志完整、四回合reward求和一致。
第四回合repair_train_007完整55秒，return−24.997562068、physical_valid=true、Task/Strict=false。
累计四回合physical_valid4/4、Task/Strict0/4，全部失败保留；第五回合repair_train_002已启动。
11:06:39Z execution6000步/1001更新，资源current2,820,227,072、peak2,923,593,728字节，
OOM/max0、swap0；GPU44°C/1448MiB。没有第二模拟器，冻结source/配置未改。

第三/第四回合原始轨迹、cp4125/5500、截至5500步训练与更新日志、检查收据/脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-learning-20261016T1105/evidence.tar.gz`
459,990,965字节，SHA256 `c7b7c8a674282783bc8c056ebfdf69d2dfad617768efd949cd77ed32938c3d60`。
本机/远端hash与大小一致，服务器仅存储/hash。前两个回合在前两独立包，不重复打包。
后续日志/第五回合仍本地。control继续至11k后应自动接续fresh tracking组；Direct v2预检已通过、
仍未启动，须等当前配对结束和全局仿真锁释放。Goal active，四类尚未收敛，不提前最终验收。

## 18:58 CST：原阻抗control已完成三个热身回合，Goal继续

开工main `bf1c5904620059a5ff6a1f404b038944f48f73e9`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，两次读取AGENTS。
原协调器2400799/trainer2400811保持运行，唯一模拟器推进，未新建Goal/重启训练或更改冻结快照。
10:56:57Z到4125步/0更新，第四回合repair_train_007随后启动。5000步之前仍为登记热身，
三回合return−25.493411918、−26.067120701、−25.072283800，physical_valid3/3、Task/Strict0/3。
不能将热身reward小幅波动或无梯度更新解释为收敛/故障。下一重点是5000步更新和5500完整边界。
4125边界current1,895,649,280、peak2,617,638,912字节，OOM/max0、swap0，GPU43°C/约1117MiB。

第二回合repair_train_029及cp2750源文件/tar成员hash核验通过，已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-warmup-20261016T1058/evidence.tar.gz`
193,890,501字节，SHA256 `89398d832ac2abe46b389832768c8ba648fc8187f322fc25c1d74c434c8868f0`。
临时归档首版误访问在途row的step_after而退出，无包/无训练影响；修复只选闭合行，
仍在完整execution快照保留在途条目，失败脚本与journal随包归档。源脚本保留/tmp，归档包含复现源码。
首回合已有独立包；第三回合/cp4125在本次包快照后产生，仍仅本地待同步，不冒称已经归档。
服务器未计算。阻抗处理组和Direct v2继续等待当前队列，所有四方法仍未证明收敛，最终验收未运行。

用户于2026-10-16 12:52 CST明确开启Goal，要求持续推进并自主修复训练问题。Goal active，
尚未完成；旧15小时run正常按原截止收尾，新授权以独立有限阶段继续，不回写旧协议的截止。
沿用sii-research-sync协作流程，训练与分析在airpig，服务器只归档。

## 18:50 CST：修复旧Direct快照依赖，预检通过；阻抗首热身回合保全

开工main `6c5e2df121b18b5d181a3fb49393aa3081fb0de7`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，AGENTS开工及收工重读。
上一轮为进展。原阻抗control trainer2400811/协调器2400799持续运行，750→2250步/0更新；
5000热身期间无梯度更新符合登记。首回合1375步、完整55秒，Task/Strict=false、physical_valid=true，
return−25.493411918，cp1375全部hash通过；第二回合在途。最近execution资源峰值2,122,006,528、
current1,966,460,928，OOM/max0、swap0。没有改动活动源码或增加模拟器。

本轮发现并实际修复准备链路缺陷：Direct CPU pilot创建较早，冻结dispatcher缺少CUDA闭合接口，
backend模块不存在，reward helper只有旧Direct接口。prepare_gpu_pilot只拷贝新版pilot/trainer，
生成的混合版本入口在import阶段失败；原`outputs/rl_goal_direct_tracking_gpu_20261016`保留，
新增PREFLIGHT_IMPORT_FAILURE收据，服务`sii-goal-direct-tracking-gpu-preflight-20261016.service`
exit1、零仿真/零更新。该故障未影响同时运行的阻抗训练。

修复仓库`goal_tracking_pilot_20261016.py`，将pilot/trainer/dispatcher/backend guard/reward helper
作为配套模块刷新；validate_pair仍锁定登记权重，物理worker/参数controller快照保留。新增测试用
旧dispatcher/旧reward/缺backend快照，在独立子进程导入准备后的入口；修复前失败，修复后52项
Goal测试通过，diff检查通过。活动阻抗使用原快照，不会被仓库修复热修改。

新目录`outputs/rl_goal_direct_tracking_gpu_20261016_v2`已prepare并实际CUDA预检通过，登记SHA256
`109bf618dcc7f34e8d5d74d2940ab6704787bdabcf7a6c7c619890b53c9e4e06`。登记来源6c5e2df加本轮
尚未提交的准备工具修复，内容manifest为准；不伪称完全等于旧commit。Direct控制组无额外跟踪成本，
处理组额外weight4，fresh同seed2026101421、各11k；CPU1/单模拟器/3GiB/swap0/UTD1/n25不变。
派发截止2026-10-17T10:44:49.950861Z，协调器`sii-rl-goal-stage-bb18f8d17dfd.service`尚未启动，
两worker名为`sii-rl-goal-edf740b23fa9`与`sii-rl-goal-185982a6fdbe`。等待阻抗配对结束再派发，
不得启动已保留的失败目录或并行第二模拟器。
新预检CPU6/2GiB/swap0/CUDA实际exit0，两组初始网络hash一致、各一次有限丢弃更新、旧checkpoint
hash未变，峰值1,464,209,408字节、OOM/max0。没有正式训练/LAUNCH，预检不计入步数。
新旧reward helper在1375个记录区间的Direct tracking项完全一致，刷新接口没有改变该处理的数学定义。

首个阻抗GPU热身与stage01同seed/repair_train_008 CPU热身：rollout.npz SHA256均
`7370775a5d2ca67f55ff14b8adf73a046f7fbc2ace16fe47c3f006da77ba1f9e`，parameter_actions.npz均
`de68f112eca4d2e413f77250a930ce76113c8b08b5e61166ed0436a5d788aa76`；24+5数组及缺失掩码一致。
首次比较因默认array_equal将相同NaN判不同而退出，定位为48个搬运前阶段0/1/2/3的carry_load缺失，
所有有限值相等、actor observations全有限；修正missing-mask比较后只读归档exit0。原失败脚本与journal
一起保留，不填补缺失。这只验证随机热身一致，不推断学习后CPU/CUDA等价、治疗效应或收敛。

以上首回合/cp1375/reward诊断、失败/新Direct源码快照与预检、代码/测试/复现及失败收据已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-preflight-fix-20261016T1048/evidence.tar.gz`
197,775,860字节，SHA256 `86cf7d09e6693291a4a251bc3fee4833621b253f5006a0f909ed583dae9ec421`。
服务器仅存储/hash。Goal active；阻抗control→tracking继续，Direct配对已完成预检、待后续启动；
尚无奖励改善或收敛证据，最终acceptance与独立审计仍未运行。

## 18:40 CST：四族GPU验证完成，阻抗4对40奖励实验已开始

开工main `3aa0ca2d0f677155c6d67fd4aa7a86ae67f9fbb7`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`查询/fetch/read，AGENTS开工/收工重读。上一轮为进展。
导纳原2396091完成后协调器自动接续VMC2398175，无重复启动；GPU阶段10:34:53.046862Z自然闭合。
四族各1375条新增交互/连续真实更新、完整55秒、最终checkpoint与冻结来源核验通过，奖励分解重算一致。
各实际CUDA/亲和[1]、最终峰值≤3GiB，OOM/max0、swap0。全循环验证仅证明训练链路可用于GPU接续。

|方法|总steps/updates|本次return|Task/Strict|physical_valid|内存峰值bytes|
|---|---:|---:|---|---|---:|
|Direct|62906/96564|−38.733161806|false/false|false|2306428928|
|Impedance|12375/7376|−25.791857652|false/false|true|2308399104|
|Admittance|12375/7376|−25.304798245|false/false|true|2298105856|
|VMC|12375/7376|−25.222012881|false/false|true|2294398976|

n25阶段谱系各9闭合回合，全部Task/Strict失败；不足96回合且没有成功证据，收敛筛查均false。
所有training_complete=false，无最终acceptance。导纳/VMC原始回合/checkpoint、全日志、
四族更新/奖励/资源/谱系检查与复现脚本已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-close-20261016T1035/evidence.tar.gz`
534,010,065字节，SHA256 `1940f7934c88cc047e72d031ce7c369a0c2ebccd945d8d0abe81ad924f9642d8`。
前两族大型轨迹/checkpoint仍引用18:25条目已核验包，此包不重复收录；所有原始失败保留。

已实际创建并启动新GPU配对，原CPU配对保持未启动且未修改：
`outputs/rl_goal_impedance_tracking_gpu_20261016/REGISTRATION.json` SHA256
`87caa8863d96f65489e24564acaf68eb7ee52637b922a6fa7330f3cf4aba90d5`，source commit3aa0ca2。
顺序为impedance_control（原tracking权重4）、impedance_tracking（额外36、总40）；
两者均fresh网络/optimizer/replay/normalizer/RNG，同seed2026101421，其余训练条件相同。
历史checkpoint只提供丢弃预检数据，不加载进正式fresh模型；不同目标的reward总分不直接比较。
每组最多11000新交互，总22000；n25/UTD1/5000随机热身/1M optimizer日程，单seed最多8完整回合/组，
仅用于先检验奖励候选，不能取代四族完整训练或收敛要求。最终任务与物理判据保持冻结。
CPU1/单模拟器/单线程/3GiB/swap0，CUDA0不预分配、allocator .125（非GPU总内存硬限），
磁盘保留50GiB，派发保护截止2026-10-17T10:35:37.388010Z，本阶段STOP_REQUESTED在回合边界生效。

本机CPU6/2GiB/swap0/CUDA预检exit0：两组初始网络hash一致、奖励与末25步回报独立核对通过，
各一次更新有限、旧checkpoint hash未变；峰值1,506,635,776字节，OOM/max0。两次丢弃更新不计训练。
协调器`sii-rl-goal-stage-9c45a18ea80c.service`10:37:17.101585Z启动；
control服务`sii-rl-goal-33a827d0c492.service` trainer2400811，tracking服务名
`sii-rl-goal-7f55e47acca6.service`仍排队，未提前启动。
10:38:08快照182步/0更新，随后execution250步，0更新符合5000热身；首回合在途。
内存current/peak1,541,767,168、OOM/max0/swap0；GPU45°C/1105MiB，实际JAX0.7.2/cuda:0。
新冻结源码/登记/两组预检/启动快照及复现脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-gpu-launch-20261016T1038/evidence.tar.gz`
2,171,353字节，SHA256 `92303c15324ca854e402f2fa1dc083d2d5ad5bf549dad9a8b8d764d3da8b092a`。
服务器仅存储/hash；新训练轨迹尚在本机，完成回合后归档。Goal active，继续控制组→处理组，
检查完整回合Task/Strict、carry进度/物理跟踪及奖励分解；未声称权重修复有效，未最终验收。

## 18:25 CST：GPU前两族完整回合保全，导纳继续

开工main `cc986e0fdcae45dee6a09da14723e5cc7022d52d`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，AGENTS与进度重读，上一轮为进展。
原协调器2392590持续运行；阻抗2394029于10:20:32.874592Z正常完成，随后自动接续导纳2396091，
服务`sii-rl-goal-6e7a6f363edc.service`。10:23:28Z导纳11472/6473，OOM/max0、swap0，VMC仍排队。
冻结源与配置未改，没有重复启动模拟器；GPU训练未被只读归档打断。

|已完成GPU回合|总steps/updates|本段新增steps/updates|Task/Strict|physical_valid|return|内存峰值bytes|
|---|---:|---:|---|---|---:|---:|
|Direct|62906/96564|1375/1375|false/false|false|−38.733161806|2306428928|
|Impedance|12375/7376|1375/1375|false/false|true|−25.791857652|2308399104|

均完整55秒且无提前abort；两服务OOM/max0、swap0。两段1375条optimizer的step/update与父checkpoint
严格连续，最终检查点逐文件及归档成员hash通过，两个回合reward重算一致。训练链路的完整循环
与资源验证通过不代表任务成功、收敛或四族GPU阶段已经结束。阻抗服务含初始化443.595秒；
不同条件/初始化时间不构成CPU/GPU因果吞吐对比。

阻抗只读25Hz训练诊断：末10秒cursor20/28不变，位置误差12.599–13.074mm，姿态/速度均250/250
就绪、energy_scale1，参数确实在变化。这次确有整窗cursor不动证据，不用零ready计数单独推断。
折扣跟踪成本.0951568、力矩成本2.324404；继续支持已登记权重4→40的训练对照，并不证明因果根因。
Direct训练原生记录仍approach，外穿透1.30573mm导致physical_valid失败；这些原生指标未在本轮
进行最终独立子步审计，不冒充acceptance。所有失败标签与原始轨迹保留。

本机只读归档服务`sii-goal-gpu-first-pair-receipt-20261016.service`exit0；两原始回合/最终checkpoint/
训练及optimizer日志/奖励分解/carry诊断/协调器快照及复现脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-first-pair-20261016T1022/evidence.tar.gz`
548,866,014字节，SHA256 `80052f2894e1ed09256961858a2a63c04ab266241625f1ed92b8925dd90d657e`。
服务器仅传输/hash；导纳/VMC新轨迹仍仅本机或未生成，不声称已归档。

已复核两CPU奖励pilot的冻结输入、前序闭合、同seed配对、同物理/parameter清单及旧预检；两者
均未启动，也未修改。四族实际CUDA完整回合验证通过后，在新目录准备GPU配对，先执行阻抗：
`goal_tracking_pilot_20261016.py prepare-gpu --cpu-pilot outputs/rl_goal_impedance_tracking_pilot_20261016`
配合`--gpu-validation outputs/rl_goal_gpu_preflight_20261016 --root outputs/rl_goal_impedance_tracking_gpu_20261016`。
随后用本机CPU6/2GiB/swap0/CUDA0运行该新快照的preflight（两次丢弃更新），通过后launch。
仍只启动一个模拟器；不同reward总分不直接比较。Goal active，无最终验收或收敛声明。

## 18:10 CST：Stage01全部闭合，四族CUDA预检通过，实际GPU训练接续

开工main `4076420f0d1166acfe10cbb6a66dfb5cbc6c2063`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，AGENTS开工及收工重读。
10:02:17Z原协调器自然结束，四族最终检查点核验通过。本段结果：

|方法|累计steps/updates|本段完整55秒回合|Task/Strict|physical_valid|
|---|---:|---:|---:|---:|
|Direct|61531/95189|8|0/8|3/8|
|Impedance|11000/6001|8|0/8|8/8|
|Admittance|11000/6001|8|0/8|8/8|
|VMC|11000/6001|8|0/8|8/8|

VMC第7/8return−25.203426841/−25.389355820，八回合mean−25.261000130、std .067965733，
奖励重算一致。低波动失败平台不是收敛，training_complete=false；不把有限段完成当1M完成。
最后两checkpoint9625/11000逐文件及tar成员hash通过，全部失败保留。
旧trainer没有最终resource_snapshot，收尾收据明确null，不把服务结束后的缺失值写成零。
最后在途观测10:00:26Z OOM/kill0、swap0，max2082为回收计数。
收尾包（末两原始轨迹/checkpoint、全VMC日志、四族检查点核验、reward/carry/收敛筛查）位于：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage01-close-20261016T1002/evidence.tar.gz`
529,918,496字节，SHA256 `e8274358f90e0bfc895d7cb41e5fb2be331a76516937d79b623bd590e66a0642`。

下一阶段已实际登记/预检/启动，不再只是准备方案：
`outputs/rl_goal_gpu_preflight_20261016/REGISTRATION.json` SHA256
`98585360903c2164979d36129a273e719da79f0298ffaafa44ab0b2b2df49a11`，来源commit4076420。
四族按原顺序各新增1375步，总5500，Direct61531→62906，其他11000→12375；仍1M optimizer日程。
精确恢复各自网络、optimizer、replay、RNG、normalizer，仅学习后端CPU→CUDA；不声明浮点逐位等价。
物理/worker/参数源码、reward、gate/canonical48/filter/执行器/dt5e-5保持，带入此前磁盘保留线修复。
CPU1/单模拟器/单线程/3GiB/swap0/UTD1，CUDA0 allocator .125/不预分配；该比例不是总显存硬上限。
新派发保护截止2026-10-17T10:02:48.913556Z，停止入口本阶段STOP_REQUESTED。

四族各一次丢弃更新的CUDA恢复预检全部exit0、指标有限、terminal window与replay检查通过，
原checkpoint未变；峰值依次1,331,314,688/1,287,548,928/1,293,856,768/1,292,156,928字节，
OOM/max0。这四次不计入实际训练，也不代替完整回合验证。
协调器`sii-rl-goal-stage-7418f4a6bd92.service`10:08:06Z启动，Direct
`sii-rl-goal-96db82156770.service` trainer2392601、worker2392639，无重复模拟器。
10:10:04Z优化器日志61912步/95570更新，相对起点新增381/381；execution快照61750较慢，
二者时间语义分别保留。实际JAX0.7.2/cuda:0/RTX5080 Laptop，亲和[1]。
内存current/peak1,905,750,016，上限3GiB，OOM/max0、swap0；GPU45°C/1430MiB。

冻结源码、登记、四族预检和上述启动快照（非新完整回合）已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-launch-20261016T1010/evidence.tar.gz`
2,164,534字节，SHA256 `15e0f26aea078cb9bff45175d0953ab0f6cfee6d55a800bb69e583dcae11cc1f`。
GPU阶段实际训练轨迹尚在本机，完成边界后归档；服务器只存储/hash。Goal active。
接下来核验四族实际完整55秒GPU循环与最终资源，再启动已准备的Direct/阻抗奖励对照；
不同奖励总分不直接比较，检查Task/Strict与物理跟踪。未做最终acceptance或独立子步审计。

18:13 CST复查：Direct首个完整55秒GPU回合结束，62906/96564，新增1375交互/1375更新；
cp62906九文件hash通过。10:08:11.387742Z至10:13:04.311458Z约293秒含初始化，
不同条件/初始化不能直接作CPU-GPU因果吞吐比较。return−38.733161806，Task/Strict均false、
physical_valid=false（全55秒、无提前abort）；训练链路通过不代表任务或安全成功。
final memory_peak2,306,428,928/current1,724,055,552，OOM/max0、swap0，training_complete=false。
协调器已接续阻抗`sii-rl-goal-a95889cd0106.service`。Direct本次新轨迹/checkpoint暂仅本地，
尚未纳入10:10启动归档；下一安全边界保全。其余三族GPU完整回合仍待完成。

## 17:40 CST：VMC第6回合闭合，第7回合继续学习

开工main `d18ab1b41d6bc9fd0a7c9136daa5b2d4867cfc3b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read，AGENTS与进度重读。
上一轮修正诊断为进展；本轮核验原服务及PID2375301/协调器2329290 live，等待第6回合
完成并保存cp8250。7750/2751推进至8500/3501，第7回合在途，未重复启动或修改运行快照。

第6完整55秒return−25.157868312，physical_valid累计6/6、Task/Strict0/6；cp8250逐文件
及tar成员hash通过，前6reward重算一致。保留至8250的3251条optimizer记录，末温度.007400999。
第6末10秒cursor18→20（两次推进），位置误差12.018–18.622mm、姿态就绪250/250、速度249/250，
参数确实变化、energy_scale1；position/rejoin采样就绪0仍不能当没有推进的证据。
不同condition/单回合return波动不证明学习改善，未达Task/Strict，未证明收敛。

资源快照current3,111,485,440、peak=max3,221,225,472字节，memory.events.max1285，
OOM/kill0、swap0；pressure avg60=.05%。上限回收没有阻止真实更新，不扩容或重启。
GPU验证仍需四族本阶段闭合，目标目录尚未创建；核对派发/后端入口未见重复或提前启动。
冻结输入/源清单通过，未改变奖励或其他训练配置。本轮只读归档服务exit0，无额外仿真/梯度。

第6原始回合/cp8250、前6reward、carry/3251条optimizer/资源快照/复现脚本已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-episode6-20261016T0940/evidence.tar.gz`
（268,708,282字节，SHA256 `199cc0cb0b465e947f566e398a227782e683dc2eaae561863b9adc05ef0be312`）。
服务器仅传输/核验，不计算。Goal active；VMC继续剩余既定回合，再进行四族GPU完整循环验证
与已登记奖励配对。所有失败保留；未做统一acceptance或最终独立物理审计。

## 17:30 CST：路点诊断增加推进证据，区分缓慢前进与末窗停滞

开工main `f296a7dffaabdfe79bbdadcd39815ff8bd09d8ae`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read，AGENTS与进度重读。
上一轮为进展。原VMC PID2375301/协调器2329290 active，6500/1501→7250/2251，
第6回合在途；前5完整55秒physical_valid5/5、Task/Strict0/5，第5return−25.330025621。
cp6875逐文件及tar内成员hash通过，前5回合reward重算一致；未重复启动/更改运行快照。

冻结validate_office_apparatus主循环先调用task.update，再生成canonical observation；
PlannedCornerTask中间路点到达后先递增cursor并替换goal。因此观测误差是切换后的目标误差，
即便末10秒所有观测position/rejoin-ready均0，也可能仍在推进。中间路点只检查位置/重入
及姿态，不采用最终阶段速度/驻留条件。此前字段数值未错，但不能用0/250独自判停滞。
诊断新增cursor_first/last、observed_cursor_increases/decreases、sampled_cursor_unchanged
及采样顺序说明，不改环境、gate或训练。5项测试包含零就绪但实际换路点的反例及恒定目标对照，
编译/diff通过；本机只读复核21个闭合参数RL回合exit0，无新仿真/梯度。

末10秒复核结果（索引从0开始）：阻抗ep0–7全部cursor20不变；导纳ep1为18→21、ep4/5为17→18，
另5回合末窗cursor不变；VMC ep0–2为18→20、ep3为19→20、ep4为18→19，全部仍有1–2次推进。
各回合的sampled position/rejoin-ready都是0。更正任何把这些方法统一描述为完全卡死的解读：
VMC当前更符合未在55秒内走完路径，阻抗仍有一致的末窗停滞证据；这不是不同条件之间学习改善
或失败根因已确定的证明。最终Task/Strict失败标签不变，阻抗既定tracking奖励对照依据不变。

归档快照7000/2001：memory.current3,102,957,568字节，peak=max=3,221,225,472，
memory.events.max689、OOM/kill0、swap0。max为上限回收，非OOM；继续推进不重启。
本轮已核验服务器归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-waypoint-progress-20261016T0930/evidence.tar.gz`
（264,801,479字节，SHA256 `79b7d1bacc2cb2383cc3fd5beb4ccd5dea5ded3fafb06f7ed3c2c650d13fabbf`），
含第5原始回合/cp6875、前5reward、21回合重新诊断/源码/测试/资源快照和复现脚本。
旧轨迹仍在此前分包，诊断只新增不覆盖历史收据。Goal active，四族未证明收敛；VMC继续既定段，
后续四族GPU验证/已登记奖励对照不变，未做统一acceptance/独立最终物理审计。

## 17:20 CST：VMC从热身进入真实梯度学习，首次学习checkpoint保全

本轮开工main `8cb0812f2ec6ccc4551e602d71190581f5ee8038`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read，AGENTS/本进度重读。
上一轮为进展；本轮核验原服务/进程并等待实际热身切换。PID2375301与协调器2329290不变，
4750步/0更新→6000步/1001更新；第5回合worker2380589在途，仅一个模拟器，未重启或改冻结源。

前四完整55秒回合physical_valid4/4、Task/Strict0/4；第3/4 return−25.243592718/
−25.284312267。cp4125/5500所有hash及归档内成员通过，前四回合reward独立重算一致。
step5000–5500对应501条连续有限optimizer记录，保存的agent updates从0变501，
actor/critic/target critic/temperature四类文件都变化。step5500温度.0095859971，
critic loss8.947832、actor loss−.106940；只证明更新与保存真实发生，不是loss越小越成功的判据。
第3/4回合末10秒carry cursor18–20/28，位置误差分别12.008–18.755mm及12.071–18.073mm，
位置/重入0/250、姿态/速度250/250，参数变化且energy_scale1。第4后段已包含学习动作，
但不同condition/早期曝光不能作因果改善结论，25Hz也不替代最终物理子步审计。

归档快照5500/501：memory.current3,096,887,296，peak3,147,325,440，max3,221,225,472字节，
memory.events.max/OOM/kill均0、swap0。随后仍真实推进，未把接近上限本身当作重启理由。
主机GPU42°C/511MiB仅资源观察，当前训练仍CPU。只读核验/压缩服务exit0，没有梯度或额外仿真。

核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-learning-20261016T0915/evidence.tar.gz`
（461,230,645字节，SHA256 `bce8ae27d12b34b3097b19045d61bccb73359cf8d6dfc6108832593d075b1c79`），
含第3/4回合与两个checkpoint、前四reward诊断、501条更新、网络hash变化与资源/执行快照/复现脚本。
前两回合另见0900包；后续在途数据仍在本机。Goal active，继续完成VMC既定段，再执行真实四族GPU
完整循环与已登记奖励对照。四族尚未证明收敛，没有统一acceptance或最终审计通过结论。

## 17:05 CST：区分新旧终端窗口，VMC完成两次热身回合

本轮核对远端main `f1f7630985f107101b12bed3f3d8275cc3c2c927`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS。上一轮为归档/发布进展。
VMC原PID2375301与协调器2329290保持active，1500→3500步，5000步前仍0更新；
前两完整55秒回合physical_valid2/2、Task/Strict0/2、return−25.242069151/−25.237350308，
第三回合worker2378145在途。checkpoint1375/2750逐文件及tar成员hash核验通过，未重启或重复仿真。

导纳cp11000只读诊断1159条，temperature .0058060978，末25步平均绝对TD残差.544058，
非末窗口.030548。诊断脚本新增latest/earlier terminal window两个分组：最新25条残差3.840848，
旧七回合175条.073088。读取MultiStepReplay.valid_count/at和trainer更新顺序确认，末n条
只在终端出现后成为terminal-backed可采样窗口；立即边界保存前仅有终端step的更新机会。
因此汇总末段残差不应被解读为旧数据整体未学会。旧窗口actor−behavior Q均差2.630814，
仍不是独立真实Q高估或实际更优动作的证明。不能据此扩张UTD、改冻结gate或声称收敛。

两次有界诊断exit0；原分组数值逐项完全相同，25+175=200、加权残差复算通过，模型统计/
RNG/checkpoint hash未变，峰值903,589,888字节、OOM0。新分组诊断源码编译/diff通过。
VMC两回合奖励重算一致；末10秒carry cursor18–20/28、误差约12–19mm，位置/重入0/250，
姿态/速度250/250，参数实际变化且energy_scale1。不同condition和25Hz采样不支持因果改善或全子步结论。
快照3000步current1,923,268,608、peak2,026,209,280字节，上限3GiB，max/OOM/kill0、swap0；
主机swap接近满不等于该worker使用swap。GPU主机查询42°C/524MiB；沙箱内NVML查询失败，
主机只读查询成功后确认驱动可用，未变更驱动/显示。当前RL仍CPU。

已核验服务器归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-vmc-20261016T0900/evidence.tar.gz`
（387,069,253字节，SHA256 `45e732d9d9780e1504d679fb4141bf1272b9657c57e64e6113b903e86ae2b9d4`），
含前两VMC回合/两个checkpoint、reward/carry快照、导纳两份critic诊断/新源码及复现脚本。
无最终acceptance；四族未证明收敛。后续仍先收完VMC，执行四族GPU完整循环验证，再执行已登记
奖励配对实验；不因本轮诊断而增加新实验队列或改运行快照。Goal active。

## 16:50 CST：导纳有限段完成，原协调器自动接续VMC

开工main `c9ba42295443028db43206c6398d4f31f9d3cd7c`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已实时查询/fetch/read，AGENTS重读。
原导纳PID2360933从10129步持续推进，于08:48:28.608451Z正常结束11000步/6001更新，
8个完整55秒回合、cp11000逐文件hash通过。原协调器2329290在08:48:29Z派发VMC，
trainer PID2375301/worker2375327，已750步/0更新，仍在5000步热身、首回合在途。
没有人工重启/重复服务，冻结source/parameter清单通过；Direct/阻抗/导纳的有限段闭合
不是完整1M训练完成。VMC是第四族实际训练，不是四族已收敛。

导纳八回合physical_valid8/8、Task/Strict0/8，return均值−25.379613331、总体标准差
.066046870，末回合−25.520884983。八回合奖励重算一致，折扣tracking成本.12158–.16440、
峰矩成本1.60827–1.79107。末回合末10秒仍carry cursor18/28、误差12.294–19.963mm，
位置/重入0/250、姿态250/250、速度245/250，参数变化且energy_scale1。不同condition及
25Hz采样限制保持，不推断因果改善或逐物理子步gate。完整训练筛查training_candidate=false，
不足96回合/两个32条件窗口；训练Task/Strict0/8也不支持成功。training_complete=false。

收尾服务`sii-goal-admittance-close-0850`的receipt与tar已完整关闭，但之后控制台摘要读取
`state['resource_snapshot']`产生KeyError，exit1。stage01冻结trainer早于该字段新增；
不将最新源码字段倒推为旧运行已有统计。保留原脚本/归档，独立`0850b`服务只读tar逐一
核验全部checkpoint成员hash和receipt相同，exit0；没有重跑训练或覆盖旧结果。最终导纳
memory计数缺失，明确null；最后运行时观察OOM0仍仅是当时快照。VMC584步实测current/peak
均1,333,866,496字节，上限3GiB、OOM/max0、swap0，随后execution到750步，实际交互得到核验。

末回合原始数据/cp11000、完整训练与optimizer日志、八回合reward/carry、四族训练筛查
归档已核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-close-20261016T0850/evidence.tar.gz`，
277,322,329字节，SHA256 `ad63cc832e472ea8aaca5f05023710262d5afecb9ee8a958ec0315776e6c8532`。
同目录`ADMITTANCE_CLOSE_READOUT_FAILURE_20261016T0850.json` SHA256
`7f8b40513ac30de2a472e964def20dac1807153cc19eb9e716854982bebd976f`；
`VMC_HANDOFF_20261016T0850.json` SHA256
`11c33820d3d53907f60b6c5c24c6b236ac50d56480bd20981d7fed9e48e8c208`；两个对应复核脚本也已上传核验。
前7回合及checkpoint在此前分包，VMC新轨迹仍本机。Goal保持active；先收完VMC，再执行
真实四族GPU完整循环验证和已登记奖励干预，尚无最终acceptance/成功收敛结论。

16:56 CST收工复查：原VMC trainer2375301继续至1500步/0更新，第一个完整55秒回合
return−25.242069151、Task/Strict0/1、physical_valid1/1，已登记checkpoint1375。
第二回合worker2376349在途；仍仅一个模拟器，memory.current1,620,836,352字节，
max/OOM/kill0、swap0，磁盘可用84,296,880,128字节。首回合与新checkpoint仍在本机，
不属于0850归档；零更新符合5000步热身，不能从热身return判断学习收敛。

## 16:40 CST：修复每回合磁盘保护遗漏，导纳第7回合保全

开工main `681a1a3f55a18063a2622410889dafb83c5e9f77`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/read，AGENTS重读。
导纳同PID2360933从8807步/3808更新推进至快照9701/4702；第7于08:36:50Z闭合，
return−25.435066062、cp9625全部hash通过。7完整55秒physical_valid7/7、Task/Strict0/7；
第8在途、VMC排队。memory.current3,034,660,864、peak3GiB、max1877、OOM/kill0/swap0，
temperature .00650053。max是上限回收事件，未作为重启依据。

存储盘点发现实际实现遗漏：Goal派发前要求50GiB，但trainer原回合检查只读取父协议20GiB。
新增`effective_disk_reserve`取父协议/continuation/Goal最大值，拒绝非法字节数，每回合
记录free/reserve并在不足时停止下一回合，沿原退出路径保存checkpoint。49项Goal＋6项恢复
测试通过；直接运行实际AST边界块，49GiB不派发，50/60允许，70GiB父约束仍优先。
真实登记辅助函数计算50GiB，free85,491,027,968字节（约79.6GiB），没有空间不足的实际停机。
当前冻结trainer hash `c762d875d469047f311942c02f4e1bcbe81fa9d51712779f84beb6a28654ace7`未改；
候选新trainer hash `119ab188749e7b8362fc6d51dd5ff85decbf9f6cf1dd9f5846f0bd65a7de34d0`。
后续GPU验证准备会引入新trainer，GPU配对准备也更新为复制新trainer；两臂物理/parameter/
reward快照仍一致，旧CPU pilot/source不改。此前“GPU准备保留旧trainer”说明自此被此修复取代。
同时修正tracking元数据硬编码−4，按真实额外权重4/36填写；实际奖励算法没有改变。

`STORAGE_FORECAST_20261016T0840.json`保留各闭合回合/checkpoint实际大小及登记依赖：
stage01约7.06GB，保留线以上约32.12GB。按当前完整轨迹每交互101,792–117,904字节外推，
四族各1M交互仅轨迹407–472GB；尚不含checkpoint/log/source/传输缓存，不是保证总量。
长期训练须增量核验归档并把不再本地依赖的历史数据离线保留；当前不删除任何原始文件，
不降低50GiB保留线，不把此盘点当完整存储迁移已经完成。

第7完整轨迹/cp9625、修复/测试、真实登记检查/资源快照及盘点脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-disk-guard-20261016T0840/evidence.tar.gz`，
270,081,238字节，SHA256 `0d1e3c4bcc31c7c5f191b0c83fa21053a357e222c43e620e6ddc31dc02626eaf`。
服务器仅文件传输/大小/hash。Goal active；继续收完导纳并核对VMC接续，GPU真实完整循环待四族闭合。

## 16:30 CST：导纳第6回合正常闭合，稳定失败回报不等于收敛

开工核对main `e100c6d81f12c3451d286bcc249c014567acc8c6`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及远端日志/AGENTS。原导纳PID2360933、
协调器2329290均现场确认active。7750步/2751更新推进到8326步/3327更新；观察8000→8152
约74秒，无更新停滞。第6完整55秒回合08:25:17Z结束，cp8250核验通过，原进程接续第7回合。
VMC仍排队，未重复启动，未创建新的GPU训练/奖励对照目录。

6回合physical_valid6/6、Task/Strict0/6；return均值−25.346825935、总体标准差.030040937，
末回合−25.363762985。调用已有reward诊断逐步复算六回合，日志/终端标签/折扣potential
抵消一致。折扣跟踪成本.12157694–.16439618，峰矩成本1.60826888–1.66977685；任务失败成本
10.05993261、potential成本.56023853。每1375条只有1条终端Task奖励，n25直接覆盖25条。
没有发现奖励求和错误；稳定失败平台不满足Goal的成功率/条件覆盖/样本要求。

只读carry诊断复核六回合，全部末10秒仍carry。第4回合cursor18/28，位置误差17.146–18.944mm；
第5在cursor17/18，采样87/163，误差12.040–18.221mm；第6在17/18，采样170/80，
误差12.363–18.301mm。第6姿态/速度条件各250/250，位置/重入0/250；前后时序对齐与route
target重建通过。第4–6实际参数持续变化，energy_scale均1；例如第6末10秒平动刚度
493.00–888.61、质量.3238–1.0225、阻尼比.5289–1.3596。沿既有动作映射/参数应用源码检查，
尚无证据表明参数不生效或被能量限制完全抹掉。控制效果仍不足，且不同回合condition不同，
不能从误差差异推出学习改善/恶化。25Hz诊断不代表全部物理子步gate结果，不修改冻结判据。

归档快照temperature .0073591848，memory.current3,057,926,144、peak3,221,225,472，
memory.events.max1311、OOM/kill0、swap0；memory.pressure avg60=.07%。保护上限回收与
内存耗尽分开报告，当前原进程健康推进。本轮未调整奖励/训练参数、未重启或扩大内存。
真实只读诊断/压缩在本机CPU6/1GiB/swap0，exit0；没有新仿真或梯度更新。

第6完整原始回合/cp8250、六回合reward/carry与执行/资源快照、脚本已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-learning-20261016T0830/evidence.tar.gz`，
269,154,608字节，SHA256 `a83b4c807756c4c4812b7ccd227e471070324f3c38ce7c88dc777adcd0a48ea5`。
第1–5原始数据在此前分包，第7在途仅本机；服务器无计算。下一步完成导纳有限段并核对VMC
自动接续；四族闭合后执行GPU完整循环，再用已登记奖励干预检验实际效果。Goal保持active。

## 16:20 CST：GPU奖励对照交接入口完成，导纳第5回合已保存

开工核对main `5925a1c12d9641c699cbbf834fddc56565206a47`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与远端日志/AGENTS。原导纳PID2360933从
6951步/1952更新推进至归档快照7364步/2365更新；第5完整55秒回合于08:13:41Z闭合，
return−25.294348699，cp6875完整hash通过。累计physical_valid5/5、Task/Strict0/5，
第6在途、VMC排队。训练任务失败与资源故障分开：当前没有OOM，仍不能说已收敛。

已准备的CPU奖励对照原先没有显式转为新GPU登记的入口。新增
`goal_tracking_pilot_20261016.py prepare-gpu --cpu-pilot <原CPU配对目录> --gpu-validation <四族GPU完整循环目录> --root <新目录>`。
必须CPU配对从未启动且其预检通过、四族前序正常闭合、实际GPU完整55秒回合/资源保护通过；
核验相同parent协议/runtime/解释器/锁、parameter清单、scripts/assets及物理worker源码。
只复制原配对源并更新准备入口，trainer/reward不变；两臂fresh模型/optimizer/replay/normalizers、
同seed、各11k/1M日程、CPU1/3GiB/swap0/UTD1，显式CUDA0/.125 allocator，原CPU目录不变。
新登记保存原CPU登记/预检hash与GPU验证登记/execution hash，24小时派发保护；不能复制旧
CPU预检当GPU预检，必须在新source上重新实际跑2次丢弃更新，再按原launch/锁/资源准入派发。

49项Goal测试、编译/diff检查通过。合成GPU闭合fixture验证入口逻辑，不是真实GPU训练证据。
实际对现有阻抗pilot运行该入口，因stage01仍running在创建目录前exit1；完整命令/stderr在
`GPU_PAIR_READINESS_20261016T0820.json`，原CPU登记SHA256
`52884e47b1db9e4ea4a050940e70d1edcf81aa46482d44412ba2976b69472a16`保持。没有新GPU
目录/LAUNCH/训练进程；当前CPU训练继续。待stage01四族闭合，先完成已实现的GPU四族
真实全循环验证，再使用此入口执行奖励对照，不能用准备工作替代在线修复效果。

导纳快照temperature .00802963，memory.current3,164,946,432、peak3,221,225,472字节，
memory.events.max503，OOM/kill0、swap0。硬上限回收事件不等于OOM；保留3GiB限制并继续观察
真实步数，不为接近上限重启健康作业。本地约81GiB可用，50GiB派发保留线不变。
第5完整原始回合/cp6875、实现/测试、真实拒绝收据与执行/资源快照已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-pair-entry-20261016T0820/evidence.tar.gz`，
268,980,389字节，SHA256 `68548ebda3ad34e1c641c3fd6c9e7f9b1a84e98572dd055058910fc352d4fa56`。
服务器仅传输/文件hash，无计算；后续回合仍本机待归档。Goal active，四族均无可验证收敛结论。

## 16:10 CST：末端邻近诊断，导纳真实学习继续

开工核对main `bc56632dbe6a4f92f1fe7cb1f529d6b50af32229`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及远端日志/AGENTS。导纳同PID2360933从
5500/501推进至6576/1577（steps/updates），4完整55秒回合physical_valid4/4、Task/Strict0/4；
第4return−25.347365861。下一回合在途；VMC排队，原协调器继续，无重复模拟器。

新只读工具`tools/diagnose_goal_terminal_neighbours_20261016.py`检查阻抗cp11000与导纳cp5500。
每回合末25个样本，在同回合距离末端至少50步的早期候选中寻找观测/动作邻居。距离为观测
差除以整个replay每维标准差（floor1e-6）的均方，加原始动作差均方，两组等权；这不是网络
真实normalizer或物理等价判据。保留短回合跳过收据，拒绝未闭合/非有限replay；不跨回合。

阻抗200对、导纳100对：观测RMS中位数.081423/.128995，动作RMS中位数.092459/.104988，
时间差中位数2.90/3.52秒。末端n25奖励均值−22.544659/−22.502375，对应较早窗口
−.051879/−.057405；bootstrap mask分别0/1。尽管部分输入接近，原始观测差仍非零，
**奖励分量不是完整Bellman目标**，不能据此证明时间混淆、真实Q高估、输入不足或学习不可能。
本轮未改actor输入/terminal处理/奖励；结果仅补充末端残差诊断，后续需实际训练对照验证。

3项边界/动作邻居/短回合测试、编译与diff检查通过；真实诊断在本机CPU6/1GiB/swap0，
exit0、峰值100,077,568字节、OOM/max0，无JAX/模型加载/梯度/仿真，checkpoint hash前后相同。
归档快照6383步/1384更新、temperature .0087939678，内存current3,118,579,712、
peak3,165,929,472/3GiB，OOM/max0/swap0。随后anon约1.76GB/file约1.29GB，接近上限
包含文件缓存，未据此重启；全GPU38°C/498MiB，训练仍CPU。新冻结源与登记hash通过。

第4导纳完整原始轨迹/cp5500、只读工具/测试/诊断收据、execution及optimizer快照已归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-terminal-neighbours-20261016T0810/evidence.tar.gz`，
267,986,596字节，SHA256 `19116474cc1bb4db182f5fcd829131fb68f1484d793c299194d1aa9cd5024d13`。
之后数据仍本机待安全边界归档，失败/在途行均保留。Goal active，无收敛或最终acceptance；
下一阶段仍为四族stage01结束后的真实GPU全循环预检，再推进奖励对照/后续训练。

## 16:00 CST：导纳进入优化阶段，释放已核验的重复传输缓存

开工核对main `25c904e1567e3e76f596c524c0f7adcd1ada40a9`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与远端日志。上一轮为实质进展。
同一导纳PID2360933从4000推进至5250步/251更新（5000步第1次更新），原协调器2329290继续。
3个完整55秒热身回合return−25.378512382/−25.374599982/−25.322365699，Task/Strict0/3，
physical_valid3/3；第4回合在途，VMC排队。不能把热身均值稳定当作收敛。

前三回合末10秒25Hz轨迹：第1在cursor17/28，误差14.230–16.205mm；第3在cursor18/28，
误差15.337–17.132mm。第2窗口跨cursor18/19/20/21，计数49/86/86/29，误差18.864–23.463mm；
不能概括成三回合完全静止或照搬阻抗的cursor20结论。每个采样点位置/重入条件均未满足，
但25Hz无法证明采样之间的物理子步条件，更不能据此宣称planner错误或进行最终gate审计。
cp2750/4125与冻结source/parameter清单通过；没有新仿真、奖励调整或重复进程。

本地磁盘检查约78GiB可用、训练保留线50GiB，服务器共享盘约3.3TiB可用。明确枚举9个本任务
临时传输包，逐一重新检查本地/服务器最终归档的大小与SHA256，确认本地为非symlink/单硬链接
的普通文件；执行前再核对全部inode/device/mtime/size/hash，然后仅unlink精确/tmp文件。
已清理stage01-0507、credit-0518、episodes38-40-0545、direct-close-0623、impedance-0649、
impedance-learning-0704、gpu-backend-implementation-0724、impedance-close-0738、
impedance-weight-pilot-0750九包，均带完整rl-goal前缀和20261016日期，详见收据逐文件路径。
释放5,077,083,233字节（4.73GiB）；free_before82,924,175,360、free_after88,000,159,744字节，
期间训练仍在写入。保留了本地所有原始训练目录/checkpoint/source和服务器全部归档，
没有递归删除/历史实验迁移。旧日志称这些/tmp包保留是当时状态，现以此条及删除日志为准。
完整恢复命令在`TRANSFER_CACHE_CHECK_20261016T0800.json`；删除journal逐文件fsync，
结果在`TRANSFER_CACHE_RESULT_20261016T0800.json`。第一次read-only检查因系统Python缺少
hashlib.file_digest而exit1，未生成检查收据、未删除；冻结项目Python在独立服务复核/执行均exit0。
本轮仅回收临时冗余，长期1M训练仍需按阶段归档/监视增长，未降低50GiB保护线。

导纳第2/3原始回合与cp2750/4125、前三carry结果、5000步/1更新快照、存储清单与cache收据
已核验服务器最终归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-storage-20261016T0800/evidence.tar.gz`，
396,011,348字节，SHA256 `6628bdf7dfa89cf61bfe3b62e8eed136dceaed3b1f333c95ee82f79cc95e6890`。
第1回合在上一轮0750包；本轮第4及后续新数据仅本机。归档快照memory.current2,778,599,424、
peak2,808,971,264/3GiB，OOM/max0/swap0。服务器只文件传输/大小/hash检查，无服务器计算。
Goal active，未收敛/未最终验收；原GPU/Direct奖励/阻抗奖励的准备状态不变，未派发。

## 15:50 CST：阻抗权重对照实现、登记和真实预检完成，现有导纳继续

开工核对main `b0e61c671691fc0e33d5193d3b9a00611fa46e2e`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS/远端日志。上一轮为实质进展。
导纳PID2360933/原协调器2329290真实推进至2750步，仍处5000步热身、0更新；2完整55秒回合
return−25.378512382/−25.374599982，Task/Strict0/2、physical_valid2/2，第3在途。VMC排队。

新修复假设：已有阻抗8失败回合跟踪奖励约−.09，而峰矩约−1.6至−2.8，跟踪信号偏弱。
把训练跟踪权重从4提升到40，使用同一物理子步积分的bounded_error_cost（尺度仍.12m）：
保留原metric基础权重4，新增明确标记的tracking_guidance权重36；所有其他奖励项保持。
提前失败补齐新增项的折扣最坏尾部；不改变最终物理/gate/actor48/filter，也不靠改门槛解卡。
这是单变量训练假设，不能保证能克服接触/可达性问题；需看真实paired任务与安全结果。
`goal_tracking_reward_20261016.py`与trainer拒绝未登记配置/不同奖励checkpoint混用；
`goal_tracking_pilot_20261016.py`复用fresh比较流程，支持5维阻抗，与旧7维Direct保持隔离。

新独立根`outputs/rl_goal_impedance_tracking_pilot_20261016`已prepared，登记SHA256
`52884e47b1db9e4ea4a050940e70d1edcf81aa46482d44412ba2976b69472a16`；
两臂impedance_control/impedance_tracking，同seed2026101421、各最多11000新交互/1M优化日程、
5000热身、n25/UTD1、CPU1单路/3GiB/swap0，派发保护截止2026-10-17T07:46:01.068951Z。
模型/optimizer/normalizer/replay均从零；cp11000只用于只读取历史replay预检，不用于训练初始化。
真预检读取同一个1375步完整训练回合，两臂各做一次丢弃更新：初始网络hash完全相等、
终端25步累计回报及mask正确、所有metrics有限、旧checkpoint hash不变，exit0。
峰值1,365,557,248字节、OOM/max0；无仿真/模型保存。43项Goal＋5项恢复测试、编译/diff检查通过。

`IMPEDANCE_TRACKING_WEIGHT_ARITHMETIC_20261016T0748.json`在相同8条旧轨迹上复算额外
折扣罚分.830188–.866527；不是新策略回报/效果，不能用不同奖励定义的raw return比较优劣。
真实require_predecessor_complete检查拒绝当前仍运行stage01；没有LAUNCH/后台等待服务/新模拟器。
既有Direct pilot登记hash仍`42f101068a4185f7d920900de8b18f63720720436254fb3f2bbe4ab4cb7f3c91`。
GPU完整循环验证仍先于后续训练对照；此新pilot是CPU登记，未冒称GPU实测或四族训练完成。

已核验incoming大小/hash与最终独立目录hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-weight-pilot-20261016T0750/evidence.tar.gz`，
198,505,376字节，SHA256 `de29e2588ac37a95b0c04b949b0acaab05e50dd1a9a9cf0b0ce153bbdc8b2a1f`。
含完整pilot冻结source/parameter/REGISTRATION/CREDIT_PREFLIGHT、算术结果、测试、
`PREPARATION_EVIDENCE_20261016T0750.json`及导纳首回合原始轨迹/cp1375/PROTOCOL。
快照2750步、内存current1,745,911,808/peak1,989,345,280、OOM/max0/swap0；第2及后续回合
仍仅本机，原模型/runtime仍依赖既有冻结路径。Goal active，尚无收敛或最终验收。

## 15:40 CST：阻抗11k闭合，导纳真实启动；8个失败回合完整保全

开工核对main `d26bf9b139cad17ddc786cdb91be2505b6214c9a`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS/远端日志。上一轮为实质进展。
阻抗11000步/6001更新于07:35:46Z正常结束，step_budget、8个完整55秒回合、physical_valid8/8、
Task/Strict0/8。checkpoint0011000各文件hash通过；1M日程未完成，不能把有限段结束当收敛。
协调器PID2329290自动启动导纳PID2360933/user unit sii-rl-goal-7310d204f8a4，真实250→750步，
仍5000步热身、0更新、首回合在途；3GiB/swap0/单CPU1保持，OOM/max0。VMC尚未启动。

阻抗回报均值−25.587297829、总体标准差.473319155；第8回合−25.939879296。
8个末10秒窗口各250采样均停carry cursor20/28，位置与横向重入均不满足、姿态/速度均满足；
末回合位置误差12.7987–13.1865mm，forward−5.955至−4.829mm。参数动作在改变，energy_scale=1。
这不是独立物理子步审计，也不能把刚度、reward或障碍接触单独定为原因；最终gate未修改。
全8回合训练奖励复算一致：折扣potential合计均−.560238529（预期抵消），tracking罚
−.092243至−.096281、峰矩罚−1.589846至−2.833113，task罚均−10.059933。
小幅回报波动主要是峰矩差异，没有任务进展/收敛证据。

11000 cp只读诊断1159样本（固定规则包含全部末25步）：200末端附近样本absTD.320213、
actorQ−behaviorQ2.052449、策略维度饱和率37.7%；959远端样本absTD.0217425，最新回合
145样本absTD.401190，温度.00580246095。5500 cp末端absTD.928903不能直接作为同样本
改善率：样本数/轨迹/条件/归一化均变化。末端动作外推与残差值得继续查，但不是独立真实Q证明。
诊断无梯度/仿真/保存，checkpoint/RNG/normalizer不变，内存峰值895,913,984字节，exit0。
初次服务0738漏设WorkingDirectory，Python在/home/airpig找相对tools路径而exit2，未执行诊断；
在独立0738b服务明确工作目录后完成。失败与修复均写入归档收据，没有重启现有trainer。

已核验服务器最终归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-close-20261016T0738/evidence.tar.gz`，
272,146,819字节，SHA256 `dbc33e71d76da775d82c56017adc2435ad076f87ab3f1553f13d72895885c662`。
包内含第8回合原始数据、cp11000、最终training/optimizer/execution/PROTOCOL、
`IMPEDANCE_CREDIT_0011000.json`、`IMPEDANCE_REWARD_20261016T0738.json`和
`IMPEDANCE_CLOSE_20261016T0738.json`；后者保留8回合carry结果、收敛筛查、协调器快照、服务证据
与初次诊断失败。前7回合/checkpoint分包索引见下文；服务器只归档。导纳新轨迹仅本机。
四族均未满足前瞻收敛标准，GPU完整循环验证仍等stage01正常完成；Goal active、无最终acceptance。

## 15:26 CST：GPU训练路径已实现，等待现有阶段安全闭合后验证完整循环

开工核对main `3c9b58b60787344d46b31792e9f32942e7b3e51b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`与AGENTS/日志。上一轮GPU探针是实质进展。
同一CPU阻抗trainer2344947与协调器2329290活跃；9750步/4751更新、7完整55秒回合，
Task/Strict0/7、physical_valid7/7，第8在途。新两回合return−25.1302849/−26.3649992，
cp8250/9625 hash与冻结source/parameter manifest通过；其他方法状态未冒称成功。

新增后端模块与显式登记路径：普通历史CPU行为保持；GPU必须登记资源、实际JAX平台为gpu、
实际亲和性等于登记CPU（训练1，丢弃预检6）。CPU checkpoint跨到CUDA必须有明确迁移字段，
不偷偷降级回CPU。weights/optimizer/RNG/normalizer/raw replay保留，但浮点轨迹不保证逐位相同。
训练PROTOCOL/execution记录learning_backend、compute_runtime与内核memory快照；模拟器
子进程仍显式JAX_PLATFORMS=cpu，物理/MJB/dt5e-5、actor48、filter、gate、奖励/UTD1不变。
GPU0要求入场free≥4096MiB/温度<80°C，回合边界重新检查；JAX_PREALLOCATE=false、
MEM_FRACTION=.125仅为JAX池限制，不是整个GPU进程的硬显存封顶。主存3GiB/swap0硬限保留。

`rl_goal_stage_20261016.py prepare-gpu-preflight`须等待前序四方法均正常闭合并逐checkpoint
核验，才创建全新目录/源码快照/登记，各最多1375新增交互、合计5500、24小时派发保护。
逐族`probe_goal_credit_20261016.py --root <GPU阶段> --job <name>`必须实际CUDA、CPU6、
正确env下执行；正常检查25步终止窗口、原始replay、一次有限丢弃更新与cp hash后封存四族
预检，仍沿用全局仿真锁/单路/内存磁盘准入，不能从prepared直接冒充已派发。
这四回合是实际训练并保存独立checkpoint；只有四族各完整1375步/55秒、实际GPU/亲和性
匹配、OOM/kill0、swap0、峰值≤3GiB，才可用prepare-next准备常规11k续训。短回合/物理
提前失败保留，只能另登记有限GPU验证阶段继续，不以短回合推断完整循环内存通过。
普通GPU续训绑定完整循环验证的registration/execution hashes；后端切换不是奖励或最终gate变化。

当前真正调用prepare-gpu-preflight被活动stage01正确拒绝，
`outputs/rl_goal_gpu_preflight_20261016`不存在；没有GPU训练或额外等待服务。
既有`rl_goal_tracking_pilot_20261016`保持原CPU登记与冻结来源，未改写它的内容；新代码也为
未来显式GPU的fresh pair增加了真实GPU预检检查，但现有pair没有转换。下一步先完成在途
stage01；之后做独立GPU完整循环验证，再依据结果登记后续训练/奖励比较。

40项Goal测试＋5项恢复测试通过，覆盖未登记GPU/环境漂移/假绑核/未授权恢复拒绝，
GPU命令资源边界、父源与物理保持、全四族完整回合/无OOM门槛、短回合拒绝常规续训及有限
重试；trainer/dispatcher/后端编译通过。真实`GPU_BACKEND_GUARD_REGISTRATION_20261016T0721.json`
另登记102次CUDA丢弃更新，绑定backend guard源码hash
`60ffe466ae747b1cd7198faca20454e098958016ff5ce326d2eb4cd91a1f981d`，
同6875 cp、CPU6/2GiB/swap0/180秒，无仿真/模型写回。guard实际平台/设备/亲和性检查通过，
102更新有限、cp hash不变、exit0，主存峰值1,293,684,736，OOM/max0，GPU快照48°C/1425MiB。
计时286.83更新/秒为另一时点固定batch测量，不能把差异因果归到allocator fraction，也不是
完整训练循环或成功策略证明。guard预检已退出；CPU原训练持续推进。

第6/7原始回合、cp8250/9625、所有本轮源码/测试与GPU guard登记/结果和
`GPU_BACKEND_IMPLEMENTATION_20261016T0724.json`快照打包为
`/tmp/rl-goal-gpu-backend-implementation-20261016T0724.tar.gz`，534,028,451字节，
SHA256 `84534fda395ebba80b0b97ec9dbfaea450f2799f2c81313974e64e03d6b60f0e`。
已核验incoming大小/hash并发布至不存在的独立最终目录，再次核对最终SHA256一致：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-backend-implementation-20261016T0724/evidence.tar.gz`。
服务器仅传输/归档/hash。快照9625步/4626更新，memory.current
3,047,575,552、peak3,221,225,472、memory.max事件477、OOM0/swap0。内存回收压力增加，
没有放宽限制或重启。第8回合仍仅本机，Goal active，尚无收敛/最终验收。
收尾复核systemctl --user与实际PID一致，同一trainer推进至10500步/5501更新，temperature
.00606476；memory.current3,176,308,736、max事件565、OOM/kill0，第8回合仍在途。

## 15:10 CST：GPU丢弃更新探针通过，下一阶段可准备完整循环验证

开工核对main `5fbc2cbce35d2e923405fee9952b9478592f7850`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及AGENTS/日志。上一轮为实质进展；
本轮继续同一阻抗PID2344947，execution8000步/3001更新、optimizer8095步/3096更新。
第5回合完整55秒、return−25.6329256，Task/Strict0/5、physical_valid5/5；6875 checkpoint
全部hash通过。第五回合是第一个全程过热身的回合，最后10秒仍cursor20/28，误差
12.528–12.727mm，位置/重入均0/250通过，姿态/速度250/250通过；未解决carry阻塞。
末10秒实际参数中位数约[281.68,76.47,1.482,.662,1.155]，energy_scale均1，参数确实在变化。
Direct有限阶段0/8不变，导纳/VMC仍排队，fresh tracking pilot仍prepared；无最终验收。

前四回合奖励诊断保存`IMPEDANCE_REWARD_20261016T0700.json`（第5当时尚在途，明确排除）：
折扣payload势函数均−.56023853，抵消残差<4e-15是预期公式；折扣tracking罚约−.0951至
−.0957，峰矩罚−1.5898至−2.5828。相近失败回合的return变化主要来自峰矩，不能当收敛。
只读5500 checkpoint诊断`IMPEDANCE_CREDIT_0005500.json`共1021训练样本，含100个
末25步样本，后者absTD.92890、actorQ−behaviorQ2.10443；远端921样本absTD.02553。
终止4条absTD1.26775，温度.00956434；clip概率质量均值.00025095。早期末端拟合仍不足，
但这不是独立真实Q或因果归因。无梯度/仿真/模型保存，RNG、normalizer、cp hashes不变，
诊断exit0、峰值1,104,183,296字节；只包含501次已有训练更新的checkpoint。

为解决当前CPU更新吞吐，新增`tools/probe_goal_update_backend_20261016.py`：
读取同一6875 cp，用固定seed20261016抽同256索引，分别在CPU/CUDA加载后做2次预热和
100次计时的丢弃更新；102次更新全部有限、原checkpoint不变，无模拟器、无模型保存。
现有环境已有jax/jaxlib/jax-cuda13-plugin/pjrt均0.7.2，无依赖安装或环境修改。
初版只设AllowedCPUs，未进程内验证，CPU时间62秒超过wall10.8秒，不作为单核对照；
其原始源码和结果保留在包内`rl-update-probe-initial-20261016T0705.tar.gz`。
登记修订`UPDATE_BACKEND_PROBE_20261016T0706.json`明确额外预算204，总计最多306次，
CPUAffinity=6且进程内assert亲和性[6]，两端串行、2GiB/swap0/最长180秒，初次失败保留。

修正后的CPU实测100更新25.7364秒（3.88555/s），CUDA100更新.52243秒（191.41469/s），
优化器吞吐49.263倍；CPU首次预热4.165秒、GPU45.799秒（包含编译）。主存峰值分别
1,395,916,800与1,411,497,984字节，OOM/max均0，swap0。GPU设备为RTX5080Laptop，
快照46°C/1424MiB为整机显存占用。相同batch索引/checkpoint hashes通过核对；首更新
critic loss差1.9e-6，actor entropy差约1.05e-4，不能声称逐位一致或同轨迹复现。
这是固定batch吞吐，不含物理仿真、IPC、在线归一化、采样/完整训练循环，不能声称整体49倍。
下一步应实现显式登记的GPU训练后端、验证完整训练回合和内存后在安全边界使用；
当前stage01和既有fresh tracking pilot均未修改、未重启，不能改写它们的冻结配置冒充原实验。

已核验归档（服务器只传输/大小/hash）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-learning-20261016T0704/evidence.tar.gz`，
267,168,254字节，SHA256 `762955989867d078a223f6619a07eaecfdacefc6c50a76b95a658fcd414e549e`；
含第5原始回合/cp6875、奖励/credit/carry诊断与源码、当前快照。快照训练memory.current
2,909,458,432，peak3,135,127,552/3GiB，OOM/max0/swap0。
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-backend-probe-20261016T0709/evidence.tar.gz`，
11,214字节，SHA256 `05d90a7d7c441719cdb68a3ee11d888661175f11a025fb0d16180e9173fa39e2`；
含完整初/修订探针源码、登记和三次结果。探针已全部正常退出，无后台探针或传输待收尾。
第6及后续回合仍仅本机，待安全边界归档；Goal active，未收敛/未完成。

## 14:53 CST：阻抗进入梯度更新，carry停滞已有可复算定位

开工核对main `9348836f2d03fde25b3a8f5977340dbddfa1c663`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`和AGENTS。Goal保持active，当前阶段
未结束，Direct仍0/8；admittance/VMC排队，fresh tracking pilot仍prepared未派发。
阻抗同一PID2344947于5000步开始第1次更新，5500步/501更新checkpoint hash通过，
最新观察5769步/770更新；第5回合在途。4个完整55秒回合return依次−25.493412、
−26.067121、−25.072284、−24.997477，Task/Strict0/4、physical_valid4/4。
不同条件且前三仅热身，不能把相近return当收敛，或按回合顺序认定训练改进。

新增`tools/diagnose_goal_carry_stall_20261016.py`与3项测试：检查冻结source hash，
对齐前一行post-step手位置和当前pre-step canonical error。重建目标严格匹配route，
防止相差一个控制周期的错位推断；覆盖半径与横向平面不同逻辑、最终点禁止平面捷径、
错位输入拒绝。四回合最后10秒各250样本全部在carry cursor20（28点中的第21点），
到达半径与forward平面条件均未满足；姿态<.12rad与速度<.025m/s均满足。
前三热身误差12.605–13.414mm，forward仍在点后4.436–6.425mm；第4回合含501次更新，
最后10秒仍12.737–13.002mm、forward−5.417至−4.790mm。三个planner/observation源
hash与执行记录吻合，路径重建误差0。末10秒energy_scale均1，参数确有变化。
注意canonical[26:32]是command−twist，不是原始twist；本工具直接使用明确的原生速度字段。

原生rollout的unknown-edge接触从10.12–11.02秒持续至55秒，累计43.98–44.88秒，
都发生在carry。该证据提示障碍接触/路径阻塞，尚未证明刚度单因果或可通过增大刚度解决；
不得调整最终gate，也不能把25Hz采样推断当全部物理子步证明。零action7是native阻抗
后端输出语义，实际5维parameter_actions存在；原生训练审计未替代最终统一验收。

`CARRY_DIAGNOSTIC_20261016T0650.json`保存前三热身回合（真实创建06:47Z，文件名仅标签），
`CARRY_POST_WARMUP_20261016T0649.json`保存第4回合；
`IMPEDANCE_CHECKPOINT_20261016T0649.json`保存execution快照、四checkpoint校验、
optimizer首尾与资源。归档快照optimizer最后5614步/615更新，所有已记录更新满足UTD1且
指标有限；温度0.00946349。内存2,736,730,112、峰值2,897,244,160/3GiB，OOM0/max0/swap0。
打包仅本机CPU6/1GiB/swap0、exit0，无模拟器；训练保持CPU1单路。GPU44°C/526MiB为
主机观测，不是训练用GPU。另查旧v3–v6协调器各单task，未改动无关服务。

四完整失败原始回合、cp1375/2750/4125/5500、捕获日志、诊断及源码/测试已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-20261016T0649/evidence.tar.gz`，
846,865,888字节，
SHA256 `6c87112421ddc26b3b3bb66ce090cf66ac0da0a0fd8612c0df1bae4a2fd30e10`。
上传后核验size/hash，再从独立incoming目录发布至不存在的最终目录，复核最终hash一致。
本地包`/tmp/rl-goal-impedance-20261016T0649.tar.gz`保留；第5及后续回合不在本包。
14:54观察6250步/1251更新；旧v3–v6均在等待failed Direct子服务（子服务MainPID0，
其他子服务inactive），不是四个并发训练；未更改这些旧收据/服务，当前只有一个阻抗模拟器。
后续继续观察学习回合、保存失败，再按已登记顺序接续导纳/VMC及fresh奖励对照；
本次定位不是修复完成或Goal完成，不做最终acceptance。

## 14:35 CST：Direct完整阶段证据保全，阻抗继续热身

核对main `9358461c2daae6e8cd629eeca3592342d133cdcb`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS及日志。上一轮登记/真实预检为进展；
本轮真实服务仍active，补齐归档并读取闭合训练诊断，未重复训练或改活动快照。
Direct8回合都停approach，native AUDIT的目标XY误差190.62–220.24mm，Task/Strict0/8。
补齐最后四回合episode41–44及cp57406/58781/60156/61531、整个阶段training/optimizer logs、
PROTOCOL/最终execution；所有checkpoint hash和source/parameter manifest通过。
`DIRECT_CLOSE_20261016T0623.json`包含终态Direct、已有8个训练AUDIT、当时阻抗750步
快照、cgroup与收敛检查；它不是独立最终审计。

最终61,531 checkpoint的只读诊断完成：2127条样本=1024均匀抽样与全部45回合末25步的
去重并集，末端被故意增采样，不是总体无偏平均。终止45条absTD0.09649；末25步1125条
absTD0.10500、当前动作Q比历史动作高1.79795；远离终止1002条Q均值0.74485、target0.75985。
最新回合50条absTD1.92057，表明新数据仍未充分拟合。温度0.00093858，全部样本裁剪概率
质量约0.0009%；不能据此宣称真实Q高估、收敛或n25优于n1（前后样本组成不同）。
诊断服务`sii-rl-credit-final-20261016-0628.service` exit0，峰值1,077,571,584字节/OOM0；
无梯度更新/模型保存，checkpoint hash、RNG与归一化统计均未变；没有final/heldout访问。

14:34阻抗同一trainer PID2344947仍active，3000步/0梯度更新，尚在5000步探索热身。
已完成2个完整55秒回合，return−25.4934119/−26.0671207，physical_valid2/2、Task/Strict0/2，
第三回合在途。首回合抬升160.36mm但停carry、目标XY误差90.17mm、RMSE23.29mm；
属于原生训练诊断，不是最终独立指标，不能把早期阶段进展当成功。2750 checkpoint hash通过。
内存1,650,655,232字节/3GiB，此前OOM0/swap0。admittance/VMC尚未开始；fresh tracking
pilot保持prepared，等待原四族阶段全部结束，未新增等待服务或派发。

服务器独立目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-close-20261016T0623/`。
`evidence.tar.gz` 1,108,637,123字节，SHA256 `eeac5a2a0fe96e3c418a28873958525af94a4b11d2648a65412f2aa7b9c52062`；
`final_credit.tar.gz` 8,496字节，SHA256 `8ecd59850acb138616b03e0c8c037d00261a0b862bc26778f50781f49f5342da`。
两包最终远端hash均核验；首次传输自动审批超时，按提示重试完成，没有把超时当拒绝授权。
结合此前credit包的episode37、episodes38–40包，stage01 Direct全部8回合及checkpoint现已共享；
这不是更早所有历史训练的全量归档。阻抗新回合仍仅本机、待同步。Goal继续，未收敛/未验收。

## 14:21 CST：Direct阶段0/8，阻抗自动接续；fresh奖励对照预检完成

开工核对main `80c0b6133b48ae5c24f682b0c5f0ba30e02a83d0`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与日志。Direct正常结束该有限阶段：
61,531步/95,189更新，新增11k/11k；8个完整55秒回合Task/Strict0/8，physical_valid3/8。
末两个return−21.8339448、−39.4224188。最终61,531 checkpoint实际hash通过；原worker
已退出，原协调器PID2329290继续自动启动impedance_payload、PID2344947，真实250步/0更新，
处于登记5000步探索热身，不能因0更新误认卡住。admittance/VMC仍排队。Direct没有收敛，
原1M优化日程未完成；第5至8回合大型原始产物目前仅本机，待下一次同步。

奖励候选落实为独立`outputs/rl_goal_tracking_pilot_20261016/`两组有限对照：
direct_control与direct_tracking均从零初始化，不加载旧actor/critic/optimizer/replay/normalizer；
相同seed2026101421、n25/UTD1/1M日程、5000步热身、条件顺序、训练预算11k，合计22k。
唯一处理差异是tracking CONFIG。历史已续训Direct不能充当这个fresh对照组；两组原始reward
目标不同，报告效果应看匹配条件的Task/Strict、阶段与跟踪指标，不能用不同奖励数值作胜负。
本pilot最多各8个完整回合、单seed，只能提供可行性证据，绝不等于96回合收敛或四族完成。

登记SHA256 `42f101068a4185f7d920900de8b18f63720720436254fb3f2bbe4ab4cb7f3c91`，
截止2026-10-17T06:16:14.522695Z；硬限单模拟器/CPU1/1线程/3GiB/swap0、内存/磁盘准入不变。
前序`stage01`四族全部正常闭合且checkpoint吻合后，才能用本pilot冻结source中的
`rl_goal_stage_20261016.py launch --root <pilot绝对目录>`派发。launch和run双重检查前序，
仍持全局dispatch lock；当前只完成准备，没有LAUNCH/训练进程，没有创建额外等待服务。
通用四族收敛统计不能用于这两个pilot组；不能将这两组混入原四族lineage。

30项相关测试通过，覆盖fresh/同seed/仅奖励差异、前序在途/失败拒绝、缺失预检/错误处理拒绝。
真实running前序提前启动检查被拒绝，未创建LAUNCH。预检服务
`sii-rl-tracking-preflight-20261016-0617.service`正常exit0，峰值1,357,033,472字节、OOM0，
CPU6/2GiB/swap0；同一历史1375条训练transition分别灌入临时fresh模型，各一次丢弃更新。
actor/critic/target critic/temperature初始hash完全相同，n25末端窗口独立复算通过、指标有限、
源checkpoint hash未变；没有模拟器、模型保存或训练收益证据。冻结manifest与总预检均复核通过。

源码/测试、完整冻结source/parameter、REGISTRATION和CREDIT_PREFLIGHT已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-pilot-20261016T0618/evidence.tar.gz`，
2,318,827字节，SHA256 `948a868c5ff1a10fdcb237eef83def388055b665c32757b92446175d09e488ca`。
预检所读历史51,906 checkpoint在此前credit归档中；本包不重复其大型replay。
下一步跟踪阻抗的真实steps/updates与完整回合，然后依次收尾其余方法并启动已准备的对照。
Goal active；训练收敛、统一acceptance和独立最终审计仍未完成。

## 14:10 CST：密集tracking组件完成，尚未启动新奖励训练

核对远端main `e47c4164013760b1d0c30d90eb7f6d85780b287a`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS及日志。同一协调器/Direct worker活跃，
14:09 optimizer60,090步/93,748更新；六完整回合Task/Strict0/6、第七在途，其他三类排队。
58,781 checkpoint、冻结source/parameter manifest通过；内存3,168,563,200字节、OOM0，
硬限回收max1371，3GiB/swap0保护继续，不重启活动作业。

新增`goal_tracking_reward_20261016.py`，采用已有metric中的权重4与.12m误差尺度，只增加
`-4*sum(dt/55 * error²/(.12²+error²))`，不增加torque/slew项，也不改变Task终止奖励。
提前失败加上剩余完整/部分RL interval的gamma折扣最坏成本；gamma.9995、RL dt.04s和
55s时间窗保持。全回合附加成本在[-4,0]，不是可通过拖延刷取的正奖励；并不声称最优策略
不变，密集成本有可能影响取舍，需真实训练和最终任务验证。

trainer仅从显式Goal job `tracking_guidance`读取固定CONFIG，且限定Direct/office_task/
task_safety组合，避免叠加已有metric成本。未登记保持旧行为。恢复前比较父子tracking配置，
禁止旧reward replay/normalizer直接续到新目标；未来试验优先全新同seed对照，而非无依据
保留已学critic和旧奖励。收敛统计fingerprint包含tracking配置，不能混合不同目标回合。
现有prepare-next仍是原配置精确接续入口，不能用它暗中部署这一处理；新处理尚未登记/派发。

27项Goal相关测试通过（新增密集成本方向、剩余分数步、gamma1/.9995/.9、提前失败、
参数边界/非有限值、旧新恢复拒绝、收敛统计拒绝tracking漂移）；trainer编译通过。
用五回合冻结完整日志执行真实奖励复算，结果`TRACKING_COUNTERFACTUAL_20261016T0610.json`：
episode37与40原折扣回报同为−11.4082118，候选变为−13.9029927/−11.6288941；
所有原Task/Strict失败标签保持。仅算术反事实，没有新轨迹、模型更新或checkpoint/replay改写，
不能当成策略收益改善。下一步在独立有限新处理登记后做实际训练比较，当前stage继续。

源码/测试/复算结果与完整输入快照已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-component-20261016T0610/evidence.tar.gz`，
1,239,902字节，SHA256 `bbe188dc15aa95c10bdf4c1930733cee1e9513349754cbf552bb9089638f6c1e`。
Goal仍active；四方法收敛、统一acceptance及最终独立审计都未完成。

## 14:01 CST：奖励分解给出下一阶段调整依据

核对main `ea271110dc9ef16da2047e2df8fa374eefa8cc28`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS与远端日志。上一轮归档为进展，
本轮补齐`diagnose_goal_reward_signal_20261016.py`及3项针对性测试；只读训练数据。
快照五个完整回合的奖励组件、gamma、终止label、逐步连续性和势函数抵消全部通过。
每1375步只有1个Task reward非零（−20），n25中只有25/1375=1.818%窗口直接包含终止奖励；
这不是说其余步没有shaping信号，也不是说多次bootstrap无法传播奖励。
折扣shaping和都是−0.6249994097574，残差<1e-15；此抵消是有意设计，无需删除终止抵消。
安全罚分依次0/−12.5152096/−17.7244568/0/−13.9713077，跟踪error项当前为0。
两个零安全罚分回合的有界跟踪cost0.8902505与0.0720529，折扣总回报却相同；
五回合reference potential最大值都停留在初始0.12499988，原生AUDIT都在approach。
这表明当前训练目标在这些安全失败轨迹间无法持续奖励更好的跟踪；尚未证明是唯一根因。

下一阶段优先检验已有有界密集tracking项（训练奖励），最终Task/Strict不变；但更换奖励
不能直接续用旧raw reward replay/normalizer假装同目标精确恢复。须单独登记、重建或隔离
旧奖励数据，并保留原处理组，不能把当前immutable stage就地改掉。尚未部署新reward。

14:00同一worker仍active，58,781步/92,439更新、阶段新增8250/8250；6个完整回合Task/Strict
0/6、physical_valid2/6，第6return−22.475132，第7在途，其他三方法未开始。58,781 checkpoint
实际hash通过。memory.max事件1162，OOM0/swap0，继续监测硬限回收与实际吞吐。
新诊断保存全部捕获execution/protocol/closed logs及已有AUDIT/hash，明确未完成回合。
工具/测试/快照已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-reward-signal-20261016T0600/evidence.tar.gz`，
1,225,327字节，SHA256 `30a9b7c1c8e615098a3d7d2596684e03e5a865e236fa7c74400f34e43e4db9c6`。
第五回合之后原始大型产物仍仅本机、待同步；Goal active，未收敛、未最终验收。

## 13:55 CST：五个完整失败回合，补齐大型证据归档

实时核对main `436552af7c5417c9033ffd87dfb26ce8e5707559`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、两分支日志及AGENTS；Goal仍active。
同一协调器PID2329290、trainer2329294真实运行；57,750步/91,408更新，阶段新增7219/7219。
五个完整55秒回合依次return−21.667945、−34.277519、−39.487075、−21.871979、−35.653907；
Task/Strict联合0/5、physical_valid2/5，第6回合repair_train_017在途。其他三方法仍排队。
57,406 checkpoint hash核验通过；第5回合原生训练AUDIT同样停在approach，max_lift0、
目标XY误差192.09mm、RMSE803.36mm。不同条件的回报不能直接证明n25有效或无效；
目前无成功样本，不能称收敛。未执行最终统一acceptance或独立最终审计。

worker MemoryCurrent3,151,167,488字节/MemoryMax3GiB，memory.events max434，OOM/kill0、
swap0。此前增长有较多file缓存；现已出现硬限回收压力，继续观察实际吞吐和OOM，不移除保护。
本轮完成episode38–40全部原始轨迹和checkpoint53281/54656/56031的归档，附05:46Z
execution/收敛统计/优化器奖励窗口/训练AUDIT/资源快照及生成脚本；source/parameter manifest
和这三个checkpoint均已核验。服务器最终文件大小与SHA256一致：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-episodes38-40-20261016T0545/evidence.tar.gz`，
835,219,332字节，SHA256 `77b7fca926a438e8c83a96ae2e01a0c1f075420aae69e1340916112dc61860e4`。
episode37此前已独立归档；episode41及之后仍仅本机、待同步。服务器无计算，无重复训练。
本轮为运行核查与失败证据保全，未新增训练算法修复；下一步看有限阶段完整结果与自动接续，
再依据已有动作外推/approach失败证据登记后续调整，持续Goal不因本轮结束而完成。

## 13:39 CST：收敛统计检查落地，训练仍未满足判据

本轮核对main `dee4c4ba65b5866d1e31fe0d15122c34da47d384`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read日志与AGENTS。上一轮完成了精确
接续能力和真实恢复验证，属于进展；本轮保持同一协调器/Direct worker运行，没有重复派发。
13:39 optimizer已记录55,804步/89,462更新；最近已闭合checkpoint为54,656步，hash通过。
本阶段3个完整55秒回合return−21.667945、−34.277519、−39.487075，均值−31.810846、
总体标准差7.480807，Task/Strict联合0/3、physical_valid1/3，第四回合在途。
temperature最新约0.00058627；这些早期样本不是收敛或调参有效的证明。

新增`screen_goal_rl_convergence_20261016.py`落实先前登记的96回合、两个32回合窗口、
各窗全32训练条件覆盖、各窗Task AND Strict≥90%、均值漂移≤5%、末窗CV≤25%判据。
均值相对漂移明确定义为abs(new_mean-old_mean)/max(abs(old_mean),1e-12)，CV为总体标准差/
max(abs(mean),1e-12)；负回报同样处理。此数值解释在任何合格窗口出现之前固定。

沿新阶段的hash绑定lineage，只累加每段自己的闭合rows，不相加累计episodes/steps；
Direct旧n1继承的37回合不能混入本n25收敛统计。早期失败/非完整回合仍在分母，在途回合
单独保留；重复、缺失、乱序、跨奖励/agent配置拼接和缺失父方法证据会报invalid_evidence。
每份统计保留实际读取的execution与protocol快照/hash，以免活动文件后续更新导致无法复核。
统计的training_candidate即使为true，也始终不代表最终acceptance或Goal完成。

8项有针对性的测试通过，覆盖失败reward平台、Task/Strict不同时成功、条件缺失、样本不足、
均值漂移/方差、失败分母/在途回合、重复/非有限值、精确接续计数和奖励漂移拒绝。
真实阶段检查结果：Direct样本3、联合成功0；其余三类not_started，all_training_candidates=false。
统计工具只读训练收据，无仿真、无梯度、无模型选择或最终验收。
worker内存2,913,398,784字节/上限3GiB，随后memory.stat约1.97GB anon和0.92GB file缓存，
OOM/oom_kill=0、swap.current=0；系统可用内存约5.54GiB。继续观察硬限，不移除保护。
本轮源码/测试/完整统计快照已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-screen-20261016T0539/evidence.tar.gz`，
41,304字节，SHA256 `45442e7ee148cdc6cd734afe9594700778551612fd30f9837809b2b14f7ca311`。
服务器只归档/hash；第二个新回合之后的大型轨迹/checkpoint仍本机待同步。

## 13:31 CST：四方法精确接续能力完成，当前阶段继续

开工核对main `24fd0bd0dc6fda266053bcee6b7ddf7dd23dcd1b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`、AGENTS和两分支日志。上一轮新增真实诊断证据，
属于进展；本轮同一stage/worker仍active，持久化54,500步/88,158更新，新增3969/3969。
已结束2回合Task/Strict0/2，第三回合在途；另外三类排队。13:31 worker内存2,604,490,752
字节、峰值2,685,267,968，3GiB/swap0，OOM0。较早快照中约645MB为文件缓存；不能仅凭
memory.current上升就断言模型内存泄漏，也不能忽略后续硬限压力。

此前阶段工具只支持Direct从n1迁移、其他三类从零启动，不能用它反复重开来代表累计训练。
现增加`prepare-next`：必须四类都完成上一有限阶段、无未结束回合、trainer与协调器终态
一致、各自最终checkpoint和父execution hash匹配，才准备独立新目录。每类从自己的n25
checkpoint保留原始replay、网络/优化器/RNG/normalizer，仍各新增11k/1M日程，24h派发保护。
复制上一阶段的冻结trainer/worker/物理代码与parameter；仅替换协调器和预检工具，内容清单
重新登记。不同超参数、最终不足11k的尾段或异常恢复，须另按证据登记，不能混入这个精确接续入口。

后续工作顺序：`rl_goal_stage_20261016.py prepare-next --previous-stage <已完成阶段> --root <新目录>`；
在同样硬限的独立本机预检服务中，按新目录冻结工具依次运行
`probe_goal_credit_20261016.py --root <新目录> --job <四种方法各自name>`；
四份真实预检收据齐全后`seal-preflight`，最后才允许`launch`。预检只做一次丢弃的更新、
不保存新模型；登记hash、checkpoint hash和方法身份逐一绑定，缺任何一类就不能launch。
每个新阶段由Goal根据上一阶段证据决定，不自动建立无界队列，也没有acceptance入口。

15项相关测试通过，新增4项覆盖四族独立继承、活动/失败/缺失/未闭合父阶段、checkpoint篡改、
四份预检及hash绑定。对当前真实running stage调用prepare-next，正确拒绝，未创建stage02。
独立53,281步checkpoint的同配置n25恢复探针通过：53,281条raw replay、恢复后采样RNG逐项
可重复、一次更新指标有限、原checkpoint hash不变；exit0、峰值1,128,882,176字节、OOM0。
这只是Direct真实恢复验证；另外三类尚无本阶段checkpoint，其真实预检尚未完成。
活动stage01继续使用原冻结快照，当前未创建或派发下一阶段，未证明收敛、未做最终验收。
本轮源码/测试/两项真实检查脚本与收据已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-continuation-20261016T0530/evidence.tar.gz`，
14,259字节，SHA256 `bcde86e186923ad2679e97160ee328eb8018216cb0a5d405928c4f0c0b466ea9`。
服务器只归档/hash，53,281 checkpoint本体及后续原始轨迹仍在本机待同步。

## 13:22 CST：目标分布与动作外推诊断

本轮核对远端main `02053647aba71bc623b0c53fe65d60fc002a8f5b`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并fetch/read日志和AGENTS。上一轮是实质进展，
本轮确认同一协调器、trainer和唯一模拟器仍活跃，没有重新派发。第二个完整55秒回合已结束，
到53,281步/86,939更新，本阶段新增2750/2750；return分别−21.667945、−34.277519，
Task/Strict0/2、physical_valid1/2，第三回合已启动。第二回合完整结束但物理有效性失败，
不能因无abort而算成功；原始失败收据保留。

新增`tools/diagnose_goal_rl_credit_20261016.py`，对固定51,906 checkpoint作训练replay只读诊断。
没有新仿真、梯度更新、模型保存或最终测试数据。固定seed取1024个均匀索引，再加入38个回合
各末25步，去重共1948条；末端样本被刻意加权，整体均值不是replay总体的无偏估计。
独立复算上游categorical Bellman atoms的裁剪后期望与被裁剪概率质量，保留entropy项；
采用当前actor一次固定随机样本和保存的target critic，不把它当作真实最优Q。

|训练样本组|样本数|历史动作Q均值|投影后target均值|绝对TD残差均值|当前动作Q减历史动作Q|
|---|---:|---:|---:|---:|---:|
|真实terminal|38|−2.7672|−2.8679|0.1018|2.4470|
|距terminal不足25步|950|−2.6652|−2.8527|0.1884|2.5416|
|距terminal至少25步|998|2.6072|2.6576|0.0848|0.0784|
|最新完整回合子样本|57|0.9657|−0.0536|1.1743|0.0446|

整体被裁剪概率质量均值0.00006649（0.006649%），terminal组0；这次样本不支持支持集
边界截断是主要原因。当前动作维度中abs(action)>.95占33.43%，历史动作6.74%；在末25步
当前策略的Q比历史动作高约2.54，而新回合TD残差明显较大。这提示历史replay分布外动作
估值及新回合信用回传值得继续查，并不单独证明实现bug，也不构成n25的因果优劣比较。
当前非末端entropy修正均值−0.00388，远小于正Q量级；历史MC仍不是当前soft-Q真值。

2项独立目标数学测试通过。真实诊断exit0、峰值924,012,544字节、OOM0，运行在CPU6/
2GiB/swap0/180秒有限服务；模型文件hash、normalizer计数与模型RNG均未改变。
13:20训练worker内存2,324,885,504、峰值2,351,804,416字节，3GiB/swap0硬限、OOM0；
系统swap已满是既有宿主机状态，worker实际swap.current=0。GPU44°C、513MiB，仅作资源观测。

下一步保留本次登记的n25阶段，检查后续回合/四方法队列。若terminal附近历史拟合继续良好
但当前动作高估及新轨迹失败持续，再在新有限阶段登记replay分布/actor或entropy调整；
不因单个回合就中途更改活动源码。当前四方法均未证明收敛，最终acceptance仍未运行。
本轮诊断工具/测试/结果/监视快照、首个新完整回合原始轨迹及51,906 checkpoint已归档核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-20261016T0518/evidence.tar.gz`，
264,505,895字节，SHA256 `f4a47b6801fae4d367caebb92dc2e0fd48765e9117feae4ac45d7ff2f1bec7dd`。
本机/服务器hash一致，服务器只归档；第二回合及之后新checkpoint/轨迹仍本地待同步。

## 旧恢复批次最终事实

`rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety`在12:41:42安全退出，
50,531步/84,189更新、累计37回合；本段新增6875步/6875更新、5个完整55秒回合，
Task/Strict均0/5。return依次−22.1773、−35.2090、−38.6078、−40.0133、−22.1345；
仅2/5 physical_valid，3条安全失败全部保留。最终checkpoint_0050531逐文件hash通过。
status=complete仅表示旧有限段已结束，training_complete=false，不代表训练完成或收敛。

## Stage01：检验长回合信用分配

历史在线2×2 n-step研究在第一组n01尚未完成时停止，n25没有在线结果。当前n1 checkpoint
多数terminal目标已拟合、非终止Q却与历史行为回报差异明显；这构成信用分配候选依据，
不是证明实现错误。采用已有上游SimbaV2的25步critic和已测的跨回合安全replay reducer。

这次只调整n_step=1→25，UTD保持1，reward/gamma/学习率/动作接口/物理均不变。
Direct从旧50,531步checkpoint迁移，保留网络/优化器/RNG/normalizer/原始单步replay；
只在采样时生成25步回报，遇terminal立即截断，无跨回合拼接，不伪造奖励或成功样本。
其余三类使用登记的payload reward从头训练，所有raw reward和失败轨迹保留。
25步未作离策略校正，存在行为策略偏差；本阶段没有匹配的从头1步对照，不能声明因果胜出。

|顺序|方法|起点|本阶段总步上限|新增交互上限|
|---|---|---:|---:|---:|
|1|Direct/task_safety|50,531|61,531|11,000|
|2|Impedance/payload|0|11,000|11,000|
|3|Admittance/payload|0|11,000|11,000|
|4|VMC/payload|0|11,000|11,000|

四类优化器总日程仍为1M交互，表中是有限阶段节点，不缩小持续Goal的完整训练目标。
完整回合边界限制可使实际交互小于上限。队列串行、每回合保存、worker硬限3GiB/swap0/
CPU1/数值线程1，协调器独立256MiB。进场要求可用内存≥3GiB+768MiB、磁盘余量≥50GiB，
同一派发锁及宿主机worker检查防重复。阶段派发保护截止2026-10-17T05:00:57.926303Z，
即10月17日13:00:57 CST；这是agent登记的有限保护，不是“到时算收敛”。

代码以独立source快照运行，允许后续Goal继续修复仓库而不改动活动worker的源码。
阶段没有acceptance入口，子作业错误会向上传播并保存失败，而不是让协调器假报成功。

## 可复核的收敛要求

在本阶段训练开始前登记：至少96个结束回合，最后两个32回合窗口均覆盖全部32个train身份，
两窗口return均值相对变化≤5%、末窗口return变异系数≤25%，且每个窗口Task AND Strict
同时成功率≥90%。所有失败均入分母；这只是训练收敛候选筛选，最终仍需四方法训练完成后的
统一acceptance与独立物理/动作重放/hash/指标审计。当前样本远未满足，不称已收敛。

## 启动前验证与当前入口

9项恢复/阶段约束测试、4项现有多步replay测试通过。真实50,531步checkpoint预检验证：
agent与上游critic确为n_step25；末25条transition的折扣奖励与独立求和一致，next_state均
止于真实terminal；恢复50,531条原始replay后一次优化更新指标有限，原checkpoint hash未变。
预检无新仿真、不保存模型，exit0、峰值1,161,908,224字节、OOM0。

本地阶段根：`outputs/rl_goal_20261016_stage01/`；登记SHA256
`661ffad196a667731bf34c9bb3855eb6ec81070bd5a6393b06a41f5b5443fcf1`。
协调器`sii-rl-goal-stage-3ced1757b345.service`，Direct worker
`sii-rl-goal-2dc62bfe00c9.service`已启动，接续状态见阶段execution与各方法execution。
其余三方法是明确队列任务，不把排队写成已经训练。停止使用本阶段STOP_REQUESTED，等待
在途回合/检查点保存，不停止仍有子模拟器的父容器或广播信号。

开工main `11809cb960cb4acdcb6ebe1a431d622979d2a3ec`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`已查询/fetch/读取，保留无关未跟踪文档。
13:11:34首个完整55秒回合结束：新增1375步/1375更新，到51,906步/85,564更新。
return−21.667945，physical_valid=true，Task/Strict均false；checkpoint_0051906全部hash
核验通过，agent与replay保存的n_step均25，第二回合已启动。这证明新训练/保存链路闭合，
不是收敛证据，不能将单个不同condition的return与上一段直接做因果比较。

新阶段源码快照/登记/预检/启动及13:07监视收据、旧恢复全部5个完整回合原始轨迹和
最终50,531 checkpoint已归档核验至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-stage01-20261016T0507/evidence.tar.gz`。
大小750,006,095字节，SHA256
`a65bf3966e17f1a38beb244cfa7983a40a7e9bb54f7f5b8f851ee3dda38ff13a`，本机/远端一致。
服务器只传输/归档/hash，没有训练或分析计算。新阶段51,906 checkpoint及新回合轨迹仍仅本地，
留待下一次安全边界归档；原始物理runtime/MJB仍依赖登记的既有路径，此包不是完整环境镜像。
## 2026-10-17 09:15 CST — occupancy阶段收口与四族接续准备

- `rl_goal_stream_occupancy_20261017_v2` 的 control 与 occupancy 两臂均已完成 44,000
  interactions、39,001 updates、32 个完整回合；两臂 Task/Strict 都是 0/32，未达到
  training candidate 的 96 回合/双窗口/90% Task AND Strict 筛选条件，不能称收敛。
- 当前无活动 RL worker 或服务。已保留全部失败回合、checkpoint、resource 和 storage
  receipts；occupancy 只读报告脚本已通过编译。
- 下一阶段将从 `rl_goal_selected_20261016_stage02_v2` 四类精确 n25 checkpoint 继续，
  先按登记协议进行四份 credit preflight，再以每族 11,000 interactions 的独立根启动。
  physics/MJB、最终 gate、canonical48 actor 输入、公共 filter、执行器限制和 dt=5e-5
  继续冻结；服务器仅归档。

普通 Codex cgroup 预检暴露 `memory.max=max`，四份预检均以失败收据退出；本机 GPU 驱动也
不可用。已在调度器中登记显式 CUDA→CPU 本机 fallback，训练仍必须通过 systemd 的
3 GiB/禁 swap cgroup。旧 GPU 继承 stage03 未启动且保留，新 CPU continuation 改用唯一根目录。
