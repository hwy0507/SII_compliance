"""Duplicate collection cannot inflate unique labels; NPZ bytes != arrays."""
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import teacher_bank_duplicate_review_20260930 as duplicate


def make(tmp_path, *, different_parameters=False, running_collection=False):
    raw, review = tmp_path/'raw', tmp_path/'terminal'
    snapshot = review/'metadata_snapshot'
    hashes, attempts = {}, []
    fixture = dict(category='person', split='train', id='person_train_0000', seed=42,
                   active_physical_parameters={'mass':.1})
    fixture['physical_config_sha256'] = duplicate.digest(fixture['active_physical_parameters'])
    for phase, folder in (('search','search/person/vmc/c00/0'),('collection','collection/person_train_0000/vmc')):
        path = raw/folder; path.mkdir(parents=True)
        x = [1.] if different_parameters and phase == 'collection' else [0.]
        request = dict(fixture=fixture, method='vmc', phase=phase, x=x, teacher={'gain':x[0]+1})
        (path/'request.json').write_text(json.dumps(request))
        execution = dict(status='running' if running_collection and phase=='collection' else 'completed', returncode=0)
        (path/'execution.json').write_text(json.dumps(execution))
        # Same arrays, different NPZ container/compression.
        save = np.savez if phase == 'search' else np.savez_compressed
        save(path/'rollout.npz', time=np.arange(5.), strings=np.array(['a','b']), missing=np.array([np.nan]))
        if running_collection and phase == 'collection': (path/'rollout.npz').write_bytes(b'not-an-npz')
        audit = dict(fixture_id=fixture['id'], method='vmc', split='train', model_sha256='a'*64,
            eligible=True, esn_label_eligible=True, files_sha256={
                name:duplicate.sha(path/name) for name in ('request.json','rollout.npz')})
        (path/'audit.json').write_text(json.dumps(audit))
        for name in ('request.json','audit.json','execution.json'):
            dest=snapshot/folder/name;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes((path/name).read_bytes());hashes[folder+'/'+name]=duplicate.sha(dest)
        attempts.append(dict(folder=folder, split='train', status='running_confirmed'
            if running_collection and phase=='collection' else 'eligible'))
    report = dict(original_run=str(raw),metadata_sha256=hashes,status={'attempts':attempts},
        closeout=dict(bank_certified_locked=True,reconstructed_groups={'person/vmc':dict(
            best_complete_candidate={'index':0,'x':[0.]},selected_controller_config={'gain':1.},
            candidates=[dict(index=0,anchors=[{'folder':'search/person/vmc/c00/0'}])])}))
    (review/'review.json').write_text(json.dumps(report))
    return raw,review


def test_repeat_does_not_inflate_unique_data_and_container_difference_is_not_value_difference(tmp_path):
    raw,review=make(tmp_path)
    report=duplicate.review_duplicates(review,raw,tmp_path/'out',duplicate.sha(review/'review.json'),True)
    row=report['accounting'][0]
    assert row['completed_executions']==2 and row['duplicate_executions']==1
    assert row['unique_training_fixture_ids']==1 and row['unique_eligible_vmc_labels_any_phase']==1
    assert row['unique_eligible_vmc_labels_collection']==1
    pair=report['selected_search_collection_pairs'][0]
    assert pair['all_npz_arrays_equal']
    assert not pair['files'][0]['zip_file_bytes_equal']


def test_different_controller_is_not_same_execution_identity(tmp_path):
    raw,review=make(tmp_path,different_parameters=True)
    report=duplicate.review_duplicates(review,raw,tmp_path/'out',duplicate.sha(review/'review.json'),True)
    assert not report['duplicate_identity_groups']
    assert not report['selected_search_collection_pairs']
    assert report['accounting'][0]['unique_eligible_vmc_labels_any_phase']==1


def test_running_collection_npz_is_never_opened(tmp_path):
    raw,review=make(tmp_path,running_collection=True)
    report=duplicate.review_duplicates(review,raw,tmp_path/'out',duplicate.sha(review/'review.json'),True)
    assert not report['selected_search_collection_pairs']
    assert report['accounting'][0]['completed_executions']==1
    assert len(report['skipped_incomplete_or_invalid'])==1


def test_content_difference_is_detected(tmp_path):
    a,b=tmp_path/'a.npz',tmp_path/'b.npz'
    np.savez(a,state=np.array([1.,2.]))
    np.savez_compressed(b,state=np.array([1.,3.]))
    result=duplicate.compare_npz(a,b)
    assert not result['arrays_equal']
    assert not result['members'][0]['values_equal']
