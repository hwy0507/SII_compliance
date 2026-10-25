"""Training-set comparison using the user's empirical minimum-time reference.

Consumes audit summaries, never runs a simulator or verifies physical evidence.
The registered method x case matrix must be complete, including failures.
This is a separate protocol from the preregistered-reference SPT standard.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


SCHEMA = 'sii-training-comparison-empirical-v1'


def number(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'{name}: expected a number')
    value = float(value)
    if not math.isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f'{name}: invalid value')
    return value


def vector7(values, name, *, positive=False):
    if not isinstance(values, (list, tuple)) or len(values) != 7:
        raise ValueError(f'{name}: expected seven values')
    return [number(x, name, positive=positive) for x in values]


def contact_torque_summary(samples, thresholds_nm):
    """Time-weighted all-joints compliance during actual human contact only.

    samples: iterable of {dt_s, human_contact, torque_nm[7]}. Contact labels
    must come from the registered human-robot channel, not all external contacts.
    Signed torque is allowed; thresholds apply to absolute actuator torque.
    """
    thresholds = vector7(thresholds_nm, 'thresholds', positive=True)
    elapsed = contact = compliant = 0.
    excess_integrals = [0.] * 7
    peaks = [0.] * 7
    count = 0
    for row in samples:
        count += 1
        dt = number(row['dt_s'], 'dt_s', positive=True)
        active = row['human_contact']
        if type(active) is not bool:
            raise ValueError('human_contact must be boolean')
        raw = row['torque_nm']
        if (not isinstance(raw, (list, tuple)) or len(raw) != 7
                or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in raw)):
            raise ValueError('torque_nm must contain seven signed numbers')
        torque = vector7([abs(x) for x in raw], 'torque_nm')
        elapsed += dt
        peaks = [max(a, b) for a, b in zip(peaks, torque)]
        if active:
            contact += dt
            compliant += dt * all(t <= limit for t, limit in zip(torque, thresholds))
            excess_integrals = [old + dt * max(0., t - limit)
                                for old, t, limit in zip(excess_integrals, torque, thresholds)]
    if not count:
        raise ValueError('No physical samples supplied')
    return dict(elapsed_s=elapsed, human_contact_s=contact,
                human_below_threshold_s=compliant,
                human_above_threshold_s=contact-compliant,
                human_compliance_ratio=compliant/contact if contact else None,
                human_torque_excess_integral_nm_s_per_joint=excess_integrals,
                peak_torque_nm_per_joint=peaks)


def completion_bonus(*, task_success, strict_success, completion_time_s, horizon_s=55.):
    """Optional reward-only efficiency term; never uses a moving empirical T_ref.

    Value is 5 * (1 - T/H) on strict success and zero on failure. This is a
    monotone time surrogate, NOT exact SPT. Not yet wired into the trainer.
    """
    horizon = number(horizon_s, 'horizon_s', positive=True)
    if type(task_success) is not bool or type(strict_success) is not bool:
        raise ValueError('Success labels must be boolean')
    if strict_success and not task_success:
        raise ValueError('Strict requires Task')
    if not strict_success:
        return 0.
    time = number(completion_time_s, 'completion_time_s', positive=True)
    if time > horizon:
        raise ValueError('Completion lies outside the audit horizon')
    return 5. * (1. - time/horizon)


def summarize(data):
    if data.get('schema') != SCHEMA:
        raise ValueError('Unknown comparison schema')
    methods, cases = data['methods'], data['case_ids']
    for name, ids in [('methods', methods), ('case_ids', cases)]:
        if (not isinstance(ids, list) or not ids
                or any(not isinstance(x, str) or not x.strip() for x in ids)
                or len(set(ids)) != len(ids)):
            raise ValueError(f'{name} must be a nonempty list of distinct identifiers')
    thresholds = vector7(data['torque_thresholds_nm'], 'torque_thresholds_nm', positive=True)
    horizon = number(data['horizon_s'], 'horizon_s', positive=True)
    expected = {(m, c) for m in methods for c in cases}
    records = {}
    for row in data['records']:
        key = row['method'], row['case_id']
        if key not in expected or key in records:
            raise ValueError(f'Unexpected or duplicate comparison row: {key}')
        for field in ('task_success', 'strict_success', 'full_horizon', 'machine_safety_violation'):
            if type(row[field]) is not bool:
                raise ValueError(f'{field} must be boolean')
        if row['strict_success'] and (not row['task_success'] or row['machine_safety_violation']):
            raise ValueError('Strict success contradicts Task/safety labels')
        elapsed = number(row['elapsed_s'], 'elapsed_s', positive=True)
        if elapsed > horizon+1e-6 or (row['full_horizon'] and abs(elapsed-horizon) > 1e-6):
            raise ValueError('Inconsistent audit horizon')
        if row['task_success']:
            if not row['full_horizon']:
                raise ValueError('Task success requires the full frozen audit horizon')
            time = number(row['completion_time_s'], 'completion_time_s', positive=True)
            if time > elapsed or row.get('completion_time_definition') != 'final_stable_placement_certification':
                raise ValueError('A gate-matched completion timestamp is required')
        elif row.get('completion_time_s') is not None:
            raise ValueError('Failed task must not supply a completion time')
        if row['torque_thresholds_nm'] != thresholds:
            raise ValueError('All methods must use the same declared thresholds')
        vector7(row['peak_torque_nm_per_joint'], 'peak_torque_nm_per_joint')
        contact = number(row['human_contact_s'], 'human_contact_s')
        below = number(row['human_below_threshold_s'], 'human_below_threshold_s')
        if below > contact+1e-9 or contact > elapsed+1e-6:
            raise ValueError('Invalid contact-only denominator')
        records[key] = row
    if set(records) != expected:
        raise ValueError(f'Missing {len(expected-set(records))} registered rows; failures cannot be omitted')
    successful = [r['completion_time_s'] for r in records.values() if r['strict_success']]
    reference = min(successful) if successful else None
    reports = {}
    for method in methods:
        rows = [records[method, case] for case in cases]
        n = len(rows)
        contact = sum(r['human_contact_s'] for r in rows)
        below = sum(r['human_below_threshold_s'] for r in rows)
        peaks = [max(r['peak_torque_nm_per_joint'][j] for r in rows) for j in range(7)]
        reports[method] = dict(
            episodes=n, task_success_rate=sum(r['task_success'] for r in rows)/n,
            strict_success_rate=sum(r['strict_success'] for r in rows)/n,
            spt_empirical=sum(reference/max(reference, r['completion_time_s'])
                              if r['strict_success'] else 0. for r in rows)/n,
            peak_torque_nm=max(peaks), peak_torque_nm_per_joint=peaks,
            human_contact_s=contact, human_below_threshold_s=below,
            human_above_threshold_s=contact-below,
            human_compliance_ratio=below/contact if contact else None,
            zero_contact_episodes=sum(r['human_contact_s'] == 0 for r in rows),
            machine_safety_violation_rate=sum(r['machine_safety_violation'] for r in rows)/n)
    return dict(schema=SCHEMA, scope='training_set_only',
                reference_rule='global_minimum_strict_success_time_across_all_registered_results',
                reference_time_s=reference, reference_is_posthoc=True,
                success_definition='task_success AND strict_success',
                torque_thresholds_nm=thresholds,
                threshold_status='engineering_reference_not_validated_human_comfort',
                physical_evidence_verified=False, methods=reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    report = summarize(json.loads(raw))
    report['input_sha256'] = hashlib.sha256(raw).hexdigest()
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
