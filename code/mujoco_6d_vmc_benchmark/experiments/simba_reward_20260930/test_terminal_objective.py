"""Prevent successful placement from being penalized for avoided contacts."""
from terminal_objective import reward_task_success
def main():
    placed=dict(placement_complete=True,task_success=True,physical_valid=True,
                strict_success=False,contact_coverage_valid=False,abort_reason=None)
    assert reward_task_success(placed,"task_physical")
    assert not reward_task_success(placed,"legacy_strict")
    for key in ("placement_complete","task_success","physical_valid"):
        assert not reward_task_success(dict(placed,**{key:False}),"task_physical"),key
    assert not reward_task_success(dict(placed,abort_reason="physics"),"task_physical")
    assert not reward_task_success(dict(placed,placement_complete=False,final_task_stage="retreat"),"task_physical")
    print("7 terminal objective assertions PASS")
if __name__=="__main__":main()
