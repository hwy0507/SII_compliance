"""Pure-unit coverage for the validation checkpoint Pareto archive."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from evaluate_wbc_velocity_residual_checkpoints import (  # noqa: E402
    OBJECTIVES,
    discover_candidates,
    pareto_frontier,
    select_representative,
)


def _candidate(identifier: str, values: tuple[float, ...], passed: bool = True) -> dict:
    return {
        "candidate_id": identifier,
        "gate": {
            "passed": passed,
            "summary": {key: {"mean": value} for key, value in zip(OBJECTIVES, values)},
        },
    }


def test_discover_candidates_requires_matching_vecnormalize(tmp_path: Path) -> None:
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    (checkpoints / "ppo_wbc_residual_1600_steps.zip").touch()
    (checkpoints / "ppo_wbc_residual_800_steps.zip").touch()
    (checkpoints / "ppo_wbc_residual_800_steps_vecnormalize.pkl").touch()
    (tmp_path / "ppo_wbc_residual_final.zip").touch()
    (tmp_path / "vecnormalize.pkl").touch()
    candidates = discover_candidates(tmp_path)
    assert [item["candidate_id"] for item in candidates] == ["step_800", "final"]


def test_pareto_filters_gate_failures_and_dominated_points() -> None:
    candidates = [
        _candidate("a", (1.0, 1.0, 1.0, 1.0, 1.0)),
        _candidate("b", (1.2, 1.3, 1.1, 1.4, 1.2)),
        _candidate("c", (0.8, 1.6, 1.3, 1.1, 1.1)),
        _candidate("bad", (0.1, 0.1, 0.1, 0.1, 0.1), passed=False),
    ]
    frontier = pareto_frontier(candidates)
    assert [item["candidate_id"] for item in frontier] == ["a", "c"]


def test_representative_uses_predeclared_equal_rank_rule() -> None:
    frontier = [
        _candidate("recovery", (0.5, 1.4, 1.4, 1.4, 1.4)),
        _candidate("balanced", (0.8, 0.8, 0.8, 0.8, 0.8)),
        _candidate("torque", (1.3, 1.3, 1.3, 1.3, 0.5)),
    ]
    assert select_representative(frontier)["candidate_id"] == "balanced"
