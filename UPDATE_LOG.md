# Update Log

This file tracks code and experiment updates on the `baseline` branch. New entries go at the top. Large experiment artifacts remain on DGX Spark; each entry records their absolute server paths so another agent can inspect them without downloading them to a workstation.

## 2026-09-30 — Initialize baseline workflow

- Created the `baseline` branch from GitHub `main` at commit `2e37ddc95d94a4a01d531ae1bf2625a454826d2a` (`Add office-v5 ESN baseline handoff`).
- Inspected `main`: it did not contain an `UPDATE_LOG.md`; therefore this is the first log entry and there are no prior main-log entries to reconcile.
- Added the project workflow skill on the research Mac at `/Users/hwy/.codex/skills/sii-compliance-repo-workflow/`.
- Spark canonical branch checkout: `/home/arm1/SII_compliance_baseline`.
- Existing simulation/runtime and experiment artifact root: `/home/arm1/vmc_mujoco_runtime/`.
- This entry records workflow setup only; no experiment, model, or benchmark result was modified or claimed.
