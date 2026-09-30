# ESN Algorithm-Only Screen, 2026-09-29

## Scope

This screen changed only the ESN inference algorithm. The office-v5 combined-v4
fixture, seed, action7 contract, actor-visible canonical48D fields, actuator
amplitude/slew limits, external-penetration gate, and evaluation arguments were
held fixed. All runs used the registered development step `dt=1e-4`; none is a
formal `dt=5e-5` safety result. Every failed rollout and raw trace is retained.

Fixed evaluation arguments: `combined-contact-v2`, `corner-placement`,
`events=all`, `task=pick_place`, `duration=30 s`, seed `2026091751`, ball speed
`1.7 m/s`, launch `2 s`, person start/stroke `3 s/.2 m`, rod start/hold/stroke
`7 s/6 s/.235 m`.

## Results

| candidate | task/strict | final stage | ext. penetration (mm) | RMSE (m) | peak torque (Nm) | peak speed (m/s) | cup s | pillar s | rebound |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| pure ESN | no/no | carry | 0.12913 | 0.10738 | 35.79 | 0.09140 | 11.756 | 0 | no |
| VMC/ESN 50% | no/no | carry | 0.19068 | 0.08369 | 43.67 | 0.08326 | 0 | 5.891 | no |
| VMC/ESN 75% | no/no | carry | 0.11268 | 0.09404 | 39.06 | 0.07383 | 0 | 0.226 | no |
| ESN shadow, zero applied residual | no/no | carry | 0.10125 | 0.07614 | 35.39 | 0.06411 | 0 | 16.272 | no |
| load-gated ESN, release tau 0.64 s | no/no | carry | 0.17152 | 0.07212 | 37.78 | 0.07506 | 0 | 11.071 | no |
| quiet-centered ESN, center tau 0.64 s | no/no | carry | 0.12190 | 0.09182 | 37.77 | 0.07315 | 0 | 0 | no |
| quiet-centered ESN, center tau 2.56 s | no/no | carry | 0.16054 | 0.09756 | 34.60 | 0.07416 | 0 | 0 | no |

The pure ESN result is physically gentle and avoids prolonged pillar contact,
but leaves a near-constant residual in carry. The 50% and 75% blends trade
task progress against contact and do not complete placement. The shadow run
shows that the frozen fixture also blocks the unchanged WBC route, so zeroing
the ESN is not a success oracle. The new quiet-centered variants reduce the
persistent readout bias but do not create the missing route-level retreat and
release behavior.

## New algorithm

`proprio48_esn128_action7_load_gated_v1` and
`proprio48_esn128_action7_quiet_centered_v1` are implemented in
`scripts/current_student_policy_20260921.py`. The reservoir always advances.
The output gate uses only the existing canonical48D joint-load estimate
(`32:39`) and estimated wrench (`39:45`); no contact truth, ball state, event
time, task stage, visual/range, or geometry is exposed. Gate scales and center
were calibrated from the six saved teacher traces only:

* load scale `1.52071085098`, wrench scale `3.47030568491`;
* center `0.64`, width `0.10`, attack tau `0.04 s`;
* release tau `0.64 s` for the direct gate;
* quiet-centering tau candidates `0.64 s` and `2.56 s`.

The teacher-only activity classifier has balanced accuracy `0.93450` (TPR
`0.95828`, TNR `0.91072`). The source and checkpoint lineage is recorded in
the model sidecars under
`outputs/esn_combined_v4_algorithm_screen_20260929/models/`.

## Conclusion

No candidate passes the unchanged combined task. This is a real negative result,
not a gate failure: the ball rebound condition is still false and the combined
contact/placement contract is unmet. The best algorithm-only safety/trajectory
tradeoff in this screen is the load-gated model (RMSE `7.21 cm`, external
penetration `0.172 mm`), while pure ESN gives the cleanest pillar-avoidance
behavior. Further progress requires a learned route/retreat policy or new
teacher trajectories; changing environment geometry or gates would invalidate
the baseline comparison and is explicitly out of scope here.

## Follow-up pure-ESN readout screen, 2026-09-29

The next pass kept deployment strictly pure ESN (`hybrid_vmc_blend=0`) and
changed only the reservoir/readout algorithm. A current-source VMC diagnostic
was also run to separate teacher feasibility from student fitting: under the
same combined-v4 fixture it reached `carry`, had no ball rebound, external
penetration `0.27809 mm`, peak torque `45.44 Nm`, peak speed `0.10815 m/s`, and
was task/strict false. It is retained as a diagnostic and is not a proposed
method result.

| candidate | task/strict | final stage | ext. penetration (mm) | RMSE (m) | peak torque (Nm) | peak speed (m/s) | cup valid | rebound | failure |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|
| shared dual readout, qvel gate | no/no | carry | 0.15216 | 0.06220 | 46.40 | 0.07473 | no | no | cup tilt/shift and no rebound |
| shared dual readout, impact gain 1.5 | no/no | carry | 0.16931 | 0.06089 | 46.18 | 0.10477 | no | no | cup placement failed |
| shared dual readout, conservative gate | no/no | carry | 0.55200 | 0.06322 | 51.74 | 0.07461 | no | no | physical validity failed |
| shared dual readout, channel gains | no/no | lift | 0.17801 | 0.66332 | 41.68 | 0.19276 | yes | no | route diverged |
| shared dual readout, impact gain 2.0 | no/no | aborted | 0.94562 | 0.08124 | 51.29 | 0.26606 | no | no | global penetration exceeded 2 mm |
| fixed-reservoir ridge from saved hybrid actions | no/no | carry | 0.24366 | 0.06679 | 45.03 | 0.08325 | no | no | no rebound; pillar contact |
| fixed-reservoir NumPy MLP from saved hybrid actions | no/no | carry | 0.19572 | 0.06653 | 44.27 | 0.10602 | yes | no | no rebound; no placement |

The ridge and NumPy MLP checkpoints were trained from actual 48D observations
and applied actions in retained same-fixture hybrid rollouts, then evaluated as
standalone ESNs. This is an offline data-source experiment, not a hybrid
deployment claim. The actor still received only canonical48D proprioception;
contact truth, ball state, event time, task stage, visual/range and geometry
were excluded. The PyTorch version of the same fitting attempt failed before
training because `libtorch_cpu.so` could not be mapped under the 3 GiB address
limit; that failed attempt is retained and did not produce a checkpoint.

The qvel-gated head is the best pure-ESN trajectory tradeoff in this follow-up
(`6.09 cm` RMSE at `0.16931 mm` penetration), but it still does not satisfy the
combined task. Increasing only impact-head gain does not recover ball rebound:
gain 2.0 becomes physically invalid, while channel-specific gains destabilize
the route. These results rule out further threshold/gain tweaking as evidence
of success. No candidate passed unchanged task and strict gates, so formal
`dt=5e-5` evaluation remains locked. All raw rollouts, failed checkpoints,
sidecars and source hashes are under
`outputs/esn_combined_v4_algorithm_screen_20260929/`,
`outputs/esn_pure_distill_hybrid_trace_20260929/`, and
`outputs/esn_algorithm_diagnostic_teacher_current_20260929/`.

Independent action replay of the best impact-gain checkpoint and the NumPy MLP
checkpoint reproduced every saved `esn_action` sample exactly (`max abs diff =
0` over 750 policy steps each). This validates the action/reservoir execution
chain; it does not turn either failed rollout into a task success.

## Matched office-v5 six-condition ESN/MLP comparison, 2026-09-29

The separate office-v5 six-condition screen kept the unchanged 55 s development
fixture, canonical48D input, action7 interface, gates and actuator limits. The matched
MLP was `48-128-128-7`; the ESN used a 128-unit multi-timescale reservoir and
128-unit nonlinear readout. Both therefore have 256 hidden/state units under the
explicit equal-neuron accounting used here. No forbidden field entered either actor.

| candidate | task | strict | hard task | hard penetration mm |
|---|---:|---:|---:|---:|
| matched MLP128 exposure-v3 | 5/6 | 3/6 | false | 0.187--0.198 |
| exposure-balanced ESN v1 | 6/6 | 3/6 | true | 0.1788 |
| exposure DAgger3 ESN | 6/6 | 4/6 | true | 0.1790 |
| fail-focused DAgger4 ESN | 5/6 | 3/6 | false | 0.2080 |

DAgger3 is the selected algorithm-only candidate: it has a reproducible `+1` task
and `+1` strict advantage over the matched MLP on this fixed development screen.
DAgger4 is a pre-registered negative follow-up that oversampled the two DAgger3
failure-condition visits; it is retained and not selected. All rows are `dt=1e-4`
development results, not formal `dt=5e-5` or hardware claims. DAgger4 raw traces and
audit are in `outputs/esn_office_joint_esn_stiff_20260929/dagger4_eval/`.

Across the six development conditions, DAgger3 had mean/max waypoint RMSE
`152.18/163.76 mm`, peak torque `37.42/40.99 Nm`, peak speed
`0.13322/0.14078 m/s`, and penetration `0.16823/0.17896 mm`. The MLP had
`151.44/165.93 mm`, `35.77/36.63 Nm`, `0.13458/0.14330 m/s`, and
`0.18980/0.19814 mm`, respectively. Thus the ESN's task/strict gain comes with a
moderate torque increase, while penetration and worst-case tracking remain within
the unchanged development gate; this trade-off is reported rather than hidden.

## Teacher-response transfer screens, 2026-09-29

The remaining strict failures were traced to the unchanged exposure gate: DAgger3
rod contact duration was `0.2771 s` for rod-start9 and `0.1206 s` for shift-plus,
below the fixed `0.4 s` hand/rod requirement. The stiff teacher itself produced
`0.2886 s` and `0.1431 s`. The pre-registered damped teacher (half action, damping
x2) raised rod-start9 to `0.7930 s` and passed task/strict, but shift-plus remained
at `0.2383 s`. Uniform scales 0.4 and 0.6 did not improve either condition.

| candidate | teacher/ESN data change | task | strict |
|---|---|---:|---:|
| DAgger3 | stiff labels on exposure-balanced ESN visits | 6/6 | 4/6 |
| DAgger5 | balanced DAgger3 visits, one copy per condition | 6/6 | 3/6 |
| DAgger6 | raw damped teacher rod9/shift traces added | 5/6 | 3/6 |
| DAgger7 | damped labels on the same DAgger3 visits | 6/6 | 3/6 |

DAgger6's rod-start9 task regression and DAgger7's unchanged strict count show that
teacher action quality alone does not transfer through the current student readout;
the student needs a route-specific recovery state that is not sufficiently represented
by the current canonical48D history. Every follow-up had zero action/reservoir replay
error and passed physical-substep recomputation. DAgger3 remains selected. Raw traces,
plans, checkpoints and lineage are archived in
`outputs/esn_office_joint_esn_stiff_20260929/`.

## Matched-budget dual-readout follow-up, 2026-09-29

The dual-readout follow-up kept the same 256 hidden/state-unit budget as the
matched MLP and changed only the ESN readout organization. A shared 128-unit
reservoir feeds separate 64-unit route and recovery heads. The causal selector
uses only `||qvel_t-qvel_{t-1}||` from canonical48D; no contact, ball, event,
stage, visual or distance field enters the actor. Route labels use retained stiff
teacher traces and recovery labels use fixed damped-teacher traces plus DAgger3
visits. Checkpoint SHA256:
`ab9059fa35b11535939a1b4bd85f8d8861b46fce643371211ee7446565a42d3d`.

On the unchanged six-condition development screen (`dt=1e-4`), independent
audit gave task `6/6`, strict `3/6`:

| condition | task | strict | RMSE mm | peak torque Nm | peak speed m/s | penetration mm | rod contact s |
|---|---:|---:|---:|---:|---:|---:|---:|
| original | pass | pass | 155.037 | 36.181 | 0.143372 | 0.196690 | 0.8964 |
| rod-start7 | pass | pass | 132.259 | 38.448 | 0.143372 | 0.196690 | 1.3925 |
| rod-start9 | pass | fail | 137.435 | 40.358 | 0.143372 | 0.196690 | 0 |
| rod-hold6 | pass | pass | 156.083 | 36.181 | 0.143372 | 0.196690 | 0.9493 |
| shifted-plus | pass | fail | 140.364 | 36.269 | 0.115101 | 0.175997 | 0.2659 |
| hard | pass | fail | 163.903 | 36.414 | 0.121416 | 0.207867 | 1.1618 |

Action and reservoir-state replay errors were zero for all six episodes, and
independent physical-substep recomputation matched the saved metrics. The
selector did not recover the two exposure-sensitive rod conditions and degraded
strict count relative to DAgger3 (4/6); this candidate is retained as a negative
mechanism result and is not promoted to combined-v4 or formal `dt=5e-5`.

## Damped-label impact-response follow-up, 2026-09-29

One fixed follow-up retained the DAgger3 route head and fitted a second readout
from the damped-label DAgger7 checkpoint. A causal qvel-transient gate blended the
heads; the reservoir, action filter and 256-unit accounting were unchanged.
Checkpoint SHA256 is `b936be8b95fde31e0049606f9ce83321b3191b3dce8e6e71aebed23d6e64b826`.

The independent six-condition audit gave task `6/6`, strict `3/6`:

| condition | task | strict | RMSE mm | peak torque Nm | peak speed m/s | penetration mm |
|---|---:|---:|---:|---:|---:|---:|
| original | pass | pass | 159.960 | 37.283 | 0.143233 | 0.196159 |
| rod-start7 | pass | pass | 136.166 | 40.753 | 0.143233 | 0.196159 |
| rod-start9 | pass | fail | 147.518 | 40.756 | 0.143233 | 0.196159 |
| rod-hold6 | pass | pass | 163.571 | 37.283 | 0.143233 | 0.196159 |
| shifted-plus | pass | fail | 136.927 | 36.343 | 0.115233 | 0.176815 |
| hard | pass | fail | 164.796 | 36.348 | 0.118440 | 0.207172 |

Action and reservoir-state replay were exactly reproducible and physical-substep
metrics matched. Strict count did not exceed DAgger3, so the route/impact split is
retained as a negative result and no further gate sweep is justified.

## Direct DAgger3 transfer to frozen combined-v4, 2026-09-29

The selected DAgger3 pure ESN was evaluated once in the unchanged combined-v4
fixture containing the ball, person, rod, cup/pillar interaction and corner
placement. The run used `hybrid_vmc_blend=0`, development `dt=1e-4`, the original
task and strict gates, and no new actor field. It reached `carry` and failed both
task and strict. Independent replay was exact (`0` action and reservoir-state
error). The physical metrics were RMSE `90.371 mm`, peak torque `42.324 Nm`, peak
speed `0.070400 m/s`, and external penetration `0.099829 mm`.

The failure was a sustained pillar interaction from `16.728 s` through the end of
the `55 s` rollout (`23.896 s` contact), with no placement or ball rebound. Thus
the six-condition DAgger3 gain does not transfer to the final combined fixture;
the raw rollout, execution manifest and substep audit are retained under
`results/dagger3_combined_v4/` and
`outputs/esn_office_joint_esn_stiff_20260929/dagger3_combined_v4_audit/`.

## Combined-exposure DAgger8 follow-up, 2026-09-29

To test whether the combined failure was simply missing state coverage, one
additional pure ESN was trained with the actual DAgger3 combined-v4 rollout
included once as an exposure trace and relabeled by the same stiff VMC teacher.
The world, gate, action interface, actor fields and actuator limits stayed fixed.
Checkpoint SHA256 is `03fec322b4c9c84b48ab1842de49dd0dab95abdbd3e332b6532b4c30b1754142`.

The unchanged combined-v4 re-evaluation still failed task and strict at `carry`.
It improved the physical trajectory metrics to RMSE `53.364 mm`, peak torque
`44.899 Nm`, peak speed `0.068360 m/s`, and external penetration `0.091927 mm`,
but pillar contact lasted `22.189 s` (from `15.141 s` to the end), cup shift was
`1.373 mm`, and no placement/rebound occurred. Action and reservoir-state replay
were exact. This is a useful tracking improvement without task recovery; the
failure and all raw files are retained under
`outputs/esn_office_joint_esn_combined_dagger8_20260929/` and
`results/combined_dagger8_v4/`.
