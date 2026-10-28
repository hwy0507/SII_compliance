"""Read-only paired Direct trajectories/rewards from frozen evaluations.

Three conditions were selected before these evaluations. Checkpoint changes
span multiple interventions; this comparison does not isolate their causes.
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


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(__file__) != protocol['source_sha256']:
        raise ValueError('Analysis source drift')
    for path, digest in protocol['input_hashes'].items():
        if sha(path) != digest:
            raise ValueError('Frozen input changed: '+path)
    os.sched_setaffinity(0, {protocol['cpu']})
    os.nice(protocol['nice'])
    runtime = Path(protocol['reward_runtime'])
    sys.path.insert(0, str(runtime/'source/tools'))
    from spt_rl_reward_20261025 import SPTReward
    from training_comparison_metrics_20261025 import completion_bonus
    output = Path(protocol['output'])
    output.mkdir(parents=True, exist_ok=False)
    results, series, identities = [], {}, {}
    components = ('progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
                  'torque_slew', 'penetration', 'peak_torque', 'terminal', 'failure_tail')
    for entry in protocol['episodes']:
        folder = Path(entry['path'])
        adapter = json.loads((folder/'ADAPTER.json').read_text())
        outcome = json.loads((folder/'rollout.json').read_text())
        terminal = json.loads((folder/'TERMINAL.json').read_text())
        journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
        if (len(journal) != 1375 or not outcome['full_task_horizon_completed']
                or outcome['abort_reason'] or not outcome['physical_valid']):
            raise ValueError('Expected complete physical evaluation')
        if adapter['arguments']['dt'] != .00005:
            raise ValueError('Changed dt')
        identity = (sha(folder/'rollout.mjb'), sha(folder/'rollout.plan.json'),
                    adapter['fixture']['physical_config_sha256'])
        prior = identities.setdefault(entry['case_id'], identity)
        if prior != identity or identity[0] != terminal['model_sha256']:
            raise ValueError('Unpaired physical model/plan/fixture')
        reducer = SPTReward()
        sums = {key: 0. for key in (*components, 'completion_efficiency')}
        rewards = []
        for index, row in enumerate(journal):
            done = index == len(journal)-1
            nxt = terminal if done else journal[index+1]
            result = terminal['result'] if done else dict(task_success=False, strict_success=False)
            value, terms = reducer(current_potential=row['payload_potential'],
                next_potential=nxt['payload_potential'], interval=nxt['interval'], terminated=done,
                task_success=result['task_success'], strict_success=result['strict_success'])
            bonus = completion_bonus(task_success=result['task_success'], strict_success=result['strict_success'],
                completion_time_s=terminal['completion_time_s']) if done else 0.
            rewards.append(value+bonus)
            for key in components:
                sums[key] += terms[key]
            sums['completion_efficiency'] += bonus
        if not np.isclose(sum(sums.values()), sum(rewards), rtol=0, atol=1e-8):
            raise AssertionError('Reward reduction mismatch')
        if entry['label'] == 'nominal':
            recorded = json.loads((folder/'REWARD_AUDIT.json').read_text())
            if not np.isclose(recorded['reward'], sum(rewards), rtol=0, atol=1e-8):
                raise AssertionError('Independent nominal reward mismatch')
        with np.load(folder/'rollout.npz') as arrays, np.load(folder/'audit_filter.npz') as filtered:
            times, payload = arrays['time'], arrays['object_position']
            actions = np.asarray([row['action'] for row in journal])
            if arrays['observation'].shape != (1375, 48) or actions.shape != (1375, 7):
                raise ValueError('Changed actor contract')
            if not np.allclose(np.diff(times), .04, rtol=0, atol=1e-7):
                raise ValueError('Changed actor clock')
            if entry['label'] == 'nominal' and np.any(actions != 0):
                raise ValueError('Nominal action not zero')
            early = times <= 10.
            result = dict(case_id=entry['case_id'], label=entry['label'], path=str(folder),
                task_success=outcome['task_success'], strict_success=outcome['strict_success'],
                final_task_stage=outcome['final_task_stage'], task_events=outcome['task_events'],
                completion_time_s=terminal['completion_time_s'], max_lift_m=outcome['max_lift_m'],
                placement_error_xy_m=outcome['placement_error_xy_m'], reward=sum(rewards), reward_components=sums,
                discounted_reward=float(np.asarray(rewards) @ np.power(.9995, np.arange(1375))),
                action_mean=actions.mean(axis=0).tolist(), action_mean_first10s=actions[early].mean(axis=0).tolist(),
                filter_wbc_scale_mean=float(filtered['wbc_scale'].mean()),
                filter_wbc_scale_first10s=float(filtered['wbc_scale'][early].mean()),
                filter_yield_twist_first10s=filtered['yield_twist'][early].mean(axis=0).tolist(),
                model_sha256=identity[0], plan_sha256=identity[1], fixture_sha256=identity[2])
            results.append(result)
            series[(entry['case_id'], entry['label'])] = (times.copy(), payload.copy(), filtered['wbc_scale'].copy())
    report = dict(registration_sha256=sha(args.registration), rows=results, exact_physical_pairing=True,
        nominal_reward_independent_check=True, new_physics=0, optimizer_updates=0,
        limitation='Only three prespecified conditions, not whole-cohort ranking. Different frozen checkpoints '
        'span multiple training interventions, so this is not a causal attribution or current actor-LR result.')
    (output/'ANALYSIS.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cases = list(identities)
    fig, axes = plt.subplots(3, len(cases), figsize=(14, 9), constrained_layout=True)
    for column, case in enumerate(cases):
        for label in ('nominal', 'cycle3', 'cycle7'):
            times, payload, scale = series[(case, label)]
            axes[0, column].plot(times, payload[:, 2], label=label)
            axes[1, column].plot(times, 1000*np.linalg.norm(payload[:, :2]-[.69, -.31], axis=1), label=label)
            axes[2, column].plot(times, scale, label=label)
        axes[0, column].set_title(case.replace('_train_0000', ''))
        for row, ylabel in enumerate(('Payload height (m)', 'Placement XY error (mm)', 'Public-filter WBC scale')):
            axes[row, column].set_ylabel(ylabel)
            axes[row, column].set_xlabel('Time (s)')
            axes[row, column].grid(alpha=.2)
            axes[row, column].legend()
    fig.suptitle('Frozen Direct evaluations: same conditions, no causal attribution')
    fig.savefig(output/'fixed_direct_comparison.png', dpi=150)
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
