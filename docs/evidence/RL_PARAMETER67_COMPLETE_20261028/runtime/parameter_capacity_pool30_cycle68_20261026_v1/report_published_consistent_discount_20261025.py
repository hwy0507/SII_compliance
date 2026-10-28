"""Report fresh consistent-discount probes; no training or physics."""
import argparse
import hashlib
import json
import math
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
        if not entry['reward_and_bellman_discounts_matched'] or entry['replay_subset_size']!=41250:
            raise ValueError('Incomplete or mismatched objective subset')
        if entry['checkpoint_sha256']!=p['checkpoints'][method]['sha256']:
            raise ValueError('Checkpoint identity mismatch')
        a,b=entry['results']
        if (a['initial_full_state_sha256']!=b['initial_full_state_sha256']
                or a['sampling_rng_sha256']!=b['sampling_rng_sha256']):
            raise ValueError('Unpaired fresh state or replay sampling')
        if {a['gamma'],b['gamma']}!={.99,.9995}:raise ValueError('Unexpected discounts')
        for arm in (a,b):
            expected=list(range(p['record_every'],p['updates_per_arm']+1,p['record_every']))
            if [row['updates'] for row in arm['curve']] != expected:
                raise ValueError('Incomplete or duplicate optimization curve')
            if arm['final'] != arm['curve'][-1]['diagnostic'] or not arm['parent_unchanged']:
                raise ValueError('Final diagnostic or immutable parent mismatch')
            if not math.isclose(arm['terminal_discount_1374'],arm['gamma']**1374,rel_tol=1e-12):
                raise ValueError('Delayed terminal attenuation mismatch')
            for row in arm['curve']:
                if not all(math.isfinite(value) for section in ('metrics','diagnostic')
                           for value in row[section].values()):
                    raise ValueError('Nonfinite optimization diagnostic')
            arm_path=args.run/method/f"gamma_{arm['gamma']:g}.json"
            if json.loads(arm_path.read_text())!=arm:
                raise ValueError('Per-arm record differs from completion receipt')
        item=p['checkpoints'][method]
        if sha(item['path']) != item['sha256'] or sha(item['transitions']) != item['transitions_sha256']:
            raise ValueError('Immutable checkpoint or transition input drift')
        methods[method]=entry;files[method]=dict(path=str(path),sha256=sha(path))
    args.output.mkdir(parents=True,exist_ok=False)
    report=dict(methods=methods,evidence=files,registration_sha256=sha(registration),
        source_sha256=sha(__file__),updates=sum(e['updates'] for e in methods.values()),
        new_physics=0,auxiliary_weights_saved=False,convergence_claim=False,
        interpretation='Matched Bellman/PBRS gamma, fresh full learners and paired sampling. Historical context remains fixed. Low gamma attenuates delayed terminal success; stable value magnitudes cannot select an online controller.')
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
            style='-' if arm['gamma']==.9995 else '--'
            for ax,(key,title) in zip(axes.flat,metrics):
                ax.plot(x,[row[key] for row in values],style,color=color,label=f"{method} gamma={arm['gamma']:g}")
                ax.set_title(title);ax.set_xlabel('Auxiliary updates');ax.grid(alpha=.2)
    axes[0,0].set_yscale('symlog',linthresh=1)
    axes[0,1].set_yscale('log');axes[1,0].set_ylim(-.02,1.02);axes[1,1].set_ylim(-.02,1.02)
    axes[0,0].legend(fontsize=8,ncol=2)
    fig.suptitle('Fresh consistent-discount probe: frozen replay, no online policy-quality claim')
    fig.savefig(args.output/'consistent_discount.png',dpi=160);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(13,9),constrained_layout=True)
    metrics=[('agent_train/q_loss','Critic loss'),
             ('agent_train/entropy_coefficient','Temperature alpha'),
             ('agent_train/actor_entropy','Batch policy entropy'),
             ('agent_train/actor_loss','Actor loss (not a success metric)')]
    windows={}
    for color,(method,entry) in zip(['C0','C1','C2','C3'],methods.items()):
        windows[method]={}
        for arm in entry['results']:
            style='-' if arm['gamma']==.9995 else '--'
            for ax,(key,title) in zip(axes.flat,metrics):
                ax.plot([row['updates'] for row in arm['curve']],
                        [row['metrics'][key] for row in arm['curve']],style,color=color,
                        label=f"{method} gamma={arm['gamma']:g}")
                ax.set_title(title);ax.set_xlabel('Auxiliary updates');ax.grid(alpha=.2)
            late=[row for row in arm['curve'] if row['updates']>p['updates_per_arm']-5000]
            windows[method][str(arm['gamma'])]=dict(
                window='Recorded diagnostics within final5000 updates, not every optimizer step',
                observations=len(late),first_update=late[0]['updates'],last_update=late[-1]['updates'],
                mean_recorded_critic_loss=sum(row['metrics']['agent_train/q_loss'] for row in late)/len(late),
                q_change=late[-1]['diagnostic']['replay_q_mean']-late[0]['diagnostic']['replay_q_mean'],
                terminal_mae_change=late[-1]['diagnostic']['in_bag_terminal_mae']-late[0]['diagnostic']['in_bag_terminal_mae'],
                sampled_entropy_minus_target=arm['final']['sampled_policy_entropy']-late[-1]['metrics']['agent_train/target_entropy'],
                terminal_reward_discount_at_start=arm['terminal_discount_1374'],
                convergence_claim=False)
    axes[0,0].set_yscale('log');axes[0,1].set_yscale('log')
    axes[1,1].set_yscale('symlog',linthresh=1)
    axes[0,0].legend(fontsize=8,ncol=2)
    fig.suptitle('Finite fixed-replay training diagnostics; no online success claim')
    fig.savefig(args.output/'optimization_diagnostics.png',dpi=160);plt.close(fig)
    (args.output/'LATE_WINDOWS.json').write_text(json.dumps(windows,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
