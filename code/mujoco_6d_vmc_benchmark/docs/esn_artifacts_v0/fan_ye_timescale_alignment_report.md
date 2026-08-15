# Fan Ye 时间尺度对齐 ESN：WBC-aware 预筛选结果

## 方法来源与本工作采用的部分

本阶段依据 Fan Ye 等人的 *Reservoir controllers design through robot-reservoir timescale alignment*（Communications Engineering, 2025，DOI: `10.1038/s44172-025-00418-1`）重构 ESN 的设计顺序：

1. 先由机器人/任务动态产生 actuation probe；
2. 随机生成多个 fixed reservoir；
3. 在**不训练 readout、不查看控制回报**的情况下，以频谱 containment ratio（CR）判断 reservoir 是否覆盖机器人动态时间尺度；
4. 以 echo state property index（ESPI）判断相同输入下对初值的残余敏感性；
5. 仅让 CR-high、ESPI-low 的候选进入后续 readout 训练和 closed-loop 比较。

这与先前的通用 `ComplianceESN` 骨架不同：新 `FanYeAlignedESN` 没有 action feedback，采用论文 Eq. (7) 的连续 leaky state update，以及 Eq. (8)-(9) 的 `[1; In; s]` linear ridge readout。它仍然只输出被安全投影的 7D VMC residual，不会直接输出电机 torque。

## 针对 Panda + WBC 的必要适配

Fan Ye 论文的对象是 cart-pole，reservoir 输入为机器人当前 state 和 target state；本文任务是固定基 Panda 的碰撞柔顺抓取。因此不可照搬 paper 的 cart-pole 数值阈值，而采用以下一一对应：

| Fan Ye paper | 本工作 WBC-aware adaptation |
|---|---|
| robot actuation/state probe | 通过物理碰撞 gate 的 Panda train trajectory |
| robot state / target state | 部署合法的 `[q(7), qdot(7), wbc_task_twist(6)]` |
| absolute-median state normalization | 11 条 train trace 的逐通道 absolute median normalization |
| robot FFT envelope | 20-D deployable trace 的去均值、加窗频谱最大包络 |
| reservoir FFT envelope | 在同一合法输入下的所有 reservoir node 最大频谱包络 |
| CR | 正规化频谱的 `sum(min(robot, reservoir))/sum(robot)` |
| ESPI | 10 个随机初值相对零初值、washout 后 state MSE 的平均 |

去均值不是原论文的额外性能技巧，而是 Panda 关节存在固定姿态偏置；若不去均值，静态姿态的 DC 分量会淹没我们真正关心的碰撞/回归动态频率。该差异会随代码和结果一起记录。

学生输入没有 rod/contact/force/obstacle/future release/fixture ID。预筛选脚本只从 `.npz` 显式读取 `joint_position`、`joint_velocity` 和 `wbc_task_twist`，其他诊断字段即使存在于 MuJoCo trace 中也不会被加载。

## 服务器预筛选

在 ESN train split 的 11 条通过有效碰撞 gate 的 physical rod trace 上，使用 25 Hz ESN update（MuJoCo 4 ms trace 每 10 帧采样一次）生成 128 个 paper-informed reservoir candidate：

- `N ∈ {24, 32, 48, 64}`；
- spectral radius 在 `[0.5, 2.0]`；
- input scaling 在 `[0.1, 2.0]`；
- reservoir time constant 在 `[0.040, 0.320] s`；
- connection probability 在 `[2/N, min(20/N,1)]`；
- bias scaling 在 `[0.01, 1.0]`；
- ridge coefficient 在 `[1e-8, 1e-2]`。

结果：

| 项目 | 数值 |
|---|---:|
| train physical trace 数 | 11 |
| 随机 reservoir 数 | 128 |
| CR/ESPI Pareto frontier 数 | 1 |
| 最优候选 index | 22 |
| CR | 0.997594 |
| ESPI | `2.455e-24` |
| robot dynamic bandwidth | 4.909 Hz |
| reservoir dynamic bandwidth | 9.273 Hz |

候选 #22 配置为：`N=64`、spectral radius `1.86639`、input scale `1.60125`、time constant `0.05149 s`、connection probability `0.16095`、bias scale `0.64790`、ridge coefficient `0.007569`。完整 128 个候选及其 metrics 在 [fan_ye_timescale_screen_train.json](fan_ye_timescale_screen_train.json)。

CR 的五数概括（min / Q1 / median / Q3 / max）为 `0.5630 / 0.7189 / 0.7860 / 0.8693 / 0.9976`；ESPI 为 `2.46e-24 / 2.31e-10 / 2.25e-7 / 7.35e-6 / 5.04e-4`。因此该选择不是随意挑一个默认 spectral radius，而是有明确的 robot-reservoir temporal coverage 证据。

## 不能过度解释的地方

- Fan Ye 论文中 `CR > 0.4` 是其 cart-pole ROC 实验下的选择；本工作没有把它当 Panda 的通用阈值。
- 本次 CR/ESPI 只来自 ESN train split；validation 只能用于之后选择 readout/teacher/action envelope，冻结的 WBC-aware V4 更不能参与选择。
- CR 高、ESPI 低仅说明 reservoir dynamics 合格；没有训练 readout 前，不能声称 ESN 已经改善轨迹误差、冲击力、扭矩或回归时间。
- `+z` 仍未纳入物理有效 fixture pool；结论仍限于五个轴对齐 rod approach，不是任意连续 3D collision。

## 后续 Fan Ye-compatible 实验顺序

1. 在 11 条 train fixture 上创建**不含 privileged observation**的安全 action-probe 数据；teacher 可以离线使用完整仿真诊断产生标签，但 ESN 不读取它们。
2. 对 #22 及少量 CR/ESPI 接近的候选，用 train trace 拟合 7D bounded VMC residual 的 ridge readout。
3. 在 11 条 validation fixture 上冻结 teacher target、ridge 和 action safety envelope。
4. 仅在以上选择冻结后，将 selected ESN 与 VMC-gated / VMC-energy / impedance / rigid 一起运行 WBC-aware V4 final test。
