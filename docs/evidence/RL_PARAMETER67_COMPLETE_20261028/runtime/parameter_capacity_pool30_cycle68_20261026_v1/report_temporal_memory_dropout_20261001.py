"""Independently audit the complete memory and paired-dropout diagnostic."""
import argparse
import json
from pathlib import Path
import numpy as np
from audit_temporal_narrow_screen_20261001 import audit, sha


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    campaign = args.root / "temporal_s52_latent_dropout_20261001_v1"
    state = json.loads((campaign / "execution.json").read_text())
    if state["status"] != "complete":
        raise RuntimeError("Dropout campaign incomplete")
    reference = args.root / "temporal_frozen_runtime_s52_20261001_v1"
    reset = args.root / "temporal_s52_memory_reset_20261001_v1"
    rows = [dict(setting="memory_reset", **audit(reset, "esn"))]
    training, parity = {}, {}
    for label in ("p000", "p010"):
        train, evaluation = campaign / f"{label}_train", campaign / f"{label}_eval"
        training[label] = json.loads((train / "TRAINING_COMPLETE.json").read_text())
        for kind in ("esn", "mlp"):
            row = audit(evaluation, kind)
            rows.append(dict(setting=label, **row))
            if label == "p000":
                parity[kind] = dict(checkpoint_byte_identical=sha(evaluation/f"{kind}_temporal.npz") == sha(reference/f"{kind}_temporal.npz"),
                                    rollout_byte_identical=sha(evaluation/f"{kind}_combined_v4.npz") == sha(reference/f"{kind}_combined_v4.npz"))
    for key in ("train_fixture_ids", "validation_fixture_ids", "teacher_trace_sha256", "teacher_chain_sha256",
                "manifest_sha256", "seed", "mlp_seed", "epochs", "trainable_parameters"):
        if training["p000"][key] != training["p010"][key]:
            raise ValueError(f"Unmatched training field: {key}")
    for kind, fields in (("esn", ("mean", "std", "win", "w", "leak", "input_mask", "fmean", "fstd", "alpha", "output_gain")),
                         ("mlp", ("mean", "std", "hidden"))):
        with np.load(campaign/f"p000_train/{kind}_temporal.npz") as a, np.load(campaign/f"p010_train/{kind}_temporal.npz") as b:
            for field in fields:
                if not np.array_equal(a[field], b[field]):
                    raise ValueError(f"Unexpected non-readout difference {kind}/{field}")
    report = dict(rows=rows, training=training, zero_dropout_parity=parity,
                  source_sha256=sha(Path(__file__)), campaign_execution_sha256=sha(campaign/"execution.json"),
                  matched_data_seed_epochs_width_and_normalization=True,
                  limitations=["Single training seed pair and one development scene, not cross-condition generalization.",
                               "ESN and MLP apply dropout to different representations; equal probability/width/budget does not imply equivalent feature semantics.",
                               "Memory reset changes history and feature distribution; lower metrics without task completion are not an improvement.",
                               "All failures retained; no formal result or ESN superiority inferred from replay MSE."])
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"rows": [{k:r[k] for k in ("setting","method","task_success","strict_success","final_task_stage","position_rmse_3d_mm","peak_torque_nm","peak_speed_mps","external_penetration_mm")} for r in rows], "zero_dropout_parity":parity}, indent=2))


if __name__ == "__main__":
    main()
