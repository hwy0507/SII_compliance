"""Fit a pure proprio48 ESN readout with a fixed reservoir and NumPy.

This is a low-memory companion to the PyTorch trainer.  It keeps the
reservoir and first nonlinear readout layer from a registered checkpoint and
fits only the final action readout on saved observation/action traces.  The
trace labels are the actions actually submitted by the source run; deployment
uses ``hybrid-vmc-blend=0``.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7  # noqa: E402


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def trace_path(case: str) -> Path:
    root = ROOT / "outputs" / case
    options = [root / "rollout.npz", root / "rollout" / "rollout.npz"]
    options.extend(sorted(root.glob("*/rollout.npz")))
    for p in options:
        if p.exists():
            return p
    raise FileNotFoundError(f"no rollout.npz for {case}")


def load_case(case: str) -> dict:
    p = trace_path(case)
    with np.load(p, allow_pickle=False) as z:
        obs = np.asarray(z["observation"], dtype=np.float32)
        action = np.asarray(z["applied_action"], dtype=np.float32)
    if obs.ndim != 2 or obs.shape[1] != 48 or action.shape != (len(obs), 7):
        raise ValueError(f"invalid canonical trace {p}: {obs.shape}, {action.shape}")
    return {"case": case, "path": str(p), "sha256": digest(p), "obs": obs, "action": action}


def inverse_action(y: np.ndarray) -> np.ndarray:
    y = np.clip(np.asarray(y, dtype=np.float64), -0.999, 0.999)
    out = np.arctanh(y)
    p = np.clip(y[:, 0], 1e-4, 1.0 - 1e-4)
    out[:, 0] = np.log(p / (1.0 - p))
    return out


def features(actor: ESN128Proprio48Action7, obs: np.ndarray) -> np.ndarray:
    actor.reset()
    return np.asarray([actor.features(row) for row in obs], dtype=np.float64)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--train-case", action="append", required=True)
    ap.add_argument("--ridge", type=float, default=0.03)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.ridge <= 0:
        raise ValueError("ridge must be positive")

    rows = [load_case(x) for x in args.train_case]
    with np.load(args.base, allow_pickle=False) as z:
        if str(z["contract"]) != "proprio48_esn128_action7_v1":
            raise ValueError("base checkpoint contract")
        base = {k: z[k].copy() for k in z.files if k != "metadata"}

    obs_all = np.concatenate([r["obs"] for r in rows], axis=0)
    mean = obs_all.mean(axis=0).astype(np.float32)
    std = obs_all.std(axis=0).clip(min=0.03).astype(np.float32)
    actor = ESN128Proprio48Action7(mean, std, seed=int(base.get("seed", 20260921)))
    actor.win = np.asarray(base["win"], dtype=np.float64)
    actor.w = np.asarray(base["w"], dtype=np.float64)
    actor.leak = np.asarray(base["leak"], dtype=np.float64)
    actor.input_mask = np.asarray(base["input_mask"], dtype=np.float64)
    actor.alpha = 1.0
    actor.output_gain = 1.0

    fs = [features(actor, r["obs"]) for r in rows]
    fcat = np.concatenate(fs, axis=0)
    fmean = fcat.mean(axis=0)
    fstd = np.maximum(fcat.std(axis=0), 0.03)
    x = np.concatenate([(f - fmean) / fstd for f in fs], axis=0)
    # Preserve the registered nonlinear hidden layer; only the final action
    # readout is fitted.  This keeps the checkpoint shape compatible with the
    # canonical pure-ESN runtime.
    hidden = np.tanh(x @ np.asarray(base["w1"], dtype=np.float64).T + np.asarray(base["b1"], dtype=np.float64))
    x = np.c_[hidden, np.ones(len(hidden))]
    y = inverse_action(np.concatenate([r["action"] for r in rows], axis=0))

    # Fixed ridge readout.  The action labels are the source execution
    # requests; no contact or task metadata enters this solve.
    lhs = x.T @ x + float(args.ridge) * np.eye(x.shape[1])
    rhs = x.T @ y
    solved = np.linalg.solve(lhs, rhs)
    w2 = solved[:-1].T.astype(np.float32)
    b2 = solved[-1].astype(np.float32)

    checkpoint = dict(
        contract="proprio48_esn128_action7_v1", seed=np.int64(actor.seed), mean=mean,
        std=std, win=actor.win.astype(np.float32), w=actor.w.astype(np.float32),
        leak=actor.leak.astype(np.float32), input_mask=actor.input_mask.astype(np.float32),
        alpha=np.float64(1.0), output_gain=np.float64(1.0),
        fmean=fmean.astype(np.float32), fstd=fstd.astype(np.float32),
        w1=np.asarray(base["w1"], dtype=np.float32), b1=np.asarray(base["b1"], dtype=np.float32),
        w2=w2, b2=b2,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, **checkpoint)
    metadata = {
        "contract": checkpoint["contract"], "method": "fixed_reservoir_ridge_readout",
        "base_checkpoint": str(args.base), "base_checkpoint_sha256": digest(args.base),
        "trace_cases": [r["case"] for r in rows],
        "trace_sha256": [r["sha256"] for r in rows], "ridge": args.ridge,
        "forbidden_inputs": ["contact truth", "ball state", "event time", "task stage", "visual/range", "geometry"],
        "deployment_contract": "pure ESN; hybrid_vmc_blend=0",
        "fit_samples": int(len(x)), "output_sha256": digest(args.output),
    }
    args.output.with_suffix(".json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
