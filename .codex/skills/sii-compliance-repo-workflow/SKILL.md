---
name: sii-compliance-repo-workflow
description: Maintain the SII_compliance research repository, its baseline branch, and Spark-hosted project files. Use for any work on this FR3 compliance-control project.
---

# SII Compliance Repo Workflow

Apply this workflow whenever continuing the SII compliance-control research project, including experiment runs, code changes, result analysis, and handoffs.

## Canonical locations

- GitHub: `https://github.com/hwy0507/SII_compliance`
- Integration branch: `baseline`
- Spark repository checkout: `/home/arm1/SII_compliance_baseline`
- Spark experiment/runtime data: `/home/arm1/vmc_mujoco_runtime/`
- Project skill on this Mac: `/Users/hwy/.codex/skills/sii-compliance-repo-workflow/`

Keep project code, data, logs, models, figures, and media on the Spark server. The local skill files are the only expected project-workflow files on the Mac. Do not copy large experiment outputs into GitHub; commit current source, concise reports, and pointers to server artifacts.

## At the start of every project conversation

1. Connect to the remote and fetch `origin/main` and `origin/baseline` before changing project files.
2. Read `UPDATE_LOG.md` from `origin/main` (or the current `main` checkout) and identify changes since the baseline branch's last recorded main commit. If the file is absent, record that fact in the eventual log update; do not infer unseen changes.
3. Read `UPDATE_LOG.md` on `baseline` and inspect repository status, current branch, commit, and any running server jobs relevant to the request.
4. Continue project work from `/home/arm1/SII_compliance_baseline` on branch `baseline`. Never develop or commit project changes directly on `main`.
5. Preserve existing user modifications and running jobs. Do not delete or overwrite server results as routine cleanup.

If the Spark checkout is missing, recreate it from the `baseline` branch using available credentials. If authentication prevents this, stop before making an alternate untracked project copy and report the precise blocker.

## During work

- Write project artifacts on Spark. Use dated, descriptive paths under `/home/arm1/vmc_mujoco_runtime/` or a suitable subdirectory of `/home/arm1/SII_compliance_baseline/`.
- Keep code needed by other agents in the Git repository. Keep large raw data, checkpoints, GIFs, logs, and derived arrays on Spark; place their absolute server paths and short descriptions in `UPDATE_LOG.md`.
- Maintain reproducibility: record commit/hash, command, configuration, seeds, protocol, key metrics, and whether results are smoke/development/formal.
- Never combine results from different protocols without explicitly labeling the difference. Do not claim an experiment succeeded unless its actual task and physical-validity gates passed.
- Stage only files belonging to the current task. Inspect `git status` and the staged diff before every commit; never bulk-add the entire repository or generated output directories.

## At the end of every change batch

1. Update `UPDATE_LOG.md` on `baseline` with a newest-first entry containing date, concise change summary, affected repository paths, exact Spark paths for code/results/logs/checkpoints/media, validation or experiment status, and the source `main` commit inspected at task start.
2. If a task made no file changes, do not create a no-op commit. If it changed files, commit the scoped changes and the log together on `baseline`, then push `baseline` to `origin` before reporting completion.
3. Verify the pushed remote SHA equals the local `baseline` SHA. Keep the Spark checkout on the pushed branch and verify its status is clean except for intentionally untracked server-only artifacts.
4. If credentials/network prevent pushing, do not say it was pushed. Preserve the commit and server files, report the exact unpushed commit and blocker, and resume the push on the next project turn.

Do not force-push, rewrite shared history, push to `main`, or commit secrets, credentials, large generated data, or machine-specific temporary files.
