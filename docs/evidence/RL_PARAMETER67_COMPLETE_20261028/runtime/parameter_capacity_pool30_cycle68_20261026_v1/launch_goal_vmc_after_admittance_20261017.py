"""Wait for the registered admittance recovery, then dispatch VMC once."""
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import time
import sys

BENCH = Path(__file__).resolve().parents[1]
ADM = BENCH / "outputs/rl_goal_recovery_20261017_admittance_v1/admittance_payload/execution.json"
ROOT = BENCH / "outputs/rl_goal_recovery_20261017_vmc_v1"
REG = ROOT / "REGISTRATION.json"
RECEIPT = ROOT / "HANDOFF_RECEIPT.json"
LOCK = BENCH / "outputs/.v4_recovery_dispatch.lock"
sys.path.insert(0, str(BENCH / "tools"))
from rl_goal_stage_20261016 import read, write, worker_command  # noqa: E402
from rl_recovery_control_20261016 import active_workers, verify_checkpoint  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    reg = read(REG)
    job = next(j for j in reg["jobs"] if j["name"] == "vmc_payload")
    while True:
        state = read(ADM)
        if state["status"] == "complete":
            if state.get("steps") != 41250 or state.get("stop_reason") != "step_budget":
                raise RuntimeError(f"admittance completed unexpectedly: {state.get('steps')} {state.get('stop_reason')}")
            break
        if state["status"] != "running":
            write(ROOT / "HANDOFF_STOP.json", dict(status="blocked_by_admittance", observed=state, utc=now()))
            raise RuntimeError(f"admittance did not complete: {state.get('status')}")
        time.sleep(30)

    with LOCK.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        state = read(ADM)
        if state["status"] != "complete" or state["steps"] != 41250:
            raise RuntimeError("admittance state changed while acquiring dispatch lock")
        workers = active_workers()
        if workers:
            write(ROOT / "HANDOFF_STOP.json", dict(status="active_worker_seen", workers=workers, utc=now()))
            raise RuntimeError(f"active workers present: {workers}")
        output = Path(job["output"])
        if output.exists():
            raise FileExistsError(f"VMC output already exists: {output}")
        checkpoint = Path(job["checkpoint"])
        checked = verify_checkpoint(checkpoint)
        assert checked["step"] == job["inherited_steps"] == 23375
        command = worker_command(reg, job)
        launch = dict(status="dispatching", utc=now(), prerequisite=str(ADM),
                      prerequisite_steps=state["steps"], checkpoint=checked,
                      command=command, active_workers_before=workers)
        with (ROOT / "HANDOFF_LAUNCH.json").open("x") as file:
            json.dump(launch, file, indent=2, ensure_ascii=False)
            file.write("\n")

    result = subprocess.run(command, text=True, capture_output=True)
    receipt = dict(status="complete" if result.returncode == 0 else "failed_preserved",
                   returncode=result.returncode, started_utc=launch["utc"], ended_utc=now(),
                   command=command, stdout=result.stdout[-20000:], stderr=result.stderr[-20000:],
                   checkpoint=checked, prerequisite_steps=state["steps"])
    write(RECEIPT, receipt)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
