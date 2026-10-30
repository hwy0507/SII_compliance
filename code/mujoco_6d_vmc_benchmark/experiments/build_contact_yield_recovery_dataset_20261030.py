"""Append only audited, actually executed teacher recovery suffixes.

Student prefixes retain observation history for recurrent warm-up, carry their
actual student actions solely as inert labels, and have zero fitting weight.
Pure validation identities remain untouched and are the only selection set.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'scripts')]


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()

def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def build(recovery,base,out):
    recovery=Path(recovery).resolve();base=Path(base).resolve();out=Path(out).resolve()
    assert not out.exists(), 'Never overwrite a dataset or interrupted fit'
    reg=read(recovery/'REGISTRATION.json');state=read(recovery/'execution.json')
    assert state['status']=='complete_four_recovery_probes_pending_shared_data_decision'
    assert state['registration_sha256']==sha(recovery/'REGISTRATION.json') and len(state['rows'])==4
    for name,digest in reg['source_sha256'].items():
        assert sha(ROOT/name)==digest,name
    base_meta=read(base/'data/DATA_COMPLETE.json');base_state=read(base/'execution.json')
    assert base_state['status']=='complete' and base_state['model_lock_sha256']==sha(base/'MODEL_LOCK.json')
    assert base_meta['qualified_episodes']==30 and base_meta['frames']==15750
    with np.load(base/'data/training_data.npz',allow_pickle=False) as z:arrays={k:z[k].copy() for k in z.files}
    assert arrays['observation'].shape==(15750,48) and arrays['requested_teacher_action'].shape==(15750,7)
    assert np.all(arrays['importance']==1.)
    from audit_special_scene_metrics_v2_20261030 import episode
    augmentation=[]
    expected_ids=['rod_mlp01_7s','ball_rnn01_10s','ball_mlp01_10s','ball_rnn01_20s']
    assert [c['id'] for c in reg['cases']]==expected_ids
    assert [r['id'] for r in state['rows']]==expected_ids
    names={k:[v] for k,v in arrays.items()}
    # Add the common train-only lineage columns. Prefix targets are the actual
    # student actions but weight zero; no counterfactual teacher label enters.
    for i,(case,row) in enumerate(zip(reg['cases'],state['rows'])):
        folder=Path(row['folder']);assert folder.is_dir() and row['qualified'] is True
        handoff=read(folder/'HANDOFF_REVIEW.json');audit=read(folder/'INDEPENDENT_AUDIT.json')
        qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert handoff['qualified'] and handoff['teacher_suffix_candidate_only'] and handoff['no_training_performed']
        assert handoff['no_final_test_performed'] and audit['status']=='passed'
        assert qualification['status']=='qualified' and all(qualification[k] is True for k in ('task_success','safety_valid','scene_contact_valid'))
        assert all(sha(folder/n)==h for n,h in qualification['input_hashes'].items())
        ex=read(folder/'execution.json');expected_s=20. if case['scene']=='rod' else 30.
        metric=episode(folder,case['model']['name'],case['condition']['id'],expected_s)
        assert metric['task_success'] and metric['strict_success'] and metric['machine_compliant']
        assert ex['status']=='complete' and ex['physics_dt_s']==.00005
        assert ex['steps']==round(expected_s/.04) and ex['substeps']==ex['steps']*800
        assert ex['student_checkpoint_sha256']==case['model']['checkpoint_sha256']
        with np.load(folder/'trajectory.npz',allow_pickle=False) as z:obs=z['observation'].copy();applied=z['action'].copy()
        with np.load(folder/'handoff_actions.npz',allow_pickle=False) as z:h={k:z[k].copy() for k in z.files}
        prefix=case['student_steps'];n=len(obs)
        assert n==ex['steps'] and prefix<n and h['physical_step_completed'].all()
        assert not h['teacher_loss_mask'][:prefix].any() and h['teacher_loss_mask'][prefix:].all()
        assert np.all(h['role'][:prefix]=='student_prefix') and np.all(h['role'][prefix:]=='executed_teacher_suffix')
        np.testing.assert_array_equal(h['teacher'][prefix:],applied[prefix:])
        np.testing.assert_array_equal(h['student'][:prefix],applied[:prefix])
        original=base.parent/'contact_yield_student_development_20261030_v1/episodes'/('rod_00__special_mlp_scratch_s2026102801' if case['scene']=='rod' else ('ball_00__special_rnn_scratch_s2026102801' if case['model']['family']=='rnn_scratch' else 'ball_00__special_mlp_scratch_s2026102801'))/case['scene']
        # Bind the exact failed student prefix from its original saved rollout.
        assert sha(folder/'scene.mjb')==sha(original/'scene.mjb')
        with np.load(original/'trajectory.npz',allow_pickle=False) as z:orig_obs=z['observation'].copy();orig_act=z['action'].copy()
        np.testing.assert_array_equal(obs[:prefix],orig_obs[:prefix]);np.testing.assert_array_equal(applied[:prefix],orig_act[:prefix])
        eid=30+i
        names['observation'].append(obs)
        names['requested_teacher_action'].append(applied.copy())
        names['requested_teacher_action'][-1][:prefix]=applied[:prefix] # actual student actions, explicitly zero-weight
        names['episode'].append(np.full(n,eid,np.int64));names['train'].append(np.ones(n,bool))
        names['physical_execution'].append(np.ones(n,bool))
        names['importance'].append(np.r_[np.zeros(prefix),np.ones(n-prefix)].astype(np.float64))
        augmentation.append(dict(episode=eid,id=case['id'],scene=case['scene'],split='train',source_folder=str(folder),
            source_identity=case['condition']['id'],family=case['model']['family'],seed=case['model']['seed'],
            student_prefix_steps=prefix,teacher_supervised_steps=n-prefix,frames=n,expected_duration_s=expected_s,
            task_success=True,strict_success=True,machine_compliant=True,teacher_suffix_only=True,
            zero_loss_warmup=True,prefix_target='actual student action, importance exactly zero; not teacher-labelled',
            trajectory_sha256=sha(folder/'trajectory.npz'),handoff_actions_sha256=sha(folder/'handoff_actions.npz'),
            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),review_sha256=sha(folder/'HANDOFF_REVIEW.json'),
            independent_audit_sha256=sha(folder/'INDEPENDENT_AUDIT.json'),checkpoint_sha256=case['model']['checkpoint_sha256']))
    values={k:np.concatenate(v,axis=0) for k,v in names.items()}
    assert len(values['episode'])==18500 and len(np.unique(values['episode'][values['train']]))==28
    assert len(np.unique(values['episode'][~values['train']]))==6
    assert int(np.sum(values['importance']==0))==1175
    assert int(np.sum(values['importance']==1))==17325
    assert np.all(values['train'][values['importance']==0])
    assert not set(values['episode'][values['train']]).intersection(values['episode'][~values['train']])
    values['teacher_action']=values['requested_teacher_action'].copy()
    out.mkdir(parents=True);(out/'data').mkdir()
    np.savez_compressed(out/'data/training_data.npz',**values)
    lineage=list(base_meta['lineage'])
    for a in augmentation:
        lineage.append(dict(episode=a['episode'],id=a['id'],scene=a['scene'],split='train',folder=a['source_folder'],frames=a['frames'],
            reused=False,augmented=True,student_prefix_steps=a['student_prefix_steps'],supervised_frames=a['teacher_supervised_steps'],
            hashes={'trajectory.npz':a['trajectory_sha256'],'handoff_actions.npz':a['handoff_actions_sha256']}))
    data_path=out/'data/training_data.npz';meta=dict(base_meta)
    meta.update(schema='sii-vmc-special-scenes-recovery-augmented-v1',training_data_sha256=sha(data_path),
        base_dataset_sha256=base_meta['training_data_sha256'],episodes=34,qualified_episodes=30,frames=18500,
        pure_qualified_episodes=30,augmented_recovery_episodes=4,zero_weight_warmup_frames=1175,
        teacher_supervised_recovery_frames=2750-1175,all_real_execution=True,lineage=lineage,
        recovery_augmentation=augmentation,validation_identities=base_meta['validation_identities'],
        validation_unchanged=True,selection='Same original six pure teacher validation identities; zero recovery data in validation/selection; same per-family candidate grid.')
    write(out/'data/DATA_COMPLETE.json',meta)
    reg2=dict(schema='sii-contact-yield-scrape-recovery-fair-retrain-v1',dataset_sha256=meta['training_data_sha256'],base_dataset_sha256=base_meta['training_data_sha256'],
        recovery_registration_sha256=sha(recovery/'REGISTRATION.json'),recovery_execution_sha256=sha(recovery/'execution.json'),
        recovery_cases=augmentation,seeds=[2026102801,2026102802,2026102803],candidates_per_family_seed=12,neural_updates=32000,
        esn_grid=dict(rho=[.5,.8],input_gain=[.08,.25,.6],ridge=[.001,.1]),
        neural_grid=dict(learning_rate=[1e-4,3e-4,1e-3,3e-3],weight_decay=[0,1e-5,1e-4]),
        selection='minimum requested-action MSE on the exact same six original pure-teacher validation identities for every family/seed; first minimum, fixed seed list',
        recurrent_warmup='Feed actual observed student prefix through RNN hidden state with importance=0 and skip all-zero-loss optimizer batches; no counterfactual teacher prefix labels.',
        comparison='All three families train on exact same 30 pure episodes plus the same four actual recovery rollouts; ESN uses importance-weighted ridge, neural families use the same 32k updates and 12-grid.',
        models=['ESN','RNN','MLP'],metrics='Task; Strict; dual-pass SPT; mean peak torque; human comfort NA where unmeasured; machine compliance',
        final_test='Frozen isolated unseen108 only after all nine locked models and fixed development review pass; never used for fitting or selection.')
    write(out/'REGISTRATION.json',reg2)
    write(out/'RECOVERY_AUGMENTATION.json',dict(status='verified_actual_teacher_suffixes_only',base_data_sha256=base_meta['training_data_sha256'],new_data_sha256=meta['training_data_sha256'],episodes=augmentation,
        counterfactual_prefix_rows_used_as_teacher_labels=0,zero_weight_prefix_rows=1175,teacher_supervised_rows=1575,all_four_task_strict_machine_pass=True))
    write(out/'execution.json',dict(status='dataset_complete',dataset_sha256=meta['training_data_sha256'],model_lock_sha256=None))
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recovery',type=Path,required=True);p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    print(json.dumps(build(a.recovery,a.base,a.output),ensure_ascii=False,indent=2))
