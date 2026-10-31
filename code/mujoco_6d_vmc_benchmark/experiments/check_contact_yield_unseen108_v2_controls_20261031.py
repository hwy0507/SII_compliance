"""Exercise the locked-v2 final108 coordinator without invoking MuJoCo physics."""
import argparse
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import evaluate_contact_yield_unseen108_locked_v2_20261031 as adapter
import run_v9_unseen_matrix_20261030 as evaluator
from collect_special_scene_actions_20261028 import read, sha, write


REGISTRATION = adapter.OUTPUTS / "contact_yield_locked_unseen108_20261031_v3" / "REGISTRATION.json"


def check(output):
    reg = read(REGISTRATION)
    calls = []

    def synthetic_case(root, case, registration):
        calls.append(case["id"])
        return {
            "id": case["id"],
            "folder": "synthetic-no-physics",
            "metrics_sha256": "0" * 64,
            "pairing": {
                "model_sha256": case["condition"]["id"],
                "initial_observation": [0.0] * 48,
                "filter_config": {},
            },
        }

    with tempfile.TemporaryDirectory(prefix="final108-v2-controls-") as temp:
        root = Path(temp) / "complete"
        root.mkdir()
        write(root / "REGISTRATION.json", reg)
        with patch.object(evaluator, "check_resources"), \
                patch.object(evaluator, "inactive"), \
                patch.object(evaluator, "properties", return_value={"ActiveState": "inactive"}), \
                patch.object(adapter.wide_development, "run_case", side_effect=synthetic_case):
            adapter.run(root)
            state = read(root / "execution.json")
            assert state["status"] == "complete_pending_independent_review"
            assert len(state["rows"]) == 108
            assert calls == [case["id"] for case in reg["cases"]]
            try:
                adapter.run(root)
            except AssertionError:
                pass
            else:
                raise AssertionError("duplicate dispatch accepted")
            assert len(calls) == 108

        failed = Path(temp) / "failed"
        failed.mkdir()
        write(failed / "REGISTRATION.json", reg)
        attempts = []

        def fail_fourth(root, case, registration):
            attempts.append(case["id"])
            if len(attempts) == 4:
                raise RuntimeError("synthetic infrastructure failure")
            return synthetic_case(root, case, registration)

        with patch.object(evaluator, "check_resources"), \
                patch.object(evaluator, "inactive"), \
                patch.object(evaluator, "properties", return_value={"ActiveState": "inactive"}), \
                patch.object(adapter.wide_development, "run_case", side_effect=fail_fourth):
            try:
                adapter.run(failed)
            except RuntimeError:
                pass
            else:
                raise AssertionError("synthetic infrastructure failure was swallowed")
            state = read(failed / "execution.json")
            assert state["status"] == "failed_preserved"
            assert len(state["rows"]) == 3
            assert state["current"] == reg["cases"][3]["id"]
            assert len(attempts) == 4
            try:
                adapter.run(failed)
            except AssertionError:
                pass
            else:
                raise AssertionError("failed run restart accepted")

        incomplete = Path(temp) / "incomplete"
        incomplete.mkdir()
        write(incomplete / "REGISTRATION.json", reg)
        write(incomplete / "execution.json", {
            "status": "complete_pending_independent_review",
            "rows": [{"id": case["id"]} for case in reg["cases"][:107]],
            "registration_sha256": sha(incomplete / "REGISTRATION.json"),
        })
        review_output = incomplete / "REVIEW.json"
        try:
            adapter.review(incomplete, review_output)
        except AssertionError:
            pass
        else:
            raise AssertionError("incomplete 107-row review accepted")
        assert not review_output.exists()

    result = {
        "status": "passed_zero_physics_v2_adapter_controls",
        "registration_sha256": sha(REGISTRATION),
        "test_source_sha256": sha(Path(__file__)),
        "ordered_dispatch_rows": 108,
        "duplicate_dispatch_rejected": True,
        "synthetic_failure_after_calls": 4,
        "failure_receipts_preserved": 3,
        "failed_run_restart_rejected": True,
        "incomplete_107_row_review_rejected": True,
        "physics_calls": 0,
    }
    write(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Control audit output already exists"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = check(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))
