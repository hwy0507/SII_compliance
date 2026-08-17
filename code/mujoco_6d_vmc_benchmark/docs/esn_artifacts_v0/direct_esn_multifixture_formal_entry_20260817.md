# Direct ESN multi-fixture DAgger：正式训练入口（2026-08-17）

## 训练协议

本轮从单 fixture DAgger 升级为 multi-fixture 数据聚合，并已实际运行。

- 固定 nominal WBC；Direct ESN 独立输出 slowdown 与 6-D yielding twist。
- online input 仍为 32 维 deployable state；contact force、杆几何、impactor type、release time 只在 teacher/offline evaluation 中存在。
- 训练 fixture：`0, 1, 2`。
- held-out 验证 fixture：`3`；从未进入 readout fitting。
- 每次 DAgger：收集三个 rod fixture 的 student-visited counterfactual labels，加一条 no-rod neutral archive。
- 反事实 rollout horizon：24 physics steps（96 ms）。
- readout update：proximal ridge，`prior_readout_weight = 100`，防止单轮拟合远离安全 parent checkpoint。
- 训练轮数：3。
- counterfactual label dilation：0；此前稠密 label 试验会造成持续 residual，已明确排除。

正式 checkpoint：

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_formal_multifixture_dagger_20260817/seed_20260907/direct_esn_dagger_iteration_03.npz
```

## 固定 seed 的 matched benchmark

所有 4 个 fixture 都满足：task success、effective collision、finite state、无 hard torque limit。fixture 3 是未参与拟合的 held-out case。

| Fixture | Split | Fixed WBC RMSE (mm) | Direct ESN RMSE (mm) | Δ RMSE | Fixed→ESN impulse (N·s) | Fixed→ESN rejoin (ms) | Fixed→ESN recovery jerk (m/s³) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0 | train | 8.816 | **7.775** | **−1.041** | 0.9031 → 0.9003 | 880 → **800** | 6.1 → 10.6 |
| 1 | train | 11.893 | **9.243** | **−2.650** | 1.5241 → 1.5210 | 960 → **600** | 10.3 → 85.8 |
| 2 | train | 15.537 | **12.031** | **−3.506** | 2.1635 → 2.1622 | 960 → **480** | 2.5 → 135.7 |
| 3 | held-out | 17.901 | **15.504** | **−2.397** | 2.5038 → 2.5051 | 1000 → **640** | 15.0 → 119.2 |

配对 no-rod 结果：task success=true、hard torque limit=false、mean yielding twist=`0.00173 m/s`、mean WBC slowdown=`0.00275`。因此 nominal neutrality 保持成立。

## 判定

这标志着项目已达到 **正式 multi-fixture DAgger 训练入口**：

1. 单 fixture 的过拟合/任务失败已由跨 fixture counterfactual aggregation 消除。
2. 训练 fixture 与 held-out fixture 的 post-contact RMSE 和 rejoin latency 都优于 Fixed WBC。
3. 接触 impulse 在 train fixtures 小幅降低；held-out fixture 3 仅有 `+0.0013 N·s` 的轻微上升，需要作为安全预算继续约束。
4. recovery jerk 是当前最主要 trade-off，尤其 fixture 2/3 明显高于 Fixed WBC；因此本 checkpoint 允许进入正式训练和消融，但**不能作为最终论文冻结模型**。

## 关于“多 seed”

本环境当前固定 fixture、固定 initial checkpoint 且没有 rollout 随机化；以不同 rollout seed 重复会得到完全一致的 checkpoint。它验证了实现的确定性，但不是独立统计重复。

正式训练后的统计验证必须引入至少一种真实变化源：

- 不同 reservoir initialization seed；
- rod start time / stroke / height 的随机化训练分布；
- 或两者同时使用。

当前 checkpoint 应被视作后续随机化训练的 **deterministic reference**。
