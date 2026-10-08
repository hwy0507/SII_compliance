"""One finite, guarded continuation from existing final evaluation to audits.

No recurring scheduler, simulation, learning, checkpoint selection or heldout
access while waiting. Preserve failures. Publication remains a reviewed step.
"""
import argparse
from datetime import datetime, timezone
import fcntl
from pathlib import Path
import subprocess
import sys
import time

from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root, out = a.root.resolve(), a.output.resolve()
    assert out.is_relative_to(root) and not out.exists()
    guard = (root/'.final_delivery.lock').open('a')
    fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
    protocol = read(root/'PROTOCOL.json')
    deadline = datetime.fromisoformat(protocol['dispatch_deadline_utc'])
    source = root/'source_v9'
    entries = [
        ('verification', root/'analysis_stage08_source/verify_repair_final_20261009.py',
            ['--root',str(root),'--output',str(out/'verification')]),
        ('controller_audit', root/'final_controller_audit_source_v1/audit_repair_final_controllers_20261009.py',
            ['--root',str(root),'--dynamic-script',str(root/'dynamic_replay_v5/replay_repair_dynamic_controllers_20261009.py'),
             '--output',str(out/'controller_audit')]),
        ('comparison', root/'analysis_stage13_source/render_repair_comparison_20261009.py',
            ['--root',str(root),'--verified',str(out/'verification'),
             '--controllers',str(out/'controller_audit'),'--output',str(out/'comparison')]),
        ('compute_ledger', root/'analysis_stage08_source/report_repair_compute_20261009.py',
            ['--root',str(root),'--output',str(out/'COMPUTE_LEDGER_FINAL.json')]),
        ('potential_audit', root/'analysis_stage13_source/audit_repair_potential_objective_20261009.py',
            ['--root',str(root),'--output',str(out/'POTENTIAL_OBJECTIVE_FINAL.json')]),
    ]
    expected = {
        'verification':'71727df25d25659588f80239f190b1b331bab0ab0b14597d69b1568c1b85e231',
        'controller_audit':'4f54d0f4026161a2bb33adc25e39ec988f4337424bd100b1ffc7ffe8473b43db',
        'comparison':'07aa97e4f46d805545ddca59001259e160f5899448cf6aea885d856307b05bb9',
        'compute_ledger':'119b715ac721677aecdee302964f71e84022af90a225ab8ffdf9c3a6f7b68019',
        'potential_audit':'f707cb7cf46d9c646fe441a3eed6344c3acc21c2fd18b3bacae2eb69541511db',
    }
    for label, script, _ in entries:
        assert sha(script) == expected[label], label
    dynamic = root/'dynamic_replay_v5/replay_repair_dynamic_controllers_20261009.py'
    assert sha(dynamic) == 'd677c7d5d86073af2c2d9ae3fbba29ad500d6470683088168e2a97045e178f5c'
    assert datetime.now(timezone.utc) < deadline
    out.mkdir()
    registration = dict(registered_utc=now(), source_sha256=sha(__file__),
        protocol_sha256=sha(root/'PROTOCOL.json'), deadline_utc=deadline.isoformat(),
        python=sys.executable, import_source=str(source),
        commands=[dict(stage=label, command=[sys.executable,str(script),*args],
                       script_sha256=expected[label]) for label,script,args in entries],
        dynamic_replay_sha256=sha(dynamic),
        scope='Wait existing384; sequential audit/report only. No new physics, learning, model selection, '
              'Git writes or recurring task. In-flight audits may finish; no new stage after original deadline.')
    write(out/'REGISTRATION.json', registration)
    state = dict(status='running',stage='waiting_existing_final_evaluation',started_utc=now(),checks=[])
    def save():
        state['updated_utc'] = now()
        write(out/'execution.json', state)
    save()
    try:
        while True:
            final = root/'final_evaluation/execution.json'
            if final.exists():
                s = read(final)
                if s['status'] == 'complete':
                    assert s['completed'] == s['expected'] == 384
                    # Report is written after complete state. Wait for both it
                    # and successful coordinator termination before auditing.
                    coordinator = read(root/'continuation_v3/execution.json')
                    if coordinator['status'] == 'complete' and (root/'final_evaluation/REPORT.json').exists():
                        break
                elif s['status'] not in ('running','registered'):
                    raise RuntimeError('Final evaluation incomplete: '+s['status'])
            if (root/'continuation_v3/FAILURE.json').exists():
                raise RuntimeError('Existing coordinator failure preserved; do not continue dependent audits')
            if datetime.now(timezone.utc) >= deadline:
                raise TimeoutError('Original deadline reached before full final cohort')
            result = subprocess.run(['systemctl','--user','is-active','sii-r15-continuation-v3.service'],
                capture_output=True,text=True)
            assert result.returncode in (0,3,4)
            if result.stdout.strip() not in ('active','activating','deactivating'):
                # The coordinator can finish between the two read-only polls.
                # Recheck its receipt instead of labelling normal exit a fault.
                if read(root/'continuation_v3/execution.json')['status'] == 'complete':
                    assert final.exists() and read(final)['status'] == 'complete'
                    assert (root/'final_evaluation/REPORT.json').exists()
                    continue
                raise RuntimeError('Existing coordinator stopped before complete final evidence')
            time.sleep(30)
        lock = read(root/'FINAL_MODEL_LOCK.json')
        assert lock['status'] == 'frozen' and lock['protocol_sha256'] == registration['protocol_sha256']
        state['final_model_lock_sha256'] = sha(root/'FINAL_MODEL_LOCK.json')
        for label, script, args in entries:
            if datetime.now(timezone.utc) >= deadline:
                raise TimeoutError('No new audit stage after original deadline: '+label)
            assert sha(script) == expected[label]
            assert sha(dynamic) == registration['dynamic_replay_sha256']
            state['stage'] = label
            save()
            print(label, 'started',now(),flush=True)
            command = [sys.executable,str(script),*args]
            with (out/(label+'.log')).open('x') as stream:
                rc = subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT).returncode
            state['checks'].append(dict(stage=label,returncode=rc,ended_utc=now(),
                log_sha256=sha(out/(label+'.log'))))
            save()
            assert rc == 0, label+' failed; original output and log retained'
        potential = read(out/'POTENTIAL_OBJECTIVE_FINAL.json')
        assert potential['pending_log_flush'] == 0
        assert all(s['state_status'] == 'complete' for s in potential['segments'])
        state.update(status='complete',stage='audited_comparison_ready_for_review',ended_utc=now(),
            comparison=str(out/'comparison/COMPARISON.md'),
            comparison_sha256=sha(out/'comparison/COMPARISON.md'),
            note='Supervising agent must inspect results, limitations and logs, then publish authorized GitHub changes.')
        save()
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc),ended_utc=now())
        save()
        raise


if __name__ == '__main__':
    main()
