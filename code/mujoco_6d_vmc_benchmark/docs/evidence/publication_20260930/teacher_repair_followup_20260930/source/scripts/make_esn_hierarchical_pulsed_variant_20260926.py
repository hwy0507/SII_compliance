"""Add a one-shot reservoir-triggered margin pulse to a frozen hierarchy."""
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
    parser.add_argument("--pulse-steps", type=int, required=True)
    parser.add_argument("--pulse-scale", type=float, default=1.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if (not 1 <= args.confirm_steps <= 25 or not 1 <= args.pulse_steps <= 100
            or not np.isfinite(args.pulse_scale) or not 0 < args.pulse_scale <= 1):
        raise ValueError("confirm steps must be in [1,25] and pulse steps in [1,100]")
    args.output.mkdir(parents=True)
    with np.load(args.base, allow_pickle=False) as source:
        if str(source["contract"]) != "proprio48_esn128_action7_hierarchical_margin_v1":
            raise ValueError("unsupported base contract")
        payload = {key: source[key].copy() for key in source.files if key not in ("contract", "metadata")}
        base_metadata = json.loads(str(source["metadata"]))
    payload["selector_confirm_steps"] = np.int64(args.confirm_steps)
    payload["selector_pulse_steps"] = np.int64(args.pulse_steps)
    payload["selector_pulse_scale"] = np.float64(args.pulse_scale)
    metadata = {
        "method": "frozen_phase_triggered_margin_pulse",
        "base_sha256": sha(args.base),
        "selector_threshold": 0.5,
        "selector_confirm_steps": args.confirm_steps,
        "selector_pulse_steps": args.pulse_steps,
        "selector_pulse_scale": args.pulse_scale,
        "selector_confirmation_seconds": 0.04 * args.confirm_steps,
        "selector_pulse_seconds": 0.04 * args.pulse_steps,
        "gate_metrics": base_metadata["gate_metrics"],
        "temporal_logic": "one pulse per episode; trigger from sustained reservoir phase evidence; then return to R15",
        "deployment_inputs": "unchanged proprio48 plus policy-local reservoir/counter state",
        "frozen_components": ["all checkpoint weights", "R15 base policy", "margin expert", "reservoir",
                              "normalization", "action filter", "safety filter", "task and penetration gates"],
    }
    checkpoint = args.output / "hierarchical_margin_pulsed.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(
            stream,
            contract="proprio48_esn128_action7_hierarchical_margin_pulsed_v1",
            metadata=json.dumps(metadata),
            **payload,
        )
    report = {**metadata, "checkpoint_sha256": sha(checkpoint)}
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
