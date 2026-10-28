"""Robot-only hand-surface inertia screen, reusing nine declared IK postures.

Unlike the earlier hand-origin screen, point Jacobians include the hand's
rotational mobility. Directions are all 26 nonzero vectors of {-1,0,1}^3 in
the hand frame, chosen independently of ball state or contact truth. For each
direction, use the robot collision mesh support vertex. No simulation is run.
"""
import hashlib
import itertools
import json
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior_path = ROOT / 'outputs/esn_office_posture_screen_20260927/posture_screen.json'
    prior = json.loads(prior_path.read_text())
    base = ROOT / 'outputs/esn_office_recovery_20260927/r33_local_all'
    out = ROOT / 'outputs/esn_office_surface_inertia_20260927'
    out.mkdir(exist_ok=False)
    model = mujoco.MjModel.from_binary_path(str(base / 'rollout.mjb'))
    data = mujoco.MjData(model)
    with np.load(base / 'rollout.npz') as trace:
        initial = trace['neuron_qpos'][0].copy()
        data.mocap_pos[:] = trace['mocap_pos'][0]
        data.mocap_quat[:] = trace['mocap_quat'][0]
    hand = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'hand')
    geom = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'hand_collision')
    mesh = model.geom_dataid[geom]
    assert model.geom_type[geom] == mujoco.mjtGeom.mjGEOM_MESH
    start, count = model.mesh_vertadr[mesh], model.mesh_vertnum[mesh]
    vertices = model.mesh_vert[start:start + count].astype(np.float64)
    directions = np.array([x for x in itertools.product((-1, 0, 1), repeat=3) if any(x)], dtype=float)
    directions /= np.linalg.norm(directions, axis=1)[:, None]
    mass = np.zeros((model.nv, model.nv))
    jp = np.zeros((3, model.nv))
    jr = np.zeros_like(jp)
    rows, raw = [], []
    for candidate in prior['candidates']:
        if not candidate['valid_initial_pose']:
            continue
        data.qpos[:] = initial
        data.qpos[:7] = candidate['qpos7']
        data.qvel[:] = 0.
        mujoco.mj_forward(model, data)
        np.testing.assert_allclose(data.xpos[hand], prior['target_position'], atol=1e-6, rtol=0)
        np.testing.assert_allclose(data.xmat[hand].reshape(3, 3), prior['target_rotation'], atol=1e-6, rtol=0)
        world_vertices = vertices @ data.geom_xmat[geom].reshape(3, 3).T + data.geom_xpos[geom]
        normals = directions @ data.xmat[hand].reshape(3, 3).T
        mujoco.mj_fullM(model, data, mass)
        samples = []
        for direction, normal in zip(directions, normals, strict=True):
            point = world_vertices[np.argmax(world_vertices @ normal)]
            mujoco.mj_jac(model, data, jp, jr, point, hand)
            jac = normal @ jp
            mobility = float(jac @ np.linalg.solve(mass, jac))
            assert mobility > 0.
            samples.append(dict(hand_frame_normal=direction.tolist(), point_world_m=point.tolist(),
                                normal_mobility_per_kg=mobility, effective_mass_kg=1. / mobility))
        values = np.array([s['effective_mass_kg'] for s in samples])
        rows.append(dict(joint3_offset_rad=candidate['joint3_offset_rad'], qpos7=candidate['qpos7'],
                         worst_surface_normal_effective_mass_kg=float(values.max()),
                         median_surface_normal_effective_mass_kg=float(np.median(values)), samples=samples))
        raw.append(values)
    baseline = next(row for row in rows if row['joint3_offset_rad'] == 0.)
    selected = min(rows, key=lambda row: row['worst_surface_normal_effective_mass_kg'])
    base_samples = np.array([s['effective_mass_kg'] for s in baseline['samples']])
    chosen_samples = np.array([s['effective_mass_kg'] for s in selected['samples']])
    improvement = 1. - selected['worst_surface_normal_effective_mass_kg'] / baseline['worst_surface_normal_effective_mass_kg']
    report = dict(purpose=__doc__, selection='minimum worst support-normal effective mass over all26 predefined hand-frame directions',
                  baseline=baseline, selected=selected, candidates=rows,
                  worst_metric_relative_reduction=float(improvement),
                  directions_improved=int(np.sum(chosen_samples < base_samples - 1e-10)),
                  directions_worsened=int(np.sum(chosen_samples > base_samples + 1e-10)),
                  per_direction_selected_over_baseline=(chosen_samples / base_samples).tolist(),
                  actor_uses_external_state=False, simulations_run=0, setup_promoted=False,
                  caveats=['Surface support vertices approximate possible contacts; directions are not exhaustive.',
                           'Unconstrained local inertia, no coupled contact dynamics or actuator guarantees.',
                           'A changed ready posture would be a shared initialization change, not an ESN-only gain.',
                           'No evidence here proves a penetration or full-task improvement.'],
                  hashes={str(p.relative_to(ROOT)): digest(p) for p in
                          (prior_path, base / 'rollout.mjb', base / 'rollout.npz', Path(__file__))})
    np.savez_compressed(out / 'surface_mass_grid.npz', hand_frame_directions=directions,
                        joint3_offset_rad=[row['joint3_offset_rad'] for row in rows], effective_mass_kg=raw)
    (out / 'SURFACE_INERTIA_SCREEN.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k not in ('baseline', 'selected', 'candidates')}, indent=2))
    for row in rows:
        print(row['joint3_offset_rad'], row['worst_surface_normal_effective_mass_kg'], row['median_surface_normal_effective_mass_kg'])


if __name__ == '__main__':
    main()
