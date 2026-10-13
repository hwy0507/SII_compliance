"""Bounded frozen-ESN check of a new common continuous reference adapter."""
from pathlib import Path
import sys
import numpy as np
import run_old_office_reference_fix_20261013 as prior
from continuous_old_office_reference_20261013 import ContinuousCarryReference


class RecordedReference(ContinuousCarryReference):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        prior.instances.append(self)


def audit(run, config, checkpoint, memory_ablation):
    row = prior.audit(run, config, checkpoint, memory_ablation)
    ref = prior.instances[0]
    trace = np.asarray(ref.progress_records)
    delta = np.diff(np.r_[0., trace[:, 0]])
    assert np.all(delta >= -1e-12) and np.all(delta <= .06*.04+1e-12)
    np.testing.assert_allclose(trace[:, 2:], delta[:, None]/.04*ref.tangent, atol=1e-12)
    row.update(changed_component='common carry reference position and feedforward together',
               reference_progress_and_feedforward_audited=True)
    prior.worker.write(run/'AUDIT.json', row)
    return row


def main():
    worker = prior.worker
    original_main = worker.main
    def configured_main():
        worker.evaluator.PickPlaceTask = RecordedReference
        worker.AUDIT_FUNCTION = audit
        worker.EXTRA_SOURCE_FILES += [Path(__file__), Path(prior.__file__),
            Path(__file__).with_name('continuous_old_office_reference_20261013.py'),
            Path(__file__).with_name('old_office_waypoint_reference_20261013.py')]
        worker.RUNTIME_PROVENANCE.update(
            purpose='Frozen original ESN; single registered common continuous-reference check',
            changed_component='Common pose-governed carry reference and consistent feedforward',
            reference_rule='60mm/s nominal,12mm lead,80mm lateral and0.12rad orientation bounds from existing task settings',
            no_checkpoint_or_scaling_changes=True,
            prior_run='original_esn_reference_fix_20261013_v2/episode')
        try:
            original_main()
        finally:
            output = Path(sys.argv[sys.argv.index('--output')+1])
            if output.exists() and prior.instances:
                worker.write(output/'reference.json', prior.instances[0].metadata())
    worker.main = configured_main
    prior.transfer.main()


if __name__ == '__main__':
    main()
