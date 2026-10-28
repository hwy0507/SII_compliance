"""Run the registered office-v7 three-obstacle development comparison."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
LOCK = Path("/home/arm1/sii_shared/SII_compliance/runs/main/all_methods_formal_20261003_104728/VALIDATION_LOCK.json")
V6 = Path("/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002")
PARAMETER = Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02")
MENAGERIE = Path("/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie")

METHODS = (
    "zero", "original_vmc_native", "fixed_vmc", "fixed_admittance", "fixed_impedance",
    "parameter_vmc", "parameter_admittance", "parameter_impedance",
    "direct_metric_74001", "direct_office_task_74001",
    "recovery_lift0.035_distance0.02", "recovery035_esn_fixed",
    "paired_recovery035__fp64", "paired_recovery035_rnn_fp64",
    "recovery035_esn_memoryless", "paired_feature_matched_mlp",
    "paired_feature_matched_rnn",
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write(path: Path, value: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(path)


def selected_candidates(lock: dict) -> list[dict]:
    candidates = {row["name"]: row for row in lock["candidates"]}
    missing = [name for name in METHODS if name not in candidates]
    if missing:
        raise ValueError(f"missing frozen methods: {missing}")
    return [candidates[name] for name in METHODS]


def run_one(root: Path, candidate: dict, condition_id: str, protocol: dict, source: Path) -> dict:
    name = candidate["name"]
    run = root / name
    config = root / f"{name}.config.json"
    write(config, candidate.get("config", {}))
    kind = (
        "nominal" if candidate.get("nominal") else
        "adapted_rl" if candidate.get("adapted_rl") else
        "rl" if candidate.get("rl_case") else
        "classical" if candidate.get("controller") else "office"
    )
    command = [
        sys.executable, str(source / "tools" / "office_v7_worker_20261008.py"),
        "--research-protocol", str(root / "PROTOCOL.json"),
        "--protocol-sha256", sha(root / "PROTOCOL.json"),
        "--research-condition", condition_id, "--worker-kind", kind,
        "--v6-input", str(V6), "--reference", str(V6 / "esn_original_v2" / "rollout.json"),
        "--config", str(config), "--output", str(run), "--contact-audit",
        "--physics-dt", str(protocol["physics_dt_s"]),
    ]
    if candidate.get("checkpoint"):
        command += ["--checkpoint", candidate["checkpoint"]]
    if candidate.get("controller"):
        command += ["--controller", candidate["controller"], "--parameter-source", str(PARAMETER)]
    if candidate.get("rl_case"):
        command += ["--case", candidate["rl_case"], "--bridge", str(V6 / "source" / "bridge_frozen.py")]
    row = {"method": name, "category": candidate["category"], "command": command, "started_utc": now()}
    write(root / f"{name}.execution.json", row)
    unit = "sii-office-v7-" + root.name.replace("_", "-") + "-" + str(abs(hash(name)) % 100000)
    # Archived Orbax arrays carry CUDA sharding. Match their original runtime;
    # silently falling back to CPU makes restore fail before any simulation.
    from run_paper_final_validation_20261003 import ENV as frozen_environment
    managed = [
        "systemd-run", "--user", "--wait", "--pipe", "--collect", "--unit=" + unit,
        "--property=MemoryMax=3G", "--property=MemorySwapMax=0",
    ] + ["--setenv=" + key + "=" + value for key, value in {
        **frozen_environment,
        "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "MUJOCO_MENAGERIE_PATH": str(MENAGERIE),
        # optimize_tool_contact_20261002 validates this as a full Git SHA.
        # Keep the archived source identity explicit instead of using the short
        # display prefix that caused the preserved run-001 infrastructure fail.
        "SII_SOURCE_BASE_COMMIT": "a518ed45ffa2fd2aab84bdc29bba9243ebdaf9d1",
    }.items()] + command
    with (root / f"{name}.log").open("w") as log:
        result = subprocess.run(managed, cwd=source, stdout=log, stderr=subprocess.STDOUT)
    row.update(returncode=result.returncode, ended_utc=now())
    if (run / "AUDIT.json").exists():
        row["audit"] = json.loads((run / "AUDIT.json").read_text())
    if result.returncode != 0:
        row["status"] = "failed_preserved"
    else:
        row["status"] = "complete"
    write(root / f"{name}.execution.json", row)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=ROOT)
    parser.add_argument("--queue-count", type=int, default=4)
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    lock = json.loads(Path(LOCK).read_text())
    candidates = selected_candidates(lock)
    condition = {
        "id": "office_v7_seq_000", "role": "development",
        "overrides": {
            "ball_speed": 1.45, "ball_launch_time_s": 2.0,
            "person_start": 4.5, "person_stroke": 0.20,
            "rod_start": 14.0, "rod_stroke": 0.235, "rod_hold": 5.0,
            "events": "all", "combined_thick_corner_pillar_v4": True,
            "planned_hand_corner": True, "unexpected_edge": True,
            # The archived evaluator accepts the legacy parser for arbitrary
            # registered times; the actual v7 timing is recorded above and in
            # PROTOCOL/CONDITIONS, so no frozen schedule code is changed.
            "allow_lateral_rejoin": True, "interaction_schedule": "legacy",
        },
    }
    conditions = {"schema": "sii-office-v7-conditions-v1", "conditions": [condition]}
    write(root / "CONDITIONS.json", conditions)
    protocol = {
        "schema": "sii-office-v7-sequential-v1", "registered_utc": now(),
        "scene": "ball_short_then_person_long_then_rod_long_then_thick_corner_place",
        "source_lock": str(LOCK), "source_lock_sha256": sha(Path(LOCK)),
        "formal_model_sha256": "d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3",
        "physics_dt_s": 0.00005, "duration_s": 55.0, "seed": 2026100807,
        "condition_file_sha256": sha(root / "CONDITIONS.json"),
        "methods": METHODS, "gate": "unchanged office-v6 task/strict; no new success threshold",
        "actor_inputs": "unchanged 48D proprioceptive/reference-relative fields; no contact truth, object state, event time, visual/distance fields",
        "unchanged": ["geometry", "target", "planner", "common WBC", "action7", "actuator amplitude/slew", "task/strict gate", "MJB"],
        "event_order": ["ball launch 2.0 s", "person 4.5--11.5 s", "rod 14.0--22.5 s", "corner placement after transport"],
    }
    write(root / "PROTOCOL.json", protocol)
    write(root / "MODEL_MANIFEST.json", {"candidates": candidates, "condition": condition})
    source = args.source.resolve()
    # Preserve a complete source overlay for independent replay without copying outputs.
    shutil.copy2(source / "tools" / "office_v7_worker_20261008.py", root / "office_v7_worker_20261008.py")
    state = {"status": "running", "started_utc": now(), "protocol_sha256": sha(root / "PROTOCOL.json"), "rows": []}
    write(root / "execution.json", state)
    def launch(candidate: dict) -> dict:
        return run_one(root, candidate, condition["id"], protocol, source)
    with ThreadPoolExecutor(max_workers=max(1, min(args.queue_count, 4))) as pool:
        rows = list(pool.map(launch, candidates))
    state["rows"] = rows
    state["status"] = "complete" if all(row.get("status") == "complete" for row in rows) else "complete_with_failures_preserved"
    state["ended_utc"] = now()
    write(root / "execution.json", state)
    summary = {
        "protocol_sha256": state["protocol_sha256"], "condition": condition,
        "completed": sum(row.get("status") == "complete" for row in rows), "total": len(rows),
        "task": sum(bool(row.get("audit", {}).get("task_success")) for row in rows),
        "strict": sum(bool(row.get("audit", {}).get("strict_success")) for row in rows),
        "rows": rows,
    }
    write(root / "SUMMARY.json", summary)


if __name__ == "__main__":
    main()
