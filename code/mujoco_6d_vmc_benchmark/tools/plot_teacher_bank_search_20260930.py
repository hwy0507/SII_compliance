"""Plot all paired completed training-search anchors; no simulation or selection.

Status JSON selects the common contiguous prefix. Its recorded audit hashes bind
the per-episode metrics, which older status schemas only store as aggregates.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

COLORS = {'vmc':'#0072B2', 'admittance':'#D55E00', 'impedance':'#009E73'}
LABELS = {'passive_corner':'Passive collision: thick corner',
          'active_short':'Short active impact: ball / impactor',
          'active_long':'Sustained active push: hand / rod'}
METRICS = ('rmse_m', 'peak_torque_nm', 'peak_speed_mps')


def read_bound(path, expected=None):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected is not None and digest != expected:
        raise ValueError('Evidence hash mismatch: '+str(path))
    value = json.loads(raw)
    json.dumps(value, allow_nan=False)
    return value, digest


def extract_points(report_path, campaign_root=None):
    report, digest = read_bound(report_path)
    search = report['search_progress']
    if not search.get('available') or not report['provenance'].get('fixtures_match_plan'):
        raise ValueError('Status lacks verified search / fixture evidence')
    source_root = report['campaign_root']
    root = Path(source_root if campaign_root is None else campaign_root).resolve()
    attempts = {r['folder']:r for r in report['attempts']}
    if len(attempts) != len(report['attempts']):
        raise ValueError('Duplicate attempt folders')
    groups = {(g['category'],g['method']):g for g in search['method_category']}
    points, categories, selected = [], [], set()
    for category in search['category']:
        name = category['category']
        indices = category['common_complete_prefix_indices']
        if indices != list(range(category['common_complete_prefix_count'])):
            raise ValueError('Noncontiguous claimed common prefix')
        methods = [m for c,m in groups if c == name]
        if set(methods) != set(COLORS):
            raise ValueError('Expected VMC, admittance, impedance matched methods')
        blocks = {b['candidate_index']:b for b in category['blocks']}
        for index in indices:
            if not blocks[index]['all_methods_complete'] or not blocks[index]['model_pairing_verified']:
                raise ValueError('Unverified paired candidate')
            pairing = {}
            for method in methods:
                candidates = {c['index']:c for c in groups[name,method]['candidates']}
                candidate = candidates[index]
                if not candidate['complete']:
                    raise ValueError('Incomplete candidate in common prefix')
                anchors = candidate['anchors']
                anchor_ids = [a['anchor_index'] for a in anchors]
                if len(set(anchor_ids)) != len(anchor_ids) or len(anchors) != search['anchors_per_candidate']:
                    raise ValueError('Incomplete or duplicated anchor set')
                pairing[method] = {}
                for anchor in anchors:
                    row = attempts[anchor['folder']]
                    if (not anchor['complete'] or anchor['errors'] or row['errors']
                            or row['status'] not in ('eligible', 'physical_failure')
                            or row['status'] != anchor['status']
                            or (row['category'],row['method'],row['split']) != (name,method,'train')):
                        raise ValueError('Invalid completed training anchor')
                    folder = (root/row['folder']).resolve()
                    if root not in folder.parents:
                        raise ValueError('Audit path outside campaign')
                    audit_hash = row['metadata_sha256'].get('audit.json')
                    if not audit_hash:
                        raise ValueError('Audit hash absent in status')
                    audit, actual = read_bound(folder/'audit.json', audit_hash)
                    if (audit['fixture_id'] != row['fixture_id'] or audit['method'] != method
                            or audit['split'] != 'train' or not isinstance(audit['eligible'],bool)
                            or audit['eligible'] != (row['status'] == 'eligible')
                            or audit['model_sha256'] != row['model_sha256']
                            or audit['model_sha256'] != anchor['model_sha256']):
                        raise ValueError('Audit / status identity mismatch')
                    values = {key:audit[key] for key in METRICS}
                    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v)
                           or v < 0 for v in values.values()):
                        raise ValueError('Missing or invalid metrics; refusing to silently omit a paired case')
                    pairing[method][anchor['anchor_index']] = (row['fixture_id'],row['model_sha256'])
                    if row['folder'] in selected:
                        raise ValueError('Attempt reused across plotted candidate blocks')
                    selected.add(row['folder'])
                    points.append(dict(category=name, method=method, candidate_index=index,
                        anchor_index=anchor['anchor_index'], folder=row['folder'], fixture_id=row['fixture_id'],
                        status=row['status'], eligible=audit['eligible'], metrics=values,
                        model_sha256=audit['model_sha256'], audit_sha256=actual,
                        failure_reasons=audit.get('failure_reasons', [])))
            if any(value != pairing[methods[0]] for value in pairing.values()):
                raise ValueError('Fixture / compiled-model pairing mismatch')
        excluded = [r for r in attempts.values() if r['category'] == name and r['phase'] == 'search'
                    and r['folder'] not in selected]
        categories.append(dict(category=name, common_candidate_indices=indices,
            candidates_per_method=len(indices), anchors_per_candidate=search['anchors_per_candidate'],
            points_per_method=len(indices)*search['anchors_per_candidate'],
            excluded_search_attempts=len(excluded),
            excluded_status_counts=dict(Counter(r['status'] for r in excluded))))
    return dict(schema=1, source_report=str(Path(report_path).resolve()), source_report_sha256=digest,
        source_report_generated_at_utc=report['generated_at_utc'],
        source_campaign_root=source_root, campaign_root=str(root),
        plan_sha256=report['provenance']['plan_sha256'],
        plot_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        bank_state=search['bank_state'], categories=categories, points=points,
        method_colors=COLORS, units=dict(rmse_m='m', peak_torque_nm='Nm', peak_speed_mps='m/s'),
        scope='Paired complete contiguous training-search candidate prefix; all eligible and failed episodes retained, including task and exposure failures. Not independent validation, locked selections, or equal wall/CPU budget. Partial/unpaired attempts excluded and counted. Metrics extracted from status-hash-verified audits; no trajectory recomputation. RMSE measures stage-waypoint tracking over the recorded rollout, not smooth global-path error or a guarantee of full-task completion.',
        command=sys.argv)


def render(data, output):
    output = Path(output).resolve()
    root = Path(data['campaign_root']).resolve()
    if output == root or root in output.parents:
        raise ValueError('Output must be outside original campaign')
    output.mkdir(parents=True, exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    plt.rcParams.update({'font.size':10, 'axes.spines.top':False, 'axes.spines.right':False,
                         'pdf.fonttype':42, 'savefig.facecolor':'white'})
    rows = data['categories']
    fig, axes = plt.subplots(len(rows), 2, figsize=(12, 3.6*len(rows)+1.2), squeeze=False)
    for i, row in enumerate(rows):
        points = [p for p in data['points'] if p['category'] == row['category']]
        for j, (metric, ylabel) in enumerate((('peak_torque_nm','Peak actuator torque (Nm)'),
                                             ('peak_speed_mps','Peak end-effector speed (m/s)'))):
            ax = axes[i,j]
            for method, color in COLORS.items():
                for eligible, marker in ((False,'X'),(True,'o')):
                    chosen = [p for p in points if p['method'] == method and p['eligible'] == eligible]
                    ax.scatter([p['metrics']['rmse_m'] for p in chosen],
                               [p['metrics'][metric] for p in chosen],
                               color=color, marker=marker, s=76, alpha=.8,
                               edgecolors='white', linewidths=.6, zorder=3)
            ax.set(xlabel='Stage-waypoint tracking RMSE (m)', ylabel=ylabel)
            ax.set_title(LABELS.get(row['category'],row['category'])+'\n'+
                f'{row["candidates_per_method"]} candidate(s) × {row["anchors_per_candidate"]} anchors / method\n'
                f'{row["excluded_search_attempts"]} partial/unpaired attempts excluded', fontsize=10, loc='left')
            ax.grid(alpha=.18)
            ax.margins(.12)
            if not points:
                ax.text(.5,.5,'No common completed prefix',ha='center',transform=ax.transAxes)
    handles = [Line2D([],[],color=color,lw=3,label=method.upper() if method=='vmc' else method.title())
               for method,color in COLORS.items()]
    handles += [Line2D([],[],color='#555555',marker=m,linestyle='',markersize=8,label=l)
                for m,l in [('o','Eligible'),('X','Retained failed episode')]]
    fig.suptitle('Training-search episodes — not independent validation', fontsize=16,y=.99)
    fig.legend(handles=handles,loc='upper center',bbox_to_anchor=(.5,.966),ncol=5,frameon=False)
    fig.text(.5,.018,'All paired complete-prefix episodes shown; no best-candidate or success-only selection.\n'
             'Metrics from hash-verified source audits; this plot does not recompute physical trajectories.\n'
             'Equal candidate / anchor counts do not imply equal CPU time. Speed is reported, not maximized.',
             ha='center',fontsize=9,color='#444444')
    fig.tight_layout(rect=(0,.055,1,.94),h_pad=2.2,w_pad=2.2)
    for suffix in ('png','pdf'):
        fig.savefig(output/('paired_training_search.'+suffix),dpi=180)
    plt.close(fig)
    (output/'plot_points.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
    manifest = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir()) if p.is_file()}
    (output/'files_sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--campaign-root', type=Path,
                        help='Explicit relocated campaign for audit reads; preserves source report paths and hashes')
    parser.add_argument('--output', type=Path, required=True, help='New directory outside campaign; never overwritten')
    args = parser.parse_args()
    data = extract_points(args.report, args.campaign_root)
    render(data,args.output)
    print(json.dumps(dict(output=str(args.output.resolve()), plotted_points=len(data['points']),
                          categories=data['categories'])))


if __name__ == '__main__':
    main()
