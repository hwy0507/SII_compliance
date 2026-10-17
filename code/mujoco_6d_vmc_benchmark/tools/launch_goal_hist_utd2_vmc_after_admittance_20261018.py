"""Dispatch the registered historical-UTD2 VMC job after admittance closes.

This is a one-shot handoff. It refuses an incomplete prerequisite, any active
worker, or an existing VMC output, and preserves a launch/receipt record on
both success and failure. It does not run acceptance or alter the registration.
"""
from datetime import datetime, timezone
import fcntl
import json
import argparse
from pathlib import Path
import subprocess
import sys

BENCH = Path(__file__).resolve().parents[1]
ROOT = BENCH / "outputs/rl_goal_n1_historical_utd2_20261018_v1"
REG = ROOT / "REGISTRATION.json"
ADM = ROOT / "admittance_payload" / "execution.json"
OUT = ROOT / "vmc_payload"
LOCK = BENCH / "outputs/.v4_recovery_dispatch.lock"
LAUNCH = ROOT / "vmc_payload.HANDOFF_LAUNCH.json"
RECEIPT = ROOT / "vmc_payload.HANDOFF_RECEIPT.json"

sys.path.insert(0, str(BENCH / "tools"))
from rl_goal_stage_20261016 import read, worker_command, write  # noqa: E402
from rl_recovery_control_20261016 import active_workers  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--retry-after-failed', action='store_true')
    args = parser.parse_args()
    reg = read(REG)
    job = next(j for j in reg["jobs"] if j["name"] == "vmc_payload")
    adm = read(ADM)
    if not (adm.get("status") == "complete" and adm.get("steps") == 11000 and
            adm.get("stop_reason") == "step_budget"):
        raise RuntimeError(f"admittance prerequisite is not closed: {adm.get('status')} "
                           f"steps={adm.get('steps')} stop={adm.get('stop_reason')}")
    if len(adm.get("rows", [])) != 8 or adm["rows"][-1].get("step_after") != 11000:
        raise RuntimeError("admittance does not have eight complete registered rows")
    launch_path, receipt_path = LAUNCH, RECEIPT
    if RECEIPT.exists():
        previous = read(RECEIPT)
        if not args.retry_after_failed or previous.get('status') != 'failed_preserved':
            raise FileExistsError("VMC output or non-failed handoff receipt already exists")
        attempt = 1
        while (ROOT / f"vmc_payload.HANDOFF_RETRY_{attempt:03d}_LAUNCH.json").exists() or \
                (ROOT / f"vmc_payload.HANDOFF_RETRY_{attempt:03d}_RECEIPT.json").exists():
            attempt += 1
        launch_path = ROOT / f"vmc_payload.HANDOFF_RETRY_{attempt:03d}_LAUNCH.json"
        receipt_path = ROOT / f"vmc_payload.HANDOFF_RETRY_{attempt:03d}_RECEIPT.json"
    if OUT.exists() or launch_path.exists() or receipt_path.exists():
        raise FileExistsError("VMC output or handoff receipt already exists; refusing retry")

    command = worker_command(reg, job)
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        workers = active_workers()
        if workers:
            raise RuntimeError(f"active workers present: {workers}")
        if OUT.exists() or launch_path.exists() or receipt_path.exists():
            raise FileExistsError("VMC output or handoff receipt appeared during lock")
        launch = {
            "status": "dispatching",
            "started_utc": now(),
            "prerequisite": str(ADM),
            "prerequisite_steps": adm["steps"],
            "prerequisite_stop_reason": adm["stop_reason"],
            "active_workers_before": workers,
            "job": job,
            "command": command,
        }
        with launch_path.open("x") as handle:
            json.dump(launch, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

    result = subprocess.run(command, text=True, capture_output=True)
    receipt = {
        "status": "complete" if result.returncode == 0 else "failed_preserved",
        "returncode": result.returncode,
        "started_utc": launch["started_utc"],
        "ended_utc": now(),
        "prerequisite_steps": adm["steps"],
        "command": command,
        "stdout_tail": result.stdout[-20000:],
        "stderr_tail": result.stderr[-20000:],
    }
    receipt["launch_record"] = str(launch_path)
    write(receipt_path, receipt)
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
