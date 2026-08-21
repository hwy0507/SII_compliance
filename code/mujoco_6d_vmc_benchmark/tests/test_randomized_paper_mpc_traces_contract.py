"""Static contracts for train-only randomized Paper-MPC trace generation."""

from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "record_randomized_paper_mpc_traces.py"


def test_randomized_trace_generator_has_disjoint_seed_and_manifest_contract() -> None:
    source = SCRIPT.read_text()

    assert '"--count"' in source
    assert '"--seed"' in source
    assert '"--stroke-jitter-m"' in source
    assert '"--height-jitter-m"' in source
    assert '"--start-jitter-s"' in source
    assert '"manifest": str(manifest_path)' in source
    assert '"kind": "board"' in source
    assert '"kind": "no_rod"' in source
