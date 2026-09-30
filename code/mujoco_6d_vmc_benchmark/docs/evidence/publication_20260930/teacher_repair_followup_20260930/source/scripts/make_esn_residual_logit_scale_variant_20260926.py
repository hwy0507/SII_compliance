"""Create an auditable residual-logit scale variant of a proprio48 ESN."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--scale", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    if not np.isfinite(args.scale) or not 1.0 < args.scale <= 1.5:
        raise ValueError("scale must be finite and in (1, 1.5]")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_v1":
            raise ValueError("unsupported checkpoint contract")
        payload = {key: source[key].copy() for key in source.files if key != "metadata"}
    if payload["w2"].shape[0] != 7 or payload["b2"].shape != (7,):
        raise ValueError("expected a seven-channel final readout")
    payload["w2"][1:] *= args.scale
    payload["b2"][1:] *= args.scale
    payload["metadata"] = json.dumps(
        {
            "method": "fixed_esn_residual_logit_scale_diagnostic",
            "base_sha256": sha256(args.base),
            "residual_logit_scale": args.scale,
            "unchanged_channel": "channel 0 WBC feedback-authority schedule",
            "scaled_channels": "channels 1:7 translational and rotational residual logits",
            "scope": "R16 exposed-condition margin diagnostic; physical validation required",
            "deployment_inputs": "unchanged proprio48",
        }
    )
    checkpoint = args.output / "model.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream, **payload)
    report = {
        "base_sha256": sha256(args.base),
        "residual_logit_scale": args.scale,
        "checkpoint_sha256": sha256(checkpoint),
    }
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
