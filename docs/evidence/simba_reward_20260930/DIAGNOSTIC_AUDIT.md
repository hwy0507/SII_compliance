# Independent supplemental diagnostic audit

Created: 2026-09-30T18:13:10.848453 (server CST)

Post-primary development diagnostic, not held-out confirmation. Both rewards train from scratch with continuous pose/speed-aware progress potential. Fixed common40k checkpoint,2 seeds per reward,6 identical known fixtures each.

| Reward | Success | Physical valid | Full55s | RMSE(cm) | Peak actual torque(Nm) | Peak speed(m/s) |
|---|---:|---:|---:|---:|---:|---:|
| office_task | 0/12 | 11/12 | 12/12 | 19.196306 ± 8.755207 | 39.532790 ± 0.505953 | 0.153733 ± 0.057066 |
| metric | 0/12 | 12/12 | 12/12 | 68.931514 ± 9.365863 | 51.119535 ± 1.596541 | 0.334076 ± 0.100951 |

Mean±sample SD across2 seed means, not across24 independent seeds. All failures retained.

## Training coverage

- metric_seed41001: 40000 transitions, 16000000 physical substeps, stage counts {'0': 40000}; 29 ended episodes, {'approach': 29}; Phi<1e-6 9.310%; abs(progress)>1e-6 90.683%.
- metric_seed41002: 40000 transitions, 16000000 physical substeps, stage counts {'0': 39964, '1': 36}; 29 ended episodes, {'approach': 28, 'align': 1}; Phi<1e-6 34.675%; abs(progress)>1e-6 65.660%.
- office_task_seed41001: 40000 transitions, 16000000 physical substeps, stage counts {'0': 38637, '1': 1363}; 29 ended episodes, {'approach': 28, 'align': 1}; Phi<1e-6 29.350%; abs(progress)>1e-6 70.110%.
- office_task_seed41002: 40000 transitions, 16000000 physical substeps, stage counts {'0': 35037, '1': 4963}; 30 ended episodes, {'approach': 25, 'align': 5}; Phi<1e-6 18.735%; abs(progress)>1e-6 80.990%.

All117 ended training episodes had no grasp-stage completion or task success. Improved numerical density has not solved task exploration.

## Verification

{
  "all8jobs_rc0": true,
  "common40k": true,
  "all_run_checks_pass": true,
  "all24_model_hashes_match": true,
  "all24_time_and_counts_match": true,
  "raw_recomputation_scope": "all24 episodes; all physical substeps; position RMSE time-weighted, max absolute qfrc_actuator, max translational twist norm",
  "raw_recompute_max_abs_error": {
    "rmse_m": 1.8557599901214417e-11,
    "peak_torque_nm": 1.8728810999846246e-06,
    "peak_velocity_mps": 1.4748340548820238e-08
  }
}

## Abort details


## Interpretation limits

- Two training seeds; sample SD describes these seeds and is not a confidence interval.
- Same six already-known development fixtures; no independent confirmation.
- 40k diagnostic linear learning-rate horizon differs from primary100k horizon; do not interpret as a strict one-factor matched40k ablation.
- All task and physical failures remain in metric means. Any premature abort has a shorter observed interval and cannot be treated as a full55s trajectory.
- Physical validity is the existing validator flag; it is not an assertion that every force safety threshold or event-contact coverage passed.
- Equal normalizer diagnostics verify recorded sample counts/denominator/counters, not an independent complete moments tensor hash.
- Training117 ended episodes exclude unfinished partial episodes, but coverage counts include all160000 training transitions.

Full per-seed, episode and raw-array audit: `/home/arm1/vmc_mujoco_runtime/reward_study_20260930/progress_dense_diagnostic_04/report/DIAGNOSTIC_AUDIT.json`.

## Physical-invalid case

Office_task seed41001 case4 has max external numerical penetration0.218134mm (ball versus fr3_link6), exceeding0.2mm physical-validity gate. It remains below2mm emergency-abort gate, so55s completed and abort_reason is null. This is not an early-aborted trajectory.

The upstream optimizer uses optax.linear_schedule (simbaV2_agent.py lines115/158/184), not cosine:1e-4 to5e-5 over80000 diagnostic updates versus200000 primary updates. Each diagnostic completed70002 updates.
