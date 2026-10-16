"""Compare registered training pilots; never rank different reward totals.

Metrics are native training audits, not independent final acceptance. Every
attempt remains visible, including missing, partial, short, or invalid receipts.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from statistics import median

from rl_goal_stage_20261016 import read, digest, verify_inputs, verify_preflight, job_parameter_source
from goal_tracking_pilot_20261016 import validate_pair, verify_pilot_preflight

METRICS = ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps', 'penetration_mm',
           'placement_error_xy_m')


def episode_record(row):
    item = dict(episode=row['episode'], condition_id=row['condition_id'],
                run=row['run'], step_before=row['step_before'],
                step_after=row.get('step_after'), return_value=row.get('return_value'),
                result=row.get('result'), closed='ended_utc' in row,
                receipt_valid=False, errors=[])
    if not item['closed']:
        item['errors'].append('incomplete_attempt')
        return item
    try:
        audit_path = Path(row['run'])/'AUDIT.json'
        item['audit_sha256'] = digest(audit_path)
        if item['audit_sha256'] != row['audit_sha256']:
            raise ValueError('audit_hash_mismatch')
        audit = read(audit_path)
        if not audit.get('training'):
            raise ValueError('not_a_training_receipt')
        result = row['result']
        for key in ('task_success', 'strict_success'):
            if type(result[key]) is not bool or audit[key] is not result[key]:
                raise ValueError('gate_result_mismatch')
        if audit['full_horizon'] is not result['full_task_horizon_completed']:
            raise ValueError('horizon_result_mismatch')
        metrics = {key: audit[key] for key in METRICS}
        if not all(isinstance(v, (int, float)) and math.isfinite(v)
                   for v in metrics.values()):
            raise ValueError('missing_or_nonfinite_metric')
        if not all(type(item[k]) is int for k in ('step_before', 'step_after')) or not (
                0 <= item['step_before'] < item['step_after']):
            raise ValueError('invalid_training_exposure')
        item['metrics'] = metrics
        item.update(receipt_valid=True, stage=audit['stage'],
                    physical_seconds=audit['physical_seconds'],
                    joint_success=result['task_success'] and result['strict_success'])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        item['errors'].append(str(exc))
    return item


def phase(item):
    if item['step_after'] <= 5000:
        return 'warmup'
    return 'learned' if item['step_before'] >= 5000 else 'mixed'


def compare(control, treatment):
    """Require episode+condition identity and equal exposure, retaining exclusions."""
    def index(records):
        result = {}
        for item in records:
            key = (item['episode'], item['condition_id'])
            if key in result:
                raise ValueError('duplicate_episode_condition')
            result[key] = item
        return result
    left, right = index(control), index(treatment)
    pairs = []
    for key in sorted(left.keys() | right.keys()):
        a, b = left.get(key), right.get(key)
        pair = dict(episode=key[0], condition_id=key[1], control=a, treatment=b,
                    comparable=False, reasons=[])
        if a is None or b is None:
            pair['reasons'].append('counterpart_missing')
        elif not all(item['closed'] and item['receipt_valid'] for item in (a, b)):
            pair['reasons'].append('incomplete_or_invalid_receipt')
        else:
            pair['phase'] = phase(a)
            if any(not item['result']['full_task_horizon_completed'] for item in (a, b)):
                pair['reasons'].append('short_episode_retained_not_full_horizon_comparison')
            if (a['step_before'], a['step_after']) != (b['step_before'], b['step_after']):
                pair['reasons'].append('different_training_exposure')
            if not pair['reasons']:
                pair['comparable'] = True
                pair['native_metric_delta_treatment_minus_control'] = {
                    metric: b['metrics'][metric]-a['metrics'][metric] for metric in METRICS}
        pairs.append(pair)
    groups = {}
    for label in ('warmup', 'mixed', 'learned'):
        selected = [p for p in pairs if p['comparable'] and p['phase'] == label]
        groups[label] = dict(pairs=len(selected), median_native_metric_delta={
            m: median(p['native_metric_delta_treatment_minus_control'][m] for p in selected)
            for m in METRICS} if selected else None)
    return dict(pairs=pairs, by_phase=groups)


def summarize(records):
    closed = sum(r['closed'] for r in records)
    successes = sum(r.get('joint_success', False) and r['receipt_valid'] for r in records)
    return dict(attempts=len(records), closed_attempts=closed,
                incomplete_attempts=len(records)-closed,
                invalid_closed_receipts=sum(r['closed'] and not r['receipt_valid'] for r in records),
                verified_joint_successes=successes,
                verified_joint_success_fraction_of_closed=successes/closed if closed else None)


def validate_protocol(protocol, job, registration_sha):
    expected = dict(goal_registration_sha256=registration_sha, seed=job['seed'],
        controller=job['controller'], reward_variant=job['reward_variant'],
        hyperparameter_id=job['hp'], segment_limit=job['limit'],
        maximum_steps=1000000, warmup_steps=5000, utd=1)
    if any(protocol.get(k) != value for k, value in expected.items()):
        raise ValueError('Executed protocol does not match registered pilot')
    if protocol.get('tracking_guidance') != job.get('tracking_guidance'):
        raise ValueError('Executed tracking guidance differs')
    if protocol.get('payload_occupancy_guidance') != job.get('payload_occupancy_guidance'):
        raise ValueError('Executed occupancy guidance differs')
    if protocol['agent_config']['n_step'] != 25 or protocol['reward']['mode'] != job['reward']:
        raise ValueError('Executed credit horizon or reward mode differs')


def report(root):
    reg = read(root/'REGISTRATION.json')
    regularized=reg.get('experiment_kind')=='resumed_actor_regularization_pilot'
    if regularized:
        from goal_actor_regularization_pilot_20261016 import validate_pair as validate_regularized_pair
        validate_regularized_pair(reg)
    else:
        validate_pair(reg)
    verify_inputs(reg)
    verify_preflight(reg) if regularized else verify_pilot_preflight(reg)
    registration_sha = digest(root/'REGISTRATION.json')
    arms, records, protocols = {}, [], []
    for job in reg['jobs']:
        path = Path(job['output'])/'execution.json'
        if path.exists():
            protocol = read(path.parent/'PROTOCOL.json')
            validate_protocol(protocol, job, registration_sha)
            if regularized:
                parent=read(Path(job['checkpoint']).parent/'PROTOCOL.json')
                assert protocol['agent_config']==dict(parent['agent_config'],actor_bc_alpha=job['actor_bc_alpha'])
                assert protocol['reward']==parent['reward'] and protocol['prior_file_sha256']==parent['prior_file_sha256']
                assert protocol['parameter_source']==job_parameter_source(reg,job)
                assert protocol['actor_regularization_migration']==job['actor_regularization_migration']
            protocols.append(protocol)
            # Read once so the embedded snapshot and its digest describe identical bytes.
            blob = path.read_bytes()
            state = json.loads(blob)
            if regularized:
                assert state['resumed_from']['checkpoint']==job['checkpoint']
                assert state['resumed_from']['inherited_steps']==job['inherited_steps']
                assert state['resumed_from']['hashes']==job['checkpoint_hashes']
            conditions = protocol['training_conditions']
            if any(row['condition_id'] != conditions[row['episode'] % len(conditions)]
                   for row in state['rows']):
                raise ValueError('Executed condition order differs from protocol')
            items = [episode_record(row) for row in state['rows']]
            arms[job['name']] = dict(execution_snapshot=state,
                execution_snapshot_sha256=hashlib.sha256(blob).hexdigest(),
                protocol_sha256=digest(path.parent/'PROTOCOL.json'),
                summary=summarize(items))
        else:
            items = []
            arms[job['name']] = dict(status='not_started', summary=summarize(items))
        records.append(items)
    if len(protocols) == 2 and protocols[0]['training_conditions'] != protocols[1]['training_conditions']:
        raise ValueError('Pilot arms have different training conditions')
    comparison=compare(*records)
    if regularized:
        for pair in comparison['pairs']:
            if pair['comparable']:
                pair['same_reward_return_delta_treatment_minus_control']=pair['treatment']['return_value']-pair['control']['return_value']
    return dict(observed_utc=datetime.now(timezone.utc).isoformat(),
        registration_sha256=registration_sha, arms=arms,
        comparison=comparison, same_reward_definition=regularized,convergence_proven=False, final_acceptance=False,
        limitations='Single-seed online training pilot. Matched identities and equal step windows only; policies keep changing within episodes. Return differences are allowed only for the registered same-reward actor-regularization pair. Different reward totals are never subtracted or ranked. Native metrics are not an independent physics/action replay audit. Missing, failed, short and invalid attempts remain visible; no success claim from low error alone.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = report(args.root.resolve())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    print(json.dumps({k: v['summary'] for k, v in result['arms'].items()}))
