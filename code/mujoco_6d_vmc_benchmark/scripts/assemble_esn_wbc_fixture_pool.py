#!/usr/bin/env python3
"""Combine audited ESN fixture-screening rounds into one selection pool.

The source manifests remain immutable screening evidence.  This utility only
combines their candidates after checking that their WBC/reference/controller
boundaries match, so a supplementary direction-specific physical probe cannot
silently contaminate a different benchmark protocol.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    if data.get("reference_source") != "fixed_panda_wbc":
        raise ValueError(f"{path}: expected fixed_panda_wbc reference source")
    if data.get("splits", {}).get("test"):
        raise ValueError(f"{path}: a train/validation source must not contain test fixtures")
    return data


def _qualified_row(row: dict[str, Any], source_path: Path) -> dict[str, Any]:
    """Give each combined row an immutable source-qualified fixture ID."""

    result = dict(row)
    result["source_fixture_id"] = result["fixture_id"]
    result["source_manifest"] = str(source_path)
    result["fixture_id"] = f"{source_path.stem}__{result['source_fixture_id']}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-manifests", type=Path, nargs="+", required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    sources = [_load(path) for path in args.source_manifests]
    first = sources[0]
    selection = first["selection_controller"]
    gate = first["effective_collision_gate"]
    validity_gate = first["validity_gate"]
    for path, source in zip(args.source_manifests[1:], sources[1:]):
        if source["selection_controller"] != selection or source["effective_collision_gate"] != gate or source["validity_gate"] != validity_gate:
            raise ValueError(f"{path}: selector or validity gate differs from the first source")
    candidates = [
        _qualified_row(candidate, source_path)
        for source_path, source in zip(args.source_manifests, sources)
        for candidate in source["candidates"]
    ]
    selected = [
        _qualified_row(row, source_path)
        for source_path, source in zip(args.source_manifests, sources)
        for split_name in ("train", "validation")
        for row in source["splits"][split_name]
    ]
    fixture_ids = [row["fixture_id"] for row in selected]
    if len(set(fixture_ids)) != len(fixture_ids):
        raise ValueError("fixture IDs overlap across screening rounds")
    split = {
        "train": [row for row in selected if row["split"] == "train"],
        "validation": [row for row in selected if row["split"] == "validation"],
        "test": [],
    }
    if not split["train"] or not split["validation"]:
        raise ValueError("combined fixture pool needs non-empty train and validation splits")
    output: dict[str, Any] = {
        "schema_version": 1,
        "stage": "assembled WBC-aware ESN train/validation physical fixture pool",
        "scope": first["scope"],
        "data_boundary": first["data_boundary"],
        "reference_source": "fixed_panda_wbc",
        "selection_controller": selection,
        "effective_collision_gate": gate,
        "validity_gate": validity_gate,
        "source_manifests": [str(path) for path in args.source_manifests],
        "screening_summary": {
            "candidate_count": len(candidates), "valid_fixture_count": len(selected),
            "invalid_fixture_count": len(candidates) - len(selected),
            "invalid_fixtures": [{"fixture_id": row["fixture_id"], "reasons": row["selector_invalid_reasons"]} for row in candidates if not row["selector_valid"]],
        },
        "candidates": candidates,
        "splits": split,
    }
    args.output_manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output_manifest.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps({"train": len(split["train"]), "validation": len(split["validation"]), "invalid": output["screening_summary"]["invalid_fixture_count"]}, indent=2))


if __name__ == "__main__":
    main()
