# Direct ESN reservoir bootstrap 修复后的正式训练（2026-08-17）

## 修复思路

旧的随机 reservoir bootstrap 仅从单一 rod phase-teacher trace 初始化，导致不同 reservoir 在 no-rod 与 rejoin 阶段出现明显自激。修复后不再使用该单一 teacher 作为随机 reservoir 起点：

1. 使用通过 deterministic multi-fixture selection gate 的 Direct ESN reference；
2. 在 training fixture `0,1,2` 与 no-rod 上生成完整 40 ms deployable state/action expert traces；
3. 每个 reservoir seed 先做 reference behavior cloning，再执行三轮 fixture `0,1,2` 的 counterfactual/proximal DAgger；
4. fixture `3` 始终 held-out。

独立 reservoir：`71`、`137`、`251`。

## 已修复的部分

| Reservoir | no-rod task | hard torque limit | no-rod mean yield (m/s) |
|---:|:---:|:---:|---:|
| 71 | pass | false | 0.00080 |
| 137 | pass | false | 0.00183 |
| 251 | pass | false | 0.00108 |

相较旧 bootstrap（0.00404–0.10283 m/s），nominal neutrality 已得到实质修复。

## Multi-fixture 结果摘要

所有 rod fixture 均完成 task、具有有效碰撞、没有 hard torque limit，且 contact impulse 均小幅下降或近似持平。下表列出与 Fixed WBC 的 post-contact RMSE 差值；负值表示 ESN 更好。

| Reservoir | Fixture 0 | Fixture 1 | Fixture 2 | Held-out fixture 3 | 判定 |
|---:|---:|---:|---:|---:|---|
| 71 | +0.132 mm | +1.463 mm | +6.369 mm | +3.173 mm | reject |
| 137 | **−0.477 mm** | **−0.106 mm** | +2.252 mm | +6.971 mm | reject |
| 251 | **−0.242 mm** | +0.147 mm | +4.717 mm | +4.822 mm | reject |

所有三个 seed 在 fixture 0/1 上已获得安全的、接近或略优于 Fixed WBC 的轨迹结果；但 fixture 2 与 held-out fixture 3 的 RMSE 都未通过 selection gate。rejoin latency 虽普遍更短，但当前不能用它掩盖更大的 trajectory error 与 recovery jerk trade-off。

## 结论与冻结选择

- **修复成功**：stable-reference behavior cloning 解决了随机 reservoir 的 no-rod 自激问题。
- **正式训练仍未完成 selection**：当前随机 reservoir 不能在强碰撞 fixture 2/3 上泛化到所需轨迹精度。
- 因此不选择任何本轮随机 reservoir checkpoint 作为 proposed 模型。
- 仍保留 [[direct_esn_multifixture_formal_entry_20260817]] 中的 deterministic multi-fixture reference 作为可工作的研究 reference。

## 下一步限定

下一轮不是继续更换 reservoir seed，而是扩展 teacher coverage：为 fixture 2/3 增加重碰撞的 counterfactual trajectory/action teacher，采用 train/validation split（例如 0/1/2 的不同 impact timing 训练，fixture 3/未见 timing 验证），并在 bootstrap 阶段直接约束 heavy-impact post-contact RMSE 与 recovery jerk。

服务器输出：

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_reservoir_repair_20260817/
```
