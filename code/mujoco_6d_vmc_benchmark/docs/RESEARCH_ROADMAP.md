# 柔顺控制研究历程与后续计划（FixedWBC → Paper-MPC → 论文系统移植）

> 分支：`paper-mpc-baseline` · 日期：2026-08-19 · 状态：PaperMPC 三场景实验进行中

---

## 0. 一页纸总览

```text
名义控制器演进:   FixedWBC(手写解析伪逆) ─► Pink WBC(原仓库vendored差分IK) ─► PaperMPC(论文系统复刻)
柔顺层架构:       twist层让位(改参考) ─► 力矩残差(阻抗式, 3%预算) [用户核心洞察]
机器人:           Panda ─► FR3 + Panda Hand (FK 零偏差验证)
撞击场景:         单次棒击 ─► 双撞击 ─► 棒/球/倾斜木板 三场景
评价重心:         位置恢复(ΔRMSE) ─► 力域指标(力峰值/力矩峰值/torque rate) + 难工况边界
最终去向:         FR3 真机(FCI力矩流) + 论文系统(grasp_anywhere compliance槽位)
```

---

## 1. 起点：为什么会有 FixedWBC（2026-08-15）

**背景问题**：高层名义运动指令 + 低层接触后柔顺让位/恢复/回轨。

**当时的约束**：
- 实验室主工程（Visibility-Aware Mobile Grasping）是 Fetch + ManiSkill/Gazebo/ROS 栈，无法直连 Panda/FR3 力矩级 MuJoCo 场景；
- 目标是尽快建立"柔顺层 benchmark"，名义控制器只需要**确定性、冻结、透明**。

**FixedWBC 设计**（`fixed_panda_wbc.py`，121 行，教科书标准律）：

$$\dot{x}^{WBC} = \dot{x}^{ff} + K_p(x^\star - x) + K_R\,\mathrm{Log}(R^\star R^\top),\qquad
\dot{q}^{WBC} = J_\lambda^{\#}\dot{x}^{WBC} + (I - J_\lambda^{\#}J)K_N(q_0 - q)$$

- Kp=3.0，K_R=2.5，阻尼伪逆 λ=0.035，事后 clip（1.25 rad/s）
- **设计文档即声明它是可替换 adapter**：任何 WBC 逐周期发布 `(SE(3) target, twist, q̇)` 即可替换，柔顺层与评估代码不动——后续两次换控制器（Pink、PaperMPC）都兑现了这个承诺。

---

## 2. 架构关键决策：力矩残差（用户洞察）

最初柔顺层在 **twist 层**（修改 WBC 速度参考 = 导纳式）。用户提出核心架构：

> "WBC 输出一个速度，ESN/MLP/VMC **不要修改这个速度**，直接输出力矩。"

实现为**阻抗式柔顺**（`execution_mode="torque_residual"`）：

```text
τ_total = clip( τ_servo + τ_residual , ±τ_hw )
τ_servo = τ_grav + K_v(q̇_cmd − q̇),   τ_residual = π(x)·Δτ_budget
```

- 柔顺发生在**力域**（碰撞瞬间改变力平衡），而非只挪参考；
- 残差预算 = 硬件限位的百分比 → 最坏情况有解析上界（3% ≈ 腕部 0.36 Nm），真机可部署性契约。

**为什么不全接管（组会拷打后的复盘）**：安全上界、学习问题规模、任务维度匹配、公平比较、residual 范式文献支撑。全接管对照实验列入计划（见 §8.3）。

---

## 3. VMC 基线血泪史（强基线的代价）

复刻 Zhang et al. (IROS 2024) 弹簧-小车虚拟机构（tanh 饱和弹簧 + inerter + J^T 映射）：

| 迭代 | 问题 | 结论 |
|---|---|---|
| v1 | damper 项 `D·(offset_rate − offset_rate) ≡ 0` | 显式阻尼缺失 |
| v2 | `D·offset_rate` | 太强，首次撞击即发散 |
| v3 | 标准阻抗正刚度 | 机械臂更硬，全线失败 |
| v4 | 负刚度让位 | 正反馈，完全发散 |
| **v5（终版）** | **纯弹簧 J^T 映射，k=2.2，3% 预算** | **稳定，4/4 任务成功** |

**独立佐证**：VMC 原作者调好的切割仿真（sally-00/cutting_simulation）中，主柔顺元件（背弹簧）阻尼比 **ζ≈0.04**——原作者自己的设计惯例就是"近零阻尼弹簧 + 隐式耗散"，与我们的修复殊途同归。

稳定版数据：fx0-3 改善 −3.0/−4.5/−7.9/−8.9 mm，无撞击残差 0.064 Nm，力矩限位从未触发。

---

## 4. ESN 作为核心算法（论文主贡献线）

**严格 Fan Ye 式骨架 + 可消融扩展**：
- 固定随机储备池（160 神经元，ρ<1），漏积分 $s_{t+1}=(1-\alpha)s_t+\alpha\tanh(W_{in}x_t+W_r s_t+b)$
- 唯一可训练：线性读出（岭回归闭式解）
- 32 维纯本体感受观测 `[q, q̇, ξ_nom, e_pose, ė]`——无传感器特权

**蒸馏管线**：特权反事实教师（读接触力）→ DAgger → 覆盖行为克隆 → ESN 学生。

**核心结果**（32 seeds，FR3）：
- ESN −18.2±0.55 mm vs MLP −9.8±3.57 mm（held-out fx3），**ESN 稳定 6.5 倍**
- 通过率 31/32 vs 28/32
- 撞击时间泛化：9 个时间点波动 < 0.5 mm

**结构性发现（值得单独成节）**：
1. **CR 设计坍缩**：层级控制（WBC 内环）下，谱半径 0.67–0.93 全部同性能——储备池设计参数不重要，**架构位置才重要**；
2. 镜像等变门控被 7-DOF 冗余 IK 阻塞（证伪，删除）；
3. 导数匹配正则（保响应速度、压多余抖动）保留为消融项。

---

## 5. FR3 迁移（真机对齐）

FR3 臂 + Panda Hand 嫁接（attachment_site，-45°），home 位 FK 与 Panda **零偏差**（[0.5545, 0, 0.6245]）。后续 Pink URDF 验证再次 0.000 mm。真机平台确认为 FR3 → 仿真-真机无换型风险。

---

## 6. 名义控制器升级线（"复刻仓库 WBC"）

### 6.1 Pink WBC（vendored 原代码）

来源：Prepose-Sampler 生态的 `autolife-planning` 0.3.4 wheel（x86_64-only，服务器 aarch64 → 纯 Python 部分原样 vendor，NOTICE 记录出处）。

- `PinkIKSolver` **一行未改**；适配层只做：FR3 ChainConfig、45° 法兰常量偏移、每 40ms 调用一次差分模式、包成 WBCCommand 契约
- QP 差分 IK vs FixedWBC 的解析伪逆：限位在 QP 内保证可行、位置/姿态分离计权、LM 自适应阻尼
- **实测**：fx0-3 全部成功，at-grasp ~1 mm（FixedWBC 20.1 mm 失败）——限位感知恢复 + 任务分离计权 + LM 阻尼三因素

### 6.2 论文系统发现（Visibility-Aware Mobile Grasping）

读论文 + 本地主工程代码，确认完整分工：

```text
规划器: πg 子目标(行为树+采样) + πv velocity-aware注视 + πr 全身规划(Hybrid A*+RRT+VAMP, 50-80ms重规划)
控制器: MPC 轨迹跟踪 —— 20Hz, 输出 10 维速度指令(底盘2+躯干1+臂7)
预留槽: grasp_anywhere/control/compliance.py —— ComplianceController Protocol
         (名义参考+本体感受+力采样输入; DISABLED/SHADOW/ACTIVE 模式; 前任=残差PPO)
```

**关键对齐**：论文 MPC 输出速度 ↔ 我们架构"上层发速度"；compliance.py 契约 ↔ 我们 32 维观测（子集关系）。我们的 ESN 就是 ResidualPPO 的继任者。

### 6.3 PaperMPC（当前实验，忠实复刻）

读 `maniskill_env_mpc.py` 源码发现其"MPC"实为**一步二次型速度控制**：

$$(B^\top Q B + R)\,u = B^\top Q (x_{ref} - x),\qquad \text{臂块 } B=I:\; u = \underbrace{g\tfrac{Q}{Q+R}}_{2.31}(q_{wp+k} - q)$$

参数逐项复刻：Q_arm=12, R_arm=1, gain=2.5, lookahead=2, 最近 waypoint 前向搜索, 限速 7 rad/s（`paper_mpc_wbc.py`）。固定底座 FR3 只裁掉底盘/躯干块，臂块求解一字不差。

---

## 7. 三接缝分析（移植论文系统的技术路线）

```text
接缝① 参考源:    smoothstep knots ─► TOPP-RA(原仓库方法, vendored trajectory模块) [已部署待跑]
接缝② 名义控制器: FixedWBC/Pink ─► PaperMPC(公式级复刻) [进行中]
接缝③ 执行层:    速度伺服+残差 ─► 论文系统compliance槽位(SHADOW→ACTIVE) / FR3 FCI
```

**已消掉的雷**：ManiSkill GPU 渲染（arm64）不再必需——MuJoCo 复刻已覆盖科研结论；机器人换型（Fetch→FR3）由真机平台确认反向对齐。

---

## 8. 未来研究计划

### 8.1 近期（本周，paper-mpc-baseline 分支）

| # | 实验 | 回答的问题 |
|---|---|---|
| 1 | PaperMPC 无柔顺 × {棒, 球, 倾斜木板} | 论文控制器裸机基线（力矩峰值/回位速度/成功率） |
| 2 | ESN/MLP 零迁移上 PaperMPC × 三场景 | 训练好的柔顺层跨名义控制器迁移性 |
| 3 | VMC 三场景分别调参（k × budget 网格） | 手工基线在新控制器下的最优形态 |
| 4 | TOPP-RA 参考 ×（1-3） | 时间最优参考（零速度余量）下柔顺层价值 |

### 8.2 中期（评测协议升级）

- **力域主指标**：同工况下撞击力峰值、伺服力矩峰值、torque rate、恢复段 jerk（Pink/PaperMPC 已把位置恢复做到 ~1mm，位置叙事让位给力域——这才是柔顺的本义）
- **难工况边界扫描**：撞击强度 / 执行器弱化（torque_limit_scale）/ 持续挤压 / 多次撞击 / 传感噪声，找 WBC-only 成功率跌破 100% 的临界点，柔顺层贡献 = 边界外推量
- **名义控制器鲁棒性矩阵**：{Fixed, Pink, PaperMPC} × {smoothstep, TOPP-RA} —— 证明贡献不绑定特定名义控制器（论文强论证）

### 8.3 中期（算法与消融）

- **全接管 vs 残差对照**：ESN 输出总力矩（100% 权限，含/不含重力补偿前馈）vs 3% 残差——用数据回答组会"为什么不全接管"（`torque_takeover` 模式已埋入 env）
- **budget sweep**：0/1/3/5/10%/全接管 单图
- **ESN 消融表**：derivative-matching on/off、通道缩放、CR 扫描（设计坍缩作为分析小节）
- 必要时在 PaperMPC 环境上重蒸馏 ESN（零迁移若降级）

### 8.4 远期（系统移植与真机）

1. `compliance.py` Protocol Facade 包 ESN（半天工作量，接入即实例化）
2. 论文系统 SHADOW 模式试跑（零风险集成测试）→ ACTIVE
3. 在论文系统场景分布（动态障碍长程操作）上重训/微调 ESN，系统级指标 + 力域指标双评
4. FR3 真机：FCI 1kHz 力矩流，上层低频发速度、底层高频伺服+残差（速率分层已建模）
5. 论文定位：**挂在名义控制器层上的通用残差力矩柔顺层**（ESN 为核心算法），在三种名义控制器、多种参考时序、三类撞击工况上验证

---

## 9. 经验教训存档

1. **契约先行**：WBC 可替换 adapter 的设计承诺，让两次换控制器零改柔顺层；
2. **强基线要自己调到稳定为止**（VMC 五轮迭代），否则对比无效；
3. **原作者代码是最好的规范**（ζ≈0.04 佐证 spring-only；MPC 实为一步二次型）；
4. **位置指标 vs 力域指标**：名义控制器越强，柔顺的贡献越应向力域收敛——这是叙事的自我修正；
5. **每个"加料"都要消融表挣座位**，证伪的（mirror gate）果断删。
