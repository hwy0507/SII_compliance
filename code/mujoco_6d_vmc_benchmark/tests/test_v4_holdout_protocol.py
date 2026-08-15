"""Static protocol guards for the V4 timing holdout declaration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from screen_benchmark_v4_holdout import (  # noqa: E402
    DEFAULT_HOLDOUT_START_TIMES_S,
    PILOT_START_TIMES_S,
    V4_HOLDOUT_CASES,
)


def test_holdout_is_five_side_and_excludes_unvalidated_positive_z() -> None:
    sides = {case["rod_approach_side"] for case in V4_HOLDOUT_CASES}
    assert sides == {"negative_x", "positive_x", "negative_y", "positive_y", "negative_z"}
    assert "positive_z" not in sides


def test_holdout_times_do_not_overlap_development_pilot() -> None:
    assert set(DEFAULT_HOLDOUT_START_TIMES_S).isdisjoint(PILOT_START_TIMES_S)


@pytest.mark.parametrize("case", V4_HOLDOUT_CASES)
def test_holdout_case_has_replayable_physical_geometry(case: dict[str, float | str]) -> None:
    assert case["rod_stroke_m"] > 0.0
    assert case["rod_height_m"] > 0.0
    assert isinstance(case["rod_approach_side"], str)
