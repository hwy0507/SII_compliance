"""Explicit role-aware condition wrapper around unchanged archived-v6 workers.

No new actor inputs, scene geometry, task gates or filter settings are added.
Final sealed evaluation is deliberately not supported by this development worker.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import paper_office_worker_20261002 as office
from research72_protocol_20261003 import FIELDS, LOW, HIGH


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--research-protocol', type=Path, required=True)
    p.add_argument('--protocol-sha256', required=True)
    p.add_argument('--research-condition', required=True)
    p.add_argument('--worker-kind', choices=('office','classical','rl'), default='office')
    a, rest = p.parse_known_args()
    protocol = json.loads(a.research_protocol.read_text())
    assert office.worker.sha(a.research_protocol) == a.protocol_sha256
    assert protocol['schema'] == 'sii-research72-v1'
    path = a.research_protocol.parent/'CONDITIONS.json'
    assert office.worker.sha(path) == protocol['condition_file_sha256']
    condition = next(c for c in json.loads(path.read_text())['conditions'] if c['id'] == a.research_condition)
    assert condition['role'] in ('train','imitation_validation','development')
    values = condition['overrides']
    assert set(values) == set(FIELDS)
    assert all(lo <= values[k] <= hi for k, lo, hi in zip(FIELDS,LOW,HIGH))
    assert values['rod_start'] >= values['person_start'] + 8.
    original = office.evaluation_settings
    def settings(v6, dt, condition_file=None, condition_id=None):
        assert condition_file is None and condition_id is None
        assert dt == protocol['physics_dt_s']
        expected, overrides, provenance = original(v6, dt)
        assert expected == protocol['formal_model_sha256']
        overrides.update(values)
        provenance.update(condition_id=condition['id'], data_role=condition['role'],
            research_protocol_sha256=a.protocol_sha256, research_condition=condition,
            condition_file_sha256=office.worker.sha(path),
            condition_wrapper_sha256=office.worker.sha(Path(__file__)),
            use='New predeclared training/development identity, never a blinded final test')
        return expected, overrides, provenance
    office.evaluation_settings = settings
    output = Path(rest[rest.index('--output')+1]).resolve()
    if a.worker_kind == 'classical':
        import paper_classical_worker_20261002 as selected
    elif a.worker_kind == 'rl':
        import paper_rl_worker_20261002 as selected
    else:
        selected = office
    sys.argv = [sys.argv[0], *rest]
    try:
        selected.main()
    finally:
        if output.exists():
            office.worker.write(output/'RESEARCH_ROLE.json', dict(protocol_sha256=a.protocol_sha256,
                condition=condition, worker_kind=a.worker_kind,
                wrapper_source_sha256=office.worker.sha(Path(__file__)),
                sampler_source_sha256=office.worker.sha(Path(__file__).with_name('research72_protocol_20261003.py'))))
            (output/'research72_worker.py.txt').write_text(Path(__file__).read_text())


if __name__ == '__main__':
    main()
