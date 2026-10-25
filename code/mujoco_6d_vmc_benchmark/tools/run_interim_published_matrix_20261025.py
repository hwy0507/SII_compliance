"""Registered sequential frozen-policy matrix with physical/filter/torque audits.

Uses explicitly selected training cases, retains every failed task, and compares
only matching frozen nominal rows. Does not select the final empirical SPT time.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temp.replace(path)


def main(args):
    p = json.loads(args.registration.read_text())
    out, audit_root = Path(p['output']), Path(p['audit_runtime'])
    if (out/'STARTED.json').exists():
        raise FileExistsError('Matrix already dispatched; inspect original process')
    for path, digest in p['source_and_input_hashes'].items():
        if sha(path) != digest:
            raise ValueError('Registered source/input drift: '+path)
    for path in p['required_finished_receipts']:
        json.loads(Path(path).read_text())
    os.sched_setaffinity(0, {p['cpu']})
    write(out/'STARTED.json', dict(pid=os.getpid(), started_unix=time.time(),
        registration_sha256=sha(args.registration), source_sha256=sha(__file__)))
    sys.path.insert(0, str(audit_root))
    from summarize_published_episode_audit_20261025 import summarize
    from replay_published_filter_audit_20261025 import audit as filter_audit
    from replay_published_torque_audit_20261025 import audit as torque_audit
    nominal = json.loads(Path(p['nominal_rows']).read_text())['rows']
    rows = []
    try:
        for job in p['jobs']:
            method = job['controller']
            folder = out/method
            command = [sys.executable, '-B', str(audit_root/'evaluate_published_compliance_20261025.py'),
                '--runtime', p['runtime'], '--registration', p['training_registration'],
                '--checkpoint', job['checkpoint'], '--output', str(folder), '--device', job['device'],
                '--learner-cpu', str(p['cpu']), '--physics-cpu', str(p['cpu']), '--audit-substeps']
            if p.get('stochastic', False):
                command.extend(['--stochastic', '--action-seed', str(p['action_seed'])])
            for case in p['case_ids']:
                command.extend(['--case-id', case])
            with (out/(method+'.log')).open('xb') as log:
                child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
                write(out/'PROGRESS.json', dict(controller=method, child_pid=child.pid,
                    state='physics_running', audited_cases=len(rows), planned_cases=len(p['jobs'])*len(p['case_ids']),
                    started_unix=time.time(), command=command))
                if child.wait() != 0:
                    raise RuntimeError('Physical evaluation failed; retain all evidence: '+method)
            for case in p['case_ids']:
                episode = folder/case
                physical = summarize(episode, p.get('method_label_prefix', 'cheq_cycle01_')+method, case)
                filtered, torque = filter_audit(episode), torque_audit(episode)
                write(episode/'PHYSICAL_AUDIT.json', physical)
                write(episode/'FILTER_REPLAY_AUDIT.json', filtered)
                write(episode/'TORQUE_REPLAY_AUDIT.json', torque)
                fixed = [r for r in nominal if r['method'] == 'nominal_'+method and r['case_id'] == case]
                if len(fixed) != 1:
                    raise ValueError('Missing or ambiguous same-interface nominal comparison')
                if physical['row']['torque_thresholds_nm'] != fixed[0]['torque_thresholds_nm']:
                    raise ValueError('Comparison threshold mismatch')
                rows.append(dict(controller=method, case_id=case, learned=physical['row'], nominal=fixed[0],
                    public_filter_verified=filtered['passed'], torque_projection_verified=torque['passed'],
                    episode=str(episode)))
                write(out/'ROWS.json', dict(rows=rows, complete_registered_training_cohort=False,
                    final_spt_reference_selected=False, convergence_claim=False))
        write(out/'FINISHED.json', dict(ended_unix=time.time(), cases=len(rows),
            complete_interim_matrix=True, complete_registered_training_cohort=False,
            final_spt_reference_selected=False, convergence_claim=False,
            scope=p.get('scope', 'Three prespecified representative training cases per interface, not final ranking')))
    except BaseException as error:
        write(out/'FAILURE.json', dict(error=repr(error), audited_cases=len(rows)))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
