#!/usr/bin/env python3
"""Overnight statistical validation of the v18b delay-line result.

Question: is ESN-DL's 16.7 N peak margin over MLP-DL (and the #1 overall
ranking) robust across independent training replicates, or a lucky draw?

replicate = {data noise realization, fit seeds}
          -> 7 scenario-aware teacher episodes
          -> ESN-DL x5 seeds (fixed tc=0.3/240 cfg) + one alternative cfg
          -> MLP + MLP-DL subprocesses (same information sets)
          -> 8-board eval x 5 controllers -> result.json

Morning: mean+-std / win rates / per-metric dominance / weight sensitivity
/ champion replicate checkpoints.
"""
from __future__ import annotations

import fcntl
import json
import os as _os
import subprocess
import sys
import time
from pathlib import Path

_GPU_LOCK = Path("/tmp/dl_gpu.lock")


def _locked_mlp(out_dir: Path, data_path: Path, hidden: int = 256) -> None:
    """MLP subprocesses share one GPU -- serialize them across workers."""
    for attempt in range(3):
        with open(_GPU_LOCK, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            try:
                D._mlp_subprocess(out_dir, data_path, hidden)
                return
            except RuntimeError:
                if attempt == 2:
                    raise
                time.sleep(10)

import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import delayline_experiment as D
import lift_experiment as L
from extraction_experiment import NeutralPolicy
from direct_esn_compliance import DirectESNController

WORKERS = 4
MAX_HOURS = 14.5
REPLICATES = tuple(range(120))
ROOT = Path("/home/arm1/vmc_mujoco_runtime/outputs/overnight_v18")
CFG_MAIN = json.load(open("/home/arm1/vmc_mujoco_runtime/outputs/dl_esn/dl_cfg.json"))
CFG_ALT = {}            # default reservoir, recorded for config sensitivity
SEEDS = (11, 29, 97, 123, 555)
METRICS = ("Fint", "peak", "errF_mm", "contact_s", "chatter", "saturation_s", "score")
NAMES = ("FW", "VMC", "MLP", "MLP-DL", "ESN-DL")


def log(rep: int, msg: str) -> None:
    print(f"[w{rep % WORKERS} {time.strftime('%H:%M:%S')}] {msg}", flush=True)


def collect(episodes, entry, data_seed):
    env = D._env_for_noise(entry)
    m, ep = L.rollout(env, data_seed, teacher=D._expert_for(entry), collect=True)
    env.close()
    episodes.append(dict(obs=list(ep["obs"]), actions=ep["actions"],
                         weights=ep["weights"]))
    return m


def run_replicate(rep: int) -> None:
    out = ROOT / f"rep{rep:03d}"
    if (out / "result.json").exists():
        log(rep, "skip (done)")
        return
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    data_seed = 1000 + rep * 37

    # 1) data
    episodes = []
    for entry in D.DATA_GRID:
        collect(episodes, entry, data_seed)
    np.savez_compressed(out / "teacher_data.npz",
                        episodes=np.asarray(episodes, dtype=object))
    log(rep, f"data done ({len(episodes)} eps, {time.time()-t0:.0f}s)")

    # 2) students
    for seed in SEEDS:
        D.fit_dl(episodes, seed, CFG_MAIN).model.save_npz(out / f"dl_s{seed}.npz")
    D.fit_dl(episodes, 11, CFG_ALT).model.save_npz(out / "dl_alt_s11.npz")
    (out / "mlp_raw").mkdir(parents=True, exist_ok=True)
    _locked_mlp(out / "mlp_raw", out / "teacher_data.npz")
    D._write_dl_episodes(episodes, out / "teacher_data_dl.npz")
    (out / "mlp_dl").mkdir(parents=True, exist_ok=True)
    _locked_mlp(out / "mlp_dl", out / "teacher_data_dl.npz")
    log(rep, f"students fitted ({time.time()-t0:.0f}s)")

    # 3) eval (deterministic boards -> one rollout each)
    esn = D.DelayLineEnsemble(
        [D.DelayLineESN(DirectESNController.from_npz(p))
         for p in sorted(out.glob("dl_s*.npz"))])
    alt = D.DelayLineESN(DirectESNController.from_npz(out / "dl_alt_s11.npz"))
    controllers = [("FW", NeutralPolicy()), ("VMC", L._tuned_vmc()),
                   ("MLP", D._load_mlp(out / "mlp_raw")),
                   ("MLP-DL", D._load_mlp(out / "mlp_dl", dl=True)),
                   ("ESN-DL", esn)]
    results = {n: [] for n, _ in controllers}
    for entry in D.EVAL_BOARDS:
        for name, policy in controllers:
            env = D._env_for(entry)
            m = L.rollout(env, 7, policy)
            env.close()
            results[name].append(m)
    table = {n: {k: float(np.mean([m[k] for m in ms])) for k in METRICS}
             for n, ms in results.items()}
    # alt-config sensitivity probe on one cue board
    env = D._env_for(D.EVAL_BOARDS[0])
    m_alt = L.rollout(env, 7, alt)
    env.close()
    table["_alt_cfg"] = {"peak": m_alt["peak"], "score": m_alt["score"]}
    table["_meta"] = {"replicate": rep, "data_seed": data_seed,
                      "elapsed_s": round(time.time() - t0, 1)}
    json.dump(table, open(out / "result.json", "w"), indent=1)
    log(rep, f"DONE ESN-DL={table['ESN-DL']['score']:.2f}/peak {table['ESN-DL']['peak']:.0f} "
             f"MLP-DL={table['MLP-DL']['score']:.2f}/peak {table['MLP-DL']['peak']:.0f} "
             f"({time.time()-t0:.0f}s)")


def aggregate() -> None:
    reps = sorted(ROOT.glob("rep*/result.json"))
    if not reps:
        print("no replicates")
        return
    tables = [json.load(open(p)) for p in reps]
    summary = {"n_replicates": len(tables), "per_controller": {}, "win_rates": {}}
    for name in NAMES:
        per = {k: [t[name][k] for t in tables] for k in METRICS}
        summary["per_controller"][name] = {
            k: [float(np.mean(v)), float(np.std(v))] for k, v in per.items()}
    wins = {n: 0 for n in NAMES}
    esn_beats = {"MLP-DL": 0, "MLP": 0, "VMC": 0, "FW": 0}
    for t in tables:
        best = min(NAMES, key=lambda n: t[n]["score"])
        wins[best] += 1
        for other in esn_beats:
            esn_beats[other] += int(t["ESN-DL"]["score"] < t[other]["score"])
    summary["win_rates"] = {n: wins[n] / len(tables) for n in NAMES}
    summary["esn_beats"] = {k: v / len(tables) for k, v in esn_beats.items()}
    dominance = {}
    for k in METRICS:
        if k == "score":
            continue
        dominance[k] = {"best": min(NAMES, key=lambda n: summary["per_controller"][n][k][0]),
                        "order": sorted(NAMES, key=lambda n: summary["per_controller"][n][k][0])}
    summary["dominance"] = dominance
    metric_keys = ["Fint", "peak", "errF_mm", "contact_s", "chatter", "saturation_s"]
    mat = np.stack([np.array([summary["per_controller"][n][k][0] for k in metric_keys])
                    for n in NAMES])
    norm = (mat - mat.min(axis=0)) / (mat.max(axis=0) - mat.min(axis=0) + 1e-12)
    rng = np.random.default_rng(7)
    p1 = {n: 0.0 for n in NAMES}
    for _ in range(2000):
        w = rng.dirichlet(np.ones(len(metric_keys)))
        p1[NAMES[int(np.argmin(norm @ w))]] += 1.0 / 2000
    summary["weight_sensitivity"] = {"metrics": metric_keys, "p_rank1": p1}
    alt_peaks = [t["_alt_cfg"]["peak"] for t in tables]
    summary["alt_cfg"] = {"mean_peak": float(np.mean(alt_peaks)),
                          "std_peak": float(np.std(alt_peaks))}
    champ = min(tables, key=lambda t: t["ESN-DL"]["score"])
    summary["champion"] = {"replicate": champ["_meta"]["replicate"],
                           "ESN-DL_score": champ["ESN-DL"]["score"],
                           "peak": champ["ESN-DL"]["peak"]}
    json.dump(summary, open(ROOT / "overnight_summary.json", "w"), indent=1)

    md = [f"# Overnight v18 statistical summary ({len(tables)} replicates)\n"]
    md.append("| controller | score | Fint | peak | errF | win-rate |")
    md.append("|---|---|---|---|---|---|")
    for n in NAMES:
        p = summary["per_controller"][n]
        md.append(f"| {n} | {p['score'][0]:.2f}±{p['score'][1]:.2f} "
                  f"| {p['Fint'][0]:.1f}±{p['Fint'][1]:.1f} "
                  f"| {p['peak'][0]:.1f}±{p['peak'][1]:.1f} "
                  f"| {p['errF_mm'][0]:.1f}±{p['errF_mm'][1]:.1f} "
                  f"| {summary['win_rates'][n]*100:.0f}% |")
    md.append("\nESN-DL beats: " + ", ".join(
        f"{k} {v*100:.0f}%" for k, v in summary["esn_beats"].items()))
    md.append("\n## P(rank #1) under 2000 random weightings")
    md.append("| " + " | ".join(NAMES) + " |")
    md.append("|" + "---|" * len(NAMES))
    md.append("| " + " | ".join(f"{p1[n]*100:.0f}%" for n in NAMES) + " |")
    md.append("\n## Per-metric best")
    for k, d in dominance.items():
        md.append(f"- **{k}**: {d['best']} ({' < '.join(d['order'])})")
    md.append(f"\nAlt config (default reservoir) cue peak: "
              f"{summary['alt_cfg']['mean_peak']:.0f}±{summary['alt_cfg']['std_peak']:.0f} N "
              f"(config sensitivity)")
    md.append(f"\nChampion: rep{summary['champion']['replicate']:03d} "
              f"(ESN-DL {summary['champion']['ESN-DL_score']:.2f}, peak {summary['champion']['peak']:.0f} N)")
    open(ROOT / "overnight_summary.md", "w").write("\n".join(md))
    print("\n".join(md))


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    start = time.time()
    deadline = start + MAX_HOURS * 3600

    def worker(wid: int) -> None:
        for rep in REPLICATES:
            if rep % WORKERS != wid:
                continue
            if time.time() > deadline:
                log(rep, "time budget reached")
                return
            try:
                run_replicate(rep)
            except Exception as exc:  # noqa: BLE001
                log(rep, f"FAILED: {exc!r}")

    import threading
    threads = [threading.Thread(target=worker, args=(w,)) for w in range(WORKERS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    aggregate()


if __name__ == "__main__":
    main()
