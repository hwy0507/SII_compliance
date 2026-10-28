# 非RL教师速度换算诊断与完整闭环对照

本轮沿用三真实特化场景、相同训练身份及原门槛，检查教师动作读出，而不是调整ESN以掩盖教师失败。
目前没有新的合格30条数据、学生训练或108主矩阵结果；旧失败全部保留。

## 最新完整结果与唯一接续（覆盖下文在途快照）

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
