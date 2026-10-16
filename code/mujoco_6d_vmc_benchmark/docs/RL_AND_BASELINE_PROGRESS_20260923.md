# RL 与经典柔顺 baseline 工作记录（2026-09-23）

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

## 2026-10-16 23:40 CST 物块进度奖励有限对照准备

原stage02_v2导纳2467890持续推进，收工16,250步/11,251更新；ep9/10完整physical_valid、Task/Strict0/2，
return−25.493493/−25.264967，cp13750/15125和2750连续有限更新/逐回合回报和核验。
新`rl_goal_impedance_occupancy_20261016`登记fresh control/weight4物块进度成本两组，各44k、1M优化日程；
同seed/物理/输入/滤波/执行器，原四族训练和已准备Direct alpha0/1对照不变。登记
`b3cb37f91cb713f4878fc7a0e79ae506a846feef159236baa72dd74f557caf1d`。
96项测试与真实CUDA预检通过：同初始化、1375训练样本奖励/归一化统计独立核验、末25步回报求和、各一次丢弃更新有限，
源cp23375不变、仿真/保存模型0，峰1,516,871,680字节/2GiB、OOM/max/swap0。
隔离trainer准入通过，实际提前launch因四族未闭合拒绝、无LAUNCH/execution；仅准备，未证实online收益。
报告/screen识别新reward并拒绝混用，双组不等于四族；采用候选前仍须完成明确的选型接续兼容核验。
证据及前2导纳原始回合/cp已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-occupancy-ready-20261016T1540/evidence.tar.gz`，
547,562,429字节，SHA `766cab7086f18f6305632f316daa1f06a0695491438d01b0d7ccdd25f62a2fc7`，本地/暂存/最终一致。
64回合估计需20.10GB且不含增长/缓存，当前尚不足以在50GiB保护区之上完整存放；继续核验归档/离线保留再派发。
重新核验远端后释放3份重复tar缓存2,164,485,381字节，free59.79→61.95GB；原始轨迹/cp零删除，可下载服务器包恢复缓存。
当前导纳峰3GiB/max1、OOM/swap0、GPU38°C。按sii-research-sync核对两分支main a63ff29/baseline f6e8f8c及收工AGENTS。
Goal active，四方法未证实收敛、未最终acceptance；服务器仅归档，所有失败保留。

## 2026-10-16 23:25 CST 阻抗阶段结束、导纳接续及reward诊断

stage02_v2阻抗23,375步/18,376更新，本段11,000连续有限更新、8完整physical_valid回合、Task/Strict0/8；
末return−25.320493、temperature .001968527。协调器自动接续导纳2467890，观测12,500步/7,501更新；VMC待运行。
阻抗3GiB峰/max3175但OOM/swap0；导纳约2.55GB峰、OOM/swap0，GPU38°C。主机已有swap占用与worker区分。
cp19250只读credit与5回合分解显示动作有变化、无能量限幅触发，末段位置误差约12.7–15.8mm，任务仍失败。
99个路径点切换中97个局部误差成本上跳，收紧误差尺度可能加重推进惩罚；因此未采用该直觉候选。
新增未部署物块进度occupancy成本helper和测试，93项Goal测试通过；shadow显示无局部参考切换项，
但这只是不同reward的固定轨迹重算，不是新策略改善；未接入trainer/登记在线处理或重标历史replay。
phi不保证成功时为1，需独立有限配对及奖励一致的训练历史。既有Direct actor正则化pair仍待四族阶段结束。
4份诊断/源码与阻抗cp17875–22000和原始回合已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-payload-diagnosis-20261016T1520/evidence.tar.gz`，
1,088,411,543字节，SHA `dc7f72746fd2c72f8371dade4b5292b0fe9586846d9a09ee64f365a8e3e8fa31`。
最后cp23375/回合及完整日志补包267,249,973字节，SHA
`0d6c9510a533779f87676215e7079e0c92d450b27f879ec69327cd095c043f86`，已核验同服务器runs/main下
`rl-goal-impedance-stage02-close-20261016T1525/evidence.tar.gz`，本地/暂存/最终一致。
实时查询/fetch/read main fe07aa9/baseline f6e8f8c，收工重读AGENTS；本机计算、服务器仅文件/hash，free约61GB。
收工导纳13,250步/8,251更新、峰2.65GB、max/OOM/swap0，free60.999GB。
Goal active，未证实任何方法收敛、未最终验收，所有失败保留。详见RL_GOAL_PROGRESS_20261016.md本次条目。

## 2026-10-16 23:00 CST 正则化分支接续与失败统计保持

原阻抗worker2455377未重启，归档快照17,000步/12,001更新，收工18,250步/13,251更新。
新增4完整55秒回合、physical_valid4/4、Task/Strict0/4；前三回合/cp13750/15125/16500及4125连续有限更新已核验归档。
补齐已完成正则化pair→显式选型→四族接续→后续普通阶段入口，保留各方法实际参数快照/optimizer/replay，
不重复迁移；分支前失败另存源收据，处理后固定配置窗口不混用旧回报，短失败和在途回合仍明确计数。
90项Goal测试通过，跨阶段测试为合成闭合收据；真实pair仍未开始，未选赢家、未修改任何活动source。
同reward配对报告要求完整reward/prior/config/恢复来源相符；只有等身份/等曝光的完整回合作比较。
证据服务器目录`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-regularized-lineage-20261016T1455/`，
evidence.tar.gz SHA `1553ff87d7c62ad6f5c0e18e6b95eb905504debb36b9c1ebcdb7019602182122`（808,823,865字节），
最终代码source_final.tar.gz SHA `d31acdcb7af0d0e0d53fa381b68b9288cf1cbad34939d8a95fc8333efa1bc98f`（21,964字节），本地/远端一致。
核验远端后移除T1415/T1440两份重复传输缓存2,479,027,859字节，可从服务器恢复；原始回合/checkpoint零删除。
free升至63.66GB；阻抗峰3GiB/max287、OOM/swap0。开工main e19feda/baseline f6e8f8c已查询/fetch/read，收工重读AGENTS。
Goal active，继续四族队列及后续在线验证，所有方法未证实收敛，未最终acceptance。

## 2026-10-16 22:40 CST Direct闭合与actor正则化配对接续预检

stage02_v2 Direct完成有限段21,262步/16,263更新，新增10回合=7完整+3穿透短终止；
physical_valid6/10、Task/Strict0/10，全部10,269新增更新连续有限、reward和/cp hash核验。
自动接续阻抗2455377，观测14,000步/9,001更新，首个新完整回合return−25.729180仍失败。
新online pair从Direct最终cp21262共享恢复，alpha0/1各新增11k；仅迁移原生actor_bc_alpha，
optimizer/replay/normalizer/RNG和冻结物理/reward/输入保留。86项Goal测试、隔离导入和两组trainer准入通过。
两组真实CUDA预检验证完整网络/优化器hash及统计/RNG精确恢复，各一次丢弃更新有限；
处理组额外保存/重载验证通过，无仿真/部署。前置四族尚未闭合，实际launch被拒且未创建派发记录。
登记`1be1942c09c6f03b5b361b0c694e9449331edd36aa0febd451e6055601a87f45`；
运行根`outputs/rl_goal_actor_regularization_online_20261016`，只完成预检，不证明正则化在线收益。
Direct峰值3GiB/max事件1330但OOM/swap0；两组预检峰约1.33/1.56GB，roundtrip1.63GB，均OOM0。
尾6Direct原始回合/cp及pair证据本地包1,611,100,590字节，SHA
`da29a35e1835a90b48e7a684bb09f79da6e750a413a6844b55f4fc799533b806`，本地/服务器hash一致，已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-bc-online-ready-20261016T1440/evidence.tar.gz`。
服务器仅存储/hash；本轮未删除数据。收工阻抗14,750步/9,751更新，OOM/swap0，仍正常运行。
main610cdbc/baseline f6e8f8c实时查询/fetch/read、收工重读AGENTS；四族未收敛，Goal active、未最终acceptance。

## 2026-10-16 22:15 CST Direct只读信用诊断与动作正则化探针

stage02_v2原训练进程持续16250步/11251更新；新增5闭合、3完整、physical_valid2/5、Task/Strict0/5。
前4回合/cp11333/11446/12821/14196和3203连续更新/回报和核验，第5回合/cp15571仅本地待同步。
cp12821较早250末端窗口absTD .005644但当前动作Q高.681024，最新25末端absTD2.456717；
clip概率质量均值.0000248693，支持继续调查动作偏移，不证明真实Q或实现bug。
新增同cp/同批次alpha0/1各256丢弃更新探针，使用原生SimbaV2 actor_bc_alpha，仅内存修改、无仿真/模型保存。
动作历史MSE .557015→.230609，饱和4.8131%→.1116%，只是训练replay诊断；未部署处理/未证明任务收益。
81项Goal测试通过；探针峰值约1.32GB/2GiB、主训练峰2.786GB/3GiB，OOM/swap0。
诊断/探针/前4原始回合及cp已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-credit-regularization-20261016T1415/evidence.tar.gz`，
867,927,269字节，SHA256 `a2af18129ff12927befd61ee26f0f48c07ddd985051271d2175f2ad3f92dd2e8`。
按sii-research-sync读取两分支与AGENTS，保留失败和活动快照；Goal active，无收敛或最终验收结论。

## 2026-10-16 22:05 CST Direct配对闭合与四方法接续修复

完整Direct control/tracking均0/8；tracking11000步/6001更新、8完整physical_valid7/8，
control10993步/7完整+1短失败。3个完整学习配对RMSE中位差+241.535mm，额外tracking权重未证明收益。
选Direct fresh-n25 control cp10993和原GPU验证三参数cp12375，各新增11k，不重置学习。
第一次selected stage在派发前缺pilot依赖失败，无trainer输出，完整保留；修复快照依赖及预检checkout回退，
2回归先失败后通过，全部79项Goal测试通过。独立v2快照隔离核验与四族真实恢复预检通过。
当前`rl_goal_selected_20261016_stage02_v2`，协调器2447861、Direct2447875，已真实恢复推进。
归档快照11333/6334，随后前2接续回合13.60/4.52秒穿透终止、Task/Strict均false；cp11333/11446仅本地待归档。
OOM0/swap0，原3GiB/单路资源和冻结接口不变，50GiB磁盘保护保持；短失败增加cp开销，需跟进归档。
服务器已核验两包（主机arm1@192.168.31.70，根`/home/arm1/sii_shared/SII_compliance/runs/main/`）：
`rl-goal-direct-pair-selected-20261016T1350/evidence.tar.gz`，1,014,664,550字节，
SHA256 `4926680f57691f57adb2845fcb33882f8dd0f9e0a2cd5648b1333ecbb4cb64c2`；
`rl-goal-selected-snapshot-fix-20261016T1400/evidence.tar.gz`，3,259,135字节，
SHA256 `c471f8b7da9a223097010736e7db974ee2dd2d59225175ad3610f923d778d0df`。
首包重复本地tar已移除，原始数据/cp保留，服务器可恢复；修复按快照内容hash标识。
按sii-research-sync核对两分支并保留失败；Goal active，工作流恢复不等于策略收敛，无最终验收。

## 2026-10-16 21:35 CST 逐方法接续实现与Direct tracking学习

tracking原worker7000步/2001更新，5完整Task/Strict0/5；cp2750/4125/5500及501条连续有限更新核验。
首全学习配对RMSE+241.535mm、峰矩+10.129753Nm，仍失败，不能声称加tracking权重已修复。
新增显式四族来源选择接续，保留各自cp/奖励/optimizer/replay/RNG，拒绝未闭合来源/跨族/变更冻结源；
下一普通stage沿新末cp接续。收敛统计沿真实分支保留失败、不混不同奖励历史，原门槛不变。
78项Goal测试通过，真实GPU/阻抗/Direct冻结源兼容；Direct running被正确拒绝，尚未实际选择或派发新stage。
学习轨迹/cp、兼容证据和候选实现已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-selection-20261016T1335/evidence.tar.gz`，
648,113,768字节，SHA256 `9c2e566639765d54913205185058758431faaa1a450ced8536878259fef3d8d6`。
peak3GiB/max512、OOM0/swap0；继续完整Direct对照，随后按证据/存储预算接续。Goal active，未收敛/未最终验收。

## 2026-10-16 21:15 CST Direct末回合安全失败保全，tracking自动接续

Direct control实际10993步/5994连续有限更新，7完整55秒+1短回合，Task/Strict0/8；
末回合54.72秒穿透3.930900mm中止、return−41.679094，不能写成8完整或已收敛。
原协调器自动启动tracking worker2432993，快照2250步/0更新；首1375步实际额外奖励−.388026116762，
非reward replay数组和初始模型/obs_norm均与control一致，只证明接入、不证明有效学习。
已完成阻抗16失败回合64个大型文件离线保留，回收2,294,939,982字节；服务器原件保留、144cp文件hash不变，
离线后完整配对报告相同。恢复清单/日志/RESTORE.md保存并归档，最终审计前须恢复所需原件。
control末4回合/cp含失败、tracking首回合/cp、学习/奖励核验和离线收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-control-close-retention-20261016T1310/evidence.tar.gz`，
1,198,940,149字节，SHA256 `4d38896ac3492a6ddbf0993dab9482fd30172a08e21cf2b954afcc83297677eb`。
本机计算、服务器仅存储/hash。继续完整tracking对照；后续需同时安排checkpoint存储和精确接续，
不能在约19GB安全余量内直接派四族44k（当前体积估算已约39GB）。Goal active，四类未收敛/未最终验收。

## 2026-10-16 20:55 CST Direct真实更新与原始归档恢复

Direct原worker归档快照7000步/2001更新，5完整55秒physical_valid5/5、Task/Strict0/5。
cp5500有501条连续有限更新，actor/critic hash改变；cp2750/4125/5500及5500条训练记录核验通过。
新增已闭合训练回合四类大文件离线/恢复工具，10安全测试及全部69项Goal测试通过。
已完成阻抗失败回合暂移4文件144,291,728字节并恢复，33回合文件与9checkpoint文件hash保持；
最终零离线文件，未删当前Direct数据，尚未批量执行长期保留。内存peak3GiB/max383，OOM0/swap0。
新轨迹/cp、工具/测试与实测收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-learning-offline-20261016T1255/evidence.tar.gz`，
647,988,847字节，SHA256 `7d96b43f7bc0b9edd606baef6d4297f1e7a5deec30872f9f871a850f7458adea`。
第5回合/cp6875仍本地待归档；继续Direct完整对照及后续较长训练。Goal active，四族均无收敛结论，未最终验收。

## 2026-10-16 20:40 CST Direct热身与有限接续预算

Direct原进程3250步/0更新，两个完整55秒Task/Strict0/2、physical_valid2/2；5000热身尚未结束。
首回合/cp1375核验通过。后续prepare-next新增显式22k/33k/44k预算能力，保留四族各自cp、
1M上限和资源保护，59项Goal测试通过；新长阶段未派发，活动Direct快照未改。
14个本地/远端重新核验的重复/tmp传输包已移除，释放5,461,537,291字节，服务器可完整恢复；
原始实验/轨迹/cp/失败不删，长期存储仍需继续处理。
首回合、缓存回收与代码/测试证据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-first-storage-20261016T1240/evidence.tar.gz`，
189,850,878字节，SHA256 `7c74a262eb65e4121a5ab0b5b4fcc0e663dd3af71d1e2689f858d7914b29b6ad`。
Goal active，继续Direct对照；四方法未证明收敛或最终验收。

## 2026-10-16 20:28 CST 阻抗对照结束，Direct v2接续

阻抗control/tracking各11000步/6001更新、8完整55秒、physical_valid8/8、Task/Strict0/8。
4个全学习配对的RMSE中位差−.100881mm，但放置误差+2.718305mm，峰矩/峰速/穿透略增；
提高跟踪权重未证明有效修复，有限pilot不是收敛。最终checkpoint/日志核验通过，失败全部保留。
原服务正常退出、全局锁释放后启动Direct v2，control PID2424017已750步/0更新热身，
from scratch、n25/UTD1/CUDA0、各11k预算，后接weight4处理组；没有重复仿真。
最终两回合/cp、完整对照及Direct启动证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-pair-close-direct-launch-20261016T1226/evidence.tar.gz`，
540,752,690字节，SHA256 `77e18a30d230fd041a5042cc1165e996c6d3abf0b8567876ee30fa2f9d2ab436`。
Goal active，继续Direct及后续四方法训练；未最终验收。

## 2026-10-16 20:15 CST 两个全学习配对完成、仍未解卡

tracking原进程9000步/4001更新，6完整55秒Task/Strict0/6、physical_valid6/6。
cp6875/8250及3251条连续有限更新核验通过。两全学习配对的RMSE中位差−.100881mm、
放置误差−1.274364mm，但峰矩/峰速/穿透略增，未证明有效收敛。
两回合末段carry20/28；首回合servo遥测表明名义指令非零、等效速度限幅几乎无影响，
进一步排查不能直接归因为该限幅器。未改活动源码/gate，OOM0/swap0，保留内存限制。
两原始轨迹/cp/配对/诊断已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learned-20261016T1212/evidence.tar.gz`，
534,465,416字节，SHA256 `aa19ceb33724a597a141fd8b10074635bb7da0af6d4fdfaeb0c741871188f5fb`。
Goal active，继续完整配对及Direct v2，未最终验收；详见Goal进度。

## 2026-10-16 20:05 CST tracking进入真实更新，原进程继续

tracking原trainer2413986已6500步/1501更新，四完整55秒Task/Strict0/4、physical_valid4/4。
cp5500的501条更新连续有限，actor/critic保存文件改变；cp2750/4125/5500及5500步日志核验通过。
配对报告3热身/1混合/0全学习；混合对RMSE差−0.00004432mm、放置误差+0.017674mm，
无有效改善结论。继续登记处理组，未重复启动或改活动快照；OOM/max0、swap0。
第2–4轨迹/cp、学习日志和配对/核验证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-learning-20261016T1200/evidence.tar.gz`，
653,909,672字节，SHA256 `9d26c72d6443420a51ffd36aaddf1b53c621e204de963b2bafc76633b0cf09ac`。
Goal active，Direct v2待阻抗对照完成，四类均未证明收敛/最终验收；详见Goal进度。

## 2026-10-16 19:43 CST tracking首回合实际奖励/replay核验

tracking2500步/0更新热身，首完整回合return−26.51296、Task/Strict失败、physical_valid=true。
与control同条件首回合轨迹/动作及未更新网络hash完全一致；1375区间新增成本为−36*bounded_error，
合计−1.019543795131，实际checkpoint replay奖励匹配，五个非reward数组一致。
证明处理实际进入训练，不证明学习改善；当前只有1对热身、0对学习结果。原trainer健康，无OOM/swap。
首轨迹/cp/奖励分解/配对与replay核验已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-tracking-first-20261016T1142/evidence.tar.gz`，
193,524,455字节，SHA256 `ebc3e5cb64c190426c45684c0b376d5939f5588080bde14d3ae6d39d9a3b6a03`。
Goal active，继续处理组及后续Direct，尚未收敛/最终验收。

## 2026-10-16 19:35 CST 阻抗control11k闭合，tracking自动启动

control11000步/6001连续有限更新、8完整55秒，Task/Strict0/8、physical_valid8/8，未收敛。
原协调器自动启动tracking trainer2413986，实际from scratch、跟踪总weight40，现750步/0更新热身。
control最后3回合/cp8250/9625/11000及完整日志/交接/诊断已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-control-close-20261016T1132/evidence.tar.gz`，
803,419,415字节，SHA256 `16f0082c6802fa746cb1e2a83342746458166d65821add63bee32d3e8a8cf0ae`。
control共8回合及所有边界cp加此前包均已保全，服务器仅存储/hash；其最终内存max1828但OOM0/swap0。
两个全学习回合末段仍carry20/28、位置约12.6–12.8mm，继续既定权重对照，不作改善结论。
Direct v2待当前配对结束，Goal active，四类尚无收敛/最终验收证据。

## 2026-10-16 19:16 CST 阻抗8000步，配对报告与第五回合归档

原trainer2400811到8000步/3001更新，五个完整回合Task/Strict0/5、physical_valid5/5。
第五全学习回合return−25.68230、仍carry，尚未收敛。新增配对报告按条件/曝光匹配及热身阶段分组，
保留所有失败/缺失，不比较不同reward总分；6测试和真实报告通过，处理组未启动因此无配对效果结论。
工具/报告/第五轨迹/cp6875已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-pair-report-20261016T1116/evidence.tar.gz`，
266,677,855字节，SHA256 `6c16b1005c956b60e11604f29b1c7d8e9deb199096c2efa7a0fbb2709c193093`。
内存包含约1.46GB文件缓存，随后3GiB触顶回收max85、OOM0/swap0，仍真实推进；继续跟踪压力。
Goal active，未改活动训练或冻结接口，未最终验收。

## 2026-10-16 19:07 CST 阻抗热身转学习已核验

原trainer2400811到6000步/1001更新；cp5500的501条真实更新连续且有限、actor/critic文件hash改变，
cp4125/5500源文件及归档成员hash通过。第四完整回合return−24.997562，四回合Task/Strict0/4、
physical_valid4/4，无收敛结论。OOM/max0、swap0，仍单模拟器/3GiB/UTD1/CUDA0。
第三/第四轨迹与两个checkpoint、截至5500步日志和核验源码已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-learning-20261016T1105/evidence.tar.gz`，
459,990,965字节，SHA256 `c7b7c8a674282783bc8c056ebfdf69d2dfad617768efd949cd77ed32938c3d60`。
Goal active；继续阻抗control→tracking，Direct v2后续接续，最终acceptance仍未运行。

## 2026-10-16 18:58 CST 阻抗control三个热身回合闭合

Goal active，原trainer2400811持续4125步/0更新（5000步热身），三个55秒回合
physical_valid3/3、Task/Strict0/3，return−25.49341/−26.06712/−25.07228。
OOM/max0、swap0；第四回合已启动，未重复派发或改活动源码。下一核查5000真实更新及5500checkpoint。
第二回合/cp2750核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-warmup-20261016T1058/evidence.tar.gz`，
193,890,501字节，SHA256 `89398d832ac2abe46b389832768c8ba648fc8187f322fc25c1d74c434c8868f0`。
归档首版误处理在途行的失败及修复记录均保留，训练未受影响；第三回合仍本地待同步。
阻抗处理组/Direct v2尚未启动；当前无收敛/最终验收结论，详见Goal进度。

## 2026-10-16 18:50 CST 修复Direct GPU准备依赖遗漏，阻抗热身继续

旧Direct快照转GPU只刷新部分模块，实测入口ImportError；修复为配套刷新五模块，保留原失败目录。
回归先复现失败，修复后52项Goal测试通过。Direct新v2目录实际CUDA预检通过、OOM0，未启动仿真。
原阻抗trainer2400811继续2250步/0更新，首1375步完整热身Task/Strict失败、physical_valid=true，
return−25.49341，cp核验通过；同seed历史CPU热身两轨迹文件hash一致，不能据此声称学习改善。
首比较对匹配NaN误判的失败也保留。修复/预检/失败/首回合与checkpoint已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-direct-preflight-fix-20261016T1048/evidence.tar.gz`，
SHA256 `86cf7d09e6693291a4a251bc3fee4833621b253f5006a0f909ed583dae9ec421`。Goal active，尚未收敛/最终验收。

## 2026-10-16 18:40 CST 四族GPU完整验证闭合，阻抗奖励对照已开训

四族各新增1375步/1375更新、完整55秒，checkpoint/奖励/资源检查通过，OOM0/swap0。
四回合Task/Strict均失败；n25谱系各9回合仍全失败，未收敛。导纳/VMC原始数据与四族收尾归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-close-20261016T1035/evidence.tar.gz`，
SHA256 `1940f7934c88cc047e72d031ce7c369a0c2ebccd945d8d0abe81ad924f9642d8`，前两族引用原独立包。
阻抗GPU新配对已prepare/preflight/launch：跟踪权重4对40，两fresh同seed组各11k、串行/3GiB/swap0，
冻结物理/gate等不改；control trainer2400811已有250交互/0更新（5000热身），tracking仍排队。
源码/登记/预检/启动快照已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-gpu-launch-20261016T1038/evidence.tar.gz`，
SHA256 `92303c15324ca854e402f2fa1dc083d2d5ad5bf549dad9a8b8d764d3da8b092a`。Goal active，无奖励改善/收敛或最终验收声明。

## 2026-10-16 18:25 CST GPU前两族完整回合已归档，导纳在途

Direct62906/96564、阻抗12375/7376，各新增1375步/1375更新，两完整55秒回合Task/Strict均false；
Direct physical_valid=false、阻抗true。checkpoint/更新序列/reward重算通过，峰值约2.31GB、OOM0/swap0。
阻抗末10秒仍cursor20/28、误差12.599–13.074mm，支持后续已登记跟踪权重对照，未证明根因或收敛。
两完整轨迹/checkpoint/日志及诊断已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-first-pair-20261016T1022/evidence.tar.gz`，
SHA256 `80052f2894e1ed09256961858a2a63c04ab266241625f1ed92b8925dd90d657e`。
导纳原PID2396091已11472/6473，VMC排队。Goal active；四族GPU循环完成后先运行阻抗奖励配对，未最终验收。

## 2026-10-16 18:10 CST 四族首段结束，GPU实际接续训练

Stage01四族各8完整回合Task/Strict0/8；Direct61531/95189，另三族11000/6001（steps/updates）。
VMC均值−25.261000130/std .067965733，physical_valid8/8；失败平台不算收敛，Goal active。
四族最终checkpoint及VMC末两原始回合/奖励/日志已核验归档至服务器runs/main/
`rl-goal-stage01-close-20261016T1002/evidence.tar.gz`（完整主机根同下），SHA256
`e8274358f90e0bfc895d7cb41e5fb2be331a76516937d79b623bd590e66a0642`。
新GPU阶段各1375步，四族各一次CUDA恢复预检均通过；10:08Z实际启动，Direct由61531推进至
61912步、95570更新（新增381/381），OOM0/swap0，首回合在途。保持单模拟器/3GiB/冻结物理等，
不是GPU完整回合验证已通过。源码/登记/预检/真实启动收据已核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-launch-20261016T1010/evidence.tar.gz`，
SHA256 `15e0f26aea078cb9bff45175d0953ab0f6cfee6d55a800bb69e583dcae11cc1f`。后续完整循环通过后运行奖励对照，未最终验收。
18:13复查Direct GPU首个55秒完整回合结束62906/96564，cp九文件hash通过；return−38.73316，
Task/Strict与physical_valid均false，保留失败。峰值2,306,428,928字节、OOM0/swap0。
协调器已自动接续阻抗；Direct新轨迹/checkpoint暂仅本地待后续归档，不冒充已进入启动包。

## 2026-10-16 17:40 CST VMC六完整回合，学习更新继续

VMC原PID2375301推进至8500步/3501更新，第7回合在途；6完整55秒physical_valid6/6、
Task/Strict0/6，第6return−25.157868312，末10秒cursor18→20，仍未完成任务或收敛。
cp8250与奖励重算通过，OOM0/swap0。原始回合/checkpoint/优化器及资源收据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-episode6-20261016T0940/evidence.tar.gz`，
SHA256 `199cc0cb0b465e947f566e398a227782e683dc2eaae561863b9adc05ef0be312`。Goal active，冻结设置不改，后续GPU验证与奖励对照不变。

## 2026-10-16 17:30 CST 纠正零路点就绪计数的含义，VMC五回合仍未成功

VMC7250步/2251更新，5完整55秒physical_valid5/5、Task/Strict0/5，第5return−25.33003。
规划器先换目标再记观测，0/250位置就绪不能单独证明停滞；只读诊断新增cursor推进计数，5测试通过。
复核21回合：阻抗8/8末窗cursor20不变，导纳3/8末窗仍推进，VMC5/5末窗推进1–2个路点。
失败标签不变、不推断因果改善；冻结环境/gate不改。第5回合/cp6875及修正诊断已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-waypoint-progress-20261016T0930/evidence.tar.gz`，
SHA256 `79b7d1bacc2cb2383cc3fd5beb4ccd5dea5ded3fafb06f7ed3c2c650d13fabbf`。Goal active，VMC第6回合在途。

## 2026-10-16 17:20 CST VMC学习更新与checkpoint实际变化通过核验

VMC原PID2375301推进至6000步/1001更新，4个完整55秒回合Task/Strict0/4、physical_valid4/4，
第4 return−25.284312267。cp4125→5500中updates0→501，四类网络文件hash变化，501条更新
连续且指标有限；首次学习已落盘但尚无收敛。第5在途，OOM0/swap0，冻结源/限制不变。
第3/4回合、两checkpoint及更新/奖励/资源证据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-vmc-learning-20261016T0915/evidence.tar.gz`，
SHA256 `bce8ae27d12b34b3097b19045d61bccb73359cf8d6dfc6108832593d075b1c79`。Goal active，训练继续。

## 2026-10-16 17:05 CST 导纳critic诊断分层，VMC两完整热身回合

VMC原trainer到3500步/0更新（5000热身），两完整55秒回合Task/Strict0/2、physical_valid2/2，
return−25.24207/−25.23735；第三在途。导纳cp11000末窗口残差拆分为最新25条3.84085、
旧175条.07309，避免把仅有一次更新机会的新终端窗口当成整体拟合失败；仍无成功/收敛证据。
只读诊断exit0、原统计不变、checkpoint/RNG未改；VMC前两回合和cp1375/2750、诊断收据归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-credit-vmc-20261016T0900/evidence.tar.gz`，
SHA256 `45e732d9d9780e1504d679fb4141bf1272b9657c57e64e6113b903e86ae2b9d4`。Goal active，后续GPU验证/奖励对照不变。

## 2026-10-16 16:50 CST 导纳11k有限段结束，VMC真实接续

导纳11000步/6001更新、8完整55秒回合，physical_valid8/8、Task/Strict0/8，reward均值
−25.37961、std.06605，未收敛。cp11000核验通过，原协调器自动启动VMC PID2375301，
已750步/0更新、仍热身，无重复训练。末回合/最终checkpoint/完整日志与八回合诊断归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-close-20261016T0850/`，
包SHA256 `ad63cc832e472ea8aaca5f05023710262d5afecb9ee8a958ec0315776e6c8532`。
摘要脚本在归档完成后因旧记录缺resource_snapshot报错，独立服务逐成员复核归档完整；
错误sidecar保留、缺失最终导纳内存值不补造。VMC交接实测OOM0/swap0。Goal active。
16:56 CST复查VMC1500步/0更新，首完整回合return−25.242069151、Task/Strict0/1、
physical_valid1/1；第二回合在途，新数据仍在本机，热身期不判收敛。

## 2026-10-16 16:40 CST Goal磁盘保留线修复，导纳第7回合归档

导纳9701步/4702更新，7完整55秒physical_valid7/7、Task/Strict0/7；第8在途。修复trainer
每回合只查旧20GiB、遗漏Goal50GiB的问题：后续取所有登记最大值，回合边界保存后停止新派发。
49项Goal＋6项恢复测试通过，真实登记计算50GiB；当前约79.6GiB，活动冻结source保持不变。
GPU新配对准备会引入该修复；额外tracking权重说明改为真实4/36，奖励计算保持。
第7轨迹/cp9625、修复与存储盘点已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-disk-guard-20261016T0840/`，
SHA256 `0d1e3c4bcc31c7c5f191b0c83fa21053a357e222c43e620e6ddc31dc02626eaf`。未删原始文件；
四百万交互轨迹空间外推407–472GB，后续仍需归档/离线保留。Goal active，未收敛。

## 2026-10-16 16:30 CST 导纳6回合奖励/实际参数复核，训练继续

导纳快照8326步/3327更新，cp8250与第6完整55秒回合正常保存，physical_valid6/6、
Task/Strict0/6。reward均值−25.34683、标准差.03004是失败平台。六回合奖励重算一致；
末回合末10秒仍carry17/18，误差12.36–18.30mm，参数变化且energy_scale1，尚无动作不应用证据。
不同condition与25Hz样本限制保留，不将该诊断当因果改善或最终物理审计。OOM0/swap0，
max1311回收事件未造成观察到的更新停滞；原服务继续，无重复进程，VMC排队。
第6轨迹/cp8250与六回合诊断归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-learning-20261016T0830/`，
SHA256 `a83b4c807756c4c4812b7ccd227e471070324f3c38ce7c88dc777adcd0a48ea5`。Goal active。

## 2026-10-16 16:20 CST GPU配对训练准备入口已补齐，导纳第5回合保全

导纳快照7364步/2365更新，5完整55秒回合physical_valid5/5、Task/Strict0/5；第5return−25.29435。
新增从未启动CPU对照创建独立fresh GPU对照的显式入口，要求四族真实GPU全循环通过和冻结
物理/runtime匹配，原CPU目录保持，必须新的CUDA预检。49项Goal测试通过；实际调用因前序
仍在运行按预期拒绝，未建GPU目录或新模拟器。memory.events.max503、OOM0/swap0，继续更新。
第5导纳原始轨迹/cp6875与实现/测试/拒绝收据已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-pair-entry-20261016T0820/`，
SHA256 `68548ebda3ad34e1c641c3fd6c9e7f9b1a84e98572dd055058910fc352d4fa56`。
Goal active，准备入口不是GPU训练验证或收敛；实际GPU全循环和奖励对照尚未派发。

## 2026-10-16 16:10 CST 末端邻近诊断与导纳梯度更新

导纳6576步/1577更新，4完整55秒回合physical_valid4/4、Task/Strict0/4；VMC排队。
只读阻抗11000/导纳5500 replay：同回合末端与早期邻居的n25奖励约−22.5对−.05，
但bootstrap mask不同、输入非精确相同，不能将奖励差当作完整目标矛盾或已证实bug。
3项测试/真实诊断通过，checkpoint未变，未改冻结输入/gate；OOM0/swap0，无重复训练。
原始第4导纳回合/cp5500和诊断已保全至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-terminal-neighbours-20261016T0810/`，
包SHA256 `19116474cc1bb4db182f5fcd829131fb68f1484d793c299194d1aa9cd5024d13`。
Goal继续；GPU完整循环预检/奖励对照尚未派发，未声称收敛或最终通过。

## 2026-10-16 16:00 CST 导纳开始梯度更新，重复传输缓存已核验清理

导纳5250步/251更新、3完整热身回合Task/Strict0/3；部分carry窗口仍跨多个路径点，不能
直接照搬阻抗固定点停滞的原因。cp2750/4125与对应原始回合已核验归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-admittance-storage-20261016T0800/`。
重新核验9个/tmp传输包与服务器最终SHA256后清理4.73GiB冗余，保留全部原始数据/checkpoint；
恢复命令与逐文件收据已归档，本地约82GiB可用。未改变训练协议或保护线，Goal继续。

## 2026-10-16 15:50 CST 阻抗新鲜配对奖励干预已准备，尚未在线训练

根据8个失败回合的弱跟踪奖励证据，实现并登记权重4→40、其余一致的阻抗fresh两臂对照，
各11k/同seed/n25/UTD1/CPU1/3GiB/swap0；43项Goal＋5项恢复测试和真实2次丢弃更新预检通过。
初始网络相等、checkpoint不变、无OOM；stage01尚未完成，实际就绪检查拒绝新派发。
导纳原训练已2750步/0更新、2完整回合Task/Strict0/2；冻结源码未改。新pilot与导纳首回合
已核验归档至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-weight-pilot-20261016T0750/`。
尚无干预效果/收敛结论，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:40 CST 阻抗阶段结束但未收敛，导纳按原队列启动

阻抗11000步/6001更新、8个完整55秒回合，Task/Strict0/8、physical_valid8/8，仍停carry。
回报−25.5873±.4733的波动主要来自峰矩，不能当作成功平台。cp11000/最终轨迹与训练诊断
已核验归档至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-impedance-close-20261016T0738/`。
原协调器自动接续导纳PID2360933，已750步/0更新（热身），无OOM/swap；VMC排队。
四族训练与最终验收未完成，GPU完整循环验证尚未派发。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:26 CST 显式GPU接续实现并通过资源guard预检

新增四族GPU完整循环验证阶段入口：前序正常闭合后，各最多1375新交互，完成四个完整回合
且实际设备/亲和性/内存检查通过才允许常规续训。当前提前prepare被正确拒绝，没有GPU训练。
40项Goal＋5项恢复测试通过；真实CUDA guard102次丢弃更新有限、峰值1.293GB、OOM0、
checkpoint不变。原CPU阻抗9750步/4751更新、7完整回合Task/Strict0/7；第8在途。
第6/7轨迹及cp8250/9625和实现证据已核验归档至服务器独立目录
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl-goal-gpu-backend-implementation-20261016T0724/`，
534,028,451字节，SHA256 `84534fda395ebba80b0b97ec9dbfaea450f2799f2c81313974e64e03d6b60f0e`。
详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 15:10 CST 发现可用GPU更新加速，阻抗仍未过carry

同一阻抗训练已8000步/3001更新、5完整回合Task/Strict0/5；第五回合/cp6875已核验归档。
奖励分解与5500 cp只读诊断显示回报变化主要来自峰矩、末端价值拟合尚不足，不是收敛。
有限CPU/CUDA丢弃更新探针通过：修正绑核并验证实际亲和性[6]后，同batch更新CPU3.89/s、
CUDA191.41/s；优化器部分49.26倍，完整循环尚未测。初次未核验绑核的结果保留但排除比较。
无仿真/模型保存/活动环境修改；下一步登记GPU后端并验证完整循环，不修改冻结活动stage。
源码、所有探针与失败训练证据已归档核验，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:53 CST 阻抗梯度更新启动，carry阻塞定位

阻抗5500步/501更新checkpoint已核验，继续推进至5769/770，4个完整回合Task/Strict0/4、
physical_valid4/4。闭合训练诊断显示四回合末10秒均卡carry第21/28点：位置误差未进12mm，
也未越过横向重入平面；姿态/速度满足。原生未知凸边接触持续到结束，不能把低刚度定为
唯一原因或放宽门槛。新增3项诊断测试通过，四回合/四checkpoint已完成远端大小/hash核验；详细证据、
hash与局限见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。Goal active，尚无收敛或最终验收。

## 2026-10-16 14:35 CST Direct失败证据归档齐全，阻抗继续推进

Direct阶段8回合均停approach，Task/Strict0/8；最后4回合/4 checkpoint与完整日志已归档核验，
本阶段8回合现分三包共享。最终checkpoint只读诊断显示最新回合TD残差仍大，未证明收敛。
阻抗真实3000步/0更新（热身），2完整回合physical_valid2/2但Task/Strict0/2，第三回合在途；
2750 checkpoint hash通过。新tracking对照已准备，仍等待四族阶段闭合。详见
[Goal进度](RL_GOAL_PROGRESS_20261016.md)中的服务器路径/hash与诊断局限。

## 2026-10-16 14:21 CST Direct阶段结束，阻抗已自动接续

Direct61,531步/95,189更新，本阶段8完整回合Task/Strict0/8、physical_valid3/8，最终hash通过。
原协调器自动切至impedance，真实250步/0更新（5000步热身），后两族排队；无重复训练。
密集tracking的fresh同seed两组对照已登记，各11k、总22k；前序四族全部闭合后才允许派发。
30项测试和两组真实丢弃更新预检通过（相同初始网络hash、峰值1.36GB/OOM0），源码/登记/
预检已归档。未启动新对照，未收敛/未最终验收；详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:10 CST 密集跟踪奖励组件与隔离检查完成

Direct60,090步/93,748更新，第七回合继续，已完成六回合Task/Strict0/6；其他三类排队。
新增可选有界tracking奖励（权重4）和提前失败剩余成本，旧新奖励resume及统计拼接均拒绝。
27项相关测试与trainer编译通过；五条真实历史轨迹奖励复算确认更好的跟踪获得更高候选回报。
仅验证奖励算术，未部署新训练、不声称策略改善；活动源码/物理保持，Goal继续。
源码/测试/完整输入与复算证据已核验归档，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:01 CST 训练奖励诊断与第六回合闭合

Direct58,781步/92,439更新，6个完整回合Task/Strict0/6，58,781 checkpoint hash通过；
第7回合继续，其余三方法排队。新增奖励分解工具/3项测试，五回合完整快照通过公式/日志核验。
Task信号每1375步仅末步−20；无安全罚分的两条失败轨迹跟踪cost差异很大但折扣总回报相同。
支持下一阶段检验密集跟踪奖励，未证明唯一根因，未改变当前训练或重标最终gate。
诊断源码/完整证据已归档核验，路径/hash见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:55 CST 五个完整回合与失败产物归档

Goal active；Stage01 Direct57,750步/91,408更新，新增7219/7219，5完整回合Task/Strict0/5、
physical_valid2/5；第5回合return−35.653907、仍停approach，第6回合在途，其余三方法排队。
57,406 checkpoint hash通过，OOM0/swap0，但内存已触及硬限回收，继续观察。
episode38–40原始轨迹及三个checkpoint已核验归档，835,219,332字节；episode41之后待同步。
未收敛、未最终验收，详细hash/服务器位置见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:39 CST 收敛统计可复核，第四回合继续

Stage01 Direct optimizer已到55,804步/89,462更新，54,656 checkpoint hash通过；3完整回合
return均值−31.810846、标准差7.480807，Task/Strict0/3、physical_valid1/3，第四回合在途。
新增按精确阶段lineage统计的收敛筛选，落实原登记96回合/两个32回合窗口及联合成功要求，
保留失败/未完成，拒绝重复计数或跨reward拼接；8项测试通过，真实结果不满足收敛。
worker OOM0/swap0，其他三类未启动。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:31 CST 精确接续入口完成，第三回合继续

Stage01 Direct已到54,500步/88,158更新，保持UTD1；2个结束回合Task/Strict0/2，第三回合在途。
补齐四方法各自checkpoint的prepare-next及逐方法预检封存，避免后续阶段误从零重训。
15项测试通过；真实53,281步n25 checkpoint/replay/RNG恢复与一次丢弃更新通过（峰值1.13GB/OOM0）。
当前running阶段被正确拒绝提前接续，未建立stage02，活动冻结源码不变。其他三类排队，
其真实接续预检待checkpoint生成后执行；未收敛/未验收。入口见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:22 CST Goal训练继续，完成只读Bellman/动作诊断

同一Stage01 Direct worker已完成2个完整回合，到53,281步/86,939更新，新增2750/2750；
return−21.667945/−34.277519，Task/Strict0/2、physical_valid1/2，第三回合运行中。
固定51,906 checkpoint的训练replay诊断通过：target裁剪概率质量极小，但terminal附近
当前动作Q明显高于历史动作，新回合TD残差较大；记录为动作外推/样本学习候选线索，未断言bug。
2项数学测试通过；真实只读诊断无梯度/仿真，峰值924MB、OOM0，模型hash/RNG不变。
活动训练和冻结快照保持，其他三类排队，未收敛、未验收。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:02 CST 持续Goal接续，Stage01已启动

用户明确开启持续Goal，旧15小时截止不再作为后续工作的终止授权；旧run保持原始收据。
旧恢复结束于50,531步，本段5个完整回合Task/Strict0/5，最终checkpoint hash通过。
新`outputs/rl_goal_20261016_stage01/`已登记四方法串行、各新增最多11k、25步回报、UTD1，
Direct保留旧checkpoint及原始replay，仅作明确的信用窗口迁移。13项测试与真实checkpoint
预检通过；协调器与Direct worker已启动，其余三方法排队，未收敛、未验收。
后续优先检查该阶段execution/service；详情与完成判据见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 12:04 CST 已授权修复落地，恢复训练完成首个回合

用户明确授权后，旧v2保存卡死进程已退出，partial checkpoint保留；旧v3b两路收完在途回合，
阻抗112,750步、Direct73,365步checkpoint均校验通过，末尾历史源码变更导致的失败收据保留。
确认子进程退出才结束旧协调器。新独立service已从v4的43,656步checkpoint恢复：新增1375步/
1375更新，45,031步checkpoint hash通过，真实UTD1、3GiB硬限、swap0、OOM0，源码hash一致。
首个55秒回合return−22.1773，Task/Strict均false，尚未收敛；下一回合已运行。其余三方法
未启动，未做统一acceptance。原派发截止12:33:19 CST仍有效，结束在途回合后保存退出。

**后续监视入口改为**父目录`RECOVERY_CURRENT.json`与
`outputs/rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety/execution.json`，
service为`sii-rl-v4-recovery-recovery-20261016-1140b.service`；旧execution保留为历史，不得
重复启动旧协调器。详细故障、reward分项与只读critic诊断见[修复报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:32 CST 修复进展

已实查v2保存卡死、v3b遗留并发和UTD失配；完善独立硬限恢复入口与每回合checkpoint，
5项回归测试通过。真实checkpoint恢复/梯度更新诊断通过（峰值约1.45GiB、OOM0），
排除该checkpoint不加载或完全不更新，但尚未证明闭环收敛。恢复登记已就绪，旧进程处理被
自动审批拒绝、未执行，仍需明确授权才能释放资源并启动恢复。
详见 [修复与验证报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:06 CST 复查

v4无进程、无新增交互，日志仍47,448步/84,898更新；34已结束回合Task/Strict各0/34，
其他三方法未启动，43,656步checkpoint hash复核通过。MemAvailable约3072MiB仅等于worker
上限且无余量，旧v3b两路仍运行，本轮未恢复或验收，原截止12:33:19 CST不变。
本轮收据及资源细节见 [v4监视报告](RL_V4_MONITOR_20261016.md)。

## 2026-10-16 10:46 CST 复查

v4进程为空、无新增步数；原running收据为中断前状态。仍为47,448步持久化日志、34已结束
回合，Task/Strict各0/34，其余三方法未启动；43,656步checkpoint hash复核通过。
MemAvailable=3035MiB不足3072MiB worker预算（未加余量），本轮未派发恢复或验收。
原截止12:33:19 CST不变，旧v3b进程未干预；详见下方交接报告的本轮补充。

## 2026-10-16 10:33 CST 最新 v4 状态

Direct 至少 47,448 步，34 个已结束回合 Task/Strict 均 0/34，其余三方法未启动；没有收敛或
acceptance 结果。宿主机检查发现实际 UTD=2 与登记1不符，且没有独立3GiB/禁swap硬限。
本轮请求安全停止后整个v4进程树消失，未写出新checkpoint；保留在途失败收据，不冒充正常
回合末退出。已准备独立恢复trainer并验证UTD循环，但可用内存不足，尚未恢复。
详见 [本轮证据、修复和交接](RL_V4_MONITOR_20261016.md)。下文为历史结果，不代表当前进程状态。

最新结果以 [本周三维对比周报](BASELINE_WEEKLY_REPORT_20260923.md) 为准：已完成当前 48D 五方法配对、阻抗积分参考 K300/K900 对照及导纳参考 r2 完整回合。以下 primitive 与 RL pilot 记录保留作前期工程诊断，不与当前配对主表混合。全套检查现为 105 项通过；本轮实验已结束，无后台训练或仿真遗留。

本周先完成 impedance/admittance 的开发矩阵，再建立两类 RL baseline 的文献与本机复现入口：

1. RL 调 VMC/阻抗/导纳参数；
2. RL 直接输出柔顺 action。

当前 GitHub 主线为 `0e9142e9b6c03c22995914e9ef66226cfca27a18`。本记录只引用有 source hash、命令和结果文件的实验。

后续新增公平比较审计：[FAIR_METHOD_COMPARISON_20260923.md](FAIR_METHOD_COMPARISON_20260923.md)。历史 120 条 isolated push 不能冒充 current proposed 的正式对照：完整 provenance 缺失、旧 source/controller 标签不可靠、全部超过当前 0.2 mm 门槛。当前冻结 48D 模型来源见 [CANONICAL_MODEL_PROVENANCE_20260923.md](CANONICAL_MODEL_PROVENANCE_20260923.md)；新配对 panel 矩阵和接口限制见 [PANEL_CLASSICAL_INTEGRATION_20260923.md](PANEL_CLASSICAL_INTEGRATION_20260923.md)。

## 1. 服务器经典 baseline

服务器完成了 24 条隔离运行：

```text
controller × fixture × variant
2 × (ball, push, corner, table_corner) × 3 = 24
```

完整结果：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume/FINAL_RESULT.json
```

本机只读保存了同一汇总：

```text
outputs/server_baseline_20260923/FINAL_RESULT.json
```

固定参数开发矩阵的通过情况如下：

| 控制器 | ball | push | corner | table_corner | 总计 |
|---|---:|---:|---:|---:|---:|
| Cartesian impedance | 3/3 | 3/3 | 0/3 | 0/3 | 6/12 |
| Cartesian admittance | 2/3 | 0/3 | 0/3 | 0/3 | 2/12 |

这里的通过数已经同时满足严格的 `penetration <= 0.2 mm`、有效接触、无上游误碰和任务完成条件。完整的逐回合 penetration、端点误差、峰值外力、峰值力矩和失败原因见 [CLASSICAL_BASELINES_20260923.md](CLASSICAL_BASELINES_20260923.md)。

实现边界需要保留：impedance 使用 `J.T @ (K e + D e_dot)`，并经现有 torque feasibility/slew 栈；admittance 使用本体 joint-load 估计 wrench，积分 `M x_dd + D x_d + K x = wrench`，再输出 bounded Cartesian velocity residual。admittance 当前把虚拟 offset 用于内部弹簧反馈，但没有把 offset 变成独立的 WBC reference，因此 nominal WBC 会和虚拟位移产生竞争；这解释了 push/corner/table_corner 的失败，也是下一轮应修正的控制接口问题。

这组数据是 source primitive 的固定参数开发诊断，不是 office blind-test，也不是参数搜索后的论文最终 baseline。当前结果支持的结论是：传统 impedance 在球/棍推 primitive 上有可用工况，但在两个桌角 fixture 上没有通过完整任务 gate；admittance 的固定配置还没有通过持续推压和桌角任务。

复现命令（服务器隔离 source snapshot）：

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/source_resume
/home/arm1/vmc_mujoco_runtime/.venv/bin/python scripts/run_classical_matrix_20260923.py \
  --output /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie --workers 8
```

## 2. 2024 年以后“RL 调参数”文献

详细核验见 [RL_PARAMETER_LITERATURE_20260923.md](RL_PARAMETER_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 适合本项目的 baseline 解释 |
|---|---|---|
| Da-VIL: Adaptive Dual-Arm Manipulation with Reinforcement Learning and Variable Impedance Control | ICRA 2025，DOI `10.1109/ICRA55743.2025.11127487` | PPO 输出 6 个笛卡尔对角刚度，再由 CVXPY QP 和动力学计算关节力矩；适合映射为 RL 输出 6D VMC stiffness |
| Impedance Primitive-Augmented Hierarchical Reinforcement Learning for Sequential Tasks | ICRA 2025，DOI `10.1109/ICRA55743.2025.11128462` | 高层选择 primitive，参数策略输出阶段相关刚度/任务参数，primitive 内使用自适应刚度；适合做 phase-conditioned parameter baseline |
| Variable Impedance Control Combining Reinforcement Learning and Gaussian Process Regression | IEEE-RAS Humanoids 2024，DOI `10.1109/Humanoids58906.2024.10769856` | RL/FCEM 学 stiffness-damping，GP 建模物体重量变化，momentum observer 提供外力矩估计；公开资料不足以编造完整 obs/action，应先按 paper-spec 补齐 |

这类 baseline 的 action 不是项目的 7D action。公平实现应为：RL 使用允许的本体观测输出 `K/D` 或低维 schedule，解析 VMC/阻抗控制器将参数转换为项目统一的 7D action，再通过同一安全栈。物体姿态、质量、接触 truth、未来事件和障碍物几何必须从 blind student observation 中剔除。

## 3. 2024 年以后“RL 直接输出动作”文献

详细核验见 [RL_ACTION_LITERATURE_20260923.md](RL_ACTION_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 动作和迁移限制 |
|---|---|---|
| SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning | ICRA 2024，DOI `10.1109/ICRA57147.2024.10610040` | RLPD/SAC 风格，7D 常见形式是 6D pose delta + gripper；可作为 SAC/RLPD-action7 的算法来源 |
| HIL-SERL: Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning | Science Robotics 2025，DOI `10.1126/scirobotics.ads5033` | RLPD + demonstration/human intervention；动作为 Cartesian 6D twist/target，夹爪另有离散策略；没有真实 FR3 和纠正数据不能声称忠实复现 |
| AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries | RSS 2024，[官方论文页](https://roboticsproceedings.org/rss20/p064.html) | PPO 直接输出 6D incremental pose，底层 task-space impedance；actor 使用目标位姿，critic 使用 privileged state，必须改成 48D proprio-only 才能公平比较 |

三篇的动作语义都不同于当前 ESN 的 `[slowdown, yield_6d]`。本项目应实现 interface-matched `PPO-action7` 和 `SAC/RLPD-action7`，把原论文作为算法来源，而不是把原论文 action 维度直接塞进当前环境。

## 4. 本机 RL 工程预实验

本机使用 RTX 5080（CUDA 12.8 PyTorch，`torch 2.11.0+cu128`），运行环境为 `.venv-rl`。仓库 89 个测试仍然通过：

```bash
PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts \
  .venv-rl/bin/python -m pytest -q code/mujoco_6d_vmc_benchmark/tests
# 89 passed
```

由于本机主内存约 16 GB，训练脚本使用单进程 `DummyVecEnv`、单环境、1--3 个 CPU 核和 6 GB 内存上限。首轮并发 16 worker 曾触发系统 OOM；该故障已定位并停止并发方案。

入口脚本：[run_rl_local_pilot_20260923.py](../tools/run_rl_local_pilot_20260923.py)。它会写入 command、Git/source hash、依赖版本、normalization、checkpoint 和冻结评估；默认只用两条旧 rod development fixture 训练，另两条 fixture 做验证，不使用 office 数据。

### 4.1 PPO 调六维刚度

输出目录：

```text
outputs/rl_pilot_r2_stiffness_ppo/
```

配置：`51D proprioception -> PPO -> 6D stiffness action`，8,192 steps，单进程，约 42 s。零动作和学习策略在 4 个 legacy fixture 上均通过旧版“有效碰撞 + 抓起保持 + 配对 no-rod + 无 hard torque limit”判据：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [true, true, true, true],
 "publication_ready": false}
```

这个结果只证明 RL 调参链能运行；零动作也全部通过，不能据此宣称 PPO 改善了 VMC 或优于 ESN。它还没有使用当前 canonical 48D observation、四类正式 teacher split 或 office blind test。

### 4.2 SAC 直接输出动作

输出目录：

```text
outputs/rl_pilot_r2_direct_sac/
```

配置：`32D legacy WBC state -> SAC -> 7D direct residual action`，8,192 steps，单进程，约 69 s。零动作四个 fixture 全通过，而学习策略四个 fixture 全未通过：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [false, false, false, false],
 "publication_ready": false}
```

冻结评估显示 learned SAC 在这些短预算、旧 32D 环境中没有建立有效接触和任务完成行为。这是失败的工程预实验，不能解释为“RL 直接动作方法不适合本项目”；它提示后续必须改为当前 48D contract、统一 reward/gate、先用 teacher replay warm-start，再做 SAC/RLPD sweep。

## 5. 当前状态与后续执行顺序

导纳 offset 已接入 WBC 参考，且修复运动学快照时序问题；r2 在三个当前 panel 条件下完成 24 s 全程实验。阻抗已改为积分 WBC twist 的移动平衡点，K300/K900 候选均保留。两者仍未成为可靠通过完整 gate 的最终 baseline，四类 primitive 的修正版全矩阵也尚未重跑。

1. 先为所有方法补齐统一的物理子步速度/实际 actuator torque 记录，并明确状态机参考下的全程与阶段误差口径。
2. 在训练/验证条件上给 impedance/admittance 固定调参预算、验收规则和模型选择规则；冻结后评估新的共同条件，不用这三条开发结果冒充独立测试。
3. 在当前 canonical 48D observation 和 7D action contract 上实现 `PPO-action7` 与 `RL-tune-VMC`；调参方法按单独控制器家族解释。
4. 用 VMC teacher bank 初始化 prior replay，实现 `SAC/RLPD-action7`；训练和 ESN 使用同一 fixture-level split、action hold、normalization 和 gates。
5. 扩大共同物理条件和独立训练 seed，最后执行冻结配置下的 office blind test。全部失败回合保留 failure reason、penetration、contact pair、force/torque 和 trace。

当前已完成的是可复现的 baseline 起点与 RL 工程链路，不是论文最终比较矩阵。
