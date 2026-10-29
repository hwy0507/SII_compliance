"""Present the complete independently reviewed current108 without reselection."""
import argparse
import csv
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read, sha, write
from special_scene_metrics_20261030 import aggregate
from run_v9_unseen_matrix_20261030 import grouped

TARGET = ROOT/'outputs/contact_yield_isolated_unseen108_20261030_v1'
HANDOFF = ROOT/'outputs/contact_yield_final108_handoff_20261030_v1'
FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
LABELS = ('ESN (ridge)', 'RNN', 'MLP')
METRICS = (
    ('task_rate', 'Task success (%)', 100),
    ('strict_rate', 'Strict success (%)', 100),
    ('spt_both_conditional', 'SPT | Task AND Strict', 1),
    ('peak_torque_mean_nm', 'Mean episode peak torque (Nm)', 1),
    ('human_comfort', 'Human comfort: unmeasured', 100),
    ('machine_compliance_rate', 'Machine compliance (%)', 100),
)


def verify_report(reg, state, report):
    assert report['status'] == 'verified_complete_isolated_unseen_matrix'
    assert state['status'] == 'complete_pending_independent_review'
    assert len(reg['cases']) == len(state['rows']) == len(report['rows']) == 108
    ids = [c['id'] for c in reg['cases']]
    assert len(set(ids)) == 108 and [r['id'] for r in state['rows']] == ids
    assert [r['id'] for r in report['independent_replays']] == ids
    assert all(r['actor_replay_max_abs'] == r['filter_replay_max_abs'] == 0
               for r in report['independent_replays'])
    expected = [(c['model']['name'], c['condition']['id']) for c in reg['cases']]
    assert [(r['method'], r['condition']) for r in report['rows']] == expected
    summary = aggregate(report['rows'], expected)
    assert report['summary'] == summary
    for key, fields in [('family', ('family',)), ('family_scene', ('family', 'scene'))]:
        assert report[key] == grouped(report['rows'], reg['models'], summary['t_ref_s'], fields)
    assert len(report['family']) == 3 and {r['family'] for r in report['family']} == set(FAMILIES)
    assert all(r['episodes'] == 36 and r['human_comfort'] is None for r in report['family'])
    return summary


def load():
    # Source/provenance checks reuse the exact new-model registration adapter.
    # This function is never called by synthetic presentation controls.
    import evaluate_contact_yield_unseen108_20261030 as adapter
    reg = read(TARGET/'REGISTRATION.json')
    state = read(TARGET/'execution.json')
    report = read(TARGET/'FINAL_REVIEW.json')
    handoff = read(HANDOFF/'execution.json')
    assert handoff['status'] == 'final108_verified_pending_delivery'
    assert handoff['review_sha256'] == sha(TARGET/'FINAL_REVIEW.json')
    adapter.check(reg)
    assert report['registration_sha256'] == state['registration_sha256'] == sha(TARGET/'REGISTRATION.json')
    assert report['execution_sha256'] == sha(TARGET/'execution.json')
    assert report['reviewer_sha256'] == sha(ROOT/'tools/run_v9_unseen_matrix_20261030.py')
    verify_report(reg, state, report)
    return reg, report


def table(rows, columns):
    lines = ['| '+' | '.join(label for _, label, _ in columns)+' |',
             '| '+' | '.join('---' for _ in columns)+' |']
    for row in rows:
        values = []
        for key, _, scale in columns:
            value = row[key]
            values.append('NA' if value is None else f'{value*scale:.6g}'
                          if isinstance(value, (int, float)) else str(value))
        lines.append('| '+' | '.join(values)+' |')
    return '\n'.join(lines)


def export(output):
    assert not output.exists(), 'Preserve previous reports'
    reg, report = load()
    bound = {name: sha(TARGET/name) for name in ('REGISTRATION.json', 'execution.json', 'FINAL_REVIEW.json')}
    output.mkdir(parents=True)
    for name, rows in [('episodes', report['rows']), ('methods', report['summary']['methods']),
                       ('families', report['family']), ('family_scene', report['family_scene'])]:
        # Nested per-episode audit records remain in the original JSON; scalar
        # CSV values preserve None as NA rather than fabricated zeros.
        columns = sorted({k for row in rows for k, value in row.items()
                          if not isinstance(value, (dict, list))})
        with (output/(name+'.csv')).open('x', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns)
            writer.writeheader()
            writer.writerows({k: 'NA' if row.get(k) is None else row[k] for k in columns} for row in rows)
    families = {r['family']: r for r in report['family']}
    fig, axes = plt.subplots(2, 3, figsize=(12, 7), layout='constrained')
    for ax, (key, label, scale) in zip(axes.flat, METRICS):
        for i, family in enumerate(FAMILIES):
            value = families[family][key]
            if value is None:
                ax.text(i, .5, 'NA', ha='center', transform=ax.get_xaxis_transform())
            else:
                ax.bar(i, value*scale, color=('#0072B2', '#009E73', '#D55E00')[i])
        ax.set_xticks(range(3), LABELS); ax.set_xlim(-.6, 2.6)
        ax.set_title(label, fontsize=10); ax.grid(axis='y', alpha=.2)
        if key != 'peak_torque_mean_nm':
            ax.set_ylim(0, scale*1.08)
        else:
            ax.set_ylim(bottom=0)
    fig.suptitle('New isolated-scene test: all 108 episodes retained\nPooled family metrics: 36 episodes / 3 seeds each', fontsize=12)
    for ext in ('png', 'pdf'):
        fig.savefig(output/('six_metrics.'+ext), dpi=180)
    plt.close(fig)
    columns = [('family', 'Family', 1), ('episodes', 'Episodes', 1), *METRICS]
    lines = ['# New isolated-scene ESN/RNN/MLP comparison', '',
             'Complete independently reviewed 108-cell matrix. All failed episodes remain in denominators. '
             'Nine models were frozen before the test; this renderer performs no fitting or selection.', '',
             f"Global BOTH-success reference time T_ref: {report['summary']['t_ref_s']} s.", '',
             table([families[f] for f in FAMILIES], columns), '',
             'Family values pool 36 episodes across three seeds; they are not mean ± seed standard deviation. '
             'SPT conditions on Task AND Strict success and compares potentially different successful subsets. '
             'No BOTH-success episode gives SPT=NA. Peak torque averages every episode, including failures. '
             'Completion is confirmed at 13 sampled terminal states spanning 0.48 s, not a substep success proof.', '',
             'Human comfort is unmeasured (NA). Disturbance-contact torque compliance is a separate proxy, '
             'not evidence of human comfort or safety calibration. No measured proxy contact gives proxy=NA.', '',
             table(report['family'], [('family', 'Family', 1),
                   ('disturbance_contact_proxy_contact_s', 'Proxy contact (s)', 1),
                   ('disturbance_contact_proxy_compliance', 'Contact-time-weighted proxy (%)', 100)]), '',
             '## Model-level results', '',
             table(report['summary']['methods'], [('method', 'Model', 1),
                   ('episodes', 'Episodes', 1), ('task_success', 'Task', 1),
                   ('strict_success', 'Strict', 1), ('both_success', 'BOTH', 1), *METRICS[2:]]), '',
             'Scope: registered interpolation conditions only, not broad OOD. Historical composite-scene results '
             'remain separate and are not overwritten. See the immutable FINAL_REVIEW.json for per-episode '
             'failure reasons, physical-horizon audits, action/filter replay and original limitations.', '']
    (output/'REPORT.md').write_text('\n'.join(lines))
    for name, digest in bound.items():
        assert sha(TARGET/name) == digest
    write(output/'PRESENTATION_RECEIPT.json', dict(
        status='rendered_complete_verified_contact_yield108', source=str(TARGET),
        source_sha256=bound, presenter_sha256=sha(Path(__file__)),
        artifacts={p.name: sha(p) for p in output.iterdir()},
        no_new_physics=True, no_reselection=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); export(args.output.resolve())
