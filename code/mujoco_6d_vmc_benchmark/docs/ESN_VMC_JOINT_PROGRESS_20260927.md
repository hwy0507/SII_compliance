# VMC teacher＋ESN 联合优化：首轮结果与运行入口

01:18 CST补充：八组重建全部完成，continuation_v3接续全部十组训练；八组15条新回合的独立实际奖励核验通过。
补齐计算账本，物理数据复用和废弃/重建梯度分账；两个direct初始同噪声预热各有Task成功但穿透0.98245mm，
Strict均失败，不是梯度学习后的成功。新最终矩阵仍未开始，全部16方法和失败将保留，详见15小时记录第八阶段。

10月9日01:05 CST：144经典筛选＋48确认完成，Task/Strict均0。独立原生伺服对照确认新平滑奖励
把4ms更新误按物理0.05ms归一化，首阻抗回合成本0.366185应为0.00457731（约80倍）。
source_v9修复并通过积分加密不变性/区间可加性测试；八个metric作业回合边界保存后重建，
七组已接续并进入实际梯度，direct metric seed1的55932条历史转移仍在重建。
两个task奖励作业未停，环境/gate/actor不变；旧权重、失败和额外计算全部保留，final24仍封存。
强enhanced teacher实际使用本体48D/估计负载及共享名义指令，不能自动当成特权策略排除。
完整证据见15小时记录第六/七阶段；最终新矩阵和收敛证据尚未完成。

23:54 CST新快照：经典144/144筛选完成，Task/Strict均0，无基础设施失败；48回合确认已开始。
direct metric/task约3.65/3.725万交互，本接续段26/36回合无成功，6/14条因原穿透线早停。
独立动作/hash/optimizer检查通过，但多数停approach，不能声称RL充分训练。
三类参数shield各1375步重放误差0；阻抗02的13750条原生伺服日志满足等效命令/加速度/力矩slew约束。
日志频率实际250Hz，纠正“每个物理子步”的描述；磁盘遥测是预防调整，不是已证实的OOM修复。
两组RL和确认作业继续，final24仍封存。详见15小时记录第五阶段及服务器对应四份审计JSON。

## 2026-10-08 21:23 CST起：15小时baseline修复与重新比较，进行中

用户新授权本机/Spark算力用于15小时修复，截止次日12:23 CST；最后5小时留给模型冻结与统一评估。
已完成独立VMC单位修复/阻抗投影参考与执行命令限制的代数验收；补齐RL优化日志、真实力矩平滑成本和初始potential。
服务器新run `arm1:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`，
10路上限、每路单线程3GiB，旧暂停进程不动。首诊断事件名错误在报告阶段退出，失败保留并用既有settle模式独立重试。
22:10 CST：经典验收6/6完成、Task/Strict均0/6，高刚度阻抗虽到retreat但物块掉落；
经典筛选18/144完成。两组direct RL在4125步安全保存后用source_v4接续，
嵌套optimizer日志修复及真实梯度/保存恢复探针通过；闭环梯度烟测仍运行。
没有新的最终成功率，旧384表不改。
详见 [15小时记录](BASELINE_REPAIR_15H_20261008.md)。纯RL没有混入示范，不要求最终ESN胜出。

22:35 CST补充：RL首5500步真实梯度烟测通过后，独立重算修正了首力矩差分的人工初始化成本。
metric从相同原始转移重建学习器，task奖励不受影响；两组均在source_v5接续，未重跑物理。
阻抗丢物定位到厚桌角接触期间的夹持滑移，失败仍保留；最终统一矩阵尚未启动。

23:05 CST：source_v7有限接续服务已启动，等待现有经典筛选，随后确认/冻结先验并启动剩余8组RL。
开发排序加入实际物块3D放置距离以避免空手retreat获优先，保留原排序；不改gate、不解封final。
5维RL优化器探针、1375步VMC完整状态/动作重放及六项独立物理指标检查通过。
计划22:00 UTC在回合边界收口训练，再做统一开发/最终评测；原次日12:23 CST截止不延长。

23:24 CST：原接续器在派发前被v2/source_v8替代，已有仿真/训练不动。真实RL cgroup达到3GiB并有
回收压力但无OOM；后续原生阻抗日志改为磁盘顺序float64，10000行NPZ逐位一致及控制律契约通过。
screen116/144完成，direct RL约2.8/2.9万交互仍无训练Task成功；新最终条件仍未打开。

## 2026-10-08：经典/RL 实现审计，尚不能作为充分优化的论文对照

用户要求检查baseline是否实现不足。本轮复现VMC读出/action解码的2/2/1.6倍单位不一致；
阻抗4cm边界切向积分停滞，首条件末段持续到边界，且其原生力矩路径不消费上游受限关节命令。
五个最终RL checkpoint有约4.9万真实交互、36–38个训练回合，但训练Task/Strict均零，
缺少actor/critic loss等收敛记录。未确认导纳方程或官方RL更新符号错误。
旧384回合统计不变；其0/24不能直接支撑“ESN优于完善经典控制/充分训练RL”。

详见 [实现公平性审计](BASELINE_IMPLEMENTATION_FAIRNESS_AUDIT_20261008.md)。
已核验源码/数值探针/训练链证据在
`arm1:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_implementation_audit_20261008/v2/`。
已完成只读诊断与归档；本轮无训练/仿真运行中。未完成修复后开发验收、因果消融和新统一评测。
本轮没有改控制器、环境、gate或checkpoint；后续修复不能以确保ESN胜出为验收目标。

## 2026-10-08：office-v7 统一24条件最终完成

20:45:50 CST，本批16方法×24条件全部完成，384/384个55秒回合，无基础设施失败；八路评估与最终报告服务均正常退出。ESN Task/Strict为20/24、16/24，matched RNN17/24、14/24，matched MLP15/24、12/24；enhanced teacher24/24、20/24。经典三类、参数RL三类、直接RL两类和nominal zero均0/24真实任务成功。ESN相对matched RNN的RMSE/峰速低4.61%/2.53%，峰矩高2.55%；最坏穿透0.696mm，仍未全部安全通过。配对精确McNemar p(Task/Strict)=0.5078/0.7744，不声称显著全面优势。

完整表、接触覆盖、失败与统计局限见 [最终报告](OFFICE_V7_UNIFORM24_FINAL_20261008.md)。
服务器 `arm1:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/report_final/`。
已完成全部评估、独立审计及最终核验；本批没有运行中作业。baseline性能修复与ESN安全泛化仍未完成。
以下为历史进度，旧“运行中”状态由本条覆盖。

## 2026-10-07：峰值力矩代理与泛化读出开发（本轮）

- 固定 parent ESN reservoir 和 canonical48D/action7，本轮只改 readout 拟合；环境、gate、执行器限制和 sealed 24 条件均未改/未读。
- 36 候选固定网格在 20/5 identity split 上完成。最佳平滑候选：`ridge=1.0, smooth_weight=0.1, action_weight=0.005`，checkpoint SHA256 `69ecee9d57f34d67be5bec47a4be621d58b9957cc066b1fad0cac7bf588146e4`。
- 离线 validation：MSE `0.000612`、delta energy `0.009489`、action energy `0.009701`、最大单步跳变 `1.366`；父 ESN 对应 `0.000242/0.014357/0.012396/1.566`。噪声折中候选 SHA256 `c327ee61c583beb5a392b3752496f6e8eabc136e181551408d4471ded7acab6e`。
- 运行状态：训练/离线 replay 已完成；闭环 development 尚未完成。兼容 `.venv-canonical-rl` 已找到，但本机受限容器无法建立 worker 所需的 `MemoryMax≤3G` cgroup（`systemd-run --user` bus 不可用），arm1 SSH 也不可达；未启动 formal dt=5e-5 sealed 评估。物理步数、task/strict、真实峰矩、RMSE、峰速均未新增。
- 证据：`docs/ESN_TORQUE_GENERALIZATION_20261007.md`、`outputs/esn_torque_generalization_20261007_grid/REPLAY_COMPARISON.json`；服务器归档 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/` 已核验。失败原因和未完成项保留，不把离线代理指标写成物理通过。

## 2026-10-07：ESN 重点指标全方法表

已将用户指定的 16 个方法统一统计 Task/Strict、RMSE、峰速、接触 P95、恢复率和最大穿透，见
`docs/RESEARCH72_ESN_SELECTED_METRICS_ALL_METHODS_20261007.md`。不构造单一加权总分。

## 2026-10-07：柔顺性指标统计

统一 `/24` 回合已重算球/人手/棍子接触 P95、冲量、接触时长、恢复率、穿透和力矩总变差；ESN 的接触力较低，
但恢复率仍低，不能仅凭低接触力宣称柔顺性全面优于 RNN。详见 `docs/RESEARCH72_COMPLIANCE_METRICS_20261007.md`。

## 2026-10-07：统一主表口径

最终论文主表采用每个 family 一个冻结模型、同一 24 个 held-out 条件的统一 `/24` 矩阵，见
`docs/RESEARCH72_UNIFORM24_MATRIX_20261007.md`。三 seed `/72` 结果保留为敏感性附录，避免把经典单模型
与多 seed 神经模型混用分母。

## 2026-10-07：因果储备池状态变化读出实验

针对最终矩阵中 ESN 与 matched RNN 差距较小的问题，完成一项只修改 ESN 读出的机制实验：固定
128 单元多时间尺度储备池和 parent 读出，加入因果 `Δh`/`|Δh|` residual，并用 RMS 状态变化门控
小幅输出（阈值 2.0、gain 0.25）。48D 本体输入、action7、原 gate、执行器限制和正式 `dt=5e-5`
均未改；禁止字段审计通过。

固定身份留出离线审计中，修正解码后的因果 ESN MSE `0.000228972`，matched RNN `0.000234517`；清空储备池后
因果 ESN 的 memory gap `0.006588982`，RNN 为 `0.006481536`。这支持 ESN 确实利用了储备池历史，
但瞬态窗口 MSE 仍高于 RNN，不能声称全面优势。

服务器已核验的 office-v6 开发锚点中，旧 v3 gain=0.25 从 parent ESN 的 task/strict 失败提升到通过，且
RMSE `29.400 mm`、峰矩 `49.032 Nm`、峰速 `0.3461 m/s`，均优于 matched RNN 的 `29.938 mm`、
`54.435 Nm`、`0.3863 m/s`；该结果仅是单一开发锚点，仍需多条件复核。服务器归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_state_delta_gate_dev_20261007_v3_gain025/`。

该服务器锚点属于解码修正前的 v3；本轮已生成 v4 并发现真实父解码为 `clipped_linear`，因此 v3 数字
不能直接当作 v4 闭环结果。v4 目前只有离线审计和本地 office-v5 smoke，待同一 office-v6 worker 复核。
本地 office-v5 兼容 smoke（不同环境版本）task/strict 为 false/false，已单独保留，不能混入 office-v6
公平矩阵。完整方法、离线审计、失败原因和下一步见 `docs/ESN_CAUSAL_STATE_DELTA_EXPERIMENT_20261007.md`。

## 2026-10-07：最终 912 回合闭合

最终模型锁定后一次性开启 24 个 held-out 条件，38×24=912/912 完成；task 284、strict 218。
ESN(readout refit) 60/72 task、43/72 strict，matched RNN 58/72 task、44/72 strict，matched MLP 28/72 task、26/72 strict。
ESN 的 33.780 mm RMSE 和 0.372 m/s 峰速均值支持任务/速度权衡优势，但 strict 与峰值力矩不全面领先。
最终物理矩阵、360 条 RL 独立 replay、三视角媒体和失败回合保存在服务器本轮根；详见
`docs/RESEARCH72_FINAL_RESULTS_20261007.md`。研究目标已从“等待最终评估”转为结果审计和论文表述。

## 2026-10-04 11:00UTC：补核两个seed303 RL训练段

VMC参数303/直接task303的32新回合、43991转移/35192800子步及43959可核验奖励一致；
32首项仍排除，54.64秒穿透失败保留。累计240回合训练链审计，不是最终冻结策略的任务表现。
四证据服务器本轮根`rl_completed_continuation_audit_v4/`与Git同字节，详见RL_REWARD_AND_CONTINUATION；
0新增仿真/学习/选模，原队列继续、最终统一评估及投稿结论未完成。

## 2026-10-04 10:42:08UTC：容量与队列进展

最新不可变快照RL370053交互/590136更新、三开发37/168、42/168、21/144，含5短回合，120拟合完成。
队列0/2自然进入49500阶段，尚非15模型边界完成。原容量模型剩余开发理想17.598–18.432h，
完整912与2h收尾后余量4.424–6.376h，不含全部额外等待/加载，不增搜索。实际PID持续存活，最终仍封存。
两个1042证据服务器本轮根与Git同字节，详见RESEARCH72_CAPACITY_FORECAST；0新物理/训练/选模。

## 2026-10-04 10:00UTC：补核直接动作RL训练记录

direct office-task 301自然完成27500上限阶段，实际26746步；16新回合/16996800子步与21230可核验奖励一致，
16首奖励仍未核验，一条24.84秒穿透失败保留。三工具无新增物理/梯度，原开发与RL继续。
服务器本轮根`rl_completed_continuation_audit_v3/`三文件与Git证据同字节，详见RESEARCH72_RL_REWARD_AND_CONTINUATION。
这是训练数据一致性，不是冻结策略最终成功率；最终912/独立actor/论文结论仍待完成。

## 2026-10-04 09:44:06UTC：既定队列推进与容量复核

新公开快照RL331644交互/513318更新，neural-LR32/168、context38/168、readout19/144，三组含3短失败。
原预测器剩余开发理想18.624–19.506h、完整912/2h收尾后余量4.317–6.317h，仍非含等待/冷加载保证。
原监督/训练PID存活，最终24封存；0新仿真/学习/选模，不据正余量加搜索。两个0944证据Git与服务器同字节，
共享本轮根及具体hash见RESEARCH72_CAPACITY_FORECAST；完整比较/独立最终actor/论文结论仍未完成。

## 2026-10-04：已完成拟合成本对照

新增RESEARCH72_TRAINING_COST_TABLE，从固定08:45:42UTC快照核算120作业/288ridge/384000更新，
ESN60ridge/seed、无记忆36、普通网络7拟合/seed、同特征9。披露不同参数、父权重和teacher共享成本，
不称等训练预算或全方位效率优势；当前RL/开发继续、最终封存，0新增物理/学习/选模。

## 2026-10-04 09:14UTC：补齐新的RL训练证据

六新自然完成27500阶段的130回合（含38短失败）独立核验：129707转移父前缀/新增真实观测动作、
103765600物理子步区间与129577奖励一致；130首奖励仍未核验。0新物理/actor/训练，原队列不改。
失败训练轨迹不能当最终策略成功率或ESN优势。证据共享本轮根rl_completed_continuation_audit_v2，
详见RESEARCH72_RL_REWARD_AND_CONTINUATION；最终24封存、912及完整投稿结论仍未完成。

## 2026-10-04 09:04:53UTC：最终后处理接通

原研究作业继续；新一次性监督PID2550310实际waiting_for_final，单线程/3GiB，0新物理/训练/选模。
待最终批次终止后运行原a3工具的15个RL独立动作回放、38×24统一统计及全部模型固定条件三视角视频；
短失败/缺失保留，无自动重试。本机/Spark各9项合成编排测试通过，不等于实际最终审计。
模型锁和912仍未产生；论文解释/目视检查未完成，不能声明ESN领先。详见RESEARCH72_FINAL_DELIVERY_20261004.md，
服务器根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，
新源码final_delivery_source_v1及登记final_delivery_v1已核验，未改活跃runtime。

## 2026-10-04 08:45:42UTC：成本核验与审计范围更正

新公开账本0850保存原回合身份/trace与audit hash，neural-LR29/168、context34/168、refit16/144，含2条短回合。
RL累计287566实际交互/425162更新，120拟合完成；原预测剩余开发理想19.736–20.669h，完整912/2h收尾后余量4.127–6.178h，非保证。
DEVELOPMENT_AUDIT原仅汇总worker已有数值，本轮明确不是独立物理子步复算；完整阶段和最终审计仍未完成。
实际七服务cgroup OOM/kill均0，max非零；7282022共享源码3297文件逐内容/大小/模式/集合核验。
最终24仍封存，稳定作业不改、不增加搜索。快照/预测Git同字节，服务器根
arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。

## 2026-10-04 08:36UTC：neural-LR与readout继续，最终条件仍封存

服务器收据更新为 neural-LR29/168、context gate34/168、context readout refit15/144；RL与final transition继续，尚未生成模型锁或正式评估。

## 2026-10-04 08:26UTC：neural-LR与readout继续，最终条件仍封存

服务器收据更新为 neural-LR28/168、context gate34/168、context readout refit14/144；RL与final transition继续，尚未生成模型锁或正式评估。

## 2026-10-04 08:17UTC：context gate继续，最终条件仍封存

服务器收据更新为 context gate34/168、neural-LR27/168、context readout refit13/144；RL与final transition继续，尚未生成模型锁或正式评估。

## 2026-10-04 08:07UTC：neural-LR继续，最终条件仍封存

服务器收据更新为 neural-LR27/168、context gate33/168、context readout refit13/144；RL与final transition继续，尚未生成模型锁或正式评估。

## 2026-10-04 08:00UTC：前置开发继续，最终条件仍封存

最新服务器收据为 neural-LR26/168、context gate33/168、context readout refit13/144；RL与final transition继续，尚未生成模型锁或正式评估。

## 2026-10-04 07:49UTC：队列继续，模型仍未冻结

服务器收据更新为 neural-LR26/168、context gate32/168、context readout refit12/144；RL与衔接监护继续，模型锁和最终评估尚未产生。

## 2026-10-04 07:37UTC：readout开发继续，最终条件仍封存

服务器收据更新为 context gate32/168、context readout refit11/144、neural-LR25/168；neural-LR worker仍active，RL边界监护与final transition继续刷新，未创建最终评估。

## 2026-10-04 07:31UTC：开发继续，最终条件仍封存

服务器收据更新为 neural-LR25/168、context gate32/168、context readout refit10/144；RL adaptation 与边界监护继续，final transition 仍等待前置，未创建最终评估。

## 2026-10-04 07:22UTC：服务资源审计，最终条件仍封存

arm1 服务仍 active：neural-LR24/168、context gate31/168、context readout refit10/144，RL adaptation 与边界监护继续；final transition 仍等待前置，最终评估未创建。3GiB 开发/RL队列未出现 OOM/kill，未重启或新增作业。

## 2026-10-04 07:08UTC：开发队列继续，最终条件仍封存

只读复核服务器收据：增强网络23/168、context gate31/168、context readout refit9/144；RL adaptation仍运行，RL共同边界监护为`watching`。连续衔接仍`waiting_for_predecessors`，`final_evaluation_v1`不存在；没有新增派发或重启，失败仍保留。

## 2026-10-04 06:50UTC：服务器队列继续，最终条件仍封存

读取服务器既有收据：增强网络开发完成22/168、context gate完成30/168、context readout refit完成8/144；RL adaptation仍运行，RL共同边界监护为`watching`。连续衔接仍`waiting_for_predecessors`，`final_evaluation_v1`不存在；未重复启动或手工派发，失败仍在分母中。

## 2026-10-04 06:18UTC（文件名0717仅为运行标识）：登记开发和RL继续，尚未解封

最新公开快照（文件名`EXPOSURE_SNAPSHOT_20261004_0717.json`，内部`created_utc=06:18:25.398327`，0717仅为运行标识）RL177603交互/206734更新，context29/168、增强网络19/168、新refit6/144；三RL队列及其监护仍存活。
连续衔接PID2513613仍`waiting_for_predecessors`，final_evaluation_v1不存在，最终24条件封存；不重复启动或手工派发。
新预测剩余开发22.511–23.573h、最终912物理22.824–23.942h、2h收尾后余量3.678–5.857h；不扩展搜索。
快照/预算证据已提交，完整开发、共同RL边界、冻结、正式评估和独立最终审计仍未完成。

## 2026-10-04 06:09UTC：连续衔接已启动，最终条件仍封存

一次性sii-r72-final-transition-v1/PID2513613已实际运行，只等待全部既定开发/审计/RL边界关闭；无定时任务、无新搜索。
完成后按已有规则依次学习选模、38模型汇总、冻结、912最终评估，缺前置/失败/已有最终输出即保留停止；8项编排回归通过。
当前waiting_for_predecessors，steps为空；五项仍未结束，尚未实际选模/冻结/开封。后续须先查该进程与final_transition_v1/execution.json，不重复手工派发final。
两源与登记已核验共享本轮根final_transition_source_v1/final_transition_v1，actual runtime固定a3b8c97；详见RESEARCH72_FINAL_TRANSITION。
服务器arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
05:59快照RL165754交互/191536更新、context28/168、增强网络19/168、refit4/144；含最终912和2h收尾的理想余量3.67–5.87h，不再扩大搜索。
独立最终RL actor、统计/媒体与投稿结论仍需在物理完成后执行，目标active。

## 2026-10-04 05:51UTC：五家族RL奖励物理输入闭合

从原始时间戳独立划分并复算62训练回合82004区间/65603200物理子步，误差/力矩/时长/过滤动作核对通过，4个短失败全部保留。
direct_metric301完整续训到27336步/22回合，5500父前缀与新增21836转移核验；新21818奖励精确一致，18首奖励未核验。
累计81942缓存奖励核验/62初始potential未知首项；物理归约通过不证明potential、逐梯度更新、真机物理或最终策略表现。
新工具六项边界/篡改回归通过，Spark1线程1GiB约33s、0新物理/actor/拟合；三完成结果276836字节全hash/大小核验。
本轮根reward_intervals_audit_v1与两源reward_intervals_source_v1共享，Git原字节小证据，见RESEARCH72_RL_REWARD_AND_CONTINUATION。
服务器arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
05:41已复核所有原队列PID/服务存活；开发及RL继续，不追加搜索，24最终封存、完整比较未完成。

## 2026-10-04 05:35UTC：最终边界汇总预检和继续运行

完整38模型汇总回归增至8项，真实解析15个合成RL共同边界/监护关闭账本，包含49336/49500步差异；
拒绝缺失边界与关闭hash篡改，后续1375收尾步记成本而不选权重。没有执行实际最终选择或解封。
当前13完成存档964文件约1.84GB经真实候选验证函数核对，两遍hash耗时1.99/.91s；不据此代替未来冷加载/推理/物理耗时。
main9ccabdd的3284源码已完整核验归档。最新公开快照RL151254交互/171034更新，context26/168、增强网络18/168、refit3/144，稳定队列继续。
本轮根EXPOSURE_SNAPSHOT_20261004_0535.json SHA2809fa0829b508af25ede9c933cbca54b9a804441589cca64ed59c786ebe83a9；
服务器arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
最终24保持封存，整阶段开发/全部RL共同边界/912最终比较仍待完成；不因少量新样本提前宣称ESN优势。

## 2026-10-04 05:19UTC：RL完整续训和奖励核验

导纳/VMC301自然完成27500步/20回合/45002更新，存档与5500继承前缀/新增22000实际转移核验通过；不再只是16500中途快照。
冻结奖励实现重算五RL家族代表段60124缓存奖励逐值一致，44首奖励因初始potential未保存明确排除；原短失败及补偿项保留。
四回归通过，未从子步独立重算区间、未重算梯度，0新actor/物理/拟合；共享五审计文件全hash/大小核验，Git小证据同字节。
详见RESEARCH72_RL_REWARD_AND_CONTINUATION，当前RL140438交互/154400更新、context25/168、增强网络17/168、新refit2/144。
实际PID与三RL内存事件核验，OOM0，不重启；含最终912和2h收尾的理想余量3.63–5.86h，额外等待仍非保证。
最终24封存、目标active；继续已有全部开发与RL共同边界，不新增搜索或预定ESN胜者。

## 2026-10-04 04:59UTC：新模型部署成本与有效RNN学习

新18模型在同公开训练序列的74,250次actor-only计时完成，18模型warm重放精确，0拟合/物理。
ESN3780学习系数、32.2–32.8μs；普通MLP5504/7.85–7.91μs，RNN21888/9.89–10.10μs，不能称ESN推理更快。
新matched RNN三个seed选择4000/3600/3600更新，验证动作MSE略低于ESN；全部144闭环仍按原计划保留，不用代理MSE判任务成功。
本机1线程3GiB计算，六文件已核验共享refit_inference_archive_v1，PROFILE Git同字节，见READOUT_REFIT_RESULTS。
原四仿真继续、最终24封存；仅补成本与实现证据，没有新搜索或最终模型选择。

## 2026-10-04 04:52UTC：首条refit闭环与最终汇总预检

refit seed301/development000 worker审计task/strict通过，完整55s；RMSE30.699mm、峰力矩49.981Nm、峰速度.349058m/s、外穿透.143599mm。
请求/filter/储备池重放误差0，原始失败/其他条件不变；仅1/144完成，阶段独立审计尚未做，不据单条宣布泛化。
旧context24/168、增强网络15/168，三RL队列继续持租约，最终24仍封存。
选择器JSON证据路径同类错误提前修复；72候选完整合成账本、篡改和缺回合拒绝各3项在本机/Spark通过，原38模型汇总5项通过。
零实际选模/新物理/拟合；selection_guard_source_v1两源核验，实际最终选择须用已修复最新入口，不能回用旧9e版本。

## 2026-10-04 04:36UTC：新数据实际重训完成，144开发启动

teacher40完整采集完成，task40/40、strict25/40；实际导出20训练＋5验证、34,375帧。
独立验证8身份审计：旧7任务/6strict→新8任务/5strict，桌角力模积分上升，合格验证柱接触0/5；失败全部保留。
04:20:58前瞻登记修订02，原三条RL实际持租约和P90容量余量均核验后，04:22–04:26本机完成18共享数据拟合。
ESN仍128固定储备池＋固定本体交互，只训练3780读出；6纯固定模型72候选独立重建通过，18actor共24,750帧输入隔离/重放误差0。
763文件已核验到共享本轮根local_context_readout_refit_archive_v1，完整18×8开发登记并启动单租约队列，当前0/144；无离线筛掉模型。
登记路径字符串处理错误在写出spec前修复，原训练不重跑；新成本工具计入已登记144，即使未派发也不遗漏。
RL导纳/VMC301各16,500步存档保留5,500前缀精确一致，新增11,000条真实转移复核；不是逐梯度或最终策略证明。
q1自然取得租约，实际一次性让槽工具events为空，没有对研究进程暂停/恢复信号。
当前累计120拟合、RL106418交互/102858更新、context23/168、增强网络14/168；最终24封存，912完整比较未开始。
源/参数/seed/hash和独立证据见RESEARCH72_READOUT_REFIT_RESULTS；服务器根
arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
剩余开发理想24.33–25.47h，完整最终和2h收尾后余量3.48–5.74h，额外等待仍是风险；不增加新搜索。

## 2026-10-04 03:51UTC：teacher训练数据改善与柔顺代价

已独立复算相同32训练身份的新旧teacher共64完整回合/7040万物理子步，协议/config/MJB/trace/chain/native/telemetry及原三指标核验通过。
新teacher task29→32、strict18→20；RMSE40.779→40.233mm、峰力矩50.885→50.764Nm、峰速度不变。
推杆P95力16.951→12.628N，但桌角力模积分8.169→22.369Ns、接触时长4.112→8.583s；不是全面柔顺改进。
strict8改善6退化，20新合格示范的柱接触仍仅2条（与旧2条身份不同），旧失败全部保留，不更改资格/gate。
结果68文件已核验共享teacher_data_train_comparison_v1，SUMMARY Git同字节；见RESEARCH72_TEACHER_DATA_QUALITY。
采集37/40、context18/168、增强网络10/168；未新拟合或登记修订02，先等完整验证/动作filter导出再判断追加学习。

## 2026-10-04 03:27UTC：统一RL最终边界已登记

后续容量复算已计全部15模型每个最多2750额外步：剩余开发21.91–22.94h，最终912物理22.82–23.94h，2h收尾后余量7.18–9.32h。
仍是假设及时取租约的预测；7项算术检查通过，共享budget_forecast_source_v5与BUDGET_FORECAST_20261004_0327.json，Git原字节。没有据此新增拟合。

为保护完整38×24最终矩阵，03:24在任何模型进入49,500阶段前为全部15个RL登记该自然完整回合边界。
原80k优化器日程/奖励/runtime不变；后续多余阶段仅精确SIGUSR1温和收尾，最多额外2750步/模型计成本但不选择权重。
监护服务已启动、零信号；Spark7项测试含真实临时子进程通过，最终选择5项通过；缺边界/闭环证据不能冻结。
源码和登记证据已核验共享`rl_final_boundary_source_v1`/`rl_final_boundary_v1`，详见RESEARCH72_RL_FINAL_BOUNDARY。
真实成本快照teacher32/40（32训练均task通过、20strict），context16/168、增强网络8/168；RL72418交互/44856更新。
尚未新拟合/登记修订02，24最终条件保持封存；当前仍是运行中研究，不是RAL投稿完成或ESN全面领先。

## 2026-10-04 02:51UTC：实际RL接续起点与串行队列容量

导纳/VMC301均已完成首续训回合至6875累计步；独立进程从父checkpoint重放真实首随机动作，精确一致。
每个只一次actor、0更新/物理，未冒充全段优化器或最终策略回放；6合成检查通过，源与两结果在共享rl_resume_action_audit_v1，Git同字节证据。
另两个首段存档核验通过；任务奖励303的train031在carry外穿透2.560352mm提前中止，真实5168步/338更新保留。
新预测补上实际串行RL最长队列：全部80k时理想剩余开发31.28–32.70h、最终22.82–23.94h，含2h收尾余量+0.67至−1.88h，尚未计租约等待。
6项容量检查通过，budget_forecast_archive_v4四文件已核验；需据真实稳态提前安排共同预算边界，不能等48h截止再处理。
当前teacher26/40、context13/168、增强网络4/168；原四仿真继续。无新的停止信号/预算修订/拟合，最终24封存。

## 2026-10-04 02:22UTC：论文方法正文与首任务奖励RL存档

新增英文RESEARCH72_MANUSCRIPT_METHODS：按实际公式描述128多尺度储备池、2884学习系数、同特征及普通网络差异，
明确点损失并非跨架构完全等价、参数RL为7/5/7维、placement为25Hz检查、strict不含强制接触覆盖。
仅方法/实验设置草稿，不写未完成的最终结果或预设ESN优势；已核验归档本轮根methods_draft_v1/docs/，正文SHA b7d2feabb5c2477ce56943f0fd1c83bdabc9f50cec06cdc2576c3313ddd2b5c3。
新增直接任务奖励302/阻抗303存档审计，两模型各5500步/1002更新；rl_saved_state_audit_v2原件与Git同字节，详见RL_MEMORY_PREFLIGHT。
最新采集21/40、context10/168、增强学习率组2/168；RL八首段完成/累计46875交互，q1仍等租约，OOM0。
无新拟合/物理派发/预算修改，稳定四仿真继续；实际续训、最终模型锁/24留出/完整比较仍未完成。

## 2026-10-04 01:54UTC：首5D存档、名义八条件与剩余容量

六RL模型各5500步/1002更新；独立存档全部文件、回放/计数/RNG/44源、24训练轨迹hash核对通过，含真实5D阻抗302。
零推理/物理/梯度，实际续训和最终actor回放仍待完成；3文件rl_saved_state_audit_v1已共享核验，Git保留原结果和5D manifest。
名义规划＋WBC八条完整开发/审计结束，task/strict0/8、均停carry；低RMSE不算完成，见CONTROLLER_CONFIRMATION。
新teacher16/40、context8/168、学习率组已接续；RL累计35750交互。全cap预测剩余开发31.57–33.04h、最终22.82–23.94h，
含2h收尾余量约+1.20至−1.39h；不追加144开发或跳过新权重开发验证，修订02仍未登记。最终24仍封存。

## 2026-10-04 01:44UTC：物理装置与论文解释核验

精确MJB/七源hash/公开1375帧只读检查：1kg自由球、80g自由物块、摩擦抓取、有限质量驱动人/杆；
实际任务装置非mocap，但模型确有场外旧mocap，不能全局称无mocap。驱动力限幅不等于接触峰力上限。
零物理/拟合/封存读取，3文件apparatus_audit_v1已共享核验，Git小证据同字节；见RESEARCH72_APPARATUS_SCOPE。
新teacher14/40、名义7/8、context7/168；RL四个首段5500步/1002更新，首5D模型仍在跑，第三queue等租约。
两子服务缓存回收增加而OOM0，不重启；最终24封存，没有新ESN优势或可投稿完整结论。

## 2026-10-04 01:19UTC：纯ESN身份独立核对

12 ESN＋6无记忆拟合的全部216候选固定矩阵、时间尺度、gate按seed精确重建，合同拒绝额外学习层；每模型两项内存负对照通过。
本机1.183s、无新训练/推理/物理，Spark档案逐hash相同；fixed_reservoir_audit_v1源码与结果已核验共享，Git小证据同字节。
这是只训练读出的实现依据，不是新颖性/闭环稳定/泛化证明。详见RESEARCH72_INPUT_AND_MEDIA_AUDIT。
RL两queue第二模型开始梯度，3GiB限额发生file-cache回收、OOM仍0；原稳定作业继续，不改物理或预算，最终24封存。

## 2026-10-04 00:56UTC：真实RL首段保存与追加工作容量

首导纳301/VMC301各5500步/1002更新并保存，75文件全hash、回放/终止/恢复边界只读核验通过；两子服务峰2.67/2.66GiB无OOM。
已轮转下一模型，第三仍等租约；还不构成真实续训或最终效果。原始manifest已入Git，权重/轨迹留服务器。
更新预测既有开发32.697–34.220h、最终912纯物理22.824–23.942h；追加144会挤占保留比较，修订02仍不登记。
新teacher和记忆机制开发继续；不减baseline、不改gate或开封，详见RL_MEMORY_PREFLIGHT和CAPACITY_FORECAST。

## 2026-10-04 00:35UTC：参数确认完成、RL和新teacher接续

64完整确认及独立审计完成；选teacher09/adm03/imp02/vmc11，teacher8/8task、7/8strict，柱子/link6超穿透失败保留。
原teacher同身份8/4，改善尚未转化成新ESN结果；新40训练/验证实际示范采集中。经典均0/8task，有限预算不称理论上限。
两条RL已真实运行且完成首回合，子服务峰约1.94GiB、OOM/max0，仍warm-up更新0；第三队列等租约。物理总并发4。
已知teacher最终入口55s逐值重放通过，真实24最终未读。三步长短诊断50→25μs峰力差10.4%、积分差.5%，不能声称峰力收敛。
全部源/选择/汇总hash见RESEARCH72_CONTROLLER_CONFIRMATION_20261004及RESEARCH72_NUMERICAL_DIAGNOSTIC；Git证据同字节。
官方SimbaV2完整225源文件归档/live核验，独立RL额外回放及报告14合成检查通过；实际新RL审计待训练/评估完成。
更强网络/context队列接续；修订02未登记、无最终优势结论。

## 2026-10-03 23:47UTC：RL动作来源独立审计准备

确认42/64，四队列运行。独立冻结RL actor回放入口及最终报告覆盖连接14项合成检查通过；保留缺失/失败，不重算物理。
5文件源码overlay已在rl_actor_replay_engineering_v1/evidence核验，详见RESEARCH72_RL_ACTOR_REPLAY_20261004。
真实新RL及其审计尚未完成；最终24不读，旧作业源不热改，修订02未登记。

## 2026-10-03 23:30UTC：统一对比图导出准备

16方法、五类接触的SVG/PNG导出三项合成测试及目视核验完成；图直接读取已审计报告，不重算区间或挑选方法。
缺失/失败/无配对保留，成功接触子集仅条件诊断；0物理/拟合，真最终封存不读。
figure_engineering_archive_v4/evidence全10文件已核验共享，详见RESEARCH72_FIGURE_EXPORT；teacher/经典确认仍运行，后续组待前序。

## 2026-10-03 23:10UTC：投稿方法定位继续核对

参数确认16/64完成、四仿真稳定。补读Shen等RAL作者稿全正文，明确气动物理储备池/滞回补偿与本项目接触操作的区别；
ICRA2025 RC+FORCE和2026 ESN无传感力估计仅元数据/摘要核对，不能冒充全文复现或首次性证据。
8文件related_work_review_v2归档已核验；0新仿真/拟合，最终封存不读，详见RESEARCH72_METHOD_POSITIONING。

## 2026-10-03 22:57UTC：RL内存预检与误差口径

实际learner依赖/80k Replay＋1.086GB等量常驻压力下，单GPU4周期/8工程更新峰值2.649GiB，无OOM，更新丢弃，
工程checkpoint完整hash不变，0物理/0候选。未替代真实三learner/5500步续训验证，见RESEARCH72_RL_MEMORY_PREFLIGHT。
核对RMSE原定义为当前task-stage goal距离，不是共享时间参考轨迹；最终列名/说明明确，不改数字或gate。
参数确认继续；最终封存、新组待前序、修订02仍未登记。

## 2026-10-03 22:45UTC：初始264回合完整独立审计通过

33模型×8公开条件全264完成，261完整/3短失败保留，四队列各66条独立物理/动作/状态复核完成。
ESN点版19/24task、9/24strict，积分版11/24、4/24；三个点版seed严格3/8、4/8、2/8，不挑seed宣称稳健。
同特征RNN六权重均选择第0步父ESN初始化；小学习率增强组仍须闭环，不能把当前相同计数当充分优化对照。
推杆暴露点版24/24、积分21/24、无记忆23/23完整；P95、累计负载和恢复存在权衡，没有全面优势。
共享public_initial_report_v2/REPORT.json SHA adb7ff8e71117d09a612796e6a56ca02b17b430054ca707f51832112194d7b4d，Git同字节证据。
汇总v1的Path类型错误保留，修复后v2仅重做JSON报告，0新物理/拟合。完整表/来源见RESEARCH72_INITIAL_DEVELOPMENT。
teacher/经典64确认已开始；增强组/RL/再采集待前序。24最终封存，修订02未登记，未达到投稿结论。

## 2026-10-03 22:05UTC：短步长诊断登记，初始246/264

第七开发身份完整，初始ESN/matchedRNN各4/6放置、1/6严格；仍未完成整批独立审计。
登记原teacher/公开train_000的3×3s步长检查，最多9模拟秒，等待followup和共享租约，当前0派发。
正式55s/50μs、gate及本体输入不变；探针永不当示范、最终成功或任务失败分母，成本单列保留。
9项工程检查通过、已核验独立runtime；不是新的ESN效果。修订02未登记，24最终仍封存。
见RESEARCH72_NUMERICAL_DIAGNOSTIC的源/规范hash与资源说明。

## 2026-10-03 21:35UTC：现有102模型输入边界核对

实际部署load_current回放同一train_000：全部102模型/140250动作精确符合导出；扰动声明18维之外30字段时
动作和82500次可见状态检查逐值不变，checkpoint未改，3负对照通过。不证明真实传感器或闭环安全，0新训练/物理。
已知teacher三视角55s完整工程回放与全帧解码约20.46s，峰值0.644GiB；不是ESN结果或新留出成功。
全部原始hash/源、102行及媒体已核验共享，详见RESEARCH72_INPUT_AND_MEDIA_AUDIT。
四稳定物理队列最近220/264；新teacher、记忆调制组和RL待前序，真正24最终封存，修订02未登记。

## 2026-10-03 21:15UTC：第六条件与追加实验时限

第六公开开发条件完整33候选，初始ESN4/6放置、0/6严格：四条放置的pillar/link7穿透0.223–0.594mm，
另两条停carry；303积分版RMSE247.992mm。此为初始候选开发，增强组仍待验证，不当最终选型结果。
21:09成本快照209/264，完整回合中位351.820s/P90378.758s；若15RL都跑满80k，现有剩余开发理想35.25–37.83h。
额外144回合会挤占最终912回合与收尾；本轮不登记修订02、不新拟合。待teacher数据/真实RL吞吐再核算。
全部失败与gate保留；源/hash/已共享预算见RESEARCH72_CAPACITY_FORECAST_20261003.md。

## 2026-10-03 20:56UTC：拟合追加前的实际RL成本

官方GPU5D/7D探针每次动作＋UTD2约18–19ms，冷编译16–71s，峰值2.07GiB；只是单learner零物理工程计时。
164次更新后权重丢弃，原工程checkpoint5D/7D完整74/73文件hash不变。真实三组竞争、learner＋物理内存和续跑尚待验证。
同预算全部baseline继续；可选ESN新拟合仍须等teacher数据与完整时间核算，不能以GPU利用率决定追加。
初始198/264，第六身份32/33；无新候选或学习预算修订02，最终24封存。详见RESEARCH72_RL_THROUGHPUT。

## 2026-10-03 20:37UTC：首次球撞与25Hz策略时钟

前五完整公开身份全部33初始候选＋原teacher共170轨迹：首段接触0.45–0.50ms，下次actor计算延后9.20–32.20ms；
170/170峰值和首段接触均在那次计算前。不能把低首撞峰值当即时ESN反馈优势；先前姿态/WBC/物理影响仍存在。
不改变gate、指标或actor时钟。4时序测试通过，零新物理/拟合；图/逐轨迹hash已在Spark核验，见RESEARCH72_IMPACT_TIMING。
初始184/264；当前依旧等待完整teacher确认与新组，RL v2等待，学习修订02未登记，最终24封存。

## 2026-10-03 20:15UTC：第五开发条件与baseline覆盖保障

初始169/264；development_004全33模型完整。ESN4/6task、1/6strict，三条放置成功仍因pillar/link7
穿透0.209686/0.279906/0.573083mm失败，303temporal的RMSE250.986mm且仍carry。
原门槛保留，全失败继续计入；不能声称稳健优势。teacher确认及后续新组仍等待，24最终条件封存。
RL首次训练前登记轮转边界5500/27500/49500/71500/80000，确保各组先得到checkpoint；只停零派发旧等待器，
活跃v2、独立runtime_v4已核验；16工程检查通过，实际物理续训未验证。详见RESEARCH72_RL_DISPATCH。
另18统计/报告回归通过，补bootstrap点区间退化标记，原10000重抽数值方案不变，不将[1,1]解释成总体确定性。

## 2026-10-03 19:37UTC：99公开轨迹覆盖诊断

前三完整身份全33候选本体距离诊断完成；训练18整身份留一校准P95=0.308898，未使用验证或开发校准。
ESN303temporal在development_001有72.7%帧超此参照，RMSE124.44mm；302temporal严格成功仍46.9%、95.20mm。
因此不是失败分类器或因果证明。ESN clip约0–0.3%，单纯裁剪不是多数偏离的原因。图/逐帧距离/源码已核验共享，
见RESEARCH72_PROPRIO_SUPPORT_20261003.md；0新拟合/仿真。第四完整条件ESN与matchedRNN各4/6严格。
整体143/264，teacher确认和新组仍等待；修订02未登记，最终24封存。

## 2026-10-03 19:19UTC：下一轮读出拟合入口准备完成

初始开发131/264，第四条件32/33；4物理队列继续。新readout-refit工程入口强制teacher已确认且数据导出完成，
再使用原12组ridge与固定128交互读出；同特征MLP/RNN给相同G，普通网络在数据不变时复用已完成权重/回合。
计划新增12或18模型，仍须在真实拟合前登记预算；目前修订02不存在、无新拟合。14项工程及旧选择链回归通过。
详见RESEARCH72_READOUT_REFIT_PREPARATION_20261003.md。若teacher数据改变不当孤立结构消融，保留全部历史失败。

## 2026-10-03 18:59UTC：接触统计覆盖补齐与第三完整开发条件

初始开发115/264；第三共同条件33候选11task/5strict，ESN与matchedRNN各3/6task、1/6strict。
matchedMLP2/6strict、memoryless1/3strict；ordinaryMLP/RNN0严格。是含损失候选的开发结果，非最终模型泛化率。
全6ESN与原teacher时序图揭示放置阶段窗外人体接触；新v4保留旧指标，补全部实际时长/窗外负载。
7条原生完整轨迹旧字段精确一致，14合成检查通过；没有新拟合或物理回合、无运行快照热改。
逐条hash、全部曲线和登记说明见RESEARCH72_SUPPLEMENTAL_CONTACT_20261003.md；最终仍封存。

## 2026-10-03 18:36UTC：最终入口串联与方法定位

开发100/264已有逐回合AUDIT，第三条件仍32/33；不使用未齐条件决定模型。当前无新拟合/预算修订。
最终38模型候选汇总器完成5项合成/文件衔接检查；相同teacher跳过再采集时核验0新物理并另存closure，
不改历史执行。仍未生成真正最终锁或解封24条件。方法定位文档与公开引用原件已同步服务器，
明确固定特征线性读出非首创、新交互效果未证实；详细hash/路径见UPDATE_LOG。

## 2026-10-03 18:10UTC：第二条件暴露恢复推进问题

development_001完整33候选8task/7strict，ESN与matchedRNN均3/6严格，memoryless0/3。
ESN303点版54.76s才开始release，积分版54.24s才load_transfer，XY虽小仍未完成原55s稳定放置要求；
RMSE102.724/124.436mm。另301积分版柱子穿透0.687mm。全失败保留，不能把接近目标等同任务成功。
全33只读诊断在服务器本轮根public_contact_diagnostics_condition1_v1，hash见UPDATE_LOG；没有新示范/拟合。
最终汇总/媒体和中断保留工程验证完成，仍未打开真正24条件；现有4物理队列保持运行。

## 2026-10-03 17:46UTC：读出结构工程就绪，尚无新拟合

初始开发60/264，四队列稳定。完整首条件代数诊断显示记忆项可覆盖当前负载的反向请求；
新可选r*tanh(G*c)固定交互允许当前本体信息调制记忆读出，仅训练线性系数。
4组合随机工程探针最大NumPy/Torch差5.61e-15；旧102模型完整1375帧重放精确相同。
尚未新增拟合、闭环结果或预算修订02；ESN48/seed cap已满。优先等待teacher选择/真实再采集再决定共享拟合。
已核验服务器本轮根context_readout_engineering_archive_v1及public_contact_diagnostics_v3，详见UPDATE_LOG与结构说明。
单条已知train_000最终入口预演等待前序，仅工程验证；真正24最终条件仍封存。

## 2026-10-03 17:08UTC：闭环动作偏差定位，不当执行标签

首条件33模型完整14task/10strict，ESN与matchedRNN各4task/3strict（各6损失候选回合）。
ESN303柱子-link7最差穿透晚于首次接触0.3914/15.97625s；原teacher在学生观测历史上的
离线查询于41.72s建议z=-0.2049，学生仍+0.3368。说明实际闭环动作与原teacher有偏差，
不能从查询断言换动作必然安全。开发历史没有进入训练，所有请求/实际过滤量/反事实查询分别记录。
本轮服务器根public_contact_diagnostics_v2，Git小证据与源码hash见UPDATE_LOG；原v1保留。
当前37/264开发完成；实测343s/回合，末轮912回合物理约21.72h，后续开发须保留最终评估余量。

## 2026-10-03 16:50UTC：ESN种子稳定性与公平成本

开发24/264已完成、四队列稳定。首条件三seed两损失ESN仅3/6 strict；seed303点/积分外穿透
0.551/0.476mm超0.2mm，点版放置成功也不能当安全成功。尚不能泛化到8开发条件。
102个已拟合模型本地单线程3GiB动作重放误差全0；ESN可训练系数2884，actor-only中位耗时约32us，
普通MLP/RNN约8/10us；宽度相同不等于参数/计算成本相同。实际ns、源码与hash已归档服务器
本轮根inference_profile_archive_v1/inference_profile_v1，精确入口见UPDATE_LOG。
统计模块8项合成测试、预算锁7项保护和恢复删失3项合成测试通过，真实完整回合v3数值与v2一致。
只修正提前终止后的观察时长，不改gate或已有运行源码；24最终身份继续封存。

## 2026-10-03 16:30UTC：首个闭环成功存在，但脱离效果尚弱

96控制器筛选完整且独立审计通过：teacher21task/13strict，三个经典方法各0/24；仍待8条件确认。
初始264学习回合已开始。首条件/seed ESN点版通过，XY24.774mm，积分版26.381mm放置失败；
无记忆/初始matchedMLP也通过。ESN点版RMSE较小，但推杆接触更长、累计力更大、保持期脱离仅1.3ms，
无记忆约2.19s；不能据此声称记忆提升柔顺性。全部恢复诊断右删失，柱子未触对ESN记NA。
新有限teacher-refinement等待参数选择，原32train/8validation真实采集，配置相同则不重复；
不给学生使用开发历史，不自动新增训练预算。默认导出原生回归得到同数据hash，选择器3项合成回归通过。
主机arm1@192.168.31.70，本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，
见controller_screen_v1、early_learning_metrics_v1、teacher_refinement_v1及Git小证据。最终24条件继续封存。

## 2026-10-03 15:37UTC：输入调制记忆的配对机制实验已拟合

原ESN在load归零后context不能影响后续动作，这是代码与合成干预一致验证的表达限制，尚不是实际失败因果证明。
真实teacher低负载活跃记忆片段短于探针；完整teacher动作重放误差1.11e-16。新固定随机context-leak调制保持纯ESN，
同时提供给matchedMLP/RNN/memoryless；无新增观测、运行teacher或环境改动。21模型本地拟合与服务器逐hash核验完成。
离线误差变差，合成长期保持仍不理想，不能宣称优化成功；全部21进入相同8开发条件168回合，原组保留。
AMENDMENT_01先登记将学习候选上限24→48，明确披露实际各族成本不同；原截止不变。服务器本轮根
local_context_gate_archive_v1与context_gate_development_v1，源码/hash见UPDATE_LOG；当前服务等待稳定旧四队列结束。
筛选74/96运行正常；24最终条件未读取。下一步以闭环失败证据决定是否保留该机制。

## 2026-10-03 15:11UTC：冻结检查与真实成本核对

四条开发筛选队列稳定，15:08快照56/96完成；未因中间失败重复启动。最终模型锁/独立worker/四槽队列已实现，
6项合成数据保护回归通过，真实最终条件仍封存，真实最终执行未启动。完整源码资产集合与checkpoint均需匹配。
新分析方案预先声明条件和训练seed的成对统计、接触缺失NA、恢复删失及成本差异，不预设ESN最好。
初始33模型108ridge候选/96000梯度更新，48复核另192000更新；共享teacher采集48次包含20strict失败。
小证据EXPOSURE_SNAPSHOT_20261003_1520.json在本轮Spark根及Git，SHA与入口见UPDATE_LOG。
当前仍等待实际ESN闭环结果以决定算法修改；离线累计偏差只作为诊断，未获跨条件任务成功结论。

## 2026-10-03 14:43UTC：防止欠优化baseline，诊断ESN累计偏差

同数据小学习率复核48拟合已完成并归档，21个新权重等待8身份闭环；ordinary RNN验证点误差改善36.42%，
ordinary MLP改善23.91%，matched RNN也有小幅收益。仍在原候选cap内，不选择幸运seed。
33模型×6离线验证动作filter诊断完成：ESN积分损失降低累计残差代理，但约98.0→87.8mm的量是开放回放积分，
不是真实位移、任务RMSE或成功证据。后续依据闭环失败机制决定ESN优化，不预定胜者。
新增8回合零让位名义WBC参考待运行；额外开发与RL在原四队列流程之后共享槽位，每评估回合释放以便ESN插入。
服务器本轮根`local_neural_refinement_archive_v1/`、`additional_development_v1/`，小证据/hash及初始SOURCE标签澄清见根UPDATE_LOG。
24最终条件继续封存，当前尚不具备新的闭环泛化结论。

## 2026-10-03 14:18UTC：RL恢复链与后续资源准备

新RL checkpoint全嵌套hash、5D/7D模型优化器重放及replay/RNG恢复工程检查通过；0新物理步。
15个办公RL训练计划等待前序，3队列共享4仿真槽位，为ESN继续开发留容量；原8万步总预算不变。
实际回合分段续跑将在首个5500步段之后验证。现有控制器筛选20/96完成，未停/重启稳定队列。
服务器本轮根`rl_checkpoint_probe_v2/`与`rl_office_adaptation_v1/`，源/hash详见根UPDATE_LOG。
当前重点仍是33模型在共同8开发身份上的闭环效果，最终24身份继续封存。

## 2026-10-03 13:50UTC：真实示范与33模型完成，闭环开发启动

48条teacher全完成，44任务/28严格成功；同数据18训练＋6验证、33000帧已导出。
本机33模型拟合结束并逐权重/源码核验到Spark，ESN固定储备池、仅训练受约束线性读出。
离线记忆模型误差较低但不当闭环结论；同特征MLP/RNN全部选中初始化，需检查验证收益缺失。
仅2/18合格训练示范有柱接触，12条穿透失败最差对是柱/link7；报告覆盖，不声称无接触即柔顺成功。
已知训练身份完整RL IPC重放通过：1375步、55秒、全部物理子步数组精确相同，未开始RL训练。
正在执行预登记48控制器候选×2开发身份；随后全33学习模型×8身份，以及各经典前2候选×8身份。
有限连续进程`sii-r72-followup-v1`等待前序完成，不增加同时仿真数量。
服务器根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`，
模型`local_learning_archive_v1/learning_v1/`，筛选`controller_screen_v1/`，协议/hash/源码位置详见根UPDATE_LOG。
24最终身份继续封存；本轮尚无新模型闭环成功结论，不能声称已经满足RAL证据要求。

## 2026-10-03 12:32UTC：新数据采集与学习接口准备

teacher最近核验28/48完整、25任务成功、15严格成功，所有失败继续保留，不改采样/门槛。
新增实际请求/过滤/执行链资格导出、真实身份mask，纯ESN读出差分/16步积分目标及同样损失的MLP/RNN。
本地旧训练数据工程拟合/导出回放/输入隔离通过，不是新闭环结果；新数据33模型3seed计划尚未开训。
办公RL在线通信/原官方SimbaV2训练/冻结评估代码已准备，须先通过已知train_000完整原生重放。
连续依赖服务`sii-r72-prepare-learning-20261003-v2`等collector完成才导出/重放；原生无torch的依赖已去除。
源在 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149_learning_runtime_v2/`；
两端tar hash核验，详见根UPDATE_LOG/RESEARCH_STATUS。24最终条件仍封存，未获得新泛化结论。

## 72小时新研究已登记（2026-10-03 11:49UTC）

固定入口为仓库根 `RESEARCH_STATUS.md`。用户假期3–4天授权按72小时至10-06 11:30UTC执行，
前48小时开发、之后冻结评估/审计。原v6几何/gate/WBC/actor契约不变；新身份在原扰动范围采样。
32训练＋8离线验证＋8开发的真实teacher回合已在Spark四个3GiB单线程服务启动，全部dt5e-5。
24新最终条件已封存，仅记录hash，未读取/执行。旧已知最终结果不当新盲测，不用于蒸馏。
服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`，
初始源在相邻`research72_20261003_1149_runtime/`，base33f4380＋3新增脚本；tar两端hash核验完成。
公开协议在 `evidence/research72_20261003/PROTOCOL.json`，本轮尚无已完成新学习/留出结果。
后续必须同合格真实数据训练ESN/MLP/RNN，并补baseline办公适配；不再以低模仿误差推断任务成功。

## 全26模型统一正式测试重跑（2026-10-03，已完成）

用户再次要求在统一测试环境实际运行。旧矩阵“0/0”表示两个成功计数均为0，各自分母4，
不是未测试；旧四扰动组已统一运行，但正式dt5e-5当时只测7个开发合格模型。
本轮新授权为有限26模型×1个原v6锚点，全部重新运行，权重/归一化/几何/目标/门槛不改，
不重训、不按旧成功筛选。新协议与新run独立，不延长旧12小时预算，不覆盖旧实验。
服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/all_methods_formal_20261003_104728/`。
源快照为相邻`all_methods_formal_20261003_104728_runtime/`及各queue/source；base main c2bbc79，
baseline ebb0e1e，新增两个有限派发/报告脚本；原worker和物理不改。采用原生Spark运行库避免已知跨库差异。
最多4条顺序队列，各1线程、MemoryMax3GiB/Swap0；主服务`sii-all-formal-coordinator-20261003-104728`。
26/26均完整55秒，独立共同世界/初态、子步/动作/源/权重及26条真实放置重建已通过；
5模型task/strict通过：增强teacher、普通RNN两seed、同特征RNN seed1、无记忆重训。
两个ESN、七RL、七普通/调参经典以及其余对照失败。21个失败末态为13 carry、4 approach、4 retreat。
ESN seed1掉块、seed2放置XY28.19mm超25mm；RL调参三条停carry、RL action四条停approach。
7条已有formal结果重复的轨迹hash和全部三指标完全相同，未用重复试验增加独立样本数。
[正式统一矩阵](evidence/all_methods_formal_20261003/report/MATRIX.md)将任务/严格成功分列为是/否，
包括26模型完整接触指标、失败征象及来源。双遍hash核验2787文件/3826668265字节，
完整清单在相邻`all_methods_formal_20261003_104728_integrity/NATIVE_INTEGRITY.json`，
SHA `e0869790eb167394cb88a7ba5bc2953d5c830a6fe012141e3b37ef1ae8adaa7f`。
本机174份下载证据逐项核验一致。该有限重测无运行中作业；这是已知单锚点复测，不是盲测泛化证据。

用户随后授权假期期间自主持续优化ESN并兼顾baseline、面向RAL准备公平可投稿结果，按72小时新研究窗口规划。
新研究与本次冻结重测分开记录；已知结果不再作为盲测，不以预设ESN胜出为选指标依据。

## 全部baseline统一柔顺性矩阵（2026-10-03）

已将26方法×4条件104个既有v6回合整理为[统一矩阵](evidence/unified_compliance_20261003/MATRIX.md)，
包含3种RL调参、4个RL action及全部经典/学习对照。全回合统计保留失败、显式接触分母、无接触NA；
接触积分/时长/恢复删失及全任务再接触也已列出，未混合formal/随机补充。新增仿真与训练均为0。
ESN对本轮冻结RL有任务完成优势，但接触负担和力矩并非全面更低；没有共同strict成功回合支撑
与RL的“同等任务成功时柔顺提升”结论，训练曝光差异仍在。两个ESN正式步长失败的结论不变。
脚本/矩阵已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unified_compliance_20261003_1034/`，
详细字段、来源hash、失败及核验收据见同目录Git证据。无运行中实验，稳定泛化目标仍未完成。

## 十二小时预算内研究最终交接（2026-10-03）

全部物理和独立审计结束：104主比较＋56随机＋7正式步长，共167新增完整55秒回合。
主比较ESN两seed strict1/4、2/4，随机补充各4/8；同特征RNN主比较各2/4、随机1/8与2/8。
增强teacher随机5/8、无记忆5/8；两个ESN正式步长均放置失败，teacher/无记忆/RNN seed1成功。
有局部优势，未证明全面最好、储备池记忆必要性或真实环境泛化；不把不同组分母合并。
三个同seed共同strict条件中ESN更快完成，但推杆p95力都更高。随机strict子集ESN杆保持期
最长无接触间隙中位数仅1.1/1.3ms，仍不能宣称持续主动滑脱；恢复时延删失明确记录。

193选定记录的接触覆盖/失败征象、192完整末态和1原abort均已核验；67条成功完成时间补充
25Hz采样勘误（原插值早20ms），不改gate。47完整三机位视频及2上下对比已核对hash；
两步长7对轨迹分叉仅作事后诊断，不用于训练或选型。全文及视频索引见
`PAPER_ESN_12H_RESULTS_20261003.md`、`PAPER_ESN_12H_METHODS_20261003.md`。

2026-10-02 22:24:07UTC服务器主执行根双遍hash核验完成，40094文件/32802129515字节：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`。
清单位于同父目录`paper_esn_12h_native_integrity_20261003_final/NATIVE_INTEGRITY.json`，SHA
`f2bd06e2a7a1b4e26c85eaaa0a6e96061da88b729232c8775a2a58317579b3e8`。Git证据目录保留结果、
24份汇总所引用独立审计、媒体索引及收据；大轨迹、checkpoint、MP4留服务器，本机存播放缓存。
运行源码以各run/source及overlay为准，整理后的Git源码另按提交SHA归档source目录。

已完成：本轮冻结比较、审计、报告及共享证据；无本任务运行中作业，无定时任务。
尚未完成：跨分辨率/条件稳定ESN、持续杆推滑脱、对强对照的持续优势、真实机器人验证。
后续优先扩充真实teacher承载转移/掉块前闭环历史，不能把2条实际teacher＋48合成序列写成
大量独立成功物理场景。当前final条件已知，后续训练须登记新验证，不能重新调参后冒充盲测。

## 十二小时研究21:41UTC：主比较与formal完成，ESN未全面领先

104/104四设计条件及共同配置/独立物理审计完成，全部完整55秒。
ESN seed1 task/strict1/1（分母4），seed2为3/2；同特征RNN为3/2和4/2，普通RNN为4/2和2/1，
同特征MLP2/2，无记忆3/2，增强teacher3/2。七个经典方法、七个冻结RL和名义zero均0/4任务成功。
h3两个ESN通过但teacher失败，无记忆也通过，不能独占归因于储备池记忆。
h1 ESN seed1虽然XY3.427mm，却高于目标32.445mm、停load_transfer；h2则物块掉至地面，
XY214.157mm，不能把retreat阶段或低RMSE当放置。失败原始记录未改。

7/7正式dt=5e-5锚点及独立审计完成：teacher、无记忆、同特征RNN seed1通过task/strict；
两个ESN、RNN seed2、VMC04均任务失败。两个ESN的外穿透.174092/.140342mm并未超限，
失败在放置；开发成功没有保持到更小步长。详细表见`PAPER_ESN_12H_RESULTS_20261003.md`。
主协调器complete；八随机条件按之前锁定的7模型资格开始，不能因formal失败改变模型或删除资格。
14条其余设计条件视频全部55秒/1375帧、三机位并下载hash核验；h1全26与formal全7媒体仍生成。
原生开发RL的16.36秒安全终止视频另完整保留409帧，短时长审计通过。
尚未完成：56随机回合、193条终版汇总/全任务接触及末态核验、最终文档/Git/原生整体完整性。

## 十二小时研究21:09UTC：继续冻结验证，补齐接触覆盖与完整展示

主验证81/104条完成，仍4模拟器、单线程/3GiB；没有新训练/调参或重启。最终交付连续服务
`sii-paper-final-delivery-20261003.service`等待原协调器完成，再生成主表、h1全部26模型和formal全部7模型
的三机位视频；之后等待56条随机验证完成，生成193条选定记录及全体独立放置重建。
这是一次性后处理作业，不是定时任务，不执行新的物理积分。失败保留、abort按真实时长展示。

独立纯本体输入边界审计：10模型各1375帧、其余30字段改为固定seed大幅随机值，动作/隐藏状态差均0。
主执行根`ACTOR_INPUT_BOUNDARY_AUDIT.json` SHA `1db78fc30bc58c8dfbf8646e964d406c6fa6625219942c7aeb9575db33077540`。
112原生开发回合全量索引`development_catalog/catalog.json` SHA
`2025309ff33dbeed251dcb0643c735057129d7a425fc1f19a15f56dbbd0c62e1`，task14/strict10；
与本机82条、不同库7条兼容诊断分开，不作为最终26模型统计。完整学习69目录/58训练完成记录，失败导出保留。

开发曲线发现人手指令结束后的再接触，因此补充全任务/窗口外接触审计，原事件窗口统计不覆盖、不删改。
该补充为事后测量覆盖诊断，不冒充预登记优越性终点。原放置判定每个25Hz有效样本计.04秒，
13样本计.52秒但首末跨度.48秒，审计说明已纠正；原task/strict一律不变，不宣称子步连续保持认证。
后处理源包`final_delivery_source_20261003_0505.tar.gz` SHA
`2d7ecfc244d0449722a1ba928900492d7487f7eca326580956ce22ba93738c21`已核验于服务器主执行根。
初次打包误含历史outputs且传输未完即尝试解包，失败未执行；完整旧包与不完整解包保留在独立
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_transfer_diagnostic_20261003_0439/`。
替代包排除outputs，传输完成后先SHA核验再解包，新目录不覆盖任何运行源码；`SOURCE_TRANSFER_DIAGNOSTIC_20261003.json`记录过程。
未完成：主比较/formal/随机补充全部最终审计、最终论文结论、全根归档验证与Git发布。

## 十二小时研究20:09UTC：26模型已锁定，最终评估开始

38条原生经典候选全部结束并通过独立审计；确定性规则选中admittance_01、impedance_12、
original_vmc_04。VMC04开发strict通过，另VMC01仅task通过（外穿透.710550mm）；导纳/阻抗均
未在开发锚点完成放置，全部失败与原参数保留。最终26模型于20:09:22UTC锁定，四条件同步启动，
当前4个仿真进程、每个单线程/3GiB。之后不再训练/调参。
服务器主执行根中`final_model_lock/VALIDATION_LOCK.json`的SHA256为
`755974da1d4d5a3fb1aa24aa779cf91ede2e83768de2b9dd21089de863166701`；本地副本核验一致。
7个formal合格者在四条件前确定：增强35mm teacher、固定ESN两seed、无记忆重训、同特征RNN两seed、VMC04。

在任何最终回合开始之前，20:01:17UTC另登记8个PCG64固定随机扰动条件，作为7个开发合格者的
补充稳健性检查（56回合）；原26×4主比较完整保留，未入补充组的模型不算失败。
`PAPER_ESN_12H_SENSITIVITY_20261003.json` SHA
`d9191c98ee76691b449322c6ccfdfbd0522563314730854725309afd2eb1b252`，
快照`sensitivity_source_20261003_0405.tar.gz` SHA
`cc106f3e17677089805b97778535dc6278514046f1e56a7df2fdae52c82eb17d`已共享核验。
补充协调器只在主比较/formal全部审计完成后串接，不是定时任务，不根据最终结果改资格。
代码仅为新条件文件增加精确hash白名单；正在运行的原四条件源码快照未改。

本机82条开发回合与全部后处理/小型证据索引已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_local_audits_20261002_141136/evidence/`，
746文件/7062404字节，manifest `3f859cd8ea65d7684aa6c8cf63768c68680240e15632ebb861962ea6d3ede870`。
10个主学生各53500输入的学习回放重建最大误差0；证据主执行根`LEARNING_REPLAY_DIAGNOSTIC.json`，
SHA `baa4736bc99911eef867af5e9f31e84fffca577c77bbff0115044c0112951fc5`，实际在airpig离线计算。
6条新增55秒三机位视频全部1375帧解码并下载核验，ESN2/RNN1/MLP1代表拼图已目视检查；
两个RNN及ESN2的真实释放/支撑末态重建也通过。现有成功不证明推杆保持期持续滑脱。
baseline源/参数/7个RL checkpoint等537文件1013195685字节另存主执行根`baseline_dependencies/`，
索引SHA `71edb6111a6ef8786734d146a1c084ea00f96a53f3f3a2ea1ad83d2395badb14`；不改原运行目录。
运行中：104条主条件队列；待运行：7条formal、56条随机补充。未完成最终统计、媒体、整根原生完整性核验和Git发布。

## 十二小时研究19:27UTC：停止拟合，转入冻结配对验证

所有新学生训练于18:52UTC前结束；19:00UTC登记最终选型规格，之后不再训练/调参。
同特征可训练RNN两个seed都完成原生开发task/strict：seed1为42.442060mm/50.390430Nm/
.389962m/s、穿透.196021mm；seed2为29.329836mm/49.395878Nm/.360622m/s、穿透.114708mm。
两条独立指标/动作/状态审计通过。RNN seed2人手p95/冲量14.413N/26.607Ns，杆11.390N/37.757Ns，
未接触柱子；其负载较低不能直接解释为同曝光下更柔顺。ESN并非唯一能成功的结构。
原VMC固定搜索也出现strict通过的original_vmc_04：36.384884mm/48.822414Nm/.368985m/s，
穿透.120831mm；完整38候选仍顺序评估，不提前按局部结果结束搜索。

最终一次性协调器`sii-paper-final-coordinator-20261003.service`已运行，先等待稳定经典队列完成、
独立审计，再生成26模型锁和四条件配对；所有开发strict合格者另做5e-5步长，不据最终条件筛选。
协调器不训练、不调度定时任务，每个队列单线程/3GiB，仿真总并发不超过4。
截至此记录最终条件尚未派发，正式步长尚未完成。模型与参数冻结后不因测试结果再修改。
源快照位于服务器主执行根`final_validation_source_20261003_0320.tar.gz`，SHA256
`b251daadfb8846a04880e1717a1df42f067b8c2d7ebe8e9dfbe1cfb06d2bf702`；规格和封存条件也在该快照内。

新增已核验归档（均在`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`）：

- `paper_esn_12h_learning_complete_20261002_141136/evidence/`：69组、3710文件、265297768字节，
  包括全部顶层学生训练、失败导出、数据与离线队列；manifest
  `f0229abc25df6042a339035671f6a65cf5e069974ba88b432a028b0e72645e90`。
- `paper_esn_12h_classical_slice2_20261002_141136/evidence/`：本机剩余29条，1712文件、3104419394字节；
  manifest `3a3eb4f64e83ea6706f819b41a95efb20c71cce67384ce725add133c0b668a5c`。

六条补充开发三机位视频正在从保存状态渲染，包括两个RNN、ESN seed2、teacher以及MLP/名义失败。
运行源/结果仍在`paper_esn_12h_rl_20261002_141136/`；原始执行路径不改写。19:08UTC复查远端main
282433d339feef66b0334f223f82a6eea96b040b、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6未变。

## 十二小时研究 18:45 UTC：35mm组两个ESN seed成功，但记忆必要性尚未成立

同原生v6锚点、完整55秒、原门槛：35mm组固定128储备池两seed均task/strict通过。
seed1为29.012838mm/50.684875Nm/.389144m/s、外穿透.179431mm、XY12.165mm、有效保持18.04s；
seed2为28.014857mm/50.289936Nm/.354489m/s、外穿透.110893mm、XY21.914mm。
seed1独立末态重建、两条成功ESN（含50mm组）的55秒/1375帧三机位视频及逐帧解码完成。
不能把两个初始化seed当跨环境泛化；四个最终条件仍未使用。

35mm组重新训练的无记忆模型也task/strict通过：32.042943mm/52.798248Nm/.356138m/s，
外穿透.108959mm。因此原成功模型逐观测清空后失败并不足以证明“记忆必要”。同宽普通MLP/RNN
两seed各0/2 task/strict；feature-matched可训练MLP/RNN已完成离线学习、正在闭环，以拆分固定
load×context特征与循环记忆的影响。长历史RNN两seed一条放置但穿透.429421mm，strict均失败；
原64步与新256步训练实际非padding曝光约477万/454万，近似匹配而非完全相等。

共享DAgger把35mm组四条已完成学生历史全部反事实重标注，原8条留出身份逐数组不变；
两个新ESN均外穿透超限（.535208/.604829mm），暂不替代原固定ESN。读出MSE优化版也失败。
50mm组第二seed/无记忆/读出优化均失败，所有失败已保留。没有因离线误差更低而声称物理更好。

35mm seed1接触：球、人手、杆、凸边、柱子均实际发生；人手p95约14.884N、冲量28.980Ns，
杆p95约13.776N、冲量46.724Ns，但杆保持期最大无接触间隙仅1.1ms，不能声称主动蹭开。
杆撤回0.103s后即接触下一凸边，恢复统计按先验删失，不填一个虚假恢复时间。
50mm成功seed1没有柱接触，杆撤回后稳定重返路径约1.2065s；这些接触曝光差异必须展示。

服务器主执行根仍为`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`。
35mm基础/机制组分别`recovery035_learned_native`、`recovery035_mechanism_native`，共享DAgger为
`recovery035_dagger_native`，长RNN为`rnn_long_native`，特征匹配为`feature_matched_native`。
已核验639项/100781194字节完整学习证据：
`/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_learning_evidence_1815_20261002_141136/evidence/`，
manifest `f6a56266094c5fb7c89ff6adec32b10bad100ff82ef087ea1cd77a078f799b48`。
运行中：本机经典剩余候选、原生38条经典复评、学生对照及完成批次独立审计；未完成终版锁定、
正式步长、四条件配对、最终统计/全部归档/Git发布。模型/数据各bundle收据保存在本run archive_receipts。

## 十二小时研究 17:56 UTC：首条纯线性读出 ESN 开发 strict 成功

统一原baseline解释器后，`recovery05_esn_fixed`完成55秒，task/strict均true，真实最终XY误差
7.929mm；RMSE41.475743mm、峰矩50.135914Nm、峰速.357187m/s、外穿透.125753mm。
128固定储备池，仅2884个线性读出系数学习，独立7维输出，无部署VMC或额外隐藏读出。
这是一个开发锚点，不是正式步长或泛化结论；独立末态重建与整批接触审计正在进行。
同组条件漏率ESN最终XY25.161mm略超原25mm而失败；adaptive-leak版本task通过但柱子穿透
.484566mm，strict失败。所有结果保留，不能把只完成放置者称安全成功。

服务器执行根（源码在对应批次source，未提交源码有逐文件hash）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`。
当前成功回合`recovery05_learned_native/recovery05_esn_fixed/`；模型已核验共享在
`/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_recovery05_learned_20261002_141136/evidence/`，
bundle manifest SHA `f20cebe3bc35de2ac53afb65cd3784c91e90a99e3275044e8b6915d528853122`。
14个历史baseline/ESN锚点已逐数组精确重现，共15回合统一场景/解释器/初态审计通过，
证据`RL_NATIVE_PARITY.json`、`ANCHOR_NATIVE_PARITY.json`、`BASELINE_COMMON_COHORT.json`。

六个恢复teacher在原环境有3条task/strict成功；35mm/.02m progress配置稳定保持13.6s，
29.894mm/49.246Nm/.384913m/s，已成为下一蒸馏数据组。50mm组继续全部跑完；35mm组保留
原生成功与本机失败实际执行标签，同身份留出，固定/条件漏率离线模型完成，MLP/RNN同数据训练中。
宽范围漏率未改善离线误差，不派发。经典剩余29条本机单模拟器运行中，服务器学生两批运行中。
最终四条件仍封存；尚未锁定终版、完成正式步长/泛化/记忆因果对照或最终媒体，不能声称ESN最佳。

## 十二小时研究中期：统一运行环境，纯ESN到达目标但保持时长不足

仍在原授权窗口内连续执行，无定时任务。原始VMC本地单条task/strict通过，尚非稳健性结论。
同数据128单元纯ESN的temporal_.25（只优化402个读出系数、加入.64秒动作积分代理）已在
冻结v6末帧完成松爪、真实桌面支撑、无机器人接触与静止，XY12.557mm、Z约.003mm；但直到
55秒末才张开夹爪，连续有效保持仅.04秒，低于原.5秒，task/strict仍false。原始轨迹保留，
没有延长回合、提前宣布成功或更改判据。550000子步RMSE28.915mm、峰矩49.162Nm、峰速
.382531m/s、最大外穿透.168985mm，末态独立重建核验。其他分组MLP/RNN/积分权重0对照均失败。

新固定对角、级联和阈值储备池未改善离线留出，未进入物理；限幅线性读出留出改善到.000831，
但其闭环仍卡carry，说明离线拟合不等于放置。正在顺序运行预登记teacher恢复/平滑候选，
MLP/RNN已获得同动作积分目标的额外4000更新；之后做同预算读出校准。环境、actor输入、
gate、执行器约束不动，四个最终配对条件仍未使用。

运行环境纠正：服务器最初RL七条使用错误的simba_v2_venv+CUDA12 overlay，已保留为兼容性
诊断，不纳入精确复现。使用原baseline的reward_study_20260930/venv_gpu及gpu_env.sh库路径
重跑七条，恢复了历史三指标与direct_office_task_74002的穿透终止；所有task/strict仍失败。
统一运行环境的VMC与七个非RL锚点正在核验，避免混合本机/服务器数值差异作为算法优势。
服务器原生运行（尚待最后归档总审计）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`，
其中evaluations_native为正确RL环境，evaluations_r4为兼容性诊断，native_anchor为非RL核验；
源码native_source_20261003_0040.tar.gz SHA56b205febf6bc90cb3f96380179664ee18f8e83259db7e3dda974bf1d58d4d3e。
首个native_anchor服务在仿真前因缺少锁目录退出，journal保留；只创建新源码副本outputs目录
后恢复，未覆盖任何回合。批处理器已为以后启动创建该目录，避免同类预启动错误。

新增九条经典控制器开发失败已独立审计且782项973,560,594字节SHA核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_classical_slice1_20261002_141136/evidence/`，
manifest b04f3ec8db8e16e470a98e540c4d77d87c1ec1e7176f7326d943393613577d66。
其余最近学习批次目前仅本地待同步；未完成最终锁模、纯ESN task/strict、formal及跨条件证据。

## 2026-10-02 十二小时同场景研究：15:05 UTC阶段记录，仍在执行

授权14:11:36UTC至次日02:11:36UTC，无定时任务。开工main282433d、baseline ebb0e1e；
采用baseline已冻结的office-validation-v6，MJB173e404b，55s/dt1e-4。该世界为开发场景，
不能把v5→v6当作算法改进。原始VMC配置{}现已完成真实释放稳定放置，task/strict=true，
RMSE28.690mm、峰矩50.573Nm、峰速.384913m/s、最大外部穿透.194972mm、XY11.205mm，
终端稳定保持2.64s。四类真实接触存在，但杆保持期无明显持续脱离，三项settled-rejoin均删失。
这是一条成功强baseline，不是ESN优势。首批其他4条全部失败；旧ESN与两版新蒸馏ESN均仍卡carry。
原始VMC临近穿透门槛，未验证稳健性。新128单元分组ESN、同数据同128hidden的MLP/RNN已完成
离线训练，闭环待测；既有导纳/阻抗/参数VMC正在相同v6核验，保留各自控制律。
先验指标层次、候选预算与所有限制见[PAPER_ESN_12H_PROTOCOL_20261002.md](PAPER_ESN_12H_PROTOCOL_20261002.md)。
首批5条完整轨迹/动作/储备池/filter/物理子步/穿透审计539项520,615,243字节已SHA核验共享：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_initial_20261002_141136/evidence/`。
该目录source为确切运行源码，manifest SHA53cbdf8bda7dfdb9b25393c1afaf8d2e32a78c795dabdb48627734c053cc7111。
后续批次目前仅本地待归档；未完成纯ESN成功、同数据最终比较、formal与跨条件证据。

## 2026-10-02 纯 MLP / 可训练 RNN 替换：8条完整开发回合均未成功

按用户新授权，用两套既有 teacher 数据训练128宽MLP和Elman RNN，各两个seed、相同2400
更新/序列曝光。固定tool-contact-v5、MJB b092662a、规划/WBC/gate/公共输入与执行器限制。
8条55秒开发回合全部完成，task/strict=0/8。原VMC组MLP/RNN两seed平均RMSE为39.060/29.307mm，
峰矩38.470/38.933Nm、峰速.404145/.386349m/s，均卡carry；RNN没有改善最终放置。
恢复41组无稳定优势：RNN seed1距目标101.545mm但RMSE74.640mm，seed2全程approach，不能把
低RMSE/低峰矩当进步。MLP seed2距目标59.899mm仍未放置。原VMC MLP seed2穿透.205319mm超限。
四个RNN的离线拟合误差都较低，但没有任务成功；128宽相同不等于参数量相同，旧ESN另有128非线性读出。
8条物理/动作/filter/状态/接触和4组训练曝光审计、两条55秒三机位视频完成。首次预启动资产路径
失败保留并复用原checkpoint；未重复训练或丢失败。已核验680项、747,693,072字节共享在
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/mlp_rnn_replacement_20261002_131535/evidence/`，
运行源码在其中evaluations/source，后处理源码postprocess_source。无运行中作业。
未完成：稳定放置/strict、成功teacher数据、formal与跨条件泛化。
完整表格、hash与限制见[MLP/RNN报告](MLP_RNN_REPLACEMENT_REPORT_20261002.md)。

## 2026-10-02 四小时固定环境联合优化：72条完成，仍未放置

授权09:01:55–13:01:55UTC，连续任务、无定时任务。预登记48条teacher/名义候选与24条
纯ESN回合全部55秒完成，task/strict均0；候选额度用完后停止物理派发。环境tool-contact-v5、
原MJB、路径/WBC/gate/执行器限制未改，本机单模拟器/1线程/3GiB，baseline作业未动。
原VMC蒸馏ESN为30.058mm/39.210Nm/.370185m/s、穿透.111707mm，但仍卡carry。
推进最远teacher47最终XY49.157mm，59.485mm/40.926Nm/.385393m/s；未碰未知凸边、
后段卡柱子，推杆连续受力8.8172s，不能称全程滑脱/恢复成功。
context调制记忆在teacher44配对中减小大幅漂移，但teacher47配对仍卡lift。加入自身失败
历史重标注及积分action损失后，配对RMSE153.759→125.970mm，峰矩/峰速略升且仍失败。
最后gain.75及清空历史两条穿透超限，全部保留；清空历史的低RMSE来自退回卡住状态。
13个有效训练模型（128储备池＋128非线性读出）及1个拒绝部署的旧标签模型保存。
不是只训线性读出的经典ESN，也不是与历史MLP严格参数匹配；本轮未做MLP新实验。
72条三指标/动作/状态/公共filter/幅值/4ms指令变化率及源/配置/hash审计完成，33条接触
sidecar独立复算一致；5组配对数据、seed、预算一致性通过。完整两条55秒原速三视角视频已生成。
运行中：无物理或训练任务；共享核验状态/地址见[完整报告](VMC_ESN_FOUR_HOUR_REPORT_20261002.md)。
未完成：成功teacher数据、ESN稳定放置/strict、正式步长与跨条件泛化。

## 2026-10-02 环境/三机位共享交接

用户认可tool-contact-v5展示，先冻结当前环境与拍摄交给其他agent。本轮仅文档与
`--reference-dir`可移植入口，未新跑仿真/训练，环境/gate/权重/相机不变。
已完成：完整配置、三机位和共享证据的[交接文档](OFFICE_TOOL_CONTACT_HANDOFF_20261002.md)，
共享参考与原权重/非覆盖参数一致性检查、短探针拒绝检查。当前本任务无运行中作业。
未完成仍为完整放置/安全、正式步长、跨条件泛化；VMC新采集和ESN新学习留待后续。
完整55秒仍task/strict=false，不把交互展示认可视为任务成功。

## 2026-10-02 先修球/棍接触，暂停算法修复

用户要求优先可见球撞和棍推末端，未重训/改ESN。独立tool-contact-v5采用真实1kg/半径60mm球
撞掌部，缩短并反向布置棍子至z=.64m，固定保持期延长到23.5秒。球零初速反事实确认
13.845mm额外手部偏移；棍无物块/人体接触，15.1201–19.1801秒在仍伸出时已脱离受力接触。
仍有回碰/抖动，最长连续段.1061秒，不能称平滑永久滑脱。前28秒穿透.111485mm。
完整55秒开发回合仍task/strict失败，后段原柱子/link7穿透.653202mm；
三指标49.428mm/45.880Nm/.370425m/s。原ESN动作/状态重放误差0，额外日志回放完全一致。
候选失败、完整/慢放/原速媒体和公平接入见[报告](TOOL_CONTACT_REPAIR_20261002.md)。
当前无运行中仿真；未完成连续平滑脱离、全场安全和放置，按用户要求本轮不修算法。

## 2026-10-02 未知桌边障碍：名义阻塞已复现，学习恢复尚未成功

按用户视频新增独立凸边场景，先验地图遗漏、从reset起真实存在；纯本体actor与执行器
限制不变。修复公共路点接回把纵向前进误计为横向偏离的问题，保留v1并统一重跑v2。
两轮共8条55秒开发回合完成，名义无凸边task/strict成功；名义有凸边从11.3937秒持续
接触到55秒，task失败；原ESN/MLP都未触及新凸边就停carry，尚不能测试其脱困能力。
ESN三指标26.496mm/37.763Nm/.084326m/s；MLP24.843mm/36.977Nm/.061384m/s。
动作/状态重放、子步指标、相同路线/阻塞MJB及完整媒体核验完成；当前无运行中作业。
未完成：新参考下学生正常推进、接触恢复放置、正式步长/跨条件验证。几何绕路可行
不等于动态执行或ESN成功。完整证据和共享入口见[报告](UNEXPECTED_EDGE_CONTACT_TASK_20261002.md)。

## 2026-10-02 靠手桌角规划任务落地

按用户新定义增加独立planned-hand-corner-v1：先静态规划与IK姿态搜索，物块在目标区
松手并稳定放置即task成功，接触覆盖独立报告。原ESN、零动作名义执行各55秒完成，
同规划hash50f32f7e；名义成功、XY误差10.8mm，ESN停carry仍失败。
ESN持续残差与名义纠偏相反是后续适配重点，不能再把此失败全部归咎目标不可达。
新协议不能和旧mandatory-contact strict混算；无重训、无运行中作业。
详细三指标、独立审计及共享媒体见[新任务报告](PLANNED_HAND_CORNER_TASK_20261002.md)。

## 2026-10-02 新时序完整ESN回放完成

按用户新授权复用原p=.1 ESN，顺序扰动55秒开发回合完成并输出三视角GIF/MP4。
task/strict=false，停load_transfer；38.708mm/48.463Nm/.094228m/s，穿透.122975mm。
人手接触末次8.8977秒；推杆12秒启动后没有有效机器人接触，柱子同样未覆盖。
不能算完成复杂任务；动作/状态/物理子步审计通过。无重训、无其他方法重评、无运行中作业。
完整证据和服务器媒体见[本次回放报告](ESN_SEQUENTIAL_R12_REPLAY_20261002.md)。

## 2026-10-02 用户授权顺序扰动修复

新独立协议`sequential-r12-v1`只将推杆起点7→12秒，人手3–10秒、推杆12–21.5秒。
不需重训，已有各方法权重/参数复用，后续统一重评；旧结果不与新时序混算。
启动参数防错、55秒指令无重叠检查及两个80ms物理检查通过，模型与初始轨迹一致。
尚未跑新55秒效果、实际接触间隔或strict；无运行中仿真，不宣称任务已解决。
共享证据及baseline接入见[时序交接](OFFICE_SEQUENTIAL_R12_HANDOFF_20261002.md)。

## 2026-10-01 15:40 UTC 记忆因果对照与dropout收尾

固定seed52 ESN逐次清空历史停align，task/strict=false，25.213mm/34.820Nm/.076344m/s；
没有抓起物块，不能把低指标解释成改善。p=0/.1两组等预算训练和四条冻结3.11.0评估完成：
ESN从lift推进到load_transfer，RMSE48.971→44.666mm，峰速.116950→.094228m/s，
但峰矩43.600→47.458Nm，仍未放置；MLP两组task均true，strict全部false。
五条均完整55s/550000子步；独立动作/储备池/物理审计通过。p=0 checkpoint和raw rollout
与原冻结参考逐字节一致，教师身份/数据/归一化/储备池检查通过。

预算纠正：自动化05:48:54UTC创建，按八小时保守推算13:48:54应收尾；先前错误使用
唤醒日程16:20作为计算截止，不能当作延长授权。这些晚期诊断单列，不计作八小时内完成。
发现冲突后未新增campaign；已启动末回合15:40:30完成。heartbeat已PAUSED，
当前无仿真，新实验需新的明确预算。已在AGENTS记录预算依据规则，原执行记录不重写。
详见[完整诊断报告](ESN_MEMORY_DROPOUT_DIAGNOSTIC_20261001.md)；ESN任务/strict与泛化仍未完成。

## 2026-10-01 15:16 UTC seed52 冻结运行时复核完成

同checkpoint、同参数在MuJoCo3.11.0完成ESN/MLP两条55s开发复核。两条MJB均精确匹配
冻结5eaee4aa；实际cgroup≤3GiB/单线程、manifest/源码/模型检查通过，子进程均rc0。
ESN仍停lift，task/strict=false，三指标48.971mm/43.600Nm/.116950m/s；
MLP task=true/strict=false，46.908mm/45.907Nm/.070165m/s。相较先前3.14.0，
ESN RMSE降低23.252mm但未修复任务，不能将版本偏移当作全部失败原因。

新旧四条重新审计action/储备池重放误差为0。ESN最后10秒误差中位28.920mm、速度
0.000860m/s、ready=0，输入/储备池没有上述截断/饱和；离线清空历史会改变action
RMS .157981，但不证明闭环会改善。下一步重点诊断历史状态与读出的持续偏置，
训练期历史扰动需与同预算MLP对照；不改环境和gate，不解锁formal。

已完成：冻结复核、独立审计和离线记忆诊断；运行中：无仿真；未完成：ESN任务/strict
稳健成功与跨条件验证。详见[复核报告](ESN_MLP_FROZEN_RUNTIME_PAIR_20261001.md)。

## 2026-10-01 14:50 UTC 完整性审计与运行时偏移纠正

最新六条开发回合补强审计完成：ESN task 0/3、MLP task 3/3，strict 双方均 0/3；
seed52 ESN 停 lift（72.223 mm / 44.403 Nm / 0.125044 m/s），MLP 完成放置
（46.980 mm / 45.918 Nm / 0.070165 m/s）。这些是多个开发设置，不是三次独立同分布重复。
源数据未改，动作/储备池精确重放、checkpoint/MJB绑定及物理数组有限值检查通过。

发现最近 MJB 对应 MuJoCo 3.14.0，旧冻结运行时为 3.11.0，双方不能互读 MJB。
最新六条同模型配对有效，但不能与旧批次作算法单因素排名。下一次评估须显式使用
/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python，先核验 3.11.0、
模型 hash、source/config/checkpoint 与 MemoryMax，再做同 checkpoint 的运行时诊断。
不重新训练来掩盖版本混杂，不改环境/gate，不解锁正式步长。

seed42 配置已恢复，seed52 独立保存；历史命令不重写。窄屏/seed52 没有独立 execution.json，
历史 MemoryMax 未证实，配置也不是训练前 Git 提交；撤回这些过强的记录描述。
本轮没有启动仿真；既有子 agent 已完成，本机/服务器未见相关运行中的评估任务。
GitHub/Spark 经获准网络访问恢复，已读取 main ba84ed8 与 baseline 699e317，未合并 baseline。
详细审计与归档收据见 [ESN_MLP_TEMPORAL_INTEGRITY_20261001.md](ESN_MLP_TEMPORAL_INTEGRITY_20261001.md)。

已完成：六条重新审计、配置修复、运行时定位、服务器hash归档；运行中：无新实验；未完成：strict 成功、
跨条件泛化、冻结运行时的本轮 checkpoint 复核及 formal dt=5e-5。

## 2026-10-01 temporal-consistency `delta=0.25` seed replication（本地完成，待同步）

针对窄屏中唯一到达 retreat 的 `delta_weight=0.25` ESN，使用第二训练 seed
`2026100152`（MLP `2026100153`）复现；manifest、7/2 split、combined-v4、gate、
纯本体输入和执行器限制均未变。ESN 在 lift 停止，task/strict=false，RMSE
`72.223 mm`、峰矩 `44.403 Nm`、峰速 `0.125044 m/s`、穿透 `0.131457 mm`、
推杆最长连续接触 `0.0471 s`；MLP task=true、strict=false，最终 retreat，
RMSE `46.980 mm`、峰矩 `45.918 Nm`、峰速 `0.070165 m/s`、穿透 `0.151728 mm`。

两条均为开发 `dt=1e-4`、55 s、550000 子步。独立审计
`outputs/esn_mlp_temporal_consistency_replication_20261001_s52/INDEPENDENT_AUDIT.json`
显示 action replay 和 ESN reservoir replay 最大误差为0，三项物理指标重算一致。该
复现否定首轮 `delta=0.25` ESN 的稳健改善，formal `dt=5e-5` 继续锁定；专题报告见
[`ESN_MLP_TEMPORAL_CONSISTENCY_REPLICATION_20261001.md`](ESN_MLP_TEMPORAL_CONSISTENCY_REPLICATION_20261001.md)。

## 2026-10-01 temporal-consistency narrow follow-up（本地完成，待同步）

在上一轮 `delta_weight=0/0.5/1.0` 屏幕后，预注册窄区间
`delta_weight=0.25/0.75`，只改变加权相邻 action 增量损失。锁定 teacher
manifest SHA256=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、
7/2 identity split、canonical48D/action7、ESN/MLP 宽度128、combined-v4、原
gate、纯本体 actor 输入和执行器限制。ESN seed=`2026100150`，MLP
seed=`2026100151`；四条都是开发 `dt=1e-4`、55 s、550000 物理子步。

| delta | 方法 | task | strict | 最终阶段 | RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 球反弹 | 推杆最长连续接触 s |
|---:|---|:---:|:---:|---|---:|---:|---:|---:|:---:|---:|
| 0.25 | ESN | 否 | 否 | retreat | 52.502 | 45.556 | 0.117007 | 0.146245 | 是 | 0.7673 |
| 0.25 | MLP | 是 | 否 | retreat | 44.193 | 44.268 | 0.093121 | 0.140633 | 是 | 0.1243 |
| 0.75 | ESN | 否 | 否 | carry | 74.311 | 43.161 | 0.108427 | 0.136028 | 是 | 0.0025 |
| 0.75 | MLP | 是 | 否 | retreat | 45.095 | 45.203 | 0.074644 | 0.099006 | 否 | 0.0123 |

`delta=0.25` ESN 到达 retreat 且推杆连续接触最长，但没有完成放置；两条 MLP
完成 task，仍因柱子接触覆盖不足或球反弹失败而 strict=false。独立审计
`outputs/esn_mlp_temporal_consistency_narrow_20261001/INDEPENDENT_AUDIT.json`
重放 action/ESN reservoir 状态误差均为0，并从物理子步重算三项指标。没有
strict 候选，formal `dt=5e-5` 继续锁定；结果不支持 ESN 相对 MLP 的优势。
专题报告见 [`ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md`](ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md)。
本轮大产物仅本地，arm1 与 GitHub 网络仍不可达。

## 2026-10-01 temporal-consistency seed replication（本地完成，待同步）

对首轮 `delta_weight=1.0` 候选使用第二训练 seed `2026100142`（MLP `2026100143`）复现，其他协议完全不变。ESN 在 carry 停止，task/strict=false，RMSE `257.986 mm`、峰矩 `44.770 Nm`、峰速 `0.1423 m/s`、穿透 `0.1774 mm`；MLP task=true、strict=false。两条均为开发 `dt=1e-4`、55 s、550000子步，独立 action/储备池/物理审计通过。该复现否定首轮单 seed 的稳健 ESN 改进，formal `dt=5e-5` 继续锁定；证据在 `outputs/esn_mlp_temporal_consistency_20261001_rep_seed42/`，仅本地待同步。

## 2026-10-01 temporal-consistency loss screen（本地完成，待同步）

在锁定 manifest、7/2 identity split、canonical48D/action7、128 宽度和 frozen combined-v4 上，只改变训练目标：weighted action MSE 加 `delta_weight` 倍相邻 action 增量 MSE，候选 `0/0.5/1.0`。环境、gate、禁止输入和执行器限制均未改；ESN seed `2026100140`、MLP seed `2026100141`。

六条开发回合均为 `dt=1e-4`、55 s、550000 物理子步。ESN 全部 task/strict=false，最终 carry/carry/load_transfer；`delta_weight=1.0` 的 ESN RMSE 40.378 mm，但停在 load_transfer。MLP 的 `0.5/1.0` 完成 task，strict 仍 false，原因是 required contact coverage 不足。指标、checkpoint 和失败原因详见 [`ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md`](ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md)。

六条独立审计均通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP reservoir replay 为 null，物理子步均为550000。无 strict 候选，formal `dt=5e-5` 继续锁定。原始证据保留在三个 `outputs/esn_mlp_temporal_consistency_20261001_dw*/` 目录；GitHub/arm1 当前不可达，产物仅本地待同步。

## 2026-10-01 low-scale weight-decay screen（本地完成，待同步）

在锁定 teacher manifest（SHA256 `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`）上完成成对 ESN/MLP weight-decay 屏幕。固定 canonical48D/action7、7/2 identity split、128 宽度、`input_scale=0.25`、combined-thick-corner-pillar-v4、原 gate、纯本体输入和执行器限制，只改变 AdamW `weight_decay=1e-5/1e-4/1e-3`。训练 seed 为 ESN `2026100130`、MLP `2026100131`。

所有六条都是开发 `dt=1e-4`、55 s、550000 物理子步。ESN 三组 task/strict 均为 false，均在 `lift` 停止；MLP 三组 task=true、strict=false，均因柱子等 required contact coverage 不足而未过 strict。指标（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）为：

| weight decay | ESN | MLP |
|---:|---|---|
| 1e-5 | `77.173 / 42.170 / 0.1106 / 0.1635` | `48.442 / 44.781 / 0.0662 / 0.1106` |
| 1e-4 | `75.485 / 42.723 / 0.1078 / 0.0997` | `60.176 / 45.249 / 0.1172 / 0.1323` |
| 1e-3 | `73.093 / 41.235 / 0.1134 / 0.0919` | `47.831 / 44.426 / 0.0702 / 0.1666` |

六条独立审计均通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP reservoir replay 为 null，物理子步均为550000。两次仿真前 setup failure（hash变量错误、teacher root错误）已保留并明确不计实验回合。新增专题报告见 [`ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md`](ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md)；原始 rollout、MJB、checkpoint、审计保留在三个 `outputs/esn_mlp_low_scale_weight_decay_20261001_wd*/` 目录。GitHub 与 arm1 当前不可达，产物仅本地待同步；formal `dt=5e-5` 继续锁定，结果不支持 ESN 优势。

## 2026-10-01 低输入尺度 ESN output-gain 屏幕

在同一 `input_scale=0.25` checkpoint 上预注册只改输出增益 `0.80/0.90/0.95`，其余
teacher manifest、7/2 split、canonical48D/action7、combined-v4、gate、禁止输入和执行器
限制均未变。三条开发回合均为 55 s/550000 子步、`dt=1e-4`，结果为：`.80` 停 lift，
RMSE/峰矩/峰速/穿透 `60.590/37.618/.1031/.1257`；`.90` 停 carry，
`144.782/37.867/.1395/.1705`；`.95` 停 lift，`73.919/37.051/.1019/.1150`。三条
task/strict 全部否，柱子覆盖均失败。独立 action/ESN reservoir replay 最大误差为0，
物理子步均为550000；没有候选解锁 formal `dt=5e-5`。完整结果见
[`ESN_LOW_SCALE_GAIN_SCREEN_20261001.md`](ESN_LOW_SCALE_GAIN_SCREEN_20261001.md)，原始回合
保留于 `outputs/esn_low_scale_gain_screen_20261001_v1/`，服务器归档待网络恢复。

## 2026-10-01 低输入尺度 ESN alpha 屏幕

在先前 `input_scale=0.25` 单 seed task-success 候选上预注册只改 action-readout
平滑 `alpha=0.25/0.50/0.75`。低尺度 base checkpoint SHA256 为
`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`；teacher
manifest、7/2 identity split、canonical48D/action7、combined-v4、gate、禁止输入和
执行器限制均未变。三条都是开发 `dt=1e-4`、55 s、550000 子步：

| alpha | task | strict | 阶段 | RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆最长接触 s |
|---:|---:|:---:|---|---:|---:|---:|---:|---:|
| .25 | 否 | 否 | lift | 68.485 | 35.127 | .1010 | .1423 | .0056 |
| .50 | 否 | 否 | carry | 138.424 | 39.585 | .1275 | .1373 | .6642 |
| .75 | 否 | 否 | lift | 59.341 | 37.282 | .1041 | .1101 | .0064 |

三条均未完成放置，且柱子接触覆盖均不满足；`.75` 还未通过球反弹条件。独立审计显示
每条 action replay/ESN reservoir replay 最大误差均为0，物理子步均为550000。结果只说明
平滑改变停滞位置，不能支持 ESN 泛化或相对 MLP 优势；没有 strict 候选，formal `dt=5e-5`
继续锁定。完整结果见 [`ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md`](ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md)，
原始回合保留于 `outputs/esn_low_scale_alpha_screen_20261001_v1/`；服务器归档待网络恢复。

## 2026-10-01 固定 reservoir / readout seed 分解（本地，待同步）

为区分 input-scale=0.25 单 seed 成功中的 reservoir 与读出随机性，固定 reservoir seed=`2026100101`，只改变 readout seeds=`2026100121/22/23`；input scale、teacher、MLP、环境、gate、输入和执行器限制均不变。ESN 三条 task/strict=`0/3`、`0/3`，最终 lift/carry/carry；MLP 三条 task=`3/3`、strict=`0/3`。所有行仍为开发 `dt=1e-4`、55 s/550000 子步，动作/状态/物理审计通过。固定 reservoir 不能消除 ESN seed 敏感性，formal `dt=5e-5` 继续锁定；收据 SHA=`eda963478fa3362d7ed4078bb6d6e9eb1bd500126310670eed8b83bfcbe54af6`。详见 [`ESN_FIXED_RESERVOIR_20261001.md`](ESN_FIXED_RESERVOIR_20261001.md)。

## 2026-10-01 纯 ESN input-scale 屏幕与三种种子复现（本地，待同步）

第三轮单因素屏幕只改变 ESN 输入权重尺度 `0.25/0.45/0.80`。low=`0.25` 的 ESN 首次完成 task（retreat），指标为 RMSE `68.471 mm`、峰矩 `48.004 Nm`、峰速 `0.1164 m/s`、穿透 `0.1499 mm`，但 strict=false；0.45 ESN 在 carry 停止且穿透 `0.7154 mm`，0.80 ESN 在 load_transfer 停止。三组 MLP 对照均 task=true、strict=false。

对唯一 task=true 的 ESN low 候选做预注册种子 `2026100118/19/20` 复现后，ESN task/strict 为 `0/3`、`0/3`，分别停在 lift；因此单 seed 成功不能称为稳健泛化。复现仍是同一 manifest、7/2 split、场景、gate、actor 输入、执行器限制、55 s、开发 `dt=1e-4` 和 550000 子步。所有 12 条（屏幕6+复现6）动作 replay、ESN 状态 replay 和物理子步审计通过，没有任何 strict 通过，formal `dt=5e-5` 继续锁定。屏幕收据 SHA=`0fe9e346533fb27ba4ba306b49d9bc128dbe2bf584b1a168d1ae8dba934e42a2`，复现收据 SHA=`688ae6b3556023d64eb1c68ba2d84cde0b6ca461892240cbe9f8a83666b484f2`。详见 [`ESN_INPUT_SCALE_20261001.md`](ESN_INPUT_SCALE_20261001.md)。

## 2026-10-01 纯 ESN spectral-radius 屏幕（本地，待同步）

在上一轮 leak 时间尺度屏幕之后，预注册只改变固定 128 单元 ESN reservoir 的谱半径：`0.60/0.90/1.10`，每组都配同宽度 MLP 对照。teacher manifest、canonical48D/action7、7/2 identity split、估计负载训练权重、combined-v4 场景、原 gate、actor 输入、执行器限制、seed `2026091751`、55 s、开发 `dt=1e-4` 和 550000 子步均未变。

三组 ESN task/strict 均为 false：谱半径 0.60 在 lift 停止（RMSE `934.262 mm`、峰矩 `53.141 Nm`、峰速 `0.2172 m/s`、穿透 `0.1127 mm`），0.90 在 lift 停止且穿透超限（`144.160 / 50.655 / 0.2157 / 1.5602`），1.10 到 carry 但未放置（`224.085 / 45.164 / 0.2020 / 0.1049`）。MLP 仅 0.90 完成 task，strict 仍为 false；其余 MLP 也失败，不能把 task 完成写成 strict 通过。

独立审计 `outputs/esn_mlp_spectral_screen_20261001/INDEPENDENT_AUDIT.json` 通过：六条均为 550000 物理子步，动作重放最大误差为 0，ESN 储备池回放最大误差为 0。完整训练/闭环 metadata、失败回合和 73 文件收据保留在 `outputs/esn_mlp_spectral_screen_20261001_{low,baseline,high}/`，收据 SHA256=`6505943bf8a8711fb03a2e48a86545cc1937e77b8f1e64c5e9459179a182ae0`；详见 [`ESN_SPECTRAL_SCREEN_20261001.md`](ESN_SPECTRAL_SCREEN_20261001.md)。没有候选解锁 formal `dt=5e-5`。

## 2026-10-01 纯 ESN reservoir leak 时间尺度屏幕（本地，待同步）

在固定 teacher manifest、canonical48D/action7、128 单元、7/2 identity split、估计负载训练权重和 combined-thick-corner-pillar-v4 闭环上，预注册只改变 ESN reservoir 的三组 leak 时间常数：fast `0.04/0.16/0.64 s`、baseline `0.08/0.40/1.60 s`、slow `0.16/0.80/3.20 s`。每组都训练同宽度 MLP 对照；环境、原 gate、actor 输入、执行器限制、seed `2026091751`、55 s、开发 `dt=1e-4` 和 550000 物理子步均未变。

结果为：fast ESN 在 lift 停止（task/strict=false，RMSE `182.592 mm`、峰矩 `55.548 Nm`、峰速 `0.1311 m/s`、外部穿透 `0.1669 mm`）；baseline ESN 在 carry 停止（`86.080 mm / 40.585 Nm / 0.0862 m/s / 0.1540 mm`）；slow ESN 在 lift 发散（`717.503 mm / 58.190 Nm / 0.5007 m/s / 0.1732 mm`）。fast/baseline MLP 完成 task 但 strict=false，slow MLP 在 load_transfer 停止；不能把 MLP task 完成写成 strict 通过。六条均为开发结果，没有候选解锁 formal `dt=5e-5`。

独立审计 `outputs/esn_mlp_tau_screen_20261001/INDEPENDENT_AUDIT.json` 通过：六条都是 55 s/550000 子步，动作重放最大误差均为 0，ESN 储备池状态重放最大误差均为 0，RMSE/峰矩/峰速由物理子步文件复算一致。训练/闭环脚本、checkpoint、execution metadata、失败回合和 70 文件收据保留在 `outputs/esn_mlp_tau_screen_20261001_{fast,baseline,slow}/`，汇总收据 SHA256=`361116939aee2ef4b6bedbcba828b215a516de3158434c00161e7e9c4694eea0`。详见 [`ESN_TAU_SCREEN_20261001.md`](ESN_TAU_SCREEN_20261001.md)。

本轮开工已核对 main 缓存 SHA `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 和 baseline 缓存 SHA `4dad929b6550b167943becd271836f0c74a21a38`；GitHub/arm1 在本轮网络限制下不可达，故本轮产物目前仅本地、待同步，未声称服务器归档。失败原因保留为 ESN 分别在 lift/carry 阶段失去任务进展；未调整 gate、环境或输入字段。

## 2026-10-01 纯 ESN output-gain 屏幕

在 alpha 屏幕之后，预注册只改变 v4 ESN checkpoint 的输出增益
`output_gain=0.80/0.90/0.95`，不组合 alpha，也没有修改 office-v5、gate、
canonical48D 输入、执行器限制或 MLP。计划配置为
`configs/esn_gain_screen_20261001.json`，配置 SHA256 为
`1d0e8cb73db0a8effa142a3fcdbc2dd026edf70eaa4517231b72815895ce5c90`；基准
checkpoint `outputs/vmc_teacher_esn_mlp_weighted_20261001_v4/esn_weighted.npz`
SHA256 为 `bb0bd4df0f9467932c15999853f67fe662aaf5f34c06b79855d4d1ab9a4cf1b0`。
预注册源码提交为本地 `9e9580a`，因本轮网络限制尚未推送 GitHub。

三条开发回合都使用相同 combined-thick-corner-pillar-v4、seed `2026091751`、
55 s、`dt=1e-4` 和 550000 个物理子步：

| output_gain | task | strict | 最终阶段 | RMSE mm | 峰值力矩 Nm | 峰值速度 m/s | 穿透 mm | 推杆最长接触 s |
|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0.80 | 否 | 否 | carry | 520.286 | 41.950 | 0.1879 | 0.1688 | 2.3685 |
| 0.90 | 否 | 否 | lift | 407.785 | 46.242 | 0.2134 | 0.1350 | 0.2759 |
| 0.95 | 否 | 否 | lift | 454.745 | 44.605 | 0.2160 | 0.1243 | 0.2722 |

三条均未完成放置，不能解锁 formal `dt=5e-5`。独立审计
`outputs/esn_gain_screen_20261001_v1/gain_{080,090,095}_audit.json` 均通过：
动作重放最大误差为 0、储备池状态重放最大误差为 0、物理时长为 55.000000000000014 s、
物理子步为 550000。失败回合、原始 rollout、MJB、checkpoint 和日志均保留在
`outputs/esn_gain_screen_20261001_v1/`，并已逐项核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_gain_screen_20261001_v1/`。
文件收据 `FILE_SHA256_REL.txt` SHA256 为
`6ed5e73204de983d481200bcf5082a50e1259fbd55a281934aa33e7460dcff74`；对应提交
`7fa6a6e39459cf846f21400c7f5fa5d4301da1ca` 的源码快照位于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7fa6a6e39459cf846f21400c7f5fa5d4301da1ca/repository.tar`，
SHA256 为 `1a79dd2583859e38ce785d2cd96bfb5efd1b0a2af436c4565224123c92277015`。

这组屏幕没有找到成功候选；gain=0.80 的推杆连续接触最长，但 RMSE 较大且最终停在
carry，gain=0.90/0.95 在 lift 停滞。结论只支持“固定 teacher bank 下的输出增益屏幕未解决
ESN 闭环失稳”，不支持 ESN 优于 MLP，也不支持真实环境部署结论。

## 2026-10-01 paired ESN/MLP seed 屏幕

为区分 ESN 随机初始化方差，按预注册配置
`configs/esn_mlp_seed_screen_20261001.json` 在同一 manifest（SHA256
`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`）上成对训练
seed `2026100106/07/08`。每组均为固定 7 条训练身份、2 条留出身份、估计负载训练权重、
canonical48D/action7、128 宽度；环境、gate、actor 输入和执行器限制没有改变。

训练验证加权 MSE 与闭环结果如下。闭环均为 combined-v4、55 s、550000 子步、开发
`dt=1e-4`，独立审计均通过 action replay、ESN 储备池 replay 和三项物理子步复算：

| seed | 方法 | val weighted MSE | task | strict | 最终阶段 | RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm |
|---:|---|---:|---:|---:|---|---:|---:|---:|---:|
| 106 | ESN | 5.250e-5 | 否 | 否 | lift | 874.772 | 55.664 | 0.1639 | 0.1089 |
| 106 | MLP | 1.907e-5 | 是 | 否 | retreat | 52.402 | 44.708 | 0.0730 | 0.1772 |
| 107 | ESN | 5.648e-5 | 否 | 否 | load_transfer | 187.222 | 47.666 | 0.1601 | 0.1612 |
| 107 | MLP | 1.693e-5 | 是 | 否 | retreat | 33.860 | 44.542 | 0.0707 | 0.1530 |
| 108 | ESN | 5.954e-5 | 否 | 否 | lift | 37.743 | 38.843 | 0.0721 | 0.1714 |
| 108 | MLP | 1.759e-5 | 是 | 否 | retreat | 43.083 | 45.083 | 0.0724 | 0.1843 |

ESN checkpoint SHA256 依次为 `08f223201de36352115e8b944028d3fc875e33b4a2135f9e3a9e8e3f07df3083`、
`7a72a25743087bc0119cb0545a370119d251e624a19aeb15f8f0555844d0503a` 和
`f7d4e0cf5beabddad9a440da9585399f54d23388e1b460f3c6d37fd41168d4b7`；对应 MLP 为
`b7579559269ba234d99754ef58f59faf99240e5c040461697b64439088a6c227`、
`783f64be585e7fd5ed0afb72ac68d5df85c59d625b1263e3bfcfc5eb93f0a950` 和
`bee7d284edee1064fe5de05bced2747c4c32610c97b00745fddef4fab5e9134a`。seed=108 的 ESN
数值指标已接近成功，但 placement gate 未完成，不能记为 task success；三组均不解锁
formal `dt=5e-5`。完整训练 metadata、失败回合和审计保留在
`outputs/vmc_teacher_esn_mlp_seed_screen_20261001_s{106,107,108}_correct/`。
三组完整原始证据（含训练 metadata、checkpoint、rollout、失败日志和审计）已归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_mlp_seed_screen_20261001_v1/`；
证据 tar SHA256=`12ebe6d9529df5dd0bc967a45ed7a5ac77d1d0e4774d8fe10203ac5f158e5aa8`，三份
相对文件收据均在对应 seed 目录。提交 `9888f6cc361004a70a24851e7915062ca5962a5f` 的源码
快照位于 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9888f6cc361004a70a24851e7915062ca5962a5f/repository.tar`，
SHA256=`36563d9b960253ba1ec4a71ac3a4a1fea3966aa9afbdfe4727ad271e5ee9c589`。

## 2026-10-01 纯 ESN action-readout alpha 屏幕

为测试闭环振荡/过冲是否来自 ESN action 更新过快，预注册只改 ESN checkpoint 内部的
readout smoothing `alpha`，候选固定为 `0.25/0.50/0.75`。VMC teacher、MLP、场景、gate、
canonical48D 输入和执行器限制完全不变；alpha 屏幕计划和 base/config hash 见
`configs/esn_alpha_screen_20261001.json` 与
`outputs/esn_alpha_screen_20261001_v1/SCREEN_PLAN.json`。

三个候选均使用同一 combined-v4、55 s、550000 子步、开发 `dt=1e-4`：

| alpha | task | strict | 最终阶段 | RMSE mm | 峰值力矩 Nm | 峰值速度 m/s | 穿透 mm | 推杆最长接触 s |
|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 0.25 | 否 | 否 | lift | 367.725 | 50.319 | 0.2420 | 0.6467 | 2.2952 |
| 0.50 | 否 | 否 | lift | 411.708 | 36.347 | 0.2306 | 0.1787 | 0.5018 |
| 0.75 | 否 | 否 | carry | 95.040 | 41.629 | 0.0848 | 0.1276 | 0.0038 |

三条回合的动作重放和 ESN 储备池状态重放均为 0，物理子步审计均为 55 s/550000；独立
审计分别位于 `outputs/esn_alpha_screen_20261001_v1/alpha_025_audit/`、`alpha_050_audit/`
和 `alpha_075_audit/`。alpha=0.75 在三项数值指标上较好但仍未完成任务，alpha=0.25
虽延长推杆接触却违反穿透门槛。该屏幕没有成功候选，不解锁 formal `dt=5e-5`；失败回合
全部保留。完整 38 文件已归档并核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_alpha_screen_20261001_v1/`，
收据 `FILE_SHA256_REL.txt` SHA256=`45dcf2d710a8ea12cd0f6ba0277669da76deb6af889347e6ec1f9e01575fbffa`。

## 2026-10-01 v3：修正过滤标签后的公平闭环重跑

在继续 ESN/MLP 比较前，修正训练脚本的标签出口：目标现在明确读取每条
`execution_chain.npz/filtered_action`，同时保留并校验 `rollout.npz/applied_action`。
训练 metadata 另写入 execution-chain hash，并固定 ESN/MLP 推理源码 hash；新增回归测试覆盖
这个语义。冻结 teacher manifest（SHA256
`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`）和场景、gate、actor
输入、执行器限制均未改变。

v3 使用 seed `2026100104`、估计负载训练权重 `1+3*tanh(||wrench[39:45]||/0.5)`，新模型与
审计位于 `outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/`。在同一无初始细步的
combined-v4 开发命令下，所有行都是 55 s / 550000 物理子步、`dt=1e-4`：

| 方法 | task | strict | 最终阶段 | RMSE mm | 峰值力矩 Nm | 峰值速度 m/s | 外部穿透 mm |
|---|---:|---:|---|---:|---:|---:|---:|
| 冻结 VMC teacher | 通过 | 否 | retreat | 43.438 | 50.324 | 0.1008 | 0.1525 |
| v3 ESN | 否 | 否 | carry | 406.806 | 43.246 | 0.2404 | 0.1929 |
| v3 MLP | 通过 | 否 | retreat | 43.333 | 44.405 | 0.0753 | 0.1012 |

ESN 与 MLP 的动作重放误差均为 0；ESN 储备池重放误差为 0，三项物理子步指标和
55 s/550000 子步审计通过。v3 MLP 保持 task 成功但没有满足持续接触 strict；v3 ESN
在 carry 停滞。v3 不解锁 formal `dt=5e-5`，失败回合和首轮带细步诊断均保留。
v3 checkpoint SHA256：ESN `a5560ca073c3afed6d553c1ee7a37ac32d537f1245aa6369feabeb022dff40b4`，
MLP `e27c4ed63cd5f604c5338c90aa87b09e61a90f401a2d92f674c1e69a501e45f0`；独立审计为
`outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/independent_audit_norefine/AUDIT.json`。
当前本机仿真 0；v3/v4 已归档并逐项核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`
（68 文件，收据 `FILE_SHA256_REL.txt` SHA256=`ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`）。

随后完成一个预注册无负载权重对照 v4（seed `2026100105`，emphasis `0`），用来区分负载
加权和 ESN 随机读出影响。相同 55 s/550000 子步 frozen command 的结果为：ESN
task/strict `false/false`、最终 `lift`、RMSE `526.818 mm`、峰矩 `44.416 Nm`、峰速
`0.2204 m/s`、穿透 `0.1323 mm`；MLP `true/false`、放置完成、RMSE `38.832 mm`、
峰矩 `44.286 Nm`、峰速 `0.0807 m/s`、穿透 `0.1527 mm`。动作重放和 ESN 储备池重放
仍为 0，独立审计位于 `outputs/vmc_teacher_esn_mlp_weighted_20261001_v4/independent_audit_norefine/AUDIT.json`。
v3/v4 都表明当前九条 VMC teacher 轨迹下 MLP 的闭环任务完成较稳定，而 ESN 在 lift/carry
之间随机失稳；两者均未通过 sustained-contact strict，不能宣称 ESN 优势或解锁正式步长。
服务器归档未覆盖既有 v1 目录。

## 2026-10-01 VMC teacher 数据上的 ESN/MLP 加权读出续实验

在冻结的 combined-thick-corner-pillar-v4、canonical48D/action7、执行器
限制和原始 gate 下，新增一轮只改训练损失的公平比较。ESN 与 MLP 均保持
128 单元预算；训练时对估计力/负载本体通道使用预注册的平滑权重
`1+3*tanh(||wrench[39:45]||/0.5)`，该权重不进入 actor、没有运行时 gate，
也没有增加任何禁用输入。完整报告见
[VMC teacher→ESN/MLP weighted](VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md)。

新 checkpoint 的独立闭环结果（开发 `dt=1e-4`，55 s/550000 子步）如下：

| 方法 | task | strict | placement | RMSE mm | 峰值力矩 Nm | 峰值速度 m/s | 柱最长接触 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| VMC teacher（原 v5） | 通过 | 否 | 完成 | 43.438 | 50.324 | 0.1008 | 0.0670 |
| weighted ESN | 否（lift停滞） | 否 | 未完成 | 688.378 | 62.020 | 0.1800 | 0.0050 |
| weighted MLP | 通过 | 否 | 完成 | 50.381 | 46.634 | 0.0823 | 0.6056 |

weighted MLP 的推杆接触时间明显高于原 v5 MLP 的 0.0127 s，同时完成放置，
但仍未满足原始持续接触门槛；weighted ESN 仍在 lift 失败。ESN held-out
动作 MSE 从 `4.40e-5/6.89e-5` 降为 `3.59e-5/4.08e-5`，MLP 从
`1.45e-5/2.87e-5` 降为 `1.23e-5/1.53e-5`，说明回放改善没有自动转化为
闭环严格成功。三项子步指标、动作/储备池状态重放与 hash 审计通过。两名学生
均 strict=false，因此没有解锁 `dt=5e-5` 正式重跑；失败完整保留，环境/gate
未改。运行中仿真 0。完整 campaign 已归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v1/`，
远端目录含 `ARCHIVE_FILE_LIST.txt` 收据，checkpoint hash 已逐项核对。

## 2026-09-30 三类数据生成与经典 baseline

13:55 UTC收尾：原十小时窗口结束，最后派发13:46:18、动态结束13:48:22、归档结束13:48:50，
服务rc0退出，截止后派发0。终态162搜索＋27验证（24动态/3初态无效）＋26collection。
全部26追加raw审计通过，9重复对57NPZ/612数组全同。严格VMC训练出口9唯一（厚角4、
短撞4、持续1），205排除、1因部分配对缺模型绑定而保守隔离；该隔离本身也未满足接触，
不代表已证明模型矛盾。无新ESN、运行中0，1000合格/类与综合泛化均未完成。
最终配对指标及局限见[十小时交接](TEACHER_BANK_TEN_HOUR_REPORT_20260930.md)。

13:01 UTC：预注册验证24动态＋3初态无效，共27条目完整记账，独立三指标/动作/source
审计通过。有效8个fixture上的VMC/导纳/阻抗录取3/8、0/8、4/8；不把缺失的第9个场景
藏掉，也不把task与曝光录取混为一谈。持续推碰仍未满足要求。验证不回流调参，稳定
collection已开始、原截止不变；重复anchor不增唯一标签，无新ESN。比较和raw审计1850文件
已核验至服务器runs/main/teacher_bank_review_checkpoint_20260930_1300/evidence/，详见
[锁参验证报告](TEACHER_BANK_LOCKED_VALIDATION_20260930.md)。

12:47 UTC：新增严格train-only标签出口及去重，原锁定快照仍仅2/3/1个唯一合格VMC
训练fixture，无新ESN。预注册验证发现一条棍推初态约60mm交叉，三方法均保留拒绝，
不是控制器动态失败；未换场景或调参。独立continuation v2接续剩余验证和原collection，
13:48:16截止不变。首次接续v1在资源检查阶段零派发失败，CPU controller缺失已明确记录，
v2单sim/1线程/MemoryMax3GiB/Swap0；不再声称CPUQuota配置请求就是实际执行配额。
相关70测试通过；源码、协议、严格标签及诊断已核验共享路径见[三类记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)。

11:44 UTC：162搜索全部完成，27录取/135未录取，独立候选/排名/source/model审计认证
bank锁定。最终训练录取厚角VMC/导纳/阻抗2/3、0/3、2/3；短撞3/3、1/3、2/3；持续
1/3、0/3、0/3。持续阻抗仍有task/strict 2/3，不能把0录取说成0任务能力。
27验证已启动、参数不回调，collection尚未开始；VMC唯一合格训练fixture为2/3/1，无新ESN。
完整BO27/27与首个人推raw审计通过；49文件证据已核验至服务器runs/main/
teacher_bank_review_checkpoint_20260930_1138/evidence/；锁参/公平表/162点图等1609文件已核验
至teacher_bank_review_checkpoint_20260930_1150/evidence/，见[锁参报告](TEACHER_BANK_LOCKED_SEARCH_20260930.md)。

11:31 UTC：持续人推首次录取（VMC c05 anchor0），原记录同段1.2643s让位14.3532mm、
task/strict true；同候选棍/推板仍失败，故1/3。独立raw复核正在进行，最后经典组还运行，
bank未锁定，无validation/collection/新ESN。定义有效字段投影3300唯一且train/val无精确
重复，不等于3300动态有效。c05短撞退化诊断和定义审计56文件已核验到服务器runs/main/
teacher_bank_review_checkpoint_20260930_1124/evidence/，详见[三类记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)。

11:10 UTC接续：完整c00–c04为135回合、23录取/112失败，c05仍运行；短撞VMC c04同参数
3/3而c05为0/3。参数未锁定，validation/collection/新ESN均未开始，保持原预算和截止。
资产覆盖审计发现旧Panda-only清单漏FR3，完整133文件已核验共享；本机冻结源码初始化
9/9原MJB逐字节复现，零积分。ARM首个静态重建有差异，补充采集阻断。原v10源/物理
及稳定服务未改；[更正报告](TEACHER_BANK_ASSET_REPRODUCTION_CORRECTION_20260930.md)
明确替代此前“全部实际资产已核验”的不完整表述。135检查点与本机静态证据112文件已
核验到服务器runs/main/teacher_bank_review_checkpoint_20260930_1104/evidence/。
公平比较工具分离任务/strict/接触/录取，指标采用三方法共同完整证据集合；11测试通过。

09:40 UTC：四个候选108回合完整，17录取/91失败、全部逐回合归档，c04运行。短撞VMC c03
同参数3/3，三指标独立重算和动作/状态重放通过；球形条件误差和电机峰矩降低，但接触峰力
升至2221N、穿透0.18863mm，仍不是安全部署或泛化证据。持续推碰三方法均0/12；参数未锁定，
validation/collection/新ESN未开始。详见[短撞审计](TEACHER_BANK_SHORT_C03_REVIEW_20260930.md)。
新终态工具11项测试通过；审计/源/验收964文件已核验归档至服务器runs/main/
teacher_bank_review_checkpoint_20260930_0913/evidence/。原六候选预算及派发截止继续遵守。

08:40 UTC检查点：三个初始候选81回合完整，10录取/71失败；实际BO已经开始。VMC唯一
合格fixture厚角2/短撞3/持续推碰0，仍非单参数跨条件成功率。首个BO的厚角VMC c03为1/3，
未超c01的2/3。独立汇总与冻结优化器同实现重放相符，参数向量差0；不宣称BO已经改善。
初始81点公平图和首次BO审计44文件已核验归档至服务器runs/main/
teacher_bank_review_checkpoint_20260930_0848/evidence/；详见[首次BO复核](TEACHER_BANK_FIRST_BO_REVIEW_20260930.md)。
固定搜索继续，参数未锁定，验证/collection/新ESN未开始，原13:48:16 UTC派发截止不变。

07:35 UTC：c00/c01共54回合完成并归档，8录取/46失败，第三组初始参数c02运行中。
VMC唯一合格训练fixture厚角2/短撞3/持续推碰0；短撞三条来自不同参数，不能说单控制器3/3。
collection仍0、无新ESN、参数未锁定，固定BO阶段尚未开始。三指标公平配对图工具已完成，
保留所有失败并绑定原audit hash；5项校验和视觉检查通过，服务器路径映射不改历史记录。
最新预算与图表归档见[三类主记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)。

06:32 UTC检查点：c00三类/三方法共27回合完整，5录取/22失败、全部有归档凭据；持续推碰
三方法均0/3，已继续c01，不改搜索预算。人手子步独立复核显示VMC连续1.2516s让位9.09595mm，
不能将跨间断的27mm宏观位移代替原1cm同段门槛；详见[人推复核](TEACHER_BANK_PERSON_ANCHOR_REVIEW_20260930.md)。
新审计及完整配对状态位于服务器runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/。

06:18 UTC：v10完成21条搜索，录取5条；其中VMC短撞2条已独立复核三指标/hash并重放，
正式collection仍0。c00厚角VMC/导纳/阻抗录取0/3、0/3、2/3，短撞2/3、0/3、1/3。
持续推碰VMC三条未录取，导纳正在运行；参数银行未锁定，尚无验证/新ESN结果。
VMC合格短撞峰力约1368/1350 N，阻抗合格短撞约2077 N，不能将电机峰矩合规当真实碰撞安全。
详见[独立复核](TEACHER_BANK_V10_FIRST_SEARCH_SUCCESS_AUDIT_20260930.md)及[当前预算/失败说明](TEACHER_BANK_THREE_DOMAINS_20260930.md)。
最新状态/工具已核验归档到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0621/evidence/`。
以下05:29/05:49为历史检查点，不代表当前数量。

按用户新增授权，构建每类1000训练＋100验证的厚桌角/短撞/持续推碰训练域，并将VMC、
导纳、阻抗纳入同场景同预算搜索。原冻结测试不变；尚未开始新ESN蒸馏。
截至05:29 UTC，v6六条主动pilot、v8九条全类别pilot已完成并核验归档；新厚边缘仅阻抗
一条通过，RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s，但接触分段很多，不能称平顺蹭过。
合格新VMC教师轨迹仍0。v5阻抗内存审计问题已修并独立复审归档；v8原记录完整保留。
人手曝光改为沿真实推力方向的连续接触位移，反向/纯切向/撤回后运动不能冒充让位。
候选排序修正为成功anchor数优先；实际资产、跨候选模型和曝光/物理时间轴关联核验已加。
73项测试通过。当前v10固定预算搜索本机单环境、1线程、3GiB执行，计算截止13:48:16 UTC。
旧corner task/strict结果不能
当作上抬碰face的证据；新增曝光诊断已纠正这一点，不弱化筛选来晋级。
已核验源码/配置位于
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/`。
详细预算、失败保留和实时状态见 [三类数据记录](TEACHER_BANK_THREE_DOMAINS_20260930.md)。
05:49 UTC v10首个厚桌角参数配对完成：VMC/导纳/阻抗录取0/3、0/3、2/3，候选尚未锁定，
不能当独立验证。九条pilot离线归因进一步区分晚期放置失败、收敛超时与接触分段统计：
球撞并非当场掉块，人推约27mm宏观让位也不等于连续接触通过，详见
[失败归因](TEACHER_BANK_PILOT_FAILURE_CAUSES_20260930.md)。新报告与复算源码已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`。
下文“当前无仿真”仅指先前teacher修正阶段，不表示本轮无作业。

## 2026-09-30 teacher 先修正、后蒸馏

用户要求先验证 teacher 在特化场景稳定，再做纯 ESN。正确归档 MuJoCo 3.11 的首轮
八条完整回合及独立审计已完成：三个修正均通过 corner 的 task/strict，原版失败；
综合场景 pair_average 完成任务、穿透 0.187935 mm，但缺少柱接触，strict 仍失败。
第二轮四条回合也已完成审计，目前无本任务仿真运行。速度项权重 0.25 + K×2/B×sqrt(2)
在 corner task/strict 通过，综合 task 通过、strict 因柱接触缺失失败；综合放置动作
差分 RMS 降低约 86.3%，RMSE/峰矩/峰速为 37.406 mm / 48.127 Nm / 0.070574 m/s。
共 12 条有效回合保留，teacher 各状态与公共过滤链重放误差全部为 0；尚未完成独立
特化全协议与跨条件验证，不自动进入 ESN 蒸馏。
详细机制、冻结模型哈希、解释器错误纠正和运行入口见 [修正记录](TEACHER_REPAIR_20260930.md)。
环境/gate/公共执行器不变；未解封保留场景、未启动 formal 或新 ESN 蒸馏。

用户重新明确 teacher 和 ESN 均可优化后，已恢复软件研究。原安全门、纯本体、
物理场景、共同执行器及三个保留布局继续冻结。没有完成最终科研目标，也
没有替换 R34、提交代码或重启定时任务。

## 已完成：J1 八回合 teacher 机制筛查

四个固定配置 × 原始/强球撞，全部 55 s，均正常退出，任务 8/8、严格 4/8。
四个原始条件通过；四个强球撞都因首次外部穿透 .207370134 mm 超过 .2 mm
而不通过，其中默认 teacher 还没有足够推杆接触。失败全部保留。

| teacher | 原始峰矩 Nm | 强球撞峰矩 Nm | 强球撞峰速 m/s | 强球撞 waypoint RMSE mm | 强球撞推杆接触 s |
|---|---:|---:|---:|---:|---:|
| 默认 | 39.424 | 42.952 | .118029 | 138.353 | 0 |
| 全动作半幅 | 38.068 | 38.511 | .137059 | 160.768 | .866 |
| 半幅＋阻尼×2 | 35.562 | 36.030 | .123578 | 163.084 | .700 |
| 半幅＋刚度×2、阻尼×sqrt(2) | 36.729 | 36.765 | .109692 | 163.295 | 1.222 |
| 存档 R34 ESN（参照，未重跑） | 36.719 | 38.501 | .114701 | 160.761 | .799 |

这些差异说明 teacher 仍有可调空间，不支持“已尽力、无法改进”。也没有一个
候选在所有指标上全面占优。默认 teacher 强球撞未形成推杆接触，不能把其
较低 waypoint RMSE 当成充分扰动下的优势。刚度候选相对 R34 强球撞峰矩
约降 4.5%、峰速降 4.4%，waypoint RMSE 升约 1.6%；当前只是一回合条件对照。
该指标包含阶段目标切换，并非连续参考轨迹跟踪误差。

刚度候选在原始/强球撞进入撤离阶段的时刻分别为 40.92/42.40 s，默认是
46.16/49.96 s；这是阶段推进时间，不等于任务最终成功时刻。最终物块 XY
误差和阶段停留时长也完整保存，不能仅按较小峰矩选择论文结果。

已完成 11,000 次动作及 teacher 内部状态的独立重放，动作最大差
5.55e-17。八条物理子步 RMSE/峰矩/峰速独立复算通过；各条件世界 MJB 与
R34 完全一致，记录控制源码 hash 与冻结源一致。原始归档约 0.7 GiB：

- [八回合完整表](../outputs/esn_office_joint_teacher_j1_20260927/J1_RESULTS.md)
- [独立审计和逐文件 hash](../outputs/esn_office_joint_teacher_j1_20260927/J1_AUDIT.json)
- [输出映射审计](../outputs/esn_office_joint_teacher_j1_20260927/action_contract/ACTION_CONTRACT_AUDIT.md)

## J2 候选两回合已完成；本机同源参照运行中

仅改变 teacher 动作归一化参数，执行器上限不变。两个既定条件，200 次
非饱和单位转换检查通过。Spark 启动请求在 TCP 连接阶段超时，未执行远端
命令；随后只读复核远端服务 LoadState=not-found，确认没有重复作业。

因此在本机启动单 worker、CPUQuota 100%、MemoryMax 3G、SwapMax 512M，
服务名 `esn-office-joint-teacher-j2-local-20260927.service`。两回合现均已正常
退出，原始与强球撞 task=true，strict 分别 true/false。目录：
`outputs/esn_office_joint_teacher_j2_20260927/source_snapshot/results`。
本机原始条件已完成 task=true、strict=true，但与 Spark 的 MJB hash 不同，
记录控制源码 hash 相同。读取两个 MJB 后发现资产路径长度、BVH 树排列不同，
以及惯量等浮点差异；虽原始首撞峰值仅差约 1.61e-9 mm，也不能据此证明完整
动力学等价或忽略 BVH 差异。J2 当前是机制候选，必须补充本机同源默认
teacher 参照并审计，才可隔离动作编码的闭环影响，不据跨主机比较替换模型。
在这两回合结束后，已按新冻结的 reference_plan.json 启动固定两回合同机
默认 teacher 参照，复用完全相同源目录及资产路径。服务名
`esn-office-joint-teacher-j2-reference-20260927.service`，仍仅一个 worker，
3G/512M 内存/交换、CPUQuota100%。日志位于 J2 根目录 reference_queue.log，
结果 job id 为 j2_default_reference_original/hard，原两回合不重跑。
这是为消除主机混杂补的参照，不是增加候选或按结果继续调参。
J1/J3 始终同 Spark 来源，不受此比较问题影响。

J2 快照 SHA256：`44a95c507f43b4f409073cae17252c7251d45a7def33ed9925be7214e3fdd7c3`。
稳定作业不迁移或重启；查当前 execution.json 再接续。

## 正在运行：J3 刚度候选补齐开发条件

J1 中刚度候选展示了峰矩/峰速与误差的权衡，值得检查条件敏感性；这不是
已宣布胜出。保持同一配置不重调，只运行提前7秒、提前9秒、保持6秒推杆及
正移布局四个剩余开发条件。与 J1 的原始/强球撞合并为六条件，禁止重复计数。
Spark 服务 `esn-office-joint-teacher-j3-20260927.service`，两个 worker，
6G/1G 内存/交换上限；启动前原另一项训练已自然结束，未被本任务终止。

远端目录：
`/home/arm1/vmc_mujoco_runtime/esn_office_joint_teacher_j3_20260927`。
本机快照目录：`outputs/esn_office_joint_teacher_j3_20260927/source_snapshot`。
快照 SHA256：`419d39a8e800403695c9782eb3535e541dc1c31e7528a6afc76c49a57de4492b`。

## 下一步验收与未完成项

收齐 J2/J3 后，先审计三项物理指标、动作/状态重放、源码、世界及主机差异。
J3 合并全部六条件，曝光不足继续按失败记录，保留布局不解封。没有候选
解决首次球撞；后续还需研究更广的本体状态驱动 teacher/ESN 结构，不能
重复将相同零输入读出改动当成首撞修复。

后续蒸馏需明确原始请求、执行接口过滤后的 action 和实际机器人执行量。
当前解析合成标签不等于已核验的物理 teacher bank。先选可解释的 teacher
机制，再进行学生闭环验证及匹配预算的记忆消融；本轮没有新 ESN checkpoint。

网络短时中断没有导致重跑或丢失 J1 数据；原传输连接恢复后已收齐八回合。
最后复核：J1 全部结果的远端/本机 rsync checksum dry-run 无差异；J3 服务
active/running，两个回合进展至约26 s，内存约1.24 GB。本机 J2 候选两回合
已正常退出，两个同机参照继续运行。后续接续先检查服务和 execution.json，
不据此静态记录重复启动。

## ESN 蒸馏训练（2026-09-27）

已冻结 teacher 后启动全 48D 纯本体 ESN 蒸馏：训练轨迹为 J1/J3 stiff
teacher 的四个开发条件，验证轨迹为提前 9 秒推杆和正移布局，seed
2026092707，128 单元多时间尺度 reservoir、128 单元非线性读出、单线程和
3GB 内存上限。标签是 teacher 提交给共同执行接口的七维 action，并保存
source trace hash；contact truth、ball state、event time、stage 和视觉信息
没有进入 actor。第一次服务因日志目录不存在而在执行前退出，已保留
`attempt_1.json`，无 checkpoint/数据产生；第二次服务
`esn-office-joint-train-stiff-20260927-v2.service` 已按相同参数启动。
训练完成后必须先做固定观测重放，再在六个开发条件中闭环评估；不能把
离线 action 拟合误差当成泛化成功。

评估注意事项：`run_office_batch_20260927.py` 将结果写入 benchmark 公共
`results/` 目录；本轮唯一批处理队列持有 lock，完成后会逐目录复制到
`outputs/esn_joint_stiff_student_eval_20260927/eval_v2/results/`，并记录
源文件 hash。公共目录中的六个 `student_*` 条目属于本轮 ESN，不能与旧
实验目录混用。

训练结果：训练完成，最佳验证 action MSE `0.0003169985`，checkpoint
SHA256 `833458682888b46a60411a32151f2107877ea63676dd533c0d75f83c9c62d320`。
模型 contract `proprio48_esn128_action7_v1`，输出层未加入额外 gate；完整
训练协议和失败尝试保存在 `outputs/esn_office_joint_esn_stiff_20260927/`。
六条件闭环服务 `esn-joint-stiff-student-eval-20260927.service` 已启动，
单本机 MuJoCo/单线程/3GB 内存上限；计划文件为
`configs/esn_joint_stiff_student_eval_20260927.json`。结果完成前不宣称
泛化或替换参考模型。

## DAgger 闭环复评（2026-09-27）

第一版学生的六条件闭环完成后，使用其实际访问的四类困难轨迹重新计算
stiff-VMC 标签，训练 `model_dagger_v1`。该模型仍是同一
`proprio48_esn128_action7_v1` 合约、128 单元多时间尺度储备池、7 维动作和
纯本体 48D 输入；没有加入接触真值、球状态、事件时间、阶段或视觉。模型
checkpoint SHA256 为
`7525048d87044f8cc30ae44fff00d510c755c4d1113908403fe8b6e96ef66619`，训练
记录见 `outputs/esn_office_joint_esn_stiff_20260927/model_dagger_v1/`。

首次批处理因默认 `/home/airpig/miniforge3/bin/python3` 缺少 Pillow，在任何
物理积分前六条均退出；这些失败条目保留在公共 `results/dagger_student_*`，
不得计入性能。随后使用已有成功评估环境
`.venv-canonical-rl/bin/python`，新 job id 为 `dagger2_student_*`，单 worker
完成六个开发条件。计划和独立审计分别为：

- `configs/esn_joint_stiff_dagger_eval_20260927.json`
- `outputs/esn_joint_stiff_dagger_eval_20260927/eval_v1/ESN_JOINT_AUDIT.json`

独立重放动作、储备池状态和物理子步 RMSE/峰矩/峰速均通过，结果如下：

| 条件 | task | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆接触 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| original | 通过 | 通过 | 156.354 | 36.692 | .143418 | .196148 | .851 |
| rod start7 | 通过 | 通过 | 134.586 | 40.466 | .143418 | .196148 | 1.318 |
| rod start9 | 通过 | 失败 | 140.663 | 40.661 | .143418 | .196148 | 0 |
| rod hold6 | 通过 | 通过 | 157.279 | 36.692 | .143418 | .196148 | .963 |
| shifted plus | 通过 | 失败 | 139.812 | 36.842 | .115245 | .175849 | .181 |
| hard ball | 通过 | 失败 | 165.774 | 36.463 | .109660 | .207795 | 1.386 |

因此 DAgger 版本在这六个**开发**条件上 `task 6/6`、`strict 3/6`，相对第一版
`task 4/6`、`strict 1/6` 有明确改善；但推杆时序提前/变化时仍有曝光失败，强
球撞仍超过 0.2 mm（0.207795 mm）。这不是 held-out 泛化或真实机器人证据，
也不能把 `6/6` 任务完成改写为六条件安全门全部通过。原始轨迹、每回合
execution、失败门、源文件 hash 和 plan/checkpoint hash 全部保留。

## DAgger2 与 wrench 加权消融（2026-09-27）

将 DAgger 六条实际闭环轨迹作为第二轮访问状态、仍由相同 stiff-VMC 根据
`obs[39:45]` 计算标签，得到 `model_dagger2_v1`（seed `2026092709`，
checkpoint SHA256 `2d0a2dbf17172bd3a6d1eaea537e3309e718fe3d61ed92ef96b02450acfa81c7`）。
六条件独立审计位于
`outputs/esn_joint_stiff_dagger2_eval_20260927/eval_v1/ESN_JOINT_AUDIT.json`：
`task 6/6`、`strict 3/6`，waypoint RMSE/峰矩较 DAgger1 多数下降，但严格
通过数没有继续上升。这表明访问状态扩充有帮助，却没有消除推杆曝光和首撞
门槛问题。

为区分“记忆不足”与“扰动状态样本权重不足”，另行训练了
`model_wrench_v1`（seed `2026092710`，wrench-norm 固定权重 3，仅使用
48D 中 actor 可见的 wrench 估计，checkpoint SHA256
`8975edeb50a68b583034ee1945ff4d8b57303158d64c705cc3d8af9621006352`）。其
离线验证 MSE 为 `2.13e-5`，明显高于 DAgger2 的 `8.28e-6`；六条件闭环
已完成独立运行，结果为 `task 6/6`、`strict 4/6`（见 wrench1 审计）；它
改善了严格通过数，但仍不是 held-out 泛化证据。该消融不改变 gate、物理、
任务或 held-out 划分。

第二轮 wrench 加权 DAgger（`model_wrench_dagger_v2`，seed `2026092711`，
checkpoint SHA256 `daf876c3647ece26e54ad78813d9106fa0d4c8e4c75386d8d704ae50cc21da47`）
把 `model_wrench_v1` 的六条闭环轨迹作为访问状态重新打标签。审计位于
`outputs/esn_joint_stiff_wrench_dagger2_eval_20260927/eval_v1/ESN_JOINT_AUDIT.json`，
得到 `task 6/6`、`strict 3/6`，没有超过 wrench1 的 `strict 4/6`，因此不把
它选为当前开发候选。当前最好的开发候选仍是 wrench1：四条严格通过，失败
集中在 shifted-plus 和 hard ball；尚未满足解封 held-out 的条件。

随后完成固定动作低通消融 `model_wrench_alpha05`：从 wrench1 checkpoint
复制，仅把 ESN action smoothing `alpha` 从 1.0 改为 0.5，checkpoint SHA256
`19e1b500e02565588b17906cd523ae451b7f15bd69f5cb25a98d11778185c8a7`。六条件
独立审计在 `outputs/esn_joint_stiff_alpha05_eval_20260927/eval_v1/`，结果为
`task 6/6`、`strict 4/6`。它降低了多数峰矩和峰速，但 shifted-plus 推杆接触
仍只有 `0.182 s`，hard 穿透升至 `0.208280 mm`；严格通过数没有超过 wrench1。
因此不选为主模型，也不把低通消融写成安全改进。

## 慢时间尺度 reservoir 消融（2026-09-27）

为直接检验“复杂扰动需要更长本体记忆”的假设，保持 128 单元、同一读出
预算和 wrench-norm 权重 3，仅将默认三组时间常数 `.08/.4/1.6 s` 同比例
放大为 2 倍，重训 `model_wrench_tau2_v1`。checkpoint SHA256 为
`86d0038fd9a267853038f0f56071c937ef18de75af038309fc20ebaa1407f498`，六条件
审计位于 `outputs/esn_joint_stiff_tau2_eval_20260927/eval_v1/`。

结果为 `task 3/6`、`strict 1/6`：shifted-plus 严格通过且接触 `2.519 s`，
但原始、rod-hold 和 hard 任务失败，hard 穿透 `0.207174 mm`。因此更长
reservoir 记忆没有带来跨条件泛化，不能替代当前 wrench1 候选；所有动作/状态
重放、物理指标和失败轨迹均已独立审计保存。

## 受约束读出负结果（2026-09-27）

为检验“ESN 读出动作变化率”是否是剩余失败原因，在 wrench1 数据上加入
固定 `delta_weight=1` 的相邻时刻 teacher-action 导数匹配损失；该项只使用
actor 可见的 48D 序列和 teacher action，不引入 gate、接触真值、事件时间或
阶段标签。模型 `model_wrench_delta_v3` 的 checkpoint SHA256 为
`81747530e59318dd67dbe9a481b4abea7d06819899eebec04b39ade995e20287`。

六条件审计位于 `outputs/esn_joint_stiff_delta_eval_20260927/eval_v1/`，结果
为 `task 4/6`、`strict 1/6`；原始和 rod-hold 条件任务失败，shifted-plus
推杆接触仅 `0.016 s`，hard 穿透 `0.208081 mm`。因此动作导数约束显著
退化，不再作为后续主线；这支持将研究重点转回 teacher/执行器接口和受扰动
本体状态覆盖，而不是继续堆叠同类读出正则。

## J2 action-unit 对齐 teacher 六条件复核（2026-09-27，已完成）

J2 的完整六条件队列因 wrapper 参数转发问题曾有两轮仿真前失败：
`j2full_aligned_*`、`j2full2_*` 和 `j2full3_*` 的 exit code 2 均保留在
公共 `results/`，没有物理积分，不能计入性能。修复了
`tools/run_office_joint_teacher_20260927.py` 的手工 argv 消费，并让
`tools/run_office_batch_20260927.py` 支持计划级 entrypoint；随后以单 worker、
1 CPU、虚拟内存上限 3 GiB 运行新的 `j2full4_*` 六条件。wrapper 现在把
`--teacher-config` 从冻结 evaluator 的 argv 中明确剥离，manifest 的 argv、
配置和 wrapper hash 已保存。

独立审计：
`J2FULL4_AUDIT.json` 和 `J2FULL4_RESULTS.md`（归档在
`outputs/esn_office_joint_teacher_j2_full4_20260927/`）。六回合各 1375 次
teacher action/状态重放、全部物理子步 RMSE、实际 generalized actuator torque、
末端线速度峰值和 MJB/source/config hash 均通过；结果为 `task 6/6`、`strict 3/6`：

| 条件 | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 外部穿透 mm | 推杆接触 s |
|---|---:|---:|---:|---:|---:|---:|
| original | 通过 | 156.797 | 38.828 | 0.143303 | 0.196223 | 0.797 |
| rod start7 | 通过 | 132.339 | 41.843 | 0.143303 | 0.196223 | 1.397 |
| rod start9 | 失败 | 135.017 | 42.444 | 0.143303 | 0.196223 | 0 |
| rod hold6 | 通过 | 157.844 | 38.828 | 0.143303 | 0.196223 | 0.850 |
| shifted plus | 失败 | 140.584 | 38.113 | 0.115232 | 0.176534 | 0.184 |
| hard ball | 失败 | 162.493 | 38.390 | 0.111476 | 0.207370 | 0.951 |

因此 J2 没有达到 stiff teacher 的开发集 `strict 4/6`，也没有改善 hard/shifted
失败机制；按预先冻结的预算规则，不用 J2 轨迹另训主 ESN，不把 action-unit
对齐宣布为 teacher 改进。J2 的完整原始轨迹、execution、失败原因、wrapper
和源文件 hash 仍保留，供后续共同执行接口研究使用。J3 stiff 补齐的四条结果
保持 `strict 2/4`，与 J1 原始/强球撞合并为 stiff `4/6`；J2/J3 均未解封
held-out，也不构成真实机器人证据。

## Wrench 权重 6 固定消融（2026-09-28，负结果）

为检验 wrench-norm 加权是否存在单调收益，在同一 48D/action7、128 单元
多时间尺度储备池、训练轨迹、验证条件和执行器预算下，将固定权重从 3 提高
到 6，seed 为 `2026092712`。输入仍只包含 canonical48D 的 actor-visible
`obs[39:45]` 估计负载；没有接触真值、球状态、事件时间、任务阶段或视觉。
checkpoint SHA256 为
`27fdd4fa1ce59cb2f2f5b0387e78ee38e92e4643d2ebc3298e8d9b80baecbaca`。

独立审计位于
`outputs/esn_office_joint_esn_stiff_wrench6_eval_20260927/eval_v1/ESN_JOINT_AUDIT.json`。
动作和储备池状态重放、物理时间加权 RMSE、实际 generalized actuator torque
和末端速度峰值均通过；闭环为 `task 6/6`、`strict 3/6`。hard 外部穿透
`0.207528 mm`，与 wrench1 的 `0.207610 mm` 接近且仍高于 0.2 mm，
没有安全改进；因此不采用权重 6，不解封 held-out，也不继续做无依据的同类
权重扫掠。

## 当前运行状态（2026-09-28 复核）

- J1、J2、J3 及 wrench6 闭环队列均已结束；本机没有遗留 MuJoCo、batch 或训练进程。
- Spark SSH 当前仍在 TCP 连接阶段被环境拒绝，未启动或重启任何远端作业；不能假设
  Spark 上有存活服务，既有 J2/J3 结果只以本地归档和审计为准。
- 当前开发集最佳仍为 `model_wrench_v1`：`task 6/6`、`strict 4/6`；J2 对齐
  teacher 与 wrench6 均为严格 3/6。三个 held-out 条件继续封存，最终目标尚未完成。
- 下一步优先级是共同执行接口/受扰动本体覆盖的可解释诊断；不再进行没有新因果
  假设的同类 wrench 权重或时间常数扫掠。

## Wrench1 reservoir 记忆因果消融（2026-09-28，已完成）

首轮 reset 队列在物理积分前被旧 evaluator 拒绝（它只接受旧的
`proprio48_office_vmc_memory_esn_v1` contract）；这些 `wrench1_memory_reset_*`
exit code 1 保留且不计性能。随后仅放宽兼容性检查，使同样是 stateful、48D 的
`proprio48_esn128_action7_v1` 进入 reset ablation；旧 45D policy 仍被拒绝。
物理世界、动作滤波、执行器预算、gate 和 checkpoint 均未改变。

新六条件审计见
`outputs/esn_office_joint_esn_stiff_wrench_memory_reset2_eval_20260927/eval_v1/ESN_JOINT_AUDIT.json`。
每个观测前清零 reservoir，仅保留当前本体输入和固定读出；动作/储备池状态
重放、物理时间加权 waypoint RMSE、实际 actuator torque、末端速度峰值和
hash 均通过。结果为 `task 3/6`、`strict 0/6`，而连续记忆的 wrench1 为
`task 6/6`、`strict 4/6`：

| 条件 | reset task | reset strict | RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| original | 失败 | 失败 | 150.622 | 39.743 | 0.143252 | 0.196420 | 1.049 |
| rod start7 | 通过 | 失败 | 153.401 | 37.514 | 0.143252 | 0.196420 | 1.785 |
| rod start9 | 通过 | 失败 | 150.976 | 40.188 | 0.143252 | 0.196420 | 0.644 |
| rod hold6 | 失败 | 失败 | 129.103 | 41.397 | 0.143252 | 0.196420 | 1.313 |
| shifted plus | 失败 | 失败 | 149.005 | 42.079 | 0.115053 | 0.176065 | 0 |
| hard ball | 通过 | 失败 | 163.815 | 42.385 | 0.129101 | 0.207205 | 0.566 |

这是一项固定 checkpoint 的推理消融，不是重新训练的 feed-forward baseline；它
支持“储备池历史是当前跨条件 task 完成能力的必要因素”这一可解释结论，但不
解决 hard 首撞或接触曝光门槛，也不构成 held-out/硬件成功。后续不再把无记忆
策略作为主线。

## canonical48D 字段来源审计与 sensors-only 匹配预算消融（2026-09-28）

为避免把“无外部感知”误写成“只含原始传感器”，先对当前最佳 wrench1 的一条
完整 hard 轨迹做了只读字段来源审计：
`outputs/esn_office_input_provenance_audit_20260928/INPUT_PROVENANCE_AUDIT.json`。
审计确认 actor 没有接触真值、球状态、事件时间、阶段标签、视觉或距离输入；但
canonical48D 中 `command/error/path_direction` 共 15 维依赖 WBC/任务参考，不能
直接称作“sensor-only”。q/dq 是直接关节本体量，load/wrench 是编码器/动力学
观测器估计，参考派生量则是本体状态与任务参考的组合。

随后按预先登记的匹配预算做了一个因果字段消融：保持 stiff teacher 数据、DAgger2
访问轨迹、128 单元多时间尺度 reservoir、wrench-norm 权重 3、action7、执行器
限制、物理子步和六个开发条件完全不变，只将 command/error/path_direction 置零
并重新训练；checkpoint SHA256 为
`f75ea7cd927fe51623c77d9698e851b1c924b27875eea5fb65b954c2b41a34c2`。计划、训练
manifest 和完整原始轨迹归档于
`outputs/esn_office_joint_esn_stiff_sensors_only_eval2_20260928/`；独立审计为
`ESN_JOINT_AUDIT.json`。

| 条件 | task | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 外部穿透 mm | 推杆接触 s |
|---|---:|---:|---:|---:|---:|---:|---:|
| original | 通过 | 通过 | 154.892 | 36.341 | 0.143396 | 0.196369 | 0.854 |
| rod-start7 | 通过 | 通过 | 132.956 | 38.795 | 0.143396 | 0.196369 | 1.104 |
| rod-start9 | 通过 | 失败 | 157.911 | 39.774 | 0.143396 | 0.196369 | 0 |
| rod-hold6 | 通过 | 通过 | 156.227 | 36.341 | 0.143396 | 0.196369 | 0.937 |
| shifted-plus | 通过 | 失败 | 134.734 | 36.132 | 0.115289 | 0.176450 | 0.129 |
| hard-ball | 通过 | 失败 | 163.189 | 35.706 | 0.117556 | 0.207805 | 1.262 |

该 mask 模型为 task `6/6`、strict `3/6`，低于 full48 wrench1 的 task `6/6`、
strict `4/6`；hard 穿透也略升至 `0.207805 mm`，shifted-plus 推杆曝光降至
`0.129 s`。固定 checkpoint 的动作/储备池重放、物理时间加权 RMSE、实际
generalized actuator torque 和末端峰速均通过。结论是：在当前数据和预算下，
WBC/任务参考派生字段对闭环性能有可测贡献；它不是外部感知，但论文应明确
“纯本体接口 + 内部参考”与“只含传感器字段”两种说法的区别。该消融不改变
gate、held-out 封存或任何失败回合，也不能据此声称 full48 ESN 已安全泛化。

首次 batch wrapper 因同名原始回合目录已存在而退出的条目保留在
`results/sensors_only_original/`；随后按相同配置直接完成并独立归档的六回合是
`sensors_only2_*`，失败 wrapper 不计入性能。

## wrench1 请求—共同过滤—物理执行链审计（2026-09-28）

为明确“teacher/ESN 请求”不能等同“实际执行量”，对 wrench1 六条已完成轨迹做了
只读重放，归档于
`outputs/esn_office_action_execution_chain_v2_20260928/ACTION_EXECUTION_CHAIN_AUDIT.json`。
保存的 `esn_action` 与 evaluator 提交给共同执行接口的 `applied_action` 逐元素完全
一致；随后按 office 固定 `maximum_linear_yield_mps=.32`、原角速度及变化率限制
重放 `VelocityResidualActionFilter`，最后从物理子步独立读取 generalized actuator
torque 和末端速度。接触真值仅用于离线分层，没有进入 actor 或新 rollout。

六回合 action 幅值饱和率均为 0；完整 55 s 回合的 slew-limited 决策占比仅
`0.1%–0.4%`。shifted-plus 的推杆接触分层中，过滤后 yield 与请求值 RMSE 为 0，
但 raw action 峰值仅约 `0.040`；因此该回合曝光不足更指向访问状态/读出响应偏弱，
而不是共同接口削弱了一个强 ESN 请求。每条球撞轨迹中，碰撞后首个 25 Hz 决策
区间都受变化率限制，但首次亚毫秒冲击在该观测之前已完成；不能据此把调大 slew
作为 hard 首峰修复。物理峰矩为 `35.672–40.044 Nm`、末端峰速为
`0.109680–0.143267 m/s`，均从子步数据独立复算，不能与 action7 混称。

该审计把下一条有信息增益的路线收窄为 shifted-plus 受扰动状态覆盖/teacher 响应，
而非改共同变化率限制；hard 首峰仍是观测带宽之前的物理边界。没有因此启动新
teacher 候选或解封 held-out。

## 延迟球撞展示片段（2026-09-28）

为改善动图开场观感，新增了一个独立的展示场景：球在 `t=2.0 s` 发射，发射前
保持 reset 位姿，首次接触约 `2.08125 s`。片段使用当前 wrench1 checkpoint，时长
8 s，归档于 `outputs/esn_office_delayed_ball_demo_20260928_v2/`，视频和 GIF 均有
媒体/源文件哈希。

这不是正式六条件评估：片段在 lift 阶段结束，`task_success=false` 只反映展示
提前结束；不计入 task/strict、baseline 或 held-out 结果。正式评估仍使用默认
`ball_launch_time_s=0`，安全门、扰动和条件封存没有改变。

## 延迟球新场景 ESN 重设计（2026-09-28，已完成首轮闭环）

为改善展示和研究“球在进入场景约 2 s 后才撞击”的开发场景，新增固定
`ball_launch_time_s=2.0` 的 teacher protocol。它是开发条件，不能替换原始
`t=0` hard-ball，也没有把发射时间、事件时钟、球状态或阶段标签送入 actor。
配置、四条真实闭环 teacher 轨迹、原始请求/共同接口 action、内部状态、物理
子步数据和 source/config/hash 归档于
`outputs/esn_office_joint_teacher_delayed2_20260928/`；独立审计为
`DELAYED2_AUDIT.json`。teacher 的四回合结果：

| 条件 | task | strict | 外部穿透 mm | 推杆接触 s |
|---|---:|---:|---:|---:|
| delayed nominal | 通过 | 通过 | 0.164478 | 0.855 |
| delayed rod-start9 | 通过 | 失败 | 0.164478 | 0.306 |
| delayed shifted-plus | 通过 | 失败 | 0.125916 | 0.072 |
| delayed hard-ball | 通过 | 通过 | 0.194522 | 0.404 |

在固定 128 单元和 action7/canonical48D 预算下，ESN 结构重设计为四时间尺度
leaky reservoir（32 单元各，tau=`0.04/0.16/0.64/2.56 s`），训练数据混合
四条原始 stiff-VMC 轨迹中的 nominal/hard/rod7/hold6 与两条 delayed
nominal/hard 实际 teacher 轨迹；wrench-norm 权重固定 3，seed `2026092814`。
训练脚本新增 `--tau-layout medium4`，未改变默认三尺度布局。checkpoint：
`outputs/esn_office_joint_esn_delayed2_20260928/model_medium4_v1/best.npz`，
SHA256 `9739b6644b7bcbc2f7c8e5bee87342482f5ee00c3f543b32604f4fbe7315b5cc`，
离线验证 action MSE `1.5206635907816235e-05`。训练峰值常驻内存约 856 MB，
单线程完成；没有并发启动其他仿真。

四个 delayed 闭环和六个原始 `t=0` 回放均完成独立动作/储备池/物理子步审计：

| 评估 | task | strict | 备注 |
|---|---:|---:|---|
| delayed medium4（4 条） | 4/4 | 2/4 | nominal、hard strict；rod9/shift-plus 曝光不足 |
| t=0 medium4（6 条） | 6/6 | 3/6 | original、rod7、hold6 strict；rod9/shift-plus 曝光不足，hard 穿透 0.208138 mm |

详细审计分别为
`outputs/esn_office_joint_esn_delayed2_20260928/eval_delayed2_medium4/ESN_JOINT_AUDIT.json`
和 `outputs/esn_office_joint_esn_delayed2_20260928/eval_t0_medium4/ESN_JOINT_AUDIT.json`。
两套审计的 action replay、reservoir replay、三项物理子步指标、实际
generalized actuator torque 和模型/计划 hash 均通过。delayed hard ESN 的外部
穿透为 `0.198201 mm`，在原门槛内；这只是 delayed 开发条件证据，不是 held-out
或硬件结果。

### 当前状态（2026-09-28）

- 已完成：延迟 teacher 四回合、medium4 ESN 训练、delayed 四回合闭环、原始
  t=0 六回合交叉回放和独立审计；当前没有运行中的本机作业。
- 当前可汇报结论：延迟场景重新训练的 medium4 ESN 能完成 delayed nominal/hard
  并保留原始 task 6/6，但 strict 仅 delayed 2/4、原始 3/6；它没有消除
  rod-start9/shift-plus 接触曝光失败，也没有解决原始 hard 的 0.2 mm 门槛。
  因而仍不能解封 held-out、替换 `wrench1` 正式开发候选或声称真实环境成功。
- 尚未完成：在不改变输入和 gate 的前提下，针对推杆时序曝光和原始 hard 首撞
  的 teacher/本体状态覆盖仍需新因果实验；正式 held-out 三布局继续封存。

## 保守推杆时序与 teacher 候选筛查（2026-09-28）

针对“推杆时序是鲁棒性关键指标”的要求，新增固定 `rod_hold=6 s` 的保守开发
协议，分别测试 delayed `rod_start=7 s` 与 `rod_start=9 s`。medium4 ESN 在
两条回合均 `task=true, strict=true`，外部穿透均 `0.168514 mm`，推杆接触时长
分别为 `1.674 s` 与 `0.701 s`。这两条结果和 delayed nominal/hard 合并为
保守开发窗口的 `4/4 task、4/4 strict`；审计原始目录为
`results/delayed2_medium4_rod7_hold6` 与 `results/delayed2_medium4_rod9_hold6`，
动作/储备池和物理子步重放沿用同一 checkpoint 与不变 gate。

同时完成两个预注册 teacher 候选的四条件筛查，均不采用：

| 候选 | delayed strict | hard 外部穿透 | 结论 |
|---|---:|---:|---|
| action scale 0.75 | nominal 1/1，其余失败 | 0.206873 mm | 放大动作仍未解决短推杆时序，且超过 0.2 mm |
| filter tau 0.02 s | nominal 1/1，其余失败 | 0.221086 mm | 加快 wrench 滤波仍未解决短推杆时序，安全退化 |

候选的原始轨迹、请求 action、实际执行量、失败回合和配置均保留在
`results/gain075_*`、`results/fastfilter_*`，不据单回合挑选模型。当前保守结论是：
medium4 ESN 对“晚出现但保持足够久”的推杆时序具有开发集稳健性；短 hold 的
rod9/shift-plus 仍作为接触窗口不足的诊断失败保留，不能被重命名为成功。原始
t=0 hard 仍只作冻结参照，正式门槛未改。

## 展示冲击与角落放置后续（2026-09-28）

- 已完成冲击慢动作渲染：完整 55 s 保守 delayed rollout 仍 task/strict=true，
  冲击峰值接触力 2071.20 N，最大外部穿透 0.188555 mm。普通视频和独立
  4 倍慢动作分别为
  `outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout.mp4` 与
  `outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout_impact_slowmo.mp4`；
  慢动作只重采样物理子步状态，不进入 actor、不改变动作或 gate。
- 已实现开发开关 `--interaction-demo`、`--corner-placement`：杯子/柱子先过
  初始无重叠审计，角落支撑改为显式 `office_v5_corner_top` 接触；正式默认
  场景、t=0 条件和门槛不变。
- 进行中/未完成：开发 interaction 场景能产生真实柱子接触（首次约 0.296 s），
  但当前 teacher/ESN 都会在 carry 阶段被路线接触阻挡；杯子接触尚未达到可
  汇报的柔顺蹭过窗口。corner-placement 的顶面、目标元数据和支撑审计已保存，
  30 s teacher probe 仍未完成放置，失败审计为
  `outputs/vmc_corner_nominal_dev11_20260928/rollout.json`。下一轮优先修正
  角落 approach/推杆 rail 的几何路线，再蒸馏 ESN；不把该失败改写成成功。

## 2026-09-28 交互展示与厚桌角复核

本轮复核发现 interaction-demo 的旧杯子位置 `[.540,-.255]` 与待抓物块手柄
发生 `13.5 mm` 初始重叠，审计拒绝；该失败保留在
`outputs/vmc_interaction_cup_path2_20260928`。interaction 开关现固定为
`cup_xy=[.520,-.330+0.018*variant]`，普通 corner-only 位置不变；当前源文件
SHA256 为 `dc77a7d2cb738a53dcfd0bfac0d91e1827b7b8ad6f5006722c93005053e09791`。

展示步长 `dt=1e-4` 仅用于开发交互可视化，正式安全评估仍保持 `5e-5`。teacher
角落交互探测 `outputs/vmc_interaction_corner_cup_path5_dt1e4_20260928/rollout.json`
出现真实杯子接触 `0.278 s / 56.6 N`，杯子位移 `1.879 mm`、倾角 `0.267 deg`；
但在 carry 阶段未完成角落释放，且全局地面球穿透 `0.349 mm`，不计 task/strict。
同一 medium4 ESN（checkpoint SHA256
`9739b6644b7bcbc2f7c8e5bee87342482f5ee00c3f543b32604f4fbe7315b5cc`）的回放
`outputs/esn_interaction_corner_cup_path5_dt1e4_20260928/rollout.json` 出现杯子
接触累计 `3.436 s / 60.0 N`，位移 `1.112 mm`、倾角 `0.737 deg`；同样停在
carry，不能声称“复杂障碍+角落放置”已完成。完整 ESN 交互动图在该目录的
`rollout.gif` 和 `rollout.mp4`。

柱子真实接触的历史回合 `outputs/esn_office_corner_interaction_dev2_20260928` 也
已从原始 `rollout.mjb`/`rollout.npz` 只读重放为
`rollout_pillar_interaction.gif`/`.mp4`；片段标注接触窗口 `12.70–17.67 s`，不
改变原回合或把 carry 阻挡失败改写为成功。

更靠近路线的候选
`outputs/esn_interaction_corner_cup_path7_dt1e4_20260928/rollout.json` 被保留为
失败：align 阶段持续顶住杯子，峰值 `1618.7 N`、位移 `11.1 mm`。它虽未超过
外部穿透门槛，却不是柔顺蹭过，代码已回退到前述低力交互几何。

corner-only 的 `outputs/esn_corner_blend05_targeted3_20260928` 仍保持
`task/strict/release=true`、最大外部穿透 `0.001854 mm`，作为厚桌角最终放置的
可汇报结果；interaction-demo 只展示真实障碍接触，不替代 corner 放置结果。

球撞击展示新增只读标注版
`outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout_impact_slowmo_annotated.gif`
及同名 MP4，在原慢动作帧上叠加末端位移三轴轨迹和峰值 `0.058 m/s`。它不改变
轨迹、actor 输入、动作或 gate；约 `5.8 mm` 的冲击后末端响应因此可在全景画面
中直接观察。

### 本轮状态

- 已完成：杯子初始重叠修复；teacher/ESN 低力杯子接触复核；完整 ESN 交互动图；
  球撞击末端响应显示增强；corner-only 成功模型与动图保持有效。
- 运行中：无本机或 Spark 仿真作业；没有启动新的远端作业。
- 尚未完成：同一回合同时满足“杯子/柱子柔顺交互 + 角落最终放置 + 正式
  `dt=5e-5` 安全门”的跨条件 ESN 结果。当前不调整 gate、不解封 held-out，
  也不把展示步长结果写成正式安全通过。

## 2026-09-28 resumed combined-scene geometry diagnosis

After the interrupted run, no local or Spark simulation process was active. The
trial42 audit was rechecked before launching new work: worst external geometry
`69` is the FR3 `right_finger`, while the development fixture geometry is
`office_v5_cup_contact_handle`; the pillar was not the source of the reported
`0.2970 mm` penetration.

Three registered development probes were retained with the unchanged medium4
checkpoint (`9739b6644b7bcbc2f7c8e5bee87342482f5ee00c3f543b32604f4fbe7315b5cc`):

| probe | fixture change | task/strict | ext. penetration | cup shift | contact evidence | conclusion |
|---|---|---:|---:|---:|---|---|
| trial43, 8 s | handle endpoint `.075/.135` | n/a | `0.1860 mm` | negligible | no cup/pillar window before horizon | retained short probe |
| trial44, 30 s | same handle; v2 pillar | fail/fail | `0.1860 mm` | `16.40 mm` | cup `1.519 s`, `8.88 N`; no pillar | handle no longer causes finger penetration, but cup route is not compliant |
| trial45, 30 s | handle endpoint `.060/.125`, lower friction | fail/fail | `0.1860 mm` | `8.66 mm` | no cup/pillar window; stopped `load_transfer` | contact coverage is lost; rejected |
| trial46, 30 s | restore trial44 handle; pillar `y=-.330` (v3) | fail/fail | `0.1860 mm` | `16.40 mm` | cup `1.519 s`, `8.88 N`; no pillar | moving the pillar into the retreat corridor does not create a force-bearing window |

All three are `dt=1e-4` development probes and are not formal safety results.
Trial44/46 have peak generalized actuator torque `51.75 Nm`, peak linear speed
`0.07145 m/s`, and 3-D position RMSE `0.05882 m`; they are retained as failures,
not filtered from the comparison. Trial43's source hash was
`79b236ce72f93e488d83c6c664c8ab7e3553e2563577d5dc4cc182d846a94d58`, trial45's
was `b8e3f7f0ff126326bd37c629ae95de33fab8635a5b0bbc42c36eb9974ed97f3b`, and
the current combined-v3 source is
`41fb7d1398f47504577df00f8e3169d5fb45021e3da4eed52ff3b3d075262985`.
The frozen actor input, action7 contract, actuator amplitude/slew limits,
external-penetration gate, and formal `dt=5e-5` protocol were not changed.

Current scientific status remains: corner-only medium4 ESN is valid separately
(`outputs/esn_corner_blend05_targeted3_20260928`), and delayed-ball/rod timing
development evidence remains valid, but one combined office-v5 episode with
cup brush, pillar brush, and corner placement has not been achieved. The next
useful experiment must alter the registered retreat-route geometry or the
teacher route with an explicit pre-registered hypothesis; repeating cup-handle
length or pillar-y candidates is not informative.

## 2026-09-28 trajectory-supported pillar candidate

Trial47 registered the first geometry chosen from the measured trial46 hand path:
combined-v4 placed the raised pillar at `[.585,-.300]` while restoring the
trial44 handle. It did create a real pillar window (`14.0556--29.9999 s`,
`6.8007 s`, peak `116.81 N`), but the pillar blocked the carry route before
release. The retained result is task/strict false, `physical_valid=false`, final
stage `carry`, no cup contact, cup shift `2.01 mm`, external penetration
`0.22898 mm` (worst pair `office_v5_pillar` vs `fr3_link7_collision`), peak
torque `47.49 Nm`, peak speed `0.07475 m/s`, and 3-D RMSE `0.07070 m`.

This is an informative negative result: a pillar placed in the measured hand
corridor is not a valid combined fixture because it is encountered before
placement. The pillar must instead be reachable after release through a
registered teacher/task route; changing its position alone is insufficient.
Raw trial47 data are retained at
`outputs/esn_combined_contactv4_handle45_trial47_probe30s_dt1e4_20260928/`.
The source hash is `469b827e3b4a6d43b4d368f303894a321db9e5cf0c549cf49cb018cef910a808`;
all actor, gate, actuator and formal-step constraints remain frozen.

## 2026-09-28 resumable overnight campaign

Added `tools/overnight_esn_combined_campaign_20260928.py`, a lock-protected,
single-worker runner with a 3 GiB address-space limit, one BLAS/MuJoCo thread,
execution manifests, raw rollout preservation, source/checkpoint hashes, and
failure summaries. It disables EGL rendering during physics because the renderer
is not reliable under this memory limit; media is a separate read-only step. A
Codex heartbeat named `overnight-esn-combined-campaign` resumes unfinished work
without duplicating an evaluator process.

The first complete run is archived in
`outputs/overnight_esn_combined_campaign_20260928/`: current-source combined-v4
development failed (`0.26623 mm` penetration; pillar `37.485 s / 125.16 N`; carry
blocked); the current-source corner-only reference stopped at load transfer
(`0.001843 mm` penetration), so the older targeted3 success is not reproducible
under the current source; and the delayed-ball formal reference passed unchanged
gates (`0.18855 mm`, `37.76 Nm`, `0.14243 m/s`, RMSE `0.00889 m`). The campaign
did not launch a formal combined rerun after the development candidate failed.

## 2026-09-28 resumable overnight campaign

Added `tools/overnight_esn_combined_campaign_20260928.py`, a lock-protected,
single-worker runner with a 3 GiB address-space limit, one BLAS/MuJoCo thread,
execution manifests, raw rollout preservation, source/checkpoint hashes, and
failure summaries. It does not enable rendering during physics because EGL
shadow-framebuffer creation is not reliable under the memory limit; rendering is
kept as a separate read-only media step. A Codex heartbeat named
`overnight-esn-combined-campaign` is active to resume the runner without
duplicating an evaluator process.

The first complete run is archived in
`outputs/overnight_esn_combined_campaign_20260928/`:

| case | task/strict | external penetration | key result |
|---|---:|---:|---|
| combined-v4 development, current source | fail/fail | `0.26623 mm` | pillar `37.485 s / 125.16 N`, carry blocked, no placement |
| corner-only formal reference, current source | fail/fail | `0.001843 mm` | stopped at `load_transfer`; old targeted3 success is not reproducible under current source |
| delayed-ball formal reference | pass/pass | `0.18855 mm` | task complete; torque `37.76 Nm`, speed `0.14243 m/s`, RMSE `0.00889 m` |

The delayed-ball pass is a formal unchanged-gate reference condition, not the
combined cup/pillar/corner claim. The campaign intentionally did not launch a
formal combined rerun after the development candidate failed. Existing media
from earlier archived trajectories remain labelled by their original source and
condition; no stale GIF is promoted as current-source combined success.

## 2026-09-28 heartbeat resume check

The resumable campaign was invoked again at `2026-09-28 22:40 +0800`. Its lock,
existing-result checks, source hashes, and checkpoint hashes completed without
starting a duplicate evaluator; all registered cases already have preserved
`execution.json` and raw rollout files. No new physics result was fabricated or
relabelled. There is currently no active local office evaluator process.

### 2026-09-28 overnight campaign idempotent resume (23:40 +0800)

The runner was invoked again with the recorded `.venv-rl/bin/python` after a
process and lock check. No evaluator was running; existing rollout files and
`execution.json` manifests were preserved without duplicate simulation. The
combined-v4 development candidate remains task/strict false, final stage
`carry`, with pillar contact `37.4848 s / 125.16 N` and external penetration
`0.26623 mm`; its formal `dt=5e-5` rerun therefore remains skipped. The
delayed-ball formal reference remains an unchanged-gate task/strict pass at
`0.18855 mm`; the current-source corner-only reference remains a failure at
`load_transfer`. Source/checkpoint hashes and all frozen contracts are
unchanged; failed rollouts remain retained.

### 2026-09-29 overnight heartbeat resume (00:43 +0800)

The required process check found no active evaluator or campaign. The recorded
`.venv-rl/bin/python` runner completed an idempotent resume at 00:43; all
existing `execution.json` and raw rollout files were reused, with no duplicate
physics integration. Source and checkpoint hashes remained unchanged. Combined-v4
development is still task/strict false (`carry`, `0.26623 mm` penetration), so
the formal `dt=5e-5` combined case remains skipped. The delayed-ball formal
reference remains the current-source unchanged-gate pass (`0.18855 mm`); all
failures remain archived.

### 2026-09-29 overnight heartbeat resume (02:40 +0800)

No evaluator or campaign process was active at the preflight check. The bounded
runner reused its existing lock, manifests, and raw rollouts; no duplicate
physics integration occurred. Hashes are unchanged. Combined-v4 remains
task/strict false at development resolution (`0.26623 mm` penetration), so the
formal `dt=5e-5` combined run remains locked out. Delayed-ball remains the
current-source formal unchanged-gate pass at `0.18855 mm`.

### 2026-09-29 overnight heartbeat resume (01:38 +0800)

Process and lock checks found no active evaluator. The bounded runner reused all
existing manifests and raw rollouts; no duplicate physics run was started.
Source/checkpoint hashes are unchanged. Combined-v4 remains development
task/strict false with `0.26623 mm` penetration, so formal `dt=5e-5` remains
skipped. Delayed-ball remains the current-source unchanged-gate formal pass at
`0.18855 mm`; failed episodes remain retained.

## 2026-09-29 relaxed-pillar diagnostic

At the user's request, only the pillar was relaxed in a separate development
condition. The ESN, ball/person/rod disturbances, cup/corner geometry, actor
inputs, gates and actuator limits were unchanged. The smaller, lower-friction
pillar reduced external penetration from combined-v4's `0.26623 mm` to
`0.117404 mm`; cup contact was `0.8807 s / 7.279 N`, cup shift/tilt were
`9.839 mm / 0.849 deg`, peak torque `48.813 Nm`, and peak speed `0.068410 m/s`.
The run still ended in `load_transfer` with task/strict false and no pillar
contact, so it is not a complete combined success. An intermediate placement
did create pillar contact (`1.739 s / 60.82 N`) but penetrated `0.5255 mm` and
was rejected. Full details are in
`docs/ESN_RELAXED_PILLAR_DIAGNOSTIC_20260929.md`.

## 2026-09-29 algorithm-only ESN screen

The combined-v4 fixture and all evaluation/gate/actuator conditions were frozen;
only ESN inference was changed. The preregistered 50% and 75% ESN/VMC blends,
pure ESN, and an ESN shadow run all completed their 30 s development rollouts
and remain task/strict false at final stage `carry`. The pure ESN achieved
`0.12913 mm` external penetration and `35.79 Nm` peak torque but left a nearly
constant carry residual and did not rebound the ball. The 50% blend reduced RMSE
to `0.08369 m` but reached `0.19068 mm` penetration and sustained pillar
contact; 75% reached `0.09404 m` RMSE with `0.11268 mm` penetration but had only
`0.226 s` pillar contact. The shadow run (zero applied ESN residual) also
stopped at carry with `16.272 s` pillar contact, establishing that the frozen
WBC route itself is blocked under this fixture.

Two algorithm-only variants were then added: a causal load gate and a
quiet-state centered readout. Both use only canonical48D joint-load and
estimated-wrench fields, with thresholds calibrated from six saved teacher
traces (balanced activity classification accuracy `0.93450`); no contact truth,
ball state, event time, stage, visual/range, or geometry enters the actor.
The load-gated `tau_release=.64 s` rollout gave the best RMSE in this screen
(`0.07212 m`, `0.17152 mm` external penetration, `37.78 Nm`) but still had
`11.071 s` pillar contact and no placement. Quiet-centering at `0.64 s` and
`2.56 s` remained carry failures with `0.12190/0.16054 mm` penetration.

Full table, source/checkpoint lineage, raw rollout paths, and failure causes are
in `docs/ESN_ALGORITHM_ONLY_SCREEN_20260929.md` and
`outputs/esn_combined_v4_algorithm_screen_20260929/`. The new inference classes
are in `scripts/current_student_policy_20260921.py`, with construction script
`tools/make_esn_load_gated_variant_20260929.py` and unit tests
`tests/test_esn_load_gated_20260929.py`. No formal `dt=5e-5` rerun was unlocked:
none of the unchanged development candidates passed task and strict gates.

### 2026-09-29 pure-ESN continuation

The deployment contract is now explicitly pure ESN for this branch: every new
closed-loop evaluation used `--hybrid-vmc-blend 0`; no environment, gate,
actor-visible field, actuator bound or test condition was changed. The impact
response generator import-path defect was fixed and its unit test passes. Its
shared-reservoir dual-readout candidate reached carry with `0.15216 mm`
external penetration, `0.06220 m` RMSE, `46.40 Nm` peak torque and
`0.07473 m/s` peak speed, but cup placement and ball rebound both failed.
An impact-head gain 1.5 variant improved RMSE to `0.06089 m` and retained
`0.16931 mm` penetration, but still failed placement/rebound. Conservative,
channel-scaled and gain-2 variants were retained as negative controls; they
either destabilized the route or exceeded physical validity.

The current-source VMC teacher was run once under the same frozen fixture as a
diagnostic. It also failed (`carry`, no rebound, `0.27809 mm` penetration), so
the student failure is not evidence that a pure ESN merely copied an otherwise
successful teacher. A fixed-reservoir ridge readout and a low-memory NumPy MLP
readout were then trained from retained same-fixture applied-action traces and
deployed as pure ESNs. The MLP reached `carry`, `0.19572 mm` penetration,
`0.06653 m` RMSE, `44.27 Nm`, `0.10602 m/s`, with cup validity true but no
rebound or placement. The ridge candidate was physically invalid at
`0.24366 mm` and also failed task completion. All attempted rollouts and
malformed/aborted attempts remain preserved with sidecars and hashes.

This round adds useful negative evidence but no reportable combined success;
formal `dt=5e-5` remains locked because no unchanged development candidate
passed both task and strict gates. Continue only with a pre-registered causal
readout/trajectory hypothesis; do not reinterpret the offline hybrid trace
source as a hybrid ESN result or select away failures.
Independent replay of the best impact-gain and NumPy-MLP actions reproduced all
750 saved policy samples per rollout exactly (maximum absolute difference zero).

### 2026-09-29 matched-budget ESN screen

This screen changed only ESN learning data/mechanism. The office-v5 world, MuJoCo
parameters, task and strict gates, canonical48D actor input, action7 interface, and
actuator amplitude/slew limits stayed frozen. The matched MLP is `48-128-128-7`; the
ESN uses a 128-unit multi-timescale reservoir and 128-unit nonlinear readout. Thus both
have 256 hidden/state units under the explicit equal-neuron accounting used here. Both
exclude contact truth, ball state,
event/stage, visual and distance fields.

DAgger3 used actual exposure-balanced ESN closed-loop visits, relabeled by the same
stiff-VMC teacher from the estimated proprioceptive wrench only (wrench weight 3,
seed 2026092932). Its checkpoint SHA256 is
`a1af76a0f9b3471717009f5c49e56194da2624f3807cba3092796a8b31c1e1c5`. Independent
action/reservoir replay and physical substep recomputation passed; six development
conditions were task `6/6`, strict `4/6`.

DAgger4 was a pre-registered failure-focused follow-up: only rod-start9 and
shift-plus DAgger3 visits were added, each repeated three times, with the same
teacher, input, reservoir and budget. Its checkpoint SHA256 is
`6b0c01b0b865e61e7b5c8bd98bb8e7f45fe1381e20482f4a941f955d2c918d7b`. Replay and
physical audits passed, but the closed loop regressed to task `5/6`, strict `3/6`;
rod-start9 task failed and hard penetration was `0.208001 mm`. DAgger4 is retained
as a negative result and does not replace DAgger3. Raw rollouts, plans, hashes and
audit are under `outputs/esn_office_joint_esn_stiff_20260929/dagger4_eval/`.

The matched MLP128 remains task `5/6`, strict `3/6`, so DAgger3 has a reproducible
`+1` task and `+1` strict advantage on this fixed development screen. These are all
`dt=1e-4` development results; no formal `dt=5e-5`, held-out, or hardware claim is
authorized because six-condition strict is not complete.

### 2026-09-29 teacher-response probes and follow-up ESN screens

The remaining strict failures were diagnosed from the unchanged gate: rod contact
duration was only `0.2771 s` for DAgger3 rod-start9 and `0.1206 s` for shift-plus,
below the fixed `0.4 s` hand/rod exposure requirement. The stiff teacher itself had
the same limitation (`0.2886 s` and `0.1431 s`), so this is a teacher-response/data
problem rather than an action replay or physics-audit problem.

Two fixed teacher-only probes were retained. Scaling the stiff teacher to `0.4` gave
rod durations `0 s` and `0.1363 s`; scaling to `0.6` gave `0.0185 s` and `0.1253 s`.
Neither was used for ESN training. The existing damped candidate (half action plus
damping x2) improved rod-start9 to `0.7930 s` and passed task/strict with penetration
`0.196223 mm`, `39.44 Nm` peak torque and `0.14330 m/s` peak speed. It improved
shift-plus only to `0.2383 s`, so shift-plus still failed strict. These teacher traces
are archived under `outputs/esn_office_joint_esn_stiff_20260929/teacher_probes_20260929/`.

Three ESN follow-ups then tested how to transfer that teacher response while retaining
the equal 256 hidden/state-unit budget and canonical48D input:

| candidate | data change | task | strict | conclusion |
|---|---|---:|---:|---|
| DAgger5 | DAgger3 six actual visits, balanced once each | 6/6 | 3/6 | no strict gain |
| DAgger6 | add damped teacher rod9/shift raw traces | 5/6 | 3/6 | rod9 task regressed |
| DAgger7 | relabel DAgger3 visits with damped teacher | 6/6 | 3/6 | labels did not transfer exposure |

All three had independent action/reservoir replay max error `0` and physical-substep
recomputation passed. DAgger3 remains selected at task `6/6`, strict `4/6`; DAgger5,
6 and 7 are retained as negative or non-superior screens with plans, hashes and raw
rollouts in `outputs/esn_office_joint_esn_stiff_20260929/`. No gate, environment,
actor field or actuator limit was modified, and no formal `dt=5e-5` run is unlocked.

## 2026-09-29 dual64 纯 ESN 结构复核

在固定环境、gate、canonical48D/action7、执行器限制和 256 hidden/state-unit
预算下完成了 dual-readout ESN：共享 128 单元 reservoir，route 和 recovery 各
64 单元；选择量是纯本体 `||qvel_t-qvel_{t-1}||`，不含接触真值、球状态、
事件/阶段、视觉或距离。训练脚本已修复为使用已审计的 DAgger3 原始 rollout
和 damped-teacher probe 路径，所有 trace SHA、teacher 配置和 checkpoint hash
写入 sidecar。checkpoint 为
`outputs/esn_office_joint_esn_dual64_20260929/model_dual64_v1/best.npz`，SHA256
`ab9059fa35b11535939a1b4bd85f8d8861b46fce643371211ee7446565a42d3d`。

六个 unchanged development 条件的独立动作/储备池回放与三项物理子步指标审计均
通过；结果为 task `6/6`、strict `3/6`。rod-start9 和 shifted-plus 仍未达到
固定接触门槛，hard 外部穿透 `0.207867 mm`。相对于当前 DAgger3 的 strict
`4/6` 没有改进，因此 dual64 只作为负结果保留，不替换主候选，也不解封
combined-v4 held-out 或 formal `dt=5e-5`。审计文件位于
`outputs/esn_office_joint_esn_dual64_20260929/dual64_audit/`，计划位于
`configs/esn_joint_stiff_dual64_eval_20260929.json`。

同日又完成一次固定的 damped-label impact-response 读出实验：route 使用 DAgger3，
impact head 使用 DAgger7，仍是共享 128 reservoir、128 readout、256 总预算，
并用纯本体 qvel 瞬态作因果 selector。checkpoint SHA256 为
`b936be8b95fde31e0049606f9ce83321b3191b3dce8e6e71aebed23d6e64b826`。六条件审计
结果为 task `6/6`、strict `3/6`；rod-start9、shifted-plus 仍失败，hard 穿透
`0.207172 mm`。动作/储备池回放与物理子步复算均通过。该分支低于 DAgger3 的
strict `4/6`，不进入 combined-v4 或 formal `dt=5e-5`。

## 2026-09-29 DAgger3 综合场景迁移

为避免把六条件开发优势误当成最终场景成功，直接将当前主候选 DAgger3
（checkpoint SHA256 `a1af76a0f9b3471717009f5c49e56194da2624f3807cba3092796a8b31c1e1c5`）
放入冻结的 `combined-contact-v2 + corner-placement` 综合场景。使用纯 ESN
`hybrid_vmc_blend=0`、原 gate、原 action7/canonical48D 和开发 `dt=1e-4`，未改
环境或 actor 输入。结果为 task/strict `false/false`，最终阶段 `carry`。

独立动作/储备池回放误差为 0，三项物理子步复算通过：RMSE `90.371 mm`、峰值
力矩 `42.324 Nm`、峰值速度 `0.070400 m/s`、外部穿透 `0.099829 mm`。
失败原因可解释且保留：柱子接触从 `16.728 s` 持续到 55 s（约 `23.896 s`），
没有完成放置或球反弹。原始 rollout、execution、指标和审计位于
`results/dagger3_combined_v4/` 与
`outputs/esn_office_joint_esn_stiff_20260929/dagger3_combined_v4_audit/`。
该结果表明六条件 DAgger3 的 +1 strict 优势尚未迁移到最终综合环境，不能声称
complex-v4 成功，也不解封 formal `dt=5e-5`。

## 2026-09-29 combined-exposure DAgger8

针对综合场景持续柱接触，固定增加一条实际 combined-v4 访问轨迹，用同一 stiff-VMC
在其 48D 本体状态上重标注并重训纯 ESN；环境、gate、actor 输入、执行器和 256 单元
预算均不变。checkpoint SHA256 为
`03fec322b4c9c84b48ab1842de49dd0dab95abdbd3e332b6532b4c30b1754142`。综合回合仍
task/strict `false/false`、最终 `carry`，但 RMSE 降至 `53.364 mm`，峰值力矩
`44.899 Nm`，峰值速度 `0.068360 m/s`，外部穿透 `0.091927 mm`。柱接触仍从
`15.141 s` 持续到结束（约 `22.189 s`），cup 位移约 `1.373 mm`，没有 placement
或 rebound；动作/储备池回放误差为 0。结果说明综合暴露重标注改善跟踪，却没有提供
脱柱恢复行为，不能声称综合场景成功；原始轨迹和审计保留在
`results/combined_dagger8_v4/` 与 `outputs/esn_office_joint_esn_combined_dagger8_20260929/`。

## 2026-09-29 single-pillar + thick-corner provenance and contact audit

The newer opt-in combined fixture has a 2 s delayed ball, hand and sustained
rod pushes, one pillar instead of cup plus pillar, and corner placement. It is
separate from the frozen baseline. The `v1` flag was reused during geometry
development, so archived MJB hashes now identify results in
`configs/esn_combined_thick_corner_pillar_v1_20260929.json` and
`docs/ESN_COMBINED_THICK_CORNER_PILLAR_AUDIT_20260929.md`.

Completed: the old 4 mm pillar `ridge_v1` pure ESN placed and retreated, but
strict failed at 0.943513 mm external penetration (limit 0.2 mm). Action and
reservoir replay error was zero; independent physical-substep RMSE/torque/speed
were 43.9415 mm / 58.8085 Nm / 0.245539 m/s. The current 2 mm pillar geometry
produced only 0.0264 s pillar contact and stalled at load transfer; it did not
pass task or strict. Both failures remain archived. Saved control bins support
48.5 mm hand movement during rod interaction, but do not prove continuous
physical-substep rubbing. The payload/corner saved-state first contact occurred
in carry, not lift. These are development `dt=1e-4` observations, not formal
results. Evaluator-only contact diagnostics now record continuous rod runs and
payload/corner contact by stage for subsequent runs without altering any gate.

Running: no local office evaluator was active at this audit. Not complete:
one fixed, visibly meaningful pillar fixture and a pure-ESN rollout that
simultaneously satisfies placement, 0.2 mm safety, rod rub while still in
contact, and lift-phase thick-corner contact. No formal `dt=5e-5` rerun is
unlocked.

The independently flagged v2 geometry also failed its 15 s physics probe:
moving the whole corner slab x from `.650` to `.640` produced hand/corner
contact at `0.7306 s` and stalled the pure ESN in `align`. Its longest
continuous rod run was `0.2371 s` with only `1.80 mm` hand motion; payload
never contacted the corner in lift. MJB SHA256 `f1fe21a8e05f2643f18384aa23553fc6adf3298b9a154463ac3456621e40dd7d`.
The failure and raw 15 s rollout are retained; it is not a full-task result.
No evaluator was running at this check. Next: design a separately versioned
local lift contact that preserves pre-grasp clearance.

The separate v3 local-face/bridge probe also failed at `align`: the bridge
touched the robot by `1.0963 s` and the payload never touched the corner
during lift. Its MJB is `1ac3312081d08c3c3ccd4e5f7d067a5ccafbf56d5108b9958bb06c1cb7019882`.
More importantly, both v2 and v3 place their 15 mm pillar across the ball
lane; the ball deflected by `2.04 s` without a ball/robot event. The old
4 mm v1 geometry had a real ball/link6 impact at `2.0939 s`. This rules out
using v2/v3 low penetration as a collision-response success. Their failed
traces remain archived. Running: none; incomplete: a single dynamically
valid scene meeting the ball, rod, pillar, lift-corner and task/safety goals.

The separate v4 world was then run for the full 55 s with the same pure-ESN
ridge checkpoint and `dt=1e-4`. Ball/link6 impact occurred at `2.0939 s` and
rebounded; payload/corner contact during lift totaled `0.2080 s`. Nevertheless
task/strict were both false: the final stage was `load_transfer`, the best
load-transfer position error was `16.798 mm` against the unchanged `12 mm` gate,
pillar exposure was only `0.0375 s`, and worst external penetration was
`0.394114 mm` against the `0.2 mm` limit. The longest continuous rod contact
was `0.0349 s` with only `0.122 mm` hand motion. Independent 550,000-substep
RMSE/torque/speed were `47.0526 mm / 58.0678 Nm / 0.272753 m/s`; all 1375
actions and reservoir states replayed exactly. MJB SHA256
`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`.
Full provenance and failures are in the combined-fixture audit. Running: none.
Not complete: task/strict success, continuous rod rub, or formal `dt=5e-5`.

A pre-registered algorithm-only output-gain 0.8 ablation on exactly the same
v4 MJB improved external penetration from `0.394114` to `0.136818 mm`, RMSE
from `47.0526` to `43.1634 mm`, peak torque from `58.0678` to `53.3077 Nm`,
and peak speed from `0.272753` to `0.096728 m/s`. Ball rebound and lift-phase
payload/corner contact remained. However task/strict stayed false/false at
`load_transfer`: best position error `14.986 mm` exceeded the unchanged 12 mm
gate, the pillar was never contacted, and the longest uninterrupted rod contact
was only `0.0683 s` with `0.059 mm` hand motion. Independent action/reservoir
replay was exact and all three 550,000-substep metrics were recomputed; hashes,
seed, plan, commands and raw failures are in the combined audit. Running: none.
Unfinished: pure-ESN combined task/strict and meaningful continuous rubbing.

The 0.98 gain-only screen stayed in lift with task/strict false/false. It had
`0.173824 mm` penetration, `32.2391 mm / 43.0499 Nm / 0.088481 m/s`
RMSE/peak-torque/peak-speed, ball rebound, only `0.0023 s` lift-corner contact,
no pillar contact, and `0.0361 s` longest continuous rod contact. Best lift
position error was `14.228 mm`; replay and substep audit passed. This negative
screen also does not unlock formal evaluation.

The pre-registered output-gain 0.95 screen on the same v4 MJB reduced
penetration to `0.120669 mm`, RMSE/peak torque/peak speed to
`28.5777 mm / 39.3901 Nm / 0.083917 m/s`, and retained ball rebound. It still
failed task/strict, remaining in `lift` with best position error `13.716 mm`,
no pillar or lift-corner contact, and only `0.0218 s` continuous rod contact.
Replay and substep audits passed; this candidate is retained as a negative
result. No formal rerun is unlocked.

## 2026-10-07 — v2 anchored readout torque/generalization follow-up

Completed: fixed-reservoir v2 anchored readout candidate
`ridge=0.1, smooth_weight=0.01, action_weight=0.0001, parent_trust=100`
was evaluated with the unchanged office-v6 worker, canonical48D/action7
interface, original gate and actuator limits, formal `dt=5e-5`, one thread,
and `MemoryMax=3GiB`. It passed task/strict on development_000, 001 and 004
and failed strict on 002, 003, 005 and 006, for `5/8` task and `4/8` strict.
Passing strict metrics: RMSE `28.338–36.499 mm`, peak torque `48.836–49.909 Nm`, peak speed
`0.349–0.366 m/s`, and maximum penetration `0.139–0.164 mm`; all action and
reservoir replay checks were exact. Checkpoint SHA256 is
`da281fbe03e122f0d36bb6e5e65183f9fd480b2f5acfd6a939404888075f5d59`.

The failures are retained and informative. development_002 completed
55 s with penetration `0.174 mm` but missed task/strict; its paired parent
ESN aborted at `24.32 s` with `2.602 mm` penetration. development_003 also
completed 55 s with `0.139 mm` penetration and only `38.311 Nm` peak torque,
but missed placement; development_005 passed task but failed strict at
`0.486 mm` penetration, and development_006 missed placement despite
`0.160 mm` penetration. These results support a limited robustness/low-torque
signal and explicitly do not establish cross-condition generalization or
task success. No sealed final condition was read and the uniform `/24` matrix
was not changed.

Infrastructure failures from early retries (wrong working directory, missing
thread environment, missing Git provenance, and Menagerie path) are preserved
under the campaign root and excluded from physical denominators. Raw audits,
source commit, checkpoint hashes, traces and local summaries are listed in
`docs/ESN_TORQUE_GENERALIZATION_20261007.md` and
`outputs/esn_torque_v2_corrected_20261007/`.

Independent audit completed: `paper_metrics_20261002.py` re-read each saved
`rollout_metrics/substep_metrics.npz` and `research_substeps.npz` on arm1 and
recomputed RMSE, peak actuator torque, peak end-effector speed, penetration,
horizon/abort and contact/recovery diagnostics. All six rows matched their
worker `AUDIT.json` values within floating-point rounding; action, reservoir,
and common-filter replay errors remained zero. The compact audit ledger is
`outputs/esn_torque_v2_corrected_20261007/INDEPENDENT_AUDIT_SUMMARY.json`.

Running: no new worker at this checkpoint. Not complete: confirmation on the
remaining registered development identities, independent substep/contact
audit aggregation, and any claim of a new frozen ESN model. The candidate is
not promoted until the unchanged selection rule is satisfied.

2026-10-07 v2 `.003` 候选已完成八个 development 闭环，task/strict `4/8`、`3/8`；四个严格通过回合
RMSE `29.634–34.438 mm`、峰矩 `49.907–50.485 Nm`、峰速 `0.349–0.366 m/s`、穿透 `0.140–0.184 mm`。
development_000 strict 因 `0.581 mm` 穿透失败；development_003/004/005/006 虽低穿透但放置失败，其中
development_005 峰矩仅 `40.169 Nm`，明确不能把低峰矩当成功或柔顺性结论。所有回合完整保存，三项 replay 最大差
`0`；arm1 独立 paper metrics 已核对。首次 dev001 目录错误作为基础设施失败保留并排除。候选 checkpoint
`5b043942da39ff6ee280c56a95b8198a30609ba9fcfde16580fe7fe6e6166dad`，证据账本为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s005_summary.json`。

2026-10-08 noise consistency 候选已完成八个 development 闭环，task/strict `0/8`、`0/8`；全部完整执行，
RMSE `27.721–31.180 mm`、峰矩 `39.309–48.710 Nm`、峰速 `0.354–0.385 m/s`、穿透 `0.138–0.178 mm`。
低峰矩和低穿透均未转化为放置成功，因此不升级该候选。独立 paper metrics 已核对，证据账本为
`outputs/esn_torque_v2_corrected_20261007/closed_loop_noise_summary.json`，原始回合保存在 arm1 campaign 根目录。

为完成因果配对，父 ESN checkpoint `acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7`
已在八个相同 development 条件上补齐，task/strict `7/8`、`6/8`。父 ESN 在 development_002 以
`2.602 mm` 穿透中止，在 development_004 完整执行但 strict 因 `0.657 mm` 失败；其余回合保留原始审计。
配对账本为 `outputs/esn_torque_v2_corrected_20261007/parent_paired_summary.json`。配对结果显示 `.003`
readout 的收益是条件依赖的：某些条件穿透下降，但另一些条件放置失败或峰矩高于父 ESN；不能写成统一降矩/泛化优势。

state-delta v4 只做了正式 `dt=5e-5` 的 development_000 smoke：task=true、strict=false，RMSE
`30.459 mm`、峰矩 `53.107 Nm`、峰速 `0.3647 m/s`、穿透 `0.5795 mm`，replay 最大差 `0`。独立
paper metrics 已核对。由于首条件相对父 ESN 和 `.003` 候选均未改善，按停止规则未派发其余条件；候选不进入正式矩阵。
## 2026-10-08 — office-v7 three-obstacle unified comparison

Completed one independent development condition using the unchanged office-v6 MJB, gate, actor contract and actuator limits. The registered schedule is ball 2.0 s, person 4.5 s, rod 14.0–22.5 s, followed by thick-corner placement; formal `dt=5e-5`, 55 s, seed `2026100807`, canonical48D/action7. The 17-method campaign is archived at `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_three_obstacle_20261008/run_003/`.

Twelve methods completed physical rollouts: task `4/12`, strict `3/12`. `recovery035_esn_fixed`, `recovery035_esn_memoryless` and the matched MLP passed task/strict in this single condition; matched RNN failed because of `0.423 mm` penetration. Five RL transfer rows were preserved as infrastructure failures from a pinned JAX/Orbax sharding error and are not counted as physical zeros. The full table and limitations are in `docs/OFFICE_V7_ALL_METHODS_20261008.md`. This development condition does not amend the sealed office-v6 matrix and does not establish generalization.

## 2026-10-08 — 新 16 × 24 综合条件与 RL 恢复

按用户要求开始新的 office-v7 384 回合有限评测，固定每个方法一个旧 uniform24 首模型，
24 个同配对扰动条件，formal dt=5e-5、55 s。这不是复用旧 office-v6 结果或旧 v7 单条件模型。
球/人手/棍的扰动参数预注册，布局/MJB、任务门槛、actor 输入及执行器限制不变。
RL 加载修复为恢复原 CUDA/JAX/Orbax 环境；五个 checkpoint 各 1375 动作 exact replay 通过，
归一化/计数均冻结。本轮不训练；可运行不等于任务表现已改善。

2026-10-08 14:05 CST 快照：7/384 回合通过独立子步审计。ESN/matched RNN/matched MLP
在新条件 000 均 Task/Strict 通过；三类参数 RL 停在 carry，direct-metric 停在 approach。
全部保留，未形成任何方法完整 `/24`。四路有限服务稳定运行；另有只等待结束的报告服务，
不会新增仿真或定时任务。最终 Task/Strict 按各 24 回合报告，早停及失败保留分母。

详见 `docs/OFFICE_V7_UNIFORM24_20261008.md`。真实源码、登记及产物在
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。
`report_final/` 是批次结束后的预定产物，目前未完成；不能引用为最终结果。尚未完成完整
384 回合及跨方法结论，不据单条件声称 ESN 优势。

### 中间快照（2026-10-08 15:48 CST）

批次完成 `77/384` 回合，4 回合运行中。当前计数为 ESN `5/5 task, 4/5 strict`、
matched RNN `4/5, 3/5`、matched MLP `3/5, 2/5`、ordinary RNN `2/4, 1/4`、
ordinary MLP `4/5, 4/5`、memoryless `2/5, 2/5`、enhanced teacher `4/4, 3/4`。
经典控制器、五类 RL 和 nominal zero 的已完成回合当前均未 Task 成功。由于每个方法还未
完成 24 个条件，不能报告最终成功率或泛化结论。

已完成回合的 ESN 均值为 RMSE `28.89 mm`、峰矩 `51.49 Nm`、峰速 `0.362 m/s`、
最坏穿透 `0.375 mm`；matched RNN 为 `29.86/49.80/0.363/0.474`，matched MLP 为
`44.17/47.67/0.373/0.297`。这些均值混合了成功和失败回合，不能作为单独柔顺性排名。
中间报告位于服务器 `office_v7_uniform24_20261008/report_progress_current/`；
最终报告仍由等待服务在批次结束后生成。

### 八路接续及失败机制核查（2026-10-08 18:08 CST）

用户再次要求充分利用算力后，仅调度资源由4路提高到8路，单线程/3GiB、原模型、场景、
步长及gate均保留。旧四回合自然结束后仅补审计，没有重跑；166完成后派发新回合，
首批8个约6–7分钟完成，当前174/384完成、8运行。新服务
`sii-office-v7-uniform24-v2-20261008.service` 与 `sii-office-v7-uniform24-report-v2-20261008.service`
正在运行，**不要恢复旧协调器或旧报告等待服务**。原协议保持原样，资源补充在 `DISPATCH_V2.json`。

只读诊断确认经典VMC/调参VMC受阻近静止、导纳有末段运动但未到位、经典阻抗有无外部接触
的带载抬升静差；直接动作RL约93%–95%控制步触发变化率限制。详见
`docs/OFFICE_V7_STALL_AND_DISPATCH_20261008.md`。证据在服务器同run的 `dispatch_v2/`，
诊断未用于本批选模型或调参数，不能声称baseline性能已经修复。全384回合和后续独立开发
因果消融尚未完成。
