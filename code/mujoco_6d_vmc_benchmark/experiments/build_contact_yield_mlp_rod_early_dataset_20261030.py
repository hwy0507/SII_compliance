"""Append only qualified seed01 early-handoff suffixes to the v4 shared data."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT/'scripts')]
from audit_contact_yield_recovery_fits_20261030 import audit as audit_fits
RECOVERY = ROOT/'outputs/contact_yield_mlp_rod_early_recovery_20261030_v1'
BASE = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v4'
OUTPUT = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v5'
OUTPUT_RETRY = ROOT/'outputs/contact_yield_recovery_retrain_20261030_v6'
ACCEPTED = ('rod_mlp01_early_4p48s', 'rod_mlp01_early_4p60s')
EXPECTED = (*ACCEPTED, 'rod_mlp02_prelimit_4p48s', 'rod_mlp02_prelimit_4p60s')
AUDIT_SOURCE = 'tools/audit_contact_yield_recovery_fits_20261030.py'
REGISTERED_AUDIT_SHA256 = '64978d5869b1f07dc9a55ff96306cff3c7a5da99e5906e9d99fd87093c4da215'
TRAINER_SOURCE = 'tools/train_contact_yield_recovery_models_20261030.py'
REGISTERED_TRAINER_SHA256 = 'c73c5b009e725c558f05e82bbac53a08ed99cdc9cc3fd678f4e9d7c2b67bb626'

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()

def read(path): return json.loads(Path(path).read_text())
def write(path, value): Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def verify_audit_compatibility(prior_audit):
    registered = read(RECOVERY/'REGISTRATION.json')['source_sha256'][AUDIT_SOURCE]
    current = sha(ROOT/AUDIT_SOURCE)
    assert registered == REGISTERED_AUDIT_SHA256
    recomputed = audit_fits(BASE, ROOT)
    assert prior_audit['status'] == recomputed['status'] == 'passed'
    for key in ('dataset_sha256', 'model_lock_sha256',
                'frozen_actor_replays', 'same_neural_schedule_sha256'):
        assert prior_audit[key] == recomputed[key], key
    old_jobs, new_jobs = prior_audit['candidate_jobs'], recomputed['candidate_jobs']
    assert len(old_jobs) == len(new_jobs) == 75
    for old, new in zip(old_jobs, new_jobs):
        assert old['name'] == new['name']
        assert old['checkpoint_sha256'] == new['checkpoint_sha256']
        assert math.isclose(old['validation_mse'], new['validation_mse'], rel_tol=0., abs_tol=1e-12)
    return dict(path=AUDIT_SOURCE, historical_registered_sha256=registered,
        current_sha256=current, historical_fit_audit_sha256=sha(BASE/'FIT_AUDIT.json'),
        v4_dataset_sha256=recomputed['dataset_sha256'], compatibility='passed',
        compared_fields=['dataset_sha256', 'model_lock_sha256', '75 candidate names/checkpoint hashes exact and validation MSE within 1e-12',
                         'frozen_actor_replays', 'same_neural_schedule_sha256'],
        historical_audit_receipt_preserved=True)

def build(output=OUTPUT):
    output = Path(output).resolve()
    assert output in (OUTPUT.resolve(), OUTPUT_RETRY.resolve()) and not output.exists()
    reg, state = read(RECOVERY/'REGISTRATION.json'), read(RECOVERY/'execution.json')
    assert state['status'] == 'complete_four_recovery_probes_pending_shared_data_decision'
    assert state['registration_sha256'] == sha(RECOVERY/'REGISTRATION.json')
    assert [row['id'] for row in state['rows']] == list(EXPECTED)
    source_compatibility = []
    for name, digest in reg['source_sha256'].items():
        current = sha(ROOT/name)
        if current != digest and name == AUDIT_SOURCE:
            assert digest == REGISTERED_AUDIT_SHA256
            source_compatibility.append(dict(path=name, historical_sha256=digest, current_sha256=current,
                reason='Backward-compatible v1/v2/v3 dataset population audit extension'))
            continue
        if current != digest and name == TRAINER_SOURCE:
            assert digest == REGISTERED_TRAINER_SHA256
            source_compatibility.append(dict(path=name, historical_sha256=digest, current_sha256=current,
                reason='Added exact v3 dataset population and zero-weight-row contract checks before fitting'))
            continue
        assert sha(ROOT/name) == digest, name
    base_meta = read(BASE/'data/DATA_COMPLETE.json')
    base_state, base_lock, base_audit = (read(BASE/name) for name in ('execution.json','MODEL_LOCK.json','FIT_AUDIT.json'))
    assert base_state['status']=='complete' and base_state['model_lock_sha256']==sha(BASE/'MODEL_LOCK.json')
    assert base_lock['status']=='frozen' and base_audit['status']=='passed'
    audit_compatibility = verify_audit_compatibility(base_audit)
    assert base_meta['training_data_sha256']==sha(BASE/'data/training_data.npz')
    assert base_meta['episodes']==36 and base_meta['qualified_episodes']==30
    with np.load(BASE/'data/training_data.npz',allow_pickle=False) as archive: arrays={k:archive[k].copy() for k in archive.files}
    assert arrays['observation'].shape==(19500,48) and arrays['requested_teacher_action'].shape==(19500,7)
    assert int(np.sum(arrays['importance']==0.))==1480
    assert len(np.unique(arrays['episode'][arrays['train']]))==30 and len(np.unique(arrays['episode'][~arrays['train']]))==6
    from audit_special_scene_metrics_v2_20261030 import episode as audit_metrics
    additions=[]
    for identity in ACCEPTED:
        case=next(c for c in reg['cases'] if c['id']==identity); row=next(r for r in state['rows'] if r['id']==identity); folder=Path(row['folder'])
        assert row['qualified'] is True and folder.is_dir()
        handoff=read(folder/'HANDOFF_REVIEW.json'); qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        independent=read(folder/'INDEPENDENT_AUDIT.json'); execution=read(folder/'execution.json')
        assert handoff['status']=='reviewed' and handoff['qualified'] and handoff['teacher_suffix_candidate_only']
        assert handoff['no_training_performed'] and handoff['no_final_test_performed'] and independent['status']=='passed'
        assert qualification['status']=='qualified' and all(qualification[k] is True for k in ('task_success','safety_valid','scene_contact_valid'))
        assert all(sha(folder/n)==h for n,h in qualification['input_hashes'].items())
        metrics=audit_metrics(folder,case['model']['name'],case['condition']['id'],20.)
        assert metrics['task_success'] and metrics['strict_success'] and metrics['machine_compliant']
        assert execution['status']=='complete' and execution['physics_dt_s']==.00005 and execution['steps']==500 and execution['substeps']==400000
        assert execution['student_checkpoint_sha256']==case['model']['checkpoint_sha256']
        with np.load(folder/'trajectory.npz',allow_pickle=False) as archive: obs=archive['observation'].copy(); applied=archive['action'].copy()
        with np.load(folder/'handoff_actions.npz',allow_pickle=False) as archive: h={k:archive[k].copy() for k in archive.files}
        prefix=case['student_steps']; assert obs.shape==(500,48) and applied.shape==(500,7) and h['physical_step_completed'].all()
        assert not h['teacher_loss_mask'][:prefix].any() and h['teacher_loss_mask'][prefix:].all()
        assert np.all(h['role'][:prefix]=='student_prefix') and np.all(h['role'][prefix:]=='executed_teacher_suffix')
        np.testing.assert_array_equal(h['teacher'][prefix:],applied[prefix:]); np.testing.assert_array_equal(h['student'][:prefix],applied[:prefix])
        original=ROOT/'outputs/contact_yield_targeted_student_development_20261030_v2/episodes'/('rod_00__special_mlp_scratch_s'+str(case['model']['seed']))/'rod'
        assert sha(folder/'scene.mjb')==sha(original/'scene.mjb')
        with np.load(original/'trajectory.npz',allow_pickle=False) as archive:
            np.testing.assert_array_equal(obs[:prefix],archive['observation'][:prefix]); np.testing.assert_array_equal(applied[:prefix],archive['action'][:prefix])
        eid=int(arrays['episode'].max())+1
        arrays['observation']=np.concatenate((arrays['observation'],obs))
        arrays['requested_teacher_action']=np.concatenate((arrays['requested_teacher_action'],applied.copy()))
        arrays['episode']=np.concatenate((arrays['episode'],np.full(500,eid,np.int64)))
        arrays['train']=np.concatenate((arrays['train'],np.ones(500,bool)))
        arrays['physical_execution']=np.concatenate((arrays['physical_execution'],np.ones(500,bool)))
        arrays['importance']=np.concatenate((arrays['importance'],np.r_[np.zeros(prefix),np.ones(500-prefix)].astype(np.float64)))
        additions.append(dict(episode=eid,id=identity,scene='rod',split='train',source_folder=str(folder),source_identity=case['condition']['id'],
            family=case['model']['family'],seed=case['model']['seed'],student_prefix_steps=prefix,teacher_supervised_steps=500-prefix,frames=500,
            expected_duration_s=20.,task_success=True,strict_success=True,machine_compliant=True,teacher_suffix_only=True,zero_loss_warmup=True,
            trajectory_sha256=sha(folder/'trajectory.npz'),handoff_actions_sha256=sha(folder/'handoff_actions.npz'),
            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'),review_sha256=sha(folder/'HANDOFF_REVIEW.json'),
            independent_audit_sha256=sha(folder/'INDEPENDENT_AUDIT.json'),checkpoint_sha256=case['model']['checkpoint_sha256']))
    arrays['teacher_action']=arrays['requested_teacher_action'].copy()
    assert arrays['observation'].shape==(20500,48) and arrays['requested_teacher_action'].shape==(20500,7)
    assert int(np.sum(arrays['importance']==0.))==1707 and int(np.sum(arrays['importance']==1.))==18793
    assert len(np.unique(arrays['episode'][arrays['train']]))==32 and len(np.unique(arrays['episode'][~arrays['train']]))==6
    output.mkdir(parents=True); (output/'data').mkdir()
    np.savez_compressed(output/'data/training_data.npz',**arrays); data_path=output/'data/training_data.npz'
    lineage=list(base_meta['lineage'])
    for a in additions: lineage.append(dict(episode=a['episode'],id=a['id'],scene='rod',split='train',folder=a['source_folder'],frames=500,reused=False,augmented=True,student_prefix_steps=a['student_prefix_steps'],supervised_frames=a['teacher_supervised_steps'],hashes={'trajectory.npz':a['trajectory_sha256'],'handoff_actions.npz':a['handoff_actions_sha256']}))
    metadata=dict(base_meta); metadata.update(schema='sii-vmc-special-scenes-recovery-augmented-v3',augmentation_round=3,training_data_sha256=sha(data_path),
        parent_data_sha256=base_meta['training_data_sha256'],episodes=38,qualified_episodes=30,frames=20500,pure_qualified_episodes=30,
        augmented_recovery_episodes=8,zero_weight_warmup_frames=1707,teacher_supervised_recovery_frames=3043,all_real_execution=True,lineage=lineage,
        early_rod_recovery_augmentation=additions,rejected_early_rod_probes=[dict(id=r['id'],qualified=False,reason='Independent safety/contact gate failed; retained outside training data',folder=r['folder'],review_sha256=r['review_sha256']) for r in state['rows'] if r['id'] not in ACCEPTED],
        recovery_source_compatibility=source_compatibility,
        validation_identities=base_meta['validation_identities'],validation_unchanged=True,selection='Same six pure-teacher validation identities; no recovery rows in validation or selection.')
    write(output/'data/DATA_COMPLETE.json',metadata)
    registration=read(BASE/'REGISTRATION.json'); registration.update(schema='sii-contact-yield-scrape-recovery-fair-refit-v3',dataset_sha256=metadata['training_data_sha256'],
        parent_data_sha256=base_meta['training_data_sha256'],parent_model_lock_sha256=sha(BASE/'MODEL_LOCK.json'),early_recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),
        early_recovery_execution_sha256=sha(RECOVERY/'execution.json'),early_recovery_cases=additions,excluded_probe_ids=[r['id'] for r in state['rows'] if r['id'] not in ACCEPTED],
        seeds=[2026102801,2026102802,2026102803],candidates_per_family_seed=12,neural_updates=32000,
        selection='Minimum requested-action MSE on the same six original pure-teacher validation identities; no recovery row is validation.',
        recurrent_warmup='Actual observed student prefixes have importance zero; no counterfactual teacher prefix labels.',
        comparison='ESN, RNN and MLP share the same 36-episode v4 parent dataset plus the same two qualified seed01 early rod-recovery rollouts and unchanged validation identities; equal candidate counts and neural update budgets.',
        final_test='Unseen108 remains sealed pending fixed27 development qualification and separate final handoff review.')
    write(output/'REGISTRATION.json',registration)
    write(output/'RECOVERY_SOURCE_COMPATIBILITY.json',dict(status='passed_exact_allowlist',historical_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),allowed_changes=source_compatibility,
        all_other_registered_recovery_sources_exact=True))
    write(output/'AUDIT_SOURCE_COMPATIBILITY.json',audit_compatibility)
    write(output/'RECOVERY_AUGMENTATION.json',dict(status='verified_two_actual_seed01_teacher_suffixes_only',parent_data_sha256=base_meta['training_data_sha256'],new_data_sha256=metadata['training_data_sha256'],episodes=additions,
        excluded_failed_probe_ids=[r['id'] for r in state['rows'] if r['id'] not in ACCEPTED],counterfactual_prefix_rows_used_as_teacher_labels=0,
        zero_weight_prefix_rows=sum(a['student_prefix_steps'] for a in additions),teacher_supervised_rows=sum(a['teacher_supervised_steps'] for a in additions),all_included_task_strict_machine_pass=True))
    write(output/'execution.json',dict(status='dataset_complete',dataset_sha256=metadata['training_data_sha256'],parent_data_sha256=base_meta['training_data_sha256'],model_lock_sha256=None,
        recovery_registration_sha256=sha(RECOVERY/'REGISTRATION.json'),recovery_execution_sha256=sha(RECOVERY/'execution.json')))
    return metadata

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path,default=OUTPUT); args=parser.parse_args()
    print(json.dumps(build(args.output),ensure_ascii=False,indent=2))
