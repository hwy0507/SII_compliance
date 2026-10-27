"""Bounded static contact checks of saved frames; no dynamics integration or training."""
from pathlib import Path
import argparse, hashlib, json, os, time
import numpy as np
import mujoco

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, {54})
    root = args.root
    plan = json.loads((root/'REGISTRATION.json').read_text())
    assert sha(__file__) == plan['source_sha256']
    for path, expected in plan['input_hashes'].items():
        assert sha(path) == expected
    rows, saved = {}, {}
    total = 0
    for item in plan['episodes']:
        cycle = item['cycle']
        folder = Path(item['folder'])
        report = json.loads((folder/'rollout.json').read_text())
        model = mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'))
        data = mujoco.MjData(model)
        geom_ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, name)
                    for name in plan['pair']]
        assert min(geom_ids) >= 0 and all(model.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX for g in geom_ids)
        target_body = int(model.geom_bodyid[geom_ids[1]])
        joint = int(model.body_jntadr[target_body])
        assert model.jnt_type[joint] == mujoco.mjtJoint.mjJNT_FREE
        qadr, vadr = int(model.jnt_qposadr[joint]), int(model.jnt_dofadr[joint])
        assert model.opt.timestep == 5e-5
        with np.load(folder/'rollout.npz', allow_pickle=False) as z:
            arrays = {name: z[name].copy() for name in z.files}
        n = len(arrays['time'])
        assert n == item['saved_frames'] and n == report['baseline_policy']['actions']
        assert np.allclose(np.diff(arrays['time']), .04, atol=1e-8, rtol=0)
        pair_penetration = np.zeros(n)
        global_penetration = np.zeros(n)
        counts = np.zeros(n, dtype=np.int32)
        position_error = np.zeros(n)
        # Signed separation over OBB separating axes: positive certifies disjoint boxes.
        max_axis_separation = np.zeros(n)
        for i in range(n):
            data.qpos[:] = arrays['qpos'][i]
            data.qvel[:] = arrays['qvel'][i]
            data.ctrl[:] = arrays['ctrl'][i]
            data.mocap_pos[:] = arrays['mocap_pos'][i]
            data.mocap_quat[:] = arrays['mocap_quat'][i]
            data.time = float(arrays['time'][i])
            mujoco.mj_forward(model, data)
            total += 1
            position_error[i] = np.max(np.abs(data.xpos[target_body] - arrays['object_position'][i]))
            for c in data.contact:
                g1, g2 = int(c.geom1), int(c.geom2)
                if model.geom_bodyid[g1] != model.geom_bodyid[g2]:
                    global_penetration[i] = max(global_penetration[i], -float(c.dist))
                if {g1, g2} == set(geom_ids):
                    counts[i] += 1
                    pair_penetration[i] = max(pair_penetration[i], -float(c.dist))
            a, b = geom_ids
            ra, rb = data.geom_xmat[a].reshape(3, 3), data.geom_xmat[b].reshape(3, 3)
            axes = [*ra.T, *rb.T] + [np.cross(x, y) for x in ra.T for y in rb.T]
            delta = data.geom_xpos[b] - data.geom_xpos[a]
            gaps = []
            for axis in axes:
                norm = np.linalg.norm(axis)
                if norm < 1e-12:
                    continue
                axis = axis / norm
                gaps.append(abs(np.dot(delta, axis)) - np.dot(model.geom_size[a], np.abs(ra.T @ axis))
                            - np.dot(model.geom_size[b], np.abs(rb.T @ axis)))
            max_axis_separation[i] = max(gaps)
        # Saved xposes can lag qpos by one physical integration step; do not demand equality.
        displacement = np.linalg.norm(np.diff(arrays['object_position'], axis=0), axis=1)
        velocity = np.linalg.norm(arrays['qvel'][:, vadr:vadr+3], axis=1)
        angular = np.linalg.norm(arrays['qvel'][:, vadr+3:vadr+6], axis=1)
        packed = dict(time=arrays['time'], object_position=arrays['object_position'],
                      target_qpos=arrays['qpos'][:, qadr:qadr+7], target_qvel=arrays['qvel'][:, vadr:vadr+6],
                      stage=arrays['stage'], pair_penetration_m=pair_penetration,
                      global_penetration_m=global_penetration, pair_contact_count=counts,
                      forward_saved_position_error_m=position_error, max_axis_separation_m=max_axis_separation)
        np.savez_compressed(root/f'cycle{cycle}_saved_contacts.npz', **packed)
        j = int(np.argmax(pair_penetration))
        rows[str(cycle)] = dict(saved_frames=n, static_forward_calls=n,
            original_global_peak_m=report['stats']['max_penetration_m'],
            original_worst_pair=report['stats']['worst_pair'],
            original_corner_contact_by_stage=report['stats']['contact_diagnostics']['corner_target_by_stage'],
            original_task=report['task_success'], original_strict=report['strict_success'],
            original_abort=report['abort_reason'],
            sampled_pair_max_m=float(pair_penetration[j]), sampled_pair_max_time_s=float(arrays['time'][j]),
            sampled_pair_over2mm=int(np.sum(pair_penetration > .002)),
            sampled_global_max_m=float(global_penetration.max()),
            sampled_separated_but_penetrating=int(np.sum((max_axis_separation > 1e-8) & (pair_penetration > 1e-8))),
            max_frame_displacement_m=float(displacement.max()), max_frame_displacement_end_s=float(arrays['time'][1:][np.argmax(displacement)]),
            max_saved_linear_speed_mps=float(velocity.max()), max_saved_angular_speed_rps=float(angular.max()),
            max_forward_saved_position_error_m=float(position_error.max()),
            final_interval=dict(start_s=float(arrays['time'][-2]), end_s=float(arrays['time'][-1]),
                                displacement_m=float(displacement[-1]), linear_speed_before=float(velocity[-2]), linear_speed_after=float(velocity[-1])),
            values_sha256=sha(root/f'cycle{cycle}_saved_contacts.npz'))
        saved[str(cycle)] = packed
    for path, expected in plan['input_hashes'].items():
        assert sha(path) == expected
    assert total == plan['max_static_forward_calls']
    result = dict(passed=True, time=time.time(), methods=rows, static_forward_calls=total,
                  mujoco_version=mujoco.__version__, dynamics_integration_steps=0, optimizer_updates=0,
                  replay_writes=0, source_and_inputs_unchanged=True,
                  limitations=['Static contacts only at saved 25Hz qpos/mocap frames, not original substep contact replay.',
                               'Original MJB loaded without runtime callbacks or warmstart; contact-force estimates are not compared.',
                               'Forward xposes correspond to saved qpos; original saved xposes may precede integration.',
                               'Unsampled 50-microsecond extrema and root cause cannot be inferred from absence at 25Hz.',
                               'No environment, gate, reward or training modifications.'])
    (root/'REVIEW.json').write_text(json.dumps(result, indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
    for cycle, a in saved.items():
        axes[0,0].plot(a['time'], a['object_position'][:,2], label=cycle)
        axes[0,1].plot(a['time'], np.linalg.norm(a['target_qvel'][:,:3],axis=1), label=cycle)
        axes[1,0].plot(a['time'], a['pair_penetration_m']*1000, label=cycle)
        axes[1,1].plot(a['time'], a['max_axis_separation_m']*1000, label=cycle)
    titles=['Saved payload height (m)', 'Saved payload linear speed (m/s)',
            'Static pair penetration at saved frames (mm)', 'Maximum separating-axis gap (mm)']
    for ax, title in zip(axes.flat,titles):
        ax.set_title(title); ax.set_xlabel('Saved time (s)'); ax.grid(alpha=.3); ax.legend(title='Cycle')
    fig.suptitle('Impedance long0000: saved trajectories and static contacts; no substep replay')
    fig.savefig(root/'saved_collision_comparison.png',dpi=150);plt.close(fig)
    print(json.dumps(result,indent=2),flush=True)

if __name__ == '__main__':
    main()
