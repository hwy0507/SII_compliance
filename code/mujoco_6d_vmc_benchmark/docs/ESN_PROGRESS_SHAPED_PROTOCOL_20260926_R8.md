# ESN reservoir progress-shaped protocol R8 (2026-09-26)

## Evidence motivating the change

R7 aggregate passes task and strict penetration gate on fixtures 9330 and
9331, but fails 9332. On 9332, the fixed VMC teacher and the neutral zero-
residual WBC also fail. Constant positive z-yield biases fail before grasp.
Therefore the next test must be phase conditional and cannot be pure teacher
imitation or a global action bias.

## Frozen method

Use the R7 aggregate checkpoint as the base. Recompute the same 18 cumulative
reservoir histories and fixed VMC labels. For training samples whose archived
stage is loaded lift or later, define the observable path-progress error as
`max(dot(position_error_xyz, commanded_path_direction) - 0.012 m, 0)`. Raise
the teacher label's translational action component along the commanded path to
at least `min(gain * progress_error, 0.30)`. All earlier-stage labels remain
unchanged. Stage is used only to construct training targets; it is not a
deployment input.

Fit only the final readout with loaded-stage weight 2.0 and proximal ridge
0.01. The 48-D normalization, heterogeneous-leak 128-unit reservoir, first
head layer, output smoothing, action projection, safety filter, runner, task
gate, and strict 0.2 mm penetration gate remain frozen.

The fixed gain budget is exactly 0.5, 1.0, and 1.5 per metre. Each checkpoint
is evaluated once on fixtures 9330--9332 on the same Spark snapshot. No new
gain is added after results are observed. A checkpoint is feasible only at
task+strict 3/3. Among feasible checkpoints choose mean physical-substep RMSE,
then peak torque, then peak speed.

Only a feasible checkpoint may run the frozen 9340--9345 cross-condition set;
all six must pass task and strict gate. This remains simulation evidence and
does not constitute a real-robot readiness claim.
