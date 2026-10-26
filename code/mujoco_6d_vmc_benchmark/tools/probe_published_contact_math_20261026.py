"""Registered read-only microbenchmarks; no stepping or live-runtime edits.

The norm candidate is restricted to contiguous real float64 vectors of length
three. Reconstructed contacts are not historical solved contact forces. Local
timings do not establish full-trajectory equivalence or online speedup.
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


def original_norm(value):
    return float(np.linalg.norm(value))


def candidate_norm(value):
    # Caller must establish the restricted contract before entering a hot loop.
    return float(np.sqrt(value.dot(value)))


def check_norm(value):
    if value.shape != (3,) or value.dtype != np.float64 or not value.flags.c_contiguous:
        raise ValueError('Candidate requires contiguous float64 shape (3,)')
    with np.errstate(all='ignore'):
        old, new = original_norm(value), candidate_norm(value)
    if np.float64(old).tobytes() != np.float64(new).tobytes():
        raise AssertionError('Norm bit pattern differs')


def old_geometry(model, pairs):
    return [model.geom_bodyid[a] != model.geom_bodyid[b] for a, b in pairs]


def held_geometry(view, pairs):
    return [view[a] != view[b] for a, b in pairs]


def integration_state(model, data):
    spec = mujoco.mjtState.mjSTATE_INTEGRATION
    state = np.empty(mujoco.mj_stateSize(model, spec))
    mujoco.mj_getState(model, data, state, spec)
    return state.tobytes()


def measure(arms, repeats, iterations):
    names = list(arms)
    wall, cpu = {k: [] for k in names}, {k: [] for k in names}
    for repeat in range(repeats):
        for name in names[repeat % len(names):] + names[:repeat % len(names)]:
            start, cpu_start = time.perf_counter(), time.process_time()
            for _ in range(iterations):
                arms[name]()
            cpu[name].append(time.process_time() - cpu_start)
            wall[name].append(time.perf_counter() - start)
    return dict(wall_s=wall, cpu_s=cpu,
                median_wall_us={k: float(np.median(v))*1e6/iterations for k, v in wall.items()},
                median_cpu_us={k: float(np.median(v))*1e6/iterations for k, v in cpu.items()})


def main(registration):
    p = json.loads(registration.read_text())
    if sha(__file__) != p['source_sha256'] or mujoco.__version__ != p['mujoco_version']:
        raise ValueError('Registered source/environment drift')
    out = Path(p['output'])
    out.mkdir(exist_ok=False)
    os.sched_setaffinity(0, {p['cpu']})
    os.nice(10)
    started = time.time()
    (out/'EXECUTION.json').write_text(json.dumps(dict(pid=os.getpid(), started_unix=started,
        registration_sha256=sha(registration), source_sha256=sha(__file__)), indent=2)+'\n')
    rng = np.random.default_rng(p['seed'])
    synthetic = np.ascontiguousarray(rng.normal(size=(p['random_vectors'], 3)) *
                                    np.exp2(rng.uniform(-500, 500, (p['random_vectors'], 1))))
    special = np.array([[0., -0., 0.], [1e-320, -1e-320, 1e-320],
                        [1e308, -1e308, 1e308], [np.inf, 0., 0.],
                        [np.nan, 1., -1.]], dtype=np.float64)
    for value in np.concatenate([synthetic, special]):
        check_norm(value)
    models = {}
    model_rows = []
    for item in p['models']:
        if sha(item['path']) != item['sha256']:
            raise ValueError('Model drift')
        model = mujoco.MjModel.from_binary_path(item['path'])
        view = model.geom_bodyid
        if not np.shares_memory(view, model.geom_bodyid):
            raise AssertionError('Expected live model array view')
        before = view.tobytes()
        pairs = [(a, b) for a in range(model.ngeom) for b in range(model.ngeom)]
        if old_geometry(model, pairs) != held_geometry(view, pairs):
            raise AssertionError('Geometry body comparison differs')
        if before != model.geom_bodyid.tobytes():
            raise AssertionError('Model changed during reading')
        models[item['id']] = model
        model_rows.append(dict(id=item['id'], model_sha256=item['sha256'],
            ngeom=model.ngeom, exhaustive_pairs=len(pairs), exact=True, model_view_unchanged=True))
    snapshots = []
    real_vectors = 0
    forwards = 0
    for case in p['cases']:
        if sha(case['trajectory']) != case['trajectory_sha256']:
            raise ValueError('Trajectory drift')
        model = models[case['id']]
        with np.load(case['trajectory'], allow_pickle=False) as trajectory:
            for row in trajectory['observation']:
                # Recorded canonical estimated wrench force/torque components.
                for value in (row[39:42], row[42:45]):
                    check_norm(np.ascontiguousarray(value, dtype=np.float64))
                    real_vectors += 1
            for requested_time in p['snapshot_times_s']:
                index = int(np.abs(trajectory['time']-requested_time).argmin())
                data = mujoco.MjData(model)
                for name in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat'):
                    getattr(data, name)[:] = trajectory[name][index]
                data.time = float(trajectory['time'][index])
                mujoco.mj_forward(model, data)
                forwards += 1
                before = integration_state(model, data)
                contacts = data.contact
                pairs = list(zip(map(int, contacts.geom1), map(int, contacts.geom2)))
                forces = []
                for i in range(data.ncon):
                    force = np.zeros(6)
                    mujoco.mj_contactForce(model, data, i, force)
                    check_norm(force[:3])
                    forces.append(force[:3].copy())
                    real_vectors += 1
                view = model.geom_bodyid
                geometry = measure(dict(original=lambda: old_geometry(model, pairs),
                    candidate=lambda: held_geometry(view, pairs)), p['repeats'], p['iterations'])
                norms = measure(dict(original=lambda: [original_norm(v) for v in forces],
                    candidate=lambda: [candidate_norm(v) for v in forces]), p['repeats'], p['iterations'])
                if before != integration_state(model, data):
                    raise AssertionError('Probe mutated integration state')
                snapshots.append(dict(case=case['id'], time_s=float(data.time), ncon=data.ncon,
                    geometry=geometry, norms=norms, integration_state_unchanged=True))
    result = dict(started_unix=started, finished_unix=time.time(), models=model_rows,
        norm_random_vectors=len(synthetic), norm_special_vectors=len(special),
        norm_recorded_or_reconstructed_vectors=real_vectors, all_norm_results_bitwise_equal=True,
        snapshots=snapshots, mj_forward_calls=forwards, mj_step_calls=0,
        new_physical_transitions=0, optimizer_updates=0, formal_runtime_changed=False,
        registration_sha256=sha(registration), scope='Restricted microbenchmark only',
        limitations=['Reconstructed contacts need not match historical solved forces.',
            'No full-trajectory or online speedup validation; live source not modified.',
            'Float64 contiguous shape(3,) norm only; no promise for other layouts/dtypes.',
            'Repeated cached reads under shared CPU load are not an end-to-end benchmark.'])
    (out/'SUMMARY.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(out), models=len(model_rows), snapshots=len(snapshots),
        real_vectors=real_vectors, status='passed', mj_step_calls=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration', type=Path, required=True)
    main(parser.parse_args().registration)
