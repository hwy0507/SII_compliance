# Targeted Contact-Yield Recovery

## 2026-10-30 18:57 CST Fixed27 Result

The v6 recovery refit has completed and its fixed train00 development matrix has now completed all 27 rows with an independent review. Task passed 27/27 and Strict passed 25/27. ESN and RNN each passed 9/9; MLP passed 7/9. All 27 actor and action-filter replays matched exactly (`max_abs_error=0`). Each episode completed 500 actor steps and 400,000 physical substeps under CPU6, one thread, one simulator, 3 GiB memory and no swap. The isolated unseen108 set was not read or dispatched.

Both failures are rod MLP cases with distinct physical behavior. Seed01 passed Task and the machine gate but failed the required rod behavior: it yielded 10.23 mm, never crossed the held rod, and never rejoined before retraction; it completed the task at 16.28 s after the rod withdrew. Seed03 crossed at 11.24 s and confirmed rejoin at 12.16 s before the 12.76 s retraction, but contacted `fr3_link7` and reached 0.236507 mm penetration, above the frozen 0.20 mm limit. The complete trajectories, strict qualification failures and audits remain preserved.

The training and physics evidence does not point to a broken teacher or a shared environment/gate issue: all methods used the same qualified data and frozen runner, while ESN and RNN passed all nine cells. The three MLP locks have validation MSE 1.59e-4 to 1.69e-4, compared with roughly 3.36e-5 to 4.00e-5 for ESN and 3.17e-5 to 3.60e-5 for RNN. This suggests the stateless 48-input MLP has difficulty representing contact timing and maintaining safe clearance. It does not yet prove the cause; a targeted observation/action aliasing analysis should precede any new architecture or dataset registration. No physics, gate, actor input, validation identity, or final-test condition was changed.

The v6-specific fit audit passed for 75 candidates, nine locked models and nine actor replays. This is fit/replay integrity only, not evidence that every policy qualifies. The fixed27 handoff had two preflight-only failures before any physical episode; both receipts remain preserved. The corrected run and independent report are under `outputs/contact_yield_recovery_student_handoff_20261030_v4/` and `outputs/contact_yield_recovery_student_development_20261030_v5/`. No final108 result exists.

## 2026-10-30 18:31 CST Update

The recovery-augmented v6 fit has now completed all 75 candidates with zero fit failures. Its independent `FIT_AUDIT.json` passed with 75 candidate records, nine frozen models, and nine actor replays. This certifies the registered fit and replay checks only; it does not establish closed-loop qualification.

The previous recovery fixed27 handoff was still bound to the older v3 lock, so it did not automatically evaluate v6. A new v6-specific diagnosis wrapper and handoff now bind the exact v6 execution, dataset, lock, audit, and source hashes while reusing the existing fixed27 train00 physical runner. No model reselection or unseen108 access is permitted.

Two preflight failures were preserved before any physical episode: handoff v2 incorrectly required the target directory to remain absent after its prepare phase; v3 used an old target path inside the reused runner. The corrected v4 handoff started the unique target `outputs/contact_yield_recovery_student_development_20261030_v5`. At 18:31 CST it has completed 3/27 rows: rod ESN and RNN seed01 pass Task/Strict/machine checks; rod MLP seed01 fails Strict while passing the machine gate, consistent with the earlier rejoin-timing concern. Rod ESN seed02 is in progress. Resource limits are CPU6, one thread, one simulator, 3 GiB memory, and no swap. The final108 remains untouched.

## Scope

This is a development-only diagnosis on the fixed `rod_00` training identity. It uses the already locked MLP seed 2026102801 and seed 2026102803, their exact saved student prefixes, the unchanged VMC teacher, existing action filter and unchanged physical worker. It does not inspect or dispatch the isolated unseen108 test. Physics, actor input, gates, actuator limits, filter and `dt=5e-5` remain frozen.

## 2026-10-30 16:55 CST Continuation

The four additional early-handoff probes are complete and audited. MLP seed01 handoffs at 4.48s and 4.60s passed Task, Strict and machine gates; seed02 handoffs at both times failed the frozen penetration gate and are excluded from fitting. All four receipts remain under `outputs/contact_yield_mlp_rod_early_recovery_20261030_v1/`.

The new shared dataset has 38 episodes and 20,500 frames: 32 training episodes and the same six pure-teacher validation identities. It contains 1,707 zero-weight student-prefix frames and 18,793 positive-weight rows; 3,043 rows are VMC-teacher recovery suffixes. The two failed seed02 prefixes remain only in rejection receipts. Dataset SHA256 is `29093f8d62ef5b7e072b813112b13723170314fd6f43511a1b1b56c5c7a8db32`.

An independent compatibility audit reproduced the completed v4 fit audit without changing its historical receipt: the dataset and model-lock hashes, 75 candidate names/checkpoint hashes, nine actor replays and neural schedules matched; validation MSE differences were below `1e-12` due to floating-point accumulation order. The current auditor supports the registered v1 round1, v1 round2 and v3 round3 populations. Exact old/new source hashes are recorded in the v6 dataset compatibility receipts.

Two fit launches failed before any candidate started and remain preserved: v5 hit the old trainer schema guard; v6 hit a missing `numpy` import in the new dataset contract check. The trainer now verifies v3 population, split, physical flags and weight counts, and the next attempt uses a distinct v6 dataset and v7 handoff.

At 16:55 CST, v7 is active on CPU6, one thread, `MemoryMax=3 GiB`, `MemorySwapMax=0`: 8/75 fits are complete, MLP seed01 candidate00 is running, with no fit failures. Memory was about 1.30 GiB. This is fit progress only; no new fixed27 result or unseen108 evaluation exists yet. GitHub could not be reached; cached main is `450dcce3cea6c7cd4a1a2eb67535aa5ac417edbd` and cached baseline is `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`. Nothing from this continuation is claimed pushed or shared.

The four probes ran sequentially on CPU6, one thread, `MemoryMax=3 GiB`, `MemorySwapMax=0`. Each completed 500 actions / 400,000 physical substeps. Independent replay verified the student prefix and mixed action/filter history exactly (`max_abs_error=0`) for all four. The independent audit status `passed` means provenance and replay were reproduced; it does not override qualification failures.

## Results

| Probe | Student prefix | Task | Strict | Machine gate | Peak external penetration | Executed teacher suffix | Training eligible |
|---|---:|---:|---:|---:|---:|---:|---:|
| MLP seed01, post-yield | 5.20 s | pass | pass | pass | 0.03708 mm | 370 frames | yes |
| MLP seed01, late-yield | 7.00 s | pass | pass | pass | 0.03708 mm | 325 frames | yes |
| MLP seed03, early handoff | 4.48 s | pass | fail | fail | 0.25188 mm | 388 frames | no |
| MLP seed03, later pre-limit handoff | 4.60 s | pass | fail | fail | 0.23600 mm | 385 frames | no |

The two seed01 cases show that the unchanged teacher can complete these two post-yield student states under the current gates. The seed03 interventions still exceed the frozen 0.20 mm penetration limit after teacher takeover. This does not isolate a single cause: it shows that the tested seed03 states cannot safely be repaired by these two takeover times. Both failures remain preserved and are excluded from fitting.

## Shared Refit

The new dataset is `outputs/contact_yield_recovery_retrain_20261030_v4/data/training_data.npz`, SHA256 `bcfe105df77080e7604a1725011e63bf8a2f786346966afae4e7300bb87dfc12`. It carries the prior common 34-episode dataset plus the two qualified seed01 recovery suffixes: 36 episodes, 19,500 frames, 1,480 zero-weight student warmup frames and 2,270 teacher-supervised recovery frames in total. The original six pure-teacher validation identities are unchanged. No counterfactual prefix is teacher-labelled.

The common ESN/RNN/MLP fit used the existing registered 75-candidate budget, three fixed seeds, the same validation selection rule, and 32,000 updates for each neural candidate. All 75 fit receipts and all nine selected models completed. The independent fit audit passed after its schema check was extended to recognize this explicitly marked augmentation round; it verified all nine frozen actor replays. The first audit attempt failed because the old auditor hard-coded the previous 34-episode population. That failure receipt remains in the training handoff; no fit was repeated or changed.

The independent fixed27 train-identity review passed. It covers only the existing `rod_00`, `ball_00`, and `corner_00` training identities, with no reselection or unseen108 access. The v4 lock scored Task 27/27 and Strict 24/27. ESN and RNN each scored 9/9 Strict; MLP scored 6/9. Rod MLP seed01 still misses the required yield/rejoin timing (Task pass, machine-safe); seed02 exceeds the 0.20 mm penetration gate at 0.21267 mm (Task pass, Strict and machine gate fail); seed03 now passes. The prior recovery-enhanced fixed27 had only 1/3 rod MLP Strict. Thus the shared refit improved one of the three MLP seeds but did not qualify the whole model family. Actor and filter replays across all 27 rows were exact (maximum absolute error 0).

The final108 handoff remains `development_not_qualified_no_final_dispatch`; no test conditions were read. Further repair is focused on the two remaining rod MLP failures, using earlier student-to-teacher handoff states at 4.48 s and 4.60 s for seeds01 and02. This second probe campaign is now running sequentially. Any new executed teacher suffix still must independently pass the unchanged gates before it can enter another shared refit.

## Receipts

- Probe registration: `outputs/contact_yield_targeted_recovery_20261030_v1/REGISTRATION.json`, SHA256 `d97473a96ba09ebd2b1ccba807cde6dd683d9f1613cf5301eef14c9f5d39c310`.
- Probe execution: `outputs/contact_yield_targeted_recovery_20261030_v1/execution.json`, status `complete_four_recovery_probes_pending_shared_data_decision`; four full rows, no infrastructure error.
- New dataset registration: `outputs/contact_yield_recovery_retrain_20261030_v4/REGISTRATION.json`; dataset hash above.
- Fit handoff: `outputs/contact_yield_recovery_training_handoff_20261030_v4/REGISTRATION.json`, SHA256 `8ae5fe2f141cc9508d2782a2684267584eda28b9b9309856cc684ab4a7d3bd5b`.
- Independent fit audit: `outputs/contact_yield_recovery_retrain_20261030_v4/FIT_AUDIT.json`, status `passed`, 75 candidate fits and nine exact frozen actor replays.
- Fixed27 v2: `outputs/contact_yield_targeted_student_development_20261030_v2/`; `REVIEW.json` status is `verified_fixed27_development_diagnosis`, 27/27 complete and independently replayed.
- Early rod recovery probe v1: `outputs/contact_yield_mlp_rod_early_recovery_20261030_v1/`; four cases, current status in `execution.json`.
- At the time of this report, GitHub was unreachable from the local environment. Cached `origin/main` was `450dcce3cea6c7cd4a1a2eb67535aa5ac417edbd`; cached `origin/baseline` was `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`. These are not claimed as current remote refs.
