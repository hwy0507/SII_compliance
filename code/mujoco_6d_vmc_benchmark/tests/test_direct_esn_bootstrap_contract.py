"""Static contract checks for reservoir-seed Direct ESN bootstrap."""

from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_direct_esn_multifixture.py"


def test_bootstrap_keeps_direct_esn_period_and_distinct_reservoir_seed():
    source = SCRIPT.read_text()
    assert "--reservoir-seed" in source
    assert "dt_s=0.04" in source
    assert '("phase_teacher_rod", args.base_rod_trace, 10' in source
    assert '("phase_teacher_no_rod", args.base_no_rod_trace, 1' in source
    assert "DirectESNController(config)" in source
    assert "--expert-traces" in source
    assert "--no-rod-expert-trace" in source
    assert '"bounded_action"' in source
