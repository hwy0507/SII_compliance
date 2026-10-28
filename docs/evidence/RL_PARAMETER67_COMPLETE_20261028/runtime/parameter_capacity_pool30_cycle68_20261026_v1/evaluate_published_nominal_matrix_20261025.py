"""Fixed-controller common-cohort comparison with physical and filter audits.

Runs only registered zero actions through each existing controller interface.
Retains task failures, verifies physical models, reconstructs training reward,
and records contact-only metrics. Does not choose an empirical SPT reference
before the complete final comparison is available.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def reward_audit(folder, runtime):
    sys.path.insert(0, str(runtime/'source/tools'))
    from spt_rl_reward_20261025 import SPTReward
    from training_comparison_metrics_20261025 import completion_bonus
    journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
    terminal = json.loads((folder/'TERMINAL.json').read_text())
    if not journal or any(np.any(np.asarray(row['action']) != 0) for row in journal):
        raise ValueError('Nominal comparison must use zero parameter/residual actions')
    reducer = SPTReward()
    components, total = {}, 0.
    for index, row in enumerate(journal):
        done = index == len(journal)-1
        nxt = terminal if done else journal[index+1]
        result = terminal['result'] if done else dict(task_success=False, strict_success=False)
        value, terms = reducer(current_potential=row['payload_potential'],
            next_potential=nxt['payload_potential'], interval=nxt['interval'], terminated=done,
            task_success=result['task_success'], strict_success=result['strict_success'])
        bonus = completion_bonus(task_success=result['task_success'], strict_success=result['strict_success'],
            completion_time_s=terminal['completion_time_s']) if done else 0.
        total += value+bonus
        for name, amount in terms.items():
            if name in ('total', 'final_reward'):
                continue
            # Reducer metadata fields are not additive reward components.
            if name in ('progress', 'occupancy', 'time', 'comfort_torque', 'contact_force',
                    'torque_slew', 'penetration', 'peak_torque', 'terminal', 'failure_tail'):
                components[name] = components.get(name, 0.)+amount
        components['completion_efficiency'] = components.get('completion_efficiency', 0.)+bonus
    if abs(sum(components.values())-total) > 1e-7:
        raise ValueError('Reward components disagree with reconstructed return')
    return dict(steps=len(journal), reward=total, components=components,
        zero_actions_verified=True, training_reward_source_sha256=sha(runtime/'source/tools/spt_rl_reward_20261025.py'))


def main(args):
    protocol = json.loads(args.registration.read_text())
    if sha(Path(__file__)) != protocol['runner_sha256']:
        raise ValueError('Registered matrix runner drift')
    root, audit_root, output = map(Path, (protocol['runtime'], protocol['audit_runtime'], protocol['output']))
    if sha(root/'RUNTIME.json') != protocol['runtime_sha256']:
        raise ValueError('Frozen runtime manifest mismatch')
    for name, digest in protocol['audit_sources'].items():
        if sha(audit_root/name) != digest:
            raise ValueError('Audit source mismatch: '+name)
    train = json.loads(Path(protocol['training_registration']).read_text())
    if sha(Path(protocol['training_registration'])) != protocol['training_registration_sha256']:
        raise ValueError('Training cohort registration changed')
    if sha(Path(train['reference_plan'])) != train['reference_plan_sha256']:
        raise ValueError('Frozen nominal reference plan changed')
    if args.slot not in range(len(protocol['cpus'])):
        raise ValueError('Unregistered worker slot')
    cpu = protocol['cpus'][args.slot]
    os.sched_setaffinity(0, {cpu})
    sys.path.insert(0, str(audit_root))
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit
    jobs = [job for i, job in enumerate(protocol['jobs']) if i % len(protocol['cpus']) == args.slot]
    conditions = {c['id']: c for c in train['conditions']}
    status_path = output/f'SLOT_{args.slot}.json'
    if status_path.exists():
        raise FileExistsError('Slot already dispatched; inspect original process before any recovery')
    rows = []
    write(status_path, dict(pid=os.getpid(), cpu=cpu, state='running', completed=0, assigned=len(jobs)))
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', MUJOCO_GL='disable',
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
    try:
        for job in jobs:
            if (output/'STOP_REQUESTED').exists():
                write(status_path, dict(pid=os.getpid(), state='stopped_between_episodes', completed=len(rows)))
                return
            condition = conditions[job['case_id']]
            if sha(Path(condition['path'])) != condition['sha256']:
                raise ValueError('Condition definition changed')
            folder = output/job['controller']/job['case_id']
            folder.parent.mkdir(exist_ok=True)
            command = [sys.executable, '-B', str(audit_root/'audit_published_episode_20261025.py'),
                '--runtime', str(root), '--output', str(folder), '--controller', job['controller'],
                '--fixture', condition['path'], '--reference-plan', train['reference_plan']]
            with folder.with_suffix('.log').open('xb') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
                write(status_path, dict(pid=os.getpid(), cpu=cpu, state='physics_running',
                    child_pid=child.pid, job=job, completed=len(rows), assigned=len(jobs), updated_unix=time.time()))
                if child.wait() != 0:
                    raise RuntimeError('Physical worker failed: '+str(folder))
            if sha(folder/'rollout.mjb') != condition['model_sha256']:
                raise ValueError('Actual physical model differs from common registered condition')
            physical = summarize(folder, 'nominal_'+job['controller'], job['case_id'])
            filtered = audit(folder)
            reward = reward_audit(folder, root)
            write(folder/'PHYSICAL_AUDIT.json', physical)
            write(folder/'FILTER_REPLAY_AUDIT.json', filtered)
            write(folder/'REWARD_AUDIT.json', reward)
            rows.append(dict(physical['row'], category=condition['category'], reward=reward['reward'],
                public_filter_replay_verified=filtered['passed'], episode=str(folder)))
            write(output/f'ROWS_SLOT_{args.slot}.json', dict(rows=rows,
                planned_total=len(protocol['jobs']), complete_matrix=False, final_spt_reference_selected=False))
        write(status_path, dict(pid=os.getpid(), cpu=cpu, state='complete', completed=len(rows),
            assigned=len(jobs), ended_unix=time.time()))
    except BaseException as error:
        write(output/f'FAILURE_SLOT_{args.slot}.json', dict(error=repr(error), completed=len(rows),
            note='Preserve worker evidence and all task failures; no automatic retry or exclusion'))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--slot', type=int, required=True)
    main(parser.parse_args())
