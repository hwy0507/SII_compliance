# Predictive Authority Development Report

## Scope

This branch tests whether the fixed Fan Ye-style ESN 120-ms WBC pose-error-change forecast can control when a learned WBC residual is allowed to act. The ESN is independent of VMC: it reads only deployable WBC/proprioceptive state and never reads contact, force, rod state, obstacle geometry, fixture ID, reward, or future phase.

The PPO actor remains a 32-D current-state MLP. The predictor is not appended to its observation. Instead it modulates residual authority before the shared action, velocity, torque, and torque-slew safety filters. This isolates prediction-to-control transfer from PPO representation changes.

All campaigns use the isolated post-V4 development manifest. The V4 final holdout was not used for training, parameter selection, checkpoint selection, or this report.

## Controller Contract

At each 40-ms decision instant, the ESN predicts the 120-ms normalized WBC pose-error change. Its radial projection onto current normalized WBC pose error determines predicted outward growth versus rejoin. The multiplier never amplifies authority; the existing slew limiter remains the final guard against abrupt command change.

```text
current WBC/proprioceptive state -> fixed fast/slow ESN -> delta pose error
current tracking error -> base authority gate
predicted radial rejoin -> authority multiplier in [m_min, 1]
PPO residual action * gated authority -> shared safety filter -> Panda torque
```

## Physical Interface Smoke

With a fixed residual action on two validation fixtures, both predictive-authority and no-prediction rollouts completed task success, valid collision, matched no-rod success, and no hard torque limit. With aggressive `m_min=0.35`, the multiplier was nontrivial on 54 of 155 control decisions in fixture 0 and had mean `0.938`. Against the same fixed action without modulation, it reduced mean slowdown from `0.1135` to `0.0979`, mean yield-twist norm from `0.01655` to `0.01438`, and recovery RMSE from `37.16 mm` to `30.44 mm`.

This confirms the ESN forecast is causally connected to the physical control path. It is not a PPO performance claim.

## Aggressive Release Ablation

Remote artifacts: `/home/arm1/vmc_mujoco_runtime/outputs/esn_predictive_authority_repro3_20260816`

Three matched seeds used 102,400 requested PPO steps per lane, `impulse_constrained` reward, eight parallel environments per lane, a 32-D current-state MLP baseline, and predictive-authority ESN with `m_min=0.35`.

| Result | Value |
|---|---:|
| Complete pairs | 3 |
| Gate-passing pairs | 1 |
| ESN task gate failures | 1 seed (`8/9` task success) |
| MLP task gate failures | 1 seed (`8/9` task success) |
| Gated-pair recovery RMSE difference | `-1.167 mm` |
| Gated-pair rejoin-latency difference | `-351.1 ms` |
| Gated-pair impulse difference | `+0.077 N s` |
| Gated-pair peak torque difference | `+0.137 Nm` |
| Gated-pair peak jerk difference | `+7.83 m/s^3` |

The single positive pair cannot support a performance claim. The ESN-specific task-success failure shows that granting only 35% authority during predicted rejoin can be too restrictive for some fixtures.

## Conservative Release Ablation

Remote artifacts: `/home/arm1/vmc_mujoco_runtime/outputs/esn_predictive_authority_min060_repro3_20260816`

The matched protocol was repeated with `m_min=0.60`.

| Result | Value |
|---|---:|
| Complete pairs | 3 |
| Gate-passing pairs | 2 |
| ESN task gate failures | 0 |
| MLP task gate failures | 1 seed (`8/9` task success) |
| ESN-MLP recovery RMSE | `-0.137 +/- 0.334 mm` |
| ESN-MLP rejoin latency | `-102.2 +/- 168.9 ms` |
| ESN-MLP impulse | `-0.011 +/- 0.076 N s` |
| ESN-MLP peak torque | `-0.136 +/- 0.074 Nm` |
| ESN-MLP paired-offset RMSE | `-0.104 +/- 0.041 mm` |
| ESN-MLP peak jerk | `+1.63 +/- 0.84 m/s^3` |

This mapping is safer, but not a robust superiority result: only two pairs pass the predeclared gate, the recovery benefit is small relative to seed variation, and jerk is worse in both eligible pairs.

## Over-Conservative Confirmation Ablations

Two deterministic confirmation gates were implemented and smoke tested: require agreement with a constant-twist 120-ms kinematic extrapolation, or require the measured WBC error derivative to indicate rejoin. Both preserve causality and physical safety, but are too conservative in fixed-action smoke: mean authority multipliers were `0.979` and `0.974`, respectively. The latter 51k PPO smoke had a matched baseline task gate failure, so it is not interpretable as evidence for or against ESN.

## Strict Conclusion

The ESN forecast remains technically useful: its development validation translation RMSE is `0.790 mm`, compared with `6.066 mm` for the matched constant-twist forecast. However, the current policy-independent authority modulation does **not** yet provide a stable, multi-seed control improvement and must not be reported as the proposed controller result.

The positive fixed-action and single-seed signals justify continued research, but the next branch should change the forecast's control role rather than continue unstructured gate-parameter sweeps. The most defensible next branch is bounded WBC reference retiming or task-gain scheduling driven by predicted error dynamics, benchmarked separately from the PPO residual actor.

## Predictive WBC Feedback Ablation

Remote artifacts: `/home/arm1/vmc_mujoco_runtime/outputs/predictive_wbc_feedback_smoke_20260816`

To separate ESN prediction from PPO stochasticity, a zero-residual deterministic benchmark compared fixed WBC with an ESN that scales only the WBC position and orientation feedback terms. The planned feedforward task twist and all downstream safety bounds stayed fixed.

| Controller | Task/no-rod success | Effective collision | Recovery RMSE | Rejoin latency | Peak torque | Peak jerk |
|---|---:|---:|---:|---:|---:|---:|
| Fixed WBC | `9/9` | `8/9` | `8.570 mm` | `618.9 ms` | `31.409 Nm` | `950.3 m/s^3` |
| ESN-WBC, minimum feedback `1.0` | `9/9` | `8/9` | `8.570 mm` | `618.9 ms` | `31.409 Nm` | `950.3 m/s^3` |
| ESN-WBC, minimum feedback `0.60` | `9/9` | `8/9` | `8.728 mm` | `627.8 ms` | `31.402 Nm` | `960.4 m/s^3` |

The `1.0` row is exactly identical to fixed WBC, confirming the forecast mode and evaluation interface are mechanically equivalent when no gain modulation is allowed. The `0.60` controller is safe but worsens recovery RMSE by `0.158 mm`, rejoin by `8.9 ms`, and peak jerk by `10.2 m/s^3`; its small torque and impulse reductions do not compensate. Direct ESN modulation of fixed WBC feedback is therefore a negative ablation and will not receive more training budget.
