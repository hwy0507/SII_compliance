#!/usr/bin/env python3
"""Materialize pre-registered action-readout smoothing variants for a pure ESN."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    plan = json.loads(args.config.read_text())
    allowed = {float(v) for v in plan["alpha_values"]}
    if allowed != {0.25, 0.5, 0.75}:
        raise ValueError("unexpected alpha screen")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as z:
        arrays = {k: z[k].copy() for k in z.files}
    if str(arrays.get("contract", "")) != "proprio48_esn128_action7_v1":
        raise ValueError("wrong ESN contract")
    if arrays["win"].shape != (128, 49) or arrays["w"].shape != (128, 128):
        raise ValueError("wrong reservoir shape")
    base_hash = sha(args.base)
    variants = []
    for alpha in sorted(allowed):
        checkpoint = dict(arrays)
        checkpoint["alpha"] = np.float64(alpha)
        path = args.output / f"esn_alpha_{alpha:.2f}.npz"
        np.savez_compressed(path, **checkpoint)
        variants.append({"alpha": alpha, "path": str(path), "sha256": sha(path), "base_sha256": base_hash})
    metadata = {"contract": "pure_esn_alpha_screen_20261001_v1", "base_checkpoint": str(args.base),
                "base_sha256": base_hash, "config": str(args.config), "config_sha256": sha(args.config),
                "variants": variants, "actor_contract": plan["actor_contract"],
                "forbidden_inputs": plan["forbidden_inputs"], "unchanged": plan["unchanged"],
                "selection": plan["selection"]}
    (args.output / "SCREEN_PLAN.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
