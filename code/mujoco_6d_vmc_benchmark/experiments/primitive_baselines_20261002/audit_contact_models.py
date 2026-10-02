"""Read-only inventory of actual archived ball/contact models and anchor traces."""
import hashlib,json
from pathlib import Path
import mujoco
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
def inspect(path):
    model=mujoco.MjModel.from_binary_path(str(path));rows=[]
    for i in range(model.ngeom):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,i) or ""
        if "ball" not in name:continue
        rows.append(dict(name=name,type=int(model.geom_type[i]),size=model.geom_size[i].tolist(),
            margin=float(model.geom_margin[i]),gap=float(model.geom_gap[i]),
            solref=model.geom_solref[i].tolist(),solimp=model.geom_solimp[i].tolist(),
            priority=int(model.geom_priority[i]),contype=int(model.geom_contype[i]),
            conaffinity=int(model.geom_conaffinity[i]),friction=model.geom_friction[i].tolist(),
            rgba=model.geom_rgba[i].tolist(),body_mass=float(model.body_mass[model.geom_bodyid[i]])))
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),dt=float(model.opt.timestep),geoms=rows)
def main():
    models=dict(primitive_anchor=inspect(ROOT/"final_reference01/zero/ball_reference/model.mjb"),
        office_v5=inspect(ROOT/"office_bridge/transfer01/zero/rollout.mjb"))
    anchors=[]
    for name in ["zero","direct_metric_74001","direct_office_task_74001","fixed_impedance","parameter_impedance"]:
        path=ROOT/"final_reference01"/name/"ball_reference"
        result=json.loads((path/"result.json").read_text())
        original=json.loads((path/"original.json").read_text())
        anchors.append(dict(id=name,task=result["task_success"],strict=result["strict_success"],
            intended_contact=result["contact_exposed"],launch=original.get("ball_launch_state"),
            contacts={k:v for k,v in result["contacts"].items() if "primitive_free_ball" in k}))
    report=dict(models=models,anchors=anchors,notes=[
        "Primitive anchor: 60 mm visual radius, 51 mm rigid-core radius, 9 mm soft contact margin; solref 0.012/0.75, plus massless hard core solref 0.0006/1.",
        "Office v5: 60 mm sphere with zero margin; solref 0.0004/0.55. Different time-constant/damping settings, not the same contact law.",
        "MuJoCo solref is a solver contact response parameterization, not a calibrated measured Young modulus.",
        "Old visual sphere remains rigid in rendering while the soft margin represents shell compression. Primitive 0.2 mm negative-contact-distance gate limits rigid-core overlap; it does not cap virtual shell compression at 0.2 mm.",
        "Listed anchor contact summaries include all robot contact in the episode; inspect actual first/last times and native traces for temporal interpretation.",
        "This inventory changes no physics and does not establish contact material realism or causally isolate controller response."])
    path=ROOT/"BALL_CONTACT_MODEL_INVENTORY.json";path.write_text(json.dumps(report,indent=2,allow_nan=False))
    print(json.dumps(dict(output=str(path),models=len(models),anchor_comparisons=len(anchors))))
if __name__=="__main__":main()
