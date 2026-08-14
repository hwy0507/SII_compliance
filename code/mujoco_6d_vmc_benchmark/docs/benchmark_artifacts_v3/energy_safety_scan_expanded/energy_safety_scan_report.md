# 独立验证集上的 energy-budget safety 参数扫描

## 一句话结论

在**独立于已冻结 V2 与 V3 的 16 个有效物理碰撞 fixture** 上，11 个候选 safety 配置均通过完整的任务与碰撞有效性门槛，且平均 post-contact jerk P95 均不高于同一验证集的 impedance 基线。按扫描前固定的选择规则，选中 **`slow_smoothing`**：仅将 direction-smoothing 时间常数由 40 ms 改为 **80 ms**，其余能量罐参数保留默认值。

这个选择是“在达到平滑性门槛的候选中，恢复误差最小”的选择，而不是将若干单位不同的指标事后加权成一个分数。它仍然只是 MuJoCo 中的 validation 选择；下一步必须把参数冻结后，在 V2/V3 上做一次**不再调参**的 holdout evaluation。

## 1. 为什么这不是在 V2/V3 上调参

V2 与 V3 已冻结，只作为后续泛化测试。这里新建的 validation 候选由以下参数的笛卡尔积组成：

| 因子 | 取值 |
|---|---|
| 侧向来杆方向 | `negative_y`, `positive_y` |
| 来杆开始时间 | 1.040 s, 1.100 s |
| 杆行程 | 0.165 m, 0.170 m |
| 杆高度 | 0.535 m, 0.545 m |

这 16 个候选与 V2/V3 的时间—高度组合不同。先用固定的 tapered-VMC selector 筛除无效候选；最终 **16/16** 都满足实体碰撞和完整抓取任务条件。每一个 controller/configuration 还都配对运行了无杆参考 episode。

固定有效性门槛为：仿真有限；有 rod–hand 实体接触；峰值接触力至少 15 N；接触冲量至少 0.45 N·s；稳定回归到 5 mm 轨迹管；物块被抬起且在终点保持；无 hard torque limit；匹配 no-rod episode 同样任务成功。

## 2. 预先声明的选择规则

1. 一个 energy configuration 必须在全部 16 个 validation fixture 上通过上述硬门槛；
2. 其平均 post-contact jerk P95 必须不大于同一 validation set 的 impedance 基线；
3. 在满足前两条的 energy configuration 中，选择 recovery RMSE 最小者；
4. 仅在 RMSE 相同的情况下，使用更低 torque-rate peak 破平局。

本次 impedance 平滑性阈值为 **301.176 m/s³**。没有把 RMSE、jerk、力矩等异量纲指标任意合成为单一加权分数。

## 3. 扫描空间

除表中变化项外，默认值为：`initial=0.80 J`、`minimum=0.08 J`、`maximum=1.20 J`、`recharge=0.60`、`minimum direction scale=0.30`、`direction transition speed=0.08 m/s`、`smoothing tau=40 ms`。

| 标签 | initial/min/max (J) | recharge | direction floor | tau |
|---|---:|---:|---:|---:|
| `low_tank` | 0.55 / 0.08 / 0.90 | 0.60 | 0.30 | 40 ms |
| `default` | 0.80 / 0.08 / 1.20 | 0.60 | 0.30 | 40 ms |
| `high_tank` | 1.05 / 0.08 / 1.50 | 0.60 | 0.30 | 40 ms |
| `low_recharge` | 0.80 / 0.08 / 1.20 | 0.40 | 0.30 | 40 ms |
| `high_recharge` | 0.80 / 0.08 / 1.20 | 0.80 | 0.30 | 40 ms |
| `fast_smoothing` | default | 0.60 | 0.30 | 20 ms |
| **`slow_smoothing`** | **default** | **0.60** | **0.30** | **80 ms** |
| `yield_friendly` | default | 0.60 | 0.15 | 40 ms |
| `small_tank` | 0.16 / 0.08 / 0.30 | 0.60 | 0.30 | 40 ms |
| `near_empty_tank` | 0.10 / 0.08 / 0.20 | 0.60 | 0.30 | 40 ms |
| `near_empty_no_recharge` | 0.10 / 0.08 / 0.20 | 0.00 | 0.30 | 40 ms |

后三个低能量配置是有意加入的“预算会实际绑定”的检查。它们避免了把仅由方向平滑产生的结果误称成 energy-tank 效果。

## 4. 聚合结果（16/16 common-valid）

所有数值为 rod episode 在全部有效 fixture 上的均值。RMSE 越小越好；jerk、峰值力矩及 torque-rate 越低越好。

| 方法 / 配置 | Recovery RMSE (mm) | Recovery IAE (mm·s) | Rejoin latency (s) | Jerk P95 (m/s³) | Peak torque (N·m) | Torque-rate peak (N·m/s) |
|---|---:|---:|---:|---:|---:|---:|
| impedance | 1.703 | 1.108 | 0.273 | 301.176 | 31.871 | 293.566 |
| VMC-gated | 1.735 | 1.151 | 0.259 | 333.790 | 30.135 | 87.960 |
| `low_tank` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `default` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `high_tank` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `low_recharge` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `high_recharge` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `fast_smoothing` | 2.032 | 1.316 | 0.297 | **282.778** | 30.133 | 87.959 |
| **`slow_smoothing` (selected)** | **2.000** | **1.301** | **0.287** | 300.747 | **30.130** | 87.958 |
| `yield_friendly` | 2.103 | 1.356 | 0.303 | 286.697 | 30.133 | **87.958** |
| `small_tank` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `near_empty_tank` | 2.022 | 1.312 | 0.293 | 290.993 | 30.132 | 87.959 |
| `near_empty_no_recharge` | 2.266 | 1.436 | 0.344 | 284.332 | 30.132 | 87.959 |

所有 11 个 energy configuration 都满足三条预注册可行性条件。因此 `slow_smoothing` 因为 2.000 mm 的恢复 RMSE 最小而被选中；其平均 jerk 为 300.747 m/s³，仍低于 impedance 的 301.176 m/s³ 阈值。`fast_smoothing` 有更低 jerk，但它不符合本次“恢复精度优先”的第二阶段目标，不能在看过结果后替换选择规则。

## 5. Safety layer 实际是否触发

这部分诊断很重要：energy-budget safety layer 不是仅凭名字就可声称发挥了作用。

| 配置 | 平均最小 tank (J) | 平均 tank (J) | 平均 direction scale | 平均 energy scale |
|---|---:|---:|---:|---:|
| `default` | 0.750 | 0.797 | 0.645 | 1.000 |
| `slow_smoothing` (selected) | 0.750 | 0.796 | 0.642 | 1.000 |
| `small_tank` | 0.115 | 0.159 | 0.645 | 0.994 |
| `near_empty_tank` | 0.080 | 0.108 | 0.645 | 0.950 |
| `near_empty_no_recharge` | 0.080 | 0.084 | 0.645 | 0.776 |

解释如下：

- 在默认储能范围，`energy_scale=1.000`，说明 return-drive 的正功没有耗尽预算；性能差异主要来自 causal direction smoothing，而不是 tank 饱和。
- `near_empty_tank` 已发生轻度缩放，但本组场景的宏观指标仍近似默认值。
- `near_empty_no_recharge` 的平均能量缩放为 0.776，表明预算明确绑定。相对 default，它使 jerk P95 从 290.993 降至 284.332 m/s³（约 **2.3%**），但 RMSE 从 2.022 增至 2.266 mm（约 **12.1%**），稳定回归也更慢。这是预期的安全—恢复折中，而不是无代价改善。

因此，冻结的选择是一个可靠的“平滑方向切换”设置，但不应把它描述为一次强能量罐介入带来的突破。能量预算在低储能、零 recharge 的压力测试中确实会发生因果限制，并呈现可测的平滑性—恢复取舍。

## 6. 与普通基线的正确解读

选中的 `slow_smoothing` 相比 impedance：

- recovery RMSE 高 0.297 mm（约 17.4%），所以不能宣称精度更好；
- jerk P95 低 0.430 m/s³（约 0.14%），只是刚好满足预注册阈值，优势很小；
- peak torque 低约 5.5%；
- torque-rate peak 低约 70.0%，这是当前 VMC 系列更稳定、更明确的安全执行优势。

相比 VMC-gated，`slow_smoothing` 的 jerk P95 低约 9.9%，但 RMSE 高约 15.3%。因此目前合理结论仍是：六维 VMC / safety layer 提供受控让位与较低执行突变的路径，换取一定的回归精度；它尚未在所有指标上压倒 rigid 或 impedance。

## 7. 可复现材料与下一步

- [验证 fixture manifest](energy_safety_validation_manifest.json)
- [完整 episode 级 JSON](energy_safety_scan.json)
- [完整 episode 级 CSV](energy_safety_scan.csv)
- 扫描代码：`scripts/scan_energy_safety.py`

下一步严格流程：从此处冻结 `slow_smoothing` 的七个参数；为 V2/V3 ladder 增加显式的 JSON config 注入；只运行 selected VMC-energy，一次性在 V2、V3 上做无调参评估；再将它与已完成的 default VMC-energy、VMC-gated、impedance 在 common-valid subset 上对比。若 holdout 上的优势消失，也必须如实保留该结论。
