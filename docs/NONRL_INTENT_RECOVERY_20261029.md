# 非RL teacher恢复项修复：独立版本与有限物理验证

当前状态：整项混合版及仅平衡点版各六条对照均完整结束并审查，**尚未整体修复**。
目前唯一活动队列是原平衡点机制的单字段`intent_velocity_mps .015→.03`六项对照。
这不是新的主矩阵结果，也不是 ESN 已修复的结论。此前所有失败、v5学生和v6采集保留。

最新中间结果：intent030的rod00/ball00合格、ball01失败，其余仍在途。
本候选已经不能用于新30或拟合，即使后续office通过也不改变这一点。
收完登记六项，分析完整末段波动/阻尼与动作速度换算，不继续只按某个回合通过调小偏置。
最新在途收据须直接读取原execution，不以本页早期快照代替。

## 17:25 UTC：第二版完整结果，单字段后续在途（覆盖下文在途描述）

仅平衡点版五训练身份4/5合格：rod00、ball00、ball01、corner00；ball04仍失败。
三个ball末段速度依次0.000271556、0.002132642、0.028225448m/s，原门0.02未变。
office000完整55秒仍Task/Strict=false、carry；末250帧平均z误差−11.7927mm，
但同时有x误差4.9484mm，不能拿单轴低于12mm替代三维位置门及持续保持。
恢复记忆均值0.736907、z动作0.0744767，actor/filter回放0；完整物理及源归档核验通过。
[全部六项审查](evidence/NONRL_INTENT_RECOVERY_20261029/EQUILIBRIUM_COMPLETE_REVIEW.json)。

第二版完整物理/源码/收据732成员、615536640字节逐成员及远端暂存/最终大小hash核验通过，
共享`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_equilibrium_controls_20261029_v1/FULL_PROBE.tar`，
SHA256 `4e4a6af34cb9f27b2d2aff9b311063f3ca10b0567c75774d24bacf0b8bd6aea8`。
[收据](evidence/NONRL_INTENT_RECOVERY_20261029/EQUILIBRIUM_SHARED_RECEIPT.json)，不含intent030在途数据，无删除。

保存的末250帧沿路径指令中位数0.0079963m/s、范围0.0060369–0.0106051；
原0.015归一化下平均intent仍0.5358745。当前只将这个已有参数改为0.03m/s，
使相同历史的小指令偏置因子减半；它也同时改变既有记忆释放项，这一点明确保留，
不能把它描述为仅改读出。其他参数、物理、gate、filter、actor输入、场景和seed不变。
200步高指令对照下原/新动作及记忆精确一致，复制的冻结office源码逐文件相同；
这不是新的物理成功或全局稳定保证。

新本机缓存`outputs/special_equilibrium_intent030_20261029_v1`，登记SHA256
`9d9f0904b64630e7d30a7f8d270cebf3a861b6bfd28ef358f6f4f32f88951355`；
`sii-special-equilibrium-intent030-v1-20261029.service`，parent991347，
17:25:58 UTC真实开始，3GiB/单线程/单模拟器/CPUQuota100%/swap0。
原两个服务已自然结束，勿重启。新队列仍为原五train+office000，完整前不重采/拟合。
完成后使用同审查器及该新root审六项；全部通过才登记新30，否则保留失败继续检查。
旧v6的18/108准备不可使用，Goal active。

## 第一版完整结果与第二版实际接续

第一版五训练身份3合格：rod00、ball04、corner00；ball00/01末段速度分别
0.0259775494/0.0297396678m/s，超过原0.02门，ball04为0.000452481m/s。
原office000完整55秒仍Task/Strict=false、carry；末250帧竖直误差均值−15.0039mm、
恢复记忆均值0.7532029、z动作均值0.0907057。原actor/filter回放误差0。
这再次否定同历史反事实输出减小等于物理修复。完整审查
[BLEND_COMPLETE_REVIEW.json](evidence/NONRL_INTENT_RECOVERY_20261029/BLEND_COMPLETE_REVIEW.json)。

新候选保留原恢复混合系数，而只将平衡点中的额外抬升距离乘以intent：
`correction=clip(gain*(offset_m*intent+pose_error_z)-command_z, ±velocity_mps)`。
其目的在于接近目标时消除抬升偏置，同时保留原来的位置和指令速度反馈；
此前整项混合系数衰减会连同这部分反馈一起削弱。该机制解释仍待完整物理验证，不能写成已证实因果。

2700步覆盖3速度权重×3水平分量×3指令幅度×100步：动力学/滤波状态/记忆、非z动作保持，
反馈加偏置的独立算术、完整意图/竖直路径精确一致、reset/有限幅值均通过。
完整1375帧新actor在现场和新冻结副本中的输出字节hash相同。
新actor、driver均独立文件；原六项源码由各回合source归档保留，未覆盖失败。

新登记SHA256 `6297d8afe7a90ca0942e8d65651a0266c67d646e9e73f330df39c805285e468d`，
本机`outputs/special_intent_equilibrium_20261029_v1`；
`sii-special-intent-equilibrium-v1-20261029.service`，parent984041，
17:11:28 UTC真实开始，3GiB/单线程/单模拟器/swap0/CPUQuota100%。
相同五训练身份+原office000，不调验证08/09、不拟合、不启动新30。
只有原六项均通过才另登记新30；不能复用失败v6或此前未执行的18/108准备。
当前12条件仍是已看过的回归条件，不是unseen。

第一版六项完整物理/源码/收据共732成员、612792320字节，逐成员大小/hash及远端暂存/最终核验通过：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_intent_blend_controls_20261029_v1/FULL_PROBE.tar`，
SHA256 `88018036982fd13a0689ea4bd49a32c79cd977f9760b1a4785721ee94a4b841f`。
[共享收据](evidence/NONRL_INTENT_RECOVERY_20261029/BLEND_SHARED_RECEIPT.json)。不含第二版在途数据或学生拟合；未删除本地。

下一步直接检查此唯一活动服务及execution，完成后运行
`tools/review_intent_recovery_controls_20261029.py --root outputs/special_intent_equilibrium_20261029_v1`。
通过后才使用该审查器的`--collection-output`登记新30；失败则保留全部回合并继续定位，
不要改正在运行的登记source、重复启动、直接训练或宣称主矩阵已修复。Goal active。

## 为什么继续修teacher

原同条件对照已证明新teacher本身在office000失败，而历史teacher可以完成。
旧数据还存在桌角0.16、其他场景/评测0.32m/s的动作尺度不一致，已在采集接口与数据准入修复。
因此不能把退化统一解释为ESN容量不足或训练步数少。

`.75/平均`读出在五个固定训练身份通过，但综合场景末段仍停在carry：
最后250帧竖直误差均值−15.8226mm，恢复记忆均值0.4222785。
完整物理对照已否定单纯缩短release时间足以修复：`.25s`仍失败，`.05s`还导致ball04失败。
本轮不继续减小这个参数。

## 新机制与边界

新版本保留`.75/平均`、原release_s=1.257675717389726、完整虚拟动力学与恢复记忆更新。
只把恢复读出的混合系数再乘以原有canonical48中的水平路径运动意图：

`intent=clip(dot(command_xy,path_unit_xy)/0.015,0,1)*horizontal²`

`activation=recovery_memory*horizontal²*intent`

运动意图充分时精确保持旧输出；运动意图为零时恢复普通虚拟动力学读出。
没有增加stage、时钟、障碍位置、接触身份或任务gate输入；不改冻结物理、MJB、公共filter、
执行器限制与dt=5e-5。这是主动teacher修复候选，不声称被动性或闭环稳定性证明。

旧actor保留。新机制由显式config版本选择，未知版本拒绝；三个真实场景与office使用同一新actor。
office执行器是原冻结source的完整副本，只增加新actor和入口两文件；原文件逐hash一致。
两新增文件会进入实际worker的source_overlay并接受原回放审计。

## 已实际验证

- 3种速度读出权重×4种意图情形×100步，共1200步合成对照：动力学状态、记忆和非z动作保持；
  完整意图/竖直路径输出逐值相同，零/部分意图满足独立标量混合复算，reset及有限幅值通过。
- 旧office完整1375帧回放误差0；新actor在根源码与冻结复制源码中的完整输出字节hash一致。
- 同历史反事实末250帧z动作均值0.0841568→0.0425754，仅离线读出，**不是物理改善证据**。
- 六个修改模块AST、git whitespace检查通过。首次准备被sandbox拒绝systemd查询，提升权限后
  测试代码读取可选intent阈值时出现KeyError；改用actor既有默认值后通过。两次均在登记/物理前，
  没有改实验结果或重跑物理。

## 有限物理登记

本机缓存：`code/mujoco_6d_vmc_benchmark/outputs/special_intent_recovery_20261029_v1`。
登记SHA256：`ecbffa20a2e5d3b73c1bc5a0394890fc2df90e2e70bf17f6027fb56248af4d84`。
服务：`sii-special-intent-recovery-v1-20261029.service`，parent976221；
2026-10-28 16:56:00 UTC实际开始，单模拟器/数值线程1/CPUQuota100%/3GiB/swap0。

固定顺序为rod00、ball00/01/04、corner00五个训练身份，随后原office000回归。
保持原seed/场景参数/MJB和资格判据，不用验证08/09调参、不拟合测试动作。
office000及当前12条件已被反复检查，后续只能称回归比较，不能称未见测试。

首条rod00完整20秒并通过原接触/让位/穿越/持续回位审计：4.7542s接触，4.84s开始让位，
7.72s蹭过，7.88s确认回位，均早于12.80s撤棍；仍需其他五项完整结果。

全部六项通过才独立登记新30采集。新30全部资格审查后，才以共同24+6划分、同候选预算、
同验证规则和三seed重训ESN ridge/RNN/MLP；随后真实场景学生闭环检查、完整108及六指标审计。
若teacher通过而学生失败，进一步分离模仿误差与闭环覆盖；不会用低训练loss替代真实行为。
目前无新拟合/新主矩阵。Goal active；最新单字段队列在途产物仅本机，完整物理归档须在结束后核验。

开工实际fetch/read main `a998343cad916c1758cf33151fa3c330dfe267c8`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
独立RL更新保留，无RL操作、服务器计算或子agent。
收尾远端main新增`d4e8d136`（独立RL66）已读并fast-forward保留，冻结非RL源无变化。

第一版修复提交`b77fd976470f0caf2fc9227884460f8327d1667f`已正常push并实际ls-remote核验。
该commit的benchmark scripts/tools及选定报告/小证据1069文件、2324217字节逐内容核验并共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_intent_repair_source_20261029_v1/SOURCE_AND_EVIDENCE.tar.gz`，
SHA256 `2153a0b71855a55edddffc3b3b78a9fa66c46014aac41dbfd61b44e986670d9a`。
该源码包不是全仓库/原始物理，也不含随后单字段工具与本段进展。
第二版完整审查和单字段源码已通过科学提交c078a9b4及远端合并0dc08fe1428c62c14540bfee5b9b764ae6abe67d正常push并核验。
并行RL66早期更新52b1e12d已读，双方AGENTS/UPDATE_LOG自动合并保留，非RL绑定代码未变。
