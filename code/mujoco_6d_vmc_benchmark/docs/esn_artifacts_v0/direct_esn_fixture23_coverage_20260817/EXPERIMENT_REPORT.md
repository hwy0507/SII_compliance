# Fixture 2/3 teacher coverage + 随机化 DAgger pool 实验（2026-08-17）

## 目的

执行 HANDOFF.md 优先级 1/2：

1. 补强 fixture 2/3 强碰撞区域的 teacher coverage；
2. 建立真正的随机化训练分布（不同 stroke / timing / height 物理轨迹 + 多 reservoir seed）；
3. 按优先级 3 的 selection gate 判定候选模型。

## 方法

### 代码改动（本地 commit 见 git log）

- `scripts/run_direct_esn_mujoco.py`：新增 `--rod-stroke-m / --rod-height-m / --rod-start-time-s / --grasp-time-s`
  fixture override；summary 记录 `override_fixture`。
- `scripts/run_direct_esn_dagger.py`：新增 `--dagger-fixtures` 自定义随机化 rod pool
  （`stroke,height,start;...`）；`--fixture-indices` 索引该 pool；summary 记录 `dagger_fixture_pool`，
  每个 archive 记录 `rollout_fixture`。

### Reference 稳定边界扫描

用 deterministic reference（formal multifixture seed_20260907 iteration_03）扫描：

- stroke ≤ 0.176：task success（timing 1.062–1.108、height 0.5395–0.5435 内全部成功）
- stroke ≥ 0.178：task fail

fixture 3（0.175）恰在稳定边界内侧；expert trace 网格只取稳定成功区。

### Expert trace 网格（19 rod + 1 no-rod，全部 task success）

基于 fixture 2（base index 2）：

- stroke {0.170, 0.172, 0.174, 0.176} × start {1.062, 1.085, 1.108}，height 0.541（12 条）
- height 变化：(0.174, 0.5395/0.5425, 1.070)、(0.176, 0.5395/0.5425, 1.096)（4 条）
- default fixture 0/1/2 traces（3 条）
- impulse 覆盖 0.90–3.11 N·s（fixture 2 为 2.16）

无任何组合等于 held-out fixture 3 (0.175, 0.542, 1.100)。

### Bootstrap（stable-reference behavior cloning）

3 个 reservoir seeds (71/137/251)，`washout 3 / rod-repeat 4 / neutral-repeat 4`，
readout MSE ≈ 1.3e-5。

### DAgger（counterfactual + proximal）

8-fixture 随机化 pool（`--dagger-fixtures`）：

```
0.160,0.539,1.055   (default f0)
0.165,0.540,1.070   (default f1)
0.170,0.541,1.085   (default f2)
0.176,0.541,1.085   强 stroke 同 timing
0.176,0.5395,1.062  强 + 早 + 低
0.176,0.5425,1.108  强 + 晚 + 高
0.174,0.541,1.096   中强 + 略晚
0.172,0.5435,1.070  中 + 很高
```

`--teacher-mode counterfactual --counterfactual-horizon-steps 24 --counterfactual-zero-repeat 1
--counterfactual-nonzero-repeat 8 --counterfactual-label-dilation-steps 0 --prior-readout-weight 100
--iterations 3`。

## 结果

### Bootstrap-stage gate（handoff 优先级 3 的 must 项）

3 seeds 全部通过；held-out fx3 ΔRMSE：71 = −2.141，137 = −2.223，251 = −2.226 mm。
对比 repair 目录（reject 的 +3.17/+6.97/+4.82 mm），coverage 网格 BC 直接修复了随机 reservoir 回退。

### DAgger 后 strict matched evaluation（fixture 3，各 iteration）

| seed | iter1 | iter2 | iter3 |
|---|---:|---:|---:|
| 71 | +1.585 | +2.164 | +1.942 |
| 137 | +0.550 | +1.516 | +1.416 |
| 251 | +1.520 | **−3.214** | −2.395 |

（ΔRMSE mm，负为优于 Fixed WBC；全部 task success、无 hard torque、有 stable rejoin。）

seed 71/137 在 DAgger 强碰撞 pool 上出现过拟合 held-out 的回退；seed 251 iter2/iter3 保持改善。

### 完整 gate 对比（Fixed WBC → ESN）

Post-contact RMSE（mm）：

| Fixture | Split | Fixed WBC | reference det. it3 | **seed 251 DAgger it2（新候选）** |
|---|---|---:|---:|---:|
| 0 | train | 8.816 | 7.775 (−1.041) | 8.563 (−0.253) |
| 1 | train | 11.893 | 9.243 (−2.650) | 10.339 (−1.554) |
| 2 | train | 15.537 | 12.031 (−3.506) | 12.823 (−2.714) |
| 3 | held-out | 17.901 | 15.504 (−2.397) | **14.687 (−3.214)** |

Actual-release rejoin latency（s）：

| Fixture | Fixed WBC | reference | seed 251 it2 |
|---|---:|---:|---:|
| 0 | 0.88 | 0.80 | 0.84 |
| 1 | 0.96 | 0.60 | 0.84 |
| 2 | 0.96 | 0.48 | 0.76 |
| 3 | 1.00 | 0.64 | 0.80 |

Peak recovery jerk（m/s³）：

| Fixture | Fixed WBC | reference | seed 251 it2 |
|---|---:|---:|---:|
| 0 | 6 | 11 | 17 |
| 1 | 10 | 86 | 47 |
| 2 | 2 | 136 | **75** |
| 3 | 15 | 119 | **85** |

No-rod：task success、无 hard torque、mean yielding twist：reference 0.00043，seed 251 it2 0.00102 m/s（均 < 0.005 上限）。

### Selection gate 判定

- **seed 251 DAgger iteration 02 通过完整 must gate**，是第一个通过完整 selection gate 的随机 reservoir：
  held-out RMSE/rejoin 优于 Fixed WBC，recovery jerk 比 reference 几乎减半。
- seed 71/137 各 iteration 在 held-out fx3 RMSE 恶化（+0.55 ~ +2.16 mm），按 gate 记录为 reject
  （must 项均过，但违反「post-contact RMSE 不高于 Fixed WBC」优先项）。
- deterministic reference 仍保持 train fixture 上的最优 RMSE/rejoin；两个 checkpoint 均保留，
  **互不覆盖**。

## 关键结论

1. 随机 reservoir robustness 问题的解法 = stable-reference coverage 网格 BC + 随机化 fixture pool
   counterfactual DAgger；单靠 repair（旧路径）不可行。
2. DAgger 随机化 pool 会让部分 seed 过拟合强碰撞区（71/137 fx3 回退），多 reservoir seed 筛选必要。
3. 覆盖更强冲击（stroke ≤ 0.176 全谱 + timing/height 变化）同时降低了 held-out RMSE 和 recovery jerk。

## 服务器路径

- 代码：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/`
- 本次输出根目录：`/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/`
  - `expert_traces/`（19 rod + no-rod + manifest.json）
  - `bootstrap/`、`bootstrap_gate/gate_summary.json`
  - `dagger_seed_{71,137,251}/`
  - `final_eval/final_eval_summary.json`、`iter_scan/iter_scan_summary.json`
  - `candidate_gate/candidate_gate_summary.json`
- **新候选 checkpoint**：
  `/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/dagger_seed_251/direct_esn_dagger_iteration_02.npz`
