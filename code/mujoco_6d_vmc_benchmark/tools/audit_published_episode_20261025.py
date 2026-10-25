"""Add observational physical-substep telemetry to a frozen episode adapter.

The sole source seam appends a recorder call after the existing reward telemetry
sample. It changes no state/action/controller/physics/gate values. Exact source
hashes are recorded; a paired deterministic replay must validate transparency.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Recorder:
    def __init__(self, folder):
        self.folder = folder
        self.data = None
        self.count = 0
        self.limits = None

    def sample(self, env, stats, human_force):
        if self.data is None:
            self.limits = np.asarray(env.torque_limits[:7], float).copy()
            self.data = np.lib.format.open_memmap(self.folder/'audit_substeps.npy', mode='w+',
                dtype=np.float64, shape=(1_100_000, 11))
        if self.count >= len(self.data):
            raise ValueError('Frozen55s/dt5e-5 audit capacity exceeded')
        row = self.data[self.count]
        row[0] = float(env.model.opt.timestep)
        row[1:8] = env.data.qfrc_actuator[:7]
        row[8] = human_force
        row[9] = stats['max_external_penetration_m']
        row[10] = float(env.data.time)
        self.count += 1

    def finish(self, receipt, completed):
        if self.data is not None:
            self.data.flush()
        receipt.update(samples=self.count, completed=completed,
            columns=['dt_s', *['torque_joint'+str(i+1)+'_nm' for i in range(7)],
                     'human_robot_force_sum_n', 'external_penetration_peak_so_far_m', 'time_s'],
            actuator_limits_nm=self.limits.tolist() if self.limits is not None else None,
            substeps_sha256=sha(self.folder/'audit_substeps.npy') if self.data is not None else None,
            note='Read only first samples rows; preallocated tail is not physical data')
        if self.folder.exists():
            (self.folder/'AUDIT_EXTENSION.json').write_text(json.dumps(receipt, indent=2)+'\n')


def run(args):
    source = args.runtime/'source/tools/published_compliance_episode_20261025.py'
    hashes = json.loads((args.runtime/'SOURCE_HASHES.json').read_text())
    if sha(source) != hashes['tools/published_compliance_episode_20261025.py']:
        raise ValueError('Frozen episode adapter mismatch')
    spec = importlib.util.spec_from_file_location('frozen_published_episode', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = inspect.getsource(module.run)
    seam = "                              float(human_force), float(stats['max_external_penetration_m'])))"
    if original.count(seam) != 1:
        raise ValueError('Observation-only telemetry seam changed')
    extension = seam+'\n        PUBLISHED_AUDIT_RECORDER.sample(env, stats, human_force)'
    patched = original.replace(seam, extension)
    recorder = Recorder(args.output.resolve())
    module.PUBLISHED_AUDIT_RECORDER = recorder
    exec(compile(patched, str(Path(__file__).resolve()), 'exec'), module.__dict__)
    receipt = dict(wrapper_sha256=sha(Path(__file__)), base_adapter_sha256=sha(source),
        base_function_sha256=hashlib.sha256(original.encode()).hexdigest(),
        instrumented_function_sha256=hashlib.sha256(patched.encode()).hexdigest(),
        transformation='one recorder call after reward sample; no assignment to MuJoCo state',
        actor_receives_audit_data=False, physics_timestep_changed=False)
    completed = False
    try:
        module.run(args)
        completed = True
    finally:
        recorder.finish(receipt, completed)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--fixture', type=Path)
    parser.add_argument('--reference-plan', type=Path)
    parser.add_argument('--controller', choices=('direct', 'impedance', 'admittance', 'vmc'), default='direct')
    parser.add_argument('--ipc', action='store_true')
    parser.add_argument('--probe-seconds', type=float)
    parser.add_argument('--nominal-reference', action='store_true')
    run(parser.parse_args())
