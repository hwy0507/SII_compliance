# ESN 因果状态变化读出实验（2026-10-07）

## 目的

ESN 与 matched RNN 在最终 office-v6 矩阵的总体差距很小：ESN 的 task 为 60/72、strict 为
43/72，RNN 为 58/72、44/72。新实验不扩大储备池、不增加观测字段、不修改环境或 gate，专门检验
储备池对“碰撞后瞬态—恢复”历史的优势能否转化成更好的动作。

## 预注册机制

固定 parent ESN 的 128 单元多时间尺度储备池和已有读出，只增加两组因果内部特征：

\[
\Delta h_t=h_t-h_{t-1},\qquad |\Delta h_t|.
\]

以冻结 parent 的读出为基线，用 ridge 在 20 个训练身份上拟合 1,792 个 residual 系数；用
储备池变化幅度的 RMS 做因果门控，阈值固定为 2.0，输出 residual 固定乘 0.25，并在读出
preactivation 域相加后再按原 action7 解码。储备池、输入映射、48D 本体输入、执行器幅值/变化率
限制、原始 gate 和 `dt=5e-5` 正式保留条件均不变。actor 不读取接触真值、球/物块状态、事件时间、
任务阶段、视觉或距离字段。

候选 checkpoint（统一父模型 `clipped_linear` 解码后的版本）：

`outputs/esn_state_delta_gate_20261007_v4_gain025_clipparity/checkpoint.npz`

SHA256：`7e10362d32a666b0e1d2cc7cad4bbed7c3280d6dc081058873751b57a413345f`。
训练数据 SHA256：`7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0`。

## 离线身份留出与记忆消融

在 20/5 固定身份划分的 6,875 个 held-out 帧上，按完整时间顺序回放，再做“每个观测都清空储备池”
的因果消融。动作 MSE 只作机制诊断，不当作任务成功：

| 方法 | 完整留出 MSE | 瞬态窗口 MSE | 清空储备池 MSE | 总 memory gap |
|---|---:|---:|---:|---:|
| parent ESN | 0.000241633 | 0.000590783 | 0.006579908 | 0.006338275 |
| 因果 Δh ESN（修正解码） | **0.000228972** | 0.000545588 | 0.006817954 | **0.006588982** |
| matched RNN | 0.000234517 | **0.000511666** | 0.006716053 | 0.006481536 |

“memory gap”是清空储备池后 MSE 减去完整顺序 MSE。因果 Δh ESN 的整体留出误差比 matched RNN
低约 0.99%，且 memory gap 高约 5.1%，说明它确实更依赖并利用历史状态；瞬态窗口 MSE 仍略高于
RNN，因此不能声称已经全面超过 RNN。独立审计原始数据、seed、模型 SHA 和输入禁用字段见
`outputs/esn_state_delta_gate_20261007_v4_gain025_clipparity/CAUSAL_MEMORY_AUDIT.json`；小型证据副本已提交到
`docs/evidence/esn_state_delta_20261007/`。

## 闭环开发证据

在服务器归档的相同 office-v6 默认开发锚点（`dt=1e-4`）上，前一轮固定 gain=0.25 的 v3 候选相对 parent
ESN 与 matched RNN 的结果为：

| 方法 | task | strict | RMSE | 峰值力矩 | 峰值速度 | 最大穿透 |
|---|---:|---:|---:|---:|---:|---:|
| parent ESN | 失败 | 失败 | 30.039 mm | 49.831 Nm | 0.3416 m/s | 0.1435 mm |
| matched RNN | 通过 | 失败 | 29.938 mm | 54.435 Nm | 0.3863 m/s | 0.2359 mm |
| 因果门控 ESN gain=0.25 | **通过** | **通过** | **29.400 mm** | **49.032 Nm** | **0.3461 m/s** | **0.1100 mm** |

该锚点上 ESN 同时降低三项连续指标，并从 parent 的 task/strict 失败变为通过；物理子步、动作和
储备池回放均通过。归档目录为：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_state_delta_gate_dev_20261007_v3_gain025/`

服务器当前不可达时，以上路径只按前一轮已核验收据引用，不重新声称本轮已上传。

该服务器锚点属于旧 v3（训练脚本修正前）闭环记录；本轮修正了 `clipped_linear` 解码并生成 v4，
所以不能把 v3 的闭环数字直接当作 v4 的闭环结果。v4 目前只有离线审计和本地 office-v5 兼容 smoke，
必须在同一 office-v6 worker 上重新闭环后才能更新候选。

本地 office-v5 兼容性 smoke 使用相同 checkpoint、55 s、`dt=1e-4`，结果为 task/strict=false/false、
RMSE 456.748 mm、峰矩 68.982 Nm、峰速 0.361326 m/s、最大外部穿透 0.196223 mm；它和 office-v6
锚点不是同一环境版本，只作为失败兼容性记录，保存在候选目录 `v5_smoke_dev_anchor/`，不进入公平矩阵。

## 结论与下一步

这项设计提高了 ESN 的机制可解释性和在一个冻结开发锚点上的优势幅度，但还不是跨条件或正式
`dt=5e-5` 结论。下一步只有在同一 frozen office-v6 worker 可用时，按预注册的开发身份先做
多条件闭环审计；若 strict 仍通过，再按原协议决定是否解封正式评测。失败回合必须保留，不能调 gate、
放宽输入或把离线 MSE 当任务成功。
