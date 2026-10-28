"""Verify paired learning comparisons share data and their declared budget."""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now

PAIRS = [
    ('esn_coupled_signed', 'esn_coupled_abs', 'absolute_load_drive'),
    ('esn_recovery_fast', 'esn_recovery_long', 'reservoir_time_scales'),
    ('esn_progress44_fixed', 'esn_progress44_gated', 'contextual_leak'),
    ('esn_final47_fixed', 'esn_final47_gated', 'contextual_leak'),
    ('esn_dagger_base', 'esn_dagger_drift', 'integrated_action_loss_and_checkpoint_selection'),
]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    a = p.parse_args()
    rows = []
    for left, right, difference in PAIRS:
        one, two = a.root/left, a.root/right
        m1, m2 = [json.loads((d/'TRAINING_COMPLETE.json').read_text()) for d in (one, two)]
        for key in ('seed', 'updates', 'real_weight', 'delta_weight', 'config_sha256', 'lineage'):
            if m1[key] != m2[key]:
                raise ValueError(f'Unmatched {key}: {left}/{right}')
        fields = ('observation', 'episode', 'train', 'requested_teacher_action',
                  'filtered_teacher_action', 'importance')
        with np.load(one/'training_data.npz') as z1, np.load(two/'training_data.npz') as z2:
            for key in fields:
                np.testing.assert_array_equal(z1[key], z2[key])
            samples = len(z1['episode'])
            train_ids, holdout_ids = set(z1['episode'][z1['train']]), set(z1['episode'][~z1['train']])
            assert not train_ids.intersection(holdout_ids)
        with np.load(one/'checkpoint.npz') as z1, np.load(two/'checkpoint.npz') as z2:
            np.testing.assert_array_equal(z1['w'], z2['w'])
            np.testing.assert_array_equal(z1['win'][:, :6], z2['win'][:, :6])
            if difference != 'absolute_load_drive':
                np.testing.assert_array_equal(z1['win'], z2['win'])
            if difference != 'reservoir_time_scales':
                np.testing.assert_array_equal(z1['leak'], z2['leak'])
        rows.append(dict(left=left, right=right, deliberate_difference=difference, samples=samples,
                         identical_data_fields=list(fields), identities_disjoint=True,
                         seed=m1['seed'], updates=m1['updates'],
                         checkpoint_sha256=[sha(d/'checkpoint.npz') for d in (one, two)]))
    write(a.root/'PAIRED_LEARNING_AUDIT.json', dict(created_utc=now(), pairs=rows,
          source_sha256=sha(Path(__file__)),
          limitation='Within-ESN matched data/budget; architectural parameter counts and compute are not identical. Synthetic identity holdout is not physical generalization.'))
    print(json.dumps(dict(pairs_verified=len(rows))))


if __name__ == '__main__':
    main()
