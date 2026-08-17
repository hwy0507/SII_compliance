"""Static contract checks for the MuJoCo Direct ESN mode."""

from pathlib import Path


ENV_PATH = Path(__file__).resolve().parents[1] / "scripts" / "wbc_velocity_residual_env.py"


def test_direct_mode_is_explicit_and_bypasses_legacy_policy_layers():
    source = ENV_PATH.read_text()
    assert '"direct_esn"' in source
    assert "Direct ESN is the primary collision-response policy" in source
    assert "phase_projected_action = raw_policy_action.copy()" in source
    assert "current_authority_gate = 1.0" in source

