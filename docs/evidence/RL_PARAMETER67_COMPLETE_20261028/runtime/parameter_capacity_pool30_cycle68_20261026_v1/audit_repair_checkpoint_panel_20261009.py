"""Read-only, finite critic panel for all ten registered RL training jobs.

Capture the latest fully registered checkpoint once, before any diagnostics.
Never select policies by diagnostic outcome or touch final conditions. Each
child loads one frozen learner without simulator or optimizer updates; failures
are recorded alongside successes rather than silently replaced.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys

from office_v7_uniform24_20261008 import read, write, sha, now
from research72_checkpoint_20261003 import checkpoint_hashes
from run_paper_final_validation_20261003 import ENV


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    root, source, out = a.root.resolve(), a.source.resolve(), a.output.resolve()
    assert not out.exists()
    jobs_file = root/'RL_JOBS_CORRECTED.json'
    jobs = read(jobs_file)['jobs']
    assert len(jobs) == 10 and len({(j['family'], j['seed']) for j in jobs}) == 10
    diagnostic = source/'tools/inspect_repair_critic_20261009.py'
    assert diagnostic.is_file()
    entries = []
    for job in jobs:
        segment = Path(job['output'])
        state = read(segment/'execution.json')
        assert state['status'] in ('running', 'complete')
        assert state['checkpoint_rows'], (job['family'], job['seed'])
        row = max(state['checkpoint_rows'], key=lambda c: c['step'])
        cp = Path(row['path'])
        assert checkpoint_hashes(cp) == row['hashes']
        entries.append(dict(family=job['family'], seed=job['seed'], checkpoint=str(cp),
                            step=row['step'], hashes=row['hashes']))
    out.mkdir(parents=True, exist_ok=False)
    write(out/'REGISTRATION.json', dict(created_utc=now(), jobs_sha256=sha(jobs_file),
        entries=entries, source_sha256=sha(__file__), diagnostic_sha256=sha(diagnostic),
        diagnostic_environment_overrides=dict(ENV),
        rule='Latest fully registered checkpoint per job at one snapshot, all ten included.',
        scope='Historical behavior replay only; no physics, optimizer, model selection or final access. Different step counts disclosed.'))
    results = []
    for entry in entries:
        name = entry['family']+'_'+str(entry['seed'])
        result = out/(name+'.json')
        command = [sys.executable, str(diagnostic), '--checkpoint', entry['checkpoint'], '--output', str(result)]
        record = dict(entry, started_utc=now(), command=command)
        with (out/(name+'.log')).open('x') as stream:
            rc = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                env={**os.environ, **ENV}).returncode
        record.update(ended_utc=now(), returncode=rc,
                      status='passed' if rc == 0 else 'diagnostic_failure_preserved')
        assert checkpoint_hashes(Path(entry['checkpoint'])) == entry['hashes']
        if rc == 0:
            evidence = read(result)
            assert evidence['steps'] == entry['step']
            assert evidence['normalization_and_checkpoint_unchanged']
            assert evidence['checkpoint_hashes'] == entry['hashes']
            record.update(output=str(result), output_sha256=sha(result),
                actor_saturation=evidence['actions']['deterministic_actor']['action_abs95_fraction'],
                terminal_value_residual=evidence['terminal_q_minus_normalized_reward'],
                sampled_td_residual=evidence['replay_q_minus_expected_td_backup'],
                temperature=evidence['temperature'])
        results.append(record)
        write(out/'execution.json', dict(status='running', updated_utc=now(), rows=results))
        print(name, record['status'], entry['step'], flush=True)
    write(out/'execution.json', dict(status='complete' if all(r['status'] == 'passed' for r in results)
        else 'incomplete_preserved', ended_utc=now(), rows=results,
        interpretation='Passing means diagnostic reproducibility, not convergence or task success. '
        'Sampled one-action TD residual is stochastic; behavior returns are not current-policy returns.'))
    if any(r['status'] != 'passed' for r in results):
        raise RuntimeError('Incomplete critic diagnostics; failed attempts preserved')


if __name__ == '__main__':
    main()
