# 公平性修正：实时状态

2026-10-13T14:50:05.843204+00:00；parallel_v4_parallel_condition_prospective_20261013_acceptance_003；状态 `prospective_evaluation`。

本机动态内存准入、最多4独立CPU核、每worker1线程/禁swap；完整保留39拟合/288回合原协议，服务器只归档。

```json
{
  "archive": {
    "status": "verified",
    "receipt": {
      "verified_utc": "2026-10-13T14:50:03.842778+00:00",
      "files_verified": 904,
      "total_bytes": 7893221,
      "manifest_sha256": "245ac10a3e47ede55513f9fde2eefcc7fe09e5c2644339921045ef0896fe54e1",
      "actual_compute_host": "airpig",
      "local_execution_root": "/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/fair_comparison_20261013_v2/delivery_parallel_v4_parallel_condition_prospective_20261013_acceptance_003/evidence",
      "published_evidence": "/home/arm1/sii_shared/SII_compliance/runs/main/fair_comparison_20261013_v2_parallel_v4_parallel_condition_prospective_20261013_acceptance_003/evidence",
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
    "updated_utc": "2026-10-13T14:50:00.677396+00:00",
    "active": null,
    "dispatcher": "dispatch_v4",
    "handoff_completed_utc": "2026-10-13T05:38:09.564858+00:00",
    "previous_execution_sha256": "1cc60991a5099119031f3db461419da3ca1476ffdff770b77c99292d919df968",
    "fits_complete": 39,
    "model_lock_sha256": "4da573485533ad1d7a7d0a026ee8a33a46812e6f7dcb517ae3b2c632a652f3ab",
    "active_jobs": {
      "0": {
        "cap": 2147483648,
        "cpu": 1,
        "unit": null,
        "job": null,
        "started_utc": "2026-10-13T14:49:59.329365+00:00"
      }
    },
    "evaluated": 144,
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
| esn_gradient_s2026101301 | 4/8 | pending | pending | pending | pending | pending | 0 |
| esn_gradient_s2026101302 | 4/8 | pending | pending | pending | pending | pending | 0 |
| esn_gradient_s2026101303 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_scratch_s2026101301 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_scratch_s2026101302 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_scratch_s2026101303 | 4/8 | pending | pending | pending | pending | pending | 0 |
| mlp_scratch_s2026101301 | 4/8 | pending | pending | pending | pending | pending | 0 |
| mlp_scratch_s2026101302 | 4/8 | pending | pending | pending | pending | pending | 0 |
| mlp_scratch_s2026101303 | 4/8 | pending | pending | pending | pending | pending | 0 |
| esn_ridge_s2026101301 | 4/8 | pending | pending | pending | pending | pending | 0 |
| esn_ridge_s2026101302 | 4/8 | pending | pending | pending | pending | pending | 0 |
| esn_ridge_s2026101303 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_from_ridge_s2026101301 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_from_ridge_s2026101302 | 4/8 | pending | pending | pending | pending | pending | 0 |
| rnn_from_ridge_s2026101303 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_admittance_boundary_06 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_admittance_boundary_07 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_direct_metric | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_direct_office_task | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_direct_office_task_historical_entropy | 4/8 | pending | pending | pending | pending | pending | 4 |
| historical_enhanced_teacher | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_esn | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_impedance_boundary_01 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_impedance_boundary_02 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_matched_mlp | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_matched_rnn | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_memoryless | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_nominal_zero | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_ordinary_mlp | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_ordinary_rnn | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_parameter_admittance | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_parameter_impedance | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_parameter_impedance_historical_entropy | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_parameter_vmc | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_vmc_boundary_00 | 4/8 | pending | pending | pending | pending | pending | 0 |
| historical_vmc_boundary_05 | 4/8 | pending | pending | pending | pending | pending | 0 |

每个新网络有3个seed，不挑最好seed。历史方法每配置仍只有既有训练seed，不能复制成3seed。
全部失败计入分母，未完成不记0/0；早停的低速度/低冲量不能当作优点。
接触P95、冲量、接触覆盖、恢复删失及原始指标均存 REPORT.json；结果不完整时不宣布排名。

|方法/seed|人手P95 N / 接触回合|棍P95 N / 接触回合|桌角P95 N / 接触回合|人手冲量 N·s|棍冲量 N·s|桌角冲量 N·s|
|---|---:|---:|---:|---:|---:|---:|

不接触的P95为NA；冲量按全部回合描述，不能忽略未到达接触位置或早停的失败。
