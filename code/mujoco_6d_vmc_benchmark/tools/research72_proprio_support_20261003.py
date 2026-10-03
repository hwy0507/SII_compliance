"""Public-only, no-fit instantaneous proprioceptive support diagnostic.

Export all candidates of explicitly named completed public development IDs on
Spark, then compute on local CPU. Distances do not test recurrent-state support,
prove causation, select models, or generate new teacher labels.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import numpy as np

FIELDS=[*range(14,17),*range(20,23),*range(26,29),*range(39,48)]
SCALE=np.r_[np.full(3,.06),np.full(3,.08),np.full(3,.06),np.full(3,8.),np.ones(6)]
CLIP=np.r_[np.full(9,4.),np.full(6,12.),np.full(3,4.)]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def features(obs):
    assert obs.ndim==2 and obs.shape[1]==48 and np.isfinite(obs).all()
    normalized=obs[:,FIELDS]/SCALE
    return np.clip(normalized,-CLIP,CLIP),np.any(np.abs(normalized)>CLIP,axis=1)


def export(root,phase,conditions,out):
    protocol=read(root/'PROTOCOL.json');spec=read(phase/'SPECIFICATION.json')
    assert spec['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    roles={c['id']:c['role'] for c in read(root/'CONDITIONS.json')['conditions']}
    assert len(set(conditions))==len(conditions) and all(roles[c]=='development' for c in conditions)
    models={c['name']:c for c in spec['candidates']};selected={};queue_receipts=[]
    for path in sorted(phase.glob('queue_[0-3]/execution.json')):
        payload=path.read_bytes();state=json.loads(payload)
        queue_receipts.append(dict(path=str(path),snapshot_sha256=hashlib.sha256(payload).hexdigest()))
        for row in state['rows']:
            if row['condition_id'] not in conditions or 'audit_sha256' not in row:continue
            key=(row['condition_id'],row['candidate']);assert key not in selected
            run=path.parent/row['name'];audit=read(run/'AUDIT.json')
            assert sha(run/'AUDIT.json')==row['audit_sha256'] and audit['model_sha256']==protocol['formal_model_sha256']
            assert audit['trace_sha256']==sha(run/'rollout.npz')==row['trace_sha256']
            assert audit['actor_replay_performed']
            selected[key]=(run,row,audit)
    assert set(selected)=={(c,m) for c in conditions for m in models}, 'Need all candidates on every requested public identity'
    out.mkdir(parents=True,exist_ok=False)
    rows=[];observations=[];times=[];groups=[]
    for index,((condition,name),(run,row,audit)) in enumerate(sorted(selected.items())):
        with np.load(run/'rollout.npz',allow_pickle=False) as data:
            obs=data['observation'].copy();clock=data['neuron_time'].copy()
        assert len(obs)==len(clock) and np.isfinite(obs).all()
        observations.append(obs);times.append(clock);groups.append(np.full(len(obs),index,np.int32))
        candidate=models[name]
        rows.append(dict(index=index,candidate=name,condition_id=condition,category=candidate['category'],
            seed=candidate['seed'],variant=candidate['variant'],run=str(run),
            audit_sha256=row['audit_sha256'],trace_sha256=row['trace_sha256'],
            task_success=audit['task_success'],strict_success=audit['strict_success'],full_horizon=audit['full_horizon'],
            final_stage=audit['stage'],rmse_mm=audit['rmse_mm'],samples=len(obs)))
    np.savez_compressed(out/'public_observations.npz',observation=np.concatenate(observations),
                        time=np.concatenate(times),group=np.concatenate(groups))
    write(out/'MANIFEST.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)),protocol_sha256=sha(root/'PROTOCOL.json'),
        specification_sha256=sha(phase/'SPECIFICATION.json'),queue_snapshots=queue_receipts,rows=rows,
        observations_sha256=sha(out/'public_observations.npz'),
        role='All requested public development candidates, both successes and failures; no final reads, no physical simulation'))


def diagnose(data,metadata,public,out):
    from scipy.spatial import cKDTree
    meta=read(metadata);manifest=read(public/'MANIFEST.json')
    assert meta['training_data_sha256']==sha(data) and meta['all_real_execution']
    assert meta['protocol_sha256']==manifest['protocol_sha256']
    assert manifest['observations_sha256']==sha(public/'public_observations.npz')
    with np.load(data,allow_pickle=False) as z:
        train=z['train'].astype(bool);obs=z['observation'][train];episodes=z['episode'][train]
    assert len(np.unique(episodes))==meta['training_identities']>=2
    allowed={r['episode'] for r in meta['lineage'] if r['data_role']=='train'}
    assert set(np.unique(episodes))==allowed
    x,train_clipped=features(obs)
    # Each threshold-calibration query excludes its entire teacher identity,
    # not merely the sample next to itself in the same smooth history.
    loo=np.empty(len(x))
    for eid in np.unique(episodes):
        mask=episodes==eid;tree=cKDTree(x[~mask]);loo[mask]=tree.query(x[mask],k=1,workers=1)[0]
    threshold=float(np.percentile(loo,95));tree=cKDTree(x)
    with np.load(public/'public_observations.npz',allow_pickle=False) as z:
        actual=z['observation'].copy();group=z['group'].copy();clock=z['time'].copy()
    query,clipped=features(actual);distance=tree.query(query,k=1,workers=1)[0]
    rows=[]
    for entry in manifest['rows']:
        mask=group==entry['index'];d=distance[mask]
        assert len(d)==entry['samples']
        rows.append(dict(entry,nearest_distance_median=float(np.median(d)),
            nearest_distance_p95=float(np.percentile(d,95)),nearest_distance_max=float(d.max()),
            fraction_above_training_identity_loo_p95=float(np.mean(d>threshold)),
            actor_component_clipped_fraction=float(np.mean(clipped[mask]))))
    out.mkdir(parents=True,exist_ok=False)
    np.savez_compressed(out/'distances.npz',training_loo=loo,public_distance=distance,
                        public_group=group,public_time=clock,public_clipped=clipped)
    write(out/'SUPPORT.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)),training_data_sha256=sha(data),metadata_sha256=sha(metadata),
        public_manifest_sha256=sha(public/'MANIFEST.json'),distances_sha256=sha(out/'distances.npz'),
        observed_fields=FIELDS,fixed_physical_scales=SCALE.tolist(),fixed_actor_clip_bounds=CLIP.tolist(),
        threshold=threshold,training_identity_count=len(allowed),training_samples=len(x),
        training_clipped_fraction=float(train_clipped.mean()),rows=rows,
        threshold_rule='95th percentile of instantaneous nearest-neighbor distance to OTHER complete training identities; no development/validation calibration',
        limitations='Instantaneous18D clipped proprioception only, not reservoir-state support. Descriptive and correlated samples; no OOD detector claim, causal attribution, hypothesis test, new labels or candidate selection. Distance after clipping cannot characterize excursions beyond the clip; clipping fraction is separately shown.',
        fitting_performed=False,new_physics_episodes=0))
    print(json.dumps(dict(rows=len(rows),training_loo_p95=threshold,output=str(out))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='mode',required=True)
    e=s.add_parser('export')
    for n in ('root','phase','output'):e.add_argument('--'+n,type=Path,required=True)
    e.add_argument('--condition',action='append',required=True)
    d=s.add_parser('diagnose')
    for n in ('data','metadata','public','output'):d.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args()
    if a.mode=='export':export(a.root.resolve(),a.phase.resolve(),a.condition,a.output.resolve())
    else:diagnose(a.data,a.metadata,a.public,a.output.resolve())
