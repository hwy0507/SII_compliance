"""Review completed nominal interfaces without running physics or controllers.

Verify archived physical/filter evidence and observed actuator limits. Earlier
nominal traces lack torque-projection inputs: do not claim projection replay.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main(registration):
    p = read(registration)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    for name, expected in p['input_hashes'].items():
        if sha(name) != expected:
            raise ValueError('Registered input drift: '+name)
    if sha(__file__) != p['source_sha256']:
        raise ValueError('Review source drift')
    out = Path(p['output'])
    out.mkdir(exist_ok=False)
    original = read(p['nominal_registration'])
    train = read(original['training_registration'])
    if sha(original['training_registration']) != original['training_registration_sha256']:
        raise ValueError('Nominal cohort registration drift')
    if sha(Path(original['runtime'])/'RUNTIME.json') != original['runtime_sha256']:
        raise ValueError('Nominal runtime drift')
    for name, digest in original['audit_sources'].items():
        if sha(Path(original['audit_runtime'])/name) != digest:
            raise ValueError('Original audit source drift: '+name)
    conditions = {c['id']: c for c in train['conditions']}
    rows = [r for f in p['row_files'] for r in read(f)['rows']]
    result = dict(registration_sha256=sha(registration), methods={}, new_physics=0,
        optimizer_updates=0, final_spt_reference_selected=False,
        complete_four_interface_matrix=False, projection_replay_claim=False)
    for method in p['methods']:
        selected = [r for r in rows if r['method'] == 'nominal_'+method]
        if len(selected) != len(conditions) or {r['case_id'] for r in selected} != set(conditions):
            raise ValueError('Selected interface lacks complete registered cohort: '+method)
        evidence = []
        for row in selected:
            folder = Path(row['episode'])
            physical = read(folder/'PHYSICAL_AUDIT.json')
            filtered = read(folder/'FILTER_REPLAY_AUDIT.json')
            reward = read(folder/'REWARD_AUDIT.json')
            hashes = {}
            for report in [physical, filtered]:
                for name, digest in report['evidence_sha256'].items():
                    if name in hashes and hashes[name] != digest:
                        raise ValueError('Audit receipts disagree: '+name)
                    hashes[name] = digest
            for name, digest in hashes.items():
                if sha(folder/name) != digest:
                    raise ValueError('Archived evidence drift: '+str(folder/name))
            for key, value in physical['row'].items():
                if row[key] != value:
                    raise ValueError('Matrix row differs from physical audit: '+key)
            if not (filtered['passed'] and filtered['decisions'] == 1375
                    and physical['actor_input_and_executed_action_trace_equal']
                    and reward['steps'] == 1375 and reward['zero_actions_verified']):
                raise ValueError('Incomplete nominal physical/filter/reward audit')
            if abs(sum(reward['components'].values())-reward['reward']) > 1e-7 or reward['reward'] != row['reward']:
                raise ValueError('Reward aggregate mismatch')
            if sha(folder/'rollout.mjb') != conditions[row['case_id']]['model_sha256']:
                raise ValueError('Actual model differs from cohort')
            journal = [json.loads(line) for line in (folder/'actor_intervals.jsonl').read_text().splitlines()]
            if len(journal) != 1375 or any(np.any(np.asarray(r['action']) != 0) for r in journal):
                raise ValueError('Nominal raw actions are not identically zero')
            extension = read(folder/'AUDIT_EXTENSION.json')
            meta = read(folder/'audit_filter.json')
            if sha(meta['source_file']) != meta['source_sha256']:
                raise ValueError('Frozen filter/projection configuration source drift')
            n = extension['samples']
            if n != 1100000 or not extension['completed']:
                raise ValueError('Not a complete 55 second nominal episode')
            raw = np.load(folder/'audit_substeps.npy', mmap_mode='r', allow_pickle=False)[:n]
            if raw.shape != (n, 11) or not np.isfinite(raw).all() or not np.all(raw[:, 0] == .00005):
                raise ValueError('Invalid physical substeps')
            limits = np.asarray(extension['actuator_limits_nm'])
            if not np.array_equal(limits, [87.]*4+[12.]*3):
                raise ValueError('Frozen actuator limits differ')
            torque = raw[:, 1:8]
            peaks = abs(torque).max(axis=0)
            if np.any(peaks > limits+1e-12):
                raise ValueError('Observed actuator amplitude exceeded')
            servo = torque.reshape(-1, 80, 7)
            if not np.array_equal(servo, np.broadcast_to(servo[:, :1, :], servo.shape)):
                raise ValueError('Observed torque changed within registered servo interval')
            delta = abs(np.diff(servo[:, 0, :], axis=0))
            rate = np.asarray(meta['config']['maximum_torque_rate_nmps'])
            if not np.array_equal(rate, [700.]*4+[160.]*3):
                raise ValueError('Original torque slew limits differ')
            if np.any(delta > rate*.004+1e-10):
                raise ValueError('Observed consecutive-servo torque slew exceeded')
            contact = raw[:, 8] > original['contact_force_onset_n']
            compliant = np.all(abs(torque) <= np.asarray(original['torque_thresholds_nm']), axis=1)
            contact_s = float(raw[contact, 0].sum())
            below_s = float(raw[contact & compliant, 0].sum())
            if (not np.array_equal(peaks, row['peak_torque_nm_per_joint'])
                    or abs(contact_s-row['human_contact_s']) > 1e-8
                    or abs(below_s-row['human_below_threshold_s']) > 1e-8):
                raise ValueError('Recomputed physical metrics disagree')
            if contact_s == 0 and row['human_compliance_ratio'] is not None:
                raise ValueError('No-contact compliance must be NA')
            evidence.append(dict(case_id=row['case_id'], samples=n,
                observed_amplitude_verified=True, observed_subsequent_servo_slew_verified=True,
                first_servo_previous_torque_verified=False, projection_inputs_available=False,
                peak_observed_slew_nmps_per_joint=(delta.max(axis=0)/.004).tolist(),
                receipts={name:sha(folder/name) for name in
                    ['PHYSICAL_AUDIT.json','FILTER_REPLAY_AUDIT.json','REWARD_AUDIT.json']},
                evidence_sha256=hashes))
            print(method, row['case_id'], 'verified', flush=True)
            del raw, torque, servo, delta
        summaries = {}
        for category in ['all', 'passive_corner', 'active_short', 'active_long']:
            group = selected if category == 'all' else [r for r in selected if r['category'] == category]
            success = [r for r in group if r['task_success'] and r['strict_success']]
            contact_s = sum(r['human_contact_s'] for r in group)
            below_s = sum(r['human_below_threshold_s'] for r in group)
            summaries[category] = dict(episodes=len(group), task=sum(r['task_success'] for r in group),
                strict=sum(r['strict_success'] for r in group),
                machine_safety_violations=sum(r['machine_safety_violation'] for r in group),
                mean_reward=float(np.mean([r['reward'] for r in group])),
                peak_generalized_torque_nm=max(max(r['peak_torque_nm_per_joint']) for r in group),
                strict_success_completion_time_s=[r['completion_time_s'] for r in success],
                human_contact_s=contact_s, human_compliant_s=below_s,
                contact_time_weighted_compliance=below_s/contact_s if contact_s else None,
                episodes_with_human_contact=sum(r['human_contact_s'] > 0 for r in group),
                strict_failure_stages=dict(Counter(r['final_task_stage'] for r in group if not r['strict_success'])))
        result['methods'][method] = dict(summary=summaries, rows=selected, evidence=evidence)
        write(out/(method+'.json'), result['methods'][method])
    result.update(finished_unix=time.time(), limitations=[
        'Complete selected nominal interfaces, not the final four-interface learned/ESN comparison.',
        'Engineering torque thresholds; no clinical human-comfort validation.',
        'Existing physical/filter replay verified; actual amplitude and subsequent-servo slew recomputed.',
        'Original v4 has no torque-projection inputs or initial previous torque; full projection replay is not claimed.',
        'No final Tref, SPT selection, policy ranking, new simulation or training.'])
    write(out/'REVIEW.json', result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args().registration)
