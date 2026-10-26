# 2026-10-26 参数cycle9审查、Direct4及30路采样续训

原Goal active，尚未达到reward稳定且loss健康的收敛要求。本文更新此前
`RL_CYCLE07_VMC_RECOVERY_AND_SERL03_20261026.md` 的实时状态；不改变冻结物理、MJB、
gates、公共filter、执行器、dt5e-5、30条件及SPT reward。无子agent。

执行根目录B为 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
本轮fetch/read main=`a3670e267f546bd6c0b1905a923fca5ba36f91f9`，
baseline=`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。另一主机非RL第三条件27/108审计已读，
不干预其任务，也不把该条件/模型直接作为本集群最终ESN比较。

## 完整周期的新证据

| 方法 | 周期 | 累计steps / critic更新 | Task / Strict，各30 | 平均reward | 终端Q MAE | 末1000次Q loss均值 |
|---|---:|---:|---:|---:|---:|---:|
| 官方SERL Direct | 4 | 203962 / 1591704 | 0 / 0 | −32.559259 | 1.217256 | 见原诊断图，未用此表估计 |
| Impedance | 9 | 409500 / 404501 | 18 / 17 | −2.223415 | 15.377358 | 49.780140 |
| Admittance | 9 | 408500 / 403501 | 15 / 14 | −8.672159 | 7.494278 | 274.789183 |
| VMC，恢复pair后 | 8 | 368250 / 363251 | 17 / 17 | −2.819754 | 51.755224 | 725.854180 |

四份完整周期审查均通过：父replay所有字段前缀逐项精确，新增reward从冻结interval journal
逐条重建误差0，模型/fixture/计划及terminal一致，网络与optimizer有限。这里的审查不是重新计算
原始物理子步，也不等于冻结策略独立成功。三张新诊断图已目视核验。

Direct4新增40748条；29完整55秒，`passive_corner_train_0900` 第873动作因
`global_penetration_exceeded_2mm` 提前终止，approach失败保留在30分母。reward相较cycle3
−34.198有所改善，但仍0成功；抽样Q均值7.8565、TD MAE0.02008、alpha0.0006329。
150历史终端×10critic的误差中位数0.0417、p95=0.5805、最大33.9814，不能以低TD loss称收敛。
只读诊断完整网络/optimizer/RNG digest不变，0更新。

I/A9均新增41250，30完整、无abort。I的cycle7/8/9终端MAE3.649→9.121→15.377，
末Q loss3.505→13.585→49.780；reward近似稳定未代表价值网络健康。
A相较cycle8 reward有所回升，但末loss29.514→274.789、终端MAE3.926→7.494；
Q均值−41.523、范围−261.7至1430.1，不能描述为持续改善或健康收敛。
I/A原806847/806849按登记完成退出，cycle9只读2062385也已完成，不重启旧进程；
本轮没有登记或启动参数cycle10。

V8恢复pair后任务与reward略好，但Q均值290.486、p95=1935.853、最大2264.091，
末loss725.85，原target撤回不是修复。原1497979仍按登记继续9；约10:24 UTC快照402083步、
20完成/10在途/0待派。原只读2062386等待精确cycle9边界；不得按快照或等待超时重启训练。

精确checkpoint SHA256：

- D4：`f3bd281cd41643f8d9e038003e96302b42f8a42765c5f851ba35c50da6bc920e`
- I9：`e9fca1f0db39659ab33d30a5e93b328fd92a19612b3e1eef7b3c529827d23049`
- A9：`2a06d355cda30c3e47618d1fe232144aa251fec408a018f5cf0c2d1f45b1bb2b`
- V8：`57cba307e1c808397b580b240bad406508dafe17fbb7734d7c0705ef3e5228a8`

## Direct4审查器的失败与修正

`B/runs/serl_cycle04_review_20261026_v1` 的原协调器2062387已失败退出，并非仍在等待。
生成脚本时粗略替换 `==3`→`==4`，误将 `len(episodes)==30` 改成40。训练与准确周期归档没有失败。
原错误源码/日志保留；独立v2将冻结条件与回合计数显式固定30，重新执行只读审查并通过。
`CORRECTION.json` 还记录其他参数8/9待审脚本的30计数检查。没有重跑物理或训练。
新Direct5/6审查使用带匹配次数断言的完整表达式替换，保留条件/回合30及正确历史终端计数，
分别编译核验后派发，避免重复此生成错误。

## Direct5/6的有限采样并发试验

已启动 `B/runs/serl_pool30_cycle05_06_20261026_v2/direct`，learner PID2818100/GPU0/CPU0。
30个condition采样进程共享物理CPU1–12；总CPU预算没有扩展。保留D4完整learner、Adam、
replay、RNG、历史、官方十critic/随机二target/无entropy backup、8critic:1actor、batch32768。
Direct仍零示范、无人工纠正、不导入旧CHEQ权重/replay，无CHEQ nominal mixing；公共动作首维
由raw `(a0+1)/2` 映射为slowdown，公共零动作才是nominal，不能把首维增大解释成加速。

新wrapper只在固定trainer main替换两处：并发数守卫和sampler taskset亲和性。固定官方SERL
commit `1fa2af7496be042e43d36120a7c8d1b71f1bfb59`、learner实现和物理源码不变。
原main可由两处逆变换逐字节恢复；实际运行的候选main SHA为
`6214fe1c941172ab30366a4046c9774e0198c1f25c45d4f9728c1e898b873363`。
`SAMPLER_PATCH.json`、`SAMPLER_MAIN.py.txt` 与driver/registration hashes披露base+patch来源，
不能只引用旧trainer hash隐去新调度。更高并发改变数据到达顺序，不是逐位等价训练。

另有同名v1候选：30slot轮转绑定12单核，完成准备和check-only但**从未启动learner**；
保留该冻结目录，用独立v2共享CPU集合方案替代。不能把两个候选算成两次在线训练。

v2真实check-only通过：准确父state/review/source/hash/预算；改变UTD、clock、batch、预算、
workers或CPU配置均拒绝。实际启动只读核验在205962steps/1607704updates时通过：
父203962条replay前缀全部精确，新增2000步恰增16000critic更新，完整历史、官方config与来源保持，
网络/optimizer有限，30实际子进程CPU集合1–12、learner CPU0、30MJB匹配。
2000条新增动作/执行动作/canonical48缩放/nextstate/reward全部核验，reward重建误差0；
该启动快照无终端，不能当作周期终端审查。

准确边界归档器2833375在 `serl_pool30_archive_view_20261026_v2`，输出
`serl_pool30_archive_20261026_v2`；只读5/6协调器2946490/2946491分别在
`serl_pool30_cycle05_review_20261026_v2` / `serl_pool30_cycle06_review_20261026_v2`。
它们不自动派发下一训练阶段。旧Direct521120与533451均已完成，勿重启。

## 批量大小健康诊断：完成20000辅助更新，没有找到恢复证据

因I/A末loss连续增长，登记一次新实验 `B/runs/parameter_cycle09_batch_health_probe_20261026_v1`。
各自准确cycle9完整网络/Adam/RNG恢复，两臂batch32768与256各5000更新，每250记录，
共两方法×两臂×5000=20000辅助更新；0物理，不保存或推广权重，不修改正式checkpoint。
这与此前早期吞吐测量及actorLR/target probes是不同问题与父状态，没有重复已完成任务填占用。
两臂初始full-state digest与全部诊断值一致，replay初始抽样seed一致；batch不同意味着抽样条数、
后续RNG流与算力成本不同，不能声称完整同一抽样流或等数据预算。原checkpoint和replay未改变，
20点/臂、预算、hash、有限值独立核验通过，图已检查。PID2868662/2868663均正常完成，勿重跑。

| 方法/臂 | 终端MAE | in-bag终端MAE | 非终端抽样absQ p95 | 最后记录Q loss |
|---|---:|---:|---:|---:|
| I batch32768 | 13.088 | 9.017 | 463.294 | 62.846 |
| I batch256 | 27.043 | 25.996 | 394.987 | 40.352 |
| A batch32768 | 7.605 | 7.171 | 160.353 | 282.952 |
| A batch256 | 10.452 | 10.227 | 160.745 | 1221.781 |

I小批量降低Q尾部但终端拟合明显变差；A两臂仍无修复，小批量终端拟合更差。
单个最后loss不等于稳定末段均值，更不能跨不同batch当作同精度估计。
这里不足以支持直接恢复batch256作为修复，也不能把大批量在历史replay上较好的终端拟合
宣称在线健康；因此没有根据此诊断更改正式参数训练。价值网络异常的原因仍未解决。

## GPU与吞吐：混合窗口达到50%，持续正式训练要求仍未满足

新60样本、66.63秒只读窗口记录GPU均值58.283/57.867/55.183/52.717%。
GPU0是正式Direct、GPU3是正式VMC；GPU1/2是上述有限诊断，不是参数在线训练。
全部原正式PID在窗口内存活，profile本身0更新/0物理。

Direct 28.817transition/s、230.538critic更新/s，learner使用0.745核、sampler合计5.534核；
旧12worker窗口29.34transition/s、234.74critic更新/s，尚未证明30worker提速。
是否减少尾部等待仍需后续完整周期测量，不能按并发数量宣称改善。
VMC同期38.153steps/s、0.947 learner核、9.282 sampler核；这是不同阶段观测，不作因果加速结论。
辅助结束后即时GPU为59/0/0/55%，所以**每卡持续≥50%没有达成**。不重复已完成辅助维持数字。

## 交接入口与未完成项

小证据在 `docs/evidence/rl_cycle09_and_serl_pool_20261026/SOURCES.json`，逐项记录SSD来源、
仓库路径、大小和SHA。完整checkpoint、运行时、环境、轨迹仍在本集群SSD；这不是HDD全量备份，
也没有声称已传到arm1。HDD约464MiB剩余，大产物继续放SSD。

继续核实原Direct5/6与VMC9并收取精确边界审查；I/A9已经结束，诊断也完成，不能按旧PID重启。
下一项科学问题是区分价值网络拟合能力、移动bootstrap目标与actor/target耦合导致的漂移，
需先登记可审计的有限对照，再据结果决定参数后续阶段；当前没有已验证的修复。
最终冻结策略完整验证、指定ESN/SPT公平比较、健康收敛和持续GPU要求均未完成，Goal保持active。

本轮小文档交接副本：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_CYCLE09_SERL_POOL_STATUS_20261026_102818`（仅本文、AGENTS与UPDATE_LOG，非运行状态全备份）。
