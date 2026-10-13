# 公平性修正：实时状态

2026-10-13T05:22:05.556486+00:00；parallel_models_locked；状态 `models_locked`。

本机动态内存准入、最多4独立CPU核、每worker1线程/禁swap；完整保留39拟合/288回合原协议，服务器只归档。

```json
{
  "archive": {
    "status": "verified",
    "receipt": {
      "verified_utc": "2026-10-13T05:22:03.757651+00:00",
      "files_verified": 956,
      "total_bytes": 220632399,
      "manifest_sha256": "e8af933b29e2698f5569346dc3812d630402a5a8b6627d600fa4ed626c78eb59",
      "actual_compute_host": "airpig",
      "local_execution_root": "/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/fair_comparison_20261013_v2/delivery_parallel_models_locked/evidence",
      "published_evidence": "/home/arm1/sii_shared/SII_compliance/runs/main/fair_comparison_20261013_v2_parallel_models_locked/evidence",
      "historical_execution_paths_preserved": true
    }
  },
  "execution": {
    "status": "models_locked",
    "started_utc": "2026-10-13T04:50:33.752087+00:00",
    "jobs": [],
    "server_compute": false,
    "final_test_reads": 0,
    "registration_sha256": "a2e80a62252e97af7137ded2962a5790087d8154e2e01c52d0d7a305b2f44b64",
    "updated_utc": "2026-10-13T05:21:37.903167+00:00",
    "active": null,
    "dispatcher": "parallel_v3",
    "handoff_completed_utc": "2026-10-13T05:15:51.478873+00:00",
    "previous_execution_sha256": "dc85e0a7ea3717570904db697a593c8e8aa68d91ee3c258688ec1c2699365daa",
    "fits_complete": 39,
    "model_lock_sha256": "4da573485533ad1d7a7d0a026ee8a33a46812e6f7dcb517ae3b2c632a652f3ab"
  }
}
```

