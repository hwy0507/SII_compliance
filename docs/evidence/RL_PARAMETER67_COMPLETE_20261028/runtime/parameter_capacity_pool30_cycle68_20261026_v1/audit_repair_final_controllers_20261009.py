"""Audit every classical/parameter-RL episode after the full final cohort ends.

144 parameter-shield replays, 96 chronological VMC/admittance state/action
replays, and 48 native-impedance servo-bound audits. No physics or training.
Each controller replay gets its own process so native backend overrides cannot
leak between controllers. Incomplete/failed checks remain explicit.
"""
import argparse
from pathlib import Path
import subprocess
import sys
from office_v7_uniform24_20261008 import read, write, sha, now
from evaluate_baseline_repair_20261008 import validate_candidate


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--dynamic-script', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    assert not out.exists()
    lock = read(root/'FINAL_MODEL_LOCK.json')
    assert lock['status'] == 'frozen' and lock['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert lock['models_sha256'] == sha(lock['models'])
    source = Path(lock['source'])
    for rel, digest in lock['source_hashes'].items(): assert sha(source/rel) == digest
    final = root/'final_evaluation'
    state = read(final/'execution.json')
    assert state['status'] == 'complete' and state['completed'] == state['expected'] == 384
    families = {prefix+method for prefix in ('classical_', 'parameter_')
                for method in ('vmc', 'admittance', 'impedance')}
    candidates = {c['family']:c for c in read(lock['models'])['candidates'] if c['family'] in families}
    assert set(candidates) == families
    for candidate in candidates.values(): validate_candidate(candidate)
    ids = {c['id'] for c in read(final/'CONDITIONS.json')['conditions']}
    assert len(ids) == 24
    rows = [read(path) for path in sorted((final/'episodes').glob('*.execution.json'))]
    rows = [r for r in rows if r['family'] in families]
    assert len(rows) == 144 and {(r['family'], r['condition_id']) for r in rows} == {
        (family, condition) for family in families for condition in ids}
    shield_script = source/'tools/audit_repair_parameter_trace_20261008.py'
    assert shield_script.is_file() and a.dynamic_script.is_file()
    out.mkdir(parents=True, exist_ok=False)
    write(out/'REGISTRATION.json', dict(created_utc=now(), source_sha256=sha(__file__),
        lock_sha256=sha(root/'FINAL_MODEL_LOCK.json'), expected_episodes=144,
        expected_shield_checks=144, expected_dynamic_checks=96, expected_native_servo_checks=48,
        scripts={str(p):sha(p) for p in (shield_script, a.dynamic_script)},
        purpose='Complete frozen cohort audit; no model selection, physics or optimization.'))
    results = []
    for row in rows:
        c = candidates[row['family']]
        assert row['status'] == 'complete' and row['candidate'] == c['name']
        run = final/'episodes'/row['name']
        assert sha(run/'AUDIT.json') == row['audit_sha256']
        assert sha(run/'rollout.npz') == row['trace_sha256']
        method = row['family'].split('_', 1)[1]
        record = dict(family=row['family'], condition_id=row['condition_id'], run=str(run),
                      started_utc=now(), checks=[])
        scripts = [('shield', shield_script)]
        if method != 'impedance': scripts.append(('dynamic', a.dynamic_script))
        for label, script in scripts:
            target = out/(row['name']+'.'+label+'.json')
            command = [sys.executable, str(script), '--run', str(run),
                       '--parameter-source', c['parameter_source'], '--output', str(target)]
            with (out/(row['name']+'.'+label+'.log')).open('x') as stream:
                rc = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT).returncode
            check = dict(kind=label, command=command, returncode=rc,
                         status='passed' if rc == 0 else 'audit_failure_preserved')
            if rc == 0:
                value = read(target)
                assert value['status'] == 'passed' and value['method'] == method
                if label == 'dynamic': assert value['action_output_compared']
                if label == 'shield' and method == 'impedance': assert value['native_servo']['rows'] > 0
                check.update(evidence=str(target), evidence_sha256=sha(target))
            record['checks'].append(check)
        record.update(ended_utc=now(), status='passed' if all(c['status'] == 'passed' for c in record['checks'])
                      else 'audit_failure_preserved')
        results.append(record)
        write(out/'execution.json', dict(status='running', updated_utc=now(), rows=results))
        if len(results) % 12 == 0: print(len(results), 'of144 audited', flush=True)
    failures = [r for r in results if r['status'] != 'passed']
    write(out/'execution.json', dict(status='complete' if not failures else 'incomplete_preserved',
        ended_utc=now(), expected=144, passed=len(results)-len(failures), rows=results,
        scope='Virtual state/action replay and parameter shielding; native command/spring/torque slew bounds. '
        'Physical torque/speed/penetration audited separately. No independent full robot dynamics replay or passivity proof.'))
    if failures: raise RuntimeError(f'{len(failures)} controller audits failed; all attempts retained')


if __name__ == '__main__':
    main()
