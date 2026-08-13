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
joint command is

\[
\tau = \operatorname{clip}(\tau_g + J(q)^\top w,\tau_{\min},\tau_{\max}).
\]

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

Once a candidate passes the torque/surge gates, render it with:

```bash
export MUJOCO_GL=egl
python scripts/run_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/best_kappa_demo \
  --kappas 1.00 --render-gif
```

The current reference generator is a repeatable reaching proxy.  Replacing
`NominalReference` with the real fixed WBC output is the next interface step;
the controller, safety limits, logging schema and metrics remain unchanged.
