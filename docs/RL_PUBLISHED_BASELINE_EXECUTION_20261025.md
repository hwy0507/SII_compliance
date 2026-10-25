# Published compliance baseline: running implementation and evidence

2026-10-25. This records a **new source-built training cohort**, not recovery of
the historical office-v6 MJB or proof that any RL method has converged.

## Authorization and selected method

The active user goal delegates method/interface adaptations, permits simulation
and four RTX4090 GPUs, covers passive, active-short and active-long tasks, and
removes the total training-step cap. Original task/safety gates and public motor
limits remain common. Necessary interface adaptations do not imply permission
to fabricate historical assets, discard failures or label a flat bad policy as
learned convergence.

Primary implementation: the authors' code for **CHEQ-ing the Box: Safe Variable
Impedance Learning for Robotic Polishing**, IFAC-PapersOnLine 2025,
[DOI 10.1016/j.ifacol.2025.10.241](https://doi.org/10.1016/j.ifacol.2025.10.241),
[paper](https://arxiv.org/abs/2501.07985),
[source](https://github.com/Data-Science-in-Mechanical-Engineering/polishing-cheq)
at `1a3c1fee3332848068afdb127c4fa33eee420418` (MIT).
Underlying CHEQ is Reinforcement Learning Journal 2024, not CoRL.

The implementation retains five Q networks, target critics, the authors'
SAC/ensemble update, automatic temperature, uncertainty-dependent nominal/RL
mixing, context in actor/critic, and **raw RL actions** in replay. The same
authors' plain SAC is available as an ablation, not mislabelled as CHEQ.

This is a **CHEQ-core adaptation to FR3 control interfaces**, not a reproduction
of the paper's polishing results or a claim that only the objective changed.
The paper has different observations (including measured F/T and path lookahead)
and pose/gain actions. This cohort uses project proprioception, current control
laws and gates; no polishing-specific success thresholds are transplanted.

| Interface | Policy action | Execution |
|---|---:|---|
| Direct | 7 | WBC authority plus Cartesian velocity residual; shared filter |
| Impedance | 5 | Positive bounded stiffness/damping parameters; repaired native Cartesian torque law |
| Admittance | 7 | Mass/inertia, stiffness and damping parameters; reference offset to shared filter |
| VMC | 7 | Grouped stiffness/damping and readout parameters; repaired physical action units |

All four primary actors receive canonical48 divided by fixed SI scales, plus
their **own mixing weight** (49 total). That extra scalar is algorithm state,
not contact truth, task phase, obstacle pose or a success label. Plain SAC uses
48. The original ESN's 48 inputs and its recurrent state must be disclosed
separately in the eventual comparison.

Platform/training changes: gamma .99 to .9995 for the 55 s horizon; 5000 warmup
transitions instead of the upstream config's 15000; bounded uniform warmup;
local parallel collection; correct next-state mixing context; finite-horizon
terminal masks; full replay/optimizer/temperature/RNG resume. Networks remain
256x256; actor/critic LR 3e-4, tau .005, replay capacity 1M. Initial v1 used
batch256/UTD1; current registered v3 uses batch16384/UTD2 on all four interfaces
following measured GPU throughput. These are adaptations, not paper defaults.
Changing algorithm, reward or observation scaling requires a new registered run.

## Recovered runtime and physical preflight

Actual host: `rltest-1025--a6ed2ff39b3c-s5gnp35dxg`.
All paths below are **on this current server**, not the unreachable old archive.

Base directory:
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`.

- Interpreter: `env/bin/python`, isolated Python 3.11.17, MuJoCo 3.11.0,
  NumPy 2.2.6, Torch 2.8.0+cu128. Full dependencies are in each runtime lock.
- `runtime/source_train04` (current v3; initial v1 used `source_train02`): frozen scripts/tools/assets, the published learner,
  complete hashes, and parameter sources recovered from baseline commit
  `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` with main's existing controller repairs.
- Robot assets: Menagerie `f3b6013629c7b94f8ee93fd977b161fa8350f9bc`, 128 hashed
  FR3/Panda files. No historical MJB/checkpoint identity is claimed.
- Pure physics uses `MUJOCO_GL=disable`. Initial EGL import failure was resolved
  without changing Xorg, display drivers, system services or contact physics.

Actual checks completed:

1. All four GPUs executed CUDA backpropagation.
2. All four control interfaces executed 80 ms physical probes with identical
   initial MJB hash and valid physical telemetry.
3. All four ran ten nonzero CHEQ decisions in 400 ms closed-loop probes, with
   their own mixing context and the real shared control chain.
4. Authors' SAC updated on each GPU using actual physical transitions. Authors'
   ensemble learner also updated on a complete 1375-transition recorded episode.
   Restoring optimizer, target networks, log-temperature and RNG yielded an
   exactly identical next update (parameter/log-alpha difference 0).
5. Two zero-policy construction/preflight episodes ran the full 55 s and reached
   Task/Strict success. The combined-geometry disturbance-off episode's final
   stable-placement certification was about 24.64 s. These are **nominal-control
   feasibility checks**, not trained-RL or disturbed-condition performance.
6. Wrapped replay restored the exact next sampled batch; a reward plateau with
   no improvement is rejected by the convergence-candidate diagnostic. Nine
   existing comparison-metric numerical tests passed.

Small committed evidence:
[`PUBLISHED_COMPLIANCE_PREFLIGHT_20261025.json`](../code/mujoco_6d_vmc_benchmark/docs/evidence/PUBLISHED_COMPLIANCE_PREFLIGHT_20261025.json).
Raw MJB/physics traces, dependency environment and logs stay outside Git.

## Common task cohort and initial failure retained

`runs/cohort30_v2/REGISTRATION.json` freezes 30 training conditions, 10 per
category, generated by the existing teacher-bank sampler. The indices
`0,100,200,300,337,400,500,600,671,900` were selected before physical results.
This is a representative **new 30-condition training set**, not the complete
historical 3000-trajectory corpus or a held-out evaluation.

The initial `cohort30_v1` attempt incorrectly tried to run the later static-map
planner again after introducing the passive fixtures. The planner rejected
contact scenes before simulation. Those failures remain on disk. The corrected
adapter loads the **same frozen nominal plan** from the successful independent
reference for every condition. Obstacles remain physically present and are
absent from that prior map; no per-condition replanning or gate relaxation occurs.
All 30 initial physical probes then passed. Model hashes are checked before
each training episode's first action; source and robot-asset hashes are checked
on construction. Preflight is not a guarantee of task success under disturbance.

The shared evaluator retains the planned-hand-corner success definition, full
55 s horizon, stable released placement, lift, external penetration and abort
criteria. Physics dt is 5e-5 s; servo 4 ms; actor 40 ms (1375 transitions per
complete episode). The old teacher-bank geometry generator supplies disturbance
primitives; the later task's placement gate remains explicit in this new cohort.

## Reward, evaluation and training status

The existing common `spt_v1` physical reward supplies payload progress/occupancy,
time, actual-human-contact torque/force costs, peak torque, penetration, servo
torque slew and strict terminal success. An additional strict-success-only
efficiency bonus is `5*(1 - completion_time/55)`. Failure receives no efficiency
bonus. This is a training surrogate, not an assertion of exact SPT optimization.

Final SPT follows the user's new request: one posthoc global minimum strictly
successful completion time across the registered comparison, labelled
`SPT_empirical`; failures remain in the denominator. No changing empirical
reference is fed into training. Initial engineering torque thresholds are
43.5 Nm for joints1-4 and 6 Nm for joints5-7. Human-contact compliance is time
weighted only during actual human contact; no contact means NA. These thresholds
are engineering references, not a validated human comfort certification.

Initial training `runs/cheq_four_interfaces_seed20261025_v1` failed on all four
methods at about 10009 real transitions. At the second warmup boundary, the
authors' interior uncertainty-to-weight branch returned a NumPy singleton array;
multiplying it by a CUDA action tensor raised TypeError. The adapter now casts
this scalar explicitly, without changing the uncertainty law. A regression test
exercises steps4999/5000/9999/10000/10001/11000 on three independent samplers.

There was no complete-cycle checkpoint before that failure: **the previous
optimizer states were lost**, not resumed. `runs/recovered_replay_v1` retains
10000/10000/10001/10000 completed nonterminal transitions. Recorded physical
telemetry reproduced the rewards with max error0. Raw actions were reconstructed
from nonzero mixed actions/weights with float32 rounding; reapplying the weight
reproduced the recorded mixed action with max error0. Incomplete tails were
excluded. The portable `recover_published_replay_20261025.py` reproduces these
arrays and records source hashes; it is deliberately limited to this cycle-zero,
zero-nominal recovery case. This is not exact optimizer recovery.

A second launch (`v2`) was cancelled before sampling or updates because replay
import repeatedly decompressed NPZ arrays per row. Materializing the columns
once repaired this startup problem. All attempts and failures remain on SSD.

**Current primary run:** `runs/cheq_four_interfaces_seed20261025_v3`, registered
by `runs/cohort30_v2/REGISTRATION_GPU_V4.json`, with frozen `source_train04`.
Direct/GPU0, Impedance/GPU1, Admittance/GPU2, VMC/GPU3 each have nine physics
samplers. Thirty-six samplers and four learner CPUs reserve40 cores. Optimizers
started fresh with the recovered real replay; progress `steps` includes imported
transitions. New optimizer updates and per-method checkpoints were verified.
Current progress is `PROGRESS.json`, failures `FAILURE.json`, and optimizer
metrics `optimizer.jsonl`; do not infer running state from this dated document.

Every1000 new transitions, at complete condition cycles, and on exceptions,
atomic checkpoints retain learner, target critics, optimizers, temperature, RNG
and replay. They explicitly state **environment_state_saved=false**: partial
checkpoint recovery starts new episodes, not exact mid-physics continuation.
`STOP_REQUESTED` inside a method directory drains its current complete cycle.
There is no total-step cap. A plateau candidate requires at least six complete
cycles, improvement >=2 over the first two cycle means, and the last three cycle
means within max(.5,2% of their absolute mean). It remains a **candidate requiring
optimizer and deterministic-policy review**, not an automatic convergence claim.

User subsequently requested GPU utilization >=50% and authorized useful project
training during analysis to protect against the cluster idle shutdown (<15%).
A formal-only60s sample averaged52.98/46.47/51.62/49.71%; a second steady sample
averaged52.65/49.68/50.23/46.72%, including a GPU3 instantaneous0% sample. Thus
four-card sustained50% has **not** yet been demonstrated. Initial emergency
updates on real project transitions were stopped at the formal handoff; they
are not formal policy results. Raw measurements are `runs/FORMAL_GPU_UTILIZATION_60S.json`
and `runs/FORMAL_GPU_STEADY_60S.json`.

The planned authors' **plain-SAC online ablation** has now started separately as
`runs/sac_four_interfaces_seed20261025_v1`, using
`runs/cohort30_v2/REGISTRATION_SAC_ABLATION_V1.json`. Each method gets two physics
samplers and one additional learner CPU, bringing combined allocation to52 of55
cores. It uses the same30 conditions, physical runtime, reward, batch16384/UTD2,
and seed; fresh initialization/replay,48 observations, no CHEQ mixing or ensemble.
It has5000 warmup transitions before updates. Separate artifacts are retained;
these jobs are actual online ablations, not no-op utilization loops. GPU sharing
can reduce primary wall-clock throughput; compare physical steps and full-cycle
learning evidence, not time alone. Additional seeds have not started.

The independent `evaluate_published_compliance_20261025.py` entry point copies
one atomic checkpoint to an immutable evaluation snapshot, validates the same
registration/reference/model hashes, and runs deterministic actions through the
same frozen adapter. It performs no optimizer/replay updates. A condition subset
is explicitly diagnostic, not a complete comparison; physical substep audit is
still required separately. One early Direct snapshot (21000 steps including10000
imported transitions) is being checked on the first registered passive condition
in `runs/interim_direct_deterministic_v1`; this is an integration/early-policy
check, not final acceptance. It uses CPU52/53 while running, for54/55 total cores.
The first evaluator revision and learner source are archived with their exact
execution hashes; subsequent launches resolve the learner from frozen runtime.

Early training evidence is now available: Direct exploration produced approach
penetration aborts, while initial complete55s parameter-policy passive episodes
failed at carry (rough episode return -31). These are initial learning data,
not convergence or a fair final method ranking. Current source/status evidence
is in `PUBLISHED_COMPLIANCE_RECOVERY_20261025.json`; its timestamp is a snapshot,
not a continuously updated dashboard.

No method is currently claimed converged. No ESN comparison or unseen test has
been completed. The designated existing ESN checkpoint remains unavailable:
local searches found none, the old archive is unreachable, and GitHub has no
release assets or Actions artifacts. Training can proceed, but the final paired
comparison requires the actual model; it must not be silently replaced by a
newly fitted ESN or by historical performance numbers.

GitHub main read access works. Write access is unavailable in this session;
local commits are preserved and are not described as pushed.
