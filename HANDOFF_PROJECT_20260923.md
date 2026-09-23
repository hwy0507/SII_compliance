# SII Compliance / FR3 柔顺控制项目：完整交接文档

**文档版本：** 2026-09-23
**交接对象：** 后续接手本项目的 agent、研究助理或论文合作者
**项目仓库：** [hwy0507/SII_compliance](https://github.com/hwy0507/SII_compliance)
**当前 GitHub 主线 commit：** `8eb9ab1488f99dc8e5493f28b82744662bc5ece5`
**服务器：** `arm1@192.168.31.70`，主机名 `spark-4eb4`
**服务器项目根目录：** `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/`

---

## 0. 先读这里：最重要的结论和边界

这个项目不是“训练一个网络替代整套机器人系统”，而是：

1. 保留高层任务规划器和名义 WBC；
2. 用 VMC 在多个接触物理条件下生成高质量的柔顺 action teacher；
3. 让 MLP、ESN 或其他 student 只根据 FR3 在真实部署中可获得的本体信息，直接预测柔顺 action；
4. 在冻结模型后，把它们放到训练时没有见过的新物体、新布局、新接触顺序和组合事件的复杂办公室场景中测试。

当前统一的 student 学习目标是 **动作本身**，不是 VMC 参数：

```text
错误理解：student 输入本体状态，输出 VMC 的 K/D/M 参数
当前正确理解：student 输入本体状态，直接输出 7 维柔顺 action
```

7 维 action 为：

```text
[slowdown,
 yield_vx, yield_vy, yield_vz,
 yield_wx, yield_wy, yield_wz]
```

VMC 参数只用于 teacher 的生成和记录，不能作为 MLP/ESN 的训练标签。teacher action 是 VMC 经过物理仿真、安全过滤和任务筛选后实际执行的最终 action。

当前已完成的工作可以分成四层：

| 层 | 状态 | 说明 |
|---|---|---|
| 物理场景 | 已完成开发验收 | 球撞、持续棍推、两个桌角/厚桌角、复杂办公室场景均已搭建过 |
| VMC teacher | 已有可用候选和搜索脚本 | 需要继续按严格 split 重建正式 teacher bank |
| MLP/ESN | 已有 BC、ESN reservoir、readout 和评估入口 | 综合办公室的旧 ESN128 版本抓起成功但最终放置失败 |
| 论文级结论 | 尚未完成 | 目前不能宣称 ESN 在所有场景、所有指标上显著优于所有 baseline |

特别注意：项目经历了大量早期原型，旧版斜木板、早期单棍、VMC 参数学生、PPO stiffness、Direct-ESN、Fan-Ye ESN 和办公室恢复脚本仍然存在于服务器历史归档中，但不能自动当作当前论文主线。

---

## 1. 论文问题定义

### 1.1 研究目标

目标是为真实 FR3 机械臂设计一种低层柔顺控制器，使机械臂在执行抓取—抬升—搬运—放置任务时，面对下列情况能够安全、平滑且任务导向地响应：

- 高速球体突然撞击末端；
- 棍子或人手持续推动末端；
- 抓取物块从桌下抬升时擦到桌角/桌板边缘；
- 真实办公室中的水杯、柱子、桌边或多个障碍物组合；
- 障碍物未建模或无法提前预测；
- 外部作用结束前也不能依靠“等待固定时间”或视觉判断恢复。

最终想证明的是：

> 对特化 primitive fixture 分别调优的 model-based VMC 可以提供足够丰富的动作分布；具备时间记忆的 ESN 可以从这些 action teacher 数据中学习一个统一映射，在未知复杂场景中比固定 VMC、无记忆 MLP 和传统笛卡尔阻抗/导纳控制拥有更好的综合柔顺性和泛化能力。

### 1.2 真实部署信息边界

student 在部署时允许读取：

- 关节位置 `q`；
- 关节速度 `qdot`；
- 电机电流或关节力矩估计；
- 由机器人模型计算的末端位姿、速度；
- 名义 WBC 的目标/跟踪误差；
- 由关节负载和动力学项因果估计的末端 6D wrench；
- 任务阶段命令或名义任务速度（如果该信号在真实系统中确实可得）。

student 不允许读取：

- 障碍物位置、速度、几何和类别；
- MuJoCo 的 contact pair 真值；
- signed distance、contact normal 的仿真真值；
- 未来状态、未来外力或障碍物撤回时间；
- 由脚本硬编码的事件时钟；
- “球撞击已经发生”“棍子已经退出”等 privileged event flag。

teacher 可以在离线仿真中利用更完整的信息筛选成功轨迹，但 privileged 变量只能用于标签生成、任务 gate 和物理审计，绝不能进入 student observation。

### 1.3 柔顺行为定义

柔顺不是“机械臂永远贴着原轨迹”。在接触期间合理行为是：

1. 法向方向降低等效刚度，允许末端让位；
2. 持续推压时沿切向或可行方向绕开，而不是突然向后甩臂；
3. 不能穿过刚体障碍物；
4. 不应把大力矩传递到上游关节；
5. 外力尚未撤离时不能依赖“棍子退回去以后再回位”；
6. 外力撤离后平滑重新加入名义轨迹；
7. 继续完成抓取、抬升、搬运和放置。

因此评价必须同时考虑接触阶段和恢复阶段，而不能只看整个回合的平均轨迹误差。

---

## 2. GitHub、服务器和本机工作树的真实状态

### 2.1 GitHub 当前主线

截至 2026-09-23，远端只保留：

```text
main
```

当前主线 commit：

```text
8eb9ab1488f99dc8e5493f28b82744662bc5ece5
```

已从远端删除的历史分支：

```text
archive/origin-main-20260923
paper-mpc-baseline
codex/fr3-nus-mujoco-progress
```

删除前已导出到服务器，不是直接丢弃。当前 GitHub 的 `main` 保留 canonical 源码、配置、测试和必要文档，不包含大型 GIF、MP4、checkpoint、运行日志和历史输出。

### 2.2 服务器上的历史归档

整理前的完整 `origin/main` 快照：

```text
/home/arm1/SII_compliance_archive/20260923_origin_main_5d0e457/
```

主要文件：

```text
SII_compliance_origin_main_5d0e457.tar.gz
sii_compliance_origin_main_5d0e457.sha256
METADATA.txt
```

从 GitHub 主线移出的旧代码、旧报告和旧实验输出：

```text
/home/arm1/SII_compliance_archive/legacy_20260923_removed_from_main/
```

主要文件：

```text
removed_files.tar.gz
sii_removed_manifest.json
sii_remove.list
```

非主线 branch snapshot：

```text
/home/arm1/SII_compliance_archive/github_branches_removed_20260923/
```

包括：

```text
paper-mpc-baseline_9cac814.tar.gz
codex_fr3-nus-mujoco-progress_32d111a.tar.gz
BRANCH_COMMITS.txt
SHA256SUMS
```

### 2.3 当前 canonical 源码

GitHub `main` 的当前 MuJoCo 源码主目录：

```text
code/mujoco_6d_vmc_benchmark/
```

服务器对应目录：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/
```

服务器源码导出 provenance：

```text
code/mujoco_6d_vmc_benchmark/docs/server_source_20260923.json
```

当前 provenance manifest 覆盖 120 个 `scripts/*.py` 文件，包含源路径、文件大小和 SHA-256。校验命令：

```bash
cd code/mujoco_6d_vmc_benchmark
python tools/check_source_export.py
```

### 2.4 本地原始工作树注意事项

本地工作树：

```text
/Users/hwy/Desktop/个人/科研/SII科研/compliance
```

这个工作树在长期实验过程中积累了大量用户未提交内容，包括：

- `outputs/`；
- `remote_work/`；
- 临时 patch；
- 历史 JSON/NPZ；
- 旧版 GIF 删除后的 git 状态；
- 与早期 direct-action 路线相关的文件。

不要对这个原始工作树执行：

```bash
git reset --hard
git clean -fd
git checkout -- .
```

新 agent 应优先：

1. clone GitHub `main`；或
2. 直接进入服务器 canonical 目录；或
3. 使用一个新的 worktree。

不要把本地脏工作树的旧 `README.md`、旧 `code/direct_action/` 或旧 `outputs/` 自动当成 GitHub 当前主线。

---

## 3. 当前代码组织

### 3.1 主线执行链

```text
fixed_panda_wbc.py / paper_mpc_wbc.py
              ↓
wbc_velocity_residual_core.py
              ↓
fr3_contact_interface_20260917.py
              ↓
run_vmc_6d_constrained_push_20260918.py
              ↓
search_unified_6d_teacher_20260921.py
              ↓
build_current_teacher_bank_20260921.py
              ↓
audit_four_scene_dataset_20260918.py
              ↓
train_matched_action7_20260921.py
              ↓
run_matched_stage1_20260921.py
              ↓
evaluate_matched_guarded_push_20260921.py
              ↓
office_complex_scene_v5_20260917.py
```

### 3.2 关键脚本索引

| 文件 | 职责 | 使用建议 |
|---|---|---|
| `scripts/fixed_panda_wbc.py` | 固定基座 FR3/Panda resolved-rate WBC | 名义速度和姿态控制参考 |
| `scripts/paper_mpc_wbc.py` | paper-style velocity/reference layer | 论文中 paper-WBC 的参考实现 |
| `scripts/wbc_velocity_residual_core.py` | 统一 7D action、安全过滤、速度伺服、力矩约束 | 所有方法应复用 |
| `scripts/fr3_contact_interface_20260917.py` | 因果 joint-load observer、6D wrench 估计 | student 的本体力觉输入来源 |
| `scripts/run_vmc_6d_constrained_push_20260918.py` | 6D VMC dynamics 和棍推验收场景 | VMC teacher 核心 |
| `scripts/vmc_compliance_baseline.py` | VMC 兼容封装 | baseline 和复用接口 |
| `scripts/vmc_torque_baseline.py` | 力矩形式 VMC | 历史/对照使用 |
| `scripts/search_unified_6d_teacher_20260921.py` | 多场景 6D VMC 参数搜索 | teacher 候选生成 |
| `scripts/build_current_teacher_bank_20260921.py` | 构建 teacher bank | 统一数据集入口 |
| `scripts/audit_four_scene_dataset_20260918.py` | 数据来源、物理有效性、split 审计 | 训练前必须执行 |
| `scripts/convert_push_teacher_to_proprio48_20260921.py` | 历史 trace 转 canonical proprio observation | 旧数据迁移 |
| `scripts/train_matched_action7_20260921.py` | MLP / nonlinear ESN / linear ESN 公平训练入口 | 当前推荐入口 |
| `scripts/train_current_mlp_action7_20260921.py` | MLP action BC | MLP 对照训练 |
| `scripts/train_esn128_action7_20260918.py` | 128 reservoir + 128 readout 版本 | 旧版 ESN128 复现 |
| `scripts/esn128_action7_20260918.py` | ESN128 模型和推理 contract | 旧版模型加载 |
| `scripts/current_student_policy_20260921.py` | 冻结 student 推理接口 | 部署/评估加载 |
| `scripts/run_matched_stage1_20260921.py` | 多 seed 训练、验证、选模 | 统一训练预算 |
| `scripts/evaluate_matched_guarded_push_20260921.py` | student 冻结后的棍推评估 | 基础场景验证 |
| `scripts/office_complex_scene_v5_20260917.py` | 复杂办公室开发场景 | 泛化开发测试 |
| `scripts/run_rod_perturbation_benchmark.py` | rigid / impedance / VMC 等对照 | 经典 baseline 验证 |
| `scripts/run_grasp_impact_benchmark.py` | 抓取和球撞基础 fixture | 物理抓取/冲量检查 |
| `scripts/run_panel_push_20260920.py` | 棍推和挡板约束 | 持续推压与绕行 |
| `scripts/run_loaded_push_audit_20260918.py` | 持物棍推、抓取后安全审计 | 避免“棍子一撤才回位” |
| `scripts/render_compliance_audited.py` | 物理审计后的渲染和指标输出 | GIF 必须配合数值审计 |
| `scripts/scene_gates.py` | 任务成功和物理有效性 gates | 不能只看动图 |

### 3.3 Legacy 代码

下列路线存在过，但已经不是当前 GitHub `main` 的论文主入口：

- early Direct-ESN / Fan-Ye ESN；
- PPO、RL stiffness 和 residual policy；
- Fetch/ManiSkill whole-body-motion-control；
- 早期斜木板、薄桌板、旧桌角；
- 早期固定时间释放、固定时间回位规则；
- 历史办公室 recovery 版本；
- 早期 CEM 参数学生版本。

这些内容在服务器 `legacy_20260923_removed_from_main` 中保存。当前 `scripts/` 中仍可能有少量旧日期后缀文件，是为了兼容 office/runtime 动态 import；看到文件存在不代表它是当前论文结论。

---

## 4. 统一控制接口和数学模型

### 4.1 名义 WBC / paper-WBC

高层规划器产生任务 waypoint、目标位姿和名义末端 twist。固定基座 WBC 将名义 Cartesian command 转为关节速度：

$$
\dot q_{\mathrm{nom}}
=\operatorname{clip}\left(
J^\#(q)\left(\nu_d+K_e e_{SE(3)}\right)
+(I-J^\#J)\dot q_{\mathrm{null}},
-\dot q_{\max},\dot q_{\max}
\right).
$$

paper-style reference layer 的简化速度更新可以表示为：

$$
\dot q_{\mathrm{nom}}
=\operatorname{clip}\left(
g(Q+R)^{-1}Q(q_{\mathrm{ref}}-q),
-\dot q_{\max},\dot q_{\max}
\right),
$$

并通过 waypoint queue、nearest waypoint 和 lookahead 保持名义轨迹连续。当前仿真主线没有把视觉障碍物真值直接交给柔顺 student。完整 NUS 高层视觉规划器尚未作为当前 top-level runner 完全复现；目前主要复现了其 velocity-aware / nominal velocity 到低层控制接口的结构。

### 4.2 7D action

所有需要公平比较的方法都输出同一个动作：

$$
a_t=\left[
a_t^{slow},a_t^{v_x},a_t^{v_y},a_t^{v_z},
a_t^{\omega_x},a_t^{\omega_y},a_t^{\omega_z}
\right]\in[-1,1]^7.
$$

第一个通道请求降低名义 WBC 速度比例，后六个通道是末端线速度和角速度残差。典型映射为：

$$
s_t=1-\max(0,a_t^{slow})(1-s_{\min}),
$$

$$
\xi_{yield,t}
=a_{t,1:6}\odot
[v_{max,x},v_{max,y},v_{max,z},
\omega_{max,x},\omega_{max,y},\omega_{max,z}],
$$

$$
\dot q_{cmd}
=s_t\dot q_{nom}+J^\#(q)\xi_{yield,t}.
$$

之后经过统一的 action clipping、slew-rate limiting、关节速度/加速度约束、阻尼伪逆和 torque safety projection。最终力矩包含速度伺服和 bias/gravity compensation：

$$
\tau_{servo}=\tau_{bias}+K_v(\dot q_{cmd}-\dot q),
$$

$$
\tau_t=\operatorname{rate\_limit}
\left(\operatorname{project}_{[-\tau_{max},\tau_{max}]}
(\tau_{servo})\right).
$$

因此比较方法时，不能改变高层轨迹、WBC、动作缩放或安全层，否则不是公平对照。

### 4.3 接触力和本体 wrench

student 不读取 MuJoCo contact truth。`fr3_contact_interface_20260917.py` 用关节侧负载、bias 和 Jacobian 做因果估计：

$$
\hat\tau_{ext}
=\tau_{measured}-\tau_{model}(q,\dot q)-\tau_{servo},
$$

$$
\hat w_{ext}
=\left(J^T\right)^\#\hat\tau_{ext}.
$$

实际代码还包含滤波、死区、力/力矩限幅以及数值稳定处理。contact pair、真实接触法向和 penetration 只能用于仿真物理审计，不得放进 student observation。

---

## 5. VMC baseline 和 teacher

### 5.1 VMC 的设计

VMC 在本项目中同时是 baseline 和 teacher。当前正式版本扩展到 6D：3 个平移通道 + 3 个旋转通道。

基本方程：

$$
M_v\ddot x_v+D_v\dot x_v+K_vx_v
=\operatorname{sat}_{\sigma}(\hat w_{ext}),
$$

其中 $x_v\in\mathbb R^6$ 是虚拟位移/小角度姿态偏移，$M_v,D_v,K_v$ 是 6D 对角或主轴坐标系下的参数，$\hat w_{ext}$ 是本体负载观测器给出的 6D wrench。弹簧力使用平滑饱和避免大误差发散：

$$
f_K(x_v)=\sigma\tanh(K_vx_v/\sigma).
$$

主轴旋转通过固定 `axis_rotation_rpy` 将世界坐标中的接触方向映射到虚拟模型主轴。最后输出 6D yielding velocity，再映射为统一 7D action。

### 5.2 VMC 搜索参数

当前扫描对象不应只包含一个标量 stiffness。至少包括：

- $K_x,K_y,K_z,K_{r_x},K_{r_y},K_{r_z}$；
- $D_x,D_y,D_z,D_{r_x},D_{r_y},D_{r_z}$；
- $M_x,M_y,M_z,M_{r_x},M_{r_y},M_{r_z}$；
- force / moment saturation；
- 各轴 deadband；
- virtual velocity limit；
- virtual offset limit；
- displacement feedback gain；
- wrench filter time constant；
- action amplitude / slew limit；
- 主轴 RPY；
- 棍推场景中的接触持续、回归和安全边界相关 teacher 参数。

早期搜索曾经达到约 41 个标量编码维度。参数量大时不能直接暴力全网格，应使用：

1. warm-start feasible VMC；
2. 对角 CEM / 局部扰动；
3. 分阶段扩大范围；
4. 每个 physical fixture 独立搜索；
5. 先做任务/物理 gate，再保留 Pareto 候选；
6. 已通过的 best 不能被失败候选覆盖；
7. 固定随机种子和候选列表，保证可恢复。

### 5.3 Teacher 不是单一“最优参数”

三个核心指标存在冲突：

- 轨迹误差越小通常意味着更硬；
- 接触力越小通常需要更多让位；
- 力矩峰值越低可能牺牲回位速度；
- 持续推压场景还要考虑切向绕行和任务完成。

因此 teacher 选择应采用分层筛选：

```text
第一层：任务必须完成
第二层：真实接触、无上游误碰、无穿模、夹持有效
第三层：速度/力/力矩/轨迹误差满足安全阈值
第四层：在多目标指标上保留 Pareto 非支配候选
```

不要只用一个手工 weighted sum 选出一条 teacher；需要保留多组不同接触方向、入射角、加载时间和 VMC 参数的动作，才能给 ESN/MLP 学到真实 action distribution。

---

## 6. MLP baseline

MLP 是无显式递归状态的 feed-forward behavior cloning baseline。它与 ESN 必须使用：

- 相同 observation contract；
- 相同 7D action contract；
- 相同 teacher 数据；
- 相同 train/validation/test fixture split；
- 相同 seed 数量和训练预算；
- 相同 action scaling、loss weighting 和输出安全层。

典型形式：

$$
h_1=\phi(W_1\tilde o_t+b_1),
$$

$$
h_2=\phi(W_2h_1+b_2),
$$

$$
\hat a_t=W_oh_2+b_o.
$$

其中 $\tilde o_t$ 是标准化本体观测，$\phi$ 通常为 ReLU、tanh 或代码中配置的激活函数。训练目标是 teacher action 的加权 MSE：

$$
\mathcal L_{MLP}
=\frac1N\sum_t
\left\|\operatorname{diag}(s_a)^{-1}
(\hat a_t-a_t^{teacher})\right\|_2^2.
$$

MLP 没有 reservoir state，因此每一个动作只由当前 observation 决定。如果“接触还在持续”和“接触已经结束”在当前观测上很相似，MLP 容易发生：

- 棍子未撤回就过早回位；
- 外力撤离后持续输出让位；
- 进入 lift 后速度残差不能归零；
- 多场景 teacher action 冲突时输出平均动作。

这正是 ESN 时间状态需要被验证的地方，而不是默认 ESN 一定更好。

---

## 7. ESN：当前应该如何理解

### 7.1 ESN 结构

ESN 由固定随机 reservoir 和可训练 readout 组成。当前主线训练的是 action readout，而不是 VMC 参数：

$$
z_t=[\tilde o_t,h_{t-1}],
$$

$$
h_t=(1-\alpha)h_{t-1}
+\alpha\tanh(W_{in}\tilde o_t+W_{res}h_{t-1}+b),
$$

$$
\hat a_t=W_{out}[\tilde o_t,h_t]+b_{out}.
$$

reservoir 权重随机初始化后固定；通常只训练 readout。这样 ESN 仍然有“训练”：

- reservoir 本身不通过梯度学习；
- readout 通过 ridge regression、闭式最小二乘或 Adam 训练；
- 如果使用 online RLS，则 readout 在部署过程中继续递归更新；
- 当前 canonical action-distillation 版本默认是固定 reservoir + supervised readout，不应把历史在线 RLS 版本混称为同一个模型。

### 7.2 ESN 的时间记忆意义

碰撞本身是瞬时的，但柔顺行为不是瞬时分类问题。历史信息可以帮助区分：

- 当前力觉是第一次冲击还是持续推压；
- 末端偏移是仍被障碍物约束还是已经自由；
- 当前速度偏差是接触让位动作还是释放后的回位过程；
- 棍子是否持续在手部接触附近；
- 机械臂是否已经完成 grasp、lift、carry 等阶段转换。

因此 ESN 的优势不是“记住一个碰撞发生过”，而是把一段因果传感序列编码为低维隐状态，从而输出有阶段一致性的 action。

### 7.3 ESN 公平性

ESN 不能获得 MLP 没有的额外视觉、事件 flag、未来窗口或 teacher 参数。公平比较至少应报告：

- trainable parameter count；
- 固定 reservoir 参数是否计入模型容量；
- readout 参数量；
- MLP hidden width/depth；
- reservoir size、spectral radius、leak rate；
- 相同的输入维度、动作维度、训练样本数、seed 和 early stopping 规则。

历史 ESN128 版本：

```text
45 维本体观测/任务命令
        ↓
128 个固定 reservoir 神经元
        ↓
当前观测 + reservoir state
        ↓
128 个 tanh readout 隐藏单元
        ↓
7 维 action
```

实际可训练参数约 23,175，训练使用 120 epochs，训练本身约 23.5 秒。但这个 ESN128 版本是 2026-09-18 的旧综合场景开发版本，不能直接等同于最终论文 frozen checkpoint。

### 7.4 ESN 训练方式

当前 canonical 训练入口：

```bash
python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/esn_run \
  --model esn_nonlinear \
  --seed 20260921
```

线性 readout 消融：

```bash
python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/esn_linear_run \
  --model esn_linear \
  --seed 20260921
```

该流程原则上包括：

1. 按 scene / fixture / VMC parameter group 做互斥 split；
2. 只用 train split 计算 observation/action normalization；
3. 按场景和轨迹均衡采样，避免 ball 样本数量压过 corner；
4. 每条 trajectory 在开始时 reset reservoir state；
5. teacher action 是实际执行且经过安全层的 action；
6. validation 只用于选 checkpoint，不用于修改测试协议；
7. 最终 test fixture 完全冻结后再运行。

历史项目还实现过 BC、ridge、DAgger、CEM readout refinement 和 online RLS。它们可以作为 ablation 或后续研究，但不能在报告中把不同版本混合成一个“ESN”。

---

## 8. 场景设计和物理约束

### 8.1 四个 primitive fixture / 三类行为

论文实验通常将场景按行为归类为三类，但 teacher 数据更准确地分为四个 fixture：

1. **ball**：动态球短时冲量撞击末端；
2. **rod/push**：棍子或人手持续推压末端；
3. **pre-grasp table corner**：抓取前接触桌角；
4. **loaded/thick table corner**：夹持物块后抬升并擦过厚桌角，最终放到桌面。

因此不要在文档中说“只有三个数据场景”而漏掉两个桌角状态；更准确的说法是“球、棍推、桌角三类接触行为，桌角包含抓取前和持物两个 physical fixture”。

### 8.2 球撞场景

物理要求：

- 球是有限质量刚体；
- 球通过初始速度或约束释放产生真实冲量；
- 不允许 teleport 到机械臂内部；
- 必须在 physics substep 记录 contact force、impulse、接触对象和最大 penetration；
- 末端要产生可见偏移，不能“几千牛但机械臂一动不动”；
- 撞击后要录制完整回位过程，不能只录第一帧或截断在冲击瞬间；
- 抓取动作必须在冲击前尚未完成，避免把球撞击变成无任务意义的后处理。

### 8.3 棍推场景

棍子用于模拟人手持续推着机械臂移动，不是简单碰一下：

```text
接近 → 接触 → 持续推压 → 机械臂让位/绕行 → 棍子仍在接触时保持柔顺 → 棍子撤回 → 回到名义轨迹 → 抓取/抬升
```

不能使用以下不合格做法：

- 固定 0.55 s 或固定 8.0 s 回位；
- 读入棍子是否已经撤回的事件标志；
- 棍子撤回后才突然执行回位；
- 用视觉判断棍子离开；
- 棍子穿过 hand collision；
- 棍子只接触空气或擦过末端。

挡板用于约束机械臂前后大幅甩臂，形成合理的“只能从棍子旁边蹭过去”假设。挡板也必须是真实有厚度的刚体，且只约束末端附近，不应误伤 FR3 上游关节。

### 8.4 桌角定义

“桌角”不是一块斜木板，也不是两条无厚度的公共边。最终桌角应理解为：

- 水平桌板，有厚度；
- 竖直 apron/侧板，有厚度；
- 两者宽度一致；
- 竖直板朝机械臂的那条边与横向板边缘完全重合；
- 不存在可见空隙或突出；
- 机械臂只能碰到物理实体，不得穿模；
- 末端直上直下时与桌角边缘产生合理接触，然后通过切向滑移上桌。

桌角场景的成功不只是“擦到边”：

1. 物块必须被真实夹持；
2. 末端从桌下向上移动；
3. 末端/物块必须与竖直板或桌板边缘有真实接触；
4. 需要完成柔顺让位和切向滑移；
5. 物块最终稳定放在水平桌面上；
6. 释放动作必须由“物块稳定接触桌面”决定，而不能由固定时间替代；
7. 不能出现物块抬起后滑落、穿过桌板、只擦边不放置或释放过早。

### 8.5 复杂办公室场景

办公室开发场景包含过往讨论过的：

- 水杯；
- 柱子；
- 桌边/桌角；
- 球；
- 行人手/棍子类外力；
- 多事件组合和不同布局。

它的作用是最终泛化测试，不是 teacher 训练集。办公室里的球曾经使用旧硬接触模型，而 primitive teacher 中部分球使用软壳球，这会造成接触力分布偏移，必须在报告中明确。

---

## 9. 已完成的 VMC 棍推验收结果

服务器交接文档：

```text
remote_work/VMC_6D_CONSTRAINED_PUSH_HANDOFF_20260918.md
```

服务器脚本：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/run_vmc_6d_constrained_push_20260918.py
```

验收网页：

```text
http://192.168.31.70:8765/vmc6d_constrained_push_20260918.html
```

代表性成功回合设置：

- 棍推角度约 `0.35 rad`；
- 棍高约 `0.60 m`；
- 持续推入约 `3.8 s`；
- 前后边界约为 `x=0.715 m` 和 `x=0.365 m`；
- hand collision 直接与棍子发生接触；
- 挡板用于防止大幅后撤；
- 控制器仍然是 VMC，不是视觉规划器或事件规则。

代表性结果：

| 指标 | 值 |
|---|---:|
| 任务成功 | 是 |
| 峰值接触力 | 约 125.1 N |
| 峰值关节力矩 | 约 39.63 N·m |
| 末端最终误差 | 约 7.2 mm |
| 切向绕行量 | 约 38.6 mm |
| 最大数值压入 | 约 0.108 mm |

这个结果证明 VMC teacher 在该棍推 fixture 上存在“持续接触、先让位、沿切向绕行、随后重新抓取”的可用行为，但它只是一个开发验收回合，不能直接作为最终泛化 benchmark。

---

## 10. 2026-09-18 ESN128 综合办公室结果

这部分是重要的失败结果，不能省略。

### 10.1 模型

旧版 ESN128 结构：

```text
45 维本体观测和任务命令
        ↓
128 维固定 reservoir
        ↓
当前输入 + reservoir state
        ↓
128 维 tanh readout hidden layer
        ↓
7 维 action
```

训练：

- 四类冻结 primitive teacher 数据；
- 120 epochs；
- AdamW；
- GPU 约 23.5 s；
- 可训练参数约 23,175；
- 不使用办公室数据训练；
- 本轮没有 RL、CEM 或 office 上调参；
- checkpoint 只按基础场景 validation 选取。

### 10.2 结果

综合办公室每个布局运行约 55 s，结果如下：

| 布局 | 抓起 | 最终放置 | 接触后轨迹 RMSE | 速度 P95 | 峰值关节力矩 | 最大压入 | 物理验收 |
|---|---|---|---:|---:|---:|---:|---|
| 0 | 是 | 否，停在抬升 | 4.899 cm | 0.0719 m/s | 45.297 N·m | 0.1974 mm | 通过 |
| 1 | 是 | 否，停在抬升 | 4.705 cm | 0.0857 m/s | 44.786 N·m | 0.2014 mm | 未通过 |
| 2 | 是 | 否，停在抬升 | 4.544 cm | 0.0726 m/s | 45.950 N·m | 0.2275 mm | 未通过 |

现象：

- 三个布局都抓起了物块；
- 三个布局都没有最终放置；
- 外部推压结束后，ESN 仍持续输出速度修正；
- 末端没有稳定停进抬升目标附近；
- 因此没有进入搬运和释放阶段；
- 既有任务 gate 要求位置误差小于 12 mm、线速度小于 0.025 m/s，并连续保持 0.2 s；
- 本轮没有放宽 gate，也没有提前释放来制造成功。

布局 1、2 的最大数值压入分别约 `0.2014 mm` 和 `0.2275 mm`，超过既定 `0.2 mm` 门槛，不应直接并入正式性能统计。布局 0 物理验收通过但任务失败，说明问题不能全部归因于环境。

当时记录的可能原因包括：

- 基础 teacher 中没有足够多的“接触结束后、持物、接近目标时”动作；
- 多个 teacher action 在相似本体观测下存在冲突；
- 训练数据覆盖了接触，但没有充分覆盖任务阶段收敛和 release 前稳定状态；
- 办公室硬接触球与训练软壳球存在接触模型分布偏移；
- ESN 的持续 residual 没有在正确的任务状态下自然衰减。

这些是待验证假设，不能直接写成已经证明的根因。

网页和服务器目录曾使用：

```text
http://192.168.31.70:8765/esn128_office_20260918.html
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/esn128x128_four_scene_20260918/
```

---

## 11. teacher 数据、split 和数据泄漏规则

### 11.1 数据样本

每一个训练样本至少包含：

```text
observation_t
teacher_action_t
scene_id
fixture_id / physical_group_id
VMC parameter group
trajectory_id
timestamp / phase metadata（仅审计和分层，不直接给 student）
```

student observation 必须去除：

- 障碍物真值；
- contact pair；
- future state；
- episode event label；
- teacher 参数本身。

### 11.2 分层 split

正式 split 必须按以下层级进行：

```text
scene / fixture / VMC parameter group
```

硬性要求：

1. 同一个 physical fixture 不能同时出现在 train 和 test；
2. 同一个 parent group 的重复轨迹不能跨 split；
3. 相同 VMC parameter group 的近重复轨迹不能造成泄漏；
4. ball、rod、pre-corner、loaded-corner 需要做场景均衡；
5. validation 只用于选 checkpoint；
6. office 不参与训练和超参数搜索；
7. 先冻结 split，再冻结模型，再跑 blind office test。

### 11.3 teacher 数据增强

可以增强：

- 初始 arm posture；
- 棍入射角和推压方向；
- 球质量、半径、初速度、撞击点；
- 桌角高度、边缘接触点、桌板厚度；
- 持物质量和物块位置；
- 接触持续时间；
- 摩擦、阻尼、solver/contact time constant；
- 目标轨迹速度；
- sensor noise 和控制延迟。

不能增强为“作弊”的内容：

- 直接向输入加入障碍物类别；
- 输入棍子是否撤回；
- 输入球的未来速度；
- 输入固定 recovery timer；
- 用办公室测试轨迹重新加入 teacher bank 后仍称作 zero-shot generalization。

---

## 12. 指标定义

### 12.1 任务成功率

一次回合只有在以下全部满足时才算成功：

1. 夹爪真实闭合并保持物块；
2. 物块被抓起到要求高度；
3. 避障或接触阶段满足物理 gate；
4. 物块真实接触目标桌面；
5. 物块稳定保持一段时间；
6. 释放发生在稳定接触之后；
7. 物块没有掉落、穿模或离开目标区域。

固定时间释放，例如 `8.0 s`，不能作为最终判据，只能作为旧版 debug 逻辑。

### 12.2 轨迹跟踪误差

建议分阶段统计：

$$
e_{traj}^{phase}
=\sqrt{\frac1{|\mathcal T_{phase}|}
\sum_{t\in\mathcal T_{phase}}
\|p_t-p_t^{ref}\|_2^2}.
$$

至少分为：

- pre-contact；
- contact/yield；
- post-contact recovery；
- grasp/lift；
- carry/place。

不能只报整段平均 RMSE，因为持续推压时的合理让位会被平均掉。

### 12.3 速度平稳性

报告：

- 线速度 P50/P95；
- 峰值线速度；
- 速度突变或 jerk；
- contact 后最大前冲；
- recovery 期间速度衰减时间。

棍推场景重点看“接触仍在持续时是否持续绕行”，不能只看棍子撤回后是否回位。

### 12.4 峰值力和冲量

按外物分开统计：

- ball peak force / impulse；
- rod/person sustained force；
- table corner normal/tangential force；
- robot–floor 或 robot–panel 非预期接触。

不要把球的瞬时冲量峰值和棍子的持续推力混成一个数字。

### 12.5 关节力矩

报告：

- 全周期最大关节力矩；
- contact phase 峰值；
- recovery phase 峰值；
- 每个关节的峰值；
- torque-rate 或高频突变。

同时检查是否因为安全层饱和导致“看起来没撞动但其实控制器已经打满”。

### 12.6 物理有效性

至少包含：

- 最大数值 penetration；
- 非预期上游 link contact；
- hand/terminal contact 是否真实发生；
- 物块是否掉落；
- 夹爪接触是否持续；
- target table contact 是否真实发生；
- 球—地板、棍—桌角等不相关接触是否污染回合。

物理无效的回合不能只因为任务成功就纳入正式算法统计。

---

## 13. 经典 Cartesian Impedance / Admittance baseline

该 baseline 是论文中必须补齐的传统控制对照，不能与 VMC 混写。

### 13.1 Cartesian impedance

设名义位姿和实际位姿为 $(p_d,R_d)$、$(p,R)$，速度误差为 $e_v$、角速度误差为 $e_\omega$：

$$
e_p=p_d-p,
\qquad
e_R=\operatorname{Log}(R_dR^T),
$$

$$
F=K_p e_p+D_p e_v,
\qquad
M=K_R e_R+D_R e_\omega,
$$

$$
\tau_{imp}=J^T[F,M]^T.
$$

阻尼可以按临界阻尼关系设置：

$$
D_p=2\zeta\sqrt{m_vK_p},
\qquad
D_R=2\zeta\sqrt{I_vK_R}.
$$

### 13.2 Cartesian admittance

导纳根据测得的外力驱动虚拟质量—阻尼—弹簧：

$$
M_a\ddot x_a+D_a\dot x_a+K_a x_a
=\hat w_{ext}.
$$

积分得到让位速度或位置残差，再通过 Jacobian 伪逆加入名义 WBC。它理论上更适合“外力到运动”的响应，但如果力估计延迟、摩擦或接触方向估计不准确，可能出现滞后、过冲或不沿切向绕行。

### 13.3 baseline 公平要求

Cartesian impedance、Cartesian admittance、VMC、MLP、ESN 必须共享：

- 同一 nominal WBC；
- 同一场景和物体质量；
- 同一控制周期和 MuJoCo solver；
- 同一抓取/放置 gate；
- 同一 torque limit、velocity limit、安全过滤；
- 各自只在基础训练场景上调参；
- 复杂 office test 时冻结参数。

当前仓库已有 baseline 扫描输出和 GIF，但传统 baseline 的完整论文级 multi-seed、同协议统一矩阵仍需检查是否已经重新生成。不要把历史 `final_gifs` 目录直接当成最终论文数字。

---

## 14. 已完成媒体归档和本机清理

### 14.1 GIF 归档

所有明确属于本项目的本机 GIF（排除 `Desktop/demo_0923`）已经归档到：

```text
/home/arm1/SII_compliance_archive/mac_gifs_20260923/
```

内容：

```text
gifs/
inventory.json
SHA256SUMS
METADATA.txt
```

统计：

```text
GIF 数量：443
原始总大小：3,332,420,329 bytes，约 3.10 GiB
SHA-256 校验：443/443 通过
服务器实际文件数：443
```

按日期、算法、场景分类。清单中保留原始路径和 mtime。

### 14.2 本地保留内容

明确保留：

```text
/Users/hwy/Desktop/demo_0923/admittance.gif
/Users/hwy/Desktop/demo_0923/impedance.gif
```

另有 3 个位于 `SII科研/Htr` 的 GIF 未纳入清理，因为它们属于另一个 grasp/prepose 子项目，不属于当前 compliance 项目。

### 14.3 删除原则

删除前执行：

1. 清单生成；
2. 原始文件 SHA-256 计算；
3. 上传到 Spark；
4. 服务器逐文件 SHA-256 校验；
5. 精确路径删除；
6. 删除后检查清单路径不存在；
7. 检查 `demo_0923` 仍存在。

本地操作记录：

- [GIF inventory](</Users/hwy/Desktop/个人/科研/SII科研/compliance/remote_work/mac_project_gif_inventory_20260923.json>)
- [GIF delete report](</Users/hwy/Desktop/个人/科研/SII科研/compliance/remote_work/mac_project_gif_delete_report_20260923.json>)
- [archive script](</Users/hwy/Desktop/个人/科研/SII科研/compliance/remote_work/archive_project_gifs_20260923.py>)
- [delete script](</Users/hwy/Desktop/个人/科研/SII科研/compliance/remote_work/delete_archived_project_gifs_20260923.py>)

---

## 15. 测试与复现命令

### 15.1 本地或服务器环境

服务器项目虚拟环境：

```bash
/home/arm1/vmc_mujoco_runtime/.venv/bin/python
```

建议环境变量：

```bash
export MUJOCO_GL=egl
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
```

需要 MuJoCo Menagerie 至少提供：

```text
<menagerie>/franka_fr3/
<menagerie>/franka_emika_panda/
```

### 15.2 源码 provenance

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark
python tools/check_source_export.py
```

### 15.3 canonical smoke

```bash
python scripts/run_source_demo.py \
  --config configs/ball_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-smoke/ball \
  --smoke
```

工位开发场景：

```bash
python scripts/run_source_demo.py \
  --config configs/workstation_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-demo/workstation \
  --render
```

### 15.4 canonical tests

在 2026-09-23 精简主线发布前已经通过：

```text
89 passed
```

执行命令：

```bash
PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts \
pytest -q code/mujoco_6d_vmc_benchmark/tests
```

如果新 agent 添加或删除脚本，必须重新跑测试和 provenance。不要为了“让测试全绿”恢复已经从 main 移出的历史测试；如果测试依赖被归档的旧脚本，应判断该测试是否属于当前 canonical 主线。

### 15.5 teacher 搜索和构建

典型顺序：

```bash
python scripts/search_unified_6d_teacher_20260921.py \
  --output /path/to/teacher_search

python scripts/build_current_teacher_bank_20260921.py \
  --search-root /path/to/teacher_search \
  --output /path/to/teacher_bank

python scripts/audit_four_scene_dataset_20260918.py \
  --dataset /path/to/teacher_bank
```

真实参数需先查看脚本 `--help`；不要盲目复用历史命令，因为不同日期后缀脚本的参数和输出 contract 不完全相同。

### 15.6 MLP/ESN 训练

```bash
python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/mlp_run \
  --model mlp \
  --seed 20260921

python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/esn_run \
  --model esn_nonlinear \
  --seed 20260921

python scripts/train_matched_action7_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/esn_linear_run \
  --model esn_linear \
  --seed 20260921
```

### 15.7 冻结评估

训练后必须冻结：

- checkpoint；
- normalization；
- split；
- 物理 fixture；
- metrics gate；
- 选模规则。

然后运行：

```bash
python scripts/run_matched_stage1_20260921.py \
  --dataset /path/to/audited_teacher_bank \
  --output /path/to/matched_stage1

python scripts/evaluate_matched_guarded_push_20260921.py \
  --checkpoint /path/to/frozen_checkpoint \
  --output /path/to/push_eval

python scripts/office_complex_scene_v5_20260917.py \
  --checkpoint /path/to/frozen_checkpoint \
  --output /path/to/office_eval
```

真实命令以脚本帮助为准。不要把 office 的失败轨迹回灌进训练集后继续称作 zero-shot 泛化。

---

## 16. 当前已知问题和不可宣称内容

### 16.1 已知问题

1. ESN128 综合办公室旧结果三回合都抓起但没有最终放置；
2. 学生在目标附近的 residual 没有稳定归零，可能存在 contact-end / lift / place 状态数据不足；
3. 多 teacher 动作在相似本体观测下可能存在冲突；
4. primitive 与 office 的球接触模型不完全一致；
5. 某些历史 office 回合 penetration 超过 0.2 mm，不能进入正式统计；
6. 传统 Cartesian impedance/admittance 的最终统一 multi-seed 矩阵需要重新确认；
7. 完整 NUS 视觉高层规划器尚未作为当前主线 top-level runner 完整复现；
8. sim-to-real 仍需要传感器标定、延迟、摩擦、质量和急停保护验证；
9. 现有很多历史文件仍在服务器 legacy archive 中，容易被误当成最新实现。

### 16.2 当前不能写进论文的强结论

不要宣称：

- ESN 已经在所有环境中全面超过 MLP、VMC、WBC、阻抗和导纳；
- 旧 ESN128 office 失败结果已经证明 ESN 无法泛化；
- teacher search 找到了全局最优 VMC；
- 仅凭 GIF 可以证明没有穿模或力矩安全；
- MuJoCo force threshold 等价于真实 FR3 安全认证；
- student 看到了 contact truth 或障碍物视觉；
- 历史 RL/CEM 代码就是当前默认训练方法；
- office 开发布局等价于最终 blind test。

---

## 17. 建议后续推进路线

### 阶段 A：先冻结实验协议

1. 固定四类 primitive fixture 的 XML、solver、contact mask、质量、摩擦和随机种子规则；
2. 明确 end-effector-only contact 还是允许上游 link contact；
3. 固定任务 gate、release gate、penetration gate、force/torque gate；
4. 固定 observation 维度和 action 7D contract；
5. 固定 train/validation/test fixture split；
6. 冻结办公室 blind test 布局，禁止按结果改场景。

### 阶段 B：补充 VMC teacher bank

1. 每个 primitive 生成足够多不同姿态、入射角、接触部位和接触持续时间；
2. 每个 fixture 扫描 6D VMC 参数和必要的 filter/saturation 参数；
3. 只保留任务成功且物理有效的轨迹；
4. 按 scene/fixture/parameter group 互斥 split；
5. 输出 Pareto frontier，而不是只保留一条动作；
6. 给每条 trace 保存参数、环境随机量、seed、代码 hash、metrics 和 source path。

### 阶段 C：先做 MLP，再做公平 ESN

1. 同 teacher bank 训练 MLP；
2. 同样本数、同 seed、同 optimizer budget 训练 nonlinear ESN；
3. 训练 linear-readout ESN 作为消融；
4. 不给 ESN 增加 MLP 没有的 privileged input、额外事件 gate 或手工平滑器；
5. 记录 trainable parameter count 和 inference latency；
6. 基础场景、跨 fixture test、组合 office test 分开报告。

### 阶段 D：重点修正“接触结束后的行为”

针对历史 office 失败，优先补以下 teacher 数据：

- 外力结束但物块仍被夹持时的稳定 hold；
- 持物 lift 目标附近的低速/零 residual 状态；
- 棍子仍在接触时的持续绕行 action；
- 棍子撤回后自然回位 action；
- 桌角接触后物块已经接触桌面的稳定放置 action；
- release 前的连续 0.2 s 稳态窗口。

不能用固定时间替代这些动作，也不能加入显式 `contact_ended` label。应让模型从本体 load/velocity history 学到这些阶段。

### 阶段 E：最终 baseline 矩阵

建议至少比较：

1. paper-WBC / rigid nominal；
2. tuned 6D VMC；
3. Cartesian impedance；
4. Cartesian admittance；
5. matched MLP；
6. linear ESN；
7. nonlinear ESN；
8. 如需 RL，单独说明它是否真正使用同一 7D action 和同一 observation contract。

每种方法都在 primitive 上调参，在 office 上冻结测试；不能给 ESN 额外调参机会。

### 阶段 F：sim-to-real 前检查

在真实 FR3 前至少做：

- observation delay randomization；
- torque/current noise；
- action latency；
- friction and payload randomization；
- contact stiffness randomization；
- torque-rate and joint-limit stress test；
- external emergency stop；
- 低速低能量 dry run；
- 无物块空载接触测试；
- 有物块但低高度测试；
- 逐步增加外力而不是直接复现仿真峰值。

---

## 18. 新 agent 的推荐接手步骤

### 第一步：确认环境和版本

```bash
git clone https://github.com/hwy0507/SII_compliance.git
cd SII_compliance/code/mujoco_6d_vmc_benchmark
git rev-parse HEAD
python tools/check_source_export.py
```

期望 main commit 为 `8eb9ab1...` 附近的当前主线，provenance 校验成功。

### 第二步：阅读文档顺序

```text
README.md
code/mujoco_6d_vmc_benchmark/README.md
code/mujoco_6d_vmc_benchmark/CODE_ORGANIZATION.md
code/mujoco_6d_vmc_benchmark/SOURCE_GUIDE.md
code/mujoco_6d_vmc_benchmark/docs/RESEARCH_ROADMAP.md
code/mujoco_6d_vmc_benchmark/docs/benchmark_protocol_v1.md
code/mujoco_6d_vmc_benchmark/docs/training_protocol_v0.md
```

然后再读：

```text
remote_work/VMC_6D_CONSTRAINED_PUSH_HANDOFF_20260918.md
remote_work/ESN128_OFFICE_HANDOFF_20260918.md
remote_work/OFFICE_SCENE_V5_HANDOFF_20260917.md
remote_work/VMC_AUTO_SEARCH_HANDOFF_20260920.md
```

### 第三步：先跑 smoke，不要直接开始大规模扫描

确认：

- FR3/Panda 模型可加载；
- hand collision 名称正确；
- 夹爪 actuator 存在；
- table/apron 几何没有空隙或穿模；
- action filter 数值稳定；
- contact audit 可以工作；
- GIF 不只是第一帧。

### 第四步：确认输出目录

每次新实验使用新的不可覆盖目录，例如：

```text
outputs/teacher_bank_rebuild_20260923/
outputs/mlp_esn_matched_20260923/
outputs/office_blind_eval_20260923/
```

不要覆盖历史结果，也不要把 output 重新提交到 GitHub。

### 第五步：先报告中间事实

每次长任务至少保存：

- command line；
- git/source hash；
- seed；
- scene config；
- parameter group；
- train/validation/test manifest；
- metrics JSON；
- failure reason；
- GIF/trace path；
- 当前 best 和 Pareto frontier。

---

## 19. 服务器长任务与安全规则

服务器连接：

```bash
ssh arm1@192.168.31.70
```

长任务必须使用 `tmux`、`nohup` 或 Python `start_new_session`，不能依赖本地 SSH 窗口持续存在。自动搜索脚本曾使用过：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MUJOCO_GL=egl \
../.venv/bin/python scripts/auto_search_workstation_vmc_20260920.py \
  --hours 10 --workers 12 --population 10 --rounds 80
```

旧自动搜索输出路径：

```text
outputs/vmc_auto_search_20260920/
```

开始新搜索前必须检查：

```bash
cat outputs/<run>/state.json
tail -n 100 outputs/<run>/search.log
ps -ef | grep -E 'python|mujoco|vmc|esn'
nvidia-smi
```

不要在一个正在运行的搜索目录里修改控制源文件。若必须修改，先停止旧进程，再使用新输出目录和新 source manifest。

---

## 20. 最终交接判断

截至 2026-09-23，可以确认：

- canonical FR3/Panda MuJoCo 源码已整理并发布；
- 历史源码和非主线 branch 已在 Spark 归档；
- 项目 GIF 已按日期/算法/场景归档，且本机项目 GIF 已精确清理；
- VMC 6D teacher 和持续棍推验收场景已经出现可用成功行为；
- MLP/ESN action distillation 的统一接口已经存在；
- ESN128 已完成一轮基础场景 BC 和复杂办公室开发评估；
- 该 ESN128 版本能够在办公室中抓起物块，但三个布局均未完成最终放置；
- 这个失败结果已经被保留，不能隐藏或通过放宽判据美化；
- 论文级最终结论仍需要重建严格无泄漏 teacher bank、完成公平 baseline、多 seed、冻结 office blind test 和 sim-to-real 前验证。

最重要的后续目标不是“马上再训练一个更大的 ESN”，而是：

> 先把 VMC teacher 的接触后、持物、回位和放置动作覆盖补齐，并以 fixture-level split 重新训练匹配 MLP/ESN；然后在完全冻结的复杂办公室场景中，用任务成功率、分阶段轨迹误差、速度 P95/jerk、峰值外力、峰值关节力矩、恢复时间、穿透和非预期接触进行统一比较。

任何新 agent 如果无法确认某个脚本属于哪个版本，应优先查 `CODE_ORGANIZATION.md`、`SOURCE_GUIDE.md`、日期后缀、source manifest 和输出目录中的 `command.json/manifest.json`，不要根据文件名或 GIF 视觉效果自行推断。
