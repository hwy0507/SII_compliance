"""Numerical contact audit only; unchanged scene, control and safety gate."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import validate_office_apparatus_v5_20260917 as evaluator


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--variant', choices=('parity', 'tight_solver', 'native_ccd'), required=True)
    a = p.parse_args()
    original = evaluator.make
    options = {}

    def make(flags):
        env, task, spec = original(flags)
        opt = env.model.opt
        if a.variant == 'tight_solver':
            opt.iterations = 2000
            opt.tolerance = 1e-12
            opt.ls_iterations = 100
            opt.ls_tolerance = 1e-4
        elif a.variant == 'native_ccd':
            opt.disableflags = int(opt.disableflags) & ~int(mujoco.mjtDisableBit.mjDSBL_NATIVECCD)
        for key in ('integrator', 'solver', 'iterations', 'ls_iterations',
                    'tolerance', 'ls_tolerance', 'disableflags', 'enableflags'):
            options[key] = getattr(opt, key)
        return env, task, spec

    evaluator.make = make
    try:
        evaluator.run(argparse.Namespace(output=a.output, render=False, events='ball', task='pick_place',
            seed=2026092702, variant=-2, duration=6.2, dt=.0000015625, ball_speed=1.85,
            person_stroke=.22, rod_stroke=.24, esn_model=None, esn_mode='shadow',
            disable_selector_pulse=False, teacher='none', physics_probe_s=.08))
    finally:
        evaluator.make = original
    result = json.loads(a.output.with_suffix('.json').read_text())
    manifest = dict(purpose='numerical_diagnostic_not_ESN_success', variant=a.variant,
                    mujoco_version=mujoco.__version__, options=options, gate_m=.0002,
                    materials_masses_initial_velocity_and_controller_unchanged=True,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    result_sha256=hashlib.sha256(a.output.with_suffix('.json').read_bytes()).hexdigest(),
                    penetration_mm=result['stats']['max_external_penetration_m'] * 1000,
                    task_success=result['task_success'])
    (a.output.parent / 'solver_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
