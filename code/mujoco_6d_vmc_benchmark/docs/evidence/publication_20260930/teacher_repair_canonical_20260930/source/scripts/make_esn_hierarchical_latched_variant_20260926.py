"""Add sustained-evidence episode latching to a frozen hierarchical selector."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import sha


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--confirm-steps", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if not 1 <= args.confirm_steps <= 25:
        raise ValueError("confirm steps must be in [1, 25]")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_hierarchical_margin_v1":
            raise ValueError("unsupported base contract")
        payload = {key: source[key].copy() for key in source.files if key not in ("contract", "metadata")}
        base_metadata = json.loads(str(source["metadata"]))
    payload["selector_confirm_steps"] = np.int64(args.confirm_steps)
    metadata = {
        "method": "frozen_hierarchical_latched_margin_selector",
        "base_sha256": sha(args.base),
        "selector_threshold": 0.5,
        "selector_confirm_steps": args.confirm_steps,
        "selector_confirmation_seconds": 0.04 * args.confirm_steps,
        "selector_offset": base_metadata.get("selector_offset_from_zero", base_metadata.get("gate_offset")),
        "gate_metrics": base_metadata["gate_metrics"],
        "temporal_logic": "activate after sustained reservoir evidence; latch margin expert until episode reset",
        "deployment_inputs": "unchanged proprio48; selector and latch use only reservoir-derived history",
        "frozen_components": ["all checkpoint weights", "R15 base policy", "margin expert", "reservoir",
                              "normalization", "action filter", "safety filter", "task and penetration gates"],
    }
    checkpoint = args.output / "hierarchical_margin_latched.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(
            stream,
            contract="proprio48_esn128_action7_hierarchical_margin_latched_v1",
            metadata=json.dumps(metadata),
            **payload,
        )
    report = {**metadata, "checkpoint_sha256": sha(checkpoint)}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
