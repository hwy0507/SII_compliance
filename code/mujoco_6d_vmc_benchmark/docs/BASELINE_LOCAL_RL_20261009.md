# RL baseline本地补强（2026-10-09）

用户最新要求：充分使用本机，服务器另有用途，禁止占用服务器计算。

## 两组同八条件完整开发对照（14:10 CST）

两模型均完成11000交互/12002梯度更新，再用同一八个development身份确定性评估。
16回合全部55秒，正式物理步长`5e-5`；仍是开发集诊断，不是封存final或充分训练结果。
`monitor_v2/development_003.json`独立复算物理子步，并检查条件、checkpoint和动作链，全部通过。

|配置|Task|Strict|平均RMSE mm|平均回合峰矩 Nm|平均回合峰速 m/s|最坏外穿透 mm|最终阶段|
|---|---:|---:|---:|---:|---:|---:|---|
|直接office_task，11k|0/8|0/8|205.018|41.929|0.34735|0.17379|approach，8/8|
|RL调阻抗，11k|0/8|0/8|23.327|36.510|0.37383|0.18170|carry，8/8|

平均最终放置XY误差分别192.094mm、86.214mm。失败阶段不同，不能用较低RMSE或峰矩
宣称后者柔顺性更优。八阻抗开发回合都在意外桌沿接触43.911–44.951秒；
`IMPEDANCE_STALL_ALL8_1412.json`扩展到八训练＋八开发，保留全部失败。
14:16状态：调导纳6500交互/3002更新、调VMC1250交互/尚在预热；
剩余直接metric和两个历史熵对照未启动。两lane和只读观察器稳定，当前无新增基础设施失败。

14:23 CST归档补齐：八条调阻抗开发原始轨迹、完整成对审计和全16条停滞诊断已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage4/evidence/`，
292文件、1198991995字节，清单SHA
`168f920b8509531b43e29fee6a589630dc1267a895cb84fafb3e1a02961a022b`。
stage3保存direct八开发，stage4保存阻抗八开发；训练/checkpoint在stage2，继承smoke与
冻结基础依赖源在stage1，不将任一增量包称为全部实验。分析在airpig执行，服务器仅校验文件。

## 首个完整开发组与奖励信号（13:59 CST）

direct office_task八个开发条件全部55秒完成，Task/Strict **0/8、0/8**，
自动独立子步/动作/身份/checkpoint审计通过，全部停approach。调阻抗仍在完成最后两个开发回合；
原队列已将空闲lane分配给调导纳，当前2个预热回合完成、尚未开始梯度学习，均卡carry。
只读`monitor_v2`与有限v3调度器继续运行，无新增执行故障，不把未结束配置算作0/8。

新增`inspect_local_rl_progress_20261009.py --objective-audit`重建已完成训练的原始折扣回报，
复用既有势函数逐项审计，并与实际未折扣日志return逐项核对：

- 直接组含继承smoke共8回合，两个Task通过/Strict失败，全部终局task奖励均为−20。
  这8条的原始折扣回报都约−11.4082118316；接续7条标准差仅3.08e−15。
  原因是同样完整55秒、未通过联合Strict终局、势函数最终抵消为同初值常数；
  已经放好物块但安全/接触不通过，与没抓取成功，在该批原始完整回报中没有区分。
- 这不是奖励重建错误：实际代码与已登记的Task AND Strict终奖语义一致。
  势函数仍能帮助TD学习，尚未采到的Strict成功轨迹也会获得不同回报；
  不能据此证明所有策略等价、RL必然失败或所有差异都是此项所致。
  这里是**未缩放的环境回报**，不是包含熵项及在线归一化的soft价值目标。
- 调阻抗metric八回合原始折扣回报标准差0.5455，仍能区分部分跟踪/力矩成本，
  但Task/Strict均失败且没有正终奖。低误差和静止的持续接触也不等于完成任务。
- 下一轮应在本轮固定两熵/两奖励对照审查后，单独登记“任务进展与安全成本分解”的奖励消融；
  保留现有原奖励结果，冻结Task/Strict评估、环境与执行器约束，不能将新奖励模型冒称旧模型精确接续。
  当前只是诊断方向，尚未实施该奖励变体，未改变任何正在运行的奖励或权重。

完整direct八条件与分析源码已归档并核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage3/evidence/`：
210文件、1040156441字节，清单SHA
`70afb7ed548d2b888702f00035f7535770e5a641b2532be302fce6de5ad3ca23`。
其中`development_002.json`是当时direct8/阻抗4的审计快照，只有direct8的原始开发轨迹在此包；
阻抗开发原始轨迹待全组完成后独立归档。当前新结果不替代旧final24比较，不支持最终方法排名。
上一发布`6caa74831135bccb8961b524c145646c291f638c`的相关源码/文档/小证据包（不是完整依赖包）
亦已核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage2/review_6caa748.tar.gz`，
354665字节，SHA `4a748dc9875cb7f9e6b5cbdf2c070ad4d07cc900cf116b662bcc40606ca2a2a8`。

## 本轮运行中的早期记录

13:21 CST接续状态：直接office_task与调阻抗都已完成11000交互/12002更新，
调阻抗全部八回合参数重放及完整物理奖励重建通过。13:16独立v3协调器在核对
旧服务退出、8.88GiB可用内存、冻结源/参数/hash后启动，复用两checkpoint和已完成dev000。
当前真实状态为`parallel_v2.execution.json`；原`parallel.execution.json`的失败保留，
不要据其旧状态再次启动训练。直接组已完成2/8开发，调阻抗第1/8进行中，均尚无成功。
两路稳定，各3GiB/禁swap。一次性`monitor_v1`观察进程只记录进度/审计已完成配置，
不启动、重启或停止任何实验，不是定时任务；全部7×8完成才输出最终开发审计。

13:30 CST：直接4/8、调阻抗2/8开发完整，Task/Strict均0；六回合独立原始子步/动作/
条件身份/checkpoint复算通过。调阻抗dev000为RMSE23.289mm、峰矩37.059Nm、
峰速0.37024m/s、穿透0.14870mm，但放置XY仍差86.415mm，停carry；低RMSE不能代替任务完成。
调阻抗价值诊断亦显示终止价值拟合未充分（terminal Q残差均值0.6451、最大4.7538），
没有梯度或统计更新，不能把与历史策略回报差值直接当作价值高估。
只读观察器升级到`monitor_source_v2`/`monitor_v2`：旧仿真进度旁路文件采用原地写入，
新观察器容忍写入瞬间的空/半JSON，并将参数审计收据与物理回合分开。
v1由主动SIGINT正常退出到保留失败记录，v2记录父收据hash；两路实验与v3协调器未重启。

13:36 CST第二阶段归档完成并逐文件核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage2/evidence/`，
717文件、2736212640字节，清单SHA256
`65e69ae7f36b1f063913b0996258f90bbbd03857c06d578174a2a31b7266a632`。
包括两组完整11k段/checkpoint/原始训练轨迹、两组奖励审计、保留的开发资源失败、
同checkpoint首开发重跑、冻结接续v2/v3源码和早期价值诊断。继承的1375步smoke和
完整仿真/参数源码仍在stage1核验包，两阶段共同构成训练谱系；真实执行路径未改写。
其余新增开发轨迹及13:30之后分析尚在本机，后续另行归档，不声称包含在stage2快照中。

进一步从八训练＋两开发完整轨迹定位阻抗停滞：意外桌沿接触各持续44.21–44.81秒。
两个开发回合最后10秒，位置弹簧参考误差始终达到原4cm边界，实际末端RMS速度仅
0.130/0.143mm/s；等效关节命令未再被速度/加速度限制改变，力矩feasible scale均1，
全回合参数energy scale最小值也均1。因而这些回合没有“学习动作被能量罐全部挡掉”的证据，
更符合持续接触平衡而未脱困；这只是保存轨迹上的机理线索，不能证明阻抗无解，
也未据此放宽参考/执行器约束或给actor接触真值。详见`IMPEDANCE_STALL_1335.json`。

## 持续监看：开发入口恢复与学习诊断（13:12 CST）

本轮重新核对main `c745da382a45ed7d8ef59f6915cc3464ef2a8ea2`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，分支无新改动；不使用服务器计算。
以下是本轮中间检查，不覆盖下面的首轮登记和历史记录。

- **已完成**：direct office_task累计11000交互、12002梯度更新，包含继承的1375步smoke。
  全部原始回合和完整checkpoint保留，奖励/观测/原始动作/伺服时钟独立重建通过。
  随机预热最初两回合Task通过但Strict失败；完全进入学习后的四回合均停在approach，
  不能把预热通过当成学习提升。
- **修复基础设施**：12:54首个开发评估在物理执行前因未传`MUJOCO_MENAGERIE_PATH`失败。
  原receipt/log/目录保留；补充本地环境变量，在独立`_assets_retry_v2`目录使用同一模型/
  checkpoint/条件重跑，未重训。初版重试占用检查曾把自己的unit当成其他lane，亦在
  物理开始前拒绝；独立v3排除本unit，保留v2源。新调度器只允许这一已核验的资源错误重试，
  不允许因物理任务失败自动重跑挑结果；已完成训练收据经hash复核后复用。
- **首个开发结果**：55秒完整，Task/Strict均false，停approach；RMSE220.594391mm，
  峰矩41.923222Nm、峰速0.343847m/s、外穿透0.142227mm、放置XY误差192.094mm。
  原始actor重放和公共filter误差0，归一化未更新，模型hash与登记完全相同。
  独立重新积分110万物理子步及核对请求动作链通过。只有1/8，不能作成对方法排名。
- **运行中**：调阻抗原作业稳定保留，已经完成7个回合，正结束最后一个11k诊断回合；
  仍卡carry。旧协调器会在该训练段结束后退出，再由独立接续入口复用已完成checkpoint、
  完成两组八条件开发检查和后续五配置，科学协议/预算不变。
- **学习诊断**：固定263条均匀抽样＋全部终止转换，直接组terminal Q减归一化真实terminal
  reward的均值0.6387、最大4.5578，价值拟合仍不充分。当前soft Bellman目标平均14.4113%
  概率质量落在上界外，同样样本仅移除熵项则0.1686%；但单步裁剪损失的期望只有0.00184，
  不能仅凭边界概率就断言严重偏差。固定当前均值熵/温度贯穿整回合的敏感度计算约14.90，
  并非实测回报，也不是失败因果证明。保留登记的低熵对照，暂不变更算法/奖励。
  Q与历史behavior return之差含策略差异和熵项，不能称为纯高估。诊断不更新权重/统计；
  尝试CPU恢复GPU分片checkpoint失败后，在原本地GPU上只读恢复成功，checkpoint hash不变。
- **未完成**：全部7×8开发矩阵、低熵因果对照、足够训练/多seed、经典补强和新最终对比。
  11k仍仅诊断，不宣称baseline已经充分调好，也不据此抬高ESN结论。

新工具为`inspect_local_rl_progress_20261009.py`（区分随机/混合/学习回合）、
`audit_local_rl_development_20261009.py`（完整开发收据、原始子步和动作核验）、
`inspect_repair_critic_20261009.py`（只读价值/支持区间诊断）。
当前新证据位于本地`campaign_v2/`：`direct_011k_reward_audit/`、
`DIRECT_011K_CRITIC.json`、`DIRECT_011K_PROJECTION.json`、`DEVELOPMENT_AUDIT_1308.json`；
本轮新增大产物尚未归档，不属于下方stage1服务器包。

## 首轮登记与历史记录

本轮不是恢复旧Spark队列，也不覆盖已完成15小时比较。开工核对main
`694a94d6907d6624e615b9a9cccfe2242502bd2e`与baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取日志；无分支合并。

## 已确认与修复

- 本机airpig：Core Ultra 9 275HX、约15GiB RAM、RTX 5080 Laptop 16GiB；
  GPU驱动580.178.04可用。新建独立`.venv-sii-local-rl`，不改系统驱动/显示。
- 历史MuJoCo 3.11.0二进制在本地转换到原正式dt=5e-5后，SHA仍为
  `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`。
  原几何、规划器、任务/Strict gate、48维输入和执行器限制不变。
- 新本地运行入口采用显式`SII_LOCAL_RUNTIME`，修正硬编码Spark路径和CUDA库搜索路径；
  未设置变量的历史入口保持不变。官方SimbaV2固定commit
  `86899c277cdc697b2b02d827243de1ea93f20a1d`；适配器仅替换源码目录路径，保存前后hash。
- 参数动作采用已登记full-range映射：旧中心乘0.5–2不能覆盖全合法区间；
  新映射保持零动作对应中心，并覆盖上下界。原变化率/能量罐约束不变。
- 独立参数轨迹审计兼容新映射的字符串版本标签：标签精确比较，数值字段仍逐项重放；
  补齐适配器源码hash。不会把版本标签强行转数值，也不会跳过数值审计。

## 有限开发计划

`tools/local_rl_campaign_20261009.py`登记、预检、1375步真实物理smoke、断点接续、
每项最多11000交互及八个development条件检查。五族全部覆盖：RL调VMC/导纳/阻抗、
直接metric/office_task；另为直接office_task与调阻抗登记历史低熵对照，共七配置、
同seed2026100911，最多77000个新训练交互。学习率按500000总步计划，
11000只是诊断段，不是收敛预算；到段尾审查后才决定50k/100k/250k/500k延长和三seed复核。

参数三族保持metric reward，直接两族各用原登记reward；没有把调阻抗悄然改成task reward。
所有配置从零开始，无teacher/BC；短smoke的完整checkpoint接续到相同配置，不重置计数，
也不把随机预热成功当学习成功。新旧低熵对照共用此次完整参数范围，因此这组对照检验探索强度，
不单独识别旧映射与新映射的因果效应。

训练仅用原32训练身份，诊断仅用原8开发身份。旧final24已公开，不再作为新留出结果；
本入口不复制、不读取封存final，也没有自动最终评估分支。开发检查全用原55秒和正式物理步长，
这仍是开发数据，不因dt较细就变成未见场景泛化结论。

初次smoke使用一个本机模拟器与GPU学习器，数值线程1，整组进程MemoryMax=3GiB/禁swap。
完成smoke后由`local_rl_parallel_20261009.py`登记资源补充协议，改为两个本机lane，
每lane最多一个模拟器、3GiB、禁swap，最大合计6GiB；启动要求本机可用内存至少7GiB。
每lane串行训练及其八条件开发检查，跨配置并行；已有进程检查和锁防重复，不按GPU占用率认定进展。
48小时是agent设置的此次有限队列失效保护，不是用户给定时长，也不是训练充分性的标准。
没有定时任务。失败/中断目录保留，已有完整收据核hash后可跳过，失败必须用新attempt。

## 当前状态与位置

GPU梯度/归一化/checkpoint两种动作维度预检、完整参数范围数值测试、正式模型hash核验均通过。
12:20 CST首个1375步/55秒真实物理smoke完整结束，用时5分30秒；Task=true、Strict=false，
RMSE 28.4595mm、峰矩49.0145Nm、峰速0.364766m/s，外穿透0.273794mm，最差接触为柱子—link6。
放置XY误差11.8742mm。动作/共同filter一致性误差0；独立子步奖励重建误差0，replay观测/原始动作一致。
这是AR(1)随机预热、梯度更新0，不能当成训练后RL提升或成功率；失败保留。
checkpoint包含1375条replay、优化器/归一化/RNG/条件顺序和hash。

12:21 CST两路本地长进程已启动：直接office_task从smoke checkpoint接续，调阻抗metric从零开始；
随后依照登记队列跑其余五配置及各八开发条件。两学习器GPU各约584MiB，
初始可用RAM约8.84GiB；每lane独立3GiB/禁swap/两个CPU亲和核，数值线程1。
资源补充SHA `267d16b273044cdc64349f15afa21f30f747111807e21dcef9419399296424ad`。
`parallel.execution.json`是当前队列状态；旧`execution.json`仅是已经完成的smoke阶段状态。
随后两路各再完成一个完整回合：直接动作接续回合Task=true/Strict=false（穿透0.342624mm），
调阻抗首回合Task=false/Strict=false（停在carry，穿透0.176869mm、放置XY误差87.338mm）。
都仍处于5000步随机预热；不把不同训练身份的单回合指标当方法排名。
调阻抗1375次参数重放及13750行伺服记录独立审计通过：能量/参数更新数值误差0，
最大等效关节速度命令0.702001rad/s、加速度8.0rad/s²、力矩变化率比约1.0，未放宽限制。
该追加审计小文件入Git；对应新原始回合仍在本地训练目录，未包含在下面较早的stage1大包。
初版`campaign_v1`仅登记，未派发物理回合；补齐参数轨迹审计后建立`campaign_v2`。

实际本地工作根：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/`。
其中`runtime/history/source_v9`和`parameter_v2`来自历史只读下载；
`campaign_v2/source`为本轮冻结执行源，`parameter_fullrange`为本轮适配器，
PROTOCOL/SOURCE_HASHES/PARAMETER_HASHES/RUNTIME_HASHES记录实际路径与内容。
协议SHA `ef3ec8c85bd06ccb2a915d861116286e29b78a13ec1df4da02f0c0a5825bd2bb`。

服务器旧数据来源（仅文件读取/传输）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`。
本轮已完成证据已归档并核对大小/hash：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_local_rl_20261009_stage1/stage1_verified_snapshot.tar.gz`，
190281186字节，SHA256 `ffdad404d6713fceda5e9824b2969b160379f1adecfc3a6dfb3af8b43bdeec12`。
包内包含`source/`、`parameter_fullrange/`、`continuation_source_v1/`、完整首回合/其checkpoint、
GPU预检和物理奖励审计、配置及全部输入hash。实际执行仍在airpig；服务器仅存文件。
它是已完成阶段快照，不包含正在变化的两路训练目录；后续产物待完成边界另行归档。
可直接审阅的小型证据位于Git的`outputs/baseline_local_rl_20261009/evidence_stage1/`。

未完成：本轮真实梯度后的闭环诊断、合理训练充分性证据、多seed、开发选模、新留出统一比较。
旧经典/RL零成功结论不因迁移/数值测试通过而改写，也不能据此声明ESN全面领先。
