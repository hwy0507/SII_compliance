# 当前完整目标证据与首撞慢放（2026-09-27）

目标仍未完成。用户最新明确要求 VMC teacher＋ESN 联合优化并继续推进，
现已恢复软件研究，见[新目标与固定预算实验](ESN_VMC_JOINT_OBJECTIVE_20260927.md)。
此前“无具体软件下一步”的判断范围过大，已撤回；物理标定不是联合优化
的前置条件。纯本体、原材料/solver及门槛保持，保留参考仍为R34。旧
[阻塞审计](ESN_OFFICE_BLOCKED_AUDIT_20260927_R2.md)仅记录当时决策。

新进展见[联合优化首轮报告](ESN_VMC_JOINT_PROGRESS_20260927.md)：J1 八回合
teacher 筛查已完成并审计，J2/J3 运行中。尚无新 ESN checkpoint；以下
R34 任务/安全证据仍成立，不能把 teacher 候选结果计为 proposed 成功。

| 目标要求 | 当前权威证据 | 状态 |
|---|---|---|
| 实际目标办公室仿真，包含人手、球、推杆、静态障碍 | R34各回合MJB、office-v5源码、全任务回放 | 已覆盖这些场景组成；不是真实机器人/真实人实验 |
| 真实物理抓取、搬运、稳定放置、松爪和撤离 | R34六条55s完整结果及独立审计，task6/6 | 六个开发回合完成 |
| 全部条件外部穿透≤.2mm | 强球撞.207370134mm，其余五条低于门槛 | 未完成 |
| 足够接触曝光与严格综合门 | 提前9s推杆0s、正移布局.225s，低于.4s要求；strict3/6 | 未完成 |
| 多条件开发/保留划分 | 冻结development_protocol及hash | 已划分；未按结果重选 |
| 保留条件跨环境稳健性 | 原协议禁止开发通过前解封；本机rollout/execution索引无三个保留seed记录 | 未运行，不能宣称泛化成功 |
| 保留所有成功、失败、模型/源/参数/seed/hash/原始数据 | R34、R35、R36、观察器候选及所有诊断独立报告/归档 | 当前已运行实验均保留 |
| 可汇报动图及可解释结果 | 既有原场景严格通过/强球撞任务成功回放；新增首撞慢放与哈希 | 已制作，未将安全失败隐去 |
| 方法优势与真实部署边界 | 零残差也可完成已诊断任务，R35/R36无明确整体增益 | 不支持ESN独占优势或硬件安全部署结论 |

R34证据：`outputs/esn_office_r34_stress_20260927/R34_STRESS_RESULTS.json`、
`R34_INDEPENDENT_AUDIT.json`。其后两个候选没有跨过完整门槛，见
[R36回归](ESN_OFFICE_EQUILIBRIUM_20260927.md)和
[观察器因果审计](ESN_OFFICE_OBSERVER_AUDIT_20260927.md)。

## 可用于汇报的首撞证据

[首撞慢放GIF](../outputs/esn_office_impact_explanation_20260927/final/first_impact.gif)
和[MP4](../outputs/esn_office_impact_explanation_20260927/final/first_impact.mp4)
包含办公室全景、手球近景、重建穿透曲线、采样时间轴和原始策略输入/动作。
它仅回放首次约100ms；完整55s的任务结果来自同一条原记录。

[同一回合完整任务动图](../outputs/esn_office_r34_stress_20260927/hard_task_success_replay/replay.gif)
保留抓放和撤离过程，标题明确task=true、strict=false。

首撞慢放由保存MJB与原始qpos逐帧生成，没有再次积分物理。重建峰值
.207370134350628mm，原记录.207370134380088mm，差2.95e-11mm。画面不
夸大几何压入；微小穿透用数值曲线说明。状态稀疏区间保留断线，不填造
连续运动。原统计使用积分前缓存接触几何，保存qpos为积分后状态，两类
时间戳可差一个1.5625us子步；不能用回放画面替代原物理指标。

视频164帧、1280×864、20fps、8.2s；GIF合并重复停留帧后124帧，总时长
仍8.2s。时轴为非匀速慢放，标注真实存档时间。已完整解码核对帧数/时长、
检查峰值和末帧图像、复核全部媒体hash以及80ms前动作严格为0。
渲染使用本机单线程、MemoryMax=3G/SwapMax=512M用户scope；已终止，没有
遗留仿真或渲染任务。来源/逐帧记录/输出hash位于同目录manifest.json。

## 可陈述及不可陈述的结论

可以陈述：本体ESN在当前六个开发场景完成完整物理任务，但完整安全/曝光
门槛只有3/6。首次强球撞约55.06–55.51ms，非零负载直到80ms才进入ESN；
当前零初态、只由wrench驱动且保持零负载平衡的读出修改不能改变该首撞。
接触后理想力矩和克隆状态诊断进一步显示该接触阶段局部控制影响受到
耦合约束强烈抑制，详见[表面惯量与驱动力证据](ESN_OFFICE_SURFACE_AUTHORITY_20260927.md)。

不能陈述：全部纯本体控制器必然失败、物理接触参数已被证明错误、ESN已在
盲测或真实机器人安全成功、只有ESN可以完成任务。下一分支若做独立共同
标定，需要用户决定并提供/确定独立物理依据，不能为过线挑参数。具体
[待决提案](ESN_CONTACT_CALIBRATION_PROPOSAL_20260927.md)已准备；当前未实施。

## 联合优化当前快照（2026-09-27）

在上述结论基础上，DAgger 和 wrench-norm 加权分支已完成开发集闭环审计：

- 第一版 48D ESN：`task 4/6`、`strict 1/6`；
- DAgger1：`task 6/6`、`strict 3/6`；
- DAgger2：`task 6/6`、`strict 3/6`；
- 当前开发集最佳的 wrench1：`task 6/6`、`strict 4/6`。

wrench1 使用 checkpoint
`8975edeb50a68b583034ee1945ff4d8b57303158d64c705cc3d8af9621006352`，权重
仅由 canonical48D 中 actor 可见的 `obs[39:45]` wrench 估计范数确定；未使用
接触真值、球状态、事件时间、阶段或视觉。其失败集中在 shifted-plus 和
hard ball，hard 的外部穿透约 `0.207610 mm`，仍超过 `0.2 mm`；因此没有
解封 held-out，也没有真实环境/硬件安全结论。所有新回合和 DAgger2/wrench
消融审计分别保存在 `outputs/esn_joint_stiff_*_eval_20260927/`，旧失败和
Pillow 环境错误也原样保留。

另外完成了 action smoothing `alpha=0.5` 的固定消融：六条件仍 `task 6/6`、
`strict 4/6`，峰矩略低但 hard 穿透升至 `0.208280 mm`、shifted-plus 接触
仅 `0.182 s`。因此当前没有证据表明单纯低通能解决复杂办公环境瓶颈，
主模型仍为 wrench1；保留条件继续封存。

受约束读出导数匹配消融（`delta_weight=1`）进一步验证了这一点：六个开发
条件仅 `task 4/6`、`strict 1/6`，原始和 rod-hold 任务失败，因此不采用。
当前证据不支持将动作平滑/导数正则作为泛化主因；下一阶段应优先分析
teacher 与共同执行接口在受扰动本体状态下的闭环覆盖。

多时间尺度消融也已完成：reservoir 三组时间常数整体放大 2 倍后，六条件
仅 `task 3/6`、`strict 1/6`；虽然 shifted-plus 通过严格门槛，但原始、
rod-hold 和 hard 失败。因此更长记忆不是当前可汇报的泛化结构，主模型仍为
wrench1，保留条件继续封存。

## J2 action-unit 对齐 teacher 的完整复核（2026-09-27）

J2 wrapper 的两轮参数传递失败（`j2full2_*`、`j2full3_*`，exit code 2）已
保留且明确排除；修复后新的 `j2full4_*` 六回合均完成物理积分。独立报告为
`outputs/esn_office_joint_teacher_j2_full4_20260927/J2FULL4_AUDIT.json`，
对应原始 MJB、NPZ、teacher trace、execution 和源码快照均在同一目录。
动作/状态重放与三个物理子步指标审计通过，结果 `task 6/6`、`strict 3/6`。
条件顺序为 original、rod-start7、rod-start9、rod-hold6、shifted-plus、hard；
严格失败原因为 rod-start9 接触 0 s、shifted-plus 接触 0.184 s、hard 外部
穿透 0.207370 mm。该结果低于 stiff teacher 的 `strict 4/6`，因此没有用 J2
轨迹新增 ESN，也没有解封 held-out。J2 只作为共同执行接口的负对照和可复核
数据源保留，不能写成 proposed 优势。
## Wrench 权重 6 固定消融（2026-09-28）

在 wrench1 的同一数据、reservoir、action7、物理预算和开发条件上，将
actor-visible wrench-norm loss weight 从 3 提高到 6，得到 checkpoint
`27fdd4fa1ce59cb2f2f5b0387e78ee38e92e4643d2ebc3298e8d9b80baecbaca`。独立
审计 `outputs/esn_office_joint_esn_stiff_wrench6_eval_20260927/eval_v1/` 已
核对 action/reservoir replay 与三项物理指标；结果 `task 6/6`、`strict 3/6`。
hard 穿透 `0.207528 mm` 仍越过 0.2 mm，rod-start9/shifted-plus 接触曝光
也未达门槛，故权重 6 不替代 wrench1，也不支持继续无依据扫同类权重。

## Wrench1 reservoir 记忆消融（2026-09-28）

当前最佳 wrench1 checkpoint 固定不变，仅在每次观测前清零 reservoir。为支持
该 canonical48D checkpoint，evaluator 做了最小兼容修复：只接受 stateful 48D
ESN，旧 45D policy 仍拒绝；首轮仿真前参数错误记录保留。六条件独立审计在
`outputs/esn_office_joint_esn_stiff_wrench_memory_reset2_eval_20260927/eval_v1/`，
动作/状态 replay 与三项物理子步指标均通过，结果为 task 3/6、strict 0/6。
连续记忆 wrench1 为 task 6/6、strict 4/6。这个匹配预算消融支持 reservoir
历史对当前跨条件任务完成的因果贡献，但不改变 hard 穿透和曝光失败，也不是
held-out 或硬件证据。

## 2026-09-28 输入来源与 sensors-only 匹配预算消融

字段来源审计归档于 `outputs/esn_office_input_provenance_audit_20260928/`。它确认
当前 actor 没有外部感知、接触真值、球状态、事件时间或阶段标签，但 48D 中的
`command/error/path_direction` 是 WBC/任务参考派生量，不是原始传感器。为把这
个边界变成可检验结果，按相同 teacher/DAgger2 数据、reservoir、wrench 权重、
action7 和执行器预算重训了一个只保留 q/dq/估计关节负载/估计 wrench 的 mask
模型（checkpoint SHA256
`f75ea7cd927fe51623c77d9698e851b1c924b27875eea5fb65b954c2b41a34c2`）。六开发
条件 task 为 `6/6`、strict 为 `3/6`，低于 full48 wrench1 的 `6/6`、`4/6`；
hard 穿透 `0.207805 mm`，shifted-plus 推杆曝光 `0.129 s`。动作/储备池重放和
三项物理指标独立审计通过。该结果说明内部参考派生字段对当前闭环有可测贡献，
但不引入外部信息；论文应明确使用“纯本体接口 + 内部参考”而非“只含传感器”。
它不改变安全门、held-out 封存或失败回合，也不构成真实硬件证据。
