# Data-Driven Compliance Control for FR3

> 更新日期：2026-09-21
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

仓库中早期的 Fetch、ManiSkill、PPO residual 路线仍作为历史代码保留，但已经不是当前研究主线。当前主要代码位于：

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

## 4. Teacher 数据场景

当前基础 teacher bank 包含四个场景族：

| 场景 | 目标行为 | 主要随机化 |
|---|---|---|
| 球撞 `ball` | 短时冲击后让位、衰减振荡、回到名义抓取轨迹 | 球质量、速度、半径、入射角、碰撞时刻、机械臂姿态 |
| 持续棍推 `push` | 障碍物不主动退出时保持柔顺，沿棍/局部约束滑移并重新尝试抓取 | 推动角度、高度、行程、持续时间、载荷、前后挡板几何 |
| 抓取前桌角 `corner` | 末端接触桌角后滑移脱离，继续完成抓取 | 桌角位置、姿态、接触方向、目标位置 |
| 持物厚桌角 `table_corner` | 抓起物块后接触有厚度的桌侧边缘，柔顺蹭过并稳定放置 | 桌角厚度/位置、物块位置、持物质量、接触角度 |

数据采集必须保留真实 MuJoCo 刚体接触，禁止通过 teleport、焊接物块到手、隐藏穿模或预设 student 事件时钟制造成功轨迹。每条轨迹都记录 contact pair、penetration、task stage、末端状态、关节力矩和 teacher action，并对物理失败轨迹留档而不是静默删除。

### 4.1 数据划分

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

## 5. Student Observation

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

## 6. MLP 与 ESN

### 6.1 MLP baseline

匹配版 MLP 使用：

```text
48D observation -> Linear(128) -> tanh
                -> Linear(128) -> tanh
                -> Linear(7)   -> bounded action
```

48D 输入时可训练参数量为 `23,687`。MLP 没有显式递归状态，只能从当前 observation 估计动作，因此是较强但无内部时序记忆的 data-driven baseline。

### 6.2 Proposed nonlinear ESN

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

### 6.3 公平训练协议

MLP 和 nonlinear ESN 共享：

- 完全相同的 train/validation/test episode；
- 相同 observation 和 7D action label；
- 按 `scene -> episode -> time` 的均衡采样；
- 相同 batch size、优化器、更新步数、action-scaled MSE 和随机种子集合；
- 仅依据基础场景 validation 指标选择 checkpoint；
- 相同 action filter、WBC、速度伺服和 torque safety stack；
- 复杂办公室场景不参与训练和选模。

当前主线是 supervised action distillation，不是从零 RL。RL、CEM readout refinement 和 torque takeover 代码仍保留用于消融或历史复现，但不能被描述成当前默认 ESN teacher-student 训练流程。尤其是 mixed-CEM refinement 只有在完成公平 BC 对比后才能作为独立扩展实验报告。

## 7. 测试场景与泛化目标

四个基础场景用于 teacher 搜索、数据审计和源域留出验证。最终论文测试应冻结为更接近真实办公室的组合环境，包括：

- 新桌面、柜体、柱子和水杯布局；
- 未参与训练的接触物体和几何尺寸；
- 不同机械臂姿态、接触部位和持物状态；
- 球撞后继续运动、持续人手/棍推动、桌边滑移等事件组合；
- 事件顺序、持续时间和入射方向变化；
- 只从 robot-side signals 判断何时让位、保持接触或重新回轨。

正式测试时，VMC baseline 可以在测试场景上依据预先声明的预算调参；MLP/ESN 必须保持冻结，不能读取测试标签或重新训练。开发过程中反复看过并修改过的办公室场景只能作为 development acceptance set，最终 paper test 需要另行冻结未见条件。

## 8. 评估协议

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

## 9. 仓库结构

```text
SII_compliance/
├── README.md                              # 当前项目总览
├── code/
│   ├── mujoco_6d_vmc_benchmark/           # 当前主线
│   │   ├── SOURCE_GUIDE.md                # 服务器源码导出与复现说明
│   │   ├── configs/                       # 可复现开发场景配置
│   │   ├── docs/                          # 协议、阶段报告和历史实验说明
│   │   ├── scripts/                       # WBC/VMC/MLP/ESN/场景/采集/评估代码
│   │   ├── tests/                         # 协议与接口测试
│   │   └── tools/                         # 源码来源校验工具
│   ├── whole-body-motion-control/         # NUS/移动抓取相关历史与集成参考
│   └── residual_compliance_fetch_server_20260706/
│                                           # 早期 Fetch/ManiSkill 柔顺研究，非当前主线
└── reports/                               # 早期交接与方向文档
```

关键代码入口：

- `scripts/paper_mpc_wbc.py`：NUS paper control layer 的固定基座复现；
- `scripts/fixed_panda_wbc.py`：resolved-rate FR3/Panda WBC；
- `scripts/wbc_velocity_residual_core.py`：共享 7D action、安全过滤和速度伺服；
- `scripts/fr3_contact_interface_20260917.py`：因果 load observer 和部署边界；
- `scripts/run_vmc_6d_constrained_push_20260918.py`：6D VMC teacher；
- `scripts/collect_four_scene_pareto_20260918.py`：四场景扫描和 Pareto 采集；
- `scripts/build_current_teacher_bank_20260921.py`：当前 teacher bank 构建；
- `scripts/audit_four_scene_dataset_20260918.py`：数据泄漏、物理组和来源审计；
- `scripts/train_matched_action7_20260921.py`：匹配 MLP/nonlinear ESN/linear ESN 训练；
- `scripts/run_matched_stage1_20260921.py`：多 seed 训练、选模和开发迁移评估；
- `scripts/evaluate_matched_guarded_push_20260921.py`：冻结 student 的闭环棍推评估；
- `scripts/office_complex_scene_v5_20260917.py`：复杂办公室开发场景；
- `scripts/current_student_policy_20260921.py`：当前 checkpoint contract 和推理加载器。

## 10. 环境与快速检查

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

## 11. 当前状态

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

## 12. 下一阶段

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
- [`code/mujoco_6d_vmc_benchmark/docs/server_source_20260921.json`](code/mujoco_6d_vmc_benchmark/docs/server_source_20260921.json)
