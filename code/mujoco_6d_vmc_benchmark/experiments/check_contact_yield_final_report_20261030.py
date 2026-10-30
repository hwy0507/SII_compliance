"""Synthetic presentation controls; never read final condition/trajectory files."""
import argparse
import copy
from pathlib import Path
import tempfile
from unittest.mock import patch
import report_contact_yield_final108_20261030 as presenter
from run_v9_unseen_matrix_20261030 import make_cases, SEEDS


def fixture(all_failed=False):
    models = [dict(name=f+'_s'+str(s), family=f, seed=s)
              for f in presenter.FAMILIES for s in SEEDS]
    conditions = [dict(id=scene+str(i), scene=scene) for scene in ('rod', 'ball', 'corner') for i in range(4)]
    cases = make_cases(models, conditions)
    rows = []
    for i, case in enumerate(cases):
        task, machine = not all_failed and i % 5 != 0, i % 7 != 0
        contact = 0 if i % 3 == 0 else .2
        rows.append(dict(method=case['model']['name'], condition=case['condition']['id'],
                         scene=case['condition']['scene'], task_success=task,
                         strict_success=task and machine, machine_compliant=machine,
                         completion_time_s=10+i/100 if task else None, peak_torque_nm=30+i/100,
                         human_contact_s=None, proxy_contact_s=contact,
                         proxy_below_threshold_s=contact/2))
    summary = presenter.aggregate(rows, [(r['method'], r['condition']) for r in rows])
    reg = dict(cases=cases, models=models)
    state = dict(status='complete_pending_independent_review', rows=[dict(id=c['id']) for c in cases])
    report = dict(status='verified_complete_isolated_unseen_matrix', rows=rows,
                  summary=summary, independent_replays=[dict(id=c['id'], actor_replay_max_abs=0,
                                                            filter_replay_max_abs=0) for c in cases])
    for key, fields in [('family', ('family',)), ('family_scene', ('family', 'scene'))]:
        report[key] = presenter.grouped(rows, models, summary['t_ref_s'], fields)
    return reg, state, report


def check():
    reg, state, report = fixture()
    presenter.verify_report(reg, state, report)
    reg0, state0, report0 = fixture(all_failed=True)
    presenter.verify_report(reg0, state0, report0)
    assert report0['summary']['t_ref_s'] is None
    assert all(r['spt_both_conditional'] is None for r in report0['family'])
    rejected = []
    cases = [
        ('missing_failed_row', lambda r: r['rows'].pop(0)),
        ('duplicate_row', lambda r: r['rows'].__setitem__(1, copy.deepcopy(r['rows'][0]))),
        ('false_tref', lambda r: r['summary'].update(t_ref_s=0)),
        ('changed_spt', lambda r: r['family'][0].update(spt_both_conditional=0)),
        ('fabricated_human_comfort', lambda r: r['family'][0].update(human_comfort=1)),
        ('actor_error', lambda r: r['independent_replays'][0].update(actor_replay_max_abs=.1)),
        ('replay_identity', lambda r: r['independent_replays'][0].update(id='wrong')),
    ]
    for name, alter in cases:
        bad = copy.deepcopy(report); alter(bad)
        try:
            presenter.verify_report(reg, state, bad)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError('Accepted '+name)
    import evaluate_contact_yield_unseen108_20261030 as adapter
    for name, handoff in [
        ('handoff_incomplete', dict(status='waiting_for_fixed27_review')),
        ('handoff_review_changed', dict(status='final108_verified_pending_delivery', review_sha256='old')),
    ]:
        with patch.object(presenter, 'read', side_effect=[reg, state, report, handoff]), \
             patch.object(presenter, 'sha', return_value='changed'), patch.object(adapter, 'check') as provenance:
            try:
                presenter.load()
            except AssertionError:
                pass
            else:
                raise AssertionError('Accepted '+name)
            assert provenance.call_count == 0
            rejected.append(name)
    with tempfile.TemporaryDirectory() as temp:
        target, output = Path(temp)/'synthetic_source', Path(temp)/'synthetic_presentation'
        target.mkdir()
        for name in ('REGISTRATION.json', 'execution.json', 'FINAL_REVIEW.json'):
            presenter.write(target/name, {'synthetic_control_only': True})
        with patch.object(presenter, 'TARGET', target), patch.object(presenter, 'load', return_value=(reg0, report0)):
            presenter.export(output)
            assert 'NA' in (output/'REPORT.md').read_text()
            csv = (output/'episodes.csv').read_text().splitlines()
            assert len(csv) == 109
            assert len(presenter.read(output/'PRESENTATION_RECEIPT.json')['artifacts']) == 7
            before = {p.name: presenter.sha(p) for p in output.iterdir()}
            try:
                presenter.export(output)
            except AssertionError:
                pass
            else:
                raise AssertionError('Existing presentation overwritten')
            assert before == {p.name: presenter.sha(p) for p in output.iterdir()}
    return dict(status='passed_synthetic_final108_presentation_controls',
                presenter_sha256=presenter.sha(Path(presenter.__file__)),
                checker_sha256=presenter.sha(Path(__file__)), rejected=rejected,
                all_failed_108_retained=True, no_success_spt_is_na=True,
                human_comfort_is_na=True, duplicate_export_rejected=True,
                real_final_files_read=False, physics_episodes=0,
                scope='Synthetic schema/aggregation and export glue only. No current108 result or physical certification.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); assert not args.output.exists()
    presenter.write(args.output, check())
    print('final presentation controls passed with synthetic108 only')
