# Direct ESN matched post-contact benchmark（2026-08-17）

## 目的

本 benchmark 固定同一 Panda grasp 任务、fixture `0`、seed `20260817`，将首次碰撞与碰撞后的回归拆开度量：

1. `contact_onset/release`：由离线 trace 的 rod–hand force（阈值 `0.2 N`）定义；不进入 Direct ESN 在线输入。
2. `contact impulse`：直接累积环境每个 action 周期中的物理 `contact_impulse_delta_ns`，不从 action-level 峰力近似积分。
3. `post-contact RMSE / IAE`：从实际接触释放至抓取时刻的名义轨迹偏差。
4. `rejoin`：实际释放后，连续 3 个 40 ms action 点均处于 `5 mm` 内的首次时刻。
5. 同时保留预定杆回撤时刻（`1.695 s`）的 rejoin latency，便于与旧 phase 报告对照。

## 物理时间点

| 项目 | 值 |
|---|---:|
| 实际接触 onset | 1.20 s |
| 实际接触 release | 1.32 s |
| 杆的预定回撤结束 | 1.695 s |
| 抓取阶段开始 | 2.40 s |

## 严格 matched 结果

所有方法均满足：task success、effective collision、finite state，且没有 hard torque limit。

| 方法 | contact impulse (N·s) | peak deviation (mm) | post-contact RMSE (mm) | post-contact IAE (mm·s) | actual release→rejoin (s) | scheduled release→rejoin (s) | peak recovery jerk (m/s³) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fixed WBC | 0.9031 | **12.37** | **8.82** | **8.73** | **0.88** | **0.505** | **6.10** |
| counterfactual Direct ESN `b864` | **0.8977** | 12.79 | 9.64 | 9.85 | 1.16 | 0.785 | 29.45 |
| error-aligned / canonicalized ESN | **0.8955** | 56.93 | 9.79 | 9.97 | 1.16 | 0.785 | 27.91 |

## 判定

- `b864` 仅在冲量上有很小下降（约 `0.59%`），但 post-contact RMSE、IAE、两种 rejoin latency 和 recovery jerk 都差于 Fixed WBC。因此它是一个稳定的 DAgger smoke checkpoint，**不是可声称优于 baseline 的模型**。
- error-aligned/canonicalized ESN 的全程峰值偏离达到 `56.93 mm`，属于明确失败的 ablation；该代码路径维持 opt-in，不能作为默认 Direct ESN 行为。
- 因为首次力峰与三者几乎相同（约 `19.72 N`），本场景中峰力不能作为反应式 ESN 是否有效的主指标。后续应以 post-contact RMSE、IAE、actual-release rejoin、recovery jerk 为主要优化目标，并把 impulse 作为安全约束。

## 可复现命令

```bash
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts

python evaluate_direct_esn_post_contact.py \
  --controller /home/arm1/vmc_mujoco_runtime/outputs/direct_esn_counterfactual_weight_scan_20260817/b864/direct_esn_dagger_iteration_01.npz \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie \
  --fixture-index 0 --seed 20260817 \
  --output-dir /home/arm1/vmc_mujoco_runtime/outputs/direct_esn_post_contact_benchmark_20260817/b864_exact
```

输出目录也包括 Fixed WBC 与 Direct ESN 的独立 trace，适合后续绘制 2D trajectory、force、speed、torque 和 phase 图。
