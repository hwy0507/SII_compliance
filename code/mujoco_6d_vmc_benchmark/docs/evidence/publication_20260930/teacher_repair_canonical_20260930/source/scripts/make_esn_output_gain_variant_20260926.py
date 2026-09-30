"""Create an auditable ESN output-gain diagnostic checkpoint."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--gain", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not np.isfinite(args.gain) or not 0.0 <= args.gain <= 1.0:
        raise ValueError("gain must be finite and in [0, 1]")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_v1":
            raise ValueError("unsupported contract")
        payload = {key: source[key].copy() for key in source.files if key not in ("metadata", "output_gain")}
        payload["output_gain"] = np.float64(args.gain)
        payload["metadata"] = json.dumps({
            "method": "fixed_esn_output_gain_diagnostic",
            "base_sha256": sha256(args.base),
            "output_gain": args.gain,
            "scope": "causal development diagnostic only",
        })
    checkpoint = args.output / "model.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, **payload)
    report = {
        "base_sha256": sha256(args.base),
        "output_gain": args.gain,
        "checkpoint_sha256": sha256(checkpoint),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
