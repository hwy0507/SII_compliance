"""Portable front door to the exported primitive and workstation runners.

Does not need historical outputs, checkpoints or a server account. A smoke
checks initialization and numerical execution, not task/compliance success.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def command_for(args):
    config = json.loads(args.config.read_text())
    flags = dict(config['arguments'])
    if args.smoke:
        # The audited environment validates a minimum episode duration because
        # its contact protocol and post-event metrics need several seconds.
        # Keep the configured duration (rather than inventing an invalid short
        # episode); smoke mode only disables rendering and requests the runner's
        # settle/initialization path where supported.
        flags['duration'] = max(float(flags.get('duration', 6.2)), 6.2)
        flags['settle_only'] = True
        flags['render'] = False
    if args.render:
        flags['render'] = True
    flags.update(output=str(args.output.resolve()), menagerie=str(args.menagerie.resolve()))
    if args.model is not None:
        flags['model'] = str(args.model.resolve())
        flags['mixture'] = 0.
    entry = ROOT / 'scripts' / config['entrypoint']
    if entry.parent != ROOT / 'scripts' or not entry.is_file():
        raise ValueError('Config must select a local scripts entrypoint')
    command = [sys.executable, str(entry)]
    for key, value in flags.items():
        if value is None or value is False:
            continue
        command.append('--' + key.replace('_', '-'))
        if value is not True:
            command.append(str(value))
    environment = dict(os.environ)
    environment.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    environment.setdefault('MUJOCO_GL', 'egl' if sys.platform.startswith('linux') else 'glfw')
    for key, value in config.get('environment', {}).items():
        environment[key] = json.dumps(value) if isinstance(value, dict) else str(value)
    # Never inherit a model cache keyed for a different scenario/model.
    environment.pop('VMC_MODEL_CACHE_DIR', None)
    environment.pop('VMC_MODEL_CACHE_KEY', None)
    return command, environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT / 'configs' / 'workstation_source_demo.json')
    parser.add_argument('--menagerie', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New output prefix, e.g. outputs/demo/rollout')
    parser.add_argument('--model', type=Path)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    command, environment = command_for(args)
    if args.dry_run:
        print(json.dumps({'argv': command, 'cwd': str(ROOT), 'smoke_only': args.smoke}, indent=2))
        return
    for robot in ('franka_fr3', 'franka_emika_panda'):
        if not (args.menagerie / robot).is_dir():
            parser.error(f'Missing Menagerie model directory: {robot}')
    if args.output.with_suffix('.json').exists():
        parser.error('Output exists; choose a new prefix to preserve the prior experiment')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(command, cwd=ROOT, env=environment, check=False)
    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
