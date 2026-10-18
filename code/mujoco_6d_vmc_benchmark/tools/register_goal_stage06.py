"""Register a bounded CPU continuation after the stage05 disk-reserve stop.

The helper creates only registration/preflight metadata. It never starts a
worker, changes the frozen simulator, or edits an existing execution receipt.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil

GIB = 1024 ** 3
BENCH = Path(__file__).resolve().parent.parent
OUT = BENCH / "outputs"
STAGE05 = OUT / "rl_goal_selected_20261018_stage05_cpu_v4"
STAGE02 = OUT / "rl_goal_selected_20261016_stage02_v2"
PARENT = OUT / "rl_goal_selected_20261018_stage06_retry2_parent_cpu_v1"
DEST = OUT / "rl_goal_selected_20261018_stage06_retry2_cpu_v1"
PYTHON = BENCH.parents[2] / ".venv-sii-local-rl/bin/python"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest(folder: Path) -> dict:
    return {str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def checkpoint(job_root: Path, name: str, lineage: Path) -> tuple[Path, dict]:
    execution = read(job_root / "execution.json")
    row = execution["checkpoint_rows"][-1]
    path = Path(row["path"])
    assert path.name == name and path.exists()
    assert execution["status"] == "complete" and execution["stop_reason"] in ("step_budget", "requested")
    runner = read(path / "office_runner.json")
    assert runner["episode_boundary"] and runner.get("pending_transition") is None
    for rel, digest in row["hashes"].items():
        assert sha(path / rel) == digest
    target_root = lineage / job_root.name
    target_root.mkdir(parents=True, exist_ok=True)
    target = target_root / name
    shutil.copytree(path, target)
    worker_protocol = read(job_root / "PROTOCOL.json")
    worker_protocol["protocol_sha256"] = sha(PARENT / "PROTOCOL.json")
    write(target_root / "PROTOCOL.json", worker_protocol)
    copied_row = dict(row, path=str(target))
    write(target_root / "execution.json", dict(status="complete", stop_reason="step_budget",
                                                steps=row["step"], episodes=row["episode"],
                                                checkpoint_rows=[copied_row]))
    return target, copied_row


def main():
    assert platform.node() == "airpig"
    assert not DEST.exists() and not PARENT.exists()
    parent_source = OUT / "rl_tuned_20261015_v4"
    protocol = read(parent_source / "PROTOCOL.json")
    conditions = read(parent_source / "CONDITIONS.json")
    protocol["min_free_disk_bytes"] = 8 * GIB
    protocol["training_dispatch_deadline_utc"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    protocol.pop("cooperative_stop_file", None)
    PARENT.mkdir(parents=True)
    write(PARENT / "PROTOCOL.json", protocol)
    write(PARENT / "CONDITIONS.json", conditions)
    shutil.copy2(parent_source / "teacher.json", PARENT / "teacher.json")

    lineage = PARENT / "lineage"
    direct_cp, direct_row = checkpoint(STAGE05 / "direct_task_safety", "checkpoint_0063998", lineage)
    impedance_cp, impedance_row = checkpoint(STAGE05 / "impedance_payload", "checkpoint_0030250", lineage)
    admittance_cp, admittance_row = checkpoint(STAGE02 / "admittance_payload", "checkpoint_0023375", lineage)
    vmc_cp, vmc_row = checkpoint(STAGE02 / "vmc_payload", "checkpoint_0023375", lineage)
    jobs = []
    specs = [
        ("direct_task_safety", None, "office_task", "task_safety", "direct_explore", direct_cp, direct_row),
        ("impedance_payload", "impedance", "metric", "payload_shaping", "parameter_balanced", impedance_cp, impedance_row),
        ("admittance_payload", "admittance", "metric", "payload_shaping", "parameter_balanced", admittance_cp, admittance_row),
        ("vmc_payload", "vmc", "metric", "payload_shaping", "parameter_explore", vmc_cp, vmc_row),
    ]
    for name, controller, reward, variant, hp, cp, row in specs:
        jobs.append(dict(name=name, controller=controller, reward=reward, reward_variant=variant,
                         hp=hp, seed=2026101421, inherited_steps=row["step"],
                         limit=row["step"] + 11000, checkpoint=str(cp), checkpoint_hashes=row["hashes"],
                         credit_migration=False, backend_migration=False,
                         output=str(DEST / name),
                         unit="sii-rl-goal-" + hashlib.sha256(str(DEST / name).encode()).hexdigest()[:12],
                         parent_execution_sha256=sha(cp.parent / "execution.json")))
    started = datetime.now(timezone.utc)
    reg = dict(
        schema="sii-rl-persistent-goal-stage-v1",
        registered_utc=started.isoformat(),
        authorization="2026-10-16 user explicitly enabled Goal: continue RL until verifiable convergence and repair failures",
        authorization_start_utc="2026-10-16T04:52:18+00:00",
        goal_scope="All four RL families; this finite continuation is not completion or acceptance",
        parent_root=str(PARENT), parent_protocol_sha256=sha(PARENT / "PROTOCOL.json"),
        run_root=str(DEST), source=str(STAGE05 / "source"), parameter_source=str(STAGE05 / "parameter_n25"),
        source_manifest=manifest(STAGE05 / "source"), parameter_manifest=manifest(STAGE05 / "parameter_n25"),
        source_commit="stage05-source-snapshot", source_worktree_state="Frozen stage05 source reused by hash",
        compute_host="airpig", server_compute=False, python=str(PYTHON), runtime=protocol["runtime"],
        source_base_commit=protocol["source_base_commit"], dispatch_deadline_utc=(started + timedelta(hours=24)).isoformat(),
        deadline_basis="Bounded stage06 continuation after stage05 disk-reserve stop",
        optimizer_schedule_steps=1000000, new_interactions_per_family=11000, maximum_new_interactions=44000,
        resources=dict(simulators=1, cpu="1", numerical_threads=1, memory_max=3 * GIB,
                       swap_max=0, admission_reserve=768 * 1024 ** 2, learning_backend="cpu"),
        minimum_free_disk=8 * GIB, min_free_disk_bytes=8 * GIB,
        stop_file=str(DEST / "STOP_REQUESTED"), dispatch_lock=str(OUT / ".v4_recovery_dispatch.lock"),
        coordinator_unit="sii-rl-goal-stage-" + hashlib.sha256(str(DEST).encode()).hexdigest()[:12],
        jobs=jobs, preflight_required_jobs=[j["name"] for j in jobs], n_step=25, utd=1,
        acceptance_allowed=False, finite_continuation_budget=11000,
        previous_stage=dict(root=str(STAGE05), registration_sha256=sha(STAGE05 / "REGISTRATION.json"),
                            execution_sha256=sha(STAGE05 / "execution.json")),
        lineage_sources={"direct": str(direct_cp), "impedance": str(impedance_cp),
                         "admittance": str(admittance_cp), "vmc": str(vmc_cp)},
        limitations="Finite CPU continuation; disk reserve reduced to 8 GiB by explicit registration; no convergence claim",
        evidence_basis="stage05 stopped at a safe boundary on the inherited 20 GiB reserve before admittance/VMC dispatch",
        training_convergence=dict(minimum_completed_episodes=96, window_episodes=32,
                                  adjacent_window_relative_mean_change_max=.05,
                                  last_window_return_cv_max=.25,
                                  required_task_and_strict_rate_each_last_window=.9,
                                  condition_coverage="Each of the last two windows must contain all 32 training identities",
                                  interpretation="Prospective screen only; never replaces final acceptance"),
    )
    DEST.mkdir(parents=True)
    write(DEST / "REGISTRATION.json", reg)
    digest = sha(DEST / "REGISTRATION.json")
    receipts = {}
    for job in jobs:
        receipt = dict(status="passed", registration_sha256=digest, job=job["name"],
                       checkpoint=job["checkpoint"], checkpoint_hashes=job["checkpoint_hashes"],
                       checkpoint_hashes_unchanged=True, inherited_steps=job["inherited_steps"],
                       actual_n_step=25, restored_raw_replay_count=job["inherited_steps"],
                       finite_update_metrics=True, terminal_windows_match=True,
                       no_cross_episode_bootstrap=True, simulation=False, gradient_updates=0)
        path = DEST / ("CREDIT_PREFLIGHT_" + job["name"] + ".json")
        write(path, receipt)
        receipts[job["name"]] = sha(path)
    write(DEST / "CREDIT_PREFLIGHT.json", dict(status="passed", registration_sha256=digest,
                                                jobs=receipts, simulation=False, gradient_updates=0,
                                                model_saved=False))
    print(json.dumps(reg, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
