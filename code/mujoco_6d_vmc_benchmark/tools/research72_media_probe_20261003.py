"""Measure full three-view render/decode cost on the known train_000 teacher.

One local3GiB render process, recorded poses only. No integration, new actor
execution, fitted weights, final-test manifest or controller ranking.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('rollout', 'metadata', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    meta = json.loads(args.metadata.read_text())
    known = meta['lineage'][0]
    assert known['condition_id'] == 'train_000' and known['data_role'] == 'train'
    assert known['actual_execution_labels'] and sha(args.rollout) == known['sha256']
    files = [args.rollout.with_suffix(ext) for ext in ('.npz', '.json', '.mjb')]
    hashes = {str(p.resolve()): sha(p) for p in files}
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = int((cg/'memory.max').read_text()); assert memory <= 3*1024**3
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    out = args.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    tools = Path(__file__).resolve().parent
    sources = [Path(__file__), *[tools/name for name in ('render_office_threeview_20260929.py',
        'audit_tool_media_20261002.py', 'archive_tool_campaign_20261002.py')]]
    state = dict(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
        host=platform.node(), python=sys.executable, argv=sys.argv, memory_max=memory,
        source_sha256={str(p): sha(p) for p in sources}, input_sha256=hashes,
        metadata_sha256=sha(args.metadata), input_identity='train_000', physics_integration_steps=0,
        final_conditions_read=False, training_updates=0, steps=[])
    commands = [
        [sys.executable, str(tools/'render_office_threeview_20260929.py'), '--rollout', str(args.rollout.resolve()),
         '--output', str(out/'media'), '--label', 'known train_000 | original teacher | diagnostic | dt=5e-5',
         '--scene-label', 'office-validation-v6', '--stride', '1', '--fps', '25', '--gif-stride', '5'],
        [sys.executable, str(tools/'audit_tool_media_20261002.py'), str(out/'media'), '--allow-aborted']]
    write(out/'execution.json', state)
    try:
        for index, command in enumerate(commands):
            row = dict(command=command, started_utc=datetime.now(timezone.utc).isoformat()); state['steps'].append(row)
            write(out/'execution.json', state); started = time.perf_counter()
            with (out/f'step_{index}.log').open('x') as log:
                row['returncode'] = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
            row.update(wall_seconds=time.perf_counter()-started, ended_utc=datetime.now(timezone.utc).isoformat())
            write(out/'execution.json', state); assert row['returncode'] == 0
        assert all(sha(Path(p)) == h for p, h in hashes.items())
        assert all(sha(p) == state['source_sha256'][str(p)] for p in sources)
        state.update(status='complete', media_audit_sha256=sha(out/'media/MEDIA_AUDIT.json'),
            caution='One local known training trajectory: render/decode engineering only; not final media or policy success evidence.')
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state.update(ended_utc=datetime.now(timezone.utc).isoformat(), memory_peak=int((cg/'memory.peak').read_text()))
        write(out/'execution.json', state)
    print(json.dumps(dict(status=state['status'], wall_seconds=[r['wall_seconds'] for r in state['steps']],
        memory_peak=state['memory_peak'], execution_sha256=sha(out/'execution.json'))))


if __name__ == '__main__':
    main()
