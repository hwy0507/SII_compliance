# 当前 48D 模型与 classical baseline 配对开发结果（2026-09-23）

本表为全新重跑的 panel push 开发诊断，参数尚未完成公平预算调优，不能作为论文最终排名。VMC、impedance、admittance、冻结 MLP、冻结 nonlinear ESN 共享三组物理条件和任务规则。全部仿真完成回合均计入指标，包括失败回合；执行错误单列，不按零误差处理。

| 方法 | 完成数 | 任务通过 | panel gate通过 | 位置 RMSE (mm) | 峰值力矩 (N·m) | 峰值速度 (m/s) | 速度 P95 (m/s) | 最坏穿透 (mm) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| vmc | 3/3 | 3/3 | 1/3 | 136.8408 ± 33.3774 | 35.7578 ± 1.4621 | 0.1227 ± 0.0091 | 0.0688 ± 0.0021 | 0.2098 |
| impedance | 3/3 | 3/3 | 0/3 | 18.8875 ± 0.0308 | 87.0000 ± 0.0000 | 1.6557 ± 0.0062 | 0.0819 ± 0.0012 | 0.3685 |
| admittance | 3/3 | 2/3 | 1/3 | 137.2197 ± 51.9895 | 39.6110 ± 1.1253 | 0.1390 ± 0.0087 | 0.0775 ± 0.0013 | 0.2018 |
| mlp | 3/3 | 2/3 | 1/3 | 133.8750 ± 61.3143 | 36.7327 ± 0.8514 | 0.1458 ± 0.0034 | 0.0692 ± 0.0007 | 0.2081 |
| esn | 3/3 | 1/3 | 1/3 | 148.5661 ± 26.2340 | 36.8063 ± 0.7322 | 0.1437 ± 0.0088 | 0.0696 ± 0.0006 | 0.2017 |

数值为回合均值 ± 回合标准差（n=3），不是训练 seed 置信区间；穿透列为最坏回合。

通过 panel gate 的条件并不相同：VMC/旧导纳通过 9302，MLP/ESN通过 9300，旧阻抗没有通过条件。因此目前没有全部方法共同有效的配对条件集，不能各取自己的成功回合再拼一张排名表。唯一 MLP/ESN 同时通过的 9300 上，ESN 的 RMSE 和力矩更高而采样速度峰值更低，呈现权衡，不能由三条开发回合得出普遍优势。

## 原始 trace 复核与阶段误差

本地保留全部 15 份 `rollout.npz`；独立工具 `tools/audit_panel_traces_20260923.py` 从原始位置、目标和 twist 复算，15 条全程 RMSE 和速度峰值均与汇总匹配（绝对容差 `1e-12`），采样间隔均为 0.04 s。每份 trace 的 SHA-256 与完整逐阶段指标保存在 `docs/evidence/classical_20260923/panel48_trace_audit.json`。

额外检查训练/推理预处理：MLP 训练时归一化后裁剪至 ±12，而现有 `CurrentMLP.act` 不执行此裁剪。使用本次冻结 checkpoint 的 mean/std 检查三份原始观测，最大绝对归一化值依次为 10.09845、10.11595、10.57864，三回合均有 0/28,800 元素、0/600 step 超过 12，因此该代码差异没有影响本轮结果。后续更强扰动评估仍需统一训练/推理的裁剪契约。

下表为每种方法三个回合的阶段 RMSE 均值（mm）；阶段时长因状态机而不同，不能作为统一时间轴的接触窗口比较。

| 方法 | approach | align/grasp approach | close gripper | loaded lift |
|---|---:|---:|---:|---:|
| VMC | 38.090 | 46.156 | 5.571 | 143.603 |
| impedance（接口诊断） | 33.272 | 21.905 | 1.271 | 18.734 |
| admittance | 38.090 | 46.156 | 5.735 | 144.642 |
| MLP | 37.692 | 45.577 | 6.117 | 140.416 |
| ESN | 38.046 | 45.882 | 5.676 | 156.030 |

除旧阻抗诊断外，各方法全程平方误差约 96.7%–98.0% 来自 Z 方向。这表明当前 waypoint RMSE 主要受持物抬升过程影响，不宜将其单独解释成横向接触让位品质。旧阻抗较小的 RMSE 伴随无有效杆接触、超高速度和力矩饱和，不能据此判优。

## 评价口径与公平性边界

- RMSE：25 Hz 的末端位置相对当前任务 waypoint 的欧氏误差。任务阶段按状态切换，各方法的切换时刻可不同；这是相同参考规则下的 waypoint 跟踪指标，不能称为同一绝对时钟轨迹误差。
- 力矩：4 ms 控制步更新的 applied command 最大绝对关节力矩，细物理步保持命令。早期快照字段名 physics_peak_motor_torque_nm 在此更正语义，数值不改；不是子步实际 qfrc_actuator 测量峰值。
- 速度：25 Hz 末端线速度范数的峰值及 P95，可能漏掉更短瞬态。最终正式矩阵应增加所有方法共用的 physics-substep 审计。
- panel gate：任务通过、杆接触 >0.3 s、终止前 2 s 已脱离杆、杆末态距离 >2 mm、非目标物外部穿透 <0.2 mm、所有外物接触均无 link0–link4 误碰；它仍不是最终办公室稳定放置门。
- impedance 替换速度伺服为 Jᵀ Cartesian wrench，复用力矩限幅和 slew，但名义速度/加速度约束不能直接约束其实际运动；高速度、力矩饱和和无杆接触结果只能视为待修正实现诊断。
- admittance 当前仍仅输出虚拟速度，尚未加入完整虚拟位姿参考跟踪；该固定参数失败不能代表充分调优的导纳控制。
- 三组条件的角度、高度、质量联动变化，不是全因子 test。三组均为开发条件，不用于 office blind-test 结论。

## 物理条件

```json
[
  {
    "seed": 9300,
    "push_angle": -0.15,
    "push_height": 0.575,
    "payload_mass": 0.085
  },
  {
    "seed": 9301,
    "push_angle": -0.05,
    "push_height": 0.58,
    "payload_mass": 0.1
  },
  {
    "seed": 9302,
    "push_angle": 0.1,
    "push_height": 0.585,
    "payload_mass": 0.115
  }
]
```

## 模型与运行来源

```json
{
  "mlp": {
    "path": "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/mlp/20260923_retry1/best.npz",
    "sha256": "5327061ccbfc147c410be355bd82c6769736978de971afa48a01844fc4dd87b7"
  },
  "esn": {
    "path": "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/unified_6d_matched_students_20260921/esn_nonlinear/20260923_retry1/best.npz",
    "sha256": "0f9d1c2970bbf9e35f9748eb68ae73c84340e6f4e193f3ee37e584970337975a"
  }
}
```

原始汇总：`docs/evidence/classical_20260923/panel48_final.json`。协议：`docs/evidence/classical_20260923/panel48_protocol.json`。
协议保存运行源码 hashes、参考 arguments、VMC 参数和模型 hashes；每回合保留 command/log/JSON/NPZ。

运行环境为 Spark aarch64、Python 3.12.3、MuJoCo 3.11.0、numpy 2.5.2。已逐回合计算服务器归档编译模型 `.mjb` 的 SHA-256：每个物理条件下，五种方法的模型文件完全相同；后续 reference 变体也与对应条件逐字节一致。完整路径/hash/文件大小见 `docs/evidence/classical_20260923/server_model_metadata.json`。这提供了场景/编译物理参数一致的实证，仍不表示不同控制器具有相同闭环状态或完全相同内部控制结构。

## 下一步验收

为传统控制器修正接口并在同一开发集上固定调参预算；通过真实接触、任务和物理门后，与冻结 ESN/MLP 在新的一组预先固定物理条件上评估。保留失败率、三项指标和阶段统计，不从本轮失败表推导 proposed 的论文级优势。
