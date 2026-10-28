"""Register a unique recovery continuation for an interrupted admittance worker.

The original stage is intentionally left immutable.  This helper only copies the
sealed source/parameter snapshots and writes a new finite registration whose
admittance job resumes from the last verified episode-boundary checkpoint.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil

BENCH = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = BENCH / "outputs/rl_tuned_20261015_v4"
STAGE = BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1"
DEST = BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1"
GIB = 1024 ** 3


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def manifest(folder):
    return {
        str(p.relative_to(folder)): digest(p)
        for p in sorted(Path(folder).rglob("*"))
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }


def main():
    assert platform.node() == "airpig"
    assert not DEST.exists(), "Recovery directory already exists; never reuse it"
    stage_reg = read(STAGE / "REGISTRATION.json")
    protocol = read(ORIGINAL_ROOT / "PROTOCOL.json")
    assert stage_reg["parent_root"] == str(ORIGINAL_ROOT)
    assert stage_reg["parent_protocol_sha256"] == digest(ORIGINAL_ROOT / "PROTOCOL.json")
    old = read(STAGE / "admittance_payload/execution.json")
    assert old["status"] == "running"
    checkpoint = STAGE / "admittance_payload/checkpoint_0030250"
    checkpoint_row = next(row for row in old["checkpoint_rows"] if row["path"] == str(checkpoint))
    runner = read(checkpoint / "office_runner.json")
    assert checkpoint_row["step"] == runner["step"] == 30250
    assert runner["episode_boundary"] and runner["pending_transition"] is None
    assert old["stop_requested"] is False

    source = DEST / "source"
    parameter = DEST / "parameter_n25"
    shutil.copytree(STAGE / "source", source)
    shutil.copytree(STAGE / "parameter_n25", parameter)

    jobs = []
    for original in stage_reg["jobs"]:
        job = dict(original)
        job["output"] = str(DEST / original["name"])
        job["unit"] = "sii-rl-goal-" + hashlib.sha256(job["output"].encode()).hexdigest()[:12]
        job["dispatchable"] = original["name"] == "admittance_payload"
        if original["name"] == "admittance_payload":
            job.update(
                inherited_steps=30250,
                limit=41250,
                checkpoint=str(checkpoint),
                checkpoint_hashes=checkpoint_row["hashes"],
                parent_execution_sha256=digest(STAGE / "admittance_payload/execution.json"),
                recovery_from_interrupted_stage=str(STAGE),
            )
        jobs.append(job)

    now = datetime.now(timezone.utc)
    registration = dict(
        schema="sii-rl-persistent-goal-stage-v1",
        registered_utc=now.isoformat(),
        authorization="2026-10-16 user explicitly enabled Goal: keep advancing RL training to convergence and autonomously repair problems",
        authorization_start_utc=stage_reg["authorization_start_utc"],
        goal_scope="Admittance-only finite recovery from exact episode boundary; VMC remains a separate coordinator handoff",
        parent_root=str(ORIGINAL_ROOT),
        parent_protocol_sha256=digest(ORIGINAL_ROOT / "PROTOCOL.json"),
        parent_stage=str(STAGE),
        parent_stage_registration_sha256=digest(STAGE / "REGISTRATION.json"),
        parent_stage_execution_sha256=digest(STAGE / "execution.json"),
        interrupted_worker_execution_sha256=digest(STAGE / "admittance_payload/execution.json"),
        recovery_checkpoint=checkpoint_row,
        run_root=str(DEST),
        source=str(source),
        parameter_source=str(parameter),
        source_manifest=manifest(source),
        parameter_manifest=manifest(parameter),
        source_commit=stage_reg["source_commit"],
        source_worktree_state="Copied from immutable stage04 snapshot; this recovery does not modify stage04",
        compute_host="airpig",
        server_compute=False,
        python=stage_reg["python"],
        runtime=stage_reg["runtime"],
        source_base_commit=stage_reg["source_base_commit"],
        dispatch_deadline_utc=(now + timedelta(hours=24)).isoformat(),
        deadline_basis="Finite recovery budget registered after an interrupted worker; no historical budget extension",
        optimizer_schedule_steps=1000000,
        new_interactions_per_family=11000,
        maximum_new_interactions=44000,
        finite_continuation_budget=11000,
        previous_stage=dict(root=str(STAGE), registration_sha256=digest(STAGE / "REGISTRATION.json"),
                            execution_sha256=digest(STAGE / "execution.json")),
        resources=dict(simulators=1, cpu="1", numerical_threads=1, memory_max=3 * GIB,
                       swap_max=0, admission_reserve=768 * 1024 ** 2),
        minimum_free_disk=50 * GIB,
        stop_file=str(DEST / "STOP_REQUESTED"),
        dispatch_lock=str(BENCH / "outputs/.v4_recovery_dispatch.lock"),
        coordinator_unit="sii-rl-goal-stage-" + hashlib.sha256(str(DEST).encode()).hexdigest()[:12],
        jobs=jobs,
        n_step=25,
        utd=1,
        acceptance_allowed=False,
        recovery_only_job="admittance_payload",
        recovery_reason="stage04 worker exited after writing an incomplete episode; exact checkpoint_0030250 is the last valid boundary",
        evidence_basis="Preserve the interrupted stage04 receipt and replay only from its last verified episode-boundary checkpoint",
    )
    write(DEST / "REGISTRATION.json", registration)
    write(DEST / "RECOVERY_PLAN.json", dict(
        status="registered_not_launched",
        source_stage=str(STAGE),
        source_execution_sha256=digest(STAGE / "admittance_payload/execution.json"),
        checkpoint=str(checkpoint),
        checkpoint_step=30250,
        registered_limit=41250,
        dispatchable_job="admittance_payload",
        other_jobs_preserved_without_dispatch=True,
        created_utc=now.isoformat(),
    ))
    print(json.dumps(dict(destination=str(DEST), checkpoint=str(checkpoint), limit=41250,
                          registration_sha256=digest(DEST / "REGISTRATION.json")), indent=2))


if __name__ == "__main__":
    main()
