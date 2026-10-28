"""Fixed two-arm paired training/evaluation campaign with a dispatch cutoff."""
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import subprocess
import sys

from verify_temporal_frozen_runtime_20261001 import ROOT, DEADLINE, runtime, write, now, sha


def main():
    root = ROOT / "outputs/temporal_s52_latent_dropout_20261001_v1"
    runtime_info = runtime()
    root.mkdir(parents=True, exist_ok=True)
    with (root / "campaign.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = root / "execution.json"
        if state_path.exists():
            raise FileExistsError("Preserve existing campaign; inspect manually before resume")
        state = dict(status="running", started_utc=now(), runtime=runtime_info,
                     deadline_utc=DEADLINE.isoformat(), commands=[], source_sha256=sha(__file__))
        write(state_path, state)
        for label in ("p000", "p010"):
            train = root / f"{label}_train"
            evaluation = root / f"{label}_eval"
            config = ROOT / f"configs/temporal_s52_latent_dropout_{label}_20261001.json"
            commands = [
                [sys.executable, str(ROOT/"tools/train_esn_mlp_temporal_consistency_screen_20261001.py"),
                 "--manifest", str(ROOT/"outputs/teacher_bank_label_manifest_20260930_final_v1/manifest.json"),
                 "--root", str(ROOT/"outputs/teacher_bank_three_domains_20260930_v10"),
                 "--config", str(config), "--output", str(train), "--delta-weight", "0.25"],
                [sys.executable, str(ROOT/"tools/verify_temporal_frozen_runtime_20261001.py"),
                 "--root", str(evaluation), "--checkpoint-source", str(train)],
            ]
            for phase, command in zip(("train", "eval"), commands):
                if datetime.now(timezone.utc) >= DEADLINE:
                    state.update(status="deadline_no_new_dispatch", ended_utc=now())
                    write(state_path, state)
                    return
                record = dict(label=label, phase=phase, command=command, config_sha256=sha(config), started_utc=now())
                state["commands"].append(record)
                write(state_path, state)
                with (root/f"{label}_{phase}.log").open("x") as log:
                    result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
                record.update(returncode=result.returncode, ended_utc=now())
                if result.returncode:
                    state.update(status="failed_preserved", ended_utc=now())
                    write(state_path, state)
                    return
                if phase == "eval" and json.loads((evaluation/"execution.json").read_text())["status"] != "complete":
                    state.update(status="evaluation_incomplete", ended_utc=now())
                    write(state_path, state)
                    return
                write(state_path, state)
        state.update(status="complete", ended_utc=now())
        write(state_path, state)


if __name__ == "__main__":
    main()
