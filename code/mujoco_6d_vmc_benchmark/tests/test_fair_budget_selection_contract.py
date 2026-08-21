"""Static checks for the predeclared fair budget-selection protocol."""

from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "run_fair_budget_selection.py"


def test_selection_protocol_separates_validation_and_test_seeds() -> None:
    source = SCRIPT.read_text()

    assert '"--validation-seeds"' in source
    assert '"--test-seeds"' in source
    assert '"shared_budget_validation_selection_then_heldout_test"' in source
    assert '"test_rows"' in source


def test_esn_and_vmc_share_budget_candidates_and_selection_rule() -> None:
    source = SCRIPT.read_text()

    assert '"--budgets"' in source
    assert "for budget in budgets" in source
    assert "selection_key(summary" in source
    assert 'for family in ("esn", "vmc")' in source
