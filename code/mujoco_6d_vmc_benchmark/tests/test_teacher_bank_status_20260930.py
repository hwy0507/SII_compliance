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
            execution_status='completed', returncode=0, receipt=False, x=None, model_hash='a'*64):
    folder = root/relative
    phash = status.sha(root/'plan.json')
    put(folder/'request.json', dict(fixture=fixture, method=method, phase=phase, plan_sha256=phash,
                                   teacher={'gain':1.}, x=x))
    put(folder/'execution.json', dict(status=execution_status, returncode=returncode,
        host='remote-host', started=1., finished=3., plan_sha256=phash))
    put(folder/'audit.json', dict(fixture_id=fixture['id'], split=fixture['split'], method=method,
        eligible=eligible, esn_label_eligible=eligible and method=='vmc',
        model_sha256=model_hash,
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


def verified_rollout(folder, events, **flags):
    put(folder/'rollout.json', dict(stats=dict(events=events), **flags))
    audit = status.read_json(folder/'audit.json')
    audit['files_sha256'] = {'rollout.json':status.sha(folder/'rollout.json')}
    put(folder/'audit.json', audit)


def test_contact_events_preserve_metadata_without_counting_support_as_edge(tmp_path):
    root, fixtures = campaign(tmp_path)
    folder = attempt(root, fixtures[0], 'completed')
    edge = dict(peak_n=1350., impulse_ns=.4, robot_parts=['hand'], first_s=2., duration_s=.001)
    top = dict(peak_n=9999., impulse_ns=2., robot_parts=['payload'])
    verified_rollout(folder, {'office_v5_corner_face':edge, 'office_v5_corner_top':top}, task_success=True)
    report = status.summarize(root)
    contact = report['attempts'][0]['contact_metadata']
    assert contact['available']
    assert contact['actual_sha256'] == contact['expected_sha256']
    assert contact['events']['office_v5_corner_top'] == top
    assert contact['relevant_events'] == {'office_v5_corner_face':edge}
    assert report['method_category'][0]['metrics_all_completed']['peak_torque_nm']['maximum'] == 40.
    rendered = status.markdown(report)
    assert '1350.0' in rendered and '9999' not in rendered
    assert 'not independent physical-substep recomputation' in rendered


@pytest.mark.parametrize('category,apparatus,event', [
    ('active_short', 'rod', 'ball'), ('active_long', 'person', 'person_hand'),
    ('active_long', 'rod', 'rod')])
def test_contact_category_selection_and_false_evaluator_fields(tmp_path, category, apparatus, event):
    folder = tmp_path/'case'
    folder.mkdir()
    events = {name:dict(peak_n=1., impulse_ns=.1, robot_parts=['hand'])
              for name in ('ball', 'person_hand', 'rod')}
    put(folder/'rollout.json', dict(stats=dict(events=events), ball_rebound=False,
                                   strict_success=False, task_success=True))
    audit = dict(files_sha256={'rollout.json':status.sha(folder/'rollout.json')},
                 failure_reasons=['evaluator_strict_failure'])
    contact = status.contact_metadata(folder, dict(category=category, apparatus=apparatus), audit)
    assert list(contact['relevant_events']) == [event]
    assert contact['evaluator_booleans']['ball_rebound'] is False
    assert 'strict_success' in contact['evaluator_false_fields']
    assert contact['audit_failure_reasons'] == ['evaluator_strict_failure']


def test_contact_missing_and_mismatched_hashes_do_not_change_primary_status(tmp_path, monkeypatch):
    root, fixtures = campaign(tmp_path)
    folder = attempt(root, fixtures[0], 'completed')
    report = status.summarize(root)
    assert report['attempts'][0]['contact_metadata']['reason'] == 'missing_or_invalid_rollout_audit_hash'
    verified_rollout(folder, {'ball':dict(peak_n=5.)})
    (folder/'rollout.json').write_text('changed invalid JSON')
    report = status.summarize(root)
    assert report['attempts'][0]['contact_metadata']['reason'] == 'rollout_audit_hash_mismatch'
    assert report['attempt_counts']['eligible'] == 1


def test_noncompleted_rollout_metadata_is_not_read(tmp_path, monkeypatch):
    root, fixtures = campaign(tmp_path)
    folder = attempt(root, fixtures[0], 'running', execution_status='running')
    verified_rollout(folder, {'ball':dict(peak_n=5.)})
    def forbidden(*args, **kwargs):
        raise AssertionError('Running rollout was read')
    monkeypatch.setattr(status, 'contact_metadata', forbidden)
    report = status.summarize(root)
    assert 'contact_metadata' not in report['attempts'][0]


def search_campaign(tmp_path, count=3):
    root, fixtures=campaign(tmp_path)
    plan=json.loads((root/'plan.json').read_text())
    plan.update(search_candidates_per_category=count, anchor_indices=[0,1])
    put(root/'plan.json',plan)
    return root,fixtures


def candidate(root,fixtures,method,index,anchors=(0,1),history=True,model_hash='a'*64):
    x=[index/10.]
    base=root/f'search/passive_corner/{method}/c{index:02d}'
    put(base/'decision.json',dict(x=x))
    for anchor in anchors:
        attempt(root,fixtures[anchor],str((base/str(anchor)).relative_to(root)),method=method,
                phase='search',x=x,model_hash=model_hash,eligible=anchor==0)
    if history:
        path=base.parent/'history.json'
        rows=json.loads(path.read_text()) if path.exists() else []
        rows.append(dict(index=index,x=x,total=2,eligible_count=1,score=1.,constraint=1.))
        put(path,rows)
    return base


def test_partial_deadline_budget_excludes_extra_method_candidates(tmp_path):
    root,fixtures=search_campaign(tmp_path)
    for method in ('vmc','impedance'):candidate(root,fixtures,method,0)
    candidate(root,fixtures,'vmc',1)
    candidate(root,fixtures,'impedance',1,anchors=(0,),history=False)
    put(root/'teacher_bank.json',{'passive_corner/vmc':[dict(index=1,x=[.1])]})
    report=status.summarize(root,now=101.)
    search=report['search_progress']
    methods={r['method']:r for r in search['method_category']}
    assert methods['vmc']['complete_candidate_count']==2
    assert methods['impedance']['complete_candidate_count']==1
    assert search['category'][0]['common_complete_prefix_indices']==[0]
    assert search['category'][0]['comparable_anchor_evaluations_per_method']==2
    assert search['category'][0]['complete_candidates_outside_comparison']['vmc']==[1]
    assert search['partial_blocks_at_deadline'][0]['candidate_index']==1
    assert search['bank_state']=='provisional_not_locked'
    assert 'not an equal-budget controller comparison' in status.markdown(report)


def test_out_of_order_complete_candidate_does_not_extend_common_prefix(tmp_path):
    root,fixtures=search_campaign(tmp_path)
    for method in ('vmc','impedance'):candidate(root,fixtures,method,1)
    search=status.summarize(root)['search_progress']
    assert all(r['complete_candidate_count']==1 for r in search['method_category'])
    assert search['category'][0]['common_complete_prefix_count']==0
    assert search['category'][0]['complete_candidates_outside_comparison']['vmc']==[1]


def test_history_cannot_invent_completed_candidates_or_lock(tmp_path):
    root,fixtures=search_campaign(tmp_path,count=1)
    candidate(root,fixtures,'vmc',0,anchors=(0,))
    put(root/'anchor_feasibility.json',{'infeasible_method_categories':[]})
    put(root/'teacher_bank.json',{'passive_corner/vmc':[dict(index=0,x=[0.])]})
    search=status.summarize(root)['search_progress']
    assert search['method_category'][0]['history_without_complete_evidence']==[0]
    assert search['method_category'][0]['complete_candidate_count']==0
    assert not search['full_search_evidence_complete']
    assert search['bank_state']=='provisional_not_locked'


def test_lock_requires_complete_search_matching_bank_and_post_search_marker(tmp_path):
    root,fixtures=search_campaign(tmp_path,count=1)
    bank={}
    for method in ('vmc','impedance'):
        candidate(root,fixtures,method,0)
        bank['passive_corner/'+method]=[dict(index=0,x=[0.],anchor_feasible=False)]
    put(root/'teacher_bank.json',bank)
    assert status.summarize(root)['search_progress']['bank_state']=='provisional_not_locked'
    put(root/'anchor_feasibility.json',{'infeasible_method_categories':list(bank)})
    assert status.summarize(root)['search_progress']['bank_state']=='locked_after_complete_search'
    bank['passive_corner/vmc'][0]['x']=[.9];put(root/'teacher_bank.json',bank)
    assert status.summarize(root)['search_progress']['bank_state']=='provisional_not_locked'


def test_complete_counts_do_not_establish_pairing_when_model_hashes_differ(tmp_path):
    root,fixtures=search_campaign(tmp_path,count=1)
    candidate(root,fixtures,'vmc',0)
    candidate(root,fixtures,'impedance',0,model_hash='b'*64)
    search=status.summarize(root)['search_progress']
    assert all(r['complete_candidate_count']==1 for r in search['method_category'])
    assert search['category'][0]['common_complete_prefix_count']==0
    assert search['partial_blocks'][0]['all_methods_complete']
    assert not search['partial_blocks'][0]['model_pairing_verified']


def test_pilot_reuse_and_recovery_are_logical_anchors_not_double_budget(tmp_path):
    root,fixtures=search_campaign(tmp_path,count=1)
    base=candidate(root,fixtures,'vmc',0,anchors=())
    origin0=str((base/'0').relative_to(root))
    pilot=attempt(root,fixtures[0],'pilot/passive_corner/vmc',phase='pilot',x=[0.])
    put(root/'reuse_records'/(origin0+'.json'),dict(reused_relative=str(pilot.relative_to(root)),
        request_sha256=status.sha(pilot/'request.json')))
    origin1=str((base/'1').relative_to(root))
    attempt(root,fixtures[1],origin1,phase='search',x=[0.],execution_status='interrupted',returncode=1)
    retry='recovery_attempts/'+origin1+'/retry0001'
    attempt(root,fixtures[1],retry,phase='search',x=[0.],eligible=False)
    put(root/'recovery_records'/(origin1+'.json'),dict(origin_relative=origin1,active_relative=retry))
    candidate(root,fixtures,'impedance',0)
    search=status.summarize(root)['search_progress']
    assert search['method_category'][0]['complete_candidate_count']==1
    assert search['category'][0]['comparable_anchor_evaluations_per_method']==2
    assert search['category'][0]['common_complete_prefix_indices']==[0]


def test_completion_after_deadline_does_not_erase_cutoff_partial_block(tmp_path):
    root,fixtures=search_campaign(tmp_path,count=1)
    candidate(root,fixtures,'vmc',0)
    folder=candidate(root,fixtures,'impedance',0)/'1'
    execution=json.loads((folder/'execution.json').read_text())
    execution.update(started=99.,finished=103.)
    put(folder/'execution.json',execution)
    search=status.summarize(root,now=104.)['search_progress']
    assert search['category'][0]['common_complete_prefix_count']==1
    assert search['partial_blocks']==[]
    cutoff=search['partial_blocks_at_deadline']
    assert len(cutoff)==1
    assert cutoff[0]['methods']['impedance']['completed_anchors']==1
    assert cutoff[0]['methods']['vmc']['completed_anchors']==2
