"""Create an auditable one-channel ESN readout-bias diagnostic."""
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
    parser.add_argument("--channel", type=int, required=True)
    parser.add_argument("--delta", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.channel < 0 or args.channel >= 7 or not np.isfinite(args.delta):
        raise ValueError("invalid channel or delta")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_v1":
            raise ValueError("unsupported contract")
        payload = {key: source[key].copy() for key in source.files if key not in ("metadata", "b2")}
        bias = source["b2"].copy()
        bias[args.channel] += args.delta
        payload["b2"] = bias
        payload["metadata"] = json.dumps({
            "method": "fixed_esn_logit_bias_diagnostic",
            "base_sha256": sha256(args.base),
            "channel": args.channel,
            "delta": args.delta,
            "scope": "causal development diagnostic only; not a selected policy",
        })
    checkpoint = args.output / "model.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, **payload)
    report = {
        "base_sha256": sha256(args.base),
        "channel": args.channel,
        "delta": args.delta,
        "checkpoint_sha256": sha256(checkpoint),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
