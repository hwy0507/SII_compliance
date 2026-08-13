# MuJoCo 6D End-Effector VMC Benchmark

This directory contains the first, deliberately narrow, MuJoCo benchmark for
the compliance project.  It is a **fixed-nominal-reference proxy**, not yet a
replacement for the whole-body controller.  Its contract is intentionally
simple: a reference provider supplies a nominal end-effector pose and twist;
the 6D virtual-model controller is the only component that converts that
reference into arm torques.

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

The current reference generator is a repeatable reaching proxy.  Replacing
`NominalReference` with the real fixed WBC output is the next interface step;
the controller, safety limits, logging schema and metrics remain unchanged.
