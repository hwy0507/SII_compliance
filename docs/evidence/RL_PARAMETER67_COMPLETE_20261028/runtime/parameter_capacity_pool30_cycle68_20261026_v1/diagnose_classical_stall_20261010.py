"""Stored-trajectory diagnosis; no physics rollout and no actor truth inputs."""
import argparse
from collections import Counter
from pathlib import Path
import mujoco
import numpy as np
from classical_acceptance_20261010 import read, write, sha, now


def diagnose(run):
    with np.load(run/'rollout.npz') as z:
        t = z['time']; obs = z['observation']; stage = z['stage']
        actual = obs[:, 14:20] - obs[:, 26:32]
        late = t > t[-1]-10.
        m = mujoco.MjModel.from_binary_path(str(run/'rollout.mjb'))
        d = mujoco.MjData(m)
        robot = {i for i in range(m.ngeom) if m.geom(i).name.startswith(('robot_', 'left_', 'right_'))}
        # Include all arm bodies and fingers by ascending body ancestry to link0.
        hand = m.body('hand').id
        robot_bodies = set()
        for b in range(1, m.nbody):
            ancestor = b
            while ancestor:
                if m.body(ancestor).name in ('link0', 'fr3_link0'):
                    robot_bodies.add(b)
                    break
                ancestor = int(m.body_parentid[ancestor])
        robot.update(i for i in range(m.ngeom) if int(m.geom_bodyid[i]) in robot_bodies)
        target = m.geom('target_object_geom').id
        focus = np.flatnonzero(late)[::25]
        pairs = Counter(); depths = {}; poses = []
        relative = []
        for i in focus:
            d.qpos[:] = z['qpos'][i]; d.qvel[:] = z['qvel'][i]
            d.mocap_pos[:] = z['mocap_pos'][i]; d.mocap_quat[:] = z['mocap_quat'][i]
            mujoco.mj_forward(m, d)
            lag = float(np.linalg.norm(d.xpos[hand]-z['hand'][i]))
            assert lag < 1e-4
            relative.append((d.xmat[hand].reshape(3,3).T @ (z['object_position'][i]-z['hand'][i])).tolist())
            names = []
            for c in d.contact:
                a, b = map(int, c.geom)
                if c.dist > 0 or not (a in robot or b in robot or target in (a,b)):
                    continue
                key = '|'.join(sorted((m.geom(a).name or f'geom#{a}', m.geom(b).name or f'geom#{b}')))
                depths[key] = max(depths.get(key, 0.), float(-c.dist*1000))
                names.append(key)
            pairs.update(set(names))
            poses.append(dict(time_s=float(t[i]),stage=int(stage[i]),contacts=names,kinematic_lag_m=lag))
        task = read(run/'AUDIT.json')
        return dict(run=str(run), created_utc=now(), physics_steps=0,
            task=task['task_success'], strict=task['strict_success'], final_stage=task['stage'],
            window_s=[float(t[late][0]),float(t[-1])],
            median_pose_error=np.median(obs[late,20:26],axis=0).tolist(),
            median_nominal_twist=np.median(obs[late,14:20],axis=0).tolist(),
            median_measured_twist=np.median(actual[late],axis=0).tolist(),
            median_wrench=np.median(obs[late,39:45],axis=0).tolist(),
            median_action=np.median(z['applied_action'][late],axis=0).tolist(),
            final_finger_positions=z['qpos'][-1,7:9].tolist(),
            hand_final=z['hand'][-1].tolist(), payload_final=z['object_position'][-1].tolist(),
            payload_hand_frame_late=relative, late_geometry_contact_sample_counts=dict(pairs),
            late_geometry_max_penetration_mm=depths, samples=poses,
            semantics='mj_forward on stored poses; contact geometry counts at 1 Hz, NOT original substep forces or duration. Median twists from canonical proprioception.',
            hashes={p.name:sha(p) for p in [run/'rollout.npz',run/'rollout.mjb',run/'AUDIT.json',Path(__file__)]})


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    result=diagnose(a.run)
    write(a.output,result)
    print({k:v for k,v in result.items() if k not in ('hashes','samples','payload_hand_frame_late')})


if __name__=='__main__':main()
