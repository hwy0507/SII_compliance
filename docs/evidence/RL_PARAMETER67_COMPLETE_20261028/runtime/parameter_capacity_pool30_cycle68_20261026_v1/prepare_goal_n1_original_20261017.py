"""Register a finite n-step=1/original-reward RL diagnostic stage.

The stage reuses only the frozen source snapshot and parameter implementation
from the completed occupancy pilot; it creates no training process and does
not modify any prior checkpoint or protocol.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
BENCH = HERE.parents[1]
OUT = BENCH / "outputs" / "rl_goal_n1_historical_utd2_20261018_v1"
PREVIOUS = BENCH / "outputs" / "rl_goal_n1_original_20261017_v3"
ROOT = BENCH / "outputs" / "rl_tuned_20261015_v4"
SOURCE_ROOT = BENCH / "outputs" / "rl_goal_stream_occupancy_20261017_v2"
SOURCE = SOURCE_ROOT / "source"
PARAMETER_BASE = SOURCE_ROOT / "parameter_n25"
PARAMETER = OUT / "parameter_n1"
PYTHON = "/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and p.suffix in (".py", ".json")}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main() -> None:
    assert not OUT.exists(), OUT
    assert SOURCE.is_dir() and PARAMETER_BASE.is_dir()
    protocol = json.loads((ROOT / "PROTOCOL.json").read_text())
    assert protocol["physics_dt_s"] == 5e-5
    methods = [
        {"name": "direct_task_safety", "controller": None, "reward": "office_task", "hp": "historical"},
        {"name": "impedance_payload", "controller": "impedance", "reward": "metric", "hp": "historical"},
        {"name": "admittance_payload", "controller": "admittance", "reward": "metric", "hp": "historical"},
        {"name": "vmc_payload", "controller": "vmc", "reward": "metric", "hp": "historical"},
    ]
    OUT.mkdir(parents=True)
    import shutil
    shutil.copytree(PARAMETER_BASE, PARAMETER, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (PARAMETER / "official_parameter_agent.py").write_text(
        "from official_parameter_agent_base import OfficialParameterAgent\n"
        "BATCH_SIZE = 256\n"
    )
    # The source snapshot is shared read-only; its content hash is recorded
    # instead of duplicating a multi-megabyte tree for this finite arm.
    source_manifest = files(SOURCE)
    parameter_manifest = files(PARAMETER)
    jobs = []
    for method in methods:
        output = OUT / method["name"]
        inherited = 0
        jobs.append(dict(
            name=method["name"], controller=method["controller"], reward=method["reward"],
            reward_variant="original", hp=method["hp"], seed=2026101421,
            inherited_steps=inherited, limit=11000 + inherited,
            checkpoint=None,
            credit_migration=False,
            output=str(output),
            unit="sii-rl-goal-" + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        ))
    registration = dict(
        schema="sii-rl-persistent-goal-stage-v1",
        registered_utc=datetime.now(timezone.utc).isoformat(),
        authorization="2026-10-16 user explicitly enabled persistent RL Goal",
        authorization_start_utc="2026-10-16T04:52:18+00:00",
        goal_scope="finite four-family diagnostic of n_step=1 and original reward; not completion",
        parent_root=str(ROOT), parent_protocol_sha256=sha(ROOT / "PROTOCOL.json"),
        run_root=str(OUT), source_root=str(SOURCE_ROOT), source=str(SOURCE), parameter_source=str(PARAMETER),
        source_manifest=source_manifest, parameter_manifest=parameter_manifest,
        source_commit="working-tree-source-snapshot",
        source_worktree_state="Shared immutable source snapshot; manifests are authoritative",
        runtime=protocol["runtime"], source_base_commit=protocol["source_base_commit"],
        dispatch_deadline_utc=(datetime.now(timezone.utc).replace(microsecond=0)).isoformat(),
        deadline_basis="Replaced below with a 24-hour fail-safe deadline for this finite stage",
        optimizer_schedule_steps=1000000, new_interactions_per_family=11000,
        maximum_new_interactions=44000,
        compute_host="airpig", server_compute=False, python=PYTHON,
        resources=dict(simulators=1, numerical_threads=1, memory_max=3 * 1024**3,
                       memory_max_bytes=3 * 1024**3, swap_max=0, swap_max_bytes=0,
                       cpu="1", cpu_affinity=[1], utd=2, cgroup_required=True, backend="cpu"),
        stop_file=str(OUT / "STOP_REQUESTED"),
        dispatch_lock=str(BENCH / "outputs/.v4_recovery_dispatch.lock"),
        coordinator_unit="sii-rl-goal-stage-" + hashlib.sha256(str(OUT).encode()).hexdigest()[:12],
        jobs=jobs, acceptance_allowed=False,
        previous_stage=str(PREVIOUS),
        minimum_free_disk=20 * 1024**3,
        treatment=dict(n_step=1, utd=2, reward_variant="original",
                       original_task_and_strict_gate_unchanged=True,
                       actor_input="canonical48 unchanged", physics_dt_s=5e-5),
        finite_budget=dict(new_interactions_per_method=11000, stop_at_step=11000,
                           total_new_interactions=44000, max_steps=1000000),
        methods=methods,
        limitations=["No checkpoint is selected from acceptance outcomes",
                     "This stage is a finite diagnostic, not a convergence claim",
                     "All failures remain in the denominator"],
    )
    from datetime import timedelta
    registration["dispatch_deadline_utc"] = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    registration["deadline_basis"] = "24-hour fail-safe for this finite stage under the persistent goal"
    write(OUT / "REGISTRATION.json", registration)
    write(OUT / "execution.json", dict(status="registered", registration_sha256=sha(OUT / "REGISTRATION.json"),
                                       methods=[], started_utc=None, ended_utc=None))
    print(OUT)


if __name__ == "__main__":
    main()
