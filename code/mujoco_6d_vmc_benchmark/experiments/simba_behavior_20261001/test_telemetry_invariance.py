"""Integration check: logger changes neither physical state nor policy action."""
from pathlib import Path
import argparse,json,sys,hashlib
import numpy as np
BASE=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(BASE/"scripts"),str(BASE/"experiments/simba_reward_20260930")]
from office_env import default_args
import validate_office_apparatus_v5_20260917 as validator

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    paths=[BASE/"scripts"/n for n in ("validate_office_apparatus_v5_20260917.py","behavior_telemetry_20261001.py")]
    source_before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    class Zero:
        kind="mlp";dt=.04
        def act(self,obs):return np.zeros(7)
    outputs=[]
    for enabled in (False,True):
        args=default_args(a.output/str(enabled)/"rollout",seed=2026100101,variant=0,duration=10.,physics_dt=.0001)
        args.behavior_log=enabled
        raw=validator.run(args,policy_override=Zero());outputs.append((args.output,raw))
    delta={}
    with np.load(outputs[0][0].with_suffix(".npz")) as left,np.load(outputs[1][0].with_suffix(".npz")) as right:
        for k in ("time","qpos","qvel","ctrl","hand","stage","object_position","observation","applied_action"):
            delta[k]=float(np.max(np.abs(left[k]-right[k])));assert delta[k]==0.,k
    assert outputs[0][1]["model_sha256"]==outputs[1][1]["model_sha256"]
    for k in ("position_rmse_3d_m","linear_speed_peak_mps","generalized_actuator_torque_peak_nm"):
        assert outputs[0][1]["metrics"][k]==outputs[1][1]["metrics"][k]
    from behavior_evaluate import evaluate_file
    behavior=evaluate_file(outputs[1][0].with_suffix(".json"),outputs[1][0].parent/"rollout_behavior.npz")
    assert source_before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},"Source changed during test"
    report=dict(source_sha256=source_before,status="pass",duration_s=10,physics_dt=.0001,classification="logger no-op smoke, not task performance",
                deltas=delta,telemetry=outputs[1][1]["behavior_telemetry"],behavior=behavior)
    (a.output/"VALIDATION.json").write_text(json.dumps(report,indent=2)+"\n")
    print("LOGGER INVARIANCE PASS",flush=True)
if __name__=="__main__":main()
