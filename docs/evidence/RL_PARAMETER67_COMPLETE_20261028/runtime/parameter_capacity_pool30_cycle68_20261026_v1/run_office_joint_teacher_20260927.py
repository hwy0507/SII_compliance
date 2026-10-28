"""Run configurable proprioceptive VMC in an otherwise frozen office evaluator.

This wrapper changes the teacher only. Scene, task, observer, WBC, cadence and
gates are inherited verbatim from the frozen R34/R36 evaluator. Config is fixed
before a rollout; neither simulator truth nor task stage enters the teacher.
"""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import run_vmc_6d_constrained_push_20260918 as vmc

BASE_TEACHER = vmc.SixDVirtualDynamics
ALLOWED_OPTIONS = {
    'stiffness_6d', 'damping_6d', 'mass_6d', 'wrench_limit_6d',
    'deadband_6d', 'velocity_limit_6d', 'offset_limit_6d',
    'action_limit_6d', 'offset_tracking_gain_6d', 'filter_tau',
    'axis_rotation_rpy',
}


def make_teacher_class(config, records):
    options = config.get('options', {})
    if set(options) - ALLOWED_OPTIONS:
        raise ValueError('Unknown teacher option')
    scale = float(config['action_scale'])
    if not np.isfinite(scale) or not 0 < scale <= 1:
        raise ValueError('Teacher action scale must be in (0, 1]')
    BASE_TEACHER(options)  # Fail before creating a rollout on invalid parameters.

    class ConfiguredTeacher(BASE_TEACHER):
        def __init__(self, unused_options):
            if unused_options:
                raise ValueError('Unexpected evaluator-side teacher configuration')
            super().__init__(options)
            self.action_scale = scale

        def act(self, wrench_world, dt=.04):
            raw = super().act(wrench_world, dt)
            action = raw * self.action_scale
            records.append(dict(wrench=np.asarray(wrench_world).copy(), dt=dt,
                                raw_action=raw.copy(), applied_action=action.copy(),
                                filtered=self.filtered.copy(), offset=self.offset.copy(),
                                velocity=self.velocity.copy()))
            return action

    return ConfiguredTeacher


def main():
    # Parse the wrapper-only option manually.  The batch runner intentionally
    # places ``--output`` before this flag, and argparse's mixed known/unknown
    # parsing can otherwise leave the known pair in its ``forwarded`` tail.
    # Keeping the evaluator argv as an exact ordered slice also makes the
    # action-contract audit reproducible.
    raw = list(sys.argv[1:])
    try:
        config_index = raw.index('--teacher-config')
        config_path = Path(raw[config_index + 1])
    except (ValueError, IndexError):
        raise ValueError('Required wrapper option --teacher-config PATH')
    forwarded = raw[:config_index] + raw[config_index + 2:]
    if '--teacher' not in forwarded or forwarded[forwarded.index('--teacher') + 1] != 'vmc6d':
        raise ValueError('Explicit --teacher vmc6d required')
    output = Path(forwarded[forwarded.index('--output') + 1])
    manifest_path = output.parent / 'joint_teacher_manifest.json'
    if manifest_path.exists() or output.with_suffix('.json').exists():
        raise RuntimeError('Preserve existing attempt')
    config = json.loads(config_path.read_text())
    records = []
    cls = make_teacher_class(config, records)
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest = dict(config=config, teacher_input='encoder-derived wrench only',
                    truth_in_actor=False, task_stage_in_actor=False,
                    config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
                    wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    status='running', argv=forwarded)
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    original_argv = sys.argv
    vmc.SixDVirtualDynamics = cls
    sys.argv = [str(ROOT / 'scripts/validate_office_apparatus_v5_20260917.py')] + forwarded
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
        manifest['status'] = 'completed'
    except BaseException as error:
        manifest.update(status='failed', error=repr(error))
        raise
    finally:
        vmc.SixDVirtualDynamics = BASE_TEACHER
        sys.argv = original_argv
        if records:
            trace = output.parent / 'teacher_internal.npz'
            np.savez_compressed(trace, **{k: np.asarray([r[k] for r in records]) for k in records[0]})
            manifest['trace_sha256'] = hashlib.sha256(trace.read_bytes()).hexdigest()
        manifest['steps'] = len(records)
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
