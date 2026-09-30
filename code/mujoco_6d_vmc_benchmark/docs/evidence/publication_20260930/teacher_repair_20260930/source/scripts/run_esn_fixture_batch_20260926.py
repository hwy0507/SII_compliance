"""Run a frozen ESN fixture plan with bounded, auditable concurrency."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    if args.max_workers < 1 or args.max_workers > 4:
        raise ValueError("max-workers must be in [1, 4]")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    plan = json.loads(args.plan.read_text())
    fixtures = plan["fixtures"]
    ids = [str(item["id"]) for item in fixtures]
    if len(ids) != len(set(ids)):
        raise ValueError("fixture ids must be unique")
    args.output.mkdir(parents=True)
    manifest = {
        "runner": str(args.runner.resolve()),
        "runner_sha256": sha256(args.runner),
        "model": str(args.model.resolve()),
        "model_sha256": sha256(args.model),
        "plan": str(args.plan.resolve()),
        "plan_sha256": sha256(args.plan),
        "python": sys.executable,
        "max_workers": args.max_workers,
        "fixtures": fixtures,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    def run(item: dict) -> dict:
        fixture_id = str(item["id"])
        target = args.output / f"seed_{fixture_id}"
        command = [
            sys.executable, str(args.runner), "--model", str(args.model),
            "--output", str(target), "--seed", fixture_id,
            "--push-angle", str(item["push_angle"]),
            "--push-height", str(item["push_height"]),
            "--payload-mass", str(item["payload_mass"]),
        ]
        started = time.time()
        result = subprocess.run(command, check=False)
        record = {
            "id": fixture_id,
            "command": command,
            "returncode": result.returncode,
            "wall_s": time.time() - started,
        }
        (args.output / f"job_{fixture_id}.json").write_text(json.dumps(record, indent=2) + "\n")
        return record

    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        results = list(pool.map(run, fixtures))
    complete = {
        "status": "complete" if all(row["returncode"] == 0 for row in results) else "failed",
        "wall_s": time.time() - started,
        "jobs": results,
    }
    (args.output / "COMPLETE.json").write_text(json.dumps(complete, indent=2) + "\n")
    print(json.dumps(complete, indent=2))
    if complete["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
