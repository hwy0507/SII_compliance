"""Run the four registered RL checkpoints through independent acceptance.

This script only reads the completed training checkpoints.  It creates a new
acceptance directory, verifies checkpoint/protocol hashes, and runs one
registered ``repair_acceptance_000`` condition per method.  It never edits a
training receipt and never selects a checkpoint from evaluation results.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


HERE = Path(__file__).resolve()
BENCH = HERE.parents[1]
OUT = BENCH / "outputs" / "rl_goal_acceptance_20261017_v1f"
ROOT_PROTOCOL = BENCH / "outputs" / "rl_tuned_20261015_v4" / "PROTOCOL.json"
CONDITIONS = BENCH / "outputs" / "rl_tuned_20261015_v4" / "CONDITIONS.json"
RUNTIME = BENCH / "outputs" / "baseline_local_rl_20261009" / "runtime"
V6 = RUNTIME / "v6"
REFERENCE = V6 / "esn_original_v2" / "rollout.json"
PYTHON = Path("/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def checkpoint_hashes(path: Path) -> dict[str, str]:
    result = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise RuntimeError(f"symlink in checkpoint: {item}")
        if item.is_file():
            result[str(item.relative_to(path))] = sha(item)
    required = ("official_agent_state.json", "actor", "critic", "target_critic",
                "temperature", "obs_norm", "rew_norm")
    assert "official_agent_state.json" in result
    assert all(any(name == key or name.startswith(key + "/") for name in result)
               for key in required[1:])
    return result


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main() -> int:
    assert PYTHON.is_file(), PYTHON
    assert ROOT_PROTOCOL.is_file() and CONDITIONS.is_file()
    root_protocol_sha = sha(ROOT_PROTOCOL)
    root_protocol = json.loads(ROOT_PROTOCOL.read_text())
    assert root_protocol["schema"] == "sii-baseline-strengthening-v1"
    assert root_protocol["physics_dt_s"] == 5e-5
    assert root_protocol["formal_model_sha256"]
    conditions = {row["id"]: row for row in json.loads(CONDITIONS.read_text())["conditions"]}
    acceptance = conditions["repair_acceptance_000"]
    assert acceptance["role"] == "acceptance"

    methods = {
        "direct": dict(
            training=BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1/direct_task_safety",
            checkpoint=BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1/direct_task_safety/checkpoint_0040512",
            controller=None,
        ),
        "impedance": dict(
            training=BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1/impedance_payload",
            checkpoint=BENCH / "outputs/rl_goal_selected_20261016_stage04_mixed_cpu_v1/impedance_payload/checkpoint_0034375",
            controller="impedance",
        ),
        "admittance": dict(
            training=BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1/admittance_payload",
            checkpoint=BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1/admittance_payload/checkpoint_0041250",
            controller="admittance",
        ),
        "vmc": dict(
            training=BENCH / "outputs/rl_goal_recovery_20261017_vmc_v1/vmc_payload",
            checkpoint=BENCH / "outputs/rl_goal_recovery_20261017_vmc_v1/vmc_payload/checkpoint_0034375",
            controller="vmc",
        ),
    }
    OUT.mkdir(parents=True, exist_ok=False)
    manifest_paths = {}
    for name, item in methods.items():
        training_protocol = item["training"] / "PROTOCOL.json"
        hashes = checkpoint_hashes(item["checkpoint"])
        assert json.loads(training_protocol.read_text())["controller"] == item["controller"]
        manifest = OUT / name / "checkpoint_manifest.json"
        write_json(manifest, dict(
            schema="sii-goal-rl-acceptance-manifest-v1",
            created_utc=datetime.now(timezone.utc).isoformat(),
            method=name, controller=item["controller"],
            checkpoint=str(item["checkpoint"].resolve()), hashes=hashes,
            training_protocol=str(training_protocol.resolve()),
            training_protocol_sha256=sha(training_protocol),
            root_protocol=str(ROOT_PROTOCOL.resolve()),
            root_protocol_sha256=root_protocol_sha,
            acceptance_condition=acceptance,
            frozen_model_sha256=root_protocol["formal_model_sha256"],
            physics_dt_s=root_protocol["physics_dt_s"],
            server_compute=False, resources=dict(simulators=1, threads=1,
                memory_max_bytes=3 * 1024**3, swap_max_bytes=0),
        ))
        manifest_paths[name] = manifest

    top = dict(schema="sii-goal-rl-acceptance-v1", status="running",
               started_utc=datetime.now(timezone.utc).isoformat(), host="airpig",
               root_protocol_sha256=root_protocol_sha, acceptance_condition=acceptance,
               methods=[])
    write_json(OUT / "execution.json", top)
    for name, item in methods.items():
        target = OUT / name / "repair_acceptance_000"
        source_tools = item["training"].parent / "source" / "tools"
        wrapper = source_tools / "baseline_repair_worker_20261008.py"
        assert wrapper.is_file()
        argv = [str(PYTHON), str(wrapper), "--research-protocol", str(ROOT_PROTOCOL),
                "--protocol-sha256", root_protocol_sha, "--research-condition",
                "repair_acceptance_000", "--phase", "acceptance", "--worker-kind",
                "adapted_rl", "--v6-input", str(V6), "--reference", str(REFERENCE),
                "--config", str(BENCH / "outputs/rl_tuned_20261015_v4/teacher.json"),
                "--output", str(target), "--physics-dt", ".00005", "--contact-audit",
            "--parameter-source", str(item["training"].parent / "parameter_n25"),
                "--agent-checkpoint", str(item["checkpoint"]), "--checkpoint-manifest",
                str(manifest_paths[name])]
        if item["controller"]:
            argv += ["--controller", item["controller"]]
        env = dict(os.environ, JAX_PLATFORMS="cpu", XLA_PYTHON_CLIENT_PREALLOCATE="false",
                   OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                   MUJOCO_MENAGERIE_PATH=str(RUNTIME / "menagerie"),
                   SII_MEMORY_MAX_BYTES=str(3 * 1024**3), SII_MEMORY_LIMIT_MODE="rss_monitor")
        log = OUT / name / "acceptance.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        # The desktop sandbox cannot create a user systemd unit.  Keep the
        # single CPU lane and record this limitation; the run is still audited
        # against the registered 3 GiB protocol and any failure is preserved.
        command = ["taskset", "-c", "1"] + argv
        row = dict(method=name, command=command, checkpoint=str(item["checkpoint"]),
                   checkpoint_hashes=checkpoint_hashes(item["checkpoint"]), status="running",
                   started_utc=datetime.now(timezone.utc).isoformat())
        with log.open("x") as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                    env=env, cwd=source_tools.parent.parent)
        row.update(status="complete" if result.returncode == 0 else "failed_preserved",
                   returncode=result.returncode, ended_utc=datetime.now(timezone.utc).isoformat(),
                   output=str(target), log=str(log))
        write_json(OUT / name / "execution.json", row)
        top["methods"].append(row)
        top["updated_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(OUT / "execution.json", top)
        if result.returncode:
            top["status"] = "failed_preserved"
            write_json(OUT / "execution.json", top)
            return result.returncode
    top["status"] = "complete"
    top["ended_utc"] = datetime.now(timezone.utc).isoformat()
    write_json(OUT / "execution.json", top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
