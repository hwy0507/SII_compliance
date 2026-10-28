"""Run the offset-only teacher on an unchanged copied office evaluator."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]

import baseline_repair_worker_20261008 as baseline
import intent_equilibrium_teacher_20261029 as extension


def main():
    worker = baseline.office.worker
    assert worker.ParameterTeacher is extension.LegacyParameterTeacher
    assert Path(worker.__file__).resolve().parent == ROOT/'tools'
    worker.ParameterTeacher = extension.IntentEquilibriumTeacher
    original_settings, original_main = baseline.office.evaluation_settings, worker.main
    sources = [Path(extension.__file__).resolve(), Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)):worker.sha(p) for p in sources}

    def settings(*args, **kwargs):
        model, overrides, provenance = original_settings(*args, **kwargs)
        provenance.update(teacher_mechanism=extension.VERSION,
                          teacher_extension_sources=hashes,
                          teacher_extension_inputs='canonical48 only; scale equilibrium offset, preserve original feedback and memory')
        return model, overrides, provenance

    def instrumented_main():
        worker.EXTRA_SOURCE_FILES = list(worker.EXTRA_SOURCE_FILES)+sources
        assert all(worker.sha(ROOT/name)==digest for name,digest in hashes.items())
        return original_main()

    baseline.office.evaluation_settings = settings
    worker.main = instrumented_main
    try:
        baseline.main()
    finally:
        assert all(worker.sha(ROOT/name)==digest for name,digest in hashes.items())


if __name__ == '__main__':
    main()
