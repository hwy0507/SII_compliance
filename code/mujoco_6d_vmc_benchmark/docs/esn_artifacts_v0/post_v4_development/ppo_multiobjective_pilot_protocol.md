# Post-V4 PPO 多目标 pilot：预注册开发协议

## 动机

三 seed 复现表明，原始 PPO final 可能降低 recovery RMSE，但改善不稳定，且平均 rejoin latency、jerk、impulse 未同步改善。本 pilot 只在 post-V4 development 训练/验证池上筛选新的训练目标；V4 final 禁止访问。

## 固定部分

- 物理 fixture、Panda WBC、Fan Ye fixed reservoir、84D actor observation、7D residual action、energy safety 和 PPO 主超参数均与 run001 相同。
- actor 不接触 rod/contact/force/obstacle/future-phase/fixture-ID 等受限信息。
- 每个候选使用 seed `20260818`、8 并行环境、200,000 requested steps；对独立 validation 9 fixtures 做 deterministic matched rod/no-rod 评估。
- 仅在 validation 上选择候选；任何候选都不进入 V4 final。

## 新的、默认关闭的 reward 项

1. `residual_magnitude_penalty`：惩罚已被 causal residual gate 施加的 stiffness/drive residual 幅值，避免残差在完成让位后持续维持大偏置。
2. `recovery_tube_time_penalty`：仅在训练 reward 内、杆释放后且误差仍在 5 mm rejoin tube 外时，惩罚每一个 control step。释放时刻不是 actor 输入；actor 仍只根据部署时可得的 WBC/proprioception/ESN 状态行动。

## 候选与选择规则

| 候选 | gate hold/taper (s) | jerk wt | action-change wt | magnitude wt | tube-time wt | κ / drive log-rate (s⁻¹) |
|---|---:|---:|---:|---:|---:|---:|
| `smooth_medium` | 0.22 / 0.10 | 0.060 | 0.006 | 0.0010 | 0.010 | 1.20 / 0.80 |
| `smooth_strong` | 0.20 / 0.12 | 0.100 | 0.009 | 0.0025 | 0.018 | 1.00 / 0.65 |

候选必须先满足：9/9 task、9/9 matched no-rod task、9/9 effective collision，且无硬 torque 违规。满足后按以下词典序选择：

1. rejoin latency 不高于 zero-residual 的 0.0322 s；
2. peak jerk 与 contact impulse 均不高于 zero-residual；
3. 最低 recovery RMSE；
4. 最低 paired trajectory-offset RMSE。

若没有候选同时满足前两项，则如实记录“没有通过的 multiobjective candidate”，不进入新的 multi-seed 或 V4 final。
