"""Counterexamples to the retired aggregate stage-plus-lift gate."""
from behavior_gates import evaluate_behavior

def example():
    return dict(contact_required=["ball","cup"],full_task_horizon_completed=True,
                execution_complete=True,physical_valid=True,task_success=False,
                placement_complete=False,final_task_stage="carry",max_lift_m=.16,
                stats={"events":{"ball":{"duration_s":.001},"cup":{"duration_s":4.}}})

def test_lift_and_contact_do_not_prove_recovery():
    result=evaluate_behavior(example())
    assert result["behavior_success"] is None
    assert result["interaction_exposure_valid"] is True

def test_missing_cup_cannot_be_removed():
    try:evaluate_behavior(example(),expected_contacts=["ball"])
    except ValueError:pass
    else:raise AssertionError("must reject changed original protocol")

def test_missing_evidence_not_converted_to_failure_or_success():
    raw=example();raw["stats"]["events"].pop("cup")
    result=evaluate_behavior(raw)
    assert result["behavior_success"] is None
    assert result["interaction_exposure_valid"] is False

def test_hold_is_not_automatically_success():
    raw=example();raw["arguments"]={"task":"hold"}
    assert evaluate_behavior(raw)["behavior_success"] is None

if __name__=="__main__":
    for f in list(globals().values()):
        if callable(f) and getattr(f,"__name__","").startswith("test_"):f()
    print("4 tests PASS")
