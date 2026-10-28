"""Read-only real-trace regression: additive v4 metrics, unchanged legacy fields.

Accepts explicit public runs only; never discovers or opens sealed conditions.
"""
import argparse
import importlib.util
import json
from pathlib import Path
from paper_metrics_20261002 import measure, sha, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--old-source', type=Path, required=True)
    p.add_argument('--run', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    spec = importlib.util.spec_from_file_location('legacy_metric_regression', a.old_source)
    legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
    a.output.mkdir(parents=True)
    rows = []
    for index, run in enumerate(a.run):
        old = legacy.measure(run); new = measure(run)
        changed = [key for key in old if key not in ('created_utc', 'metric_version', 'metric_source_sha256')
                   and old[key] != new[key]]
        if changed:
            raise AssertionError(dict(run=str(run), changed_legacy_fields=changed))
        path = a.output/f'{index:03d}.metrics.json'
        path.write_text(json.dumps(new, indent=2, allow_nan=False)+'\n')
        rows.append(dict(run=str(run.resolve()), metrics=str(path), metrics_sha256=sha(path),
            trace_sha256=new['trace_sha256'], legacy_fields_exact=True,
            task_success=new['task_success'], strict_success=new['strict_success'],
            human_event_integral_ns=new['contact']['human']['impulse_ns'],
            human_whole_integral_ns=new['supplemental_contact']['whole_observed_horizon']['human']['impulse_ns'],
            human_outside_integral_ns=new['supplemental_contact']['outside_event_window']['human']['impulse_ns'],
            human_outside_duration_s=new['supplemental_contact']['outside_event_window']['human']['contact_duration_s']))
    result = dict(created_utc=now(), source_sha256=sha(Path(__file__)),
        legacy_source_sha256=sha(a.old_source), new_metric_source_sha256=sha(Path(measure.__code__.co_filename)),
        rows=rows, new_physics_episodes=0, new_fits=0,
        note='Public diagnostic cohort, not final model selection or heldout evaluation; all old numerical and outcome fields exactly unchanged.')
    (a.output/'REGRESSION.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
