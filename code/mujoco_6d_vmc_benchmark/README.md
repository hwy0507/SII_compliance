# MuJoCo 6D End-Effector VMC Benchmark

This directory contains the MuJoCo compliance benchmarks for this project.
They use a **fixed-nominal-reference proxy**, not yet a replacement for the
whole-body controller (WBC).  The controller contract is intentionally
separate: a reference provider supplies a nominal end-effector pose and twist;
the 6D virtual-model controller is the only component that converts that
reference into arm torques.

The original free-space reaching script remains useful for controller
calibration, but it is **not** the task-level benchmark.  The task-level entry
point is `scripts/run_grasp_impact_benchmark.py`: Panda descends toward a free
object, receives an impact during that open-gripper approach, recovers toward
its nominal approach, and then physically grasps and lifts the object. Results
from the retired free-space diagnostic GIFs and the retired post-grasp impact
fixture must not be used as evidence for the manipulation task.

## Model

The Franka Panda end-effector is coupled to a virtual carriage by six
saturating spring-damper channels:

\[
w_i = \sigma_i\tanh(k_i e_i/\sigma_i) + d_i\dot e_i,\quad i=1,\ldots,6,
\]

where the first three entries are forces and the final three are moments.  The
joint command is built from the virtual wrench as

\[
\tau_w = J(q)^\top w,\qquad
\tau = \tau_g + \alpha\tau_w,
\]

where the largest \(\alpha\in[0,1]\) that respects the joint-torque box is
used before a per-joint torque-rate limiter.  This preserves the requested
wrench direction as far as the torque constraints allow; it is not a simple
per-joint output clip.

The first experiment holds a strong symmetry assumption: the three
translational directions share one baseline stiffness and the three rotational
directions share another.  A single dimensionless multiplier `kappa` scales
both blocks.  This is the physically meaningful version of “all six springs
are the same”: translational and rotational stiffness do not have compatible
units.

The virtual carriage follows the fixed nominal reference through its own
mass/inertia and damping.  It is not rigidly tied to the reference, so it can
lag during contact and avoids accumulating an unbounded forward spring force.

## Metrics

Each run writes a JSON evaluation matrix containing the requested primary
metrics:

1. post-intervention end-effector position/orientation tracking error;
2. end-effector speed distribution, forward-surge score, acceleration and
   jerk peaks;
3. commanded and applied motor-torque peaks, normalized torque ratio, and
   saturation fraction.

It also records contact duration, peak contact force, impulse and maximum
penetration as diagnostic quantities.  These do not select a stiffness in the
first pass, but prevent a low-torque controller from silently remaining in
contact with the obstacle.

## Reproducible first-pass protocol

The following is the current **simulation-only** baseline.  It uses the
official `mujoco_menagerie/franka_emika_panda` model, MuJoCo 3.11, a reachable
joint-space reference converted to an end-effector pose/twist, and an obstacle
whose collision mask is restricted to the Panda `hand` geometry.  Therefore,
the reported contact is an end-effector contact, rather than an accidental
upper-arm or elbow collision.

- Reference source: deterministic fixed nominal reaching proxy.  It must be
  replaced by fixed WBC pose/twist output before making a WBC+VMC claim.
- Fixed fixture: `contact-time-constant = 0.05 s`; this is an environment
  calibration (penetration/force/jerk trade-off), not a VMC tuning variable.
- Symmetric VMC: `zeta = 1.8`, virtual mass/inertia scale `1.0`, force/moment
  saturation `24 N / 3 Nm`, and the six-channel common stiffness multiplier
  `kappa`.
- Virtual-reference coupling: drive-stiffness scale `0.75`, drive damping
  ratio `2.0`.
- Primary gates: no-contact tracking must remain below 15 mm final position
  error; contact runs must have observed hand contact, zero hard torque-limit
  frames, final position error below 15 mm, and position RMSE below 40 mm.
  Forward surge, jerk and torque peak are compared on the resulting Pareto
  set rather than collapsed into an unvalidated single score.

With this fixture, the first `kappa` sweep (`0.50, 0.65, 0.80, 1.00, 1.25,
1.60, 2.00`) identifies `kappa = 1.60` as a practical presentation candidate:
post-contact position RMSE `35.6 mm`, final error `9.8 mm`, maximum forward
surge `0.0966 m/s`, jerk peak `1394 m/s^3`, contact-force peak `27.2 N`, and
applied torque peak ratio `0.339`, with zero hard torque-limit frames.  This
is a Pareto choice: `kappa = 2.00` improves RMSE slightly (`35.5 mm`) but
raises contact impulse (`4.51 N s` versus `4.38 N s`).  These numbers are
deterministic MuJoCo results for the stated fixture, **not** real-robot or
full-WBC results.

## Physical approach-impact-recovery-grasp benchmark

`run_grasp_impact_benchmark.py` provides the benchmark that matches the
intended task: **receive an impact while descending to grasp, yield/recover,
then still complete the physical grasp**.

- The yellow target is a free MuJoCo rigid body resting on a physical table.
  It is neither welded to the hand nor kinematically attached.
- Panda's existing coupled finger tendon has a physical position actuator.  It
  opens for approach and closes after the end effector reaches the target;
  lifting is sustained by fingertip contact and friction.
- The red impactor has finite mass and moves on a one-dimensional rail.  It is
  launched during the open-gripper descent, before `GRASP_TIME_S`; after its
  one initial velocity it evolves only through the MuJoCo equations of motion
  and contact solver.  It is not a mocap object and is never teleported.
- The impact rail is aligned with the approaching hand.  The validity check
  records the actual `impactor_geom`--`hand_collision` contact pair, rather
  than a proximity test or a contact with some arbitrary arm link.

Every manipulation run is invalid unless all of the following hold:

1. `impactor_hand_contact_observed`: the collision occurs during the open
   approach and actually contacts the hand;
2. `target_lifted`: after recovery, the free target leaves the tabletop by at
   least 120 mm;
3. `target_held_at_end`: it remains elevated and within the hand/object
   distance gate at the end of the episode;
4. `hard_limit_fraction = 0`; and
5. contact penetration remains within the predeclared fixture tolerance.

The current first valid manipulation fixture uses a 0.08 kg target, 0.16 kg
rail impactor, 0.8 m/s launch speed, and a 0.015 s contact time constant.  The
impact happens at 1.35 s and gripper closure begins at 2.10 s.  In the first
valid `kappa = 1.30` approach-impact trial, the impactor actually contacts the
hand, the block is subsequently lifted and still held at the end, and maximum
penetration is 3.23 mm.  The approach-recovery position RMSE is 13.9 mm, the
pre-grasp position error is 12.7 mm, peak jerk is 780 m/s^3, and the peak
applied arm-torque ratio is 0.367 with no hard-limit frames.  This only
establishes a deterministic **MuJoCo VMC baseline**.  VMC provides compliant
yield/rejoin around a fixed nominal path; active obstacle avoidance requires
the next WBC/ESN layer to alter that nominal path from contact or perception.
It is not an assertion of real-hardware safety or a complete WBC+VMC result.

## Server setup and run

The server runtime is deliberately outside this repository:

```bash
~/vmc_mujoco_runtime/.venv/bin/python -m pip install -r requirements.txt
export MUJOCO_GL=egl
python scripts/run_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/initial_sweep \
  --kappas 0.30 0.50 0.75 1.00 1.50 2.00
```

Run the paired no-contact regression for the candidate with:

```bash
export MUJOCO_GL=egl
python scripts/run_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/kappa_1p60_no_contact \
  --kappas 1.60 --damping-ratio 1.8 \
  --carriage-drive-scale 0.75 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.05 --disable-obstacle
```

Then render the corresponding hand-only contact trial with:

```bash
export MUJOCO_GL=egl
python scripts/run_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/kappa_1p60_demo \
  --kappas 1.60 --damping-ratio 1.8 \
  --carriage-drive-scale 0.75 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.05 --render-gif
```

To run the physical grasp-and-impact baseline instead, use:

```bash
export MUJOCO_GL=egl
python scripts/run_grasp_impact_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/approach_impact_k130_demo \
  --kappas 1.30 --damping-ratio 1.8 \
  --carriage-drive-scale 0.75 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --impact-speed 0.80 --render-gif
```

For a paired manipulation control trial, use the same command with
`--disable-impact`; it must still pass the target-lifted and target-held gates.

The current reference generator is a repeatable reaching proxy.  Replacing
`PickLiftCarryReference` with the real fixed WBC output is the next interface
step; the controller, safety limits, logging schema and metrics remain
unchanged.

## Rod perturbation: departure and return of the six-spring system

`scripts/run_rod_perturbation_benchmark.py` is the primary fixture for the
intended compliance demonstration.  A green cylindrical rod is mounted on a
finite-mass, position-driven physical slide.  During the open-gripper descent
it moves laterally into the Panda `hand_collision` geometry, holds briefly,
then retracts smoothly.  The benchmark logs all of the quantities needed to
show the six-spring mechanism rather than merely reporting a collision:

- `carriage_displacement[0:3]` and `[3:6]`: the three translational and three
  rotational virtual-spring deflections;
- `vmc_wrench[0:3]` and `[3:6]`: their corresponding virtual force/moment;
- actual end-effector, blue nominal marker, and cyan virtual carriage in the
  rendered scene; and
- peak deviation from nominal, rejoin error before gripper closure, contact
  force/impulse/penetration, velocity/jerk, and applied torque ratio.

This finite pick trajectory is a **moving attractor / trajectory tube**, not a
mathematical limit cycle.  For the exact phrase “depart from and return to a
limit cycle,” use a separate periodic nominal pose and phase variable.  The
rod fixture nevertheless tests the same desired VMC behavior for the grasp
task: departure from the moving nominal tube under an external physical push,
then a bounded return sufficiently close to complete the grasp.

The current paired baseline uses `kappa = 1.60`, VMC damping ratio `1.8`,
virtual-carriage drive scale `1.60`, rod stroke `0.16 m`, and fixed contact
time constant `0.015 s`.  The rod physically contacts the hand from about
`1.260 s` to `1.344 s`; it is commanded in from `1.08 s`, held, and smoothly
retracted by `1.72 s`, before gripper closure at `2.10 s`.  The perturbed run
passes all task gates (physical rod--hand contact, later target lift, target
still held, and zero hard torque-limit frames), with 3.40 mm maximum contact
penetration.  Its six-spring response has 8.70 mm peak translation and 8.64
mrad peak rotation of carriage-to-hand deflection, 4.66 N peak virtual force,
0.318 Nm peak virtual moment, 18.1 mm peak end-effector deviation from nominal
and 11.4 mm error immediately before closure.  The matched `--disable-rod`
control must accompany every reported rod trial, because a fixed nominal
reference has nonzero tracking error even without a perturbation.

Run the rod fixture and its paired no-rod control as follows:

```bash
export MUJOCO_GL=egl
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_k160 \
  --kappas 1.60 --damping-ratio 1.8 \
  --carriage-drive-scale 1.60 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 --render-gif

python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_k160_no_rod \
  --kappas 1.60 --damping-ratio 1.8 \
  --carriage-drive-scale 1.60 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 --disable-rod
```

### Readable perturbation-and-rejoin rendering

The full tabletop camera is useful for showing the overall pick-and-lift task,
but it makes a real 20--30 mm external-push displacement hard to see.  For a
presentation GIF, use the **rendering-only** `hand-closeup` camera and render
the short pre-grasp window.  This camera follows the **nominal** pose rather
than the measured hand, so it cannot hide actual departure by following it.
The blue nominal marker, magenta measured-end-effector marker, cyan carriage,
and magenta 0.48 s measured trajectory tail are drawn at their unscaled,
physical coordinates.

The following is a deliberately soft visibility/trade-off case, not the
recommended final stiffness: it makes the compliance response especially
readable, while the stiffer `kappa = 1.60` case above remains the current
rejoin-quality baseline.  Always compare it with its matched no-rod control.

```bash
export MUJOCO_GL=egl
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_soft_demo \
  --kappas 0.20 --damping-ratio 1.8 \
  --carriage-drive-scale 0.50 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 \
  --camera-view hand-closeup --render-start-time 0.90 --render-end-time 2.40 \
  --playback-speed 0.5 --render-gif

python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_soft_demo_no_rod \
  --kappas 0.20 --damping-ratio 1.8 \
  --carriage-drive-scale 0.50 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 --disable-rod \
  --camera-view hand-closeup --render-start-time 0.90 --render-end-time 2.40 \
  --playback-speed 0.5 --render-gif

python scripts/render_rod_comparison.py \
  --perturbed-gif outputs/rod_soft_demo/rod_perturbation_kappa_0.20.gif \
  --perturbed-trace outputs/rod_soft_demo/rod_perturbation_kappa_0.20_trace.npz \
  --reference-gif outputs/rod_soft_demo_no_rod/rod_perturbation_kappa_0.20.gif \
  --reference-trace outputs/rod_soft_demo_no_rod/rod_perturbation_kappa_0.20_trace.npz \
  --time-start 0.90 --time-end 2.40 \
  --output outputs/rod_soft_demo/rod_vs_no_rod_recovery_kappa_0.20.gif
```

For this paired `kappa = 0.20` trial, the rod touches the hand from `1.260 s`
to `1.332 s`; the true peak difference from the no-rod end-effector trajectory
is `23.0 mm`.  The trial subsequently lifts and retains the free block, with a
2.03 mm maximum rod--hand contact penetration and no hard torque-limit frame.
The 26.9 mm pre-grasp nominal error makes its safety--rejoin trade-off explicit;
it is evidence of a visible compliant departure, **not** a tuned final
controller.
