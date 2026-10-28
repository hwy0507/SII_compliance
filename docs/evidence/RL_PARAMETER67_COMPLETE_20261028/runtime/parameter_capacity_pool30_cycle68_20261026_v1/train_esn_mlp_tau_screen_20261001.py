#!/usr/bin/env python3
"""Pre-registered ESN leak-time screen on the locked VMC teacher bank.

Only the fixed reservoir leak vector changes across profiles.  The actor
contract, 128-unit budget, teacher manifest, identity split, loss weights and
MLP control are otherwise unchanged.  Runtime inputs remain canonical48D
proprioception; forbidden contact/object/stage/visual fields are never read.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7

WEIGHTED = ROOT / "tools" / "train_vmc_teacher_esn_mlp_weighted_20261001.py"
spec = importlib.util.spec_from_file_location("weighted_train", WEIGHTED)
weighted = importlib.util.module_from_spec(spec); spec.loader.exec_module(weighted)

PROFILES = {"fast": (0.04, 0.16, 0.64), "baseline": (0.08, 0.40, 1.60), "slow": (0.16, 0.80, 3.20)}
SEEDS = {"fast": 2026100109, "baseline": 2026100110, "slow": 2026100111}

def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def leak_for(tau):
    dt = ESN128Proprio48Action7.dt
    return 1.0 - np.exp(-dt / np.concatenate([np.full(43, tau[0]), np.full(43, tau[1]), np.full(42, tau[2])]))

def esn_features(rows, seed, tau, normalization=None):
    if normalization is None:
        obs = np.concatenate([r["observation"] for r in rows])
        mean = obs.mean(0).astype(np.float32); std = obs.std(0).clip(min=.03).astype(np.float32)
    else:
        mean, std, fmean, fstd = normalization
    actor = ESN128Proprio48Action7(mean, std, seed=seed)
    actor.leak = leak_for(tau).astype(np.float64)
    fs = []
    for r in rows:
        actor.reset(); fs.append(np.stack([actor.features(x) for x in r["observation"]]).astype(np.float32))
    if normalization is None:
        packed = np.concatenate(fs); fmean = packed.mean(0).astype(np.float32); fstd = packed.std(0).clip(min=.03).astype(np.float32)
    return mean, std, fmean, fstd, fs, actor

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True); ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True); ap.add_argument("--profile", choices=sorted(PROFILES), required=True)
    ap.add_argument("--seed", type=int, default=None); ap.add_argument("--epochs", type=int, default=160)
    a = ap.parse_args(); profile = a.profile; seed = SEEDS[profile] if a.seed is None else a.seed
    if a.output.exists(): raise FileExistsError(a.output)
    a.output.mkdir(parents=True)
    if sha(a.manifest) != "6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3": raise ValueError("Unregistered manifest")
    rows, manifest = weighted.base.load_rows(a.manifest, a.root); train, val = weighted.base.split_rows(rows)
    if len(train) != 7 or len(val) != 2: raise ValueError("Unexpected frozen split")
    wm, wv = weighted.weights(train, 3.0), weighted.weights(val, 3.0)
    y = np.concatenate([r["action"] for r in train]).astype(np.float32); yv = np.concatenate([r["action"] for r in val]).astype(np.float32)
    tau = PROFILES[profile]
    mean, std, fmean, fstd, fs, reservoir = esn_features(train, seed, tau)
    _, _, _, _, vfs, _ = esn_features(val, seed, tau, (mean, std, fmean, fstd))
    x = np.concatenate([(f-fmean)/fstd for f in fs]).astype(np.float32); xv = np.concatenate([(f-fmean)/fstd for f in vfs]).astype(np.float32)
    w, wvcat = np.concatenate(wm), np.concatenate(wv)
    esn_state, eh, ev, epred = weighted.fit_model(x, y, w, xv, yv, wvcat, "esn", seed, a.epochs)
    ex = np.concatenate([(r["observation"]-mean)/std for r in train]).astype(np.float32); exv = np.concatenate([(r["observation"]-mean)/std for r in val]).astype(np.float32)
    mlp_state, mh, mv, mpred = weighted.fit_model(ex, y, w, exv, yv, wvcat, "mlp", seed+1, a.epochs)
    esn = weighted.pack_esn(esn_state, (mean, std, fmean, fstd), reservoir, seed)
    mlp = weighted.pack_mlp(mlp_state, mean, std, seed+1)
    ep, mp = a.output/"esn_tau.npz", a.output/"mlp_tau.npz"; np.savez_compressed(ep, **esn); np.savez_compressed(mp, **mlp)
    from current_student_policy_20260921 import load_current
    parity = {}
    for kind, path, prediction, score in (("esn", ep, epred, ev), ("mlp", mp, mpred, mv)):
        actor = load_current(path); replay=[]
        for row in val:
            actor.reset(); replay.append(np.stack([actor.act(x) for x in row["observation"]]))
        replay=np.concatenate(replay); delta=float(np.max(np.abs(replay-prediction))); replay_score=float(np.average(np.mean((replay-yv)**2,axis=1),weights=wvcat))
        if delta > 2e-6 or abs(replay_score-score) > 1e-8: raise ValueError(f"{kind} export parity mismatch")
        parity[kind] = {"max_abs": delta, "weighted_mse": replay_score}
    meta = {"contract":"VMC_teacher_ESN_tau_screen_20261001_v1", "profile":profile, "tau_s":tau, "seed":seed, "mlp_seed":seed+1, "manifest_sha256":sha(a.manifest), "train_fixture_ids":[r["fixture_id"] for r in train], "validation_fixture_ids":[r["fixture_id"] for r in val], "checkpoint_sha256":{"esn":sha(ep),"mlp":sha(mp)}, "esn_validation_weighted_mse":ev,"mlp_validation_weighted_mse":mv,"export_parity":parity,"forbidden_inputs":["contact truth","object/ball state","event time","task stage","visual/range"],"actor_contract":"canonical48D/action7; pure proprioception","reservoir_width":128,"loss_emphasis":3.0,"source_sha256":{str(Path(__file__)):sha(Path(__file__)),str(WEIGHTED):sha(WEIGHTED),str(ROOT/"scripts"/"esn128_proprio48_action7_20260921.py"):sha(ROOT/"scripts"/"esn128_proprio48_action7_20260921.py")},"teacher_trace_sha256":{r["fixture_id"]:r["trace_sha256"] for r in rows},"teacher_chain_sha256":{r["fixture_id"]:r["execution_chain_sha256"] for r in rows},"invocation":sys.argv}
    (a.output/"TRAINING_COMPLETE.json").write_text(json.dumps(meta,indent=2)+"\n"); (a.output/"training_history.json").write_text(json.dumps({"esn":eh,"mlp":mh},indent=2)+"\n"); print(json.dumps(meta,indent=2))

if __name__ == "__main__": main()
