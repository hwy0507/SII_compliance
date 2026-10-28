"""Build only registered, audited real-special-scene identities (24+6).

No scene-level holdout, synthetic trajectories, composite scenes or test labels.
Failed demonstrations remain in their source folders and block a formal build.
The plan must be saved before collection, with 10 distinct conditions per scene.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text())
def write(path, value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def build(plan_path, out):
    plan_path=plan_path.resolve();plan=read(plan_path)
    if plan.get('schema')!='sii-three-real-scenes-collection-plan-v2':
        raise ValueError('A prospective multi-identity collection plan is required')
    entries=plan['episodes']
    if len(entries)!=30 or len({r['id'] for r in entries})!=30:
        raise ValueError('Expected 30 distinct identities')
    expected=Counter({(s,p):n for s in ('rod','ball','corner') for p,n in (('train',8),('validation',2))})
    if Counter((r['scene'],r['split']) for r in entries)!=expected:
        raise ValueError('Require each scene in both partitions:8 train+2 validation')
    for scene in ('rod','ball','corner'):
        configs={json.dumps(r['scene_parameters'],sort_keys=True) for r in entries if r['scene']==scene}
        if len(configs)!=10:
            raise ValueError(f'Duplicate physical conditions in {scene}; a new seed alone is insufficient')
    if out.exists(): raise FileExistsError(out)
    arrays={k:[] for k in ('observation','requested_teacher_action','episode','train','physical_execution','importance')}
    lineage=[];seen=set();teacher_hashes=set()
    for i,entry in enumerate(entries):
        folder=Path(entry['folder']).resolve()
        if folder in seen: raise ValueError('Duplicate source folder')
        seen.add(folder)
        execution=read(folder/'execution.json')
        if execution.get('controller_role') != 'teacher':
            raise ValueError('Only explicitly identified teacher actions may enter a new dataset')
        if execution.get('action_contract') != plan.get('action_contract') or not plan.get('action_contract'):
            raise ValueError('Missing or mismatched registered action contract')
        if execution['filter_config']['maximum_linear_yield_mps'] != .32:
            raise ValueError('All three scenes must use the frozen test action scale 0.32 m/s')
        if execution['status']!='complete' or execution['scene']!=entry['scene']:
            raise ValueError('Incomplete or mismatched physical execution')
        if execution['physics_dt_s']!=.00005:
            raise ValueError('Unexpected physical timestep')
        if execution.get('collection_plan_sha256')!=sha(plan_path) or execution.get('collection_identity')!=entry['id']:
            raise ValueError('Run was not bound to this prospective collection plan')
        audit=read(folder/'INDEPENDENT_AUDIT.json')
        if audit['status']!='passed': raise ValueError('Actor/filter replay failed')
        for name,digest in audit['input_hashes'].items():
            if sha(folder/name)!=digest: raise ValueError(f'Stale independent audit:{folder/name}')
        qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        if qualification.get('schema')!='sii-real-special-demonstration-qualification-v1':
            raise ValueError('Require saved-substep qualification, not a hand-written success label')
        for name,digest in qualification['input_hashes'].items():
            if sha(folder/name)!=digest: raise ValueError(f'Stale physical qualification:{folder/name}')
        if not all(qualification.get(k) is True for k in ('task_success','safety_valid','scene_contact_valid')):
            raise ValueError('Nonqualified demonstration; preserve and fix teacher before collecting replacement')
        if qualification['trajectory_sha256']!=sha(folder/'trajectory.npz') or qualification['execution_sha256']!=sha(folder/'execution.json'):
            raise ValueError('Stale demonstration qualification')
        if entry['scene']=='rod':
            behavior=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
            if behavior['status']!='passed' or behavior['hashes']['trajectory.npz']!=sha(folder/'trajectory.npz'):
                raise ValueError('Rod must pass before withdrawal')
        with np.load(folder/'trajectory.npz') as z:
            obs=z['observation'].copy();act=z['action'].copy();time=z['time'].copy()
        if obs.ndim!=2 or obs.shape[1]!=48 or act.shape!=(len(obs),7): raise ValueError('Interface mismatch')
        if len(obs)<100 or not np.isfinite(obs).all() or not np.isfinite(act).all(): raise ValueError('Invalid samples')
        if not np.allclose(np.diff(time),.04,rtol=0,atol=1e-8): raise ValueError('Clock mismatch')
        arrays['observation'].append(obs);arrays['requested_teacher_action'].append(act)
        arrays['episode'].append(np.full(len(obs),i,dtype=np.int64))
        arrays['train'].append(np.full(len(obs),entry['split']=='train',dtype=bool))
        arrays['physical_execution'].append(np.ones(len(obs),dtype=bool))
        arrays['importance'].append(np.ones(len(obs)))
        teacher_hashes.add(execution['teacher_config_sha256'])
        lineage.append(dict(episode=i,id=entry['id'],scene=entry['scene'],split=entry['split'],folder=str(folder),frames=len(obs),
                            hashes={name:sha(folder/name) for name in ('trajectory.npz','execution.json','teacher.json','INDEPENDENT_AUDIT.json','DEMONSTRATION_QUALIFICATION.json')}))
    if len(teacher_hashes)!=1: raise ValueError('Require a single frozen VMC teacher across all three families')
    if next(iter(teacher_hashes))!=plan['teacher_config_sha256']:
        raise ValueError('Teacher changed after collection registration')
    out.mkdir(parents=True);(out/'data').mkdir()
    values={k:np.concatenate(v) for k,v in arrays.items()};values['teacher_action']=values['requested_teacher_action'].copy()
    np.savez_compressed(out/'data/training_data.npz',**values)
    metadata=dict(schema='sii-vmc-special-scenes-dataset-v2',training_data_sha256=sha(out/'data/training_data.npz'),
                  collection_plan_sha256=sha(plan_path),episodes=30,qualified_episodes=30,frames=len(values['episode']),
                  all_real_execution=True,position_error_context=True,teacher_config_sha256=next(iter(teacher_hashes)),
                  training_identities=[r['id'] for r in entries if r['split']=='train'],
                  validation_identities=[r['id'] for r in entries if r['split']=='validation'],lineage=lineage,
                  selection_split='Fixed six validation identities, two per real scene; same requested-action MSE for all families',
                  old_composite_scene_excluded=True)
    write(out/'data/DATA_COMPLETE.json',metadata)
    write(out/'REGISTRATION.json',dict(schema='sii-special-scene-retrain-v2',dataset_sha256=metadata['training_data_sha256'],
          seeds=[2026102801,2026102802,2026102803],candidates_per_family_seed=12,neural_updates=32000,
          esn_grid=dict(rho=[.5,.8],input_gain=[.08,.25,.6],ridge=[.001,.1]),
          neural_grid=dict(learning_rate=[1e-4,3e-4,1e-3,3e-3],weight_decay=[0,1e-5,1e-4]),
          selection=metadata['selection_split'],comparison='Equal candidate count, not equal FLOPs or parameter count',
          metrics='Task rate; Strict rate; conditional BOTH-success SPT; all-episode mean peak torque; actual human-contact weighted comfort; machine compliance',
          test_source='outputs/nonrl_new30_fair_20261026_v2; 12 already inspected frozen conditions; 9 models=108 episodes'))
    write(out/'execution.json',dict(status='dataset_complete',dataset_sha256=metadata['training_data_sha256']))
    return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.plan,a.output),ensure_ascii=False,indent=2))
