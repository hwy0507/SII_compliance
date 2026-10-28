"""Run the historical parameter teacher with complete wrapper provenance."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
import baseline_repair_worker_20261008 as baseline


def main():
    worker=baseline.office.worker
    assert Path(worker.__file__).resolve().parent==ROOT/'tools'
    original_settings,original_main=baseline.office.evaluation_settings,worker.main
    sources=[Path(__file__).resolve(),Path(baseline.__file__).resolve()]
    hashes={str(p.relative_to(ROOT)):worker.sha(p) for p in sources}

    def settings(*args,**kwargs):
        model,overrides,provenance=original_settings(*args,**kwargs)
        provenance.update(teacher_mechanism='legacy_parameter_teacher_v1',
            teacher_extension_sources=hashes,
            teacher_extension_inputs='Original canonical48 ParameterTeacher; no new actor inputs or class replacement')
        return model,overrides,provenance

    def instrumented_main():
        worker.EXTRA_SOURCE_FILES=list(worker.EXTRA_SOURCE_FILES)+sources
        assert all(worker.sha(ROOT/n)==h for n,h in hashes.items())
        return original_main()

    baseline.office.evaluation_settings=settings
    worker.main=instrumented_main
    try:baseline.main()
    finally:
        assert all(worker.sha(ROOT/n)==h for n,h in hashes.items())


if __name__=='__main__':main()
