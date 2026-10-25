# 两篇强化学习柔顺控制论文的迁移评估与实验登记建议

更新日期：2026-10-25

本文根据 Zhang 等人在 CoRL 2023 发表的在线导纳残差学习工作，以及 Portela 等人在 ICRA
2024 发表的腿式机器人力控制工作，评估它们对本项目 FR3 柔顺控制研究的可采纳部分。
本文是方法决策和实验登记建议，不是两篇论文的复现报告，也不把论文平台上的结果写成 FR3
结果。当前训练入口和 reward 仍以 [RL_SPT_TRAINING_HANDOFF_20261025.md](RL_SPT_TRAINING_HANDOFF_20261025.md)
为准。

## 结论和采纳边界

两篇论文可以为当前项目提供两个互补的研究方向：

1. 让策略输出解析控制器的低维参数残差，由导纳、阻抗或 VMC 控制器执行。这条路线有明确
   的物理结构，适合研究接触时刚度、阻尼和速度如何调整。
2. 让策略根据一段本体观测历史直接输出当前项目已有的动作接口。这条路线适合研究接触历史
   和内部记忆是否能帮助策略在外力持续存在时让位并继续完成任务。

建议把两条路线登记为独立实验族，分别与当前四类 `spt_v1` baseline 比较。不要把两条路线
合并成一个“改进 RL”，也不要在一次训练中同时改变观测历史、动作接口、critic 信息和 reward。

下列内容可以采纳为设计原则：

- 参数策略输出有界残差，而不是直接输出电机力矩；残差经过正值、范围和变化率约束后再交给
  解析控制器。
- 直接动作策略可以使用 canonical48 的时间历史或递归隐藏状态，以表达接触前后变化；每一帧
  的原始观测权限仍与现有 actor 合同一致。
- 如果使用仿真真值外力或其他 privileged state 训练 critic，必须单独标注为 privileged-critic
  变体；部署 actor、最终测试 actor 和纯本体 baseline 不能混列。
- 复杂接触任务应优先比较任务成功、安全违规、SPT 和接触负载，训练 reward 只作为学习诊断。

下列内容不能直接采纳为当前项目配置：

- FANUC 或 B1-Z1 平台的动作维度、控制频率、episode 长度、网络大小和并行环境数量；
- 论文中的接触刚度/阻尼、力目标、奖励权重和力阈值；
- 论文自己的 assembly/pivoting 或 whole-body force 结果；
- 将真实腕部 F/T 传感器、障碍物真值、碰撞时刻或未来事件标签加入当前 actor；
- 把论文中 10/10、9/10 或低力误差写成 FR3 的成功或安全证据。

当前 physics/MJB、`dt=5e-5`、Task/Strict gate、canonical48 actor 输入、公共 action filter 和
执行器限制继续冻结。任何采用论文机制的新实验都必须新建 variant、source snapshot、配置
和 checkpoint lineage，不能给旧 reward/replay 静默换标签。

## 论文一：在线导纳残差学习

Zhang 等人的 CoRL 2023 工作针对接触丰富操作中的仿真到现实参数失配。它先学习任务动作和
初始导纳参数，再根据近期接触力记录搜索参数残差，之后继续执行。其核心贡献对当前 FR3 的
可迁移部分是“策略负责高层任务和柔顺参数，解析导纳控制器负责物理执行”，而不是论文中的
具体机器人、传感器或在线优化器。

论文中的笛卡尔导纳模型可写为

\[
M(\ddot x_c-\ddot x_d)+D(\dot x_c-\dot x_d)+K(x_c-x_d)=F_{\rm ext}.
\]

其中 $M,D,K$ 是对角参数。若按临界阻尼关系设置，单个方向可以使用
$d_i=2\sqrt{m_i k_i}$。这说明策略至少应被限制在正值和有界参数集合内；它不证明任何固定
的参数范围适用于当前 FR3。

论文还使用了近期力序列的 record-and-replay 来预测短期接触响应，并周期性优化残差。这个
机制可以作为后续“在线适应”研究，但不能直接并入当前统一训练比较：它会引入部署时的额外
优化器、时间窗口和未来力序列假设，改变了方法定义。

论文的 assembly 动作包括末端速度和刚度项，pivoting 动作是部分方向的速度与刚度。当前 FR3
的动作接口和控制周期不同，所以这里只能采纳“低维参数残差 + 解析控制器”的结构，不能复制
论文的 12 维或 4 维动作空间。

论文报告的 SAC、DDPG 和 TD3 对照可以作为算法敏感性研究的来源。当前项目已有 pinned
SimbaV2 训练入口，因此不应为了模仿论文而把所有 baseline 直接改成另一套 SAC 实现。若要
增加 SAC 或 TD3，必须登记为新的算法 variant，并固定观测、动作、reward、seed、预算和
checkpoint 选择规则。

## 论文二：历史本体观测与力控制

Portela 等人的 ICRA 2024 工作面向 Unitree B1 加 Z1 的腿式全身操作。其策略使用本体观测
历史、状态估计器和直接关节目标动作；critic 可以读取训练时的 privileged state。可迁移的
方法思想是：接触反应依赖一段时间历史，而非只依赖当前一帧；训练 critic 的信息权限可以
比部署 actor 更丰富，但必须在实验报告中显式分栏。

该工作中的单步观测、17 维动作、30 帧历史、PD/全身控制器和 4096 个并行 Isaac Gym 环境
均属于其平台配置。它们不能覆盖当前 FR3 的 canonical48、action7 或四种在线参数接口。
当前 direct-action 方案应保持已有动作契约，例如以末端速度/角速度残差和柔顺门控构成 action7；
若实际接口不同，应以冻结 source 和 adapter 的登记值为准，而不是根据论文数字重写接口。

论文中使用位置、期望力跟踪、碰撞、关节限制、速度、加速度和动作差分等项。当前项目可以
借鉴“把安全与平滑列为独立项”的组织方式，但奖励权重必须重新按 FR3 的物理量纲和 SPT
目标登记。指数乘积奖励不作为当前默认 reward，因为它可能让任务、安全和效率的贡献难以
审计，也不能替代独立 Task/Strict gate。

privileged critic 的正确写法是：critic 可以在训练中接收额外真值，actor 仍只接收部署允许的
输入；状态估计器的误差也要单独记录。下列四行不能混成一个结果：

| 变体 | Actor 输入 | Critic 输入 | 可用于正式纯本体比较 |
|---|---|---|---|
| encoder-only | canonical48 当前帧或其历史 | 同一权限 | 可以 |
| history actor | canonical48 历史/递归状态 | 同一权限 | 可以，需单列记忆结构 |
| privileged critic | canonical48 历史 | 加入注册的训练真值 | 可以作为单独训练变体，不能标成纯本体 |
| privileged actor | 含外力真值、障碍物真值或未来标签 | 同上 | 不可以进入当前正式 actor 对比 |

## 面向当前 FR3 的严谨迁移方案

### A. 参数残差策略

先选择一个解析控制器作为主对象，每次策略输出少量参数的无量纲残差。推荐顺序是：

1. 六个笛卡尔刚度缩放；
2. 六个阻尼缩放，或由刚度和质量计算阻尼；
3. 六个目标速度/动作残差；
4. 只有在前述变体完成稳定性审计后，才考虑虚拟质量或更高维参数。

可用如下形式生成实际参数：

\[
u_t=u_0\odot\exp\left(\alpha\tanh(a_t)\right),
\]

或对有明确上下界的量使用有界线性映射。随后必须经过参数上下界、正值约束、每次更新最大
变化量和执行器公共限制。这样可以避免策略通过输出负阻尼或跳变刚度获得短期 reward。

策略更新频率应与当前控制接口登记一致。物理积分仍使用冻结 `dt=5e-5`；策略不应在每个
物理子步重新学习。建议先在现有 40 ms 控制间隔输出一次参数，并在两个策略输出之间保持
或平滑插值；确切选择要作为 variant 字段记录并通过动作/物理 replay 核验。

参数策略的 reward 继续使用当前 `spt_v1` 统一定义：payload progress、剩余任务时间、真实
人体接触期间的力/力矩代理、峰值力矩、穿透、实际力矩变化和 Task AND Strict 终奖。论文的
assembly 位置 reward 可以作为诊断项，不能替换 SPT 训练代理，也不能使用无接触时段伪造
舒适比例。

### B. 直接动作策略

直接动作变体应在当前 action7 接口内比较。第一阶段保留当前 canonical48 单帧输入；第二阶段
只增加一个明确登记的历史编码器，输入仍是连续的 canonical48 序列，不加入障碍物真值、接触
时间标签或未来事件。可比较：

- 单帧 MLP：测量“没有时间记忆”的下限；
- canonical48 历史堆叠或 GRU：测量可训练记忆；
- 固定 reservoir + readout 的 ESN：作为当前项目的记忆基线；
- PPO 或 SAC direct-action：分别登记算法，而不是把算法和记忆结构混为一个因素。

动作经过同一个 public filter 和执行器限制。不得因为 direct policy 不稳定而绕过 filter、替换
动作范围、改变动作频率或把失败 episode 从统计中删除。

### C. 训练时 privileged critic

若采用论文二的训练范式，可让 critic 使用仿真中真实接触力、未滤波外力或其他已登记真值，
同时要求 actor 只使用 canonical48。该变体的目的是研究训练辅助信息是否改善优化，不是证明
部署 actor 拥有这些真值。必须额外记录：

- privileged 字段的名称、来源、单位和时间对齐；
- actor 与 critic 的输入 hash；
- 状态估计器是否存在、训练目标和验证误差；
- 训练/验证/测试是否使用了同一信息权限；
- 最终 replay 是否能证明 actor 没有读取 privileged 字段。

当前第一轮不建议把 privileged critic 和新的 reward、历史 encoder、参数残差同时引入。每次
只改变一个因素，才能解释 reward 不收敛是实现问题、信息不足、探索不足还是目标冲突。

### D. 在线导纳残差优化

该机制可作为单独的部署适应研究，不纳入第一轮统一 RL/ESN 排名。需要先定义接触窗口、
记录时长、外力预测误差、残差搜索预算、参数恢复策略和停止条件。所有优化只能使用过去已
观测的信号；不能把测试回合未来力序列或碰撞标签提供给在线优化器。适应前后的策略必须在
相同条件、相同任务门和相同安全审计下比较，且把“固定策略”和“在线适应策略”列为不同方法。

## 调参与算法选择的实验顺序

文献中的学习率、折扣因子、batch size、外力刚度和 episode 长度不能直接移植。当前任务是
55 秒长时域 FR3 任务，现有 `spt_v1` 已固定单步 TD、UTD=1、gamma、replay 和物理审计协议。
建议按以下顺序调参：

1. 先做单个方法、单个 seed 的完整 1375 步预检，核对真实物理推进、reward 分解和 actor/filter
   replay；预检不是训练成功。
2. 固定 reward 与接口，只比较少量探索强度和学习率候选，例如 temperature、entropy 系数、
   actor/critic learning rate；每个候选独立 run，禁止覆盖失败收据。
3. 若长时域 credit assignment 明显不足，再单独登记 n-step 或 PPO rollout 变体；不能把
   n-step 改动和 reward 改动同时写进同一个 checkpoint lineage。
4. 对 direct-action，先比较单帧与历史编码器；对 parameter-RL，先比较低维刚度/阻尼残差。
5. 只有在实现、reward 量纲和探索行为都通过审计后，才扩展到三 seed、四路服务器并行和百万
   步上限。并行增加样本量，不改变方法选择规则。

训练判据仍与项目既定要求一致：训练 reward 必须在有实际学习改善后趋稳，而不是从第一回合
就平坦；至少观察多个完整条件周期、相邻窗口均值、斜率、波动区间、optimizer diagnostics、
entropy/temperature、参数变化和数值失败。稳定 reward 不等于任务成功，任务失败也必须保留。

## 统一比较和论文写法

最终比较至少分开报告：Task success rate、Strict success rate、SPT、完成时间、逐关节峰值
力矩、实际人体接触期间舒适力矩合规比例、人体接触力/冲量、穿透、速度和失败原因。SPT 的
`T_ref` 必须在测试前按固定参考流程登记，不能从被测方法的最快回合反填。

结果表应至少包含下列列：

| 方法 | 算法 | 控制输出 | Actor 权限 | Critic 权限 | 历史长度/记忆 | reward variant | seed | Task/Strict | SPT | 安全指标 |
|---|---|---|---|---|---|---|---|---|---|---|
| ESN | readout training | action7 | canonical48 history | same | fixed reservoir | registered | … | … | … | … |
| direct RL | PPO/SAC/SimbaV2 | action7 | canonical48 | same/privileged separate | none/history | registered | … | … | … | … |
| parameter RL | SAC/registered learner | controller parameters | canonical48 | same/privileged separate | none/history | registered | … | … | … | … |

论文中可以这样表述：CoRL 2023 提供了参数残差和接触后局部适应的设计依据；ICRA 2024 提供了
历史本体输入、状态估计器和 privileged critic 分栏的设计依据。当前 FR3 实验只验证这些机制
在冻结场景、统一信息权限和 SPT 评估下是否有效，不声称复现两篇论文的机器人结果。

## 当前执行决策

- **立即采纳为设计原则**：参数残差的物理约束、历史本体输入作为独立变量、privileged critic
  的显式分栏、统一任务/安全/效率指标。
- **暂不改动当前首轮训练入口**：`spt_v1` reward、canonical48、action7/现有参数接口、
  public filter、冻结 MJB/gate 和 `dt=5e-5` 保持不变。
- **下一步可登记的两个新 variant**：`parameter_residual_sac_v1`、`direct_history_ppo_v1`。
  二者都必须从头创建 source/config/replay/checkpoint，不得接续旧 reward 的 optimizer state。
- **暂不纳入统一排名**：真实部署在线 record-and-replay 残差适应；它应在固定策略比较之后
  作为单独的 adaptation study。

## 文献来源和证据边界

1. Zhang et al., “Efficient Sim-to-real Transfer of Contact-rich Manipulation Skills with Online
   Admittance Residual Learning,” CoRL 2023, PMLR 229：
   <https://proceedings.mlr.press/v229/zhang23e/zhang23e.pdf>
2. Portela et al., “Learning Force Control for Legged Manipulation,” ICRA 2024，预印本：
   <https://arxiv.org/pdf/2405.01402>

论文中的 success rate、力误差、硬件、外力场和网络配置只属于论文实验；本项目需重新登记并
实测。本文发布的是迁移判断与可复现实验约束，不是已完成的 FR3 训练、收敛或测试结果。
