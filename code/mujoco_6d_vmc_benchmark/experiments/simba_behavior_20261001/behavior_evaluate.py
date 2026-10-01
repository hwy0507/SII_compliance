"""Offline behavior evidence, separate from placement and training rewards.

No actor/model/environment mutation. Required contacts come from raw protocol,
never from observed contacts. Missing time series yields unknown, not success.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
try:
    from .behavior_protocol import DEFAULT, PROTOCOL_VERSION, DEFAULT_EVENT_KINDS
except ImportError:
    from behavior_protocol import DEFAULT, PROTOCOL_VERSION, DEFAULT_EVENT_KINDS


def _base(status, reason):
    return dict(status=status, success=(True if status == "passed" else
        False if status in ("failed", "not_exposed") else None), reason=reason)


def _runs(active, time, gap):
    indices = np.flatnonzero(active)
    if not len(indices):
        return []
    splits = np.flatnonzero(np.diff(time[indices]) > gap+1e-9)+1
    return [x for x in np.split(indices, splits) if len(x)]


def _settle_start(good, time, dt, start, end, duration):
    acc = 0.
    first = None
    for i in np.flatnonzero((time >= start) & (time <= end)):
        if good[i]:
            if first is None:
                first = float(time[i])
            acc += float(dt[i])
            if acc >= duration-1e-9:
                return first
        else:
            acc = 0.
            first = None
    return None


def _impact_settled(z, j, inds, th):
    t = z["time"]
    begin = float(np.nanmin(z["contact_first"][inds, j]))
    end = float(np.nanmax(z["contact_last"][inds, j]))
    finish = begin+th.window_s
    mask = (t >= begin) & (t <= finish)
    finite = (np.isfinite(z["position_error_m"]) &
              np.isfinite(z["rotation_error_rad"]) &
              np.isfinite(z["hand_twist"][:, :3]).all(axis=1))
    if not finite[mask].all():
        return dict(_base("unknown", "nonfinite_recovery_state"), start_s=begin)
    good = ((z["position_error_m"] <= th.position_m) &
            (z["rotation_error_rad"] <= th.rotation_rad) &
            (np.linalg.norm(z["hand_twist"][:, :3], axis=1) <= th.speed_mps))
    # Reaching a different waypoint must not create an artificial error drop.
    ref = z["reference_position"]
    pre = max(0, int(np.searchsorted(t, begin))-1)
    recovery_indices = np.flatnonzero(mask)
    refrot = z["reference_rotation"]
    changed = recovery_indices[(np.linalg.norm(ref[recovery_indices]-ref[pre], axis=1)>1e-8) |
        (np.linalg.norm(refrot[recovery_indices]-refrot[pre], axis=(1, 2))>1e-8)]
    if len(changed):
        finish = min(finish, float(t[changed[0]]))
    active = z["contact_duration"] > 0
    overlap = active & (z["contact_first"] <= end) & (z["contact_last"] >= begin)
    overlap[:, j] = False
    if np.any(overlap):
        return dict(_base("unknown", "attribution_confounded_by_overlapping_contact"),
                    start_s=begin, end_s=end, recovery_time_s=None)
    # Any later independent contact, including a second impact by the same
    # ball, censors attribution to this impact. Never credit the first impact
    # for recovery that only occurs after a later intervention.
    future = active & (z["contact_first"] > end+1e-9) & (z["contact_first"] <= finish)
    future[inds, j] = False
    competing = z["contact_first"][future]
    censor = None
    if len(competing):
        finish = float(np.min(competing))
        censor = "competing_contact"
    elif len(changed):
        censor = "reference_changed"
    bad = np.flatnonzero((t >= begin) & (t < finish) & ~good)
    if not len(bad):
        # It may reject the disturbance without leaving tolerance. Keep this
        # distinct from a recovery trajectory; no zero-second fake recovery.
        return dict(_base("unknown", "no_resolved_departure"),
                    start_s=begin, end_s=end, disturbance_rejected=True,
                    recovery_time_s=None)
    first_bad = int(bad[0])
    recovery = _settle_start(good, t, z["dt"],
                            max(end, float(t[first_bad])), finish, th.settle_s)
    if recovery is not None:
        return dict(_base("passed", "post_impact_settled_recovery"),
                    start_s=begin, end_s=end, recovery_start_s=recovery,
                    recovery_time_s=recovery-end, departure_time_s=float(t[first_bad]))
    reason = censor or ("truncated_window" if t[-1] < begin+th.window_s-1e-9
                        else "no_settled_recovery_within_window")
    return dict(_base("unknown" if censor or reason == "truncated_window" else "failed",
                      reason), start_s=begin, end_s=end, recovery_time_s=None)


def _impact_progress(z, j, inds, th):
    """Recover the original target, then physically advance along task route.

    Target is frozen at contact onset. A new waypoint cannot erase the original
    target error; motion and signed route progress, not stage labels, establish
    progress. No slow/settled condition is imposed on legitimate onward motion.
    """
    t = z["time"]
    begin = float(np.nanmin(z["contact_first"][inds, j]))
    end = float(np.nanmax(z["contact_last"][inds, j]))
    limit = begin+th.window_s
    pre = max(0, int(np.searchsorted(t, begin))-1)
    active = z["contact_duration"] > 0
    overlap = active & (z["contact_first"] <= end) & (z["contact_last"] >= begin)
    overlap[:, j] = False
    if np.any(overlap):
        return _base("unknown", "attribution_confounded_by_overlapping_contact")
    future = active & (z["contact_first"] > end+1e-9) & (z["contact_first"] <= limit)
    future[inds, j] = False
    censored = bool(np.any(future))
    if censored:
        limit = float(np.min(z["contact_first"][future]))
    use = np.flatnonzero((t >= end) & (t < limit))
    if not len(use):
        return _base("unknown", "no_post_impact_window")
    values = (z["hand_position"][use], z["hand_rotation"][use],
              z["route_progress_m"][use], z["reference_position"][pre],
              z["reference_rotation"][pre])
    if not all(np.isfinite(x).all() for x in values):
        return _base("unknown", "missing_pose_or_actual_progress")
    ep = np.linalg.norm(z["hand_position"]-z["reference_position"][pre], axis=1)
    rotations = np.einsum("ij,njk->nik", z["reference_rotation"][pre].T, z["hand_rotation"])
    er = np.arccos(np.clip((np.trace(rotations, axis1=1, axis2=2)-1.)/2., -1., 1.))
    ready = use[(ep[use] <= th.position_m) & (er[use] <= th.rotation_rad)]
    if not len(ready):
        return _base("unknown" if censored or t[-1] < begin+th.window_s else "failed",
                     "original_target_not_regained_after_contact")
    anchor = int(ready[0])
    delta = np.linalg.norm(z["hand_position"]-z["hand_position"][anchor], axis=1)
    gain = z["route_progress_m"]-z["route_progress_m"][anchor]
    good = (delta >= th.progress_m) & (gain >= th.progress_m)
    onset = _settle_start(good, t, z["dt"], float(t[anchor])+1e-9, limit, th.settle_s)
    common = dict(target_regained_s=float(t[anchor]),
                  original_target_position_error_m=float(ep[anchor]),
                  original_target_rotation_error_rad=float(er[anchor]),
                  reference_position_at_contact=z["reference_position"][pre].tolist())
    if onset is not None:
        idx = int(np.searchsorted(t, onset))
        return dict(_base("passed", "original_target_regained_then_real_task_progress"),
                    **common, progress_onset_s=onset,
                    resume_delay_s=onset-end,
                    net_hand_displacement_m=float(delta[idx]),
                    net_route_progress_m=float(gain[idx]),
                    progress_hold_s=th.settle_s)
    return dict(_base("unknown" if censored or t[-1] < begin+th.window_s else "failed",
                      "no_retained_physical_task_progress_after_regaining_target"), **common)


def _impact(z, j, inds, th):
    settled = _impact_settled(z, j, inds, th)
    progress = _impact_progress(z, j, inds, th)
    if settled["status"] == "passed" or progress["status"] == "passed":
        combined = _base("passed", "impact_settled_recovery_or_onward_task_progress")
    elif settled["status"] == "failed" and progress["status"] == "failed":
        combined = _base("failed", "neither_settled_recovery_nor_onward_progress")
    else:
        combined = _base("unknown", "impact_evidence_incomplete")
    # Keep original scalar recovery fields for callers, but never invent a
    # zero recovery time when the hand never left the tolerance region.
    combined.update({k: v for k, v in settled.items() if k not in ("status", "success", "reason")})
    combined.update(impact_settled_recovery=settled, post_impact_progress=progress,
                    impact_settled_recovery_success=settled["success"],
                    impact_progress_success=progress["success"])
    return combined


def _sustained(z, j, inds, th):
    t = z["time"]
    begin = float(np.nanmin(z["contact_first"][inds, j]))
    finish = begin+th.window_s
    inds = inds[t[inds] <= finish]
    duration = float(np.sum(z["contact_duration"][inds, j]))
    span = float(np.nanmax(z["contact_last"][inds, j]))-begin
    gaps = z["contact_first"][inds[1:], j]-z["contact_last"][inds[:-1], j]
    base = dict(start_s=begin, active_duration_s=duration,
                contact_span_s=span, contact_duty_ratio=duration/max(span, 1e-12),
                max_inter_contact_gap_s=max(0., float(np.max(gaps))) if len(gaps) else 0.,
                contact_episode_semantics="force-bearing episodes merged across gaps up to protocol gap_s; not uninterrupted contact")
    if duration < th.sustained_s-1e-9:
        return dict(_base("failed", "insufficient_sustained_contact"), **base)
    # Endpoints must both be force-bearing and after onset. Net displacement,
    # not summed positive speed/path length, rejects oscillation and retreat.
    anchor = int(inds[0])
    direction = z["task_direction"][anchor].copy()
    norm = float(np.linalg.norm(direction))
    if not np.isfinite(norm) or norm < 1e-9:
        return dict(_base("unknown", "undefined_task_direction"), **base)
    direction /= norm
    rel = z["contact_relative"][:, j]
    normals = z["contact_normal"][:, j]
    parts = z["contact_parts"][:, j]
    if not np.isfinite(rel[inds]).all() or not np.isfinite(normals[inds]).all():
        return dict(_base("unknown", "missing_relative_contact_geometry"), **base)
    if len(set(parts[inds].tolist())) != 1 or not str(parts[anchor]):
        return dict(_base("unknown", "contact_robot_body_set_changed"), **base)
    if not np.isfinite(z["route_progress_m"][inds]).all():
        return dict(_base("unknown", "missing_actual_ordered_route_progress"), **base)
    cumulative = 0.
    best_tangent = best_progress = 0.
    candidates = []
    for index in inds:
        cumulative += float(z["contact_duration"][index, j])
        if cumulative < th.sustained_s-1e-9:
            continue
        selected = inds[inds <= index]
        weights = z["contact_impulse"][selected, j]
        normal = np.sum(normals[selected]*weights[:, None], axis=0)
        nn = float(np.linalg.norm(normal))
        if nn < 1e-12:
            continue
        normal /= nn
        delta = rel[index]-rel[anchor]
        tangent = float(np.linalg.norm(delta-normal*float(delta@normal)))
        hand_delta = z["hand_position"][index]-z["hand_position"][anchor]
        projected = float(hand_delta @ direction)
        route_gain = float(z["route_progress_m"][index]-z["route_progress_m"][anchor])
        # Both measured hand motion and actual route projection must advance.
        progress = min(projected, route_gain)
        best_tangent = max(best_tangent, tangent)
        best_progress = max(best_progress, progress)
        candidates.append((int(index), tangent, projected, route_gain,
                           tangent >= th.tangent_m and progress >= th.progress_m))
    # Retain progress until the observed contact-window endpoint. A positive
    # excursion followed by return cannot pass by cherry-picking its peak.
    good_tail = []
    for candidate in reversed(candidates):
        if not candidate[4]:
            break
        good_tail.append(candidate)
    if good_tail and t[good_tail[0][0]]-t[good_tail[-1][0]] >= th.settle_s-1e-9:
        last, first = good_tail[0], good_tail[-1]
        return dict(_base("passed", "active_contact_slide_and_retained_net_progress"),
                    **base, progress_onset_s=float(t[first[0]]),
                    resume_delay_s=float(t[first[0]])-begin,
                    tangent_net_m=last[1], task_projection_m=last[2],
                    ordered_route_gain_m=last[3], evidence_end_s=float(t[last[0]]),
                    retained_tail_contact_duration_s=float(np.sum(z["contact_duration"][[c[0] for c in good_tail], j])),
                    retained_progress_s=float(t[last[0]]-t[first[0]]))
    return dict(_base("failed", "no_contact_slide_with_net_task_progress"),
                **base,
                tangent_net_m=candidates[-1][1] if candidates else None,
                task_net_progress_m=min(candidates[-1][2:4]) if candidates else None,
                max_candidate_tangent_m=best_tangent,
                max_candidate_task_progress_m=best_progress,
                note="transient excursion is insufficient; threshold must be retained to contact-window endpoint")


def evaluate(raw, telemetry=None, *, required_contacts=None, event_kinds=None,
             thresholds=DEFAULT):
    legacy = {k: raw.get(k) for k in ("task_success", "strict_success",
        "placement_complete", "physical_valid", "full_task_horizon_completed",
        "execution_complete", "abort_reason", "contact_required")}
    required = list(raw.get("contact_required", []) if required_contacts is None
                    else required_contacts)
    original = set(raw.get("contact_required", []))
    if not original.issubset(required):
        raise ValueError("Cannot remove original protocol-required contacts (including cup)")
    kinds = dict(DEFAULT_EVENT_KINDS)
    kinds.update(event_kinds or {})
    result = dict(protocol=PROTOCOL_VERSION,
        role="development operational definition; threshold sensitivity pending",
        thresholds=thresholds.to_dict(), required_contacts=required,
        placement_success=bool(raw.get("placement_complete", False)),
        physical_valid=raw.get("physical_valid"), legacy=legacy,
        event_results=[], sensitivity_factors=[.5, 1., 2.])
    fields = ("time", "dt", "hand_position", "hand_rotation", "reference_position", "reference_rotation", "hand_twist",
              "position_error_m", "rotation_error_rad", "task_direction",
              "route_progress_m", "obstacle_ids", "contact_duration",
              "contact_impulse", "contact_first", "contact_last", "contact_normal",
              "contact_relative", "contact_parts")
    z = None
    if telemetry is not None:
        if isinstance(telemetry, (str, Path)):
            if Path(telemetry).is_file():
                with np.load(telemetry, allow_pickle=False) as data:
                    z = {k: data[k].copy() for k in data.files}
        else:
            z = telemetry
    missing = list(fields) if z is None else [k for k in fields if k not in z]
    if not missing and (not len(z["time"]) or not np.isfinite(z["time"]).all()
                        or not np.isfinite(z["dt"]).all()
                        or np.any(np.diff(z["time"]) <= 0) or np.any(z["dt"] <= 0)):
        missing = ["valid_monotone_time"]
    for key in required:
        kind = kinds.get(key)
        if missing:
            entry = _base("unknown", "missing_continuous_telemetry")
            entry["missing_fields"] = missing
        elif kind not in ("impact", "sustained"):
            entry = _base("unknown", "event_kind_not_declared")
        elif key not in list(z["obstacle_ids"]):
            entry = _base("not_exposed", "required_obstacle_not_contacted")
        else:
            j = list(z["obstacle_ids"]).index(key)
            runs = _runs(z["contact_duration"][:, j] > 0, z["time"], thresholds.gap_s)
            episodes = [(_impact(z, j, ix, thresholds) if kind == "impact" else
                         _sustained(z, j, ix, thresholds)) for ix in runs]
            statuses = [e["status"] for e in episodes]
            # Every encountered burst needs evidence; passing one does not
            # conceal a later sustained stall. Very short sustained bursts are
            # exposure fragments, not independent sustained-push attempts.
            qualified = [e for e in episodes if kind == "impact" or
                         e.get("active_duration_s", 0) >= thresholds.sustained_s-1e-9]
            if not qualified:
                entry = _base("not_exposed", "no_qualifying_contact_episode")
            elif all(e["status"] == "passed" for e in qualified):
                entry = _base("passed", "all_qualifying_event_episodes_passed")
            elif any(e["status"] == "failed" for e in qualified):
                entry = _base("failed", "one_or_more_event_episodes_failed")
            else:
                entry = _base("unknown", "event_evidence_incomplete")
            entry["episodes"] = episodes
        entry.update(obstacle_id=key, kind=kind)
        entry["clearance_status"] = "unknown_without_obstacle_withdrawal_or_clearance_trace"
        entry["local_progress_not_full_clearance"] = True
        result["event_results"].append(entry)
    statuses = [e["status"] for e in result["event_results"]]
    if not required:
        status = "unknown"
    elif any(s in ("failed", "not_exposed") for s in statuses):
        status = "failed"
    elif all(s == "passed" for s in statuses):
        status = "passed"
    else:
        status = "unknown"
    result["behavior_status"] = status
    result["behavior_success"] = True if status == "passed" else False if status == "failed" else None
    full = bool(raw.get("full_task_horizon_completed") and
                raw.get("execution_complete") and not raw.get("abort_reason"))
    strict = (False if raw.get("physical_valid") is False or not full else
              None if raw.get("physical_valid") is not True else result["behavior_success"])
    drop = None
    drop_time = None
    if z is not None and "object_position" in z:
        obj = z["object_position"]
        if len(obj) and np.isfinite(obj).all():
            was_lifted = np.maximum.accumulate(obj[:, 2]) >= obj[0, 2]+thresholds.object_lift_m
            dropped = np.flatnonzero(was_lifted & (obj[:, 2] < thresholds.object_floor_z_m))
            drop = bool(len(dropped))
            drop_time = float(z["time"][dropped[0]]) if drop else None
    result["object_drop"] = dict(observed_drop=drop, time_s=drop_time,
        status="unknown" if drop is None else "detected" if drop else "not_observed",
        definition="after measured lift of0.1m from initial center, center below0.39m",
        grasp_integrity_certified=False,
        note="absence of a floor-drop witness does not certify uninterrupted grasp")
    if drop:
        strict = False
    result["strict_behavior_success"] = strict
    result["compliant_progress_success"] = result["behavior_success"]
    result["strict_compliant_progress_success"] = strict
    result["strict_scope"] = "local contact behavior + full horizon + original physical_valid + no observed floor drop; not a general grasp-integrity certificate"
    result["full_horizon_completed"] = full
    return result


def evaluate_file(raw_path, telemetry_path=None, **kwargs):
    """Convenience API for shared evaluator; raw files remain unmodified."""
    return evaluate(json.loads(Path(raw_path).read_text()), telemetry_path, **kwargs)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--telemetry", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = evaluate(json.loads(a.raw.read_text()), a.telemetry)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
