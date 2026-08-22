#!/usr/bin/env bash
set -euo pipefail

# Long-running server-side sweep for the independent multi-head ESN.  The
# development split is used for CEM updates; v4_final_held_out is evaluated
# only after each checkpoint is frozen and never feeds back into selection.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="/home/arm1/vmc_mujoco_runtime/.venv/bin/python"
MENAGERIE="/home/arm1/vmc_mujoco_runtime/mujoco_menagerie"
ROOT="/home/arm1/vmc_mujoco_runtime/outputs/dual_phase_esn_multhead_overnight_20260822"
MLP="/home/arm1/vmc_mujoco_runtime/outputs/dual_phase_mlp_screen_20260822/mlp_h128_s20265601.npz"

mkdir -p "$ROOT"
export MUJOCO_GL=osmesa
export PYTHONPATH="$SCRIPT_DIR"

# name seed reservoir basis population iterations smoothing
RUNS=(
  "seed01 20268501 160 40 20 18 0.85"
  "seed02 20268502 240 24 24 18 0.85"
  "seed03 20268503 320 24 24 18 0.95"
  "seed04 20268504 240 32 28 20 1.00"
  "seed05 20268505 320 32 24 20 0.75"
  "seed06 20268506 192 48 20 22 0.90"
)

for spec in "${RUNS[@]}"; do
  read -r name seed reservoir basis population iterations smoothing <<< "$spec"
  out="$ROOT/$name"
  mkdir -p "$out"
  model="$out/esn_cem_multhead_independent_best.npz"
  if [[ ! -f "$model" ]]; then
    "$PYTHON" -u "$SCRIPT_DIR/train_dual_phase_esn_cem_multhead.py" \
      --menagerie "$MENAGERIE" --out-dir "$out" \
      --iterations "$iterations" --population "$population" --elite-count 6 \
      --basis-dimension "$basis" --reservoir-size "$reservoir" \
      --yield-smoothing-alpha "$smoothing" --seed "$seed" \
      > "$out/train.log" 2>&1
  fi
  eval_out="$out/final_eval"
  if [[ ! -f "$eval_out/robustness.json" ]]; then
    mkdir -p "$eval_out"
    "$PYTHON" -u "$SCRIPT_DIR/evaluate_dual_phase_robustness.py" \
      --menagerie "$MENAGERIE" --out "$eval_out/robustness.json" \
      --esn "$model" --mlp "$MLP" --budget 0.04 \
      --split v4_final_held_out --methods PaperMPC VMC MLP ESN \
      > "$eval_out/eval.log" 2>&1
  fi
done

date -Is > "$ROOT/overnight_complete.txt"
