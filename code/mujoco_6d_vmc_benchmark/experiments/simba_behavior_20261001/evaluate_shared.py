"""Frozen-policy evaluation on a shared Office fixture manifest."""
from pathlib import Path
import argparse,hashlib,json,os,sys,time
import numpy as np
BASE=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(BASE/"scripts"),str(BASE/"experiments/simba_reward_20260930")]
from office_env import default_args
import validate_office_apparatus_v5_20260917 as validator

def write(path,obj):
    tmp=path.with_suffix(path.suffix+".tmp");tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n");tmp.replace(path)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(a):
    from behavior_evaluate import evaluate_file
    out=a.output;out.mkdir(parents=True,exist_ok=False)
    entries=json.loads(a.manifest.read_text())
    if not entries:raise ValueError("Empty manifest")
    policy=None;before=None;checkpoint_hash={}
    if a.method=="rl":
        from evaluate import load_frozen_agent
        agent=load_frozen_agent(a.checkpoint);before=agent.diagnostics()
        class Frozen:
            kind="mlp"
            dt=.04
            def act(self,obs):return agent.sample_action(obs,training=False)
        policy=Frozen()
        checkpoint_hash={str(p.relative_to(a.checkpoint)):sha(p) for p in a.checkpoint.rglob("*")
                         if p.is_file() and p.name not in ("replay.npz","runner_state.json")}
    elif a.method=="zero":
        class Zero:
            kind="mlp"
            dt=.04
            def act(self,obs):return np.zeros(7)
        policy=Zero()
    else:
        checkpoint_hash={str(a.checkpoint):sha(a.checkpoint)}
    write(out/"PROTOCOL.json",dict(method=a.method,checkpoint=str(a.checkpoint),
        checkpoint_sha256=checkpoint_hash,manifest_sha256=sha(a.manifest),
        cases=entries,physics_dt=a.physics_dt,duration_s=a.duration,
        actor_truth=False,normalizers_frozen=True,esn_weight=.25 if a.method=="hybrid" else None,
        classification="frozen parameters on known development geometry; not unseen-office or hardware",
        source_sha256={str(p.relative_to(BASE)):sha(p) for p in
            list((BASE/"scripts").glob("*.py"))+list(Path(__file__).parent.glob("*.py"))}))
    rows=[]
    for i,case in enumerate(entries):
        args=default_args(out/f"case_{i:03d}"/"rollout",seed=case["seed"],
              variant=case["variant"],duration=a.duration,physics_dt=a.physics_dt,
              ball_speed=case["ball_speed"],person_stroke=case["person_stroke"],
              rod_stroke=case["rod_stroke"],events=case.get("events","all"),render=a.render)
        args.behavior_log=True
        if a.method in ("esn","hybrid"):
            args.esn_model=a.checkpoint
            args.hybrid_vmc_blend=.25 if a.method=="hybrid" else 0.
        result=validator.run(args,policy_override=policy)
        behavior=evaluate_file(args.output.with_suffix(".json"),args.output.parent/(args.output.name+"_behavior.npz"))
        if a.method=="rl" and before!=agent.diagnostics():raise AssertionError("Frozen evaluation updated normalizers")
        row=dict(case=case,raw_result=str(args.output.with_suffix(".json")),behavior=behavior,
                 metrics=result["metrics"],physical_valid=result["physical_valid"],
                 legacy_task_success=result["task_success"],legacy_strict_success=result["strict_success"],
                 legacy_placement_complete=result["placement_complete"],abort_reason=result["abort_reason"],
                 full_horizon=result["full_task_horizon_completed"],model_sha256=result["model_sha256"],
                 checkpoint_sha256=checkpoint_hash)
        rows.append(row);write(out/f"case_{i:03d}"/"BEHAVIOR.json",behavior)
        write(out/"SUMMARY.json",dict(status="running",method=a.method,rows=rows))
    write(out/"SUMMARY.json",dict(status="complete",method=a.method,rows=rows,
        normalizers_before=before,normalizers_after=agent.diagnostics() if a.method=="rl" else None))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--method",choices=["rl","zero","esn","hybrid"],required=True)
    p.add_argument("--checkpoint",type=Path);p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True);p.add_argument("--physics-dt",type=float,default=.00005)
    p.add_argument("--duration",type=float,default=55.);p.add_argument("--render",action="store_true")
    a=p.parse_args()
    if a.method!="zero" and a.checkpoint is None:p.error("checkpoint required")
    run(a)
