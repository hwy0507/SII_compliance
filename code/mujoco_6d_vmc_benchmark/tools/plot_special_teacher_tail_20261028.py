"""Plot saved TRAIN-only ball tail motion; no simulation or relabeling."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write


def main(output):
    assert not output.exists()
    midpoint=ROOT/'outputs/special_teacher_midpoint_20261028_v1'
    review=read(midpoint/'REVIEW.json')
    assert review['selected']=='v075_avg1'
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True,layout='constrained')
    evidence=[]
    for ax,identity in zip(axes,('ball_01','ball_04')):
        locations=[
            ('1.0 / average (v6)',ROOT/'outputs/special_scene_vmc_collection_20261028_v6'/identity/'ball'),
            ('0.5 / no average',ROOT/'outputs/special_teacher_tail_repair_20261028_v2'/(identity+'_v05_avg0')/'ball'),
            ('0.75 / average',midpoint/('v075_avg1_'+identity)/'ball')]
        for label,folder in locations:
            with np.load(folder/'legacy.npz',allow_pickle=False) as z:
                time=z['time'].copy()
                speed=np.linalg.norm(np.diff(z['object_position'],axis=0)/.04,axis=1)
            tail=time[1:]>=time[-1]-4.
            ax.plot(time[1:][tail]-time[-1],speed[tail],label=label,linewidth=1.3)
            evidence.append(dict(identity=identity,label=label,source=str(folder/'legacy.npz'),
                sha256=sha(folder/'legacy.npz'),tail10frames_max_speed_mps=float(speed[-9:].max()),
                plotted_time_relative_end_s=(time[1:][tail]-time[-1]).tolist(),plotted_speed_mps=speed[tail].tolist()))
            if label=='0.75 / average':
                expected=next(r['tail_object_speed_max_mps'] for r in review['rows'] if r['id']=='v075_avg1_'+identity)
                assert float(speed[-9:].max())==expected
        ax.axhline(.02,color='black',linestyle='--',linewidth=1,label='Original tail gate: 0.02 m/s')
        ax.axvspan(-.36,0,color='grey',alpha=.15)
        ax.set(title=identity+' (training identity)',xlabel='Time relative to episode end (s)',xlim=(-4,0),ylim=(0,None))
        ax.grid(alpha=.2)
    axes[0].set_ylabel('Object translational speed (m/s)')
    axes[1].legend(fontsize=8,loc='upper left')
    fig.suptitle('Teacher tail motion from complete saved trajectories\nShading: original final-10-frame gate window; not a student or final-test result',fontsize=11)
    output.mkdir(parents=True)
    fig.savefig(output/'teacher_tail_motion.png',dpi=160)
    plt.close(fig)
    write(output/'teacher_tail_motion.json',dict(scope=__doc__,review_sha256=sha(midpoint/'REVIEW.json'),
        threshold_mps=.02,gate_window='Nine position differences of the last ten saved frames; dt=.04 s',rows=evidence,
        plot_sha256=sha(output/'teacher_tail_motion.png')))
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args().output.resolve())
