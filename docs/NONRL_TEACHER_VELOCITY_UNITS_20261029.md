# 非RL教师速度换算诊断与完整闭环对照

本轮沿用三真实特化场景、相同训练身份及原门槛，检查教师动作读出，而不是调整ESN以掩盖教师失败。
目前没有新的合格30条数据、学生训练或108主矩阵结果；旧失败全部保留。

## 18:34 UTC：原恢复机制仍失败，保存状态定位物块顶边角

原恢复机制+匹配归一化的六项已完整结束，五train均合格，但office000完整55秒仍carry、
Task/Strict均false，actor/filter回放0。[完整审查](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_UNITS_COMPLETE_REVIEW.json)。
末250帧平均z误差−13.334510mm，恢复记忆0.149669；恢复原机制也没有兼顾三场景与综合回归。
此候选未推广到新30/拟合。完整733文件、608839680字节已核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_legacy_units_controls_20261029_v1/FULL_PROBE.tar`，
SHA256 `daa832c524b98a31409d454e853728443db92ab9fcdacc3275d301bfcdf48a54`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_UNITS_SHARED_RECEIPT.json)；无本地删除。

从两条完整轨迹固定抽取24/46/54秒，保存qpos/mocap重建几何、侧面与俯视渲染，0物理积分步。
实际PNG已目视检查，候选46/54秒重建到`target_object_geom`与`office_v5_unexpected_edge`接触，
分离距离−0.023102/−0.029099mm；历史54秒已retreat。并非只有误差数字，而是携带物块顶住边角。
模型hash相同，保存hand与重建hand最大差2.080微米。三帧无接触不证明整个回合无接触；
这是几何重建，不是接触力或独立动力学回放，橙/绿仅显示颜色。
[几何收据](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_EDGE_STATES_REVIEW.json)，
[真实保存状态图](evidence/NONRL_INTENT_RECOVERY_20261029/legacy_edge_states.png)。

原v6与归一化版同三训练ball配对、MJB/seed/参数/actor回放核验通过。
ball01原末窗口最大速度0.035079899→0.003880211m/s，最后10秒RMS0.016835373→0.006783650；
ball04末窗口0.028606792→0.000676317；ball00末窗口0.002991014→0.004830989有退化，仍合格。
原v6 ball00虽通过末窗口，较长尾段仍有速度峰，不能把短窗口资格等同全段稳定。
[配对数值](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_TRAIN_COMPARISON.json)，
[实际曲线](evidence/NONRL_INTENT_RECOVERY_20261029/legacy_ball_speed.png)，不含验证集或学生结果。

源码检查：两种设置的虚拟动力学近零平衡点子步Jacobian谱半径均小于1，未发现该局部积分发散。
这不能排除与机器人/估计器/接触耦合后的不稳定。匹配归一化同时降低瞬态与静态柔顺读出；
因此新有限对照恢复原v6读出/恢复/velocity1/平均，仅将平移虚拟阻尼[28,28,55]→[56,56,110]。
旋转阻尼、质量、刚度、物理/公共filter/执行器/输入/gate/dt全保持，无新手工恢复机制。
相对直接前驱同时恢复旧归一化并加阻尼；只相对原v6为单参数族变化。
8000子步独立积分状态误差0，恒定小输入稳态动作差1.8041e−16；只是实现与静态映射检查。
[算术检查](evidence/NONRL_INTENT_RECOVERY_20261029/DAMPING_ACTOR_CHECKS.json)。

唯一队列`sii-special-teacher-damping-v1-20261029.service`，parent1025522，18:30:14.835 UTC启动，
`outputs/special_teacher_damping_20261029_v1`登记SHA256
`c7efd1d4ee74650d2c2e62a0883b36b59b31d55ae783047476367eb3b22b3fec`。
CPU100%/3GiB/swap0/线程1，原队列已自然结束；同五train+已看office000，有限六项，无自动推广。
18:34 rod00、ball00合格，ball01在途。棍推接触4.73275/让位4.84/蹭过7.80/持续回位8.88秒，早于12.80撤棍。
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/DAMPING_REGISTRATION.json)。
完整后用`review_teacher_damping_control_20261029.py --root ...`，在途调用已实际拒绝且无REVIEW。
只有全部六项原资格通过才用其`--collection-output`登记新30；旧legacy reviewer的recollect文字只针对归一化，
不能用于阻尼版交接。新30全合格后再共同24+6/三seed/各12候选、真实场景闭环与108回归。
目前主矩阵尚未修复；Goal active，无RL/子agent/服务器计算。当前12为已检查回归，不能叫unseen。

本轮实际fetch/read main e6df2f8b、baseline f6e8f8c；初次fetch网络失败，后实际成功，未用缓存冒充最新。
新源码/图与在途阻尼目前仅本机/待Git发布，不在上述完整legacy物理包中。

## 前轮18:14 UTC：读出恢复完整失败，定位持续边角接触（在途状态已过时）

`full_velocity`原六项于18:09:11 UTC完整结束：五训练条件均合格，ball00/01/04末段速度
为0.000081655、0.000106471、0.000043462m/s；office000完整55秒仍carry，Task/Strict均false。
末250帧平均x误差5.218761mm、z误差−11.856263mm、恢复记忆0.735522，actor/filter回放0。
[完整六项审查](evidence/NONRL_INTENT_RECOVERY_20261029/FULL_VELOCITY_COMPLETE_REVIEW.json)。
恢复velocity_weight为1没有解决综合任务，禁止直接用此教师重采或拟合。

该完整六项732文件/610129920字节已逐成员及共享暂存/最终hash核验，保存于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_full_velocity_controls_20261029_v1/FULL_PROBE.tar`，
SHA256 `d4d4381469b3d43f1727b4c8158ca554d4750cad138eadaea98ab77eaac7b66c`。
[完整共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/FULL_VELOCITY_SHARED_RECEIPT.json)，无删除。

本轮新增了[边角接触范围审计](evidence/NONRL_INTENT_RECOVERY_20261029/EDGE_PERSISTENCE_REVIEW.json)，
核对历史成功与四个失败版本的相同MJB、实际归档evaluator/task源码、完整轨迹及原Task/Strict。
`prior_contact_peak`的五个通道仅是ball/person_hand/rod/cup/pillar，不含另记的unexpected_edge。
因此末250帧这五列为零，不能推断无边角接触或教师凭空抬升。

历史成功教师的边角接触最后时刻47.239700s，49.16s进入load_transfer、49.80s release、53.04s retreat；
而四个失败版本均有边角接触记录持续到回合末尾。以速度换算组为例，边角接触累计32.187200s、
峰值28.580736N、冲量90.404888Ns。这将问题定位到实际脱离边角的过程，不能只按末段误差
继续减小恢复偏置。事件摘要不证明整个时段连续接触，不是独立动力学积分，也不证明单一控制项因果。
接触真值仅用于离线审计，未加进actor或拟合标签。

新有限对照采用原v6教师：velocity_weight=1、平均输入、原恢复机制和原默认intent阈值.015。
**相对原v6只增加教师归一化分母[.32,.32,.32,.6,.6,.6]**；相对直接前驱则同时撤回intent平衡点
机制及.03释放阈值，明确不是相对前驱的单参数试验。v6原教师曾通过office，但完整30中有四ball失败；
本次检验已观察到的归一化改善能否在保留原恢复机制时兼顾两者，未更改物理/场景/gate/filter。
400步同历史状态/恢复记忆及独立动作算术通过；1375帧根源码与冻结副本actor输出字节hash均为
`2e4a19a3d1c3915c6522c61884fd91c72fce276215a0dce026d0ad44e46799a8`。

唯一新队列`sii-special-teacher-legacy-units-v1-20261029.service`，parent1016229，18:12:54 UTC开始，
`outputs/special_teacher_legacy_units_20261029_v1`，登记SHA256
`bf56be8626c04de939d8a7a4a1bbf8025fa98bc9593135b323926c1155a2c464`。
仍为原五train+office000，实际单模拟器/单线程/CPU100%/3GiB/swap0。
源副本原文件保持，仅增加完整记录wrapper来源的legacy driver；原intent reviewer保留，另建
`review_legacy_units_controls_20261029.py`，完成后须用它审查此root，全六项通过才登记新30。
[新登记](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_UNITS_REGISTRATION.json)，
[算术检查](evidence/NONRL_INTENT_RECOVERY_20261029/LEGACY_UNITS_ACTOR_CHECKS.json)。
当前未新采30/拟合/108，Goal active；在途结果仅本机，不能称主矩阵修复。

已发布源码d19365115e57f3a14941b5fba338ed657d94ea78的benchmark scripts/tools及选定小证据1096文件
已逐Git blob/大小/可执行位核验，共3048351字节，SHA256
`fb556e5cf498de657eb64e88aa061aa260dfeba072514d762d88e46c7b7b3577`，共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_velocity_units_source_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`。
[收据](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_SOURCE_SHARED_RECEIPT.json)；不是全仓库/物理/模型备份，
不含本节稍后新增的边角审计与legacy准备。full_velocity完整物理归档状态另记，未删除本地。

## 前一轮：速度换算完整结果与读出恢复接续（在途描述已过时）

速度换算组已于17:52:51 UTC完整结束，五训练条件全合格，office000完整55秒仍carry、
Task/Strict均false；因此不允许使用本候选重采新30或拟合。
[全部六项审查](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_UNITS_COMPLETE_REVIEW.json)。

| 原训练身份 | 原末段最大速度 m/s | 换算修正后 m/s | 原资格→新资格 |
|---|---:|---:|---|
| ball00 | 0.000077932 | 0.000171074 | 合格→合格 |
| ball01 | 0.025616929 | 0.000245490 | 失败→合格 |
| ball04 | 0.000126547 | 0.000028759 | 合格→合格 |

ball01最后10秒速度RMS从0.011372676降到0.000447444m/s；没有把ball00的小幅退化隐藏。
相同seed、场景参数、MJB及完整actor回放已核验，图来自真实物理轨迹，已目视检查。
[逐项对照](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_UNITS_COMPARISON.json)，
[实际曲线](evidence/NONRL_INTENT_RECOVERY_20261029/paired_ball_speed.png)。

office最后250帧位置门通过比例为0、姿态为1、速度为0.996。平均x误差7.064211mm、
z误差−12.223260mm；基础z请求均值仅0.000052513，恢复激活均值0.605499，
公共滤波后的z让位速度均值0.014887602m/s。末段恢复项持续向上，不能用球撞改善代替综合修复。
这些边缘统计不替代完整carry或最终Task/Strict gate，也不构成该项独立致败的证明。
初次绘图检查误把累计浮点时间步容差设为1e−12而拒绝（最大偏差1.328e−12），
已将纯时间算术检查改为2e−11，远小于一个物理子步；无资格门变化、无物理重跑。

完整732文件、608860160字节已本机逐成员及共享暂存/最终哈希核验：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_velocity_units_controls_20261029_v1/FULL_PROBE.tar`，
SHA256 `ceeb6262b94d866459487998f008ba8d8341bdf368f917144e5213330a80c8bf`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_UNITS_SHARED_RECEIPT.json)。

原历史同条件对照中velocity_weight=1可以完成office，而.75不能。本次仅恢复该读出权重为1，
保留换算尺度、平均输入、平衡点机制、intent=.03、原release及全部其他条件。
400步同历史内部动力学/记忆精确一致，非恢复通道独立读出算术误差0；不是物理成功证明。
唯一新队列`sii-special-teacher-full-velocity-v1-20261029.service`，parent1007482，
17:56:42 UTC开始，`outputs/special_teacher_full_velocity_20261029_v1`，登记SHA256
`8579e7b7e055af45bf1f09b2babf5efef1e312a5dbfa38444e7d3ca5c1e35435`。
实际CPUQuota100%、MemoryMax3221225472、swap0、线程1；原队列已自然结束，无重复模拟器。
[新登记](evidence/NONRL_INTENT_RECOVERY_20261029/FULL_VELOCITY_REGISTRATION.json)，
[实现检查](evidence/NONRL_INTENT_RECOVERY_20261029/FULL_VELOCITY_ACTOR_CHECKS.json)。
新队列仍为五train+office000六项有限对照，不自动搜索/收集/拟合；新产物仅本机、待完整归档。
完成后使用`review_intent_recovery_controls_20261029.py --root outputs/special_teacher_full_velocity_20261029_v1`。
所有六项通过后才另登记新30，不可使用失败v6的旧18/108准备。Goal active。

## 已完成的前置诊断

上一组`intent_velocity_mps=.03`六回合已经完整结束：五个训练条件4个合格，
ball01末段速度为0.025616929m/s，超过原0.02m/s门；office000完整55秒仍停在carry，
Task和Strict均失败。末250帧平均位置误差x=7.163877mm、z=−10.636212mm，
恢复记忆均值0.801116。actor/filter精确回放通过，但不改变失败结论。

完整732文件、614789120字节已核验并共享至：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_intent030_controls_20261029_v1/FULL_PROBE.tar`。
SHA256 `c7626aa3a5a06a3e654b0af5b3ba2c01adc7ee5abe9c0c139512fdec5bea4841`；
[完整审查](evidence/NONRL_INTENT_RECOVERY_20261029/INTENT030_COMPLETE_REVIEW.json)，
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/INTENT030_SHARED_RECEIPT.json)。

随后逐一复核三个版本×ball00/01/04共9条真实训练轨迹，所有actor回放误差为0。
失败的intent030 ball01末段恢复项很小，持续动作波动主要来自基础VMC读出；
仅继续调低抬升偏置不能解释或解决所有现象。频谱并不支持宣称存在已确认的单一窄带振荡。
这些都是保存轨迹的描述性诊断，不是新的物理仿真或因果稳定性证明。

[九轨迹诊断](evidence/NONRL_INTENT_RECOVERY_20261029/FEEDBACK_DIAGNOSIS.json)，
[实际曲线](evidence/NONRL_INTENT_RECOVERY_20261029/actual_ball01_feedback.png)。
图中红线是最后原资格窗口的阈值，不是整段20–30秒的成功判据。

## 单项修正与实验边界

教师内部默认归一化分母为`[.16,.16,.20,.6,.6,.6]`，公共动作速度尺度为
`[.32,.32,.32,.6,.6,.6]`，因此无饱和时，相对虚拟速度读出的线性分量增益是2、2、1.6。
这可能包含历史调参意图，不能仅凭数值不同就宣称已确认单位实现错误。

新对照只将教师`options.action_limit_6d`设为公共尺度，使这一步换算增益一致。
该字段在这里是教师读出的归一化分母，并非机器人执行器限制、虚拟速度饱和限制或公共filter。
归一化动作大小变化也可能改变派生slowdown，不能把它描述成对闭环完全中性的单位重写。
保持`.75/平均`、平衡点恢复机制、intent=.03、release、其他参数、场景、seed和原gate。
不改MJB/物理、canonical48、公共filter、执行器限制及dt=5e-5。

400步同历史合成检查中，内部虚拟动力学状态和恢复记忆逐值保持；400个低幅无饱和样本中，
公共尺度×请求动作与虚拟速度读出的最大换算误差1.3877787807814457e−17。
这只是算术与实现检查，不代表真实末端速度精确跟踪，也不证明物理成功。
[检查](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_UNITS_ACTOR_CHECKS.json)，
[登记](evidence/NONRL_INTENT_RECOVERY_20261029/VELOCITY_UNITS_REGISTRATION.json)。

## 执行与后续

本机缓存`code/mujoco_6d_vmc_benchmark/outputs/special_teacher_velocity_units_20261029_v1`，
登记SHA256 `8d6abdee50b29f5f7f007a1898bbbed9e8bf91924e781af69f31a943287e72dc`。
用户级服务`sii-special-teacher-velocity-units-v1-20261029.service`，parent998653，
2026-10-28 17:40:12 UTC开始；一个模拟器、数值线程1、CPUQuota100%、3GiB、swap0。
同五个训练身份及已检查过的office000共六项，全部原gate通过才允许另登记新30。
服务active时审查器实际拒绝提前审查，没有产生完整REVIEW或错误推广。

17:48 UTC快照：五个训练身份已合格，office000仍在途；此快照不替代完整结果。
在途源不得热改或重复启动。该实验只在本机计算，服务器只存档。

新棍推完整20秒原审计通过：4.734s末端实际接触，4.84s开始让位，7.84s蹭过，
10.20s确认持续回位，早于12.80s撤棍。最大让位17.488mm，原5mm回位管与0.08s保持不改。
这是具体训练条件上的行为资格，不替代综合Task/Strict或其他九个棍推条件。

后续须新30全部资格通过，再共同24train/6val、每方法每seed12候选、三seed重训
ESN解析ridge/普通RNN/MLP；继而真实特化场景学生闭环与当前12×9回归比较。
仍报告Task、Strict、双成功条件SPT、平均回合峰矩、实际接触舒适代理、机器合规率。
office000以及当前12已被反复检查，只能称回归，不能称未见测试；office动作不入拟合。
若教师通过而学生退化，再由同观测动作重放及闭环分布覆盖分离学习误差与场景覆盖。
不放宽门、不改失败、不承诺ESN必然优于其他方法。Goal active。

本轮实际fetch/read远端main从60db98f9前进至ea21d0b2，baseline为f6e8f8c。
新增独立RL日志已读并fast-forward保留，无RL操作或子agent。

收尾远端新增482ff64f独立RL审查准备已读；与科学提交08fcce99的AGENTS/UPDATE_LOG顶部
新增冲突按双方原内容全部保留处理，未改任何已绑定仿真源。新full_velocity首rod已合格，
进入ball00，其余尚未完成；后续状态必须读取实际execution，不能把首条通过当作全部通过。
