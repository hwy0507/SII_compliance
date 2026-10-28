> Historical snapshot. Superseded by [RL_RESUME33_PARAMETER53_20261028.md](RL_RESUME33_PARAMETER53_20261028.md): 32/52 are complete; 33/53 now running. Preserve the original account below.

# RL handoff: Direct32 + parameter52 active (2026-10-27)

Goal remains active. This handoff supersedes the older shutdown note that still says Direct29/parameter49.

## Verified before launch

- Parameter51 three-controller review passed: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity_pool30_cycle51_review_20261026_v1/REVIEW.json`.
- Parameter52 preparation and all three exact check-only restores passed:
  - `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity_pool30_cycle52_20261026_v1/CHECK_ONLY_COMPLETE.json`
  - exit codes impedance/admittance/vmc: `0/0/0`
- Direct31 full 30/30 cycle completed at `1,286,790` steps. Its complete checkpoint was archived and hash-verified:
  - `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take_cycle31_archive_20261027_v1/direct/cycle_00031.pt`
  - SHA256 `736c8d6573513956b7c2e841c7deb36d42bb41413b5358a5f952e562d5b10242`
- Corrected Direct31 review passed at:
  - `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take_cycle31_review_20261027_v1/REVIEW.json`
  - `1,286,790` steps, `41,250` new transitions, reward mean `-30.90756769442996`, 30/30 full horizons, no aborts, exact reward and 32-step target reconstruction.
- Direct31 health/diagnostic review passed at:
  - `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take_cycle31_review_20261027_v1/DIAGNOSIS.json`

## Active jobs

1. Direct32, GPU0, 30 workers, CPUs 0-12:
   - run: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take_cycle32_20261027_v1`
   - launch: `LAUNCH.json`
   - registration: `REGISTRATION.json`
   - resume checkpoint: Direct31 archive above
   - process launch PID recorded in `LAUNCH.json` (recheck actual identity before acting)
2. Parameter52, GPU1/2/3, 30 workers each, CPUs 13-25 / 26-38 / 39-51:
   - run: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity_pool30_cycle52_20261026_v1`
   - launch: `LAUNCH.json`
   - registration per controller under `impedance/`, `admittance/`, `vmc/`
   - resumes exact parameter51 archives under `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_capacity_pool30_cycle51_archive_20261026_v1/`

## Continue after these cycles

- Let Direct32 and parameter52 reach complete condition cycles. Do not launch duplicates while their `PROGRESS.json`/processes are active.
- Archive complete Direct32 to `serl_take_cycle32_archive_20261027_v1/direct/cycle_00032.pt`, hash-check it, then run a cycle32 review/health diagnosis.
- Archive parameter52 to `parameter_capacity_pool30_cycle52_archive_20261026_v1`, run the corresponding complete review/health/saved review.
- After both reviews, read reward/loss and prepare the next finite unchanged continuations (Direct33 and parameter53) only from the exact reviewed archives. No convergence claim is authorized by this handoff.

## Recovery command

After a restart, inspect this file and the paths above first. Recheck process identity with `ps` and GPU state with `nvidia-smi`; then continue from the active run directories and exact archived checkpoints. Never resume from a partial episode or `checkpoint_latest.pt` unless its cycle boundary and hash have been independently verified.
