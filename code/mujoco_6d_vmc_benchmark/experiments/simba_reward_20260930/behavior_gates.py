"""Legacy-summary audit: exposure/progress are not compliant-recovery evidence.

This compatibility reader intentionally returns unknown for behavior until
time-aligned telemetry is evaluated by simba_behavior_20261001/behavior_evaluate.py.
It never overwrites the historical success fields.
"""
from __future__ import annotations
import math

def evaluate_behavior(raw, *, expected_contacts=None, task_kind=None):
    declared = raw.get("contact_required")
    if declared is None:
        return dict(behavior_success=None, strict_behavior_success=None,
                    evidence_status="unknown_missing_protocol", reasons=["missing_contact_required"])
    if expected_contacts is not None and list(expected_contacts) != list(declared):
        raise ValueError("Expected contacts must match original protocol; do not remove failed events")
    observed=raw.get("stats",{}).get("events",{})
    checks={}
    for name in declared:
        value=float(observed.get(name,{}).get("duration_s",0.))
        checks[name]=math.isfinite(value) and value>(.0002 if name=="ball" else .4)
    full=(raw.get("full_task_horizon_completed") is True
          and raw.get("execution_complete") is True and not raw.get("abort_reason"))
    physical=raw.get("physical_valid") if isinstance(raw.get("physical_valid"),bool) else None
    return dict(
        behavior_success=None, strict_behavior_success=None,
        evidence_status="unknown_missing_temporal_response_evidence",
        interaction_exposure_valid=all(checks.values()),
        contact_checks=checks, expected_contacts=list(declared),
        full_horizon_completed=full, physical_valid=physical,
        legacy_task_success=raw.get("task_success"),
        legacy_placement_completion=raw.get("placement_complete"),
        task_kind=task_kind or raw.get("arguments",{}).get("task"),
        progress_diagnostic_only=dict(final_stage=raw.get("final_task_stage"),
                                      max_lift_m=raw.get("max_lift_m"),
                                      task_events=raw.get("task_events")),
        reasons=["aggregate contact duration and final stage cannot establish event-ordered recovery"],
    )
