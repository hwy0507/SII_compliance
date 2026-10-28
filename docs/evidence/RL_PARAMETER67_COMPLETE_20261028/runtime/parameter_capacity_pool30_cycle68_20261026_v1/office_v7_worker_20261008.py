"""Development-only worker for the re-timed three-obstacle office-v7 scene.

The archived office-v6 model, task gates, action contract and actuator limits are
unchanged.  This wrapper only accepts a separately registered condition file so
that the disturbance schedule is auditable and cannot be confused with the
sealed office-v6 evaluation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import paper_office_worker_20261002 as office


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--research-protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--research-condition", required=True)
    parser.add_argument(
        "--worker-kind",
        choices=("office", "classical", "rl", "adapted_rl", "nominal"),
        default="office",
    )
    args, rest = parser.parse_known_args()
    protocol = json.loads(args.research_protocol.read_text())
    assert office.worker.sha(args.research_protocol) == args.protocol_sha256
    assert protocol["schema"] == "sii-office-v7-sequential-v1"
    conditions_path = args.research_protocol.parent / "CONDITIONS.json"
    assert office.worker.sha(conditions_path) == protocol["condition_file_sha256"]
    condition = next(
        row
        for row in json.loads(conditions_path.read_text())["conditions"]
        if row["id"] == args.research_condition
    )
    assert condition["role"] == "development"
    values = dict(condition["overrides"])
    original = office.evaluation_settings

    def settings(v6, dt, condition_file=None, condition_id=None):
        assert condition_file is None and condition_id is None
        assert dt == protocol["physics_dt_s"]
        expected, overrides, provenance = original(v6, dt)
        assert expected == protocol["formal_model_sha256"]
        overrides.update(values)
        provenance.update(
            condition_id=condition["id"],
            data_role="development",
            research_protocol_sha256=args.protocol_sha256,
            research_condition=condition,
            condition_file_sha256=office.worker.sha(conditions_path),
            condition_wrapper_sha256=office.worker.sha(Path(__file__)),
            use="Retimed three-obstacle development scene only; never a sealed test or training label",
        )
        return expected, overrides, provenance

    office.evaluation_settings = settings
    output = Path(rest[rest.index("--output") + 1]).resolve()
    if args.worker_kind == "nominal":
        import research72_nominal_worker_20261003 as selected
    elif args.worker_kind == "adapted_rl":
        import research72_adapted_rl_worker_20261003 as selected
    elif args.worker_kind == "classical":
        import paper_classical_worker_20261002 as selected
    elif args.worker_kind == "rl":
        import paper_rl_worker_20261002 as selected
    else:
        selected = office
    sys.argv = [sys.argv[0], *rest]
    try:
        selected.main()
    finally:
        if output.exists():
            office.worker.write(
                output / "OFFICE_V7_ROLE.json",
                {
                    "protocol_sha256": args.protocol_sha256,
                    "condition": condition,
                    "worker_kind": args.worker_kind,
                    "wrapper_source_sha256": office.worker.sha(Path(__file__)),
                },
            )
            (output / "office_v7_worker.py.txt").write_text(Path(__file__).read_text())


if __name__ == "__main__":
    main()
