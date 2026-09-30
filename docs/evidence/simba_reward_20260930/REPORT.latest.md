# SimbaV2 Office 奖励对照：实时报告

生成时间：2026-09-30T09:19:41.996998+00:00；阶段：complete；状态：complete。

服务器目录：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/campaign_03`

主对照为 office_task 与 metric；metric_nosmooth 是平滑项消融。以下为仿真开发评估，不宣称真实机器人部署效果。

## 实际训练预算

| 方法 | Seed | 状态 | transitions | updates | 已记录物理子步 | wall h |
|---|---:|---|---:|---:|---:|---:|
| office_task | 41001 | step_budget_complete | 100000 | 190002 | 40000000 | 1.80 |
| metric | 41001 | step_budget_complete | 100000 | 190002 | 40000000 | 1.82 |
| office_task | 41002 | step_budget_complete | 100000 | 190002 | 40000000 | 1.74 |
| metric | 41002 | step_budget_complete | 100000 | 190002 | 40000000 | 1.79 |
| office_task | 41003 | step_budget_complete | 100000 | 190002 | 40000000 | 1.73 |
| metric | 41003 | step_budget_complete | 100000 | 190002 | 40000000 | 1.78 |
| metric_nosmooth | 41001 | step_budget_complete | 100000 | 190002 | 40000000 | 1.78 |
| metric_nosmooth | 41002 | step_budget_complete | 100000 | 190002 | 40000000 | 1.81 |

**混合长度失败诊断：fixed_final 含提前终止回合。下表保留全部原始失败指标，不补齐至 55 s；不得与完整 55 s 结果简单排名。**


## 统一评测：按训练 seed 汇总

每个 seed 先对相同评测条件求均值，再对独立训练 seed 等权统计。RMSE 单位 cm；力矩为每回合峰值实际 N·m；速度为每回合峰值 m/s。评测文件完备仅指 SUMMARY 写完，实际完成 55 s 单独统计；缺失时长不推测。

| 评测 | 方法 | Seed | episodes | 评测文件完备 | 完整55s/总数 | 提前abort | 实际时长s | RMSE cm | 峰值力矩 | 峰值速度 | strict | task | physical |
|---|---|---:|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| fixed_final | metric | 41001 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 20.600 | 48.908 | 0.1879 | 0.000 | 0.000 | 0.333 |
| fixed_final | metric | 41002 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 17.576 | 56.910 | 0.3147 | 0.000 | 0.000 | 0.167 |
| fixed_final | metric | 41003 | 6 | True | 5/6 | 1 | 55.00, 17.64, 55.00, 55.00, 55.00, 55.00 | 23.438 | 48.211 | 0.3226 | 0.000 | 0.000 | 0.333 |
| fixed_final | office_task | 41001 | 6 | True | 5/6 | 1 | 55.00, 55.00, 38.72, 55.00, 55.00, 55.00 | 49.672 | 49.156 | 0.4655 | 0.000 | 0.000 | 0.833 |
| fixed_final | office_task | 41002 | 6 | True | 1/6 | 5 | 21.32, 21.52, 21.48, 55.00, 20.04, 20.92 | 56.307 | 51.966 | 0.3987 | 0.000 | 0.000 | 0.167 |
| fixed_final | office_task | 41003 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 74.022 | 64.227 | 0.3883 | 0.000 | 0.000 | 1.000 |
| test | metric | 41001 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 4.190 | 37.770 | 0.1742 | 0.000 | 0.000 | 1.000 |
| test | metric | 41002 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 6.807 | 36.479 | 0.1437 | 0.000 | 0.000 | 1.000 |
| test | metric | 41003 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 1.825 | 38.913 | 0.1329 | 0.000 | 0.000 | 1.000 |
| test | metric_nosmooth | 41001 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 2.857 | 40.908 | 0.1104 | 0.000 | 0.000 | 1.000 |
| test | metric_nosmooth | 41002 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 2.984 | 42.672 | 0.1704 | 0.000 | 0.000 | 1.000 |
| test | office_task | 41001 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 5.291 | 33.016 | 0.1093 | 0.000 | 0.000 | 1.000 |
| test | office_task | 41002 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 11.162 | 36.814 | 0.0521 | 0.000 | 0.000 | 1.000 |
| test | office_task | 41003 | 6 | True | 6/6 | 0 | 55.00, 55.00, 55.00, 55.00, 55.00, 55.00 | 15.007 | 55.988 | 0.1193 | 0.000 | 0.000 | 1.000 |

## Seed 均值 ± 样本标准差

| 评测 | 方法 | 独立 seeds | 完整55s/总数 | 提前abort | 解释范围 | RMSE cm | 峰值力矩 N·m | 峰值速度 m/s |
|---|---|---:|---:|---:|---|---:|---:|---:|
| fixed_final | metric | 3 | 17/18 | 1 | mixed_length_failure_diagnostic | 20.5381 ± 2.9316 | 51.3428 ± 4.8341 | 0.2751 ± 0.0756 |
| fixed_final | office_task | 3 | 12/18 | 6 | mixed_length_failure_diagnostic | 60.0004 ± 12.5882 | 55.1167 ± 8.0142 | 0.4175 ± 0.0419 |
| test | metric | 3 | 18/18 | 0 | full_55s_descriptive | 4.2742 ± 2.4923 | 37.7209 ± 1.2178 | 0.1503 ± 0.0214 |
| test | metric_nosmooth | 2 | 12/12 | 0 | full_55s_descriptive | 2.9203 ± 0.0895 | 41.7902 ± 1.2472 | 0.1404 ± 0.0424 |
| test | office_task | 3 | 18/18 | 0 | full_55s_descriptive | 10.4868 ± 4.8930 | 41.9397 ± 12.3139 | 0.0936 ± 0.0363 |

评测文件尚未完备的 seed 不进入上述跨 seed 统计；文件已写完但提前物理终止的失败仍全部保留，不能称作完整55s回合。n≤3 不给出夸大的显著性或置信区间结论。

## 待完成与异常

- fixed_final: 混合长度失败诊断。包含提前终止回合；原始 RMSE/峰值只覆盖实际运行时长，不能与完整 55 s 回合简单排名。失败全部保留，未补齐或填补指标。

## 解释边界

- This is Office simulation, not real FR3 hardware validation or a blind previously unseen benchmark.
- RMSE uses current task-stage waypoint and all physical substeps; no post-contact-only metric is silently substituted.
- Means include failures and physically invalid episodes; physical validity, task and strict success remain separate.
- Evaluation file completion is not physical-horizon completion. Early-abort RMSE/peaks cover actual observed duration only; mixed lengths are failure diagnostics, not directly comparable full-55s rankings.
- Peak torque is actual qfrc_actuator Nm; group value is mean of per-episode maxima, not one global maximum.
- Peak velocity is a maximum, not P95. Lower speed/torque alone can indicate stalling rather than better control.
- Different reward totals are not comparable performance scores; never rank reward groups by total return.
- Training dt and formal evaluation dt may differ; source/model/fixture hashes and both timesteps must be retained.
- Fixed-budget and validation-selected checkpoint results are separate. Missing fixed-final results are not replaced by arbitrary selected checkpoints.
- Unequal achieved transitions, update counts or physical substep budgets limit causal comparison; report actual budgets.
- Zero successes or flat short learning curves do not prove inherent algorithm weakness or convergence.
- Three or fewer training seeds allow descriptive uncertainty only; episodes are not independent learner seeds.

曲线数据在 learning_curves.csv；逐评测回合 episodes.csv；逐训练 seed per_seed.csv；跨 seed across_seed.csv；实际预算 budgets.csv。恢复/停滞需结合阶段、完整任务成功率和录像诊断，不能只看总 reward。
