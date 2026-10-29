"""Plot exact saved payload velocities for the development-only comparison."""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import read,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=read(args.report)
    assert report['status']=='development_stability_comparison_no_new_physics'
    assert not args.output.exists()
    fig,axes=plt.subplots(1,2,figsize=(10.8,4.7),sharey=True)
    colors=['#248276','#c45047','#385e9c']
    for ax,group in zip(axes,report['groups']):
        for color,row in zip(colors,group['episodes']):
            folder=Path(row['folder'])
            for name,digest in row['input_hashes'].items():assert sha(folder/name)==digest
            with np.load(folder/'legacy.npz',allow_pickle=False) as z:
                time=z['time'];speed=np.linalg.norm(np.diff(z['object_position'],axis=0)/.04,axis=1)
            mask=time[1:]>=time[-1]-5
            ax.semilogy(time[1:][mask],np.maximum(speed[mask],1e-7),color=color,lw=1.4,label=row['label'])
        ax.axhline(.02,color='#444444',ls='--',lw=1,label='Frozen task limit: 0.02 m/s')
        ax.set_title(group['identity']+' ('+group['split']+')',fontsize=11)
        ax.set_xlabel('Simulation time (s)');ax.grid(alpha=.18);ax.legend(fontsize=7,loc='upper center',bbox_to_anchor=(.5,-.23),ncol=2,frameon=False)
        ax.set_ylim(1e-5,.15)
    axes[0].set_ylabel('Payload speed between saved 25-Hz states (m/s)')
    fig.suptitle('Development checks: terminal payload stability, last 5 seconds',fontsize=12)
    fig.text(.5,.015,'Same initial canonical48 and MJB within each panel. Saved-state analysis; not unseen-test performance.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,.10,1,.94));fig.savefig(args.output,dpi=170);plt.close(fig)
    print(args.output)


if __name__=='__main__':main()
