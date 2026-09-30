"""Launch the matched stage-1 campaign as a detached server process."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "paper_stage1_matched_20260921"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    launch_file = OUTPUT / "launch.json"
    if launch_file.exists():
        previous = json.loads(launch_file.read_text())
        pid = int(previous.get("pid", -1))
        if pid > 0:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                pass
            else:
                raise RuntimeError(f"Campaign process is already running: {pid}")
    command = [str(ROOT.parent / ".venv" / "bin" / "python"),
               str(ROOT / "scripts" / "run_matched_stage1_20260921.py"),
               "--output", str(OUTPUT), "--workers", "3", "--epochs", "100"]
    environment = dict(os.environ, MUJOCO_GL="egl", OPENBLAS_NUM_THREADS="1",
                       OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    log = (OUTPUT / "campaign.log").open("a")
    process = subprocess.Popen(command, cwd=ROOT, env=environment, stdout=log,
                               stderr=subprocess.STDOUT, start_new_session=True)
    payload = {"pid": process.pid, "started_unix_s": time.time(), "command": command,
               "output": str(OUTPUT), "log": str(OUTPUT / "campaign.log")}
    temporary = launch_file.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2)); temporary.replace(launch_file)
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
