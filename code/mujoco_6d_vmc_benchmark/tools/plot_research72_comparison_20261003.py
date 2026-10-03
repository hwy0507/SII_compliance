"""Vector/raster publication figures from the already audited comparison JSON.

No model selection, simulation, fitting, new statistics, or condition-manifest
reads. Preserve all families, missing outcomes, unexposed NA and paired subsets.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

ORDER = ('esn','memoryless','ordinary_mlp','ordinary_rnn','matched_mlp','matched_rnn',
         'enhanced_teacher','classical_admittance','classical_impedance','classical_vmc',
         'parameter_admittance','parameter_impedance','parameter_vmc',
         'direct_metric','direct_office_task','nominal_zero')
LABELS = dict(esn='ESN', memoryless='Memoryless', ordinary_mlp='MLP', ordinary_rnn='RNN',
    matched_mlp='Feature-matched MLP', matched_rnn='Feature-matched RNN', enhanced_teacher='VMC teacher',
    classical_admittance='Fixed admittance', classical_impedance='Fixed impedance', classical_vmc='Fixed VMC',
    parameter_admittance='RL admittance', parameter_impedance='RL impedance', parameter_vmc='RL VMC',
    direct_metric='Direct RL: metric', direct_office_task='Direct RL: task', nominal_zero='Nominal WBC')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(report, synthetic):
    assert bool(report.get('synthetic_demo', False)) == synthetic
    if not synthetic:
        assert report['model_lock_sha256'] and report['evidence']
        assert report['sealed_manifest_read_by_report'] is False
    families = report['families']
    assert 'esn' in families and set(report['esn_minus_baseline']) == set(families)-{'esn'}
    assert sum(v['strict']['planned'] for v in families.values()) == report['planned']
    assert sum(v['strict']['observed'] for v in families.values()) == report['audited']
    for family in families.values():
        for key in ('task','strict'):
            r = family[key]
            assert 0 <= r['successes'] <= r['observed'] <= r['planned']
            assert r['missing'] == r['planned']-r['observed']
            assert (r['rate'] is None) == (r['missing'] > 0)
            assert len(r['per_seed']) == r['seeds']
            assert sum(s['planned'] for s in r['per_seed']) == r['planned']
    return [x for x in ORDER if x in families]+sorted(set(families)-set(ORDER))


def style(ax, labels):
    ax.set_yticks(range(len(labels)), labels)
    ax.set_ylim(len(labels)-.5, -.5)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='x', color='#dde2e7', linewidth=.6)
    ax.set_axisbelow(True)


def interval(ax, y, statistic, color='#197c78'):
    """Draw the stored interval without assuming it encloses the point estimate."""
    n = statistic['paired_cells']
    if not n:
        assert statistic['difference'] is None and statistic['ci95'] is None
        ax.text(.98, y, 'NA (n=0)', transform=ax.get_yaxis_transform(), ha='right', va='center', color='#777')
        return
    value = statistic['difference']; low, high = statistic['ci95']
    assert np.isfinite([value,low,high]).all() and low <= high
    ax.hlines(y, low, high, color=color, linewidth=1.5)
    ax.plot(value, y, 'D' if statistic.get('point_interval') else 'o', color=color, markersize=4)
    ax.text(1.015, y, str(n), transform=ax.get_yaxis_transform(), ha='left', va='center', fontsize=7)


def outcome_figure(report, families, synthetic):
    labels = [LABELS.get(f, f) for f in families]
    fig, axes = plt.subplots(1, 2, figsize=(12, max(5., .35*len(families)+1.7)),
                            gridspec_kw=dict(width_ratios=[1.2,1]))
    ax = axes[0]; style(ax, labels); ax.set_xlim(-.03,1.04)
    for y, name in enumerate(families):
        values = report['families'][name]
        for key, offset, color in (('task',-.13,'#8996a5'),('strict',.13,'#197c78')):
            r = values[key]
            if r['rate'] is None:
                ax.hlines(y+offset, *r['planned_rate_bounds'], color=color, linestyle='--', linewidth=2)
            else:
                ax.plot(r['rate'], y+offset, 'o', color=color, markersize=5,
                        label=key.capitalize() if y == 0 else None)
            if key == 'strict':
                for index, seed in enumerate(r['per_seed']):
                    if seed['observed'] == seed['planned']:
                        jitter=(index-(len(r['per_seed'])-1)/2)*.045
                        ax.plot(seed['successes']/seed['planned'], y+.23+jitter, '|', color='#192f3b', markersize=6)
        strict = values['strict']
        text = f"{strict['successes']}/{strict['planned']}"
        if strict['missing']: text += f"; {strict['missing']} missing"
        ax.text(1.06,y,text,transform=ax.get_yaxis_transform(),va='center',fontsize=7)
    ax.set_xlabel('Task / strict success fraction'); ax.set_title('All planned episodes; ticks = complete seeds')
    # Explicit handles keep legends valid when the first family is incomplete.
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([],[],marker='o',linestyle='',color=c,label=l)
        for l,c in (('Task','#8996a5'),('Strict','#197c78'))],loc='upper center',
        bbox_to_anchor=(.37,.91),ncol=2,fontsize=8,frameon=False)
    baselines=[f for f in families if f!='esn']; right=axes[1]
    style(right,[LABELS.get(f,f) for f in baselines]); right.axvline(0,color='#8a9097',linewidth=.8)
    for y,name in enumerate(baselines):interval(right,y,report['esn_minus_baseline'][name]['strict_success'])
    right.set_xlabel('ESN minus baseline: strict success fraction')
    right.set_title('Stored crossed 95% intervals\nRight labels = paired cells')
    role='SYNTHETIC LAYOUT ONLY — NOT RESEARCH RESULTS' if synthetic else 'Frozen-model comparison'
    fig.suptitle(f"{role}\nAudited {report['audited']}/{report['planned']} planned episodes",fontsize=12)
    fig.text(.02,.025,'Dashed ranges bound missing outcomes, not confidence intervals. Diamonds mark point bootstrap intervals.\n'
        'Intervals are exploratory, not multiplicity-adjusted; three training seeds do not establish population certainty.',fontsize=8)
    fig.subplots_adjust(left=.16,right=.965,bottom=.14,top=.84,wspace=.85)
    return fig


def contact_figure(report, families, synthetic, events=('human','rod','unknown_edge')):
    baselines=[f for f in families if f!='esn']
    fig,axes=plt.subplots(len(events),2,figsize=(12,max(10.,len(baselines)*.67+2.8)*len(events)/3),squeeze=False)
    for i,event in enumerate(events):
        for j,(field,label) in enumerate((('contact_p95_force_n','P95 force (N)'),('impulse_ns','Force-magnitude integral (N s)'))):
            ax=axes[i,j];style(ax,[LABELS.get(f,f) for f in baselines])
            ax.axvline(0,color='#8a9097',linewidth=.8)
            for y,name in enumerate(baselines):
                interval(ax,y,report['esn_minus_baseline'][name]['jointly_strict_full_exposed_contacts'][event][field])
            event_label={'human':'Human push','rod':'Rod push','unknown_edge':'Table edge',
                         'ball':'Ball impact','pillar':'Pillar'}[event]
            ax.set_title(f'{event_label}: {label}');ax.set_xlabel('Paired mean: ESN minus baseline')
    role='SYNTHETIC LAYOUT ONLY — NOT RESEARCH RESULTS' if synthetic else 'Outcome-conditioned contact diagnostics'
    fig.suptitle(role+'\nBoth methods strictly successful, full-length, and actually exposed',fontsize=12)
    fig.text(.02,.012,'All baselines retained; NA = no eligible pairs. Right labels count paired cells, not independent environments.\n'
        'These conditioned subsets do not establish overall or causal superiority. Force integral is not signed net impulse.\n'
        'Diamonds mark point intervals; stored exploratory bootstrap intervals are shown without recomputation.',fontsize=8)
    # Reserve physical space for the title/footer even in the shorter two-event figure.
    height = fig.get_size_inches()[1]
    fig.subplots_adjust(left=.16,right=.96,bottom=1.1/height,top=1-.95/height,wspace=.65,hspace=.38)
    return fig


def render(report, output, synthetic=False):
    families=validate(report,synthetic);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'svg.fonttype':'none'})
    files={}
    for name,builder in (('outcomes',outcome_figure),('contact_pairs',contact_figure),
        ('contact_pairs_ball_pillar',lambda r,f,s:contact_figure(r,f,s,('ball','pillar')))):
        figure=builder(report,families,synthetic)
        for extension in ('svg','png'):
            path=output/f'{name}.{extension}';figure.savefig(path,dpi=160,facecolor='white');files[path.name]=sha(path)
        plt.close(figure)
    return dict(files_sha256=files,family_order=families,
        role='synthetic_layout_only' if synthetic else 'figures_from_audited_frozen_comparison',
        no_new_statistics=True, no_sealed_manifest_read=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--synthetic-demo',action='store_true');args=p.parse_args()
    digest=sha(args.report);report=json.loads(args.report.read_text())
    result=render(report,args.output,args.synthetic_demo)
    assert sha(args.report)==digest
    result.update(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(__file__),
        report=str(args.report.resolve()),report_sha256=digest,command=sys.argv,
        matplotlib=matplotlib.__version__,numpy=np.__version__)
    (args.output/'FIGURE_MANIFEST.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
