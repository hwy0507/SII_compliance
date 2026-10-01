"""Bounded, four-way exploration screen; outputs stay on Spark.
No behavior result is used for selection here; training coverage is diagnostic.
"""
from pathlib import Path
import argparse, hashlib, json, os, shutil, subprocess, sys, time

REPO=Path("/home/arm1/SII_compliance_baseline")
STUDY=Path("/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001")
OLD=Path("/home/arm1/vmc_mujoco_runtime/reward_study_20260930")
REL=Path("code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930")
PY=OLD/"venv_gpu/bin/python"

def write(path, obj):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n")
    tmp.replace(path)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-id",default="exploration_pilot_01")
    parser.add_argument("--temperature-screen",action="store_true")
    parser.add_argument("--terminal-objective",choices=["legacy_strict","task_physical"],default="legacy_strict")
    args=parser.parse_args()
    if "/" in args.run_id:raise ValueError("run-id must be a simple directory name")
    STUDY.mkdir(exist_ok=True)
    out=STUDY/args.run_id
    out.mkdir(exist_ok=False)
    frozen=STUDY/("frozen_"+args.run_id)
    shutil.copytree(OLD/"frozen_v3", frozen)
    for name in ("train.py","official_agent.py","evaluate.py","office_env.py","progress_potential.py","terminal_objective.py"):
        shutil.copy2(REPO/REL/name,frozen/REL/name)
    root=frozen/"code/mujoco_6d_vmc_benchmark"
    sha={str(p.relative_to(frozen)):hashlib.sha256(p.read_bytes()).hexdigest()
         for p in frozen.rglob("*.py")}
    specs=[dict(id=reward+("_standard_entropy" if ent==-.5 else "_low_entropy"),
                reward=reward,entropy_coef=ent,seed=51001)
           for reward in ("office_task","metric") for ent in (-.5,-2.)]
    if args.temperature_screen:
        specs=[dict(id=reward+("_standard_temperature" if temp==.01 else "_low_temperature"),
                    reward=reward,entropy_coef=-.5,initial_temperature=temp,seed=51001)
               for reward in ("office_task","metric") for temp in (.01,.0001)]
    write(out/"PROTOCOL.json",dict(
        classification="training-only exploration screen, not final baseline",
        main_inspected="3336864",source=str(frozen),source_sha256=sha,runs=specs,
        gamma=.9995,warmup_std=.02,warmup_steps=5000,actual_steps=10000,
        learning_rate_budget=200000,utd=2,physics_dt=.0001,duration=55,
        unchanged="network, action range, actor observations, scene, physical gate, task gate, normalizers",
        no_teacher=True,no_vmc=True,task_terminal=args.terminal_objective,
        progress="shared dense pose/speed potential; both rewards identical progress",
        selection="rank shared exploration setting by minimum across rewards of fraction episodes reaching grasp; then total grasp episodes; ties choose standard setting. Pilot uses training episodes only, never final test.",
        final_protocol_pending=True))
    running=[]
    for spec,cpu in zip(specs,("5,6","7,8","15,16","17,18")):
        cmd=[str(PY),str(frozen/REL/"train.py"),"--output",str(out/spec["id"]),
             "--reward",spec["reward"],"--seed",str(spec["seed"]),
             "--steps","200000","--stop-after-step","10000","--wall-seconds","1800",
             "--checkpoint-every","5000","--gamma",".9995","--warmup-std",".02",
             "--entropy-coef",str(spec["entropy_coef"]),"--terminal-objective",args.terminal_objective,
             "--initial-temperature",str(spec.get("initial_temperature",.01))]
        env=dict(os.environ,STUDY_CANONICAL_ROOT=str(root),STUDY_DENSE_PROGRESS="1")
        log=(out/(spec["id"]+".log")).open("w")
        proc=subprocess.Popen(["taskset","-c",cpu]+cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
        running.append(dict(spec=spec,proc=proc,log=log,cmd=cmd))
    while True:
        rows=[dict(**s["spec"],pid=s["proc"].pid,returncode=s["proc"].poll(),cmd=s["cmd"]) for s in running]
        write(out/"STATE.json",dict(updated_utc=time.time(),runs=rows,status="complete" if all(r["returncode"] is not None for r in rows) else "running"))
        if all(r["returncode"] is not None for r in rows):break
        time.sleep(15)
    for s in running:s["log"].close()
    write(out/"COMPLETE.json",dict(runs=rows,successful=all(r["returncode"]==0 for r in rows)))
    if not all(r["returncode"]==0 for r in rows):raise RuntimeError("Pilot failed; inspect preserved logs")

if __name__=="__main__":main()
