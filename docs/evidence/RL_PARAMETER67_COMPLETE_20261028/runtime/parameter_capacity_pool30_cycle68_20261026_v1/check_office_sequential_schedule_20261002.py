"""Bounded schedule regression: two 80ms probes, never a task evaluation."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import mujoco
import numpy as np
import validate_office_apparatus_v5_20260917 as evaluator


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    config_path = ROOT / 'configs/office_combined_v4_sequential_r12_20261002.json'
    config = json.loads(config_path.read_text())
    reference = ROOT / 'outputs/temporal_s52_latent_dropout_20261001_v1/p010_eval/esn_combined_v4.json'
    old = json.loads(reference.read_text())['arguments']
    old['esn_model'] = ROOT / 'outputs/temporal_s52_latent_dropout_20261001_v1/p010_eval/esn_temporal.npz'
    old['render'] = False
    old['physics_probe_s'] = .08
    new = dict(old, rod_start=12., interaction_schedule='sequential-r12-v1')
    cgroup = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory_max = (cgroup / 'memory.max').read_text().strip()
    assert memory_max != 'max' and int(memory_max) <= 3 * 1024**3
    assert mujoco.__version__ == config['runtime']['mujoco']
    record = dict(status='running', purpose=__doc__, argv=sys.argv,
                  runtime=mujoco.__version__, memory_max=memory_max,
                  threads={k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')},
                  config_sha256=sha(config_path), reference_sha256=sha(reference),
                  checkpoint_sha256=sha(old['esn_model']),
                  source_sha256={str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), Path(evaluator.__file__))})
    execution = args.output / 'execution.json'
    execution.write_text(json.dumps(record, indent=2))
    try:
        schedule = evaluator.interaction_schedule(SimpleNamespace(**new))
        assert schedule['person']['start'] + sum(schedule['person'][k] for k in ('press', 'hold', 'retract')) == 10.
        assert schedule['rod']['start'] == 12.
        for t in np.linspace(0, 55, 55001):
            levels = [evaluator.smooth_profile(t, **{k: s[k] for k in ('start', 'press', 'hold', 'retract')}) for s in schedule.values()]
            assert not (levels[0] > 0 and levels[1] > 0)
        for field, value in (('rod_start', 7.), ('person_start', 4.), ('rod_hold', 3.)):
            bad = dict(new, **{field: value})
            try:
                evaluator.interaction_schedule(SimpleNamespace(**bad))
            except ValueError:
                pass
            else:
                raise AssertionError(f'Stale {field} not rejected')
        outcomes = {}
        for label, values in (('legacy', old), ('sequential', new)):
            values['output'] = args.output / label
            with (args.output / f'{label}.log').open('w') as log, contextlib.redirect_stdout(log):
                evaluator.run(SimpleNamespace(**values))
            result = json.loads(values['output'].with_suffix('.json').read_text())
            assert result['model_sha256'] == config['development_mjb_sha256']
            assert not result['task_success'] and not result['strict_success']
            assert not result['full_task_horizon_completed']
            assert result['abort_reason'] is None
            outcomes[label] = dict(schedule=result['schedule'], model_sha256=result['model_sha256'],
                                   task_success=result['task_success'], strict_success=result['strict_success'])
        with np.load(args.output / 'legacy.npz') as a, np.load(args.output / 'sequential.npz') as b:
            assert a.files == b.files
            for key in a.files:
                np.testing.assert_array_equal(a[key], b[key], err_msg=key)
        assert sha(old['esn_model']) == record['checkpoint_sha256']
        record.update(status='complete', outcomes=outcomes, all_pre_event_arrays_equal=True,
                      commanded_overlap=False, stale_overrides_rejected=True,
                      limitations='80ms prefix only; no contact separation or 55s task outcome has been evaluated')
    except BaseException as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        record['artifacts_sha256'] = {p.name: sha(p) for p in args.output.iterdir() if p.is_file() and p != execution}
        execution.write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
