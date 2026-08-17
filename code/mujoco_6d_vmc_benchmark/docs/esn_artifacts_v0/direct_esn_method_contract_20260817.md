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

The student reservoir receives only deployment-available robot/WBC signals:

- seven joint positions;
- seven joint velocities;
- six-dimensional nominal WBC end-effector twist.
- six-dimensional WBC pose error;
- six-dimensional WBC twist error.

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

## First local smoke result

The existing physical rod trace was used only as a smoke fixture. It produced
1,750 samples, with 1,725 samples after a 25-step washout. The Direct ESN
readout fit had teacher-action MSE `4.63e-4` and MAE `4.36e-3`; online
saturation was `0.16%`. These are trace imitation diagnostics only: they do
not establish recovery RMSE, rejoin latency, torque safety, or task success.

## Closed-loop server smoke and current blocker

The Direct ESN was connected to the actual fixed-WBC MuJoCo Panda task on
August 17, 2026. The integration contract is verified: the rod-impact smoke
can finish the grasp without a hard torque limit, and the environment reports
`controller_family = direct_esn`, `uses_vmc = false`, and WBC feedback scale
`1.0`.

This is **not a reportable performance result yet**. A matched no-rod rollout
reveals a closed-loop distribution-shift problem: a small ESN residual can
create a WBC tracking deviation, then the student observes that self-induced
deviation and increases its own yielding action. Trace-level teacher imitation
therefore does not guarantee closed-loop nominal neutrality.

The following corrections are now implemented:

1. fixed-WBC no-rod zero-action traces enter readout fitting as neutral data;
2. fitting and deployment use the same 40 ms physical ESN period;
3. the privileged teacher is a phase machine: pre-contact labels are exactly
   zero, contact labels slow/yield, and rejoin labels are allowed only after
   contact;
4. a WBC-deviation activation envelope prevents residual authority inside the
   nominal tracking deadband.

The next required algorithm stage is DAgger-style privileged relabeling:
roll out the current student, collect its visited states, use contact truth
only offline to produce counterfactual safe labels, and refit the readout.
This must be completed before comparing Direct ESN with rigid/impedance/VMC
baselines or claiming a deployment-ready controller.

Artifacts:

- `scripts/direct_esn_compliance.py`
- `scripts/collect_direct_esn_teacher.py`
- `scripts/train_direct_esn_readout.py`
- `scripts/evaluate_direct_esn_compliance.py`
- `tests/test_direct_esn_compliance.py`
- `docs/esn_artifacts_v0/direct_esn_smoke_20260817/`
