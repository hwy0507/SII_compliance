"""Recompute auditable task/safety metrics for frozen ESN fixture batches."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def parse_batch(spec: str, penetration_limit_m: float) -> dict:
    if "=" not in spec:
        raise ValueError(f"batch must be LABEL=PATH, got {spec!r}")
    label, raw_root = spec.split("=", 1)
    root = Path(raw_root).resolve()
    manifest_path = root / "manifest.json"
    complete_path = root / "COMPLETE.json"
    if not manifest_path.is_file() or not complete_path.is_file():
        raise FileNotFoundError(f"incomplete batch metadata: {root}")
    manifest = load(manifest_path)
    complete = load(complete_path)
    fixtures = [int(item["id"]) for item in manifest["fixtures"]]
    rows = []
    for fixture in fixtures:
        episode = root / f"seed_{fixture}"
        result_path = episode / "rollout.json"
        trace_path = episode / "rollout.npz"
        audit_path = episode / "metrics" / "audit_manifest.json"
        status_path = episode / "status.json"
        for required in (result_path, trace_path, audit_path, status_path):
            if not required.is_file():
                raise FileNotFoundError(required)
        result = load(result_path)
        audit = load(audit_path)
        status = load(status_path)
        if int(status["status"]) != 0:
            raise RuntimeError(f"fixture {fixture} returned {status['status']}")
        episodes = audit.get("episodes", [])
        if len(episodes) != 1:
            raise ValueError(f"fixture {fixture} has {len(episodes)} substep episodes")
        substep = episodes[0]
        contact = result["contact"]
        penetration = float(contact["all_external_max_penetration_m"])
        task = bool(result["success"])
        strict = bool(
            task
            and result["grasp_lift_success"]
            and not result["invalid_physics"]
            and penetration <= penetration_limit_m
        )
        rows.append(
            {
                "fixture": fixture,
                "task_success": task,
                "strict_success": strict,
                "grasp_lift_success": bool(result["grasp_lift_success"]),
                "invalid_physics": bool(result["invalid_physics"]),
                "endpoint_error_mm": 1000.0 * float(result["endpoint_error_m"]),
                "lift_m": float(result["lift_m"]),
                "penetration_mm": 1000.0 * penetration,
                "substep_position_rmse_mm": 1000.0 * float(substep["position_rmse_3d_m"]),
                "peak_torque_nm": float(substep["generalized_actuator_torque_peak_nm"]),
                "peak_speed_mps": float(substep["linear_speed_peak_mps"]),
                "files": {
                    "result": str(result_path),
                    "result_sha256": sha256(result_path),
                    "trace": str(trace_path),
                    "trace_sha256": sha256(trace_path),
                    "substep_audit": str(audit_path),
                    "substep_audit_sha256": sha256(audit_path),
                },
            }
        )
    return {
        "label": label,
        "root": str(root),
        "batch_status": complete["status"],
        "manifest": str(manifest_path),
        "manifest_sha256": sha256(manifest_path),
        "model_sha256": manifest["model_sha256"],
        "runner_sha256": manifest["runner_sha256"],
        "plan_sha256": manifest["plan_sha256"],
        "task_success": sum(row["task_success"] for row in rows),
        "strict_success": sum(row["strict_success"] for row in rows),
        "total": len(rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--penetration-limit-mm", type=float, default=0.2)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    if args.penetration_limit_mm <= 0:
        raise ValueError("penetration limit must be positive")
    report = {
        "contract": "esn_fixture_batch_summary_v1",
        "strict_definition": {
            "task_success": True,
            "grasp_lift_success": True,
            "invalid_physics": False,
            "all_external_max_penetration_mm_max": args.penetration_limit_mm,
        },
        "batches": [
            parse_batch(spec, args.penetration_limit_mm / 1000.0)
            for spec in args.batch
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        row["label"]: {
            "task": f"{row['task_success']}/{row['total']}",
            "strict": f"{row['strict_success']}/{row['total']}",
        }
        for row in report["batches"]
    }, indent=2))


if __name__ == "__main__":
    main()
