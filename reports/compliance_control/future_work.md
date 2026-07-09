# Compliance Future Work

## Goal

在 `whole-body-motion-control` 提供的高层名义运动之下，完成动态障碍接触后的柔顺恢复控制。

## Method Direction

```text
nominal tracking
  + analytic compliance prior
  + residual RL
  + contact history
  -> recovery / return-to-track
```

## Near-Term Focus

1. 提高 benchmark 难度，增加真实接触与释放阶段。
2. 把 `contact history` 纳入 policy，而不是只看当前帧。
3. 用统一指标评估恢复质量、碰撞程度与轨迹平滑性。
4. 把成熟接口回接到 `whole-body-motion-control`。

## Next Week Checklist

- [ ] 定义主工程到 compliance module 的输入输出接口
- [ ] 在 PPO observation 中加入固定长度 contact history
- [ ] 设计更难的动态障碍 benchmark
- [ ] 重新跑一轮 PPO 短训并记录核心指标
- [ ] 对比新旧策略的恢复效果与平滑性
- [ ] 整理回接主工程所需的接口与依赖
