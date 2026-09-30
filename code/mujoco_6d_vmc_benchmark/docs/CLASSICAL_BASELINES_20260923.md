# Classical impedance/admittance baselines (2026-09-23)

This is a fixed-parameter development diagnostic on the v7 source primitives. It is not an office blind-test result and does not claim tuned or paper-ready parameters. The matrix has 24 rollouts: `impedance` and `admittance` × `ball`, `push`, `corner`, and `table_corner` × three fixture variants (seeds 20260923/24/25). Each rollout ran for 24 s on the server with `dt=1e-4`, MuJoCo Newton, and the shared contact/safety instrumentation.

The immutable result is on the server at `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume/FINAL_RESULT.json`. The isolated source snapshot is under `.../outputs/baseline_impedance_admittance_20260923/source_resume/`.

Counts below are three variants per fixture. `legacy` is the runner's historical 2-mm stop gate and is retained only for comparability. `strict` requires task completion, valid contact, no upstream contact, and maximum external penetration <= 0.2 mm.

| controller | fixture | legacy pass | strict pass | penetration (mm, 3 variants) | endpoint error (m, 3 variants) | peak force (N, 3 variants) |
|---|---:|---:|---:|---:|---:|---:|
| impedance | ball | 3/3 | 3/3 | 0.048, 0.050, 0.048 | 0.001, 0.001, 0.001 | 70.9, 77.9, 63.8 |
| impedance | push | 3/3 | 3/3 | 0.126, 0.133, 0.125 | 0.009, 0.001, 0.001 | 1307.7, 1347.0, 1308.1 |
| impedance | corner | 0/3 | 0/3 | 0.540, 0.234, 0.200 | 0.351, 0.373, 0.375 | 12826.0, 9402.5, 7194.0 |
| impedance | table_corner | 0/3 | 0/3 | 0.590, 0.596, 0.597 | 0.014, 0.014, 0.014 | 1066.8, 1071.5, 1071.2 |
| admittance | ball | 2/3 | 2/3 | 0.000, 0.000, 0.000 | 0.009, 0.020, 0.007 | 55.8, 61.2, 67.2 |
| admittance | push | 0/3 | 0/3 | 0.108, 0.108, 0.105 | 0.039, 0.039, 0.040 | 127.3, 130.2, 131.4 |
| admittance | corner | 0/3 | 0/3 | 0.030, 0.051, 0.044 | 0.376, 0.369, 0.357 | 5278.5, 4776.0, 4954.9 |
| admittance | table_corner | 0/3 | 0/3 | 0.398, 0.325, 0.194 | 0.063, 0.051, 0.029 | 682.2, 708.5, 512.2 |

Overall: impedance legacy 6/12 and strict 6/12; admittance legacy 2/12 and strict 2/12. These are fixed-parameter development results, not tuned office benchmarks.

Impedance computes `w = K e + D e_dot`, maps it through the current body Jacobian (`J.T @ w`), and injects the result through the existing velocity-servo torque feasibility and slew projection. The WBC command is read at each physics substep from current `data.time`.

Admittance reads estimated proprioceptive joint-load slots, maps them to a bounded tool wrench, and integrates `M x_ddot + D x_dot + K x = wrench` at 20 internal updates per RL step. It outputs bounded Cartesian velocity (`x_dot`) as the velocity residual. The integrated offset enters spring feedback, but no separate pose-offset reference is fed to WBC, so nominal WBC can pull against the virtual displacement during contact. This is a limitation for the next baseline revision.

`table_corner` and `corner` are separate fixtures. Corner gets stuck at contact with large force/penetration; table_corner generally reaches apron/contact but fails the complete release/endpoint gate and often exceeds 0.2 mm penetration.

Reproduction from the isolated server snapshot:

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/source_resume
/home/arm1/vmc_mujoco_runtime/.venv/bin/python scripts/run_classical_matrix_20260923.py \
  --output /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie --workers 8
```
