"""Aggregate completed native audits, requiring evidence for every saved episode."""
import datetime,json
from pathlib import Path
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
def main():
    metrics=[];balls=[]
    for group in ["final_evaluation01","final_reference01"]:
        for p in sorted((ROOT/group).rglob("result.json")):
            a=json.loads(p.with_name("METRIC_AUDIT.json").read_text())
            assert a["pass_numeric"]
            metrics.append(dict(episode=str(p.parent),substeps=a["substeps"],errors=a["absolute_errors"]))
            if p.with_name("ball_native_substeps.npz").exists():
                b=json.loads(p.with_name("BALL_CONTINUITY_AUDIT.json").read_text())
                bb=json.loads(p.with_name("BALL_AUDIT.json").read_text())
                assert b["pass_continuity"]
                balls.append(dict(episode=str(p.parent),velocity_jump=b["maximum_nonlaunch_velocity_jump_mps"],
                    position_residual=b["maximum_nonlaunch_translation_update_residual_m"],
                    momentum_residual=bb.get("max_native_momentum_residual_ns"),contact=bb["intended_contact"]))
    assert len(metrics)==208 and len(balls)==52
    out=dict(generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        metric_episodes=len(metrics),native_substeps=sum(x["substeps"] for x in metrics),
        ball_episodes=len(balls),maximum_nonlaunch_velocity_jump_mps=max(x["velocity_jump"] for x in balls),
        maximum_nonlaunch_translation_residual_m=max(x["position_residual"] for x in balls),
        maximum_momentum_residual_ns=max(x["momentum_residual"] for x in balls if x["momentum_residual"] is not None),
        metrics=metrics,balls=balls,
        scope="Saved native numerical consistency; no hardware safety, material realism or algorithm efficacy guarantee.")
    (ROOT/"FINAL_NATIVE_AUDIT_SUMMARY.json").write_text(json.dumps(out,indent=2,allow_nan=False))
    print(json.dumps({k:v for k,v in out.items() if k not in ["metrics","balls"]}))
if __name__=="__main__":main()
