"""Audit frozen demonstration alignment and error strata; no fitting or physics."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','model-lock','collection','output'): p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args(); parent=a.parent.resolve(); output=a.output.resolve()
    assert not output.exists()
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    source=parent/'source'
    sys.path[:0]=[str(source/'tools'),str(source/'scripts')]
    from research72_build_demonstrations_20261003 import filtered_labels
    meta=read(parent/'data/DATA_COMPLETE.json'); dataset=parent/'data/training_data.npz'
    assert sha(dataset)==meta['training_data_sha256']
    with np.load(dataset) as z: data={k:z[k].copy() for k in z.files}
    obs=data['observation']; ep=data['episode']; train=data['train']; target=data['requested_teacher_action']
    assert data['physical_execution'].all() and np.all(data['importance']>0)
    assert not set(ep[train]) & set(ep[~train])
    teacher=np.empty(len(ep),dtype='U64'); stage=np.full(len(ep),-1,dtype=int)
    observed=[]; missing=[]
    for entry in meta['lineage']:
        ids=np.flatnonzero(ep==entry['episode']); teacher[ids]=entry['teacher_config_sha256']
        assert np.all(train[ids]==(entry['data_role']=='train'))
        trace=Path(entry['path']); run=trace.parent
        if not trace.exists():
            missing.append(dict(episode=entry['episode'],condition=entry['condition_id'],path=str(trace)))
            continue
        assert sha(trace)==entry['sha256']
        assert sha(run/'execution_chain.npz')==entry['chain_sha256']
        assert sha(run/'execution.json')==entry['execution_sha256']
        assert sha(run/'config.json')==entry['teacher_config_sha256']
        receipt=read(run/'execution.json'); assert receipt['status']=='complete'
        audit=read(run/'AUDIT.json'); assert audit['task_success'] and audit['strict_success']
        with np.load(trace) as z:
            np.testing.assert_array_equal(obs[ids],z['observation'])
            np.testing.assert_array_equal(target[ids],z['applied_action'])
            stage[ids]=z['stage']
        with np.load(run/'execution_chain.npz') as z:
            for d,c in (('requested_teacher_action','requested_action'),('clipped_teacher_action','clipped_action'),
                        ('filtered_teacher_action','filtered_action'),('executed_yield_twist','yield_twist'),
                        ('executed_wbc_scale','wbc_scale')):
                np.testing.assert_array_equal(data[d][ids],z[c])
        raw,filtered=filtered_labels(obs[ids],read(run/'config.json'))
        raw_error=float(np.max(abs(raw-target[ids])))
        filter_error=float(np.max(abs(filtered-data['filtered_teacher_action'][ids])))
        assert raw_error<=1e-10 and filter_error<=1e-12
        observed.append(dict(episode=int(entry['episode']),condition=entry['condition_id'],trace_sha256=sha(trace),
                             chain_sha256=entry['chain_sha256'],teacher_replay_max_abs=raw_error,filter_replay_max_abs=filter_error))
    # Force and torque estimates are normalized by their registered actor scales,
    # rather than mixing N and Nm in one norm. This is NOT an actual-contact mask.
    scaled_load=np.max(abs(obs[:,39:45]/np.array([8,8,8,1,1,1])),axis=1)
    sets={'all':np.ones(len(ep),bool),'normalized_load_le_1e-6':scaled_load<=1e-6,
          'normalized_load_gt_1e-6':scaled_load>1e-6}
    for value in np.unique(teacher): sets['teacher_'+value[:8]]=teacher==value
    for value in np.unique(stage[stage>=0]): sets['local_source_stage_'+str(value)]=stage==value
    for value in (0,): sets['exact_zero_current_wrench']=np.max(abs(obs[:,39:45]),axis=1)==value
    strata={}
    for split,base in (('train',train),('validation',~train)):
        strata[split]={}
        for name,mask in sets.items():
            use=base&mask
            strata[split][name]=dict(frames=int(use.sum()),
                nonzero_teacher_action_frames=int(np.sum(np.max(abs(target[use]),axis=1)>1e-6)),
                teacher_action_mean_square=float(np.mean(target[use]**2)) if use.any() else None,
                teacher_action_max_abs=float(np.max(abs(target[use]))) if use.any() else None)
    models=[]
    lock=read(a.model_lock)
    assert lock['training_data_sha256']==sha(dataset)
    for model in lock['models']:
        cp=Path(model['checkpoint']); completion=Path(model['metadata'])
        assert sha(cp)==model['checkpoint_sha256'] and sha(completion)==model['metadata_sha256']
        replay=cp.parent/'exported_replay.npz'
        with np.load(replay) as z:
            np.testing.assert_array_equal(z['episode'],ep); prediction=z['prediction'].copy()
        assert prediction.shape==target.shape and np.isfinite(prediction).all()
        err=np.mean((prediction-target)**2,axis=1)
        np.testing.assert_allclose(err[~train].mean(),read(completion)['validation_mse'],atol=1e-8,rtol=0)
        row=dict(name=model['name'],checkpoint_sha256=sha(cp),replay_sha256=sha(replay),strata={})
        for split,base in (('train',train),('validation',~train)):
            row['strata'][split]={name:dict(mse=float(err[base&mask].mean()) if np.any(base&mask) else None,
                share_of_split_sse=float(err[base&mask].sum()/err[base].sum())) for name,mask in sets.items()}
        models.append(row)
    fields=sorted(set(range(14,17))|set(range(20,23))|set(range(26,29))|set(range(39,48)))
    # Exact observational aliasing, without asserting that history is identical.
    _,inverse,count=np.unique(obs[:,fields],axis=0,return_inverse=True,return_counts=True)
    sums=np.stack([np.bincount(inverse,weights=target[:,j],minlength=len(count)) for j in range(7)],axis=1)
    conditional_mean=sums/count[:,None]
    irreducible_sse=float(np.sum((target-conditional_mean[inverse])**2))
    ledger_path=a.collection/'data/QUALIFICATION_LEDGER.json'; ledger=read(ledger_path)
    ledger_summary=Counter()
    for row in ledger:
        key='included' if row['included'] else 'not_dispatched_or_unfinished' if 'task' not in row else f"excluded_task_{row['task']}_strict_{row['strict']}"
        ledger_summary[key]+=1
    report=dict(status='completed',source_sha256=sha(Path(__file__)),data_sha256=sha(dataset),
        metadata_sha256=sha(parent/'data/DATA_COMPLETE.json'),model_lock_sha256=sha(a.model_lock),
        replay_source_sha256={str(f.relative_to(source)):sha(f) for f in (
            source/'tools/research72_build_demonstrations_20261003.py',source/'tools/optimize_tool_contact_20261002.py',
            source/'scripts/vmc_teacher_stable_readout_20260930.py',source/'scripts/wbc_velocity_residual_core.py')},
        frames=len(ep),importance_unique=np.unique(data['importance']).tolist(),
        verified_local_trajectories=observed,unverified_original_trajectories=missing,
        teacher_episode_counts=dict(Counter(t['teacher_config_sha256'] for t in meta['lineage'])),
        strata=strata,models=models,
        exact_current_input_aliasing=dict(fields=fields,duplicate_frame_count=int(count[count>1].sum()),
            duplicate_groups=int((count>1).sum()),memoryless_minimum_empirical_mse=irreducible_sse/target.size,
            definition='Exact current allowed-input groups, all data; lower bound for deterministic memoryless map only, not recurrent models.'),
        expanded_collection_ledger=dict(path=str(ledger_path.resolve()),sha256=sha(ledger_path),counts=dict(ledger_summary)),
        limitations=['Only locally available source trajectories replayed; absent remote originals explicitly unverified.',
            'Normalized estimated load is not true human contact; no comfort claim from this stratification.',
            'Stage strata cover only locally verified sources; not the entire 55-episode dataset.',
            'Existing candidate checkpoints and dataset unchanged. No physical run, collection, retraining or test-based selection.'])
    output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('frames','importance_unique','teacher_episode_counts','exact_current_input_aliasing','expanded_collection_ledger')},indent=2))
    print('Verified local originals:',len(observed),'Unavailable originals:',len(missing))
    print('Validation low-current-load strata:',json.dumps(strata['validation']['normalized_load_le_1e-6']))
    for model in models:
        print(model['name'],json.dumps(model['strata']['validation']))


if __name__=='__main__': main()
