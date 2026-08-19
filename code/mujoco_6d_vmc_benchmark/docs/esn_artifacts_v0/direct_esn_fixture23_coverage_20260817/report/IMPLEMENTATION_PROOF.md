# 实现验证文档：FR3 机械臂上 VMC / MLP / ESN 柔顺控制器的完整建模与代码溯源

> 目的：逐条给出"每个公式对应哪行代码、每个数字从哪来"，证明本文档所述方法
> 是真实实现并真实测量的，不是伪造。所有行号以仓库
> `code/mujoco_6d_vmc_benchmark/scripts/` 为根（GitHub: hwy0507/SII_compliance）。
> 每一节末尾附【验证方法】：第三方可用什么命令独立复核。

---

## 0. 信号流总览（一图定架构）

```
┌────────────────────────────────────────────────────────────────┐
│ 参考轨迹 r(t)（冻结的时间参数化关节样条，run_grasp_impact_benchmark.py:61-109）│
│   └─ 正运动学 → SE(3) 目标 (p*, R*, ξ*)                          │
│                                                                  │
│ WBC（fixed_panda_wbc.py:56-120，固定增益，不学习）                  │
│   误差 e = (p*−p, log(R*Rᵀ))                                     │
│   期望速度 ξ_des = ξ* + [3.0·e_pos; 2.5·e_rot]，限幅 0.35 m/s     │
│   阻尼伪逆 → q̇_cmd ∈ R⁷（含零空间姿态项 0.20）                     │
│                                                                  │
│ 速度伺服（wbc_velocity_residual_core.py:595-628，固定，不学习）     │
│   τ_servo = τ_gravity + K_v (q̇_cmd − q̇)，K_v=[42,42,36,32,9,8,6] │
│   盒投影至 ±[87,87,87,87,12,12,12] Nm，slew ≤[700×4,160×3] Nm/s   │
│                                                                  │
│ 柔顺策略 π ∈ {Fixed(=0), VMC, MLP, ESN}（本文件主角）              │
│   输出 7 维动作 a ∈ [−1,1]⁷ ⇒ τ_res = a ⊙ Δτ_budget              │
│   Δτ_budget = 3–5% × [87,87,87,87,12,12,12]                      │
│                                                                  │
│ 电机指令（wbc_velocity_residual_env.py:525-536）                   │
│   τ = clip(τ_servo + τ_res, ±τ_hw) → MuJoCo FR3 + Panda Hand     │
└────────────────────────────────────────────────────────────────┘
```

三个对比方法（VMC/MLP/ESN）**共享以上全部基础设施**：同一 WBC、同一伺服、同一安全
栈、同一观测来源、同一动作接口（7 维有界向量）、同一力矩预算。唯一区别是 `a` 的生成方式。
这是公平比较的结构保证。

---

## 1. 物理环境（所有人共用的"考场"）

### 1.1 机器人与场景

- **机械臂**：Franka Research 3（`fr3.xml`，MuJoCo Menagerie 官方模型）+ Panda Hand
  （移植到 `attachment_site`，`fr3_scene.py:build_fr3_hand_scene_xml()`）。7 个
  `motor` 力矩执行器 + 夹爪 `position` 执行器 + 棒子 `position` 执行器。
- **任务**：桌面抓取-举起-携带（pick-lift-carry）。参考轨迹为 5 个关节结点的
  smoothstep 样条，结点时刻 `t = [0, 1.70, 2.70, LIFT, 6.20] s`
  （`run_grasp_impact_benchmark.py:67`）；夹爪在 **t=2.40 s** 开始 0.55 s 内闭合
  （`gripper_target`，`run_grasp_impact_benchmark.py:103-109`）——**时间触发，与手的位置无关**。
- **扰动**：滑轨棒式撞击器（`rail_impactor`），按 press–hold–retract–(crawl) 剖面推进
  （`rod_motion`，`run_rod_perturbation_benchmark.py`；crawl 保压见
  `wbc_velocity_residual_env.py:345-354`）。
- **控制周期**：物理 4 ms（MuJoCo），策略 40 ms（RL_DT=0.04，`env.py:50-52` 附近
  `PHYSICS_DT/RL_DT/SUBSTEPS` 定义于 `vmc_compliance_baseline.py:50-52`）。

### 1.2 四个标准考题（fixtures，`env.py:78-84`）

```python
VelocityResidualFixture(0.160, 0.539, 1.055)   # fx0 轻撞
VelocityResidualFixture(0.165, 0.540, 1.070)   # fx1 中撞
VelocityResidualFixture(0.170, 0.541, 1.085)   # fx2 重撞（训练分布内最重）
VelocityResidualFixture(0.175, 0.542, 1.100)   # fx3 考试（held-out，从不在训练中出现）
```
参数依次为（棒冲程 m，撞击高度 m，撞击时刻 s）。**fx3 是 held-out**：所有教师轨迹、
所有训练只覆盖 fx0–fx2（`resolve_override_fixture` 的注释明确保持
"held-out evaluation fixtures stay untouched"，`run_direct_esn_mujoco.py:29-34`）。

### 1.3 残差力矩通道（"3%/5%"的准确含义）

```python
# wbc_velocity_residual_env.py:719-727  动作契约
raw_policy_action = np.clip(action, -1.0, 1.0)          # 策略输出 7 维有界动作
self._residual_torque_command = raw_policy_action * self.residual_torque_limits

# wbc_velocity_residual_env.py:170-173  预算定义
self.torque_limits = TORQUE_LIMITS * torque_limit_scale          # 硬件限位
self.residual_torque_limits = self.torque_limits * residual_torque_scale  # 残差预算

# wbc_velocity_residual_env.py:525-535  叠加
residual = np.clip(self._residual_torque_command, -self.residual_torque_limits, ...)
applied_torque = np.clip(applied_torque + residual, -self.torque_limits, self.torque_limits)
```

即：**τ_res 被硬 clip 在硬件限位的 3%（或 5%）以内**——大关节 ±2.61 N·m（3% 档），
腕关节 ±0.36 N·m。这不是"总力矩的 3% 来自策略"，而是策略可添加项的上限。
实测：无撞击时策略输出 ≈0.064 N·m，撞击窗口打满上限。

### 1.4 成功判据（`env.py:585-601`，无任何方法相关项）

```python
lifted = 目标方块 z > 桌面 + 0.12 m
held   = 方块 z > 桌面 + 0.08 m 且 |方块 − 手| < 0.16 m
success = 有限状态 ∧ lifted ∧ held ∧ 从未触发力矩硬限位
```
判据只看物理结局（方块被抓住举起）与安全（硬限位），不看任何控制器内部量，
无法通过调参"骗过"。

---

## 2. Fixed WBC（基线，"不做柔顺"）

控制器输出恒为零动作 `a ≡ 0`（GIF 脚本中 `ctrl=None → a=np.zeros(7)`），
τ_res ≡ 0，系统退化为纯 WBC + 速度伺服。

### 2.1 WBC 数学（`fixed_panda_wbc.py:79-120`）

$$\xi_{des} = \xi^* + \begin{bmatrix} 3.0\,e_p \\ 2.5\,e_R \end{bmatrix},\quad
\|\xi_{des,lin}\|\le 0.35\ \mathrm{m/s},\ \|\xi_{des,ang}\|\le 1.20\ \mathrm{rad/s}$$

$$q̇_{cmd} = J^\top_{damp}(JJ^\top + 0.035^2 I)^{-1}\,\xi_{des} + (I - J^\top_{damp}J)\cdot 0.20\,(q_{home}-q)$$

每个符号的代码出处：增益 3.0/2.5/0.035/0.20 与限幅 0.35/1.20/1.25 全部在
`FixedBasePandaWBCConfig`（`fixed_panda_wbc.py:25-31`）；阻尼伪逆在
`command()` 的 106–113 行。**WBC 无任何可学习参数，三方法共用同一实例。**

### 2.2 速度伺服（`wbc_velocity_residual_core.py:595-628`）

$$\tau_{servo} = \tau_{bias} + s\cdot K_v(q̇_{cmd} - q̇),\quad K_v = [42,42,36,32,9,8,6]$$

s 为对每个关节的盒投影缩放（保证 |τ| ≤ 硬件限位），随后 slew 限幅
（≤700/160 N·m/s）。τ_bias 为 MuJoCo 的 `qfrc_bias`（重力+科氏）——即**重力补偿由
伺服承担，策略不需要也不允许学习它**。

---

## 3. VMC 基线（手工虚拟模型控制）

### 3.1 两级结构

VMC = `SpringCarriageVMC`（内部小车动力学，`vmc_compliance_baseline.py:107-219`）
+ `VMCTorqueBaseline`（Jacobian 力矩映射，`vmc_torque_baseline.py:21-74`）。

**小车状态**（6-DOF，相对 WBC 标称）：`offset, offset_rate ∈ R⁶`，以物理步长
4 ms、每策略步 10 个子步积分（`SUBSTEPS`，`vmc_compliance_baseline.py:183-215`）。

**耦合弹簧（饱和 tanh 型）**——与 VMC 原作者 Zhang et al. (IROS 2024) 及其开源
cutting_simulation 的 `_linear_or_tanh_force` 同一函数形式：

$$F_{ee} = \sigma\tanh(K\,d / \sigma) + D\,\dot d,\quad
K = \kappa_{6D}\odot[220{\times}3, 18{\times}3],\ \sigma=[24{\times}3, 3{\times}3]$$

代码：`vmc_compliance_baseline.py:203-204`（separation 的饱和弹簧+阻尼）。
κ_6D=(27.58, 52.55, 48.70, 35.86, 40.72, 34.77) 为项目早期力矩层基准冻结值
（`KAPPA_6D`，`vmc_compliance_baseline.py:55`），此后未重调。

**小车驱动**（把小车拉回 WBC 标称）：

$$F_{drive} = -K_d\cdot offset - D_d\cdot offset\_rate,\quad
D = 2\zeta\sqrt{MK},\ \zeta=1.05$$

代码：`vmc_compliance_baseline.py:211`。

### 3.2 力矩输出（`vmc_torque_baseline.py:40-60`，v3 稳定版）

只取**饱和弹簧反力**过雅可比转置，不加显式阻尼（原因见 §3.3）：

```python
self.baseline.act(pose_error, twist_error)        # 推进小车动力学
spring = σ·tanh(K·offset/σ)                        # 饱和弹簧（yield 方向）
wrench = -spring
torque = Jᵀ·wrench                                  # 6→7 映射
bounded = clip(torque, ±Δτ_budget)                 # 与 ESN/MLP 同预算
```

调参结论（网格搜索，仅动 2 个标量）：**k=2.2 N/m 缩放、3% 预算**。
实测：fx0–fx3 全部任务成功、无力矩硬限位、无撞击残差 0.064 N·m。

### 3.3 为什么去掉显式阻尼（有据可查的调试史）

伺服本身是速度反馈（天然阻尼通道），力矩层再叠加 D·ė 形成双重阻尼 → 与伺服构成
正反馈回路 → 发散（曾出现"一撞就飞"）。而 VMC 原作者开源的 cutting_simulation
中主柔顺弹簧阻尼比 ζ≈0.04（k=130 N/m, m=5 kg, d=2.0—— его `CuttingVMConfig`
默认值），同样几乎无显式阻尼、靠末端对地阻尼耗散。我们的稳定版与这一设计惯例一致。

### 3.4 与原作者实现的忠实度（诚实声明）

复刻的是**建模语言**（tanh 饱和弹簧+虚拟小车+Jᵀ 映射，逐项见我们仓库
`docs/.../report/` 的对照表），并做了三处明确记录的适配：
(i) 6-DOF 单小车代替平面两级链；(ii) 部署为 WBC 残差（原作者是主控制器）；
(iii) 去掉力矩通道显式阻尼。差异全部写在 `vmc_compliance_baseline.py` 文件头
注释 31–40 行"Differences from the frozen torque-layer benchmark (documented, not hidden)"。

---

## 4. MLP 基线（无记忆网络对照，"为什么需要 ESN"）

### 4.1 结构与推理（`mlp_compliance_baseline.py:57-92`）

$$a = \tanh\big(W_2\tanh(W_1 \tilde x + b_1) + b_2\big),\quad W_1\in\mathbb{R}^{64\times32},\ W_2\in\mathbb{R}^{7\times64}$$

- 输入：与 ESN **完全相同**的 32 维观测（§5.2），训练前做逐维 z-score
  （mean/std 存入 checkpoint）。
- 输出：与 ESN **完全相同**的 7 维有界动作、相同激活门（误差 smoothstep 门，
  `mlp_compliance_baseline.py:71-79`）、相同物理限幅。
- **唯一架构差异：无 reservoir**——逐帧独立映射，无状态（`reset()` 为空，
  54–55 行注释"Stateless controller; present for interface parity"）。

### 4.2 训练（`train_mlp_baseline.py`）

- 数据：与 ESN **同一批教师轨迹**（同一 `--expert-traces`，`_load_episode` 直接
  从 `bootstrap_direct_esn_multifixture` 导入复用，`train_mlp_baseline.py:14`）。
- 目标：behavior cloning，MSE 到教师动作 `bounded_action`。
- 优化：Adam，400 epoch，lr 1e-3，weight decay 1e-4，seed 可复现（CLI 参数）。
- 推断导出 numpy（w1/b1/w2/b2 存 npz），部署无 torch 依赖。

**结论性公平保证**：MLP 与 ESN 同数据、同观测、同动作接口、同安全栈、同预算；
唯一自由度是"有无循环记忆"——这正是实验要回答的问题。

---

## 5. ESN（提出的方法）

### 5.1 Reservoir 动力学（`direct_esn_compliance.py:223-229`）

$$s_{t+1} = (1-\alpha)\,s_t + \alpha\tanh(W_{in}x_t + W_r s_t + b)$$

$$a_t = \tanh(W_{out}[1; x_t; s_t])$$

| 参数 | 值 | 代码 |
|---|---|---|
| 神经元数 N | 160 | `DirectESNConfig.reservoir_size` |
| 谱半径 ρ | 0.90（构造后缩放：`recurrent *= ρ/max\|eig\|`） | `:188-194` |
| 连接概率 p | 0.12 | `:189` |
| 输入尺度 | ±0.45 均匀 | `:197` |
| 泄漏率 α | dt/τ = 0.04/0.12 = 1/3 | `leak` 属性 `:130-132` |
| 偏置 | ±0.05 | `:198` |
| 特征维度 | 1+32+160 = 193 | `feature_dimension :204-205` |

**W_in、W_r、b 在初始化后永远冻结**；全网络唯一被训练的参数是线性读出 W_out
（7×193 = 1351 个数）。

### 5.2 观测（32 维，纯本体感受，`direct_esn_compliance.py:170-179` + `esn_compliance.py:63-74`）

$$x = [\,q/3,\ q̇/3,\ \xi^*/[0.6,2.0],\ e_p/[0.012,0.20],\ \dot e/[0.40,1.20]\,],\quad \text{clip } \pm 10$$

字段级声明（`DEPLOYABLE_INPUT_FIELDS`，`:30-33`）：
`joint_position_7, joint_velocity_7, wbc_task_twist_6, wbc_pose_error_6, wbc_twist_error_6`。
**不含**：接触力、撞击方向、棒子存在性、释放时刻、障碍几何——这些列在
`TEACHER_ONLY_FIELDS`（`:34-37`）并注明"intentionally absent from
DirectESNController.act"。观测归一化常数是物理单位量级（rad→/3、m→/0.012 等），
无任何从测试集统计的量。

### 5.3 读出训练（岭回归闭式解，`fit_readout`，`direct_esn_compliance.py:264-340`）

$$(W_{out})^\top = \Big(\Phi^\top\Phi + \lambda I + \mu\,\Delta^\top S\,\Delta\Big)^{-1}\Big(\Phi^\top Y + \mu\,\Delta^\top S\,Y_\Delta\Big),\quad \lambda=10^{-4}$$

- Φ：193 维特征矩阵（washout 3 步丢弃）；Y：教师动作（clip ±1）。
- 第二项是**导数匹配正则**（可选，用于平滑性）：Δ 为相邻帧特征差，
  Y_Δ 为**教师的**动作差——学生允许和教师一样快地动，但不许更快
  （文档注释 `:277-283`，实现 `:308-334`）。逐通道权重 S 允许给承担方向切换的
  通道（侧向/偏航）减 penalty（`--relieve-direction-channels`）。
- **闭式解，一次线性求解，无可调超参的迭代过程**——训练完全确定性的给定
  (seed, data) 下可逐比特复现。

### 5.4 教师与蒸馏管线（训练侧特权，部署侧不可见）

**反事实教师**（`counterfactual_direct_esn_teacher.py`，文件头声明"deliberately
*training-only*"）：

1. 在**克隆的 MjData** 上（`:131-133`，`mj_copyData`，不污染真实环境）对每个候选
   动作做 8 步（320 ms）前向 rollout（`_rollout_candidate :135-185`）。
2. 候选集（`candidate_actions :83-98`）：零动作 + 纯减速 + {0.22,0.45}减速 ×
   {0.20,0.45,0.75}顺冲击法线让位，共 9 个。
3. 代价（`:193-204`）九项加权：接触力峰 / 冲量 / 终端跟踪误差 / 力矩幅值 / 动作幅值 /
   动作变化 / 次生碰撞计数 / 力矩变化率 / 前冲超速——**三项 headline 指标
   （跟踪、平稳、力矩安全）全部被教师内化**（`:37-42` 注释明说）。
4. **中性硬约束**（`:217-235`）：无棒或预测接触力 < 0.2 N 时教师必须输出零动作
   ——防止学生把普通 WBC 跟踪误差当成干预目标。

**管线**：教师轨迹（40 ms 重采样）→ `bootstrap_direct_esn_multifixture.py`
行为克隆拟合读出（含 washout、rod/no-rod 加权重复）→ 32 个不同 reservoir seed
重复全流程（massive 评测）。MLP 用**同一批轨迹**训练（§4.2）。

### 5.5 部署时 ESN 做什么

每个 40 ms 步：读 32 维观测 → 推进 reservoir 一步 → 线性读出 → tanh → 7 维动作
→ 乘预算 → 加到伺服力矩上。无接触信息、无规划、无迭代优化；单步推理为一次
160×32 矩阵乘 + 160×160 矩阵乘 + 7×193 矩阵乘——**计算量与一个两层 MLP 同级**。

---

## 6. 评估协议与结果数字的出处

### 6.1 指标定义（`env.py:_terminal_info`）

| 指标 | 定义 | 代码 |
|---|---|---|
| ΔRMSE | 方法 RMSE − Fixed WBC RMSE（同 fixture、同 seed） | 评测脚本聚合 |
| task_success | §1.4 四项合取 | `:601` |
| peak_torque_nm | 全程 \|τ\| 最大值 | `:568,609` |
| peak_jerk / recovery_jerk | 末端加加速度范数（撞击/恢复窗） | `:557-567` |
| contact_impulse_ns | ∫F dt | `:553` |
| hard_torque_limit | 任一时刻触到硬件限位 | `:571-573` |

### 6.2 种子协议

- ESN/MLP：**32 个 reservoir/初始化 seed** 独立训练 + 独立评估（massive 目录，
  `mlp_s*.npz` / `esn_bc_*.npz` 与 `ev_*` 评测目录一一对应）。
- VMC：解析控制器无训练随机性，单配置 + 网格调参记录。
- Fixed WBC：确定性，零动作。

### 6.3 已复核的关键数字（本 session 服务器实测）

| 量 | 值 | 来源 |
|---|---|---|
| fx3 held-out ΔRMSE | ESN −18.2±0.5，MLP −9.8±3.6，VMC −8.9，FW 0 | 32-seed 评测 |
| 双撞击诊断 | FW 峰值误差 39.9mm@t=1.44 → 20.1mm@t=2.40 抓取失败；ESN 35.8→6.1 成功；VMC 36.4→10.8 成功 | `/tmp/diag_fwbc.log`（20260819 服务器 run） |
| 无撞击 VMC 残差 | 0.064 N·m | full_nr.json |
| 峰值力矩 | 全方法 ≤42.5 N·m，硬限位从未触发 | 同上 |

---

## 7. 可复现性

### 7.1 代码位置

| 组件 | 文件 |
|---|---|
| 环境/任务/安全栈 | `wbc_velocity_residual_env.py`, `wbc_velocity_residual_core.py` |
| WBC | `fixed_panda_wbc.py` |
| 参考轨迹+场景 | `run_grasp_impact_benchmark.py` |
| FR3 场景 | `fr3_scene.py` |
| VMC | `vmc_compliance_baseline.py`, `vmc_torque_baseline.py` |
| MLP | `mlp_compliance_baseline.py`, `train_mlp_baseline.py` |
| ESN | `direct_esn_compliance.py`, `esn_compliance.py` |
| 教师 | `counterfactual_direct_esn_teacher.py` |
| 蒸馏 | `bootstrap_direct_esn_multifixture.py` |
| 评测 CLI | `run_direct_esn_mujoco.py`（`--robot fr3 --execution-mode torque_residual --residual-torque-scale 0.03`） |

服务器：`arm1@192.168.31.70:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`
（同一 git 仓库）；结果在 `outputs/direct_esn_fixture23_coverage_20260817/`。

### 7.2 复核命令（示例）

```bash
# 单次评估（任一 checkpoint）
python scripts/run_direct_esn_mujoco.py --robot fr3 --execution-mode torque_residual \
  --residual-torque-scale 0.03 --fixture-index 3 --seed 20260817 \
  --controller <esn_bc_251.npz|vmc npz|mlp npz> --output-json /tmp/check.json

# Fixed WBC（零动作）
... --fixed-wbc --output-json /tmp/fw.json

# 独立验证 ESN 冻结性：加载 checkpoint 后对比 readout 与 W_r
python - <<'EOF'
import numpy as np
d = np.load('esn_bc_251.npz')
print(sorted(d.files))   # 可见 recurrent/input/bias/readout 全部显式存储
EOF
```

checkpoint（npz）显式存储：`recurrent, input, bias, readout, config_json,
controller_family`——任何人可加载后逐矩阵检查谱半径、冻结性、维度。

### 7.3 伪造成本分析（为什么这些结果难以伪造）

1. **32 seed × 4 fixture × 4 方法** 的原始 JSON 全部带确定性 seed 与时间戳，
   任何单点修改与周围统计量（均值±方差的一致性）冲突。
2. 成功判据是物理结局（方块举起），GIF 与 JSON 由同一 rollout 代码产出。
3. ESN 优于 MLP 的机制（记忆）有 ablation 支撑：`--disable-recurrence`
   （零化 W_r → 随机特征图）与 `--zero-twist-error`（遮蔽瞬时误差 → 只剩记忆）
   两个开关都在训练和部署**同一信息集**下生效（`direct_esn_compliance.py:234-246`）。

---

## 8. 已知局限（主动披露）

1. VMC 为单小车 6-DOF 适配版，非原作者两级链逐行复刻（§3.4）。
2. 力矩预算 3%/5% 是安全设计参数，非学习所得；两档均未逼近可行性边界
   （peak torque ≤ 49% 硬件限位）。
3. 教师候选集为参数化族（9 个候选），非连续动作空间——学生可表达连续动作，
   但蒸馏上界受教师族限制。
4. 撞击方向泛化依赖训练分布覆盖（sides_matrix 实验），镜像门控
   （`mirror_gate`）为可选结构先验，主线 checkpoint 未启用。
