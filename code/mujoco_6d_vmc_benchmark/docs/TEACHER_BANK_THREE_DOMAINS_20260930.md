# 三类 teacher 数据与经典 baseline：10 小时工作记录

用户授权窗口：2026-09-30 03:48:16—13:48:16 UTC（北京时间 11:48:16—21:48:16）。
截止时停止派发新仿真，已开始的回合允许完整保存；不能把场景定义数当成成功示范数。
本轮新增的是训练域，不修改冻结综合测试环境、原任务 gate、执行器或 actor 输入。

## 11:10 UTC：完整五候选检查点与资产覆盖更正

10:40完整c00–c04共135回合，23录取/112失败，逐回合有归档凭据。厚角VMC/导纳/阻抗
为4/15、0/15、7/15；短撞9/15、2/15、1/15；持续推碰均0/15。它们是跨参数搜索计数。
短撞VMC c04同参数3/3，c05截至11:08已0/3；最后候选仍继续原固定预算，不据此改选参
规则。当前尚未锁定bank，validation/collection/新ESN尚未开始，VMC唯一合格训练fixture
仍厚角2/短撞3/持续推碰0，远未采满每类1000条示范。

发现旧资产清单只有85个Panda文件，遗漏实际FR3本体；此前“全部实际资产核验”表述更正。
完整133文件已核验共享，本机冻结源码真实初始化9/9 MJB逐字节复现（零积分）；单用导出
XML重编译0/9一致，定位质量默认值与运行时mask没有完整回写。原源/plan和稳定作业未改。
Spark首个source静态重建不一致，补充动态采集保持阻断，不混入公平比较，详见
[资产复现更正](TEACHER_BANK_ASSET_REPRODUCTION_CORRECTION_20260930.md)。
静态审计及135检查点112文件已核验到服务器runs/main/teacher_bank_review_checkpoint_20260930_1104/evidence/。
新增公平展示器将task/strict/接触曝光/录取分列；只对同fixture三方法完整同长且三指标全部
可核对的共同集合聚合，缺项不单独丢弃某一方法。未锁定时拒绝给固定策略成绩。最后版本
11测试通过；Spark driver 8测试通过，但并未启动。仍只报告dt=1e-4开发结果。

## 09:40 UTC：四个候选108回合，短撞同参数3/3

c00至c03完成108回合，17录取/91失败；全部有逐回合核验归档凭据，c04第一回合运行。
共同完整候选前缀[0,1,2,3]，每方法/类别12条。厚角VMC/导纳/阻抗为3/12、0/12、6/12；
短撞6/12、1/12、1/12；持续推碰均0/12。此表是搜索预算统计，非单策略成功率。

VMC短撞c03同一参数3/3（原c00为2/3），六条配对轨迹的三指标独立重算、冻结VMC/filter/
状态重放和源/配置/模型hash通过。球形条件RMSE64.667→37.662mm，峰矩47.935→45.004Nm，
但峰力1793→2221N、外部穿透0.11744→0.18863mm，不能声称全面安全改善。穿透仅存档
元数据核对，未独立动力学重算；详见[短撞c03复核](TEACHER_BANK_SHORT_C03_REVIEW_20260930.md)。
其证据及新终态工具/验收964文件已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0913/evidence/`。

终态工具11项测试通过，将保存JSON字节快照、独立重建选参/锁定/后续固定参数一致性和
元数据归档缺口；不重算所有原始轨迹或重新核验服务器receipt。预算仍6候选，银行未锁定，
validation/collection/新ESN仍0。VMC合格唯一训练fixture仍2/3/0，未达到每类1000。

## 08:40 UTC：初始81回合完整，进入真正BO阶段

三个初始候选c00/c01/c02共81回合：10录取/71失败。厚角VMC/导纳/阻抗为2/9、0/9、4/9，
短撞为3/9、0/9、1/9，持续推碰全部0/9；属于跨参数搜索统计，不能解释为单控制器成功率。
首个BO厚角VMC c03后来完成1/3，未超过c01的2/3。参数银行尚未锁定，验证/collection为0。
训练输入和初始分数独立汇总通过，冻结BO同实现重放参数误差0。首次使用可行性LCB搜索，
非性能EI，约束仍是离散失败代理；详见[首次BO复核](TEACHER_BANK_FIRST_BO_REVIEW_20260930.md)。
81点三指标图与复核44文件已SHA核验共享至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/`。
稳定v10服务继续原固定预算。尚未完成各类1000条合格示范、新ESN或正式跨条件验证。
下文各时间点保留其历史状态，不以早期“0条”覆盖本检查点。

## 固定的研究目标

| 类别 | 训练配置数 | 独立验证配置数 | 训练域变化 |
|---|---:|---:|---|
| 被动厚桌角 | 1000 | 100 | 连成一体的厚边缘、水平角度、位置、宽厚、摩擦、负载 |
| 主动短时碰撞 | 1000 | 100 | 球/椭球/胶囊体，质量、尺度、水平入射角、速度、发射时间 |
| 主动持续接触 | 1000 | 100 | 人手/棍/平头推板，水平角度、推程、驱动力上限、持续时间、质量/尺寸 |

每类采用 Latin hypercube，split 和 seed 在调参前冻结。被动碰撞的实际接触时间、峰值力
是闭环结果，不声称直接采样了“被动撞击力”。当前角度覆盖是水平旋转，不声称已覆盖任意
三维来向。短时物体发射前固定在初始化位置，发射后为自由物理体；发射目标在运行前由
归档 nominal 轨迹离线确定，不追踪本回合实际机器人。该假设不进入 actor。

物理配置 hash 仅含真正作用于该类场景的字段；每条仍须验证编译模型 hash、初始几何、实际
接触及任务完整执行，不能仅凭不同 seed/hash 认定数据有效。未击中、初态非法、接触不足、
失败控制与证据损坏分别保留。

## 三种方法与公平预算

- VMC：既是纯 ESN 的 teacher 数据生成器，也是独立 model-based baseline。
- 导纳：复用 ReferenceAdmittance，以估计外力驱动 M-D-K 参考偏移及 WBC residual。
- 阻抗：复用 MovingEquilibrium，执行 `bias + Jᵀ(K e + D(v_ref-v))`，经过相同力矩限幅／
  变化率限制；不把它改名成 VMC，也不把它的零 action7 当成 ESN 的有效动作标签。

初始计划每方法每类别16个候选×3个anchor。v4完整回合实测98.3秒计算，另需归档；
在尚未开始参数优化前，将v5固定为每方法每类别6个候选×3个anchor，3个初始点＋3个
约束GP贝叶斯候选，共162回合。先寻找任务/接触/物理可行性，再优化性能；不解封旧保留集。
VMC/导纳为 7 维，阻抗为真实 5 维，固定其仅用于阻尼参数化的质量/惯量，避免搜索冗余维度。
同预算指实际模拟回合上限相同，不强求不同物理方法有相同参数维度。
搜索按轮次、类别和方法交错派发，防止截止时间前只跑了某一种方法。

参数选定后每类每方法锁定一个候选，在相同 1000 个训练环境执行；VMC 轨迹接受完整序列筛选，
另两方法保留配对 baseline 结果。当前不做 ESN 训练。某经典法无可行候选不阻止其他方法，
选其约束优先的最好已观察候选并明确标注不可行；任何失败轨迹不能成为ESN标签。
验证集只在候选锁定后运行，不回流优化。为避免1000环境长采集挤掉全部验证，v5先执行
每类预定索引0/1/11共9个验证环境×3方法，然后按剩余窗口采集；其余97/类仍未运行。
搜索anchor在优化开始前修正为0/337/671，使球/椭球/胶囊和手/杆/推板都被覆盖；旧0/333/666
对短撞的模3形状索引重复，不能称作三种物体覆盖。验证索引独立固定，不读取结果选索引。

## 筛选与审计

首先保留原 task/strict、外部穿透 ≤0.2 mm、实际力矩幅值与 4 ms servo 变化率要求。
额外训练曝光条件：厚桌角仅统计 face/连接边缘在 lift/carry 的承载接触与净上抬，排除最终
放置桌面支撑；手推需持续接触中的有限让位；杆推需接触中切向移动且在撤回前脱离。
这些是新训练数据的纳入条件，不改原正式测试 gate。接触真值只供评估，不进入 actor。

v5可行候选采用分数：`RMSE/0.05 + 0.3*max_joint_torque_ratio + 0.1*retreat_start/55`。
原v4 action_delta项在搜索前移除：阻抗直接输出力矩，action7恒零，不能据此获得平滑优势。
动作差分仍报告为方法内部诊断。RMSE 为完整物理时间的 waypoint 误差；retreat_start 是效率
代理，不能称作严格任务完成时间。峰值速度仅报告，不正向奖励速度尖峰，不新造正式速度 gate。

保留 canonical48 观察、原始 action、过滤后 action7、物理 twist/WBC scale、实际执行力矩、
速度/误差、teacher 内部状态、接触曝光记录、源码/配置/seed/模型 hash。VMC 和 filter 独立
重放；过滤后 action7 再过独立 reset filter 必须重现相同命令。NaN、错误形状、缺少物理子步、
不连续时间必须拒绝。明确物理 abort 的短回合保留为失败，不当作管线坏掉。
导纳重放目前仅覆盖 M-D-K 与动作归一化，不声称完整 FK/WBC 独立复算；阻抗重放参考积分、
记录的 Jacobian 投影和共享 limiter，并在验证单位力矩传动后将每个servo输出与其持有区间的
物理qfrc_actuator逐项对照，不声称重放了整个MuJoCo。三方法配对结束须验证相同MJB hash。

## 反馈输入审计与任务执行器边界

对冻结v10/source的只读核查确认：canonical48为q[0:7]、dq[7:14]、名义twist[14:20]、
位姿误差[20:26]、名义减实际twist[26:32]、估计关节负载[32:39]、估计wrench[39:45]和
指令路径方向[45:48]。未直接拼入接触真值、球状态、事件时间、视觉/距离或stage编号。
JointLoadObserver用dq有限差分、质量矩阵/bias/passive、实际电机力矩和摩擦补偿计算残差；
不使用qacc/contact/qfrc_constraint。VMC实际只读取估计wrench；导纳使用上述负载、位姿误差、
名义twist及机器人FK/J；阻抗在servo使用机器人位姿/twist/J及名义指令。模型/传感器理想化，
尚无真实硬件噪声或标定验证。

**“纯本体”仅指反馈控制器的外界感知来源，不能推广成整套系统无真值辅助。**
`scripts/validate_office_apparatus_v5_20260917.py:349`的corner_release_ok读取真实物块支撑
接触和物块速度；`scripts/office_task_v4_20260917.py:117`接受估计负载变化或该标志作为
释放条件，进而影响stage、夹爪和后续名义参考。这是一条真实影响闭环行为的间接路径，
不能仅称不影响控制的评估记账。三个方法共享它；本轮不修改冻结执行协议，但也不声称已完成
无需仿真真值辅助的真实机器人自主放置。上述路径相对已核验服务器
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/source/`。

## 执行与恢复

本机一个 MuJoCo 子进程、1 线程、MemoryMax=3 GiB、MemorySwapMax=0。子 agent 并行负责
实现、静态审查与小型测试，不能未经协调另开仿真。冻结 Python/MuJoCo 3.11；先查宿主进程
与 systemd（沙箱 ps 可能只看见自己的 PID namespace）。

入口：`tools/teacher_bank_campaign_20260930.py prepare|pilot|run [--archive]`。
每条 run 单独 execution.json、request、raw/audit；源码不可覆盖。归档先写 incoming，逐文件
SHA256 核验再发布到服务器 `runs/main/<campaign-name>/`。传输未完成不称已共享。
长时任务 heartbeat `teacher-10` 每 20 分钟检查，计算截止 13:48:16 UTC；额外保留至14:28:16
仅用于最后回合的归档、审计和交付，不增加计算窗口。服务和 campaign lock
避免重复启动。实际可完成量由 pilot 测得吞吐决定，10 小时优先级高于最大回合数上限。

## 07:35 UTC：54回合完成，第三组初始参数运行中

c00/c01两个候选均完成三类×三方法×三anchor，所有模型配对和history检查通过。
共8条录取、46条失败，54条均有逐文件核验归档凭据；VMC合格唯一训练fixture为厚角2、短撞3、
持续推碰0，正式collection均0。**短撞的三个合格fixture来自不同候选，不能拼成单控制器3/3。**
c00短撞VMC2/3；c01球形anchor0通过，但337/671的strict失败，故该候选仅1/3。
c01厚角VMC2/3、导纳0/3、阻抗0/3；c01持续推碰三方法均0/3。所有失败继续保留。
低力矩失败不能仅凭三指标较低晋级；尚未进入BO候选阶段，也未锁定参数或做独立验证。

相同v10服务已进入c02，缓存受限时正常回收，OOM/oom_kill均0；没有新增本机仿真或重启。
完整54回合状态36文件已核验归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0736/evidence/`，
其下`outputs/teacher_bank_reports_20260930/v10_c01_complete_0735.{json,md}`为本检查点。
原13:48:16 UTC新回合派发截止、6候选固定预算及未完成目标均保持不变。

## 配对三指标图表与复用入口

新增`tools/plot_teacher_bank_search_20260930.py`读取已保存status JSON，只纳入各类别三方法
共同完整候选前缀。逐回合audit.json须与status保存的SHA匹配，fixture/MJB、完整anchor集合、
录取标记再次核对；缺失或被改写的证据会报错，不静默删除该点。失败回合全部绘出，partial
与未配对回合另计数。图表不选择最佳候选、不重算物理子步，也不把训练搜索当成独立验证。

首个例图来自06:32快照：27点（5录取/22失败），排除并注明1条正在运行的c01回合。
三类别各有RMSE—峰值执行器力矩和RMSE—峰值末端速度两幅图，方法固定颜色、失败与录取
使用不同标记。RMSE标签明确为**stage-waypoint tracking**，不是平滑全局路径误差，也不暗示
失败或未来abort回合完成了完整任务。所有点仍按实际记录值展示，速度不正向奖励。

4项证据选择/哈希篡改/配对/不覆盖校验通过；PNG已视觉检查。脚本、测试、来源status、
完整点JSON、PNG/PDF共42份归档文件逐文件核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0717/evidence/`。
其下图表路径为`outputs/teacher_bank_plots_20260930/v10_c00_complete_0632_v3/`。
PNG SHA=`bf088ec34ac28340a6c19535654dc1d4f4d80885c63926e22643f2e1c9072824`；
points JSON SHA=`507cae91f03b65b2335c0c4fde6b08d09295dd46e1b1a1a1816f4f919b514c8e`。
随后新增可选`--campaign-root`供服务器复用，输出同时保留原`source_campaign_root`和实际
读取的`campaign_root`，不改历史status或放松SHA/模型配对核验。包括“原目录消失后的搬移复用”
在内5项测试通过；新版脚本/测试另核验归档到同一runs/main父目录的
`teacher_bank_review_checkpoint_20260930_0722/evidence/`，脚本SHA为
`705024dab83dec409d8c0c32f043c2709abf92dca0aa3ab468da234243785425`。
v3图片没有重写，仍由plot_points.json记载的上一版绘图脚本产生。
服务器复画时显式传入
`--campaign-root /home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10`。
绘图从本地运行缓存读取已完成audit，未访问正在写入的回合；目标目录须全新且位于原run外：

```bash
ulimit -v 2097152
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MPLCONFIGDIR=/tmp/sii_teacher_plot_mpl \
  /home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python \
  tools/plot_teacher_bank_search_20260930.py \
  --report outputs/teacher_bank_reports_20260930/v10_c00_complete_0632.json \
  --output outputs/teacher_bank_plots_20260930/c00_recomputed_new_directory
```

## 06:32 UTC：首轮27回合完整配对

三个类别均有c00共同完整候选前缀；三方法各9条，模型hash配对及搜索历史验证通过。
录取数按厚角/短撞/持续推碰分别为VMC 0/2/0、导纳0/0/0、阻抗2/1/0，分母均为每类别3。
共5录取、22失败，27条均有已核验归档凭据；已进入c01厚角VMC，银行仍暂定。
这仍是第一组初始参数，不是优化完成结果；没有独立验证或正式collection。

人手anchor0另做完整550000子步独立重建，段数据差≤1.22e-13且原hash全部一致：VMC
最长连续段1.2516s、同段让位9.09595mm，距1cm差0.90405mm；导纳最长.1838s/1.71166mm；
阻抗最长.0074s，单段最大让位.03322mm来自另一段。VMC/导纳宏观位移约27mm横跨间断，
不能替代连续接触筛选。详见[人推复核](TEACHER_BANK_PERSON_ANCHOR_REVIEW_20260930.md)。
源码/JSON/首轮状态38文件已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
已提交f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985完整源码2623文件另经hash/大小/权限核验共享至
同一服务器`/home/arm1/sii_shared/SII_compliance/source/f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985/`；
tar SHA=`274e159481c6f9545ce705b0bcfee90455f0c8caf7433aa7b8357d4a0f931b11`。

## 06:18 UTC：短撞首轮配对与接触载荷复核

v10累计完成21条搜索回合，5条eligible、16条物理/任务/曝光失败；另1条持续推碰导纳运行中。
这里eligible指满足现有开发筛选，不等于真实部署安全。原始21条均有逐文件核验归档凭据。
固定初始候选c00的完整配对如下（所有失败仍纳入统计）：

| 类别 | VMC | 导纳 | 阻抗 | 每方法完整anchor数 |
|---|---:|---:|---:|---:|
| 厚桌角 | 0/3 | 0/3 | 2/3 | 3 |
| 短时碰撞 | 2/3 | 0/3 | 1/3 | 3 |

VMC短撞337/671的独立子步指标、文件hash与冻结runner重放均复核通过，见
[首两条成功轨迹审计](TEACHER_BANK_V10_FIRST_SEARCH_SUCCESS_AUDIT_20260930.md)。
这是初始reference参数，不是BO改善；正式collection仍0，各类1000条合格示范尚未完成。
两条VMC球撞峰力1368/1350 N，阻抗合格短撞671也有2077 N峰力，不能以电机峰矩低推断碰撞力低，
也不能声称VMC独占成功。冲击模型/步长敏感性与硬件结构载荷尚未验证，未因此修改任何gate。
导纳671和阻抗337短撞虽task通过，ball_rebound=false导致strict失败；应与穿透失败区分。
持续推碰目前仅VMC完成3条、均不合格，尚不能三方法配对；人手/杆两条任务本身通过，
但曝光条件失败，推板还存在任务/strict失败。缺少连续让位证据不等于完全没有宏观让位。

新增status辅助表先核验rollout.json原audit hash，再提取既有接触事件、冲量与布尔失败字段；
这部分明确不是独立物理复算，不更改主指标或录取结论。19项status测试通过。
本次状态及status源码/测试38文件已核验至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0621/evidence/`，
对应`outputs/teacher_bank_reports_20260930/v10_0617.{json,md}`。
首两条VMC复核40文件已核验至同一runs/main父目录的
`teacher_bank_review_checkpoint_20260930_0603/evidence/`。
冻结v10服务继续运行，未热更新；本机单环境/1线程/3GiB，原13:48:16 UTC派发截止不变。

## 05:49 UTC：首个完整参数配对与失败机制

v10完成首个厚桌角候选c00，每方法三个固定anchor，配对模型hash一致：

| 方法 | 录取数/3 | RMSE中位数 mm | 三条最大峰矩 Nm | 三条最大峰速 m/s |
|---|---:|---:|---:|---:|
| VMC | 0/3 | 36.140 | 48.399 | 0.061602 |
| 导纳 | 0/3 | 39.888 | 50.927 | 0.064488 |
| 阻抗 | 2/3 | 30.232 | 46.595 | 0.161947 |

上述统计包含失败，只有该类别的共同完整候选前缀[0]可比较；不是独立验证成功率。
银行仍为provisional，短撞/持续推碰的相同预算配对未完成。v10服务继续运行，没有改动快照。

离线复核v8九条pilot的所有原文件hash和三项子步指标后，区分出以下机制：球撞VMC未立即
掉块，42.32s边缘部分支撑释放后滑落；导纳放置静差/漂移，阻抗carry慢收敛超时。
VMC约6s的145mm误差跳变主要是lift→carry参考waypoint切换，不是球撞导致145mm末端位移。
人推VMC/导纳跨多个接触片段有约27mm宏观同向位移，但force>0.05N判据存在大量0.1ms
间隙；不能写“完全不会让位”，也不能据4ms宏观诊断追认连续接触或schema2通过。
没有无球/无推配对，不能把相关轨迹机制称作唯一因果。详见
[pilot失败归因](TEACHER_BANK_PILOT_FAILURE_CAUSES_20260930.md)。冻结gate保持原样。

新增41文件核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`，
含失败归因JSON/脚本/报告、v10_0549预算报告及当前只读status源码。
另将已提交源码7423d5e的2618个文件逐项核验并共享到：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7423d5ef94df05470ba14188a983f92fc51846b1/`。
git archive SHA256为`47399ebcc9e6463d81f001a3112642ff362e45e9ee46f046efff37229b8cf13e`。
Git archive的uid/gid与接收账户不同，直接tar比较先被拒绝；未发布未核验副本。随后逐文件
比较SHA/大小/权限和完整文件集合通过才发布，uid/gid按接收账户保留。

## 05:23—05:29 UTC 接续核对：pilot 与搜索前审查

远端 main=`8dec129deecf2b769e765c5d91a54a64140a22a7`，
baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`，已读取两分支更新。
baseline 的 SimbaV2 campaign_03 正在 Spark 四路训练，本任务不占其仿真资源。

已完成：v6主动类别六条完整pilot及归档；v5阻抗旧raw独立复审及归档；
v8上方掌翼厚边缘18个跨类初态检查。v8被动三方法结果如下，均为dt=1e-4开发回合：

| 方法 | task | 训练接触筛选 | 可纳入 | RMSE mm | 峰矩 Nm | 峰速 m/s |
|---|---|---|---|---:|---:|---:|
| VMC | true | false | false | 36.140 | 48.160 | 0.06160 |
| 导纳 | false | true | false | 39.900 | 50.927 | 0.06160 |
| 阻抗 | true | true | true | 47.988 | 45.612 | 0.15314 |

阻抗只是一个训练fixture通过，不是跨条件结果，更不是ESN标签。其累计接触12.8117s、
18840段接触run，只有一个5ms run以0.231mm上抬通过0.1mm曝光门槛，不能称平顺明显蹭过。
VMC有真实碰边但接触中上抬仅0.0866mm，按原已注册训练筛选拒绝，不能据任务成功晋级。
独立复算阻抗550000物理子步的三指标，与原audit差均为0。

v8于05:23:21 UTC完整保存九条pilot后，被预定阶段边界锁阻止进入旧搜索。
日志末尾BlockingIOError是这次计划内停止，不是物理失败；九条execution均完成，九条归档
receipt已核验。没有向仿真子进程发送停止信号或改写冻结源码。v9已准备但未执行。

运行中：`teacher-bank-search-v10-20260930.service`，05:29:05 UTC启动，直接进入搜索。
源码210文件、metadata2文件、source_inputs3文件已逐文件核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/`。
冻结入口为该目录`source/tools/teacher_bank_campaign_20260930.py`，实际计算主机airpig；
本地相同相对目录是工作缓存。plan记录未提交源码快照hash及base commit，不能当作干净commit。

v10统一修正候选排序：失败anchor数最少优先，其次最大失败标签数，最后原平均评分。
BO约束为失败anchor数加小于0.25的标签严重度次项，全部通过为-1；它是离散失败代理，
不是连续物理超限量。评分中峰矩项是各关节峰矩/该关节限值的最大比值，不等于原始Nm排序。
原始Nm/末端峰速仍完整报告，不正向奖励速度尖峰，也不宣称存在额外实测速率硬门槛。
阻抗内部参考以250Hz积分，VMC/导纳状态25Hz、共享执行250Hz，这是现有控制实现差异。

每次新仿真前核验实际机器人资产85文件，执行记录保留核验时间/hash；同fixture的模型
hash跨方法、候选和阶段一致。审计还绑定曝光记录到完整physics时间轴，schema2人手必须
逐子步对齐，观察q/dq与前后状态对齐。九条旧pilot只读关联复核全部通过，没有改写原audit。
新搜索开始前73项测试通过。数值nonfinite仍会触发审计异常并停管线待诊断；不把缺失或
损坏的指标伪造为BO观察，也不能将算法物理发散一律解释成外部基础设施故障。

截止可能发生在某配对block中间，届时实际预算不完全相等；正式比较只用共同完整候选前缀，
partial结果另外报告。`teacher_bank.json`搜索期间只是暂定选择；完整搜索与
`anchor_feasibility.json`核验后才称锁定，验证结果不回流调参。

人手曝光schema2已完成并通过小型反例测试：只计施推/保持期间连续接触中的沿推力方向位移，
拒绝朝推手移动、纯切向移动和撤回后的位移；保留物理子步原始证据。旧schema1人手数据不
追认为schema2通过，原审计不改写。详见[曝光修正](TEACHER_BANK_PERSON_EXPOSURE_SCHEMA2_20260930.md)。
冻结综合环境、正式gate及执行器限制没有修改。

已核验服务器产物（主机均为arm1@192.168.31.70）：

- `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v6/`：源码和六条主动pilot。
- `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v8/`：源码、metadata与已完成pilot逐条归档。
- `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_reaudit_v5_20260930/impedance/`：旧raw复审、复审源码与metadata。
- `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_20260930/menagerie/`：实际使用的Panda XML/mesh，85文件SHA256核验；不称已归档其他机器人模型。
- `/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0527/evidence/`：34文件，含最新几何审计、v6/v8完成汇总和v8计划停止证据；已核验。

未完成：搜索、锁定候选的独立验证、3000个训练配置全部执行、各类1000条合格VMC轨迹、
新ESN蒸馏和正式验证。当前合格新VMC轨迹为0。3300配置定义不等于3300示范或成功回合。

## 早期初始化与审查记录（历史状态）

已完成：3300 个可复现配置；三方法接入；贝叶斯搜索/单进程恢复框架；动作、子步与曝光审计。
新测试54项通过；全部是小型正确性测试，不能代替动态表现。
独立审查修复了滤后标签未校验、NaN误差被吞、子步缺失仍晋级、合法
物理提前失败使管线停机，以及 numpy 配置在回合结束时不能 JSON 序列化的问题。

旧初始快照保留：`outputs/teacher_bank_three_domains_20260930/` 在物理运行前停止。
v2 首个被动场景被初态审计拒绝：新增连接边缘与机器人初态穿透 1.6–7.8 mm；没有把它算作
有效轨迹。其失败及源码已核验归档：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
其中 `source/tools/` 和 `source/scripts/` 是该轮真实代码；`pilot/passive_corner/vmc/` 是失败记录。
v2 源码目录还误包含历史 scripts/outputs，后续快照已排除；未删除历史数据。

连接结构已改为绕过初始手爪的两段刚性连接，42 个不同训练 fixture 初态审计通过（未积分）。
见 [几何预检](TEACHER_BANK_GEOMETRY_PREFLIGHT_20260930.md)，不由初态通过推断动态成功。
v4首VMC完整回合：task/旧strict通过，但真实face曝光缺失，未入库。RMSE36.149mm、
峰矩48.367Nm、峰速0.06160m/s。其导纳在物理运行前暴露字符串adapter误匹配hybrid_teacher，
已用精确目标替换及真实源码静态测试修复，失败原样保留。
v4 的 source（206 文件）与 metadata（2 文件）已逐项 SHA256 核验到：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v4/`。
v4以上两条记录均已核验归档。原face偏离payload上抬扫掠域至少26.16mm；旧corner记录同样
不构成face上抬接触成功证据，详见 [曝光诊断](TEACHER_BANK_CORNER_EXPOSURE_DIAGNOSIS_20260930.md)。

已停止：v5 pilot，服务`teacher-bank-pilot-v5-20260930.service`，04:30:24 UTC启动。
新训练域face按转角后的右边界和顶部对齐，六个代表fixture初态通过；其首VMC动态结果
仍失败：face先挡住下降手掌，全程停在align，不能进入teacher库。导纳、阻抗也停在align。
阻抗后置审计因NPZ反复解压保留view触发3GiB限制；修复一次读列后，用原550000子步独立
复审4.39s完成，13750条servo命令→实际力矩误差0，仍拒绝任务失败；未改原execution记录。
修复并不修改仿真，旧失败完整保留。后续几何修订须另存版本，不覆盖这次负结果。
v5源码209文件、metadata2文件已核验到
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v5/`。
运行中数据完成后逐条核验归档，尚不声称全部已共享。
当前运行：`teacher-bank-active-v6-20260930.service`，只跑两个主动类别×三方法的完整pilot。
厚桌角上沿的新几何仍在离线研究，未据初态通过宣称可完成任务。
未完成：有效动态 pilot、完整调参、3000 条训练环境执行及各类 1000 条有效 teacher 配额、
独立验证、ESN 蒸馏。当前成功采集数为 0，不能由“3300 个定义”推断成功率。
v3 仅准备、未运行，几何修正通过预检后使用新冻结快照继续。

协作复核：04:15 UTC 远端 main 仍为 `38caf3152282df4963435bb65c11c93a1e4fffa5`，
baseline 已更新为 `5bc21d8d19eaf60691f561f0ad9dd4409749e667`；已读其新日志。
该分支在 Spark 做独立 SimbaV2 奖励训练，冻结其训练布局和配对种子，并修复旧 RL 额外
残差包络/错误载荷指标。此处不合并其分支、不占用其服务器仿真槽位，也不把新训练域
定义当作 baseline 已完成的最终共同评估。
