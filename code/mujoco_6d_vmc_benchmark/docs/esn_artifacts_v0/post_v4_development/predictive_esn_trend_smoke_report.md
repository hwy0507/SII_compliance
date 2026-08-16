# Predictive ESN trend smoke report

## Prediction gate

The fixed fast/slow Fan Ye reservoir plus ridge readout predicts the 120-ms
change in WBC pose error.  It was fit on 9 post-V4 development-train probe
traces and evaluated on 9 separate development-validation traces.  Inputs are
only current `q`, `qdot`, WBC task twist, WBC pose error, and WBC twist error.
The ESN receives no contact, force, rod state, obstacle state, future release,
fixture ID, or reward.

| validation 120-ms error-change predictor | translation RMSE |
|---|---:|
| fixed-reservoir ESN ridge readout | 0.790 mm |
| matched constant-twist extrapolation | 6.066 mm |

## Fair control smoke

The learned baseline is a 38-D MLP containing the same 32-D current state plus
the six-channel constant-twist forecast of error change.  The proposed lane is
a 38-D MLP containing the same current state plus the six-channel ESN forecast
of error change.  They share seed `20260971`, 102,400 PPO steps, eight
environments, impulse-constrained reward, safety adapter, action contract,
development fixtures, and validation protocol.

Both lanes pass task success 9/9, matched no-rod success 9/9, effective
collision 8/9, and zero hard torque limits.

## Paired effect

Values are predictive ESN minus matched kinematic-forecast MLP.  Negative is
favorable for all listed physical metrics.

| metric | effect |
|---|---:|
| recovery RMSE | -0.183 mm |
| rejoin latency | -48.9 ms |
| paired-offset RMSE | -0.099 mm |
| contact impulse | -0.043 N s |
| peak torque | -0.102 Nm |
| peak jerk | +14.4 m/s^3 |

The trend formulation avoids the first forecast design's duplicated absolute
error signal and gives a coherent improvement in recovery, impulse, torque,
and rejoin in this smoke.  The peak-jerk increase remains a material trade-off.
This is a promotion to three independent development seeds, not a paper claim
and not evidence of universal dominance.
