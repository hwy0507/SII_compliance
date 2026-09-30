# Delayed-ball ESN redesign report

This report records a development-only scene in which the ball is launched at 2.0 s.
The frozen office-v5 evaluator, t=0 formal condition, safety gates, action limits,
held-out layouts, and pure proprioceptive actor contract were unchanged.

The teacher protocol and four raw rollouts are archived in
`outputs/esn_office_joint_teacher_delayed2_20260928/DELAYED2_AUDIT.json`.
The redesigned ESN keeps 128 reservoir units and action7/canonical48D, but partitions
the matched budget into four leak time scales (32 units each; 0.04, 0.16, 0.64,
and 2.56 s). Training mixes actual stiff-VMC traces from the original and delayed
scenes. The checkpoint SHA256 is
`9739b6644b7bcbc2f7c8e5bee87342482f5ee00c3f543b32604f4fbe7315b5cc`.

| Evaluation | Task | Strict | Key outcome |
|---|---:|---:|---|
| Delayed-ball, 4 conditions | 4/4 | 2/4 | nominal and hard strict; rod timing failures retained |
| Original t=0, 6 conditions | 6/6 | 3/6 | original, rod7 and hold6 strict; hard remains 0.208138 mm |

Both independent audits passed action replay, reservoir replay, and physical-substep
metric recomputation. The model is useful evidence that delayed hard-ball execution is
possible with a pure proprioceptive ESN under the unchanged safety gate. It is not
evidence of held-out or real-robot success, and the current result does not justify
claiming superiority over the existing `wrench1` development candidate.

## Conservative rod timing panel

To separate a short contact window from a student failure, the same checkpoint was
tested with the rod starting at 7 s or 9 s and held for 6 s. Both episodes passed task
and strict gates. Contact exposure was 1.674 s and 0.701 s, respectively, with
0.168514 mm external penetration. The independent replay is archived at
`outputs/esn_office_joint_esn_delayed2_20260928/eval_conservative_rod/ESN_JOINT_AUDIT.json`.

Two fixed teacher response candidates were screened and rejected: action scale 0.75
left short-rod exposure failures and raised delayed-hard penetration to 0.206873 mm;
filter time constant 0.02 s also left the timing failures and raised penetration to
0.221086 mm. The original 0.5 scale and 0.04 s filter therefore remain frozen for
the conservative ESN result.

## Presentation and corner-placement follow-up (2026-09-28)

The conservative delayed rollout was rerendered with the same ESN checkpoint,
same action contract, same delayed-ball condition, and no physics or gate change.
The ordinary 25 Hz video is retained at
`outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout.mp4`; a separate
substep-sampled, 4x playback clip is
`outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout_impact_slowmo.mp4`
and its GIF counterpart. The full rollout remains task/strict true. The impact
event is recorded at 2.0584 s, peak contact force 2071.20 N, and maximum external
penetration 0.188555 mm. The slow clip is a display-only resampling of the same
trajectory; it adds no observation, actuation, reset, or safety-layer logic.

The opt-in `--interaction-demo` scene now moves the physical cup and pillar into
the corner approach after an initial-overlap audit. With the first attempted
placement, the ESN reached real pillar contact for 0.296 s but stopped in carry;
the teacher also stopped, so this is recorded as a geometry/controller-route
failure rather than a student failure. The audit is retained at
`outputs/esn_office_corner_interaction_dev2_20260928/rollout.json`.

The opt-in `--corner-placement` path now has an explicit corner support geom,
destination metadata, and a carry waypoint. Initial geometry and support checks
pass, but the current teacher route still fails to complete the placement in the
30 s probe because the apparatus rail/approach contact blocks the carry stage.
This remains an unfinished development condition; no formal result or ESN
generalization claim is made. The latest audit is
`outputs/vmc_corner_nominal_dev11_20260928/rollout.json`.

## Interaction and corner-placement follow-up (2026-09-28)

The first updated cup placement `[.540,-.255]` was rejected by the initial geometry
audit because the cup handle overlapped the payload by `13.5 mm`; that failed request
is retained. The interaction fixture was then fixed at `cup_xy=[.520,-.330]`, with the
ordinary corner-only fixture unchanged. At display resolution `dt=1e-4` (development
only), the VMC teacher produced a finite cup contact window of `0.278 s` at `56.6 N`
with `1.879 mm` cup shift and `0.267 deg` tilt in
`outputs/vmc_interaction_corner_cup_path5_dt1e4_20260928/rollout.json`. It remained in
carry and had `0.349 mm` global floor-ball penetration, so it is not a formal safety or
task result.

The frozen medium4 ESN in the same fixture produced `3.436 s` cumulative cup contact,
`60.0 N` peak force, `1.112 mm` shift and `0.737 deg` tilt in
`outputs/esn_interaction_corner_cup_path5_dt1e4_20260928/rollout.json`. The complete
render is `rollout.gif`/`rollout.mp4`. It also stopped in carry; this demonstrates a
real low-force cup interaction but does not demonstrate combined obstacle interaction
and corner release. A closer candidate was retained as a negative control:
`outputs/esn_interaction_corner_cup_path7_dt1e4_20260928/rollout.json` pinned the arm
in align with `1618.7 N` peak cup contact and `11.1 mm` shift, and was rejected.

The valid final corner result remains the separate corner-only checkpoint and rollout
`outputs/esn_corner_blend05_targeted3_20260928`, which has task/strict/release true and
`0.001854 mm` maximum external penetration. This separation preserves the frozen gate
and makes the current limitation explicit.

For the impact presentation, a display-only annotated replay was added at
`outputs/esn_office_delayed_conservative_slowmo2_20260928/rollout_impact_slowmo_annotated.gif`
and `.mp4`. It overlays the three-axis end-effector displacement trace and the measured
`0.058 m/s` peak response on the original slow-motion frames; no state, action, actor
input, physics step or gate was changed.

The retained pillar-contact rollout was also rendered read-only from its archived MJB
and state trace as `outputs/esn_office_corner_interaction_dev2_20260928/rollout_pillar_interaction.gif`
and `.mp4`. Its labeled contact window is `12.70–17.67 s`; the underlying rollout
still stops in carry and remains a failure record.

## Combined-v3 geometry diagnosis (2026-09-28)

The resumed run mapped trial42's worst external pair to FR3 `right_finger`
(geom 69), not to the pillar. A shorter/lower contact handle reduced external
penetration to `0.1860 mm`; at its interaction length it still displaced the cup
`16.40 mm` and produced no pillar contact (trial44). A more conservative handle
reduced cup displacement to `8.66 mm` but eliminated both cup and pillar contact
(trial45), so it was rejected as an interaction design.

The registered combined-v3 candidate moved the low-friction pillar to `y=-.330`
on the retreat corridor while restoring the trial44 handle. Trial46 remained a
development-only `dt=1e-4`, 30 s probe: task/strict false, stage `retreat`, cup
contact `1.519 s / 8.88 N`, no pillar window, cup shift `16.40 mm`, external
penetration `0.1860 mm`, peak torque `51.75 Nm`, peak speed `0.07145 m/s`, and
3-D RMSE `0.05882 m`. Raw files are retained under
`outputs/esn_combined_contactv3_handle45_trial46_probe30s_dt1e4_20260928/`.

This rules out handle length alone and a simple pillar-y shift as sufficient for
the combined task. The corner-only ESN result remains valid separately; a single
formal combined-scene success has not been obtained and no gate or actor input
was changed.

## Trajectory-supported pillar candidate (2026-09-28)

Trial47 placed the raised pillar at `[.585,-.300]`, selected from the measured
trial46 hand corridor. It produced a real pillar contact window of `6.8007 s`
(`14.0556--29.9999 s`, peak `116.81 N`), but blocked the arm before release.
The development-only `dt=1e-4` result was task/strict false and physically
invalid: final stage `carry`, no cup contact, cup shift `2.01 mm`, external
penetration `0.22898 mm` against `fr3_link7_collision`, peak torque `47.49 Nm`,
peak speed `0.07475 m/s`, and 3-D RMSE `0.07070 m`. Raw output:
`outputs/esn_combined_contactv4_handle45_trial47_probe30s_dt1e4_20260928/`.

The result confirms that a pillar in the hand corridor is encountered too early;
it is not a combined success. A future candidate needs a post-release teacher
route, not another blind pillar position sweep.

## Resumable overnight campaign (2026-09-28)

`tools/overnight_esn_combined_campaign_20260928.py` completed a first pass under
one thread and a 3 GiB address-space limit. Physics runs intentionally disable
EGL rendering; raw MJB/NPZ/JSON traces are preserved for separate read-only
rendering. The combined-v4 development run failed with pillar contact
`37.4848 s / 125.16 N`, carry blocked, external penetration `0.26623 mm`, and no
placement. The current-source corner-only reference also stopped at load transfer,
so the older targeted3 success cannot be replayed as current-source evidence.

The delayed-ball formal reference passed unchanged gates with `0.18855 mm`
external penetration, `37.76 Nm` peak torque, `0.14243 m/s` peak speed, and
`0.00889 m` 3-D position RMSE. The runner and heartbeat resume only unfinished
cases; they never relax gates or relabel stale media.

### Idempotent resume check (2026-09-28 23:40 +0800)

The runner was invoked again after checking for active evaluators. No evaluator
was running, and all existing raw rollouts and `execution.json` manifests were
preserved without a duplicate simulation. Combined-v4 remains a development
failure (`carry`, pillar contact `37.4848 s / 125.16 N`, external penetration
`0.26623 mm`), so the formal `dt=5e-5` combined rerun remains correctly skipped.
The delayed-ball formal reference remains the current-source formal pass at
`0.18855 mm`. No gate, actor input contract, actuator limit, or held-out
condition was changed.

### Overnight heartbeat resume (2026-09-29 02:40 +0800)

Preflight found no active evaluator. The campaign resumed idempotently and
preserved existing raw rollouts and execution manifests without duplicate
simulation. Combined-v4 remains a failed development candidate at `0.26623 mm`
penetration, so no formal combined rerun was unlocked. The delayed-ball formal
reference remains the current-source pass at `0.18855 mm`; all frozen contracts
remain unchanged.

### Overnight heartbeat resume (2026-09-29 01:38 +0800)

No evaluator was active. The runner completed an idempotent resume using the
existing lock/results and did not start duplicate physics work. Combined-v4
remains a failed development candidate (`0.26623 mm` penetration), so its
formal `dt=5e-5` case stays skipped. The delayed-ball formal reference remains
the current-source pass at `0.18855 mm`; all frozen contracts are unchanged.

### Overnight heartbeat resume (2026-09-29 00:43 +0800)

The campaign was checked for active processes and resumed with its lock and
existing-result checks. It completed without starting duplicate physics work;
source/checkpoint hashes are unchanged. Combined-v4 remains a failed development
candidate (`carry`, `0.26623 mm` penetration), so no formal combined rerun was
unlocked. The delayed-ball formal reference remains the current-source pass at
`0.18855 mm`; frozen gates, actor inputs, actuator limits, and held-out cases
were not modified.
