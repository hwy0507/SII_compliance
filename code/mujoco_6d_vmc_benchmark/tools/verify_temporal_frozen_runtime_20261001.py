"""Two serial, provenance-guarded evaluations of the unchanged seed52 pair.

Run with .venv-canonical-rl under systemd MemoryMax=3G and one thread. No
training, scene edits, or gate edits. The saved-model hook only checks bytes.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
ORIGINAL = ROOT / "outputs/esn_mlp_temporal_consistency_replication_20261001_s52"
MODEL_SHA = "5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9"
MANIFEST_SHA = "6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3"
DEADLINE = datetime.fromisoformat("2026-10-01T16:20:00+00:00")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def now():
    return datetime.now(timezone.utc).isoformat()


def runtime():
    import mujoco
    import numpy
    if mujoco.__version__ != "3.11.0":
        raise RuntimeError(f"Expected frozen MuJoCo 3.11.0, got {mujoco.__version__}")
    cgroup = next(line.split(":", 2)[2] for line in Path("/proc/self/cgroup").read_text().splitlines() if line.startswith("0::"))
    memory_file = Path("/sys/fs/cgroup") / cgroup.lstrip("/") / "memory.max"
    limit = memory_file.read_text().strip()
    if limit == "max" or int(limit) > 3 * 1024**3:
        raise RuntimeError(f"MemoryMax not enforced: {limit}")
    for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(key) != "1":
            raise RuntimeError(f"Expected {key}=1")
    return dict(python=sys.executable, python_version=platform.python_version(),
                mujoco=mujoco.__version__, numpy=numpy.__version__, host=platform.node(),
                cgroup=cgroup, memory_max_bytes=int(limit), threads=1)


def child(run, method):
    sys.path.insert(0, str(ROOT / "scripts"))
    import mujoco
    import validate_office_apparatus_v5_20260917 as evaluator
    from audit_temporal_narrow_screen_20261001 import audit
    record_path = run / f"{method}_execution.json"
    if record_path.exists():
        raise FileExistsError(record_path)
    original_path = ORIGINAL / f"{method}_combined_v4.json"
    original = json.loads(original_path.read_text())
    arguments = dict(original["arguments"])
    arguments["output"] = run / f"{method}_combined_v4"
    arguments["esn_model"] = run / f"{method}_temporal.npz"
    for name, digest in original["source_sha256"].items():
        if sha(ROOT / "scripts" / name) != digest:
            raise RuntimeError(f"Evaluator source drift: {name}")
    manifest = ROOT / "outputs/teacher_bank_label_manifest_20260930_final_v1/manifest.json"
    if sha(manifest) != MANIFEST_SHA:
        raise RuntimeError("Teacher manifest changed")
    if sha(arguments["esn_model"]) != original["neural_logging"]["model_sha256"]:
        raise RuntimeError("Checkpoint changed")
    record = dict(status="running", started_utc=now(), runtime=runtime(),
                  argv=sys.argv, arguments={k: str(v) if isinstance(v, Path) else v for k, v in arguments.items()},
                  source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
                  wrapper_sha256=sha(__file__), source_sha256=original["source_sha256"],
                  scripts_sha256={str(p.relative_to(ROOT)): sha(p) for p in sorted((ROOT / "scripts").rglob("*.py"))},
                  baseline_summary_sha256=sha(original_path), expected_mjb_sha256=MODEL_SHA,
                  checkpoint_sha256=sha(arguments["esn_model"]), manifest_sha256=MANIFEST_SHA,
                  training_record_sha256=sha(run / "TRAINING_COMPLETE.json"),
                  training_config_sha256=sha(ROOT / "configs/esn_mlp_temporal_consistency_narrow_rep_seed52_20261001.json"),
                  development_only=True)
    write(record_path, record)
    original_save = mujoco.mj_saveModel

    def save_checked(model, filename, buffer):
        value = original_save(model, filename, buffer)
        digest = sha(filename)
        record["actual_mjb_sha256"] = digest
        write(record_path, record)
        if digest != MODEL_SHA:
            raise RuntimeError(f"Frozen model mismatch before episode: {digest}")
        return value

    mujoco.mj_saveModel = save_checked
    try:
        evaluator.run(SimpleNamespace(**arguments))
        row = audit(run, method)
        write(run / f"{method}_AUDIT.json", row)
        record.update(status="complete", outcome=row)
    except BaseException as exc:
        record.update(status="failed", error=repr(exc))
        raise
    finally:
        mujoco.mj_saveModel = original_save
        record["ended_utc"] = now()
        write(record_path, record)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--method", choices=("esn", "mlp"))
    args = parser.parse_args()
    run = args.root.resolve()
    if args.method:
        child(run, args.method)
        return
    runtime_info = runtime()
    run.mkdir(parents=True, exist_ok=True)
    with (run / "campaign.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = run / "execution.json"
        if state_path.exists():
            raise FileExistsError("Existing campaign retained; inspect before any resume")
        for filename in ("esn_temporal.npz", "mlp_temporal.npz", "TRAINING_COMPLETE.json"):
            if (run / filename).exists():
                raise FileExistsError(run / filename)
            shutil.copyfile(ORIGINAL / filename, run / filename)
        state = dict(status="running", started_utc=now(), deadline_utc=DEADLINE.isoformat(),
                     runtime=runtime_info, original=str(ORIGINAL), rows=[])
        write(state_path, state)
        for method in ("esn", "mlp"):
            if datetime.now(timezone.utc) >= DEADLINE:
                state["status"] = "deadline_no_new_dispatch"
                break
            command = [sys.executable, str(Path(__file__).resolve()), "--root", str(run), "--method", method]
            with (run / f"{method}.log").open("x") as log:
                result = subprocess.run(command, cwd=REPO, stdout=log, stderr=subprocess.STDOUT)
            state["rows"].append(dict(method=method, command=command, returncode=result.returncode))
            write(state_path, state)
            if result.returncode:
                state["status"] = "failed_preserved"
                break
        else:
            state["status"] = "complete"
        state["ended_utc"] = now()
        write(state_path, state)


if __name__ == "__main__":
    main()
