"""Create a readout interpolation checkpoint for a predeclared diagnostic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import sha


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--adapted", type=Path, required=True)
    p.add_argument("--beta", type=float, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if not 0.0 < args.beta < 1.0 or args.output.exists():
        raise ValueError("beta must be in (0,1) and output must be fresh")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as b, np.load(args.adapted, allow_pickle=False) as a:
        if str(b["contract"]) != "proprio48_esn128_action7_v1" or str(a["contract"]) != str(b["contract"]):
            raise ValueError("checkpoint contract mismatch")
        payload = {key: b[key].copy() for key in b.files if key not in ("metadata", "w2", "b2")}
        payload["w2"] = ((1.0 - args.beta) * b["w2"] + args.beta * a["w2"]).astype(b["w2"].dtype)
        payload["b2"] = ((1.0 - args.beta) * b["b2"] + args.beta * a["b2"]).astype(b["b2"].dtype)
        payload["metadata"] = json.dumps({
            "method": "readout_interpolation",
            "base_sha256": sha(args.base),
            "adapted_sha256": sha(args.adapted),
            "beta": args.beta,
            "scope": "development physical diagnostic; no checkpoint selection",
        })
    checkpoint = args.output / "blended.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, **payload)
    report = {"checkpoint_sha256": sha(checkpoint), "base_sha256": sha(args.base), "adapted_sha256": sha(args.adapted), "beta": args.beta}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
