# Causal closed-loop ESN design protocol

## Hypothesis

ESN-v2 stores the history of WBC state and tracking error, but cannot tell
whether a continuing error follows the external perturbation or its own recent
bounded yield command.  The new ESN-v3 recurrence therefore appends the prior
**physical** residual command after the shared action filter:

`[q, qdot, WBC twist, WBC pose error, WBC twist error, prior filtered slowdown, prior filtered yield twist]`.

The PPO readout still sees the current 32-D state plus the 128-D reservoir
state.  The 7-D residual context is not exposed as a direct PPO feature.

## Information boundary

The context is available causally at the control instant because it is the
previous WBC scale and Cartesian twist emitted by the shared safety filter.
It excludes raw policy action, contact flag, force, rod state, obstacle pose or
geometry, future release, fixture ID, reward, and phase label.  ESN and VMC
remain independent controller families.

## Design-before-training procedure

A fixed, WBC-error-only excitation law generated 9 physical MuJoCo traces from
the isolated post-V4 development-train fixtures.  It was used only to reveal
the joint/WBC/action-filter dynamics, not as a performance baseline.  A 160
candidate Fan Ye CR/ESPI screen on the resulting 39-D robustly normalized
traces found four Pareto candidates.  No PPO reward, validation return, or V4
final outcome entered screening.

The frozen reservoirs are:

| role | candidate | nodes | time constant | CR | ESPI | reservoir bandwidth |
|---|---:|---:|---:|---:|---:|---:|
| fast loading | 107 | 64 | 48.32 ms | 0.9766 | 8.10e-11 | 6.29 Hz |
| slow recovery | 24 | 64 | 126.36 ms | 0.8534 | 4.90e-10 | 3.71 Hz |

The physical probe bandwidth was 6.59 Hz.  The fast reservoir matches the
loading band, while the slow reservoir supplies a deliberately longer settling
memory.  Its lower CR is reported rather than hidden; this is a timescale
complement, not a claim that both reservoirs maximize the same criterion.

## Promotion rule

The next test is a paired 102,400-step current-state MLP versus
`fan_ye_closed_loop_esn` smoke under the frozen impulse-constrained reward and
same development manifest.  Both lanes must reach full task/no-rod success, at
least 8/9 effective collisions, and no hard torque limit.  Recovery RMSE,
rejoin latency, impulse, jerk, and peak torque are all reported; no single
metric may be used to claim universal dominance.
