# Paper Table 1 v4 — constant-pull (paper Eq. 5b) row added

All rows identical to v3 except the added SC-VMC constant-pull variant:
the original Eq. (5b) drive of Zhang et al. (IROS 2024) — constant-magnitude
tangent pull (translation only) with viscous friction on the absolute carriage
velocity and NO position-restoring drive spring. Pull magnitude 1.0 N
(0.5/2.0 N give the same qualitative outcome, see const_pull_eval.json).

| Metric | SC-VMC constant pull (frozen) | fx0 | fx1 | fx2 | fx3 (held-out) |
|---|---|---|---|---|---|
| Post-contact RMSE (mm) | Eq. 5b drive | 8.885 | 12.969 | 17.358 | 21.313 |
| Actual-release rejoin latency (s) | Eq. 5b drive | 0.88 | 0.84 | 0.56 | 0.64 |
| Peak recovery jerk (m/s³) | Eq. 5b drive | 32.5 | 30.2 | 131.2 | 265.1 |
| Contact impulse (N·s) | Eq. 5b drive | 0.893 | 1.498 | 2.122 | 2.481 |
| Task success | Eq. 5b drive | True | True | True | False |

Reading: the paper's original constant-pull drive matches the drive-spring variant on
train fixtures but fails the held-out strong collision (task failure at every pull
magnitude). Without a position-restoring term the carriage cannot rejoin precisely
enough to complete the grasp; the drive spring used by the main SC-VMC baselines is
the moving-target adaptation (Fig. 1c of the same paper) required by this task.

No-rod neutrality (constant pull): success=True, mean yield 0.00111 m/s.

Full v3 table below unchanged:

# Paper Table 1 v3 — spring-carriage VMC baselines (auto-generated)

Protocol: matched post-contact benchmark, fixtures 0-3 (fx3 held-out), seed 20260817.
SC-VMC proprio = faithful spring-carriage reproduction (frozen v4 VMCConfig + KAPPA_6D,
zero tuning), proprioceptive drive (WBC tracking error only).
SC-VMC force = same dynamics, measured rod-on-hand wrench drive with identical
channel saturation (information-set upper bound; reads a signal the ESN forbids).
Direct ESN coverage BC = 8 independent reservoir seeds, mean±std.

| Metric | Method | fx0 | fx1 | fx2 | fx3 (held-out) |
|---|---|---|---|---|---|
| Post-contact RMSE (mm) | Fixed WBC | 8.816 | 11.893 | 15.537 | 17.901 |
| Post-contact RMSE (mm) | SC-VMC proprio (frozen) | 8.887 | 12.930 | 17.247 | 19.827 |
| Post-contact RMSE (mm) | SC-VMC force (frozen) | 8.877 | 12.248 | 16.498 | 18.593 |
| Post-contact RMSE (mm) | Direct ESN coverage BC (8 seeds) | 7.834±0.011 | 9.293±0.011 | 12.224±0.015 | 15.694±0.034 |
| Post-contact IAE (mm·s) | Fixed WBC | 8.73 | 11.47 | 13.87 | 15.75 |
| Post-contact IAE (mm·s) | SC-VMC proprio (frozen) | 8.75 | 11.90 | 13.88 | 14.64 |
| Post-contact IAE (mm·s) | SC-VMC force (frozen) | 8.78 | 11.80 | 14.83 | 16.43 |
| Post-contact IAE (mm·s) | Direct ESN coverage BC (8 seeds) | 7.68±0.01 | 8.36±0.02 | 9.36±0.02 | 12.74±0.04 |
| Post-contact peak deviation (mm) | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Post-contact peak deviation (mm) | SC-VMC proprio (frozen) | 12.61 | 21.56 | 31.70 | 36.91 |
| Post-contact peak deviation (mm) | SC-VMC force (frozen) | 12.48 | 18.96 | 26.36 | 31.07 |
| Post-contact peak deviation (mm) | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Whole-episode peak deviation (mm) | Fixed WBC | 12.37 | 18.32 | 25.45 | 30.21 |
| Whole-episode peak deviation (mm) | SC-VMC proprio (frozen) | 12.61 | 21.56 | 31.70 | 36.91 |
| Whole-episode peak deviation (mm) | SC-VMC force (frozen) | 12.48 | 18.96 | 26.36 | 31.07 |
| Whole-episode peak deviation (mm) | Direct ESN coverage BC (8 seeds) | 11.57±0.02 | 16.81±0.01 | 23.20±0.00 | 27.00±0.01 |
| Actual-release rejoin latency (s) | Fixed WBC | 0.88 | 0.96 | 0.96 | 1.00 |
| Actual-release rejoin latency (s) | SC-VMC proprio (frozen) | 0.88 | 0.88 | 0.60 | 0.52 |
| Actual-release rejoin latency (s) | SC-VMC force (frozen) | 0.88 | 1.00 | 1.00 | 1.04 |
| Actual-release rejoin latency (s) | Direct ESN coverage BC (8 seeds) | 0.80±0.00 | 0.64±0.00 | 0.52±0.00 | 0.68±0.00 |
| Contact impulse (N·s) | Fixed WBC | 0.903 | 1.524 | 2.163 | 2.504 |
| Contact impulse (N·s) | SC-VMC proprio (frozen) | 0.893 | 1.498 | 2.122 | 2.481 |
| Contact impulse (N·s) | SC-VMC force (frozen) | 0.865 | 1.508 | 2.142 | 2.483 |
| Contact impulse (N·s) | Direct ESN coverage BC (8 seeds) | 0.903±0.000 | 1.523±0.000 | 2.164±0.000 | 2.505±0.000 |
| Peak torque (N·m) | Fixed WBC | 31.41 | 31.40 | 31.40 | 31.39 |
| Peak torque (N·m) | SC-VMC proprio (frozen) | 31.44 | 31.44 | 31.43 | 31.43 |
| Peak torque (N·m) | SC-VMC force (frozen) | 31.41 | 31.41 | 31.40 | 31.37 |
| Peak torque (N·m) | Direct ESN coverage BC (8 seeds) | 31.44±0.00 | 31.42±0.01 | 31.41±0.01 | 31.38±0.01 |
| Peak recovery jerk (m/s³) | Fixed WBC | 6.1 | 10.3 | 2.5 | 15.0 |
| Peak recovery jerk (m/s³) | SC-VMC proprio (frozen) | 31.6 | 30.9 | 118.5 | 115.6 |
| Peak recovery jerk (m/s³) | SC-VMC force (frozen) | 6.1 | 10.9 | 2.6 | 14.8 |
| Peak recovery jerk (m/s³) | Direct ESN coverage BC (8 seeds) | 10.2±1.2 | 64.3±5.2 | 132.6±3.7 | 126.8±2.9 |

## ESN yield EMA ablation (negative result)

| Config | fx0-3 ΔRMSE (8-seed mean) | fx1/2/3 recovery jerk | fx3 rejoin |
|---|---|---|---|
| alpha 1.0 (off) | -0.982 / -2.600 / -3.313 / **-2.207** | 64 / 133 / 127 | 0.68 s |
| alpha 0.4 | -0.931 / -2.524 / -3.005 / -0.862 | 56 / 119 / 116 | 0.67 s |
| alpha 0.25 | -0.816 / -2.315 / -2.682 / -0.635 | 35 / 88 / 122 | 0.68 s |

EMA lowers train-fixture jerk but degrades held-out fx3 RMSE by 60-71% with no fx3
jerk benefit; deployment-side smoothing is rejected as the recovery-jerk remedy.

SC-VMC proprioceptive no-rod: success=True, hard torque=False, mean yield=0.00079 m/s.
SC-VMC force_feedback no-rod: success=True, hard torque=False, mean yield=0.00000 m/s.
