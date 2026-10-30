"""Add observational physical-substep telemetry to a frozen episode adapter.

Source seams append a recorder after the existing reward telemetry sample and
observe public-filter calls/returns. No physical or filter state is assigned.
Exact hashes are recorded; paired deterministic replay validates transparency.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
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
        self.filter_rows = []
        self.filter_metadata = None
        self.torque_rows = []
        self.torque_metadata = None

    def bind_torque(self, env, backend):
        """Observe the common torque projection before native adapters bind it."""
        if self.torque_metadata is not None or env.execution_mode != 'twist':
            raise ValueError('Torque audit requires one registered twist environment')
        original = backend.safe_velocity_tracking_torque
        source = Path(inspect.getfile(original))
        self.torque_metadata = dict(config=asdict(env.safety_config),
            source_file=str(source), source_sha256=sha(source),
            initial_previous_torque=np.asarray(env.previous_torque).copy(),
            torque_limits=np.asarray(env.torque_limits[:7]).copy(),
            scope='Common velocity-servo torque projection after controller-specific command generation')

        def observe(bias_torque, measured_joint_velocity, joint_velocity_command,
                    previous_torque, dt, config, torque_limits=None):
            current_config = asdict(config)
            recorded_config = self.torque_metadata['config']
            if (set(current_config) != set(recorded_config) or
                    any(not np.array_equal(current_config[k], recorded_config[k]) for k in current_config) or
                    torque_limits is None):
                raise ValueError('Unregistered torque projection configuration')
            if not np.array_equal(torque_limits, self.torque_metadata['torque_limits']):
                raise ValueError('Torque limits changed during observational audit')
            inputs = dict(time=float(env.data.time), dt=float(dt),
                bias=np.asarray(bias_torque).copy(), measured=np.asarray(measured_joint_velocity).copy(),
                command=np.asarray(joint_velocity_command).copy(), previous=np.asarray(previous_torque).copy(),
                limits=np.asarray(torque_limits).copy())
            result = original(bias_torque, measured_joint_velocity, joint_velocity_command,
                previous_torque, dt, config, torque_limits=torque_limits)
            self.torque_rows.append(dict(inputs, applied=np.asarray(result[0]).copy(), scale=float(result[1])))
            return result

        backend.safe_velocity_tracking_torque = observe

    def bind_filter(self, env):
        if self.filter_metadata is not None:
            raise ValueError('Only one environment per observational audit')
        filt = env.action_filter
        original = filt.filter
        self.filter_metadata = dict(config=asdict(filt.config),
            initial_wbc_scale=float(filt.wbc_scale),
            initial_yield_twist=filt.cartesian_yield_twist.copy(),
            observation_mode=env.observation_mode, execution_mode=env.execution_mode,
            source_file=inspect.getfile(type(filt)),
            source_sha256=sha(Path(inspect.getfile(type(filt)))))

        def observe(action, dt):
            requested = np.asarray(action, float).copy()
            result = original(action, dt)
            self.filter_rows.append(dict(requested_action=requested, dt=float(dt),
                wbc_scale=result.wbc_scale, yield_twist=result.cartesian_yield_twist.copy(),
                clipped=result.raw_action_clipped.copy(),
                amplitude_saturated=result.amplitude_saturated, slew_limited=result.slew_limited))
            return result

        filt.filter = observe

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
            if self.filter_metadata is not None:
                def encode(value):
                    if isinstance(value, np.ndarray):
                        return value.tolist()
                    raise TypeError(type(value).__name__)
                (self.folder/'audit_filter.json').write_text(json.dumps(
                    self.filter_metadata, default=encode, indent=2, allow_nan=False)+'\n')
                np.savez_compressed(self.folder/'audit_filter.npz', **{
                    key: np.asarray([row[key] for row in self.filter_rows])
                    for key in ('requested_action', 'dt', 'wbc_scale', 'yield_twist',
                                'clipped', 'amplitude_saturated', 'slew_limited')})
                receipt.update(filter_samples=len(self.filter_rows),
                    filter_metadata_sha256=sha(self.folder/'audit_filter.json'),
                    filter_trace_sha256=sha(self.folder/'audit_filter.npz'))
            if self.torque_metadata is not None:
                (self.folder/'audit_torque.json').write_text(json.dumps(
                    self.torque_metadata, default=lambda x: x.tolist(), indent=2, allow_nan=False)+'\n')
                np.savez_compressed(self.folder/'audit_torque.npz', **{
                    key: np.asarray([row[key] for row in self.torque_rows])
                    for key in ('time', 'dt', 'bias', 'measured', 'command', 'previous', 'limits', 'applied', 'scale')})
                receipt.update(torque_samples=len(self.torque_rows),
                    torque_metadata_sha256=sha(self.folder/'audit_torque.json'),
                    torque_trace_sha256=sha(self.folder/'audit_torque.npz'))
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
    bind_seam = '            self.env = env'
    if original.count(bind_seam) != 1:
        raise ValueError('Policy construction seam changed')
    patched = patched.replace(bind_seam, bind_seam+'\n            PUBLISHED_AUDIT_RECORDER.bind_filter(env)'
        +'\n            import audited_velocity_env as audit_backend'
        +'\n            PUBLISHED_AUDIT_RECORDER.bind_torque(env, audit_backend)')
    recorder = Recorder(args.output.resolve())
    module.PUBLISHED_AUDIT_RECORDER = recorder
    exec(compile(patched, str(Path(__file__).resolve()), 'exec'), module.__dict__)
    receipt = dict(wrapper_sha256=sha(Path(__file__)), base_adapter_sha256=sha(source),
        base_function_sha256=hashlib.sha256(original.encode()).hexdigest(),
        instrumented_function_sha256=hashlib.sha256(patched.encode()).hexdigest(),
        transformation='record substeps and observe original filter/torque projection calls/returns; no assignment to physical or filter state',
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
