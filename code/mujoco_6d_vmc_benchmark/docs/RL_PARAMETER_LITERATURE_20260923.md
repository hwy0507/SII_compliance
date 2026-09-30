# 2024 年以来 RL 调参/柔顺控制对比文献（核验版）

本清单服务于 SII compliance 项目的 teacher VMC、student ESN/MLP 对比实验。本项目VMC是解析虚拟弹簧—阻尼控制器，并非神经网络；ESN/MLP才是学习策略。这里的“RL 调参”指策略网络输出阻抗/导纳或其低维参数，随后由解析控制器（QP、阻抗控制器、MPC 等）计算关节加速度/力矩；它与 ESN 直接输出 7D 柔顺 action 的接口不同，也不等于用RL优化神经网络权重/训练超参数。若论文需要后者，本清单并未满足该更窄定义。

## 结论与可比性

三篇均为 2024 年以后正式出版的 IEEE 机器人会议论文：ICRA 2025 两篇和 Humanoids 2024 一篇。它们适合作为“RL 输出物理控制器参数”的外部基线；不能把它们的任务成功率直接等同于本项目的 blind-office 成功率。除 Da-VIL 外，公开版本没有提供可直接复现实验仓库，因此本周建议优先复现动作接口与解析控制器，再做同任务对齐。

| 文献 | venue/DOI | RL 输出 | 解析控制器 | 与本项目的关系 |
|---|---|---|---|---|
| Da-VIL: Adaptive Dual-Arm Manipulation with Reinforcement Learning and Variable Impedance Control | ICRA 2025, `10.1109/ICRA55743.2025.11127487`; arXiv:2410.19712 | PPO 策略输出 6 个笛卡尔对角刚度 `K=[kx,ky,kz,kφ,kθ,kψ]` 的离散 bin；阻尼按临界阻尼设置 | CVXPY QP 根据 `K`、参考轨迹及 MuJoCo 状态求双臂关节加速度，再由动力学换算力矩 | 最接近“RL 调 VMC/阻抗参数”；可把 6D K 作为 teacher 参数预测基线，但动作空间和双臂任务不同 |
| Impedance Primitive-augmented Hierarchical Reinforcement Learning for Sequential Tasks | ICRA 2025, `10.1109/ICRA55743.2025.11128462`; arXiv:2508.19607 | HRL 高层选 primitive；参数策略输出位置参数并附加 `Kx,Ky,Kz,Kψ` 初始刚度，阻尼由临界阻尼确定 | primitive 内闭环轨迹控制；自适应刚度律 `K̇=β|ε|−γE`，实时修改刚度 | 适合对比“分阶段/primitive 条件下的参数调度”；本项目可按 approach/contact/lift/place 阶段分桶评估 ESN action |
| Variable Impedance Control Combining Reinforcement Learning and Gaussian Process Regression | IEEE-RAS Humanoids 2024, `10.1109/Humanoids58906.2024.10769856` | FCEM搜索7个关节参数θ，K=θ²；GPR将估计外力矩映射为刚度 | 关节可变阻抗，D按临界阻尼设置；HAL公开PDF核验范围见下文 | RL-style parameter search + GPR，不冒称标准PPO/SAC的MDP策略；尚无本项目复现成绩 |

## 1. Da-VIL（建议的第一复现对象）

**官方记录。** Crossref 记录的正式出版物为 ICRA 2025，DOI `10.1109/ICRA55743.2025.11127487`；作者公开的 arXiv 版本为 [2410.19712](https://arxiv.org/abs/2410.19712)，项目页为 <https://dualarmvil.github.io/Dual-Arm-VIL/>。arXiv HTML 版本明确给出方法、状态和动作定义。

**方法核验。** 每个时刻的 observation 包含左右末端位姿变化 `{ΔxL,ΔxR}`（SE(3)，位置+四元数）、物体位姿 `Xt`（SE(3)）、两臂 7-DoF 关节位置、两臂末端 6D wrench、上一时刻刚度动作 `K_{t−1}`，以及时间和质量的正弦 embedding。策略和值函数是 MLP，训练算法是 PPO。动作是 6 个对角笛卡尔刚度参数的离散分类值，`K=Diag[kx,ky,kz,kφ,kθ,kψ]`；阻尼 `D` 按临界阻尼设置。

策略输出的 `K` 送入 CVXPY 凸 QP；QP 使用参考轨迹、阻抗误差及双臂动力学状态求关节加速度，再经动力学方程得到左右臂力矩。奖励包含末端/物体轨迹误差、目标完成、QP 不可行惩罚，以及刚度相对 EMA 的突变惩罚。该设计明确属于“RL 调解析控制器参数”，不是 RL 直接输出 torque。

**可复现映射。** 在本项目 MuJoCo 中实现一个 `rl_vmc_parameter` 对照：输入使用与 student 相同的本体可观测量；策略输出 6D `K`（或先输出标量/分组 K）；VMC 使用 K 计算 6D wrench/action。必须报告额外 privileged 输入（质量、物体位姿、参考轨迹）是否存在，以免与 blind student 不公平。论文使用双臂 pick-and-place 和已知 grasp pose，不能直接宣称适用于 FR3 单臂办公室任务。

## 2. IMP-HRL（阶段化调参基线）

**官方记录。** Crossref 正式记录为 ICRA 2025，DOI `10.1109/ICRA55743.2025.11128462`；公开版本为 [arXiv:2508.19607](https://arxiv.org/abs/2508.19607)。论文明确写明 accepted for ICRA 2025。

**方法核验。** 该方法把长时域任务写成 parameterized-action MDP：高层策略选择 primitive，低层参数策略输出 primitive 目标参数。Reach 的参数为 `(x,y,z)`，Grasp 为 `(x,y,z,ψ)`，Push 含目标和位移，Atomic 为 `(δx,δy,δz)`，Gripper 为开合。IMP-HRL 在这些参数上增加 `Kx,Ky,Kz,Kψ`，作为该 primitive 的初始刚度估计；阻尼矩阵由临界阻尼计算。primitive 执行期间采用闭环自适应刚度律 `K̇(t)=β|ε(t)|−γE`，其中 `ε` 是闭环误差、`E` 是关节能量，刚度变化通过插值平滑。

训练/评测覆盖 block lifting、door opening、object pushing、surface cleaning，并包含真实机器人验证。它的核心贡献是高层任务分解和低层柔顺参数联动，因此可作为本项目“分阶段 ESN action 是否优于单一 MLP”的强基线。

**可复现映射。** 用本项目已有 primitive/task phase 标签做高层条件输入；低层 baseline 输出 `(phase-conditioned K)`，由 VMC 将 K 转成 6D wrench。训练和 test split 必须按 fixture/布局划分；禁止把障碍物真值、接触 flag、未来阶段标签直接输入 student。若保留 phase 标签，应将它标成 task planner 提供的高层输入并对所有方法一致开放。

## 3. RL + Gaussian Process 可变阻抗（Humanoids 2024）

**官方记录。** Crossref 正式记录为 2024 IEEE-RAS 23rd International Conference on Humanoid Robots，页码 343–350，DOI `10.1109/Humanoids58906.2024.10769856`，题目为 *Variable Impedance Control Combining Reinforcement Learning and Gaussian Process Regression*。记录的出版日期为 2024-11-22。论文没有在 Crossref 条目中列出开放代码。

**已核验范围。** 作者公开版本（[HAL PDF](https://hal.science/hal-05036167v1/document)）给出可复现细节：RL 使用 all-time-stable Fast Cross-Entropy Method (FCEM) 搜索每关节标量 `θᵢ`，并定义 `Kᵢ=θᵢ²`、`Dᵢ=2ζᵢ√(Kᵢ Bᵈᵢ)`（所有实验 `ζ=1`）；优化变量因此是 7 个关节的阻抗参数，而不是直接 torque。代价由任务终止项、刚度惩罚和累计关节跟踪误差组成，并以采样频率/Nyquist 约束 K 上界。GP 阶段以每关节动量观测器估计外部交互力矩 `τ̂ₑᵢ` 为输入、最优刚度 `Kᵢ` 为输出，使用零均值平方指数核；运行时由 GPR 后验均值更新目标刚度/阻尼，不需要 wrench sensor。实验任务为 ball catching、box pushing 和不同重量的 bimanual box lifting，平台是仿真 ABB Mobile YuMi。论文没有把 FCEM 写成标准 MDP observation/action policy；因此本项目复现应把它标为 **RL-style parameter search**，并明确其输入为固定参考轨迹/任务代价及 rollout 状态、输出为 7D joint-space K（由 K 决定 D）。

**可复现建议。** 先按论文正式版本实现相同的 RL 参数化接口和 GP 后验/不确定性更新；若 PDF 无法取得，则只实现一个透明的 RL→阻抗参数适配器作为“方法族” sanity check，结果不能标为论文复现。报告应同时给出无 GP、RL+GP、固定 VMC 三组，并使用本项目统一的任务成功、峰值外力、峰值关节力矩、速度 P95、jerk、穿透与恢复时间指标。

## 与 ESN proposed method 的公平对比协议

1. **接口对齐。** ESN 仍输出项目规定的 7D action `[slowdown, yield_vx, yield_vy, yield_vz, yield_wx, yield_wy, yield_wz]`。RL 调参 baseline 输出的 K/D 先经过同一个 VMC/阻抗执行器转换为相同的 7D action，再由同一 MuJoCo 环境执行。
2. **观测对齐。** student 只能使用 FR3 本体可观测状态（关节、末端位姿/速度、wrench、历史 action 等）。Da-VIL 的物体质量、物体位姿和参考轨迹是其论文设定中的 privileged/task information，若在本项目保留，必须单独标注 `privileged RL`，并提供无 privileged 版本。
3. **训练预算。** 统一 seed、episode 数、网络参数量、动作更新频率、normalization、checkpoint 选择和 fixture-level split；报告训练样本数和 wall-clock。
4. **安全与任务 gate。** 统一使用项目已有 penetration、外力/力矩、任务完成、release 和恢复 gates。任何单一 tracking loss 结果都不能代替闭环任务成功。
5. **论文等级。** ICRA/Humanoids 属于机器人领域顶级会议；不要用 IEEE Access 论文冒充顶会。可作为补充参考但不纳入本三篇核心比较。

## 参考与核验链接

- [Da-VIL arXiv:2410.19712](https://arxiv.org/abs/2410.19712)；[DOI](https://doi.org/10.1109/ICRA55743.2025.11127487)
- [IMP-HRL arXiv:2508.19607](https://arxiv.org/abs/2508.19607)；[DOI](https://doi.org/10.1109/ICRA55743.2025.11128462)
- [Humanoids 2024 DOI](https://doi.org/10.1109/Humanoids58906.2024.10769856)
- [Crossref Da-VIL/IMP-HRL/Humanoids 元数据 API](https://api.crossref.org/works)
