"""Dependency-free smoke test for the migration boundary."""

from __future__ import annotations

from .adapter import FetchToFR3Adapter
from .contracts import FetchWaypoint, MigrationConfig
from .trajectory import resample


def _identity_fk(_q):
    return (
        (1.0, 0.0, 0.0, 0.4),
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.5),
        (0.0, 0.0, 0.0, 1.0),
    )


def _identity_ik(_pose, seed):
    return tuple(seed)


def main() -> None:
    source = [
        FetchWaypoint(0.0, (0.0, 0.0, 0.0, 0.3, 0.0, -0.5, 0.0, -1.8, 0.0, 1.5, 0.7)),
        FetchWaypoint(0.2, (0.0, 0.0, 0.0, 0.3, 0.1, -0.4, 0.0, -1.7, 0.0, 1.4, 0.7)),
    ]
    adapter = FetchToFR3Adapter(_identity_fk, _identity_ik, MigrationConfig())
    fr3 = adapter.to_fr3_waypoints(source, (0.0, -0.5, 0.0, -1.8, 0.0, 1.5, 0.7))
    dense = resample(fr3, 0.04)
    assert len(dense) == 6, len(dense)
    assert dense[-1].q == fr3[-1].q
    print(f"migration smoke passed: {len(fr3)} waypoints -> {len(dense)} FR3 samples")


if __name__ == "__main__":
    main()
