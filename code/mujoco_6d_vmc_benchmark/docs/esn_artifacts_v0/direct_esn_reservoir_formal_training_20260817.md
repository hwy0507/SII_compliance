# Direct ESN 独立 reservoir 正式训练记录（2026-08-17）

## 目的

此前的 multi-fixture reference 使用固定 reservoir，因此不同 rollout seed 会产生相同 checkpoint。为获得真实模型变化，本轮新增 bootstrap：对每个 `reservoir_seed` 用相同 rod/no-rod teacher 在部署时序（40 ms）拟合独立 readout，再执行三轮 fixture `0,1,2` 的 multi-fixture DAgger；fixture `3` 始终 held-out。

独立 reservoir：`71`、`137`、`251`。

## 硬安全事实

所有 checkpoint 在四个 rod fixture 上均完成 task、发生有效碰撞、未出现 hard torque limit。该事实不足以成为选中条件，因为稳定 rejoin、nominal neutrality 与轨迹表现同样是本项目的必要条件。

## 关键失败证据

| Reservoir | no-rod mean yield (m/s) | 训练/验证主要表现 | 判定 |
|---:|---:|---|---|
| 71 | 0.00404 | 四个 fixture 的 post-contact RMSE 均高于 Fixed WBC；fixture 0/1 无稳定 rejoin | reject |
| 137 | 0.04003 | fixture 0/1/2 RMSE 分别恶化 +5.861/+4.309/+1.447 mm，且均无稳定 rejoin | reject |
| 251 | 0.10283 | 四个 fixture 的 RMSE 均显著恶化，held-out fixture 3 恶化 +9.599 mm，recovery jerk 388.4 m/s³ | reject |

相比之下，已通过 deterministic multi-fixture reference 的 no-rod mean yield 为 `0.00173 m/s`，且 fixture 0–3 都取得 RMSE/rejoin 改善；详情见 [[direct_esn_multifixture_formal_entry_20260817]]。

## 结论

1. 已完成真实意义的多 reservoir 正式训练，而不是把同一个确定性 checkpoint 重复三次。
2. 当前 bootstrap teacher/readout 方案对 reservoir initialization **不鲁棒**；不能选择任何本轮随机 reservoir 模型作为 proposed checkpoint。
3. 当前通过 selection gate 的模型仍是 deterministic multi-fixture reference；它可以用作研究基准，但不能替代后续的 reservoir-robust training。
4. 后续应先修复 bootstrap 的稳定性，再做多 reservoir 统计：例如使用 multi-fixture counterfactual archive 初始化每个 reservoir，而不是仅用单一 rod phase trace；并将 no-rod yield、stable rejoin、recovery jerk 纳入 bootstrap-stage early rejection。

## 服务器输出

```text
/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_formal_reservoir_training_20260817/
```

每个 reservoir 子目录包含 bootstrap checkpoint、三轮 DAgger archive、fixture 0–3 的 matched post-contact benchmark 和 no-rod trace。
