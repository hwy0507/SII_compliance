"""Run independent acceptance for the completed historical UTD2 RL stage."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BENCH = Path(__file__).resolve().parents[1]
STAGE = BENCH / "outputs/rl_goal_n1_historical_utd2_20261018_v1"
OUT = BENCH / "outputs/rl_goal_acceptance_n1_historical_utd2_20261018_v3"
ROOT = BENCH / "outputs/rl_tuned_20261015_v4"
RUNTIME = BENCH / "outputs/baseline_local_rl_20261009/runtime"
V6 = RUNTIME / "v6"
REFERENCE = V6 / "esn_original_v2/rollout.json"
PYTHON = Path("/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python")
sys.path.insert(0, str(BENCH / "tools"))
from research72_checkpoint_20261003 import checkpoint_hashes  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def main():
    assert PYTHON.is_file()
    root_protocol_sha = sha(ROOT / "PROTOCOL.json")
    root_protocol = json.loads((ROOT / "PROTOCOL.json").read_text())
    registration = json.loads((STAGE / "REGISTRATION.json").read_text())
    source_tools = Path(registration["source"]) / "tools"
    conditions = json.loads((ROOT / "CONDITIONS.json").read_text())["conditions"]
    condition = next(x for x in conditions if x["id"] == "repair_acceptance_000")
    assert condition["role"] == "acceptance" and root_protocol["physics_dt_s"] == 5e-5
    assert not OUT.exists(), "Never reuse an acceptance directory"
    OUT.mkdir()
    methods = {
        "direct": ("direct_task_safety", None),
        "impedance": ("impedance_payload", "impedance"),
        "admittance": ("admittance_payload", "admittance"),
        "vmc": ("vmc_payload", "vmc"),
    }
    top = dict(schema="sii-goal-historical-acceptance-v1", status="running",
               started_utc=datetime.now(timezone.utc).isoformat(), host="airpig",
               root_protocol_sha256=root_protocol_sha, condition=condition, methods=[])
    write(OUT / "execution.json", top)
    for name, (job_name, controller) in methods.items():
        training = STAGE / job_name
        train_exec = json.loads((training / "execution.json").read_text())
        assert train_exec["status"] == "complete" and train_exec["stop_reason"] == "step_budget"
        checkpoint = training / "checkpoint_0011000"
        hashes = checkpoint_hashes(checkpoint)
        train_protocol = training / "PROTOCOL.json"
        spec = json.loads(train_protocol.read_text())
        assert spec["controller"] == controller and spec["reward_variant"] == "original"
        manifest = OUT / name / "checkpoint_manifest.json"
        write(manifest, dict(schema="sii-goal-historical-acceptance-manifest-v1", method=name,
            controller=controller, checkpoint=str(checkpoint.resolve()), hashes=hashes,
            training_protocol=str(train_protocol.resolve()), training_protocol_sha256=sha(train_protocol),
            root_protocol=str((ROOT / "PROTOCOL.json").resolve()), root_protocol_sha256=root_protocol_sha,
            acceptance_condition=condition, physics_dt_s=5e-5, server_compute=False,
            resources=dict(simulators=1, threads=1, memory_max_bytes=3 * 1024**3, swap_max_bytes=0)))
        wrapper = source_tools / "baseline_repair_worker_20261008.py"
        parameter = STAGE / "parameter_n1"
        target = OUT / name / "repair_acceptance_000"
        unit = "sii-rl-accept-hist-v3-" + name
        env = ["--setenv=OMP_NUM_THREADS=1", "--setenv=OPENBLAS_NUM_THREADS=1",
               "--setenv=MKL_NUM_THREADS=1", "--setenv=NUMEXPR_NUM_THREADS=1",
               "--setenv=JAX_PLATFORMS=cpu", "--setenv=XLA_PYTHON_CLIENT_PREALLOCATE=false",
               "--setenv=MUJOCO_MENAGERIE_PATH=" + str(RUNTIME / "menagerie")]
        inner = [str(PYTHON), str(wrapper), "--research-protocol", str(ROOT / "PROTOCOL.json"),
                 "--protocol-sha256", root_protocol_sha, "--research-condition", "repair_acceptance_000",
                 "--phase", "acceptance", "--worker-kind", "adapted_rl", "--v6-input", str(V6),
                 "--reference", str(REFERENCE), "--config", str(ROOT / "teacher.json"), "--output", str(target),
                 "--physics-dt", ".00005", "--contact-audit", "--parameter-source", str(parameter),
                 "--agent-checkpoint", str(checkpoint), "--checkpoint-manifest", str(manifest)]
        if controller:
            inner += ["--controller", controller]
        command = ["systemd-run", "--user", "--wait", "--pipe", "--unit=" + unit,
                   "--property=MemoryMax=3G", "--property=MemorySwapMax=0",
                   "--property=CPUQuota=100%", "--property=CPUAffinity=1", "--property=TasksMax=256",
                   "--working-directory=" + str(source_tools)] + env + inner
        log = OUT / name / "acceptance.log"
        row = dict(method=name, controller=controller, checkpoint=str(checkpoint), checkpoint_hashes=hashes,
                   command=command, status="running", started_utc=datetime.now(timezone.utc).isoformat())
        write(OUT / name / "execution.json", row)
        with log.open("x") as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, text=True)
        row.update(status="complete" if result.returncode == 0 else "failed_preserved",
                   returncode=result.returncode, ended_utc=datetime.now(timezone.utc).isoformat(),
                   output=str(target), log=str(log))
        write(OUT / name / "execution.json", row)
        top["methods"].append(row)
        top["updated_utc"] = datetime.now(timezone.utc).isoformat()
        write(OUT / "execution.json", top)
    top["status"] = "complete"
    top["ended_utc"] = datetime.now(timezone.utc).isoformat()
    write(OUT / "execution.json", top)


if __name__ == "__main__":
    main()
