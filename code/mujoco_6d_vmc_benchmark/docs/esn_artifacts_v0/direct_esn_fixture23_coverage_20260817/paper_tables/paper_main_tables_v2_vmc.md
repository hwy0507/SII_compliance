# Paper Table 1 v2 — with twist-layer VMC baseline (auto-generated)

Protocol: matched post-contact benchmark, fixtures 0-3 (fx3 held-out), seed 20260817.
VMC baseline = twist-layer saturating spring-damper on WBC tracking error,
tuned on train fixtures only (kappa_t 1.0, kappa_r 2.0, zeta 0.8, drive 2.0),
same 7-D action interface and safety adapter as Direct ESN; proprioceptive only.

| Metric | Method | fx0 | fx1 | fx2 | fx3 (held-out) |
|---|---|---|---|---|---|
| Post-contact RMSE (mm) | Fixed WBC | 8.816 | 11.893 | 15.537 | 17.901 |
| Post-contact RMSE (mm) | VMC compliance (tuned) | 8.610 | 11.361 | 13.307 | 11.232 |
| Post-contact RMSE (mm) | Direct ESN coverage BC (8 seeds) | 7.834±0.011 | 9.293±0.011 | 12.224±0.015 | 15.694±0.034 |
| Post-contact RMSE (mm) | Deterministic reference | 7.775 | 9.243 | 12.031 | 15.504 |
| Post-contact IAE (mm·s) | Fixed WBC | 8.73 | 11.47 | 13.87 | 15.75 |
| Post-contact IAE (mm·s) | VMC compliance (tuned) | 8.69 | 11.56 | 12.81 | 8.91 |
| Post-contact IAE (mm·s) | Direct ESN coverage BC (8 seeds) | 7.68±0.01 | 8.36±0.02 | 9.36±0.02 | 12.74±0.04 |
| Post-contact IAE (mm·s) | Deterministic reference | 7.61 | 8.22 | 9.02 | 12.42 |
| Post-contact peak deviation (mm) | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Post-contact peak deviation (mm) | VMC compliance (tuned) | 11.43 | 14.92 | 20.97 | 13.81 |
| Post-contact peak deviation (mm) | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Post-contact peak deviation (mm) | Deterministic reference | 11.56 | 16.92 | 23.24 | 26.99 |
| Whole-episode peak deviation (mm) | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Whole-episode peak deviation (mm) | VMC compliance (tuned) | 11.43 | 14.92 | 20.97 | 25.14 |
| Whole-episode peak deviation (mm) | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Whole-episode peak deviation (mm) | Deterministic reference | 11.56 | 16.92 | 23.24 | 26.99 |
| Actual-release rejoin latency (s) | Fixed WBC | 0.88 | 0.96 | 0.96 | 1.00 |
| Actual-release rejoin latency (s) | VMC compliance (tuned) | 0.96 | 1.16 | 1.36 | 1.20 |
| Actual-release rejoin latency (s) | Direct ESN coverage BC (8 seeds) | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| Actual-release rejoin latency (s) | Deterministic reference | 0.80 | 0.60 | 0.48 | 0.64 |
| Contact release time (s) | Fixed WBC | 1.32 | 1.32 | 1.36 | 1.36 |
| Contact release time (s) | VMC compliance (tuned) | 1.32 | 1.32 | 1.36 | 1.56 |
| Contact release time (s) | Direct ESN coverage BC (8 seeds) | 1.32±0.00 | 1.32±0.00 | 1.36±0.00 | 1.36±0.00 |
| Contact release time (s) | Deterministic reference | 1.32 | 1.32 | 1.36 | 1.36 |
| Contact impulse (N·s) | Fixed WBC | 0.903 | 1.524 | 2.163 | 2.504 |
| Contact impulse (N·s) | VMC compliance (tuned) | 0.959 | 1.565 | 2.214 | 2.524 |
| Contact impulse (N·s) | Direct ESN coverage BC (8 seeds) | 0.903±0.000 | 1.523±0.000 | 2.164±0.000 | 2.505±0.000 |
| Contact impulse (N·s) | Deterministic reference | 0.900 | 1.521 | 2.162 | 2.505 |
| Peak torque (N·m) | Fixed WBC | 31.41 | 31.40 | 31.40 | 31.39 |
| Peak torque (N·m) | VMC compliance (tuned) | 31.46 | 31.49 | 31.41 | 31.48 |
| Peak torque (N·m) | Direct ESN coverage BC (8 seeds) | 31.44±0.00 | 31.42±0.01 | 31.41±0.01 | 31.38±0.01 |
| Peak torque (N·m) | Deterministic reference | 31.48 | 31.44 | 31.44 | 31.49 |
| Peak recovery jerk (m/s³) | Fixed WBC | 6.1 | 10.3 | 2.5 | 15.0 |
| Peak recovery jerk (m/s³) | VMC compliance (tuned) | 17.6 | 13.1 | 16.2 | 103.5 |
| Peak recovery jerk (m/s³) | Direct ESN coverage BC (8 seeds) | 10.2±1.2 | 64.3±5.2 | 132.6±3.7 | 126.8±2.9 |
| Peak recovery jerk (m/s³) | Deterministic reference | 10.6 | 85.8 | 135.7 | 119.2 |

Note: the VMC baseline prolongs rod contact on fx3 (release 1.56 vs 1.36 s), which
shifts the post-contact window start; whole-episode peak deviation is reported as a
window-robust companion metric.

No-rod (VMC): task success True, hard torque False.

