"""Check logged potential shaping including the final cancellation term.

The potential observes arm reference progress for reward only. This audit tests
whether complete discounted shaping is exactly -weight*initial_potential,
rather than allowing empty-handed stage progress to earn a net shaping bonus.
It does not establish critic convergence or sufficient task exploration.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from office_v7_uniform24_20261008 import read, write, sha, now


def close(left, right):
    assert math.isfinite(left) and math.isfinite(right)
    assert abs(left-right) <= 1e-10, (left, right)


def inspect(path):
    payload = (path/'execution.json').read_bytes()
    state = json.loads(payload)
    spec = read(path/'PROTOCOL.json')
    cfg = spec['reward']
    gamma, weight = cfg['gamma'], cfg['progress_weight']
    assert gamma == spec['agent_config']['gamma'] and cfg['mode'] in ('metric','office_task')
    episodes = {row['episode']:row for row in state['rows'] if 'result' in row}
    accumulators = {}
    for episode, row in episodes.items():
        initial = read(Path(row['run'])/'RL_REWARD_METADATA.json')['initial_potential']
        accumulators[episode] = dict(initial=initial, count=0, discounted=0., previous_next=initial,
            maximum_potential=initial, terminated=0, residual_max=0., terminal_task=None)
    partial_line = False
    with (path/'training.jsonl').open('rb') as stream:
        for raw in stream:
            if not raw.endswith(b'\n'):
                partial_line = True
                break
            entry = json.loads(raw)
            if entry['episode'] not in accumulators:
                continue
            a = accumulators[entry['episode']]
            row = episodes[entry['episode']]
            terms = entry['terms']
            assert not a['terminated'], 'Reward after terminal'
            assert entry['step'] == row['step_before']+a['count']+1
            close(terms['current_potential'], a['previous_next'])
            effective = 0. if terms['terminated'] else terms['next_potential']
            close(terms['effective_next_potential'], effective)
            expected = weight*(gamma*effective-terms['current_potential'])
            close(terms['progress'], expected)
            a['residual_max'] = max(a['residual_max'], abs(terms['progress']-expected))
            a['discounted'] += gamma**a['count']*terms['progress']
            a['count'] += 1
            a['previous_next'] = terms['next_potential']
            a['maximum_potential'] = max(a['maximum_potential'], terms['next_potential'])
            if terms['terminated']:
                success = bool(row['result']['task_success'] and row['result']['strict_success'])
                assert terms['success'] == success and terms['failure'] == (not success)
                close(terms['task'], cfg['success_reward'] if success else -cfg['failure_penalty'])
                a['terminated'] += 1
                a['terminal_task'] = terms['task']
    rows = []
    for episode, a in accumulators.items():
        expected_count = episodes[episode]['steps']
        assert a['count'] <= expected_count
        complete = a['count'] == expected_count
        if complete:
            assert a['terminated'] == 1
            close(a['discounted'], -weight*a['initial'])
        else:
            # Completed physical receipt can precede the buffered JSONL flush.
            # Do not call the missing log tail a reward failure or invent values.
            assert state['status'] == 'running' and not a['terminated']
        rows.append(dict(episode=episode, condition_id=episodes[episode]['condition_id'],
            expected_steps=expected_count, observed_log_steps=a['count'],
            status='passed' if complete else 'pending_buffered_log_tail',
            initial_potential=a['initial'], maximum_potential=a['maximum_potential'],
            discounted_progress=a['discounted'],
            expected_complete_discounted_progress=-weight*a['initial'],
            terminal_task_reward=a['terminal_task'], max_step_formula_error=a['residual_max'],
            complete_telescoping_error=abs(a['discounted']+weight*a['initial']) if complete else None))
    return dict(path=str(path), state_status=state['status'], captured_state_steps=state['steps'],
        captured_state_sha256=hashlib.sha256(payload).hexdigest(), protocol_sha256=sha(path/'PROTOCOL.json'),
        gamma=gamma, weight=weight, trailing_partial_line=partial_line,
        completed_checks=sum(row['status']=='passed' for row in rows),
        pending_log_flush=sum(row['status']!='passed' for row in rows), episodes=rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    registration = a.root/'RL_JOBS_CORRECTED.json'
    jobs = read(registration)['jobs']
    assert len(jobs) == 10
    segments = []
    for job in jobs:
        value = inspect(Path(job['output']))
        value.update(family=job['family'], seed=job['seed'])
        segments.append(value)
        print(job['family'], job['seed'], value['completed_checks'], 'passed,',
              value['pending_log_flush'], 'pending log flush', flush=True)
    write(a.output, dict(status='passed_for_complete_logged_episodes', created_utc=now(),
        source_sha256=sha(__file__), registration_sha256=sha(registration), segments=segments,
        completed_checks=sum(s['completed_checks'] for s in segments),
        pending_log_flush=sum(s['pending_log_flush'] for s in segments),
        interpretation='Arm stage alone is not physical payload progress. However complete gamma-discounted '
            'potential shaping cancels to the initial-state constant, including terminal reset. No net '
            'empty-handed stage bonus from this term. Undiscounted logged returns need not cancel. '
            'This pathwise identity does not establish Markov sufficiency, value convergence, '
            'reward-normalizer stationarity, or learned task success. No model or environment changed.'))


if __name__ == '__main__':
    main()
