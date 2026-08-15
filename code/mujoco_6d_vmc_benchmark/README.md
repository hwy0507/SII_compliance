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

The default reference generator remains a repeatable reaching proxy so frozen
benchmark artifacts are reproducible.  The opt-in `fixed_panda_wbc` source
now puts a live fixed-base Panda WBC command adapter between that task target
generator and the low-level compliance layer; a future external WBC can replace
that adapter while retaining the same pose/twist/joint-velocity contract.

### Fixed-base Panda WBC adapter demo

The repository now supplies a Panda-side WBC command boundary for the MuJoCo
demo.  `FixedBasePandaWBC` converts a fixed SE(3) pick/lift target into a
bounded resolved-rate task command and null-space posture command at each
control tick; VMC only executes that command compliantly and does not alter
the high-level task target.  This is a fixed-base Panda adapter, not a direct
reuse of the separate Fetch/ManiSkill mobile whole-body stack.

```bash
export MUJOCO_GL=egl
python scripts/run_fixed_wbc_vmc_demo.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/fixed_wbc_vmc_demo
```

The command writes a paired physical-rod/no-rod GIF, WBC command traces and a
machine-readable summary.  See [the WBC interface and demo note](docs/wbc_integration_demo/fixed_panda_wbc_interface_and_demo.md)
for scope, information boundaries and the validated physical result.

## V1 validity-gated benchmark ladder

The current benchmark foundation is the paired physical rod fixture, its
contact–unloading–rejoin phase analysis, and a fair `rigid → impedance → VMC`
ladder.  It deliberately distinguishes no-contact, grazing, nominal-contact,
and high-impact geometry cases so a nearly missed rod cannot become a
misleadingly good compliance result.  Run it with:

```bash
export MUJOCO_GL=egl MPLBACKEND=Agg
python scripts/run_baseline_ladder.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/benchmark_ladder_v1 --explicit-vmc \
  --kappa 35 --damping-ratio 0.8 --carriage-drive-scale 8 \
  --rod-stroke 0.16 --rod-height 0.54 --grasp-time 2.1

python scripts/run_geometry_matrix.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/geometry_matrix_v1 \
  --heights 0.53 0.54 0.55 --strokes 0.14 0.16 0.18
```

See [the V1 protocol and results](docs/benchmark_protocol_v1.md) for the
definitions, validity gates, exact results, and limitations.  It is a
simulation-only fixed-reference benchmark; it is not a claim of a live WBC,
real-robot, or ESN result.

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

The original constant-softness case (`kappa = 0.20`) is deliberately retained
as a **failure/trade-off baseline**: it yields visibly, but does not regain
enough pose before the old `2.10 s` closure deadline.  It must not be presented
as a successful recovery demonstration.

The recovery candidate below still uses one shared scalar for all six springs.
It uses `kappa = 0.20` while the rod is present, then smoothly switches all six
to `kappa = 4.00` after the rod has retracted; the six virtual-carriage return
channels are scaled together from `0.50` to `4.00`.  Closure is delayed to
`2.30 s` while the same reachable pre-grasp pose is held.  This creates an
observable and measurable sequence: yield first, then rejoin, then grasp.

```bash
export MUJOCO_GL=egl
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_rejoin_demo \
  --kappas 0.20 --recovery-kappa 4.00 --recovery-ramp 0.08 \
  --damping-ratio 1.8 --carriage-drive-scale 0.50 \
  --recovery-carriage-drive-scale 4.00 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 \
  --grasp-time 2.30 --camera-view hand-closeup --render-start-time 0.90 --render-end-time 2.55 \
  --playback-speed 0.5 --render-gif

python scripts/run_rod_perturbation_benchmark.py \
  --menagerie ~/vmc_mujoco_runtime/mujoco_menagerie \
  --output-dir outputs/rod_rejoin_demo_no_rod \
  --kappas 0.20 --recovery-kappa 4.00 --recovery-ramp 0.08 \
  --damping-ratio 1.8 --carriage-drive-scale 0.50 \
  --recovery-carriage-drive-scale 4.00 --carriage-drive-damping-ratio 2.0 \
  --contact-time-constant 0.015 --rod-stroke 0.16 --disable-rod \
  --grasp-time 2.30 --camera-view hand-closeup --render-start-time 0.90 --render-end-time 2.55 \
  --playback-speed 0.5 --render-gif

python scripts/render_rod_comparison.py \
  --perturbed-gif outputs/rod_rejoin_demo/rod_perturbation_kappa_0.20.gif \
  --perturbed-trace outputs/rod_rejoin_demo/rod_perturbation_kappa_0.20_trace.npz \
  --reference-gif outputs/rod_rejoin_demo_no_rod/rod_perturbation_kappa_0.20.gif \
  --reference-trace outputs/rod_rejoin_demo_no_rod/rod_perturbation_kappa_0.20_trace.npz \
  --time-start 0.90 --time-end 2.55 \
  --output outputs/rod_rejoin_demo/rod_vs_no_rod_rejoin_kappa_0.20.gif
```

For the paired two-stage trial, the rod touches the hand from `1.260 s` to
`1.332 s` and is fully retracted at `1.72 s`.  The paired end-effector
difference peaks near `23 mm`; it then falls to about `8 mm` by `2.55 s`.
Against the nominal trajectory, error falls from `33.7 mm` at rod release to
`10.2 mm` immediately before the delayed closure: a `69.6%` recovery over that
window.  The run subsequently lifts and retains the free block, with 2.03 mm
maximum rod--hand contact penetration and no hard torque-limit frame.  This is
a first phase-scheduled VMC benchmark candidate, not yet the requested future
WBC+VMC or a real-robot deployment.

### Paper-style trajectory and error figures

`scripts/plot_trajectory_results.py` produces two PNG figures in the style of
the cited paper's component-wise trajectory/force plots.  The first figure has
the nominal WBC-reference interface, perturbed trajectory, and no-rod control
for X/Y/Z; component-wise deviations; and the norm error, paired disturbance
offset, speed and contact force.  The second figure reports the six virtual
wrench channels and three translational carriage deflections.  Shaded pink is
the commanded rod-interaction interval, the red dashed line is complete rod
retraction, and the green dotted line is closure.

At the current first-pass **low-error** candidate (`kappa = 6.00`, all six
directions shared; carriage drive scale `4.00`), the paired run gives:

| Quantity | Result |
| --- | ---: |
| Peak \(\lVert p_{EE}-p_{\mathrm{WBC-ref}}\rVert\) | 10.84 mm |
| Peak rod-induced offset versus matched no-rod run | 5.92 mm |
| Position RMSE versus WBC-reference interface | 6.62 mm |
| Paired rod-induced offset RMSE | 2.62 mm |
| Error at rod release \(t=1.72\,s\) | 8.73 mm |
| Error immediately before closure \(t=2.30\,s\) | 3.87 mm |
| Maximum rod--hand contact force | 18.62 N |
| Hard torque-limit fraction | 0 |

Generate the figures from a paired trace using:

```bash
export MPLBACKEND=Agg
python scripts/plot_trajectory_results.py \
  --rod-trace outputs/rod_opt_k600/rod_perturbation_kappa_6.00_trace.npz \
  --no-rod-trace outputs/rod_opt_k600_no_rod/rod_perturbation_kappa_6.00_trace.npz \
  --output-dir outputs/rod_opt_k600/figures \
  --rod-start 1.08 --rod-end 1.72 --grasp-time 2.30 \
  --time-start 0.90 --time-end 2.55
```

The label “WBC reference” presently means the benchmark's reachable
moving-trajectory **WBC interface proxy**, not a live whole-body controller.
When WBC is integrated, replace `nominal_position`/`nominal_twist` in the trace
with actual WBC outputs and the metrics and plotting protocol remain unchanged.

### Repeated physical rod-excitation response benchmark

A single manipulation trial contains one rod-intervention interval, so its
error and contact-force trace naturally has one transient peak.  It must not be
turned into a four- or five-peak figure by copying or time-warping samples.  To
obtain a paper-style repeated-response figure, the benchmark now provides a
separate `--response-only` protocol: the Panda holds a fixed reachable
pre-grasp end-effector pose, the gripper remains open, and one physical MuJoCo
rod performs five independent press--hold--retract motions.  The rod is a
massive rigid body on a slide joint and the hand--rod interaction is counted
from MuJoCo contact data, rather than from the command signal alone.

The reference pose in this response-only fixture is intentionally fixed so
that the repeated peaks show the six virtual-spring response clearly.  Its
slightly lower rod-support height is a fixture change for this diagnostic
experiment only; the single-press grasp benchmark retains its original
geometry and lift/hold success gate.  Therefore `target_lifted_after_recovery`
and `target_held_at_end` are not applicable to response-only runs and must not
be reported as a grasp failure.

The reproducible five-contact run used for the current figure is:

```bash
export MUJOCO_GL=egl
python scripts/run_rod_perturbation_benchmark.py \
  --menagerie mujoco_menagerie \
  --output-dir outputs/repeated_rod_k600_fixedh \
  --kappa 6.0 --recovery-kappa 6.0 --damping-ratio 1.8 \
  --carriage-drive-scale 4.0 --recovery-carriage-drive-scale 4.0 \
  --response-only --rod-start-time 0.80 --rod-cycles 5 \
  --rod-cycle-period 1.20 --rod-stroke 0.16

python scripts/run_rod_perturbation_benchmark.py \
  --menagerie mujoco_menagerie \
  --output-dir outputs/repeated_rod_k600_fixedh_no_rod \
  --kappa 6.0 --recovery-kappa 6.0 --damping-ratio 1.8 \
  --carriage-drive-scale 4.0 --recovery-carriage-drive-scale 4.0 \
  --response-only --disable-rod --rod-start-time 0.80 --rod-cycles 5 \
  --rod-cycle-period 1.20 --rod-stroke 0.16
```

Plot the paired traces with five event windows:

```bash
export MPLBACKEND=Agg
python scripts/plot_trajectory_results.py \
  --rod-trace outputs/repeated_rod_k600_fixedh/rod_perturbation_kappa_6.00_trace.npz \
  --no-rod-trace outputs/repeated_rod_k600_fixedh_no_rod/rod_perturbation_kappa_6.00_trace.npz \
  --output-dir outputs/repeated_rod_k600_fixedh/figures \
  --rod-start 0.80 --rod-end 1.44 --grasp-time 6.80 \
  --rod-cycles 5 --rod-cycle-period 1.20 --time-start 0.70 --time-end 6.40
```

For this run, contact-trace segmentation gives five separated hand--rod
windows: `[0.98, 1.08]`, `[2.18, 2.288]`, `[3.38, 3.484]`,
`[4.58, 4.684]`, and `[5.78, 5.884] s`; the peak physical contact force is
`17.13 N`.  The plotted Y position, paired rod-induced deviation, and contact
force therefore each contain five measured peaks.  Over the displayed
`0.70--6.40 s` window, the current shared-stiffness candidate gives peak
nominal/reference error `13.06 mm`, peak paired offset `7.83 mm`, nominal
position RMSE `5.03 mm`, paired-offset RMSE `3.54 mm`, and `6.33 -> 1.47 mm`
error reduction from the final rod release to the pre-closure sample.  These
are response-only diagnostics; the task-level lift/hold result is still
reported by the separate single-press grasp benchmark.

This repeated experiment is still an end-effector 6D virtual-carriage VMC
benchmark.  “WBC reference” in the plots remains the reachable trajectory
proxy described above; it is not a live WBC output, and the experiment is not
a real-robot deployment.  Once the real WBC supplies pose/twist traces, the
same paired metrics and plotting script can be reused without changing the
five-contact protocol.

### Direct WBC-reference rejoin plot

For the question “after each impact, how long until the actual hand returns to
the WBC path?”, the plotting script also writes
`wbc_rejoin_trajectory_results.png`.  Its left panel overlays the 2D X--Z
projection of the `WBC reference (proxy)` path, the actual rod+VMC
end-effector path, and the matched no-rod path in the same axes.  X captures
the approach direction while Z captures the grasp descent.  The right panel
plots the Euclidean reference error.  Orange markers denote contact onset,
green markers/lines denote release, and blue dashed markers denote the first
time the error remains within the configured rejoin tube.

The default rejoin definition is a 5 mm Euclidean position tube maintained for
80 ms.  It is intentionally explicit so the recovery time is measurable rather
than judged from a screenshot.  Change it with `--rejoin-threshold-mm` and
`--rejoin-hold-s`; the resulting `trajectory_error_metrics.json` records every
contact window, rejoin time, and release-to-rejoin latency.  With a future live
WBC trace, the same figure becomes the direct actual-versus-WBC trajectory
comparison requested for the final WBC+VMC experiment.

The same command also writes `wbc_rejoin_dynamics_results.png`.  This companion
figure uses a shared time axis and shows: EE speed with no-rod comparison;
physical rod--hand contact force versus the norm of the virtual spring force;
the three translational virtual-force channels; the three rotational
virtual-moment channels; and the seven applied motor torques split into
proximal/distal joints.  Thus a shorter rejoin time can be checked against
speed surge, contact-force peak, spring wrench, and motor-torque peak rather
than being treated as a trajectory-only result.  For the current `kappa=6`
single-press run, the corresponding peaks are `0.099 m/s` EE speed,
`18.62 N` physical contact force, `5.19 N` virtual-force norm, `0.503 N·m`
virtual-moment norm, and `30.40 N·m` applied motor torque; no hard torque-limit
frame occurred.

### Explicit translational carriage candidate (server result)

The benchmark now also supports a physical MuJoCo translational carriage.  It
is one shared 3D body with three orthogonal slide joints; the translational
spring force is applied to the Panda hand and the equal-and-opposite force to
the carriage.  The three rotational channels remain controller-integrated
SO(3) virtual channels, so this is a hybrid prototype rather than a complete
physical 6D mechanism.

The current valid Pareto candidate is:

```text
--explicit-translational-carriage --carriage-mass-kg 1.0
--kappas 35 --damping-ratio 0.8 --carriage-drive-scale 8.0
--recovery-carriage-drive-scale 8.0 --recovery-kappa 35 --recovery-ramp 0.08
--rod-stroke 0.16
```

On the same physical rod fixture and paired no-rod reference, it achieved
`7.71 mm` peak nominal error, `4.29 mm` peak paired rod offset, `4.05 mm`
nominal position RMSE, and `0.372 s` release-to-rejoin latency, while retaining
`18.51 N` peak rod contact, `30.08 N·m` peak applied torque, and successful
target lift/hold.  These figures are MuJoCo benchmark results only: the WBC
reference is still a reachable moving trajectory interface proxy, not a live
whole-body controller, and no real-robot claim follows from them.

The summary now stores
`peak_explicit_translational_spring_force_n` separately from
`peak_virtual_force_n`; the latter is the controller wrench and is intentionally
zero in the explicit translation channels.

The optional complete explicit-6D prototype is enabled with:

```bash
--explicit-translational-carriage --explicit-rotational-carriage \
--carriage-mass-kg 1.0 --rotational-carriage-inertia-scale 0.5
```

The rotational carriage is a MuJoCo ball-joint child of the translational carriage.
Its action-reaction spring moment is logged as
`explicit_carriage_moment` and plotted in the rotational-channel panel.  The
best current paired result (`kappa=35`, `zeta=0.8`, rod stroke `0.16 m`) has
`7.85 mm` peak nominal error, `4.64 mm` paired rod offset, `0.340 s`
release-to-rejoin latency, `18.63 N` peak rod force, `4.50 N·m` peak explicit
rotational spring moment, and `30.17 N·m` peak applied motor torque, with all
task validity gates passing.  This is still a simulation benchmark with a WBC
interface proxy, not a live-WBC or real-hardware result.

The rotational damping sweep is intentionally reported as a trade-off rather
than a single winner.  `rotational-damping-ratio=0.8` gives the strongest
trajectory metrics but visible high-frequency moment chatter; `1.2` is smoother
while retaining a comparable `19.68 N` physical contact peak; `2.0` reduces jerk
but lowers the contact peak to `17.19 N` and is therefore rejected for collision
non-equivalence.  The current stage-level primary result remains the stable
explicit 3D candidate, while the explicit 6D branch is ready for rotational
drive and solver-time-scale tuning.

## Training preparation: static search before RL

The current preparation uses independent stiffness multipliers in channel
order `[x, y, z, roll, pitch, yaw]`. It first generates a deterministic
Latin-hypercube experiment manifest around calibrated valid-contact geometry,
then evaluates static candidates with the same paired task and safety gates as
the benchmark. Only after that gate may a learned 25 Hz policy adjust the six
log-stiffness multipliers. The policy contract excludes MuJoCo-only rod/contact
truth and applies a fixed action-rate safety shield.

```bash
python scripts/prepare_stiffness_training.py \
  --output-dir outputs/training_prep_v0 \
  --train-samples 32 --validation-samples 8 --test-samples 8 \
  --seed 20260814
```

See [training protocol v0](docs/training_protocol_v0.md) for the 51-D
deployable observation, action mapping, randomized fixture ranges, validity
gate, and the separation between static search and later RL.
