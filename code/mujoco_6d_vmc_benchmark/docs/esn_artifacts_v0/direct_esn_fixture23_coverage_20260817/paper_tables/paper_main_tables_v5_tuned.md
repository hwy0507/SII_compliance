# Paper Table 1 v5 — TUNED spring-carriage VMC baselines (strongest-baseline protocol)

Both VMC variants tuned on TRAIN fixtures 0-2 only (27-point grid over EE-spring
scale x drive-spring scale x zeta), held-out fx3 and OOD evaluated once.
proprio: kappa x0.5, drive x1.0, zeta 0.8.  force: kappa x2.0, drive x2.0, zeta 0.8.
Selection score: mean dRMSE - 0.5*rejoin penalty - 0.005*mean jerk (train only).

| Metric | Method | fx0 | fx1 | fx2 | fx3 (held-out) |
|---|---|---|---|---|---|
| Post-contact RMSE (mm) | Fixed WBC | 8.816 | 11.893 | 15.537 | 17.901 |
| Post-contact RMSE (mm) | SC-VMC proprio (tuned) | 8.884 | 12.568 | 17.069 | 19.732 |
| Post-contact RMSE (mm) | SC-VMC force (tuned) | 8.825 | 12.004 | 15.781 | 18.186 |
| Post-contact RMSE (mm) | Direct ESN coverage BC (8 seeds) | 7.834±0.011 | 9.293±0.011 | 12.224±0.015 | 15.694±0.034 |
| Post-contact IAE (mm·s) | Fixed WBC | 8.73 | 11.47 | 13.87 | 15.75 |
| Post-contact IAE (mm·s) | SC-VMC proprio (tuned) | 8.73 | 11.53 | 14.00 | 14.62 |
| Post-contact IAE (mm·s) | SC-VMC force (tuned) | 8.73 | 11.57 | 14.09 | 16.01 |
| Post-contact IAE (mm·s) | Direct ESN coverage BC (8 seeds) | 7.68±0.01 | 8.36±0.02 | 9.36±0.02 | 12.74±0.04 |
| Post-contact peak deviation (mm) | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Post-contact peak deviation (mm) | SC-VMC proprio (tuned) | 12.64 | 21.01 | 31.23 | 36.66 |
| Post-contact peak deviation (mm) | SC-VMC force (tuned) | 12.39 | 18.54 | 25.84 | 30.60 |
| Post-contact peak deviation (mm) | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Actual-release rejoin latency (s) | Fixed WBC | 0.88 | 0.96 | 0.96 | 1.00 |
| Actual-release rejoin latency (s) | SC-VMC proprio (tuned) | 0.88 | 0.84 | 0.64 | 0.56 |
| Actual-release rejoin latency (s) | SC-VMC force (tuned) | 0.88 | 0.96 | 1.00 | 1.00 |
| Actual-release rejoin latency (s) | Direct ESN coverage BC (8 seeds) | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| Contact impulse (N·s) | Fixed WBC | 0.903 | 1.524 | 2.163 | 2.504 |
| Contact impulse (N·s) | SC-VMC proprio (tuned) | 0.890 | 1.498 | 2.122 | 2.480 |
| Contact impulse (N·s) | SC-VMC force (tuned) | 0.893 | 1.519 | 2.154 | 2.494 |
| Contact impulse (N·s) | Direct ESN coverage BC (8 seeds) | 0.903±0.000 | 1.523±0.000 | 2.164±0.000 | 2.505±0.000 |
| Peak torque (N·m) | Fixed WBC | 31.41 | 31.40 | 31.40 | 31.39 |
| Peak torque (N·m) | SC-VMC proprio (tuned) | 31.45 | 31.45 | 31.43 | 31.41 |
| Peak torque (N·m) | SC-VMC force (tuned) | 31.41 | 31.41 | 31.40 | 31.39 |
| Peak torque (N·m) | Direct ESN coverage BC (8 seeds) | 31.44±0.00 | 31.42±0.01 | 31.41±0.01 | 31.38±0.01 |
| Peak recovery jerk (m/s³) | Fixed WBC | 6.1 | 10.3 | 2.5 | 15.0 |
| Peak recovery jerk (m/s³) | SC-VMC proprio (tuned) | 42.9 | 46.3 | 96.5 | 99.8 |
| Peak recovery jerk (m/s³) | SC-VMC force (tuned) | 6.1 | 11.5 | 2.6 | 13.9 |
| Peak recovery jerk (m/s³) | Direct ESN coverage BC (8 seeds) | 10.2±1.2 | 64.3±5.2 | 132.6±3.7 | 126.8±2.9 |

## Geometry OOD (same matrix as the ESN OOD scan)

| Method | start 1.130 | start 1.150 | height 0.545 | corner |
|---|---|---|---|---|
| Direct ESN BC (8 seeds, dRMSE) | -2.951 | -2.129 | -2.404 | -1.879 |
| SC-VMC proprio (tuned, dRMSE) | +1.541 | +1.530 | +1.795 | +3.645 (fail) |
| SC-VMC force (tuned, dRMSE) | +0.170 | +0.241 | +0.236 | +0.299 |

Reading: with symmetric train-only tuning the force-feedback VMC converges to an
almost transparent compliance (dRMSE within +0.3 mm of Fixed WBC everywhere, jerk
identical to Fixed WBC), and the proprioceptive variant trades accuracy for faster
rejoin; the ESN ensemble remains the only method that improves post-contact RMSE
over Fixed WBC on every fixture while rejoining faster.

Frozen-parameter versions of both variants (no tuning) are in v3; the paper-original
constant-pull drive is in v4.  No-rod neutrality: proprio 0.00106, force 0.00000 m/s.

