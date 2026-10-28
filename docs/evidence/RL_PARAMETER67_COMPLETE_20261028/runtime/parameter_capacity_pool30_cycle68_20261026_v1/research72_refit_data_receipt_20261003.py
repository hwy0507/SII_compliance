"""Verify selected-teacher data before the optional final shared-data refit.

No fitting or physics. Refuse pending collection and never read sealed contents.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from research72_final_lock_20261003 import read, sha


def verify(root):
    assert not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol=read(root/'PROTOCOL.json'); digest=sha(root/'PROTOCOL.json')
    choice_path=root/'followup_v1/CONTROLLER_CHOICE.json'
    choice=read(choice_path); assert choice['protocol_sha256']==digest
    assert read(root/'followup_v1/execution.json')['status']=='complete'
    selected=next(c for c in choice['candidates'] if c['category']=='enhanced_teacher')
    execution_path=root/'teacher_refinement_v1/execution.json'; execution=read(execution_path)
    assert execution['status'] in ('complete', 'complete_skipped_identical_teacher')
    assert execution['choice_sha256']==sha(choice_path) and execution['selected_teacher']==selected
    reused=execution['status']=='complete_skipped_identical_teacher'
    if reused:
        assert execution['new_physics_episodes']==0 and selected['config']==read(root/'teacher.json')
        teacher_path=root/'teacher.json'; bank=root/'teacher_bank'
        data=root/'prepare_learning_v2/demonstrations'
    else:
        assert execution['new_physics_episodes']==40
        data=root/'teacher_refinement_v1/demonstrations'; bank=root/'teacher_refinement_v1/collection'
        teacher_path=bank/'teacher.json'
        selection=read(bank/'TEACHER_SELECTION.json')
        assert selection['candidate']==selected and selection['choice_sha256']==sha(choice_path)
        assert selected['config']==read(teacher_path)
        assert execution['dataset_metadata_sha256']==sha(data/'DATA_COMPLETE.json')
    assert read(bank/'execution.json')['status']=='complete'
    assert read(data/'execution.json')['status']=='complete'
    metadata=read(data/'DATA_COMPLETE.json'); dataset=data/'training_data.npz'
    assert metadata['protocol_sha256']==digest and metadata['all_real_execution']
    assert metadata['teacher_config_sha256']==sha(teacher_path)
    assert metadata['training_data_sha256']==sha(dataset)
    assert metadata['actual_filter_replay_verified'] and metadata['actual_requested_labels_preserved']
    assert sha(data/'QUALIFICATION_LEDGER.json')==metadata['qualification_ledger_sha256']
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    roles={c['id']:c['role'] for c in read(root/'CONDITIONS.json')['conditions']}
    ledger={r['condition_id']:r for r in read(data/'QUALIFICATION_LEDGER.json')}
    assert len(ledger)==(48 if reused else 40)
    included={key for key,r in ledger.items() if r['included']}
    assert included=={r['condition_id'] for r in metadata['lineage']}
    assert len(included)==len(metadata['lineage'])
    for row in metadata['lineage']:
        assert row['data_role']==roles[row['condition_id']] in ('train','imitation_validation')
        assert row['actual_execution_labels'] and not row['counterfactual_relabel'] and not row['synthetic']
        assert row['task_success'] and row['strict_success'] and ledger[row['condition_id']]['qualified']
    assert metadata['training_identities']==sum(r['data_role']=='train' for r in metadata['lineage'])>=4
    assert metadata['validation_identities']==sum(r['data_role']=='imitation_validation' for r in metadata['lineage'])>=2
    return dict(status='complete', created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(Path(__file__)), protocol_sha256=digest, selected_teacher_verified=True,
        data=str(dataset), metadata=str(data/'DATA_COMPLETE.json'),
        training_data_sha256=sha(dataset), dataset_metadata_sha256=sha(data/'DATA_COMPLETE.json'),
        teacher_choice_sha256=sha(choice_path), teacher_execution_sha256=sha(execution_path),
        teacher_config_sha256=sha(teacher_path), reused_original_teacher=reused,
        qualifying_train_identities=metadata['training_identities'],
        qualifying_validation_identities=metadata['validation_identities'],
        evidence=[dict(path=str(p),sha256=sha(p)) for p in
                  (choice_path,execution_path,data/'DATA_COMPLETE.json',data/'QUALIFICATION_LEDGER.json',data/'execution.json')],
        all_six_learning_families_receive_identical_data=True, sealed_contents_read=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); receipt=verify(a.root.resolve())
    with a.output.open('x') as stream:
        json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(data_sha256=receipt['training_data_sha256'],receipt_sha256=sha(a.output))))
