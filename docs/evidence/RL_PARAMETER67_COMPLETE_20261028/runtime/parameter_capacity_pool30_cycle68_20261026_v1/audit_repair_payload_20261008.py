"""Read-only pose/contact geometry reconstruction; no new physical rollout."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run=a.run
    assert not a.output.exists()
    m=mujoco.MjModel.from_binary_path(str(run/'rollout.mjb'));d=mujoco.MjData(m)
    hand=m.body('hand').id
    z=np.load(run/'rollout.npz');n=len(z['time']);relative=[];pose_discrepancy=[];geometry=[]
    for i in range(n):
        d.qpos[:]=z['qpos'][i];d.qvel[:]=z['qvel'][i]
        d.mocap_pos[:]=z['mocap_pos'][i];d.mocap_quat[:]=z['mocap_quat'][i]
        mujoco.mj_forward(m,d)
        # mj_step's derived xpos precedes its integrated qpos by a physical
        # substep. Quantify this lag; do not claim exact contact replay.
        pose_discrepancy.append(float(np.linalg.norm(d.xpos[hand]-z['hand'][i])))
        assert pose_discrepancy[-1]<1e-4, 'Kinematic mismatch exceeds 0.1mm diagnostic tolerance'
        relative.append(d.xmat[hand].reshape(3,3).T@(z['object_position'][i]-z['hand'][i]))
        pairs=[]
        for c in d.contact:
            if c.dist<=0:
                pair=[m.geom(int(g)).name for g in c.geom]
                if any(any(token in name for token in ('pillar','edge','cup','block','object')) for name in pair):
                    pairs.append(dict(geoms=pair,penetration_mm=float(-1000*c.dist)))
        geometry.append(pairs)
    relative=np.asarray(relative)
    start=int(np.searchsorted(z['time'],4.2));change=np.linalg.norm(relative-relative[start],axis=1)
    slipped=np.flatnonzero((z['time']>=4.2)&(change>.02))
    closed=np.flatnonzero((z['time']>=4.2)&(np.max(z['qpos'][:,7:9],axis=1)<.005))
    focus=sorted(set([start]+[int(np.argmin(abs(z['time']-t))) for t in np.arange(4.,17.,.5)]+
        ([int(slipped[0])] if len(slipped) else [])+([int(closed[0])] if len(closed) else [])))
    rows=[dict(time_s=float(z['time'][i]),stage=int(z['stage'][i]),hand=z['hand'][i].tolist(),
        payload=z['object_position'][i].tolist(),payload_in_hand_frame=relative[i].tolist(),
        relative_change_mm=float(change[i]*1000),finger_qpos=z['qpos'][i,7:9].tolist(),
        task_rotation_error_rad=float(z['task_rotation_error_rad'][i]),geometry_contacts=geometry[i]) for i in focus]
    report=dict(run=str(run),physics_steps=0,method='mj_forward on stored qpos/qvel/mocap; contact geometry only, not reconstructed contact forces',
        max_kinematic_timestamp_lag_mm=1000*max(pose_discrepancy),
        reference_time_s=float(z['time'][start]),first_20mm_relative_change_s=float(z['time'][slipped[0]]) if len(slipped) else None,
        first_empty_closed_gripper_s=float(z['time'][closed[0]]) if len(closed) else None,
        hashes={name:hashlib.sha256((run/name).read_bytes()).hexdigest() for name in ('rollout.npz','rollout.mjb')},rows=rows)
    a.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','hashes')}))


if __name__=='__main__':main()
