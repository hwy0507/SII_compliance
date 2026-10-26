# 2026-10-26 参数cycle5、SERL第二周期审查与续训

原Goal继续active。已完成真实周期审查、有限诊断及新正式阶段启动，尚未获得四方法健康收敛，
也未完成最终冻结策略/指定ESN/SPT比较。GPU每卡50%尚未全部满足。

执行位置为本集群SSD：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`（以下B）。
本轮fetch/read并快进main `b245607`，baseline仍`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
新main是另一主机非RL首个条件9回合审计，不改变本集群RL合同，也不是最终ESN指定。

## 完整周期结果

| 方法 | 完整周期编号 | 累计transition | Task / Strict，各30 | 平均reward | 终端Q绝对误差均值 |
|---|---:|---:|---:|---:|---:|
| 官方SERL Direct | 1 | 82324 | 0 / 0 | −35.10199 | 4.0901 |
| CHEQ Impedance | 5 | 244500 | 18 / 18 | −0.46473 | 4.4261 |
| CHEQ Admittance | 5 | 243500 | 13 / 12 | −12.21946 | 3.5346 |
| CHEQ VMC | 5 | 244500 | 17 / 16 | −4.59813 | 16.0117 |

三参数cycle5各新增41250transition，完整30条件；父cycle4的全部replay字段前缀精确保留，
新增reward/done、条件集合、terminal标签、MJB hash及网络有限性核验通过。cycle3历史部分
数据仍保留但不计完整周期。审查不是重新独立计算原始物理子步。
相较cycle4，Impedance Strict17→18、reward改善；Admittance13→12、VMC17→16，不能声称
大batch全面有效。VMC next Q约188→249持续增长，loss末段约70，仍有明显学习问题。
终端Q指标包括每critic的in/out-of-bag样本；完整JSON分别报告，不把总体误差下降当策略改善。

Direct第二周期实际41074条，29个完整55秒回合、1个提前终止：
`passive_corner_train_0500`在1199动作时因`global_penetration_exceeded_2mm`结束，失败保留。
30条件全部approach失败。两周期累计618600critic更新；末1000外层更新critic loss均值
.02661，Q均值15.0666。全部82324条replay与两周期journal的观测/nextstate、动作映射、
reward/done精确核验；60terminal均使用原已披露占位nextstate并零bootstrap。
当前终端Q绝对误差4.09（上周期9.95），但reward−34.2233→−35.1020，无成功，非收敛。

证据：B/runs/cheq_batch32768_online_20261026_v1/CYCLE05_REVIEW.json、
B/runs/cheq_batch_cycle05_review_20261026_v1/health、B/runs/serl_cycle01_review_20261026_v1。
两套诊断图均已目视检查，原四阶段进程正常结束，不重启原run。

## 有限对照与决策依据

先做三参数actor LR对照：B/runs/clock_batch_cycle05_actor_lr_probe_20261026_v1。
从同一完整cycle5的全learner/optimizer/replay/RNG开始，各方法两臂3e-4/3e-5、各5000更新，
batch32768，共30000辅助更新、0physics、不保存或推广权重。初始全状态与replay抽样流hash
匹配、父状态不变、完整20记录点/臂核验，图已目视检查；不是多seed或在线成功结论。

| 方法 | 终点replay Q：原LR / 0.1LR | 终点in-bag终端MAE：原LR / 0.1LR | 解释 |
|---|---:|---:|---|
| Impedance | 33.961 / 33.828 | 1.832 / 1.835 | LR敏感性小，保留原LR |
| Admittance | 72.300 / 71.686 | 3.549 / 2.480 | 降actor LR有拟合改善，但Q仍明显偏高 |
| VMC | 260.207 / 259.352 | 9.280 / 8.493 | 两臂都继续Q增长，未修复 |

VMC再检验降低critic LR：B/runs/clock_batch_cycle05_vmc_critic_lr_probe_20261026_v2，
只新增5000更新，复用上述完全相同的factor1对照。终点Q259.985、in-bag MAE6.588；Q仍增长，
不据此部署critic LR。v1错误重复派发了原factor1对照，发现后已停止；最后记录1500更新，
可能有少量未记入日志的更新，全部丢弃不推广。失败收据保留，不把这段算独立证据或隐去计算。

随后仅检验已有实现的all-five target最小值：
B/runs/clock_batch_cycle05_vmc_all5_probe_20261026_v1，新增5000更新并复用原pair对照。
所有其他state/RNG/replay及actor随机pair保留。从当前Q251.789出发，pair升至260.207，
all5降至241.533；但in-bag终端MAE由11.943升到16.910（pair9.280），上界违反仍普遍存在。
这是有代价的算法变化，不是官方CHEQ原样、不等价于纯性能优化、不证明修复；旧历史all5
阶段失败仍保留。仅据此登记有限在线试验，检验新clock/batch条件下真实轨迹变化。

Direct另做官方SERL batch吞吐测量：B/runs/serl_cycle01_batch_probe_20261026_v1。
2048/8192/32768各192外层更新，另各1次显式编译更新后恢复原状态，总4632个辅助critic更新。
全部完整state恢复digest一致、有限，无physics/权重推广。2048约127.55outer/s、32768约
34.05outer/s，采样行吞吐从约26.12万/s到111.57万/s；测量不包含JIT编译时间。
这仅支持大batch可执行及吞吐比较，不支持学习有效性结论。

## 当前正式阶段

所有新阶段均恢复已审查正式checkpoint，保留网络、Adam moments/counters、replay、RNG。
没有加载任何辅助权重。physics/MJB/gate/filter/执行器/dt5e-5、原30条件和SPT reward均不变。

| 方法 | 当前run，均相对B/runs | PID / GPU | 明确变化与阶段预算 |
|---|---|---|---|
| Direct | serl_batch32768_cycle02_20261026_v1/direct | 3339709 / 0 | batch2048→32768；1完整cycle2 |
| Impedance | clock_parameter_reviewed_cycle06_07_20261026_v1/impedance/train | 3070037 / 1 | 保持batch32768、UTD1、原LR；2完整cycle6/7 |
| Admittance | clock_parameter_reviewed_cycle06_07_20261026_v1/admittance/train | 3070069 / 2 | 仅actor LR3e-4→3e-5；2完整cycle6/7 |
| VMC | clock_parameter_reviewed_cycle06_07_20261026_v1/vmc/train | 3419078 / 3 | target随机2→全部5取min，actor仍原pair；2完整cycle6/7 |

Direct保持官方十critic、无熵backup和8critic:1actor，32768拆为8×4096 critic批次再做1次actor。
随机初始化/零示范是原cycle0的来源，本阶段不是重新初始化；完整父checkpoint82324条全部保留。
新wrapper仅替换冻结trainer的协议守卫：拒绝额外UTD/critic clock变更，验证准确父checkpoint、
源码/审查hash，限定1周期。实际check-only正负检查通过；原SERL核心和sampler源码未改。
大batch改变梯度统计，均匀采样每批终端样本期望数增加，是否改善真实学习仍待完整周期。

参数继续使用原冻结trainer支持的completed-stage入口，未改正在运行的runtime。
Admittance准备快照只改actor optimizer param-group LR；VMC只新增target_count=5元数据，
其他learner字段digest精确。两者只清空新阶段plateau聚合history，旧history完整保留在父快照，
不清空学习状态或丢弃transition。总参数决策文件中的VMC“待诊断”为较早时点，以VMC目录的
后续独立SCIENTIFIC_DECISION和实际LAUNCH为当前依据。

新四路启动独立核验B/runs/reviewed_continuation_startup_20261026_v2通过：Direct/I/A/V新增
9000/29000/28000/8000 transition时，全部父replay字段前缀精确，更新增量分别按8/1/1/1，
learner/optimizer有限、LR/target规则与登记一致；已启动12/26/24/12个MJB hash核验。
v1只读检查因浮点精确比较`3e-4*.1`与`3e-5`失败，保留日志；v2同时要求与准备父LR精确相同
并以1e-12容差核对登记值。它不是训练失败，未重启训练。

CPU仍每方法1learner+12sampler，四组0–12/13–25/26–38/39–51，检查使用52–54。
四路实际启动并推进，无FAILURE。新的只读准确周期归档器PID3494331在
B/runs/reviewed_continuation_cycle_archive_20261026_v1运行；身份匹配原learner，结束即退出，
错过边界明确报告。各阶段预算结束后必须再审查，不自动复制或延长。

## GPU、发布和剩余工作

混合窗口66.11秒：3.43/66.92/53.87/62.72%，GPU0为旧SERL收尾，后三卡是有限actor LR辅助，
不能称正式训练达标。新四路正式窗口66.48秒：**64.73/55.35/46.67/42.27%**，没有辅助训练，
前两卡超过50%，后两卡仍不足。大batch减少Direct空闲，但不能宣称四卡要求已经完成。

小证据在docs/evidence/rl_continuation_20261026，SOURCES.json逐文件记录实际SSD路径与SHA。
source子目录是实际执行脚本的审阅副本，不是独立可运行环境；冻结runtime与原manifest完整
保留在SSD。大型checkpoint/轨迹未传到另一主机，也未声称HDD关机备份覆盖了新大产物。

下一步检查完整SERL cycle2和参数cycle6/7的reward、优化健康、失败与冻结策略行为。特别检查
VMC all5是否仅降低Q而损害终端拟合/任务表现，以及Admittance降低actor LR能否在真实回合中改善。
仍需四方法充分收敛、最终完整冻结比较、指定ESN及统一SPT；不能用本报告有限诊断替代这些要求。
