# `cutting_simulation` 对比与可迁移建模建议

日期：2026-08-13
作者仓库：<https://github.com/sally-00/cutting_simulation>
作者提交：`48e1607d1e88a6d87ece3906e225da7bb904b7be`
服务器副本：`/home/arm1/vmc_mujoco_runtime/external/cutting_simulation`
本地审阅副本：`/tmp/cutting_simulation`

## 1. 已复现的服务器运行

原始仓库没有改动。使用服务器已有 MuJoCo 3.11.0、Python venv 和 EGL：

```bash
cd /home/arm1/vmc_mujoco_runtime/external/cutting_simulation
export MUJOCO_GL=egl MPLBACKEND=Agg
/home/arm1/vmc_mujoco_runtime/.venv/bin/python \
  mujoco_bridge/franka_cutting_vm_sim_mechanism.py \
  --sim-time 10.0 --results-root results_server_full --record cutting.mp4 \
  --rebuild-xml
```

运行成功，输出目录为：

```text
/home/arm1/vmc_mujoco_runtime/external/cutting_simulation/results_server_full/20260813_170639_mechanism
```

服务器 trace 的可核查结果：

| 项目 | 结果 |
|---|---:|
| 仿真时长 | 10.0 s |
| MuJoCo timestep | 0.001 s |
| 机器人关节数 | 7 |
| 完整状态 `nq/nv` | 18 / 18 |
| 控制输入 `nu` | 7 |
| 切换时刻 | 0.284, 1.518, 1.920, 3.951, 4.357, 6.476, 6.884, 8.969, 9.375 s |
| 完成 slice 数 | 5 |
| 峰值刀-板接触力 | 905.48 N |
| 峰值 tip spring force | 9.19 N |
| 峰值 back spring force | 28.29 N |
| 峰值 back-target spring force | 319.40 N |

这个运行结果是切割任务的原始复现，不应直接和我们的“棍子撞击末端”任务的
18.62 N 接触力或 0.76 s 回归时间作优劣比较；两者外部任务、几何、速度、接触
对象和控制参考都不同。

## 2. 两个项目的核心差异

| 维度 | `cutting_simulation` | 我们的 `mujoco_6d_vmc_benchmark` |
|---|---|---|
| 机器人 | Franka Research 3 (FR3) 自带 MJCF 和 mesh | 官方 Franka Emika Panda menagerie 模型 |
| 任务 | 刀具沿切板做下压/抬升/切片，约 15 次切换逻辑 | 末端抓取下探，被实体棍子横向撞击后回归 |
| 虚拟机构 | MuJoCo 中显式 virtual anchor、tip slider、back slider、4 个 orientation point slider、back-target mass | 控制器内部一个 6D virtual carriage，位置/姿态/速度由 Python 状态积分 |
| 弹簧拓扑 | tip 1 个平移弹簧；back 1 个平移弹簧；back-target 1 个平移弹簧；4 个姿态采样点构造旋转恢复 | 六个同构 6D 非线性 spring-damper channel；统一 κ 初始扫描 |
| 虚拟质量 | tip 0.1 kg；back-target mass 默认 5 kg；orientation mass 0.1 kg；均有真实 MuJoCo joints | virtual mass 只存在于 controller state，不在 MuJoCo `qpos/qvel` 中 |
| 力的施加 | `mj_applyFT` 直接在多个 site 对刀具和虚拟质量施加等反向力 | 6D wrench 经过 `J^T w` 转成 Panda 关节力矩 |
| 旋转建模 | 4 个相对末端点的笛卡尔弹簧，间接约束刀具姿态；没有显式 SO(3) rotation state | 直接使用 SO(3) log orientation error，三个 rotational virtual channels |
| 参考切换 | 根据 knife-back 高度/刀尖高度切换 back target，形成切割阶段状态机 | `PickLiftCarryReference` 生成 moving-attractor trajectory proxy |
| 关节控制 | 外部可选 EE position PD、joint-4 anchor PD、弱 nullspace posture；再加 VM force 和 gravity compensation | torque-level arm control、bias compensation、VMC wrench、torque feasibility scaling、slew rate limiter |
| 接触 | knife collision mesh 与 board/table 的 MuJoCo contact | 实体有质量 rod 与 hand collision 的 MuJoCo contact |
| 输出 | tip/back/back-target spring force、knife-board contact force、切换时间、完整 qpos/qvel、视频 | WBC proxy/actual/no-rod trajectory、paired offset、EE speed、rod force、VMC wrench、carriage displacement、motor torque、rejoin latency |

## 3. 为什么视觉上会差很多

这不是简单的参数差，而是“虚拟机构放在哪里”和“参考是什么”的差别：

1. 作者的 knife 是挂在 `fr3_link7` 下的**真实带质量刚体**，虚拟机构在刀具前端/后端两处形成真实动力学链。刀具被板接触时，虚拟质量和刀体都参与 MuJoCo 积分，因此会有明显的多阶段拖尾、切换和回弹。
2. 他们的 reference 不是一个移动 WBC 轨迹。`vm_anchor`、`vm_tip_target` 和 `vm_back_target` 是由切片状态机更新的目标，切割过程中参考点会离散切换。
3. 我们当前的 carriage 在 Python controller 中积分，不进入 MuJoCo 的质量矩阵。它产生的是一个经 `J^T` 映射后的末端恢复力矩，物理臂会动，但“弹簧质量—弹簧—末端”的中间状态不会像作者模型那样自然形成复杂的相位响应。
4. 作者的响应对象是刀具 tip/back 和四个姿态点；我们把末端 6D 误差直接压缩成 3 平移 + 3 旋转通道。对于“棍子撞击末端”的任务，直接 6D 是合理的，但想得到类似作者的丰富轨迹，必须把 virtual carriage 的质量、阻尼和接触耦合也物理化。

## 4. 最值得学习的实现

### 4.1 将 virtual carriage 放进 MuJoCo 动力学

作者通过显式 `slide` joints 和 inertial bodies 建模虚拟状态。我们下一版可以保留 6D end-effector 语义，但在 Panda 的 hand 下增加：

- 3 个平移 virtual-carriage slide joints；
- 3 个旋转 virtual-carriage joints（可先用小角度 axis-angle 近似，后续再用 quaternion/free joint）；
- 每个 virtual state 的质量、阻尼和非线性弹簧；
- virtual carriage 与 EE 之间的反向力/力矩守恒耦合。

这样 `qpos/qvel`、质量矩阵和接触冲量会同时包含 arm 与 virtual mechanism，轨迹回归形状会更接近作者的仿真。

### 4.2 多点采样比单点笛卡尔弹簧更适合姿态恢复

作者用 knife tip、knife back 和四个 orientation points 施加空间力。对我们的末端可以建立：

- 一个末端中心平移 spring；
- 沿末端局部 x/y/z 的 3--4 个虚拟采样点；
- 通过点力合成恢复力和恢复力矩。

这仍然可以解释为六维弹簧，但几何上会产生可观测的姿态—平移耦合，而不是把 rotational response 只留在一个抽象 `so3_log` 向量中。

### 4.3 引入“参考切换/相位状态机”

作者的 `_update_back_target_reference()` 用可见的几何条件切换回程目标。我们的 benchmark 可以增加显式 phase：`approach → contact-yield → release-recovery → grasp`，并把 phase、目标 pose、实际 pose、rejoin time 一起写入 trace。这样图里的“回归 WBC”会和任务阶段一一对应。

### 4.4 保留力饱和、重力补偿和可解释 trace

作者的 `tanh` spring saturation、per-channel max force、`robot_only/all/off` gravity compensation、完整 qpos/qvel 与每根弹簧力 trace 都值得保留。尤其是把 `tip_force`、`back_force`、`back_target_force` 分开记录的做法，适合我们未来六个 virtual spring 分开调参和构建评价矩阵。

## 5. 不应直接照搬的部分

- 他们的“刀具切板”不是我们的“棍子撞末端”，高达 905 N 的板接触力不能作为我们安全指标目标。
- 他们的 FR3 模型不能替代我们最终需要的 Panda/真实机械臂模型；可借鉴的是 virtual-mechanism 拓扑，不是 mesh 或初始姿态。
- 他们的四个 orientation point springs 是针对刚性刀具的几何约束；我们需要先验证六维末端平移/旋转通道与 WBC 接口，再决定是否采用四点离散化。
- 他们的切片状态机和 `back_target_rel` 切换逻辑适合切割，不应直接嵌入抓取任务。

## 6. 建议的下一步实现顺序

1. 先不改任务：在我们现有实体 rod-hand fixture 上，新增 **MuJoCo 显式 3 平移 virtual-carriage mass**，和当前 Python carriage 做 paired A/B。
2. 验证显式质量是否改善“撞击峰—释放—回归”的形状，再加入 3 个旋转状态。
3. 将当前统一 κ 保留为第一阶段强假设；分别记录六个通道的 displacement、force、effective damping 和 motor torque。
4. 加入 phase/state trace 和和作者类似的多弹簧分通道图；回归时间定义仍使用 5 mm / 80 ms 判据。
5. 最后才做六个通道独立调参和 rod mass/velocity/stroke/direction 鲁棒矩阵。

## 7. 当前结论

作者的代码不是“同一个任务的更好参数”，而是一个更接近**显式虚拟机构动力学**的实现。我们当前结果看起来差距大，主要原因是我们还没有把 virtual carriage 的中间质量和多点几何耦合放进 MuJoCo。最值得移植的不是切割流程，而是：

> 显式 virtual masses + 多点空间弹簧 + 反向力守恒 + phase/state machine + 分通道 trace。

这组改动会直接提升我们 benchmark 对“偏离极限环/参考轨迹后回归”的物理可解释性，但在接入前仍需用 paired experiments 证明它确实降低回归时间和峰值偏差。

## 8. 已实现的最小显式-carriage A/B 原型

根据上面的迁移建议，当前 benchmark 已实现一个最小但真实的 A/B 路径。它不是
完整 6D physical mechanism：仅把**三条平移通道**从 Python 内部 carriage 升级为
MuJoCo 显式状态，三条 SO(3) rotational channel 暂时保留在原有控制器中。

显式版本的结构为：

```text
moving WBC-reference proxy
       │  drive spring-damper
       ▼
one MuJoCo body: 3 orthogonal slide joints + one 0.35 kg mass
       │  nonlinear spring-damper, equal and opposite forces
       ▼
Panda hand  +  existing 3 rotational VMC channels
```

运行开关：

```bash
python scripts/run_rod_perturbation_benchmark.py ... \
  --explicit-translational-carriage --carriage-mass-kg 0.35
```

注意这里是一块带质量的 **3D carriage body**，而不是三个互不相干的单轴质量。
每步通过 `mj_applyFT` 对 carriage 和 Panda hand 施加作用力/反作用力；因而该
carriage 的三维位置和速度进入 MuJoCo `qpos/qvel` 与质量矩阵。其额外 trace 为
`explicit_carriage_position`、`explicit_carriage_velocity`、
`explicit_carriage_force`。

### 8.1 严格 paired 初始对比（尚未调参）

两种模型均使用同一 rod fixture、同一 `kappa=6`、`zeta=1.8`、translation
drive scale `4.0`、recovery ramp `0.08 s`、rod stroke `0.16 m`、grasp time
`2.30 s`，并且各自有 matched no-rod baseline。回归判据均为 5 mm 位置管连续
80 ms。

| 指标 | 原 Python 6D carriage | 显式 3D translation carriage (0.35 kg) | 解释 |
|---|---:|---:|---|
| 实际 rod-hand 接触 | 1.260--1.344 s | 1.260--1.344 s | fixture 一致 |
| 接触后回归时间 | 0.760 s | **0.732 s** | 显式版快 28 ms |
| 峰值 nominal/reference error | **10.84 mm** | 11.56 mm | 显式版增大 0.72 mm |
| paired rod-induced offset peak | **5.92 mm** | 6.46 mm | 显式版增大 0.54 mm |
| 释放时误差 | 8.73 mm | 9.05 mm | 显式版略大 |
| 闭合前误差 | 3.87 mm | **3.60 mm** | 显式版略小 |
| peak physical contact force | 18.62 N | **18.10 N** | 显式版略低 |
| peak translation spring force | 5.19 N | 3.63 N | 显式质量承担一部分动态响应 |
| peak applied motor torque | 30.40 N·m | **30.38 N·m** | 基本相同 |
| lift / hold | true / true | true / true | task gate 均通过 |

服务器输出：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/explicit_k600/
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/explicit_k600_no_rod/
```

### 8.2 诚实结论

这个 0.35 kg 初始点证明“显式虚拟质量 + 作用力/反作用力”已经可以在同一任务上
稳定运行并改变回归形状；但它没有支配性地优于旧版。它稍微缩短回归时间并降低
接触力，却增大峰值偏差。因此不能据此声称作者式显式机构天然更好，也不能把它
作为最终参数。

下一步应该对 `carriage_mass_kg`、translation stiffness、drive stiffness 和
damping 做小型 Pareto 扫描，同时要求 task lift/hold gate、无 hard torque limit，
再根据 peak error / rejoin time / peak contact force / peak torque 选择候选。之后
才加入三个显式 rotational state 或多点姿态弹簧。

## 9. 当前 Pareto 候选与有效性筛选（2026-08-13）

在服务器 MuJoCo 3.11 环境中，使用同一 Panda、同一实体 rod、同一抓取阶段和同一
无 rod paired reference 完成了显式平移 carriage 的扫描。候选参数为：

```text
mass = 1.0 kg, translation drive scale = 8.0,
kappa = 35, damping ratio zeta = 0.8,
recovery ramp = 0.08 s, rod stroke = 0.16 m
```

回归判据仍为位置误差不超过 5 mm 且连续保持 80 ms；同时要求仿真有限、目标被
抬起并在末端保持、实体 rod-hand 接触存在，且不触碰硬力矩限幅。

相对于此前的 Python-controller baseline（`kappa=6, zeta=1.8, mass=0.35 kg`
的历史候选），该点的结果为：

| 指标 | Python baseline | explicit candidate | 变化 |
|---|---:|---:|---:|
| peak nominal/reference error | 10.84 mm | 7.71 mm | -28.8% |
| peak paired rod-induced offset | 5.92 mm | 4.29 mm | -27.5% |
| position RMSE | 6.62 mm | 4.05 mm | -38.8% |
| release-to-rejoin latency | 0.760 s | 0.372 s | -51.1% |
| peak physical rod force | 18.62 N | 18.51 N | comparable |
| peak applied motor torque | 30.40 N·m | 30.08 N·m | -1.1% |
| recovery speed p95 | not retained in old baseline | 0.0114 m/s | report candidate |
| task lift / hold | true / true | true / true | pass |

这是一组同任务、同碰撞夹具、同回归定义下的多指标改进，当前可以称为“有效
Pareto 候选”，但还不能称为真机结论或 live WBC 结果。这里的 reference 仍是
reachable moving trajectory interface proxy，而不是实际 whole-body controller。

阻尼细扫显示：`zeta=0.8--1.2` 的结果稳定且接触力约 18.51 N；`zeta>=1.8` 会
引入更高峰值力矩和 jerk（例如 `zeta=1.8` 为 34.31 N·m / 2913 m/s³），因此被
排除。高 `kappa=50` 虽然表面上回归更快，但接触力降至约 11.6 N、jerk 升至约
3018 m/s³，也被判定为碰撞等价性破坏而排除。

行程鲁棒性检查还发现，`rod stroke=0.12 m` 在当前几何下没有接触（0 N、无
`rod_hand_contact_observed`），不能被当作一次成功扰动实验；该结果被记录为
fixture coverage failure，而不是控制器优胜结果。后续有效鲁棒性矩阵应先用 rod
位置/方向标定保证每一档确实发生实体接触，再比较恢复指标。

## 10. 显式 6D ball-joint 原型 smoke test（2026-08-13）

在 3D translational carriage 基础上新增可选的 MuJoCo ball-joint rotational
carriage。它是平移 carriage 的子 body，拥有三个角自由度和显式惯量；hand 与
rotational carriage 之间施加成对 spring-damper moment，rotational carriage 与
moving nominal reference 之间施加 drive moment。新增 trace 为
`explicit_carriage_rotation`、`explicit_carriage_angular_velocity` 和
`explicit_carriage_moment`。

使用 `kappa=35, zeta=0.8, translation drive=8, mass=1.0 kg, rotational inertia
scale=1.0, rod stroke=0.16 m, rod height=0.54 m` 的 smoke test 结果：

| 指标 | explicit 6D smoke |
|---|---:|
| rod-hand contact | true |
| simulation finite | true |
| target lift / hold | true / true |
| peak nominal error | 9.22 mm |
| peak paired rod offset | 5.13 mm |
| release-to-rejoin latency | 0.408 s |
| peak rod contact force | 20.17 N |
| peak explicit translation spring force | 9.05 N |
| peak explicit rotation spring moment | 3.03 N·m |
| peak applied motor torque | 30.29 N·m |

该 smoke test 证明六个通道已进入可运行的显式动力学路径，但它还不是当前 Pareto
优胜点：相对于 verified 3D candidate（7.71 mm / 0.372 s / 18.51 N），6D smoke
的偏差和接触力都更高。下一步会对 rotational inertia、rotational damping 和
rotational drive 做 paired sweep；只有在接触等价、抓取成功和 torque/jerk 不恶化
时，才会把它纳入最终候选。

### 10.1 中间惯量点的有效 6D 候选

进一步将 rotational inertia scale 调为 `0.5` 后，paired no-rod 对照显示该点
满足所有有效性 gate，并且接触强度恢复到与历史 baseline 相同量级：

| 指标 | verified 3D candidate | explicit 6D, inertia scale 0.5 |
|---|---:|---:|
| peak nominal/reference error | 7.71 mm | 7.85 mm |
| peak paired rod offset | 4.29 mm | **4.64 mm** |
| nominal position RMSE | 4.05 mm | **3.10 mm** |
| release-to-rejoin latency | 0.372 s | **0.340 s** |
| peak physical rod force | 18.51 N | **18.63 N** |
| peak explicit rotational spring moment | — | 4.50 N·m |
| peak applied motor torque | 30.08 N·m | 30.17 N·m |
| rod contact / finite / lift / hold | pass | pass |

该点是当前最有希望的显式 6D Pareto 候选：回归速度更快，RMSE 更低，碰撞峰值
和力矩没有实质恶化。它仍然是 MuJoCo 仿真结果，WBC reference 仍是 reachable
moving-trajectory proxy；在进入论文结论前，还需要做至少一个额外撞击高度或方向
的 paired validation。

### 10.2 独立旋转阻尼验证

为处理 `inertia scale=0.5` 点在旋转 moment 图中的高频 chatter，新增
`--rotational-damping-ratio` 并复现了三个阻尼点。所有三个点均为有限仿真、检测到
rod-hand 接触、目标 lift/hold 成功且没有硬力矩限幅；但碰撞等价性和轨迹指标的
权衡如下：

| rotational ζ | peak error | peak rod force | peak torque | peak jerk | 结论 |
|---:|---:|---:|---:|---:|---|
| 0.8 | 7.85 mm | 18.63 N | 30.17 N·m | 1072 m/s³ | 轨迹最强，但 chatter 明显 |
| 1.2 | 8.55 mm | 19.68 N | 30.21 N·m | 992 m/s³ | 接触等价、略平滑，但不支配 3D 主候选 |
| 2.0 | 6.48 mm | 17.19 N | 30.12 N·m | 884 m/s³ | 接触峰值偏低，碰撞等价性不足 |

因此当前阶段不把任意一个显式 6D 阻尼点宣称为全面最优：

- **阶段主结果**：显式 3D candidate（`7.71 mm / 0.372 s / 18.51 N`），动态行为最稳；
- **6D 研究结果**：显式 6D 已经跑通并显示 `ζ_rot=0.8` 可达到 `3.10 mm` nominal
  RMSE、`0.340 s` 回归时间和 `18.63 N` 接触峰值，但旋转 chatter 仍需处理；
- **下一步**：将旋转 drive stiffness、ball-joint damping 与接触求解器时间尺度
  作为独立变量，优先降低高频 moment 交替，同时保持 rod impulse 在基准范围内。
