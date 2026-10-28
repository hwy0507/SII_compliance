"""Verify an existing same-data, three-seed neural cohort before reevaluation.

No fitting, physics, or access to final outcomes. Local cache and server storage
are recorded separately. A local result alone never certifies a remote copy.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np
from office_v7_uniform24_20261008 import sha, write, now


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--learning',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--metadata',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
    from office_context_network_20261003 import OfficeContextNetwork
    from office_mlp_rnn_20261002 import OfficeMLPRNN
    from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
    meta=json.loads(args.metadata.read_text());data_hash=sha(args.data)
    assert data_hash==meta['training_data_sha256'] and meta['all_real_execution']
    with np.load(args.data,allow_pickle=False) as data:
        ep=data['episode']; train=data['train'].astype(bool); obs=data['observation']
        assert obs.shape[1]==48 and len(ep)==len(train)==len(obs)
        assert np.isfinite(obs).all()
        train_ids=set(ep[train]);val_ids=set(ep[~train])
        assert len(train_ids)==20 and len(val_ids)==5 and not train_ids.intersection(val_ids)
        assert all(len(set(train[ep==e]))==1 for e in np.unique(ep))
        probe=obs[np.linspace(0,len(obs)-1,96,dtype=int)].copy()
    allowed=set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48))
    unused=sorted(set(range(48))-allowed)
    changed=probe.copy();changed[:,unused]=np.random.default_rng(9001).normal(0,100,(len(probe),len(unused)))
    rows=[];gradient_schedule={}
    for seed in (2026100301,2026100302,2026100303):
        for family in ('esn','memoryless','matched_mlp','matched_rnn','ordinary_mlp','ordinary_rnn'):
            directory=args.learning/f'readout_refit_{family}_{seed}'
            metadata=directory/'TRAINING_COMPLETE.json'; checkpoint=directory/'checkpoint.npz'
            detail=json.loads(metadata.read_text())
            assert detail.get('training_data_sha256',detail.get('data_sha256'))==data_hash
            assert detail['checkpoint_sha256']==sha(checkpoint)
            assert detail['seed']==seed
            assert Counter(r['data_role'] for r in detail['lineage'])==Counter(train=20,imitation_validation=5)
            expected={(r['condition_id'],r['sha256'],r['data_role']) for r in meta['lineage']}
            actual={(r['condition_id'],r['sha256'],r['data_role']) for r in detail['lineage']}
            assert actual==expected, 'Different physical teacher identities'
            cls=OfficeContextNetwork if family.startswith('matched_') else OfficeMLPRNN if family.startswith('ordinary_') else OfficeVMCMemoryESN
            first,second=cls(checkpoint),cls(checkpoint)
            prediction=np.asarray([first.act(x) for x in probe])
            altered=np.asarray([second.act(x) for x in changed])
            assert prediction.shape==(96,7) and np.isfinite(prediction).all()
            np.testing.assert_array_equal(prediction,altered)
            assert np.max(abs(prediction))<=1 and np.min(prediction[:,0])>=0
            if family.startswith(('matched_','ordinary_')):
                key=(detail['schedule_sha256'],detail['actual_nonpadding_observations'],detail['updates'],detail['tbptt_steps'])
                if seed in gradient_schedule:assert key==gradient_schedule[seed]
                gradient_schedule[seed]=key
                assert detail['unused_field_isolation_pass']
            parent=detail.get('parent_checkpoint_sha256')
            if family.startswith('matched_'):
                base='esn' if family=='matched_rnn' else 'memoryless'
                assert parent==sha(args.learning/f'readout_refit_{base}_{seed}'/'checkpoint.npz')
            rows.append(dict(family=family,seed=seed,checkpoint=str(checkpoint.resolve()),
                checkpoint_sha256=sha(checkpoint),metadata=str(metadata.resolve()),metadata_sha256=sha(metadata),
                training_data_sha256=data_hash,actor_unused_field_isolation_exact=True,
                gradient_updates=detail.get('updates',0),selected_update=detail.get('selected_update'),
                observed_training_samples=detail.get('actual_nonpadding_observations'),
                parent_checkpoint_sha256=parent,learning_rate=detail.get('learning_rate'),
                trainable_parameters=detail.get('trainable_parameters',detail.get('trainable_readout_coefficients'))))
    result=dict(status='passed',completed_utc=now(),scope='existing_same_teacher_cohort_before_new_development',
        models=rows,training_data_sha256=data_hash,training_identities=20,validation_identities=5,
        model_count=len(rows),gradient_schedules={str(k):v for k,v in gradient_schedule.items()},
        matched_current_gradient_exposure=True,physics_steps=0,
        limitations=['Matched networks additionally inherit ESN/memoryless fitting; parent cost is not zero.',
                    'Same data/width do not imply equal parameter count, FLOPs, historical search, or closed-loop performance.',
                    'Synthetic field-isolation probe verifies dependence only, not generalization or training adequacy.',
                    'Only the file paths actually read here are verified; remote archive needs separate execution.'])
    write(args.output,result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('models','gradient_schedules','limitations')}))


if __name__=='__main__':main()
