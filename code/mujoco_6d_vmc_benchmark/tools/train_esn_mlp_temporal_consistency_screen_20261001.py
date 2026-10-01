#!/usr/bin/env python3
"""Train paired pure ESN/MLP students with a registered action-delta loss."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
import torch
from torch import nn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
SRC = ROOT / "tools" / "train_esn_mlp_input_scale_screen_20261001.py"
spec = importlib.util.spec_from_file_location("input_train", SRC)
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""): h.update(block)
    return h.hexdigest()

def activate(raw):
    return torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)

def fit_model(xseq, yseq, wseq, vxseq, vyseq, vwseq, kind, seed, delta_weight, epochs, latent_dropout=0.0):
    if not 0 <= latent_dropout < 1:
        raise ValueError("invalid latent dropout probability")
    torch.set_num_threads(1); torch.manual_seed(seed)
    if kind == "esn": model = nn.Sequential(nn.Linear(176, 128), nn.Tanh(), nn.Linear(128, 7))
    else: model = nn.Sequential(nn.Linear(48, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh(), nn.Linear(128, 7))
    opt = torch.optim.AdamW(model.parameters(), lr=2e-3, weight_decay=1e-5)
    tx = [torch.from_numpy(x) for x in xseq]; ty = [torch.from_numpy(y) for y in yseq]; tw = [torch.from_numpy(w) for w in wseq]
    vx = [torch.from_numpy(x) for x in vxseq]; vy = [torch.from_numpy(y) for y in vyseq]; vw = [torch.from_numpy(w) for w in vwseq]
    best = float("inf"); best_state = None; history = []
    for epoch in range(epochs):
        losses = []
        for x, y, w in zip(tx, ty, tw):
            if latent_dropout:
                # One shared mask per trajectory: no artificial temporal jumps.
                keep = 1.0 - latent_dropout
                mask = torch.bernoulli(torch.full((1, 128), keep)) / keep
                if kind == "esn":
                    latent_input = torch.cat((x[:, :48], x[:, 48:] * mask), dim=1)
                    pred = activate(model(latent_input))
                else:
                    latent = model[1](model[0](x)) * mask
                    pred = activate(model[4](model[3](model[2](latent))))
            else:
                pred = activate(model(x))
            action_loss = (((pred - y) ** 2).mean(1) * w).mean() / w.mean()
            if len(y) > 1:
                target_delta = y[1:] - y[:-1]
                pred_delta = pred[1:] - pred[:-1]
                pair_w = 0.5 * (w[1:] + w[:-1])
                delta_loss = (((pred_delta - target_delta) ** 2).mean(1) * pair_w).mean() / pair_w.mean()
            else:
                delta_loss = action_loss * 0.0
            loss = action_loss + float(delta_weight) * delta_loss
            opt.zero_grad(set_to_none=True); loss.backward(); nn.utils.clip_grad_norm_(model.parameters(), 5.); opt.step(); losses.append(float(loss.detach()))
        with torch.no_grad():
            raw = [activate(model(x)) for x in vx]
            val_num = sum((((p - y) ** 2).mean(1) * w).sum() for p, y, w in zip(raw, vy, vw))
            val_den = sum(w.sum() for w in vw); val = float(val_num / val_den)
        if epoch == 0 or (epoch + 1) % 10 == 0: history.append({"epoch": epoch + 1, "train_loss": float(np.mean(losses)), "val_weighted_action_mse": val})
        if val < best:
            best = val; best_state = {k: v.detach().numpy().copy() for k, v in model.state_dict().items()}
    model.load_state_dict({k: torch.from_numpy(v) for k, v in best_state.items()})
    with torch.no_grad(): pred = [activate(model(x)).numpy() for x in vx]
    return best_state, history, best, pred

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--manifest", type=Path, required=True); ap.add_argument("--root", type=Path, required=True); ap.add_argument("--config", type=Path, required=True); ap.add_argument("--output", type=Path, required=True); ap.add_argument("--delta-weight", type=float, required=True)
    args = ap.parse_args(); plan = json.loads(args.config.read_text())
    from datetime import datetime, timezone
    import subprocess
    execution = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
                 "invocation": sys.argv, "config_sha256": sha(args.config),
                 "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    if plan.get("require_runtime_guard", False):
        from verify_temporal_frozen_runtime_20261001 import runtime
        execution["runtime"] = runtime()
    if args.output.exists(): raise FileExistsError(args.output)
    if args.delta_weight not in plan["delta_loss_values"]: raise ValueError("unregistered delta weight")
    if sha(args.manifest) != plan["manifest_sha256"]: raise ValueError("manifest hash mismatch")
    args.output.mkdir(parents=True)
    (args.output / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    for entries in json.loads(args.manifest.read_text())["categories"].values():
        for entry in entries:
            for filename in ("rollout.npz", "execution_chain.npz"):
                if sha(args.root / entry["folder"] / filename) != entry["raw_files_sha256"][filename]:
                    raise ValueError(f"Teacher source hash mismatch: {entry['fixture_id']}/{filename}")
    rows, _ = mod.weighted.base.load_rows(args.manifest, args.root); train, val = mod.weighted.base.split_rows(rows)
    if len(train) != 7 or len(val) != 2: raise ValueError("unexpected fixed split")
    wm, wv = mod.weighted.weights(train, 3.0), mod.weighted.weights(val, 3.0)
    yseq = [r["action"].astype(np.float32) for r in train]; vyseq = [r["action"].astype(np.float32) for r in val]
    mean, std, fmean, fstd, fs, reservoir = mod.features(train, int(plan["training_seed"]), .25)
    _, _, _, _, vfs, _ = mod.features(val, int(plan["training_seed"]), .25, (mean, std, fmean, fstd))
    xseq = [((f - fmean) / fstd).astype(np.float32) for f in fs]; vxseq = [((f - fmean) / fstd).astype(np.float32) for f in vfs]
    dropout = float(plan.get("latent_dropout", 0.0))
    es, eh, ev, epred = fit_model(xseq, yseq, wm, vxseq, vyseq, wv, "esn", int(plan["training_seed"]), args.delta_weight, int(plan["epochs"]), dropout)
    exseq = [((r["observation"] - mean) / std).astype(np.float32) for r in train]; evxseq = [((r["observation"] - mean) / std).astype(np.float32) for r in val]
    ms, mh, mv, mpred = fit_model(exseq, yseq, wm, evxseq, vyseq, wv, "mlp", int(plan["training_seed"]) + 1, args.delta_weight, int(plan["epochs"]), dropout)
    ep, mp = args.output / "esn_temporal.npz", args.output / "mlp_temporal.npz"
    np.savez_compressed(ep, **mod.weighted.pack_esn(es, (mean, std, fmean, fstd), reservoir, int(plan["training_seed"])))
    np.savez_compressed(mp, **mod.weighted.pack_mlp(ms, mean, std, int(plan["training_seed"]) + 1))
    from current_student_policy_20260921 import load_current
    parity = {}
    for kind, path, preds, score in (("esn", ep, epred, ev), ("mlp", mp, mpred, mv)):
        actor = load_current(path); replay = []
        for row in val:
            actor.reset(); replay.append(np.stack([actor.act(x) for x in row["observation"]]))
        delta = float(max(np.max(np.abs(a - b)) for a, b in zip(replay, preds)))
        rs = float(sum(np.sum(np.mean((a - b) ** 2, axis=1) * w) for a, b, w in zip(replay, vyseq, wv)) / sum(w.sum() for w in wv))
        if delta > 2e-6 or abs(rs - score) > 1e-8: raise ValueError(f"{kind} parity mismatch")
        parity[kind] = {"max_abs": delta, "weighted_action_mse": rs}
    meta = {"contract": "VMC_teacher_paired_ESN_MLP_temporal_consistency_screen_20261001_v1", "delta_weight": args.delta_weight, "input_scale": .25, "seed": int(plan["training_seed"]), "mlp_seed": int(plan["training_seed"]) + 1, "manifest_sha256": sha(args.manifest), "train_fixture_ids": [r["fixture_id"] for r in train], "validation_fixture_ids": [r["fixture_id"] for r in val], "checkpoint_sha256": {"esn": sha(ep), "mlp": sha(mp)}, "esn_validation_weighted_action_mse": ev, "mlp_validation_weighted_action_mse": mv, "export_parity": parity, "loss": "weighted action MSE + delta_weight * weighted consecutive-action delta MSE", "actor_contract": plan["actor_contract"], "forbidden_inputs": plan["forbidden_inputs"], "source_sha256": {str(Path(__file__)): sha(Path(__file__)), str(SRC): sha(SRC)}, "teacher_trace_sha256": {r["fixture_id"]: r["trace_sha256"] for r in rows}, "teacher_chain_sha256": {r["fixture_id"]: r["execution_chain_sha256"] for r in rows}, "invocation": sys.argv}
    meta.update(latent_dropout=dropout, config_sha256=sha(args.config), epochs=int(plan["epochs"]),
                dropout_semantics="one inverted Bernoulli mask on 128 features per training trajectory; ESN standardized reservoir features, MLP first hidden layer; disabled during validation/inference",
                torch_version=torch.__version__, numpy_version=np.__version__,
                trainable_parameters={"esn":23559,"mlp":23687})
    meta["source_sha256"].update({str(p): sha(p) for p in (mod.WEIGHTED, mod.weighted.BASE, ROOT/"scripts/current_student_policy_20260921.py", ROOT/"scripts/esn128_proprio48_action7_20260921.py")})
    (args.output / "TRAINING_COMPLETE.json").write_text(json.dumps(meta, indent=2) + "\n"); (args.output / "training_history.json").write_text(json.dumps({"esn": eh, "mlp": mh}, indent=2) + "\n")
    execution.update(status="complete", ended_utc=datetime.now(timezone.utc).isoformat(), training_record_sha256=sha(args.output/"TRAINING_COMPLETE.json"))
    (args.output / "execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    print(json.dumps(meta, indent=2))

if __name__ == "__main__": main()
