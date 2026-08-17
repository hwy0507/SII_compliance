"""Overnight campaign: counterfactual-oracle distillation + DAgger forensics.

Phases (checkpointed; safe to rerun):
  C. Counterfactual-oracle direct distillation (bypass the teacher ceiling):
     label the 435-trace pool states with the counterfactual oracle under
     three horizons, behavior-clone the oracle labels (8 seeds x lambda),
     and evaluate on the full matrix.  Labels come from the privileged
     oracle, not from the teacher policy, so the student ceiling is the
     oracle's, not the teacher's (-2.40).
  A. DAgger forensics (why does teacher-start DAgger collapse?):
     A1: bootstrap-start (weak student) 12-iteration DAgger x 3 seeds,
         evaluate held-out every 3 iterations.
     A3: same with halved nonzero label repeat (archive-noise hypothesis).
  B. Pool-BC start + 6-iteration DAgger (strong data + mild DAgger).
Everything lands under outputs/direct_esn_fixture23_coverage_20260817/overnight/.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts")

OUT = Path("/home/arm1/vmc_mujoco_runtime/outputs/direct_esn_fixture23_coverage_20260817")
POOL = OUT / "expert_traces_pool"
ROOT = OUT / "overnight"
MEN = "/home/arm1/vmc_mujoco_runtime/mujoco_menagerie"
SCRIPTS = "/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts"
TEACHER = OUT.parent / "direct_esn_formal_multifixture_dagger_20260817/seed_20260907/direct_esn_dagger_iteration_03.npz"
SEEDS = [13, 42, 71, 137, 251, 307, 512, 1009]
HORIZONS = (24, 12, 48)
ROOT.mkdir(parents=True, exist_ok=True)

manifest = json.loads((POOL / "manifest.json").read_text())
usable = [m for m in manifest["traces"] if m["task_success"]]
print(f"[boot] pool usable: {len(usable)}", flush=True)


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


# ---------------------------------------------------------------- Phase C
def phase_c():
    from counterfactual_direct_esn_teacher import CounterfactualTeacherConfig
    from run_direct_esn_dagger import collect_student_visited_archive
    from wbc_velocity_residual_env import VelocityResidualFixture

    for horizon in HORIZONS:
        hdir = ROOT / f"oracle_h{horizon}"
        hdir.mkdir(parents=True, exist_ok=True)
        done_flag = hdir / "labels_done.json"
        if not done_flag.exists():
            config = CounterfactualTeacherConfig(horizon_steps=horizon)
            labeled = 0
            t0 = time.time()
            for index, m in enumerate(usable):
                archive = hdir / f"arc_{index:03d}.npz"
                if not archive.exists():
                    fixture = VelocityResidualFixture(
                        m["stroke"], m["height"], m["start"],
                        rod_approach_side=m["side"])
                    collect_student_visited_archive(
                        Path(TEACHER), menagerie=Path(MEN), fixture_index=0,
                        rod_enabled=True, seed=20260817, output_path=archive,
                        iteration=0, teacher_mode="counterfactual",
                        counterfactual_config=config, fixtures=(fixture,))
                labeled += 1
                if (index + 1) % 50 == 0:
                    log(f"oracle h{horizon}: {index + 1}/{len(usable)} labeled "
                        f"({(time.time() - t0) / (index + 1):.1f}s/ep)")
            # convert archives to expert-trace format (bounded_action = oracle label)
            for index in range(len(usable)):
                trace = hdir / f"tr_{index:03d}.npz"
                if trace.exists():
                    continue
                with np.load(hdir / f"arc_{index:03d}.npz") as arc:
                    np.savez_compressed(
                        trace,
                        joint_position=arc["joint_position"],
                        joint_velocity=arc["joint_velocity"],
                        wbc_task_twist=arc["wbc_task_twist"],
                        pose_error=arc["pose_error"],
                        wbc_twist_error=arc["wbc_twist_error"],
                        bounded_action=np.clip(arc["counterfactual_teacher_action"], -1.0, 1.0),
                    )
            done_flag.write_text(json.dumps({"episodes": len(usable)}) + "\n")
            log(f"oracle h{horizon}: labeling done")
        # BC on oracle labels
        traces = sorted(str(p) for p in hdir.glob("tr_*.npz"))
        no_rod = str(OUT / "expert_traces" / "ref_no_rod.npz")
        for lam in (0.0, 100.0):
            cell = hdir / f"lam_{lam:.0f}"
            for seed in SEEDS:
                model = cell / f"bc_{seed}.npz"
                if model.exists():
                    continue
                cell.mkdir(parents=True, exist_ok=True)
                with (cell / f"bc_{seed}.log").open("w") as f:
                    subprocess.run(
                        [sys.executable, "bootstrap_direct_esn_multifixture.py",
                         "--expert-traces", *traces, "--no-rod-expert-trace", no_rod,
                         "--output-model", str(model), "--output-summary",
                         str(cell / f"bc_{seed}.json"), "--reservoir-seed", str(seed),
                         "--washout-steps", "3", "--rod-repeat", "4", "--neutral-repeat", "4",
                         "--smoothness-weight", str(lam)],
                        stdout=f, stderr=subprocess.STDOUT, check=True, cwd=SCRIPTS)
        log(f"oracle h{horizon}: BC done")
        # evaluation
        summary_rows = []
        for lam in (0.0, 100.0):
            cell = hdir / f"lam_{lam:.0f}"
            per, mirror, ok = {fx: [] for fx in range(4)}, [], 0
            for seed in SEEDS:
                model = cell / f"bc_{seed}.npz"
                good = True
                for fx in range(4):
                    ev = cell / f"s{seed}_fx{fx}"
                    marker = ev / "post_contact_benchmark.json"
                    if not marker.exists():
                        ev.mkdir(parents=True, exist_ok=True)
                        subprocess.run(
                            [sys.executable, "evaluate_direct_esn_post_contact.py",
                             "--controller", str(model), "--menagerie", MEN,
                             "--fixture-index", str(fx), "--output-dir", str(ev)],
                            check=True, capture_output=True, cwd=SCRIPTS)
                    d = json.loads(marker.read_text())
                    fw, es = d["fixed_wbc"], d["direct_esn"]
                    good &= bool(es["task_success"])
                    per[fx].append(es["post_contact_rmse_mm"] - fw["post_contact_rmse_mm"])
                nr_npz = cell / f"s{seed}_nr.npz"
                if not nr_npz.exists():
                    subprocess.run(
                        [sys.executable, "run_direct_esn_mujoco.py", "--controller", str(model),
                         "--menagerie", MEN, "--fixture-index", "0", "--no-rod",
                         "--output-summary", str(cell / f"s{seed}_nr.json"),
                         "--output-trace", str(nr_npz)], check=True, capture_output=True, cwd=SCRIPTS)
                with np.load(nr_npz) as tr:
                    my = float(np.mean(np.linalg.norm(tr["yielding_twist"], axis=1)))
                good &= my < 0.005
                mtrace = cell / f"s{seed}_mirror.npz"
                if not mtrace.exists():
                    subprocess.run(
                        [sys.executable, "run_direct_esn_mujoco.py", "--controller", str(model),
                         "--menagerie", MEN, "--fixture-index", "2", "--rod-approach-side", "positive_y",
                         "--rod-stroke-m", "0.175", "--rod-height-m", "0.542",
                         "--rod-start-time-s", "1.100", "--output-summary",
                         str(cell / f"s{seed}_mirror.json"), "--output-trace", str(mtrace)],
                        check=True, capture_output=True, cwd=SCRIPTS)
                minfo = json.loads((cell / f"s{seed}_mirror.json").read_text())
                with np.load(mtrace) as tr:
                    ci = np.flatnonzero(tr["contact_force"] > 0.2)
                    w = (tr["time_s"] >= tr["time_s"][ci[0]]) & (tr["time_s"] < 2.4)
                    dev = np.linalg.norm(tr["ee_position"] - tr["nominal_position"], axis=1)
                good &= bool(minfo["task_success"])
                mirror.append(float(1000 * np.sqrt(np.mean(dev[w] ** 2))))
                ok += int(good)
            row = {"horizon": horizon, "lam": lam, "gate": f"{ok}/8",
                   "fx_d": [round(float(np.mean(per[fx])), 3) for fx in range(4)],
                   "mirror": round(float(np.mean(mirror)), 2),
                   "mirror_std": round(float(np.std(mirror, ddof=1)), 2)}
            summary_rows.append(row)
            log(f"oracle h{horizon} lam={lam}: gate={row['gate']} "
                f"fx3={row['fx_d'][3]:+.3f} mirror={row['mirror']}")
        (hdir / "oracle_eval.json").write_text(json.dumps(summary_rows, indent=2) + "\n")


# ---------------------------------------------------------------- Phase A/B
def dagger_run(tag, initial, iterations, fixtures, nonzero_repeat):
    out = ROOT / tag
    out.mkdir(parents=True, exist_ok=True)
    marker = out / "dagger_summary.json"
    if not marker.exists():
        cmd = [sys.executable, "run_direct_esn_dagger.py", "--initial-model", str(initial),
               "--menagerie", MEN,
               "--base-rod-trace", "/home/arm1/vmc_mujoco_runtime/rod_teacher_trace_v3.npz",
               "--base-no-rod-trace", "/home/arm1/vmc_mujoco_runtime/no_rod_fixed_wbc_teacher_v2.npz",
               "--output-dir", str(out), "--iterations", str(iterations),
               "--fixture-indices", fixtures, "--teacher-mode", "counterfactual",
               "--counterfactual-horizon-steps", "24",
               "--counterfactual-zero-repeat", "1",
               "--counterfactual-nonzero-repeat", str(nonzero_repeat),
               "--counterfactual-label-dilation-steps", "0",
               "--prior-readout-weight", "100"]
        with (out / "train.log").open("w") as f:
            subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True, cwd=SCRIPTS)
    # evaluate selected iterations on held-out fx3
    rows = []
    for it in range(1, iterations + 1):
        model = out / f"direct_esn_dagger_iteration_{it:02d}.npz"
        ev = out / f"eval_fx3_it{it:02d}"
        marker2 = ev / "post_contact_benchmark.json"
        if not marker2.exists():
            ev.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [sys.executable, "evaluate_direct_esn_post_contact.py", "--controller", str(model),
                 "--menagerie", MEN, "--fixture-index", "3", "--output-dir", str(ev)],
                check=True, capture_output=True, cwd=SCRIPTS)
        d = json.loads(marker2.read_text())
        fw, es = d["fixed_wbc"], d["direct_esn"]
        rows.append({"iter": it, "succ": bool(es["task_success"]),
                     "d": round(es["post_contact_rmse_mm"] - fw["post_contact_rmse_mm"], 3)})
    (out / "iteration_scan.json").write_text(json.dumps(rows, indent=2) + "\n")
    log(tag, "iteration curve:", [(r["iter"], r["d"]) for r in rows])


def phase_a_b():
    for seed in (13, 251, 71):
        dagger_run(f"aggr_bootstrap{seed}_x12", OUT / "bootstrap" / f"bootstrap_seed_{seed}.npz",
                   12, "0,1,2", 8)
    dagger_run("aggr_halflabel_x12", OUT / "bootstrap" / "bootstrap_seed_251.npz",
               12, "0,1,2", 4)
    dagger_run("aggr_poolbc_x6", OUT / "scaling_study" / "n435_N160" / "bc_251.npz",
               6, "0,1,2", 8)


if __name__ == "__main__":
    log("overnight campaign start")
    try:
        phase_c()
    except Exception as exc:  # keep the night going even if one phase fails
        log("PHASE C FAILED:", repr(exc))
    try:
        phase_a_b()
    except Exception as exc:
        log("PHASE A/B FAILED:", repr(exc))
    log("overnight campaign complete")
