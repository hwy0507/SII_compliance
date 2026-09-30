"""Low-memory NumPy MLP readout fit for a fixed pure ESN reservoir."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7  # noqa: E402


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def trace_path(case):
    root = ROOT / "outputs" / case
    for p in [root / "rollout.npz", root / "rollout" / "rollout.npz", *sorted(root.glob("*/rollout.npz"))]:
        if p.exists():
            return p
    raise FileNotFoundError(case)


def load_case(case):
    p = trace_path(case)
    with np.load(p, allow_pickle=False) as z:
        obs = np.asarray(z["observation"], dtype=np.float32)
        action = np.asarray(z["applied_action"], dtype=np.float32)
    if obs.ndim != 2 or obs.shape[1] != 48 or action.shape != (len(obs), 7):
        raise ValueError(f"invalid trace {p}")
    return case, p, obs, action


def make_features(base, cases):
    obs_all = np.concatenate([r[2] for r in cases])
    mean = obs_all.mean(0).astype(np.float32)
    std = obs_all.std(0).clip(min=.03).astype(np.float32)
    actor = ESN128Proprio48Action7(mean, std, seed=int(base["seed"]))
    actor.win = base["win"].astype(float)
    actor.w = base["w"].astype(float)
    actor.leak = base["leak"].astype(float)
    actor.input_mask = base["input_mask"].astype(float)
    fs = []
    for _, _, obs, _ in cases:
        actor.reset()
        fs.append(np.asarray([actor.features(x) for x in obs], dtype=np.float32))
    allf = np.concatenate(fs)
    fmean = allf.mean(0).astype(np.float32)
    fstd = allf.std(0).clip(min=.03).astype(np.float32)
    x = np.concatenate([(f - fmean) / fstd for f in fs], 0).astype(np.float32)
    y = np.concatenate([r[3] for r in cases], 0).astype(np.float32)
    return mean, std, fmean, fstd, x, y


def activate(raw):
    out = np.tanh(raw)
    out[:, 0] = 1.0 / (1.0 + np.exp(-np.clip(raw[:, 0], -40, 40)))
    return out


def fit(x, y, seed, epochs, batch_size, lr, weight_decay):
    rng = np.random.default_rng(seed)
    n, d = x.shape
    h = 128
    # Small deterministic perturbation around the registered readout feature
    # dimension; this model is still the same canonical ESN contract.
    w1 = rng.normal(0.0, 0.03 / np.sqrt(d), (h, d)).astype(np.float32)
    b1 = np.zeros(h, dtype=np.float32)
    w2 = rng.normal(0.0, 0.03 / np.sqrt(h), (7, h)).astype(np.float32)
    b2 = np.zeros(7, dtype=np.float32)
    params = [w1, b1, w2, b2]
    m = [np.zeros_like(p) for p in params]
    v = [np.zeros_like(p) for p in params]
    step = 0
    for _ in range(epochs):
        order = rng.permutation(n)
        for start in range(0, n, batch_size):
            idx = order[start:start + batch_size]
            xb, yb = x[idx], y[idx]
            z = xb @ w1.T + b1
            hh = np.tanh(z)
            raw = hh @ w2.T + b2
            pred = activate(raw)
            diff = (pred - yb).astype(np.float32)
            grad_raw = diff * (2.0 / len(idx))
            sig = pred[:, 0]
            grad_raw[:, 0] *= sig * (1.0 - sig)
            grad_raw[:, 1:] *= 1.0 - pred[:, 1:] ** 2
            gw2 = grad_raw.T @ hh + weight_decay * w2
            gb2 = grad_raw.sum(0)
            gh = grad_raw @ w2
            gz = gh * (1.0 - hh ** 2)
            gw1 = gz.T @ xb + weight_decay * w1
            gb1 = gz.sum(0)
            grads = [gw1, gb1, gw2, gb2]
            step += 1
            beta1, beta2, eps = .9, .999, 1e-8
            for i, (p, g) in enumerate(zip(params, grads)):
                m[i] = beta1 * m[i] + (1 - beta1) * g
                v[i] = beta2 * v[i] + (1 - beta2) * (g * g)
                mh = m[i] / (1 - beta1 ** step)
                vh = v[i] / (1 - beta2 ** step)
                p -= lr * mh / (np.sqrt(vh) + eps)
    return w1, b1, w2, b2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--train-case", action="append", required=True)
    ap.add_argument("--seed", type=int, default=2026092913)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--lr", type=float, default=2e-3)
    ap.add_argument("--weight-decay", type=float, default=1e-5)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with np.load(args.base, allow_pickle=False) as z:
        if str(z["contract"]) != "proprio48_esn128_action7_v1":
            raise ValueError("base contract")
        base = {k: z[k].copy() for k in z.files if k != "metadata"}
    cases = [load_case(c) for c in args.train_case]
    mean, std, fmean, fstd, x, y = make_features(base, cases)
    w1, b1, w2, b2 = fit(x, y, args.seed, args.epochs, args.batch_size, args.lr, args.weight_decay)
    ck = dict(contract="proprio48_esn128_action7_v1", seed=np.int64(args.seed), mean=mean, std=std,
              win=base["win"], w=base["w"], leak=base["leak"], input_mask=base["input_mask"],
              alpha=np.float64(1.0), output_gain=np.float64(1.0), fmean=fmean, fstd=fstd,
              w1=w1, b1=b1, w2=w2, b2=b2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, **ck)
    meta = dict(contract=ck["contract"], method="fixed_reservoir_numpy_mlp_readout",
                base_checkpoint=str(args.base), base_checkpoint_sha256=digest(args.base),
                trace_cases=[r[0] for r in cases], trace_sha256=[digest(r[1]) for r in cases],
                seed=args.seed, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr,
                forbidden_inputs=["contact truth", "ball state", "event time", "task stage", "visual/range", "geometry"],
                deployment_contract="pure ESN; hybrid_vmc_blend=0", fit_samples=int(len(x)),
                output_sha256=digest(args.output))
    args.output.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    main()
