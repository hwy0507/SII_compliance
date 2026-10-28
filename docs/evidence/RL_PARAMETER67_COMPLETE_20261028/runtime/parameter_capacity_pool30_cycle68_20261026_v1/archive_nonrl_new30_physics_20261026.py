"""Package audited completed conditions without modifying live experiment files."""
import argparse
import hashlib
import io
import json
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def digest_stream(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1 << 20), b""):
        h.update(block)
    return h.hexdigest()


def sha(path):
    with path.open("rb") as stream:
        return digest_stream(stream)


def require(test, message):
    if not test:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--audit", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    lock = json.loads((root / "MODEL_LOCK.json").read_text())
    execution_bytes = (root / "execution.json").read_bytes()
    execution = json.loads(execution_bytes)
    completed = {x["name"] for x in execution["evaluation"] if x["status"] == "complete"}
    expected = {x["name"] for x in lock["models"]}
    require(len(expected) == 9 and lock["status"] == "frozen", "Expected 9 locked models")
    files = {f"run/{name}": root / name for name in (
        "MODEL_LOCK.json", "PROTOCOL.json", "REGISTRATION.json", "CONDITIONS.json")}
    files["tools/" + Path(__file__).name] = Path(__file__).resolve()
    conditions = []
    rows = []
    hash_fields = {"audit_sha256": "AUDIT.json", "trace_sha256": "rollout.npz",
                   "execution_sha256": "execution.json", "model_sha256": "rollout.mjb",
                   "chain_sha256": "execution_chain.npz",
                   "substep_metrics_sha256": "rollout_metrics/substep_metrics.npz",
                   "research_substeps_sha256": "research_substeps.npz"}
    for audit_path in args.audit:
        audit = json.loads(audit_path.read_text())
        condition = audit["condition"]
        require(condition not in conditions, "Repeated condition")
        require(audit["status"] == "completed_condition_physics_audit_passed_not_final",
                "Completed independent condition audit required")
        require(Path(audit["root"]).resolve() == root, "Audit root mismatch")
        require(audit["model_lock_sha256"] == sha(root / "MODEL_LOCK.json"), "Model lock mismatch")
        condition_rows = audit["verified_physical_rows"]
        require(len(condition_rows) == 9 and {r["method"] for r in condition_rows} == expected,
                "Condition must contain all 9 models")
        files[f"audits/{condition}.json"] = audit_path.resolve()
        for row in condition_rows:
            name = f"{row['method']}__{condition}"
            run = root / "evaluation" / name
            require(row["condition"] == condition and Path(row["run"]).resolve() == run,
                    "Physical row identity mismatch")
            require(name in completed and json.loads((run / "execution.json").read_text())["status"] == "complete",
                    "Refuse incomplete episode")
            for field, relative in hash_fields.items():
                require(sha(run / relative) == row[field], f"Audit hash mismatch: {name}/{relative}")
            metric = root / "metrics" / f"{name}.json"
            require(sha(metric) == row["metric_sha256"], "Metric hash mismatch")
            files[f"run/metrics/{name}.json"] = metric
            for path in sorted(run.rglob("*")):
                require(not path.is_symlink(), "Symlinks are not archive payload")
                if path.is_file():
                    require(path.suffix != ".tmp", "Incomplete temporary file")
                    files["run/" + path.relative_to(root).as_posix()] = path
        conditions.append(condition)
        rows.extend(condition_rows)
    manifest_files = {}
    for name, path in files.items():
        require(not path.is_symlink(), "Unexpected symlink")
        before = path.stat()
        hashed = sha(path)
        after = path.stat()
        require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "Source changed during hashing")
        manifest_files[name] = {"sha256": hashed, "bytes": after.st_size}
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_root=str(root),
                    conditions=conditions, episodes=len(rows), files=manifest_files,
                    limitation="Completed conditions only; not final acceptance. Runtime dependencies and full training sources are in separate archives.")
    extra = {"MANIFEST.json": (json.dumps(manifest, indent=2)+"\n").encode(),
             "EXECUTION_SNAPSHOT.json": execution_bytes,
             "AUDITED_ROWS.json": (json.dumps(rows, indent=2)+"\n").encode()}
    args.output.mkdir(parents=True, exist_ok=False)
    partial = args.output / "PHYSICS_BUNDLE.tar.gz.partial"
    with tarfile.open(partial, "w:gz", compresslevel=1) as archive:
        for name, path in sorted(files.items()):
            archive.add(path, arcname=name, recursive=False)
        for name, content in extra.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, io.BytesIO(content))
    expected_archive = {**manifest_files, **{
        n: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)} for n, b in extra.items()}}
    with tarfile.open(partial, "r:gz") as archive:
        seen = set()
        for member in archive:
            require(member.isfile() and member.name in expected_archive and member.name not in seen,
                    "Unexpected archive member")
            target = expected_archive[member.name]
            require(member.size == target["bytes"] and digest_stream(archive.extractfile(member)) == target["sha256"],
                    "Archive payload mismatch")
            seen.add(member.name)
        require(seen == set(expected_archive), "Missing archive members")
    for name, path in files.items():
        require(path.stat().st_size == manifest_files[name]["bytes"] and sha(path) == manifest_files[name]["sha256"],
                "Source changed during packaging")
    final = args.output / "PHYSICS_BUNDLE.tar.gz"
    partial.rename(final)
    receipt = dict(status="local_package_verified_not_yet_shared", archive=str(final.resolve()),
                   sha256=sha(final), bytes=final.stat().st_size, conditions=conditions,
                   episodes=len(rows), source_files=len(files),
                   source_bytes=sum(x["bytes"] for x in manifest_files.values()),
                   manifest_sha256=expected_archive["MANIFEST.json"]["sha256"],
                   source_before_after_and_archive_payload_verified=True)
    (args.output / "LOCAL_PACKAGE_RECEIPT.json").write_text(json.dumps(receipt, indent=2)+"\n")
    print(json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
