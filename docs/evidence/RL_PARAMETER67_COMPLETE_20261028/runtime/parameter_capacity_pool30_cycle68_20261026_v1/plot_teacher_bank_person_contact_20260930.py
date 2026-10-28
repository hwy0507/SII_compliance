"""Plot audited contiguous hand-contact runs from existing physical data."""
import argparse
import json
from pathlib import Path

import numpy as np

from teacher_bank_person_success_audit_20260930 import independent_runs
from teacher_bank_validation_audit_20260930 import read,load_columns,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();output=args.output.resolve()
    review=read(args.review)
    root=Path(review['source_run']).resolve()
    if output.exists() or output==root or root in output.parents:raise ValueError('New external output required')
    points={}
    for candidate in ('c00','c05'):
        case=review['cases'][candidate];path=Path(case['folder'])/'exposure.npz'
        if sha(path)!=case['raw_sha256']['exposure.npz']:raise ValueError('Exposure changed since audit')
        raw=load_columns(path,('person_physics',))['person_physics']
        runs,details=independent_runs(raw,case['fixture'])
        index=int(np.argmax(runs[:,2]))
        detail=details[index];segment=raw[detail['first_physical_index']:detail['stop_physical_index']]
        axis=-np.asarray(case['fixture']['axis'],dtype=float);axis/=np.linalg.norm(axis)
        signed=(segment[:,3:]-segment[0,3:])@axis
        points[candidate]=dict(run_index=index,run_start_s=float(segment[0,0]),run_end_s=float(segment[-1,0]+segment[-1,1]),
            duration_s=runs[index,2],max_signed_yield_mm=float(max(0.,signed.max())*1000),
            qualified=detail['qualified'],relative_time_s=(segment[:,0]-segment[0,0]).tolist(),
            signed_yield_mm=(signed*1000).tolist(),saved_force_n=segment[:,2].tolist(),
            source_exposure_sha256=case['raw_sha256']['exposure.npz'],source_folder=case['folder'])
        del raw
    output.mkdir(parents=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
    fig,axes=plt.subplots(2,2,figsize=(11,7))
    for row,(candidate,color) in enumerate((('c00','#D55E00'),('c05','#0072B2'))):
        p=points[candidate]
        title=f'{candidate}: longest uninterrupted press/hold run ({p["run_index"]})'
        ax=axes[row,0]
        ax.plot(p['relative_time_s'],p['signed_yield_mm'],color=color,lw=1.7)
        ax.axhline(10,color='#333333',ls='--',lw=1,label='10 mm threshold')
        ax.set(ylabel='Signed displacement along push (mm)',xlabel='Time since this run begins (s)',ylim=(-.5,16),
            title=title+'\n'+f'{p["duration_s"]:.4f} s; maximum {p["max_signed_yield_mm"]:.3f} mm')
        ax.legend(loc='lower right',frameon=False)
        ax=axes[row,1]
        ax.plot(p['relative_time_s'],p['saved_force_n'],color=color,lw=1.3)
        ax.axhline(.05,color='#333333',ls='--',lw=1,label='Force predicate: > 0.05 N')
        ax.set(yscale='log',ylabel='Saved contact force (N; log scale)',xlabel='Time since this run begins (s)',
            title=f'Absolute interval: {p["run_start_s"]:.4f}–{p["run_end_s"]:.4f} s')
        ax.legend(loc='lower right',frameon=False)
        for col in range(2):axes[row,col].grid(alpha=.2)
    fig.suptitle('One training hand-push condition: c00 versus c05',fontsize=15)
    fig.text(.5,.025,'Each curve begins at its own first in-window force-positive sample; gaps are never joined; withdraw excluded.\n'
        'Force predicate is not geometric contact. Signed movement under contact is not a causal no-push comparison.\n'
        'Selected intervals only: full-episode force peaks and fragmented contacts are reported separately.',
        ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.105,1,.94),h_pad=2.4)
    for ext in ('png','pdf'):fig.savefig(output/('contiguous_person_contact.'+ext),dpi=180)
    plt.close(fig)
    payload=dict(source_review=str(args.review.resolve()),source_review_sha256=sha(args.review),
        script_sha256=sha(Path(__file__)),selection='Longest uninterrupted in-window force-positive run separately for c00 and c05; no cross-gap or withdrawal samples',
        full_trace_peak_force_not_shown=True,scope='Existing raw physical-sample plot; one training fixture, not validation/generalization',points=points)
    (output/'plot_points.json').write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps(dict(output=str(output),png_sha256=sha(output/'contiguous_person_contact.png'))))


if __name__=='__main__':main()
