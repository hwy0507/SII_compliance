"""Register the VMC continuation that follows the stage04 admittance recovery."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import sys

BENCH = Path(__file__).resolve().parents[1]
ORIGINAL_ROOT = BENCH / "outputs/rl_tuned_20261015_v4"
STAGE = BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1"
PARENT = BENCH / "outputs/rl_goal_selected_20261016_stage02_v2"
DEST = BENCH / "outputs/rl_goal_recovery_20261017_vmc_v1"
GIB = 1024 ** 3
sys.path.insert(0, str(BENCH / "tools"))
from rl_recovery_control_20261016 import verify_checkpoint  # noqa: E402


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
    return {str(p.relative_to(folder)): digest(p) for p in sorted(Path(folder).rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def main():
    assert platform.node() == "airpig"
    assert not DEST.exists(), "Recovery directory already exists; never reuse it"
    stage_reg = read(STAGE / "REGISTRATION.json")
    original_protocol = ORIGINAL_ROOT / "PROTOCOL.json"
    assert stage_reg["parent_root"] == str(ORIGINAL_ROOT)
    assert stage_reg["parent_protocol_sha256"] == digest(original_protocol)
    checkpoint = PARENT / "vmc_payload/checkpoint_0023375"
    checkpoint_row = verify_checkpoint(checkpoint)
    assert checkpoint_row["step"] == 23375

    source = DEST / "source"
    parameter = DEST / "parameter_n25"
    shutil.copytree(STAGE / "source", source)
    shutil.copytree(STAGE / "parameter_n25", parameter)

    jobs = []
    for original in stage_reg["jobs"]:
        job = dict(original)
        job["output"] = str(DEST / original["name"])
        job["unit"] = "sii-rl-goal-" + hashlib.sha256(job["output"].encode()).hexdigest()[:12]
        job["dispatchable"] = original["name"] == "vmc_payload"
        if original["name"] == "vmc_payload":
            job.update(inherited_steps=23375, limit=34375, checkpoint=str(checkpoint),
                       checkpoint_hashes=checkpoint_row["hashes"],
                       parent_execution_sha256=digest(PARENT / "vmc_payload/execution.json"))
        jobs.append(job)

    now = datetime.now(timezone.utc)
    registration = dict(
        schema="sii-rl-persistent-goal-stage-v1",
        registered_utc=now.isoformat(),
        authorization=stage_reg["authorization"],
        authorization_start_utc=stage_reg["authorization_start_utc"],
        goal_scope="VMC-only finite continuation after admittance recovery; final acceptance remains separate",
        parent_root=str(ORIGINAL_ROOT),
        parent_protocol_sha256=digest(original_protocol),
        parent_stage=str(STAGE),
        parent_stage_registration_sha256=digest(STAGE / "REGISTRATION.json"),
        admittance_recovery=str(BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1"),
        run_root=str(DEST), source=str(source), parameter_source=str(parameter),
        source_manifest=manifest(source), parameter_manifest=manifest(parameter),
        source_commit=stage_reg["source_commit"],
        source_worktree_state="Copied from immutable stage04 snapshot; VMC is not dispatched until admittance closes",
        compute_host="airpig", server_compute=False, python=stage_reg["python"],
        runtime=stage_reg["runtime"], source_base_commit=stage_reg["source_base_commit"],
        dispatch_deadline_utc=(now + timedelta(hours=24)).isoformat(),
        deadline_basis="Finite VMC continuation registered before handoff; no historical budget extension",
        optimizer_schedule_steps=1000000, new_interactions_per_family=11000,
        maximum_new_interactions=44000, finite_continuation_budget=11000,
        previous_stage=dict(root=str(STAGE), registration_sha256=digest(STAGE / "REGISTRATION.json"),
                            execution_sha256=digest(STAGE / "execution.json")),
        resources=dict(simulators=1, cpu="1", numerical_threads=1, memory_max=3 * GIB,
                       swap_max=0, admission_reserve=768 * 1024 ** 2),
        minimum_free_disk=50 * GIB,
        stop_file=str(DEST / "STOP_REQUESTED"),
        dispatch_lock=str(BENCH / "outputs/.v4_recovery_dispatch.lock"),
        coordinator_unit="sii-rl-goal-stage-" + hashlib.sha256(str(DEST).encode()).hexdigest()[:12],
        jobs=jobs, n_step=25, utd=1, acceptance_allowed=False,
        recovery_only_job="vmc_payload", prerequisite="admittance recovery must be complete",
        recovery_checkpoint=checkpoint_row,
        evidence_basis="Exact VMC continuation from the immutable stage02 episode-boundary checkpoint",
    )
    write(DEST / "REGISTRATION.json", registration)
    write(DEST / "HANDOFF_PLAN.json", dict(status="registered_not_launched",
        prerequisite=str(BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1/admittance_payload/execution.json"),
        checkpoint=str(checkpoint), checkpoint_step=23375, registered_limit=34375,
        dispatchable_job="vmc_payload", created_utc=now.isoformat()))
    print(json.dumps(dict(destination=str(DEST), checkpoint=str(checkpoint), limit=34375,
                          registration_sha256=digest(DEST / "REGISTRATION.json")), indent=2))


if __name__ == "__main__":
    main()
