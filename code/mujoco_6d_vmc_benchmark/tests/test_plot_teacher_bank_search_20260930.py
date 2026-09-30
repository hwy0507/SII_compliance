import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import plot_teacher_bank_search_20260930 as plot


def fixture(tmp_path):
    root=tmp_path/'campaign'
    groups,attempts=[],[]
    for i,method in enumerate(plot.COLORS):
        folder='search/passive_corner/'+method+'/c00/0'
        audit=dict(fixture_id='fixture0',method=method,split='train',eligible=i==0,
                   model_sha256='a'*64,rmse_m=.01+i*.01,peak_torque_nm=40.+i,peak_speed_mps=.1)
        path=root/folder/'audit.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(audit))
        state='eligible' if i==0 else 'physical_failure'
        attempts.append(dict(folder=folder,category='passive_corner',method=method,split='train',
            phase='search',errors=[],status=state,fixture_id='fixture0',model_sha256='a'*64,
            metadata_sha256={'audit.json':hashlib.sha256(path.read_bytes()).hexdigest()}))
        groups.append(dict(category='passive_corner',method=method,candidates=[dict(index=0,complete=True,
            anchors=[dict(anchor_index=0,folder=folder,complete=True,errors=[],status=state,model_sha256='a'*64)])]))
    attempts.append(dict(folder='search/partial',category='passive_corner',method='vmc',phase='search',status='running'))
    report=dict(campaign_root=str(root),provenance=dict(fixtures_match_plan=True,plan_sha256='b'*64),
        generated_at_utc='2026-09-30T01:00:00Z',attempts=attempts,
        search_progress=dict(available=True,anchors_per_candidate=1,bank_state='provisional_not_locked',
            method_category=groups,category=[dict(category='passive_corner',common_complete_prefix_indices=[0],
            common_complete_prefix_count=1,blocks=[dict(candidate_index=0,all_methods_complete=True,model_pairing_verified=True)])]))
    report_path=tmp_path/'status.json'
    report_path.write_text(json.dumps(report))
    return report_path,report


def test_all_paired_failures_kept_and_partial_not_read(tmp_path):
    path,report=fixture(tmp_path)
    data=plot.extract_points(path)
    assert len(data['points'])==3
    assert sum(p['eligible'] for p in data['points'])==1
    assert data['categories'][0]['excluded_search_attempts']==1
    assert data['source_report_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    assert data['points'][2]['metrics']['peak_torque_nm']==42.


def test_changed_audit_rejected_instead_of_silently_omitting_point(tmp_path):
    path,report=fixture(tmp_path)
    audit=Path(report['campaign_root'])/report['attempts'][0]['folder']/'audit.json'
    audit.write_text('{}')
    with pytest.raises(ValueError,match='hash mismatch'):
        plot.extract_points(path)


def test_unverified_pair_rejected(tmp_path):
    path,report=fixture(tmp_path)
    report['search_progress']['category'][0]['blocks'][0]['model_pairing_verified']=False
    path.write_text(json.dumps(report))
    with pytest.raises(ValueError,match='Unverified paired'):
        plot.extract_points(path)


def test_output_never_overwrites_or_enters_campaign(tmp_path):
    path,report=fixture(tmp_path)
    data=plot.extract_points(path)
    with pytest.raises(ValueError,match='outside'):
        plot.render(data,Path(report['campaign_root'])/'plot')
    with pytest.raises(FileExistsError):
        plot.render(data,tmp_path)


def test_explicit_archive_mapping_preserves_source_and_evidence_hashes(tmp_path):
    path,report=fixture(tmp_path)
    original=plot.extract_points(path)
    before=path.read_bytes()
    source=Path(report['campaign_root'])
    archived=tmp_path/'server_archive'
    source.rename(archived)
    assert not source.exists()
    with pytest.raises(FileNotFoundError):
        plot.extract_points(path)
    mapped=plot.extract_points(path,archived)
    assert mapped['source_campaign_root']==str(source)
    assert mapped['campaign_root']==str(archived.resolve())
    assert mapped['points']==original['points']
    assert mapped['source_report_sha256']==original['source_report_sha256']
    assert path.read_bytes()==before
