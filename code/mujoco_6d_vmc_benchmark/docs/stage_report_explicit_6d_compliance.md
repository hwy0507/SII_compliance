# 末端受撞击后的柔顺回归控制：阶段性实验汇报

**日期：** 2026-08-13  
**项目：** Panda 机械臂末端六维虚拟弹簧柔顺控制（MuJoCo）  
**面向读者：** 不要求具备机器人控制、MuJoCo 或动力学建模背景  
**代码版本：** `60a4354 Record explicit 6D damping tradeoff results`  

> 一句话结论：我们已经在 MuJoCo 中搭建并验证了“机械臂下去抓物块时，末端被实体棍子撞偏，先柔顺让开、棍子离开后再回到原抓取轨迹”的实验。当前最可靠的阶段结果是显式三维虚拟小车模型；它在同一实体碰撞下，将峰值轨迹偏差降低约 29%，将回归时间缩短约 51%，且没有提高碰撞力峰值或关节力矩峰值。完整显式六维模型也已经跑通，但其旋转通道仍有高频抖动，暂作为下一阶段优化对象。

---

## 1. 我们到底在解决什么问题？

设想一台机械臂要从桌面上抓起一个小方块。它沿着既定轨迹向下移动时，外界可能有人或一个障碍物用棍子横向碰到机械臂末端。

如果机械臂过于刚硬，碰撞会带来很大的接触力和关节力矩；如果它太软，又可能偏离很远、不能及时回到抓取轨迹，最终抓不到物块。

本项目希望实现的行为是：

1. **正常阶段：** 机械臂沿原定轨迹下去抓物块；
2. **撞击阶段：** 实体棍子碰到末端，机械臂允许末端短暂偏离，而不是硬顶住棍子；
3. **回归阶段：** 棍子撤走后，末端平滑回到原本的参考轨迹；
4. **任务完成阶段：** 机械臂继续闭合夹爪、抓起方块，并将其保持在空中。

这可以理解为给机械臂末端连接了六个“看不见的弹簧”：

```text
三个平移弹簧：控制末端向 X / Y / Z 三个方向的偏移
三个旋转弹簧：控制末端绕 X / Y / Z 三个轴的姿态偏移
```

弹簧的作用不是强制机械臂完全不动，而是让它在受到碰撞时可以有限地“让开”，再在碰撞结束后获得恢复力，回到原参考轨迹附近。

---

## 2. 实验场景：怎样保证这不是“看起来像撞到了”？

本实验使用 Franka Emika Panda 模型和 MuJoCo 3.11 物理引擎。场景中包含：

- Panda 机械臂；
- 一张具有接触属性的桌子；
- 一个自由放置、没有焊接到夹爪上的黄色方块；
- 一个具有质量、通过物理 slide joint 驱动的绿色圆柱形棍子；
- 一条可到达的末端参考轨迹；
- 用于可视化参考点、实际末端位置和虚拟小车位置的标记。

棍子不是瞬间修改位置的“视觉特效”。它具有质量和碰撞几何体，通过 MuJoCo 的接触求解器与 Panda 的 `hand_collision` 几何体发生真实碰撞。

为了避免“棍子其实没有撞到末端，但误差看起来很小”的假结论，每条被接受的实验都必须同时满足以下有效性条件：

| 有效性条件 | 小白解释 |
|---|---|
| `rod_hand_contact_observed = true` | 系统实际检测到棍子与末端发生碰撞。 |
| `simulation_finite = true` | 仿真没有数值发散、NaN 或 Inf。 |
| `target_lifted_after_recovery = true` | 撞击后机械臂仍成功把方块抬离桌面。 |
| `target_held_at_end = true` | 仿真结束时方块仍在夹爪附近并保持在空中。 |
| `hard_limit_fraction = 0` | 没有任何关节一直顶在硬力矩限幅上。 |

本报告中所有“有效候选”都通过上述检查。

---

## 3. 怎样判断“回来了”？

我们把原抓取轨迹周围画出一个半径为 **5 mm** 的管状区域，称为“参考轨迹管”（reference tube）。

当末端位置与参考轨迹的欧氏距离：

```text
小于或等于 5 mm，且连续保持至少 80 ms
```

就认为机械臂已经重新回到参考轨迹。

这比只看 GIF 或只看某一帧截图更严格：它要求末端不仅一瞬间经过参考轨迹附近，还必须稳定地待在附近一段时间。

### 3.1 本报告中的“WBC reference”是什么意思？

图中的 `WBC reference` 目前是一个**可到达的移动参考轨迹接口代理（proxy）**，不是实时运行的 Whole-Body Controller（WBC）。

换句话说，当前结论是：

> 当未来 WBC 向 VMC 模块提供末端期望位姿和速度时，现有 VMC 接口、日志和评估方法可以直接复用。

当前结论**不是**：

- 不是真机实验结论；
- 不是已部署的实时 WBC+VMC 结论；
- 不是主动感知和规划障碍物绕行的结果。

当前系统做的是“受到碰撞后的柔顺偏离与回归”，并不主动改变参考路径来绕开障碍物。

---

## 4. 建模方法：从抽象弹簧到显式 MuJoCo 虚拟机构

### 4.1 最初版本：Python 内部虚拟小车

最初的模型在 Python 控制器内部维护一个六维虚拟小车状态。控制器根据“虚拟小车与真实末端之间的偏差”算出一个六维恢复力/力矩，再通过 Jacobian 转换为 Panda 关节力矩。

这个版本可用，但虚拟质量并不在 MuJoCo 的 `qpos/qvel` 状态中；因此它更像一个控制器内部的数学状态，而不是物理引擎中的真实虚拟机构。

### 4.2 阶段主模型：显式三维平移 virtual carriage

受 `cutting_simulation` 参考实现中“显式 virtual mass + 成对作用力”的思路启发，我们将三个平移通道放进 MuJoCo：

```text
移动参考轨迹
      │
      │ drive spring-damper
      ▼
一块 MuJoCo 3D virtual carriage
  ├─ X slide joint
  ├─ Y slide joint
  └─ Z slide joint
      │
      │ 非线性平移弹簧 + 阻尼器
      │ （对 virtual carriage 和 Panda hand 施加大小相等、方向相反的力）
      ▼
Panda 手部 / 末端
```

其中“大小相等、方向相反”的力是重要的物理约束：虚拟小车拉机械臂时，机械臂也会反向拉虚拟小车。这样虚拟小车的质量、位置和速度都参加 MuJoCo 动力学积分，而不是只靠外部脚本更新。

### 4.3 扩展模型：显式六维 virtual mechanism

随后我们在 3D 平移小车下面增加了一个带 ball joint 的旋转虚拟小车：

```text
显式平移小车（X/Y/Z slide joints）
      │
      └── 显式旋转小车（ball joint，3 个角自由度）
                │
                └── 三个旋转 spring-damper moment
                          │
                          ▼
                      Panda hand
```

因此，完整 6D 原型里：

| 通道 | 在 MuJoCo 中是否为显式状态？ | 主要作用 |
|---|---|---|
| X / Y / Z 平移 | 是，3 个 slide joint | 让末端可在三个方向上柔顺偏移与恢复。 |
| 绕 X / Y / Z 旋转 | 是，1 个 ball joint 的 3 个角自由度 | 让末端姿态也可通过虚拟转动惯量、弹簧和阻尼发生柔顺响应。 |

这个扩展并不意味着 6D 已经比 3D 更好；它的意义是把六个通道都接入了可观察、可调参、可做作用力/反作用力分析的 MuJoCo 动力学链路。

---

## 5. 评价指标：为什么不只看轨迹误差？

单看“轨迹偏差小”可能会误导：例如棍子没有撞到机械臂，误差当然也小。因此我们同时报告四类指标。

| 类别 | 指标 | 含义 |
|---|---|---|
| 轨迹 | peak nominal/reference error | 撞击期间，实际末端离参考轨迹最远有多远。 |
| 轨迹 | paired rod-induced offset | 将“有棍子”与“无棍子”对应时刻相减后，棍子真正额外造成的最大偏移。 |
| 轨迹 | position RMSE | 整段过程的平均跟踪误差；越小越好。 |
| 回归 | release-to-rejoin latency | 棍子离开后，需要多久重新进入并稳定留在 5 mm 参考轨迹管内。 |
| 安全 | peak rod–hand contact force | 棍子和末端的实体接触峰值；必须与基准实验可比较。 |
| 安全 | peak applied motor torque | 七个关节中最大的实际施加力矩；越低越安全。 |
| 平稳性 | speed / acceleration / jerk | 检查是否有突然前冲、急加速或高频抖动。 |
| 任务完成 | lift / hold | 偏离和回归之后，是否真的完成抓取任务。 |

---

## 6. 实验设置

### 6.1 共同设置

| 项目 | 设置 |
|---|---|
| 机器人 | Franka Emika Panda，7 个机械臂关节。 |
| 物理引擎 | MuJoCo 3.11。 |
| 控制周期 | 4 ms。 |
| 棍子类型 | 有质量的圆柱体，通过 position actuator 驱动的 physical slide joint。 |
| 受撞对象 | Panda `hand_collision` 几何体，而不是手臂其他链节。 |
| 目标物 | 0.08 kg 自由方块，未焊接到夹爪。 |
| 基础碰撞设置 | rod stroke = 0.16 m，rod height = 0.54 m。 |
| 回归判据 | 5 mm 位置管，连续保持 80 ms。 |
| 对照方法 | 每个候选都有 matched no-rod run，排除正常抓取运动自身的误差。 |

### 6.2 为什么 rod height 也要记录？

仅改变棍子行程并不能保证它真的碰到手。我们曾发现 `rod stroke = 0.12 m` 的一个场景里，接触力是 `0 N`，说明棍子根本没有碰到机械臂。这种样本不能用来证明控制器更好，只能记为“夹具覆盖失败”。

因此脚本已增加 `--rod-height`，并把高度写入 summary，后续鲁棒性实验必须先证明每种设置确实发生了实体接触。

---

## 7. 关键结果一：显式 3D virtual carriage 是当前阶段主结果

### 7.1 参数

```text
explicit translational carriage mass = 1.0 kg
shared stiffness multiplier kappa = 35
damping ratio zeta = 0.8
translation drive scale = 8.0
recovery ramp = 0.08 s
rod stroke = 0.16 m
rod height = 0.54 m
```

### 7.2 与旧版 Python virtual carriage 的严格对比

| 指标 | 旧 Python virtual carriage | 显式 3D carriage | 变化 |
|---|---:|---:|---:|
| 峰值相对参考轨迹偏差 | 10.84 mm | **7.71 mm** | **降低 28.8%** |
| 峰值棍子诱导偏移 | 5.92 mm | **4.29 mm** | **降低 27.5%** |
| 位置 RMSE | 6.62 mm | **4.05 mm** | **降低 38.8%** |
| 棍子释放后回归时间 | 0.760 s | **0.372 s** | **缩短 51.1%** |
| 实体接触力峰值 | 18.62 N | 18.51 N | 基本一致 |
| 最大施加关节力矩 | 30.40 N·m | 30.08 N·m | 略低 |
| 抓起并保持方块 | true / true | true / true | 均通过 |

### 7.3 怎样理解这张结果表？

最重要的不是某一个数字特别小，而是多个指标同时没有恶化：

- 末端被撞开得更少；
- 棍子离开后回得更快；
- 棍子真实接触力没有被“偷偷降低”；
- 机械臂关节力矩没有提高；
- 最后仍完成抓取。

因此，显式 3D virtual carriage 不是“只让图更好看”，而是在同一任务和同一实体碰撞下得到的有效 Pareto 改进。

### 7.4 结果图如何阅读？

服务器已生成以下图：

```text
outputs/explicit_k35_damping_scan/z0.8/figures/wbc_rejoin_trajectory_results.png
outputs/explicit_k35_damping_scan/z0.8/figures/wbc_rejoin_dynamics_results.png
```

第一张图左侧把三条轨迹画在一起：

- 黑色：参考轨迹接口（WBC-reference proxy）；
- 红色：有实体棍子撞击时的实际末端；
- 蓝色虚线：没有棍子时的匹配对照轨迹。

右侧显示实际末端到参考轨迹的距离。粉色阴影是接触窗口，绿线是棍子离开，蓝色虚线是重新进入 5 mm 管的位置。该候选的 release-to-rejoin latency 为 **0.372 s**。

第二张图同时显示：末端速度、rod–hand 实体接触力、三条平移弹簧力、三条旋转力矩和七个关节力矩。它用于检查“回归更快”是否是通过突然前冲或过大力矩换来的；当前 3D 候选没有出现这种代价。

---

## 8. 关键结果二：完整显式 6D 模型已经跑通

### 8.1 最有潜力的 6D 参数点

```text
explicit translation carriage mass = 1.0 kg
rotational carriage inertia scale = 0.5
kappa = 35
global damping ratio = 0.8
rotational damping ratio = 0.8
drive scale = 8.0
rod stroke = 0.16 m
rod height = 0.54 m
```

它通过了全部任务有效性检查：

```text
rod-hand contact observed = true
simulation finite = true
target lifted = true
target held at end = true
hard torque limit fraction = 0
```

### 8.2 6D 与 3D 的比较

| 指标 | 稳定显式 3D | 显式 6D（inertia scale = 0.5） | 解读 |
|---|---:|---:|---|
| peak nominal error | **7.71 mm** | 7.85 mm | 基本相近。 |
| peak paired rod offset | **4.29 mm** | 4.64 mm | 3D 略好。 |
| nominal position RMSE | 4.05 mm | **3.10 mm** | 6D 整体平均误差更低。 |
| release-to-rejoin latency | 0.372 s | **0.340 s** | 6D 回归更快。 |
| peak rod contact force | 18.51 N | **18.63 N** | 非常接近，说明不是轻碰撞造成的虚假优势。 |
| peak motor torque | 30.08 N·m | 30.17 N·m | 基本相当。 |
| peak explicit rotation spring moment | — | 4.50 N·m | 旋转弹簧通道确实参与。 |

从轨迹和回归指标看，6D 具有进一步提升潜力；但我们没有直接把它宣布为最终方案，原因见下一节。

---

## 9. 6D 的当前问题：旋转通道高频抖动

完整 6D 模型中，旋转 ball joint 及其恢复力矩在接触后出现高频 alternating moment，简称 chatter。它可理解为“虚拟旋转弹簧在很快地来回修正”，这会让力矩曲线不够平滑。

为了处理这个问题，我们新增了独立参数：

```bash
--rotational-damping-ratio
```

它允许旋转三通道使用和三平移通道不同的阻尼，而不是所有六根弹簧永远共用一个 `zeta`。

### 9.1 旋转阻尼扫描结果

| rotation damping ratio | peak error | peak rod force | peak torque | peak jerk | 结论 |
|---:|---:|---:|---:|---:|---|
| 0.8 | 7.85 mm | 18.63 N | 30.17 N·m | 1072 m/s³ | 轨迹指标很强，但 rotational moment chatter 明显。 |
| 1.2 | 8.55 mm | 19.68 N | 30.21 N·m | 992 m/s³ | 更平滑、真实接触仍存在，但不支配 3D 主候选。 |
| 2.0 | **6.48 mm** | 17.19 N | 30.12 N·m | **884 m/s³** | jerk 降低，但接触峰值偏低，碰撞等价性不足。 |

所有阻尼点都完成抓取、没有数值发散，也没有撞上力矩硬限制。但评估不允许只看最小误差：

- `zeta_rot = 2.0` 的误差看起来很小；
- 但是接触峰值从约 18.6 N 降到 17.19 N；
- 这说明它面对的有效碰撞条件已经改变，不能简单称为控制效果更好。

因此目前最严谨的判断是：

> 显式 6D 已经验证可运行、有改善平均误差和回归速度的潜力，但旋转阻尼还未找到一个同时在轨迹、碰撞等价性和平滑性上全面优于 3D 主候选的参数点。

---

## 10. 哪些结果不能被当作成功？

科研实验中，明确记录“不应使用的结果”与报告最优结果同样重要。

| 情况 | 观察到的现象 | 为什么不能算成功 |
|---|---|---|
| rod stroke = 0.12 m | 接触力为 0 N，没有 rod-hand contact。 | 棍子没碰到机械臂，误差小没有意义。 |
| 3D 高 κ = 50 | 回归表面更快，但接触力降至约 11.6 N，jerk 升至约 3018 m/s³。 | 碰撞等价性和运动平稳性都被破坏。 |
| 6D inertia scale = 0.25 | 误差较低，但接触峰值约 16.54 N。 | 与 18.62 N 基准碰撞不够可比。 |
| 6D rotation damping = 2.0 | jerk 较低，误差也低，但接触峰值 17.19 N。 | 不能确认优势来自控制，而不是碰撞变弱。 |

本项目的原则是：**不把“碰撞更轻”误当成“控制更好”。**

---

## 11. 当前阶段可以怎样向导师汇报？

可以用下面这段话概括：

> 我们在 MuJoCo 中完成了 Panda 末端受实体棍子碰撞后的柔顺偏离、回归并继续抓取的基准任务。参考 cutting 文章的显式虚拟机构思想，我们将原本仅存在于 Python 控制器内部的虚拟小车升级为 MuJoCo 显式质量—弹簧—阻尼系统。当前稳定的显式 3D 虚拟小车在相同 rod–hand 接触峰值和不增加关节力矩峰值的前提下，将峰值轨迹偏差从 10.84 mm 降至 7.71 mm，并把棍子释放后的回归时间从 0.760 s 缩短至 0.372 s，抓取任务仍成功。显式 6D 平移加旋转模型已跑通，能进一步达到 3.10 mm RMSE 和 0.340 s 回归，但旋转 ball-joint 通道目前有高频 moment chatter，下一阶段将围绕旋转阻尼、drive stiffness 和接触求解器参数进行稳定化。

---

## 12. 下一阶段计划

### 12.1 优先级 1：让显式 6D 更平滑

在保持碰撞等价性的前提下，扫描：

```text
rotational drive stiffness
× ball-joint passive damping
× rotational damping ratio
× contact solver time constant
```

目标约束：

```text
peak rod force 约为 18.5 N
peak motor torque 不高于约 30.4 N·m
rejoin latency 不高于 0.4 s
target lift / hold 继续为 true
```

目标优化：

```text
降低 rotational moment chatter
降低 jerk peak
降低 post-release oscillation
```

### 12.2 优先级 2：形成有效的鲁棒性矩阵

在每个样本都确认发生实体碰撞后，改变：

- rod height（不同末端接触位置）；
- rod stroke（不同有效冲击强度）；
- rod direction（不同横向碰撞方向）；
- 后续的六通道独立刚度与阻尼。

每个组合仍必须做 paired no-rod 对照和任务有效性 gate 检查。

### 12.3 优先级 3：接入真实 WBC 输出

当前 `WBC reference` 是可到达的参考轨迹接口代理。未来只要真实 WBC 提供末端期望 pose/twist，即可替换 reference provider，而现有的：

- 六维 VMC torque 接口；
- 轨迹误差、回归时间、接触力、力矩和速度日志；
- paired experiment 评估；
- 2D 轨迹和 dynamics 图；

都可以复用。

---

## 13. 可复现运行入口

主实验脚本：

```text
scripts/run_rod_perturbation_benchmark.py
```

结果图脚本：

```text
scripts/plot_trajectory_results.py
```

稳定显式 3D candidate 的核心命令：

```bash
export MUJOCO_GL=egl MPLBACKEND=Agg
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie /path/to/mujoco_menagerie \
  --output-dir outputs/explicit_3d_candidate \
  --kappas 35 --damping-ratio 0.8 \
  --carriage-drive-scale 8 --recovery-carriage-drive-scale 8 \
  --recovery-kappa 35 --recovery-ramp 0.08 \
  --rod-stroke 0.16 --rod-height 0.54 \
  --explicit-translational-carriage --carriage-mass-kg 1.0
```

完整显式 6D prototype 的核心命令：

```bash
export MUJOCO_GL=egl MPLBACKEND=Agg
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie /path/to/mujoco_menagerie \
  --output-dir outputs/explicit_6d_candidate \
  --kappas 35 --damping-ratio 0.8 --rotational-damping-ratio 0.8 \
  --carriage-drive-scale 8 --recovery-carriage-drive-scale 8 \
  --recovery-kappa 35 --recovery-ramp 0.08 \
  --rod-stroke 0.16 --rod-height 0.54 \
  --explicit-translational-carriage --explicit-rotational-carriage \
  --carriage-mass-kg 1.0 --rotational-carriage-inertia-scale 0.5
```

再运行一次同参数的 `--disable-rod` 对照实验，最后用：

```bash
python scripts/plot_trajectory_results.py \
  --rod-trace <rod_trace.npz> \
  --no-rod-trace <no_rod_trace.npz> \
  --output-dir <figures_dir>
```

生成 2D 实际/参考轨迹图、回归误差图、速度/力/力矩图和评价 JSON。

---

## 14. 相关代码与资料

- 主说明：[README.md](../README.md)
- 参考作者 `cutting_simulation` 的方法对比与迁移建议：[cutting_simulation_comparison.md](cutting_simulation_comparison.md)
- rod 扰动主脚本：[`scripts/run_rod_perturbation_benchmark.py`](../scripts/run_rod_perturbation_benchmark.py)
- 绘图脚本：[`scripts/plot_trajectory_results.py`](../scripts/plot_trajectory_results.py)
- GitHub 仓库：<https://github.com/hwy0507/SII_compliance>
- 参考实现仓库：<https://github.com/sally-00/cutting_simulation>

---

## 15. 最终总结

当前的阶段性成果有三层：

1. **任务层：** 已在 MuJoCo 中完成了“抓取途中受到实体撞击、柔顺偏离、回归参考轨迹并继续抓取”的完整闭环任务；
2. **方法层：** 已将虚拟弹簧从 controller 内部抽象状态升级为显式 MuJoCo virtual carriage，完整 6D 的平移和旋转状态都已经跑通；
3. **性能层：** 稳定的显式 3D 方案已经在同一碰撞条件下证明了更小偏差、更快回归、近似相同接触力和不升高的关节力矩。

最可靠的当前结论是：

> 显式三维 virtual carriage 已经是一个可复现、任务有效、具有多指标改善的阶段主结果；显式六维 virtual mechanism 已完成建模与运行验证，并展现出更低平均误差和更快回归的潜力，但旋转高频振荡仍是下一阶段必须解决的问题。
