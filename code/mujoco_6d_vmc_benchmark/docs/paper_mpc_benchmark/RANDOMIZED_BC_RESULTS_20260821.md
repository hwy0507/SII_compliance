# 随机化教师蒸馏消融（服务器，2026-08-21）

## 设置

在随机化冲击工况上重新生成教师轨迹：12 条 rod/ball 轨迹（6 rod + 6 ball），参数范围为 stroke ±0.002 m、height ±0.0015 m、start time ±0.015 s；另加入 1 条固定木板轨迹和 1 条 no-rod 轨迹。所有教师轨迹均成功，预算为 3%。

轨迹 manifest：

```text
/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_randomized_bc_20260821/traces/manifest.json
```

训练方式与原 stable-reference coverage BC 相同：固定随机 reservoir、40 ms observation/action、washout 3、rod repeat 4、neutral repeat 4、ridge λ=1e-4、derivative matching。

## 测试结果

测试使用未参与教师生成的评估 seed `20260819–20260823`，并使用与前一轮完全相同的匹配随机化 fixture。

| 模型 | 棒击成功率 | 球击成功率 | 木板成功率 | 棒/球误差均值 |
|---|---:|---:|---:|---:|
| 旧 ESN-101（固定 coverage BC） | 20/20 | 20/20 | 10/10 | 11.04 mm |
| 旧 ESN-202（固定 coverage BC） | 20/20 | 20/20 | 10/10 | 10.42 mm |
| 旧 ESN-303（固定 coverage BC） | 20/20 | 20/20 | 10/10 | 9.30 mm |
| 新 ESN-101（随机化教师 BC） | 20/20 | 20/20 | 10/10 | 10.51 mm |
| 新 ESN-202（随机化教师 BC） | 20/20 | 20/20 | 10/10 | 9.98 mm |
| 新 ESN-303（随机化教师 BC） | 20/20 | 20/20 | 10/10 | 10.96 mm |

旧模型三 seed 棒/球均值为约 10.25 mm；新模型三 seed 均值为约 10.49 mm。新蒸馏在球击上有改善趋势，但 rod/board 上没有一致改善，因此不能把“增加随机化教师轨迹”直接宣布为性能提升。

## 结论与主表处理

这项实验作为 proposed 的训练覆盖消融和负结果保留，不替换正式 proposed checkpoint。正式 proposed 仍采用旧的 stable-reference coverage BC 配方，因为它已经通过原始和随机化测试的完整 gate，并且跨 reservoir seed 的结果更稳定。

可汇报的解释是：随机化教师覆盖保证了成功率和跨工况可用性，但教师动作分布与 Paper-MPC nominal tracking 的耦合仍然重要；简单扩大随机轨迹数量会改变 readout 的 bias，不能自动改善绝对误差。后续若继续优化，应使用分层采样或按冲击强度加权，而不是无差别增加随机轨迹。
