"""All locked models on the first common final identity; never select a win.

Render saved states only, with three synchronized views and original speed.
No physics rollout, fitting, checkpoint selection or sealed manifest read.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from research72_final_lock_20261003 import read, sha


def choose(lock, report):
    condition = sorted(report['conditions'])[0]
    rows = {(r['candidate'], r['condition_id']): r for r in report['raw_rows']}
    assert len(rows) == len(report['raw_rows'])
    selected = []
    for candidate in sorted(lock['candidates'], key=lambda c: c['name']):
        row = rows.get((candidate['name'], condition))
        item = dict(candidate=candidate['name'], category=candidate['category'], seed=candidate.get('seed'),
                    condition_id=condition, status='missing_audited_episode' if row is None else 'planned')
        if row is not None:
            metrics = row['metrics']
            item.update(run=row['run'], trace_sha256=metrics['trace_sha256'], model_sha256=metrics['model_sha256'],
                        task_success=metrics['task_success'], strict_success=metrics['strict_success'],
                        full_horizon=metrics['full_horizon'], abort_reason=metrics['abort_reason'])
        selected.append(item)
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('model-lock', 'report', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args(); lock = read(args.model_lock); report = read(args.report)
    assert sha(args.model_lock) == report['model_lock_sha256']
    assert lock['training_closed'] and lock['all_registered_finalists_included']
    selected = choose(lock, report)
    args.output.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    scripts = [tools/'render_office_threeview_20260929.py', tools/'audit_tool_media_20261002.py']
    specification = dict(created_utc=datetime.now(timezone.utc).isoformat(), source_sha256=sha(Path(__file__)),
        report_sha256=sha(args.report), model_lock_sha256=sha(args.model_lock),
        renderer_sources={str(p): sha(p) for p in scripts}, selected=selected,
        rule='Lexicographically first shared final identity, every locked model and seed, including failures. Missing audit stays missing.',
        camera_views=['overview', 'end-effector', 'pillar-corner'], physics_rerun=False,
        fps=25, frame_stride=1, simulation_deadline_not_extended=True)
    def write(path, data):
        path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
    write(args.output/'SPECIFICATION.json', specification)
    state = dict(status='running', specification_sha256=sha(args.output/'SPECIFICATION.json'), rows=[])
    try:
        for index, entry in enumerate(selected):
            row = dict(entry); state['rows'].append(row)
            write(args.output/'execution.json', state)
            if row['status'] != 'planned':
                continue
            run = Path(row['run'])
            assert sha(run/'rollout.npz') == row['trace_sha256']
            assert sha(run/'rollout.mjb') == row['model_sha256']
            target = args.output/(f'{index:02d}_'+row['candidate'])
            label = row['candidate']+' | '+row['condition_id']+' | dt=5e-5'
            if not row['full_horizon']:
                label += ' | ABORT: '+str(row['abort_reason'])
            commands = [[sys.executable, str(scripts[0]), '--rollout', str(run/'rollout.npz'),
                '--output', str(target), '--label', label, '--scene-label', 'office-validation-v6',
                '--stride', '1', '--fps', '25', '--gif-stride', '5'],
                [sys.executable, str(scripts[1]), str(target), '--allow-aborted']]
            row['commands'] = commands
            for step, command in enumerate(commands):
                assert all(sha(p) == specification['renderer_sources'][str(p)] for p in scripts)
                with (args.output/f'{index:02d}_{step}.log').open('x') as log:
                    subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT,
                        env={**os.environ, 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1', 'MKL_NUM_THREADS':'1'})
            row.update(status='rendered_and_decode_audited', video=str(target/'replay_threeview.mp4'),
                video_sha256=sha(target/'replay_threeview.mp4'), media_audit_sha256=sha(target/'MEDIA_AUDIT.json'))
            write(args.output/'execution.json', state)
        state['status'] = 'complete_with_missing' if any(r['status']=='missing_audited_episode' for r in state['rows']) else 'complete'
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = datetime.now(timezone.utc).isoformat()
        write(args.output/'execution.json', state)


if __name__ == '__main__':
    main()
