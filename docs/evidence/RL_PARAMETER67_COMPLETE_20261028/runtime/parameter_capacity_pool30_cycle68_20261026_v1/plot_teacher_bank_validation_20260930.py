"""Render a SHA-pinned fixed-policy comparison; never read live experiments.

Only the common full-horizon three-method metric cohort is plotted. Outcomes
remain counted for paired short/failed episodes in the evidence sidecar.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

METHODS = ('vmc', 'admittance', 'impedance')
CATEGORIES = ('passive_corner', 'active_short', 'active_long')
COLORS = ('#0072B2', '#D55E00', '#009E73')
LABELS = ('Thick corner', 'Short impact', 'Sustained push')
METRICS = (('rmse_m', 1000., 'Stage-waypoint RMSE (mm)'),
           ('peak_torque_nm', 1., 'Episode peak motor torque (Nm)'),
           ('peak_speed_mps', 1., 'Episode peak EE speed (m/s)'))
SCOPE = 'preregistered_validation'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract(path, expected):
    path = Path(path).resolve()
    if sha(path) != expected:
        raise ValueError('Comparison SHA256 mismatch')
    report = json.loads(path.read_text())
    if report.get('bank_certified_locked') is not True:
        raise ValueError('Certified locked bank required')
    if report.get('expected_duration_s') != 55.:
        raise ValueError('Expected the registered 55 s horizon')
    rows = [r for r in report['rows'] if r['scope'] == SCOPE]
    if len({r['folder'] for r in rows}) != len(rows):
        raise ValueError('Duplicate attempt folder')
    groups = defaultdict(list)
    for row in rows:
        if row['method'] not in METHODS or row['category'] not in CATEGORIES:
            raise ValueError('Unexpected method/category')
        groups[row['category'], row['fixture_id']].append(row)
    points, omitted = [], []
    for (category, fixture), members in sorted(groups.items()):
        flags = [r.get('paired_metric_episode') is True for r in members]
        if any(flags) and not all(flags):
            raise ValueError('Metric cohort differs across paired methods')
        if not any(flags):
            omitted.append(dict(category=category, fixture_id=fixture,
                folders=[r['folder'] for r in members],
                reasons=[r.get('metric_exclusion_reason') for r in members]))
            continue
        if sorted(r['method'] for r in members) != sorted(METHODS):
            raise ValueError('Metric cohort lacks all three methods')
        if len({r['model_sha256'] for r in members}) != 1:
            raise ValueError('Paired model mismatch')
        for row in members:
            if (row.get('pair_state') != 'paired' or row.get('same_full_duration') is not True
                    or row.get('completed_execution') is not True
                    or row.get('matches_locked_parameters') is not True):
                raise ValueError('Incomplete or unlocked metric evidence')
            if any(type(row.get(flag)) is not bool for flag in ('task', 'strict', 'exposure', 'eligible')):
                raise ValueError('Unknown outcome in plotted cohort')
            for key, _, _ in METRICS:
                value = row.get(key)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    raise ValueError('Missing or invalid metric')
            points.append(row)
    summaries = []
    for category in CATEGORIES:
        for method in METHODS:
            paired = [r for r in rows if r['category'] == category and r['method'] == method
                      and r['pair_state'] == 'paired']
            summaries.append(dict(category=category, method=method, paired_n=len(paired),
                metric_n=sum(r['category'] == category and r['method'] == method for r in points),
                outcomes={flag:{str(value):sum(r[flag] == value for r in paired)
                    for value in (True, False, 'unknown')}
                    for flag in ('task', 'strict', 'exposure', 'eligible')}))
    return dict(comparison_path=str(path), comparison_sha256=expected,
        comparison_input_review_sha256=report['input_review_sha256'],
        plot_script_sha256=sha(__file__), points=points, omitted_fixture_groups=omitted,
        excluded_validation_attempts=[r for r in report['rows']
            if r.get('phase') == 'validation' and r['scope'] != SCOPE],
        paired_outcomes=summaries, scope=SCOPE,
        semantics='All methods use the same complete full-horizon metric cohort, including task/strict/exposure failures. Short or unpaired cases are omitted from metric means for all methods and retained in paired outcome counts. Saved comparison values, not new raw-trajectory recomputation. These are development validation cases, not the frozen combined test or ESN results.',
        execution=dict(argv=[sys.executable, *sys.argv], cwd=str(Path.cwd()),
            hostname=platform.node(), python=platform.python_version(),
            started_utc=datetime.now(timezone.utc).isoformat()))


def render(data, output):
    output = Path(output).resolve()
    source = Path(data['comparison_path']).parent
    if output == source or source in output.parents:
        raise ValueError('Output must be outside original comparison')
    if output.exists():
        raise FileExistsError('Never overwrite a plot artifact')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    output.mkdir(parents=True)
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(3, 3, figsize=(13.5, 11))
    for i, category in enumerate(CATEGORIES):
        points = [r for r in data['points'] if r['category'] == category]
        fixtures = sorted({r['fixture_id'] for r in points})
        offsets = {f: .24 * (j/(len(fixtures)-1)-.5) if len(fixtures)>1 else 0.
                   for j, f in enumerate(fixtures)}
        for j, (metric, scale, ylabel) in enumerate(METRICS):
            ax = axes[i, j]
            for k, (method, color) in enumerate(zip(METHODS, COLORS)):
                selected = [r for r in points if r['method'] == method]
                for row in selected:
                    ax.scatter(k+offsets[row['fixture_id']], row[metric]*scale,
                        color=color, s=70, marker='o' if row['eligible'] else 'X', zorder=3,
                        edgecolors='white', linewidths=.55)
                if selected:
                    mean = sum(r[metric]*scale for r in selected)/len(selected)
                    ax.plot([k-.22, k+.22], [mean, mean], color='#222222', lw=1.4, zorder=2)
            ax.set_xticks(range(3), ['VMC', 'Admittance', 'Impedance'])
            ax.set_ylabel(ylabel)
            ax.set_title(f'{LABELS[i]} · {len(fixtures)} full-horizon fixtures / method', fontsize=10, loc='left')
            ax.set_xlim(-.5, 2.5)
            ax.grid(axis='y', alpha=.18)
            ax.margins(y=.2)
            if not points:
                ax.text(.5, .5, 'No complete paired metric cohort', ha='center', transform=ax.transAxes)
    handles = [Line2D([], [], color='#666666', marker=m, linestyle='', markersize=8, label=label)
               for m, label in (('o', 'Admitted'), ('X', 'Retained non-admitted episode'))]
    handles.append(Line2D([], [], color='#222222', lw=1.4, label='Mean including failures'))
    fig.suptitle('Locked-controller validation · common 55 s metric cohort', fontsize=16, y=.99)
    fig.legend(handles=handles, loc='upper center', bbox_to_anchor=(.5, .965), ncol=3, frameon=False)
    fig.text(.5, .025, 'Same fixture and model across methods; success-only filtering is not used.\n'
        'Common 55 s cohort; omitted groups, excluded validation attempts and paired outcomes are in plot_evidence.json.\n'
        'RMSE uses stage waypoints. Motor torque is not contact force. Speed is reported, not maximized.',
        ha='center', fontsize=9, color='#444444')
    fig.tight_layout(rect=(0, .085, 1, .935), h_pad=2.2, w_pad=2.2)
    for suffix in ('png', 'pdf'):
        fig.savefig(output/('locked_validation.'+suffix), dpi=180, facecolor='white')
    plt.close(fig)
    data['execution']['finished_utc'] = datetime.now(timezone.utc).isoformat()
    (output/'plot_evidence.json').write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    manifest = {p.name:sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    (output/'files_sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--comparison', type=Path, required=True)
    parser.add_argument('--comparison-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = extract(args.comparison, args.comparison_sha256)
    render(data, args.output)
    print(json.dumps(dict(points=len(data['points']), omitted_groups=len(data['omitted_fixture_groups']),
                          output=str(args.output))))


if __name__ == '__main__':
    main()
