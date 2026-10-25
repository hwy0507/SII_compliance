"""Pair complete audited training cycles by condition, without pooling stages.

This is an online-training comparison, not a fixed-policy evaluation or a
convergence decision. Critic initialization and policy changes confound causal
interpretations; reduced Q/loss after reset does not itself establish learning.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np


METHODS = ('direct', 'impedance', 'admittance', 'vmc')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def complete_rows(report, method, cycle, expected):
    if report['cycle'] != cycle or report['optimizer_updates_performed'] != 0:
        raise ValueError('Expected exact read-only complete-cycle diagnosis')
    data = report['methods'][method]
    if data.get('boundary') != 'complete_condition_cycle' or not data.get('network_state_unchanged'):
        raise ValueError('Missing complete immutable audited checkpoint')
    selected = [row for row in data['episodes'] if row['cycle'] == cycle]
    if len(selected) != len(expected) or {r['condition'] for r in selected} != set(expected):
        raise ValueError('Incomplete, duplicate or mismatched condition cohort')
    result = {}
    for row in selected:
        if row['category'] != expected[row['condition']]:
            raise ValueError('Condition category mismatch')
        if row['strict_success'] and not row['task_success']:
            raise ValueError('Strict success without task success')
        if not np.isfinite(row['reward']) or not np.isclose(
                sum(row['reward_terms'].values()), row['reward'], rtol=0, atol=1e-6):
            raise ValueError('Reward component reconstruction mismatch')
        result[row['condition']] = row
    return result


def paired_summary(before, after):
    if set(before) != set(after):
        raise ValueError('Unpaired conditions')
    ids = sorted(before)
    delta = np.array([after[c]['reward'] - before[c]['reward'] for c in ids])
    terms = set().union(*(r['reward_terms'] for r in [*before.values(), *after.values()]))
    components = {term: float(np.mean([after[c]['reward_terms'].get(term, 0.)
        - before[c]['reward_terms'].get(term, 0.) for c in ids])) for term in sorted(terms)}
    if not np.isclose(sum(components.values()), delta.mean(), rtol=0, atol=1e-6):
        raise ValueError('Paired reward decomposition mismatch')
    return dict(count=len(ids), before_reward_mean=float(np.mean([before[c]['reward'] for c in ids])),
        after_reward_mean=float(np.mean([after[c]['reward'] for c in ids])),
        paired_reward_delta_mean=float(delta.mean()), paired_reward_delta_min=float(delta.min()),
        paired_reward_delta_max=float(delta.max()), mean_reward_component_deltas=components,
        before_task=sum(bool(before[c]['task_success']) for c in ids),
        after_task=sum(bool(after[c]['task_success']) for c in ids),
        before_strict=sum(bool(before[c]['strict_success']) for c in ids),
        after_strict=sum(bool(after[c]['strict_success']) for c in ids),
        gained_strict=[c for c in ids if after[c]['strict_success'] and not before[c]['strict_success']],
        lost_strict=[c for c in ids if before[c]['strict_success'] and not after[c]['strict_success']],
        after_failure_stages=dict(Counter(after[c]['final_task_stage'] for c in ids if not after[c]['strict_success'])),
        after_aborts={c:after[c]['abort_reason'] for c in ids if after[c]['abort_reason']})


def compare(before, after, before_cycle, after_cycle, expected):
    output = {}
    for method in METHODS:
        left = complete_rows(before, method, before_cycle, expected)
        right = complete_rows(after, method, after_cycle, expected)
        entry = paired_summary(left, right)
        entry['categories'] = {}
        for category in sorted(set(expected.values())):
            select = lambda rows: {c:r for c,r in rows.items() if expected[c] == category}
            entry['categories'][category] = paired_summary(select(left), select(right))
        entry['health'] = {}
        for label, report in [('before', before), ('after', after)]:
            m = report['methods'][method]
            entry['health'][label] = {k:m.get(k) for k in (
                'steps', 'updates', 'checkpoint_sha256', 'alpha', 'sampled_q_values',
                'fixed_alpha_soft_q_global_bound', 'sampled_q_above_global_bound_fraction',
                'terminal_q_in_bag_absolute_error', 'terminal_by_restart_origin', 'recent_optimizer')}
        output[method] = entry
    return output


def main(args):
    protocol = json.loads(args.cohort_registration.read_text())
    expected = {c['id']:c['category'] for c in protocol['conditions']}
    if len(expected) != 30 or Counter(expected.values()) != Counter(
            passive_corner=10, active_short=10, active_long=10):
        raise ValueError('Expected registered balanced thirty-condition cohort')
    before, after = [json.loads(p.read_text()) for p in (args.before, args.after)]
    methods = compare(before, after, args.before_cycle, args.after_cycle, expected)
    args.output.mkdir(parents=True, exist_ok=False)
    report = dict(before_cycle=args.before_cycle, after_cycle=args.after_cycle,
        evidence={name:dict(path=str(path.resolve()), sha256=sha(path)) for name,path in
            [('before',args.before),('after',args.after),('cohort_registration',args.cohort_registration)]},
        source_sha256=sha(__file__), methods=methods, new_physics=0, optimizer_updates=0,
        convergence_claim=False, fixed_policy_comparison=False,
        limitation='Paired conditions under changing training policies. Reward/Q/loss reductions following a critic reset are not proof of convergence or a causal benefit.')
    (args.output/'COMPARISON.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    x = np.arange(4)
    for offset,label in [(-.18,'before'),(.18,'after')]:
        axes[0].bar(x+offset,[methods[m][label+'_reward_mean'] for m in METHODS],.36,label=label)
        axes[1].bar(x+offset,[methods[m][label+'_strict']/30 for m in METHODS],.36,label=label)
        axes[2].bar(x+offset,[methods[m]['health'][label]['sampled_q_values']['mean'] for m in METHODS],.36,label=label)
    for ax,title in zip(axes,['Complete-cohort mean reward','Strict success / 30','Sampled replay Q mean (symlog)']):
        ax.set_title(title);ax.set_xticks(x,METHODS,rotation=20);ax.legend()
    axes[1].set_ylim(0,1);axes[2].set_yscale('symlog',linthresh=1)
    fig.suptitle(f'Training cycle {args.before_cycle} to {args.after_cycle}; not a convergence claim')
    fig.savefig(args.output/'comparison.png',dpi=160);plt.close(fig)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['before','after','cohort-registration','output']:
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--before-cycle',type=int,required=True)
    parser.add_argument('--after-cycle',type=int,required=True)
    main(parser.parse_args())
