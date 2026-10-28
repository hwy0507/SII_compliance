"""Finish audits for an already running evaluator after a registered handoff.

Never starts physics or learning. A missing/failed child without a complete
result is an error, not a reason to relaunch the evaluation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    tmp.replace(path)


def alive(pid):
    try:
        state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
        return state != 'Z'
    except FileNotFoundError:
        return False


def run(args):
    p = json.loads(args.registration.read_text())
    out = Path(p['output'])
    if (out/'STARTED.json').exists():
        raise FileExistsError('Already adopted; inspect original process')
    for name, h in p['source_and_input_hashes'].items():
        if sha(name) != h:
            raise ValueError('Registered source/input changed: '+name)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    write(out/'STARTED.json', dict(pid=os.getpid(), source_sha256=sha(__file__),
        registration_sha256=sha(args.registration), started_unix=time.time()))
    folder, pid = Path(p['evaluation_output']), p['existing_evaluator_pid']
    result_file = folder/'RESULTS.json'
    try:
        while True:
            running = alive(pid)
            if running:
                command = Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0', b' ').decode()
                if str(folder) not in command or 'evaluate_published_compliance_20261025.py' not in command:
                    raise ValueError('Evaluator PID identity changed')
            if not running:
                result = json.loads(result_file.read_text())
                if not result['finished'] or len(result['episodes']) != len(p['case_ids']):
                    raise RuntimeError('Evaluator exited without all registered results')
                break
            write(out/'PROGRESS.json', dict(state='waiting_for_original_evaluator',
                child_pid=pid, updated_unix=time.time()))
            time.sleep(5)
        ev = result['evaluation']
        if (ev['checkpoint_sha256'] != p['checkpoint_sha256'] or
                ev['case_ids'] != p['case_ids'] or not ev['deterministic'] or
                ev['optimizer_updates_during_evaluation'] != 0):
            raise ValueError('Evaluation receipt differs from handoff')
        sys.path.insert(0, p['audit_runtime'])
        from summarize_published_episode_audit_20261025 import summarize
        from replay_published_filter_audit_20261025 import audit as filter_audit
        from replay_published_torque_audit_20261025 import audit as torque_audit
        nominal = json.loads(Path(p['nominal_rows']).read_text())['rows']
        rows = []
        for case in p['case_ids']:
            ep = folder/case
            physical = summarize(ep, p['method_label_prefix']+p['controller'], case)
            filtered, torque = filter_audit(ep), torque_audit(ep)
            if not filtered['passed'] or not torque['passed']:
                raise ValueError('Recorded execution-chain audit failed')
            for name, value in [('PHYSICAL_AUDIT.json', physical),
                                ('FILTER_REPLAY_AUDIT.json', filtered),
                                ('TORQUE_REPLAY_AUDIT.json', torque)]:
                target = ep/name
                if target.exists() and json.loads(target.read_text()) != value:
                    raise ValueError('Existing audit differs; preserve it: '+name)
                if not target.exists():
                    write(target, value)
            matches = [r for r in nominal if r['method'] == 'nominal_'+p['controller'] and r['case_id'] == case]
            if len(matches) != 1 or physical['row']['torque_thresholds_nm'] != matches[0]['torque_thresholds_nm']:
                raise ValueError('Nominal comparison mismatch')
            rows.append(dict(controller=p['controller'], case_id=case, learned=physical['row'],
                nominal=matches[0], public_filter_verified=True, torque_projection_verified=True,
                episode=str(ep)))
            write(out/'ROWS.json', dict(rows=rows, complete_registered_training_cohort=False,
                final_spt_reference_selected=False, convergence_claim=False))
        write(out/'FINISHED.json', dict(cases=len(rows), finished_unix=time.time(),
            existing_evaluator_pid=pid, physics_restarted=False, new_optimizer_updates=0))
    except BaseException as error:
        write(out/'FAILURE.json', dict(error=repr(error), failed_unix=time.time()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    run(parser.parse_args())
