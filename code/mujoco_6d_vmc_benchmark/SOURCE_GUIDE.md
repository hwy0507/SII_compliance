# Server Source Export Guide

This directory is a source-only export from the research runtime on
`arm1:/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`, captured on
2026-09-23. It is intended to make the current MuJoCo compliance work
reviewable and reproducible without committing experiment outputs, GIFs,
videos, checkpoints, or private server state.

## What is included

The export contains the current FR3/Panda-compatible MuJoCo scenes, WBC and
6D VMC control layers, primitive contact fixtures, the workstation/office
scenes, teacher-data and audit scripts, and the MLP/ESN student implementations.
The exact captured files, source paths, sizes, and SHA-256 hashes are recorded
in `docs/server_source_20260923.json`.

Historical source and result artifacts removed from the GitHub `main` branch
are archived on DGX Spark at:

```text
/home/arm1/SII_compliance_archive/20260923_origin_main_5d0e457/
/home/arm1/SII_compliance_archive/legacy_20260923_removed_from_main/
```

The first directory is a complete pre-slimming snapshot; the second contains
the exact removed-file archive and its SHA-256 manifest.

The repository intentionally does **not** include `outputs/`, model weights,
GIF/MP4 files, large datasets, Python caches, virtual environments, or server
credentials. A checkpoint or result is valid only when its generating script,
fixture, seed, and split manifest are recorded separately.

## Recommended entry points

For a compact source check, use `scripts/run_source_demo.py`. It accepts a JSON
recipe, verifies the two required MuJoCo Menagerie model directories, and
keeps output prefixes immutable. `--dry-run` prints the resolved command. The
`--smoke` mode performs a non-rendered initialization/numerical run while
respecting the environment's minimum 6.2 s episode duration.

```bash
python scripts/run_source_demo.py \
  --config configs/ball_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-smoke/ball \
  --smoke
```

The workstation recipe is a development contact demonstration, not a frozen
paper protocol:

```bash
python scripts/run_source_demo.py \
  --config configs/workstation_source_demo.json \
  --menagerie /path/to/mujoco_menagerie \
  --output /tmp/sii-demo/workstation \
  --render
```

The two JSON recipes expose the scene, reference speed, fixture geometry, and
the full six-dimensional VMC configuration in one place. They are deliberately
separate from the historical scripts so that a reviewer can see which values
were used for a particular run.

## Source layout

`audited_velocity_env.py` defines the causal environment, contact accounting,
and metric gates. `paper_mpc_wbc.py`, `fixed_panda_wbc.py`, and
`wbc_velocity_residual_core.py` define the nominal velocity/reference boundary.
`vmc_compliance_baseline.py` and `vmc_torque_baseline.py` implement the virtual
model baselines. `direct_esn_compliance.py`, `esn128_action7_20260918.py`,
and the `train_*esn*` scripts implement reservoir-state/action readouts;
`mlp_compliance_baseline.py` and `train_*mlp*` implement the matched MLP
students. The `primitive_*`, `office_*`, `workstation_*`, and `run_*` files
construct the corresponding validation fixtures and replay/evaluation loops.

Most filenames retain their server date suffix because they represent distinct
validated iterations. Do not assume that the newest timestamp is automatically
the paper protocol: read its configuration and audit output first.

## Environment setup

The server used a project-local virtual environment. On a new machine, install
the research dependencies and provide a MuJoCo Menagerie checkout:

```bash
python -m pip install -r requirements-research.txt
export MUJOCO_GL=egl  # headless Linux; use glfw for a local display
```

The expected Menagerie layout is:

```text
<menagerie>/franka_fr3/
<menagerie>/franka_emika_panda/
```

The source scripts add their own directory to the import path when launched as
files. Running from `code/mujoco_6d_vmc_benchmark` keeps relative imports and
configuration paths predictable.

## Suggested execution order

1. Run `tools/check_source_export.py` to verify the captured hashes and Python
   syntax.
2. Run the ball or workstation smoke recipe before rendering.
3. Inspect the JSON metrics and contact-pair audit before trusting a GIF.
4. For teacher collection, run the scene-specific `search_*` or
   `build_*teacher*` script and preserve its seed/manifest with the dataset.
5. Train matched MLP and ESN students using the resulting teacher actions;
   evaluate on held-out fixtures rather than replaying the training fixture.

## Important scope and limitations

This export is a faithful research snapshot, not a claim that every historical
entry point is production-ready.

- The fixed-base Panda/FR3 adapters are simulation interfaces. The complete
  NUS visibility-aware planner is not yet the default top-level runner.
- The workstation and primitive scripts include development fixtures and
  diagnostics. Freeze a paper protocol only after fixing the scene XML,
  contact masks, seeds, and train/validation/test fixture split.
- The current teacher-bank builder is useful for development, but its older
  output may contain fixture leakage. Rebuild the formal bank with a split
  manifest that keeps a physical fixture out of both training and test sets.
- The current push contact mask permits the hand/finger/end-link contact set
  defined by the fixture and rejects proximal arm links. Verify the exact mask
  in the selected scene before claiming end-effector-only contact.
- Classical impedance/admittance baselines and full sim-to-real calibration
  are research follow-ups, not implied by the presence of their scripts.
- Checkpoints, result tables, and rendered media are external artifacts. Their
  absence from this source export is intentional.

## Provenance check

Run:

```bash
python tools/check_source_export.py
```

The check must report the expected number of captured files and successful
Python syntax validation. A changed source file should update the provenance
manifest in the same commit.
