# Compute and evaluation audit — 2026-09-30

## Verified compute and preserved work

Spark has 20 ARM CPU cores, 121 GiB RAM (99 GiB available at initial check), and one NVIDIA GB10. Performance cores: 5–9 and 15–19 (3.9 GHz); efficiency cores: 0–4 and 10–14 (2.808 GHz). Four previous continuation runs occupied roughly 17.6 CPU cores while GPU utilization was 0%. Their isolated Simba environment contains CPU-only JAX/jaxlib 0.4.38, not a CUDA backend. Network weights and optimizer were restored, but replay was not restored in those continuations; their protocol explicitly records fresh replay.

At user-authorized pause, A/B/C/D had 272410/263210/248210/256210 cumulative steps. PID 1150890/1150891/1150892/1150893 were SIGSTOPed, not terminated. Latest durable checkpoints are A/B/D=250000 and C=225000. All four contain actor, critic, target critic, and temperature metadata with approximately 135–137 MB payload each. Exact process commands, progress, checkpoint manifests and resume command are in `/home/arm1/vmc_mujoco_runtime/reward_study_20260930/PAUSED_OLD_RUNS.json`. Check PID identity before `kill -CONT`; reboot loses paused RAM state but not saved checkpoints.

CPU microbenchmark (two efficiency cores, official 128 actor/512 double critic, batch 256): 2.5386 updates/s, 13.45 s compilation/warmup. This benchmark excludes physics/replay/policy overhead and is not end-to-end training throughput. Result: `/home/arm1/vmc_mujoco_runtime/reward_study_20260930/cpu_update_benchmark.json`. Existing continuation end-to-end rate was approximately 1.8–2.1 transitions/s/seed under four-way CPU contention. At that rate six hours supplies only roughly 39–45k new transitions per seed; it cannot justify the phrase sufficiently trained.

GPU compatibility is being tested in `/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu`, independently of old environments. Install logs are in the same directory. Existing CUDA 13 system libraries and existing cuDNN/NCCL are reused when compatible. Any dependency changes and actual backend must be frozen before paired reward runs.

## Why the previous six-method matrix is not a publishable ranking

1. The old runner passed fixture seed S directly to classical/MLP/ESN, but the direct-RL environment internally used S + 101 * variant. Layouts 1 and 2 therefore were not the same physical fixtures.
2. Direct RL applied `common_safe_action` residual attenuation before the old validator. That envelope must be checked against other methods before claiming common control authority.
3. The old validator and current GitHub canonical validator differ substantially: scene/task construction, observation mapping, policy adapters, actual substep metrics and strict audit semantics. A common method label does not prove matching protocol.
4. Old reward estimated torque from observation joint-load entries rather than integrating actual executed actuator torque at every physical substep. Sensor load is not the actual actuator-torque metric requested by the user.
5. Old reports mixed 55 s / dt=5e-5 with 100 s / dt=2.5e-5 results. Those are different protocols. Mean of per-episode maxima must also be distinguished from the global maximum.
6. Every previous six-method episode failed final placement; low RMSE, speed or force alone cannot establish useful compliance or task success.

## Proposed fair reward experiment

Use current main (`38caf31`, integrated into baseline `645f9fb`) as the source of scene, observer, WBC, action filter, physical step metrics and success gate; freeze the exact resulting source hashes/model hashes. Use MuJoCo 3.11, 25 Hz actor and the same physical dt in both reward arms. No teacher model, VMC parameter output, privileged actor field or reward-specific action filtering.

Run two reward arms with paired independent learner seeds and identical episode fixture/event sequences. Start from scratch in both arms; do not label old reward continuations as from-scratch paper-reward runs. Prefer at least three paired seeds if measured throughput allows; otherwise two paired seeds in this 6–7h window are exploratory and must be called that. Keep simultaneous simulation count at or below four. Training budget is equal environment transitions and update ratio, not wall-clock alone. Always report achieved steps and learning curves.

Reserve disjoint fixture seeds and exact serialized fixture configurations for train, validation and test. Check hash/seed intersections before training. Previously viewed layouts 0/1/2 are development acceptance conditions, not unseen final tests. Name the held-out test only after freezing it before results inspection. Use the same reset and event schedule for both arms.

Primary comparison: final checkpoint at the common achieved budget (no checkpoint cherry-picking). Optional validation-selected comparison uses an identical predeclared ordering: physical validity and stable placement first, then task success, then RMSE; report torque/velocity constraints and full Pareto tradeoffs instead of inventing one score after seeing results. Do not select on test episodes or choose each arm at unequal steps.

Evaluate every completed episode using the same strict placement and physical validity gates. Report success counts, all-episode RMSE, per-joint and global actual Nm peaks, peak tool speed (not P95), full duration, end-stage and failure cause. Also report physical-valid subset separately, never silently exclude invalid episodes. For variable-length failures show duration and integrated squared error alongside RMSE; do not assert equivalent ordering. Record requested/filtered/executed actions and integrated reward components. GPU usage alone is not an optimization target; throughput and complete auditable rollouts are.

## GPU probe completed at 12:05 CST

Isolated GPU environment passed official agent updates and checkpoint save/load: deterministic evaluation action maximum difference 0 after roundtrip. JAX 0.7.2/CUDA13, Flax 0.10.7, Optax 0.2.5, TFP nightly 0.26.0.dev20260929; all exact versions in GPU_VERSIONS.json. The only upstream API compatibility adaptation is `jax.tree_map = jax.tree_util.tree_map`; upstream algorithm source was not edited. MuJoCo remains 3.11.0. Existing server CUDA/cuDNN/NCCL are linked using gpu_env.sh. Old environment was untouched.

Identical agent batch256 update microbenchmarks: CPU small-core pair 2.54 updates/s; CPU performance-core pair 7.37 updates/s; GPU 122.26 updates/s, first JIT/warmup 47.18s. This is 16.6x update-only improvement over the performance-core CPU result, not an end-to-end training speedup. Evidence: gpu_update_benchmark.json, cpu_pcore_update_benchmark.json, GPU_CHECKPOINT_VALIDATION.json under the study root.

Campaign plan accepted by main agent: two reward arms x three paired seeds x 60k target transitions, UTD2, checkpoints every10k, maximum four concurrent simulations. Use a common achieved step (initial candidate50k) for the primary comparison, and explicitly report budget-short runs. Train dt1e-4 is development training; formal evaluation dt5e-5 uses the same scene and frozen gates. Reserve approximately five hours training plus one hour evaluation; update estimate after complete55s real episodes, rather than extrapolating only the6.4s smoke.
