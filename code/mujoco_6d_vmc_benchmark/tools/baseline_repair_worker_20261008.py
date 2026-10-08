"""Role-aware repaired-baseline campaign worker on the unchanged office MJB."""
import argparse
import json
from pathlib import Path
import sys
import paper_office_worker_20261002 as office


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--research-protocol', type=Path, required=True)
    p.add_argument('--protocol-sha256', required=True)
    p.add_argument('--research-condition', required=True)
    p.add_argument('--phase', choices=('train', 'development', 'acceptance', 'final'), required=True)
    p.add_argument('--worker-kind', choices=('office', 'classical', 'online', 'adapted_rl', 'nominal'), default='office')
    a, rest = p.parse_known_args()
    root = a.research_protocol.parent
    protocol = json.loads(a.research_protocol.read_text())
    assert office.worker.sha(a.research_protocol) == a.protocol_sha256
    assert protocol['schema'] == 'sii-baseline-repair-15h-v1'
    path = root/('sealed/HELDOUT.json' if a.phase == 'final' else 'CONDITIONS.json')
    key = 'sealed_condition_sha256' if a.phase == 'final' else 'condition_file_sha256'
    assert office.worker.sha(path) == protocol[key]
    if a.phase == 'final':
        lock = json.loads((root/'FINAL_MODEL_LOCK.json').read_text())
        assert lock['protocol_sha256'] == a.protocol_sha256 and lock['status'] == 'frozen'
    condition = next(c for c in json.loads(path.read_text())['conditions'] if c['id'] == a.research_condition)
    assert condition['role'] == a.phase
    assert (a.worker_kind == 'online') == (a.phase == 'train')
    original = office.evaluation_settings

    def settings(v6, dt, condition_file=None, condition_id=None):
        assert condition_file is None and condition_id is None
        assert dt == protocol['physics_dt_s']
        model, overrides, provenance = original(v6, dt)
        assert model == protocol['formal_model_sha256']
        overrides.update(condition['overrides'])
        if a.phase == 'acceptance' and overrides.get('events') == 'none':
            # Registration v1 used an unsupported name for the existing
            # disturbance-off mode. Both disable identical physical drives;
            # only 'settle' is recognized by the evaluator's final reducer.
            overrides['events'] = 'settle'
            provenance['acceptance_event_name_correction'] = 'none -> existing settle mode; original failed attempts retained'
        assert overrides.get('events', 'all') in ('settle', 'ball', 'person', 'rod', 'all')
        provenance.update(condition_id=condition['id'], data_role=condition['role'],
            research_protocol_sha256=a.protocol_sha256, research_condition=condition,
            condition_file_sha256=office.worker.sha(path),
            condition_wrapper_sha256=office.worker.sha(Path(__file__)),
            use='Independent repaired-baseline campaign; frozen geometry/gates, explicit data role')
        return model, overrides, provenance

    office.evaluation_settings = settings
    modules = dict(office='paper_office_worker_20261002', classical='paper_classical_worker_20261002',
                   online='baseline_repair_online_worker_20261008', adapted_rl='research72_adapted_rl_worker_20261003',
                   nominal='research72_nominal_worker_20261003')
    import importlib
    selected = importlib.import_module(modules[a.worker_kind])
    out = Path(rest[rest.index('--output')+1])
    sys.argv = [sys.argv[0], *rest]
    try:
        selected.main()
    finally:
        if out.exists():
            office.worker.write(out/'REPAIR_ROLE.json', dict(protocol_sha256=a.protocol_sha256,
                condition=condition, worker_kind=a.worker_kind, wrapper_sha256=office.worker.sha(Path(__file__))))


if __name__ == '__main__':
    main()
