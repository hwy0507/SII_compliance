"""Run the current four-method RL checkpoints through independent acceptance.

The training receipts are immutable inputs.  This runner creates a fresh
acceptance directory, verifies checkpoint hashes, and executes one frozen
``repair_acceptance_000`` rollout per method under the registered CPU cgroup.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess


BENCH = Path(__file__).resolve().parents[1]
PARENT = BENCH / "outputs/rl_goal_selected_20261018_stage06_retry2_parent_cpu_v1"
RECOVERY = BENCH / "outputs/rl_goal_recovery_20261018_backend_cpu_v3"
OUT = BENCH / "outputs/rl_goal_acceptance_20261018_v3"
RUNTIME = BENCH / "outputs/baseline_local_rl_20261009/runtime"
V6 = RUNTIME / "v6"
REFERENCE = V6 / "esn_original_v2/rollout.json"
PYTHON = Path("/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def hashes(path: Path) -> dict[str, str]:
    result = {}
    for item in sorted(path.rglob("*")):
        if item.is_symlink():
            raise RuntimeError(f"symlink in checkpoint: {item}")
        if item.is_file():
            result[str(item.relative_to(path))] = sha(item)
    required = ("official_agent_state.json", "actor", "critic", "target_critic",
                "temperature", "obs_norm", "rew_norm")
    if "official_agent_state.json" not in result:
        raise RuntimeError(f"missing official agent state: {path}")
    for prefix in required[1:]:
        if not any(name == prefix or name.startswith(prefix + "/") for name in result):
            raise RuntimeError(f"missing {prefix} in checkpoint: {path}")
    return result


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main() -> int:
    if OUT.exists():
        raise FileExistsError(OUT)
    if not PYTHON.is_file() or not REFERENCE.is_file():
        raise FileNotFoundError("local RL runtime or reference rollout")
    protocol = PARENT / "PROTOCOL.json"
    conditions = json.loads((PARENT / "CONDITIONS.json").read_text())["conditions"]
    condition = next(row for row in conditions if row["id"] == "repair_acceptance_000")
    protocol_sha = sha(protocol)
    methods = {
        "direct": (BENCH / "outputs/rl_goal_selected_20261018_stage06_retry2_cpu_v1/direct_task_safety",
                   BENCH / "outputs/rl_goal_selected_20261018_stage06_retry2_cpu_v1/direct_task_safety/checkpoint_0074998", None),
        "impedance": (BENCH / "outputs/rl_goal_selected_20261018_stage06_retry2_cpu_v1/impedance_payload",
                      BENCH / "outputs/rl_goal_selected_20261018_stage06_retry2_cpu_v1/impedance_payload/checkpoint_0041250", "impedance"),
        "admittance": (RECOVERY / "admittance_payload", RECOVERY / "admittance_payload/checkpoint_0034375", "admittance"),
        "vmc": (RECOVERY / "vmc_payload", RECOVERY / "vmc_payload/checkpoint_0034375", "vmc"),
    }
    for name, (training, checkpoint, controller) in methods.items():
        execution = json.loads((training / "execution.json").read_text())
        if execution.get("status") != "complete" or execution.get("stop_reason") != "step_budget":
            raise RuntimeError(f"training is not complete: {name}")
        if not checkpoint.is_dir():
            raise FileNotFoundError(checkpoint)

    OUT.mkdir(parents=True)
    top = {
        "schema": "sii-goal-rl-acceptance-v2",
        "status": "running",
        "started_utc": now(),
        "host": "airpig",
        "protocol": str(protocol.resolve()),
        "protocol_sha256": protocol_sha,
        "acceptance_condition": condition,
        "physics_dt_s": 5e-5,
        "server_compute": False,
        "resources": {"simulators": 1, "threads": 1, "memory_max_bytes": 3 * 1024**3,
                      "swap_max_bytes": 0},
        "methods": [],
    }
    write(OUT / "execution.json", top)
    for name, (training, checkpoint, controller) in methods.items():
        checkpoint_hashes = hashes(checkpoint)
        training_protocol = training / "PROTOCOL.json"
        manifest = OUT / name / "checkpoint_manifest.json"
        write(manifest, {
            "schema": "sii-goal-rl-acceptance-manifest-v2",
            "created_utc": now(), "method": name, "controller": controller,
            "checkpoint": str(checkpoint.resolve()), "hashes": checkpoint_hashes,
            "training_execution": str((training / "execution.json").resolve()),
            "training_protocol": str(training_protocol.resolve()),
            "training_protocol_sha256": sha(training_protocol),
            "root_protocol": str(protocol.resolve()), "root_protocol_sha256": protocol_sha,
            "acceptance_condition": condition, "physics_dt_s": 5e-5, "server_compute": False,
        })
        target = OUT / name / "repair_acceptance_000"
        wrapper = RECOVERY / "source/tools/baseline_repair_worker_20261008.py"
        argv = [str(PYTHON), str(wrapper), "--research-protocol", str(protocol),
                "--protocol-sha256", protocol_sha, "--research-condition", "repair_acceptance_000",
                "--phase", "acceptance", "--worker-kind", "adapted_rl", "--v6-input", str(V6),
                "--reference", str(REFERENCE), "--config", str(PARENT / "teacher.json"),
                "--output", str(target), "--physics-dt", ".00005", "--contact-audit",
                "--parameter-source", str(RECOVERY / "parameter_n25"),
                "--agent-checkpoint", str(checkpoint), "--checkpoint-manifest", str(manifest)]
        if controller:
            argv += ["--controller", controller]
        unit = f"sii-rl-goal-accept-20261018-v3-{name}"
        command = ["systemd-run", "--user", "--wait", "--pipe", f"--unit={unit}",
                   "--property=MemoryMax=3G", "--property=MemorySwapMax=0",
                   "--property=CPUQuota=100%", "--property=CPUAffinity=1",
                   "--property=TasksMax=256", f"--working-directory={RECOVERY / 'source'}",
                   "--setenv=OMP_NUM_THREADS=1", "--setenv=OPENBLAS_NUM_THREADS=1",
                   "--setenv=MKL_NUM_THREADS=1", "--setenv=NUMEXPR_NUM_THREADS=1",
                   "--setenv=JAX_PLATFORMS=cpu", "--setenv=XLA_PYTHON_CLIENT_PREALLOCATE=false",
                   f"--setenv=MUJOCO_MENAGERIE_PATH={RUNTIME / 'menagerie'}"] + argv
        log = OUT / name / "acceptance.log"
        row = {"method": name, "controller": controller, "command": command,
               "checkpoint": str(checkpoint), "hashes": checkpoint_hashes,
               "status": "running", "started_utc": now(), "output": str(target), "log": str(log)}
        write(OUT / name / "execution.json", row)
        with log.open("x") as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                    text=True, cwd=RECOVERY / "source")
        row.update(status="complete" if result.returncode == 0 else "failed_preserved",
                   returncode=result.returncode, ended_utc=now())
        write(OUT / name / "execution.json", row)
        top["methods"].append(row)
        top["updated_utc"] = now()
        if result.returncode:
            top["status"] = "failed_preserved"
            write(OUT / "execution.json", top)
            return result.returncode
        write(OUT / "execution.json", top)
    top["status"] = "complete"
    top["ended_utc"] = now()
    write(OUT / "execution.json", top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
