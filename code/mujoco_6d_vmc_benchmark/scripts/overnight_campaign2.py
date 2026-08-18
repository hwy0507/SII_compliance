"""Overnight campaign part 2: chained after part 1 finishes.

Phases:
  G. Oracle-DAgger: counterfactual DAgger starting FROM the oracle-BC student
     (the teacher here is the oracle itself, not the reference policy -- if
     the earlier collapse came from the teacher, oracle-started DAgger should
     stay healthy and might exceed plain oracle BC).
  F. Big-reservoir oracle BC on the h24 labels (N 400/1000 x 8 seeds).
  D. Smoothness extension for oracle students (lambda 50/200, all horizons).
  E. Oracle label-density variant (nonzero repeat 16, h24 only).
  I. Readout ensemble of the v3 bidirectional 8 seeds (average readout).
  H. Final generalization matrix (multi-cycle + geometry OOD + weak +x) for
     the best oracle model and the v3 ensemble.
Results under outputs/direct_esn_fixture23_coverage_20260817/overnight2/.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts")

OUT = Path("/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817")
ROOT = OUT / "overnight"
ROOT2 = OUT / "overnight2"
MEN = "/home/arm1/vmc_mujoco_runtime/mujoco_menagerie"
SCRIPTS = "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts"
SEEDS = [13, 42, 71, 137, 251, 307, 512, 1009]
ROOT2.mkdir(parents=True, exist_ok=True)


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def wait_for_part1(timeout_s=8 * 3600):
    log("waiting for overnight part 1 ...")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        log_path = ROOT / "campaign.log"
        if log_path.exists() and "overnight campaign complete" in log_path.read_text():
            log("part 1 complete, starting part 2")
            return True
        time.sleep(60)
    log("part 1 timeout; starting anyway")
    return False


def bc_fit(traces, no_rod, out_model, seed, size=160, lam=0.0):
    if out_model.exists():
        return
    out_model.parent.mkdir(parents=True, exist_ok=True)
    with (out_model.parent / (out_model.stem + ".log")).open("w") as f:
        subprocess.run(
            [sys.executable, "bootstrap_direct_esn_multifixture.py",
             "--expert-traces", *traces, "--no-rod-expert-trace", no_rod,
             "--output-model", str(out_model), "--output-summary",
             str(out_model.parent / (out_model.stem + ".json")),
             "--reservoir-seed", str(seed), "--reservoir-size", str(size),
             "--washout-steps", "3", "--rod-repeat", "4", "--neutral-repeat", "4",
             "--smoothness-weight", str(lam)],
            stdout=f, stderr=subprocess.STDOUT, check=True, cwd=SCRIPTS)


def eval_fx(model, fx, ev_dir):
    marker = ev_dir / "post_contact_benchmark.json"
    if not marker.exists():
        ev_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "evaluate_direct_esn_post_contact.py", "--controller", str(model),
             "--menagerie", MEN, "--fixture-index", str(fx), "--output-dir", str(ev_dir)],
            check=True, capture_output=True, cwd=SCRIPTS)
    d = json.loads(marker.read_text())
    fw, es = d["fixed_wbc"], d["direct_esn"]
    return (bool(es["task_success"]),
            es["post_contact_rmse_mm"] - fw["post_contact_rmse_mm"])


def no_rod_yield(model, tag):
    nr_npz = ROOT2 / f"{tag}_nr.npz"
    if not nr_npz.exists():
        subprocess.run(
            [sys.executable, "run_direct_esn_mujoco.py", "--controller", str(model),
             "--menagerie", MEN, "--fixture-index", "0", "--no-rod",
             "--output-summary", str(ROOT2 / f"{tag}_nr.json"),
             "--output-trace", str(nr_npz)], check=True, capture_output=True, cwd=SCRIPTS)
    with np.load(nr_npz) as tr:
        return float(np.mean(np.linalg.norm(tr["yielding_twist"], axis=1)))


def phase_f_d():
    h24 = ROOT / "oracle_h24"
    traces = sorted(str(p) for p in h24.glob("tr_*.npz"))
    if not traces:
        log("phase F/D skipped: no h24 labels")
        return
    no_rod = str(OUT / "expert_traces" / "ref_no_rod.npz")
    jobs = [(size, 0.0) for size in (400, 1000)] + [(160, 50.0), (160, 200.0)]
    for size, lam in jobs:
        cell = ROOT2 / f"oracle_h24_N{size}_lam{lam:.0f}"
        for seed in SEEDS:
            bc_fit(traces, no_rod, cell / f"bc_{seed}.npz", seed, size=size, lam=lam)
        per3, ok = [], 0
        for seed in SEEDS:
            model = cell / f"bc_{seed}.npz"
            s, d = eval_fx(model, 3, cell / f"s{seed}_fx3")
            ok += int(s)
            per3.append(d)
        log(f"F/D N{size} lam{lam:.0f}: fx3 succ {ok}/8 d={np.mean(per3):+.3f}±{np.std(per3, ddof=1):.3f}"
            f" no_rod={no_rod_yield(cell / 'bc_251.npz', cell.name):.5f}")


def phase_g():
    h24 = ROOT / "oracle_h24"
    start = h24 / "lam_0" / "bc_251.npz"
    if not start.exists():
        log("phase G skipped: oracle BC missing")
        return
    for iterations in (6, 12):
        out = ROOT2 / f"oracle_dagger_x{iterations}"
        out.mkdir(parents=True, exist_ok=True)
        if not (out / "dagger_summary.json").exists():
            with (out / "train.log").open("w") as f:
                subprocess.run(
                    [sys.executable, "run_direct_esn_dagger.py", "--initial-model", str(start),
                     "--menagerie", MEN,
                     "--base-rod-trace", "/home/arm1/vmc_mujoco_runtime/rod_teacher_trace_v3.npz",
                     "--base-no-rod-trace", "/home/arm1/vmc_mujoco_runtime/no_rod_fixed_wbc_teacher_v2.npz",
                     "--output-dir", str(out), "--iterations", str(iterations),
                     "--fixture-indices", "0,1,2", "--teacher-mode", "counterfactual",
                     "--counterfactual-horizon-steps", "24",
                     "--counterfactual-zero-repeat", "1", "--counterfactual-nonzero-repeat", "8",
                     "--counterfactual-label-dilation-steps", "0",
                     "--prior-readout-weight", "100"],
                    stdout=f, stderr=subprocess.STDOUT, check=True, cwd=SCRIPTS)
        rows = []
        for it in range(1, iterations + 1):
            model = out / f"direct_esn_dagger_iteration_{it:02d}.npz"
            s, d = eval_fx(model, 3, out / f"eval_fx3_it{it:02d}")
            rows.append({"iter": it, "succ": s, "d": round(d, 3)})
        (out / "iteration_scan.json").write_text(json.dumps(rows, indent=2) + "\n")
        log(f"oracle-DAgger x{iterations}:", [(r["iter"], r["d"]) for r in rows])


def phase_i():
    # readout ensemble of the v3 bidirectional seeds
    from direct_esn_compliance import DirectESNController
    out = ROOT2 / "v3_ensemble.npz"
    if not out.exists():
        base = None
        readouts = []
        for seed in SEEDS:
            ctrl = DirectESNController.from_npz(
                OUT / "coverage_v3_directional" / "lam_0" / f"bc_{seed}.npz")
            base = ctrl
            readouts.append(ctrl.readout_copy())
        base.set_readout(np.mean(readouts, axis=0))
        base.save_npz(out)
    ds = [eval_fx(out, fx, ROOT2 / f"ens_fx{fx}")[1] for fx in range(4)]
    log(f"v3 readout ensemble: fx0-3 d = {[round(x, 3) for x in ds]} "
        f"no_rod={no_rod_yield(out, 'v3_ens'):.5f}")
    return out


def phase_h(ensemble_model):
    """Generalization matrix: multi-cycle + geometry OOD + weak +x side."""
    candidates = {
        "v3_lambda0_seed251": OUT / "coverage_v3_directional" / "lam_0" / "bc_251.npz",
        "v3_ensemble": ensemble_model,
    }
    h24 = ROOT / "oracle_h24" / "lam_0" / "bc_251.npz"
    if h24.exists():
        candidates["oracle_h24_seed251"] = h24
    for name, model in candidates.items():
        # multi-cycle
        for period in (0.80, 1.00):
            trace = ROOT2 / f"{name}_mc_p{period:.2f}.npz"
            if not trace.exists():
                subprocess.run(
                    [sys.executable, "run_direct_esn_mujoco.py", "--controller", str(model),
                     "--menagerie", MEN, "--fixture-index", "2", "--rod-cycles", "2",
                     "--cycle-period-s", str(period), "--output-summary",
                     str(ROOT2 / f"{name}_mc_p{period:.2f}.json"), "--output-trace", str(trace)],
                    check=True, capture_output=True, cwd=SCRIPTS)
            info = json.loads((ROOT2 / f"{name}_mc_p{period:.2f}.json").read_text())
            with np.load(trace) as tr:
                ci = np.flatnonzero(tr["contact_force"] > 0.2)
                w = (tr["time_s"] >= tr["time_s"][ci[0]]) & (tr["time_s"] < 2.4)
                dev = np.linalg.norm(tr["ee_position"] - tr["nominal_position"], axis=1)
            log(f"H {name} mc p{period}: succ={info['task_success']} "
                f"rmse={1000 * np.sqrt(np.mean(dev[w] ** 2)):.2f}")
        # geometry OOD + weak +x
        for tag, args in {
            "ood_late1130": ["--rod-stroke-m", "0.172", "--rod-height-m", "0.541",
                             "--rod-start-time-s", "1.130"],
            "ood_high545": ["--rod-stroke-m", "0.172", "--rod-height-m", "0.545",
                            "--rod-start-time-s", "1.085"],
            "side_posx": ["--rod-approach-side", "positive_x"],
        }.items():
            s, d = eval_side(model, args, ROOT2 / f"{name}_{tag}")
            log(f"H {name} {tag}: succ={s} d={d:+.3f}")


def eval_side(model, extra, ev_dir):
    marker = ev_dir / "post_contact_benchmark.json"
    if not marker.exists():
        ev_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "evaluate_direct_esn_post_contact.py", "--controller", str(model),
             "--menagerie", MEN, "--fixture-index", "2", "--output-dir", str(ev_dir), *extra],
            check=True, capture_output=True, cwd=SCRIPTS)
    d = json.loads(marker.read_text())
    fw, es = d["fixed_wbc"], d["direct_esn"]
    return bool(es["task_success"]), es["post_contact_rmse_mm"] - fw["post_contact_rmse_mm"]


if __name__ == "__main__":
    wait_for_part1()
    log("overnight part 2 start")
    for name, fn in (("F/D", phase_f_d), ("G", phase_g), ("I", phase_i)):
        try:
            log(f"phase {name} begin")
            fn()
        except Exception as exc:
            log(f"PHASE {name} FAILED:", repr(exc))
    try:
        log("phase H begin")
        phase_i_model = ROOT2 / "v3_ensemble.npz"
        phase_h(phase_i_model)
    except Exception as exc:
        log("PHASE H FAILED:", repr(exc))
    log("overnight part 2 complete")
