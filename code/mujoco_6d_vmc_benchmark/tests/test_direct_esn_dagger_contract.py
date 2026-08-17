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

