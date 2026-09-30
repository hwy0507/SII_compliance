"""Status accounting separates fixture design, usable data and infrastructure."""
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import teacher_bank_status_20260930 as status


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def campaign(tmp_path):
    root = tmp_path/'campaign'
    fixtures = [dict(id='train0', category='passive_corner', split='train'),
                dict(id='train1', category='passive_corner', split='train'),
                dict(id='val0', category='passive_corner', split='validation')]
    put(root/'fixtures.json', fixtures)
    put(root/'plan.json', dict(categories=['passive_corner'], methods=['vmc', 'impedance'],
        train_per_category=1000, fixtures_sha256=status.sha(root/'fixtures.json'),
        deadline_epoch=100., max_total_attempts=10000, sources={'example.py':'source-hash'}))
    return root, fixtures


def attempt(root, fixture, relative, *, method='vmc', phase='collection', eligible=True,
            execution_status='completed', returncode=0, receipt=False):
    folder = root/relative
    phash = status.sha(root/'plan.json')
    put(folder/'request.json', dict(fixture=fixture, method=method, phase=phase, plan_sha256=phash,
                                   teacher={'gain':1.}))
    put(folder/'execution.json', dict(status=execution_status, returncode=returncode,
        host='remote-host', started=1., finished=3., plan_sha256=phash))
    put(folder/'audit.json', dict(fixture_id=fixture['id'], split=fixture['split'], method=method,
        eligible=eligible, esn_label_eligible=eligible and method=='vmc',
        failure_reasons=[] if eligible else ['required_contact_missing'],
        rmse_m=.01, peak_torque_nm=40., peak_speed_mps=.1, penetration_mm=.1))
    if receipt:
        put(root/'archive_receipts'/relative/'receipt.json',
            dict(verified_path='arm1@server:/shared/'+relative, verified_at=3.))
    return folder


def test_definition_counts_do_not_inflate_deduplicated_teacher_data(tmp_path):
    root, fixtures = campaign(tmp_path)
    attempt(root, fixtures[0], 'search/original', phase='search')
    attempt(root, fixtures[0], 'collection/repeat', receipt=True)
    attempt(root, fixtures[0], 'collection/another-repeat')
    attempt(root, fixtures[2], 'validation/executed', phase='validation')
    attempt(root, fixtures[1], 'collection/impedance', method='impedance')
    report = status.summarize(root, now=101.)
    assert report['total_definitions'] == 3
    assert report['attempts_total'] == 5
    vmc = report['vmc_training_data']['passive_corner']
    assert vmc['unique_eligible_train_any_phase'] == 1
    assert vmc['unique_eligible_train_collection'] == 1
    assert vmc['collection_shortfall'] == 999
    assert report['archive_counts']['recorded_verified_receipt'] == 1
    assert report['budget']['deadline_reached']
    assert report['budget']['completed_attempt_wall_seconds'] == 10.


def test_failed_process_with_eligible_audit_never_becomes_teacher_data(tmp_path):
    root, fixtures = campaign(tmp_path)
    attempt(root, fixtures[0], 'failed', execution_status='failed', returncode=1)
    attempt(root, fixtures[1], 'physical-failure', eligible=False)
    report = status.summarize(root)
    assert report['attempt_counts']['infrastructure_failed'] == 1
    assert report['attempt_counts']['physical_failure'] == 1
    assert report['failure_reasons'] == {'required_contact_missing':1}
    assert report['vmc_training_data']['passive_corner']['unique_eligible_train_any_phase'] == 0
    assert report['method_category'][0]['metrics_all_completed']['rmse_m']['count'] == 1


def test_running_unverified_host_and_corrupt_metadata_are_separate(tmp_path):
    root, fixtures = campaign(tmp_path)
    attempt(root, fixtures[0], 'remote-running', execution_status='running', returncode=None)
    folder = attempt(root, fixtures[1], 'invalid-audit')
    (folder/'audit.json').write_text('{"eligible":NaN}')
    report = status.summarize(root)
    assert report['attempt_counts']['running_unverified_host'] == 1
    assert report['attempt_counts']['incomplete_or_invalid_evidence'] == 1
    assert report['vmc_training_data']['passive_corner']['unique_eligible_train_any_phase'] == 0


def test_plan_binding_mismatch_does_not_count_valid_data(tmp_path):
    root, fixtures = campaign(tmp_path)
    folder = attempt(root, fixtures[0], 'changed-request')
    request = json.loads((folder/'request.json').read_text())
    request['plan_sha256'] = 'wrong'
    put(folder/'request.json', request)
    report = status.summarize(root)
    assert report['attempt_counts']['incomplete_or_invalid_evidence'] == 1
    assert 'request_plan_hash_mismatch' in report['attempts'][0]['errors']


def test_no_unexecuted_validation_or_source_results_are_opened(tmp_path, monkeypatch):
    root, fixtures = campaign(tmp_path)
    sealed = root/'validation/unexecuted/private.json'
    put(sealed, {'do_not_read': True})
    source = root/'source/outputs/audit.json'
    put(source, {'do_not_read': True})
    original = status.read_json
    def checked(path):
        assert Path(path) not in (sealed, source)
        return original(path)
    monkeypatch.setattr(status, 'read_json', checked)
    report = status.summarize(root)
    assert report['attempts_total'] == 0


def test_report_output_is_external_nonoverwriting_and_run_unchanged(tmp_path):
    root, fixtures = campaign(tmp_path)
    attempt(root, fixtures[0], 'completed')
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    report = status.summarize(root)
    with pytest.raises(ValueError, match='outside'):
        status.write_reports(report, root/'report')
    paths = status.write_reports(report, tmp_path/'reports/status')
    assert all(p.is_file() for p in paths)
    assert json.loads(paths[0].read_text())['provenance']['plan_sha256'] == status.sha(root/'plan.json')
    assert 'VMC train' in paths[1].read_text()
    with pytest.raises(FileExistsError):
        status.write_reports(report, tmp_path/'reports/status')
    after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    assert before == after
