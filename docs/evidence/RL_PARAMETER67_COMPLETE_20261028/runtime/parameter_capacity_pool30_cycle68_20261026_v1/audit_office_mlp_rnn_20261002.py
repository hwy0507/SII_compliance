"""Independent paired-data, learned recurrence and deployment replay audit."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    a = p.parse_args()
    run = a.root.resolve()
    physics = json.loads((run/'FINAL_PHYSICS_AUDIT.json').read_text())
    assert len(physics['rows']) == 8 and not physics['pending']
    by_name = {Path(row['run']).name: row for row in physics['rows']}
    rows, pairs, lineage_checks = [], [], []
    for dataset in ('original', 'recovery41'):
        data = run/'data'/dataset/'training_data.npz'
        metadata = json.loads((run/'data'/dataset/'TRAINING_COMPLETE.json').read_text())
        for source in metadata['lineage']:
            path = Path(source['path'])
            assert sha(path) == source['sha256']
            original = json.loads(path.with_suffix('.json').read_text())
            assert original['task_success'] == source['task_success']
            assert original['strict_success'] == source['strict_success']
            lineage_checks.append(dict(dataset=dataset, **source, trace_and_failure_label_verified=True))
        with np.load(data) as z:
            obs, target, episode, train = [z[k].copy() for k in
                                          ('observation', 'filtered_teacher_action', 'episode', 'train')]
        assert not set(episode[train]).intersection(episode[~train])
        sequence = [np.flatnonzero(episode == ep) for ep in np.unique(episode)]
        fields = np.asarray(list(range(39, 45)) if dataset == 'original' else
                            [*range(14, 17), *range(20, 23), *range(26, 29), *range(39, 48)])
        expected_scale = np.maximum(obs[train][:, fields].std(0), .005)
        for seed in (2026100201, 2026100202):
            pair = []
            for kind in ('mlp', 'rnn'):
                name = f'{dataset}_{kind}_{seed}'
                training = run/('train_'+name)
                receipt = json.loads((training/'TRAINING_COMPLETE.json').read_text())
                state = json.loads((training/'execution.json').read_text())
                assert state['status'] == 'complete'
                assert receipt['seed'] == seed and receipt['kind'] == kind and receipt['updates'] == 2400
                assert receipt['data_sha256'] == sha(data)
                assert receipt['checkpoint_sha256'] == sha(training/'checkpoint.npz') == by_name[name]['checkpoint_sha256']
                assert receipt['schedule_sha256'] == sha(training/'schedule.json')
                assert receipt['metadata_sha256'] == sha(run/'data'/dataset/'TRAINING_COMPLETE.json')
                assert receipt['exported_replay_sha256'] == sha(training/'exported_replay.npz')
                for rel, digest in receipt['source_sha256'].items():
                    assert sha(run/'evaluations/source'/rel) == digest
                with np.load(training/'checkpoint.npz') as z:
                    np.testing.assert_array_equal(z['fields'], fields)
                    np.testing.assert_array_equal(z['scale'], expected_scale)
                    iw, ow = z['input_w'].astype(float), z['output_w'].astype(float)
                    rw = z['recurrent_w'].astype(float) if kind == 'rnn' else None
                with np.load(training/'exported_replay.npz') as z:
                    stored = z['prediction'].copy()
                    np.testing.assert_array_equal(z['episode'], episode)
                prediction = np.empty_like(stored)
                for ids in sequence:
                    hidden = np.zeros(128)
                    for i in ids:
                        features = np.clip(obs[i, fields]/expected_scale, -12, 12)
                        hidden = np.tanh(iw@features + (rw@hidden if rw is not None else 0.))
                        raw = ow@hidden
                        prediction[i] = np.r_[np.clip(raw[0], 0, 1), np.tanh(raw[1:])]
                replay_error = float(np.max(abs(prediction-stored)))
                assert replay_error <= 1e-12
                change = None
                if rw is not None:
                    q, _ = np.linalg.qr(np.random.default_rng(seed+1000).normal(size=(128, 128)))
                    change = float(np.linalg.norm(rw-(.8*q).astype(np.float32)))
                    assert change > 1e-6, 'Recurrent weights must actually be learned'
                row = dict(name=name, dataset=dataset, kind=kind, seed=seed,
                           parameter_count=receipt['trainable_parameters'], selected_update=receipt['selected_update'],
                           independent_export_replay_max_abs=replay_error, learned_recurrent_weight_change_frobenius=change,
                           groups=receipt['groups'], numpy_torch_max_abs=receipt['numpy_torch_max_abs'],
                           fields=fields.tolist(), training_source_verified=True, physics=by_name[name])
                rows.append(row)
                pair.append(receipt)
            for key in ('data_sha256', 'metadata_sha256', 'schedule_sha256', 'updates', 'fields', 'batch_size', 'tbptt_steps', 'action_delta_weight'):
                assert pair[0][key] == pair[1][key], key
            pairs.append(dict(dataset=dataset, seed=seed, identical_training_exposure=True,
                              data_sha256=pair[0]['data_sha256'], schedule_sha256=pair[0]['schedule_sha256']))
    result = dict(created_utc=now(), rows=rows, pairs=pairs, source_trace_lineage=lineage_checks,
                  argv=sys.argv, source_sha256=sha(Path(__file__)), numpy_version=np.__version__,
                  physics_audit_sha256=sha(run/'FINAL_PHYSICS_AUDIT.json'),
                  status='complete', limitation='Two training seeds on one seen development world; no generalized success estimate. Same width, unequal trainable parameters. Offline holdout is synthetic identity holdout.')
    write(run/'PAIRED_MODEL_AUDIT.json', result)
    print(json.dumps(dict(models=len(rows), pairs=len(pairs), task=sum(r['physics']['task_success'] for r in rows),
                          strict=sum(r['physics']['strict_success'] for r in rows))))


if __name__ == '__main__':
    main()
