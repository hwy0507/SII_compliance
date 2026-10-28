"""Display every public support-diagnostic trajectory, without winner selection."""
import argparse
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter,NullFormatter


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=json.loads(a.report.read_text())
    families=['esn','memoryless','matched_mlp','matched_rnn','ordinary_mlp','ordinary_rnn']
    assert {x['category'] for x in r['rows']}==set(families)
    assert len(r['rows'])==99
    plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans','pdf.fonttype':42})
    fig,axes=plt.subplots(2,3,figsize=(11,6.8),sharex=True,sharey=True)
    styles=[('Strict success','#187c61','o',lambda x:x['strict_success']),
            ('Task only','#d17a00','s',lambda x:x['task_success'] and not x['strict_success']),
            ('Task failed','#ad3940','x',lambda x:not x['task_success'])]
    maximum=max(x['rmse_mm'] for x in r['rows']);minimum=min(x['rmse_mm'] for x in r['rows'])
    for ax,family in zip(axes.flat,families):
        rows=[x for x in r['rows'] if x['category']==family]
        for label,color,marker,keep in styles:
            selected=[x for x in rows if keep(x)]
            ax.scatter([100*x['fraction_above_training_identity_loo_p95'] for x in selected],
                [x['rmse_mm'] for x in selected],s=35,c=color,marker=marker,alpha=.7,label=label,linewidths=1.)
        short=[x for x in rows if not x['full_horizon']]
        ax.scatter([100*x['fraction_above_training_identity_loo_p95'] for x in short],
            [x['rmse_mm'] for x in short],s=110,facecolors='none',edgecolors='black',linewidths=1.,label='Short history')
        ax.set_title(f'{family}  ({len(rows)} trajectories)')
        ax.set_yscale('log');ax.set_ylim(minimum*.8,maximum*1.25);ax.set_xlim(-3,103)
        ax.set_yticks([25,50,100]);ax.yaxis.set_major_formatter(ScalarFormatter());ax.yaxis.set_minor_formatter(NullFormatter())
        ax.grid(True,alpha=.18);ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    fig.supxlabel('Samples beyond the training identity-LOO P95 distance (%)',y=.092,fontsize=10)
    fig.supylabel('Observed-horizon trajectory RMSE (mm, log scale)',x=.045,fontsize=10)
    handles,labels=axes[0,0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='upper center',bbox_to_anchor=(.5,.935),ncol=4,frameon=False)
    fig.suptitle('Public development: instantaneous proprioceptive support vs tracking error',y=.986,fontsize=12)
    fig.text(.5,.018,'All initial candidates on development_000–002. Some checkpoints/points coincide.\n'
        'Descriptive, correlated trajectories; no recurrent-state OOD or causal claim. Short histories are circled.',
        ha='center',va='bottom',fontsize=9,color='#444444')
    fig.subplots_adjust(top=.845,bottom=.16,hspace=.28,wspace=.14)
    a.output.mkdir(parents=True,exist_ok=False)
    for suffix in ('png','pdf'):fig.savefig(a.output/f'support_vs_error.{suffix}',dpi=180)
    plt.close(fig)
    manifest=dict(report_path=str(a.report.resolve()),report_sha256=sha(a.report),source_sha256=sha(Path(__file__)),
        plotted_trajectories=99,selection='All rows of the fixed public diagnostic report, all failures retained',
        artifacts={p.name:sha(p) for p in a.output.iterdir()})
    (a.output/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')


if __name__=='__main__':main()
