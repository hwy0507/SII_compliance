# Critic 时钟候选、六轮训练复核与 GPU 恢复（2026-10-26）

用户再次指出四张 GPU 空闲后，实际检查确认旧八个初始化重复实验均已正常结束。没有重启旧进程。
当前四卡运行十二个独立 critic 配对任务，另有四个在线入口完整回合预检；全部独立目录、有限预算。
这不是正式策略已收敛，也不能把辅助更新计作在线策略训练。Goal 继续。

## 最新六轮训练结果

独立复核 `fresh_cycle05_scientific_review_v1/REVIEW.json`，核对780个源码文件、120条末轮终端/模型/条件/参考规划/reward/replay、四份 checkpoint。
所有末轮回合55s；这是训练过程中策略变化的回合统计，不是冻结策略 acceptance，也不是原始子步重新审计。
诊断图已目视核验，Q loss 与目标Q整体继续增长，不能因回合 reward 近似重复而称收敛。

| 方法 | steps | Task | Strict | 末轮均值reward | 最后1000次Q loss | replay终端MAE |
|---|---:|---:|---:|---:|---:|---:|
| direct | 247500 | 0/30 | 0/30 | -32.965075 | 390.695 | 247.853 |
| impedance | 246984 | 18/30 | 17/30 | -2.274513 | 10690.257 | 817.922 |
| admittance | 247500 | 13/30 | 13/30 | -10.443821 | 2995.150 | 622.330 |
| vmc | 247500 | 17/30 | 16/30 | -4.544566 | 3487.720 | 847.340 |

四路被动条件均0/10。Impedance短0600穿透0.230442318mm，VMC同条件0.214652339mm，都超过原0.2mm Strict阈值，失败保留。
周期3→5：Direct仍0/0；Impedance仍18/17；Admittance13/12→13/13；VMC17/17→17/16。不能说持续改善。
Direct改善0.09068、Impedance1.04981都未满足原 reward 改善≥2条件。原四 learner 全部结束，不原样延长。

## 三种独立 critic 初始化的配对结果

复用原seed20261027，新增26/28；四接口×三seed×两臂×50k，共120万辅助critic更新，24臂/1200诊断点。
三种初始critic hash不同；同方法actor/replay完全一致；两臂初始函数与采样流一致；不可变输入hash核验通过。
只训练critic，固定父actor/alpha/mixing context；全回放cycle0/1都参与拟合，没有未参与拟合的测试数据。

| 方法 | 无时钟终端MAE均值 | 有时钟终端MAE均值 |
|---|---:|---:|
| direct | 17.760 | 8.487 |
| impedance | 30.606 | 11.354 |
| admittance | 69.204 | 19.699 |
| vmc | 74.311 | 25.806 |

全部12个方法/seed配对的最终终端MAE较低，但部分误差先降后升、Q持续移动；这不是充分收敛。
继承父critic的对照此前不显示通用时钟改善，不能声称时钟单独修复所有值估计问题。
新图 `fresh_initialization_replications_v1/fresh_initialization_clock_diagnosis.png` 已目视核验。
辅助权重不保存/推广，不能当作部署策略。

## 本次运行中的补充验证及算力

`fresh_critic_clock_withheld_cycle_v1` 使用同一已验证工具，四接口×三独立初始化×两臂×50k。
只用cycle0拟合，cycle1不参与**本次critic拟合**。父actor/alpha此前见过cycle1，因此不是完整未见数据或未见条件泛化。
已登记总120万critic更新，0actor更新、0新物理。每卡三个进程，CPU0–11；启动与实际更新核验12/12，无失败。
不得以利用率为由无限续跑，结束后须科学复核。

约一分钟30次采样，GPU0–3均值98.07/98.27/98.90/98.50%，最低94/97/98/97%。
这是混合诊断负载，不能称正式在线吞吐或保证未来持续占用。

## 独立在线候选的实现与验证

默认关闭 `critic_clock`；目前只支持CHEQ。actor实际网络仍49维（canonical48静态缩放+自身mixing context）；
critic/replay50维，附加 `(1375-已执行动作数)/1375`，不读取接触真值、未来abort或任务标签。
actor prehook剥离最后时钟列，梯度/动作/对数概率对直接时钟输入不敏感；critic新增列置零、保留原始函数。
**critic时钟会改变CHEQ的不确定性与mixing，actor自身mixing context因而可能间接受到影响**；不是“完全相同控制器”或reward-only复现。

每个采样stream独立计数；观测查询不增加计数，成功生成动作后增加一次。
55s结束后时钟为0；859动作早停仍保留516/1375，不利用未来终止时间。
终端next observation其余字段按原规则保留，done仍关闭bootstrap。
替换critic首层后重建fresh Adam、重新冻结target参数；actor优化器保留，target对action的梯度保留。
checkpoint带架构flag，拒绝新旧架构静默互转；环境状态不包含在learner checkpoint，回合边界恢复重新reset。

四接口 pinned CHEQ 验证通过：actor隔离、critic时钟可学习、优化器参数归属、target action梯度、stream/reset/horizon/早停、完整状态恢复后下一次update精确相等、默认关闭时与source16构造和更新精确一致。
四份已有测试文件17项通过。最初尝试pytest发现环境没有pytest，改用这些测试原生unittest入口通过，未安装依赖。

独立runtime：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/critic_clock_candidate_v1`。
相对source16仅五个明确文件改动，源码/参数/上游/机器人清单核验；不包含尚未部署的contact_math候选。
四个 `active_short_train_0000` 完整回合预检已开始，各最多1375动作，共最多440万物理子步，0优化更新（低于原5000 warmup）。
这是trainer/真实物理/回放时钟联通预检，不是正式新训练阶段；四个进程均已开始推进。
预检保留完整checkpoint供终端和replay复核；全部正式阶段选定/启动仍待上述证据与预检完成。

## 保存位置与下一步

本机集群主机 `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`；路径前缀 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。原始数据/模型/运行日志在SSD，不提交Git。
完整证据索引见同名JSON；无新airpig/Spark传输声明。远端核对main50613a5、baseline f6e8f8c。

下一步完成十二个跨周期critic对照与四接口真实回合预检，再决定独立在线阶段；继续固定cycle3代表矩阵、接触math完整验证的独立复核。
原物理/MJB、Task/Strict gate、公共filter、执行器限制、dt、reward保持不变。指定最终ESN未提供，不能替换为历史ESN或另一个八条件矩阵。
最终仍需真实策略学习改进、优化健康与冻结策略评估，之后进行30条件训练集公平比较和SPT_empirical/contact-only舒适审计。
