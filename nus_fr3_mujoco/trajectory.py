"""Trajectory utilities shared by the NUS migration and FR3 controller."""

from __future__ import annotations

from typing import Iterable, List, Sequence

from .contracts import FR3Waypoint


def _lerp(left: Sequence[float], right: Sequence[float], ratio: float) -> tuple[float, ...]:
    return tuple(a + ratio * (b - a) for a, b in zip(left, right))


def validate_monotonic(waypoints: Iterable[FR3Waypoint]) -> List[FR3Waypoint]:
    result = list(waypoints)
    if not result:
        raise ValueError("trajectory must contain at least one waypoint")
    for previous, current in zip(result, result[1:]):
        if current.time_s <= previous.time_s:
            raise ValueError("waypoint times must be strictly increasing")
    return result


def resample(waypoints: Iterable[FR3Waypoint], dt_s: float) -> List[FR3Waypoint]:
    """Linearly resample an FR3 trajectory without changing its endpoints."""

    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")
    source = validate_monotonic(waypoints)
    if len(source) == 1:
        return source

    result: List[FR3Waypoint] = []
    segment = 0
    final_time = source[-1].time_s
    count = int(final_time // dt_s)
    sample_times = [min(index * dt_s, final_time) for index in range(count + 1)]
    if sample_times[-1] < final_time:
        sample_times.append(final_time)

    for sample_time in sample_times:
        while segment + 1 < len(source) and sample_time > source[segment + 1].time_s:
            segment += 1
        left = source[segment]
        if segment + 1 >= len(source):
            right = left
            ratio = 0.0
        else:
            right = source[segment + 1]
            span = right.time_s - left.time_s
            ratio = 0.0 if span <= 0.0 else (sample_time - left.time_s) / span
        phase = left.phase if ratio < 0.5 else right.phase
        result.append(FR3Waypoint(sample_time, _lerp(left.q, right.q, ratio), phase))
    return result
