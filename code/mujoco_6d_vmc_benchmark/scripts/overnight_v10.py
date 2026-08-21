#!/usr/bin/env python3
"""Overnight statistical solidification (v10), ~15 h budget, 4 workers.

Why: the ESN-vs-MLP suite ranking shuffles +-1 point between DAgger refits
(a refit lottery).  One more single run cannot settle it.  This program runs
many INDEPENDENT training replicates and aggregates:

  replicate = {data noise realization, ESN fit seeds, MLP seeds}
            -> data -> train (ESN bias-fit + MLP) -> dagger x2 -> suite eval

Morning deliverables (overnight_summary.json / .md):
  1. mean +- std of every controller's suite score across replicates
  2. win rates: fraction of replicates where ESN ranks #1 / beats MLP
  3. per-metric dominance table (Fint / peak / errF / chatter / saturation)
  4. weight-sensitivity: 2000 Dirichlet-random weight draws over the
     normalized per-metric means -> P(rank #1) per controller
     (answers: is the ranking robust to the score weights, or rigged?)
  5. champion replicate (lowest ESN score) checkpoints preserved

Usage: nohup python overnight_v10.py &
"""
from __future__ import annotations

import json
import os as _os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

_os.environ.setdefault("MUJOCO_GL", "osmesa")
import lift_experiment as L
from extraction_experiment import (NeutralPolicy, UngatedESN, UngatedMLP,
                                   VMCScheduled, _fit_esn)
from direct_esn_compliance import DirectESNController

WORKERS = 4
MAX_HOURS = 14.5
REPLICATES = tuple(range(240))
ROOT = Path("/home/arm1/vmc_mujoco_runtime/outputs/overnight_v10")
LOG = Path("/tmp/overnight_v10")
ESN_SEEDS = (11, 29, 97, 123, 555)
METRICS = ("Fint", "peak", "errF_mm", "contact_s", "chatter", "saturation_s", "score")


def log(rep: int, msg: str) -> None:
    stamp = time.strftime("%H:%M:%S")
    print(f"[w{rep % WORKERS} {stamp}] {msg}", flush=True)


def load_episodes(path: Path):
    with np.load(path, allow_pickle=True) as archive:
        raw = list(archive["episodes"])
    return [dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"])
            for ep in raw]


def run_replicate(rep: int) -> None:
    out = ROOT / f"rep{rep:02d}"
    done_flag = out / "result.json"
    if done_flag.exists():
        log(rep, "already done, skip")
        return
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    data_seed = 1000 + rep * 37

    # 1) data: fresh noise realization
    cfg = json.load(open(L.OUT / "teacher_cfg.json"))
    teacher = L.LiftTeacher(y_yield=cfg["y_yield"], pre_t=cfg["pre_t"])
    episodes = []
    for entry in L.DATA_GRID:
        env = L.build_env(*entry, seed=data_seed, noise=L.DATA_NOISE)
        m, ep = L.rollout(env, data_seed, teacher=teacher, collect=True)
        env.close()
        episodes.append(dict(obs=list(ep["obs"]), actions=ep["actions"],
                             weights=ep["weights"]))
    np.savez_compressed(out / "teacher_data.npz",
                        episodes=np.asarray(episodes, dtype=object))
    log(rep, f"data done ({len(episodes)} eps, {time.time()-t0:.0f}s)")

    # 2) ESN fit (bias-fit is on via lift_experiment import) + MLP subprocess
    best_cfg = json.load(open(L.OUT / "esn_selected_cfg.json"))
    for seed in ESN_SEEDS:
        model, mse = _fit_esn(episodes, seed, best_cfg)
        model.save_npz(out / f"esn_s{seed}.npz")
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                       capture_output=True, text=True,
                       env={**_os.environ, "EXT_OUT": str(out), "MLP_HIDDEN": "256",
                            "MLP_EPOCHS": "15000"})
    if r.returncode != 0:
        raise RuntimeError(f"mlp subprocess failed: {r.stderr[-500:]}")
    log(rep, f"students fitted ({time.time()-t0:.0f}s)")

    def students():
        esn = L.EnsemblePolicy([UngatedESN(DirectESNController.from_npz(p))
                                for p in sorted(out.glob("esn_s*.npz"))])
        from mlp_compliance_baseline import MLPComplianceController
        mlp = L.EnsemblePolicy([UngatedMLP(MLPComplianceController.from_npz(p))
                                for p in sorted(out.glob("mlp_s*.npz"))])
        return esn, mlp

    # 3) dagger x3 (relabel student-visited states, refit into out/)
    for rnd in (1, 2, 3):
        esn, _ = students()
        new_eps = []
        for entry in L.DATA_GRID + L.HELDOUT:
            env = L.build_env(*entry, seed=data_seed + rnd, noise=L.DATA_NOISE)
            m, ep = L.rollout(env, data_seed + rnd, policy=esn, teacher=teacher, collect=True)
            env.close()
            new_eps.append(dict(obs=list(ep["obs"]), actions=ep["actions"],
                                weights=ep["weights"]))
        episodes = episodes + new_eps
        for seed in ESN_SEEDS:
            model, mse = _fit_esn(episodes, seed, best_cfg)
            model.save_npz(out / f"esn_s{seed}.npz")
        r = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                           capture_output=True, text=True,
                           env={**_os.environ, "EXT_OUT": str(out), "MLP_HIDDEN": "256",
                                "MLP_EPOCHS": "15000"})
        if r.returncode != 0:
            raise RuntimeError(f"mlp dagger refit failed: {r.stderr[-500:]}")
        log(rep, f"dagger round {rnd} done ({time.time()-t0:.0f}s)")

    # 4) extra ESN seeds -> ESN10 ensemble variant (does bigger help?)
    for seed in (2024, 31337, 777, 42, 8):
        model, mse = _fit_esn(episodes, seed, best_cfg)
        model.save_npz(out / f"esn_s{seed}.npz")
    esn, mlp = students()
    esn10 = L.EnsemblePolicy([UngatedESN(DirectESNController.from_npz(p))
                              for p in sorted(out.glob("esn_s*.npz"))])
    controllers = [("FW", NeutralPolicy()),
                   ("VMC", L._tuned_vmc()),
                   ("MLP", mlp),
                   ("ESN", esn),
                   ("ESN10", esn10)]
    results = {name: [] for name, _ in controllers}
    for entry in L.EVAL_BOARDS:
        for name, policy in controllers:
            env = L.build_env(*entry, seed=7)
            m = L.rollout(env, 7, policy)
            env.close()
            results[name].append(m)
    table = {}
    for name, ms in results.items():
        table[name] = {k: float(np.mean([m[k] for m in ms])) for k in METRICS}
        table[name]["completed"] = float(np.mean([m["completed"] for m in ms]))
    table["_meta"] = {"replicate": rep, "data_seed": data_seed,
                      "elapsed_s": round(time.time() - t0, 1)}
    json.dump(table, open(done_flag, "w"), indent=1)
    log(rep, f"DONE ESN={table['ESN']['score']:.2f} ESN10={table['ESN10']['score']:.2f} "
             f"MLP={table['MLP']['score']:.2f} ({time.time()-t0:.0f}s total)")


def aggregate() -> None:
    reps = sorted(ROOT.glob("rep*/result.json"))
    if not reps:
        print("no replicates finished")
        return
    all_tables = [json.load(open(p)) for p in reps]
    names = ("FW", "VMC", "MLP", "ESN", "ESN10")
    summary: dict = {"n_replicates": len(all_tables), "per_controller": {}, "win_rates": {}}

    # 1) mean +- std across replicates
    for name in names:
        per = {k: [t[name][k] for t in all_tables] for k in METRICS}
        summary["per_controller"][name] = {
            k: [float(np.mean(v)), float(np.std(v))] for k, v in per.items()}

    # 2) win rates
    wins = {n: 0 for n in names}
    esn_beats_mlp = 0
    for t in all_tables:
        best = min(names, key=lambda n: t[n]["score"])
        wins[best] += 1
        esn_beats_mlp += int(t["ESN"]["score"] < t["MLP"]["score"])
    summary["win_rates"] = {n: wins[n] / len(all_tables) for n in names}
    summary["esn_beats_mlp_rate"] = esn_beats_mlp / len(all_tables)
    esn10_beats = sum(int(t["ESN10"]["score"] < t["MLP"]["score"]) for t in all_tables)
    summary["esn10_beats_mlp_rate"] = esn10_beats / len(all_tables)

    # 3) per-metric dominance (lower = better for all listed)
    dominance = {}
    for k in METRICS:
        if k == "score":
            continue
        best = min(names, key=lambda n: summary["per_controller"][n][k][0])
        order = sorted(names, key=lambda n: summary["per_controller"][n][k][0])
        dominance[k] = {"best": best, "order": order}
    summary["dominance"] = dominance

    # 4) weight sensitivity: 2000 Dirichlet draws over normalized metrics.
    #    Answers the user's exact question: how much does MY choice of
    #    score weights decide the champion?
    metric_keys = ["Fint", "peak", "errF_mm", "contact_s", "chatter", "saturation_s"]
    means = {n: np.array([summary["per_controller"][n][k][0] for k in metric_keys])
             for n in names}
    # min-max normalize each metric across controllers to [0,1]
    mat = np.stack([means[n] for n in names])            # (4, M)
    norm = (mat - mat.min(axis=0)) / (mat.max(axis=0) - mat.min(axis=0) + 1e-12)
    rng = np.random.default_rng(7)
    win_frac = {n: 0.0 for n in names}
    draws = 2000
    for _ in range(draws):
        w = rng.dirichlet(np.ones(len(metric_keys)))
        composite = norm @ w
        win_frac[names[int(np.argmin(composite))]] += 1.0 / draws
    summary["weight_sensitivity"] = {"metrics": metric_keys,
                                     "p_rank1": win_frac}

    # 5) champion replicate (lowest ESN suite score)
    champ = min(all_tables, key=lambda t: t["ESN"]["score"])
    summary["champion"] = {"replicate": champ["_meta"]["replicate"],
                           "ESN_score": champ["ESN"]["score"],
                           "MLP_score": champ["MLP"]["score"]}
    json.dump(summary, open(ROOT / "overnight_summary.json", "w"), indent=1)

    md = [f"# Overnight v10 statistical summary ({len(all_tables)} replicates)\n"]
    md.append("| controller | score | Fint | peak | errF | win-rate |")
    md.append("|---|---|---|---|---|---|")
    for n in names:
        p = summary["per_controller"][n]
        md.append(f"| {n} | {p['score'][0]:.2f}±{p['score'][1]:.2f} "
                  f"| {p['Fint'][0]:.1f}±{p['Fint'][1]:.1f} "
                  f"| {p['peak'][0]:.1f}±{p['peak'][1]:.1f} "
                  f"| {p['errF_mm'][0]:.1f}±{p['errF_mm'][1]:.1f} "
                  f"| {summary['win_rates'][n]*100:.0f}% |")
    md.append(f"\nESN beats MLP in **{summary['esn_beats_mlp_rate']*100:.0f}%** of replicates. "
              f"ESN10 beats MLP in **{summary['esn10_beats_mlp_rate']*100:.0f}%**.")
    md.append("\n## P(rank #1) under 2000 random score weightings")
    md.append("| " + " | ".join(names) + " |")
    md.append("|" + "---|" * len(names))
    md.append("| " + " | ".join(f"{summary['weight_sensitivity']['p_rank1'][n]*100:.0f}%"
                                for n in names) + " |")
    md.append("\n## Per-metric best controller")
    for k, d in dominance.items():
        md.append(f"- **{k}**: {d['best']} ({' < '.join(d['order'])})")
    md.append(f"\nChampion replicate: rep{summary['champion']['replicate']:02d} "
              f"(ESN {summary['champion']['ESN_score']:.2f} vs MLP {summary['champion']['MLP_score']:.2f})")
    open(ROOT / "overnight_summary.md", "w").write("\n".join(md))
    print("\n".join(md))


def main() -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    ROOT.mkdir(parents=True, exist_ok=True)
    start = time.time()
    deadline = start + MAX_HOURS * 3600

    def worker(wid: int) -> None:
        for rep in REPLICATES:
            if rep % WORKERS != wid:
                continue
            if time.time() > deadline:
                log(rep, "time budget reached, stopping")
                return
            try:
                run_replicate(rep)
            except Exception as exc:  # noqa: BLE001 - a failed replicate must not kill the night
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
