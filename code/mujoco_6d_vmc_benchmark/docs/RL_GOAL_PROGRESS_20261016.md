# 持续Goal：四类RL训练与收敛修复

用户于2026-10-16 12:52 CST明确开启Goal，要求持续推进并自主修复训练问题。Goal active，
尚未完成；旧15小时run正常按原截止收尾，新授权以独立有限阶段继续，不回写旧协议的截止。
沿用sii-research-sync协作流程，训练与分析在airpig，服务器只归档。

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
