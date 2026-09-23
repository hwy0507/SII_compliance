# Data-Driven Compliance Control for FR3

> 更新日期：2026-09-23
>
> 当前主线：MuJoCo 中的 FR3/Panda 柔顺控制、VMC teacher 数据生成，以及 MLP/ESN action distillation 与复杂场景泛化验证。

本项目研究一个面向真实机械臂部署的问题：高层规划器只能提供名义任务轨迹，但真实环境中可能突然出现未建模障碍物、持续人手推动、飞来物体或桌面边缘接触。低层控制器需要仅依赖机器人可获得的 encoder / motor-current / proprioceptive 信息，及时让位、沿接触面滑移、重新汇入名义轨迹，并继续完成抓取或放置任务。

当前论文主线不是让学习策略替代整个机器人系统，而是保持规划、名义 WBC、速度伺服和安全边界一致，只比较不同柔顺策略如何产生同一个 7 维动作：

```text
task executive / nominal planner
              |
              v
paper-style WBC or resolved-rate WBC
              | nominal joint velocity / task twist
              v
VMC / MLP / ESN compliance policy
              | 7-D slowdown + Cartesian yield action
              v
shared amplitude, slew-rate, joint-speed and torque safety stack
              v
velocity servo + gravity/bias compensation
              v
MuJoCo FR3/Panda, later real FR3
```

仓库中早期的 Fetch、ManiSkill、PPO residual 路线已经从 GitHub 主线移出，并完整归档到 DGX Spark；它们不再是当前研究主线。当前主要代码位于：

```text
code/mujoco_6d_vmc_benchmark/
```

## 1. 研究问题

名义规划器负责“机械臂原本要做什么”，例如靠近物块、抓取、抬升、搬运和放置；柔顺策略负责“接触发生后如何在不破坏任务的情况下让位”。二者的信息边界被刻意分开：

- 高层规划器可以提供名义目标、名义关节速度和名义末端 twist；
- student 不读取相机、障碍物位姿、场景类别、碰撞真值或预设事件时钟；
- student 可以读取真实 FR3 可获得或可估计的关节位置、关节速度、电机力矩/电流、WBC 跟踪误差和因果估计外力；
- teacher 在仿真数据生成阶段可以利用更完整的任务成功监督筛选轨迹，但这些特权变量不得进入 student observation；
- 正式复杂办公室场景只用于冻结模型后的泛化测试，不参与训练或超参数选择。

论文希望验证的核心假设是：针对不同接触模式分别调优的 VMC 能产生高质量柔顺动作，而带有状态记忆的 ESN 可以从多簇 VMC teacher 轨迹中学习统一的动作映射，并在新的物体、布局、接触顺序和组合事件中比单组固定 VMC 参数表现出更好的泛化能力。

## 2. 统一控制接口

### 2.1 名义 WBC

仓库提供两种固定基座 FR3/Panda 名义速度控制器：

- `PaperMPCWBC`：复现 NUS visibility-aware mobile grasping 系统控制层中的单步二次 MPC 和 waypoint queue 机制，并约化为固定基座 7 自由度机械臂；
- `FixedBasePandaWBC`：使用阻尼伪逆、SE(3) 反馈和零空间姿态项产生名义关节速度。

当前 `PaperMPCWBC` 的机械臂控制律可写为：

$$
\dot q_{\mathrm{nom}}
= \operatorname{clip}\!\left(
g\,(Q+R)^{-1}Q\,(q_{\mathrm{ref}}-q),
-\dot q_{\max},\dot q_{\max}
\right),
$$

其中 waypoint queue 采用与原系统一致的 nearest-waypoint 和 lookahead 逻辑。当前仿真没有把视觉障碍物状态交给低层柔顺策略；未来可以把完整 NUS 规划器接到相同的 WBC command boundary，而无需修改 MLP/ESN 动作接口。

### 2.2 7 维柔顺动作

VMC、MLP 和 ESN 使用相同动作定义：

$$
a_t=[a_t^{\mathrm{slow}},a_t^{v_x},a_t^{v_y},a_t^{v_z},
a_t^{\omega_x},a_t^{\omega_y},a_t^{\omega_z}]\in[-1,1]^7.
$$

- 第 1 维是名义 WBC 减速请求；
- 第 2--4 维是世界坐标系中的末端线速度残差；
- 第 5--7 维是末端角速度残差；
- 全零动作严格退化为原始名义 WBC，不引入额外柔顺修正。

动作经过共享的幅值和变化率限制：

$$
s_t=1-\max(0,a_t^{\mathrm{slow}})(1-s_{\min}),
$$

$$
\xi_{\mathrm{yield},t}
=a_{t,1:6}\odot
[v_{\max},v_{\max},v_{\max},\omega_{\max},\omega_{\max},\omega_{\max}],
$$

然后通过阻尼 Jacobian 伪逆映射到关节速度：

$$
\dot q_{\mathrm{cmd}}
=s_t\dot q_{\mathrm{nom}}
+J^{\#}(q)\,\xi_{\mathrm{yield},t}.
$$

`VelocityResidualActionFilter` 统一执行 action clip、WBC scale slew、残差速度 slew、关节速度和关节加速度限制。随后 P 型速度伺服、bias/gravity compensation、解析 torque box projection 和 torque-rate limiter 产生最终力矩：

$$
\tau_{\mathrm{servo}}
=\tau_{\mathrm{bias}}+K_v(\dot q_{\mathrm{cmd}}-\dot q),
$$

$$
\tau_t=\operatorname{rate\_limit}
\left(\operatorname{project}_{[-\tau_{\max},\tau_{\max}]}
(\tau_{\mathrm{servo}})\right).
$$

因此各方法共享名义控制器、执行器、安全限制和动作语义，唯一区别是 $a_t$ 的生成方式。

### 2.3 控制周期

- 策略周期：`40 ms`，即 `RL_DT = 0.040`；
- 每个策略动作内部执行多个 MuJoCo physics/control substeps；
- 接触敏感场景可以把物理步长降低至 `0.5 ms` 或配置文件指定值；
- MLP、ESN 和 VMC 均在相同策略周期上输出动作。

## 3. VMC：Baseline 与 Teacher

VMC 在当前项目中有两个身份：

1. **Model-based baseline**：固定一组参数后直接在未见过的测试条件中运行；
2. **Teacher**：在不同物理 fixture 上独立扫描 6D 参数，保留满足任务成功和物理约束的 Pareto 动作轨迹，用于训练 MLP/ESN。

当前 6D virtual dynamics 使用三维平移和三维旋转通道。简化形式为：

$$
M_v\ddot x_v+B_v\dot x_v+K_vx_v
=\operatorname{sat}_{\sigma}(w_{\mathrm{ext}}),
$$

$$
\xi_{\mathrm{yield}}
=\dot x_v+K_{\mathrm{offset}}x_v,
$$

其中 $w_{\mathrm{ext}}$ 来自关节侧因果 load observer 和末端 Jacobian 所构造的等效 6D wrench，而不是直接读取 MuJoCo contact truth。可扫描参数包括：

- 6D stiffness；
- 6D damping；
- 6D virtual mass/inertia；
- force/moment saturation；
- deadband；
- virtual velocity limit；
- virtual offset limit；
- action limit；
- offset tracking gain；
- wrench filter time constant；
- VMC 主轴旋转；
- 场景相关的接触、释放和回归参数。

由于跟踪误差、峰值力、峰值力矩、完成时间和平滑性之间存在真实冲突，teacher 选择不使用单一手工加权总分。流程是在每个物理 fixture 内先应用任务和物理有效性门槛，再保留经验 Pareto 非支配参数/轨迹。它是有限扫描范围内的 Pareto 集，不是全局最优证明。

## 4. 经典笛卡尔导纳与阻抗 Baseline

当前仓库把两个经典控制器作为低层柔顺 baseline。二者都接收同一个名义 WBC 参考位姿/速度和机器人本体感觉状态，但输出路径不同：

- **笛卡尔阻抗（Cartesian impedance）**：根据末端位姿误差和速度误差直接构造 6D 笛卡尔虚拟力/力矩，再通过 $J^T$ 映射为关节力矩；
- **笛卡尔导纳（Cartesian admittance）**：根据测得或估计的外力/力矩驱动一个虚拟质量-阻尼-弹簧系统，积分得到末端让位速度/位移，再通过 Jacobian 伪逆生成关节速度残差。

在本项目的统一比较中，两者都必须复用相同的名义 WBC、MuJoCo 接触模型、速度/力矩安全栈、抓取阶段和任务成功判据。它们不读取障碍物几何、接触真值或未来事件时间。

### 4.1 笛卡尔阻抗控制

设名义末端位姿为 $(p_d,R_d)$，实测末端位姿为 $(p,R)$，名义 twist 为 $\nu_d=[v_d,\omega_d]$，实测 twist 为 $\nu=[v,\omega]$。代码中使用：

$$
e_p=p_d-p,
\qquad
e_R=\operatorname{Log}(R_dR^T),
$$

$$
e_v=v_d-v,
\qquad
e_\omega=\omega_d-\omega.
$$

平移和转动通道分别采用阻抗形式：

$$
F=K_p e_p+D_p e_v,
\qquad
M=K_R e_R+D_R e_\omega.
$$

代码按照阻尼比 $\zeta$ 由虚拟质量/惯量自动设置阻尼：

$$
D_p=2\zeta\sqrt{m_vK_p},
\qquad
D_R=2\zeta\sqrt{I_vK_R}.
$$

为避免大误差时输出无限增大的力，弹簧项先经过逐轴饱和，再进行向量范数限制：

$$
F_s=F_{\max}\tanh\left(\frac{K_p e_p}{F_{\max}}\right),
\qquad
M_s=M_{\max}\tanh\left(\frac{K_R e_R}{M_{\max}}\right),
$$

$$
F=\operatorname{sat}_{\|\cdot\|\le F_{\max}}(F_s+D_pe_v),
\qquad
M=\operatorname{sat}_{\|\cdot\|\le M_{\max}}(M_s+D_Re_\omega).
$$

最终笛卡尔 wrench 为 $w=[F,M]$，通过末端几何 Jacobian 转成关节力矩：

$$
\tau_{\mathrm{imp}}=J(q)^Tw,
\qquad
\tau=\operatorname{rate\_limit}\left(
\operatorname{project}_{[-\tau_{\max},\tau_{\max}]}
(\tau_{\mathrm{bias}}+\alpha\tau_{\mathrm{imp}})\right).
$$

其中 $\alpha$ 是在 torque box 内尽可能大的公共缩放系数，用来保持 wrench 方向而不是简单地逐关节截断。当前 rod baseline 使用的固定参数在代码中是：平移刚度 `900 N/m`、转动刚度 `45 Nm/rad`、阻尼比 `1.2`、力界 `24 N`、力矩界 `3 Nm`；对应代码的 high-stiffness `rigid` 对照为 `8000 N/m`、`360 Nm/rad`、阻尼比 `1.5`、`90 N`、`12 Nm`。正式论文应把这些值写在 protocol 中，并在相同的 fixture 上重新调参，而不能把开发版单个参数直接宣称为全局最优。

代码实现位于 `scripts/run_rod_perturbation_benchmark.py` 的 `_direct_cartesian_wrench`：

```python
def _direct_cartesian_wrench(
    nominal_position, nominal_rotation, nominal_twist,
    ee_position, ee_rotation, ee_twist,
    translation_stiffness, rotation_stiffness,
    damping_ratio, maximum_force, maximum_moment,
):
    position_error = nominal_position - ee_position
    rotation_error = so3_log(nominal_rotation @ ee_rotation.T)
    velocity_error = nominal_twist - ee_twist

    translation_damping = 2.0 * damping_ratio * np.sqrt(
        VMCConfig().virtual_mass * translation_stiffness
    )
    rotation_damping = 2.0 * damping_ratio * np.sqrt(
        VMCConfig().virtual_inertia * rotation_stiffness
    )

    force = _saturated_translation_spring(
        translation_stiffness, maximum_force, position_error
    )
    force += translation_damping * velocity_error[:3]

    moment = maximum_moment * np.tanh(
        rotation_stiffness * rotation_error / maximum_moment
    )
    moment += rotation_damping * velocity_error[3:]

    return np.concatenate([
        _saturate_vector_norm(force, maximum_force),
        _saturate_vector_norm(moment, maximum_moment),
    ]), np.concatenate([position_error, rotation_error])
```

这个控制器的物理含义是：末端被推离名义轨迹后，弹簧误差产生回归力，阻尼项抑制相对速度；它不显式积分外力产生一个新的虚拟末端状态，因此属于直接 Cartesian impedance。

### 4.2 笛卡尔导纳控制

导纳控制的输入是估计外 wrench $w_{\mathrm{ext}}$，输出是期望运动。当前 6D 虚拟动力学可写为：

$$
M_a\dot\nu_a+B_a\nu_a+K_a\xi_a
=w_{\mathrm{ext}},
$$

$$
\dot\xi_a=\nu_a,
\qquad
\nu_{\mathrm{yield}}=\nu_a+K_{\mathrm{off}}\xi_a.
$$

这里 $\xi_a$ 是虚拟 carriage 相对 nominal 的 6D 位移/姿态偏移，$\nu_a$ 是虚拟 carriage 的 6D 速度。该系统的作用是把外力转换成受质量、阻尼和弹簧约束的让位速度：力越大，虚拟状态越偏；阻尼和弹簧决定响应速度、超调与回归速度。

离散化时，控制周期为 $\Delta t=0.04\,\mathrm{s}$，代码在一个策略周期内使用多个子步积分：

$$
\nu_{k+1/2}
=\operatorname{clip}\left[
\nu_k+\frac{\Delta t}{N_s}M_a^{-1}
\left(w_k-B_a\nu_k-K_a\xi_k\right),
-\nu_{\max},\nu_{\max}\right],
$$

$$
\xi_{k+1/2}
=\operatorname{clip}\left[
\xi_k+\frac{\Delta t}{N_s}\nu_{k+1/2},
-\xi_{\max},\xi_{\max}\right].
$$

重复 $N_s$ 次后，将：

$$
a_{1:6}=\operatorname{clip}\left(
\frac{R_6\left(\nu_a+K_{\mathrm{off}}\xi_a\right)}
{[v_{\max},v_{\max},v_{\max},\omega_{\max},\omega_{\max},\omega_{\max}]},
-1,1\right)
$$

作为统一 7D action 的 6 个 yielding 通道；第 0 维由 yielding action 的幅度或测量误差产生 WBC slowdown 请求。随后仍然经过共享 action filter 和速度伺服，不直接绕过安全层。

当前代码中的核心状态更新位于 `scripts/run_vmc_6d_constrained_push_20260918.py`：

```python
def act(self, wrench_world, dt=0.04):
    wrench = np.asarray(wrench_world, dtype=float)
    self.filtered += (1.0 - np.exp(-dt / self.filter_tau)) * (
        wrench - self.filtered
    )

    w = self.R6.T @ self.filtered
    w = np.sign(w) * np.maximum(np.abs(w) - self.deadband, 0.0)
    w = self.sigma * np.tanh(w / self.sigma)

    for _ in range(20):
        spring = self.sigma * np.tanh(
            self.k * self.offset / self.sigma
        )
        acc = (w - self.b * self.velocity - spring) / self.mass
        self.velocity = np.clip(
            self.velocity + acc * (dt / 20.0),
            -self.vmax, self.vmax,
        )
        self.offset = np.clip(
            self.offset + self.velocity * (dt / 20.0),
            -self.xmax, self.xmax,
        )

    residual = self.velocity + self.offset_gain * self.offset
    action = np.zeros(7)
    action[1:] = np.clip(
        self.R6 @ residual / self.action_limits,
        -1.0, 1.0,
    )
    action[0] = np.clip(
        np.linalg.norm(action[1:]) / np.sqrt(6.0), 0.0, 1.0
    )
    return action
```

对于当前的 student teacher 数据，`wrench_world` 来自 `fr3_contact_interface_20260917.py` 的因果关节负载观测器和 Jacobian 等效 wrench；仿真中的 `contact_force`、障碍物位姿和事件时钟只用于审计与任务 gate，不能作为部署 observation。`vmc_compliance_baseline.py` 的 `SpringCarriageVMC`/`VMCComplianceAdapter` 是同一导纳思想的兼容封装，并额外把位姿/速度误差转换为可部署的 WBC slowdown 通道。

### 4.3 两者的差异与公平比较

| 项目 | 笛卡尔阻抗 | 笛卡尔导纳 |
|---|---|---|
| 主要输入 | 位姿误差、twist 误差 | 估计外力/力矩，及其因果滤波值 |
| 内部状态 | 通常无显式虚拟末端状态 | 6D 虚拟位移/速度状态 |
| 直接输出 | Cartesian wrench，再映射为 $J^Tw$ | yielding twist/offset，再映射为关节速度 |
| 柔顺调节量 | $K,D,F_{\max},M_{\max}$ | $M_a,B_a,K_a,K_{\mathrm{off}},\nu_{\max},\xi_{\max}$ |
| 主要优点 | 结构简单、轨迹回归直接 | 可表达持续接触中的让位和滑移 |
| 主要风险 | 刚度过高时冲击/力矩大，过低时回归慢 | 估计力噪声、积分漂移和参数耦合 |
| 当前代码 | `_direct_cartesian_wrench` | `SixDVirtualDynamics`, `SpringCarriageVMC` |

两种 baseline 都应在相同场景、相同 nominal WBC、相同 action/torque safety gate 和相同 task-success gate 下比较。不能因为阻抗控制器输出的是 torque、导纳控制器输出的是 velocity residual，就给它们使用不同的物理步长、不同的碰撞模型或不同的成功标准。

## 5. Teacher 数据场景

当前基础 teacher bank 包含四个场景族：

| 场景 | 目标行为 | 主要随机化 |
|---|---|---|
| 球撞 `ball` | 短时冲击后让位、衰减振荡、回到名义抓取轨迹 | 球质量、速度、半径、入射角、碰撞时刻、机械臂姿态 |
| 持续棍推 `push` | 障碍物不主动退出时保持柔顺，沿棍/局部约束滑移并重新尝试抓取 | 推动角度、高度、行程、持续时间、载荷、前后挡板几何 |
| 抓取前桌角 `corner` | 末端接触桌角后滑移脱离，继续完成抓取 | 桌角位置、姿态、接触方向、目标位置 |
| 持物厚桌角 `table_corner` | 抓起物块后接触有厚度的桌侧边缘，柔顺蹭过并稳定放置 | 桌角厚度/位置、物块位置、持物质量、接触角度 |

数据采集必须保留真实 MuJoCo 刚体接触，禁止通过 teleport、焊接物块到手、隐藏穿模或预设 student 事件时钟制造成功轨迹。每条轨迹都记录 contact pair、penetration、task stage、末端状态、关节力矩和 teacher action，并对物理失败轨迹留档而不是静默删除。

### 5.1 数据划分

正式划分按 `scene / physical fixture / VMC parameter group` 进行，而不是把同一 rollout 的相邻时间窗随机拆分：

- 同一物理 fixture 不能同时出现在 train、validation 和 test；
- 同一 parent parameter/fixture group 的增强样本继承原 split；
- 重复轨迹按 observation + action hash 去重；
- normalization 只使用未增强的训练轨迹计算；
- 办公室复杂场景不进入训练集或模型选择集。

Teacher action 是最终执行的 7 维柔顺动作，不是 stiffness、damping 或其他 VMC 参数。Student 学习的是：

$$
\pi_{\theta}:o_{0:t}\longmapsto a_t,
$$

而不是：

$$
\pi_{\theta}:o_t\longmapsto(K,B,M).
$$

## 6. Student Observation

当前目标 observation contract 是 48 维本体感觉输入：

| 信号 | 维度 | 部署来源 |
|---|---:|---|
| 关节位置 $q$ | 7 | joint encoder |
| 关节速度 $\dot q$ | 7 | encoder differentiation / driver |
| 名义 WBC task twist | 6 | nominal controller |
| WBC pose error | 6 | robot state + nominal target |
| WBC twist error | 6 | robot state + nominal command |
| 估计关节外载荷 | 7 | momentum/load observer |
| 估计末端 6D wrench | 6 | joint load + Jacobian |
| 当前名义路径方向 | 3 | nominal controller |
| **总计** | **48** | 无视觉、无接触真值、无场景 ID |

仓库仍兼容早期 45D contract，其中末端 wrench 只有三维力；正式后续实验应优先使用统一 48D contract，并在 checkpoint 中明确写入 contract name，避免 45D/48D 模型混用。

## 7. MLP 与 ESN

### 7.1 MLP baseline

匹配版 MLP 使用：

```text
48D observation -> Linear(128) -> tanh
                -> Linear(128) -> tanh
                -> Linear(7)   -> bounded action
```

48D 输入时可训练参数量为 `23,687`。MLP 没有显式递归状态，只能从当前 observation 估计动作，因此是较强但无内部时序记忆的 data-driven baseline。

### 7.2 Proposed nonlinear ESN

当前主 ESN 使用 128 个固定 reservoir units，并把 reservoir 分成多时间尺度状态：

$$
x_t=(1-\alpha)x_{t-1}
+\alpha\tanh(W_{\mathrm{in}}\bar o_t+W_{\mathrm{res}}x_{t-1}).
$$

当前时间常数簇为 `0.08 s / 0.4 s / 1.6 s`，用于同时表达冲击瞬态、持续推动和较慢的接触恢复。Reservoir 的输入矩阵和递归矩阵在标准 teacher-student 训练中固定，不通过 backpropagation 更新；训练的是读出部分。

非线性 ESN head 为：

```text
[48D normalized observation, 128D reservoir state]
    -> Linear(128) -> tanh -> Linear(7) -> bounded action
```

其可训练参数量为 `23,559`，与 48D MLP 的 `23,687` 基本匹配。这样比较时，ESN 的优势不能来自额外训练预算或更大的可训练网络，而应来自固定 reservoir 所提供的因果历史状态。

仓库同时保留经典 linear-readout ESN：

```text
[observation, reservoir state, bias] -> weighted ridge regression -> 7D action
```

48D 输入和 128 reservoir 时只有 `1,239` 个可训练 readout 参数。它用于验证“经典低容量 ESN 是否足够”，不能与参数匹配的 nonlinear ESN 混为一谈。

### 7.3 公平训练协议

MLP 和 nonlinear ESN 共享：

- 完全相同的 train/validation/test episode；
- 相同 observation 和 7D action label；
- 按 `scene -> episode -> time` 的均衡采样；
- 相同 batch size、优化器、更新步数、action-scaled MSE 和随机种子集合；
- 仅依据基础场景 validation 指标选择 checkpoint；
- 相同 action filter、WBC、速度伺服和 torque safety stack；
- 复杂办公室场景不参与训练和选模。

当前主线是 supervised action distillation，不是从零 RL。RL、CEM readout refinement 和 torque takeover 代码仍保留用于消融或历史复现，但不能被描述成当前默认 ESN teacher-student 训练流程。尤其是 mixed-CEM refinement 只有在完成公平 BC 对比后才能作为独立扩展实验报告。

## 8. 测试场景与泛化目标

四个基础场景用于 teacher 搜索、数据审计和源域留出验证。最终论文测试应冻结为更接近真实办公室的组合环境，包括：

- 新桌面、柜体、柱子和水杯布局；
- 未参与训练的接触物体和几何尺寸；
- 不同机械臂姿态、接触部位和持物状态；
- 球撞后继续运动、持续人手/棍推动、桌边滑移等事件组合；
- 事件顺序、持续时间和入射方向变化；
- 只从 robot-side signals 判断何时让位、保持接触或重新回轨。

正式测试时，VMC baseline 可以在测试场景上依据预先声明的预算调参；MLP/ESN 必须保持冻结，不能读取测试标签或重新训练。开发过程中反复看过并修改过的办公室场景只能作为 development acceptance set，最终 paper test 需要另行冻结未见条件。

## 9. 评估协议

任务成功是前置 gate，柔顺指标不能掩盖抓取失败、物块滑落、未完成放置或绕开障碍后不再执行任务。当前主要指标包括：

| 类别 | 指标 |
|---|---|
| 任务 | grasp/lift/place success、strict success、完成时间 |
| 跟踪 | 接触后的末端 tracking RMSE、endpoint error、回轨时间 |
| 运动 | speed distribution、P95/peak speed、acceleration、jerk、突然前冲检测 |
| 接触 | peak force、impulse、contact duration、最大 penetration、接触部位 |
| 执行器 | peak motor torque、torque ratio、hard-limit frames、torque-rate saturation |
| 泛化 | 各场景成功率、未见 fixture 最坏值、跨事件组合退化幅度 |

多指标结果不应被随意压成一个未经验证的总分。当前做法是：先通过任务/物理有效性 gate，再报告 tracking、速度/平滑性、接触力和电机力矩的 Pareto 关系、中位数及最坏值。

## 10. 仓库结构

```text
SII_compliance/
├── README.md                              # 当前项目总览
├── code/
│   ├── mujoco_6d_vmc_benchmark/           # 当前主线
│   │   ├── SOURCE_GUIDE.md                # 服务器源码导出与复现说明
│   │   ├── CODE_ORGANIZATION.md            # 当前主线/legacy/实验入口分层
│   │   ├── configs/                       # 可复现开发场景配置
│   │   ├── docs/                          # 当前协议、路线图和必要方法说明
│   │   ├── scripts/                       # 兼容路径保持扁平；入口按 scripts/README.md 分层
│   │   │   └── README.md                  # canonical、baseline、legacy 入口索引
│   │   ├── tests/                         # 协议与接口测试
│   │   └── tools/                         # 源码来源校验工具
└── reports/                               # 早期交接与方向文档
```

### 历史代码与实验归档

为了让 GitHub `main` 只保留当前论文主线代码，整理前的完整快照和本次移出的历史内容已存放在 DGX Spark：

```text
/home/arm1/SII_compliance_archive/20260923_origin_main_5d0e457/
/home/arm1/SII_compliance_archive/legacy_20260923_removed_from_main/
```

其中：

- `20260923_origin_main_5d0e457/SII_compliance_origin_main_5d0e457.tar.gz` 是整理前 `origin/main`（commit `5d0e4574b5708b5131046f8b9d141633d399f726`）的完整 tracked-file 快照；
- `legacy_20260923_removed_from_main/removed_files.tar.gz` 是本次从 GitHub 主线移出的历史代码、旧项目、旧结果和旧报告附件；
- 两个目录都包含 SHA-256 清单，可用于逐文件恢复和校验；
- 同一整理前快照也保留在 GitHub 分支 `archive/origin-main-20260923`，但正式开发只使用 `main`。

本机项目 GIF 的历史归档（按文件日期 / 算法 / 场景分类）位于 DGX Spark：

```text
/home/arm1/SII_compliance_archive/mac_gifs_20260923/
```

该目录包含 `inventory.json`、`SHA256SUMS` 和 `METADATA.txt`；归档共 443 个 GIF。为避免误删，桌面目录 `/Users/hwy/Desktop/demo_0923` 未纳入归档清理，仍保留在本机。

当前主线中仍保留少量被 office/runtime 动态导入的兼容模块；它们属于运行时支持，不代表对应的历史算法仍是论文主结果。

关键代码入口：

- `scripts/paper_mpc_wbc.py`：NUS paper control layer 的固定基座复现；
- `scripts/fixed_panda_wbc.py`：resolved-rate FR3/Panda WBC；
- `scripts/wbc_velocity_residual_core.py`：共享 7D action、安全过滤和速度伺服；
- `scripts/fr3_contact_interface_20260917.py`：因果 load observer 和部署边界；
- `scripts/run_vmc_6d_constrained_push_20260918.py`：6D VMC teacher；
- `scripts/search_unified_6d_teacher_20260921.py`：统一六维 VMC 参数搜索和 Pareto 候选；
- `scripts/build_current_teacher_bank_20260921.py`：当前 teacher bank 构建；
- `scripts/audit_four_scene_dataset_20260918.py`：数据泄漏、物理组和来源审计；
- `scripts/train_matched_action7_20260921.py`：匹配 MLP/nonlinear ESN/linear ESN 训练；
- `scripts/run_matched_stage1_20260921.py`：多 seed 训练、选模和开发迁移评估；
- `scripts/evaluate_matched_guarded_push_20260921.py`：冻结 student 的闭环棍推评估；
- `scripts/office_complex_scene_v5_20260917.py`：复杂办公室开发场景；
- `scripts/current_student_policy_20260921.py`：当前 checkpoint contract 和推理加载器。

## 11. 环境与快速检查

推荐使用 Linux、NVIDIA GPU 和 EGL headless rendering。准备 MuJoCo Menagerie，至少包含：

```text
<menagerie>/franka_fr3/
<menagerie>/franka_emika_panda/
```

安装研究依赖：

```bash
cd code/mujoco_6d_vmc_benchmark
python -m pip install -r requirements-research.txt
export MUJOCO_GL=egl
```

校验服务器源码导出和 Python 语法：

```bash
python tools/check_source_export.py
```

运行球撞 source smoke：

```bash
python scripts/run_source_demo.py \
  --config configs/ball_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-smoke/ball \
  --smoke
```

运行当前实体工位棍推开发场景：

```bash
python scripts/run_source_demo.py \
  --config configs/workstation_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-demo/workstation \
  --render
```

训练单个匹配模型：

```bash
python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/new_training_run \
  --model esn_nonlinear \
  --seed 20260921
```

`--model` 可选 `mlp`、`esn_nonlinear` 或 `esn_linear`。训练脚本要求数据目录存在 `READY.json` 和经过审计的 manifest，并拒绝覆盖已有输出目录。

## 12. 当前状态

截至 2026-09-21：

- FR3/Panda MuJoCo 名义 WBC、统一速度残差动作接口和安全栈已经实现；
- 球撞、持续棍推、抓取前桌角和持物厚桌角四类基础场景已有 VMC teacher/search/audit 代码；
- 当前源码支持 45D 历史 observation 和目标 48D proprioceptive observation；
- 匹配参数量的 MLP、nonlinear ESN，以及经典 linear-readout ESN 训练代码已经实现；
- 数据构建代码能够按 fixture/parameter group 做互斥 split，并检查重复轨迹和跨 split 泄漏；
- 实体工位、挡板约束和复杂办公室开发场景已经进入代码库；
- 当前仓库提交的是源码、配置和协议，不包含服务器上的 teacher 数据、模型 checkpoint、GIF/MP4 或大型输出；
- 正式论文级 teacher bank、冻结 checkpoint、最终办公室 blind test 和真实 FR3 sim2real 结果仍需在固定协议下重新生成并归档。

当前不能宣称的结论：

- 不能仅凭开发 GIF 宣称 ESN 已经优于全部 baseline；
- 不能把基础场景留出条件称为真实办公室泛化；
- 不能把 MuJoCo force threshold 当作真实 FR3 安全认证；
- 不能把 teacher 使用的任务成功监督或仿真状态描述成 student 部署输入；
- 不能把历史 RL/CEM 代码描述成当前默认训练方法。

## 13. 下一阶段

1. 用统一 48D observation 重新生成并审计四场景 VMC teacher bank；
2. 扩大每个场景的姿态、入射角、接触部位、载荷和接触时长覆盖；
3. 在相同数据、参数量、seed 和训练预算下完成 MLP 与 nonlinear ESN 多 seed 训练；
4. 冻结模型和所有模型选择规则；
5. 冻结独立复杂办公室 test suite，禁止继续按测试结果修改场景或模型；
6. 对固定 VMC、MLP、linear ESN、nonlinear ESN 和声明的经典控制 baseline 做同协议闭环评估；
7. 完成观测噪声、控制延迟、摩擦/质量变化和 contact-model randomization；
8. 将 `ActionBoundary`、load observer 和 torque safety stack 对接真实 FR3，并先从低速、低能量、外部急停保护的实验开始。

更详细的源码说明、已知限制和 provenance 校验见：

- [`code/mujoco_6d_vmc_benchmark/SOURCE_GUIDE.md`](code/mujoco_6d_vmc_benchmark/SOURCE_GUIDE.md)
- [`code/mujoco_6d_vmc_benchmark/docs/server_source_20260923.json`](code/mujoco_6d_vmc_benchmark/docs/server_source_20260923.json)
