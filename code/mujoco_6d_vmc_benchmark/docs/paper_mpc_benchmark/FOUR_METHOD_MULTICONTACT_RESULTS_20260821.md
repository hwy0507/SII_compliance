# Four-method multi-contact MuJoCo results — 2026-08-21

## Confirmatory result

On one new, predeclared held-out cohort of 40 matched `positive_y`, finite-mass ellipsoidal-hand-proxy fixtures, the frozen proposed ESN achieved **38/40 (95.0%)** success. The frozen VMC baseline achieved **31/40 (77.5%)**; the selected memoryless MLP and nominal-only PaperMPC each achieved **0/40**.

The ESN therefore outperformed validation-selected VMC *in this declared in-distribution contact distribution*: matched at-grasp error was **−3.788 mm** (ESN minus VMC; fixture 95% bootstrap CI **[−6.741, −1.086] mm**, seed 95% CI **[−6.458, −1.422] mm**) and matched success exact paired-binomial test was **p = 0.0391** (8 ESN-only wins, 1 VMC-only win).

This is not evidence of universal contact OOD generalization or real-robot performance. The earlier direction/geometry-shift ESN failure must remain reported alongside this result.

## Protocol and fairness controls

The protocol was written before MLP training and test execution in [`FOUR_METHOD_MULTICONTACT_PROTOCOL_20260821.md`](FOUR_METHOD_MULTICONTACT_PROTOCOL_20260821.md). All 160 runs use the same generated fixture for each `(seed, fixture_index)`, the PaperMPC nominal WBC backend, FR3 torque limits, residual safety clamp and success criterion. Test seeds were `20261516–20261525`, with four fixtures per seed. No test fixture was used for ESN training/CEM, VMC selection, MLP selection, or rerun-based tuning.

The proposed controller is the frozen 320-unit fast--slow Direct ESN trained as `successful-only multi-contact BC + train-only CEM bounded readout-row gains`, deployed at 5% residual budget. VMC is the previously validation-selected analytic torque-residual controller (`k=1.0`, 2% budget). The MLP is a strict memoryless 32-D behaviour-cloning baseline at 5% budget: it uses precisely the ESN deployable observation (`q`, `qdot`, nominal twist, pose error, WBC twist error), exact same 18 successful contact traces plus one neutral trace, and no contact force, fixture parameters, geometry, direction, timing, or future information. Per-trace action labels were converted from their recorded residual budget to the common 5% deployment unit.

The four predeclared MLP candidates used hidden widths `{64, 128}` and seeds `{20261501, 20261502}`. All were 0/20 on independent validation. The predeclared selection rule then selected `h64_s20261502` because it had lower mean at-grasp error (29.795 mm). The nominal baseline invokes original PaperMPC with a zero compliance residual; its supplied 5% environment residual scale has no behavioural effect because emitted residual action is zero.

## Full held-out table

Values are mean ± population SD over all 40 rollouts, including failures. `Recovery` is only defined where a rollout returns below the recovery threshold after measured impact, so it is not a success-only timing metric.

| Method | Budget | Success | At-grasp error (mm) | Peak post-impact error (mm) | Peak force (N) | Peak torque (N·m) | Contact bouts | Hard limit | Recovery (s; n) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Original PaperMPC, nominal only | zero residual | 0/40 (0.0%) | 30.432 ± 1.555 | 74.637 ± 2.380 | 95.662 ± 24.475 | 32.282 ± 0.082 | 3.325 ± 1.403 | 0/40 | — (0) |
| VMC, frozen `k=1.0` | 2% | 31/40 (77.5%) | 19.668 ± 7.642 | 126.338 ± 3.804 | 96.167 ± 24.777 | 32.846 ± 0.468 | 2.200 ± 0.458 | 1/40 | 1.480 ± 0.000 (1) |
| MLP BC, selected `h64/s20261502` | 5% | 0/40 (0.0%) | 29.429 ± 1.251 | 73.203 ± 4.715 | 96.129 ± 24.341 | 34.442 ± 0.953 | 3.125 ± 1.144 | 1/40 | — (0) |
| **Proposed ESN, frozen CEM readout** | **5%** | **38/40 (95.0%)** | **15.880 ± 2.747** | **81.916 ± 12.880** | **95.797 ± 24.494** | **34.036 ± 0.721** | **2.450 ± 0.630** | **1/40** | **1.529 ± 0.137 (37)** |

## Matched ESN comparisons

Negative differences favour ESN for error, force, torque, and contact bouts. Force is essentially tied in magnitude and should not be presented as a material safety win. ESN is not uniformly best in every safety metric: versus VMC it uses +1.189 N·m peak torque (fixture 95% CI [+0.846, +1.511]) and +0.250 contact bouts (95% CI [+0.100, +0.425]), although every method has only 0--1 hard-limit event in 40 trials.

| ESN minus comparison | At-grasp error (mm), fixture 95% CI | Seed 95% CI | Success discordance / exact p | Other material trade-offs |
|---|---:|---:|---:|---|
| PaperMPC nominal | −14.552 [−15.667, −13.448] | [−15.262, −13.875] | 38 ESN-only / 0 Paper-only; 7.28e−12 | Peak torque +1.753 N·m; post-impact error +7.279 mm. |
| VMC | −3.788 [−6.741, −1.086] | [−6.458, −1.422] | 8 ESN-only / 1 VMC-only; 0.0391 | Peak force −0.371 N (tiny); torque +1.189 N·m; bouts +0.250; post-impact error −44.422 mm. |
| MLP BC | −13.549 [−14.548, −12.592] | [−14.167, −12.958] | 38 ESN-only / 0 MLP-only; 7.28e−12 | Peak force −0.333 N (tiny); torque −0.407 N·m; bouts −0.675; post-impact error +8.713 mm. |

## Reproducibility artifacts

Server output directory: `/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_four_method_mlp_20260821/`.

| Artifact | SHA-256 |
|---|---|
| `mlp_validation_results.json` | `2ce1ee071917e7d6f673e5cff35f95bfb1be0e3bd42b0bf68491d28a76d2b412` |
| `four_method_heldout_results.json` | `5409f4e25b3d5be14d9e642e9985329ba4323e9931ebe87814518b0dbbe112e2` |
| `four_method_heldout_analysis.json` | `1b6bb0cc2a85b8de368f03e1c50447975c7ccbdf0db9ceb32cd2193f7d98c81e` |

Local ignored copies are in `outputs/paper_mpc_four_method_mlp_20260821/`. The scripts used are `scripts/train_mlp_baseline.py`, `scripts/run_multicontact_four_method_benchmark.py`, and `scripts/analyze_four_method_benchmark.py`.
