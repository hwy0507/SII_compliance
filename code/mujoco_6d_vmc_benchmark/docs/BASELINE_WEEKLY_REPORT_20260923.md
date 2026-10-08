# 本周 baseline 进展与三维对比（2026-09-23）

### 2026-10-08：office-v7 全方法24条件最终闭合

20:45:50 CST，本批16方法×24条件全部完成，384/384个55秒回合，无基础设施失败；八路评估与最终报告服务均正常退出。ESN Task/Strict为20/24、16/24，matched RNN17/24、14/24，matched MLP15/24、12/24；enhanced teacher24/24、20/24。经典三类、参数RL三类、直接RL两类和nominal zero均0/24真实任务成功。ESN相对matched RNN的RMSE/峰速低4.61%/2.53%，峰矩高2.55%；最坏穿透0.696mm，仍未全部安全通过。配对精确McNemar p(Task/Strict)=0.5078/0.7744，不声称显著全面优势。

见 [最终统一表](OFFICE_V7_UNIFORM24_FINAL_20261008.md)，完整服务器证据位于
`arm1:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/report_final/`。
五类RL共120回合加载/动作重放/归一化冻结通过；运行修复不代表性能改进，0/24是完整55秒物理失败。
没有本批运行中作业；后续优化须在独立开发条件进行，不从当前24评测条件挑参数。

### 2026-10-08 office-v7 三类障碍统一开发场景

新增独立 `office-v7` 条件：球 2.0 s、手推 4.5 s、棍推 14.0–22.5 s，最后厚桌角放置；几何、MJB、gate、actor 输入、action7 与执行器限制均沿用 office-v6。正式 `dt=5e-5`、55 s、17 个注册方法中 12 个完成物理回合，task `4/12`、strict `3/12`。三类通过行是 ESN fixed、ESN memoryless 与 matched MLP；matched RNN 因 `0.423 mm` 穿透失败。参数/RL 五行被 JAX/Orbax checkpoint sharding 基础设施错误阻止，保留为 `not run`，未伪装成物理失败。详表见 `docs/OFFICE_V7_ALL_METHODS_20261008.md`，原始收据在 arm1 的 `office_v7_three_obstacle_20261008/run_003`。这只是新 development protocol，未覆盖 office-v6 正式矩阵，也不能从单条件声称泛化优势。

### 2026-10-07 ESN-only 读出平滑开发

本轮只修改 ESN readout，不改 baseline、环境、gate 或 actor 输入。固定 20/5 identity split 的 36 候选网格选出平滑候选；离线 validation action delta energy `0.009489`（父 ESN `0.014357`），action energy `0.009701`（父 `0.012396`），最大单步 action 跳变 `1.366`（父 `1.566`），但 action MSE `0.000612`（父 `0.000242`）。这些是降低峰矩的代理，不能替代真实物理峰矩和 task/strict。兼容依赖解释器已找到，但本机 worker 的 3 GiB cgroup 审计不可用；服务器归档已完成，闭环 development 未完成，sealed 条件未读取；详见 `docs/ESN_TORQUE_GENERALIZATION_20261007.md`。

### 2026-10-07 全部方法的 ESN 重点指标表

按用户指定的 16 个方法统一列出 Task/Strict、RMSE、峰速、人手/棍子接触 P95，并保留恢复率和最大穿透约束。
展示表见 `docs/RESEARCH72_ESN_SELECTED_METRICS_ALL_METHODS_20261007.md`。

### 2026-10-07 柔顺性接触/恢复统计

在统一 `/24` cohort 上新增球、人手、棍子的接触 P95、冲量、接触时长、恢复率、最大穿透和力矩总变差统计。
ESN 人手/棍子接触 P95 为 19.6/13.4 N，恢复 3/24、2/24；matched RNN 为 20.4/13.8 N，恢复 1/24、1/24。
报告见 `docs/RESEARCH72_COMPLIANCE_METRICS_20261007.md`；右删失和无接触均保留为 NA/未恢复，不当作零。

### 2026-10-07 统一单模型/24条件主表

修正最终表的分母不一致问题：论文主表固定每个 family 的一个模型，在相同 24 个 office-v6 held-out
条件上重算。神经网络/RL 统一采用模型锁中 seed `2026100301`，经典控制器、teacher 和 nominal zero
使用唯一冻结模型；不按结果挑选 seed。统一结果见
`docs/RESEARCH72_UNIFORM24_MATRIX_20261007.md`，原三 seed `/72` 汇总仅作为附录敏感性分析。


### 2026-10-07 ESN 因果储备池读出专项（baseline 冻结）

本轮只对 proposed ESN 做算法读出实验，baseline 模型、office-v6 场景、gate、canonical48D/action7
接口和执行器限制均未修改。新增 `Δh`/`|Δh|` 因果 residual 与状态变化门控；修正真实解码后固定身份
留出 MSE 为0.000228972，matched RNN 为0.000234517，储备池清空 memory gap 为0.006588982 对0.006481536。
服务器已核验的单开发锚点上，gain=0.25 ESN task/strict 通过且三项连续指标优于 matched RNN；这仍不是
跨条件或正式 `dt=5e-5` 结果。方法和全部失败/兼容性记录见 `docs/ESN_CAUSAL_STATE_DELTA_EXPERIMENT_20261007.md`。

### 2026-10-07 最终公平矩阵闭合

38 个冻结模型×24 个 held-out 条件全部完成（912/912）；task 284、strict 218。统一矩阵见
`docs/RESEARCH72_FINAL_RESULTS_20261007.md`。ESN 60/72 task、43/72 strict；matched RNN 58/72 task、44/72 strict；
普通/匹配 MLP、memoryless、经典控制器与 RL 全部保留在相同场景和分母中。ESN 的优势应表述为 task success、RMSE 和峰速权衡，
不能声称 strict、峰值力矩或所有 baseline 上全面领先。360 条 RL 最终回合独立 actor replay 完成，失败与短回合未删除。

### 2026-10-04 11:00UTC seed303两个训练段审计

VMC参数/直接task的32新回合/35192800子步、43959奖励核验一致，32首项未核验；54.64秒穿透失败保留。
分别累计27500/27159实际步数，未冒充共同上限或冻结策略最终成绩。四证据服务器本轮根
`rl_completed_continuation_audit_v4/`与Git同字节，详见RL_REWARD_AND_CONTINUATION；原训练/开发继续。

### 2026-10-04 10:42:08UTC 公开进度与预算

RL累计370053交互/590136更新，三开发37/168、42/168、21/144（含5短失败），120拟合完成。
两个RL队列已进入登记49500阶段；最终15模型边界/912统一测试仍未完成。原预测剩余开发理想17.598–18.432h，
912/2h收尾后余量4.424–6.376h，不含全部等待/加载，不追加实验。1042两证据服务器本轮根与Git同字节，
见RESEARCH72_CAPACITY_FORECAST；未以未闭合worker汇总宣称最终优势，0新增训练/仿真/选模。

### 2026-10-04 10:00UTC 直接动作RL续训新增审计

task301新增16真实回合/16996800子步、21230奖励一致；保留一条24.84秒穿透失败及16未核验首奖励。
累计26746步未伪装27500上限；不以在线训练失败率宣称最终策略或ESN优劣。原任务继续、最终封存。
三份结果同字节共享至服务器本轮根`rl_completed_continuation_audit_v3/`与Git证据，详见RL_REWARD_AND_CONTINUATION报告。

### 2026-10-04 09:44:06UTC 预算与进度复核

最新公开成本RL331644交互/513318更新；120拟合完成，neural-LR32/168、context38/168、refit19/144，含3短回合。
原容量模型剩余开发理想18.624–19.506h，保留912与2h收尾后4.317–6.317h；冷加载/额外等待未全计，不扩搜索预算。
原监督和训练/开发PID经实际/proc核验存活，最终24仍封存。两个0944快照/预测已同字节保存在Git与服务器本轮根，
见RESEARCH72_CAPACITY_FORECAST；这是成本与worker汇总，非最终独立审计，0新训练/仿真/选模。

### 2026-10-04 已完成拟合的成本矩阵

新RESEARCH72_TRAINING_COST_TABLE公开六模仿家族全部120作业的ridge/梯度/参数/重复样本访问/进程耗时，
总288ridge、384000更新；ESN60ridge/seed对无记忆36，普通网络7拟合/seed对同特征9，不能称等计算预算。
54个同特征网络使用父权重，选第0步也保留实际训练成本；teacher80数据采集尝试、8初始开发和四家族160调参回合分开。
RL仍训练中，不拼成最终成本/性能结论。来源为已核验08:45:42UTC快照，0新物理/训练，原队列保持。

### 2026-10-04 09:14UTC 新续训段独立核验

三seed阻抗、导纳302、直接metric302/task302共六新完成段，130回合、129707转移、103765600物理子步。
原5500父前缀及新增真实观测/动作/终止一致；129577奖励精确一致、130首奖励因初始potential缺失未核验。
task302保留26短失败、metric302保留12短失败；这是在线学习记录，不作为冻结策略最终成功率。
Spark单线程1GiB/67.019秒，0新物理/梯度；原RL/开发继续，最终24封存。
结果八文件已完整核验在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_completed_continuation_audit_v2/，
详见RESEARCH72_RL_REWARD_AND_CONTINUATION，Git保留物理/奖励审计及清单原字节。

### 2026-10-04 09:04:53UTC 最终独立回放与交付衔接

新增一次性后处理监督，等待原最终批次与独立子步审计终止，逐个回放全部15个RL模型的全部已审计回合，
包括失败/短回合；原统计工具继续将缺失放在38×24计划分母中。之后接既有图和全模型同条件三角度视频。
PID2550310实际waiting_for_final、单线程3GiB，原训练/开发作业不变，无新物理、无定时任务。
本机/Spark各9项编排测试通过；实际RL回放/最终矩阵/媒体尚未完成，不据此声明ESN优势。
源码/登记在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下
final_delivery_source_v1、final_delivery_v1，已逐hash核验；详见RESEARCH72_FINAL_DELIVERY_20261004.md。

### 2026-10-04 08:45:42UTC 可复核成本与审计范围

新公开账本（文件标识0850）核验队列所引用AUDIT的hash，RL累计287566交互/425162更新；120拟合完成。
neural-LR29/168、context34/168、refit16/144，包括2条短回合；程序complete不等于55秒完整或task成功。
上一份DEVELOPMENT_AUDIT实际上仅汇总worker指标，本轮已更正标题/范围，不称独立物理子步审计。
原预测器剩余开发理想19.736–20.669h，保留912回合/2h收尾后余量4.127–6.178h，仍不保证按期完成。
七服务实际cgroup OOM/kill均0，max计数非零；源码7282022全部3297文件内容/大小/模式/文件集合核验通过。
固定环境/选择规则/全部候选不变；原队列继续，最终条件封存，没有新增仿真或搜索。
证据在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，
EXPOSURE_SNAPSHOT_20261004_0850.json与BUDGET_FORECAST_20261004_0850.json已同字节存Git。

### 2026-10-04 06:18:25UTC 既定开发队列继续（旧文件标识0717）

RL累计177603交互/206734更新，context29/168、增强网络19/168、新refit6/144；25个相关运行PID仍存活。
连续衔接服务保持等待，尚未选模/冻结/解封；最终比较仍固定38×24，失败回合继续保留。
按新快照余量，剩余开发22.511–23.573h，最终912物理22.824–23.942h，2h收尾后3.678–5.857h；不追加搜索。
详见RESEARCH72_FINAL_TRANSITION及共享根，Git证据仅含快照/预测小文件，非最终结果。

### 2026-10-04 06:09UTC 最终矩阵连续衔接

一次性依赖监督已运行，待全部开发与15个RL共同边界及监护关闭后才按既有规则选模/冻结/跑完整38×24。
当前PID2513613存活、waiting_for_predecessors、steps空，未开封最终条件；8项编排回归通过，不是最终策略结果。
后续先检查final_transition_v1/execution.json避免重复派发。05:59快照RL165754交互/191536更新，context28/168、增强19/168、refit4/144。
两源/登记/容量证据已核验共享，见RESEARCH72_FINAL_TRANSITION；不修改baseline预算/门槛或追加搜索。

### 2026-10-04 05:51UTC 奖励从物理日志到回放缓存的核验

五家族六完成训练段62回合/82004控制区间/65603200子步独立重算误差积分、峰力矩、时长并核对公共过滤action；6项边界回归及实际核算通过。
direct_metric301续训至27336实际步/22回合，新增18回合含3短失败，父前缀/新增转移核验；原task303短失败也保留，合计4个短失败。
累计81942奖励与冻结公式/缓存一致、62首奖励因初始potential未知排除；不声称potential独立重算、收敛或最终策略成功。
Spark1线程1GiB、0新物理/拟合/actor，两源与三结果全hash/大小核验，Git物理/奖励/清单同字节。
原开发及RL作业保持，最终24封存；详见RESEARCH72_RL_REWARD_AND_CONTINUATION，共享本轮根reward_intervals_audit_v1。

### 2026-10-04 05:35UTC 共同边界完整矩阵检查

最终选择8项合成回归通过，新增真实串联15个RL共同边界/关闭证据；包含自然短回合导致49336而非49500步，保留实际步数与后续1375未用步成本。
缺登记边界不回退到最新权重，关闭证据hash变化拒绝；实际13已完成存档另经真实候选校验，无训练/物理/封存读取。
RL累计151254交互/171034更新，context26/168、增强网络18/168、新refit3/144；尚未完成全部开发和15个共同最终边界。
main9ccabdd完整3284文件已核验共享；本轮根EXPOSURE_SNAPSHOT_20261004_0535.json SHA2809fa0829b508af25ede9c933cbca54b9a804441589cca64ed59c786ebe83a9。
服务器arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；没有缩小最终38×24矩阵或宣称ESN胜出。

### 2026-10-04 05:19UTC RL真实续训及奖励输入管道

导纳/VMC301完整27500阶段的75/74存档、44源与原轨迹引用核验，5500前缀/新增22000转移逐值关联真实执行；非最终策略评价。
新奖励缓存审计覆盖五家族代表训练段，60124奖励与冻结公式逐值一致，44个首奖励初始potential缺失明确排除；短失败补偿保留。
四项合成回归通过，未加载learner/actor、未执行物理或改奖励；保存区间未在此独立从子步重算，不夸大全覆盖。
共享rl_completed_continuation_audit_v1五文件和reward_replay_source_v1两源核验，Git原字节证据，详见RESEARCH72_RL_REWARD_AND_CONTINUATION。
三RL实际活跃且OOM0，累计140438交互/154400更新；context25/168、增强网络17/168、新refit2/144，最终24未解封。

### 2026-10-04 04:59UTC 新组公平成本与更强RNN

18模型同公开序列单线程actor-only计时74250次，导出重放误差0；ESN约32–33μs而普通MLP/RNN约8/10μs，参数少不等于推理快。
新matched RNN三个seed均选择真实3600–4000更新的checkpoint，其验证动作MSE略优于ESN，不再是原初始组的零步选择现象。
全部新模型同数据、同8开发身份继续，代理误差不判任务；没有再加搜索或筛掉baseline。
共享refit_inference_archive_v1六文件hash/大小/模式核验，PROFILE Git同字节，详细数值与限制见READOUT_REFIT_RESULTS。

### 2026-10-04 04:52UTC 最终全候选汇总保护

修正最终学习选择器JSON路径/hash类型兼容，完整72候选合成账本跑通实际load_phase/main；全部失败仍保留18选定模型、refit少1回合或teacher收据变化均拒绝。
本机/Spark各3通过，原38模型汇总5通过；实际最终选模未运行，24仍封存。共享selection_guard_source_v1两源核验，不改运行中实验。
新refit仅首条seed301/development000 worker审计task/strict通过（30.699mm/49.981Nm/.349058m/s，外穿透.143599mm），整阶段独立审计待完结，不称泛化优势。
旧context24/168、增强网络15/168、新refit1/144及三RL原队列继续，不削减baseline或新增搜索。

### 2026-10-04 04:36UTC 共享新teacher的六家族重训与RL真实继承

teacher40/40任务、25/40strict，20训练＋5验证同数据供全部六模仿家族；验证strict6→5的退步及柱暴露0/5公开保留。
修订02在拟合前登记，18模型本机1线程/3GiB完成；纯ESN只学3780读出，6固定模型72候选及18actor输入/动作重放通过。
763文件已核验共享local_context_readout_refit_archive_v1，18×8开发完整登记启动，全部旧候选保留，不能以新数据差值单独证明记忆机制。
累计实际ESN60候选/seed、无记忆36，ordinary+matched MLP/RNN各16，不称等计算。成本144回合前瞻计入，不削减最终38×24矩阵。
导纳/VMC301继承5500前缀、追加11000真实转移核验通过，未逐梯度或独立奖励重算；q1自然得槽，未发暂停/恢复信号。
当前120拟合、RL106418交互/102858更新、旧context23/168、增强网络14/168、新refit0/144，最终条件仍封存。
共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；
详见RESEARCH72_READOUT_REFIT_RESULTS、TEACHER_DATA_QUALITY和Git原字节证据；没有新的全面ESN优势结论。

### 2026-10-04 03:51UTC teacher同训练身份配对审计

64完整回合7040万子步重算并关联原始hash通过，新teacher task32/32（旧29）、strict20/32（旧18），严格改进8条而退化6条。
推杆P95均值降低，桌角接触时长及累计力模上升；新合格示范仍仅2条柱接触，不将task改善当全面柔顺领先。
68产物文件已核验共享teacher_data_train_comparison_v1，Git小证据同字节，详见RESEARCH72_TEACHER_DATA_QUALITY。
采集37/40、context18/168、增强网络10/168；全部失败保留，尚未新学生拟合或开封最终条件。

### 2026-10-04 03:27UTC 共同RL边界与完整比较保留

修订后预测计满每模型52,250交互总成本，最终912和2h收尾均保留，理想总余量7.18–9.32h；真实等待/冷加载仍未包含。
7项容量检查通过，原件已共享核验并保留Git同字节JSON，不将预测余量当追加ESN预算授权。

所有5家族×3seed统一前瞻登记49,500自然阶段，保留原80k优化器日程，实际完整回合预算48,126–49,500。
选择不读奖励/任务成败，后续两冗余阶段完整回合收尾，额外最多2750步/模型全部计成本；缺模型不静默回退。
Spark7边界测试全通过、最终选择5通过；监护已运行但尚未对训练发信号，原作业不重启。详见RESEARCH72_RL_FINAL_BOUNDARY。
teacher32训练回合task32/32、strict20/32，8验证仍待完成；增强网络8/168、context16/168，RL72418交互/44856更新。
这不是最终比较或ESN结果，保持全部方法、912留出目标和原冻结物理/gate，未追加拟合或解封。

### 2026-10-04 02:51UTC 真实续训首动作与剩余时窗

导纳/VMC301实际续训至第5回合结束，独立加载父checkpoint后首随机动作与真实记录逐值一致；0新增物理/梯度，非全段重放。
新增任务奖励303首段5168步/338更新，train031穿透2.560352mm中止保留；另VMC303首段5500步，两个存档核验通过，累计十首段。
审计源与结果共享rl_resume_action_audit_v1、rl_saved_state_audit_v3，Git原件；详见RL_MEMORY_PREFLIGHT。
容量模型新增不可拆分RL队列约束，跑满全部80k并完成912最终回合的余量约+0.67至−1.88h，且未计q1继续等待。
6容量＋6接续检查通过，预算预测四文件已共享核验；当前不改稳定runtime或按失败剪除baseline，下一步优先明确共同边界。
teacher26/40、context13/168、增强网络4/168，未完成最终模型锁与保留测试，ESN优势仍未证明。

### 2026-10-04 02:22UTC 方法草稿与八模型RL首段

英文方法/设置草稿RESEARCH72_MANUSCRIPT_METHODS已核对实际源，明确48接口中的18使用字段、128宽度不等于相同参数/算力、
MLP/RNN的真实架构/损失差异，以及RL参数动作7/5/7与底层控制律；task/strict不被新指标替换。
正文已核验到共享本轮根methods_draft_v1；最终变体/结果/摘要主张待全方法留出，未宣称投稿就绪。
直接任务奖励302和阻抗303首段存档独立核验通过，含全部原始训练trace引用hash，新增审计v2与Git同字节。
八模型各5500步/1002更新，累计46875交互；q1等租约、OOM0。新teacher21/40、context10/168、增强网络2/168。
不追加搜索、不省略baseline、不重启稳定作业；实际续训/最终统一912回合与审计仍待完成。

### 2026-10-04 01:54UTC 六真实RL存档与名义参考

六RL各5500交互/1002更新，含5D阻抗；完整文件/回放/计数/RNG/原源和轨迹hash独立核验通过，未混称实际续训或任务成功。
名义规划＋WBC八条完整开发及独立审计完成，task/strict0/8、全carry；RMSE26.697mm低而任务未完成，详见CONTROLLER_CONFIRMATION。
本轮证据rl_saved_state_audit_v1、nominal_development及预算v3均服务器已核验，Git保存小型原件，source/hash见专题报告。
teacher16/40、context8/168，增强网络已接续；全RL cap下最终窗口很紧，不追加候选或省略baseline。最终留出仍封存。

### 2026-10-04 01:44UTC 共同物理装置与真实资源进展

新增精确MJB/实际源/公开轨迹只读审计：自由球1kg、物块80g摩擦抓持，有限质量人/杆代理，驱动力限制不是接触力保证。
保留场外旧mocap及球2s前保持的真实设置；仿真比较不当人体安全或硬件部署证明。原环境/gate不改，详见RESEARCH72_APPARATUS_SCOPE。
3文件证据与服务器原件逐hash一致，Git同步；0新仿真/拟合/最终条件访问。
teacher14/40、名义7/8、context7/168；RL四模型首段完成，后续两模型4750步，第三等租约。缓存max事件增加、OOM0；最终全方法比较待完成。

### 2026-10-04 01:19UTC ESN方法身份与持续资源核对

从seed重建18个ESN/无记忆拟合的216保留候选，固定输入/循环/gate/时间尺度逐值一致，拒绝新增隐藏层；真实服务器权重逐hash关联。
MLP/RNN矩阵允许学习，不把它们误归入纯ESN；0拟合/物理，无效负对照只存内存。结果与源已共享，见RESEARCH72_INPUT_AND_MEDIA_AUDIT。
两真实RL队列第二模型开始梯度；峰触3GiB且max事件>0、OOM0，当前主要可回收file-cache，继续观察，不声称后续无OOM保证。
开发/新teacher未完成，原24最终封存，尚没有正式全baseline比较结论。

### 2026-10-04 00:56UTC 真实RL首段checkpoint核验

调导纳301/调VMC301各5500交互、4完整回合、1002更新，存档75文件及经验回放/计数/边界/源hash核验通过。
两真实queue子服务累计峰2.67/2.66GiB，max/oom0，已轮转下一模型；第三等共享槽位。真实续训/最终冻结回放尚未完成。
本轮只读不产生新拟合或物理回合；不能把训练存档等同放置成功。原始manifest入Git，其余服务器路径见RESEARCH72_RL_MEMORY_PREFLIGHT。
最新容量不足以追加144开发同时保证912最终，故暂不增加ESN候选，全部baseline与原最终分母保留。

### 2026-10-04 00:35UTC 全部经典确认与真实RL接续

8候选×8开发条件64完整回合/独立审计完成。选teacher09(8task/7strict)、adm03/imp02/vmc11(各0/8task)；
teacher柱子/link6 .31387mm失败不删，经典有限搜索不宣称普遍上限。排序优先门槛/成功/最坏穿透，非只挑最低RMSE。
两个RL实际训练首回合已结束，仍warm-up无梯度；各子服务峰约1.94GiB无OOM，第三等租约。总4物理，新teacher40条采集中。
已知teacher55s最终入口精确重放/审计通过；三步长短诊断峰力10.4%敏感，正式50μs/gate不改，不作策略/硬件安全证明。
上游SimbaV2完整源归档225文件及live匹配，最终报告新增失败阶段/恢复删失和严格checkpoint证据关联；14项合成检查通过。
服务器research72_20261003_1149根下原始轨迹/hash保留，见RESEARCH72_CONTROLLER_CONFIRMATION_20261004等报告。
增强网络/context仍待完整闭环；真正24最终封存，尚不构成RAL最终结论。

### 2026-10-03 23:47UTC 独立RL actor回放与证据覆盖

除worker内回放，新增独立进程重载冻结SimbaV2，对全部完成评估（含失败/短回合）核验raw action、观测、normalizer及hash。
最终矩阵保留缺少额外回放的物理结果，并显示incomplete覆盖。14项合成测试通过、源码overlay已共享，真实RL回放未执行。
确认42/64运行；RL等前序，未把工程检查当训练/任务成功，见RESEARCH72_RL_ACTOR_REPLAY_20261004。

### 2026-10-03 23:30UTC 全baseline图表公平呈现准备

最终图保持全部16方法固定顺序，缺失上下界、无配对NA和全部五事件不省略；同一审计报告直接导出，无新筛选/统计。
三项合成测试与目视核验通过，source/input/六图已在figure_engineering_archive_v4/evidence逐hash共享；仅工程样例不是比较结果。
teacher/经典确认运行，RL仍待前序；见RESEARCH72_FIGURE_EXPORT，最终封存不读。

### 2026-10-03 23:10UTC 方法定位与公平比较边界

补读近期RAL储备池控制作者稿，及ICRA2025/2026无传感ESN力估计摘要；未把不同软体任务的结果移作本项目优势。
固定特征/线性读出与机器人RC均有先例，必须比较充分优化的MLP/RNN、经典与RL并完成机制消融后决定主张。
0新实验/预算，8文件响应与阅读边界已共享核验，见RESEARCH72_METHOD_POSITIONING；参数确认16/64、四仿真继续。

### 2026-10-03 22:57UTC RL组合内存预检

用真实训练依赖、完整80k Replay和实测物理队列1.086GB等量压力做4周期有限CUDA更新，峰值2.649GiB，距3GiB约360MiB，
无OOM/0新物理；8工程更新丢弃，原7D checkpoint73文件hash不变。真实三learner与训练回合仍待验证，不冒充baseline开训。
记录/源已共享核验，见RESEARCH72_RL_MEMORY_PREFLIGHT。另明确原RMSE为各回合当前阶段goal误差，不能单独作为共同轨迹跟踪优势。

### 2026-10-03 22:45UTC 初始同条件264回合完成

所有33初始候选×8身份实跑及独立审计完成，3短回合保留。ESN点版/积分strict9/24与4/24；普通MLP点版7/24，
无记忆及同特征MLP各版本6/24，普通RNN两版本均0/24。不是最终选定权重或留出率，不能删初始失败。
同特征RNN六权重均selected_update=0，保留ESN初始化，当前同计数不证明算法优势；增强学习率组仍待闭环。
完整任务/负载/暴露/删失与全部seed在RESEARCH72_INITIAL_DEVELOPMENT及同字节JSON证据，报告SHA adb7ff8e71117d09a612796e6a56ca02b17b430054ca707f51832112194d7b4d。
64回合teacher与经典参数确认已开始；RL适配、增强组和最终38×24比较未完成，封存条件不读。

### 2026-10-03 22:05UTC 短数值诊断与公平分母

原teacher/公开train_000登记3×3s dt100/50/25μs诊断，待前序和共享租约，0实际派发；正式55s/50μs不变。
核对球尖峰数值敏感性，不用于候选排名、示范或完整任务分母；所有成本保留。3原生模型/角色＋6预算/账本检查通过。
初始246/264，第七身份完整ESN/matchedRNN各1/6strict，matchedMLP2/6、memoryless1/3、普通MLP1/6、普通RNN0/6。
增强组/RL仍待前序，24最终封存，详情和hash见RESEARCH72_NUMERICAL_DIAGNOSTIC。

### 2026-10-03 21:35UTC 输入与媒体交付工程

全部102学习模型在同一train_000的1375观测上检查声明字段，140250动作精确重放，未声明字段扰动不改动作/可见状态；
包含全部普通及matched MLP/RNN，未按成功筛选，不涵盖RL或真实传感器有效性。3负对照通过。
同一已知teacher原轨迹完整三机位55s本地渲染18.77s、全帧解码1.69s，0物理积分、0拟合，峰值0.644GiB。
输入和输出hash、全部102行与10文件媒体已核验共享。最终首条件全38模型/seed规则不变，未冒充新最终结果。
四物理队列最近220/264，其他阶段等前序；详情见RESEARCH72_INPUT_AND_MEDIA_AUDIT。

### 2026-10-03 21:15UTC 第六开发条件与最终测试容量

第六身份初始ESN/matchedRNN各4task/0strict（n6）；matchedMLP2/2、memoryless1/1、普通MLP2/1、普通RNN2/0。
失败/短回合保留，不将候选计数当最终方法成功率。ESN四条放置均柱子穿透超限，原0.2mm不变。
新容量预测计入全部15RL至80k、所有已登记队列及最终912回合；理想预算不足以再加144回合，因此本次不追加拟合。
三RL真实吞吐仍未验证，增强baseline仍等待；最终矩阵和独立审计不能被ESN追加实验挤掉。
只读快照与3项会计测试/源hash见RESEARCH72_CAPACITY_FORECAST，0新物理/0学习。

### 2026-10-03 20:56UTC 官方RL吞吐与完整训练验证边界

零物理GPU探针完成：5D/7D单次动作＋两更新约18–19ms，首轮编译16–71s，峰值2.07GiB；
同进程顺序计时可能复用缓存，不能按冷启动数值排名算法。164工程更新单独计数，权重丢弃不进入候选。
原checkpoint74/73文件集合与字节精确不变；真实三learner争用、组合内存和物理续跑还未发生。
198/264初始开发，四仿真稳定；RL v2等前序，完整结果不能提前写为已完成。源/收据hash见RESEARCH72_RL_THROUGHPUT。

### 2026-10-03 20:37UTC 首撞峰值的归因边界

170条公开轨迹统一核对真实actor时钟：首段球接触0.45–0.50ms，距下次40ms周期actor计算还有9.20–32.20ms。
170/170球窗峰值先于该计算，不能按首峰大小归因25Hz ESN即时反馈优势；先前动作/姿态和公共WBC仍影响结果。
保留所有峰值、失败和原门槛，柔顺性同时结合撞后恢复、持续接触负载和放置。4合成检查、0新物理/拟合；
实际数据/源码/图hash见RESEARCH72_IMPACT_TIMING，包含全部初始学习候选和teacher，不冒充RL已验证。
初始184/264，4仿真稳定，RL v2仍等前序，封存身份未读。

### 2026-10-03 20:15UTC 公平覆盖的RL轮转续训与第五条件

RL原逐模型跑满的派发顺序改为每队列5模型共同累计边界5500/27500/49500/71500/80000，
首次office训练前登记，同80k上限/奖励/网络/输入/截止。只替换零派发的等待器；活跃v2独立runtime，
旧记录原样加supersession收据。16调度/模型汇总/锁回归通过，实际续跑尚待验证；更频繁进程启动有编译成本。
最后模型保留实际步和调度截止原因，不称等训练量/收敛。源码与产物hash见RESEARCH72_RL_DISPATCH及根UPDATE_LOG。
第五完整条件ESN和matchedRNN各4/6task、1/6strict；matchedMLP2/2、memoryless1/1、ordinaryMLP1/1、ordinaryRNN3/0。
仍是候选开发，非最终比较；三条ESN已放置因pillar穿透超0.2mm失败。初始169/264，4仿真稳定，最终24封存。
统计报告新增点区间/恒定差值分别标记，18回归通过；原探索性交叉bootstrap不变，不声称总体零不确定性。

### 2026-10-03 19:37UTC 全候选本体覆盖诊断与第四条件

对前三共同身份的全部99轨迹用同一固定18D本体尺度做训练身份留一近邻诊断，阈值仅由18训练身份校准。
包括MLP/RNN/无记忆全部失败与短回合，图中重合的父模型行为如实保留；不作独立帧显著性检验或胜者排名。
第四共同身份ESN/matchedRNN各5/6task、4/6strict；matchedMLP2/6strict、memoryless1/3、ordinaryMLP1/6、ordinaryRNN0/6。
不是最终选择后成功率，增强baseline仍待运行。初始143/264，4稳定仿真；只读诊断0新物理/拟合。

### 2026-10-03 19:19UTC 新读出对照与重复计算防护准备

共享teacher再拟合入口已准备。若数据改变，6学习类同数据；若数据不变，普通MLP/RNN复用已完成的point权重及回合，
只新评估ESN/无记忆/同特征MLP/RNN的固定交互变化，不把同一权重重复跑当新增seed。新模型注册和最后选择均核验谱系。
14工程测试通过，尚无修订02、新拟合或新增闭环；现有初始131/264，RL和后续组继续等待，最终24仍封存。

### 2026-10-03 18:59UTC 全方法补充接触统计规范

新增全观测时长及原事件窗外负载，仅作描述，旧事件/恢复/task/strict不变；防止漏报放置阶段人体接触。
完整/短失败分开，无接触NA、缺旧字段missing，不相加重叠的external/edge列。最终矩阵另展示全部观测安全审计。
14测试及7条真实原生旧字段精确回归通过，原运行snapshot不改；该补充是开发观察后登记，不冒充最初预注册。
第三完整开发条件ESN/matchedRNN各1/6严格，matchedMLP2/6、memoryless1/3、ordinaryMLP/RNN0严格；
增强组和RL仍待运行，不能按旧候选宣称最强baseline已完成。初始115/264，总4仿真；24最终仍封存。

### 2026-10-03 18:36UTC 最终38模型完整性与RL选权重规则

新增最终汇总器强制6学习族、5RL族各3seed及5确定性参考，缺失方法/seed不静默缩矩阵，
开发失败也保留。RL按最新完成训练边界选择，不按测试/奖励事后挑checkpoint；实际步数与stop_reason独立披露。
5项合成与文件衔接检查通过，真实最终尚未执行。初始开发100/264，4队列稳定；RL仍等待前序。
方法定位文档注明ESN新颖性、容量与成本边界，固定变换不能隐去或冒充普通MLP/RNN没有信息访问。

### 2026-10-03 18:10UTC 第二条件与全方法最终汇总入口

第二公开条件33候选均实跑：ESN/matchedRNN各3/6严格，ordinaryMLP1/6，ordinaryRNN/matchedMLP各0/6，
memoryless0/3。不是最终选定方法成功率，也不以尚未改善的旧网络结论代替后续小学习率组。
新最终矩阵按计划全方法/seed保留失败和未审计缺失，接触NA、删失和完整/短回合分开，交叉置信区间明确条件。
8统计/证据链回归、2最终队列故障回归、1全模型媒体选择回归通过；没有真正最终数据或新物理回合。
完整计划先落盘，工程失败的队列不会抹掉其他已完成peer的审计机会；原运行快照保持不变。

### 2026-10-03 17:46UTC 共享特征与最终入口工程

开发60/264完成，4稳定队列；MLP/RNN小学习率组、调制记忆组及RL仍按登记顺序等待。
新增未拟合context×state读出给同特征MLP/RNN同样固定特征，不增加actor信息；128宽度不代表等参数。
全部旧102模型完整train_000重放精确；新随机系数仅工程探针，不计入任务优劣或候选选择。
最终入口已知训练轨迹预演已登记等待，独立合成协议不会解封真实24条件。服务器证据与hash见UPDATE_LOG。

### 2026-10-03 17:08UTC 首条件33模型结果齐备

同development_000：ESN6候选回合4task/3strict，matchedRNN同为4/3，matchedMLP2/2（分母6），
memoryless1/1（分母3），ordinaryMLP1/1、ordinaryRNN2/0（各分母6）。不是跨条件/选定权重最终成功率。
全部模型参与离线柱子接触诊断；matchedRNN部分仍等同初始ESN，后续小学习率增强baseline尚待执行。
失败对照不删掉，truth仅离线诊断不作actor/训练输入。当前37/264完成，RL仍等待参数确认；最终仍封存。

### 2026-10-03 16:50UTC 容量与推理成本核验

同数据全部102已拟合模型零仿真完整train_000重放误差全0。可训练系数ESN2884、ordinaryMLP5504、
ordinaryRNN21888、matchedMLP22852、matchedRNN39236；同128宽度不能写成同参数数或同训练开销。
本地actor-only族中位推理ESN32.15us、普通MLP7.98us、普通RNN10us，不声称ESN推理最快。
成对条件/seed bootstrap与缺失、接触NA、删失处理完成8项合成回归；参数RL维度和阻抗力矩律差异已更正。
实际数据在服务器本轮根inference_profile_archive_v1，原始timing/source/hash与命令见根UPDATE_LOG。

### 2026-10-03 16:30UTC 筛选完成、闭环对比开始

teacher/导纳/阻抗/VMC各24次筛选已完成并独立审计，teacher21task/13strict，其余各0/24；
这些不是最终参数或盲测，下一步原定8条件确认。初始33学习模型正在同8条件实跑，
首条件ESN点版与memoryless/matchedMLP均task/strict成功，ESN积分版放置越过25mm门槛失败。
ESN点版推杆P95力更低，但脱离和力积分不如无记忆，不能只选有利指标。完整比较仍待多条件与seed。
选定teacher的40真实回合再采集入口已就绪，数据对各学习族共享；新增训练预算尚未启动。
RL参数维度导纳7D/阻抗5D/VMC7D与直接动作语义区别已在分析方案披露（16:45复核纠正概称5D）；
阻抗另有底层力矩律。最终24条件继续封存。服务器入口见UPDATE_LOG。

### 2026-10-03 15:37UTC 新记忆机制也提供给baseline

固定本体context-leak调制ESN、重训无记忆、同特征MLP/RNN共21模型已完成。同数据/128宽度；
MLP/RNN各loss复用先前3seed平均验证选出的学习率、各4000更新；固定gate不参与梯度训练。
工程数值/零平衡/输入隔离通过。全部模型将跑相同8开发条件，不能只保留ESN有利子组。
预算修订01先登记24→48cap，实际各族成本单列；旧33与学习率复核21权重仍保留比较。
新机制离线拟合普遍差于原版，未构成闭环优势；RL仍等待经典确认，最终条件继续封存。

### 2026-10-03 15:11UTC 成本与最终比较口径登记

两分支实时核对无新更新，保留稳定四仿真与后续RL队列。开发筛选15:08快照完成56/96，尚不能定稿参数。
拟合与仿真成本分开：108ridge候选、288000神经更新，RL尚未开始；失败teacher仍计入共享数据成本。
最终接口要求全部类别/随机种子进入矩阵，避免只跑开发成功方法；合成回归通过，真实留出未开封。
分析方案规定条件/seed交叉抽样、完整队列成功率、接触覆盖和恢复删失，不能把无接触或早停的低力当领先。
服务器根与逐项成本hash见UPDATE_LOG；正式公平比较仍在推进中。

### 2026-10-03 14:43UTC 神经baseline学习率校正完成

48个同数据/宽度/更新数复核完成，学习率按3seed平均身份验证误差选择，候选仍在原cap内。
普通MLP点误差下降23.91%，普通RNN下降36.42%，不是闭环成功率；21个新权重进入168回合同条件开发。
原学习率获胜的3模型复用既有开发计划，避免无信息重复；完整失败和每次训练曝光保留。
另准备相同共享WBC的零让位参考8回合。源/模型/诊断已核验到本轮Spark根，入口和hash见根UPDATE_LOG。
最终24身份未读取，15个RL办公适配模型仍等待前序，不把primitive迁移失败当RL族不适用。

### 2026-10-03 14:18UTC RL办公适配已登记，尚未开训

15个从零办公RL模型（3参数族＋2直接reward，各3seed），累计8万步/模型；先5500步段再按原优化器计划续跑，
不把续跑计为新预算。参数中心由固定规则经典开发确认给出，原控制律不变。完整状态/优化器/replay/RNG工程回归通过，
物理训练等待现有统一开发完成。新递归hash包含此前遗漏的嵌套权重，全部失败和学习成本会保留。
运行证据与源码在本轮Spark根`rl_checkpoint_probe_v2/`及`rl_office_adaptation_v1/`，完整路径/hash见根UPDATE_LOG。

### 2026-10-03 13:50UTC 同数据拟合完成与经典适配启动

33个同数据ESN/MLP/RNN/记忆消融模型完成，3seed、18真实训练＋6身份验证。所有模型均登记8开发条件实跑，
同特征网络验证选初始化的结果保留，不据此宣称ESN优越。宽度相同不等于参数/训练成本相同，继续记录成本。
导纳/阻抗/VMC各12固定预算候选与12增强teacher同步筛选（96回合），后续各2候选×8条件确认；原控制律/限制不变。
RL IPC已通过完整55秒实际物理逐数组重放，官方SimbaV2新办公训练尚未开始；primitive迁移失败仍不推广为RL族失败。
服务器 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`，
数据与模型归档均核验，细节/小证据见根UPDATE_LOG及`evidence/research72_20261003/`。最终24身份封存，当前只是开发。

### 2026-10-03 12:32UTC 同数据/办公适配准备

新teacher28/48完成、25 task/15 strict，未结束。准备33模型同数据学习任务：3seed，纯ESN点误差/积分误差、
重新训练无记忆，以及普通/同特征MLP与RNN两种损失。明确参数、父模型及优化预算差异，不只给ESN新机制。
办公RL从零适配/冻结评估/动作通信已实现，使用官方SimbaV2原归一化和基线奖励，但物理重放尚待验证，未开训。
所有新物理均原v6、dt5e-5；新24最终条件未读取。服务器学习准备源 `.../runs/main/research72_20261003_1149_learning_runtime_v2/`，
完整主机/路径/hash及空闲等待器替换记录见根UPDATE_LOG。稳定teacher作业未重启。

### 2026-10-03 11:49UTC 新72小时公平比较研究已启动

仓库根 `RESEARCH_STATUS.md` 为固定进度入口。新授权窗口至10-06 11:30UTC，初批48个事先登记的
teacher训练/验证/开发回合正在Spark四队列运行，正式dt5e-5、同v6/门槛；24最终新条件封存未测。
计划同数据ESN/MLP/RNN、显式经典及RL适配预算、逐方法曝光账本；这些训练/适配目前均未完成。
不把primitive迁移失败写成RL本质失败，不只给proposed额外数据。基础main33f4380/baselineebb0e1e已实时核对。
服务器原生根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`；
公开协议/源hash见 `evidence/research72_20261003/` 和根更新日志。前轮正式两个ESN失败结论保留。

### 2026-10-03 全26方法同一正式锚点实际重跑完成

新增[正式测试矩阵](evidence/all_methods_formal_20261003/report/MATRIX.md)：26冻结模型全部用dt5e-5、
相同v6/seed/初态/门槛，各完整55秒；不按原开发资格筛选。5个task/strict通过：增强teacher、
普通RNN两seed、同特征RNN seed1、无记忆。两个ESN均失败，三RL调参停carry、四RL action停approach。
共同配置/子步/动作/权重及26放置审计通过，7旧formal轨迹hash完全复现。单锚点不代表泛化成功率。
服务器根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/all_methods_formal_20261003_104728/`，
双遍核验2787文件/3.827GB；Git小证据和核验收据见矩阵上级目录。已结束，不改环境或重训。
下一研究窗口来自用户新授权，需补强同训练条件baseline及ESN稳定放置，保持本次冻结证据不变。

### 2026-10-03 全26方法柔顺性统一制表

新增[完整矩阵](evidence/unified_compliance_20261003/MATRIX.md)，基于相同v6/原生运行库/开发dt1e-4
四条件104条完整回合，含3个RL调参和4个RL action，保留全部失败与接触覆盖。
除任务/strict、RMSE/峰矩/峰速，还列球峰力、人手/杆/桌角P95力、力模积分、接触时长及恢复删失。
七RL本组task0/4；ESN task1/4和3/4，但RL调导纳的人手/杆P95力低于两个ESN，不能声称ESN全指标最佳。
未碰杆的固定/本轮调参阻抗记NA，不当零力。历史训练曝光不同、formal两个ESN失败均保持披露。
仅本地后处理，未新增物理回合/调参；来源hash及独立核验完成，矩阵与脚本服务器路径：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unified_compliance_20261003_1034/`。

### 2026-10-03 十二小时预算同场景终评已完成

沿用baseline已发布v6与原生Spark运行库，未改环境/gate/接口/执行器。26模型×4条件104条、
预先合格7模型×8随机56条、7正式dt5e-5均完整55秒。ESN两seed主strict1/4、2/4，随机各4/8；
同特征RNN主各2/4、随机1/8与2/8，增强teacher/无记忆随机各5/8。formal两个ESN失败，
teacher/无记忆/RNN seed1通过。ESN有局部随机成功数优势，没有全面柔顺或数值稳健优势。
普通MLP主0/4、同特征MLP2/4，普通RNN主2/4和1/4；七经典及七冻结RL各task0/4，
但后者旧primitive训练曝光与本轮office适配不同。非随机/formal合格方法是未测试，不算失败。

三个同seed共同strict条件ESN较快放置但杆p95力都更大；大量恢复记录删失，持续主动滑脱未证明。
193选定记录完整接触审计、192末态重建＋1原abort、动作/隐藏状态/配置/源hash和执行器审计完成。
完成时刻的20ms插值误差另列采样勘误，原gate不变。47完整视频＋2对比MP4已解码/hash核验。
原生证据双遍核验40094文件、32.802GB，本机/学习25份历史收据另保留（累计大小含重复）。
服务器路径、清单SHA、模型容量/数据不足/失败与后续方向详见`PAPER_ESN_12H_RESULTS_20261003.md`。
本轮无运行中作业，无定时任务；未实现稳定泛化ESN，不以改指标权重包装“最好”。

### 十二小时研究21:41UTC：主比较/正式步长未支持ESN全面优越

104四设计条件全部完整并独立审计：ESN两seed strict1/4、2/4；同特征RNN各2/4，普通RNN2/4、1/4，
同特征MLP2/4、无记忆2/4、teacher2/4。七经典、七冻结RL及zero任务均0/4，但训练曝光不同。
formal7条全部完成：teacher、无记忆及RNN seed1通过；两个ESN任务失败，穿透并未超原阈值。
开发dt上的成功不能冒充正式数值稳健。h3存在teacher失败/ESN成功，但无记忆也成功，不证明记忆必要。
固定7模型的56随机补充已开始；其余设计条件14完整视频已核验，主表/视频/终版审计仍在收尾。

### 十二小时研究21:09UTC：最终验证推进，审计覆盖扩展

主比较81/104已完成，模型/环境/门槛未改。112原生开发、82本机开发及7不同库兼容诊断分别保存；
10最终学习模型各1375帧输入边界核验通过，原先58完成训练及失败导出均保留。
后处理流水线固定展示h1全部26模型和formal全部7模型，短abort不补长；等待主/formal/随机验证及独立审计。
补充全任务人体系接触，避免指令窗口后再接触被遗漏；原事件统计不改，这项补充不冒称预登记终点。
放置累计的13个25Hz样本与连续时间证明明确区分。共享路径/源码hash/一次失败解包的保留记录见联合进度21:09节。

### 十二小时研究20:09UTC：全26模型最终锁定，开始真正的配对验证

原生38候选及独立审计完成；导纳01、阻抗12、VMC04按事前规则入选，同时保留历史固定中心。
26模型×4条件已开始，7个开发strict通过者资格已冻结，后续做formal；在首条最终回合开始前
另登记8随机条件×7合格模型的补充验证，不重开训练。最终lock及原/补充条件文件均SHA核验。
本机82条开发回合原始失败/审计全部映射到服务器；537项baseline代码/参数/权重另存共享副本。
主比较、formal与补充必须分表，不能将资格外baseline计失败或宣称当前已获泛化优势。路径见联合进度20:09记录。

### 十二小时研究19:27UTC：RNN与调参VMC也成功，尚无ESN独占优势

同特征RNN两seed开发task/strict均通过，seed2为29.330mm/49.396Nm/.360622m/s、穿透.114708mm；
固定参数搜索原VMC04亦strict通过，36.385mm/48.822Nm/.368985m/s。ESN两seed成功仍成立，
但必须与这些强对照比较。新训练已结束，最终26模型选型规则事前冻结；等待经典38候选和独立
审计后运行四个共同保留条件，并对开发strict合格者做5e-5步长验证，不以测试结果继续学习。
完整学习证据69组和剩余29条本机经典回合已SHA核验共享，路径/hash见联合进度19:27记录。
最终泛化和正式分辨率尚未完成，当前不宣布最佳；六条完整开发视频正在补齐。

### 十二小时研究18:45UTC：两个ESN初始化成功，补强公平对照

35mm teacher数据的纯固定储备池ESN两seed锚点task/strict均成功，分别29.013/28.015mm、
50.685/50.290Nm、.389144/.354489m/s；同数据普通MLP/RNN各0/2。但无记忆重训也成功，
因此不能仅由清空记忆失败证明ESN记忆是必要机制。同特征可训练MLP/RNN、长反传RNN对照已补；
长RNN有一条放置但穿透超限，共享DAgger两个ESN亦超限。38条经典候选全量原生复评中，不只
转移本机最优者。四个保留条件仍封存，最终排名/泛化尚未成立，所有负结果和原始轨迹保留。

### 十二小时研究 17:56 UTC：统一环境已有纯 ESN 开发成功，待稳健性审计

128固定单元/线性读出ESN recovery05_fixed在原baseline运行环境完成task/strict，终点XY7.929mm，
全程41.476mm/50.136Nm/.357187m/s，外穿透.125753mm。条件漏率对照XY25.161mm仍失败，
可训练漏率对照放置成功但穿透.484566mm超限。当前不构成跨条件或独占优势；改进VMC也有三条
原生成功，35mm teacher完成保持13.6s。原14方法已精确重放，共15条同运行环境一致性核验通过。
经典调参、同数据学生训练/闭环及独立审计继续；保留条件封存，完整目录见联合进度最新记录。

### 十二小时研究中期：没有预设ESN获胜，统一原baseline运行环境

原环境RL七条复跑恢复了历史结果，均未放置成功；误用另一JAX环境的七条保留为兼容性诊断。
原始VMC本地已有一条成功，安全余量小，正在原baseline解释器复核。纯ESN动作积分训练版
末帧已真实松爪放在目标内，但有效保持仅.04s不足.5s，仍判失败；28.915mm/49.162Nm/
.382531m/s、外穿透.168985mm。保持最终释放稳定放置/安全为首要结果，接触负担/恢复删失
和三项传统指标为分层诊断，不用末帧位置或低RMSE替代成功。MLP/RNN获同积分目标学习对照。
预登记经典控制器九条开发均失败，完整审计和服务器SHA归档已完成；teacher恢复/平滑与
同宽学生改进继续，保留条件仍未使用。原生运行与已核验归档路径见联合进度中期记录。

### 2026-10-02 十二小时比较在执行：15:05 UTC阶段记录

在baseline冻结v6(MJB173e404b)而非旧v5上，原始VMC{}首条完成task/strict，28.690mm/
50.573Nm/.384913m/s，穿透.194972mm接近上限；不能称稳健或ESN独占优势。首批旧ESN及恢复
teacher失败，新蒸馏两版亦未放置。任务与安全优先，新增真实接触曝光、力冲量/p95、杆保持期
脱离、恢复删失等统一子步诊断，不用事后有利权重制造“冠军分”。现有经典/后续同数据128宽
MLP/RNN正按共同v6复核，保留阻抗原伺服力矩控制律；同场景调参预算另行预登记。
首批539项证据已核验共享至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_initial_20261002_141136/evidence/`。
稳定仿真不重启，全部失败保留；本轮尚未完成最终比较、纯ESN通过、formal或泛化验证。

### 2026-10-02 固定综合环境MLP/RNN替换ESN对照

两套既有VMC数据×MLP/Elman RNN×两个训练seed，固定128宽、2400更新、相同数据和训练序列。
8条完整55秒开发回合task/strict均0，环境/规划/WBC/gate/执行器未变。原VMC组MLP/RNN平均
RMSE39.060/29.307mm、峰矩38.470/38.933Nm、峰速.404145/.386349m/s；均卡carry。
恢复41组RNN没有稳定改善，seed2甚至停approach；MLP seed2最终XY59.899mm仍未放置。
原VMC MLP seed2外穿透.205319mm超限。所有失败保留，不把离线MSE改善或早期卡住的低指标算成功。
128宽不等于参数相等；RNN循环权重确实学习，历史ESN只作训练机制不同的同数据参考。
8物理/动作/状态/接触审计、4组数据曝光核验及2条完整三视角视频完成；680项证据已核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/mlp_rnn_replacement_20261002_131535/evidence/`。
无运行中任务；稳定放置、成功teacher、formal和泛化未完成。baseline分支/作业未改动。
见[完整报告](MLP_RNN_REPLACEMENT_REPORT_20261002.md)。

### 2026-10-02 四小时固定综合环境VMC/纯ESN研究

预登记48条teacher/名义候选、24条纯ESN回合全部55秒完成，task/strict均0；是开发候选
搜索，不是72次独立成功率统计。环境/MJB/规划/WBC/gate/执行器不变。原VMC蒸馏ESN
30.058mm/39.210Nm/.370185m/s、穿透.111707mm，仍卡carry；推进最远学生integral41
76.718mm/38.129Nm/.398990m/s、最终XY76.918mm，仍没有放置。
多时间尺度、context调制记忆、反事实DAgger与积分action损失未解决历史残差释放。
13个有效训练模型与1个拒绝部署的标签错误模型保存，24回合包含后续校准/记忆消融。
所有原始失败、三指标/动作/储备池/公共filter/幅值与伺服变化率审计保存；33条另有独立
接触sidecar，6条外穿透超限，不能只报低RMSE。两条完整原速三机位视频明确标为失败。
详情及服务器核验状态见[本轮报告](VMC_ESN_FOUR_HOUR_REPORT_20261002.md)。
已完成物理/训练/审计；无新物理派发。未完成成功teacher数据、ESN放置/strict、formal与泛化。
本轮没有MLP新评估；128储备池另加128非线性读出，不声称与历史MLP参数/FLOP精确匹配。
baseline独立分支/服务器作业未修改，其他独立FLASK场景不纳入本轮对比。

### 2026-10-02 当前综合环境和三机位交接

新增[office-tool-contact-v5交接](OFFICE_TOOL_CONTACT_HANDOFF_20261002.md)，包括完整环境
几何/固定时序、公共规划/判定、三机位参数、原速视频/慢放区别、服务器轨迹/资产/hash和
跨机器复跑入口。本轮无新训练或物理改动，baseline独立分支和作业未动。后续综合对比
共用该显式版本，不能与旧office分数混算；当前ESN仍未通过完整放置和strict。
已完成共享交接；本任务无运行中仿真；VMC新数据/ESN学习、正式与泛化验证未完成。

### 2026-10-02 球/棍末端接触独立修正

按用户新要求登记tool-contact-v5：正面球撞掌部、棍抬高/改朝向/缩短，固定保持到23.5秒。
ESN权重不变；同模型球零初速对照得到13.845mm额外偏移，棍只推hand、不碰物块或人体，
在撤回前有4.06秒脱离受力接触，但后续回碰。完整放置/安全仍失败，不能作为ESN优势。
本轮只动main独立入口，不影响baseline正在跑的四特化场景或旧office环境默认设置。
后续综合对比须共同采用新物理参数/时序，详见[交接与失败](TOOL_CONTACT_REPAIR_20261002.md)。

### 2026-10-02 独立未知凸边环境及公平对照

新增规划地图遗漏的物理凸边，并统一修复路径让位后的接回逻辑；未改baseline分支或
其现有训练环境。新场景使用同一目标、路线、放置/安全阈值和旧ESN/MLP权重进行开发验证。
名义清场成功，名义阻塞失败；ESN/MLP均在新凸边接触之前停滞，因此没有学习柔顺优越性证据。
两轮8条原始轨迹保留，v2四组重跑及动作/状态/子步/完整视频审计已完成，无运行中仿真。
后续baseline必须显式接入同一新场景和v2参考跟随规则，不能和旧office任务混算成功率。
环境尺寸、门槛、两种旧权重seed、三指标和服务器地址见[交接报告](UNEXPECTED_EDGE_CONTACT_TASK_20261002.md)。

### 2026-10-02 用户新定义的桌角规划任务

新planned-hand-corner-v1采用静态路径/姿态规划，目标[.690,-.310,.545]m，成功看松手稳定放置，
接触覆盖另报。零动作名义执行成功（XY10.8mm），原ESN停carry；不能声称ESN优势。
两条55秒开发轨迹与审计/媒体已共享，无baseline训练或分支修改；未来比较必须共用
新目标、规划参考、释放逻辑和评分，不混旧任务结果。见[baseline接入](PLANNED_HAND_CORNER_TASK_20261002.md)。

### 2026-10-02 新顺序时序ESN单回合

同原p=.1权重、推杆12秒启动，55秒开发回合完成，task/strict=false，仍停载荷转移。
RMSE38.708mm/峰矩48.463Nm/峰速.094228m/s，穿透.122975mm；推杆及柱子有效接触缺失。
原始动作/储备池重放误差0、物理子步审计通过；全程媒体生成完毕。
本轮无新训练或baseline评估，不与旧7秒时序作同条件排名。见[报告](ESN_SEQUENTIAL_R12_REPLAY_20261002.md)。

### 2026-10-02 共用顺序扰动协议

用户授权将推杆起点移到12秒，人手10秒计划撤回结束后留2秒恢复；其余环境和gate不变。
所有方法可复用冻结权重/参数，无需重训，但必须在同一新协议下重新评估。
新旧时序结果分开；本轮仅通过参数防错/驱动时序/80ms物理回归，不是完整任务成功验证。
baseline分支尚未接入；共享源码和配置已归档服务器，见[交接文档](OFFICE_SEQUENTIAL_R12_HANDOFF_20261002.md)。

### 2026-10-01 记忆消融和同预算dropout诊断

逐次清空ESN历史停align，低RMSE/峰矩不代表任务改善。相同数据、seed、160epochs、
1120更新的p=0/.1训练中，ESN从lift推进至load_transfer但仍失败：三指标从
48.971mm/43.600Nm/.116950m/s变为44.666mm/47.458Nm/.094228m/s；MLP两组均完成
放置（p=.1为46.587mm/44.587Nm/.073259m/s），所有strict失败。五条物理/重放审计通过，
p=0权重和轨迹逐字节复现。固定128维整段mask在两模型表示上语义不同，不声称严格等价
结构消融、ESN优势或泛化成功。报告ESN_MEMORY_DROPOUT_DIAGNOSTIC_20261001.md。

另纠正时间预算：自动化创建+8小时与唤醒截止不一致，先前把16:20当计算截止有误；
晚期诊断单列，不能冒称原八小时内完成。已完成现有回合并暂停heartbeat，无新派发，
继续研究需明确新预算；原始失败及历史执行记录保留。

### 2026-10-01 seed52 在冻结MuJoCo3.11.0复核

两条55s/dt1e-4复核完成，模型hash与旧冻结场景完全一致，真实MemoryMax≤3GiB且串行。
ESN任务失败、strict失败，48.971mm/43.600Nm/.116950m/s；MLP任务成功、strict失败，
46.908mm/45.907Nm/.070165m/s。原3.14.0的ESN RMSE72.223mm存在运行时影响，但两版本
任务结论一致，不能宣称已修复ESN。新旧四条独立动作/状态/物理审计通过。
ESN末10秒停在约28.9mm误差且速度很低，未见输入截断/储备池饱和；离线记忆清空显著
改变输出，但不等于闭环成功。后续针对历史与读出偏置，仍保持纯ESN与公平MLP预算。
完整结果与限制见[冻结复核报告](ESN_MLP_FROZEN_RUNTIME_PAIR_20261001.md)；formal未解锁。

### 2026-10-01 temporal seed52 与完整性纠正

seed52 复现 ESN task/strict 均失败，RMSE 72.223 mm、峰矩 44.403 Nm、峰速
0.125044 m/s；MLP task=true、strict=false，46.980 mm / 45.918 Nm / 0.070165 m/s。
与窄屏合计六条，ESN task 0/3、MLP 3/3，strict 都为0；不能建立ESN优势。
六条 checkpoint/MJB 元数据、有限值、动作/储备池精确重放和550000子步指标重算通过。

本轮证实 MuJoCo 版本偏移：最近模型3.14.0，旧冻结模型3.11.0，MJB互不兼容。
同版本配对可保留，跨版本不能当作仅算法变化的对比；后续回到冻结3.11.0并显式记录运行时。
恢复seed42配置，另存seed52配置；缺失 execution.json 和历史资源限制证据如实注明，
不把训练后提交称作预提交注册。本轮无新仿真，不改scene/gate，也不合并baseline分支。
详见 [完整性审计](ESN_MLP_TEMPORAL_INTEGRITY_20261001.md)；strict与正式评估仍未完成。

### 2026-10-01 temporal-consistency narrow follow-up

在同一锁定 teacher manifest、combined-v4、原 gate 和 canonical48D/action7
协议下，预注册 `delta_weight=0.25/0.75` 的相邻 action 增量损失窄屏。四条
开发回合均完成 55 s/550000 子步：ESN task 为 `0/2`，MLP task 为 `2/2`，但
strict 均为 `0/2`。`delta=0.25` ESN 的 RMSE/峰矩/峰速/穿透为
`52.502 mm/45.556 Nm/0.117007 m/s/0.146245 mm`，推杆最长连续接触
`0.7673 s`，仍未放置；`delta=0.75` ESN 停在 carry。两条 MLP 均完成放置，
但一条缺柱子接触覆盖，另一条球反弹失败。独立 action/储备池/物理子步审计
通过，正式 `dt=5e-5` 仍未解锁；结果不支持 ESN 优势。报告见
`ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md`，原始回合仅本地待同步。

### 2026-10-01 temporal-consistency candidate replication

对首轮 `delta_weight=1.0` ESN 候选用第二 seed 复现后，ESN 仅到 carry、RMSE 257.986 mm、task/strict 均失败；MLP 完成 task 但 strict 失败。两条独立物理子步审计通过，说明首轮 ESN 到 load_transfer 的结果不具备稳健性；没有 formal `dt=5e-5`。

### 2026-10-01 temporal-consistency ESN/MLP screen

只在冻结 teacher bank 和 combined-v4 上改变训练目标，加入相邻 action 增量损失，候选 `delta_weight=0/0.5/1.0`。ESN 三组均未完成 task；`delta_weight=1.0` 到达 load_transfer，RMSE 40.378 mm，但没有 placement。MLP 两组完成 task，strict 仍为0/3，required contact coverage 不足。六条 action/储备池/物理子步审计通过，全部为开发 `dt=1e-4`，formal `dt=5e-5` 未解锁。完整表见 [`ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md`](ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md)；大产物目前仅本地待同步。

### 2026-10-01 low-scale ESN/MLP weight-decay screen

在锁定 teacher bank、canonical48D/action7、7/2 identity split 和 frozen office-v5 combined-v4 上，只改变 ESN/MLP 训练的 AdamW weight decay（`1e-5/1e-4/1e-3`），并固定 ESN 输入尺度 `0.25`。三组开发回合均为 `dt=1e-4`、55 s、550000 物理子步；ESN 三组均在 lift 停止（task/strict=0/3、0/3），MLP 三组均完成 task 但 strict=0/3，失败原因是 required contact coverage 不足。六条 action/储备池/物理子步审计通过，报告见 [`ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md`](ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md)。formal `dt=5e-5` 未解锁，结果不支持 ESN 优势；原始失败回合保留，产物目前仅本地待同步。

### 2026-10-01 低输入尺度 ESN output-gain 屏幕

在同一低输入尺度 ESN checkpoint 上只改变输出增益 `.80/.90/.95`。冻结环境、gate、纯
本体输入和执行器限制不变；三条都是开发 `dt=1e-4`、55 s/550000 子步，task/strict 均为
否：`.80` lift（`60.590/37.618/.1031/.1257`），`.90` carry
（`144.782/37.867/.1395/.1705`），`.95` lift（`73.919/37.051/.1019/.1150`），
顺序为 RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm。柱子覆盖均失败，独立 replay 与物理
子步审计通过；没有 formal `dt=5e-5`。详见
[`ESN_LOW_SCALE_GAIN_SCREEN_20261001.md`](ESN_LOW_SCALE_GAIN_SCREEN_20261001.md)。

### 2026-10-01 低输入尺度 ESN alpha 屏幕

在先前唯一一次 `input_scale=0.25` ESN task-success checkpoint 上，只改变 action-readout
平滑 `alpha=0.25/0.50/0.75`。同一 combined-v4、原 gate、纯 canonical48D 输入和执行器
限制下，三条开发回合均为 55 s/550000 子步、`dt=1e-4`，task/strict 全部为 false：
alpha .25 停在 lift（`68.485 mm / 35.127 Nm / .1010 m/s / .1423 mm`），.50 停在
carry（`138.424 / 39.585 / .1275 / .1373`），.75 停在 lift（`59.341 / 37.282 /
.1041 / .1101`）。.50 推杆接触最长 `.6642 s`，但柱子覆盖仍失败；.75 球反弹也失败。
三条独立 action/储备池/物理子步审计通过，原始回合保留在
`outputs/esn_low_scale_alpha_screen_20261001_v1/`，没有候选解锁 formal `dt=5e-5`。详见
[`ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md`](ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md)。

### 2026-10-01 fixed-reservoir ESN decomposition

固定 input-scale=0.25 和同一个 reservoir，仅改变读出 seed，ESN task success 为 0/3、strict 为 0/3；MLP 为 3/3 task、0/3 strict。结果表明单 seed ESN 成功不能归因于稳定的 reservoir 或读出机制，仍没有 formal `dt=5e-5`。

### 2026-10-01 ESN input-scale 屏幕与复现

输入尺度 0.25 的单个 ESN seed 完成 task，但 strict=false；预注册的三个新 seed 复现为 0/3 task success，说明单 seed 成功不具备泛化证据。其余输入尺度 ESN 也未过 task/strict。动作、储备池和物理子步审计通过，所有结果为开发 `dt=1e-4`，没有 formal `dt=5e-5`。

### 2026-10-01 ESN recurrent spectral-radius screen

第二轮纯 ESN 算法屏幕只改变 128 单元 reservoir 谱半径 `0.60/0.90/1.10`，并为每组训练同宽度 MLP 对照。三组 ESN 均未过 task/strict，MLP 只有谱半径 0.90 对照完成 task、strict=false；所有回合仍是开发 `dt=1e-4`。独立动作/储备池/物理子步审计通过，0.90 ESN 穿透超限被保留为失败；没有 formal `dt=5e-5`。产物目前仅本地，待 arm1 与 GitHub 网络恢复后同步。

## 2026-10-01 pure ESN output-gain screen

固定 v4 ESN checkpoint 仅筛选 `output_gain=0.80/0.90/0.95`，环境、gate、
canonical48D actor 输入、执行器限制和 MLP 均未改。三条 combined-v4 开发回合均为
55 s/550000 子步、`dt=1e-4`，结果为：0.80 停在 carry，RMSE/峰矩/峰速
`520.286/41.950/0.1879`、穿透 `0.1688 mm`；0.90 停在 lift，
`407.785/46.242/0.2134`、穿透 `0.1350 mm`；0.95 停在 lift，
`454.745/44.605/0.2160`、穿透 `0.1243 mm`。task/strict 全部 false，均未完成放置。
独立 action/储备池重放最大误差均为 0，550000 子步审计通过，因此没有 formal `dt=5e-5`
重跑。失败回合和 checkpoint 保留在本机
`code/mujoco_6d_vmc_benchmark/outputs/esn_gain_screen_20261001_v1/`，并已核验归档到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_gain_screen_20261001_v1/`。
文件收据 SHA256=`6ed5e73204de983d481200bcf5082a50e1259fbd55a281934aa33e7460dcff74`，源码快照
`source/7fa6a6e39459cf846f21400c7f5fa5d4301da1ca/repository.tar` SHA256=
`1a79dd2583859e38ce785d2cd96bfb5efd1b0a2af436c4565224123c92277015`。

## 2026-10-01 paired ESN/MLP seed screen

锁定 manifest 上的 seed `106/107/108` 成对训练结果：MLP 三组均 task=true、strict=false；
ESN 三组均 task=false，最终阶段分别为 lift、load_transfer、lift。ESN/MLP 的
`RMSE/峰矩/峰速/穿透` 分别为 `874.772/55.664/0.1639/0.1089` 与
`52.402/44.708/0.0730/0.1772`（106），`187.222/47.666/0.1601/0.1612` 与
`33.860/44.542/0.0707/0.1530`（107），`37.743/38.843/0.0721/0.1714` 与
`43.083/45.083/0.0724/0.1843`（108）。全部为开发 `dt=1e-4`、55 s/550000 子步，
独立 action/状态/物理审计通过；无 strict 通过，因此没有 formal `dt=5e-5`。seed=108
说明 ESN 可达到低误差状态但仍未完成 placement gate，不能写成 task success。
三组完整原始证据已核验归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_mlp_seed_screen_20261001_v1/`，
evidence tar SHA256=`12ebe6d9529df5dd0bc967a45ed7a5ac77d1d0e4774d8fe10203ac5f158e5aa8`；提交
`9888f6cc361004a70a24851e7915062ca5962a5f` 的源码快照 SHA256=
`36563d9b960253ba1ec4a71ac3a4a1fea3966aa9afbdfe4727ad271e5ee9c589`。

## 2026-10-01 ESN action-readout alpha 屏幕

在不改环境、gate、actor 输入、执行器限制或 MLP 的前提下，预注册测试 ESN 输出平滑
`alpha=0.25/0.50/0.75`。三条同一 frozen office-v5、55 s/550000 子步开发回合均
task/strict=false：alpha 0.25 为 lift、RMSE/峰矩/峰速 `367.725 mm/50.319 Nm/0.2420 m/s`、
穿透 `0.6467 mm`；0.50 为 lift、`411.708/36.347/0.2306`、`0.1787 mm`；0.75 为 carry、
`95.040/41.629/0.0848`、`0.1276 mm`。三条动作/储备池重放及独立子步审计通过，
但没有可晋级的 ESN 候选，也不解锁正式 `dt=5e-5`。原始回合、checkpoint 和审计均保留，
计划及归档路径见联合进度与 ESN/MLP 报告；38 文件已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_alpha_screen_20261001_v1/`。

## 2026-10-01 v3 teacher-label correction and ESN/MLP rerun

为保证后续 baseline 对比使用真正的过滤后 teacher action，修正训练 loader 为读取
`execution_chain.npz/filtered_action`，并对 rollout 与 execution chain 双 hash 校验；
原始 `applied_action` 仍保存用于审计。该修正没有改变当前九条轨迹数值（最大差
`8.9e-16`），但关闭了过滤器未来生效时的语义漏洞。新增测试通过，训练 metadata 也固定
ESN/MLP 推理源码 hash。

v3 在冻结 combined-v4、无初始细步、`dt=1e-4`、55 s/550000 子步下完成 ESN/MLP 闭环：
VMC teacher 为 task/strict `true/false`，RMSE/峰矩/峰速 `43.438 mm/50.324 Nm/0.1008 m/s`；
ESN 为 `false/false`，停在 carry，`406.806 mm/43.246 Nm/0.2404 m/s`，穿透 `0.1929 mm`；
MLP 为 `true/false`，放置完成，`43.333 mm/44.405 Nm/0.0753 m/s`，穿透 `0.1012 mm`。
学生动作回放为 0，ESN 储备池回放为 0，独立三项物理子步审计通过。严格 gate 未通过，
不解锁 `dt=5e-5`；v3、首轮细步诊断和失败记录均保留。完整路径和 checkpoint hash 见
`docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`；本轮 v3/v4 已另行同步并核验到 arm1 的
v3_v4 新目录（详见下段）。

随后完成无负载权重控制 v4（seed `2026100105`，emphasis=0），仍是同一 frozen command、
55 s/550000 子步。ESN 为 task/strict `false/false`，停在 lift，RMSE/峰矩/峰速
`526.818 mm/44.416 Nm/0.2204 m/s`，穿透 `0.1323 mm`；MLP 为 `true/false`，放置完成，
`38.832 mm/44.286 Nm/0.0807 m/s`，穿透 `0.1527 mm`。v4 动作/储备池重放与物理子步审计
通过。v3/v4 的共同结论是 MLP 在当前 teacher bank 上较稳定地完成 task，而 ESN 闭环在
lift/carry 失稳；两者均未过 strict，仍不做正式步长或泛化成功声明。v3/v4 已归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`，
68 个文件的相对路径 SHA256 收据为 `ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`。

## 2026-10-01 VMC teacher → ESN/MLP 加权读出续实验

在冻结的 office-v5 综合场景上，对 VMC teacher 标签训练的纯 ESN 与 MLP
进行了同预算加权读出续实验。唯一改动是训练阶段对估计力/负载本体通道使用
平滑样本权重；actor 输入、环境、执行器限制和 gate 均未改。weighted MLP
完成任务并将柱接触延长到 `0.6056 s`，但 strict 仍失败；weighted ESN 在
lift 阶段失败。结果表和审计入口见
[VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md](VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md)。
这轮仍是开发 `dt=1e-4`，没有满足 strict，故没有 formal `dt=5e-5` 结论。

2026-09-30 13:55 UTC终态：十小时派发窗口已结束，无截止后新回合，服务rc0退出。
162搜索＋27验证记账＋26collection，共212动态/3初态拒绝。追加collection三方法共同8个
完整训练fixture：VMC/导纳/阻抗录取5/8、0/8、5/8；RMSE均值40.176/41.389/29.608mm，
回合峰矩均值45.003/47.230/46.813Nm，峰速均值.076558/.068184/.158803m/s。最后持续
0002仅VMC/导纳完成，两条原始结果保留但不混入公平配对均值；这些是训练结果非验证。
26raw审计全通过，9重复对全同；严格teacher唯一4/4/1，共9。无新ESN，未达1000合格/类。
详情、原独立验证和失败边界见[十小时交接](TEACHER_BANK_TEN_HOUR_REPORT_20260930.md)。

2026-09-30 13:01 UTC：锁参验证全部27条目记账（24动态＋3同场景初态拒绝），独立raw
审计通过、无漏项。8个有效fixture上VMC/导纳/阻抗录取3/8、0/8、4/8，task7/8、0/8、7/8，
strict4/8、0/8、6/8；另一个预注册场景无有效动态，不可省略。持续推碰均未录取，不能
称已泛化。失败均进入完整55s配对指标表，见[验证报告](TEACHER_BANK_LOCKED_VALIDATION_20260930.md)。
1850文件审计/比较/全动态点图已核验至服务器runs/main/teacher_bank_review_checkpoint_20260930_1300/evidence/。
collection已开始，重复搜索anchor不增唯一数，原截止不变；无新ESN。

2026-09-30 12:47 UTC：验证棍推0001初态与机械臂交叉最大60.09884mm，三方法均保留拒绝，
不作为动态控制失败、不替换验证条件。独立continuation v2复用21已完成验证后接续，
冻结源/参数/原截止不变；无新ESN。严格标签出口只含train锁参轨迹，目前唯一数2/3/1，
validation和重复均不能扩充训练数。相关70测试通过。v1零派发资源检查失败与v2协议均
核验归档，CPUQuota请求未实际生效的边界已更正；MemoryMax3GiB/Swap0/单线程有效。
服务器证据及新运行入口见[三类记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)，
几何静态诊断见[初态拒绝核查](TEACHER_BANK_VALIDATION_INITIAL_REJECTION_20260930.md)。

2026-09-30 11:44 UTC：全部162搜索完成，27录取/135未录取；九组参数独立认证锁定。
选定参数训练录取厚角VMC/导纳/阻抗2/3、0/3、2/3，短撞3/3、1/3、2/3，持续1/3、0/3、0/3。
持续阻抗task/strict为2/3但接触曝光不足，不能称完全不会任务；三项指标亦无VMC全面优势。
预注册27验证正运行，未调参回流；仍缺每类1000有效示范与新ESN。人推raw复算/图和27BO
前缀检查49文件已核验归档于服务器runs/main/teacher_bank_review_checkpoint_20260930_1138/evidence/；
锁参/公平表/全162搜索图1609文件已核验至teacher_bank_review_checkpoint_20260930_1150/evidence/。
详细同参数task/strict/录取及三指标见[锁参比较](TEACHER_BANK_LOCKED_SEARCH_20260930.md)。

2026-09-30 11:31 UTC：持续VMC c05首次人手条件录取，同候选棍/推板仍失败，共1/3；
独立raw复核进行中，尚非跨条件结论。短撞c05阻抗2/3而VMC/导纳0/3，说明应保留全部
候选结果，不能只展示proposed有利结果。最后经典组继续，bank未锁定、validation/collection
尚无结果。定义覆盖/短撞c05原因诊断等56文件已核验共享于服务器runs/main/
teacher_bank_review_checkpoint_20260930_1124/evidence/。有效字段投影3300唯一，不冒称动态
验证完成；[c05报告](TEACHER_BANK_VMC_C05_DIAGNOSTIC_20260930.md)将多参关联与因果分开。

2026-09-30 11:10 UTC：五候选135回合完整，23录取/112失败。厚角VMC/导纳/阻抗4/15、
0/15、7/15，短撞9/15、2/15、1/15，持续推碰均0/15（搜索计数，不是固定策略成功率）。
c05运行；bank未锁定，验证/collection/新ESN仍未开始。新公平展示工具将任务/strict/曝光/
录取分列，三方法完整同长且全部指标证据齐全才进入共同指标集，11项测试通过。
完整资产审计纠正FR3漏清单；133文件已共享，本机冻结source静态9/9复现原MJB，但
XML-only0/9、ARM首例亦不一致，后两者保留失败；Spark动态补充阻断，不影响原本机
同模型配对。证据112文件已核验至服务器runs/main/teacher_bank_review_checkpoint_20260930_1104/evidence/，
详见[资产更正](TEACHER_BANK_ASSET_REPRODUCTION_CORRECTION_20260930.md)。未改环境/gate或重启v10。

2026-09-30 09:40 UTC：c00–c03公平前缀108回合，17录取/91失败、归档全齐。短撞VMC c03
为单参数3/3，原c00为2/3；导纳c03为1/3，阻抗c03为0/3。持续推碰仍三方法均0/12。
不能用训练候选结果声称独立泛化。六条短撞配对的三指标/动作与源hash复核通过；球形条件
电机峰矩降低但接触峰力升至2221N，穿透0.18863mm（此列仅元数据核验），见
[短撞c03报告](TEACHER_BANK_SHORT_C03_REVIEW_20260930.md)。审计及终态工具/验收964文件已核验
至服务器runs/main/teacher_bank_review_checkpoint_20260930_0913/evidence/；工具11测试通过。
参数银行仍暂定，c04继续、collection=0、未做新ESN；未改变环境、gate或同预算要求。

2026-09-30 08:40 UTC：初始三个候选81回合全部完成，10录取/71失败。厚角VMC/导纳/阻抗
为2/9、0/9、4/9；短撞3/9、0/9、1/9；持续推碰均0/9。这是跨参数搜索统计，非锁定策略
成功率。BO已启动；首个VMC厚角BO候选1/3，未超过c01的2/3。独立汇总与同实现参数重放
一致，未读validation轨迹；参数仍暂定、collection=0、无新ESN。81点图/复核及hash证据
已核验共享至服务器runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/，
见[首次BO复核](TEACHER_BANK_FIRST_BO_REVIEW_20260930.md)。没有改门槛/模型或扩大搜索预算。

2026-09-30 07:35 UTC：前两个初始候选完整54回合、8录取/46失败，c02继续运行。
VMC厚角已有2个、短撞3个唯一合格搜索fixture，但后者跨不同参数，非单控制器3/3；持续推碰
仍0，collection和新ESN仍0。新增公平三指标图，保留失败/共同完整预算并绑定audit SHA，
5项校验通过、PNG视觉检查通过，支持服务器路径映射。状态/源码/图表的已核验共享路径见
[三类记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)。这是训练搜索，不是独立验证。

2026-09-30 06:32 UTC：首个完整c00预算27条全部归档，5录取/22失败；持续推碰VMC/导纳/阻抗
均0/3，已进c01。人推独立重建证实VMC同段持续1.2516s、让位9.09595mm，导纳宏观约27mm
被接触间断分段，仍未通过原筛选；见[人推复核](TEACHER_BANK_PERSON_ANCHOR_REVIEW_20260930.md)。
新证据38文件已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
搜索未完成、参数未锁定、collection和新ESN仍0，以下为较早检查点。

2026-09-30 06:18 UTC：v10首轮c00厚角三方法录取VMC0/3、导纳0/3、阻抗2/3；短撞为2/3、0/3、1/3。
是相同模型/相同anchor数量的训练搜索比较，非锁定参数验证。VMC两条短撞hash与独立子步指标复核通过，
但接触峰力1368/1350 N，阻抗成功短撞峰力2077 N；需与电机峰矩分开解释，不代表真实部署安全。
目前21条搜索完成、另1条导纳持续推碰运行；collection=0，各类1000条有效teacher、新ESN和正式验证未完成。
新增只读状态工具展示接触载荷/细分失败，19项测试通过；没有改冻结源码、环境、gate或评分。
本轮状态与源码已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0621/evidence/`。
两条VMC复核详见[审计报告](TEACHER_BANK_V10_FIRST_SEARCH_SUCCESS_AUDIT_20260930.md)。下列早期数量为历史记录。

2026-09-30 新任务：VMC既作为teacher生成器也作为model-based baseline；导纳/真实力矩
阻抗同场景同搜索预算调参。3000训练＋300验证配置已生成，不等于有效数据已采满。
截至05:29 UTC，v6六条主动pilot及v8九条三类别pilot已完成；后者仅阻抗一个训练fixture通过，
RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s，有大量接触分段，未证明平顺泛化。
VMC合格新轨迹仍0。v10固定预算搜索正在本机运行（单环境/1线程/3GiB），73项测试通过。
人手曝光方向/时窗、成功anchor优先排序、实际资产及跨候选模型hash、观察/曝光时间关联已修。
先前非法初态和任务失败全部保留，阻抗旧raw独立复审已归档，servo到实际力矩误差0。
旧corner通过不证明上抬碰face，详见曝光诊断。
冻结综合测试与门槛未改，无新ESN结果。
源码和配置已核验共享到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/`。
详见 [三类teacher与经典baseline](TEACHER_BANK_THREE_DOMAINS_20260930.md)。
05:49 UTC首个厚桌角c00配对（三方法各三anchor）完成，VMC/导纳/阻抗录取分别0/3、0/3、2/3；
这是训练搜索结果，不是锁定参数独立验证。v8九条pilot的hash/子步指标复核通过，区分球撞
后段放置失败、慢收敛和人推接触分段；详见[失败机制报告](TEACHER_BANK_PILOT_FAILURE_CAUSES_20260930.md)。
该新报告、JSON和源码已核验共享在
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`。

2026-09-30 更新：按用户要求先修正 teacher，再重做 ESN。归档 MuJoCo 3.11 上首轮
八条回合已审计：三个 teacher 修正均通过 corner task/strict，综合 pair_average
task=true、strict=false（穿透 0.187935 mm，柱接触不足）。公共 baseline 环境、gate、
执行器和原 teacher 源码不变。第二轮也已完成：velocity025_stiff2 的 corner task/strict
通过，综合 task/strict=1/0，峰矩 48.127 Nm、峰速 0.070574 m/s、穿透 0.144922 mm，
放置阶段动作差分 RMS 相比原版降低约 86.3%，但柱接触仍缺失。共 12 条有效回合
已完成独立审计，当前无本任务仿真运行；特化全协议回归未完成，未做新 ESN 蒸馏。
另保留了误用 MuJoCo 3.14 的四条版本诊断，未混入正式结论，已加入解释器和模型预检。
完整指标、负结果及恢复入口见 [teacher 修正](TEACHER_REPAIR_20260930.md)。

**当前研究状态：VMC teacher＋ESN 联合优化已恢复，目标未完成。** 用户明确
允许优化 teacher 和学生；当前办公室分支使用默认 teacher，此前“无具体
软件路线”的判断过早，已撤回。新目标及八回合固定预算 J1 teacher 筛查见
[联合优化计划](ESN_VMC_JOINT_OBJECTIVE_20260927.md)。保留R34任务6/6、严格3/6，
不改物理/门槛、不解封保留布局；物理标定不是继续软件研究的前提。

**新一轮实际结果**：J1 四类 teacher × 两条件已完成，task8/8、strict4/8，
全部原始轨迹及三指标独立审计通过。刚度候选在强球撞相对 R34 峰矩下降约
4.5%、峰速下降4.4%，waypoint误差增加约1.6%，首撞安全仍未通过，不能写成
全面优于 ESN。J2 动作单位对齐及 J3 剩余开发条件验证正在运行。详情见
[联合优化首轮报告](ESN_VMC_JOINT_PROGRESS_20260927.md)。

**可汇报证据已补齐**：[当前完整目标核验与动图入口](ESN_OFFICE_CURRENT_EVIDENCE_20260927.md)
包含首撞慢放、完整抓放回放和未通过项目。慢放仅从原R34状态重建，无新增
物理运行；穿透峰值与原记录一致，明确标注55ms球撞/80ms首个非零观测及
task成功/strict失败。目标仍未完成，保留条件仍未运行，继续联合软件优化。

**9月27日首撞机理的后续核验**：九准备构型/26表面方向筛查仍选原姿态；
三条短时理想驱动力诊断及一条只读克隆状态审计均完成。即使接触后瞬时
施加最大分离力矩（不可部署、违反slew的诊断），穿透仍.207375mm。
约104/191um接触状态下，62.4m/s²自由加速度增量经耦合约束仅余.00044m/s²，
主要改变接触力。原始仿真逐数组parity和独立状态重建均通过。这解释局部
不敏感，不证明参数错误或所有纯本体方案不可能成功；没有改世界或门槛。
详见[表面惯量及驱动力审计](ESN_OFFICE_SURFACE_AUTHORITY_20260927.md)。
[共同接触模型独立标定](ESN_CONTACT_CALIBRATION_PROPOSAL_20260927.md)仅为待决定
的研究范围提案，未实施；不能为了ESN过线调材料。当前无运行中仿真。

**9月27日本体估计校准试验已完成并拒绝采用**：四条55s及全部原始数据已
收齐复核。scale .005→.001后，ESN原始/强球撞均从任务成功退化到卸载失败，
zero两条仍成功；同轨迹影子对照显示ESN卸载估计误差增大，位置误差始终
未进入12mm条件。默认参数和R34保持不变，未改门槛或增加感知。
见[负载估计因果审计及失败解释](ESN_OFFICE_OBSERVER_AUDIT_20260927.md)。
随后完成ESN恒定负载固定点核验和一次闭式读出校正：静态插值误差降低约53%，
原动态验证误差增约.37%，保持储备池/非线性权重和零负载/分轴性质。R36六条件
闭环回归已全部结束并审计：任务6/6、严格3/6，均与R34相同；四条阶段误差
略降但两条上升，五条最终放置误差增大。六回合平均阶段误差146.960→146.940mm，
逐回合峰值力矩均值38.598→38.815Nm、峰值速度均值.133857→.134103m/s。
没有确认整体收益，R36不替代R34，首撞安全未解决，当前无运行中仿真。见
[固定点校正协议与结果](ESN_OFFICE_EQUILIBRIUM_20260927.md)。

**首撞的架构边界已核验**：四条强球撞对照前80ms共51,200个物理子步记录
逐元素相等。球接触55.06–55.51ms结束，ESN首个非零wrench观测在80ms。
所以固定当前世界/初态/名义控制器、继续只改零负载输出为0的力驱动读出，
不能改变该首次峰值。这是当前架构的条件性结论，不是“所有纯本体方法都不行”。
不放宽.2mm门槛、不加感知，也不由现有仿真宣称可在真实机器人安全部署。

**9月27日R35数据聚合回归已完成**：同储备池、同输出增益的读出重训，六例
task6/6、strict3/6，未改善R34的安全和覆盖缺口，不替代R34。五例全程阶段
目标RMSE略降，但四例最终放置误差增大，合成验证误差也增加约5.6%。
所有退步、一次跨CPU复现校验失败及修正训练均保留，原始数据和策略重放
独立审计通过，见[R35完整报告](ESN_OFFICE_R35_AGGREGATION_20260927.md)。

**最新研究边界：用户明确要求纯本体感知。** 不增加预碰撞感知，旧“等待
感知授权”问题已关闭。仍缺强球撞安全通过、充分接触及保留条件验证；
继续原范围内诊断，见[用户决定](ESN_PROPRIO_ONLY_DECISION_20260927.md)。
此前[完整验收与阻塞复核](ESN_OFFICE_COMPLETION_AUDIT_20260927.md)作为历史保留。

**9月27日闭环记忆消融已完成**：三个开发条件上，R34保留记忆任务3/3，
每次清空储备池1/3，零残差3/3。清空后两例卸载阶段失败，支持当前模型依赖
历史进行恢复，但不证明ESN超过重新训练的前馈模型或名义WBC。强球撞穿透
仍均0.207370mm；严格验收差异还受推杆接触不足影响。五条新增、四条复用
全部已归档，九条物理指标和策略轨迹已核验。见[记忆消融报告](ESN_OFFICE_MEMORY_ABLATION_20260927.md)。

**9月27日后续更新，以此为当前状态**：R34在实际有人手推压和球撞的office-v5
六个开发压力条件任务6/6、严格综合3/6。三例完全通过；两例推杆接触不足；
强球撞完成任务且推杆接触0.799秒，但穿透0.207370mm越过0.2mm。全部数据
已归档并独立复算，动作重放误差<1e-15。见[六条件报告与动图](ESN_OFFICE_R34_FINAL_20260927.md)。
这是共同细积分精度下的开发结果，不替代下文50us历史，也不是盲测或硬件
安全结论。R34为同储备池输出统一乘0.5，闭环记忆的独立收益尚待消融。
作业全部结束；用户已否决感知范围扩展，该分支未实施。

**9月27日 proposed 专项更新**：实际有人手推压、球撞、推杆、杯子、柱子和
厚桌角的 office-v5 中，新 R33 ESN 在三个预先声明的开发场景任务 **3/3**，
均完成真实抓放和撤离；严格综合门槛 **0/3**，不能称为已安全通过。三例
物理子步 RMSE 为 152.523 / 145.576 / 135.643 mm，峰值力矩
39.808 / 38.132 / 42.336 Nm，峰值速度 .14589 / .11185 / .11249 m/s。
全量数值、失败原因、参数/源码/模型 hash 和动图见
[办公室修复报告](ESN_OFFICE_RECOVERY_20260927.md)。三个保留场景未运行。
旧 R30 在无主动扰动时也失败，问题不只是球撞或早期脉冲；修正包括零负载
平衡、分轴多时间尺度储备池和 VMC 非线性读出蒸馏。原始办公室零残差 WBC
与六维 VMC 也完成任务，不能写成“baseline 都不行、只有 ESN 可以”。
尚待解决较强球撞首次冲击的安全门槛和足够的推杆接触覆盖；以下 baseline
表属于原来各自声明的基准，不与这三例办公室开发结果混成同一验证集。

运行状态见 [持续推进记录](CONTINUOUS_BASELINE_PROGRESS_20260923.md)，失败机制见 [动作振荡因果诊断](ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md)。第一表为已审计的六条件物理子步结果，早期三条件开发结果保留在末尾。各阶段的完整数值与hash见对应链接的独立JSON；本周报同名JSON仍是早期三条件/25Hz开发快照，未代表下面的更新结果。

**9月25日最新状态**：三训练seed PPO的六条件部署和 SAC13 六条件物理部署均已结束、完整保留并独立复算。SAC13 plan SHA`125505dc0c07894c8c9d85bb04afd96d29bacc9a8a6927ab17bd68769bf3413a`，13/13 完成、0 execution error，zero7/9400 parity 通过；服务器原始目录395文件约854MiB，已取回本地并通过rsync checksum dry-run。逐条50 μs raw结果见[SAC13报告](evidence/canonical48_sac_20260925/SAC13_RESULTS_20260925.md)，JSON SHA`2dd33c0abf39346799afda68394b773d3970bd1d82e3e6abb3f52f11ac2c1db6`。两支 SAC 各为 seed20260923 的 final8192/8092：online_only 六条 task/gate=0/6，waypoint RMSE 213.387 mm、峰矩63.088 N·m、峰速0.507779 m/s；demo_prefill 六条 task/gate=0/6，192.529 mm、58.604 N·m、0.470170 m/s。demo均值较低不是成功证据，六条均停stage1，online多停stage0/1；不跨阶段比较 endpoint，不以低RMSE替代抬升、接触和 gate。

**SAC失败的已证实线索与边界**：从两份独立审计中仅提取`train/episode_*`完整回合（排除四条eval及392步partial），两支各13条训练回合task/gate均0/13，终端基础奖励全部为0。在现有潜势奖励定义下，完整折扣环境return均约0.06666666067，即`−初始潜势`；不同失败行为在这个完整环境return上没有排名。该恒等式不表示逐步学习信号或梯度为零，SAC还优化熵项，也不能单独证明奖励导致失败。demo分支确实采样到成功示范：2,071,552次replay抽样中388,385次取自预填600条示范（允许重复抽样，不是独立数据量），所以不是示范未入buffer；它仍未在8192次在线交互内形成成功闭环。未据此改reward、挑checkpoint或追加有利训练。

## 已完成：固定预算后的六条件验证

28条测量/消融、48条经典参数开发搜索、30条共同验证全部结束，无执行错误。106条原始数据已完整归档到本机，并通过服务器/本机只读checksum核对。48+30条已完成独立选择、任务/gate、原始子步峰值与误差、时间轴、配对MJB及134份冻结脚本/协议/模型hash复核；完整16候选与30验证失败分解见[固定预算最终报告](CLASSICAL_FIXED_BUDGET_VALIDATION_20260923.md)，[逐回合汇总](evidence/classical_20260923/fixed_budget/validation_final.json)保留全部失败。

| 方法 | task /6 | 完整gate /6 | 子步位置RMSE mm | 实际关节力矩峰值 Nm | 子步末端速度峰值 m/s |
|---|---:|---:|---:|---:|---:|
| 阻抗 K900、ζ1.2 | 6 | 1 | 67.646 | 35.545 | 0.12222 |
| 导纳 K150、ζ0.7 | 5 | 1 | 141.417 | 35.909 | 0.08000 |
| VMC（旧fixture固定参数） | 5 | 1 | 148.125 | 36.759 | 0.11960 |
| MLP | 5 | 0 | 132.937 | 36.600 | 0.14527 |
| Proposed ESN | 1 | 0 | 160.204 | 36.464 | 0.14577 |
| PPO8192（单fixture训练） | 0 | 0 | 179.069 | 51.572 | 0.32708 |
| zero action7（消融对照） | 0 | 0 | 209.466 | 31.827 | 0.08000 |
| PPO8192潜势奖励（全停stage1） | 0 | 0 | 19.976 | 31.739 | 0.13535 |
| PPO8192 parameter6（DGX配对训练） | 1 | 0 | 155.205 | 38.973 | 0.15037 |
| PPO8192 direct7（DGX配对训练） | 0 | 0 | 135.982 | 38.329 | 0.15610 |
| nominal_train_vmc（固定训练参数zero6） | 1 | 0 | 147.493 | 38.509 | 0.14887 |

**PPO三训练seed复验**（20260923/24/25，每seed同六fixture，均固定最终8192模型）：

| 模式 | 各seed任务成功 /6 | 各seed完整gate /6 | waypoint RMSE均值±SD mm | 峰矩均值±SD Nm | 峰速均值±SD m/s |
|---|---|---|---:|---:|---:|
| PPO parameter6 | 1、0、1 | 0、0、0 | 155.761 ± 9.310 | 38.952 ± 0.171 | 0.15262 ± 0.00825 |
| PPO direct7 | 0、0、0 | 0、0、0 | 136.941 ± 71.671 | 35.044 ± 2.323 | 0.10268 ± 0.04430 |

先在每seed内平均六条件，再计算三个均值的总体SD；这不是18次独立训练，也不为ESN单模型补造seed方差。[三seed完整结果及所有失败](PAIRED_MULTISEED_SIX_FIXTURE_RESULTS_20260925.md)的JSON SHA为`7d9fac8c9a8c77ff36995df86c91f356cc6333ae87c6c83706a380cc09382683`。新增24条策略与1条parity的582文件/1.71GB已完整归档，原始50µs指标复算及670输入/工具hash复核通过；原seed的12条策略与6条共享nominal复用已绑定审计。36条策略均完整24s，失败未剔除。

parameter6跨seed三项均值仍高于匹配nominal，未表现出稳定整体学习收益。direct7的seed24六条全部停stage1且不触杆，waypoint RMSE仅49.645mm、但末6秒共同最终目标RMSE222.284mm；seed25虽到stage3并触杆，六条物体抬升全部不足，末6秒目标RMSE252.696mm。原seed23该辅助误差为97.884mm，仍task全失败。因此较低的平均waypoint误差或峰速不能解释为更好完成任务；三个seed反映该小预算配方的行为差异，未证明RL算法已收敛或泛化。

这是预先固定的同layout六条件验证，不是office blind test或六个训练seed。全部失败回合计入均值；三维指标均使用50微秒物理子步，位置误差仍相对状态机waypoint。经典参数按开发集25Hz误差及物理峰值选定，未根据这六条件重新选择。导纳内部参考速度整形、阻抗力矩后端及有限各向同性K搜索的边界保留，不能称为完全等价控制架构或全局最优调参。新增PPO/zero与原30条在DGX同平台、同fixture MJB下配对，12条raw已复算；PPO只有单rod/8192互动步，而ESN/MLP使用多场景teacher imitation，不是等训练预算比较。zero是消融，不是经过学习的baseline。

当前结果明确不支持proposed整体优势：ESN任务仅1/6且完整gate为0/6。阻抗任务6/6也不代表最终验收完成，因为完整gate仅1/6。原24条的[物理子步三维对比与误差解释](SUBSTEP_THREE_METRIC_COMPARISON_20260923.md)和[七方法因果诊断](ESN_PANEL_CAUSAL_DIAGNOSIS_20260923.md)保留失败机制证据。

9月25日已补入[配对RL/训练名义VMC六条件18条结果与11方法附表](PAIRED_SIX_FIXTURE_RESULTS_20260924.md)。新18条全为24s且独立复算50µs raw；旧48条复用固定hash的已审计JSON，**不声称本次重新读取全部66条raw**。1,249,993,338 bytes、464个文件完整取回，服务器/本机checksum dry-run无差异，见[传输审计](evidence/paired_gym_20260924/six_fixture_transfer_audit.md)。两新RL同DGX、seed、8192互动步、PPO设置与potential reward，但6/7维输出、解析记忆/控制先验不同；旧dense/potential PPO在本机训练，六条件部署指标均来自DGX。

parameter6相对真正匹配的nominal_train_vmc没有显示整体学习收益：task同为1/6、strict同为0/6，成功条件由nominal的9402变成parameter6的9403；waypoint RMSE均值147.493→155.205mm、峰矩38.5095→38.9733Nm、峰速0.148874→0.150369m/s，三项均值均上升，不能称全条件改善。两者六条均进入stage3、均触杆；parameter6其余五条失败均含末10帧waypoint误差≥15mm，唯一task通过9403仍因杆峰穿透0.207742mm未过strict。nominal9402唯一task通过亦因0.209852mm穿透失败。原阈值未改。

新direct7六条都到stage3并触杆，不能与旧potential PPO全停stage1混称。前四条抓取抬升通过，但末10帧waypoint误差30.974–39.372mm，均未过15mm门；9404/9405物体仅抬升25.289/24.645mm，并持续触杆18.791/19.389s、最终未脱离。9400/9401又有接触时长不足0.3s的问题。与zero7相比，direct7在相同绝对(18,24]s窗口内的最终目标3D距离RMSE均值217.168→97.884mm、全程waypoint RMSE209.466→135.982mm，但task仍0/6且峰矩/峰速更高，不能称成功或安全性整体改善。这里两端均取末6秒150帧统计，不将旧zero末6秒RMSE与新direct7单一末帧距离98.545mm混比。

以共同最终手端目标`[0.54,0,0.785]m`作事后诊断：parameter6/direct7/nominal_train_vmc末帧距离均值为89.398/98.545/61.090mm；绝对(18,24]s共同末6秒150帧RMSE均值94.452/97.884/65.964mm。所有新方法都经过loaded-lift，但实际接触时长不同；这些辅助量不替换waypoint主指标，也不替代抓物、物体稳定及接触门。新18条任务与接触失败逐项保留在报告中。

新增[潜势PPO完整八方法表](PPO_POTENTIAL_DGX_RESULTS_20260924.md)已经同平台归档复算，170份源码hash、203个数值数组及7条原始子步数据通过审计。其19.976mm是停在stage1抓取对齐时相对当前waypoint的误差：六条都未闭爪/抬升，也未触发loaded-lift推杆。因此该低值不能解释为最好任务轨迹、合规或接触响应。任务、阶段和扰动实际曝光必须与三指标一起阅读，所有失败保留。

[八方法共同最终目标诊断](EIGHT_METHOD_FINAL_GOAL_EXPOSURE_20260924.md)进一步用已有最终目标`[0.54,0,0.785]m`、统一末6秒150个25Hz样本比较全部48条。末6秒共同目标3D距离RMSE的六条件均值：阻抗5.895mm、导纳28.919、VMC42.532、MLP37.943、ESN86.996、旧PPO74.531、zero217.168、潜势PPO263.756。这里对末6秒全部样本求RMSE，**不是单一末帧距离，也不替换全程waypoint主指标**。旧PPO虽距最终点比ESN近，却始终stage0、未抓物；潜势PPO六条位置轨迹完全相同，但始终stage1，手指持续碰桌面20.11s。两种PPO均未触杆，不能称完成了同等扰动恢复测试。原五方法都经历推杆，其中阻抗4/6接触不足0.3s；所有这些失败仍计入结果。246项输入/工具hash与原30条共同窗口数值复核通过。

[Canonical48 PPO640试验](CANONICAL48_RL_PILOT_20260923.md)和预声明的[8192步试验](CANONICAL48_PPO_8192_PROTOCOL_20260923.md)均已完整结束。8192最后模型在本机rod/front两条冻结评估均失败，且没有用中间checkpoint替换。新增[训练目标审计](PPO_TRAINING_OBJECTIVE_AUDIT_20260924.md)显示唯一训练成功回合的折扣reward却排最后，提示reward与任务门未完全对齐；这还不能归因全部退化。[DGX同平台12条完整结果](PPO_DGX_MATCHED_RESULTS_20260924.md)已补入上表，未拼接本机指标。PPO六条都停stage0，部分条件未触发loaded-lift推杆；较小穿透不能解释为更好的接触控制。

## ESN闭环状态覆盖审计（2026-09-25）

本轮只读回放未启动MuJoCo，也未修改checkpoint、safety filter或gate。冻结ESN及三类轨迹的完整输入、原始trace hash和结果保存在
`outputs/esn_dagger_causal_audit_20260925_r2/` 与
`outputs/esn_state_coverage_audit_20260925_r3/`。多轨迹readout checkpoint对物理轨迹动作重放误差为 `1.46e-16`（最大绝对误差 `9.16e-16`），因此不是loader/checkpoint mismatch。loaded-lift阶段slew replay比例为 adapted `76.95%`、frozen `82.71%`，无amplitude clipping；源码核对确认 `observation[39:45]` 是SixDVirtualDynamics使用的6D encoder wrench。

覆盖统计仅作解释，不用held-out选择模型。训练六条 / held-out六条 / 学生固定场景三条的 normalized feature RMS/p95/max 分别为 `1.1616/2.2608/16.5491`、`1.2481/2.3876/17.7513`、`1.6732/3.2289/18.4573`；reservoir state norm RMS/p95/max 分别为 `4.0185/4.9418/5.5450`、`4.2028/5.2225/6.2039`、`4.9492/6.1052/7.3301`。学生三条约 `2.52 s` 进入stage3，且不是三个独立随机几何。该结果支持“闭环分布/历史状态漂移”作为工作假设，但不构成因果证明或真实部署证据。下一步应是预声明的跨development fixture on-policy relabel迭代，再在未触碰validation上评估；不继续同场景beta/filter扫描，不宣称ESN已经能完成真实环境任务。

## 9月24–25日新增诊断与已完成实验

原经典106条及PPO8192训练均已结束并保留失败。新增固定教师历史12条已完整归档、独立复算，task/gate均0/12；不作为成功示范直接增广训练。[教师诊断](TEACHER_HISTORY_DIAGNOSTIC_20260924.md)区分了离线动作误差和真实闭环结果。

[接触余量诊断](CONTACT_MARGIN_HISTORY_DIAGNOSIS_20260924.md)确认30条最大外部穿透全部来自杆，22条越过0.2mm门的幅度为0.863–12.822μm。稀疏保存姿态缺少峰值时刻，不能据此判定为数值误差，所有原失败保留。共同末6秒、相同目标的辅助RMSE为阻抗5.895mm、导纳28.919、VMC42.532、MLP37.943、ESN86.996；这是事后解释，不覆盖冻结主表或选模规则。

**潜势奖励对照已完整结束**：[最终同平台报告（修订版）](PPO_POTENTIAL_FINAL_COMPARISON_20260924_REVISED.md)保留固定8192步/384updates最终模型。13完整训练回合及rod/front两个最终PPO评估都task/gate失败；新模型均停在stage1抓取对齐、尚未闭爪和抬升。外部单对象合力峰rod976.29→206.49N、front1138.24→373.28N，但约15mm终点误差只是相对当前阶段目标，不能判任务恢复；old front为stage0，前后也不是同一目标。两种zero各27原始数组逐值相同，9控制核心源/完整fixture/133资产hash一致。新基础奖励目标不同于旧密集reward，不能用reward数值增大判断优劣。[最终奖励审计](PPO_POTENTIAL_REWARD_AUDIT_20260924_FINAL.md)核对156冻结源及13完整回合恒等式；partial最后一项和实际SB3 reward buffer的审计限制保留。

**已完成**：潜势最终模型的[7条DGX同平台部署](PPO_POTENTIAL_DGX_RESULTS_20260924.md)已全部结束并完整归档458MiB，zero9400与原对照完整原始轨迹相等。600帧DGX CPU对原GPU动作parity通过，maxerr2.98e−7；未按本机失败改模型或挑checkpoint，新增六条同平台模型结果已补入上表。

**配对训练已完整结束**：[同平台RL调参/直接动作配对训练](RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md)两分支各完成固定8192互动步/384更新，没有选择中间checkpoint。parameter6输出六维K目标，经训练来源完整固定名义VMC映射为action7，验证时不使用验证teacher参数；direct7直接输出原动作。各13个完整训练回合及392步partial均审计：parameter6训练task/gate为7/13，direct7为0/13，不能以训练成功替代独立验证。两份[parameter6最终审计](evidence/paired_gym_20260924/parameter6_final_audit.md)、[direct7最终审计](evidence/paired_gym_20260924/direct7_final_audit.md)核验全部实际transition、最终四项eval、SB3 float32奖励及冻结源。CPU5/6、同CUDA、最多2个单线程物理worker的[启动记录](PAIRED_TRAINING_LAUNCH_20260924.md)保留为历史，不代表仍在运行。

**已完成的前置验收**：[两模式完整24s Gym验收](PAIRED_GYM_PARITY_RESULTS_20260924.md)及独立真实transition审计通过。各600条日志与执行动作精确对齐，163份源/134项资产及共同MJB核对通过；实际reward/VMC跨机重放差约1e−16。随后最终审计已覆盖真实8192步及partial末真实next、SB3实际float32 reward；未记录critic/advantages，不能称实际bootstrap值已核验。验收时整套172项测试通过。zero6名义VMC成功、zero7失败仅说明两种控制先验不同，不是RL收益；配对网络可训练参数量46477/46607，也不冒称完全相同函数类。

**六条件18条部署已完成并复算**：[冻结协议](RL_PAIRED_SIX_FIXTURE_DEPLOYMENT_PROTOCOL_20260924.md)中的parameter6/direct7/nominal_train_vmc均执行全部六条件，无执行错误、无安全短回合；全部task/strict失败均保留，未选择checkpoint、改reward或放宽gate。完整三指标按原50µs物理子步重算，没有把训练日志低频峰值混入主表。

执行driver及独立只读部署快照206项文件hash与5个入口导入检查通过；准备时整套201项测试通过，报告专用7项测试通过。当前工作区一项旧源码差异保留，部署从原训练快照单独复制，未覆盖用户改动。最终模型、全8192 transition审计及动作回放完成后才运行18条；报告核验计划/源码/协议/模型与逐fixture MJB、全部新raw数值及原task/panel/strict门，464项输入和工具hash保存在同名JSON。这里的464项审计hash与归档464个文件是不同计数口径。

**下一条动作RL的数据准备**：[train-only SAC/RLPD示范](TRAIN_ONLY_SAC_RLPD_DEMO_FEASIBILITY_20260924.md)已导出固定训练proof全部600步实际action7/reward/终止记录。r2与实际SB3动作缩放逐值相同，修正r1的float32运算顺序差异（最大5.96e−8）；旧版及失败证据保留，原行为、观测、奖励均未改。9项纯离线测试通过，未启动SAC/RLPD训练。该示范是额外600条训练数据，不能称与online-only同总数据预算，更不代表论文结果复现。

本机已进一步完成[真实SB3 ReplayBuffer离线验证](evidence/paired_gym_20260924/demo_r2_real_replay_verification.json)：r2全部600条插入真实buffer并覆盖全部索引采样，raw逐值一致，仅采样时归一化一次，reward不改；末done/timeout阻止placeholder bootstrap，合成归一化统计未改变。该验证为0仿真、0梯度更新，不是SAC/RLPD训练成绩。

**接触峰值证据已补齐**：[三组sidecar验证](CONTACT_SIDECAR_RESULTS_20260924.md)确认新增记录没有改变原轨迹，保存的完整峰时状态可复核原深度。VMC9403、MLP9400、ESN9403峰值分别0.199393/0.200863/0.212809mm；≥0.2mm持续分别0/0.25/1.00ms，均来自杆与link7、loaded-lift阶段。短瞬态解释低频姿态漏峰，但不是数值伪影证明或豁免理由，原严格失败保留。本组为事后机制诊断，不是新验证成绩。

**新增调参接口**：[RL→六维K/D→原VMC→action7](RL_VMC_PARAMETER_INTERFACE_20260924.md)已实现，8项离线测试与DGX两条24s闭环零参数parity通过：52个数值数组全有限，执行action/物理/接触逐值一致，MJB相同，两条均task/gate通过。原自动driver因接触集合列表顺序误报FAILED，标记原样保留，由独立finite/exact审计仅规范源码证明为set的字段解决。VMC是解析控制器，不是神经网络；该接口保留24维解析状态和原VMC slowdown规则，与direct PPO控制结构不同。真实调参训练及六条件部署现已完成，结果在主表；接口parity本身仍不代表学习收益或论文复现。

**运行中**：[多seed复验启动记录](PAIRED_MULTISEED_LAUNCH_20260925.md)。额外固定20260924/20260925，每个seed均运行parameter6/direct7各8192步，超参、reward、训练fixture和最终checkpoint规则不变。DGX持久队列549548已启动，首对549559/549560实查512/544步、各RSS约2.29GiB、系统可用112.23GiB，0执行错误；第二对在首对完整结束后自动运行，全队列最多2worker。原163执行源保持字节不变，新增source总199文件hash已独立核对。当前主表仍只有原训练seed20260923，不能把新seed运行中状态混入成绩。

**01:31心跳后更新**：新增4run中seed20260924两条已结束、完整归档checksum通过并完成全8192独立审计（[参数分支](evidence/paired_multiseed_20260924/seed20260924_parameter6_final.md)、[直接动作分支](evidence/paired_multiseed_20260924/seed20260924_direct7_final.md)）；各13完整回合+392步partial、384更新、finalzip显式seed均已核。参数训练成功4/13，但最终train/validation评估均失败、stage3、末端误差70.332/113.158mm；直接动作训练0/13，最终两评估均stage1，44.875/49.623mm只针对抓取对齐目标。两模式train/validation零对照全部raw/transition/MJB与原seed20260923精确一致，不因更换训练seed改变物理场景。当前seed20260925正在同一队列自动训练：parameter6 PID552706、direct7 PID552705；原首对PID已结束，勿重启。后续新增24条策略部署加1条nominal原始一致性复核正在准备，尚未启动，主三指标表仍不加入未经同场景部署的训练日志指标。

[训练行为修订诊断](PAIRED_TRAINING_BEHAVIOR_DIAGNOSIS_20260924_REVISED.md)发现parameter6训练探索85.828%步骤至少一轴触发变化速率限制，但确定性train/PPO为11.5%，zero为0%；三种范围K幅值均未触上/下界。该结果区分了探索噪声与确定性策略，并更正“未触幅值限制就没有限速”的推断；它是train-only相关性诊断，不说明应放宽限速或改gate。

**02:00接续更新（覆盖上方运行状态）**：新增4run已有3条完整归档、全8192独立审计和zero/MJB及CUDA600帧回放通过；最后seed20260925 parameter6已完成8192步/384更新，正在原队列四项自动评估，尚未取得最终COMPLETE。seed20260925 direct7最终train为stage0、validation为stage3，均task失败；末10帧当前目标误差55.733/24.173mm不能跨阶段解释为任务精度。此前direct7另外两个训练seed的最终train阶段为3/1，当前证据说明小预算配方对初始化/采样组合敏感，不能拆分为单一因果。新三seed六fixture主指标尚未形成，原单seed表不替换。

新增24条策略部署及1条nominal9400原轨迹复核的[协议](RL_PAIRED_MULTISEED_DEPLOYMENT_PROTOCOL_20260925.md)已固定并审查中，尚未物理启动。共享nominal六条只计一次；先每训练seed汇总六fixture，再描述三个seed均值的离散程度。主agent本轮整套237 tests通过，随后driver有界清理与报告source绑定修正的19项相关测试通过；这些工程验收不等于策略成绩。

**三训练seed最终评估现已完成**：[六run独立汇总](PAIRED_THREE_SEED_COMPARISON_20260925.md)及同名JSON（SHA256 `eec905398713208d024de84d90a322b48e5b1cd17bb45496ff7ff771aa21a3fb`）。追加4run的整个3.8GiB目录已归档、checksum无差异；合计6run均8192步/384更新并通过独立审计，24条最终train/validation × zero/PPO评估全部保留。parameter6最终train任务成功1/3、validation0/3；direct7两者均0/3。参数训练过程的完整回合成功数分别7/13、4/13、4/13，不能替代最终确定性成绩。该报告只覆盖原train/validation两条件，尚不是三训练seed的六fixture物理子步比较。上方“仍在训练/评估”的进度段保留为历史。

下一算法[标准SAC/direct7实施方案](CANONICAL48_SAC_DIRECT7_PROPOSAL_20260925.md)已审查通过，正在独立实现与无物理测试；尚未SAC训练。online-only与固定600条示范预填分别有8192/8792条可用训练transition，预计各8092次SAC更新，实际次数须核验；与PPO在线预算相同但不等网络/计算预算，也不称RLPD复现。

**新增25条部署已实际启动**：服务器输出`outputs/paired_multiseed_six_fixture_20260925_r1`、持久driver PID565765，plan SHA`c094ca89faa946e156843aa366592b43bc943f07c89f932c990d6273c6a5f467`。四run完整审计/zero/600帧CUDA回放及342输入、173执行源hash通过后启动，最多2worker；先1条nominal轨迹parity，再24条策略评估。旧三seed训练队列已结束，上方“部署未启动”段为历史；当前不能提前把这些部署填进结果表。

**标准SAC两条对照也已实际启动**：DGX `outputs/canonical48_sac_20260925_r1`，supervisor569894，online_only Python569896、demo_prefill Python569898；每支固定8192在线步，示范额外0/600，标准uniform replay，不称RLPD。201项独立source、同平台零物理preflight与具体plan通过审核，PLAN SHA`2a47e065b2fd8055ec67624a56e0942347e3d7a428f065d131803bdc284f4734`。当前2训练+2部署合计4物理worker；真实初始模型/101步前缀正在核对，尚无SAC最终成绩。先前“尚未SAC训练”描述保留为准备历史。

**后续完成状态**：25/25 PPO部署已正常结束、0执行错误，完整归档及独立raw报告处理中。两SAC已完成8192在线/8092更新并进入原固定最终eval；实际初始网络/alpha/RMS和前101条交互均已exact核验，首次更新同在第101步后。8个周期checkpoint的真实seed/步数/updates及三optimizer计数均通过，不选择中间模型。SAC未来六fixture子步部署仍仅为13job准备方案，尚未启动；本表未加入任何未审计的新分数。

**尚未完成（以此项为准）**：SAC两final策略的六fixture物理子步对比、更充分多条件RL训练、真正RLPD训练/论文级复现、可靠教师补集和冻结后的office blind test。三seed PPO六fixture结果与标准SAC两支训练已完成，不再列为待做。当前报告不能作为proposed优于baseline的证据。

### 两个固定VMC对照为何必须分开

旧`vmc`为六验证fixture原有的固定teacher参数；`nominal_train_vmc`取配对训练manifest中的完整固定训练options，从reset起zero6，六验证条件不换成验证teacher参数。两者都是解析VMC，task分别5/6与1/6，**并非同一baseline重复跑出的差距，也不是RL造成的差距**。`parameter6`只应与后者比较学习增益。九组options不同，两组限幅相同；下表按`x,y,z,rx,ry,rz`顺序，数值仅为便于阅读而四舍五入，实际未改原精度。

| options | 固定训练nominal（zero6的基准） | 旧fixture VMC |
|---|---|---|
| stiffness_6d | [826.3543,103.9524,996.1328,7.6702,23.5867,31.4543] | [520,360,1400,12,10,14] |
| damping_6d | [28.2869,17.7144,52.0863,5.4517,3.2764,3.7912] | [32,27,62,3,2.7,3.3] |
| mass_6d | [0.54260,0.52366,0.58401,0.04427,0.06200,0.09067] | [0.5,0.5,0.8,0.06,0.06,0.08] |
| wrench_limit_6d | [25.8201,42.9247,58.8397,4.2425,3.5675,3.5674] | [35,35,50,3,3,3] |
| deadband_6d | [0.14585,0.11381,0.16248,0.02501,0.02014,0.03598] | [0.2,0.2,0.2,0.03,0.03,0.03] |
| velocity_limit_6d | [0.09760,0.11732,0.13412,0.49528,0.60876,1] | [0.12,0.12,0.16,0.55,0.55,0.65] |
| offset_limit_6d（相同） | [0.18,0.18,0.18,0.35,0.35,0.35] | 同左 |
| action_limit_6d（相同） | [0.16,0.16,0.2,0.6,0.6,0.6] | 同左 |
| offset_tracking_gain_6d | 1.00878829 | 1.4 |
| filter_tau s | 0.01306344 | 0.04 |
| axis_rotation_rpy rad | [-0.00870393,0.02061078,-0.21182689] | [0.35,0,-0.25] |

来源为[训练manifest](../outputs/paired_parameter_action_20260924_r1_archive/training/parameter6/manifest.json)的`nominal_options`（文件SHA256 `6c0ead5219eefd0e1a1381117b7c0afef08d6dd4752b587803fd28d2fe6a0a9c`）与[冻结部署plan](../outputs/paired_six_fixture_validation_20260924_r1_archive/frozen_plan.json)的`jobs[*].environment.CORE_VMC_CONFIG`。18条plan中该fixture控制器配置完全相同，且每条指向旧VMC已审计结果hash；新部署metadata的nominal options与训练manifest完整相等。filter/axis/限幅及offset tracking共同影响yield响应，不能只以K/D名称把两个配置当作等价。参数RL在训练nominal上改变K，并令D按`D0*sqrt(K/K0)`联动；其余options保持该训练来源。

## 原三条件开发结果（历史保留）

已完成当前 48D 模型与传统控制器的配对开发实验，并针对经典控制器接口问题完成独立修正对照。以下是开发结果，不是已充分调优或未见测试集上的论文排名。所有完整回合（包括任务/物理失败）保留在数值中；执行错误不填零分。

| 方法/版本 | 执行完成 | 任务通过 | panel gate | 位置 RMSE (mm) | 峰值力矩 (N·m) | 峰值速度 (m/s) |
|---|---:|---:|---:|---:|---:|---:|
| vmc | 3/3 | 3/3 | 1/3 | 136.841 | 35.758 | 0.1227 |
| impedance | 3/3 | 3/3 | 0/3 | 18.887 | 87.000 | 1.6557 |
| admittance | 3/3 | 2/3 | 1/3 | 137.220 | 39.611 | 0.1390 |
| mlp | 3/3 | 2/3 | 1/3 | 133.875 | 36.733 | 0.1458 |
| esn | 3/3 | 1/3 | 1/3 | 148.566 | 36.806 | 0.1437 |
| impedance_reference (initial_reference_r1) | 3/3 | 0/3 | 0/3 | 105.478 | 33.469 | 0.1137 |
| admittance_reference (initial_reference_r1) | 0/3 | 不适用（执行错误） | 不适用（执行错误） | 执行失败，无指标 | 执行失败，无指标 | 执行失败，无指标 |
| impedance_reference (K900) | 3/3 | 3/3 | 0/3 | 66.010 | 34.854 | 0.1230 |
| admittance_reference (snapshot_r2) | 3/3 | 2/3 | 1/3 | 125.911 | 35.488 | 0.0800 |

表中为三个物理条件的回合均值；峰值列是“先计算每回合峰值，再求均值”。标准差和最坏值保存在同名 JSON。

## 当前判断与版本说明

本轮不能支持 proposed ESN 的整体优势。修正版导纳的三项均值均低于 ESN，但两者完整 panel gate 都仅通过 1/3；低误差、低峰值不能替代接触与任务完成。K900 阻抗虽然任务通过 3/3，仍未通过完整 panel gate。

原 impedance 直接追踪跳变 waypoint，绕过速度参考整形且没有有效杆接触，仅作接口失配诊断，不参与正式排名。原 admittance 为 velocity-only 接口。initial_reference_r1 中阻抗为 K300，导纳为 K95（执行错误）；K900 为独立阻抗候选，snapshot_r2 为保持 K95 的导纳快照修正版。

## 公平性与指标定义

- 三个条件为 seed 9300/9301/9302，联动改变角度、推杆高度、物块质量。所有完整对照均为 24 s、48D 本体观测协议、相同任务/几何/solver；原 impedance 的参考接口差异见上文，不冒充等价实现。
- 新版本协议的 base_protocol_sha256 必须与原 48D 协议相同；此工具拒绝改时长、改条件或缺少配对记录的修正版。编译模型 MJB 按条件逐字节一致的证据另行保存。
- 位置 RMSE 相对当前状态机 waypoint，包含抬升阶段，不是相同绝对时间轴的规划轨迹误差。各控制器到达阶段的时刻可不同。
- 力矩为 4 ms 控制更新的 applied command 峰值；速度为 25 Hz 末端线速度采样峰值，可能漏掉子步瞬态。不能声称已测得物理连续时间的真实峰值。
- panel gate 包含任务、真实杆接触、脱离/间隙、0.2 mm 穿透门和无上游误碰，不等同于最终办公室稳定放置门。所有方法使用原门槛，未因结果放宽。
- 直接力矩阻抗复用 torque box/slew，但替换了速度伺服；其内部执行结构与 ESN/MLP/VMC 的 action7 分支不同，必须作为控制器家族对照解释。
- 参数修正和 K300/K900 候选只属于开发阶段；不能把开发集选出的最好参数当作无偏测试结果。当前单个冻结模型的三个评估条件也不等于三次独立训练。

## 已完成核验

- 全套 105 项测试通过；120 个原始捕获源码的导出一致性及语法检查通过。
- 原五方法 15 条、K900 阻抗 3 条与 r2 导纳 3 条原始 trace 已独立复算位置 RMSE 和 25 Hz 峰值速度；r2 每条包含 600 个有限数值样本。审计文件位于 docs/evidence/classical_20260923/ 下。
- 两份 server_model_metadata*.json 共记录 29 份 MJB 哈希（含 smoke）；非 smoke 的每个条件下，9 个方法/版本的编译模型哈希一致。冻结 checkpoint 与 teacher split 的来源已单独核验。
- 本轮服务器实验已结束，原始结果、错误日志、协议与隔离源码快照均保留；没有遗留的后台训练或仿真。

## 诊断与证据入口

- [经典控制器最终开发记录与失败原因](REFERENCE_CLASSICAL_DEVELOPMENT_20260923.md)
- [原五方法矩阵、阶段 RMSE 与原始 trace 复算](PANEL_MATCHED48_COMPARISON_20260923.md)
- [当前 ESN/MLP checkpoint、teacher split 与哈希](CANONICAL_MODEL_PROVENANCE_20260923.md)
- [阻抗积分平衡点修正](IMPEDANCE_MOVING_REFERENCE_20260923.md)
- [导纳位姿参考修正及快照时序问题](ADMITTANCE_REFERENCE_VARIANT_20260923.md)
- [历史 120 条结果审计：不纳入当前论文主表](FAIR_METHOD_COMPARISON_20260923.md)
- [四类 primitive 的早期经典 baseline 诊断](CLASSICAL_BASELINES_20260923.md)
- [RL 调参的三篇文献](RL_PARAMETER_LITERATURE_20260923.md)；[RL 直接动作的三篇文献](RL_ACTION_LITERATURE_20260923.md)
- [已有本机 PPO/SAC 工程预实验](RL_AND_BASELINE_PROGRESS_20260923.md)：legacy 输入协议，仅证明训练链可运行，不加入本表。

## 仍需完成的论文验收

修正接口后的传统控制器已完成本轮有限固定预算调参与独立验证，统一物理子步速度/实际 actuator torque 及阶段误差已审计，但各方法完整gate仍未达到可靠水平。后续正式矩阵仍需更多物理条件和训练seed；RL的48D/action7 pilot已完成接口迁移，仍需更充分训练与共同评估。全部参数/模型冻结后才能做新的office blind test，不能从本轮开发或同layout验证表推出proposed的整体优势。

## 机器可读结果来源

```json
[
  {
    "label": "base",
    "result": "docs/evidence/classical_20260923/panel48_final.json",
    "protocol": "docs/evidence/classical_20260923/panel48_protocol.json",
    "result_sha256": "69041c2a6a94799a90aa7caa1a37af947d524990bbc54d60051541dade8c5d43",
    "protocol_sha256": "b56ae7784c442a4568bec703869106cff69636d381d6e3432b0732707ec86991"
  },
  {
    "label": "initial_reference_r1",
    "result": "docs/evidence/classical_20260923/reference48_final.json",
    "protocol": "docs/evidence/classical_20260923/reference48_protocol.json",
    "result_sha256": "c8c3280b04d7ba04991f38bc82f33373540b14c4d726405b4815d88cd3811bb7",
    "protocol_sha256": "34d141d6f50cd289eaf714bf6fc32775735b7baa73654db8761b83113e0c31c6"
  },
  {
    "label": "K900",
    "result": "docs/evidence/classical_20260923/reference_k900/FINAL_RESULT.json",
    "protocol": "docs/evidence/classical_20260923/reference_k900/protocol.json",
    "result_sha256": "af07f74167d3592376efb8c955031343c0e5927a0c7cfbbf290b05086ec3b8cd",
    "protocol_sha256": "1c2fcc981da800626627526f8967131197532a483b9beca3edc87d2d7a1ce971"
  },
  {
    "label": "snapshot_r2",
    "result": "docs/evidence/classical_20260923/reference_r2/FINAL_RESULT.json",
    "protocol": "docs/evidence/classical_20260923/reference_r2/protocol.json",
    "result_sha256": "ec0cbf3a77ed40e4b88d216e1300c22e0040f9dea1cb942d38bf90274e9a285d",
    "protocol_sha256": "8115ad9fe1c82f6563674a87b9966d1a0f56d44e9649bce4abc63679c2fececc"
  }
]
```

## 2026-09-27 ESN/VMC 联合优化追加记录

本周后续 office-v5 联合实验已完成 J2 action-unit 对齐 teacher 的六条件开发
复核。修复 wrapper/batch 参数转发后，`j2full4_*` 六回合均完成物理积分；
独立重放和物理子步指标审计见
`outputs/esn_office_joint_teacher_j2_full4_20260927/J2FULL4_AUDIT.json`。
结果为 task 6/6、strict 3/6（original、rod-start7、rod-hold6 通过；
rod-start9 接触 0 s、shifted-plus 接触 0.184 s、hard 穿透 0.207370 mm 失败）。
J2 未达到 stiff teacher 的 strict 4/6，因此按预先冻结规则没有以 J2 轨迹训练
新增主 ESN；既有 wrench1 仍为最佳开发候选（task 6/6、strict 4/6）。

此前 j2full2/j2full3 的参数错误退出和全部失败日志均保留、不计性能；没有
修改安全门、扰动、held-out 封存或纯本体输入约束。当前没有可据此宣称的
held-out 或真实机器人结果，后续主线转回 teacher/共同执行接口在受扰动状态
下的覆盖研究。

## Wrench 权重 6 消融（2026-09-28）

在最佳 wrench1 ESN 上将 actor-visible wrench-norm 固定权重从 3 提高到 6，
保持 canonical48D/action7、reservoir、seed、物理和 gate 不变。独立审计结果
为 task 6/6、strict 3/6；hard 外部穿透 0.207528 mm，仍超过 0.2 mm，
因此不采用该候选、不解封 held-out，也不继续无依据的同类权重扫掠。结果与
checkpoint/source/轨迹哈希保存在
`outputs/esn_office_joint_esn_stiff_wrench6_eval_20260927/eval_v1/`。

## Wrench1 记忆因果消融（2026-09-28）

固定最佳 wrench1 checkpoint，只在每个观测前清零 reservoir；兼容性修复仅允许
stateful canonical48D ESN，旧 45D policy 仍拒绝。六条件独立审计得到 task 3/6、
strict 0/6，而连续记忆 wrench1 为 task 6/6、strict 4/6。动作/状态 replay、
物理子步 RMSE、峰矩和峰速均通过，结果保存在
`outputs/esn_office_joint_esn_stiff_wrench_memory_reset2_eval_20260927/eval_v1/`。
这支持 reservoir 历史对跨条件任务完成有因果贡献，但不解决 hard 穿透/曝光，
也不构成 held-out 或真实硬件结论。

## canonical48D 字段来源与 sensors-only 消融（2026-09-28）

新增只读输入来源审计 `outputs/esn_office_input_provenance_audit_20260928/`，明确
当前 48D 是“纯本体接口 + WBC/任务内部参考”，不是只含原始传感器；接触真值、
球状态、事件时间、阶段、视觉和距离仍未进入 actor。匹配 teacher/DAgger2 数据、
128 单元 reservoir、wrench 权重 3 和执行器预算，重新训练仅保留 q/dq/估计负载/
wrench 的 mask ESN，六开发条件 task6/6、strict3/6，低于 full48 wrench1 的
strict4/6；hard 穿透 0.207805 mm、shifted-plus 推杆接触 0.129 s。动作/状态
重放和三项物理指标审计通过。该结果支持在论文中区分“无外部感知”与“只含原始
传感器”，不改变 gate 或 held-out 封存。

## wrench1 动作执行链审计（2026-09-28）

只读重放已将 ESN 原始 action7、共同执行接口过滤后的 WBC slowdown/yield 和物理
子步 actuator torque 分开归档：六开发回合无幅值饱和，完整回合变化率限制占比
最高 0.4%。shifted-plus 推杆接触分层中过滤后 yield 与请求完全一致，而 raw
action 峰值仅约 0.040，因此剩余曝光失败主要指向访问状态/读出响应，而不是接口
截断。hard 球撞后的首个 25 Hz 响应虽受 slew 限制，但首次亚毫秒冲击已结束；
不能以调大变化率限制作为该安全峰值的证据性修复。审计见
`outputs/esn_office_action_execution_chain_v2_20260928/`，未运行 held-out。

## 交互展示与厚桌角放置（2026-09-28）

修复了 interaction-demo 的杯子初始重叠：旧位置被审计发现与物块手柄重叠
`13.5 mm`，失败回合已保留。新的低力交互几何在展示步长 `dt=1e-4` 下由 teacher
产生 `0.278 s / 56.6 N` 杯子接触；固定 medium4 ESN 产生累计 `3.436 s / 60.0 N`
接触，杯子位移分别 `1.879 mm` 和 `1.112 mm`。两者都停在 carry，展示条件的球
地面穿透为 `0.349 mm`，因此不计正式安全或任务通过。更靠近路线的 `1618.7 N`
候选被保留为失败并回退。

厚桌角的正式开发结果仍是 corner-only ESN blend-0.5：task/strict/release 均通过，
最大外部穿透 `0.001854 mm`。它与障碍交互展示分开报告，避免把未完成的组合场景
包装成成功。冲击慢动作新增只读末端位移三轴轨迹叠加，展示峰值末端速度
`0.058 m/s` 和约 `5.8 mm` 响应，未改变物理、actor、动作或 gate。交互和标注媒体
路径已写入联合进度文档；当前无运行作业。

### 2026-09-28 resumed ESN combined-scene audit

The reported `0.2970 mm` trial42 pair was FR3 right-finger geom 69 against the
added cup handle. A shorter/lower handle brought external penetration to
`0.1860 mm`; at its interaction length it still displaced the cup `16.40 mm` and
produced no pillar contact (trial44). A shorter `.060/.125` handle reduced
displacement to `8.66 mm` but removed the required cup interaction (trial45).
Restoring the interaction handle and moving the pillar to the retreat corridor
(`y=-.330`) produced trial46 with the same `0.1860 mm` penetration, `1.519 s /
8.88 N` cup contact, no pillar window, and no placement. Peak torque was
`51.75 Nm`, peak speed `0.07145 m/s`, and 3-D RMSE `0.05882 m`.

These `dt=1e-4` probes are diagnostic only. Raw requests, filtered/applied
actions, reservoir traces, source hashes, and failures remain archived; no gate,
actuator limit, input contract, or held-out condition changed. The separate
corner-only ESN success remains valid, while one episode satisfying cup brush,
pillar brush, and corner placement is still unfinished.

### Trial47 pillar-route diagnostic

The first trajectory-supported pillar placement (`[.585,-.300]`) generated a
real `6.8007 s / 116.81 N` pillar window but blocked the arm before release.
Task/strict were false, physical validity was false, penetration was `0.22898 mm`,
and there was no cup contact or corner placement. This retained failure rules out
placing the pillar directly in the current hand corridor; a post-release teacher
route is required. No gate, actor input, actuator limit, or formal step changed.

### Overnight campaign status

`tools/overnight_esn_combined_campaign_20260928.py` provides resumable,
single-worker execution with source/checkpoint hashes and retained raw failures.
Its first run found current-source combined-v4 failure (`0.26623 mm` penetration;
pillar contact `37.48 s / 125.16 N`; carry blocked) and current-source corner-only
failure at load transfer. The earlier targeted3 corner result is not reproducible
under the current source and is not promoted as current evidence. The delayed-ball
formal reference passed (`0.18855 mm`, `37.76 Nm`, `0.14243 m/s`, RMSE `0.00889 m`).
EGL rendering is intentionally separate from the 3 GiB physics run; no gate or
input contract changed.

### 2026-09-28 late resume audit

The bounded overnight runner was re-invoked after a process and lock check. It
found no active office evaluator and preserved all existing raw rollouts and
manifests; no duplicate physics run was started. Combined-v4 remains a
development failure (`task/strict=false`, final stage `carry`, `0.26623 mm`
penetration), so no formal combined result exists. The current-source
delayed-ball formal reference remains valid (`task/strict=true`, `0.18855 mm`
penetration); the current-source corner-only reference remains a failure at
`load_transfer`. Hashes and frozen contracts are unchanged.

### 2026-09-29 00:43 heartbeat audit

No evaluator or campaign process was active. The bounded runner reused all
existing manifests and raw rollouts without duplicate simulation. Combined-v4
remains a failed development case (`task/strict=false`, `carry`, `0.26623 mm`),
so there is still no formal combined result. The delayed-ball formal reference
remains valid at `0.18855 mm`; source/checkpoint hashes and frozen contracts are
unchanged.

### 2026-09-29 02:40 heartbeat audit

The process check found no active office evaluator. The bounded campaign reused
existing manifests and raw rollouts without duplicate physics work. Combined-v4
remains a failed development case (`task/strict=false`, `0.26623 mm`), so no
formal combined result exists. Delayed-ball remains valid at `0.18855 mm`; all
source/checkpoint hashes and frozen contracts are unchanged.

### 2026-09-29 direct combined-v4 transfer

The selected DAgger3 pure ESN was run once in the unchanged ball/person/rod/cup/
pillar/corner fixture. It failed task and strict at `carry`; pillar contact lasted
from `16.728 s` to the end (`23.896 s`). Independent replay was exact. RMSE was
`90.371 mm`, peak torque `42.324 Nm`, peak speed `0.070400 m/s`, and external
penetration `0.099829 mm`. The complete rollout and audit are retained. This
confirms that the six-condition ESN advantage does not yet establish success in
the final combined scene; no formal `dt=5e-5` result was unlocked.

### 2026-09-29 matched-budget readout follow-ups

The dual64 route/recovery readout and the damped-label impact-response readout
were each run on the unchanged six-condition development fixture. Both preserved
the pure canonical48D/action7 contract, 256 hidden/state-unit accounting, and
single-worker evaluation. Both independently reproduced actions and reservoir
states exactly and matched physical-substep metrics. Dual64 reached task `6/6`,
strict `3/6` with hard penetration `0.207867 mm`; impact-response also reached
task `6/6`, strict `3/6` with hard penetration `0.207172 mm`. Neither exceeded
DAgger3's `6/6` task, `4/6` strict result, so both are retained as negative
algorithm evidence and no formal or combined-v4 run was unlocked.

### 2026-09-29 matched-budget dual64 ESN audit

One additional pure-ESN readout organization was tested under the unchanged
six-condition development fixture: a shared 128-unit reservoir with separate
64-unit route and recovery heads, selected by the causal canonical-qvel
transient. Total hidden/state units remained 256, matching the MLP accounting.
The checkpoint is
`outputs/esn_office_joint_esn_dual64_20260929/model_dual64_v1/best.npz`
(SHA256 `ab9059fa35b11535939a1b4bd85f8d8861b46fce643371211ee7446565a42d3d`).
Independent action/state replay and physical-substep metric checks passed with
zero replay error. Closed-loop performance was task `6/6`, strict `3/6`, below
DAgger3's strict `4/6`; rod-start9 and shifted-plus remained strict failures and
hard penetration was `0.207867 mm`. It is therefore retained as a negative
algorithm result and was not promoted to combined-v4 or formal `dt=5e-5`.

### 2026-09-29 combined-exposure DAgger8

Adding one actual combined-v4 exposure trace and relabeling it with the same
stiff VMC improved the pure ESN trajectory but not task completion. The run
remained `carry`, task/strict false, with RMSE `53.364 mm`, peak torque
`44.899 Nm`, peak speed `0.068360 m/s`, penetration `0.091927 mm`, pillar contact
`22.189 s`, and cup shift `1.373 mm`. Action/state replay was exact. This is
retained as a negative recovery result; it does not unlock formal evaluation.

### 2026-09-29 ESN-only matched-budget update

The ESN comparison kept the baseline fixture, six development conditions, canonical48D
proprioceptive actor contract, action7 interface, gate, actuator limits and failure
retention unchanged. A matched 128-width MLP (`48-128-128-7`) reached task 5/6 and
strict 3/6. Exposure-balanced ESN reached task 6/6 and strict 3/6; DAgger3, trained
from its actual closed-loop visits and relabeled by the same stiff-VMC teacher using
only estimated proprioceptive wrench, reached task 6/6 and strict 4/6. Independent
action/reservoir replay plus physical substep recomputation passed with zero replay
error.

A pre-registered fail-focused DAgger4 oversampled only rod-start9 and shift-plus
DAgger3 visits. It regressed to task 5/6 and strict 3/6, with rod-start9 task failure
and hard penetration 0.208001 mm. It remains archived as a negative result and does
not replace DAgger3. Checkpoints, source/config hashes and all raw rollouts are under
`outputs/esn_office_joint_esn_stiff_20260929/`.

These are `dt=1e-4` development results. No formal `dt=5e-5` run, held-out release,
or real-robot claim is authorized because the six-condition strict gate is not fully
passed.

### 2026-09-29 teacher-response transfer follow-up

The remaining strict failures were traced to rod exposure duration under the unchanged
gate: DAgger3 had 0.2771 s (rod-start9) and 0.1206 s (shift-plus), while the stiff
teacher itself had 0.2886 s and 0.1431 s. The existing damped teacher (half action,
damping x2) improved rod-start9 to 0.7930 s and passed task/strict, but shift-plus
remained at 0.2383 s. Uniform teacher scales 0.4 and 0.6 were negative probes.

Three ESN transfer screens were audited with the same canonical48D/action7 contract and
256 hidden/state units: balanced DAgger5 (task 6/6, strict 3/6), raw damped-trace
DAgger6 (5/6, 3/6), and damped-label-on-DAgger3-visits DAgger7 (6/6, 3/6). All had
zero action/reservoir replay error and passed physical-substep recomputation. DAgger3
remains the selected ESN at 6/6 task and 4/6 strict; all follow-up failures and teacher
probes remain archived. No gate, environment, actor input or actuator limit changed.

### 2026-09-29 pure-ESN algorithm-only continuation

The ESN branch was continued without changing the combined-v4 environment, gates,
actor input, actuator limits or formal-step protocol. All new closed-loop runs used
`hybrid_vmc_blend=0`. A qvel-transient dual-readout ESN reached `0.06089 m` RMSE,
`0.16931 mm` external penetration, `46.18 Nm` peak torque and `0.10477 m/s` peak
speed at its best gain setting, but did not rebound the ball or complete placement.
Fixed-reservoir ridge and NumPy-MLP readouts distilled from retained same-fixture
applied-action traces also failed task completion; the MLP remained physically valid
with `0.19572 mm` penetration and cup validity true. A same-fixture VMC diagnostic
also failed (`0.27809 mm`, no rebound), so no pure ESN success claim is made. All
failures, malformed/aborted attempts, execution manifests and hashes are retained;
no formal `dt=5e-5` combined rerun was unlocked.

### 2026-09-29 01:38 heartbeat audit

No office evaluator was running. The bounded campaign reused existing manifests
and raw rollouts without duplicate simulation. Combined-v4 remains a failed
development case (`task/strict=false`, `0.26623 mm`), so no formal combined
result exists. The delayed-ball formal reference remains valid at `0.18855 mm`;
source/checkpoint hashes and frozen contracts are unchanged.

### 2026-09-29 new single-pillar / thick-corner development fixture

This is a separate opt-in development fixture, not the baseline world. Geometry
versions are now disambiguated by archived MJB/source hashes in
`docs/ESN_COMBINED_THICK_CORNER_PILLAR_AUDIT_20260929.md`. A pure-ESN old
4 mm-pillar run completed the task but failed strict safety at 0.943513 mm
external penetration; the current 2 mm-pillar run kept penetration to
0.125156 mm but stalled at load transfer with only 0.0264 s pillar contact.
Independent physical-substep metrics and exact action/reservoir replay were
checked for the task-completing run. Rod-motion bins and corner-stage audit do
not yet establish the requested continuous rod rub or lift-phase corner strike.
No combined success, formal `dt=5e-5` result, or fair baseline comparison is
claimed on this new fixture.

The separate v2 15 s probe is also a negative result: the translated corner
slab contacted the hand at `0.7306 s`, before grasp, and the pure ESN stalled
in `align`. Although external penetration was `0.063049 mm`, the payload
never reached lift/corner contact. Longest continuous rod contact was
`0.2371 s` with only `1.80 mm` planar hand movement. Raw artifacts and world
hash are documented in the combined-fixture audit; this probe is not a
full-horizon task or baseline comparison.

A third, separately flagged local corner-face/bridge short probe also failed:
bridge/robot contact began at `1.0963 s`, the ESN remained in `align`, and
no payload/lift-corner contact occurred. The larger v2/v3 pillar additionally
deflected the ball before it hit the robot, unlike the older v1 ball/link6
impact at `2.0939 s`. Consequently neither the low external penetration nor
the short-probe tracking metrics show robustness to the requested ball hit.
These fixtures are development failures, not new baseline conditions or
formal results; raw world hashes and failure details are in the combined audit.

The independently versioned v4 world received a complete 55 s pure-ESN
development run. It produced a ball/link6 rebound at `2.0939 s` and
force-bearing payload/thick-corner contact during lift (`0.2080 s`), but did
not place the block: final stage `load_transfer`, task/strict both false.
External penetration reached `0.394114 mm` at pillar/link6, exceeding the
unchanged `0.2 mm` limit; pillar exposure was only `0.0375 s` and the longest
continuous rod contact only `0.0349 s`. Independently recomputed substep
RMSE/torque/speed were `47.0526 mm / 58.0678 Nm / 0.272753 m/s`; all actions
and reservoir states replayed exactly. Raw failures and SHA256 provenance are
recorded in `docs/ESN_COMBINED_THICK_CORNER_PILLAR_AUDIT_20260929.md`. This
does not unlock a formal `dt=5e-5` rerun or a baseline comparison on v4.

A fixed pure-ESN output-gain 0.8 ablation on the identical v4 world reduced
penetration to `0.136818 mm`, RMSE to `43.1634 mm`, peak torque to `53.3077 Nm`
and peak speed to `0.096728 m/s`; independent replay/substep audit passed.
It still failed task/strict at `load_transfer` (best error `14.986 mm` versus
12 mm gate), had no pillar contact and did not establish continuous rod
rubbing. This remains a negative development result, not a selected formal
policy or a fair baseline comparison.

The 0.95 gain-only follow-up on the identical world lowered penetration to
`0.120669 mm` and the three physical metrics to `28.5777 mm / 39.3901 Nm /
0.083917 m/s`, but stayed in lift with no pillar/corner contact, best position
error `13.716 mm`, and only `0.0218 s` continuous rod contact. It is retained
as a negative pure-ESN screen; formal `dt=5e-5` remains locked.

The 0.98 gain-only screen stayed in lift with task/strict false/false. It had
`0.173824 mm` penetration, `32.2391 mm / 43.0499 Nm / 0.088481 m/s`
RMSE/peak-torque/peak-speed, ball rebound, only `0.0023 s` lift-corner contact,
no pillar contact, and `0.0361 s` longest continuous rod contact. Best lift
position error was `14.228 mm`; replay and substep audit passed. This remains a
negative development screen, not a formal result.
### 2026-10-01 ESN reservoir leak-time screen

本轮按固定 teacher manifest 和冻结 combined-v4 开发条件完成纯 ESN 时间尺度屏幕；唯一算法变量是 128 单元储备池 leak 时间常数，另配同宽度 MLP 对照。fast/baseline/slow ESN 均未过 task/strict（最终分别 lift/carry/lift），而 fast/baseline MLP 完成 task、strict 均失败，slow MLP 也未完成 task。所有回合均是 `dt=1e-4` 开发结果；动作与储备池 replay、550000 物理子步和三项指标独立审计通过。没有候选解锁 formal `dt=5e-5`，不能将本轮写成 ESN 泛化或 MLP/ESN 优势。产物目前仅本地，待 arm1 与 GitHub 网络恢复后同步。
## 2026-10-07 ESN-only torque/generalization follow-up

This ESN-only follow-up did not alter the baseline methods, office-v6 scene,
gate, actor inputs, actuator limits, or sealed final conditions. A fixed
128-unit reservoir with an anchored readout (`ridge=0.1,
smooth_weight=0.01, action_weight=0.0001, parent_trust=100`) was evaluated by
the same formal `dt=5e-5`, one-thread, 3 GiB worker. It passed task/strict on
3 of 5 registered development identities and failed on 2 of 5. Passing peak
torque was `49.663–49.909 Nm` versus the parent development anchor `49.981
Nm`; failures were retained. On development_002, the parent paired run
aborted at `2.602 mm` penetration while the candidate completed 55 s at
`0.174 mm` penetration but still missed placement, illustrating that a lower
contact burden does not imply task success. The candidate is not added to the
uniform baseline/main result table or promoted to a frozen model. Details,
hashes, and raw audit locations are in
`docs/ESN_TORQUE_GENERALIZATION_20261007.md`.

## 2026-10-08 新 office-v7 统一 24 条件评测（运行中）

新登记 16 方法 × 同 24 综合扰动条件 = 384 回合，覆盖 ESN、matched/ordinary RNN/MLP、
memoryless、经典 VMC/导纳/阻抗、RL 调三种参数、两种直接动作 RL、enhanced teacher 和 zero。
固定每个 family 的旧 uniform24 首模型，本轮不训练；正式 dt=5e-5、55 s、同 MJB 与 gate。
新的时序/幅度条件与旧 office-v6 分开，不把历史结果当作新评测。

五类 RL 的 CUDA/JAX/Orbax 加载设置已修复，预检各重放 1375 个旧动作、误差 0，
归一化及训练计数未变。14:05 CST 快照已有 7/384 真实回合完成审计：首条件三种神经
模型 Task/Strict 通过，三种参数 RL 和 metric 直接 RL 未完成任务。样本未齐，不报告
最终成功率；修复的是运行故障，不是承诺 RL 性能已提升。

四路有限评测与逐回合审计正在运行，原始失败和接触覆盖均保留；批次结束后独立生成统一表。
详见 `docs/OFFICE_V7_UNIFORM24_20261008.md`；服务器证据：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。
全 384 回合、每方法 `/24` 成功率和最终跨方法结论尚未完成。

### 2026-10-08 18:08 CST：八路加速与baseline停滞审计

本批按用户最新算力要求由4路改为8路，仍单线程、每路3GiB，限定高性能CPU核。
旧四个回合正常结束后补审计，未重跑、未改冻结物理/输入/模型/gate。首批8个新回合约6–7分钟
完成，当前174/384完成、8运行；整机CPU实测40%，无基础设施失败。新调度/报告服务分别为
`sii-office-v7-uniform24-v2-20261008`、`sii-office-v7-uniform24-report-v2-20261008`。

166回合描述性诊断显示：VMC/调VMC在carry受阻近静止，首条件末段仍有未知边接触；
经典阻抗无外部障碍接触时仍有抬升静差；导纳未稳定到位；直接动作RL变化率限制触发率
约93%–95%。不能把低RMSE/峰矩当任务成功，也不能断言整个算法类别不适用。
具体因果修复应在独立开发条件验证，当前24条件只评测，不反向选权重。
源码/小型证据/原始轨迹地址见 `docs/OFFICE_V7_STALL_AND_DISPATCH_20261008.md`。
