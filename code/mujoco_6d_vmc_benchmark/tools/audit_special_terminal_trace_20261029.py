"""Reconstruct sampled terminal predicates from immutable development states.

No integration, training or formal SPT. The uninterrupted terminal suffix is
reported separately from any future, preregistered completion-hold convention.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

import mujoco
import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def terminal_suffix(time, gate):
    assert len(time) == len(gate) > 0
    if not gate[-1]:
        return None
    failed = np.flatnonzero(~gate)
    start = int(failed[-1]+1) if len(failed) else 0
    return dict(first_sample_s=float(time[start]), last_sample_s=float(time[-1]),
                samples=len(time)-start, sampled_span_s=float(time[-1]-time[start]))


def audit(folder):
    execution, legacy = read(folder/'execution.json'), read(folder/'legacy.json')
    assert execution['status'] == 'complete'
    scene = execution['scene']
    assert scene in ('rod', 'ball', 'corner')
    hashes = {n: sha(folder/n) for n in ('scene.mjb', 'trajectory.npz', 'legacy.json', 'execution.json', 'SOURCE_HASHES.json')}
    assert hashes['scene.mjb'] == execution['model_sha256']
    assert hashes['trajectory.npz'] == execution['trajectory_sha256']
    sources = read(folder/'SOURCE_HASHES.json')
    root = Path(__file__).resolve().parents[1]
    gate_sources = (['scripts/render_compliance_audited.py'] if scene == 'corner' else
        ['scripts/run_primitive_teacher_v7_20260917.py',
         'scripts/run_panel_push_20260920.py' if scene == 'rod' else 'scripts/run_primitive_coverage_20261029.py'])
    with tarfile.open(folder/'source.tar.gz') as archive:
        for name in gate_sources:
            assert sha(root/name) == sources[name], 'Terminal gate source changed since execution'
            assert hashlib.sha256(archive.extractfile(name).read()).hexdigest() == sources[name]
    with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
        states = {k: z[k].copy() for k in ('time', 'qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat')}
    time = states['time']
    assert np.isfinite(time).all() and np.allclose(np.diff(time), .04, atol=1e-8, rtol=0)
    assert all(np.isfinite(v).all() for v in states.values())
    model = mujoco.MjModel.from_binary_path(str(folder/'scene.mjb'))
    assert model.opt.timestep == .00005
    data = mujoco.MjData(model)
    cup = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'office_cup')
    target = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'target_object_geom')
    assert target >= 0
    top = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'thick_table_top')
    body = int(model.geom_bodyid[target])
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or '' for i in range(model.ngeom)]
    derived = []
    for i, t in enumerate(time):
        for key in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat'):
            getattr(data, key)[:] = states[key][i]
        data.time = float(t)
        mujoco.mj_forward(model, data)  # Derived geometry only: never mj_step.
        if scene == 'corner':
            assert top >= 0 and target >= 0
            rot = data.geom_xmat[target].reshape(3, 3)
            extent = np.abs(rot)@model.geom_size[target]
            bottom = data.geom_xpos[target, 2]-extent[2]
            surface = data.geom_xpos[top, 2]+model.geom_size[top, 2]
            margin = model.geom_size[top, :2]-np.abs(data.geom_xpos[target, :2]-data.geom_xpos[top, :2])-extent[:2]
            speed = np.linalg.norm(data.cvel[body, 3:6])
            # The original predicate uses "ever touched top"; use its saved
            # timestamp, since 25-Hz states cannot recover intervening contact.
            first = legacy['target_top_first_contact_s']
            touched = first is not None and t >= first-1e-8
            gate = (touched and np.min(margin) >= 0 and abs(bottom-surface) <= .020
                    and speed <= .08 and data.ctrl[7] >= .050
                    and np.min(margin) >= legacy['required_placement_margin_m'])
            derived.append(dict(gate=bool(gate), bottom_m=float(bottom), speed_mps=float(speed),
                                min_margin_m=float(np.min(margin)), command=float(data.ctrl[7])))
        else:
            support = False
            if cup >= 0:
                for c in data.contact[:data.ncon]:
                    pair = [names[int(c.geom1)], names[int(c.geom2)]]
                    if any('office_cup' in n for n in pair) and any('office_desk_top' in n for n in pair):
                        support = True
            derived.append(dict(cup_stable=bool(cup < 0 or (support and np.linalg.norm(data.cvel[cup, 3:6]) < .02))))
    if scene == 'corner':
        gate = np.array([r['gate'] for r in derived], dtype=bool)
        original = legacy['object_placed_on_table']
        final_comparison = {k: dict(reconstructed=derived[-1][k], recorded=legacy[v]) for k, v in
            [('bottom_m', 'final_target_bottom_z_m'), ('speed_mps', 'final_target_speed_mps'),
             ('min_margin_m', 'final_placement_min_margin_m'), ('command', 'final_gripper_command_m')]}
        predicate = 'original object_placed_on_table; scenario contact/safety qualification is separate'
    else:
        hashes['legacy.npz'] = sha(folder/'legacy.npz')
        with np.load(folder/'legacy.npz', allow_pickle=False) as z:
            np.testing.assert_array_equal(time, z['time'])
            error = np.linalg.norm(z['position']-z['target'], axis=1)
            positions, stage = z['object_position'], z['stage']
            cup_shift, cup_tilt = z['cup_shift'], z['cup_tilt']
        # Current panel branch truncates to four stages; coverage ball keeps six.
        expected_last = 3 if scene == 'rod' else 5
        assert not legacy['arguments']['settle_only']
        gate = np.zeros(len(time), dtype=bool)
        for i in range(1, len(time)):
            start = max(0, i-9)
            motion = np.max(np.linalg.norm(np.diff(positions[start:i+1], axis=0)/.04, axis=1))
            gate[i] = (positions[i, 2]-.425 > .10 and motion < .02 and error[start:i+1].mean() < .015
                       and not legacy['invalid_physics'] and not legacy['upstream_contact']
                       and stage[i] == expected_last
                       and (cup < 0 or (cup_shift[i] < .02 and cup_tilt[i] < np.deg2rad(10) and derived[i]['cup_stable'])))
        original = legacy['success']
        final_comparison = dict(final_stage=int(stage[-1]), expected_terminal_stage=expected_last)
        predicate = 'original primitive success; whole-episode invalid/upstream veto retained'
    assert bool(gate[-1]) == bool(original), 'Reconstructed final predicate differs from original'
    assert all(sha(folder/n) == h for n, h in hashes.items()), 'Input changed during audit'
    return dict(folder=str(folder.resolve()), scene=scene, hashes=hashes,
        gate_source_sha256={name: sources[name] for name in gate_sources},
        predicate=predicate, final_gate=bool(gate[-1]), original_final_gate=bool(original),
        final_predicate_parity=True, final_scalar_comparison=final_comparison,
        gate_true_samples=int(gate.sum()), uninterrupted_terminal_suffix=terminal_suffix(time, gate),
        time=time.tolist(), terminal_gate=gate.tolist())


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder', type=Path, action='append', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    rows = [audit(f) for f in a.folder]
    result = dict(schema='sii-special-sampled-terminal-trace-v1', source_sha256=sha(Path(__file__)),
        status='development_terminal_trace_not_formal_spt', rows=rows,
        limitations=['No dynamics reintegration; mj_forward reconstructs geometry on saved states only.',
            '25-Hz sampled suffix does not prove uninterrupted substep success.',
            'Primitive whole-episode invalid/upstream veto cannot time-localize historical contact.',
            'Corner terminal placement is not complete scenario qualification or office Task/Strict.',
            'No completion-hold convention or T_ref is fitted; no formal SPT is reported.'])
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print([(r['scene'], r['uninterrupted_terminal_suffix']) for r in rows])


if __name__ == '__main__':
    main()
