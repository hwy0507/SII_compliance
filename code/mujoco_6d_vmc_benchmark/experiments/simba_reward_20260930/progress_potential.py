"""Shared dense progress diagnostic, reward-only; task/actor/physics unchanged.

Continuous within a fixed task stage, with existing monotone milestone changes.
No readiness timer, event clock, contact truth or obstacle geometry is used.
"""
import math

POSITION_SCALE_M = 4.0 * 0.012
ROTATION_SCALE_RAD = 4.0 * 0.12
SPEED_SCALE_MPS = 4.0 * 0.025
PROGRESS_VERSION = "shared_dense_waypoint_recovery_v1"
CLASSIFICATION = "training_coverage_diagnostic_not_primary_campaign_result"


def dense_progress_potential(stage_index, stage_count, segment_begin, target_position,
                             position, rotation_error, linear_velocity):
    if not isinstance(stage_index, int) or not isinstance(stage_count, int):
        raise ValueError("stage/count must be integers")
    if stage_count <= 0 or not 0 <= stage_index < stage_count:
        raise ValueError("invalid stage")
    vectors = [tuple(float(x) for x in v) for v in (
        segment_begin, target_position, position, rotation_error, linear_velocity)]
    if any(len(v) != 3 or any(not math.isfinite(x) for x in v) for v in vectors):
        raise ValueError("finite three-vectors required")
    begin, target, pos, er, velocity = vectors
    direction = [b-a for a,b in zip(begin,target)]
    length2 = sum(x*x for x in direction)
    projection = (max(0.,min(1.,sum((p-b)*v for p,b,v in zip(pos,begin,direction))/length2))
                  if length2 > 1e-12 else 0.)
    error2 = sum(((p-t)/POSITION_SCALE_M)**2 for p,t in zip(pos,target))
    orientation2 = sum((x/ROTATION_SCALE_RAD)**2 for x in er)
    speed2 = sum((x/SPEED_SCALE_MPS)**2 for x in velocity)
    proximity = math.exp(-error2-orientation2-speed2)
    fraction = .5*projection + .5*proximity
    return float((stage_index+fraction)/stage_count)
