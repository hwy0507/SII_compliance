# 15小时本机teacher→student进展

更新时间：2026-10-13T00:01:28.830522+00:00；阶段：teacher_data_complete。

Baseline完整表先审计，然后才采集/训练；新数据与模型结果不得当作封存泛化成绩。

```json
{
  "execution": {
    "status": "collecting",
    "started_utc": "2026-10-12T13:45:02.122548+00:00",
    "jobs": [],
    "server_compute": false,
    "final_test_reads": 0,
    "baseline_verified_rows": 167,
    "baseline_active": {
      "target": "/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/paired_baseline_development_20261012_v2/episodes/nominal_zero__repair_development_007",
      "unit": "sii-paired-dev-fc3589409a1e12a2",
      "started_utc": "2026-10-12T17:49:45.924210+00:00"
    },
    "updated_utc": "2026-10-13T00:01:22.066859+00:00",
    "active": null,
    "baseline_completed_utc": "2026-10-12T17:56:16.164697+00:00",
    "baseline_report_sha256": "e6938945b4b2ff1d8ee562027a35272dbb23a582d6a28fc6ba6f1d6194affcc7",
    "collection_completed": 50
  },
  "archive": {
    "status": "verified",
    "receipt": {
      "verified_utc": "2026-10-13T00:01:27.656756+00:00",
      "files_verified": 985,
      "total_bytes": 52340205,
      "manifest_sha256": "d8adb1f98f31565adf4adbd3990eba03f676c8491aa7bcfa83641479b77d15ab",
      "actual_compute_host": "airpig",
      "local_execution_root": "/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/teacher_student_15h_20261012_v3/delivery_teacher_data_complete/evidence",
      "published_evidence": "/home/arm1/sii_shared/SII_compliance/runs/main/teacher_student_15h_20261012_v3_teacher_data_complete/evidence",
      "historical_execution_paths_preserved": true
    }
  }
}
```

数据：44训练身份、11验证身份，75625实际控制帧；teacher混合=True。


# 同一八条件开发比较

Shared development cohort, not final/heldout generalization or equal training budget. No new training. Original gates unchanged.

|方法|已评/计划|Task|Strict|RMSE mm|回合峰矩均值 Nm|回合峰速均值 m/s|早停|
|---|---:|---:|---:|---:|---:|---:|---:|
| esn | 8/8 | 7/8 | 2/8 | 29.5474 | 49.1958 | 0.3588 | 0 |
| matched_rnn | 8/8 | 6/8 | 4/8 | 31.6948 | 50.0186 | 0.3721 | 0 |
| matched_mlp | 8/8 | 4/8 | 3/8 | 39.7290 | 46.7197 | 0.3757 | 0 |
| ordinary_rnn | 8/8 | 3/8 | 3/8 | 37.7017 | 47.1819 | 0.3958 | 0 |
| ordinary_mlp | 8/8 | 4/8 | 4/8 | 45.5801 | 46.7726 | 0.3709 | 0 |
| memoryless | 8/8 | 3/8 | 2/8 | 34.3487 | 45.8966 | 0.3707 | 0 |
| enhanced_teacher | 8/8 | 7/8 | 6/8 | 35.2676 | 50.8158 | 0.3868 | 0 |
| nominal_zero | 8/8 | 0/8 | 0/8 | 26.6828 | 37.2374 | 0.3707 | 0 |
| vmc_boundary_00 | 8/8 | 0/8 | 0/8 | 26.9039 | 38.5904 | 0.3754 | 0 |
| vmc_boundary_05 | 8/8 | 0/8 | 0/8 | 26.1845 | 38.5237 | 0.3739 | 0 |
| admittance_boundary_06 | 8/8 | 0/8 | 0/8 | 39.9990 | 37.6189 | 0.3730 | 0 |
| admittance_boundary_07 | 8/8 | 0/8 | 0/8 | 25.2242 | 39.1063 | 0.3677 | 0 |
| impedance_boundary_02 | 8/8 | 0/8 | 0/8 | 24.5271 | 35.9253 | 0.3795 | 0 |
| impedance_boundary_01 | 8/8 | 0/8 | 0/8 | 24.8610 | 34.8339 | 0.3737 | 0 |
| direct_office_task | 8/8 | 0/8 | 0/8 | 20.0881 | 40.5305 | 0.3447 | 0 |
| parameter_impedance | 8/8 | 0/8 | 0/8 | 21.3522 | 50.1361 | 0.3752 | 0 |
| parameter_admittance | 8/8 | 0/8 | 0/8 | 27.2407 | 40.0549 | 0.3799 | 0 |
| parameter_vmc | 8/8 | 0/8 | 0/8 | 28.9559 | 37.7555 | 0.3722 | 0 |
| direct_metric | 8/8 | 0/8 | 0/8 | 225.3267 | 53.8866 | 0.3570 | 0 |
| direct_office_task_historical_entropy | 8/8 | 0/8 | 0/8 | 66.6966 | 51.0039 | 0.1849 | 8 |
| parameter_impedance_historical_entropy | 8/8 | 0/8 | 0/8 | 23.7954 | 37.5415 | 0.3793 | 0 |

失败均计入分母；早停的连续指标只覆盖实际时长，不与完整55秒直接判优。

## 接触窗口柔顺指标（描述性，需同时看接触覆盖和任务成功）

|方法|人手P95 N / 接触回合|棍P95 N / 接触回合|桌角P95 N / 接触回合|人手冲量 N·s|棍冲量 N·s|人手恢复/暴露|棍恢复/暴露|
|---|---:|---:|---:|---:|---:|---:|---:|
| esn | 13.497 / 8 | 17.258 / 8 | 7.057 / 8 | 29.279 | 32.097 | 5/8 | 1/8 |
| matched_rnn | 13.182 / 8 | 16.567 / 8 | 11.616 / 8 | 30.878 | 31.935 | 6/8 | 1/8 |
| matched_mlp | 25.610 / 8 | 17.154 / 8 | 6.477 / 8 | 74.743 | 39.258 | 1/8 | 3/8 |
| ordinary_rnn | 30.728 / 8 | 14.547 / 8 | 11.477 / 8 | 68.839 | 40.311 | 0/8 | 0/8 |
| ordinary_mlp | 44.094 / 8 | 15.855 / 8 | 5.277 / 8 | 122.108 | 37.685 | 1/8 | 0/8 |
| memoryless | 16.116 / 8 | 30.839 / 8 | 6.030 / 8 | 37.647 | 26.368 | 1/8 | 0/8 |
| enhanced_teacher | 24.819 / 8 | 16.279 / 8 | 8.498 / 8 | 60.843 | 35.857 | 3/8 | 0/8 |
| nominal_zero | 12.392 / 8 | 11.820 / 8 | 10.660 / 8 | 36.173 | 59.014 | 7/8 | 3/8 |
| vmc_boundary_00 | 11.869 / 8 | 10.652 / 8 | 9.530 / 8 | 33.418 | 50.417 | 7/8 | 6/8 |
| vmc_boundary_05 | 11.029 / 8 | 13.392 / 8 | 9.942 / 8 | 34.147 | 57.272 | 7/8 | 0/8 |
| admittance_boundary_06 | 38.678 / 8 | 11.588 / 8 | 10.052 / 8 | 87.280 | 35.809 | 0/8 | 8/8 |
| admittance_boundary_07 | 9.279 / 8 | 32.071 / 8 | 12.490 / 8 | 29.656 | 8.953 | 7/8 | 0/8 |
| impedance_boundary_02 | 16.357 / 8 | 250.099 / 3 | 7.765 / 8 | 47.886 | 0.086 | 8/8 | 0/3 |
| impedance_boundary_01 | 17.021 / 8 | 286.018 / 2 | 6.889 / 8 | 49.537 | 0.037 | 8/8 | 0/2 |
| direct_office_task | 33.510 / 8 | 18.889 / 8 | 23.127 / 4 | 85.272 | 68.467 | 0/8 | 0/8 |
| parameter_impedance | 24.882 / 8 | NA / 0 | 38.396 / 8 | 62.540 | 0.000 | 8/8 | 0/0 |
| parameter_admittance | 9.912 / 8 | 33.476 / 8 | 10.419 / 8 | 29.939 | 10.517 | 7/8 | 0/8 |
| parameter_vmc | 12.861 / 8 | 11.067 / 8 | 8.274 / 8 | 36.134 | 42.750 | 7/8 | 2/8 |
| direct_metric | 32.232 / 8 | 97.005 / 3 | NA / 0 | 39.805 | 0.438 | 0/8 | 0/3 |
| direct_office_task_historical_entropy | NA / 0 | NA / 0 | 52.778 / 8 | 0.000 | 0.000 | 0/0 | 0/0 |
| parameter_impedance_historical_entropy | 15.932 / 8 | 158.244 / 1 | 17.668 / 8 | 47.240 | 0.077 | 8/8 | 0/1 |

P95列为各实际接触回合P95的均值；冲量按全部8回合实际窗口均值，非接触为真实零冲量。
未观测到恢复者按既定窗口删失；未接触不作为恢复失败。此表不是相同接触轨迹的因果排名。
所有逐回合接触/冲量/恢复指标保留在REPORT.json rows[].metrics；缺接触与删失不填零。
经典两候选、RL两个熵附组全部展示；不能把开发调参成绩称为盲测或RL收敛。

