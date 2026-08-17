# Direct ESN compliant-controller redesign (2026-08-17)

## Research decision

The proposed experiment is now separated from VMC and from PPO:

```text
fixed WBC nominal trajectory/twist
        ↓
deployable Direct ESN
        ↓
WBC slowdown + 6D Cartesian yielding velocity
        ↓
slew / velocity / acceleration / torque safety adapter
        ↓
MuJoCo Panda command
```

WBC remains fixed and owns the nominal grasp trajectory. The ESN is the
primary collision-response controller. It is not a feature extractor for a
second policy, and it does not change WBC feedback gains. VMC remains a
separate physical baseline.

## Deployment contract

The student reservoir receives only:

- seven joint positions;
- seven joint velocities;
- six-dimensional nominal WBC end-effector twist.

The online student must not receive contact force, contact normal, obstacle
pose or geometry, impactor type, future release time, fixture ID, penetration,
or any other simulator-only field. The direct action is seven-dimensional:

```text
[wbc_slowdown, yield_vx, yield_vy, yield_vz, yield_wx, yield_wy, yield_wz]
```

The all-zero action is exactly fixed WBC. The first channel is converted to a
bounded WBC retention scale; the remaining six channels are converted to a
bounded Cartesian yielding twist.

## Teacher and student separation

The first teacher is a deterministic privileged oracle used only to generate
offline labels. It uses contact force, contact normal, penetration/signed
distance, contact duration, and tracking error to label three phases:

1. contact onset: slow the nominal WBC velocity;
2. contact: yield away from the contact normal;
3. release: smoothly rejoin the nominal WBC trajectory using the observed
   displacement error.

The readout is then fitted by ridge regression on the deployable input trace.
This is an imitation warm-start and not yet a closed-loop performance claim.
The next step is a MuJoCo rollout adapter with matched rod/ball/hand-palm
transfer fixtures and a frozen validation split.

## Local smoke result

The existing physical rod trace was used only as a smoke fixture. It produced
1,750 samples, with 1,725 samples after a 25-step washout. The Direct ESN
readout fit had teacher-action MSE `4.63e-4` and MAE `4.36e-3`; online
saturation was `0.16%`. These are trace imitation diagnostics only: they do
not establish recovery RMSE, rejoin latency, torque safety, or task success.

Artifacts:

- `scripts/direct_esn_compliance.py`
- `scripts/collect_direct_esn_teacher.py`
- `scripts/train_direct_esn_readout.py`
- `scripts/evaluate_direct_esn_compliance.py`
- `tests/test_direct_esn_compliance.py`
- `docs/esn_artifacts_v0/direct_esn_smoke_20260817/`

