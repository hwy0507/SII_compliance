"""Run the versioned teacher on a copied, hash-locked office evaluator.

This entrypoint must live alongside a complete immutable copy of the prior
office scripts/tools. It changes only the actor class reference; the original
worker still checks the exact MJB, role, physics step, filter and task gates.
The new actor and this driver are added to the worker's source overlay.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]

import baseline_repair_worker_20261008 as baseline
import intent_recovery_teacher_20261029 as extension


def main():
    worker = baseline.office.worker
    assert worker.ParameterTeacher is extension.LegacyParameterTeacher
    assert Path(worker.__file__).resolve().parent == ROOT/'tools'
    worker.ParameterTeacher = extension.IntentScaledRecoveryTeacher
    original_settings = baseline.office.evaluation_settings
    original_main = worker.main
    sources = [Path(extension.__file__).resolve(), Path(__file__).resolve()]
    hashes = {str(p.relative_to(ROOT)):worker.sha(p) for p in sources}

    def settings(*args, **kwargs):
        model, overrides, provenance = original_settings(*args, **kwargs)
        provenance.update(teacher_mechanism=extension.VERSION,
                          teacher_extension_sources=hashes,
                          teacher_extension_inputs='canonical48 command/path/pose plus inherited causal wrench memory; no task stage or oracle')
        return model, overrides, provenance

    def instrumented_main():
        # paper_office_worker has initialized EXTRA_SOURCE_FILES by now.
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
