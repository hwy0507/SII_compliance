"""Reconstruct every final cohort's sampled placement without new dynamics.

Uses the original 25 Hz discrete gate. Aborted runs remain failures, with
their short histories and explicit reasons; they are never padded to 55 s.
"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import sha, write, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); report = json.loads(a.report.read_text()); out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('audit_planned_corner_placement_20261002.py')
    shutil.copy2(source, out/source.name); shutil.copy2(__file__, out/Path(__file__).name)
    state = dict(status='running', started_utc=now(), argv=sys.argv,
                 report_sha256=sha(a.report), source_sha256=sha(source), rows=[])
    write(out/'execution.json', state)
    try:
        for index, row in enumerate(report['rows']):
            run = Path(row['run']); assert sha(run/'rollout.npz') == row['trace_sha256']
            summary = json.loads((run/'rollout.json').read_text())
            entry = dict(run=str(run), tier=row['tier'], condition=row['condition'],
                         name=row['name'], trace_sha256=row['trace_sha256'])
            if row['full_horizon']:
                output = out/(f'{index:03d}_'+row['name']+'.json')
                command = [sys.executable, str(source), '--run', str(run), '--prefix', 'rollout', '--output', str(output)]
                with (out/f'{index:03d}.log').open('x') as log:
                    subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT)
                result = json.loads(output.read_text())
                assert result['task_success'] == row['task_success'] == summary['task_success']
                entry.update(status='sampled_state_verified', task_success=result['task_success'],
                             audit_sha256=sha(output), command=command)
            else:
                assert not row['task_success'] and not row['strict_success']
                assert row['abort_reason'] == summary['abort_reason'] and row['abort_reason']
                entry.update(status='aborted_failure_preserved', task_success=False, abort_reason=row['abort_reason'])
            state['rows'].append(entry); write(out/'execution.json', state)
        assert sha(a.report) == state['report_sha256'] and sha(source) == state['source_sha256']
        state.update(status='complete', sampled_state_verified=sum(r['status']=='sampled_state_verified' for r in state['rows']),
                     aborted_failures=sum(r['status']=='aborted_failure_preserved' for r in state['rows']))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc']=now(); write(out/'execution.json', state)
    print(json.dumps({k:state[k] for k in ('status','sampled_state_verified','aborted_failures')}))


if __name__ == '__main__':
    main()
