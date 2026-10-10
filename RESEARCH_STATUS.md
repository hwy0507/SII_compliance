# 假期研究进度：ESN 与 baseline 公平比较

## 2026-10-10 15:05 CST：完整110k开发零成功，自动续训已停止

direct108458步与阻抗104500步各完成同8个development，Task/Strict均0/8。
独立审计通过不代表任务通过；本配置/预算失败不能证明所有RL不适合、调参充分或收敛。
agent停止自动续步时误将SIGUSR1发给子进程，两在途回合中断，单列基础设施事故；
此前完整验证与checkpoint完好。训练unit均inactive，仅旧归档继续。
详见[结果与事故记录](code/mujoco_6d_vmc_benchmark/docs/RL_CONVERGENCE_CONTINUATION_20261010.md)。

## 2026-10-10 13:14 CST：用户重新授权，本机RL连续接续已启动

新服务`sii-convergence-20261010-v2`已运行，首先补齐两个已保存110k模型的同八development，
随后自动恢复到165k/220k/330k/约500k节点；其余五配置也在队列，本机仍两路3GiB/禁swap/单线程。
旧15小时收口不再阻止本次新授权接续。成功稳定性与失败平台分开判定，达到步数不算收敛；
没有新的最终RL成绩，也没有服务器计算。见[续训登记](code/mujoco_6d_vmc_benchmark/docs/RL_CONVERGENCE_CONTINUATION_20261010.md)。

## 2026-10-10 12:53 CST：15小时窗口收口后的只读监看

本机无运行中的 RL/MuJoCo 作业；没有启动新计算。110k 扩展目录的实际收据均已 `complete`：direct office_task 108458 步/40 训练回合/6 Task/2 Strict，RL impedance 104500 步/36 回合/0 Task/0 Strict。只读训练轨迹审计新增物理步为0，结果仍属于训练身份，尚未完成固定8条 development 条件重评，不能写成最终 baseline 成功率或与 ESN 排名。详见 [监看审计](code/mujoco_6d_vmc_benchmark/docs/BASELINE_MONITOR_20261010.md)。

## 历史：新15小时窗口，55k接续正在评估（2026-10-09 21:33 CST）

原七配置56/56开发全完成，均零成功；18:20起接续健康作业。
直接office_task已54146交互/98294更新，首6个开发独立审计通过且均Task/Strict失败；
阻抗约51k继续训练。新的15小时预算截至10月10日12:21 CST，实际边界保存保护服务已运行。
本机两lane，无服务器计算；仅训练数据的奖励解耦审计有更丰富信号，但尚未训练该变体。
没有可用新RL或新最终比较。详见[本轮记录](code/mujoco_6d_vmc_benchmark/docs/BASELINE_OVERNIGHT_15H_20261009.md)。

截至10月10日11:30 CST，55k节点七配置均完成；直接动作110k训练身份为6/27 Task、2/27 Strict，
阻抗仍0/24，开发集尚未重评。四格离线信用试验已完成但没有新物理步，不能替代闭环比较。

## 15小时窗口已收口（2026-10-10 12:28 CST）

guard已在授权截止时停止新派发并保存已有训练回合。direct110k为108458步/40回合/6 Task/2 Strict，impedance110k为104500步/36回合/0 Task/0 Strict；均为训练身份，未做development重评。因此仍没有可直接公平比较的RL最终baseline，详见[收口报告](code/mujoco_6d_vmc_benchmark/docs/BASELINE_15H_CLOSE_20261010.md)。

## 历史：已登记延长RL训练，最终比较暂缓（2026-10-09 15:56 CST）

用户要求学到可用RL策略后再比较。原11k队列继续，新接续服务已启动并等待原队列/独立审计，
不会增加当前两路仿真或重启健康作业。四配置的同八开发全部完成且均零成功；
综合指标直接动作和历史熵对照继续。后续精确恢复到55k/110k/220k等节点，
用固定开发集筛查稳定Task与Strict成功，再做独立seed验证；全零失败平台需科学修正，不能称收敛。
接续代码与六个回归检查、32条真实开发接口复算通过；尚未开始55k接续、未获得可用新策略。
详见[延长训练登记](code/mujoco_6d_vmc_benchmark/docs/RL_EXTENDED_TRAINING_20261009.md)。

## 历史：两组八条件完成，调导纳/调VMC运行中（2026-10-09 14:16 CST）

直接office_task与RL调阻抗各11k训练＋同八开发条件完成，均Task 0/8、Strict 0/8。
16回合完整55秒、物理子步/动作/身份审计通过；分别停approach和carry。
八开发均值RMSE/峰矩/峰速分别205.018mm/41.929Nm/0.34735m/s及
23.327mm/36.510Nm/0.37383m/s，失败阶段不同，不以此排名柔顺性。
调导纳6500交互、调VMC1250交互，两个本地lane继续；原metric/低熵对照待完成。
直接组训练中所有已见Strict失败的原始折扣回报相同，包含已放好的两次预热；
势函数能帮助TD学习，但该批终奖未区分这些不同失败。只是学习信号诊断，奖励未改。
无服务器计算、无定时任务；11k不是充分训练，新统一final与多seed尚未完成。
详见[本机补强报告](code/mujoco_6d_vmc_benchmark/docs/BASELINE_LOCAL_RL_20261009.md)。

## 历史：本机RL首段完成，开发评估运行中（2026-10-09 13:21 CST）

直接office_task与调阻抗各完成11000交互/12002更新，奖励/动作及调阻抗参数审计通过。
直接组最初预热曾完成Task，但学习后的四回合均停approach；调阻抗仍卡carry，不称学习成功。
首个开发入口遗漏本地模型资源路径，在物理开始前失败；原失败保留，独立目录同checkpoint
重跑完整且审计通过，任务仍失败。13:16补齐环境变量后复用checkpoint接续，未重训。
当前进度读`parallel_v2.execution.json`，旧`parallel.execution.json`只记录已保留失败。
直接已完成2/8开发、调阻抗1/8运行中；后续五配置待执行。一次性观察进程逐组复算物理指标，
不创建定时任务，不在服务器计算。11k是诊断而非充分训练，低熵对照和收敛证据仍待完成。

### 首轮登记（12:21 CST）

用户要求服务器另作他用，新的训练/仿真/分析全部转到本机。GPU更新/归一化/恢复、
正式模型hash与全范围参数约束已核验；1375步完整物理smoke及独立奖励重建通过。
该随机预热回合Task=true、Strict=false（0.273794mm外穿透），0梯度，不是学习成功。
本机正在并行接续直接office_task与训练RL调阻抗；有限队列覆盖五RL族+两探索配置对照，
每项11k交互上限及原8开发身份检查。每lane3GiB/禁swap，服务器只接收存档。
[本地补强协议、证据和未完成项](code/mujoco_6d_vmc_benchmark/docs/BASELINE_LOCAL_RL_20261009.md)。
尚未完成训练充分性、多seed和新最终比较，以下旧批次结果保持不变。

## 已完成：15小时有限修复与重评，baseline性能仍未解决

10:50 CST最终全量审计结束，384/384新回合均完整55秒，无基础设施缺失；42240万物理子步指标核验、
144经典/参数RL控制器审计、614回合势函数抵消及计算账本通过。本批已无运行中计算服务。
ESN21/24 Task、15/24 Strict；matched RNN24/16、matched MLP13/9、enhanced teacher24/17。
三类经典和五类RL仍全0/24；实现修复不等于已训练充分或任务恢复能力已解决，不能声称ESN全面最好。

[完整16方法结果与柔顺性、失败原因](code/mujoco_6d_vmc_benchmark/docs/BASELINE_REPAIR_FINAL_RESULTS_20261009.md)。
原协调器在384结束后因报告模块漏打包退出，旧失败保留；独立v2补入原版本分析模块并完成审计，
没有重跑仿真、改权重或修改冻结源码。代码未来入口补齐依赖并提前导入，避免长实验后才发现缺模块。
未完成：强RL成功学习、经典任务恢复、同数据/多seed架构消融与真实硬件泛化，不能当作投稿级全面优势。

以下为本批运行中的历史快照；当前完成状态以上面最终收据为准。

## 本批历史快照

08:54 CST：新最终评估202/384完成、10运行，无基础设施失败；16方法各完成12或13个条件。
冻结模型清单及源hash复核未变，全部10个活动worker的OOM/oom_kill均0、每路3GiB/禁swap保持。
全量审计仍等待全部384完成，尚无最终比较结论。新快照`FINAL_MIDPOINT_20261009.json`保留精确计数。

06:56 CST：80/80开发评估完成，Task/Strict均0；78完整、2提前失败全部保留，无基础设施失败。
06:51:51锁定全部16模型，06:51:52开始新的384最终评估。独立复算十模型×八条件选模分数、
源/checkpoint hash和冻结时序通过，最终条件与训练/开发身份及完整参数元组无重复。
选中VMC seed11、导纳seed12、阻抗seed11、直接metric/task seed11；这不是两个seed的平均性能。
最终回合运行中，不能把开发零成功或部分最终回合当完整最终矩阵。详见第十八阶段。

06:17 CST：十组训练已在06:00收口后完成末回合，06:05:32全部保存，80开发回合正在运行。
参数RL实际60500–63250步，直接RL85285–164621步；当前学习段仍无Task/Strict成功，不宣称收敛。
十个最终checkpoint一致性/价值诊断通过，首轮缺cuDNN路径的诊断启动失败另存；仅修审计入口，未重训。
final24仍封存；开发选择、最终384及全量审计尚未完成。原12:23 CST总截止保持。
详情及逐seed预算见15小时记录第十七阶段；以下时间条目保留为历史快照。

05:02 CST：一次性最终审计接续服务已登记并等待现有384评测结束；当前没有执行最终审计或读取最终条件。
它在原期限内串联统计/物理轨迹核验、144控制器重放、完整全16表与预算/奖励审计，避免会话退出后遗漏。
十组训练稳定；原06:00 CST收口不变，详见15小时记录第十五阶段。不是定时任务，也不新增训练/仿真。

最新04:01 CST：十组训练稳定、OOM/oom_kill均0，当前参数约3.8–4万交互，direct最高12.775万。
新增诊断05仍无学习后Task/Strict成功，导纳一条到release、阻抗更多到retreat不能算放置。
401完整训练回合的折扣势函数终止抵消核验通过，上一快照未flush的末三条已补核；
没有净空手阶段bonus的证据，但不据此声称训练充分。全16最终表入口已准备，完整/短回合分列。
final24仍封存，原06:00 CST收口训练、12:23 CST总截止保持；尚无新的384最终成绩。

用户授权窗口：10月8日21:23至9日12:23 CST。同一冻结office场景、原Task/Strict、
纯本体输入和执行器限制；旧384回合不改，新增32训练/8开发/24封存最终条件。
VMC动作单位、阻抗有界参考/执行接口已修正并通过代数与动作重放检查；RL补齐优化日志、
完整奖励重算和恢复状态，尚未获得梯度学习后的成功或收敛证据。
六个诊断验收回合Task/Strict均0/6；高刚度阻抗存在厚桌角接触期间的夹持滑移，失败保留。

10月9日01:05 CST快照：经典144筛选＋48确认完成，Task/Strict全零，全部失败保留。
新独立审计发现力矩平滑奖励误将4ms伺服更新按0.05ms物理步长求差分，惩罚约放大80倍；
已修正奖励时钟及失败剩余成本上界，不改物理、动作、门槛。八组metric在回合边界保存后，
用原始off-policy数据重建学习器：七组已恢复且进入实际梯度更新，较长direct metric前缀仍在重建。
两个office-task奖励作业不受影响，继续原训练；旧checkpoint和废弃/重建梯度成本均保留。
不可变`source_v9`是修复版本，完成八组重建后由有限`continuation_v3`接续开发/最终评估。
此前3GiB有内存回收压力但未见OOM；原生250Hz伺服日志使用磁盘顺序float64记录。
01:10 CST八组重建全部完成，唯一`continuation_v3`正式接续十组；01:18八组共15条新回合独立奖励审计通过。
两个direct seed1历史预热曾完成放置，但最大穿透0.98245mm，Strict失败且不是学习成果。
final24仍未打开；奖励/执行链正确不等于算法性能已解决，当前enhanced teacher仍保留为强参考。
计划06:00 CST在回合边界收口训练，再做开发选择和最终16×24；不是定时任务。

02:05 CST：两seed的VMC/导纳完整动态动作重放与原生阻抗伺服限制检查通过。
十组新checkpoint只读critic诊断完成，终止状态价值误差仍明显，不能宣称已收敛。
六个神经参考的训练来源已核对：选定ESN与两个RNN为新teacher20/5数据，两个MLP及memoryless为旧teacher18/6数据。
历史选模结果保留；最终是统一测试下的系统比较，不是六者同数据/同计算的纯结构消融。
同一128宽度不等于同参数量或同训练成本。完整来源和失败诊断见15小时记录第十阶段。

完整证据、运行路径和未完成项见[15小时记录](code/mujoco_6d_vmc_benchmark/docs/BASELINE_REPAIR_15H_20261008.md)。
实现修复不等于性能问题全部解决；新最终矩阵尚未生成，不保证ESN胜出。
以下内容均为此前72小时批次及其历史快照，不代表本次新任务状态。

## 历史批次最终闭合（2026-10-07）

最终 38 模型×24 held-out 条件已完成 912/912；task 284/912、strict 218/912。最终交付状态 complete，
15 个 RL 模型的 360/360 条最终物理回合完成独立 actor replay。统一矩阵和投稿口径见
[RESEARCH72_FINAL_RESULTS_20261007](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FINAL_RESULTS_20261007.md)。
ESN 60/72 task、43/72 strict；matched RNN 58/72 task、44/72 strict。ESN 在 task、RMSE/速度权衡上表现好，
但 strict 略低于 matched RNN，因此不宣称全面领先。

2026-10-04 11:00UTC：VMC参数303和直接task303两段续训审计完成；新增32回合/35192800子步、
43959可核验奖励一致，32首项仍未核验，保留一条54.64秒穿透终止失败。
这是训练链证据，非最终任务比较；[新增审计与局限](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_REWARD_AND_CONTINUATION_20261004.md)。

2026-10-04 10:00UTC：补充direct office-task seed301新完成续训段审计；新增16回合/16996800子步、
21230个可核验奖励一致，16首奖励仍未核验；一条24.84秒穿透终止失败保留。
这是在线训练记录，不是最终策略测试；[证据与边界](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_REWARD_AND_CONTINUATION_20261004.md)。

已完成120次拟合的[实际成本对照](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_TRAINING_COST_TABLE_20261004.md)已整理：
宽度128不代表参数/搜索/计算投入相同；teacher共享成本、父模型初始化和运行中RL成本分开披露。
它是成本账本汇总，不是最终性能结果或全部研究完成证明。

2026-10-04 09:14UTC：六个新完成RL续训段的130回合/1.038亿子步、缓存前缀与奖励独立核验完成，
包含38个提前中止回合；129577奖励一致，130首奖励缺初始potential仍未核验。
这说明记录链一致，不代表最终策略已收敛或ESN领先；原训练/开发继续，最终条件封存。
[新增证据与局限](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_REWARD_AND_CONTINUATION_20261004.md)。

2026-10-04 09:04:53UTC：已接通最终评测之后的独立RL回放→统一矩阵/统计→图→全部模型三视角视频。
一次性连续服务PID2550310实际在等最终批次；原训练/开发/最终衔接服务不变，未增加搜索或解封。
本机与Spark各9项编排测试通过，尚非实际最终结果。
[后处理范围、失败处理与服务器入口](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FINAL_DELIVERY_20261004.md)。

## 2026-10-04 10:42:08 UTC 快照

neural-LR37/168、context gate42/168、readout refit21/144；120拟合已完成，RL累计370053交互/590136更新。
三组新开发包括5条物理短回合，不能将程序complete当作完整55秒或任务成功。
10:42实际四个仿真worker的cgroup `memory.events` 中oom/oom_kill均0；max计数非零说明触及内存限制，不能称没有内存压力。
final transition仍等待前置，最终24条件尚未开封，完整912比较未开始。

账本：`EXPOSURE_SNAPSHOT_20261004_1042.json`；内部真实时间为10:42:08.769010UTC。
按原预测器，剩余开发理想17.598–18.432h；保留912回合及2h收尾后余量4.424–6.376h，
不包含全部等待/冷启动，不是完成保证。没有追加搜索或重启稳定作业。
历史与证据路径保留在 [UPDATE_LOG.md](UPDATE_LOG.md) 和 [联合研究进度](code/mujoco_6d_vmc_benchmark/docs/ESN_VMC_JOINT_PROGRESS_20260927.md)。

## 当前结论

开发回合worker指标汇总见 [RESEARCH72_DEVELOPMENT_AUDIT_20261004.md](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_DEVELOPMENT_AUDIT_20261004.md)：保留历史70条和后续79条快照。它们没有独立复算物理子步，不替代完整阶段审计或最终38×24矩阵；历史readout refit ESN两条中仅一条strict，另一条外穿透0.5069 mm。

04:52UTC补充：新固定交互读出首条开发（seed301/development000）worker审计task/strict通过，
30.699mm / 49.981Nm / .349058m/s，最大外穿透.143599mm，动作/filter/储备池重放误差0。
该条仍只是一个开发样本，整阶段独立审计仍待完成；不是最终结果。工作状态表更新至10:42:08UTC快照，初始模型结果表保留其原完整阶段口径。
最终选择器JSON路径兼容错误已修复，72候选合成端到端账本及缺回合/篡改拒绝在本机与Spark各3项通过；
实际最终选择尚未运行，不能使用旧9e7fa92及更早版本的该入口。

**ESN已在多数初始开发回合完成放置，但还没有稳健通过安全门槛，也没有证明柔顺性全面优于baseline。**
尚未达到完整RAL投稿证据要求。新的最终24条件仍封存，未用于调模型。

初始33模型×8共同开发条件的264回合及独立阶段审计全部完成，261完整、3短失败。
以下各版本均为3个训练seed×8条件，是开发候选比较，不是最终选定模型的留出成功率：

| 初始方法/版本 | 放置成功 | strict成功 |
|---|---:|---:|
| 纯ESN，点损失 | 19/24 | 9/24 |
| 纯ESN，时序积分损失 | 11/24 | 4/24 |
| 无记忆，重新拟合 | 7/24 | 6/24 |
| 普通MLP，点损失 | 7/24 | 7/24 |
| 普通RNN，点损失 | 14/24 | 0/24 |

点版ESN三个seed的strict分别3/8、4/8、2/8；积分损失尚未改善闭环。
六个初始同特征RNN都选择了第0步ESN初始化，另有小学习率增强网络等待闭环，不能据初始组宣称充分优化RNN不如ESN。
点版ESN推杆暴露24/24，其P95力均值21.432N、力模积分36.733Ns；无记忆完整暴露23/23对应24.303N、33.242Ns。
暴露集合不同，峰力与累计负载存在权衡，不能当作全面柔顺领先。

[完整初始结果、全部seed/版本及局限](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_INITIAL_DEVELOPMENT_20261003.md)。
[上轮26方法单条件矩阵](code/mujoco_6d_vmc_benchmark/docs/evidence/all_methods_formal_20261003/report/MATRIX.md)另行保留，不与本轮分母混合。

## 已完成、运行中与未完成

| 工作 | 当前状态 |
|---|---|
| 条件/协议 | 32训练＋8离线验证＋8闭环开发；另24最终身份封存 |
| 初始teacher | 48回合及审计完成：44任务/28strict；训练32为29/18，验证8为7/6，开发8为8/4 |
| 真实示范 | 18合格训练＋6整身份验证，共33,000帧；所有拒绝/失败尝试仍计成本 |
| 初始学习组 | 33拟合及264闭环/独立审计完成 |
| teacher/经典参数 | 96筛选＋64确认及审计完成；teacher09为8/8task、7/8strict，其余选定adm03/imp02/vmc11 |
| 名义规划＋WBC | 八条共同开发全完成/独立审计通过，task/strict均0/8，均停carry |
| 更强MLP/RNN | 48学习率复核拟合完成；21模型的168开发回合已接续，当前37/168 |
| contextual-leak ESN及同机制对照 | 21拟合完成；开发42/168。离线误差变差，不能先称优化成功 |
| 选定teacher再采集 | 40/40完成，task40、strict25；20训练＋5验证合格示范，已由全部六个模仿家族共享拟合 |
| 固定本体×记忆读出 | 修订02前瞻登记，18拟合/固定矩阵/字段重放/763文件归档完成，开发21/144，全部候选继续 |
| RL office适配 | 三队列继续运行；累计370053交互/590136更新；两个队列已进入49,500阶段，全部15模型共同边界不变 |
| RL接口/恢复工程 | 导纳/VMC301各27,500步续训阶段已完整审计，父5,500前缀与新增22,000真实转移核验；非逐梯度或最终任务审计 |
| RL奖励数据 | 四批审计共240回合/276948区间/221558400子步、276708可核验奖励，240首奖励仍因初始potential未知排除；不是全15最终模型 |
| 最终冻结/评估 | 一次性连续衔接服务已运行但仍等待全部前置，尚未选模/冻结/开封；计划38模型×24条件=912回合 |
| 最终审计/媒体/图表 | 工程入口准备完成；真实最终证据尚未产生 |
| 论文方法与实验设置 | 英文草稿已按实现写出并共享；未选择最终变体，结果/摘要主张待真实最终证据 |

最终选择工程检查增至8项，合成完整38模型账本验证全部15个RL的登记边界、实际短回合步数和后续未用成本；
缺少边界或关闭证据篡改均阻止选择，未实际冻结或开封。新快照在共享本轮根
`EXPOSURE_SNAPSHOT_20261004_0850.json`（内部实际时间08:45:42UTC），SHA `c708837a1b011d7b623ffbf88c8fd7aac346e72eb88c115727902c24f477df67`。

[连续衔接服务](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FINAL_TRANSITION_20261004.md)将全部既定开发完成与最终912评估顺序连接。
当前PID2513613/512MiB服务仅等待，无新物理或搜索。后续先查共享`final_transition_v1/execution.json`及实际PID，
不重复手工派发final矩阵；它的最终complete也不替代独立RL actor回放、统计/媒体和论文完成审计。

累计120个拟合模型均已完成本地训练、归档及字段/重放检查，不是120个最终模型。
其中15个ESN与9个无记忆对照的全部288候选已按seed独立重建固定矩阵，并与服务器档案逐hash关联；
支持只训练读出的实现身份，不构成稳定性或最终任务效果证据。
纯ESN没有运行时teacher混合。新的固定本体×记忆读出在04:20UTC登记修订02后拟合，储备池仍128，
只训练3780读出系数；累计ESN每seed60候选，新18模型共享teacher20/5数据并各测试相同8开发身份。
新数据和架构同时变更，不能称单因素机制消融；[实际重训证据](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_READOUT_REFIT_RESULTS_20261004.md)。
不同家族的ridge次数、梯度更新、示范采集与RL交互分别报告，不称“等计算预算”。

## 下一步和判定依据

1. 64确认和40再采集已完成；保留teacher09的柱子/link6穿透.314mm开发失败及15条再采集strict失败。
2. 完成RL真实续训/共同边界关闭以及全部已登记增强组和新读出的开发闭环，总并发≤4。
3. 跟进实际容量，保留完整最终比较，不再凭离线误差扩大搜索，不按失败删候选或方法。
4. 全方法冻结后才开封24条件，完成独立子步/动作审计、成对区间及固定首条件的全方法三机位媒体。

[容量核算](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CAPACITY_FORECAST_20261003.md)估计最终912回合纯物理约22–24小时，另需审计/报告。
全80k原预测余量仅+0.67至−1.88小时，实际等待还会缩短余量。03:24在任何模型启动目标阶段前，
已为全部15模型登记统一49,500自然完整回合边界；实际48,126–49,500步，原80k优化器日程不变。
独立持续监护已运行，尚未发训练信号；原队列后续冗余阶段可额外采0–2750步/模型，全部计成本而不选其权重。
缺任一模型边界/关闭证据则不冻结，不因结果删baseline。见[登记与核验](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_FINAL_BOUNDARY_20261004.md)。
06:18:25UTC新预测按每RL模型最大52,250总成本并计入新登记144回合，理想剩余开发22.511–23.573h；
保留最终912和2h收尾后预计余量3.678–5.857h。最终P90最晚起点10月5日09:33UTC，需提前完成开发。
仍未计额外等待/冷加载，不是完成保证；成本工具已将新增144计作登记工作，未来不再重复记作假设新增。
最终同时报告任务、strict、失败阶段、接触暴露、P95/力模积分、恢复/删失和运动指标，不以加权总分挑胜者。
[方法正文草稿](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_MANUSCRIPT_METHODS_20261004.md)给出ESN公式、对照差异、精确task/strict口径及投稿前缺口；不构成实验完成声明。
[分析方案](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_ANALYSIS_PLAN_20261003.md)、
[独立RL动作回放](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_ACTOR_REPLAY_20261004.md)和
[图表入口](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_FIGURE_EXPORT_20261003.md)区分工程检查与实际结果。
[真实续训及奖励核验](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_RL_REWARD_AND_CONTINUATION_20261004.md)
已扩展物理区间归约，保留4个短失败与62个未核验首奖励；direct_metric301实际27,336步也保留，
不补写为名义27,500上限，不把训练管道一致性当最终策略性能。

## 时间和研究边界

本轮保守72小时窗口：**2026-10-03 11:30至10-06 11:30 UTC**（北京时间10月3日19:30至10月6日19:30）。
第48小时停止新开发，并提前预留最终评估/审计。无定时任务，不重启稳定作业，不为占满机器空转。
固定office-v6几何、目标、规划/WBC、输入、执行器和原task/strict门槛；dt=50μs、55s全程。
球2s，人手完全收回至少1s后才推杆；仅已登记小范围扰动，不称跨环境或真机泛化。
actor禁止接触真值、障碍状态、事件时间、任务阶段、视觉和距离；RL奖励诊断字段不拼入actor。
本地拟合/渲染优先，单模拟器、1–2线程、3GiB；Spark仿真≤4，保持已冻结原生物理运行库。

RMSE是到各回合当前阶段goal的子步误差，不是共同时间参考轨迹；停滞带来的低误差不算优势。
170条公开轨迹的首球撞峰值均先于首次可用碰后actor计算，不能归因于25Hz策略即时反馈，也不是硬件安全证明。
初始18条、新20条合格训练示范都仅2条碰柱子，新5条合格验证示范则0条，覆盖不足仍是限制。固定储备池/线性读出已有机器人先例；
[文献与方法定位](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_METHOD_POSITIONING_20261003.md)不构成首次性或稳定性证明。

[新旧teacher数据质量](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_TEACHER_DATA_QUALITY_20261004.md)：
同32训练身份独立复算64条/7040万子步，新teacher放置29→32、strict18→20，但桌角接触时长4.11→8.58s、
力模积分8.17→22.37Ns。新20条合格示范仍只有2条柱接触，不能称覆盖问题已解决；8条strict改善、6条退化均保留。
同8验证身份独立复算另16完整回合：task7→8、strict6→5、桌角力模积分6.26→20.04Ns，不称全面teacher改善。

[teacher/经典完整确认](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_CONTROLLER_CONFIRMATION_20261004.md)：teacher从相同开发8/4改善至8/7，尚非ESN结果。
[短步长诊断](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_NUMERICAL_DIAGNOSTIC_20261003.md)：50→25μs球峰力差10.4%，积分差.5%，峰值未证明收敛。
最终入口的已知teacher 55s重放逐值一致；是工程验证，真实24保留条件仍封存。

[装置审计](code/mujoco_6d_vmc_benchmark/docs/RESEARCH72_APPARATUS_SCOPE_20261004.md)核对精确MJB和原执行源码：
1 kg自由球、有限质量人手/杆代理、摩擦抓取，实际装置不是mocap；同时保留了场外旧mocap对象。
14/80 N是杆/人基座驱动力限幅，不是接触峰力上限；这些仿真比较不构成人体安全或硬件验证。

## 服务器与Git复现入口

主机 `arm1@192.168.31.70`，本轮根 `/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
完整提交源码位于 `/home/arm1/sii_shared/SII_compliance/source/<完整SHA>/`；真正执行版本以各实验execution/source hash为准。

| 内容 | 本轮根下位置 |
|---|---|
| 初始teacher/示范 | `teacher_bank/`、`prepare_learning_v2/demonstrations/` |
| 初始开发/报告 | `learning_development_v1/`、`public_initial_report_v2/REPORT.json` |
| 参数筛选/确认 | `controller_screen_v1/`、`controller_confirmation_v1/`、`followup_v1/` |
| 初始/学习率/记忆组拟合 | `local_learning_archive_v1/`、`local_neural_refinement_archive_v1/`、`local_context_gate_archive_v1/` |
| 增强组/teacher新采集 | `additional_development_v1/`、`context_gate_development_v1/`、`teacher_refinement_v1/` |
| 活跃RL campaign | `rl_office_adaptation_v2/`；v1为零派发后保留的历史等待记录 |
| 短数值诊断/已知轨迹最终入口演练 | `public_numerical_probe_v1/`、`final_rehearsal_v1/`；不是实际最终测试 |

本轮开工核验已推送main `66c72b90fdbcd7355b2fad2029f482ef24a555b4`，完整3238文件已共享核验；
baseline为 `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`，未整分支合并。
大型原始产物留服务器，Git保存源码、协议、小型证据与hash；逐轮命令/运行库/归档收据见更新日志。
