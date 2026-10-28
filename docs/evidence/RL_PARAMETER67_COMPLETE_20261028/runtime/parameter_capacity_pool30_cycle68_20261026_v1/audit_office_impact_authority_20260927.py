"""Local linearized motor-authority estimate from archived contact states.

This is a diagnostic small-time estimate, not a global impossibility theorem.
It deliberately uses contact truth offline to define the audited normal;
none of these values enter a deployed actor.
"""
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=ROOT/'outputs/esn_office_recovery_20260927/r33_screen/r33_shift_minus'
    out=ROOT/'outputs/esn_office_impact_bandwidth_20260927'
    out.mkdir(exist_ok=True)
    model=mujoco.MjModel.from_binary_path(str(base/'rollout.mjb'));data=mujoco.MjData(model)
    trace=np.load(base/'rollout_ball_detail.npz');full=np.load(base/'rollout.npz')
    data.mocap_pos[:]=full['mocap_pos'][0];data.mocap_quat[:]=full['mocap_quat'][0]
    ball=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_ball_geom')
    hand=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
    jp=np.zeros((3,model.nv));jr=np.zeros_like(jp);mass=np.zeros((model.nv,model.nv))
    motor_map=np.eye(model.nv)[:,:7];rates=np.array([700,700,700,700,160,160,160])
    limits=np.array([87,87,87,87,12,12,12]);rows=[]
    contact_times=trace['time'][trace['contact']]
    first=float(contact_times.min());last=float(contact_times.max())
    for i in np.flatnonzero(trace['contact']):
        data.qpos[:]=trace['qpos'][i];mujoco.mj_forward(model,data)
        for ct in data.contact[:data.ncon]:
            gs=[int(ct.geom1),int(ct.geom2)]
            if ball not in gs:continue
            other=gs[1] if gs[0]==ball else gs[0]
            if int(model.geom_bodyid[other])!=hand:continue
            mujoco.mj_fullM(model,data,mass)
            mujoco.mj_jac(model,data,jp,jr,ct.pos,hand)
            normal=ct.frame.reshape(3,3)[0]
            coefficient=normal@jp@np.linalg.solve(mass,motor_map)
            # Local estimate assumes this effective inertia/J remain constant
            # during the sub-millisecond contact, and omits contact coupling.
            horizon=last-first+float(model.opt.timestep)
            slew_disp=float(np.abs(coefficient)@rates*horizon**3/6)
            instant_disp=float(np.abs(coefficient)@(2*limits)*horizon**2/2)
            rows.append(dict(time=float(trace['time'][i]),penetration_m=max(0.,-float(ct.dist)),
                normal_acceleration_per_joint_torque=coefficient.tolist(),
                max_local_motor_displacement_with_slew_m=slew_disp,
                ideal_instant_full_torque_reversal_displacement_m=instant_disp))
    record=dict(purpose='offline local motor-authority estimate, not a proposed controller',
        first_contact_s=first,last_contact_s=last,contact_window_s=last-first+float(model.opt.timestep),
        peak_estimated_slew_limited_displacement_m=max(r['max_local_motor_displacement_with_slew_m'] for r in rows),
        fine_step_hard_ball_excess_m=.00020737013438008847-.0002,
        assumptions=['local J and unconstrained M held constant over contact window',
                     'ignores coupled contact dynamics; estimate, not certified upper bound',
                     'instant reversal hypothetical ignores slew, reported only as contrast for actuator authority'],
        rows=rows,input_hashes={name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ('rollout.mjb','rollout_ball_detail.npz')},
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (out/'local_motor_authority.json').write_text(json.dumps(record,indent=2))
    print(json.dumps({k:v for k,v in record.items() if k!='rows'},indent=2))


if __name__=='__main__':main()
