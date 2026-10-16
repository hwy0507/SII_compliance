"""Optional TRAIN-ONLY dense tracking cost for an explicitly registered goal job.

Use the existing physical integral of e²/(.12²+e²), divided by 55 seconds.
No new observations, task labels, physics or action transformations. A positive
cost is subtracted; early failure cannot avoid its discounted worst-case tail.
This deliberately changes the training objective, unlike potential shaping.
"""
import math


CONFIG = dict(schema='sii-goal-bounded-tracking-v1', weight=4.,
              horizon_s=55., control_dt_s=.04, gamma=.9995,
              error_scale_m=.12)
PARAMETER_CONFIG = dict(CONFIG, schema='sii-goal-parameter-tracking-weight-v1',
                        weight=36., base_error_weight=4.)


def validate_guidance(job, *, controller, reward, reward_variant):
    cfg = job.get('tracking_guidance') if job else None
    if cfg is None:
        return None
    if cfg not in (CONFIG, PARAMETER_CONFIG):
        raise ValueError('Only the explicitly specified tracking treatment is implemented')
    if cfg == CONFIG:
        if controller is not None or reward != 'office_task' or reward_variant != 'task_safety':
            raise ValueError('Direct tracking treatment requires Direct task_safety')
    elif controller not in ('impedance', 'admittance', 'vmc') or reward != 'metric' or reward_variant != 'payload_shaping':
        raise ValueError('Additional metric tracking weight requires parameter payload_shaping')
    return dict(cfg)


def check_reward_resume(parent, current):
    if parent.get('tracking_guidance') != current.get('tracking_guidance'):
        raise ValueError('Changed tracking reward requires fresh training or an explicit replay/normalizer rebuild')


def discounted_cost_tail(remaining_s, *, weight, horizon_s, control_dt_s, gamma):
    """Future full and partial intervals begin one discount after this transition."""
    if not all(math.isfinite(x) for x in (remaining_s, weight, horizon_s, control_dt_s, gamma)):
        raise ValueError('Nonfinite tracking configuration')
    if remaining_s < 0 or weight < 0 or horizon_s <= 0 or control_dt_s <= 0 or not 0 < gamma <= 1:
        raise ValueError('Invalid tracking configuration')
    n = int(math.floor(remaining_s/control_dt_s+1e-9))
    partial = max(0., remaining_s-n*control_dt_s)
    if partial < 1e-9: partial = 0.
    discounted_count = float(n) if gamma == 1 else gamma*(-math.expm1(n*math.log(gamma)))/(1-gamma)
    return weight/horizon_s*(control_dt_s*discounted_count+gamma**(n+1)*partial)


def tracking_terms(bounded_error_cost, interval_s, elapsed_s, *, terminated, success, config):
    if config not in (CONFIG, PARAMETER_CONFIG):
        raise ValueError('Unregistered tracking treatment')
    horizon = config['horizon_s']
    if not all(math.isfinite(x) for x in (bounded_error_cost, interval_s, elapsed_s)):
        raise ValueError('Nonfinite tracking telemetry')
    if (interval_s <= 0 or interval_s > config['control_dt_s']+1e-7 or
            elapsed_s < interval_s-1e-7 or elapsed_s > horizon+1e-7 or
            bounded_error_cost < 0 or bounded_error_cost > interval_s/horizon+1e-10):
        raise ValueError('Invalid normalized physical tracking integral or time')
    if success and not terminated:
        raise ValueError('Success requires a terminal transition')
    tail = 0.
    if terminated and not success:
        tail = discounted_cost_tail(max(0., horizon-elapsed_s), weight=config['weight'],
            horizon_s=horizon, control_dt_s=config['control_dt_s'], gamma=config['gamma'])
    return dict(tracking_guidance=-config['weight']*bounded_error_cost,
                tracking_failure_continuation=-tail)


def main():
    """Counterfactual reward arithmetic only: never rewrite replay/checkpoints."""
    import argparse
    from datetime import datetime, timezone
    import hashlib
    import json
    from pathlib import Path
    from diagnose_goal_reward_signal_20261016 import decompose
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.receipt.read_bytes(); receipt = json.loads(raw)
    spec = receipt['protocol_snapshot']
    assert spec.get('tracking_guidance') is None, 'Do not double-charge existing guidance'
    config = CONFIG if spec['controller'] is None else PARAMETER_CONFIG
    validate_guidance({'tracking_guidance': config}, controller=spec['controller'],
                      reward=spec['reward']['mode'], reward_variant=spec['reward_variant'])
    assert all(spec['reward'][key] == config[key] for key in ('gamma', 'horizon_s', 'control_dt_s', 'error_scale_m'))
    if config == PARAMETER_CONFIG:
        assert spec['reward']['error_weight'] == config['base_error_weight']
    rows = []
    for row in receipt['execution_snapshot']['rows']:
        if 'ended_utc' not in row: continue
        entries = receipt['closed_log_entries'][str(row['episode'])]
        original = decompose(row, entries, spec)
        assert original['status'] == 'complete', 'Need complete frozen training logs'
        cost = discounted_cost = 0.; previous_time = 0.
        for i, entry in enumerate(entries):
            t = entry['terms']; elapsed = t['elapsed_s']
            terms = tracking_terms(t['bounded_error_cost'], elapsed-previous_time, elapsed,
                terminated=t['terminated'], success=t['success'], config=config)
            value = sum(terms.values()); cost += value; discounted_cost += config['gamma']**i*value
            previous_time = elapsed
        old_discounted = sum(original['discounted_components'].values())
        rows.append(dict(episode=row['episode'], condition=row['condition_id'],
            result_unchanged=row['result'], original_return=row['return_value'],
            candidate_return=row['return_value']+cost, added_tracking_return=cost,
            original_discounted_return=old_discounted,
            candidate_discounted_return=old_discounted+discounted_cost,
            added_discounted_tracking_return=discounted_cost))
    result = dict(observed_utc=datetime.now(timezone.utc).isoformat(), config=config,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        receipt_path=str(args.receipt.resolve()), receipt_sha256=hashlib.sha256(raw).hexdigest(),
        rows=rows, simulation=False, gradient_updates=0, replay_modified=False, checkpoint_modified=False,
        interpretation='Counterfactual train-reward arithmetic on the same historical trajectories, '
        'not new policy returns, effectiveness, convergence or acceptance. Fresh matched training '
        'or a separately validated full replay/normalizer rebuild is required before deployment.')
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
