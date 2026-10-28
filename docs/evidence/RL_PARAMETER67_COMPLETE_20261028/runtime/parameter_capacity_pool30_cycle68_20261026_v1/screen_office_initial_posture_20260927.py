"""Exposed office posture feasibility screen using robot-intrinsic inertia.

Fixed end-effector pose, nine predeclared redundant joint-3 targets. Candidate
ranking uses worst-direction translational inertia at the hand origin, not
ball direction, event schedule or rollout success. Any selected setup must
be shared by all controllers and retested; this is not ESN-only credit.
"""
import hashlib
import json
from pathlib import Path
import sys
import mujoco
import numpy as np
from scipy.optimize import least_squares
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from run_benchmark import so3_log


def main():
    base=ROOT/'outputs/esn_office_recovery_20260927/r33_local_all'
    out=ROOT/'outputs/esn_office_posture_screen_20260927';out.mkdir(exist_ok=False)
    model=mujoco.MjModel.from_binary_path(str(base/'rollout.mjb'));data=mujoco.MjData(model)
    with np.load(base/'rollout.npz') as z:
        initial=z['neuron_qpos'][0].copy();data.mocap_pos[:]=z['mocap_pos'][0];data.mocap_quat[:]=z['mocap_quat'][0]
    data.qpos[:]=initial;mujoco.mj_forward(model,data)
    hand=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
    target_position=data.xpos[hand].copy();target_rotation=data.xmat[hand].reshape(3,3).copy()
    mass=np.zeros((model.nv,model.nv));jp=np.zeros((3,model.nv));jr=np.zeros_like(jp)
    rows=[]
    for offset in (-1.,-.75,-.5,-.25,0.,.25,.5,.75,1.):
        redundant_target=float(initial[2]+offset)
        def residual(q):
            data.qpos[:]=initial;data.qpos[:7]=q;mujoco.mj_forward(model,data)
            return np.r_[data.xpos[hand]-target_position,.1*so3_log(target_rotation@data.xmat[hand].reshape(3,3).T),.01*(q[2]-redundant_target)]
        fit=least_squares(residual,initial[:7],bounds=(model.jnt_range[:7,0]+1e-5,model.jnt_range[:7,1]-1e-5),
                          max_nfev=1500,xtol=1e-13,ftol=1e-13,gtol=1e-13)
        error=residual(fit.x)
        mujoco.mj_fullM(model,data,mass);mujoco.mj_jacBody(model,data,jp,jr,hand)
        mobility=jp@np.linalg.solve(mass,jp.T)
        eig=np.linalg.eigvalsh(mobility)
        bad=[]
        for c in data.contact[:data.ncon]:
            if c.dist<-.00001 and model.geom_bodyid[c.geom1]!=model.geom_bodyid[c.geom2]:
                bad.append(dict(pair=[mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,int(g)) for g in (c.geom1,c.geom2)],depth_m=-float(c.dist)))
        valid=bool(np.linalg.norm(error[:3])<1e-6 and np.linalg.norm(error[3:6])<1e-7 and abs(error[6])<1e-6 and not bad)
        rows.append(dict(joint3_offset_rad=offset,qpos7=fit.x.tolist(),valid_initial_pose=valid,
            position_error_m=float(np.linalg.norm(error[:3])),rotation_error_rad=float(np.linalg.norm(error[3:6])/.1),
            worst_direction_effective_mass_kg=float(1/eig.min()),xyz_effective_mass_kg=(1/np.diag(mobility)).tolist(),
            hand_mobility=mobility.tolist(),initial_overlap=bad,solver_success=bool(fit.success)))
    valid=[r for r in rows if r['valid_initial_pose']]
    selected=min(valid,key=lambda r:r['worst_direction_effective_mass_kg']) if valid else None
    result=dict(purpose=__doc__,selection='minimum worst-direction hand-origin translational inertia among valid poses',
        target_position=target_position.tolist(),target_rotation=target_rotation.tolist(),candidates=rows,selected=selected,
        benchmark_change_requires_shared_initialization=True,physics_episodes_run=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        model_sha256=hashlib.sha256((base/'rollout.mjb').read_bytes()).hexdigest())
    (out/'posture_screen.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
