# 按方法独立完成周期并交接采样资源

> 最新状态（2026-10-26 UTC）：四路原SAC已全部完整收尾。新Impedance已从全新state以12worker开始学习；Direct已从完整cycle0以12worker接续cycle1。Admittance/VMC仍完成各自原cycle0，之后由原协调器自动交接。以下启动时记录保留其历史时点；本次补充详见文末。GPU50%、健康收敛和最终比较均未完成。

## 实际改变

取消旧资源交接的“四路新CHEQ都预热并开始更新”统一等待条件，改为各方法独立交接。
这只改变调度依赖，不改变 source_train16、batch256/UTD1、gamma=.9995、reward、物理/MJB、
actor信息、gate、公共filter、执行器或dt，也没有重新开始已经运行的CHEQ。

原v1逻辑在发出STOP前等待两个旧协调器完成。Impedance仍有原SAC需要收尾，之后还需
新CHEQ双worker预热；较快的Direct可能在此期间越过首个周期并进入下一整轮双worker，
导致可避免的额外等待。新协议让当前三路CHEQ立即登记“完整当前周期后停止”，
与同接口SAC分别收尾，二者都退出且完整checkpoint核验通过后立即恢复该方法。

- Direct、Admittance、VMC：完整当前cycle0边界复制全网络、target、Adam、温度、RNG、
  replay和历史；继续剩余五个周期，若实际边界不同则按六周期总预算扣减。
- Impedance：新CHEQ此前确实未启动。只等待原SAC当前完整cycle4释放对应核，随后直接
  用同source/seed/protocol、空replay/全新state、12sampler启动六周期。
- CPU/GPU分配保持原资源登记：D learner0+workers1–12/GPU0，I learner14+15–25/52/GPU1，
  A learner26+27–38/GPU2，V learner39+40–51/GPU3；共52核，13/53/54保留。
- 改变sampler数量会改变未来采样和RNG交织，不声称未来轨迹逐位等价；没有增加原阶段
  总周期预算，也不把六周期完成当作收敛。GPU50%要求仍未达到，当前尚不能评价扩容效果。

## 已执行与尚未执行

旧priority coordinator1956030、fresh dispatcher1146202、SAC coordinator691298均通过
各自COORDINATOR_STOP/DISPATCH_STOP正常退出，实际DISPATCH_STOPPED的已派发方法与登记一致。
它们已经退役，不应重启。旧进程没有触发额外Impedance learner。

新逐方法协调器 **2471936** 已运行，输出 `runs/cheq_fresh_ready_seed20261025_v2`。
它已写入六个新的完整周期停止请求，原Impedance SAC的既有STOP字节hash保持不变。
没有向learner发送进程信号，没有部分回合接续。冻结trainer仅在外层周期边界检查STOP；
内部仍派发当前全部30条件，失败回合保留。

原只读observer1968149在无子进程、无已完成阶段的等待状态被明确替换为 **2472115**，
原0/1/3/5审计仍保留；从原run、旧v1目录和新v2目录定位真实checkpoint。新归档器
**2472286** 从空LAUNCH开始跟随各路实际启动，持续归档至原有限阶段结束。
旧两个early/migration归档器在所有旧learner退出且父状态保存后才通过MONITOR_STOP结束，
没有写入伪造的旧协调器MIGRATION_FINISHED。

启动核验时原七learner均保持PID/启动身份、仍在运行且无FAILURE：

| 方法 | 新CHEQ步数/完成条件 | 对应SAC步数/完成条件 |
|---|---|---|
| Direct | 14431 / 10 | 367540 / 11（cycle8） |
| Impedance | 尚未启动 | 215028 / 20（cycle4） |
| Admittance | 12271 / 8 | 225243 / 27（cycle4） |
| VMC | 13153 / 8 | 242693 / 9（cycle5） |

条件数分母均30，是结束回合数，不是成功数。三路CHEQ均cycle0。
此时新协调器状态为draining_or_resuming_independently、launched为空；
**只证明完整周期收尾已经请求且原训练继续，并不证明恢复或12worker扩容已经完成。**

## 验证和产物

四项新增守卫测试通过：三resume+一fresh组合、缺失/重复parent、CPU/GPU与仍在收尾的
其他方法资源冲突、旧协调器未退役或意外多派发。复用既有完整周期/预算核验函数；
实际七parent命令/启动身份/EXECUTION/STOP及780源码、24参数、30条件/参考计划hash核验。
旧冻结runtime、协议和checkpoint没有修改。新工具及测试文件在UTC跨日至26日前编写，
保留其20261025文件名；本报告按实际整理日期20261026命名。

实际集群主机 `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`，SSD根
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`：

- `runs/CHEQ_FRESH_READY_METHODS_V2.json`：新调度协议，覆盖旧统一等待v1。
- `runtime/fresh_ready_methods_v2/`：冻结协调工具、预检、旧协调器退出/新启动收据。
- `runs/cheq_fresh_ready_seed20261025_v2/`：实际收尾/后续恢复run。
- `runs/CHEQ_FRESH_READY_METHODS_AUDIT_V2.json`、`runs/fresh_ready_methods_audit_v2/`：替代只读观察。

配套JSON记录协议、实际启动核验和证据hash。剩余工作仍是原有限阶段的完整周期科学review、
健康收敛、固定策略训练集矩阵、SPT/接触舒适性和指定ESN比较；指定ESN缺口不变，Goal active。
本轮fetch main a52dfba4486af8d263d5cd0a976c3102482ff249、baseline
f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，远端无新增。

## 首路完整周期收尾已核验（2026-10-26 UTC补充）

原Admittance SAC1316018已正常退出，不应重启。FINISHED为stopped_at_complete_cycle，
cycle4/226765步/412500updates/replay226765；30条件完整集合、全部55秒、Task/Strict13/13各30。
终端结果/时长/实际模型hash核对通过，最终checkpoint与独立cycle00004归档字节hash相同：
`06925f845801f30cda2e9e78f9fd30e5f1e1ee279bb4fc2c4d5e27be00961998`。
只读观察/复核没有新增physics/updates，不代表critic健康或固定策略接受。证据位于新run的
ADMITTANCE_SAC_DRAIN_REVIEW.json，配套JSON含其hash与摘要。

对应fresh Admittance1314547仍在完成自己的cycle0，原协调2471936仍存活、未启动任何恢复learner；
只有该fresh也完整结束后才12worker接续。此次确认的是第一路SAC按计划正常收尾，
不是整个资源交接结束。原启动快照的七learner全部live描述仅指当时，不代表此补充时点。

## Direct、VMC也已正常完成周期并退出（2026-10-26 UTC补充）

| 原SAC | 结束周期 | 总步数 | 总更新 | Task/Strict，各30 | 完整55秒 |
|---|---:|---:|---:|---:|---:|
| Direct，原PID1215621 | 8 | 384621 | 722758 | 0/0 | 28 |
| VMC，原PID726082 | 5 | 268509 | 495000 | 17/17 | 30 |

两原进程均正常FINISHED=stopped_at_complete_cycle，勿重启。各30条件完整集合、终端结果、
时长、实际MJB/replay和最终checkpoint与独立归档hash均核验。Direct被动0671/0400分别
395/902action因穿透超限提前结束，两个失败保留；不把整组写成30个55秒回合。
Direct最终hash `ad62c3f1219b484c00e2c28315e9ddd389b390f84288014c989414c37169bf9d`，
VMC最终hash `2643cb155f92937ec4def6ef63b663f5167d13074b0453bf52e08594c9d1d791`。
新run内DIRECT_SAC_DRAIN_REVIEW.json和VMC_SAC_DRAIN_REVIEW.json记录逐条件收据；
本轮只读观察和核验0新增physics/updates，未改科学设置，也没有重新诊断最终critic健康。

原SAC现仅Impedance1557140仍在收尾。三fresh learner继续各自cycle0，逐方法协调器
2471936/审计2472115/归档2472286仍活跃，尚无新恢复learner。17/30训练成功不能替代
固定策略评估、收敛或相对名义控制的学习改善；各方法此处周期不同，不作统一排名。

## Impedance实际开始学习，Direct完整状态恢复（2026-10-26 UTC补充）

原Impedance SAC1557140已正常结束cycle4，228528步/412500updates，30完整55秒条件，
Task17/Strict16；最终checkpoint与原run的cycle_archive/impedance/cycle_00004.pt相同，
hash `fb4786b3b581aad7bfa656019d1fe84dc71b2c8b30b7ad63914642f32c74b85a`。
新run IMPEDANCE_SAC_DRAIN_REVIEW.json保留终端/model/时长/replay及归档核验。
至此四路原SAC均正常停止，不应重启。这些各自末轮结果不是统一预算的固定策略比较，
本次没有重新诊断它们最终critic健康，也不能用训练成功数取代收敛。

新Impedance **3849956** 按原登记从全新网络、Adam、温度和空replay启动，未导入SAC权重。
12个实际worker绑定15–25/52，learner14/GPU1；同source16、batch256、UTD1、六周期。
保留的4000步/0update快照与相同seed的CPU fresh构造比较：agent、三optimizer、log_alpha、
alpha、num_gradient_steps和observation_scale精确相同，optimizer state为空。4000条replay
奖励、done和自身混合context与真实日志精确对应。探索已消耗的RNG不与未采样构造器相等，
不将所选字段核验外推为全运行状态逐位相同。

15000步快照已有10001次更新；actor、五critic及target网络都发生变化，网络/Adam/日志
数值有限，早期4000条replay全部字段精确保留，optimizer日志步数连续。
前100/末100次critic loss均值2.23095/0.08127，仅描述学习启动，不证明收敛或Q校准。
核验时已生成的14个场景的fixture、实际MJB、reference plan、dt以及首条输入/动作符合登记。

首次只读核验误把journal的executed_action断言为5维，实际是公共7维控制动作；
原5维参数动作经ParameterController.act映射后才记录executed_action。
正确维度为canonical原始观测48、Impedance参数动作5、下游公共动作7；CHEQ网络另接
自身混合context成为49维。修正的只有新只读核验器，训练/actor/controller没有修改或重启。
ATTEMPT1_FAILURE.json保留错误，原4000步warmup.pt未被替换。

Direct原1215546完成cycle0后正常退出，41250步/36251updates、30完整55秒，
Task/Strict0/0，平均回合reward −32.96638。原协调器已自动启动 **4055508**，
learnerCPU0/GPU0、12worker CPU1–12，从完整父checkpoint恢复剩余五周期。
父checkpoint原文件、复制文件和EXECUTION记录hash一致：
`15eb22664e7e3f4c8db3eaf4566f33f7b34bf08c596b58f21bebb6eda04cbfba`。
46250步/41251updates新快照核验：全部41250条父replay字段及cycle历史精确保留，
三Adam计数延续增长、actor实际改变、网络和日志有限，新增5000条更新步连续。
父文件保留网络/target/optimizer/温度/归一化/RNG/replay，既有load_state_dict恢复这些字段；
worker数改变后未来采样和RNG交织不同，不称未来逐位一致。首12个新模型及48/7/7输入动作核验。
原协议的restart_reason描述整个fresh阶段起源；本次Direct实际接续以resumed_from/hash字段为准。

纯正式CHEQ的60秒、60样本GPU均值 **10.02/6.13/1.18/1.05%**，最小7/1/0/0%，
不含辅助GPU训练，尚未达50%。窗口内D/I已12worker，A/V仍旧双worker，
不是四路全部扩容后的稳定窗口；不据占用率加大batch/UTD改变当前科学设置。
三观察/协调PID2471936/2472115/2472286继续，完整cycle0科学诊断仍等待四路归档。

只读核验产物（上述SSD根下）：

- `runs/impedance_fresh_start_review_v1/`：失败说明、原warmup、学习后snapshot、两份review及核验脚本。
- `runs/direct_fresh_resource_resume_review_v1/`：接续后snapshot、REVIEW和核验脚本。
- `runs/cheq_fresh_ready_seed20261025_v2/GPU_60S_FIRST_IMPEDANCE_12WORKERS.json`：完整GPU测量。

本轮复核没有新增仿真或optimizer update，实际在途训练按原授权继续；未修改冻结runtime、
protocol、physics/MJB、actor信息、公共filter、gate、执行器限制或dt。报告JSON记录收据与脚本
hash、当时进度。下一步仍是完成原六周期阶段并据完整周期证据审查reward、critic/actor、
固定策略结果；指定ESN比较、最终SPT和接触审计未完成。Goal保持active。
