# Independent ESN domain-randomized result（服务器 MuJoCo，2026-08-22）

## 最终结论

本轮把 ESN 作为独立方法训练：从零 readout 开始，固定随机 reservoir，通过自身 MuJoCo rollout return 做 antithetic random-search；没有读取 VMC checkpoint、VMC teacher trace、VMC action 或 VMC 参数。最终 v4 训练覆盖低/高板位、软/硬接触和 0/40/80 ms residual delay，随后在 16 条全新条件上评测。

| 方法 | 成功率 | 物理审计 | Pre 峰值力 N | Pre 冲量 N·s | Post 峰值力 N | Post 冲量 N·s | 总冲量 N·s | Peak jerk m/s³ | 最终抬升 mm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PaperMPC | 16/16 | 16/16 | 19.749 | 5.728 | 9.180 | 1.261 | 6.989 | 1007.9 | 195.47 |
| VMC | 16/16 | 16/16 | 20.123 | 6.352 | 9.049 | 0.990 | 7.342 | 1027.3 | 199.22 |
| MLP（旧 BC） | 6/16 | 6/16 | 26.249 | 5.892 | 7.000 | 0.590 | 6.482 | 1360.2 | 213.83 |
| ESN v4 independent | **16/16** | **16/16** | 20.610 | 6.239 | **8.066** | 1.139 | 7.377 | **1006.1** | 198.70 |

所有 16 条 ESN 条件均无初始板接触、无物块—板接触，双阶段 contact 顺序正确，penetration 审计通过。MLP 的 10 条失败都是第二阶段没有满足目标板接触，而不是“穿模成功”。

## ESN vs VMC 配对统计

16 个 matched confirmatory conditions，20,000 次 bootstrap：

- pre peak force：ESN 高 0.487 N，95% CI `[0.216, 0.744]`；
- pre impulse：ESN 低 0.114 N·s，95% CI `[-0.196, -0.037]`；
- post peak force：ESN 低 0.984 N，95% CI `[-1.296, -0.632]`；
- post impulse：ESN 高 0.149 N·s，95% CI `[0.075, 0.217]`；
- peak jerk：ESN 低 21.2 m/s³，CI 跨 0；
- final lift：ESN 低 0.52 mm，CI 跨 0；
- 五指标等权柔顺比值：`1.1164`，95% CI `[1.0079, 1.2605]`，越低越好。

## 科研解释

v4 的关键改进是任务鲁棒性：在更宽域随机化下，独立 ESN 保持 16/16 双阶段成功，且搬运高度与 VMC 基本一致。它对 post-contact peak force 和 peak jerk 有优势，但 pre peak force、post impulse 和总五指标综合分数没有胜过 VMC。因此不能声称 ESN 在当前 protocol 下全面优于 VMC。

之前的独立 ESN v1/v2 在较窄协议上具有更强的柔顺指标优势，但 v1/v2 在低板位边界会出现绕过第二块板或抬升损失。v3 用 lift floor 改善了高度，却仍在两个 confirmatory 边界条件上漏掉 post contact。v4 通过域随机训练修复了这个问题，但 Pareto 代价是冲量优势消失。

最终应汇报为：ESN 是一个独立、物理有效、鲁棒完成双阶段接触的 proposed controller；它在后阶段峰值力和时序平滑上优于 VMC，但不存在对 VMC 的全指标统治。下一步若要追求全面胜出，应研究多目标 constrained policy search / contact-aware curriculum，而不是继续手工调单一 reward 权重。

## 文件

- [v4 checkpoint](esn_ars_independent_best.npz)
- [v4 training summary](ars_summary.json)
- [v4 final four-method JSON](final_four_method.json)
- [v4 paired statistics](final_stats.json)
- [v4 development physics gate](development_gate.json)
- 训练入口：[train_dual_phase_esn_ars.py](/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709-paper-mpc-baseline/code/mujoco_6d_vmc_benchmark/scripts/train_dual_phase_esn_ars.py)
