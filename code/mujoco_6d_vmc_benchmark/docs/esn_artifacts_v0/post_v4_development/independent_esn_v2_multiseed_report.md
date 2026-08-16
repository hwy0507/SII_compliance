# Independent ESN-v2 Multi-seed Result

Date: 2026-08-16

## Protocol

Three newly trained paired seeds, `20260852` through `20260854`, use the frozen
impulse-constrained configuration. Each MLP/ESN-v2 lane uses 102,400 PPO steps,
eight parallel environments, the same 32-D deployable WBC-error state, safety
adapter, fixture manifest, reward, seed, and action contract. ESN-v2 alone has
the frozen 64-D fast and 64-D slow Fan Ye reservoir states. The V4 final holdout
is excluded.

All three paired runs pass task success 9/9, matched no-rod success 9/9,
effective collision 8/9, and zero hard torque limits in both lanes.

## Paired Effects

Negative values favor ESN-v2. Values are ESN-v2 minus current-state MLP, with
mean plus/minus population standard deviation over three seeds.

| Metric | Paired effect | Seed win rate |
|---|---:|---:|
| Recovery RMSE | -0.753 +/- 0.027 mm | 3/3 |
| Rejoin latency | -80.0 +/- 13.1 ms | 3/3 |
| Peak torque | -0.347 +/- 0.017 Nm | 3/3 |
| Paired-offset RMSE | -0.329 +/- 0.184 mm | 3/3 |
| Contact impulse | +0.107 +/- 0.302 N s | 1/3 |
| Peak jerk | +71.3 +/- 105.7 m/s^3 | 1/3 |

The recovery and peak-torque effects are consistent in all three independent
seeds. Contact impulse and jerk are mixed: one seed improves both impulse and
torque but increases jerk, while the other two seeds trade a small impulse
increase for lower recovery error and torque. Therefore the defensible result is
not universal dominance. It is a repeatable recovery and torque advantage under
matched deployment information and safety limits, with remaining smoothness and
contact-energy trade-offs.

## Decision

Promote ESN-v2 to a longer-budget paired campaign. Keep contact impulse and jerk
as co-primary outcomes, retain the current-state MLP as the learned no-memory
baseline, and report the rejected hard directional-projection ablation. Do not
select on or tune against the frozen V4 final holdout.
