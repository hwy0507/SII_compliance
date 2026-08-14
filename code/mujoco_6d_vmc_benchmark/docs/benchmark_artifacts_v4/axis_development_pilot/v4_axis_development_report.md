# V4 Axis-Coverage 物理几何开发 Pilot

## 结论

V4 已从 V2/V3 的镜像横向 `±y` 扩展到**真实构造的世界坐标轴向 rod geometry**。在 10 个未参与单点探测的 development-pilot 候选中，**9 个**通过了实体碰撞、稳定回归、抬起、保持及无硬力矩限幅的完整门槛，覆盖世界 `x`、`y`、`z` 三条轴：有效候选为 `x=3`、`y=4`、`z=2`。

这是多轴物理交互能力的开发证据，不是最终 V4 test benchmark：几何和行程由先前的物理探测确定，且 `positive_z` 尚未获得稳定 rejoin。因此它不能用于声称六个方向均已泛化，也不能用来进行最终 controller 排名。

## 1. 物理建模修改

之前的 rod 只具有世界 `y` slide 和世界 `x` 长轴。现在 `run_rod_perturbation_benchmark.py` 根据 `rod_approach_side` 在 MuJoCo XML 中构造不同的 support 位置、slide axis 和 cylinder quaternion：

| 接近方向 | Slide axis（世界） | Cylinder long axis（世界） | 作用 |
|---|---|---|---|
| `negative_x` | `+x` | `y` | 从负 x 侧前后向接近 |
| `positive_x` | `−x` | `y` | 从正 x 侧前后向接近 |
| `negative_y` | `+y` | `x` | 原有横向镜像构型，保持不变 |
| `positive_y` | `−y` | `x` | 原有横向镜像构型，保持不变 |
| `negative_z` | `+z` | `y` | 从下方上推到手部侧面 |
| `positive_z` | `−z` | `y` | 从上方下压到手部侧面 |

每个 direction 的 slide axis 与 rod long axis 均为单位向量且正交；六种模型均已通过 MuJoCo XML 构建测试。每个 episode summary 现记录 `support_position_m`、`slide_axis_world`、`rod_long_axis_world` 与 cylinder quaternion，因而几何不会被隐藏在脚本默认值中。

为了避免 vertical / fore-aft support 在匹配 no-rod reference 中静止占据工作空间，新增了显式的 `remove_rod_when_disabled` 开关。它只在 V4 no-rod reference 关闭 rod 的碰撞几何；默认关闭，因此已冻结 V2/V3 的历史行为和指标不被修改。

## 2. Protocol

- Selector：固定 six-dimensional tapered VMC，`κ=[27.58, 52.55, 48.70, 35.86, 40.72, 34.77]`；其职责仅为筛选物理 fixture，绝不作为 controller 排名方法。
- 每个候选：rod/no-rod 配对完整抓取 task。
- 新的 development-pilot 起撞时机：1.060 s、1.140 s；它们不同于用于几何探测的时机。
- 固定有效碰撞门槛：峰接触力至少 15 N、接触冲量至少 0.45 N·s。
- 完整门槛：有限仿真、rod–hand 接触、有效碰撞、稳定 5 mm / 80 ms rejoin、抬起、终点保持、无 hard torque limit、匹配 no-rod 成功。

## 3. 结果

| Fixture | 方向 / 轴 | 起撞时刻 | Peak contact force | Impulse | Rejoin latency | 有效 | 备注 |
|---|---|---:|---:|---:|---:|---|---|
| `v4pilot_negative_x_c0_t0` | `negative_x` / x | 1.060 s | 17.51 N | 1.956 N·s | 0.276 s | 是 | 完整成功 |
| `v4pilot_negative_x_c0_t1` | `negative_x` / x | 1.140 s | 18.06 N | 1.947 N·s | 0.252 s | 是 | 完整成功 |
| `v4pilot_positive_x_c1_t0` | `positive_x` / x | 1.060 s | 46.36 N | 2.431 N·s | 0.144 s | 是 | 完整成功 |
| `v4pilot_positive_x_c1_t1` | `positive_x` / x | 1.140 s | 14.88 N | 0.266 N·s | 0.000 s | 否 | 未达到力 / 冲量阈值，排除 |
| `v4pilot_negative_y_c2_t0` | `negative_y` / y | 1.060 s | 47.62 N | 2.618 N·s | 0.244 s | 是 | 完整成功 |
| `v4pilot_negative_y_c2_t1` | `negative_y` / y | 1.140 s | 38.08 N | 1.785 N·s | 0.204 s | 是 | 完整成功 |
| `v4pilot_positive_y_c3_t0` | `positive_y` / y | 1.060 s | 47.57 N | 2.700 N·s | 0.240 s | 是 | 完整成功 |
| `v4pilot_positive_y_c3_t1` | `positive_y` / y | 1.140 s | 38.19 N | 1.973 N·s | 0.204 s | 是 | 完整成功 |
| `v4pilot_negative_z_c4_t0` | `negative_z` / z | 1.060 s | 19.03 N | 4.397 N·s | 0.276 s | 是 | 完整成功 |
| `v4pilot_negative_z_c4_t1` | `negative_z` / z | 1.140 s | 27.51 N | 5.627 N·s | 0.252 s | 是 | 完整成功 |

有效覆盖统计：`x=3/4`、`y=4/4`、`z=2/2`，总计 `9/10`。这里的 z 覆盖只来自 `negative_z`；它说明“从下方”的垂直实体撞击链条已物理可行，但不能被夸大为上下对称成功。

## 4. 为什么没有把 `positive_z` 放入 Pilot

`positive_z` 已经历两类候选设计：

1. 与 x/y 相同的 interaction height：可产生实体接触，但杆会进入手的下降路径，长期接触导致没有 stable rejoin；
2. 提高 support 起点并延迟进入：仍有 22.9 N 接触和约 28.9 N·s 冲量，但 rejoin 仍为 `None`。

将 rod 移到 `y=0.08` 可避开目标物，但同时失去 rod–hand contact；将 z 向杆改成长轴 y、并以 `x=0.60` 接触手部侧面后，`negative_z` 获得了有效 fixture，而 `positive_z` 仍未通过稳定回归。因此当前应把它记录为**尚未解决的、可复现实验限制**，而不是删去失败记录或放宽门槛。

## 5. 与后续 benchmark 的边界

这个 pilot 的几何、行程是由 development probes 选择的。因此：

- 可以将它作为 VMC / safety layer 多轴可行性的工程开发证据；
- 不能将其视为独立 V4 holdout，更不能在其上重新选 controller 参数；
- 不能声称已完成 `±x/±y/±z` sign-complete 六方向泛化；
- 不能把 axis-aligned 结果泛化为连续、任意三维撞击方向或真实硬件结论。

下一步的严谨路线是：固定当前几何实现；为每个已可行侧面新采样不重合的时机 / 行程 / 高度作为 V4 holdout；保持 selected `slow_smoothing` safety 参数冻结；然后以 rigid / impedance / VMC-gated / VMC-energy ladder 做 common-valid 比较。`positive_z` 则作为独立的几何设计问题继续处理，不能和 benchmark 结果混淆。

## 6. 可复现材料

- [V4 axis-development manifest](benchmark_v4_axis_development_manifest.json)
- V4 generic screen：`scripts/screen_benchmark_v4_manifest.py`
- V4 pilot runner：`scripts/screen_benchmark_v4_axis_pilot.py`
- Six-direction geometry 与 episode runner：`scripts/run_rod_perturbation_benchmark.py`
- Geometry unit test：`tests/test_rod_approach_geometry.py`
