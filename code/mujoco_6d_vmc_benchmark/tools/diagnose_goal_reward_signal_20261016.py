"""Decompose CLOSED training returns; no simulation, model choice or acceptance.

Distinguish terminal/safety costs from potential shaping and measured tracking.
Embed the captured execution, protocol and selected log entries for reproducibility.
Never count a buffered, partial or in-flight episode as a complete observation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path


COMPONENTS = ('task', 'progress', 'error', 'peak_torque', 'time', 'smooth',
              'failure_continuation', 'physical_slew',
              'physical_slew_failure_continuation', 'safety_peak_cost',
              'safety_failure_continuation', 'tracking_guidance', 'tracking_failure_continuation')


def close(a, b):
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a, b, abs_tol=1e-8, rel_tol=1e-9):
        raise ValueError(f'Inconsistent reward evidence: {a}, {b}')


def decompose(row, entries, spec):
    if len(entries) > row['steps']:
        raise ValueError('Extra transitions in a closed episode')
    if len(entries) < row['steps']:
        if any(e['step'] != row['step_before']+i+1 or e['episode'] != row['episode']
               or e['terms']['terminated'] for i, e in enumerate(entries)):
            raise ValueError('Missing log tail is not a valid nonterminal prefix')
        return dict(status='pending_log_flush', observed=len(entries), expected=row['steps'])
    cfg = spec['reward']; gamma = cfg['gamma']; weight = cfg['progress_weight']
    if gamma != spec['agent_config']['gamma']:
        raise ValueError('Learner and shaping gamma differ')
    sums = {k: 0. for k in COMPONENTS}; discounted = sums.copy()
    initial = entries[0]['terms']['current_potential']; previous = initial
    potentials = [initial]; bounded_error = 0.; reward_total = 0.; nonzero_task = 0
    for i, entry in enumerate(entries):
        if entry['step'] != row['step_before']+i+1 or entry['episode'] != row['episode']:
            raise ValueError('Missing, repeated or cross-episode transition')
        t = entry['terms']; terminal = i == len(entries)-1
        if bool(t['terminated']) != terminal:
            raise ValueError('Terminal must be the last transition')
        close(t['current_potential'], previous)
        effective = 0. if terminal else t['next_potential']
        close(t['effective_next_potential'], effective)
        close(t['progress'], weight*(gamma*effective-previous) if cfg['mode'] != 'task_only' else 0.)
        expected_success = bool(terminal and row['result']['task_success'] and
            (spec.get('reward_variant') == 'task_safety' or row['result']['strict_success']))
        if bool(t['success']) != expected_success or bool(t['failure']) != (terminal and not expected_success):
            raise ValueError('Terminal label differs from registered reward variant')
        close(t['task'], (cfg['success_reward'] if expected_success else -cfg['failure_penalty']) if terminal else 0.)
        values = {k: float(t.get(k, 0.)) for k in COMPONENTS}
        # Safety telemetry reports positive costs; the trainer subtracts them.
        for k in ('safety_peak_cost', 'safety_failure_continuation'):
            values[k] = -values[k]
        close(sum(values.values()), t['final_reward'])
        for k, v in values.items():
            sums[k] += v; discounted[k] += gamma**i*v
        bounded_error += t['bounded_error_cost']; reward_total += t['final_reward']
        nonzero_task += t['task'] != 0
        previous = t['next_potential']; potentials.append(previous)
    close(reward_total, row['return_value'])
    expected_shaping = -weight*initial if cfg['mode'] != 'task_only' else 0.
    close(discounted['progress'], expected_shaping)
    return dict(status='complete', episode=row['episode'], condition=row['condition_id'],
        steps=len(entries), result=row['result'], return_value=reward_total,
        undiscounted_components=sums, discounted_components=discounted,
        shaping_telescoping_residual=discounted['progress']-expected_shaping,
        potential_initial=initial, potential_max=max(potentials), potential_final=previous,
        bounded_tracking_cost=bounded_error, task_reward_transition_count=nonzero_task,
        terminal_reward_fraction=nonzero_task/len(entries),
        terminal_in_n_step_fraction=min(spec['agent_config']['n_step'], len(entries))/len(entries))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); root = a.run.resolve()
    def capture(path):
        raw = path.read_bytes()
        return json.loads(raw), hashlib.sha256(raw).hexdigest()
    state, state_hash = capture(root/'execution.json')
    spec, spec_hash = capture(root/'PROTOCOL.json')
    closed = {r['episode']: r for r in state['rows'] if 'ended_utc' in r}
    logs = {ep: [] for ep in closed}; incomplete_tail = False
    with (root/'training.jsonl').open('rb') as stream:
        for raw in stream:
            if not raw.endswith(b'\n'):
                incomplete_tail = True; break
            entry = json.loads(raw)
            if entry['episode'] in logs:
                logs[entry['episode']].append(entry)
    results = [decompose(row, logs[ep], spec) for ep, row in closed.items()]
    if any(r['status'] != 'complete' for r in results[:-1]) or (
            results and results[-1]['status'] != 'complete' and state['status'] != 'running'):
        raise ValueError('Historical closed episode log is incomplete')
    audits = {}
    for ep, row in closed.items():
        audit, digest = capture(Path(row['run'])/'AUDIT.json')
        if digest != row['audit_sha256']:
            raise ValueError('Closed training audit hash changed')
        audits[ep] = dict(sha256=digest, existing_training_audit=audit)
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), run=str(root),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        execution_sha256=state_hash, protocol_sha256=spec_hash,
        execution_snapshot=state, protocol_snapshot=spec, closed_log_entries=logs,
        trailing_partial_line=incomplete_tail, episodes=results, existing_audits=audits,
        incomplete_episodes=[r['episode'] for r in state['rows'] if 'ended_utc' not in r],
        interpretation='Training reward consistency and signal inventory only. Potential cancellation is intentional; '
        'a constant discounted shaping return is not a reward bug. No counterfactual, causal tuning claim, '
        'convergence, new physical audit, held-out evaluation or acceptance. In-flight episodes excluded explicitly.')
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
