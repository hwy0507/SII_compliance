# ESN safety and cross-condition robustness report (2026-09-26)

## Bottom line

R30 is the first proposed ESN checkpoint to satisfy the complete predeclared
**guarded moving-rod benchmark** claim: task+strict `17/17` on all exposed 9330--9357 conditions,
followed by task+strict `8/8` on the once-only frozen 9360--9367 blind set.
Blind maximum penetration was 0.183139 mm against the unchanged
`all_external_max_penetration <= 0.2 mm` gate.  This supports the specific
claim **cross-condition robust in the audited guarded-rod MuJoCo setup**.

It does **not** establish completion of the full office-v5 scene.  The first
canonical48 R30 transfer to that historical exposed scene was run after the
guarded-rod audit and failed: the policy remained in approach for all 525
control steps, task and strict success were false, and required person-hand
contact was absent.  External penetration still passed at 0.177712 mm.  The
reservoir selector false-triggered its 20-step pulse at 0.08--0.84 s instead
of after loaded lift, directly exposing an office-domain history shift.

The mechanism is reservoir-timed rather than fixture-conditioned.  A learned
stage-3 detector reads only the proprio48-driven reservoir history, waits until
after grasp/loaded-lift, and applies a fixed 20-step +z clearance pulse while
leaving the R15 readout's other six action channels unchanged.  Stage, clock,
fixture identity, geometry, and contact truth are not deployment inputs.

R15 remains historically important: it first passed its nine exposed
development conditions and solved fixture 9332 where the fixed VMC teacher
fails, but its original 9350--9357 blind result was only strict 6/8.  That set
was retained and treated as exposed before R30 was developed; the new
9360--9367 plan was hash-frozen before any R15 blind trajectory was used.

These are simulation results, not evidence of real-robot readiness.  R30's
peak linear speed is about 0.253 m/s, and no HIL, low-speed hardware run,
emergency-stop validation, sensing-delay test, or hardware safety review has
yet been performed.

## Frozen R10 checkpoint

- Model: `outputs/esn_conditioned_progress_20260926_r10/conservative_050/conditioned_progress_adapted.npz`
- SHA256: `2ce4e13d01c205965a9ccd2148acec869ad296915140c336a90751740b2cd3dc`
- Deployment contract: original `proprio48_esn128_action7_v1`
- No stage, clock, geometry, fixture ID, or privileged input at deployment
- Reservoir, normalization, first readout layer, action projection, safety
  filter, physics source, task gate, and penetration gate frozen
- Only the final readout was fit

## R10 development gate (formal promotion)

| Fixture | Task | Strict | Endpoint error (mm) | Lift (m) | Penetration (mm) | Substep RMSE (mm) | Peak torque (Nm) | Peak speed (m/s) |
|---:|:---:|:---:|---:|---:|---:|---:|---:|---:|
| 9330 | yes | yes | 4.586 | 0.24495 | 0.199935 | 61.237 | 36.879 | 0.14824 |
| 9331 | yes | yes | 10.115 | 0.24064 | 0.173571 | 72.067 | 39.340 | 0.13403 |
| 9332 | yes | yes | 12.892 | 0.23866 | 0.185298 | 85.035 | 39.624 | 0.13008 |

The 9330 margin is only 0.000065 mm, so this result is a gate pass but not a
comfortable engineering margin.

## R10 cross-condition result

| Fixture | Task | Strict | Endpoint error (mm) | Lift (m) | Penetration (mm) | Substep RMSE (mm) | Peak torque (Nm) | Peak speed (m/s) |
|---:|:---:|:---:|---:|---:|---:|---:|---:|---:|
| 9340 | yes | no | 6.641 | 0.24315 | 0.201385 | 63.223 | 37.338 | 0.14652 |
| 9341 | yes | yes | 9.902 | 0.24077 | 0.187704 | 71.270 | 38.368 | 0.13866 |
| 9342 | yes | yes | 5.886 | 0.24376 | 0.198960 | 72.386 | 36.717 | 0.14086 |
| 9343 | yes | yes | 11.631 | 0.23946 | 0.188140 | 62.623 | 37.571 | 0.13505 |
| 9344 | yes | no | 3.975 | 0.24571 | 0.206054 | 65.715 | 36.986 | 0.15785 |
| 9345 | yes | yes | 14.202 | 0.23778 | 0.137808 | 91.394 | 41.607 | 0.10977 |

Task success is `6/6`; strict success is `4/6`. No failed episode or unsafe
episode was removed.

## Causal progression

| Round | Change | Task / strict result | Interpretation |
|---|---|---|---|
| R7 | cumulative DAgger only | 2/3 strict on 9330--9332; 9332 task failure | Pure teacher imitation cannot repair teacher failure |
| Teacher 9332 | VMC mixture 1.0 | task failure, 213.457 mm error | Teacher is not a feasible solution on 9332 |
| Neutral WBC 9332 | zero residual | task failure, 230.739 mm error | Recovery requires an active learned response |
| R8 gain 1.0 | global phase-conditional progress label | task 3/3, strict 2/3 | Reservoir recovery fixes 9332; 9330 exceeds strict by 0.004059 mm |
| R9 | recovery labels only on four 9332 histories | task 1/3, strict 1/3 | Sparse failure-only shaping does not generalize |
| R10 gain 0.5 | condition-separated conservative 9330 replay | development task+strict 3/3; cross task 6/6, strict 4/6 | First formal promotion; task robust, safety margin incomplete |
| R11 | weighted zero-progress replay for 9340/9344 | task 5/5, best strict 4/5 | Yield helps 9340 but worsens lowest-height 9344 |
| R12 | dual yield/clearance labels | task 5/5, best strict 4/5 | Correct response direction, insufficient isolation in linear readout |
| R13 | stronger clearance gains and weight | task 5/5, best strict 3/5 | Stronger correction transfers risk to 9332/9340; stop post-hoc search |

## Why the reservoir result is meaningful

The deployed observation never contains the training stage or fixture label.
Constant action bias was previously shown to fail early task phases. The only
mechanism available to express “normal progress,” “yield,” and “clearance” is
the reservoir state generated from proprioceptive history. R8/R10 succeeding
on 9332 while both the VMC teacher and neutral controller fail is therefore a
genuine history-conditioned recovery result, not simple cloning.

The remaining safety failures also identify the current limitation: a single
linear final readout does not cleanly separate two nearby low-height contact
regimes. Increasing a 9344 clearance target eventually shifts penetration to
9332/9340. The next method change should therefore increase readout capacity
or explicitly train a safety-margin objective; it should not continue scalar
gain sweeps on the same conditions.

## Historical recommendation after R10 (completed by R14--R30)

The following was the frozen recommendation at the R10 decision point.  It is
retained as an audit trail; the current result and next hardware-facing steps
are stated in the bottom line and the R30 sections below.

1. Freeze R10 as the task-success reference and retain all unsafe rollouts.
2. Replace the single linear final readout with a small gated/two-expert
   readout driven only by reservoir state, or solve a constrained readout fit
   with explicit high-contact margin penalties.
3. Use 9330--9345 only as development after the reported exposure.
4. Require all nine development conditions to pass with a preferred maximum
   penetration of 0.195 mm before running the already frozen 9350--9357 plan.
5. Run 9350--9357 once. All eight must pass task and the original 0.2 mm gate
   before claiming cross-condition simulation robustness.
6. Only after that proceed to hardware-in-the-loop, low-speed dry runs, and a
   real-robot safety review. No current evidence supports direct real deployment.

## Reproducibility and workspace

Spark campaign root:
`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/esn_reservoir_r5_20260926`

The campaign contains read-only source/model/control snapshots and manifests
for R9--R13. All fixture runs retain commands, return codes, rollout JSON/NPZ,
contact samples, physics-state traces, substep audit manifests, and failed
results. Total concurrent simulation processes never exceeded four.

R9 audit note: its first three 9310--9312 trajectories were an older complete
version (`9930c24b...`, `bc8d5df4...`, `4fe1e789...`) rather than the exact R8
versions. R10 and later corrected this and use the exact R8 hashes
`f0308e7b...`, `5ed4dee2...`, and `98ef3056...`. R9 was not promoted.

## R14 gated-readout audit

R14 implemented a new checkpoint contract with two frozen experts and a
logistic gate that reads only the 128-D reservoir-derived hidden state. The
yield expert was R11 weight 2 and the clearance expert was R8 gain 1.5. The
new contract was syntax checked and loaded successfully; a real archived 48-D
observation produced a finite 7-D action.

The gate did not satisfy its predeclared offline separability condition. At
offset 0 its true-positive rate was 0.9704 but false-positive rate was 0.1579.
Offset -1 reduced false positives to 0.0284 but true-positive rate to 0.8630.
Offset -2 achieved false-positive rate 0.0038 but true-positive rate only
0.05. No R14 physical rollout was launched.

The evidence supports a small nonlinear reservoir-state gate as the next
representation change. It must pass the same offline TPR/FPR requirements
before any physical evaluation; task and penetration gates remain unchanged.

## R15 nonlinear gated-readout audit

R15 keeps the same frozen R11 weight-2 yield expert and R8 gain-1.5 clearance
expert, but replaces R14's logistic gate with a deterministic 16-unit tanh MLP.
The gate still reads only the reservoir-derived hidden state; stage and fixture
identity are used only to construct offline labels. All 24 accumulated
trajectories are retained. The predeclared offline admission thresholds are
TPR >= 0.95, FPR <= 0.01, positive p05 > 0.5, and negative p95 < 0.5.

| Gate offset | TPR | FPR | Positive p05 | Negative p95 | Offline admission |
|---:|---:|---:|---:|---:|:---:|
| 0 | 1.000000 | 0.001804 | 0.992073 | 0.004036 | yes |
| -1 | 1.000000 | 0.001227 | 0.978743 | 0.001488 | yes |
| -2 | 0.996296 | 0.000072 | 0.944253 | 0.000548 | yes |

All three fixed candidates entered the identical five-condition safety screen;
none was selected post hoc. Their checkpoint SHA256 values are `c7a365d3...`,
`a97fae19...`, and `bddeb383...`, respectively. The screen produced task
`5/5` for all candidates and strict results `4/5`, `5/5`, and `3/5`. Only
offset -1 therefore entered the four-condition development remainder, where it
passed task+strict `4/4`. Combined with the screen, R15 offset -1 is
development-qualified at task+strict `9/9`.

The once-only blind result was task `8/8`, strict `6/8`:

| Fixture | Task | Strict | Endpoint error (mm) | Lift (m) | Penetration (mm) | Peak torque (Nm) | Peak speed (m/s) |
|---:|:---:|:---:|---:|---:|---:|---:|---:|
| 9350 | yes | yes | 7.320 | 0.24223 | 0.198418 | 36.549 | 0.14894 |
| 9351 | yes | yes | 9.853 | 0.24039 | 0.178357 | 38.579 | 0.13415 |
| 9352 | yes | no | 8.580 | 0.24129 | 0.203829 | 37.500 | 0.14519 |
| 9353 | yes | yes | 11.711 | 0.23896 | 0.129597 | 43.848 | 0.10663 |
| 9354 | yes | yes | 11.176 | 0.23915 | 0.183115 | 36.858 | 0.12742 |
| 9355 | yes | no | 7.969 | 0.24168 | 0.201331 | 36.601 | 0.16742 |
| 9356 | yes | yes | 12.847 | 0.23884 | 0.095832 | 43.749 | 0.10574 |
| 9357 | yes | yes | 8.634 | 0.24136 | 0.198262 | 36.882 | 0.13430 |

The R15 source/model/control snapshot was frozen read-only before launch. The
uniform recomputation reports have SHA256 `53dea4c8...` (development) and
`12d6ea17...` (blind). The frozen task gate, penetration gate, physics, and
safety filter were unchanged. R15 is a meaningful task-robust result but does
not establish cross-condition safety robustness or real-robot readiness.

## Post-R15 safety closure: R16--R28

All later rounds use the exposed eight-condition screen 9330, 9332, 9340,
9342, 9344, 9352, 9355, and 9357.  Every physical candidate retained task
success on all eight conditions, but no candidate through R28 achieved strict
8/8.  Consequently, at the end of R28 none had entered the nine-condition
exposed remainder and the hash-frozen 9360--9367 blind plan was still
unopened.  R30 later passed both gates and opened that plan exactly once, as
reported below.

| Round | Fixed change | Screen task / strict | Causal conclusion |
|---|---|---:|---|
| R16 | stronger margin expert and nonlinear gate | no candidate 8/8 strict | the expert repairs 9352/9355 but transfers risk to 9330/9340/9342/9344 |
| R17 | hierarchical risk selector above complete R15 | no physical candidate admitted | offset -1 missed FPR (0.01190); offset -2 missed TPR/p05 |
| R18--R19 | calibrated then hard selector | 8/8 / 5/8 for both hard candidates | removing soft leakage still leaves 9330/9352/9355 unsafe |
| R20 | five-step debounce | 8/8 / 6/8 | 9352 and 9355 remain unsafe |
| R21 | latch after debounce | 8/8 / 6/8 | bitwise-identical outcome to R20; switching occurs after the peak is formed |
| R22--R24 | earlier and hard-negative selector diagnoses | offline only | stage-2 hard-negative FPR is 0.51748; pre-contact state identifies phase but not which fixture will cross the gate |
| R25 | universal 30-step phase pulse | 8/8 / 5/8 | repairs 9352 but moves risk to 9340/9344/9355 |
| R26 | full-amplitude pulse for 8 or 16 steps | 8/8 / 3/8; 8/8 / 5/8 | shorter duration is not monotonically safer |
| R27 | 30-step expert interpolation at 0.25/0.50/0.75 | task 8/8 each; strict 3/8, 0/8, 4/8 | continuous expert interpolation creates new unsafe closed-loop trajectories |
| R28 | 45-step slowdown-only floor at 0.25/0.50/0.75 | task 8/8 each; strict 3/8, 4/8, 5/8 | slowing the robot does not slow the externally driven rod and changes contact geometry |

R26--R28 used the same physical-substep measurement path.  The following are
screen aggregates, not substitutes for per-fixture task and safety gates:

| Candidate | Mean substep RMSE (mm) | Max peak torque (Nm) | Max peak speed (m/s) | Max penetration (mm) |
|---|---:|---:|---:|---:|
| R26 pulse8 | 72.4300 | 41.3375 | 0.169900 | 0.206118 |
| R26 pulse16 | 68.6113 | 43.0259 | 0.168650 | 0.206632 |
| R27 scale0.25 | 68.8094 | 40.1178 | 0.169010 | 0.209282 |
| R27 scale0.50 | 65.8735 | 40.7245 | 0.171128 | 0.206959 |
| R27 scale0.75 | 63.3959 | 39.5131 | 0.172559 | 0.208857 |
| R28 slowdown0.25 | 74.9494 | 42.3863 | 0.176550 | 0.209131 |
| R28 slowdown0.50 | 80.1719 | 43.7308 | 0.172943 | 0.213600 |
| R28 slowdown0.75 | 84.1937 | 42.4975 | 0.170960 | 0.215083 |

The R26, R27, and R28 unified summaries have SHA256
`a61131c81369e90ee1e17e9406b48b1007519018c4423feda61c4a668741f476`,
`9b1410eec52290583688e5efde500e261cd1283c873d0f682ca201e427103f19`,
and `070927a56678799c737ec51f2dffd6afb67095278942eb501bf3fbd8f8ba385b`.
R28's Spark source/model/control manifest SHA256 is
`2964be06e95200fec38b5756ecd2bd405711864953db6e42a52809a7ea39f572`.

The most important observability result is negative but useful: all eight
conditions share the same reservoir trigger at control step 53 (2.16 s), while
the dangerous physical peaks occur around steps 71--79.  Before first contact,
proprio48 contains enough history to identify the common task phase but not the
unseen rod height/angle that determines the safest directional response.  The
next predeclared R29 experiment therefore kept the R15 readout and used the
reservoir phase cue only to add upward geometric clearance.  It was frozen
before reading the final two R28 candidates; its result is reported in the
next section.

## R29 vertical-clearance result and R30 timing correction

R29 retained the phase-2 trigger and changed only the +z yield floor.  Floors
0.35 and 0.50 retained task 8/8 but reached strict 4/8.  Floor 0.65 reduced
penetration to 0.002878--0.004952 mm on five conditions, but it also prevented
grasp/stage advancement; the result was task 0/8 and strict 0/8.  The three
candidate aggregates are:

| Candidate | Task / strict | Mean substep RMSE (mm) | Max peak torque (Nm) | Max peak speed (m/s) | Max penetration (mm) |
|---|---:|---:|---:|---:|---:|
| +z floor 0.35 | 8/8 / 4/8 | 85.7272 | 42.5914 | 0.161211 | 0.220566 |
| +z floor 0.50 | 8/8 / 4/8 | 84.5367 | 42.8934 | 0.158667 | 0.215631 |
| +z floor 0.65 | 0/8 / 0/8 | 55.1619 | 39.3403 | 0.152031 | 0.212454 |

The unified R29 summary SHA256 is
`4e1c2e38aa23c99b0cf9b40e817ba9aebc82488b251130b1666fbb41eec88378`;
the Spark source/model/control manifest SHA256 is
`6ba101627d5ab7583b9b7876166bb9a1d761837c09f17366e0fdeb9f3b75034e`.

R30 corrects the identified timing error without scanning another amplitude.
It trains one universal stage-3 detector on all eight retained R29 floor-0.35
histories, gives stage 2 equal hard-negative weight, and keeps the R29 0.65
vertical floor only for 20 steps after stage-3 evidence.  Offline stage-3 TPR
is 1.0 and stage-2 hard-negative FPR is 0.0.  Archived replays trigger strictly
after stage 3: one step after transition on the fit trajectories and three to
four steps after transition on the independent exposed R27/R28 trajectories.
The sole checkpoint SHA256 is
`3f6ed39af0c103ee6af07fada710cd90a781233041fb02c3f850996f22a3aae1`;
the read-only Spark manifest SHA256 is
`56c53d1274d4dbc9fed61f3653aa1eea1b499acfea889e9b764ee232f9931afa`.
Its physical screen was launched only after these checks and passed task+strict
8/8.  Per-fixture maximum penetration was 0.166605--0.185188 mm.  Mean
substep trajectory RMSE was 43.6099 mm, maximum peak actuator torque was
40.9567 Nm, and maximum peak linear speed was 0.253463 m/s.  Thus R30 closes
the exposed screen's penetration margin and tracking error, but does so with a
higher speed peak than R15/R26--R29; that trade-off is reported rather than
hidden.  The screen summary SHA256 is
`4bbc2882e8891536d6e18ca2d4fd6b9516e9b429a14ca2360009c18c2c4a9e50`.
The nine-condition exposed remainder was launched only after this 8/8 result.
It passed task+strict 9/9, so R30 is exposed-development qualified at 17/17.
Across all 17 exposed conditions, maximum penetration was 0.188467 mm, mean
substep trajectory RMSE was 45.0852 mm, maximum peak actuator torque was
41.7355 Nm, and maximum peak linear speed was 0.253463 m/s.  The combined
development summary SHA256 is
`52a6cf0db1bd0e466548ce0821871a591a86d151b9dab94d56a4ec57f844699c`.
Only after this 17/17 result was the precommitted 9360--9367 blind plan run
once.  It was not used for further tuning.

## R30 once-only blind result

| Fixture | Task | Strict | Penetration (mm) | Substep RMSE (mm) | Peak torque (Nm) | Peak speed (m/s) |
|---:|:---:|:---:|---:|---:|---:|---:|
| 9360 | yes | yes | 0.160163 | 42.001 | 37.609 | 0.252826 |
| 9361 | yes | yes | 0.183139 | 44.479 | 38.347 | 0.251201 |
| 9362 | yes | yes | 0.167409 | 46.372 | 38.959 | 0.249647 |
| 9363 | yes | yes | 0.176287 | 44.352 | 37.666 | 0.250710 |
| 9364 | yes | yes | 0.147075 | 47.845 | 40.968 | 0.248161 |
| 9365 | yes | yes | 0.170952 | 42.806 | 37.469 | 0.252291 |
| 9366 | yes | yes | 0.177786 | 47.427 | 39.878 | 0.248578 |
| 9367 | yes | yes | 0.169589 | 43.445 | 37.789 | 0.250686 |

The blind aggregate is task `8/8`, strict `8/8`, mean substep RMSE
44.8408 mm, maximum peak torque 40.9681 Nm, maximum peak speed 0.252826 m/s,
and maximum penetration 0.183139 mm.  The blind summary SHA256 is
`c55288e02bf55b2fe575c5a5c8c9d6b47d21bc6763d5cac2c00c393141b670fa`.
No blind episode was dropped or rerun.  The result establishes the frozen
guarded-rod simulation claim only. The actual office-v5 recovery campaign
must pass before considering hardware-in-the-loop or a real-robot campaign.
Do not tune further on 9360--9367.

## Full office-v5 transfer result (post-audit correction)

The historical exposed office-v5 environment contains a complete articulated
person with finite-mass hand/fingers, a free ball, an independent driven rod,
a cup, pillar, desk, and thick corner.  It is the complex scene intended by
the project handoff; the 9330--9367 moving-rod fixtures are not substitutes
for it.

The frozen R30 checkpoint was connected to the canonical 48-D observation by
supplying the full estimated 6-D wrench; no stage, event clock, person/rod
schedule, geometry, contact truth, or future state was added.  The fixed
seed-2026091751, variant-0, all-events, 21 s pick/place evaluation produced:

- task `0/1`, strict `0/1`, final stage `approach`;
- maximum robot-versus-external penetration 0.177712 mm (safety gate passes);
- ball and rod contact present, required person-hand contact absent;
- the R30 pulse active for the first 20 control steps, 0.08--0.84 s, entirely
  before task progress rather than after loaded lift.

Therefore R30 is safe and cross-condition robust only within the audited
guarded-rod benchmark.  It is not yet successful in the full complex office
task and is not ready for HIL or real-robot deployment.  The raw failure and
offline state replay are retained under
`outputs/esn_r30_office_complex_20260926/seed_2026091751_variant_0/`; this
exposed run must not be relabelled as blind or hidden from reporting.
