# 公平性修正：实时状态

2026-10-13T21:24:19.225332+00:00；parallel_v4_parallel_condition_prospective_20261013_acceptance_007；状态 `prospective_evaluation`。

本机动态内存准入、最多4独立CPU核、每worker1线程/禁swap；完整保留39拟合/288回合原协议，服务器只归档。

```json
{
  "archive": {
    "status": "verified",
    "receipt": {
      "verified_utc": "2026-10-13T21:24:18.091448+00:00",
      "files_verified": 1192,
      "total_bytes": 10221886,
      "manifest_sha256": "cad9a94f82ada6dd560c63aaa5d613cbbdd5283a022169adbfbe6a6dfcff4ffa",
      "actual_compute_host": "airpig",
      "local_execution_root": "/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/fair_comparison_20261013_v2/delivery_parallel_v4_parallel_condition_prospective_20261013_acceptance_007/evidence",
      "published_evidence": "/home/arm1/sii_shared/SII_compliance/runs/main/fair_comparison_20261013_v2_parallel_v4_parallel_condition_prospective_20261013_acceptance_007/evidence",
      "historical_execution_paths_preserved": true
    }
  },
  "execution": {
    "status": "prospective_evaluation",
    "started_utc": "2026-10-13T04:50:33.752087+00:00",
    "jobs": [],
    "server_compute": false,
    "final_test_reads": 0,
    "registration_sha256": "a2e80a62252e97af7137ded2962a5790087d8154e2e01c52d0d7a305b2f44b64",
    "updated_utc": "2026-10-13T21:24:15.350968+00:00",
    "active": null,
    "dispatcher": "dispatch_v4",
    "handoff_completed_utc": "2026-10-13T05:38:09.564858+00:00",
    "previous_execution_sha256": "1cc60991a5099119031f3db461419da3ca1476ffdff770b77c99292d919df968",
    "fits_complete": 39,
    "model_lock_sha256": "4da573485533ad1d7a7d0a026ee8a33a46812e6f7dcb517ae3b2c632a652f3ab",
    "active_jobs": {
      "1": {
        "cap": 2415919104,
        "cpu": 6,
        "unit": null,
        "job": null,
        "started_utc": "2026-10-13T21:24:14.039181+00:00"
      }
    },
    "evaluated": 288,
    "expected": 288,
    "neural_memory_cap_bytes": 2415919104,
    "pilot_peak_bytes": 1159131136
  }
}
```

# 前瞻性同条件比较

Same prospective8 and frozen39fit/36model lock; resource-only local parallel dispatch. Same science as serial protocol, no test-based model changes.

|方法/seed|已评/8|Task|Strict|RMSE mm|峰矩均值 Nm|峰速均值 m/s|早停|
|---|---:|---:|---:|---:|---:|---:|---:|
| esn_gradient_s2026101301 | 8/8 | 0/8 | 0/8 | 41.0349 | 41.0416 | 0.3760 | 0 |
| esn_gradient_s2026101302 | 8/8 | 0/8 | 0/8 | 44.4743 | 41.4299 | 0.3763 | 0 |
| esn_gradient_s2026101303 | 8/8 | 5/8 | 5/8 | 47.1445 | 46.4757 | 0.3678 | 0 |
| rnn_scratch_s2026101301 | 8/8 | 1/8 | 1/8 | 41.2611 | 42.5135 | 0.3763 | 0 |
| rnn_scratch_s2026101302 | 8/8 | 0/8 | 0/8 | 41.5592 | 41.6031 | 0.3665 | 0 |
| rnn_scratch_s2026101303 | 8/8 | 3/8 | 3/8 | 31.4982 | 44.6362 | 0.3732 | 0 |
| mlp_scratch_s2026101301 | 8/8 | 1/8 | 1/8 | 44.9822 | 42.0361 | 0.3643 | 0 |
| mlp_scratch_s2026101302 | 8/8 | 2/8 | 1/8 | 47.4623 | 44.8409 | 0.3660 | 0 |
| mlp_scratch_s2026101303 | 8/8 | 1/8 | 0/8 | 41.2899 | 42.7493 | 0.3781 | 0 |
| esn_ridge_s2026101301 | 8/8 | 6/8 | 4/8 | 32.7370 | 49.2091 | 0.3727 | 0 |
| esn_ridge_s2026101302 | 8/8 | 5/8 | 3/8 | 30.6004 | 47.8353 | 0.3717 | 0 |
| esn_ridge_s2026101303 | 8/8 | 5/8 | 4/8 | 29.3747 | 48.7672 | 0.3744 | 0 |
| rnn_from_ridge_s2026101301 | 8/8 | 6/8 | 3/8 | 30.5056 | 50.2734 | 0.3729 | 0 |
| rnn_from_ridge_s2026101302 | 8/8 | 5/8 | 3/8 | 30.6004 | 47.8353 | 0.3717 | 0 |
| rnn_from_ridge_s2026101303 | 8/8 | 5/8 | 4/8 | 29.3747 | 48.7672 | 0.3744 | 0 |
| historical_admittance_boundary_06 | 8/8 | 0/8 | 0/8 | 41.5156 | 36.9978 | 0.3731 | 0 |
| historical_admittance_boundary_07 | 8/8 | 0/8 | 0/8 | 26.1115 | 39.0693 | 0.3647 | 0 |
| historical_direct_metric | 8/8 | 0/8 | 0/8 | 227.9903 | 53.7269 | 0.3510 | 0 |
| historical_direct_office_task | 8/8 | 0/8 | 0/8 | 18.3343 | 40.4695 | 0.3400 | 0 |
| historical_direct_office_task_historical_entropy | 8/8 | 0/8 | 0/8 | 66.6966 | 51.0039 | 0.1849 | 8 |
| historical_enhanced_teacher | 8/8 | 8/8 | 6/8 | 41.6746 | 51.4851 | 0.3857 | 0 |
| historical_esn | 8/8 | 7/8 | 5/8 | 31.2487 | 50.4295 | 0.3650 | 0 |
| historical_impedance_boundary_01 | 8/8 | 0/8 | 0/8 | 24.7685 | 35.0085 | 0.3709 | 0 |
| historical_impedance_boundary_02 | 8/8 | 0/8 | 0/8 | 24.4664 | 35.9534 | 0.3782 | 0 |
| historical_matched_mlp | 8/8 | 2/8 | 1/8 | 42.6032 | 44.0784 | 0.3773 | 0 |
| historical_matched_rnn | 8/8 | 7/8 | 5/8 | 32.1243 | 50.0277 | 0.3708 | 0 |
| historical_memoryless | 8/8 | 4/8 | 3/8 | 42.6142 | 48.1134 | 0.3728 | 0 |
| historical_nominal_zero | 8/8 | 0/8 | 0/8 | 26.6830 | 37.4201 | 0.3732 | 0 |
| historical_ordinary_mlp | 8/8 | 7/8 | 4/8 | 45.5617 | 50.0660 | 0.3691 | 0 |
| historical_ordinary_rnn | 8/8 | 4/8 | 4/8 | 37.8538 | 49.7591 | 0.3930 | 0 |
| historical_parameter_admittance | 8/8 | 0/8 | 0/8 | 27.7069 | 39.7595 | 0.3749 | 0 |
| historical_parameter_impedance | 8/8 | 0/8 | 0/8 | 21.4587 | 47.0030 | 0.3743 | 0 |
| historical_parameter_impedance_historical_entropy | 8/8 | 0/8 | 0/8 | 23.6107 | 38.6383 | 0.3759 | 0 |
| historical_parameter_vmc | 8/8 | 0/8 | 0/8 | 29.7929 | 37.9179 | 0.3747 | 0 |
| historical_vmc_boundary_00 | 8/8 | 0/8 | 0/8 | 26.9436 | 38.5306 | 0.3727 | 0 |
| historical_vmc_boundary_05 | 8/8 | 0/8 | 0/8 | 26.3636 | 38.3466 | 0.3742 | 0 |

每个新网络有3个seed，不挑最好seed。历史方法每配置仍只有既有训练seed，不能复制成3seed。
全部失败计入分母，未完成不记0/0；早停的低速度/低冲量不能当作优点。
接触P95、冲量、接触覆盖、恢复删失及原始指标均存 REPORT.json；结果不完整时不宣布排名。

|方法/seed|人手P95 N / 接触回合|棍P95 N / 接触回合|桌角P95 N / 接触回合|人手冲量 N·s|棍冲量 N·s|桌角冲量 N·s|
|---|---:|---:|---:|---:|---:|---:|
| esn_gradient_s2026101301 | 36.685 / 8 | 11.021 / 8 | 12.799 / 8 | 104.561 | 42.013 | 60.019 |
| esn_gradient_s2026101302 | 43.142 / 8 | 11.328 / 8 | 11.015 / 8 | 129.304 | 41.558 | 61.019 |
| esn_gradient_s2026101303 | 44.756 / 8 | 11.641 / 8 | 8.694 / 8 | 133.374 | 42.821 | 48.955 |
| rnn_scratch_s2026101301 | 36.194 / 8 | 13.534 / 8 | 9.852 / 8 | 106.382 | 47.127 | 46.896 |
| rnn_scratch_s2026101302 | 40.295 / 8 | 12.382 / 8 | 11.443 / 8 | 111.370 | 44.647 | 60.071 |
| rnn_scratch_s2026101303 | 12.382 / 8 | 14.334 / 8 | 7.875 / 8 | 34.095 | 29.465 | 42.044 |
| mlp_scratch_s2026101301 | 43.454 / 8 | 9.823 / 8 | 10.344 / 8 | 128.119 | 39.574 | 59.390 |
| mlp_scratch_s2026101302 | 47.617 / 8 | 13.005 / 8 | 9.509 / 8 | 131.335 | 43.722 | 58.643 |
| mlp_scratch_s2026101303 | 31.465 / 8 | 9.451 / 8 | 10.054 / 8 | 80.044 | 36.630 | 68.211 |
| esn_ridge_s2026101301 | 20.458 / 8 | 21.205 / 8 | 7.876 / 8 | 46.603 | 38.122 | 41.346 |
| esn_ridge_s2026101302 | 12.749 / 8 | 62.327 / 8 | 6.826 / 8 | 28.925 | 19.094 | 56.396 |
| esn_ridge_s2026101303 | 11.366 / 8 | 33.473 / 8 | 10.715 / 8 | 26.096 | 25.027 | 37.426 |
| rnn_from_ridge_s2026101301 | 13.518 / 8 | 13.086 / 8 | 9.903 / 8 | 28.793 | 46.018 | 46.552 |
| rnn_from_ridge_s2026101302 | 12.749 / 8 | 62.327 / 8 | 6.826 / 8 | 28.925 | 19.094 | 56.396 |
| rnn_from_ridge_s2026101303 | 11.366 / 8 | 33.473 / 8 | 10.715 / 8 | 26.096 | 25.027 | 37.426 |
| historical_admittance_boundary_06 | 42.126 / 8 | 11.380 / 8 | 10.366 / 8 | 105.254 | 45.662 | 139.797 |
| historical_admittance_boundary_07 | 11.446 / 8 | 22.178 / 8 | 11.771 / 8 | 31.794 | 23.838 | 96.251 |
| historical_direct_metric | 36.596 / 8 | 87.390 / 1 | NA / 0 | 47.465 | 0.744 | 0.000 |
| historical_direct_office_task | 35.002 / 8 | 20.549 / 8 | 25.060 / 3 | 87.739 | 89.683 | 98.508 |
| historical_direct_office_task_historical_entropy | NA / 0 | NA / 0 | 52.778 / 8 | 0.000 | 0.000 | 1.821 |
| historical_enhanced_teacher | 40.322 / 8 | 12.953 / 8 | 8.546 / 8 | 99.818 | 45.945 | 24.405 |
| historical_esn | 15.842 / 8 | 13.603 / 8 | 9.525 / 8 | 36.469 | 50.560 | 32.389 |
| historical_impedance_boundary_01 | 19.223 / 8 | 272.711 / 2 | 6.877 / 8 | 53.599 | 0.046 | 290.534 |
| historical_impedance_boundary_02 | 17.834 / 8 | 259.293 / 3 | 7.763 / 8 | 49.733 | 0.079 | 323.074 |
| historical_matched_mlp | 41.446 / 8 | 22.110 / 8 | 5.526 / 8 | 121.419 | 52.011 | 40.480 |
| historical_matched_rnn | 17.134 / 8 | 14.692 / 8 | 7.442 / 8 | 35.653 | 51.370 | 31.737 |
| historical_memoryless | 37.667 / 8 | 25.427 / 8 | 15.633 / 8 | 110.582 | 41.294 | 33.281 |
| historical_nominal_zero | 14.231 / 8 | 12.332 / 8 | 10.202 / 8 | 37.357 | 72.866 | 138.298 |
| historical_ordinary_mlp | 44.375 / 8 | 15.839 / 8 | 5.295 / 8 | 129.144 | 48.592 | 22.705 |
| historical_ordinary_rnn | 32.978 / 8 | 14.729 / 8 | 11.670 / 8 | 78.592 | 50.059 | 58.434 |
| historical_parameter_admittance | 11.830 / 8 | 23.320 / 8 | 11.218 / 8 | 31.764 | 21.743 | 136.194 |
| historical_parameter_impedance | 23.920 / 8 | NA / 0 | 42.054 / 8 | 58.125 | 0.000 | 521.670 |
| historical_parameter_impedance_historical_entropy | 15.455 / 8 | 232.479 / 2 | 17.299 / 8 | 44.819 | 0.067 | 404.328 |
| historical_parameter_vmc | 15.576 / 8 | 11.526 / 8 | 8.134 / 8 | 39.028 | 53.268 | 128.863 |
| historical_vmc_boundary_00 | 13.887 / 8 | 10.661 / 8 | 9.232 / 8 | 36.542 | 61.823 | 129.033 |
| historical_vmc_boundary_05 | 12.881 / 8 | 13.208 / 8 | 9.766 / 8 | 35.665 | 70.389 | 130.702 |

不接触的P95为NA；冲量按全部回合描述，不能忽略未到达接触位置或早停的失败。
