# 多时间尺度 ESN × 多接触训练确认性协议（2026-08-21）

## 目的

跨接触实验表明，上一轮在 `negative_y + cylindrical rod` 上经过 CEM 改进的冻结 ESN，迁移到 `positive_y + ellipsoidal hand_proxy` 时失败。镜像输出 gate 也未改善该问题。因此本协议从 ESN 自身动力学下手，检验 fast–slow reservoir 是否能同时保留接触起始瞬态与卸载/恢复历史，并用多接触训练分布减少对单一接触映射的依赖。

## 算法与公平性

比较两个 320-unit Direct ESN：

| 项目 | Single-scale | Multi-scale |
|---|---:|---:|
| Reservoir units | 320 | 320 |
| Reservoir seed | 20261331 | 20261331 |
| Spectral radius | 0.90 | 0.90 |
| Input scale | 0.45 | 0.45 |
| Ridge λ | 1e-4 | 1e-4 |
| Derivative matching | enabled | enabled |
| Smoothness weight | 0.05 | 0.05 |
| Deployment budget | 5% | 5% |
| Leak dynamics | τ=0.12 s for all units | first 50% τ=0.04 s, last 50% τ=0.20 s |

两个模型使用完全相同的成功教师轨迹、采样、readout 拟合流程和 32-D deployable observation。multi-scale 只改变固定 reservoir 的 leak vector：fast 子群响应接触开始和突变，slow 子群保留卸载、恢复及二次冲击历史。readout 仍为线性 ridge readout，reservoir 权重仍固定随机生成。

部署观测严格为：

```text
q(7), qdot(7), nominal_twist(6), pose_error(6), wbc_twist_error(6)
```

没有输入接触力、装置质量/刚度/阻尼、障碍物几何或方向、接触时序、future release 信息，也没有改变共同 FR3 torque limits 或 residual safety clamp。

## 多接触训练数据

训练数据来自 MuJoCo 中两类真实有限质量接触装置：

- `negative_y + cylindrical rod`：10/10 成功 VMC teacher traces；
- `positive_y + ellipsoidal hand_proxy`：8/10 成功 teacher traces；两条失败 teacher trace（`positive_y_hand_03.npz`、`positive_y_hand_07.npz`）排除，不把失败行为作为 BC 标签；
- neutral reference：1/1 成功 trace。

两类 teacher 沿用各自先前独立 validation 选出的预算（rod 5%、hand-proxy 2%）。所有 trace 保存 `residual_budget_fraction` provenance，并在 bootstrap 时转换到统一 5% deployment budget：

```text
action_student_unit = action_trace_normalized × trace_budget / target_budget
```

该换算保持相同 physical torque，不增加额外观测或信息。

离线拟合 MSE 几乎相同：single-scale `0.0021416593`，multi-scale `0.0021424353`；因此闭环差异主要用于检验 reservoir time dynamics，而非拟合误差差异。

## 评估与选择

目标场景为 `positive_y + finite-mass ellipsoidal hand_proxy`，保留 MuJoCo 有限质量 body、阻尼 slide joint、受力受限 position servo、`solref` 接触柔度、FR3 torque limits 和 residual safety clamp。每个 seed 使用 4 个随机 fixture，参数仍在既有 contact-apparatus envelope 内随机化。

- validation：`20261311–20261315`；
- held-out test：`20261316–20261320`；
- ESN candidates：single-scale 与 multi-scale，均固定 5%；
- VMC candidates：`k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`；
- family 内选择规则：先最大化 task success，再以 mean at-grasp error 最小破平局；
- 测试只运行被选中的 ESN 与 VMC 一次。

本轮不使用此前任何 held-out test seed 进行调参。结果生成后，`20261316–20261320` 视为已消耗；不得据此继续调整 fast/slow time constants、fast fraction、reservoir size、teacher mix、budget、smoothness、CEM 或 checkpoint。

## 预期解释边界

若 multi-scale 胜出，只能说明在该多接触训练包络内，fast–slow reservoir 有助于 held-out 闭环表现；不能称为任意接触几何的自动泛化。若仍落后，则说明该动力学改进不足，下一轮需要另立全新 split，优先研究训练期 policy improvement 或受约束在线 readout adaptation，而不是回看当前 test 继续调参。所有结论仅适用于 MuJoCo；真机部署仍需 system identification、力矩/力传感器标定、安全停止和低速 dry-run。
