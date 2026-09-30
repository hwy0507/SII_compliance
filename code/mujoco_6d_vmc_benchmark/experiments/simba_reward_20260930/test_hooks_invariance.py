"""Physical no-op regression: hooks/queue actor must not change zero-action dynamics."""
import argparse
import json
from pathlib import Path
import numpy as np
from office_env import OfficeEnv, default_args, validator


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    env=OfficeEnv(args.output/"hooked",None,duration=6.4,physics_dt=.00005,save_substeps=True)
    try:
        env.reset(seed=2026093007,options={"variant":0,"events":"all"})
        while True:
            _,done,_=env.step_raw(np.zeros(7))
            if done: break
        hooked_path=env.args.output
    finally:
        env.close()
    original_args=default_args(args.output/"unhooked"/"rollout",2026093007,
        variant=0,duration=6.4,physics_dt=.00005,events="all")
    original_args.esn_mode="shadow"
    original=validator.run(original_args)
    hooked=json.loads(hooked_path.with_suffix(".json").read_text())
    deltas={}
    with np.load(hooked_path.with_suffix(".npz")) as left, np.load(original_args.output.with_suffix(".npz")) as right:
        for key in ("time","qpos","qvel","ctrl","hand","ball","ball_velocity",
                    "cup","stage","object_position"):
            assert left[key].shape==right[key].shape,(key,left[key].shape,right[key].shape)
            deltas[key]=float(np.max(np.abs(left[key]-right[key])))
            assert deltas[key]==0.,(key,deltas[key])
    for key in ("position_rmse_3d_m","linear_speed_peak_mps",
                "generalized_actuator_torque_peak_nm"):
        assert hooked["metrics"][key]==original["metrics"][key],key
    assert hooked["model_sha256"]==original["model_sha256"]
    result=dict(status="pass",duration_s=6.4,physics_dt_s=.00005,
        full_task_evaluation=False,events="all",trajectory_max_differences=deltas,
        model_sha256=hooked["model_sha256"],
        shared_metric_values={key:original["metrics"][key] for key in
            ("position_rmse_3d_m","linear_speed_peak_mps","generalized_actuator_torque_peak_nm")},
        hooked_result=str(hooked_path.with_suffix(".json")),
        original_result=str(original_args.output.with_suffix(".json")))
    (args.output/"VALIDATION.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result),flush=True)
if __name__=="__main__":main()
