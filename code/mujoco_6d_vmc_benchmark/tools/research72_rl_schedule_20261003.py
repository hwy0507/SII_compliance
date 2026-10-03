"""Registered finite RL dispatch order; no reward or outcome based selection."""
import hashlib
import json
from pathlib import Path

AMENDMENT = 'AMENDMENT_RL_ROUND_ROBIN.json'
LIMITS = (5500, 27500, 49500, 71500, 80000)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def active_campaign(root):
    root = Path(root)
    amendment = root/AMENDMENT
    if not amendment.exists():
        return root/'rl_office_adaptation_v1'
    spec = read(amendment)
    assert spec['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert spec['scope'] == 'outcome_independent_round_robin_rl_dispatch'
    assert spec['cumulative_step_boundaries'] == list(LIMITS)
    assert spec['active_campaign'] == 'rl_office_adaptation_v2'
    assert spec['superseded_campaign'] == 'rl_office_adaptation_v1'
    assert LIMITS[-1] == read(root/'PROTOCOL.json')['budget_caps']['rl_adaptation_steps_per_family_seed']
    old = root/spec['superseded_campaign']
    assert sha(old/'execution.json') == spec['superseded_execution_sha256']
    assert read(old/'execution.json')['status'] == 'waiting_for_predecessor'
    assert not list(old.glob('queue_*/execution.json')), 'Superseded registration already dispatched'
    receipt = Path(spec['supersession_receipt'])
    assert sha(receipt) == spec['supersession_receipt_sha256']
    change = read(receipt)
    assert change['status'] == 'complete' and change['old_receipts_preserved']
    assert change['stopped_physics_processes'] == change['old_rl_physics_episodes'] == 0
    return root/spec['active_campaign']


def dispatch_plan(jobs, schedule):
    if schedule == 'round_robin_cumulative_boundaries':
        return [(job, 'initial' if i == 0 else f'cumulative_{limit:07d}', limit)
                for i, limit in enumerate(LIMITS) for job in jobs]
    assert schedule == 'legacy_job_major'
    return [(job, stage, limit) for job in jobs
            for stage, limit in (('initial', 5500), ('continued', 80000))]


def closure(rows, exhausted_plan):
    complete = all(row.get('latest_manifest') for row in rows)
    return dict(status='complete' if complete else 'deadline_no_new_dispatch',
        all_models_have_completed_boundary=complete,
        all_requested_segments_dispatched=bool(exhausted_plan),
        dispatch_stop_reason='all_registered_boundaries_processed' if exhausted_plan else 'development_deadline',
        completion_semantics='Finite dispatch concluded with a checkpoint for every model; actual cumulative steps are reported, not assumed equal to the cap.')
