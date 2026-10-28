"""Independently check final placement from saved states, not stage labels."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import mujoco
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from office_task_v4_20260917 import contact_support


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run',type=Path,required=True)
    p.add_argument('--prefix',default='esn_combined_v4')
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    if Path(a.prefix).name!=a.prefix or a.prefix in ('.','..'):raise ValueError('Expected simple rollout prefix')
    prefix=a.run/a.prefix
    summary=json.loads(prefix.with_suffix('.json').read_text())
    assert summary.get('path_plan') and mujoco.__version__=='3.11.0'
    model_path=prefix.with_suffix('.mjb')
    assert sha(model_path)==summary['model_sha256']
    m=mujoco.MjModel.from_binary_path(str(model_path));d=mujoco.MjData(m)
    gid=lambda name:mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,name)
    target=gid('target_object_geom');support=gid('office_v5_corner_top')
    body=int(m.geom_bodyid[target]);joint=int(m.body_jntadr[body]);dof=int(m.jnt_dofadr[joint])
    finger_joints=[mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,n) for n in ('finger_joint1','finger_joint2')]
    fingers=m.jnt_qposadr[finger_joints]
    robot={i for i in range(m.ngeom) if (mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) or '').startswith(('fr3_','left_finger','right_finger','hand_'))}
    destination=np.asarray(summary['path_plan']['destination'])
    checks=[]
    with np.load(prefix.with_suffix('.npz')) as z:
        assert len(z['time'])==1375 and abs(float(z['time'][-1])-55)<1e-6
        np.testing.assert_allclose(np.diff(z['time']), .04, rtol=0, atol=1e-8)
        for i in range(len(z['time'])-1,len(z['time'])-14,-1):
            d.qpos[:]=z['qpos'][i];d.qvel[:]=z['qvel'][i];d.ctrl[:]=z['ctrl'][i]
            d.mocap_pos[:]=z['mocap_pos'][i];d.mocap_quat[:]=z['mocap_quat'][i]
            mujoco.mj_forward(m,d)
            xy=float(np.linalg.norm(d.xpos[body,:2]-destination[:2]));height=abs(float(d.xpos[body,2]-destination[2]))
            supported=contact_support(m,d,target,support)
            robot_contact=contact_support(m,d,target,robot)
            open_fingers=float(d.qpos[fingers].sum())>.075
            speed=float(np.linalg.norm(d.qvel[dof:dof+3]));angular=float(np.linalg.norm(d.qvel[dof+3:dof+6]))
            checks.append(dict(time_s=float(z['time'][i]),xy_error_m=xy,z_error_m=height,
                               supported=supported,robot_contact=robot_contact,open_fingers=open_fingers,
                               speed_mps=speed,angular_speed_radps=angular,
                               valid=bool(xy<.025 and height<.015 and supported and not robot_contact and open_fingers and speed<.015 and angular<.15)))
        observed_lift=float(np.max(z['object_position'][:,2])-.425)
    inferred=all(c['valid'] for c in checks) and observed_lift>.1 and summary['full_task_horizon_completed']
    assert inferred==summary['task_success'], 'Independent placement disagrees with reported task success'
    report=dict(task_success=inferred,independent_final_state_checks=checks,
                sampled_check_count=len(checks),sampled_timestamp_span_s=checks[0]['time_s']-checks[-1]['time_s'],
                credited_discrete_hold_s=.04*len(checks),max_lift_from_saved_frames_m=observed_lift,
                summary_sha256=sha(prefix.with_suffix('.json')),trace_sha256=sha(prefix.with_suffix('.npz')),
                source_sha256=sha(__file__),limitations='Saved-state forward contact reconstruction at 25Hz, not a new physics rollout. The unchanged evaluator credits 0.04s per valid sample: 13 valid samples credit 0.52s but span only 0.48s between first/last timestamps. This is not continuous substep verification of placement.')
    output=a.output if a.output is not None else a.run/'PLACEMENT_AUDIT.json'
    if output.exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(run=str(a.run),task_success=inferred,final=checks[0]),indent=2))


if __name__=='__main__':main()
