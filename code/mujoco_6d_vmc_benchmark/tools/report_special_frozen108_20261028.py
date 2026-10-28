"""Render the complete audited special-scene comparison; never select models.

Requires the real new108 audit and its unchanged report/model lock. This is
presentation of saved audited metrics, not another physics certification.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from audit_special_frozen108_20261028 import summaries
from prepare_special_frozen_test_20261028 import read, sha, require


FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
LABELS = ('ESN (ridge)', 'RNN', 'MLP')
METRICS = (
    ('task_success_rate', 'Task success (%)', 100),
    ('strict_success_rate', 'Strict success (%)', 100),
    ('spt_mean', 'SPT | Task AND Strict success', 1),
    ('peak_torque_mean_nm', 'Mean episode peak torque (Nm)', 1),
    ('human_comfort_torque_compliance_contact_time_weighted', 'Contact-time comfort proxy (%)', 100),
    ('machine_compliance_rate', 'Machine compliance (%)', 100),
)


def load_verified(audit_path):
    audit = read(audit_path)
    require(audit['status'] == 'frozen108_saved_evidence_audit_passed'
            and audit['verified_episodes'] == 108, 'Complete new108 audit required')
    prep = Path(audit['preparation'])
    plan, done = read(prep / 'REGISTRATION.json'), read(prep / 'execution.json')
    require(done['status'] == 'evaluation_complete_pending_independent_audit', 'Dispatch incomplete')
    require(done['registration_sha256'] == sha(prep / 'REGISTRATION.json'), 'Preparation changed')
    root = Path(plan['evaluation'])
    require(sha(root / 'REPORT.json') == audit['report_sha256'] == done['report_sha256'], 'Report changed')
    require(sha(root / 'INPUT_MODEL_LOCK.json') == audit['model_lock_sha256'], 'Model lock changed')
    require(sha(Path(__file__).with_name('audit_special_frozen108_20261028.py'))
            == audit['auditor_sha256'], 'Auditor source changed')
    report, lock = read(root / 'REPORT.json'), read(root / 'INPUT_MODEL_LOCK.json')
    require(report['status'] == 'complete' and len(report['rows']) == 108, 'Incomplete matrix')
    models = {m['name']: m for m in lock['models']}
    ref, methods, families = summaries(report['rows'], models)
    require(ref == audit['t_ref_s'] and methods == audit['methods']
            and families == audit['family_summary'], 'Audit aggregate mismatch')
    require(set(families) == set(FAMILIES) and len(models) == 9, 'Wrong family coverage')
    return audit, root, lock, methods, families


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve previous reports')
    audit, root, lock, methods, families = load_verified(args.audit)
    args.output.mkdir(parents=True)
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), layout='constrained')
    colors = ('#246b9d', '#c46b17', '#4b8342')
    for ax, (key, title, scale) in zip(axes.flat, METRICS):
        for i, family in enumerate(FAMILIES):
            values = families[family][key]
            for j, (seed, value) in enumerate(zip(values['seeds'], values['per_seed'])):
                if value is not None:
                    ax.scatter(i + (j-1)*.12, value*scale, c=colors[j],
                               marker=('o', 's', '^')[j], s=35, zorder=3,
                               label=f'seed {seed}' if i == 0 else None)
            if values['mean'] is not None:
                ax.errorbar(i, values['mean']*scale, yerr=values['sample_sd']*scale,
                            fmt='_', color='black', markersize=18, capsize=5, zorder=4)
            else:
                ax.text(i, .03, 'mean: NA', ha='center', transform=ax.get_xaxis_transform(), fontsize=9)
        ax.set_xticks(range(3), LABELS)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(-.45, 2.45)
        ax.grid(axis='y', alpha=.2)
        if key != 'peak_torque_mean_nm':
            ax.set_ylim(-.06*scale, 1.12*scale)
        else:
            ax.set_ylim(bottom=0)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(f'{root.name}\nCurrent12 × 3 seeds per family | black: mean ± sample SD', fontsize=12)
    fig.savefig(args.output / 'six_metrics.png', dpi=160)
    plt.close(fig)
    lines = [f'# {root.name}', '',
        'Complete current12 comparison: 108 episodes, three seeds per family. '
        'These conditions were previously inspected; this is not a new unseen confirmation.', '',
        f"Global BOTH-success reference time: {audit['t_ref_s']} s.", '',
        'SPT includes only Task AND Strict successes. Torque includes every episode. '
        'Comfort uses actual human-contact duration and the frozen half-actuator-limit proxy; '
        'no contact means NA. Comfort is not a human safety calibration. '
        'Machine compliance uses the frozen penetration, actuator and abort checks.', '',
        '| Metric | ESN | RNN | MLP |', '|---|---:|---:|---:|']
    for key, title, scale in METRICS:
        cells = []
        for family in FAMILIES:
            v = families[family][key]
            cells.append('NA' if v['mean'] is None else f"{v['mean']*scale:.4f} ± {v['sample_sd']*scale:.4f}")
        lines.append('| ' + title + ' | ' + ' | '.join(cells) + ' |')
    lines += ['', 'Means and sample standard deviations are over three seed-level values; '
        'any missing seed value leaves the family aggregate NA. Conditional SPT compares '
        'different successful subsets and must be read alongside success counts.', '',
        '| Model | Task / 12 | Strict / 12 | BOTH / 12 | Contact duration (s) |',
        '|---|---:|---:|---:|---:|']
    for model in lock['models']:
        v = methods[model['name']]
        lines.append(f"| {model['name']} | {v['task_success']} | {v['strict_success']} | "
                     f"{v['both_success']} | {v['human_contact_duration_s_total']:.6f} |")
    lines += ['', f"Source report SHA256: `{audit['report_sha256']}`.",
              f"Model lock SHA256: `{audit['model_lock_sha256']}`.", '', audit['limitation'], '']
    (args.output / 'REPORT.md').write_text('\n'.join(lines))
    receipt = dict(status='rendered_from_complete_audited_new108',
        created_utc=datetime.now(timezone.utc).isoformat(), audit=str(args.audit.resolve()),
        audit_sha256=sha(args.audit), report_sha256=audit['report_sha256'],
        model_lock_sha256=audit['model_lock_sha256'], script_sha256=sha(Path(__file__)),
        figures={'six_metrics.png': sha(args.output / 'six_metrics.png')},
        markdown_sha256=sha(args.output / 'REPORT.md'))
    (args.output / 'PRESENTATION_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
