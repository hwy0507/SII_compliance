"""Task completion and experiment exposure are separate predicates."""
def reward_task_success(raw, objective="legacy_strict"):
    if objective=="legacy_strict":
        return raw.get("strict_success") is True
    if objective!="task_physical":
        raise ValueError("Unknown terminal objective")
    # No stage inference, shortened horizon, or contact-coverage requirement.
    return (raw.get("placement_complete") is True and
            raw.get("task_success") is True and
            raw.get("physical_valid") is True and not raw.get("abort_reason"))
