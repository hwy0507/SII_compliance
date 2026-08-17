"""Static DAgger contract checks: privileged truth stays label-side only."""

from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_direct_esn_dagger.py"


def test_dagger_rollout_labels_student_visited_states_offline():
    source = SCRIPT.read_text()
    assert "collect_student_visited_archive" in source
    assert "build_privileged_teacher_trace" in source
    assert "teacher_action" in source
    assert "contact_force" in source
    assert "forbidden_online_inputs" in source
    assert "controller.act(" in source
    assert "--rod-repeat" in source
    assert "--teacher-mode" in source
    assert "select_counterfactual_action" in source


def test_counterfactual_teacher_is_explicitly_label_side_only():
    source = (SCRIPT.parent / "counterfactual_direct_esn_teacher.py").read_text()
    assert "training-only" in source
    assert "cloned MjData" in source
    assert "contact/impactor truth" in source
    assert "candidate_actions" in source
