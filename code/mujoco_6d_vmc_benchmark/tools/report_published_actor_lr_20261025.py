"""Report paired actor-learning-rate sensitivity; no training or physics."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    registration=args.run/'REGISTRATION.json';p=json.loads(registration.read_text())
    methods={};files={}
    for method in ('direct','impedance','admittance','vmc'):
        path=args.run/method/'FINISHED.json';entry=json.loads(path.read_text())
        if (entry['registration_sha256']!=sha(registration) or not entry['parent_unchanged']
                or entry['auxiliary_weights_saved'] or entry['formal_training_changed']
                or entry['new_physics'] or entry['updates']!=2*p['updates_per_arm']):
            raise ValueError('Incomplete or unexpected finite probe receipt')
        if entry['fresh_entire_learner']:
            raise ValueError('Expected restored complete parent states')
        if entry['checkpoint_sha256']!=p['checkpoints'][method]['sha256']:
            raise ValueError('Checkpoint identity mismatch')
        a,b=entry['results']
        if (a['initial_full_state_sha256']!=b['initial_full_state_sha256']
                or a['sampling_rng_sha256']!=b['sampling_rng_sha256']):
            raise ValueError('Unpaired fresh state or replay sampling')
        if {a['factor'],b['factor']}!={1.,.1}:raise ValueError('Unexpected actor learning-rate factors')
        methods[method]=entry;files[method]=dict(path=str(path),sha256=sha(path))
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(methods=methods,evidence=files,registration_sha256=sha(registration),
        source_sha256=sha(__file__),updates=sum(e['updates'] for e in methods.values()),
        new_physics=0,auxiliary_weights_saved=False,convergence_claim=False,
        interpretation='Same full parent, replay and RNG; only actor Adam learning rate differs. A slower actor may reduce harmful feedback or delay useful learning. Offline diagnostics do not establish online quality or convergence.')
    (args.output/'SUMMARY.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
    metrics=[('replay_q_mean','Replay Q mean'),
        ('in_bag_terminal_mae','In-bag terminal MAE'),
        ('above_global_bound_fraction','Fraction above current-alpha global bound'),
        ('implied_minimum_rl_authority_fraction','Fraction implying minimum CHEQ authority')]
    for color,(method,entry) in zip(['C0','C1','C2','C3'],methods.items()):
        for arm in entry['results']:
            x=[0]+[row['updates'] for row in arm['curve']]
            values=[arm['initial']]+[row['diagnostic'] for row in arm['curve']]
            style='-' if arm['factor']==1. else '--'
            for ax,(key,title) in zip(axes.flat,metrics):
                ax.plot(x,[row[key] for row in values],style,color=color,label=f"{method} actor LR ×{arm['factor']:g}")
                ax.set_title(title);ax.set_xlabel('Auxiliary updates');ax.grid(alpha=.2)
    axes[0,0].set_yscale('symlog',linthresh=1)
    axes[0,1].set_yscale('log');axes[1,0].set_ylim(-.02,1.02);axes[1,1].set_ylim(-.02,1.02)
    axes[0,0].legend(fontsize=8,ncol=2)
    fig.suptitle('Actor learning-rate probe: matched full parent states, no online policy-quality claim')
    fig.savefig(args.output/'actor_lr.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
