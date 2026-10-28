"""Audit metadata/checkpoint identities of the six unchanged neural references.

No rollout, fitting, checkpoint selection, or sealed conditions are read. This
records training differences needed to interpret the forthcoming system table.
Lineage is metadata, not an independent re-audit of every old physical trace.
"""
import argparse
from collections import Counter
from pathlib import Path
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    registry = a.root/'REFERENCE_MODELS.json'
    assert sha(registry) == read(a.root/'PROTOCOL.json')['reference_models_sha256']
    candidates = [c for c in read(registry)['candidates'] if c.get('checkpoint')]
    assert len(candidates) == 6
    rows = []
    keys = ('contract', 'network_kind', 'axis_separable', 'absolute_inputs', 'context_inputs',
            'position_context', 'reset_at_each_observation', 'readout_activation',
            'output_gain', 'readout_order', 'state_delta_readout')
    numeric_keys = ('win', 'w', 'weights', 'leak', 'scale', 'context_gate_w', 'state_context_readout_w')
    for c in candidates:
        cp = Path(c['checkpoint'])
        meta_path = cp.parent/'TRAINING_COMPLETE.json'
        assert sha(cp) == c['checkpoint_sha256']
        assert sha(meta_path) == c['training_metadata_sha256']
        m = read(meta_path)
        assert m['checkpoint_sha256'] == c['checkpoint_sha256']
        data_key = 'training_data_sha256' if 'training_data_sha256' in m else 'data_sha256'
        assert m[data_key] == c['training_data_sha256']
        with np.load(cp, allow_pickle=False) as z:
            flags = {k:z[k].item() for k in keys if k in z}
            shapes = {k:list(z[k].shape) for k in numeric_keys if k in z}
            assert all(np.isfinite(z[k]).all() for k in numeric_keys if k in z)
            stored_numeric_scalars = sum(z[k].size for k in numeric_keys if k in z)
        lineage = m['lineage']
        assert len({r['path'] for r in lineage}) == len(lineage)
        rows.append(dict(family=c['family'], checkpoint=str(cp), checkpoint_sha256=sha(cp),
            metadata=str(meta_path), metadata_sha256=sha(meta_path),
            training_data_sha256=c['training_data_sha256'], metadata_data_key=data_key,
            flags=flags, shapes=shapes,
            stored_selected_numeric_scalars=int(stored_numeric_scalars),
            declared_training_details={k:v for k,v in m.items() if k not in (
                'lineage','source_sha256','candidates','candidates_tested','ridge_candidates')},
            declared_lineage_role_counts=dict(Counter(r['data_role'] for r in lineage)),
            declared_lineage=[{k:r.get(k) for k in ('condition_id','data_role','path','sha256',
                'actual_execution_labels','synthetic','task_success','strict_success')} for r in lineage]))
    groups = {}
    for r in rows: groups.setdefault(r['training_data_sha256'], []).append(r['family'])
    write(a.output, dict(created_utc=now(), source_sha256=sha(__file__),
        registry_sha256=sha(registry), rows=rows, actual_selected_dataset_groups=groups,
        all_six_selected_models_use_same_dataset=len(groups) == 1,
        note='Checkpoint and training metadata hashes verified against registered references. '
        'Stored scalar count is neither trainable parameter count nor FLOPs. Training details are archived declarations; '
        'raw historical physical trajectories not independently re-audited here. All selected references stay unchanged. '
        'Different selected training sets and refinement histories preclude calling this an isolated architecture ablation.'))
    print({digest:families for digest,families in groups.items()}, flush=True)


if __name__ == '__main__':
    main()
