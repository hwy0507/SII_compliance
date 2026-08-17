# Direct ESN counterfactual teacher / DAgger 阶段记录

日期：2026-08-17  
范围：固定 WBC + 独立 Direct ESN；不包含 VMC，不使用接触力等 privileged truth 作为 online 输入。

## 1. 本轮完成的实现

- `counterfactual_direct_esn_teacher.py`：在当前 MuJoCo 状态复制出的 `MjData` 上比较零动作、减速和分级向外让位动作；接触力、杆运动和碰撞诊断只进入离线 teacher label。
- `run_direct_esn_dagger.py`：支持 `--teacher-mode counterfactual`、短时视界、student-visited archive 和 counterfactual label weighting。
- 无杆/无接触时 teacher 强制输出零；有杆时只有零动作 rollout 预测到接触，才开放向外让位候选。
- 额外试验了 WBC deviation-aligned yield（ESN 学让位幅值、方向由可部署的 WBC pose error 给出）。该结构保持 opt-in，默认不影响基线。

## 2. 关键 smoke 结果

### nominal neutrality

在 counterfactual teacher 修正后，no-rod archive 的非零 teacher label fraction 为 `0.0`。多组 readout weight 扫描的 no-rod 闭环均满足：

- task success：`true`
- hard torque limit：`false`
- yielding twist：约 `0.0003–0.0014 m/s`

这证明 DAgger 的 nominal 自激问题已被修复。

### rod 闭环与固定 WBC 对照

单 fixture、seed `20260817`，有效碰撞均成立，任务均成功，硬力矩限制均未触发。关键轨迹指标如下：

| 方法 | peak deviation | post-release RMSE | rejoin 到 4 mm | 备注 |
|---|---:|---:|---:|---|
| Fixed WBC | 12.37 mm | 6.57 mm | 665 ms | 当前基础参照 |
| 第一轮 counterfactual-weighted ESN（未对齐） | 12.79 mm | 7.97 mm | 945 ms | 让位信号仍偏弱 |
| error-aligned + canonicalized ESN（实验分支） | 56.93 mm | 8.05 mm | 985 ms | 明确失败，不作为默认算法 |

接触峰值力约为 `19.72 N`，各方法非常接近；这是反应式控制在首次接触冲量已经形成后才观察到 WBC 偏差的物理限制，不能将其误报为算法改进。

## 3. 结论

本轮达到的阶段性结论是：

1. **DAgger 的分布修复有效**：无杆自激被消除。
2. **counterfactual teacher 的状态克隆实现正确**：MuJoCo snapshot 不污染 live rollout，在线输入 contract 未扩大。
3. **当前 teacher 仍不足以证明 Direct ESN 优于 Fixed WBC**：rod 的 post-release RMSE 和 rejoin latency 尚未改善。
4. **误差对齐/幅值化分支不能直接纳入主结果**：会导致过大偏离，代码保留为显式 opt-in 消融，不作为默认配置。

## 4. 可复现位置

服务器输出目录：

- `/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_dagger_counterfactual_gated_20260817`
- `/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_counterfactual_weight_scan_20260817`
- `/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_error_aligned_coordinates_20260817`

重要代码提交：

- `c0f96dd`：短时反事实 MuJoCo teacher
- `13cb28c`：预测接触门控，确保 no-rod 零标签
- `e52faa2`：counterfactual 非零标签加权
- `458ab2c`：误差对齐输出（opt-in）
- `9a8e940`：误差对齐坐标训练
- `21f54dc`：将误差对齐分支恢复为 opt-in，默认不污染基线

## 5. 下一步建议

主线不应继续盲扫 reservoir 或重复提高 label weight。下一步应先做一个严格的 **post-contact-only** 评估与 teacher 设计：把“首次冲量峰值”与“碰撞后回位/轨迹保持”分开优化，并对不同接触时刻、rod stroke 和初始 WBC 偏差做 matched multi-seed 验证；只有 post-release RMSE 与 rejoin latency 同时优于 Fixed WBC，才冻结该 Direct ESN checkpoint 接入 WBC-aware ladder。
