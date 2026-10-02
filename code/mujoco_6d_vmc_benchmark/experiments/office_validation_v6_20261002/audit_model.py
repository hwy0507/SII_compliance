"""Check registered geometry and unchanged physical parameters against v5."""
import json,hashlib
from pathlib import Path
import mujoco,numpy as np
ROOT=Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
OLD=Path('/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/tool_contact_20261002/v5_esn_full/esn_combined_v4.mjb')
def main():
    new=ROOT/'construction/rollout.mjb';a=mujoco.MjModel.from_binary_path(str(OLD));b=mujoco.MjModel.from_binary_path(str(new));config=json.loads((ROOT/'PROTOCOL.json').read_text())
    edge=mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_unexpected_edge');ball=mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_BODY,'office_v5_ball');rod=mujoco.mj_name2id(b,mujoco.mjtObj.mjOBJ_BODY,'office_v5_push_rod')
    checks={}
    for name,v,target in [('edge_pos',b.geom_pos[edge],config['edge_position_m']),('edge_size',b.geom_size[edge],config['edge_half_size_m']),('ball_pos',b.body_pos[ball],config['ball_center_m']),('rod_pos',b.body_pos[rod],config['rod_center_m'])]:
        assert np.allclose(v,target,atol=1e-12,rtol=0);checks[name]=v.tolist()
    unchanged=['actuator_ctrlrange','actuator_forcerange','actuator_gear','actuator_gainprm','actuator_biasprm','dof_damping','dof_frictionloss','dof_armature','geom_solref','geom_solimp','geom_friction','body_mass','body_inertia']
    for name in unchanged:assert np.allclose(getattr(a,name),getattr(b,name),atol=1e-12,rtol=1e-12),name
    changed={}
    for name in ['geom_pos','geom_size','body_pos']:
        x,y=getattr(a,name),getattr(b,name);changed[name]=np.flatnonzero(np.any(abs(x-y)>1e-12,axis=1)).tolist()
    result=dict(status='passed',checks=checks,unchanged_physical_arrays=unchanged,changed_geometry_indices=changed,model_sha256=hashlib.sha256(new.read_bytes()).hexdigest(),construction_summary_sha256=hashlib.sha256((ROOT/'construction/rollout.json').read_bytes()).hexdigest(),note='New model compiled once on Spark; this does not claim old/new binary identity')
    (ROOT/'MODEL_AUDIT.json').write_text(json.dumps(result,indent=2))
if __name__=='__main__':main()
