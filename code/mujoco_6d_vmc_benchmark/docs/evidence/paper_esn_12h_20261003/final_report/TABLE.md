# Frozen final validation

26 models × four paired conditions; 7 development-qualified formal reruns.

| Model | Development task/strict | Heldout task/strict (n=4) | Formal task/strict | Full 55s | RMSE median/range mm (full runs) |
|---|---|---|---|---|---|
| zero | 0/0 | 0/0 | not eligible | 4/4 | 26.954 [26.321, 27.949] |
| original_vmc_native | 0/0 | 0/0 | not eligible | 4/4 | 28.804 [27.167, 31.020] |
| fixed_admittance | 0/0 | 0/0 | not eligible | 4/4 | 29.739 [28.297, 32.563] |
| fixed_impedance | 0/0 | 0/0 | not eligible | 4/4 | 23.052 [22.886, 23.170] |
| fixed_vmc | 0/0 | 0/0 | not eligible | 4/4 | 33.980 [30.613, 38.663] |
| parameter_admittance | 0/0 | 0/0 | not eligible | 4/4 | 28.999 [28.005, 29.550] |
| parameter_impedance | 0/0 | 0/0 | not eligible | 4/4 | 26.211 [25.395, 26.858] |
| parameter_vmc | 0/0 | 0/0 | not eligible | 4/4 | 38.184 [35.278, 44.296] |
| direct_metric_74001 | 0/0 | 0/0 | not eligible | 4/4 | 293.406 [51.265, 902.497] |
| direct_metric_74002 | 0/0 | 0/0 | not eligible | 4/4 | 633.786 [567.563, 742.195] |
| direct_office_task_74001 | 0/0 | 0/0 | not eligible | 4/4 | 232.332 [148.317, 294.519] |
| direct_office_task_74002 | 0/0 | 0/0 | not eligible | 4/4 | 497.574 [267.302, 690.632] |
| recovery_lift0.035_distance0.02 | 1/1 | 3/2 | 1/1 | 4/4 | 29.381 [26.743, 30.828] |
| recovery035_esn_fixed | 1/1 | 1/1 | 0/0 | 4/4 | 36.597 [28.110, 53.682] |
| paired_recovery035__fp64 | 0/0 | 0/0 | not eligible | 4/4 | 49.287 [46.222, 53.595] |
| paired_recovery035_rnn_fp64 | 0/0 | 4/2 | not eligible | 4/4 | 38.928 [36.729, 43.139] |
| recovery035_esn_seed2 | 1/1 | 3/2 | 0/0 | 4/4 | 30.435 [29.254, 32.798] |
| paired_recovery035_mlp_seed2 | 0/0 | 0/0 | not eligible | 4/4 | 35.011 [28.004, 40.675] |
| paired_recovery035_rnn_seed2 | 0/0 | 2/1 | not eligible | 4/4 | 35.804 [32.623, 41.286] |
| recovery035_esn_memoryless | 1/1 | 3/2 | 1/1 | 4/4 | 28.404 [26.584, 29.997] |
| paired_feature_matched_mlp | 0/0 | 2/2 | not eligible | 4/4 | 31.826 [27.510, 38.269] |
| paired_feature_matched_rnn | 1/1 | 3/2 | 1/1 | 4/4 | 43.453 [35.912, 54.527] |
| paired_feature_matched_rnn_seed2 | 1/1 | 4/2 | 0/0 | 4/4 | 32.193 [29.184, 37.480] |
| admittance_01 | 0/0 | 0/0 | not eligible | 4/4 | 29.432 [27.983, 34.617] |
| impedance_12 | 0/0 | 0/0 | not eligible | 4/4 | 19.893 [19.820, 19.969] |
| original_vmc_04 | 1/1 | 0/0 | 0/0 | 4/4 | 47.736 [44.759, 49.512] |

Task and strict counts are separate. The table includes all frozen models, not only successes.
Formal is the anchor at 5e-5 s; the four paired perturbations use 1e-4 s and must not be pooled with formal.

## Supplementary random conditions (development-qualified models only)

| Model | Task / 8 | Strict / 8 | Full 55s / 8 |
|---|---:|---:|---:|
| recovery_lift0.035_distance0.02 | 7 | 5 | 8 |
| recovery035_esn_fixed | 6 | 4 | 8 |
| recovery035_esn_seed2 | 5 | 4 | 8 |
| recovery035_esn_memoryless | 5 | 5 | 8 |
| paired_feature_matched_rnn | 6 | 1 | 8 |
| paired_feature_matched_rnn_seed2 | 3 | 2 | 8 |
| original_vmc_04 | 0 | 0 | 8 |

All other models were not eligible and are not counted as failures in this supplementary cohort.
