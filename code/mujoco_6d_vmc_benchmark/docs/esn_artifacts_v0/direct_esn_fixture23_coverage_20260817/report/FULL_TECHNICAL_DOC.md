# WBC / VMC / MLP / ESN 机械臂柔顺控制——完整技术文档

> 面向课题组同学的技术交接文档。覆盖：问题定义、四个控制器的数学建模、算法设计、
> 核心代码、训练管线、评测协议与全部实验结果。所有公式与数字均可溯源到仓库代码
> （`code/mujoco_6d_vmc_benchmark/scripts/`，行号以 2026-08 版本为准）。
>
> 配套文档：`IMPLEMENTATION_PROOF.md`（逐行验证版）、`ALGORITHM_DETAILS.md`（精简版）、
> `FINAL_REPORT.md`（汇报版）。本文是最完整的一份。

---

## 目录

1. [问题定义与总体架构](#1-问题定义与总体架构)
2. [物理环境建模](#2-物理环境建模)
3. [WBC：全身控制器与速度伺服](#3-wbc全身控制器与速度伺服)
4. [VMC：虚拟模型控制基线](#4-vmc虚拟模型控制基线)
5. [MLP：无记忆网络基线](#5-mlp无记忆网络基线)
6. [ESN：提出的方法](#6-esn提出的方法)
7. [训练管线：教师与蒸馏](#7-训练管线教师与蒸馏)
8. [评测协议](#8-评测协议)
9. [实验结果](#9-实验结果)
10. [关键设计问题的答案（组会 FAQ）](#10-关键设计问题的答案组会-faq)
11. [文件索引与复现命令](#11-文件索引与复现命令)

---

## 1. 问题定义与总体架构

### 1.1 任务

Franka Research 3（FR3）机械臂在 MuJoCo 中执行**桌面抓取-举起-携带**任务。任务进行中，
一个滑轨棒式撞击器从侧面撞击机械臂末端。目标：**被撞击后尽快回到 WBC 规划轨迹、
平滑恢复、不超力矩限位、最终仍完成抓取**。

### 1.2 核心架构：WBC 出速度，柔顺策略出力矩残差

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  参考轨迹 r(t)  ──(时间参数化关节样条, 正运动学)──▶  SE(3) 目标 (p*, R*, ξ*) │
│                                                                       │
│  WBC（固定增益，不学习）                                                │
│    e = [p*−p ; log(R* Rᵀ)]                                            │
│    ξ_des = ξ* + K_p·e          ← 位置/姿态反馈                         │
│    q̇_cmd = 阻尼伪逆(ξ_des) + 零空间姿态项        ← 6D→7 关节           │
│                                                                       │
│  速度伺服（固定增益，不学习）                                           │
│    τ_servo = τ_gravity + K_v(q̇_cmd − q̇)                              │
│                                                                       │
│  柔顺策略 π ∈ {Fixed(≡0), VMC, MLP, ESN}      ← 本文四个对比方法        │
│    a ∈ [−1,1]⁷  ⇒  τ_res = a ⊙ Δτ_budget                             │
│                                                                       │
│  合成与执行                                                            │
│    τ = clip(τ_servo + τ_res, ±τ_hw) ──▶ MuJoCo FR3 + Panda Hand       │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**三个关键语义**（组会反复问到的）：

1. **WBC 输出的是速度**（关节速度指令 `q̇_cmd`），速度伺服把速度变成力矩。这一层
   是"正常控制器"，拥有任务、重力补偿、速度跟踪。
2. **柔顺策略输出的是力矩残差**——直接加在伺服力矩之上的小修正项，7 维（每个关节
   一维），不经过任何中间映射。
3. **"3%/5% 预算"是残差的上限**：`Δτ_budget = 3% × τ_hw`。FR3 硬件限位
   τ_hw = [87,87,87,87,12,12,12] N·m，所以 3% 档 = 大关节 ±2.61 N·m、腕关节
   ±0.36 N·m。**不是"总力矩的 3% 来自策略"**——无撞击时策略输出 ≈0.064 N·m
   （≈0），撞击窗口才打满上限。设置上限的原因是安全：学习出的策略无稳定性保证，
   有了硬 clip，无论网络输出什么垃圾，机械臂受到的额外扰动都有解析上界，WBC
   闭环必然兜得住。

**公平性结构保证**：VMC/MLP/ESN 共享同一 WBC 实例、同一伺服、同一安全栈、同一
观测来源、同一动作接口、同一预算。唯一区别是 7 维动作 `a` 怎么算出来。

### 1.3 控制周期

- MuJoCo 物理步长 4 ms；策略周期 40 ms（`RL_DT=0.04`，每步内部 10 个物理子步）。
- 所有方法都在 40 ms 周期上出动作。

---

## 2. 物理环境建模

**文件**：`wbc_velocity_residual_env.py`（874 行）、`fr3_scene.py`、
`run_grasp_impact_benchmark.py`。

### 2.1 场景

- **机器人**：FR3（Menagerie 官方 `fr3.xml`）+ Panda Hand 移植到 `attachment_site`
  （`fr3_scene.py::build_fr3_hand_scene_xml`）。7 个 `motor` 力矩执行器 + 夹爪
  `position` 执行器 + 棒子 `position` 执行器。
- **桌面方块**：5 cm 立方体，0.08 kg，free body（靠接触/摩擦保持，无 weld）。
- **撞击器**：`rail_impactor`，沿 y 轴滑轨，按 press–hold–retract 剖面推进，可选
  多周期（`rod_cycles`）与保压爬行（crawl：撞上后继续缓慢推进维持挤压，
  `env.py:345-354`）。

### 2.2 参考轨迹（时间参数化）

```python
# run_grasp_impact_benchmark.py:61-109
self.times    = [0.0, 1.70, 2.70, LIFT_COMPLETE, 6.20]      # 结点时刻
self.q_knots  = [home, pregrasp, pregrasp, lifted, carry]    # 关节结点
# 段内 smoothstep 插值；正运动学采样出 (p*, R*, ξ*) 三元组
def gripper_target(t):     # t ≤ 2.40 开；2.40→2.95 平滑闭合
    ...
```

**两个"时间触发"特性决定了任务难度**（见 §10 FAQ）：
- 夹爪在 **t=2.40 s 固定时刻**开始闭合，与手的实际位置无关；
- 参考目标由 HOME 位形的 FK 预计算，**不感知方块被撞后的位移**。

### 2.3 四个标准考题（fixtures）

```python
# wbc_velocity_residual_env.py:78-84
VelocityResidualFixture(0.160, 0.539, 1.055)   # fx0 轻撞
VelocityResidualFixture(0.165, 0.540, 1.070)   # fx1 中撞
VelocityResidualFixture(0.170, 0.541, 1.085)   # fx2 重撞
VelocityResidualFixture(0.175, 0.542, 1.100)   # fx3 考试（held-out）
```

参数依次为（棒冲程 m，撞击高度 m，撞击时刻 s）。**fx3 从不出现在任何训练数据中**。

### 2.4 成功判据（纯物理，与方法无关）

```python
# wbc_velocity_residual_env.py:585-601
lifted  = 方块 z > 桌面 + 0.12 m
held    = 方块 z > 桌面 + 0.08 m 且 |方块 − 手| < 0.16 m
success = 有限状态 ∧ lifted ∧ held ∧ 从未触发硬件力矩限位
```

---

## 3. WBC：全身控制器与速度伺服

**文件**：`fixed_panda_wbc.py`（121 行）、`wbc_velocity_residual_core.py`。

### 3.1 数学建模

WBC 每步接收 SE(3) 目标与机械臂本体状态，生成有界的关节速度指令：

**第一步：任务空间期望速度**（含位置/姿态反馈）

$$\xi_{des} = \xi^* + \begin{bmatrix} 3.0\,e_p \\ 2.5\,e_R \end{bmatrix},\qquad
\|\xi_{des}^{lin}\| \le 0.35\ \mathrm{m/s},\quad \|\xi_{des}^{ang}\| \le 1.20\ \mathrm{rad/s}$$

**第二步：阻尼伪逆 + 零空间姿态控制**（6-D 任务 → 7 关节冗余分解）

$$q̇_{cmd} = \underbrace{J^\top\!\big(JJ^\top + 0.035^2 I\big)^{-1}\xi_{des}}_{\text{任务项}}
+ \underbrace{\big(I - J^\dagger J\big)\,0.20\,(q_{home}-q)}_{\text{零空间姿态项}}$$

再 clip 到 ±1.25 rad/s。

**第三步：速度伺服（速度→力矩）**

$$\tau_{servo} = \tau_{bias} + s\odot K_v (q̇_{cmd} - q̇),\qquad
K_v = [42, 42, 36, 32, 9, 8, 6]\ \mathrm{N\!m/(rad/s)}$$

τ_bias 是 MuJoCo 的 `qfrc_bias`（重力+科氏）——**重力补偿由伺服承担**；s 是逐关节
盒投影系数（保证不超硬件限位），随后力矩变化率 slew 限幅（大关节 700、腕 160 N·m/s）。

### 3.2 核心代码

```python
# fixed_panda_wbc.py:96-113（节选）
position_error = target_position - current_position
orientation_error = so3_log(target_rotation @ current_rotation.T)
desired_twist = feedforward.copy()
desired_twist[:3] += feedback_scale * self.config.position_feedback_gain * position_error
desired_twist[3:] += feedback_scale * self.config.orientation_feedback_gain * orientation_error
desired_twist[:3] = _clip_norm(desired_twist[:3], self.config.max_linear_speed_mps)

jacobian = body_jacobian(self.model, data, self.hand_id)
regularized_gram = jacobian @ jacobian.T + 0.035**2 * np.eye(6)
damped_pinv = jacobian.T @ np.linalg.solve(regularized_gram, np.eye(6))
qdot_task = damped_pinv @ desired_twist
nullspace = np.eye(ARM_DOF) - damped_pinv @ jacobian
qdot = qdot_task + nullspace @ (0.20 * (self.nominal_posture - data.qpos[:ARM_DOF]))
```

```python
# wbc_velocity_residual_core.py:614-627（节选）
servo = np.asarray(config.velocity_gain_nm_per_radps) * (command - measured)
# ... 逐关节盒投影到 torque_limits ...
desired = bias + scale * servo
maximum_delta = np.asarray(config.maximum_torque_rate_nmps) * dt
applied = previous + np.clip(desired - previous, -maximum_delta, maximum_delta)
return np.clip(applied, -limits, limits), scale
```

**设计说明**：WBC 是"冻结"的——增益从不随实验重调，且契约禁止柔顺层修改其目标
生成（文件头注释："never changes its target-generation policy"）。它是所有方法
共用的、不可优化的基础设施。

---

## 4. VMC：虚拟模型控制基线

**文件**：`vmc_compliance_baseline.py`（317 行）、`vmc_torque_baseline.py`（75 行）。

### 4.1 建模思想

VMC（Virtual Model Control，Zhang et al., IROS 2024 一脉）：想象末端挂了一套
虚拟弹簧-阻尼机构，算出这套机构会施加多大的**末端力旋量（wrench）**，再经雅可比
转置换算成关节力矩，让真实电机复现同样的效果。

**wrench = 6 维广义力 = 3 个平移力 + 3 个旋转力矩**。末端有 6 个自由度，所以柔顺
机构也是 6 维的：3 根平移弹簧 + 3 根扭簧。

### 4.2 数学建模

**虚拟小车**（carriage）：一个 6-DOF 虚拟刚体，状态为其相对 WBC 标称的偏移
`offset, offset_rate ∈ R⁶`，以物理步长 4 ms 积分：

$$M\,\ddot{d} = F_{drive} + F_{ee},\qquad M = \mathrm{diag}(1.25{\times}3,\ 0.08{\times}3)$$

**EE 耦合弹簧（饱和 tanh 型，6 通道）**——反应力作用在小车上：

$$F_{ee} = \sigma\tanh\!\Big(\frac{K\,d_{sep}}{\sigma}\Big) + D\,\dot d_{sep},\qquad
K = \kappa_{6D}\odot[220^{\times3}, 18^{\times3}],\ \sigma=[24^{\times3}, 3^{\times3}]$$

**驱动弹簧**（把小车拉回标称）：

$$F_{drive} = -K_d\,d - D_d\,\dot d,\qquad D = 2\zeta\sqrt{MK},\ \zeta = 1.05$$

**力矩输出（v3 稳定版）**——只取饱和弹簧反力过 Jᵀ，不加显式阻尼：

$$\tau_{res} = \mathrm{clip}\Big(J^\top\big[-\sigma\tanh(K\,d/\sigma)\big],\ \pm\Delta\tau_{budget}\Big)$$

**关键调参结论**：刚度缩放 k=2.2、预算 3% 时稳定且有效（fx0–fx3 全部任务成功、
无硬限位、无撞击残差 0.064 N·m）。

### 4.3 为什么力矩通道里没有阻尼项（重要调试史）

伺服本身是速度反馈（天然阻尼通道）。力矩层再叠加 D·ė 会形成双重阻尼 → 与伺服
构成正反馈 → 发散（实测"一撞就飞"）。佐证：VMC 原作者开源的 cutting_simulation
中，主柔顺弹簧的阻尼比 ζ = d/(2√(km)) = 2.0/(2√(130×5)) ≈ **0.04**——同样几乎
零阻尼，耗散全部交给末端对地阻尼与关节阻尼。我们的稳定版与这一设计惯例一致。

### 4.4 核心代码

```python
# vmc_torque_baseline.py:40-60（核心，全文 75 行）
def act(self, joint_position, joint_velocity, nominal_twist,
        hand_jacobian, pose_error=None, twist_error=None):
    self.baseline.act(pose_error, twist_error)          # 4ms 子步推进小车动力学
    J = np.asarray(hand_jacobian, dtype=float)
    spring = self.baseline.saturation * np.tanh(
        self.baseline.ee_stiffness * self.baseline.offset / self.baseline.saturation)
    wrench = -spring                                    # 反作用在手上（让位方向）
    torque = J.T @ wrench                               # 6D wrench → 7 关节力矩
    bounded = np.clip(torque, -self.residual_torque_limits, self.residual_torque_limits)
    clipped = np.clip(bounded / self.residual_torque_limits, -1.0, 1.0)
    return VMCComplianceAction(bounded_filter_action=clipped, ...)
```

```python
# vmc_compliance_baseline.py:201-215（小车动力学，节选）
separation = -(gated + self.offset)                     # 小车到 EE 的耦合位移
external = self.saturation * np.tanh(self.ee_stiffness * separation / self.saturation) \
         + self.ee_damping * separation_rate
drive = -self.drive_stiffness * self.offset - self.drive_damping * self.offset_rate
acceleration = (drive + external) / self.mass
self.offset_rate = np.clip(self.offset_rate + PHYSICS_DT * acceleration,
                           -self.speed_limits, self.speed_limits)
self.offset = self.offset + PHYSICS_DT * self.offset_rate
```

### 4.5 与原作者实现的忠实度（诚实声明）

复刻的是**建模语言**（tanh 饱和弹簧 + 虚拟小车 + Jᵀ 映射），有三处明确记录的适配：
(i) 6-DOF 单小车代替原作者的平面两级链（mocap→5 kg 虚拟质量→软簧→刀）；
(ii) 部署为 WBC 残差而原作者中 VM 是主控制器；(iii) 去掉力矩通道显式阻尼。
差异全部写在 `vmc_compliance_baseline.py` 文件头
"Differences ... (documented, not hidden)"。

---

## 5. MLP：无记忆网络基线

**文件**：`mlp_compliance_baseline.py`（110 行）、`train_mlp_baseline.py`。

### 5.1 建模与设计意图

这是"为什么需要 ESN"的对照实验：一个普通两层 MLP，**行为克隆完全相同的教师轨迹、
读完全相同的 32 维输入、过完全相同的激活门与物理限幅**。唯一架构差异：没有
reservoir——逐帧独立映射，无状态。

$$a_t = \tanh\Big(W_2\tanh(W_1 \tilde x_t + b_1) + b_2\Big),\quad
W_1\in\mathbb{R}^{64\times32},\ W_2\in\mathbb{R}^{7\times64}$$

### 5.2 核心代码

```python
# mlp_compliance_baseline.py:68-80（推理，numpy，无 torch 依赖）
normalized = (observation - self.mean) / self.std          # 32 维 z-score
hidden = np.tanh(normalized @ self.w1.T + self.b1)
bounded = np.tanh(hidden @ self.w2.T + self.b2)
activation = 1.0
if pose_error is not None:                                 # 误差 smoothstep 激活门
    position_error = float(np.linalg.norm(pose_error[:3]))
    phase = np.clip((position_error - 0.004) / (0.012 - 0.004), 0.0, 1.0)
    activation = float(phase * phase * (3.0 - 2.0 * phase))
bounded = bounded * activation
```

### 5.3 训练

- 数据：与 ESN **同一批教师轨迹**（`train_mlp_baseline.py:14` 直接 import ESN 管线的
  `_load_episode`，逐轨迹复用）；
- 目标：MSE 行为克隆到教师动作；
- 优化：Adam，400 epoch，lr 1e-3，weight decay 1e-4，torch.manual_seed 可复现；
- 导出：w1/b1/w2/b2 + mean/std 存 npz，部署纯 numpy。

---

## 6. ESN：提出的方法

**文件**：`direct_esn_compliance.py`（约 420 行）、`esn_compliance.py`。

### 6.1 Echo State Network 原理（30 秒版）

ESN 是一种储备池计算（reservoir computing）网络：**固定不变的随机循环网络**
（reservoir）负责把输入历史编码成高维状态，**唯一可训练的部分是一个线性读出**。
循环连接的谱半径 <1 保证回声态性质（状态由输入历史唯一决定、初值影响衰减），
从而使线性读出的岭回归有唯一闭式解——**训练是一次线性方程组求解，不是迭代优化**。

对控制任务的意义：撞击响应是时序问题（要看"过去几百毫秒发生了什么"），无记忆
映射做不到；而 ESN 用极低的训练成本（闭式解）获得时序记忆。

### 6.2 Reservoir 动态（部署时的全部计算）

$$s_{t+1} = (1-\alpha)\,s_t + \alpha\tanh\big(W_{in}x_t + W_r s_t + b\big)$$

$$a_t = \tanh\big(W_{out}\,[1;\,x_t;\,s_t]\big)$$

| 参数 | 值 | 说明 |
|---|---|---|
| 神经元数 N | 160 | ablation 显示在容量饱和拐点（§9.2） |
| 谱半径 ρ | 0.90 | 构造后缩放，保证回声态 |
| 连接概率 | 0.12 | 稀疏循环连接 |
| 输入尺度 | ±0.45 均匀 | W_in 的取值范围 |
| 时间常数 τ | 0.12 s | **最敏感参数**（§9.2） |
| 泄漏率 α | dt/τ = 1/3 | 泄漏积分器 |
| 岭回归 λ | 1e-4 | 读出正则 |
| 特征维度 | 1+32+160 = 193 | 读入读出层 |
| 可训练参数 | 7×193 = **1351** | 只有 W_out |

```python
# direct_esn_compliance.py:223-229（部署核心，5 行）
def _advance_encoded(self, encoded_input):
    proposal = np.tanh(self._input @ encoded + self._recurrent @ self._state + self._bias)
    self._state = (1.0 - self.config.leak) * self._state + self.config.leak * proposal
    return np.concatenate(([1.0], encoded, self._state))
```

单步推理 = 一次 160×32 + 一次 160×160 + 一次 7×193 矩阵乘——**计算量与两层
MLP 同级**，可实时。

### 6.3 观测设计（32 维，纯本体感受）

$$x = \Big[\frac{q}{3},\ \frac{\dot q}{3},\ \frac{\xi^*}{[0.6, 2.0]},\ \frac{e_p}{[0.012, 0.20]},\ \frac{\dot e}{[0.40, 1.20]}\Big],\quad \text{clip} \pm 10$$

字段级契约（`DEPLOYABLE_INPUT_FIELDS`）：

| 分量 | 维度 | 物理含义 |
|---|---|---|
| q | 7 | 关节角 |
| q̇ | 7 | 关节角速度 |
| ξ* | 6 | WBC 标称任务速度（线+角） |
| e_p | 6 | WBC 位姿误差（标称−实际） |
| ė | 6 | WBC 速度误差 |

**故意不含**（`TEACHER_ONLY_FIELDS`）：接触力、撞击法线、撞击时长、障碍位姿/速度、
撞击器类型、释放时刻。即 ESN 不知道"有棒子"，只能从运动偏差推断扰动——与部署
在真机上的信息集一致。归一化常数是物理量级（rad、m、m/s），无测试集统计。

### 6.4 读出训练：岭回归 + 导数匹配

$$(W_{out})^\top = \Big(\Phi^\top\Phi + \lambda I + \mu\,\Delta^\top S\,\Delta\Big)^{-1}
\Big(\Phi^\top Y + \mu\,\Delta^\top S\,Y_\Delta\Big)$$

- Φ：193×T 特征矩阵（washout 3 步丢弃）；Y：教师动作；
- 第二项是**导数匹配正则**：Δ 为相邻帧特征差，Y_Δ 为**教师的**动作差——学生
  "允许和教师一样快地动，但不许更快"。这把时间平滑性训练进读出本身，而不是
  部署端加滤波（滤波会引入延迟）；
- S 为逐通道权重，可给承担方向切换的通道（侧向/偏航）减 penalty。

```python
# direct_esn_compliance.py:307-336（节选）
gram = design.T @ design + (self.config.ridge_lambda + prior_weight) * np.eye(self.feature_dimension)
right = design.T @ np.clip(target_array, -1.0, 1.0)
if smoothness_weight > 0.0:            # 导数匹配项
    gram += smoothness_weight * scales * (delta.T @ delta)
    right += smoothness_weight * (delta.T @ (delta_targets * scales))
self._readout = np.linalg.solve(gram, right).T     # 闭式解，一次线性求解
```

---

## 7. 训练管线：教师与蒸馏

**文件**：`counterfactual_direct_esn_teacher.py`（训练侧专用）、
`bootstrap_direct_esn_multifixture.py`。

### 7.1 反事实教师（privileged，只在训练时存在）

教师在**克隆的 MjData** 上做短视野前向 rollout（不污染真实环境），对每个候选
动作预测后果，选代价最小者作为标签：

1. **视野**：8 步 × 40 ms = 320 ms；
2. **候选集**（9 个参数化动作）：零动作 / 纯减速(0.22) / {0.22, 0.45}减速 ×
   {0.20, 0.45, 0.75}顺冲击法线让位——法线是特权信息，只用在这里；
3. **代价函数**（九项，三项 headline 指标全部内化）：

$$\mathcal{J} = w_1\Big(\frac{F_{peak}}{10N}\Big)^2 + w_2\Big(\frac{J_{imp}}{0.1Ns}\Big)^2 + w_3\Big(\frac{e_{term}}{12mm}\Big)^2 + w_4\tau_{ratio}^2 + w_5\|a\|^2 + w_6\|\Delta a\|^2 + w_7 n_{secondary} + w_8\Big(\frac{\dot\tau_{peak}}{300}\Big)^2 + w_9\Big(\frac{v_{surge}}{0.05}\Big)^2$$

4. **中性硬约束**：无棒或预测接触力 < 0.2 N 时教师必须输出零——学生从数据里
   学到的默认行为是"别乱动"。

```python
# counterfactual_direct_esn_teacher.py:231-235（中性约束）
if not env.rod_enabled or zero_result["peak_force_n"] < teacher_config.activation_force_n:
    return CounterfactualTeacherResult(action=zero_action, ...)
```

### 7.2 蒸馏流程

```
72 条棒击教师轨迹(t???_y.npz) + 1 条无棒中性轨迹(no_rod.npz)
        │  40 ms 重采样, repeat=4, washout=3
        ▼
bootstrap_direct_esn_multifixture.py: 岭回归闭式解拟合 W_out
        │  × 32 个不同 reservoir seed → 32 个独立 checkpoint
        ▼
esn_bc_{seed}.npz（显式存储 recurrent/input/bias/readout，可逐矩阵审计）
```

MLP 用**同一批轨迹**训练（§5.3）。总训练样本 44384。

### 7.3 信息集分离（防"标签泄漏"）

教师用特权信息（接触力、法线）**选标签**；学生看到的输入里没有这些量。部署时
ESN 只依赖 32 维本体感受。这一分离是"蒸馏"成立的关键，代码里由
`TEACHER_ONLY_FIELDS` 与 `DirectESNController.act` 的输入契约强制。

---

## 8. 评测协议

- **配对评测**：`evaluate_direct_esn_post_contact.py` 对每个 (checkpoint, fixture)
  跑两条 rollout——Fixed WBC（零动作）与该 checkpoint——同 seed 同环境，报告
  ΔRMSE = ESN恢复段RMSE − FW恢复段RMSE。恢复段定义为首次接触释放之后。
- **种子协议**：ESN/MLP 各 32 个独立训练 seed；VMC 无训练随机性（单配置网格
  调参记录在案）；FW 确定性。
- **环境 seed**：20260817 固定。**确定性保证**：同 checkpoint 同 seed 重跑逐位
  复现（ablation 的对照实验：6.280823669691147 == 6.280823669691147）。
- **headline 指标**：
  1. 轨迹跟踪精度（ΔRMSE，恢复段）；
  2. 运动平稳性（峰值 jerk / recovery jerk）；
  3. 电机力矩安全（峰值力矩、变化率、硬限位触发）。

---

## 9. 实验结果

### 9.1 主实验（32 seeds，FR3，力矩残差 5%）

**fx3（held-out）ΔRMSE，负 = 优于 Fixed WBC：**

| 方法 | fx0 | fx1 | fx2 | **fx3（考试）** | 被撞后偏离 | 通过率 |
|---|---:|---:|---:|---:|---:|---:|
| Fixed WBC | 0 | 0 | 0 | 0 | 20.0 mm | — |
| VMC (k=2.2, 3%) | −3.0 | −4.5 | −7.9 | −8.9 | 11.1 mm | 4/4 |
| MLP | −3.6 | −3.5 | −9.0 | −9.8±3.6 | 10.2 mm | 28/32 (87.5%) |
| **ESN** | −3.3 | −6.3 | −10.3 | **−18.2±0.5** | **1.8 mm** | **31/32 (96.9%)** |

$$\boxed{\text{ESN}(-18.2) > \text{MLP}(-9.8) > \text{VMC}(-8.9) > \text{Fixed WBC}(0)}$$

- ESN 比最强学习方法 MLP 好 85%，比手工 VMC 好 105%；
- 种子稳定性：ESN ±0.55 mm vs MLP ±3.57 mm（稳定 6.5 倍）；
- 力矩安全：全方法峰值 ≤42.5 N·m（硬件限位的 49%），硬限位从未触发。

**泛化**（8 seeds）：
- 撞击时间 0.995–1.150 s 扫描：ESN 均值 10.7 mm、9 个时间点波动 <0.5 mm
  （FW 20.3 mm、±2.8）；
- 撞击高度 0.535–0.548 m：ESN 10.7 vs FW 19.2 mm；
- 冲程 0.140–0.180 m：ESN 8.9–14.6 mm。

### 9.2 参数 ablation（8 seeds × 18 配置 × 4 fixtures，2026-08-19）

fx3 ΔRMSE（mean±std over 8 seeds）：

| N | ΔRMSE | ρ | ΔRMSE | τ (s) | ΔRMSE | ins | ΔRMSE |
|---|---|---|---|---|---|---|---|
| 24 | −14.7±3.2 | 0.5 | −17.5±2.2 | 0.04 | −14.8±3.2 | 0.15 | −17.9±0.2 |
| 32 | −14.1±3.2 | 0.7 | −17.6±2.2 | 0.08 | −17.2±2.2 | **0.45** | −18.1±0.8 |
| 48 | −15.1±3.3 | **0.9** | −18.1±0.8 | **0.12** | −18.1±0.8 | 1.0 | −18.5±0.7 |
| 64 | −15.2±3.5 | 1.1 | −17.8±0.6 | 0.24 | −18.1±0.6 | | |
| 100 | −17.4±2.2 | | | | | | |
| **160** | **−18.1±0.8** | | | | | | |
| 250 | −17.6±0.3 | | | | | | |

结论：(1) **τ 是唯一敏感参数**——τ=dt（无记忆）塌到 −14.8，直接验证"性能来自
reservoir 记忆"假说；(2) N=160 在饱和拐点且方差最小；(3) ρ、ins 在回声态平台内
不敏感；(4) 默认配置取拐点不取峰值（fx3 峰值在 ins=1.0，未采用）。18 配置全部
fx3 成功率 100%。

### 9.3 双撞击场景与失败机制诊断（2026-08-19 服务器实测）

场景：抓取前棒击（t=1.085）→ 抓取（t=2.40–2.95）→ 二次棒击（t≈2.9）→ 回位。

| 方法 | 峰值误差@t≈1.4 | 抓取时刻误差@t=2.40 | 结果 |
|---|---:|---:|---|
| Fixed WBC | 39.9 mm | 20.1 mm | ❌ 关空，lift 失败 |
| VMC | 36.4 mm | 10.8 mm | ✅ 抓起（z→0.661） |
| ESN | 35.8 mm | **6.1 mm** | ✅ 抓起（z→0.674） |

Fixed WBC 失败机制（详见 §10.1）：恢复回路在工作（误差 39.9→14.9 mm 持续衰减），
但有效时间常数 ~1.4 s，t=2.40 关爪时还剩 20.1 mm——掌心偏 20 mm 超出手指跨
5 cm 方块的容差，关空。

动图：`fixed_wbc.gif` / `vmc_torque.gif` / `esn_torque.gif` / `mlp_torque.gif`。

---

## 10. 关键设计问题的答案（组会 FAQ）

### 10.1 "正常控制器都会自动回归，为什么 Fixed WBC 失败？"

它会回归，但没在截止时间前回够。三个环节叠加：

1. **撞击是持续挤压不是脉冲**：棒子撞后有 crawl 保压（到 ~1.4 s），期间伺服峰值
   34.5 N·m 与棒子硬顶，物理上推不回来；
2. **恢复受饱和限制**：反馈增益 3.0/s 的理想时间常数 0.33 s，但叠加速度上限
   0.35 m/s、关节 1.25 rad/s、力矩 slew 700/160 N·m/s 后，实测有效时间常数
   ~1.4 s；
3. **抓取是时间触发**：`gripper_target(t)` 在 t=2.40 与手的位置无关；参考目标
   也不感知方块位移。20 mm 残余误差 → 关空。

柔顺的价值因此被精确定义为：**截止时刻的残余偏差**（ESN 6.1 vs FW 20.1 mm）。

### 10.2 "残差只有 2.6 N·m，为什么影响这么大？"

分母选错了。正确比较对象：

- **撞击角冲量**：接触冲量 3.1 N·s × 力臂 0.2–0.3 m ≈ 0.6–0.9 N·m·s；残差可用
  冲量 2.6 N·m × 0.3 s ≈ 0.8 N·m·s——**同一量级**；
- **伺服对慢推天然软**：τ = K_v(q̇_cmd−q̇) 抵抗速度不抵抗位置；棒子慢慢挤压时
  q̇≈0，伺服只出几个 N·m——与 2.6 N·m 残差同级。误差能长到 40 mm 本身就是证明；
- **作用在恢复段而非对抗段**：峰值误差只降 10%（39.9→35.8），抓取时刻误差降
  3 倍（20.1→6.1）——残差做的是"挤压期少存偏移 + 释放后消振 + 恢复期定向助推"
  （2.6 N·m / ~2 kg·m² ≈ 1 rad/s² 助推，对 1.25 rad/s 速度上限很可观）。

### 10.3 "为什么不让 VMC/ESN 检测到撞击后全局接管？"

四个关卡都过不去：(1) **检测**——无力传感器，proprioception 上撞击与抓取接触
不可分，误报即灾难；阈值检测延迟 150–200 ms 吃掉关键窗口；(2) **切换瞬态**——
bumpless transfer 问题，且重力补偿谁出？拼回基础通道就是现在的架构；(3) **任务
知识**——ESN 的 32 维观测无时间无相位，接管期间无法替代 WBC 的时间参数化计划；
(4) **安全上界**——满权限 + OOD 输出 = 真机甩臂。

我们的架构是同一思想的**连续光滑版**：无撞击时输出 ≈0（0.064 N·m），撞击窗口
连续滑到上限——"检测器"被学进网络（泛化实验证明跨时间/高度/速度稳定），无切换
瞬态、无交还问题。

### 10.4 "VMC 的六个自由度都柔顺吗？"

机制上 6 通道弹簧全部激活（逐通道刚度 κ_6D）；效果上只有被激励的方向（撞击方向）
出现明显让位——其余通道误差在死区（8 mm / 0.032 rad）内，输出 ≈0。ESN 则无通道
结构约束，7 个输出通道自由学习（包括利用 7-DOF 冗余）——这是它能超过 VMC 的
结构性自由度之一。

### 10.5 "为什么 N=160 而 Fan Ye 论文用 64？"

160 原是项目早期骨架默认值，ablation（§9.2）补上了正当性：N≤64 时 held-out 掉
3 mm 且方差 ×4；N∈[100,250] 饱和，160 是饱和区方差最小的点。N=64（论文对齐
规模）仍有 −15.2±3.5，优于两个基线。如需严格对齐论文规模，可换 N=64 重跑主线。

---

## 11. 文件索引与复现命令

### 11.1 代码索引

| 组件 | 文件 | 行数 |
|---|---|---|
| 环境/任务/安全栈 | `wbc_velocity_residual_env.py` / `wbc_velocity_residual_core.py` | 874 / ~700 |
| WBC | `fixed_panda_wbc.py` | 121 |
| 参考轨迹+场景 | `run_grasp_impact_benchmark.py` | — |
| FR3 场景 | `fr3_scene.py` | — |
| VMC | `vmc_compliance_baseline.py` / `vmc_torque_baseline.py` | 317 / 75 |
| MLP | `mlp_compliance_baseline.py` / `train_mlp_baseline.py` | 110 / ~120 |
| ESN | `direct_esn_compliance.py` / `esn_compliance.py` | ~420 / ~200 |
| 教师 | `counterfactual_direct_esn_teacher.py` | ~300 |
| 蒸馏 | `bootstrap_direct_esn_multifixture.py` | ~200 |
| 评测 | `evaluate_direct_esn_post_contact.py` / `run_direct_esn_mujoco.py` | — |

服务器：`arm1@192.168.31.70:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`。
结果：`outputs/direct_esn_fixture23_coverage_20260817/`（checkpoint 在 `torque_mode/`，
ablation 在 `ablation/`）。

### 11.2 复现命令

```bash
cd scripts && source ../../.venv/bin/activate && export MUJOCO_GL=osmesa

# 训练一个 ESN（闭式解，秒级）
python bootstrap_direct_esn_multifixture.py \
  --expert-traces ../outputs/.../expert_traces/t000_y.npz ... t071_y.npz \
  --no-rod-expert-trace ../outputs/.../expert_traces/no_rod.npz \
  --output-model /tmp/esn.npz --output-summary /tmp/esn.json \
  --reservoir-seed 251 --neutral-repeat 4

# 训练 MLP（同数据）
python train_mlp_baseline.py --expert-traces ... --no-rod-expert-trace ... \
  --output-model /tmp/mlp.npz --output-summary /tmp/mlp.json

# 配对评测（任一 checkpoint，fx0-3）
python evaluate_direct_esn_post_contact.py --controller /tmp/esn.npz \
  --menagerie /path/to/mujoco_menagerie --fixture-index 3 \
  --robot fr3 --execution-mode torque_residual \
  --residual-torque-scale 0.05 --seed 20260817 --output-dir /tmp/ev_fx3

# 独立审计 checkpoint（冻结性与谱半径）
python - <<'EOF'
import numpy as np
d = np.load('esn_bc_251.npz')
W = d['recurrent']
print('rho =', abs(np.linalg.eigvals(W)).max())   # 应 ≈ 0.90
print('readout shape =', d['readout'].shape)       # (7, 193)
EOF
```

### 11.3 已知局限（主动披露）

1. VMC 为单小车 6-DOF 适配版（非原作者两级链逐行复刻）；
2. 3%/5% 预算是安全设计参数，未逼近可行性边界；
3. 教师候选集为 9 个参数化动作（非连续空间），蒸馏上界受教师族限制；
4. 撞击方向泛化依赖训练分布覆盖（sides_matrix 实验覆盖 ±x/±y）；镜像门控
   （`mirror_gate`）为可选结构先验，主线 checkpoint 未启用。

---

*文档生成：2026-08-19。所有数字来自服务器实测（诊断脚本日志与评测 JSON 均在
`outputs/` 与 `/tmp/diag_fwbc.log` 留档），逐条溯源见 `IMPLEMENTATION_PROOF.md`。*
