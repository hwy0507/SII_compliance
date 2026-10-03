# 假期研究进度：ESN 与 baseline 公平比较

最后人工核验：**2026-10-03 21:15 UTC / 北京时间10月4日05:15**。本页是 GitHub 固定入口；
每个完成的研究批次更新，具体提交见 [UPDATE_LOG.md](UPDATE_LOG.md)。运行状态有时间戳，不代表实时监控。

## 当前结论

**尚未得到可直接声称 ESN 最好的结果，也尚未达到完整 RAL 投稿证据要求。**
上一轮所有26模型在相同正式步长测试中实跑，5个成功；两个ESN均放置失败，
增强VMC、部分RNN及无记忆模型成功。低RMSE、低接触力不能替代完成任务。
这也是本轮优先补真实数据、修复ESN稳定性并增强baseline适配的原因。
[上轮全部26方法正式矩阵](code/mujoco_6d_vmc_benchmark/docs/evidence/all_methods_formal_20261003/report/MATRIX.md)。

## 本轮状态

21:09成本快照209/264；第六完整开发条件ESN4/6放置、0/6严格，四条已放置仍因柱子/link7穿透0.223–0.594mm失败。
原门槛/失败分母保留。[剩余容量核算](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CAPACITY_FORECAST_20261003.md)
显示按RL全80k估计，现有开发还需理想35.25–37.83h；再加144回合会超出预留窗口，因此本轮不登记修订02。
最终912回合纯物理约22.28–23.99h，另需审计/媒体；持续核对开始时点。已有ESN/增强baseline验证继续，不预定胜者。

20:56UTC初始198/264，第六身份仍32/33；四仿真持续。已完成[RL GPU有限吞吐探针](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_THROUGHPUT_20261003.md)：
动作＋两更新约18–19ms，首轮编译16–71s，峰值内存2.07GiB。164工程更新的权重全部丢弃，0新物理/候选；
原检查点完整文件集合和字节不变。真实三训练队列/物理续跑及组合内存尚未验证，仍不把准备工作当baseline训练完成。
可选ESN读出拟合须等teacher确认、新数据与时间核算，修订02尚未登记。

20:37UTC初始184/264，第六条件19/33，四仿真继续。
[170条完整范围的碰撞时序诊断](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_IMPACT_TIMING_20261003.md)
显示首段球接触仅0.45–0.50ms，距下次策略更新9.20–32.20ms；所有首撞峰值已在更新前发生。
因此不能单用低球撞峰值证明ESN即时反馈优势；仍完整报告峰值，并结合撞后恢复和持续接触负载。
这是零新物理/拟合的公开开发诊断，非最终比较或真机安全证据。原始hash及图已核验共享。

20:15UTC初始开发169/264，五个条件各33完整。第五条件ESN4/6放置但仅1/6严格，
其中三条柱子/link7穿透0.210–0.573mm超原0.2mm限制；增强baseline和新ESN仍待后续验证。
[RL有限轮转调度](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_DISPATCH_20261003.md)
已在首次训练前登记：各方法/seed先5500步再轮流续训，仍各最多80000步、同截止与奖励。
只替换零派发的旧等待器，原四仿真不动；活跃服务为`sii-r72-rl-office-adaptation-v2`，v1历史字段不改写。
实际续训仍待物理验证；不将队列结束混称等步数或收敛。最终24仍封存，学习预算修订02仍未登记。

19:37UTC初始143/264，四个条件已各33完整；第四条件ESN/matchedRNN各4/6严格，仍是候选开发结果。
新增[全部99轨迹的teacher覆盖诊断图](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_PROPRIO_SUPPORT_20261003.md)：
部分ESN失败伴随明显本体覆盖偏离，而clip比例很低；成功回合也可能偏离，不能当因果或胜者证据。
计算在本机仅4.163秒，无新物理/拟合；原始hash、全部点和短失败均保留并在Spark核验归档。

19:19UTC初始开发131/264，第四条件32/33，仍不提前按不齐的seed汇总胜负。
[下一轮共享拟合入口](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_READOUT_REFIT_PREPARATION_20261003.md)
工程完成：teacher确认后，纯ESN与同特征对照增加固定本体×记忆读出；如数据不变，普通MLP/RNN复用已有拟合/回合。
14项登记/数据来源/原选择入口回归通过。尚未登记修订02、未增加实际拟合，当前cap仍48；不热改稳定作业。

18:59UTC初始学习开发115/264已有逐回合AUDIT，前三个条件各33完整。第三条件ESN与matchedRNN均
3/6任务、1/6严格；matchedMLP2/6严格、memoryless1/3严格，ordinaryMLP/RNN均0严格。
仍不能宣称ESN领先；增强网络/新记忆组和RL适配继续等前序。4仿真队列未重启。
已补[全程及事件窗外接触统计](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_SUPPLEMENTAL_CONTACT_20261003.md)，
避免漏报放置时再次碰到人体模型；7条公开轨迹原生复算旧字段精确不变，14测试通过。
新指标适用于全部方法，失败/短回合保留，无接触NA；真正最终24条件仍封存。

| 工作 | 状态 | 可核验事实 |
|---|---|---|
| 新72小时协议、条件身份和封存 | 已完成 | 32训练＋8离线验证＋8闭环开发；另24留出身份封存 |
| 48条真实增强VMC teacher轨迹 | 完成并独立审计 | 44任务成功、28严格成功；其中32训练身份29/18，8离线验证7/6，8开发8/4 |
| 真实示范数据 | 完成 | 18训练＋6整身份验证，共33,000帧；失败全部保留，不混开发历史 |
| 同数据纯ESN/MLP/RNN训练与记忆消融 | 33模型训练已完成 | 本地单线程3GiB；全部权重/实际源码已在Spark核验归档，闭环开发运行中 |
| teacher及经典参数适配 | 96筛选完成并审计 | teacher21/24 task、13/24 strict；三个经典方法各0/24，待各取2个做8条件确认 |
| 办公RL接口 | 全物理重放通过 | 1375步／55秒观测、动作、状态、全部子步指标精确相同；新RL适配尚未开训 |
| RL长期训练准备 | 已登记、等待前序 | 5方法×3seed，每个最多8万累计步；网络/优化器/回放/RNG恢复验证通过，实际物理分段续跑尚待执行 |
| 学习模型闭环评估 | 四队列运行中 | 全部33模型×8共同开发条件264回合；首条件ESN点版与无记忆均通过，ESN积分版放置失败 |
| 选定teacher真实再采集 | 已登记、等待参数确认 | 原32训练/8验证身份；若teacher未改变则跳过；采集不自动启动新拟合 |
| 神经baseline学习率复核 | 48拟合完成、归档核验 | 同数据/宽度/更新数，候选总量仍在原cap内；跨3seed选率，21个新权重等待168开发回合 |
| ESN本体输入调制记忆与同机制对照 | 21拟合完成、归档核验 | 机制诊断发现固定记忆缺口；预算修订01先登记，全部21模型等待168开发回合；离线误差变差，未宣称优化成功 |
| 新冻结模型＋24条件正式评估 | 未开始 | 不按方法成功资格筛掉baseline，不以测试选权重 |
| 论文图表/置信区间/局限与交接 | 待完成 | 不预定胜者；无真机证据，不宣称现实部署成功 |

15:08 UTC成本快照：teacher48回合完整；经典/teacher开发筛选已完成56/96回合，仍在运行。
初始33模型共108次ridge候选、96000次梯度更新；学习率复核48模型另192000次更新。
这些操作不同，不可折算成“等预算”。逐回合/逐模型小型证据在
[成本快照](code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/EXPOSURE_SNAPSHOT_20261003_1520.json)。
文件名是快照标识，实际生成时间以内部created_utc为准。
最终统计与柔顺证据解释已写入[分析方案](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_ANALYSIS_PLAN_20261003.md)。
最终锁/执行接口已完成合成数据回归，尚未生成真实模型锁或打开封存条件，也未启动最终评估。

15:37UTC开发筛选74/96完整，四仿真稳定。新机制只调制储备池状态更新速度，ESN仍只训练线性读出，
无运行时teacher。相同固定调制也给MLP/RNN和重新训练的无记忆对照；旧组保留。
原ESN在合成零负载条件下不能区分卡住/前进，新结构打破该输入不可区分性，但未学出teacher长期保持，
不是任务成功的证明。真实示范中低估计负载且teacher恢复记忆仍活跃的片段存在，但远短于该合成探针。
本轮按[修订01](code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/AMENDMENT_01_CONTEXT_MEMORY.json)
将各学习族每seed候选上限24改48，其他约束和截止不变；实际使用ESN48、memoryless24、MLP/RNN合并各14，
不能宣称仍在原24预算内或计算成本相同。

16:30UTC新增观察：首条件ESN点版放置XY24.774mm，仅略小于25mm门槛；积分版26.381mm失败，
无记忆20.283mm成功。ESN点版推杆P95力较低（14.313 vs25.297N），但接触更久、力模积分更高
（43.724 vs28.817Ns），保持期间几乎未脱离（0.0013 vs2.191s）。这还不是稳健柔顺优势。
ESN未触柱子，该项NA；恢复指标均右删失。完整数据与限制见本轮根early_learning_metrics_v1/。
新增teacher再采集给所有学习方法同等数据访问；ESN既有48候选cap已用满，进一步拟合必须先明确预算修订。

16:50UTC开发24/264完成。首条件ESN三seed×两损失全部齐备，仅3/6严格通过；
seed303点/积分穿透0.551/0.476mm超过0.2mm，点版放置成功仍判strict失败。
102个已拟合模型本地重放/时延核验完成，全部动作精确复现；ESN可训练系数2884，但actor-only
中位耗时约32us，普通MLP/RNN约8/10us，不能以少参数宣称推理最快。详见UPDATE_LOG和服务器推理归档。
成对统计与最终预算锁保护合成回归通过；修正短回合恢复观察窗，完整55s指标精确不变。最终24条件未开封。

17:08UTC开发37/264完成，首条件33模型已齐（14任务/10严格）。ESN6回合4任务/3严格，
matchedRNN同为4/3；这些包含损失候选，不能当最终跨条件成功率。
柱子失败峰值晚于首次接触0.39s或约16s，反事实teacher查询与ESN出现相反z动作；只是模仿偏差诊断，
不是已执行成功的teacher标签。实际查询/过滤动作和限制见public_contact_diagnostics_v2与UPDATE_LOG。
实测343s/回合，912回合最终评估纯物理约21.72h；必须保留完整末日与审计余量，不能无限增加开发组。

## 时间与边界

18:36UTC初始学习开发100/264已有逐回合AUDIT，前两个条件各33齐备，第三条件32/33，第四条件2条。
整阶段独立复核仍待完成。最终38模型汇总入口完成5项合成/文件衔接检查，包括不删开发失败、
缺失seed阻止冻结，以及原teacher相同情况下的零重复采集closure；真正最终模型锁尚未生成。
已补[方法定位与文献核对](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_METHOD_POSITIONING_20261003.md)：
固定特征/线性读出和leaky ESN并非本项目首创，新交互尚未拟合，论文贡献仍需要闭环证据。

17:46UTC初始学习开发60/264已有逐回合AUDIT，整阶段独立复核待完成；四队列稳定；RL、选定teacher再采集与最终入口
已知训练条件重放仍等待前序。新增固定本体context×储备池读出工程实现，尚未拟合，不计为效果改善。
4种随机权重NumPy/Torch探针最大差5.61e-15，旧102模型完整1375帧动作重放全部精确相同。
原运行快照不改；ESN48候选/seed预算已用满，新增拟合前必须先登记共享预算。
诊断与验证见[结构说明](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CONTEXT_READOUT_DESIGN_20261003.md)。
最终入口的单条已知train_000重放使用独立合成协议，不接触真正24条封存条件，也不作为盲测结果。

第二条件development_001的33候选已完整：8任务/7严格；ESN和matchedRNN均3/6严格，memoryless0/3。
ESN303点版54.76s才进入release，积分版54.24s才进入load_transfer，55s内未满足原稳定放置要求；
位置接近目标不等于完成。当前优化还须处理让位后的推进/恢复效率，不能只压低峰力或放宽超时。
最终统计汇总器与失败保留入口已完成合成验证，尚未执行真实最终比较；三机位媒体固定首个共同条件、
全部最终模型/seed，不按成功挑片。真正24条件仍封存，当前没有新增拟合。

用户授权约3–4天；保守窗口 **2026-10-03 11:30至10-06 11:30 UTC**
（北京时间10月3日19:30至10月6日19:30），含准备时间。不是延长旧12小时协议。
第48小时之前结束新增开发，留时间做冻结评估、审计和报告；到截止不派新回合，已开始回合完成后保存。
证据足够可以提前停止，不为耗满预算计算。不创建定时任务。

固定baseline已发布的office-validation-v6几何、目标、公共规划/WBC、actor契约、执行器和task/strict门槛。
只在原登记的扰动范围采样新身份，球仍2s；人手完全收回后至少1s才开始推杆。
actor禁止接触真值、障碍状态、事件时间、任务阶段、视觉和距离输入。
纯ESN只训练读出，部署不混VMC。默认三训练seed、128储备池/隐藏宽度；另报告实际参数和计算成本。

第一批teacher也采用正式分辨率，**这表示物理步长，不表示是最终盲测**。
合格示范必须完整55s且原task/strict均通过；所有不合格尝试计入采集成本与失败账本。
同数据训练组不接收开发或封存历史作为示范。接触缺失记NA，恢复未观察到记删失；
成功率、暴露率和失败原因随接触指标一起报告，禁止挑出有利回合组成总排名。

新训练数据有明确覆盖缺口：18条严格成功训练示范中仅2条碰到柱子；12条穿透失败的最差接触对
是柱子与link7。接触进入速度与失败有关联，但手部速度不是link7法向速度，尚不能作因果结论。
离线ESN动作误差低于无记忆模型；同特征MLP/RNN均选中初始权重，梯度训练未改善验证误差，
需继续检查训练与闭环。以上都不作为ESN任务成功或优于baseline的证据。

后续小学习率复核已改善baseline：按跨3seed平均，普通MLP点误差下降23.9%、普通RNN下降36.4%，
同特征RNN也出现小幅验证收益。它们会进入公平闭环对比，不能继续把最初欠优化的网络当最强baseline。
ESN积分损失在固定教师观测回放中减小残余速度的累计偏差；该代理量不等于真实位移或任务RMSE。

## 服务器与复现入口

所有路径主机为 `arm1@192.168.31.70`。

- 本轮原生执行/共享：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
- 实际初始源码：同父目录 `research72_20261003_1149_runtime/`，base main `33f438075649508ceb8f84479880d5d622f4eb4f` 加本轮3脚本；不是干净commit执行。
- 主服务：`sii-research72-teacher-20261003-1149.service`；4个子服务 `sii-r72-teacher-1149-{0,1,2,3}.service`。
- 原始记录：`teacher_bank/queue_*/<condition>/`，含execution、rollout、物理子步、原始/过滤action、teacher内部状态、独立接触审计与hash。
- 每条队列 `execution.json` 保存完成/运行身份；完成行验证后才能跳过，不覆盖中断回合，不自动重试失败。
- [公开协议与条件](code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/PROTOCOL.json)；
  封存24条件只记录SHA `97ea7c7700b1d415c7139244f2481e0b930d921fe4d86b7913347731d17bf2ed`，本轮尚未读取或运行。
- 上传源码tar已两端核验SHA `0c43441298a6a68dac2d25f1578d3ee87ebd49c2c88cd0282a033e78aea4353d`。
- 初始协议/入口已推送main `659672d9b463b98b3290d461f7bfe6b8901ea572`；服务器
  `/home/arm1/sii_shared/SII_compliance/source/659672d9b463b98b3290d461f7bfe6b8901ea572/` 全3085文件内容/大小/模式核验通过。
- 连续准备服务 `sii-r72-prepare-learning-20261003-v2.service` 已完成数据导出与
  已知train_000的完整物理重放。不是最终测试。
  源码在同父目录 `research72_20261003_1149_learning_runtime_v2/`，tar SHA
  `deb7e5c546cab79d0776d1102e9205d1ff2f2c39b4df6889c9e6d881dca5e7d3` 两端一致。
  v1等待器因去除不必要torch依赖而在空闲时替换，源码/记录保留；没有重启任何teacher回合。
- 完成模型：本轮根 `local_learning_archive_v1/learning_v1/`，实际拟合在airpig，原execution路径保留。
  模型包SHA `197bc0a5f7c363832a78ddb93dbd73cad7ff793c625eb2e6e19054795360f95d` 两端一致；
  逐模型checkpoint/metadata/source/data lineage核验通过。数据SHA `b97acf4c61d9d3ba4d5fcb4817ac449b460e65a4821be632c5f61a5a1bba67c6`。
- 运行筛选 `controller_screen_v1/`；后续等待服务 `sii-r72-followup-v1` 依次运行264学习回合和64经典确认回合，
  任一阶段失败保留并停止，不盲目重试。全部是开发数据，24最终条件仍封存。
- 当前筛选源：相邻 `research72_20261003_1149_development_runtime_v2/`，base fb48427＋本批修改，
  tar SHA `850606455d85b9265c518f9408d88d3b02ce8764435410f0d56691f4798a4752`；
  后续源为同父目录 `research72_20261003_1149_development_runtime_v3/`，追加两个调度/校验脚本，
  overlay SHA `7cbaaf0da92f23180e8e2e9de5be094c55ceb2e5ef83083a978eeaf5e6254f75`，两端均核验。
- RL准备：本轮根`rl_checkpoint_probe_v2/`（工程探针，0新物理步）与`rl_office_adaptation_v1/`（等待前序）。
  新源码为相邻`research72_20261003_1149_rl_runtime_v3/`，完整运行版本链见UPDATE_LOG。
  修复checkpoint仅hash顶层文件的遗漏，现包括网络、目标网络、优化器、归一化等嵌套文件。
  三条训练队列用共享flock限总仿真≤4，各3GiB/单CPU容量；后续ESN使用相同槽位工具。
  初始5500步段与后续段共享同一80000步优化器计划、回放和RNG，累计曝光不重复相加。
- main `45662c03ca40269f08e183fa6e814a900f026aca` 已发布，服务器对应`source/<该SHA>/`全3111文件核验通过。
- main `d08dc8f23a0b5e9bbff2bed66e489620333d9052` 已发布，服务器`source/<该SHA>/`全3117文件核验通过。
- main `389e9e53bc016a03a250fe5f053a5a6513331023` 已发布，服务器`source/<该SHA>/`全3126文件核验通过。
- main `e32f02ddc16e1b65511b5a9f9cfbd316042b43ef` 已发布，服务器`source/<该SHA>/`全3133文件核验通过。
- 48学习率拟合与离线诊断归档为本轮根`local_neural_refinement_archive_v1/`，tar SHA
  `97a39b953bfbe4b90f7aab28d82b4f98c14b4f8934c0827c5d3846d2f84c04fa`；权重、训练元数据与源码全核验。
  `NEURAL_LR_SELECTION.json`只使用整身份验证动作误差，保留每组选定学习率的全部3seed。
- `sii-r72-additional-development-v1`等待旧四队列流程结束；之后先评估8回合零让位名义WBC参考，再评估21新模型。
  每回合释放共享槽位，后续ESN实验可以插入，不让整批神经baseline长期占住唯一空闲槽位。
  源为相邻`research72_20261003_1149_development_runtime_v4/`；新增overlay SHA
  `1399f47d891ef90b2d6e777e4119fe8c0a5fc9319b8106a2c014a296c18d7b5d`两端一致。零让位新接口尚待物理验证。
- 初始teacher服务继承了旧环境变量commit标签；实际源码快照/hash才是复现依据。澄清见本轮根和Git证据的
  `INITIAL_SOURCE_LABEL_CLARIFICATION.json`，未改写历史执行记录或重跑仿真。
- 新记忆机制：本轮根`local_context_gate_archive_v1/`含21模型、真实记忆覆盖与新合成探针，
  包SHA c206c4e98102bff46d0dc97a8915e5018ddfbb9369914f08ce5b2e5b1c0b2ea6；逐模型/元数据/拟合源核验通过。
  `CONTEXT_GATE_DEVELOPMENT_SPECIFICATION.json`锁定168回合，`sii-r72-context-gate-development-v1`等待followup_v1，
  之后与原额外神经开发分享空闲仿真槽位。独立源在相邻`research72_20261003_1149_context_runtime_v1/`，
  tar SHA516ed7e308b8911c355b6397217db32d963d5de6306888fd2e083ae8d293d641，base e32f02d＋本批未提交修改。

尽量本地学习/后处理；物理沿用Spark原生库以消除已观察到的跨库差异。Spark最多4仿真；
本机最多1仿真、1–2线程、3GiB。历史停止的其他作业不动。小型证据和代码进Git，大轨迹留服务器。
最终报告将区分“已完成、运行中、未完成”，并列出无法在窗口内满足的投稿关键缺口。
