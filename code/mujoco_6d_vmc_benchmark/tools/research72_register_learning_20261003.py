"""Verify all completed fits and register every model on common development IDs.

Run after copying a completed local fitting directory to its immutable server
location. This records the archive mapping without changing historical paths.
No simulation outcome or final heldout identity is read.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--learning', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--amendment', type=Path)
    a = p.parse_args()
    root, learning = a.root.resolve(), a.learning.resolve()
    state = read(learning/'execution.json')
    spec = read(learning/'SPECIFICATION.json')
    protocol_sha = sha(root/'PROTOCOL.json')
    assert state['status'] == 'complete'
    assert state['specification_sha256'] == sha(learning/'SPECIFICATION.json')
    assert spec['protocol_sha256'] == protocol_sha
    gated=spec.get('stage')=='contextual_gate_extension'
    if gated:
        assert a.amendment and sha(a.amendment)==spec['amendment_sha256']
        amendment=read(a.amendment)
        assert amendment['protocol_sha256']==protocol_sha and amendment['new_learning_cap_per_family_seed']==48
    expected=21 if gated else 33
    assert len(state['rows']) == len(spec['jobs']) == expected
    assert {r['name'] for r in state['rows']} == {j['name'] for j in spec['jobs']}
    assert all(sha(learning/'source'/k) == h
               for k, h in read(learning/'SOURCE_HASHES.json').items())
    candidates = []
    for row in state['rows']:
        assert row['returncode'] == 0
        cp = learning/row['name']/'checkpoint.npz'
        metadata_path = cp.parent/'TRAINING_COMPLETE.json'
        assert sha(cp) == row['checkpoint_sha256']
        assert sha(metadata_path) == row['training_metadata_sha256']
        metadata = read(metadata_path)
        assert metadata.get('training_data_sha256', metadata.get('data_sha256')) == spec['data_sha256']
        assert all(x['data_role'] in ('train', 'imitation_validation')
                   and x['actual_execution_labels'] for x in metadata['lineage'])
        job = next(j for j in spec['jobs'] if j['name'] == row['name'])
        candidates.append(dict(name=row['name'], category=row['family'],
            seed=job['seed'], variant=job['variant'], checkpoint=str(cp),
            checkpoint_sha256=sha(cp), training_metadata_sha256=sha(metadata_path), config={}))
    conditions = [c['id'] for c in read(root/'CONDITIONS.json')['conditions']
                  if c['role'] == 'development']
    assert len(conditions) == 8
    result = dict(registered_utc=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=protocol_sha, source_sha256=sha(Path(__file__)),
        fitting_spec_sha256=sha(learning/'SPECIFICATION.json'),
        fitting_execution_sha256=sha(learning/'execution.json'),
        data_sha256=spec['data_sha256'], conditions=conditions, candidates=candidates,
        episodes=len(candidates)*len(conditions), selection=f'All {expected} completed models; no replay-MSE success eligibility filter.',
        purpose='Paired development evaluation, not final heldout evidence.',
        fit_origin='Local airpig; original execution paths retained unchanged.',
        archived_learning_directory=str(learning),
        variant_selection='Within each family use summed strict, then task, then full horizons across all three seeds; break ties by worst penetration, mean RMSE, mean actual peak torque, lexical variant. Retain every seed for the chosen variant, never choose a lucky seed.',
        contact_reporting='Report exposure alongside force and recovery; absent contact is NA, not zero.')
    if gated:result['amendment_sha256']=sha(a.amendment)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(models=len(candidates), episodes=result['episodes'], sha256=sha(a.output))))


if __name__ == '__main__':
    main()
