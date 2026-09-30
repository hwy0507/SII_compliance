"""Detached bounded campaign: matched training, validation selection, frozen test."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
PY=Path(sys.executable).absolute()
def write(path,data):
    tmp=Path(str(path)+".tmp");tmp.write_text(json.dumps(data,indent=2)+"\n");tmp.replace(path)
def launch(command,log,cpu):
    log.parent.mkdir(parents=True,exist_ok=True)
    stream=log.open("w")
    proc=subprocess.Popen(["taskset","-c",cpu,*map(str,command)],stdout=stream,stderr=subprocess.STDOUT)
    return dict(proc=proc,stream=stream,cmd=list(map(str,command)),log=str(log),start=time.time())
def wait_jobs(jobs,limit=4,deadline=None):
    pending=list(jobs);running=[];done=[]
    cpus=["5,6","7,8","15,16","17,18"]
    while pending or running:
        used={x["cpu"] for x in running}
        while pending and len(running)<limit:
            job=pending.pop(0);cpu=next(c for c in cpus if c not in used);used.add(cpu)
            run=launch(job["cmd"],job["log"],cpu);run.update(job=job,cpu=cpu)
            running.append(run)
        for x in list(running):
            code=x["proc"].poll()
            if code is not None:
                x["stream"].close()
                done.append(dict(id=x["job"]["id"],returncode=code,log=x["log"],
                    elapsed_s=time.time()-x["start"],cmd=x["cmd"]))
                running.remove(x)
        write(STATE,dict(phase=PHASE,updated=time.time(),
             running=[dict(id=x["job"]["id"],pid=x["proc"].pid,log=x["log"],cpu=x["cpu"]) for x in running],
             pending=[x["id"] for x in pending],completed=done))
        if pending or running:time.sleep(20)
    return done

def selection_key(summary):
    a=summary["aggregate"]
    return (-a["strict_success_count"],-a["task_success_count"],-a["physical_valid_count"],
            a["arithmetic_mean_across_episode_metrics"]["position_rmse_3d_m"],
            a["arithmetic_mean_across_episode_metrics"]["peak_torque_nm"],
            a["arithmetic_mean_across_episode_metrics"]["peak_velocity_mps"])
def main(a):
    global STATE,PHASE
    root=a.output.resolve();root.mkdir(parents=True,exist_ok=False)
    STATE=root/"CAMPAIGN_STATE.json";started=time.time();PHASE="training"
    jobs=[];runs=[]
    for seed in (41001,41002,41003):
        for mode in ("office_task","metric"):
            name=f"{mode}_seed{seed}"
            runs.append(dict(id=name,mode=mode,seed=seed,path=str(root/name),primary=True))
    for seed in (41001,41002):
        name=f"metric_nosmooth_seed{seed}"
        runs.append(dict(id=name,mode="metric",seed=seed,path=str(root/name),primary=False))
    for r in runs:
        cmd=[PY,ROOT/"train.py","--output",r["path"],"--reward",r["mode"],"--seed",r["seed"],
            "--steps",a.steps,"--wall-seconds",a.train_wall_seconds,"--checkpoint-every",10000]
        if not r["primary"]:cmd+=["--smooth",0]
        jobs.append(dict(id=r["id"],cmd=cmd,log=root/"logs"/(r["id"]+".log")))
    write(root/"CAMPAIGN_PROTOCOL.json",dict(started=started,source=str(ROOT),python=str(PY),
        primary_paired_seeds=[41001,41002,41003],steps=a.steps,utd=2,
        reward_groups=["office_task","metric"],ablation="metric without smooth, seeds41001/41002",
        concurrent_simulations=4,train_dt=.0001,validation_dt=.0001,test_dt=.00005,
        validation_manifest=str(ROOT/"validation_manifest.json"),test_manifest=str(ROOT/"test_manifest.json"),
        validation_sha256=hashlib.sha256((ROOT/"validation_manifest.json").read_bytes()).hexdigest(),
        test_sha256=hashlib.sha256((ROOT/"test_manifest.json").read_bytes()).hexdigest(),
        runs=runs,selection="strict rate,task rate,physical validity,RMSE,peak actual torque,peak speed; all ascending costs",
        claims="Office simulation development conditions, not hardware or a blind unseen benchmark",
        max_train_wall_seconds_per_run=a.train_wall_seconds))
    result=wait_jobs(jobs);write(root/"TRAIN_STATUS.json",result)
    PHASE="validation"
    jobs=[];candidates=[]
    for r in runs:
        rp=Path(r["path"])
        cps=[rp/f"checkpoint_step_{s:07d}" for s in (10000,30000,50000,60000) if s<=a.steps]
        for cp in cps:
            if not (cp/"official_agent_state.json").exists():continue
            output=root/"validation"/r["id"]/cp.name
            candidates.append(dict(run=r["id"],checkpoint=str(cp),output=str(output),primary=r["primary"]))
            jobs.append(dict(id=r["id"]+"_"+cp.name,cmd=[PY,ROOT/"evaluate.py","--checkpoint",cp,
                "--manifest",ROOT/"validation_manifest.json","--output",output,"--physics-dt",.0001],
                log=root/"logs"/("val_"+r["id"]+"_"+cp.name+".log")))
    valresult=wait_jobs(jobs);write(root/"VALIDATION_STATUS.json",valresult)
    selections=[]
    for r in runs:
        options=[]
        for c in candidates:
            if c["run"]!=r["id"]:continue
            path=Path(c["output"])/"SUMMARY.json"
            if path.exists():
                summary=json.loads(path.read_text())
                if summary.get("status")!="complete":continue
                options.append((selection_key(summary),c))
        if options:
            _,selected=min(options,key=lambda x:x[0])
            selections.append(dict(**r,selected_checkpoint=selected["checkpoint"],validation_output=selected["output"]))
    write(root/"SELECTIONS.json",selections)
    PHASE="test"
    jobs=[]
    for r in selections:
        out=root/"test"/r["id"]
        jobs.append(dict(id="test_"+r["id"],cmd=[PY,ROOT/"evaluate.py","--checkpoint",r["selected_checkpoint"],
            "--manifest",ROOT/"test_manifest.json","--output",out,"--physics-dt",.00005],
            log=root/"logs"/("test_"+r["id"]+".log")))
        final=Path(r["path"])/f"checkpoint_step_{a.steps:07d}"
        if r["primary"] and final.exists() and str(final)!=r["selected_checkpoint"]:
            jobs.append(dict(id="fixed_final_"+r["id"],cmd=[PY,ROOT/"evaluate.py","--checkpoint",final,
                "--manifest",ROOT/"test_manifest.json","--output",root/"fixed_final"/r["id"],"--physics-dt",.00005],
                log=root/"logs"/("fixed_"+r["id"]+".log")))
    jobs.append(dict(id="nominal_zero",cmd=[PY,ROOT/"evaluate.py","--zero-action","--manifest",ROOT/"test_manifest.json",
        "--output",root/"test"/"nominal_zero","--physics-dt",.00005],log=root/"logs"/"nominal_zero.log"))
    tests=wait_jobs(jobs);write(root/"TEST_STATUS.json",tests)
    PHASE="complete"
    write(root/"COMPLETE.json",dict(completed=time.time(),elapsed_s=time.time()-started,
        training=result,validation=valresult,test=tests,selections=selections,
        all_processes_passed=all(x["returncode"]==0 for x in result+valresult+tests),
        results_require_review=True))
    write(STATE,dict(phase=PHASE,updated=time.time(),running=[],pending=[]))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    p.add_argument("--steps",type=int,default=60000)
    p.add_argument("--train-wall-seconds",type=float,default=10000)
    main(p.parse_args())
