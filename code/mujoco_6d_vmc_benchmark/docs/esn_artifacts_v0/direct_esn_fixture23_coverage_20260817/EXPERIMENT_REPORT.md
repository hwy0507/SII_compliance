# Fixture 2/3 teacher coverage + 随机化训练实验（2026-08-17，v2 多 seed 统计版）

## 目的

执行 HANDOFF.md 优先级 1/2/3：

1. 补强 fixture 2/3 强碰撞区域的 teacher coverage；
2. 建立真正的随机化训练分布；
3. 按正式 selection gate 判定候选模型并做多 seed 统计。

v2 修订：v1 报告中「seed 251 DAgger iter2 通过 gate」来自对 9 个 (seed, iteration) 组合做
held-out fx3 扫描后挑最优，属于测试集选择偏差，**不能作为正式结果**。本版改用统一协议：
iteration 只用 train fixtures 选择，fx3 只报告。结论因此修正。

## 方法

### 代码改动

- `scripts/run_direct_esn_mujoco.py`：`--rod-stroke-m / --rod-height-m / --rod-start-time-s /
  --grasp-time-s` fixture override；summary 记录 `override_fixture`。
- `scripts/run_direct_esn_dagger.py`：`--dagger-fixtures`（`stroke,height,start;...`）自定义随机化
  rod pool；summary 记录 `dagger_fixture_pool`，archive 记录 `rollout_fixture`。

### Reference 稳定边界

deterministic reference（formal multifixture seed_20260907 iteration_03）：stroke ≤ 0.176 全部
task success（timing 1.062–1.108、height 0.5395–0.5435），stroke ≥ 0.178 task fail。
fixture 3（0.175）在稳定边界内侧。

### Expert trace 网格（19 rod + 1 no-rod，全部 task success）

fixture 2 邻域：stroke {0.170,0.172,0.174,0.176} × start {1.062,1.085,1.108}（height 0.541，12 条）
+ height 变化 4 条 + default f0/f1/f2 3 条；impulse 覆盖 0.90–3.11 N·s。
无任何组合等于 held-out fixture 3 (0.175, 0.542, 1.100)。

### 训练管线（8 个 reservoir seeds：13, 42, 71, 137, 251, 307, 512, 1009）

1. Bootstrap：stable-reference coverage BC（`washout 3 / rod-repeat 4 / neutral-repeat 4`）。
2. DAgger：8-fixture 随机化 pool（default f0/f1/f2 + 0.176/0.541/1.085、0.176/0.5395/1.062、
   0.176/0.5425/1.108、0.174/0.541/1.096、0.172/0.5435/1.070），counterfactual h24 /
   nonzero-repeat 8 / dilation 0 / prior 100，3 iterations。
3. 统一选择协议：iteration 仅用 train fixtures 0/1/2 的平均 ΔRMSE 选择；fx3 与 no-rod 只评估报告。

## 结果

### Bootstrap-stage must gate

8/8 seeds 通过（no-rod task success、无 hard torque、mean yield < 0.005 m/s、全部 fixture
task success + stable rejoin）。

### 统一协议 8-seed 统计（Fixed WBC → ESN）

Post-contact ΔRMSE（mm，mean±std；负为改善）：

| 模型 | fx0 (train) | fx1 (train) | fx2 (train) | fx3 (held-out) |
|---|---:|---:|---:|---:|
| **Bootstrap BC-only（n=8）** | −0.982±0.011 | −2.600±0.011 | −3.313±0.015 | **−2.207±0.034** |
| DAgger iter1（train-selected，n=8） | −0.678±0.074 | −1.850±0.071 | −1.892±0.078 | **+1.146±0.390** |
| deterministic reference（单模型） | −1.041 | −2.650 | −3.506 | −2.397 |

Rejoin latency（s）与 recovery jerk（m/s³）：

| 模型 | fx0 | fx1 | fx2 | fx3 |
|---|---:|---:|---:|---:|
| BC-only rejoin | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| BC-only recjerk | 10±1 | 64±5 | 133±4 | 127±3 |
| reference rejoin | 0.80 | 0.60 | 0.48 | 0.64 |
| reference recjerk | 11 | 86 | 136 | 119 |

No-rod：BC-only mean yielding twist 0.00100±0.00000 m/s（8/8）；DAgger iter1 同为
0.00100 量级（0.00053–0.00068）。

### Selection gate 判定

- **Bootstrap BC-only：8/8 seeds 通过完整 gate（must 项 + held-out RMSE 优先项）**，
  seed 间方差 ±0.034 mm，是正式的随机化 proposed 方法。
- DAgger（随机 pool counterfactual）：8/8 seeds 在 held-out fx3 恶化（+0.55 ~ +1.59 mm，
  mean +1.146±0.390），train-only 协议下全部违反「RMSE 不高于 Fixed WBC」优先项 →
  **记录为负结果（见失败方向 F）**。
- v1 的 seed251-it2（fx3 −3.214）为 held-out 扫描选择偏差产物，仅作探索性参考，不进入正式结果。

## 结论

1. **随机 reservoir robustness 的解 = stable-reference coverage BC**：19+1 条覆盖
   stroke/timing/height 的 expert traces 让 8 个独立 reservoir 全部以极小方差复现
   reference 水平（held-out −2.207±0.034 mm vs reference −2.397 mm）。
2. **随机 pool counterfactual DAgger 在此设置下是净负贡献**：iteration 1 即把 held-out
   ΔRMSE 从 −2.2 拉到 +1.1，且随 iteration 单调劣化（train fixtures 上亦然）。
   机理推测：pool 中 5/8 为强碰撞 fixture，counterfactual nonzero 标签（repeat=8 加权）
   把 readout 拉向过强 yield，破坏 BC 学到的与 teacher 参数化一致的低误差行为；
   proximal prior 100 不足以约束。若要复活 DAgger，需要标签权重按碰撞强度归一、或
   pool 强度分布匹配 default fixtures，或仅对 student 明显偏离 teacher 的状态打标。
3. 论文建议叙事：proposed = Direct ESN coverage BC（8-seed 统计），deterministic
   reference 作为单 reservoir 上界对照，DAgger 负结果写入 ablation。

## 服务器路径

- 输出根目录：`/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817/`
  - `expert_traces/`（19 rod + no-rod + manifest.json）
  - `bootstrap/`（8 seeds）、`bootstrap_gate/gate_summary.json`
  - `dagger_seed_{13,42,71,137,251,307,512,1009}/`
  - `iter_train_select/selection_summary.json`（train-only iteration 选择）
  - `iter1_holdout/iter1_holdout_summary.json`（DAgger iter1 held-out）
  - `multiseed_statistics.json`（本表数据源）
- **正式随机化候选 checkpoints**：`bootstrap/bootstrap_seed_{13,42,71,137,251,307,512,1009}.npz`
  （8 个独立 reservoir，全部通过 gate）
