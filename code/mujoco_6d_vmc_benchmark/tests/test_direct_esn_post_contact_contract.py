"""Static checks for the matched post-contact Direct ESN benchmark."""

from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "evaluate_direct_esn_post_contact.py"
RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_direct_esn_mujoco.py"


def test_post_contact_benchmark_separates_impulse_and_rejoin_metrics():
    source = SCRIPT.read_text()
    assert "contact_onset_s" in source
    assert "contact_release_s" in source
    assert "post_contact_rmse_mm" in source
    assert "release_to_rejoin_latency_s" in source
    assert "scheduled_release_to_rejoin_latency_s" in source
    assert "fixed_wbc" in source
    assert "direct_esn" in source


def test_contact_diagnostics_are_trace_only():
    source = RUNNER.read_text()
    assert '"contact_force": float(env.last_action_contact_force)' in source
    assert '"contact_impulse_delta_ns": float(env.contact_impulse - impulse_before)' in source
    assert "never passed to the Direct ESN observation" in source
