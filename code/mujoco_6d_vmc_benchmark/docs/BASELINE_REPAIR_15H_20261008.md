# Baseline 修复与公平重评：15小时执行记录

状态：进行中。用户授权起点为2026-10-08 13:23:12 UTC（北京时间21:23），
截止2026-10-09 04:23:12 UTC（北京时间次日12:23）。
前10小时用于修复/验收/训练，23:23:12 UTC停止新训练回合派发，后5小时留给冻结、统一评测和审计。
这是持续长任务，没有创建定时任务；不得把未完成项或到达某个训练步数写成已解决。

服务器主根：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008/`。
开工远端 main `d5627f49a94651962bdb3f0c5a75c4b503c325ab`，
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。
原384回合、旧源码和四个历史暂停RL进程均保留。

## 固定协议

`PROTOCOL.json` SHA256 `ff4e3830fbbaaa40efee2d277c57b3859d19162e6ef286c971cbe22a3a44de71`。
物理模型仍为 `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`，
formal dt=5e-5、55s；几何、目标、公共规划、task/strict、本体48D actor输入及执行器限制不改。
新32训练/8开发/24最终条件来自相同扰动分布；最终条件在模型冻结前不用于学习或选择。
验收另有一条关闭主动扰动的诊断条件，保留静态MJB障碍；它不代表综合场景成功。

经典三类各24候选×2开发条件筛选，前2候选各做全部8开发条件确认。
不因为所有候选失败就宣称最优；阶段推进单列，防止把低力矩停滞解当作好控制器。
RL各族两seed，交互上限每seed20万且受时间截止约束；实际曝光、梯度、调参计算单列。
新纯RL不使用teacher标签；若后续注册示范辅助RL，必须另名列出，不伪装成纯RL。
最终沿用全部16方法身份，比较新冻结baseline与已有ESN/RNN/MLP等，并保留失败。

## 已实现与验证

1. 独立 `parameter_v1/` 保留 `controllers_legacy.py`，新修复adapter不覆盖原baseline分支或runtime。
   VMC的动作单位直接取实际安全配置，避免2/2/1.6倍解码偏差；不改共享teacher基类。
2. 阻抗改为投影式有界参考积分，保持4cm/0.2rad弹簧误差上限，保留边界切向运动；
   接入公共受限名义关节命令，再对力矩等效关节命令使用原速度/加速度限制及原力矩幅值/变化率限制。
   另外明确记录基于已知机器人frictionloss的平滑摩擦前馈和零空间姿态项。
   这仍是原生笛卡尔力矩阻抗，不声称与速度残差actor完全相同，也不是全局无源保证。
3. 本地及Spark契约探针通过：VMC物理单位误差约0；边界切向1s位移约33.91mm，
   位置/旋转界及力矩/命令限幅和变化率检查通过。代数探针不等于物理任务通过。
4. RL新训练runner记录每次梯度更新实际返回的loss/熵/温度等诊断和每步奖励项，保存完整恢复状态。
   当前官方update返回值未含Q曲线，不声称已记录Q。
   metric平滑成本改为实际物理子步力矩变化率平方积分，覆盖阻抗的原生力矩通道；
   原公共action过滤不变，额外奖励元数据不进入actor。另保存初始potential，避免首步奖励无法重放。

## 运行入口与当前限制

- `source_v1/`：最初控制器修复、注册及验收入口；`parameter_v1/`：独立控制律/先验。
- `source_v2/`：新增RL完整诊断与实际力矩平滑奖励，正在用于两个direct RL烟测。
- `source_v3/`：验收事件名称修正、经典任务共享8个物理租约；另2个槽给direct RL。
  实际新仿真总并发≤10，限定Spark高性能CPU核5–9/15–19，单线程、每worker3GiB、禁swap。
  当前用户的全算力授权用于本批资源扩展；本机仍保守使用1个模拟器和受限内存，避免历史OOM。
- `classical_acceptance_v2/`：六项新物理验收；`classical_screen/`：有限候选筛选。
- `rl/direct_metric_2026100811/initial/`、`rl/direct_office_task_2026100811/initial/`：
  各先跑5500交互步的烟测，跨过5000步warmup检查实际优化器更新、日志、checkpoint，再决定接续。

首批验收的注册误用了 `events=none`，而冻结评估器的合法关闭主动扰动模式为 `settle`。
六个55秒物理尝试结束后在最终汇总触发KeyError，未保存完整raw rollout；其日志/progress/execution
留在 `classical_acceptance/`，全部标为基础设施失败，不计算Task/Strict分数。
`ACCEPTANCE_EVENT_NAME_FIX.json`登记仅验收模式名称修正，独立新尝试在v2目录；
正式all-events场景不改。原注册协议和失败目录不覆盖。

14:10 UTC复核：六个验收重试均已完成，Task/Strict为0/6。较高刚度阻抗02/03进入retreat，
但物块在放置前掉落，最终XY偏差分别230.6/218.75mm，placement_hold为0；
RMSE分别18.744/18.211mm、外部穿透0.01934/0.01338mm，低误差和低穿透不能代替任务成功。
其余四项停在carry。验收保留静态障碍，不能称为无障碍空载试验。

两个direct RL先在4125步、3回合、0梯度处响应SIGUSR1安全保存。
独立实际SimbaV2更新探针发现optimizer返回嵌套字典，原标量日志转换不兼容；
在真实训练首次梯度前修复为递归数值日志，source_v4独立保存。
`RL_CONTRACT_TEST_V2.json`通过3次真实优化器更新、参数变化、输入不被修改及保存恢复一致性检查；
`RL_LOGGER_TYPE_FIX.json`保存接续依据。两个source_v4段从4125步接续到5500步，
不是重新采样同一批轨迹。14:10 UTC仍运行，尚未把合成探针当作闭环学习成绩。
经典筛选18/144回合已完成、8个派发记录运行中；实际物理并发受8租约限制。
运行中源码不就地修改，新变更按source版本隔离。

## 第二阶段：奖励边界与滑移诊断（14:35 UTC）

两组direct RL均完成5500交互/4回合/1002次实际梯度更新；这证明训练链能更新，不证明收敛。
独立从原始物理子步重算发现新力矩平滑奖励的首样本用了零作为前驱，
把初始化重力补偿误记为约1.22的额外成本。`source_v5`明确排除没有前驱的首个力矩差分；
其余全部物理差分、环境、门槛和actor不变。

两组各4回合的奖励/误差积分/动作一致性审计通过，证据位于
`rl/direct_{metric|office_task}_2026100811/reward_boundary_audit_rebuild_v2/REWARD_AUDIT.json`。
metric从头重建学习器，依次消费原来5500条完整off-policy转移及修正奖励，恢复归一化、
重放缓冲和1002次更新；没有重跑物理或删除失败。原1002次梯度另计为废弃诊断计算，
不能说新权重是旧权重的exact resume。office_task的该成本权重为0，奖励未变，
直接从原5500步checkpoint接续。两组现均在`continued_v5/`持续训练，截止仍受原协议限制。
第一次独立审计错误地把物理float64和learner float32逐位比较，失败记录保留；
v2按真实float32转换逐位验证，没有放宽误差阈值。

本地单线程/3GiB的只读运动学重建定位两项阻抗滑移：02/03在约9.80/8.92s时，
物块相对夹爪位移超过20mm；13.32/9.60s夹爪空闭。滑移期间存在物块与厚桌角的几何接触。
此处没有重建接触力，也不是新物理回合；记录的qpos和派生xpos有一个物理子步时间差，
最大约0.0124/0.0127mm，报告明确披露。不能据此把滑移唯一归因于某个增益。

新统一评测工具`evaluate_baseline_repair_20261008.py`要求先锁定16方法和源码，再读取final24；
按独立物理子步重算指标，区分基础设施缺失与真实物理失败。该工具尚未运行最终评测。
本机NVIDIA驱动当前不可用且本地环境缺少JAX/Flax，因此RL继续用已验证Spark运行时；
本机承担MuJoCo只读重建和代码检查，没有为追求占用率破坏稳定环境。

## 第三阶段：完整接续流程与筛选修正（15:05 UTC）

`sii-r15-continuation.service`已启动，实际源为`source_v7/`，这是本次有限长任务的接续进程，
不是定时任务。当前等待已有144经典筛选结束，不重复派发；随后执行前2×8确认，
冻结`parameter_v2`先验，启动另8个family/seed RL任务，与已有两个direct RL共10路。
`continuation_v1/SCHEDULE.json`登记22:00 UTC提前结束新训练并在回合边界保存，
为10个RL模型各8开发条件、最终16×24和审计留出时间；原15小时截止不延长。
RL使用截止前各seed最新完整checkpoint，再按同一8开发条件选择seed；所有seed结果与预算保留。
这不是多个训练seed平均的最终成功率，不能当作跨训练seed稳定性结论。

验收已说明空手retreat会误导仅基于机械臂stage的筛选。因此，在开发阶段新增明确排序修正：
仍优先strict/task/full，再按最坏及累计物块最终3D放置距离、机械臂stage、穿透、RMSE、峰矩排序。
目标取每回合原`placement_destination`，仅用于开发评价，不进入actor、不改任务gate。
原144筛选的排序/全部失败不覆盖；新的screen/confirmation排序另存
`CLASSICAL_SCREEN_PAYLOAD_RANK.json`及`CLASSICAL_CONFIRMATION_PAYLOAD_RANK.json`，生成后才可作为选择证据。
此修正由已公开开发诊断驱动，不冒称最初预注册，也没有读取final24。
本地及Spark测试通过：锁定前不读保留条件、禁止覆盖锁、缺少RL adapter不能默认为teacher/zero、
严格成功优先、不能用空手retreat冒充物块推进。

新增5维参数阻抗RL的真实优化器/保存恢复探针通过；7维已在此前验证。
VMC完整1375步动作、虚拟offset/velocity、参数和能量状态重放最大误差为0，
仅使用已记录本体48D和原安全单位。先前两次重放诊断分别用了panel默认0.16而非office0.32单位、
漏设脚本导入路径，原失败日志保留；修正的是审计入口，实际仿真控制器不变。
六项验收的独立物理子步三指标/Task/Strict重算均一致，证据位于`acceptance_independent_audit/`。

## 第四阶段：内存压力预检与日志存储（15:24 UTC）

实际读取两个direct RL cgroup：`memory.peak`到达3221225472字节，`memory.events.max`
约1200–1400，oom/oom_kill均0。不能把systemd摘要中不可信的512KiB“peak”作为工作集证据。
当前RL尚能运行，但原生阻抗额外累积每次伺服回调的两份Python数组列表，接入RL需复核内存。
新增`DiskArrayLog`顺序保存完整float64行，最终NPZ字段和数值不变，临时磁盘页可在限额下回收。
本地和Spark验证10000行保存/恢复逐位一致，VMC单位/阻抗位置旋转/命令和力矩限幅测试仍通过。
这只是存储实现变化，不是新控制律，也没有放宽3GiB限制。

只在原接续进程尚未派发新物理回合时停止它，并保存`CONTINUATION_MEMORY_PREFLIGHT.json`；
现有screen和两个direct RL未停止。新`sii-r15-continuation-v2.service`/`source_v8`已接续等待，
将把同样控制律、磁盘日志的版本用于后续`parameter_v2`；旧参数源和运行中源码保持原样。
`continuation_v1`历史状态已明确标为superseded_before_new_physics_dispatch，不能同时重启它。
后续5维RL完整物理回合的实际内存表现仍待观察，代数探针不替代运行验收。

15:24 UTC快照：screen116/144完成，无基础设施失败；两个direct RL约28000/29000交互，
仍无训练任务成功，分别已有6/12个本接续段短回合；全部保留。最终条件未打开。

## 第五阶段：完整筛选与执行链检查（15:54 UTC）

144/144经典筛选完成，无基础设施失败，Task/Strict均0/144；已自动进入48回合确认，
当前8/48完成且仍无Task成功。物块距离优先的前两名为VMC09/22、导纳17/08、阻抗00/20；
全部候选及原排序保留。尚不能说经典控制性能已修好。

新增只读训练诊断`inspect_repair_training_20261008.py`，服务器证据`TRAINING_DIAGNOSTIC_01.json`：
metric/task两个direct seed1快照约36500/37250交互；本接续段26/36个完整记录回合均Task/Strict失败，
其中6/14条因原2mm全局穿透中止线早停。原始actor、控制器action、公共过滤action和48D观测形状/
有限性/归档hash核对通过，optimizer记录未发现非有限值。主要停approach；高过滤触发比例只是
描述性信号，不能单独证明算法错误或收敛。两个实际cgroup的OOM/oom_kill仍为0，内存压力仍存在。

`audit_repair_parameter_trace_20261008.py`独立重放阻抗02的1375次参数shield，记录字段误差均0；
完整13750次原生伺服记录的等效速度上限0.835673rad/s、等效加速度上限8.000000rad/s²、
输出力矩slew最大比0.998404、弹簧位置误差最大40mm，均符合原限制。
这里是**250Hz伺服回调，不是20kHz物理子步**；更正此前对日志频率的描述。
磁盘遥测改动是预防性存储调整，并未发现旧原生日志已经导致OOM的证据；不能把它说成已证实的OOM修复。
此审计采用记录的虚拟状态输入重放shield，不冒称独立重建机器人动力学或全局无源性。
证据`NATIVE_PARAMETER_AUDIT_01.json`与原始轨迹都在同一服务器run根，实际物理速度/力矩另由子步审计评价。

GitHub阶段四已核验main `0e8e2bd9aff78ad936e5ef670a0ecf81f94ffeae`，baseline仍为
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。确认和两组RL稳定运行，parameter_v2/
其余8组训练尚未开始，final24未读，未修改环境、门槛、控制器或正在运行源码。

## 未完成

完整物理验收和独立动作/子步审计、经典筛选/确认、RL收敛与多seed充分性、
新最终模型锁定、全方法新24条件矩阵及论文级结论均尚未完成。
最终结果不以ESN获胜为条件；baseline修好后优于ESN也照实报告。
