# Independent ESN overnight multi-seed report

Date: 2026-08-16

## Scope

This report covers the completed post-V4 development campaign only.  The task
uses a physical rod that contacts the Panda end effector during approach; both
actors are evaluated by matched rod/no-rod MuJoCo rollouts.  The fixed WBC,
Panda torque backend, action bounds, safety adapter, fixtures, PPO budget,
seed, and reward profile are shared.  The current-state MLP receives the same
20-D input as Fan Ye ESN; ESN additionally receives a fixed 64-D reservoir
state.  Neither learned actor contains or controls the VMC virtual springs.

## Campaign completion

- 18 paired runs: 6 seeds x 3 reward profiles x 2 controller modes.
- 2,000,000 PPO steps per lane and 8 parallel environments per lane.
- 17/18 pairs passed the full task/no-rod/effective-contact/torque gate.
- The only pair-level failure was `contact_safe_seed20260845`: the MLP task
  gate failed while the matched ESN run passed.  It is excluded from paired
  contact-safe effect estimates.
- The V4 final holdout was not used for training, reward selection, checkpoint
  selection, or any result in this report.

## Paired effects: ESN minus MLP

Negative recovery, rejoin, impulse, jerk, or torque differences favor ESN.

| Profile | Valid pairs | Recovery RMSE | Rejoin latency | Contact impulse | Peak jerk | Peak torque |
|---|---:|---:|---:|---:|---:|---:|
| balanced | 6 | -0.114 +/- 0.065 mm | -0.0089 +/- 0.0103 s | -0.057 +/- 0.117 N s | +24.1 +/- 49.0 m/s^3 | +1.014 +/- 0.673 Nm |
| contact_safe | 5 | -0.049 +/- 0.189 mm | -0.0107 +/- 0.0219 s | -0.094 +/- 0.201 N s | -11.7 +/- 38.3 m/s^3 | -0.338 +/- 0.255 Nm |
| recovery_priority | 6 | +0.206 +/- 0.151 mm | +0.0104 +/- 0.0125 s | -0.059 +/- 0.030 N s | -4.8 +/- 17.4 m/s^3 | +0.115 +/- 1.350 Nm |

## Interpretation

`balanced` is the most repeatable recovery result: ESN lowered recovery RMSE
in all 6/6 seeds and improved rejoin latency in 4/6.  Its improvement is
modest but consistent, so the defensible claim is a repeatable recovery benefit
under matched inputs and safety limits, not a large universal dominance.

`contact_safe` gives the most favorable torque/smoothness trade-off, but the
recovery improvement is not seed-consistent.  `recovery_priority` is a negative
ablation: it reduces impulse in all 6/6 seeds but worsens recovery RMSE and
rejoin.  This rejects the simplistic assumption that more reward on recovery
automatically improves an ESN controller.

## Phase analysis of balanced profile

The phase analysis uses rod timing only offline; neither actor receives a phase,
force, rod, or obstacle feature online.  Before contact, ESN and MLP are
identical because the deployable residual authority gate is zero.  During
loading, the ESN-minus-MLP tracking RMSE difference is -0.040 mm and peak
torque difference is -0.185 Nm on average.  During post-release recovery, the
tracking RMSE difference is -0.114 mm.  The benefit therefore occurs after the
observable departure/release process, consistent with temporal memory being
useful for rejoin rather than with a pre-contact trajectory bias.

The full-episode peak torque increase under balanced training was traced to the
post-grasp lift/carry interval, not the contact/recovery window.  A frozen-model
test that returns residual authority to fixed WBC when gripper closing begins
kept task, effective-contact, recovery RMSE, impulse, and jerk unchanged for
the examined seed while reducing ESN peak torque from 35.12 Nm to 32.48 Nm.
Across all six balanced seeds, this task-window evaluation preserves the 6/6
recovery-RMSE win rate while removing the systematic peak-torque disadvantage.

## Next experiment

The next campaign trains both MLP and ESN with the same task-window constraint
enabled from the start.  It should use the balanced profile first, maintain the
same paired multi-seed protocol, and compare both final and intermediate
checkpoints on the locked development validation set.  The final report must
retain both the original full-horizon and task-window results rather than
silently replacing the earlier protocol.
