"""Read-only, dt-weighted contact attribution on frozen paired trajectories.

Per-joint exceedances overlap; dominant-joint durations partition the violating
contact time but are descriptive, not causal. No thresholds or rewards change.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def contact_summary(dt, torque, force, thresholds):
    dt, torque, force, thresholds = map(np.asarray, (dt, torque, force, thresholds))
    if (dt.ndim != 1 or not len(dt) or torque.shape != (len(dt), 7)
            or force.shape != dt.shape or thresholds.shape != (7,)
            or not all(np.isfinite(v).all() for v in (dt, torque, force, thresholds))
            or np.any(dt <= 0) or np.any(thresholds <= 0) or np.any(force < 0)):
        raise ValueError('Invalid contact arrays')
    active = force > .05
    ratio = np.abs(torque) / thresholds
    exceed = ratio > 1.
    violating = active & exceed.any(axis=1)
    compliant = active & ~exceed.any(axis=1)
    total = float(dt[active].sum())
    bad = float(dt[violating].sum())
    dominant = ratio.argmax(axis=1)
    partition = [float(dt[violating & (dominant == j)].sum()) for j in range(7)]
    if not np.isclose(sum(partition), bad, rtol=0, atol=1e-9):
        raise AssertionError('Dominant-joint partition lost contact time')
    good = float(dt[compliant].sum())
    return dict(contact_s=total, compliant_s=good, violating_s=bad,
        compliance_ratio=good/total if total else None,
        per_joint_exceed_s=[float(dt[active & exceed[:, j]].sum()) for j in range(7)],
        per_joint_exceed_fraction=[float(dt[active & exceed[:, j]].sum())/total
                                  if total else None for j in range(7)],
        dominant_joint_violating_s=partition,
        contact_peak_abs_torque_nm=np.abs(torque[active]).max(axis=0).tolist() if total else None,
        full_episode_peak_abs_torque_nm=np.abs(torque).max(axis=0).tolist(),
        bounded_torque_cost_integral_s=float(
            (dt[active] * (1 - 1/np.maximum(1., ratio[active].max(axis=1)))).sum()))


def reward_from_journal(folder, reward_class, completion_bonus):
    journal = [json.loads(x) for x in (folder/'actor_intervals.jsonl').read_text().splitlines()]
    terminal = json.loads((folder/'TERMINAL.json').read_text())
    reducer, totals, values = reward_class(), {}, []
    keys = ('progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
            'torque_slew', 'penetration', 'peak_torque', 'terminal', 'failure_tail')
    if len(journal) != 1375:
        raise ValueError('Expected full55s action journal')
    for i, row in enumerate(journal):
        done = i == len(journal)-1
        nxt = terminal if done else journal[i+1]
        labels = terminal['result'] if done else dict(task_success=False, strict_success=False)
        value, terms = reducer(current_potential=row['payload_potential'],
            next_potential=nxt['payload_potential'], interval=nxt['interval'], terminated=done,
            task_success=labels['task_success'], strict_success=labels['strict_success'])
        bonus = completion_bonus(task_success=labels['task_success'], strict_success=labels['strict_success'],
            completion_time_s=terminal['completion_time_s']) if done else 0.
        for k in keys:
            totals[k] = totals.get(k, 0.) + terms[k]
        totals['completion_efficiency'] = totals.get('completion_efficiency', 0.) + bonus
        values.append(value+bonus)
    if not np.isclose(sum(values), sum(totals.values()), rtol=0, atol=1e-8):
        raise AssertionError('Reward components do not sum to return')
    return dict(return_sum=sum(values), terms=totals,
                discounted_return=float(np.asarray(values) @ np.power(.9995, np.arange(1375))))


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Analysis source drift')
    os.sched_setaffinity(0, {protocol['cpu']})
    os.nice(10)
    for path, digest in protocol['input_hashes'].items():
        if sha(path) != digest:
            raise ValueError('Registered input drift: '+path)
    runtime = Path(protocol['reward_runtime'])
    sys.path.insert(0, str(runtime/'source/tools'))
    from spt_rl_reward_20261025 import SPTReward
    from training_comparison_metrics_20261025 import completion_bonus
    output = Path(protocol['output'])
    output.mkdir(exist_ok=False, parents=True)
    rows, series, identity = [], {}, None
    for entry in protocol['episodes']:
        folder = Path(entry['path'])
        meta = json.loads((folder/'AUDIT_EXTENSION.json').read_text())
        audit = json.loads((folder/'PHYSICAL_AUDIT.json').read_text())
        row = audit['row']
        adapter = json.loads((folder/'ADAPTER.json').read_text())
        paired = (sha(folder/'rollout.mjb'), sha(folder/'rollout.plan.json'),
                  adapter['fixture']['physical_config_sha256'])
        identity = identity or paired
        if paired != identity or adapter['arguments']['dt'] != .00005:
            raise ValueError('Unpaired model/plan/fixture/dt')
        expected_columns = ['dt_s', *['torque_joint'+str(i+1)+'_nm' for i in range(7)],
            'human_robot_force_sum_n', 'external_penetration_peak_so_far_m', 'time_s']
        if (not meta['completed'] or meta['samples'] != 1100000 or meta['columns'] != expected_columns
                or sha(folder/'audit_substeps.npy') != meta['substeps_sha256']):
            raise ValueError('Incomplete or changed physical telemetry')
        required_audits = ['FILTER_REPLAY_AUDIT.json']
        if entry['torque_audit_available']:
            required_audits.append('TORQUE_REPLAY_AUDIT.json')
        elif entry['label'] != 'nominal' or (folder/'TORQUE_REPLAY_AUDIT.json').exists():
            raise ValueError('Only the older nominal recording may lack torque replay evidence')
        for name in required_audits:
            if not json.loads((folder/name).read_text())['passed']:
                raise ValueError('Existing execution audit failed')
        a = np.load(folder/'audit_substeps.npy', mmap_mode='r')[:meta['samples']]
        thresholds = np.asarray(row['torque_thresholds_nm'])
        if not np.array_equal(thresholds, [.5*x for x in meta['actuator_limits_nm']]):
            raise ValueError('Changed engineering thresholds')
        result = contact_summary(a[:, 0], a[:, 1:8], a[:, 8], thresholds)
        for measured, key in [('contact_s', 'human_contact_s'), ('compliant_s', 'human_below_threshold_s')]:
            if not np.isclose(result[measured], row[key], rtol=0, atol=1e-8):
                raise AssertionError('Independent contact metric mismatch')
        if not np.array_equal(result['full_episode_peak_abs_torque_nm'], row['peak_torque_nm_per_joint']):
            raise AssertionError('Independent peak torque mismatch')
        reward = reward_from_journal(folder, SPTReward, completion_bonus)
        if not np.isclose(reward['terms']['comfort_torque'],
                          -2*result['bounded_torque_cost_integral_s']/55, rtol=0, atol=1e-9):
            raise AssertionError('Independent physical comfort reward mismatch')
        if entry['label'] == 'nominal':
            reference = json.loads((folder/'REWARD_AUDIT.json').read_text())
            if not np.isclose(reward['return_sum'], reference['reward'], rtol=0, atol=1e-8):
                raise AssertionError('Independent nominal reward mismatch')
        rows.append(dict(label=entry['label'], path=str(folder), audited_outcome=row,
                         contact=result, reward=reward,
                         torque_projection_replay_available=entry['torque_audit_available']))
        # Display0.1s bins, retaining dt-weighted contact metrics. No-contact bins are NA.
        bins = np.minimum((np.maximum(0., a[:, 10]-1e-8)/.1).astype(int), 549)
        active = a[:, 8] > .05
        ratio = np.abs(a[:, 1:8])/thresholds
        durations = np.bincount(bins[active], weights=a[active, 0], minlength=550)
        comfortable = active & (ratio <= 1).all(axis=1)
        good = np.bincount(bins[comfortable], weights=a[comfortable, 0], minlength=550)
        fractions = np.full(550, np.nan)
        np.divide(good, durations, out=fractions, where=durations > 0)
        exceed = np.full((550, 7), np.nan)
        for j in range(7):
            bad = active & (ratio[:, j] > 1)
            duration = np.bincount(bins[bad], weights=a[bad, 0], minlength=550)
            np.divide(duration, durations, out=exceed[:, j], where=durations > 0)
        series[entry['label']] = (fractions, exceed)
    report = dict(registration_sha256=sha(args.registration), rows=rows, paired_model_plan_fixture=identity,
        independent_physical_and_reward_checks_pass=True, new_physics=0, optimizer_updates=0,
        limitations=['One preselected active-long condition, not a cohort ranking or causal intervention.',
            'Engineering thresholds are not validated human comfort thresholds.',
            'Joint exceedances overlap; dominant-joint time is a descriptive partition, not causal attribution.',
            'Older nominal recording has physical/filter audits but no torque-projection replay artifact.',
            'No SPT reference is selected from this partial comparison.',
            'These frozen cycles3/7 do not evaluate the currently training actor-LR policy.'])
    (output/'ANALYSIS.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), constrained_layout=True)
    for i, (label, (fraction, exceed)) in enumerate(series.items()):
        t = np.arange(550)*.1+.05
        axes[i, 0].plot(t, fraction*100, label=label)
        for j in range(7):
            axes[i, 1].plot(t, exceed[:, j]*100, label='joint'+str(j+1), alpha=.8)
        for ax in axes[i]:
            ax.set(xlim=(0, 55), ylim=(-3, 103), xlabel='Time (s)', title=label)
            ax.grid(alpha=.2)
        axes[i, 0].set_ylabel('All-joint compliance during contact (%)')
        axes[i, 1].set_ylabel('Per-joint exceedance during contact (%)')
    axes[0, 1].legend(ncol=4, fontsize=8)
    fig.suptitle('Frozen Impedance active-long0000: 0.1s bins; no contact = gaps\nEngineering thresholds; overlapping joint exceedances; no causal claim')
    fig.savefig(output/'contact_tradeoff.png', dpi=160)
    fig.savefig(output/'contact_tradeoff.pdf')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
