# 回归能量安全层与 V3 困难泛化集：阶段报告

**日期：2026-08-14。** 本阶段不改变已冻结的 V2 manifest；新增的安全机制、PPO
接口与 V3 只作为下一轮研究的可复现基础。所有数值均为 MuJoCo 仿真结果。

## 1. 本阶段落实的五个方向

| 方向 | 实现状态 | 具体实现 |
|---|---|---|
| 回归能量预算 | 已实现并做 V2/V3 验证 | `EnergyBudgetSafety` 只约束相对 contact-drive 的额外 return-drive force |
| 状态/方向平滑 | 已实现 | 用 nominal–carriage 的位置与速度误差估计 closing direction；carriage 已向目标收敛时平滑降低 boost |
| 低频学习残差 | 已接入 PPO 接口 | PPO 仍是 25 Hz、6 个 stiffness + 1 个 return-drive residual；安全层在 250 Hz 物理力应用前运行 |
| 安全层部署 | 已接入静态与 PPO 路径 | 不读取 contact、contact force、rod pose/velocity、obstacle state、未来碰撞或释放时间 |
| V3 泛化测试 | 已冻结并运行代表性 ladder | 独立的 off-nominal lateral timing/height physical fixtures；不覆盖 V2 |

## 2. 能量安全层的准确含义

控制器先算出 contact-drive 基线力 `F_base` 与请求的回归力 `F_requested`，只将
增量 `ΔF = F_requested - F_base` 输入安全层。因此，接触期的基础弹簧耦合不会被
安全层突然关闭。

每个 4 ms 物理步中，安全层：

1. 仅用当前 nominal–carriage 位置/速度误差判断小车是否已经朝误差收敛；
2. 对增量回归力施加连续的 direction scale，避免在已回归方向上突然拉回；
3. 从可测 drive damping 耗散中以保守效率给 energy tank 充能；
4. 当增量力对小车执行正机械功超过可用罐能量时，缩放该增量；
5. 日志记录 tank energy、direction scale、energy scale、请求和实际 boost norm。

这里应称为 **energy-budget / passivity-inspired safety layer**，不是对带移动
reference 的整机系统作出的严格全局被动性证明。它是一个可部署的能量注入限制器。

默认 tank 参数为初始 0.80 J、最小 0.08 J、最大 1.20 J、damping recharge efficiency
0.60。它们不是从 V2 测试结果中反调得到的，后续应在独立训练/验证集扫描。

## 3. V2 安全层 pilot（冻结 V2，n=16）

| 方法 | Valid | Recovery RMSE (mm) | Recovery IAE (mm·s) | Jerk P95 (m/s³) | 峰力矩 (N·m) | Torque-rate peak (N·m/s) |
|---|---:|---:|---:|---:|---:|---:|
| VMC-gated（已有 V2 baseline） | 16/16 | **1.674** | **1.118** | 436.44 | 30.260 | 96.77 |
| VMC-energy（新） | 16/16 | 1.933 | 1.267 | **367.51** | **30.211** | **91.13** |

安全层把 jerk P95 降低约 **15.8%**，并保持所有任务有效；但 RMSE 增加约
**15.5%**。这说明“平滑回归”不是免费的，默认罐能量较保守。

## 4. V3：独立、困难的横向泛化集

V3 与 V2 完全分开，使用未出现在 V2 的撞击时机和高度组合：

- 真实来杆方向：`negative_y`、`positive_y`；
- 起撞时机：0.980 s（更早）或 1.160 s（更晚）；
- 行程：0.170 / 0.175 m；
- 杆轴高：0.525 / 0.555 m；
- 16 个候选，固定 tapered-VMC selector 只做物理有效性筛选。

筛选后得到 14 个有效 fixture。仅两个“更晚时机 + upper height + moderate stroke”
组合接触峰力和冲量不足，按原有效碰撞门槛剔除。V3 的定义是更困难的**横向**
泛化集；它尚不是任意 3D 来向 benchmark，不能夸大该覆盖范围。

## 5. V3 代表性 ladder（共同有效 n=14）

| 方法 | Valid | Recovery RMSE (mm) | Recovery IAE (mm·s) | Jerk P95 (m/s³) | 峰力矩 (N·m) | Torque-rate peak (N·m/s) |
|---|---:|---:|---:|---:|---:|---:|
| rigid | 14/14 | **0.289** | **0.202** | 483.09 | 36.023 | 672.63 |
| impedance | 14/14 | 1.964 | **1.264** | 283.50 | 31.872 | 366.14 |
| VMC-gated | 14/14 | **1.947** | 1.293 | 304.96 | 30.288 | 122.67 |
| VMC-energy | 14/14 | 2.294 | 1.487 | 289.94 | **30.278** | **122.03** |

安全层在 V3 仍然运行稳定、任务全成功，且将 VMC-gated 的 jerk P95 进一步降低
约 **4.9%**；但 RMSE 上升约 **17.8%**。因此目前的正确结论是：

> 安全层的行为跨 V2/V3 一致——少注入回归能量、降低冲击，但牺牲部分回归速度。
> 它已经是一个可靠的安全约束层，不是当前 benchmark 上的完整 Pareto 突破。

## 6. PPO / ESN 接口约束

PPO 的 deployed actor 维度保持 52：51 维本体感觉 + 前一个 drive residual。它不新增
energy tank、接触或障碍物输入。PPO 在 25 Hz 输出低频 residual；安全层在 250 Hz
使用测得的末端/小车状态过滤其 drive 增量。因此未来 ESN 只要输出同样的低频
`[Δlog κ_x..Δlog κ_yaw, Δlog drive]`，也能复用同一个安全层，无需修改 V2/V3 协议。

服务器 smoke test 已验证 `enable_drive_residual=True`、`enable_energy_safety=True` 的
PPO 环境可以完成完整抓取 episode，52-D observation contract 不变，且 safety
diagnostic 不会进入 actor observation。

## 7. 下一步（不改变已冻结 V2）

1. 在 V2 训练/验证 fixture 上扫描 tank 初始能量、上限、recharge efficiency 和
   direction smoothing time constant，以寻找“接近 gated 的 RMSE、低于 impedance
   的 jerk”的候选；扫描结果先在 V3 检验，再固定参数。
2. 用该固定安全层进行多 seed PPO 训练；PPO 只调整慢速 stiffness/drive residual，
   不学习绕过硬安全层。
3. 将 V3 扩展为真正的多来向 3D fixture：需要为 rod 的几何朝向和 slide axis 增加
   可验证的 x/z 方向参数；该扩展应作为新的 V4，而非重写当前 V3。

## 原始产物

- [V2 safety pilot JSON](v2_energy_pilot.json)
- [V3 frozen manifest](benchmark_v3_manifest.json)
- [V3 representative ladder JSON](benchmark_v3_representative_ladder.json)
- [V3 representative ladder CSV](benchmark_v3_representative_ladder.csv)
- [V3 Pareto figure](benchmark_v3_representative_pareto.png)
