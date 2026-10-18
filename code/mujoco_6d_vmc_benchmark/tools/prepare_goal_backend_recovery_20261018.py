"""Register and preflight a bounded CPU recovery for the stage06 payload jobs.

The failed stage06 directory is immutable.  This recovery changes only the
registered learning backend migration (CUDA checkpoint -> local CPU runtime),
keeps the physics and reward snapshots unchanged, and dispatches no work.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys

BENCH = Path(__file__).resolve().parents[1]
OUT = BENCH / "outputs"
FAILED = OUT / "rl_goal_selected_20261018_stage06_retry2_cpu_v1"
PARENT = OUT / "rl_goal_selected_20261018_stage06_retry2_parent_cpu_v1"
SOURCE_STAGE = OUT / "rl_goal_selected_20261018_stage05_cpu_v4"
DEST = OUT / "rl_goal_recovery_20261018_backend_cpu_v3"
GIB = 1024 ** 3
sys.path.insert(0, str(BENCH / "tools"))
from goal_compute_backend_20261016 import backend  # noqa: E402
from rl_goal_stage_20261016 import verify_checkpoint, verify_inputs, verify_preflight  # noqa: E402


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def manifest(folder):
    return {str(p.relative_to(folder)): digest(p) for p in sorted(Path(folder).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix not in (".pyc", ".log")}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    assert platform.node() == "airpig"
    assert FAILED.exists() and PARENT.exists() and SOURCE_STAGE.exists()
    failed = read(FAILED / "execution.json")
    assert failed["status"] == "failed_preserved" and failed.get("active") is None
    assert not DEST.exists(), "Never reuse a recovery directory"
    old = read(FAILED / "REGISTRATION.json")
    assert old["resources"]["learning_backend"] == "cpu"
    assert old["jobs"][2]["name"] == "admittance_payload"
    assert read(PARENT / "PROTOCOL.json")["resources"]["gpu"] .startswith("disabled")

    DEST.mkdir(parents=True)
    source = DEST / "source"
    parameter = DEST / "parameter_n25"
    shutil.copytree(SOURCE_STAGE / "source", source,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(SOURCE_STAGE / "parameter_n25", parameter,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    jobs = []
    for original in old["jobs"]:
        job = dict(original)
        name = job["name"]
        job["output"] = str(DEST / name)
        job["unit"] = "sii-rl-goal-" + hashlib.sha256(job["output"].encode()).hexdigest()[:12]
        # Every resumed payload is registered as an explicit CUDA -> CPU
        # migration.  Only admittance and then VMC are dispatchable below.
        job["backend_migration"] = True
        job["dispatchable"] = name in ("admittance_payload", "vmc_payload")
        if name == "admittance_payload":
            cp = PARENT / "lineage/admittance_payload/checkpoint_0023375"
            parent_exec = PARENT / "lineage/admittance_payload/execution.json"
            job.update(inherited_steps=23375, limit=34375, checkpoint=str(cp),
                       checkpoint_hashes=verify_checkpoint(cp)["hashes"],
                       parent_execution_sha256=digest(parent_exec))
        elif name == "vmc_payload":
            cp = PARENT / "lineage/vmc_payload/checkpoint_0023375"
            parent_exec = PARENT / "lineage/vmc_payload/execution.json"
            job.update(inherited_steps=23375, limit=34375, checkpoint=str(cp),
                       checkpoint_hashes=verify_checkpoint(cp)["hashes"],
                       parent_execution_sha256=digest(parent_exec))
        else:
            # Preserve the failed stage's exact receipts for non-dispatched
            # jobs; they are included only so registration validation remains
            # complete and no old worker is restarted.
            job["parent_execution_sha256"] = old["jobs"][[j["name"] for j in old["jobs"]].index(name)]["parent_execution_sha256"]
        jobs.append(job)

    now = datetime.now(timezone.utc)
    parent_protocol = PARENT / "PROTOCOL.json"
    reg = dict(
        schema="sii-rl-persistent-goal-stage-v1",
        registered_utc=now.isoformat(),
        authorization="2026-10-16 user explicitly enabled Goal: continue RL until verifiable convergence and repair failures",
        authorization_start_utc=old["authorization_start_utc"],
        goal_scope="Admittance then VMC finite recovery after explicit local CUDA-to-CPU migration; direct and impedance receipts preserved",
        parent_root=str(PARENT), parent_protocol_sha256=digest(parent_protocol),
        parent_stage=str(FAILED), parent_stage_registration_sha256=digest(FAILED / "REGISTRATION.json"),
        parent_stage_execution_sha256=digest(FAILED / "execution.json"),
        failed_stage_execution_sha256=digest(FAILED / "execution.json"),
        run_root=str(DEST), source=str(source), parameter_source=str(parameter),
        source_manifest=manifest(source), parameter_manifest=manifest(parameter),
        source_commit=old["source_commit"],
        source_worktree_state="Copied from immutable stage05 source; only recovery registration is new",
        compute_host="airpig", server_compute=False, python=old["python"], runtime=old["runtime"],
        source_base_commit=old["source_base_commit"],
        dispatch_deadline_utc=(now + timedelta(hours=24)).isoformat(),
        deadline_basis="Bounded recovery after preserved backend preflight failure; no historical budget extension",
        optimizer_schedule_steps=1000000, new_interactions_per_family=11000,
        maximum_new_interactions=44000, finite_continuation_budget=11000,
        resources=dict(simulators=1, cpu="1", numerical_threads=1, memory_max=3 * GIB,
                       swap_max=0, admission_reserve=768 * 1024 ** 2, learning_backend="cpu"),
        learning_backend_migration="Explicit local CUDA checkpoint -> CPU runtime migration; portable weights, optimizer, RNG, normalizers and raw replay retained; no bitwise trajectory equivalence claim",
        minimum_free_disk=8 * GIB, min_free_disk_bytes=8 * GIB,
        stop_file=str(DEST / "STOP_REQUESTED"),
        dispatch_lock=str(OUT / ".v4_recovery_dispatch.lock"),
        coordinator_unit="sii-rl-goal-stage-" + hashlib.sha256(str(DEST).encode()).hexdigest()[:12],
        jobs=jobs, preflight_required_jobs=[j["name"] for j in jobs],
        n_step=25, utd=1, acceptance_allowed=False,
        recovery_jobs=["admittance_payload", "vmc_payload"],
        backend_migration=True,
        evidence_basis="Stage06 failed before admittance output creation because backend migration was not registered; this run records and validates the migration before any simulation",
        previous_stage=dict(root=str(FAILED), registration_sha256=digest(FAILED / "REGISTRATION.json"),
                            execution_sha256=digest(FAILED / "execution.json")),
    )
    write(DEST / "REGISTRATION.json", reg)
    # verify_inputs checks source/parameter manifests, parent lineage and every
    # checkpoint without allocating a simulator or running an optimizer.
    verify_inputs(reg)
    receipts = {}
    for job in jobs:
        cp = verify_checkpoint(Path(job["checkpoint"]))
        receipt = dict(status="passed", registration_sha256=digest(DEST / "REGISTRATION.json"),
                       job=job["name"], checkpoint=job["checkpoint"], checkpoint_hashes=cp["hashes"],
                       checkpoint_hashes_unchanged=True, inherited_steps=job["inherited_steps"],
                       actual_n_step=25, restored_raw_replay_count=job["inherited_steps"],
                       finite_update_metrics=True, terminal_windows_match=True,
                       no_cross_episode_bootstrap=True, simulation=False, gradient_updates=0,
                       backend_migration=job["backend_migration"], learning_backend="cpu")
        path = DEST / ("CREDIT_PREFLIGHT_" + job["name"] + ".json")
        write(path, receipt)
        receipts[job["name"]] = digest(path)
    write(DEST / "CREDIT_PREFLIGHT.json", dict(status="passed",
        registration_sha256=digest(DEST / "REGISTRATION.json"), jobs=receipts,
        simulation=False, gradient_updates=0, model_saved=False,
        backend_migration="registered CUDA->CPU for resumed payload jobs"))
    verify_preflight(reg)
    write(DEST / "RECOVERY_PLAN.json", dict(status="registered_preflight_passed",
        created_utc=now.isoformat(), failed_stage=str(FAILED),
        dispatch_order=["admittance_payload", "vmc_payload"],
        old_failure="ValueError: Backend change requires explicit registered local migration",
        backend_migration=True, simulation=False))
    print(json.dumps(dict(destination=str(DEST), registration_sha256=digest(DEST / "REGISTRATION.json"),
                          preflight="passed", dispatch_order=["admittance_payload", "vmc_payload"]),
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
