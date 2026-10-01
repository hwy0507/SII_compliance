# 本周 baseline 进展与三维对比（2026-09-23）

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
