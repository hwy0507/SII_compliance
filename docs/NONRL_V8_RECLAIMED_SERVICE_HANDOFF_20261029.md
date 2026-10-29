# 原108结束后的临时服务回收衔接

## 连续观察：06:45–06:59UTC，93→96

30次采样中原1172675/start32623702及后处理1201537/start32942337均loaded/active，
ESN2→RNN2→MLP2完整结束并接续ESN3条件010，末样本4.04s/lift。
最高MemoryCurrent1923670016bytes/3GiB，全部OOM/oom_kill/实验swap0；主机swap仍近满。
observer9093到96自然exit0，原科学继续，不重启。

新增三条runtime均55s/无abort/TaskStrict=false；ESN2最终lift，峰矩55.770897Nm、外部
穿透1.960532mm；RNN2最终carry，39.421005Nm/0.160610mm；MLP2最终carry，
51.703655Nm/0.686113mm。三AUDIT小文件hash已核；不是新增独立子步审计或完整第十一条件结论。

[30样本及源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0645.json)，
57867bytes，SHA256 `9ee085c1438247e009c0eacc462601b1865c6465a50b62e2dfb29f067392d856`。
暂存及最终大小/hash已核共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0645_20261029_v1/V8_VERIFIED_WAIT_0645.json`。
开工mainba9748b1/baselinef6e8f8c实际fetch/read；上一轮范围诊断progress，本轮verified wait。
Goal active，主矩阵未修复；原完整审查归档→唯一v6八球及实际运动核查→正式三场景补采/
公平重训保持，无新物理/拟合/绑定源修改，可选004未重试。

## 第十条件完整与接触范围解释，原108到93

06:30:35.140–06:41:05.354UTC共22样本，原1172675/start32623702及后处理
1201537/start32942337均loaded/active，90→93并接续条件010的ESN2。
最高MemoryCurrent1859694592bytes/3GiB，所有样本OOM/oom_kill/实验swap0；主机末SwapFree0。
observer28771到93自然exit0，原科学继续。第十条件009九条全部Task/Strict=false，
前十条件90条runtime Task/Strict/BOTH均0，条件SPT为NA。

| 方法/seed末位 | 时长 s | 最终阶段 | 峰矩 Nm | 接触期舒适代理 | 机器合规 |
|---|---:|---|---:|---:|---|
| ESN1 | 46.68 | carry / abort | 76.349075 | 83.7428% | 否 |
| RNN1 | 55 | approach | 42.749390 | 100% | 是 |
| MLP1 | 55 | approach | 36.664909 | NA | 是 |
| ESN2 | 17.56 | lift / abort | 57.356194 | 99.9450% | 否 |
| RNN2 | 55 | carry | 40.027920 | 100% | 是 |
| MLP2 | 55 | carry | 51.338665 | 100% | 否 |
| ESN3 | 55 | carry | 46.331528 | 96.4407% | 是 |
| RNN3 | 55 | carry | 38.000187 | 100% | 是 |
| MLP3 | 55 | carry | 37.397362 | 100% | 是 |

MLP1无人体接触，NA不是100%；安全或低峰矩不替代Task成功。九小型AUDIT/metrics文件
hash已逐一匹配结果行；这是runtime收据核对，不是新增独立子步审计，004–009仍待原完整后处理。

本轮另读取冻结MJB的几何/刚体映射，解释ESN2“外部穿透仅0.379mm却因全局>2mm终止”：
原`rollout.json`全局峰值3.315180mm对应geom66/75，即left_finger/right_finger；
外部峰值0.378817mm对应桌角顶部与left_finger。原冻结代码的全局量统计不同刚体接触，
外部量排除机器人自接触和目标物体接触，二者不矛盾。ESN1全局/外部均2.468439mm，
最深接触对应world与fr3_link7。没有改门槛，也未重新积分或从状态重建接触。
只读范围解释服务自然exit0，运行1.462s/CPU1.241s；进程内已核affinity[6]/256MiB/swap0。

[完整条件及观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION009_COMPLETE_AND_WAIT.json)：
65882bytes，SHA256 `3b0c52d1f92651d47e4cb0c5e627204c103f8a62277fb90b51dbfeb333793490`。
[接触范围及源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION009_CONTACT_SCOPE.json)：
17683bytes，SHA256 `8c375aaa565f9ba5caae8e85661a9e23ee5b55c3ec7c62e6c0d2a0ee2ea1f8b5`。
两成员包12053bytes/SHA256 `296ea078cd1100fa495245ad6dbb1c1cf01082ff9cc9e4742a7de0431c9eb809`
已逐成员及暂存/最终大小hash核共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition009_complete_20261029_v1/EVIDENCE.tar.gz`。
开工mainc1e2bf02/baselinef6e8f8c实际fetch/read；本轮完整条件及范围诊断progress，Goal active。
主矩阵未修复；原完整审查归档→唯一v6八球/实际运动核查→正式补采/公平重训保持，
无新物理/拟合/绑定源修改，可选004未重试。

## 连续观察：06:09–06:24UTC，86→89

31次采样均确认原1172675/start32623702及后处理1201537/start32942337 loaded/active。
原协调器由MLP2接续ESN3、RNN3，再接续MLP3；末条10.04s/lift，完整条件009尚未结束。
最高MemoryCurrent1871986688bytes/3GiB；全部样本OOM/oom_kill/实验swap0。
末主机MemAvailable3822948kB、SwapFree248kB，不能把实验swap0写成全机swap0。
观察器68766达到900秒自然exit0，原科学继续，不重启。

三条新增完成runtime均55s/TaskStrict=false：MLP2峰矩51.338665Nm、穿透0.955362mm；
ESN3峰矩46.331528Nm、穿透0.148003mm，途中位置误差约1.21m；RNN3峰矩38.000187Nm、
穿透0.177308mm，未完成搬运。上述为运行收据，不是本轮新增独立子步审计。

[31样本及观察源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION009_RUNTIME_AND_WAIT.json)，
60692bytes，SHA256 `c5eae7e504b8e0f5315de2426da819a002816864be228b93dcbff04818ee332a`。
文件名中的009表示正在观察的条件，不表示完整九模型结果；本次未达到90，无完整条件结果表。
暂存及最终大小/hash已核共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0609_20261029_v1/V8_CONDITION009_RUNTIME_AND_WAIT.json`。
开工main6492ab17/baselinef6e8f8c实际fetch/read。上一轮实际运动诊断progress，本轮verified wait；
Goal active，主矩阵未修复。原完整审查归档→唯一v6八球及实际运动检查→正式三场景补采/
公平重训保持，无新增物理/拟合或绑定源修改，可选004审计未重试。

## 后续增加：真实物体运动检查，原108到85

[实际运动核查](NONRL_V8_BALL_ACTUAL_MOTION_20261029.md)：八条train球示范搬运物体投影
89.288–90.138mm、回程88.702–89.895mm，证实物体实际随动，但共享同一搬运方向。
新独立`describe_ball_actual_motion_20261029.py`检查实际手/物位置；后继八球v6原review之外
追加此描述，避免仅凭目标/actor方向认定物体已搬运。正式数据构建后亦可复用。
手算四类/四非法拒绝与真实32阶段标量复核通过；不新增gate、不改变绑定源/拟合。
四成员25290bytes/SHA6e070fc8已核共享
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_ball_actual_motion_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。
06:03原两PID仍active，06:05:22原108到85、RNN2条件009在途；v6的198源保持且未启动。
Goal active，主矩阵未修复；原完整审查归档→八球原review及实际位移→三场景补采/公平重训保持。

## 最新完整条件：008九条runtime，累计81/108

05:38:57.167–05:48:27.349UTC共20次采样，原1172675/start32623702及后处理1201537/start32942337
均loaded/active，79→81，原协调器进入条件009。最大MemoryCurrent2084233216bytes/3GiB，
所有样本oom/oom_kill/实验swap为0，主机swap仍近满。observer20511因第九条件完整自然exit0，
原科学继续，没有重启或新增物理。

第九条件九条runtime均Task/Strict=false；ESN1/3分别9.24/16.16秒global penetration abort，
其余七条完整55秒。前九条件81条runtime Task/Strict/BOTH全0，SPT NA。
九个AUDIT.json与metrics文件hash逐一匹配snapshot，metrics Task/Strict标签逐一一致；
这是小型运行收据核对，不是新增独立子步审计。独立条件审计仍000–003，004–008待原完整后处理。

| 方法/seed末位 | 时长 s | 最终阶段 | 峰矩 Nm | 接触期舒适代理 | 机器合规 |
|---|---:|---|---:|---:|---|
| ESN1 | 9.24 | lift / abort | 66.254478 | 88.1197% | 否 |
| RNN1 | 55 | approach | 43.365974 | 100% | 是 |
| MLP1 | 55 | approach | 36.664909 | NA | 是 |
| ESN2 | 55 | carry | 59.493095 | 99.3750% | 否 |
| RNN2 | 55 | carry | 38.273289 | 100% | 是 |
| MLP2 | 55 | carry | 51.135124 | 100% | 否 |
| ESN3 | 16.16 | lift / abort | 61.226051 | NA | 否 |
| RNN3 | 55 | carry | 38.054447 | 100% | 是 |
| MLP3 | 55 | carry | 43.793816 | 100% | 是 |

ESN1/2/3与MLP2外部穿透峰值分别2.938752/1.532159/3.195633/0.453863mm。
MLP1/ESN3无人体接触，NA不是100%；短回合不包装成完整55秒。全部失败保留，机器合规不替代任务成功。

[20样本、九原始结果、前九条件计数及源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION008_RUNTIME_AND_WAIT.json)，
62390bytes，SHA256 `76a416136cad7727e516cd461a1578f37d600c0b7e24e4f865b90b8487a1cbe3`。
已核暂存及最终大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition008_runtime_20261029_v1/V8_CONDITION008_RUNTIME_AND_WAIT.json`。
开工main9defd6a4/baselinef6e8f8c实际fetch/read。本轮保存完整条件失败及verified wait；Goal active，
主矩阵未修复，原108/后处理继续，唯一v6未启动。完整审查归档→八球→正式补采/公平重训保持，
无新拟合或绑定源修改，可选004审计未重试。

## 后续核验：05:31–05:36 UTC，77→79

05:31:37.140–05:36:07.222UTC共10样本，原1172675/start32623702及1201537/start32942337
保持loaded/active，完整77→79。MLP2从31.04s/carry到54.04s，原协调器随后接续ESN3，
再接续RNN3，末样本4.04s/lift。MLP2实际runtime为55s/noabort/TaskStrictfalse/carry；
ESN3实际16.16s/lift/global_penetration_exceeded_2mm/TaskStrictfalse，短回合失败保留。
这是运行收据核对，不是新增独立子步审计或完整第九条件结论。
最高MemoryCurrent2077904896bytes/3GiB，全部样本OOM/oom_kill/实验swap0；
末主机MemAvailable4190408kB、SwapFree344kB。observer61682到79后自然exit0，科学继续。

[10样本及观察源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0531.json)，
21965bytes，SHA256 `af4f76d0a6e2bfaad060c1d804e43329df6f518f99debf61270d8566b8095828`。
已核暂存及最终共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0531_20261029_v1/V8_VERIFIED_WAIT_0531.json`。
开工main08437d86/baselinef6e8f8c实际fetch/read。本轮verified wait，Goal active，主矩阵未修复。
原完整108/后处理继续，唯一v6未启动；完整审查归档→八球覆盖→正式补采/公平重训保持，
无新物理/拟合/绑定源改动，可选004审计未重试。

## 后续核验：05:20–05:28 UTC，75→77

05:20:33.735–05:28:33.887UTC共17样本，原1172675/start32623702及后处理1201537/start32942337
始终loaded/active，完整75→77；ESN2由lift进入carry后自然结束，RNN2从approach→lift→carry
完整结束，再接续MLP2，末样本4.04s/lift。两新完成runtime均55s/无abort/TaskStrict=false、
最终carry；不是新增独立子步审计或完整第九条件结论。
最高MemoryCurrent2346278912bytes/3GiB，所有样本oom/oom_kill/实验swap为0；
主机末MemAvailable4284476kB、SwapFree152kB。observer87760达第77条后自然exit0，科学继续。

[完整17样本及观察源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0520.json)，
34639bytes，SHA256 `66cb5c5d0031ebac87028448bc166d58fd75ab1b2432c515f296021444b3be7b`。
已核暂存及最终大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0520_20261029_v1/V8_VERIFIED_WAIT_0520.json`。
开工mainba81b92c/baselinef6e8f8c实际fetch/read。本轮verified wait，Goal active；原完整108与
统一后处理继续，唯一v6未启动，主矩阵尚未修复。完整审查归档→八球→正式补采/公平重训保持，
没有修改绑定源、新增物理或拟合，可选004审计未重试。

## 后续核验：05:12–05:17 UTC，73→75

本轮verified wait：05:12:48.339–05:17:48.435UTC共11次原1172675/start32623702及
后处理1201537/start32942337保持loaded/active，完整73→75；RNN1接近阶段43.04s自然结束，
原协调器接续MLP1（1.04→54.04s，仍approach），再接续ESN2，末样本4.04s/lift。
最高MemoryCurrent2174996480bytes/3GiB，所有样本oom/oom_kill/实验swap为0；
末样本主机MemAvailable4518176kB、SwapFree148kB。observer87813在第75条边界自然exit0，
不是科学结束，没有重启原评测或后处理。

[完整观察及源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0513.json)，
23787bytes，SHA256 `54afb9ac5e4c0377c0be66019a482f677483cf2f5f0a3563c40882528ebe6f21`。
暂存及最终大小/hash已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0513_20261029_v1/V8_VERIFIED_WAIT_0513.json`。
开工mainfee7484e/baselinef6e8f8c实际fetch/read。无新物理/拟合/独立子步审计；第九条件仍未完整，
原108与统一后处理继续，唯一v6未启动。Goal active，主矩阵未修复；完整审查归档后再进入
八球覆盖对照、正式三场景采集、公平重训及闭环回归，可选004审计未重试。

## 最新完整条件：007九条runtime，累计72/108

05:08:13.159–05:09:13.175UTC三次采样：原1172675/start32623702及后处理1201537/start32942337
均loaded/active，完整71→72，原协调器已进入条件008。最高MemoryCurrent1964367872bytes/3GiB，
OOM/oom_kill/实验swap为0，主机swap仍近满。observer51125因第八条件完整自然exit0，科学继续。

第八条件九条均完整55s、无abort、Task/Strict=false。前八条件72条runtime Task/Strict/BOTH全0，
SPT NA。这些是运行收据，不是新独立物理审计；独立条件审计仍仅000–003，004–007待原后处理。
九份AUDIT.json和metrics小文件hash与snapshot逐一一致，metrics的Task/Strict标签逐一相符。

| 方法/seed末位 | 最终阶段 | 峰矩 Nm | 接触期舒适代理 | 机器合规 |
|---|---|---:|---:|---|
| ESN1 | lift | 75.617134 | 59.9380% | 是 |
| RNN1 | approach | 43.393333 | 100% | 是 |
| MLP1 | approach | 36.664909 | NA | 是 |
| ESN2 | lift | 67.579155 | 87.9757% | 否 |
| RNN2 | carry | 38.772083 | 100% | 是 |
| MLP2 | carry | 51.592674 | 99.1356% | 否 |
| ESN3 | carry | 55.692780 | 21.7431% | 是 |
| RNN3 | carry | 38.696056 | 100% | 是 |
| MLP3 | carry | 44.209389 | 100% | 否 |

ESN2/MLP2/MLP3所报外部穿透峰值分别1.779645/0.545885/0.594268mm，超过原0.2mm门槛。
MLP1无人体接触，NA不是100%；机器合规也不意味着任务成功。全部失败保留，不据此改模型或门槛。

[三样本、九原始结果、前八条件计数和采样源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION007_RUNTIME_AND_WAIT.json)：
31204bytes，SHA256 `dd2a08973cf0ab6cf2b33352e46e84aa42fcebeca43d1d9dd00158fcc081d23d`。
暂存与最终归档大小/hash均核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition007_runtime_20261029_v1/V8_CONDITION007_RUNTIME_AND_WAIT.json`。
开工main28485480/baselinef6e8f8c实际fetch/read。上一轮训练曝光审计为progress，本轮保存完整条件
失败与verified wait。原108/完整后处理继续，唯一v6未启动；完整审查归档→覆盖修复→正式补采/
公平重训/闭环六指标仍待，Goal active，主矩阵尚未修复，可选004审计未重试。

## 后续核验：训练实际曝光与场景份额

[曝光报告](NONRL_V8_TRAINING_EXPOSURE_20261029.md)：新增独立日程审计，实际72神经候选全部通过，
同seed两家曝光一致，无验证身份混入或补零冒充样本；变时长手算边界和五损坏拒绝通过。
当前数据本已不等时长，棍/球/角帧份额31.7460/47.6190/20.6349%，每场景8train不等于等权；
未改训练或选择规则。补采重训后可用新工具复核实际曝光，不能由回合数推断权重。
三成员10080bytes/SHAe76f37d5已核共享
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_training_exposure_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。
05:03:45UTC原1172675/1201537仍active、71/108、MLP3条件007在途；唯一v6未启动。
本轮progress，Goal active，主矩阵未修复；原完整审查归档及后继覆盖修复顺序保持。

## 后续核验：04:47–04:57 UTC，68→70

上一轮曲线来源核验为progress；本轮为verified wait。21次准确采样中，原1172675/start32623702
及后处理1201537/start32942337始终loaded/active；完整68→70，原协调器由条件007 MLP2
接续ESN3，再接续RNN3。观察器84675达到600秒自然exit0，不代表科学任务结束。
最大MemoryCurrent2442362880bytes/3GiB，全部样本oom/oom_kill/实验swap为0；
末样本主机MemAvailable4579808kB、SwapFree140kB，主机swap仍近满。

MLP2实际progress由17.04s/carry至54.04s/carry，穿透峰从0.176021升至0.545885mm；
ESN3从4.04s/lift进入carry，51.04s时跟踪误差1.415848m。
另读取两份已完成runtime metrics：均55s、Task/Strict=false、无abort、最终carry；
MLP2/ESN3峰矩51.592674/55.692780Nm，RMSE48.781029/1136.103456mm。
这是保存的运行指标，**非本轮新增子步审计**；不扩展为完整条件或完整108结论。
末样本RNN3刚开始0.04s，原完整后处理继续。

[21样本及观察源码](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0447.json)，
41883bytes，SHA256 `ea6adfe4632822db7019b7f60f5d542093d276d8961d03d4577f72ad132614cc`。
已核暂存和最终大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0447_20261029_v1/V8_VERIFIED_WAIT_0447.json`。
开工main7328b15f/baselinef6e8f8c实际fetch/read；无新增物理/拟合/模型选择。
Goal active，主矩阵未修复；完整审查归档→唯一v6八球→正式三场景补采/公平重训保持，
v6未启动，可选004审计未重试，未修改在途或已绑定源码。

## 后续核验：当前v8学习曲线

[学习核验报告](NONRL_V8_LEARNING_CURVE_REVIEW_20261029.md)：九锁定模型/六history/原图来源及
算术通过。曲线先下降后趋平，实际cosine终值是初始学习率1%；低动作MSE不证明闭环修复。
首次精确浮点相等误判保留，按原绘图容差修正检查后通过，模型/图未改。
四成员441333bytes/SHAae6e4e4f已核暂存/最终共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_learning_visual_review_20261029_v1/FIGURES_AND_REVIEW.tar.gz`。
04:42:51 UTC原1172675/1201537保持active，随后execution为67/108、RNN2条件007在途。
Goal active，主矩阵尚未修复；原完整后处理→查看归档→唯一v6八球→三场景正式补采/重训仍待。
未新增仿真/拟合，可选004审计未重试。

## 后续核验：04:28–04:30 UTC

本轮verified wait：04:28:46.130–04:30:46.168共五次原1172675/start32623702及
后处理1201537/start32942337保持loaded/active，完整64→65，RNN1物理28.04→55秒，
原协调器接续MLP1。RNN1完整runtime Task/Strict=false、最终approach、无abort；
这是运行结果，不是新增独立物理审计。最大内存2388496384bytes/3GiB，OOM/oom_kill/
实验swap0；全机swap仍近满。observer16841达到第65条边界后自然exit0，科学继续。

[完整观察](evidence/NONRL_INTENT_RECOVERY_20261029/V8_VERIFIED_WAIT_0428.json)含源码与五样本，
12526bytes，SHA256 `b548e02f88e0d71c6325f6c99ba490d7d709cb06ad331f727d16dd2d7f4ffa92`。
已核暂存/最终共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_wait0428_20261029_v1/V8_VERIFIED_WAIT_0428.json`。
开工main02ab66aa/baselinef6e8f8c实际fetch/read，原完整108/后处理未完，唯一八球v6未启动，
Goal active。无新仿真/拟合/指标改动，可选004审计未重试。

## 最新运行结果：第七条件006完整

04:23:29.932 UTC原矩阵63/108，原1172675/start32623702和后处理1201537/start32942337
均loaded/active，原协调器已进入条件007。单次准确快照中原内存2100506624bytes/3GiB，
OOM/oom_kill/实验swap0；全机swap近满。观察脚本发现第七组已经完成后自然exit0，
只有一个保存样本，不将其写成多次持续观察；开工04:22:12另一次实际查询为62/108。

前七条件63条runtime标签Task/Strict/BOTH均0，各方法/seed各7条。第七组具体如下，
全部仍为runtime指标；仅核九份小型AUDIT.json hash和标签与快照一致，**不是新子步独立审计**。

| 方法/seed末位 | 时长 s | 结束阶段 | 峰矩 Nm | 舒适代理 | 机器合规 |
|---|---:|---|---:|---:|---|
| ESN1 | 29.48 | lift / global penetration abort | 67.559547 | NA | 否 |
| RNN1 | 55 | approach | 47.441891 | 12.0022% | 否 |
| MLP1 | 55 | approach | 36.664909 | NA | 是 |
| ESN2 | 55 | lift | 51.401569 | 99.3575% | 是 |
| RNN2 | 55 | carry | 37.534489 | 100% | 是 |
| MLP2 | 55 | carry | 51.973797 | 100% | 否 |
| ESN3 | 23.16 | lift / global penetration abort | 46.512081 | 0% | 否 |
| RNN3 | 55 | carry | 38.942760 | 100% | 是 |
| MLP3 | 55 | carry | 36.233955 | 100% | 是 |

ESN1/3触发global_penetration_exceeded_2mm，不能因其所列external penetration分别
0.142648/0.169874mm低于0.2mm便改判机器合规；global与external口径不同，abort原样保留。
RNN1/MLP2的external penetration分别1.249502/0.713273mm。NA表示无人体接触，
不是100%舒适。无BOTH成功，SPT仍NA。独立条件审计仅覆盖000–003，004–006待原完整后处理。

准确快照含采集源码、原结果九行及前七条件标签计数，27782bytes，SHA256
`76599bc70ef22d3970bff1d26e2723109200b2bb745aefdd0aec76b3f1a4b511`：
[本机证据](evidence/NONRL_INTENT_RECOVERY_20261029/V8_CONDITION006_RUNTIME_AND_WAIT.json)。
已核暂存/最终共享于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_condition006_runtime_20261029_v1/V8_CONDITION006_RUNTIME_AND_WAIT.json`。
开工mainf9c7ad63/baselinef6e8f8c实际fetch/read；原科学继续，唯一八球v6未启动。
本轮保存完整条件失败证据，Goal active，无新仿真/拟合/审计，主矩阵修复仍待。

## 上轮入口修复

主矩阵仍未修复，Goal active。原108/后处理继续，04:18:06 UTC为62/108，
条件006最后一条MLP3在途。本轮修复后继入口的真实生命周期兼容问题，未执行新物理。

## 发现与边界

实际原评测服务为`Type=simple`、`RemainAfterExit=no`、`CollectMode=inactive`，
FragmentPath位于`/run/user/1000/systemd/transient/`。
InvocationID为`1cdbbfde2fba4561902e546b2e03db38`，仍是PID1172675/start32623702。
先前真实完成的`coverage-dataset-check`服务退出后已被回收：LoadState=not-found、
ActiveState=inactive、MainPID=0、InvocationID/ControlGroup为空，ExecMainCode=0、
ExecMainStatus=0、Result=success是查询默认值，**不能作为正常exit0收据**。

旧八球v5只允许loaded/inactive/success，若原评测正常完成后被回收，会被误拒绝。
本轮不改原服务、v5登记或其198绑定源码。新增独立
`tools/prepare_ball_coverage_reclaimed_20261029.py`与唯一后继
`outputs/nonrl_ball_coverage_probe_20261029_v6`，REG SHA256
`c9450ef98e5a6597158a4ace7117ba771cab300eee49cf0ee9314ccfbf2a9e94`。
v5保留为未启动历史，增加superseded说明。v6的198源仅将旧launcher换为新launcher，
八条件、seed、teacher、物理/输入/filter/gate、资源和科学前置完全一致。

## 新守卫

先核原108 execution完整108、全部独立审计通过、REPORT hash及原preparation/model-lock。
之后才检查原服务终态，登记额外绑定boot ID、InvocationID和原cgroup绝对路径。
两种允许状态都要求同boot、原PID/start身份消失、MainPID=0且inactive：

- retained unit：loaded、同InvocationID、Result=success、ExecMainCode=1且ExecMainStatus=0；
  记录`service_exit_zero_verified=true`。
- reclaimed unit：not-found、InvocationID/ControlGroup均为空、**原cgroup路径也不存在**；
  记录`service_exit_zero_verified=false`，只根据已完成的独立科学证据和无原运行实体允许交接。
  不声称已找回原父进程退出码，不能单凭not-found进入此分支。

查询失败、残缺响应、active/deactivating、原PID仍存、旧cgroup仍存、boot变化、
不同invocation、异常exit均拒绝。原单模拟器锁、单CPU/线程、3GiB/禁swap保持。
这不是放宽物理/任务门槛，也不修改在途模型或重启科学作业。

## 验证与交接

`check_ball_reclaimed_handoff_20261029.py`验证3正向状态及14拒绝情形；实际原108未完成时
新run入口拒绝，v5/v6都没有execution.json或物理产物。真实原服务准确InvocationID/PID/start
核验通过。当前只验证软件边界，尚未发生真实完整108终态交接或八球物理运行。
实际新旧launcher差异已逐段审查，旧198源hash保持，全部科学条件逐字段相同。

- [准确登记](evidence/NONRL_INTENT_RECOVERY_20261029/V8_BALL_COVERAGE_V6_REGISTRATION.json)。
- [检查](evidence/NONRL_INTENT_RECOVERY_20261029/V8_RECLAIMED_SERVICE_HANDOFF_CHECK.json)，SHA256
  `cf229242aed087bc051c67c5e7c3b46931ccdc06cde3c9007bbd457321d6318f`。
- 五成员源码/登记/检查/superseded包18669bytes，SHA256
  `306733cd7285769008df1a30278542528fffe984cf9a3ff061dd24ca6cda3d57`，逐成员及暂存/最终核验后共享：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_v8_reclaimed_handoff_20261029_v1/SOURCE_AND_CHECKS.tar.gz`。

下一步：原108完整后处理、实际查看图表并归档后，以单CPU affinity6/数值线程1/3GiB/禁swap
运行`prepare_ball_coverage_reclaimed_20261029.py --root outputs/nonrl_ball_coverage_probe_20261029_v6 --run`。
启动前重新核主机内存和现有作业。不要再启动v5或任何更旧版本。
八球全八review仍使用原`review_ball_coverage_probe_20261029.py`；之后正式三场景采集/资格、
变时长实际train覆盖检查、公平重训和冻结108回归六指标仍待。

本轮开工main `b05249b33858a36f21c420225167a31d172337fa`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`实际fetch/read。上一轮verified wait，
本轮后继守卫修复progress。无RL/子agent/服务器计算/用户数据删除；可选004审计仍未重试。
