# Office baseline transfer bridge

This bridge evaluates frozen primitive policies in main commit 7cd5f4b7ac0a3056df76ac62bc690ded0724b104, office-tool-contact-v5. It does not modify main, the environment, common WBC reference generator, actor observation, task gates or actuator limits. The exact upstream canonical48 is passed to each policy. Four explicit callback seams are checked before compilation; the executed evaluator text and its hash are retained alongside upstream source hashes.

The expected development MJB is b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1. A changed WBC/source/configuration requires a separately frozen and verified cohort. The current bridge intentionally refuses a model mismatch.

Methods: nominal (no callback), zero_bridge (zero callback for equivalence), direct_rl (7D saved policy), parameter_fixed (BO-derived prior), parameter_rl (7/5/7D saved policy plus the same controller). Use --controller admittance, impedance or vmc for parameter methods. RL requires --checkpoint. All methods reuse the original full-run settings and main's success/strict definitions. A --probe result is an interface diagnostic, never full task evaluation.

Run on Spark under a memory-limited foreground scope after checking the total simulator count is below four:

```sh
source /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/gpu_env.sh
systemd-run --user --scope --quiet -p MemoryMax=3G -p MemorySwapMax=0 \
  python /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge/frozen02/evaluate.py \
  --method zero_bridge --probe 0.08 --output /absolute/new/output
```

Full evaluations omit --probe. No training occurs, and saved normalizer counters must remain unchanged. Outputs include source patch/text, execution and checkpoint hashes, original physical metrics/contacts/plan/MJB/state, baseline observation/action arrays, and parameter/tank trajectories where applicable. Keep the original source-based audit fields and the explicit executed-source hash together; the callbacks mean the executed evaluator is not byte-identical to main.

Known limitation: the intrinsic classical controller has internal virtual state and model-based kinematics, as in its fixed baseline; the RL actor receives only canonical48. The parameter storage-change budget is not a global passivity proof. See docs/FINAL_ENV_BASELINE_PROTOCOL_20261002.md and docs/ONLINE_PARAMETER_RL_20261002.md.

The impedance method intentionally replaces the velocity tracking torque law with its impedance wrench-to-joint-torque law, through the original torque projection and slew limiter. This is the classical controller under comparison, not an unchanged low-level velocity controller. Nominal WBC references, task executive, physical environment and actuator constraints remain shared.

Validation update: interface01 rejected the host-recompiled model before integration. MODEL_MISMATCH_AUDIT01.json records mesh collision-tree/path and floating-point differences. Frozen02 loads the verified original archive before unchanged initialization. All seven 80ms checks matched the archived MJB, and INTERFACE_AUDIT.json verifies exact zero-callback state/observation/control equivalence, including matching diagnostic NaN positions. This does not establish contact/full-horizon success.
