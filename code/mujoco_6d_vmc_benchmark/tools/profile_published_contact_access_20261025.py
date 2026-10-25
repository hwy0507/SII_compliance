"""Finite contact-access microbenchmark on reconstructed archived states.

This does not step physics, change a runtime, or prove trajectory equivalence.
mj_forward rebuilds contacts from selected saved states; warmstart and other
unsaved fields need not reproduce the original solved contact forces.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original(data):
    pairs = []
    for i in range(data.ncon):
        contact = data.contact[i]
        pairs.append((int(contact.geom1), int(contact.geom2)))
    return pairs


def held_container(data):
    pairs = []
    contacts = data.contact
    for i in range(data.ncon):
        contact = contacts[i]
        pairs.append((int(contact.geom1), int(contact.geom2)))
    return pairs


def bulk_ids(data):
    pairs = []
    contacts = data.contact
    first, second = contacts.geom1, contacts.geom2
    for i in range(data.ncon):
        pairs.append((int(first[i]), int(second[i])))
    return pairs


def integration_state(model, data):
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    state = np.empty(mujoco.mj_stateSize(model, spec))
    mujoco.mj_getState(model, data, state, spec)
    return state


def main(args):
    registration = json.loads(args.registration.read_text())
    if sha(__file__) != registration['source_sha256']:
        raise ValueError('Source drift')
    if mujoco.__version__ != registration['mujoco_version']:
        raise ValueError('MuJoCo drift')
    os.sched_setaffinity(0, {registration['cpu']})
    os.nice(registration['nice'])
    out = Path(registration['output'])
    out.mkdir(exist_ok=False, parents=True)
    start = time.time()
    rows = []
    arms = dict(original=original, held_container=held_container, bulk_ids=bulk_ids)
    forwards = 0
    for case in registration['cases']:
        for key in ('model', 'trajectory'):
            if sha(case[key]) != case[key+'_sha256']:
                raise ValueError('Input drift: '+key)
        model = mujoco.MjModel.from_binary_path(case['model'])
        with np.load(case['trajectory'], allow_pickle=False) as trajectory:
            for selected_time in registration['snapshot_times_s']:
                index = int(np.abs(trajectory['time']-selected_time).argmin())
                data = mujoco.MjData(model)
                for key in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat'):
                    getattr(data, key)[:] = trajectory[key][index]
                data.time = float(trajectory['time'][index])
                mujoco.mj_forward(model, data)
                forwards += 1
                before = integration_state(model, data)
                expected = original(data)
                for name, function in arms.items():
                    if function(data) != expected:
                        raise AssertionError('Contact ID/order mismatch: '+name)
                contacts = data.contact
                for i in range(data.ncon):
                    # Check array views preserve dist/frame values and ordering
                    # used by the existing contact-force/penetration telemetry.
                    if np.float64(data.contact[i].dist).tobytes() != np.float64(contacts.dist[i]).tobytes():
                        raise AssertionError('Distance mismatch')
                    if data.contact[i].frame.tobytes() != contacts.frame[i].tobytes():
                        raise AssertionError('Frame mismatch')
                timings = {name: [] for name in arms}
                cpu_timings = {name: [] for name in arms}
                names = list(arms)
                for repeat in range(registration['repeats']):
                    order = names[repeat % len(names):]+names[:repeat % len(names)]
                    for name in order:
                        function = arms[name]
                        tick = time.perf_counter()
                        cpu_tick = time.process_time()
                        for _ in range(registration['iterations']):
                            result = function(data)
                        cpu_elapsed = time.process_time()-cpu_tick
                        elapsed = time.perf_counter()-tick
                        if result != expected:
                            raise AssertionError('Timed result mismatch')
                        timings[name].append(elapsed)
                        cpu_timings[name].append(cpu_elapsed)
                if before.tobytes() != integration_state(model, data).tobytes():
                    raise AssertionError('Contact reading mutated integration state')
                rows.append(dict(case=case['case'], time_s=float(data.time), index=index,
                    ncon=data.ncon, exact_contact_fields=True, integration_state_unchanged=True,
                    timing_s=timings, cpu_timing_s=cpu_timings,
                    median_us_per_read={name:float(np.median(t))*1e6/registration['iterations']
                        for name,t in timings.items()},
                    median_cpu_us_per_read={name:float(np.median(t))*1e6/registration['iterations']
                        for name,t in cpu_timings.items()}))
    result = dict(registration_sha256=sha(args.registration), started_unix=start,
        ended_unix=time.time(), rows=rows, mj_forward_calls=forwards, mj_step_calls=0,
        new_physical_transitions=0, optimizer_updates=0, formal_runtime_changed=False,
        limitation='Contact ID extraction only; single CPU under shared load. Reconstructed '
        'contacts need not equal historical solved contacts. Does not prove full-loop, '
        'trajectory, reward or learner equivalence, online speedup, or GPU utilization.')
    (out/'SUMMARY.json').write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args())
