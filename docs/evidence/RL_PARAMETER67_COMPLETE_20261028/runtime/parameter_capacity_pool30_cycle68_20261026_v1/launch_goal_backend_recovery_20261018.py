"""Run the registered admittance -> VMC CPU recovery exactly once.

This coordinator owns only dispatch ordering and receipts.  Each worker keeps
the existing one simulator, CPU1, 3 GiB, no-swap cgroup envelope.
"""
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys

BENCH = Path(__file__).resolve().parents[1]
ROOT = BENCH / "outputs/rl_goal_recovery_20261018_backend_cpu_v3"
LOCK = BENCH / "outputs/.v4_recovery_dispatch.lock"
sys.path.insert(0, str(BENCH / "tools"))
from rl_goal_stage_20261016 import digest, read, verify_checkpoint, verify_inputs, verify_preflight, worker_command, write  # noqa: E402
from rl_recovery_control_20261016 import active_workers  # noqa: E402


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    reg = read(ROOT / "REGISTRATION.json")
    assert not (ROOT / "execution.json").exists(), "Recovery coordinator is one-shot"
    verify_inputs(reg)
    verify_preflight(reg)
    jobs = [j for j in reg["jobs"] if j.get("dispatchable")]
    assert [j["name"] for j in jobs] == ["admittance_payload", "vmc_payload"]
    state = dict(status="running", started_utc=now(), jobs=[], active=None,
                 registration_sha256=digest(ROOT / "REGISTRATION.json"), goal_complete=False,
                 dispatch_order=[j["name"] for j in jobs], backend_migration=True)

    def save():
        state["updated_utc"] = now()
        write(ROOT / "execution.json", state)

    with LOCK.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        if active_workers():
            state.update(status="stopped_before_dispatch", reason="active_worker_seen")
            save()
            return 2
        save()
        try:
            for index, job in enumerate(jobs):
                if index and state["jobs"][-1].get("stop_reason") != "step_budget":
                    raise RuntimeError("Previous payload did not close at its registered step budget")
                if Path(reg["stop_file"]).exists():
                    raise RuntimeError("cooperative_stop")
                if active_workers():
                    raise RuntimeError("active_worker_seen")
                output = Path(job["output"])
                if output.exists():
                    raise FileExistsError(f"Recovery output already exists: {output}")
                cp = verify_checkpoint(Path(job["checkpoint"]))
                command = worker_command(reg, job)
                launch_path = ROOT / (job["name"] + ".LAUNCH.json")
                receipt_path = ROOT / (job["name"] + ".RECEIPT.json")
                launch = dict(status="dispatching", started_utc=now(), job=job,
                              checkpoint=cp, active_workers_before=[], command=command,
                              backend_migration=True)
                launch_path.write_text(json.dumps(launch, indent=2, ensure_ascii=False) + "\n")
                state["active"] = dict(job=job["name"], unit=job["unit"], output=str(output))
                state["jobs"].append(dict(job=job["name"], command=command,
                                          started_utc=launch["started_utc"], checkpoint=cp))
                save()
                result = subprocess.run(command, text=True, capture_output=True)
                receipt = dict(status="complete" if result.returncode == 0 else "failed_preserved",
                               returncode=result.returncode, started_utc=launch["started_utc"],
                               ended_utc=now(), command=command, checkpoint=cp,
                               stdout_tail=result.stdout[-20000:], stderr_tail=result.stderr[-20000:],
                               backend_migration=True)
                write(receipt_path, receipt)
                state["active"] = None
                state["jobs"][-1].update(returncode=result.returncode, ended_utc=receipt["ended_utc"])
                if result.returncode:
                    state.update(status="failed_preserved", error="worker_failed")
                    save()
                    return result.returncode
                training = read(output / "execution.json")
                assert training["status"] == "complete"
                final_cp = verify_checkpoint(Path(training["checkpoint_rows"][-1]["path"]))
                state["jobs"][-1].update(steps=training["steps"], stop_reason=training["stop_reason"],
                                          completed_episodes=len(training["rows"]), checkpoint=final_cp,
                                          task=sum(bool(r.get("result", {}).get("task_success")) for r in training["rows"]),
                                          strict=sum(bool(r.get("result", {}).get("strict_success")) for r in training["rows"]))
                if training["stop_reason"] != "step_budget":
                    state.update(status="stopped_at_episode_boundary", reason=training["stop_reason"])
                    save()
                    return 3
                save()
            state.update(status="finite_recovery_complete", convergence_demonstrated=False,
                         goal_complete=False)
        except BaseException as exc:
            state.update(status="failed_preserved", error=repr(exc), active=None)
            save()
            raise
        finally:
            state["ended_utc"] = now()
            save()


if __name__ == "__main__":
    main()
