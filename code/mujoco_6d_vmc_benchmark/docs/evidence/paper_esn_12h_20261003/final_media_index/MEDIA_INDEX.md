# Complete three-view final media

Server: `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`.

All videos are 55 s, 25 fps, 1375 frames, with unchanged playback speed. Paths below are relative to that server root.

| Condition / dt | Model | Task | Strict | MP4 |
|---|---|---|---|---|
| h1 / 1e-4 | zero | False | False | `media_final_h1/00_zero/replay_threeview.mp4` |
| h1 / 1e-4 | original_vmc_native | False | False | `media_final_h1/01_original_vmc_native/replay_threeview.mp4` |
| h1 / 1e-4 | fixed_admittance | False | False | `media_final_h1/02_fixed_admittance/replay_threeview.mp4` |
| h1 / 1e-4 | fixed_impedance | False | False | `media_final_h1/03_fixed_impedance/replay_threeview.mp4` |
| h1 / 1e-4 | fixed_vmc | False | False | `media_final_h1/04_fixed_vmc/replay_threeview.mp4` |
| h1 / 1e-4 | parameter_admittance | False | False | `media_final_h1/05_parameter_admittance/replay_threeview.mp4` |
| h1 / 1e-4 | parameter_impedance | False | False | `media_final_h1/06_parameter_impedance/replay_threeview.mp4` |
| h1 / 1e-4 | parameter_vmc | False | False | `media_final_h1/07_parameter_vmc/replay_threeview.mp4` |
| h1 / 1e-4 | direct_metric_74001 | False | False | `media_final_h1/08_direct_metric_74001/replay_threeview.mp4` |
| h1 / 1e-4 | direct_metric_74002 | False | False | `media_final_h1/09_direct_metric_74002/replay_threeview.mp4` |
| h1 / 1e-4 | direct_office_task_74001 | False | False | `media_final_h1/10_direct_office_task_74001/replay_threeview.mp4` |
| h1 / 1e-4 | direct_office_task_74002 | False | False | `media_final_h1/11_direct_office_task_74002/replay_threeview.mp4` |
| h1 / 1e-4 | recovery_lift0.035_distance0.02 | True | True | `media_final_h1/12_recovery_lift0.035_distance0.02/replay_threeview.mp4` |
| h1 / 1e-4 | recovery035_esn_fixed | False | False | `media_final_h1/13_recovery035_esn_fixed/replay_threeview.mp4` |
| h1 / 1e-4 | paired_recovery035__fp64 | False | False | `media_final_h1/14_paired_recovery035__fp64/replay_threeview.mp4` |
| h1 / 1e-4 | paired_recovery035_rnn_fp64 | True | True | `media_final_h1/15_paired_recovery035_rnn_fp64/replay_threeview.mp4` |
| h1 / 1e-4 | recovery035_esn_seed2 | True | False | `media_final_h1/16_recovery035_esn_seed2/replay_threeview.mp4` |
| h1 / 1e-4 | paired_recovery035_mlp_seed2 | False | False | `media_final_h1/17_paired_recovery035_mlp_seed2/replay_threeview.mp4` |
| h1 / 1e-4 | paired_recovery035_rnn_seed2 | False | False | `media_final_h1/18_paired_recovery035_rnn_seed2/replay_threeview.mp4` |
| h1 / 1e-4 | recovery035_esn_memoryless | False | False | `media_final_h1/19_recovery035_esn_memoryless/replay_threeview.mp4` |
| h1 / 1e-4 | paired_feature_matched_mlp | True | True | `media_final_h1/20_paired_feature_matched_mlp/replay_threeview.mp4` |
| h1 / 1e-4 | paired_feature_matched_rnn | False | False | `media_final_h1/21_paired_feature_matched_rnn/replay_threeview.mp4` |
| h1 / 1e-4 | paired_feature_matched_rnn_seed2 | True | True | `media_final_h1/22_paired_feature_matched_rnn_seed2/replay_threeview.mp4` |
| h1 / 1e-4 | admittance_01 | False | False | `media_final_h1/23_admittance_01/replay_threeview.mp4` |
| h1 / 1e-4 | impedance_12 | False | False | `media_final_h1/24_impedance_12/replay_threeview.mp4` |
| h1 / 1e-4 | original_vmc_04 | False | False | `media_final_h1/25_original_vmc_04/replay_threeview.mp4` |
| anchor / 5e-5 | recovery_lift0.035_distance0.02 | True | True | `media_formal/00_recovery_lift0.035_distance0.02/replay_threeview.mp4` |
| anchor / 5e-5 | recovery035_esn_fixed | False | False | `media_formal/01_recovery035_esn_fixed/replay_threeview.mp4` |
| anchor / 5e-5 | recovery035_esn_seed2 | False | False | `media_formal/02_recovery035_esn_seed2/replay_threeview.mp4` |
| anchor / 5e-5 | recovery035_esn_memoryless | True | True | `media_formal/03_recovery035_esn_memoryless/replay_threeview.mp4` |
| anchor / 5e-5 | paired_feature_matched_rnn | True | True | `media_formal/04_paired_feature_matched_rnn/replay_threeview.mp4` |
| anchor / 5e-5 | paired_feature_matched_rnn_seed2 | False | False | `media_formal/05_paired_feature_matched_rnn_seed2/replay_threeview.mp4` |
| anchor / 5e-5 | original_vmc_04 | False | False | `media_formal/06_original_vmc_04/replay_threeview.mp4` |
| h2 / 1e-4 | recovery035_esn_fixed | False | False | `media_remaining_designed_conditions/00_recovery035_esn_fixed/replay_threeview.mp4` |
| h2 / 1e-4 | recovery035_esn_seed2 | True | True | `media_remaining_designed_conditions/01_recovery035_esn_seed2/replay_threeview.mp4` |
| h2 / 1e-4 | paired_feature_matched_rnn | True | True | `media_remaining_designed_conditions/02_paired_feature_matched_rnn/replay_threeview.mp4` |
| h2 / 1e-4 | paired_feature_matched_rnn_seed2 | True | False | `media_remaining_designed_conditions/03_paired_feature_matched_rnn_seed2/replay_threeview.mp4` |
| h3 / 1e-4 | recovery035_esn_fixed | True | True | `media_remaining_designed_conditions/04_recovery035_esn_fixed/replay_threeview.mp4` |
| h3 / 1e-4 | recovery035_esn_seed2 | True | True | `media_remaining_designed_conditions/05_recovery035_esn_seed2/replay_threeview.mp4` |
| h3 / 1e-4 | paired_feature_matched_rnn | True | False | `media_remaining_designed_conditions/06_paired_feature_matched_rnn/replay_threeview.mp4` |
| h3 / 1e-4 | paired_feature_matched_rnn_seed2 | True | True | `media_remaining_designed_conditions/07_paired_feature_matched_rnn_seed2/replay_threeview.mp4` |
| h4 / 1e-4 | recovery035_esn_fixed | False | False | `media_remaining_designed_conditions/08_recovery035_esn_fixed/replay_threeview.mp4` |
| h4 / 1e-4 | recovery035_esn_seed2 | False | False | `media_remaining_designed_conditions/09_recovery035_esn_seed2/replay_threeview.mp4` |
| h4 / 1e-4 | paired_feature_matched_rnn | True | True | `media_remaining_designed_conditions/10_paired_feature_matched_rnn/replay_threeview.mp4` |
| h4 / 1e-4 | paired_feature_matched_rnn_seed2 | True | False | `media_remaining_designed_conditions/11_paired_feature_matched_rnn_seed2/replay_threeview.mp4` |
| h3 / 1e-4 | recovery_lift0.035_distance0.02 | False | False | `media_remaining_designed_conditions/12_recovery_lift0.035_distance0.02/replay_threeview.mp4` |
| h3 / 1e-4 | recovery035_esn_memoryless | True | True | `media_remaining_designed_conditions/13_recovery035_esn_memoryless/replay_threeview.mp4` |

Two h1 stacked ESN (top) / matched RNN (bottom) comparisons:

- `comparison_final_h1_seed1/comparison.mp4`
- `comparison_final_h1_seed2/comparison.mp4`

Per-file hashes and local playback cache paths: `MEDIA_INDEX.json`. Failures are retained.
