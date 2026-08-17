# Paper main experiment tables (auto-generated 2026-08-17)

Protocol: matched post-contact benchmark, default fixtures 0-3 (fx3 held-out),
seed 20260817. Direct ESN coverage BC = 8 independent reservoir seeds
(stable-reference 19+1 expert-trace behavior cloning), mean±std.
Reference = deterministic multi-fixture DAgger iteration 03 (single reservoir).

## Table 1 — Matched post-contact benchmark

| Metric | Method | fx0 (train) | fx1 (train) | fx2 (train) | fx3 (held-out) |
|---|---|---|---|---|---|
| Post-contact RMSE (mm) ↓ | Fixed WBC | 8.816 | 11.893 | 15.537 | 17.901 |
| Post-contact RMSE (mm) ↓ | Direct ESN coverage BC (8 seeds) | 7.834±0.011 | 9.293±0.011 | 12.224±0.015 | 15.694±0.034 |
| Post-contact RMSE (mm) ↓ | Deterministic reference | 7.775 | 9.243 | 12.031 | 15.504 |
| Post-contact IAE (mm·s) ↓ | Fixed WBC | 8.73 | 11.47 | 13.87 | 15.75 |
| Post-contact IAE (mm·s) ↓ | Direct ESN coverage BC (8 seeds) | 7.68±0.01 | 8.36±0.02 | 9.36±0.02 | 12.74±0.04 |
| Post-contact IAE (mm·s) ↓ | Deterministic reference | 7.61 | 8.22 | 9.02 | 12.42 |
| Post-contact peak deviation (mm) ↓ | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Post-contact peak deviation (mm) ↓ | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Post-contact peak deviation (mm) ↓ | Deterministic reference | 11.56 | 16.92 | 23.24 | 26.99 |
| Actual-release rejoin latency (s) ↓ | Fixed WBC | 0.88 | 0.96 | 0.96 | 1.00 |
| Actual-release rejoin latency (s) ↓ | Direct ESN coverage BC (8 seeds) | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| Actual-release rejoin latency (s) ↓ | Deterministic reference | 0.80 | 0.60 | 0.48 | 0.64 |
| Scheduled-release rejoin latency (s) ↓ | Fixed WBC | 0.51 | 0.57 | 0.59 | 0.62 |
| Scheduled-release rejoin latency (s) ↓ | Direct ESN coverage BC (8 seeds) | 0.43±0.00 | 0.25±0.00 | 0.16±0.00 | 0.30±0.00 |
| Scheduled-release rejoin latency (s) ↓ | Deterministic reference | 0.43 | 0.21 | 0.11 | 0.26 |
| Contact impulse (N·s) ≈ | Fixed WBC | 0.903 | 1.524 | 2.163 | 2.504 |
| Contact impulse (N·s) ≈ | Direct ESN coverage BC (8 seeds) | 0.903±0.000 | 1.523±0.000 | 2.164±0.000 | 2.505±0.000 |
| Contact impulse (N·s) ≈ | Deterministic reference | 0.900 | 1.521 | 2.162 | 2.505 |
| Peak contact force (N) ≈ | Fixed WBC | 19.7 | 31.0 | 46.3 | 56.1 |
| Peak contact force (N) ≈ | Direct ESN coverage BC (8 seeds) | 19.7±0.0 | 31.0±0.0 | 46.3±0.0 | 56.1±0.0 |
| Peak contact force (N) ≈ | Deterministic reference | 19.7 | 31.0 | 46.3 | 56.1 |
| Peak torque (N·m) ≈ | Fixed WBC | 31.41 | 31.40 | 31.40 | 31.39 |
| Peak torque (N·m) ≈ | Direct ESN coverage BC (8 seeds) | 31.44±0.00 | 31.42±0.01 | 31.41±0.01 | 31.38±0.01 |
| Peak torque (N·m) ≈ | Deterministic reference | 31.48 | 31.44 | 31.44 | 31.49 |
| Peak recovery jerk (m/s³) ↓ | Fixed WBC | 6.1 | 10.3 | 2.5 | 15.0 |
| Peak recovery jerk (m/s³) ↓ | Direct ESN coverage BC (8 seeds) | 10.2±1.2 | 64.3±5.2 | 132.6±3.7 | 126.8±2.9 |
| Peak recovery jerk (m/s³) ↓ | Deterministic reference | 10.6 | 85.8 | 135.7 | 119.2 |

Fixed WBC rows are identical across methods by construction (same matched rollout).

## Table 2 — No-rod neutrality

| Metric | Fixed WBC | Direct ESN coverage BC (8 seeds) | Reference |
|---|---|---|---|
| Task success | True | 8/8 True | True |
| Hard torque limit | False | 8/8 False | False |
| Mean yielding twist (m/s) | 0.000 | 0.00106±0.00006 | 0.00043 |

## Table 3 — Geometry OOD (feasible region, unseen timing/height)

| OOD point | Task success | ΔRMSE vs Fixed WBC (mm) | Rejoin ESN vs FW (s) |
|---|---|---|---|
| start 1.130 (train ≤1.108) | 8/8 | -2.951±0.026 | 0.56±0.00 vs 0.96 |
| start 1.150 (train ≤1.108) | 8/8 | -2.129±0.117 | 0.60±0.00 vs 0.96 |
| height 0.545 (train ≤0.5425) | 8/8 | -2.404±0.048 | 0.60±0.00 vs 0.96 |
| corner (0.176, 0.5425, 1.130) | 8/8 | -1.879±0.090 | 0.68±0.00 vs 1.00 |

## Table 4 — Strength OOD boundary (stroke beyond 0.176)

Fixed WBC itself fails the task for all strokes ≥ 0.178 (physically infeasible zone);
columns give post-contact RMSE (mm) of each controller at selected strokes.

| Controller | stroke 0.178 | stroke 0.184 | stroke 0.19 |
|---|---|---|---|
| bc_13 | 26.1 | 75.6 | 99.1 |
| bc_42 | 23.7 | 31.8 | 44.5 |
| bc_71 | 23.9 | 25.6 | 27.2 |
| bc_137 | 25.4 | 33.1 | 44.1 |
| bc_251 | 24.4 | 28.8 | 29.3 |
| bc_307 | 25.7 | 69.6 | 85.8 |
| bc_512 | 25.0 | 28.4 | 30.6 |
| bc_1009 | 24.5 | 32.7 | 38.4 |
| reference | 24.0 | 30.7 | 55.1 |
| Fixed WBC (task fail) | 24.3 | 27.2 | 31.6 |

