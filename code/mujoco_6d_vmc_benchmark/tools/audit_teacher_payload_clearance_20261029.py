"""Saved-state geometry and teacher replay: clearance versus recovery.

No new dynamics, oracle in the actor, fitting, or parameter selection.
Box projections give sufficient vertical clearance, not a collision solver.
"""
import argparse
import fcntl
import itertools
from pathlib import Path

import mujoco
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from optimize_tool_contact_20261002 import ParameterTeacher


def audit(output, candidate=None):
    assert not output.exists()
    lock = (ROOT/'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    paths = [
        ('original_v6', 'special_teacher_tail_repair_20261028_v2/office_v1_avg1'),
        ('normalized', 'special_teacher_legacy_units_20261029_v1/legacy_units_office000'),
        ('damped', 'special_teacher_damping_20261029_v1/damping_office000'),
    ]
    if candidate is not None:
        # The completed original three remain in the comparison; an optional
        # fourth folder never replaces them or rewrites their saved evidence.
        candidate = candidate.resolve()
        assert candidate not in [(ROOT/'outputs'/p).resolve() for _,p in paths]
        paths.append(('candidate', str(candidate)))
    rows, vectors = [], {}
    model_hash = None
    for label, relative in paths:
        folder = ROOT/'outputs'/relative
        receipt = read(folder/'AUDIT.json')
        assert receipt['full_horizon'] and receipt['action_replay_max_abs'] == 0
        for filename, key in (('rollout.npz', 'trace_sha256'), ('rollout.mjb', 'model_sha256'),
                              ('execution_chain.npz', 'chain_sha256')):
            assert sha(folder/filename) == receipt[key]
        if model_hash is not None: assert model_hash == receipt['model_sha256']
        model_hash = receipt['model_sha256']
        model = mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'))
        data = mujoco.MjData(model)
        edge = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'office_v5_unexpected_edge')
        payload = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, 'target_object_geom')
        assert min(edge, payload) >= 0
        assert all(model.geom_type[i] == mujoco.mjtGeom.mjGEOM_BOX for i in (edge, payload))
        actor = ParameterTeacher(read(folder/'config.json'))
        signs = np.array(list(itertools.product((-1., 1.), repeat=3)))
        samples = []
        with np.load(folder/'rollout.npz', allow_pickle=False) as trace, np.load(folder/'execution_chain.npz', allow_pickle=False) as chain:
            for i, obs in enumerate(trace['observation']):
                actor.observe(obs)
                action = actor.act(obs[39:45])
                np.testing.assert_array_equal(action, chain['requested_action'][i])
                for key in ('qpos', 'qvel', 'ctrl', 'mocap_pos', 'mocap_quat'):
                    getattr(data, key)[:] = trace[key][i]
                data.time = float(trace['time'][i]); mujoco.mj_forward(model, data)
                vertices = (signs*model.geom_size[payload])@data.geom_xmat[payload].reshape(3,3).T+data.geom_xpos[payload]
                local = (vertices-data.geom_xpos[edge])@data.geom_xmat[edge].reshape(3,3)
                low, high = local.min(0), local.max(0)
                overlap_xy = bool(np.all(high[:2] >= -model.geom_size[edge,:2]) and np.all(low[:2] <= model.geom_size[edge,:2]))
                # The edge is upright: vertical interval clearance is meaningful.
                np.testing.assert_allclose(data.geom_xmat[edge].reshape(3,3)[:,2], [0,0,1], atol=1e-12, rtol=0)
                clearance = float(low[2]-model.geom_size[edge,2])
                pair = any({int(data.contact[j].geom1),int(data.contact[j].geom2)} == {edge,payload} for j in range(data.ncon))
                horizontal = min(1.,float(np.linalg.norm(obs[45:47])))
                direction = obs[45:47]/max(float(np.linalg.norm(obs[45:47])),1e-12)
                actual = obs[14:17]-obs[26:29]
                samples.append([data.time, trace['stage'][i], clearance, float(overlap_xy), float(pair),
                    actor.recovery_memory*horizontal**2, obs[22], obs[16], chain['yield_twist'][i,2],
                    float(obs[14:16]@direction), float(actual[:2]@direction), float(-obs[39:41]@direction)])
        values = np.asarray(samples)
        vectors[label] = values
        masks = {'carry': values[:,1]==4, 'last250':np.arange(len(values))>=len(values)-250,
                 'payload_edge_contact':values[:,4]>0}
        summaries = {}
        for name, mask in masks.items():
            subset = values[mask]
            summaries[name] = dict(frames=len(subset), mean=subset.mean(0).tolist() if len(subset) else None,
                minimum=subset.min(0).tolist() if len(subset) else None,
                maximum=subset.max(0).tolist() if len(subset) else None)
        row = dict(setting=label, folder=str(folder), task=receipt['task_success'], strict=receipt['strict_success'],
            actor_replay_max_abs=0., summaries=summaries,
            inputs={name:sha(folder/name) for name in ('AUDIT.json','rollout.npz','rollout.mjb','execution_chain.npz','config.json')})
        rows.append(row)
    output.mkdir(parents=True)
    np.savez_compressed(output/'geometry_and_control.npz', **vectors)
    write(output/'REVIEW.json', dict(status='complete', physics_steps=0, rows=rows,
        columns=['time_s','stage','bottom_clearance_m','xy_projection_overlap','reconstructed_payload_edge_contact',
                 'recovery_activation','reference_minus_hand_z_m','command_z_mps','filtered_yield_z_mps',
                 'command_path_mps','actual_path_mps','estimated_opposing_force_n'],
        model_sha256=model_hash, array_sha256=sha(output/'geometry_and_control.npz'), source_sha256=sha(Path(__file__)),
        limitation='Saved end-of-step geometry versus pre-step observed control. No force replay or causal counterfactual. Negative bottom clearance and XY interval overlap alone do not imply collision; contact-pair flag is independently reconstructed. Office is inspected regression, no imitation labels.'))
    print([(r['setting'],r['task'],r['summaries']['last250']) for r in rows])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, help='Additional completed office folder; retains the three original controls')
    args = parser.parse_args()
    audit(args.output.resolve(), args.candidate)
