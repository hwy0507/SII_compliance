"""Audit saved inputs, actions, configuration and archived model for office transfer."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
MODEL_SHA="b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1"

def audit(output):
    root=ROOT/"office_bridge/transfer01"
    names=["zero"]+[p+c for c in ["admittance","impedance","vmc"] for p in ["fixed_","parameter_"]]
    names += [f"direct_{r}_{s}" for r in ["metric","office_task"] for s in [74001,74002]]
    baseline=json.loads((root/"zero/rollout.json").read_text())
    common_args={k:v for k,v in baseline["arguments"].items() if k!="output"}
    base_execution=json.loads((root/"zero/EXECUTION.json").read_text())
    rows=[]
    for name in names:
        directory=root/name
        if not (directory/"rollout.json").exists():
            rows.append(dict(id=name,status="not_finished"));continue
        record=json.loads((directory/"rollout.json").read_text())
        execution=json.loads((directory/"EXECUTION.json").read_text())
        args={k:v for k,v in record["arguments"].items() if k!="output"}
        assert args==common_args,(name,"Different environment/task arguments")
        model_hash=hashlib.sha256((directory/"rollout.mjb").read_bytes()).hexdigest()
        assert model_hash==MODEL_SHA==record["model_sha256"]
        assert execution["status"]=="complete"
        assert execution["executed_evaluator_sha256"]==base_execution["executed_evaluator_sha256"]
        z=np.load(directory/"rollout.npz")
        t=z["neuron_time"];obs=z["observation"];actions=z["applied_action"]
        assert obs.shape==(len(t),48) and actions.shape==(len(t),7)
        assert np.isfinite(obs).all() and np.isfinite(actions).all()
        assert np.max(abs(actions))<=1.000001
        dt_error=float(abs(np.diff(t)-.04).max(initial=0.))
        assert dt_error<1e-8
        policy=record.get("baseline_policy")
        max_obs_error=max_action_error=None
        if policy:
            p=np.load(directory/"baseline_policy.npz")
            max_obs_error=float(abs(p["observation"]-obs).max(initial=0.))
            max_action_error=float(abs(p["action"]-actions).max(initial=0.))
            assert max_obs_error==max_action_error==0.
            assert policy["training"] is False and policy["steps"]==len(t)
            if execution.get("checkpoint"):
                assert policy["normalizers_unchanged"] is True and len(policy["normalization_hash"])==64
                wanted="checkpoint_0040000" if name.startswith("parameter_") else "checkpoint_0060000"
                assert Path(execution["checkpoint"]).name==wanted
        else:
            assert name=="zero" and np.max(abs(actions))==0.
        if name.startswith("fixed_"):
            p=np.load(directory/"parameter_actions.npz")
            center=np.asarray(policy["parameters"]["prior"])
            assert np.max(abs(p["raw_action"]))==0.
            assert np.max(abs(p["parameters"]-center))<1e-10
        rows.append(dict(id=name,status="verified",samples=len(t),model_sha256=model_hash,
            common_argument_count=len(args),obs_dimension=48,common_action_dimension=7,
            maximum_actor_time_error_s=dt_error,maximum_observation_logging_error=max_obs_error,
            maximum_action_logging_error=max_action_error,checkpoint=execution.get("checkpoint"),
            normalization_hash=policy.get("normalization_hash") if policy else None,
            full_horizon=record["full_task_horizon_completed"]))
    result=dict(rows=rows,verified=sum(r["status"]=="verified" for r in rows),planned=len(names),
        scope="Saved canonical48 and common action7, paired full configuration/model/evaluator, fixed priors and frozen inference. Impedance torque law differs by controller as intended; equal command dimensions do not mean equal low-level control laws.")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(verified=result["verified"],planned=result["planned"])))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,default=ROOT/"office_bridge/transfer_report01/PROTOCOL_AUDIT.json")
    audit(parser.parse_args().output)
