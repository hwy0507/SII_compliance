"""Build 30 pure teacher episodes plus two masked executed recovery suffixes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text())


def build(collection, output):
    collection=Path(collection).resolve();output=Path(output).resolve()
    reg=read(collection/'REGISTRATION.json');state=read(collection/'execution.json')
    assert not output.exists()
    assert state['status']=='all30_qualified_pending_independent_dataset_review'
    assert sha(collection/'REGISTRATION.json')==state['registration_sha256']
    source_root=Path(__file__).resolve().parents[1]
    assert sha(source_root/'experiments/collect_vertical_aware_special_scenes_20261030.py')==reg['coordinator_sha256']
    assert len(state['rows'])==30 and len(reg['cases'])==30
    assert all(row['qualified'] for row in state['rows'])
    assert len({row['id'] for row in state['rows']})==30
    assert sum(row['reused'] for row in state['rows'])==3
    assert Counter((c['scene'],c['split']) for c in reg['cases'])==Counter(
        {(scene,split):count for scene in ('rod','ball','corner')
         for split,count in (('train',8),('validation',2))})
    assert len(reg['augmentation_candidates'])==2
    for name,digest in reg['source_sha256'].items():
        assert sha(source_root/name)==digest,name

    pure=[];augmentation=[];lineage=[];teacher_hashes=set()
    for index,(case,row) in enumerate(zip(reg['cases'],state['rows'])):
        assert row['id']==case['id'] and row['folder']
        folder=Path(row['folder']).resolve()
        expected_folder=Path(case['reuse']).resolve() if case['reuse'] else (collection/case['id']/case['scene']).resolve()
        assert folder==expected_folder
        reference=Path(case['reference']).resolve()
        assert sha(reference/'execution.json')==case['reference_execution_sha256']
        assert sha(reference/'DEMONSTRATION_QUALIFICATION.json')==case['reference_qualification_sha256']
        review=read(folder/'HANDOFF_REVIEW.json');qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert row['review_sha256']==sha(folder/'HANDOFF_REVIEW.json')
        assert row['qualification_sha256']==sha(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert review['qualified'] is True
        assert qualification['status']=='qualified'
        assert all(qualification[k] is True for k in ('task_success','safety_valid','scene_contact_valid'))
        for name,digest in qualification['input_hashes'].items(): assert sha(folder/name)==digest
        handoff=read(folder/'HANDOFF_EXECUTION.json');execution=read(folder/'execution.json')
        assert handoff['source_stable'] is True and handoff['completed_steps']==execution['steps']
        assert handoff['executed_teacher_steps']==execution['steps']
        assert review['handoff_execution_sha256']==sha(folder/'HANDOFF_EXECUTION.json')
        assert review['independent_audit_sha256']==sha(folder/'INDEPENDENT_AUDIT.json')
        independent=read(folder/'INDEPENDENT_AUDIT.json')
        assert independent['status']=='passed'
        assert independent['handoff_execution_sha256']==sha(folder/'HANDOFF_EXECUTION.json')
        for name,digest in independent['input_hashes'].items(): assert sha(folder/name)==digest
        assert execution['status']=='complete' and execution['scene']==case['scene']
        assert execution['physics_dt_s']==5e-5 and execution['teacher_config_sha256']==reg['teacher_config_sha256']
        assert execution['action_contract']==dict(linear_yield_mps=.32,angular_yield_radps=.6,actor_dt_s=.04,
                                                    label='unfiltered normalized requested action')
        assert execution['filter_config']['maximum_linear_yield_mps']==.32
        assert execution['model_sha256']==case['model_sha256']
        assert execution['filter_config']==read(Path(case['reference'])/'execution.json')['filter_config']
        for name,digest in handoff['input_hashes'].items(): assert sha(folder/name)==digest
        teacher_hashes.add(execution['teacher_config_sha256'])
        with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
            obs=z['observation'].copy();applied=z['action'].copy();times=z['time'].copy()
        assert obs.shape==(execution['steps'],48) and applied.shape==(execution['steps'],7)
        assert len(times)==len(obs) and np.isfinite(obs).all() and np.isfinite(applied).all()
        assert len(obs)==dict(rod=500,ball=750,corner=325)[case['scene']]
        if case['scene']=='rod':
            behavior=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
            assert behavior['status']=='passed' and behavior['hashes']['trajectory.npz']==sha(folder/'trajectory.npz')
        with np.load(folder/'handoff_actions.npz',allow_pickle=False) as z:
            teacher=z['teacher'].copy();completed=z['physical_step_completed'].copy();mask=z['teacher_loss_mask'].copy();role=z['role'].copy()
        assert teacher.shape==applied.shape and completed.all() and mask.all() and np.all(role=='executed_teacher_suffix')
        np.testing.assert_array_equal(teacher,applied)
        pure.append((case,folder,obs,teacher,times))
        lineage.append(dict(episode=index,id=case['id'],scene=case['scene'],split=case['split'],
                            folder=str(folder),frames=len(obs),reused=row['reused'],
                            trajectory_sha256=sha(folder/'trajectory.npz'),execution_sha256=sha(folder/'execution.json'),
                            handoff_actions_sha256=sha(folder/'handoff_actions.npz'),
                            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json')))

    assert len(teacher_hashes)==1 and next(iter(teacher_hashes))==reg['teacher_config_sha256']
    arrays={k:[] for k in ('observation','requested_teacher_action','episode','train','physical_execution','importance')}
    for episode,(case,folder,obs,actions,times) in enumerate(pure):
        arrays['observation'].append(obs);arrays['requested_teacher_action'].append(actions)
        arrays['episode'].append(np.full(len(obs),episode,np.int64));arrays['train'].append(np.full(len(obs),case['split']=='train',bool))
        arrays['physical_execution'].append(np.ones(len(obs),bool));arrays['importance'].append(np.ones(len(obs),np.float64))
    # Validate and retain actual recovery suffixes separately until the
    # recurrent zero-loss warmup path is independently reviewed.
    augmentation_lineage=[]
    for item in reg['augmentation_candidates']:
        folder=Path(item['folder']).resolve();assert item['split']=='train'
        with np.load(folder/'trajectory.npz',allow_pickle=False) as z: obs=z['observation'].copy();applied=z['action'].copy();times=z['time'].copy()
        with np.load(folder/'handoff_actions.npz',allow_pickle=False) as z:
            target=z['teacher'].copy();completed=z['physical_step_completed'].copy();mask=z['teacher_loss_mask'].copy();role=z['role'].copy()
        prefix=item['student_prefix_steps'];assert 0<prefix<len(obs)
        assert completed.all() and not mask[:prefix].any() and mask[prefix:].all()
        assert np.all(role[:prefix]=='student_prefix') and np.all(role[prefix:]=='executed_teacher_suffix')
        np.testing.assert_array_equal(target[prefix:],applied[prefix:])
        augmentation_lineage.append(dict(id=f"rod_00_recovery_prefix{prefix}",scene='rod',split='train',
                            source_identity='rod_00',frames=len(obs),warmup_frames=prefix,supervised_frames=int(mask.sum()),
                            actual_teacher_suffix_only=True,trajectory_sha256=sha(folder/'trajectory.npz'),
                            handoff_actions_sha256=sha(folder/'handoff_actions.npz'),review_sha256=sha(folder/'HANDOFF_REVIEW.json'),
                            fitting_status='withheld pending zero-loss recurrent warmup audit'))
    values={k:np.concatenate(v) for k,v in arrays.items()}
    output.mkdir(parents=True);(output/'data').mkdir()
    values['teacher_action']=values['requested_teacher_action'].copy()
    np.savez_compressed(output/'data/training_data.npz',**values)
    metadata=dict(schema='sii-vmc-special-scenes-dataset-v2',
                  training_data_sha256=sha(output/'data/training_data.npz'),collection_registration_sha256=sha(collection/'REGISTRATION.json'),
                  collection_execution_sha256=sha(collection/'execution.json'),episodes=30,episode_count=30,qualified_episodes=30,frames=len(values['episode']),
                  all_real_execution=True,position_error_context=True,teacher_config_sha256=next(iter(teacher_hashes)),
                  training_identities=[case['id'] for case in reg['cases'] if case['split']=='train'],
                  validation_identities=[case['id'] for case in reg['cases'] if case['split']=='validation'],lineage=lineage,
                  selection='Same 6 pure validation identities, 2 per scene; requested-action MSE only; augmented train episodes never used for validation.',
                  old_composite_scene_excluded=True)
    (output/'data/DATA_COMPLETE.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (output/'data/RECOVERY_AUGMENTATION_CANDIDATES.json').write_text(json.dumps(augmentation_lineage,indent=2)+'\n')
    train_reg=dict(schema='sii-vertical-aware-fair-retrain-v1',dataset_sha256=metadata['training_data_sha256'],
                   seeds=[2026102801,2026102802,2026102803],candidates_per_family_seed=12,neural_updates=32000,
                   esn_grid=dict(rho=[.5,.8],input_gain=[.08,.25,.6],ridge=[.001,.1]),
                   neural_grid=dict(learning_rate=[1e-4,3e-4,1e-3,3e-3],weight_decay=[0,1e-5,1e-4]),
                   selection='same 6 pure validation identities and requested-action MSE for every family/seed; first minimum, fixed seed list',
                   models=['ESN','RNN','MLP'],metrics='Task; Strict; dual-pass SPT; mean peak torque; human comfort NA where unmeasured; machine compliance',
                   final_test_source='Frozen isolated unseen108 only after all nine model identities lock; no test access during fitting/selection.')
    (output/'REGISTRATION.json').write_text(json.dumps(train_reg,indent=2)+'\n')
    (output/'execution.json').write_text(json.dumps(dict(status='dataset_complete',dataset_sha256=metadata['training_data_sha256']),indent=2)+'\n')
    return metadata


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.collection,a.output),indent=2))
