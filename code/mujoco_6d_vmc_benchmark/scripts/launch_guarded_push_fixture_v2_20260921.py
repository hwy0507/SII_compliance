"""Launch the corrected physical-fixture guarded-push matrix."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "outputs" / "paper_stage1_matched_20260921"
OUTPUT = STAGE / "guarded_push_fixture_eval_v2"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    command = [str(ROOT.parent / ".venv" / "bin" / "python"),
               str(ROOT / "scripts" / "evaluate_matched_guarded_push_20260921.py"),
               "--selection", str(STAGE / "selection.json"),
               "--output", str(OUTPUT), "--workers", "16"]
    log = (OUTPUT / "evaluation.log").open("a")
    process = subprocess.Popen(command, cwd=ROOT,
                               env=dict(os.environ, MUJOCO_GL="egl", OPENBLAS_NUM_THREADS="1",
                                        OMP_NUM_THREADS="1", MKL_NUM_THREADS="1"),
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    payload = {"pid": process.pid, "started_unix_s": time.time(), "command": command,
               "invalid_predecessor": str(STAGE / "guarded_push_evaluation"),
               "reason": "runner seed did not alter physics; replaced by angle/height/payload fixtures"}
    temporary = (OUTPUT / "launch.json").with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2)); temporary.replace(OUTPUT / "launch.json")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
