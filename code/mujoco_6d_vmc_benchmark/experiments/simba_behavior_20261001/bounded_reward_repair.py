"""Bounded metric reward repair; same-seed, same-step low-entropy controls."""
from datetime import datetime, timezone
import hashlib,json,os,shutil,signal,subprocess,time
from pathlib import Path
REPO=Path("/home/arm1/SII_compliance_baseline")
STUDY=Path("/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001")
OUT=STUDY/"reward_scale_repair_03"
OLD=STUDY/"entropy_diagnostic_02"
BASE=STUDY/"frozen_main_01"
FROZEN=STUDY/"frozen_reward_repair_03"
REL=Path("code/mujoco_6d_vmc_benchmark")
SRC=FROZEN/REL
PY="/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python"
CUTOFF=datetime.fromisoformat("2026-10-01T13:12:00+00:00").timestamp()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    p=Path(p);tmp=p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(v,indent=2)+"\n");tmp.replace(p)
def env():
    return dict(os.environ,STUDY_CANONICAL_ROOT=str(SRC),STUDY_DENSE_PROGRESS="1")
def pool(tasks,phase,capacity):
    pending=list(tasks);running=[];done=[];slots=["5,6","7,8","15,16","17,18"][:capacity]
    while pending or running:
        for r in list(running):
            rc=r["proc"].poll()
            if rc is not None:
                r["log"].close();slots.append(r["cpu"]);running.remove(r)
                done.append(dict(id=r["id"],returncode=rc,command=r["command"],elapsed_s=time.time()-r["start"]))
        while pending and slots:
            item=pending.pop(0);cpu=slots.pop(0);log=(OUT/"logs"/(item["id"]+".log")).open("w")
            proc=subprocess.Popen(["taskset","-c",cpu]+item["command"],env=env(),stdout=log,stderr=subprocess.STDOUT)
            running.append(dict(**item,cpu=cpu,proc=proc,log=log,start=time.time(),stop_sent=False))
        if phase=="training" and time.time()>=CUTOFF:
            for r in running:
                if not r["stop_sent"]:r["proc"].send_signal(signal.SIGUSR1);r["stop_sent"]=True
        write(OUT/"STATE.json",dict(phase=phase,updated_utc=time.time(),running=[
            dict(id=r["id"],pid=r["proc"].pid,cpu=r["cpu"],stop_sent=r["stop_sent"]) for r in running],
            pending=[r["id"] for r in pending],completed=done))
        if pending or running:time.sleep(10)
    write(OUT/(phase.upper()+"_STATUS.json"),done)
    if any(r["returncode"]!=0 for r in done):raise RuntimeError(phase+" failed; results preserved")
def main():
    OUT.mkdir(exist_ok=False);(OUT/"logs").mkdir()
    if subprocess.check_output(["git","-C",str(REPO),"status","--porcelain"],text=True).strip():
        raise RuntimeError("Commit repair source before freezing")
    commit=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD"],text=True).strip()
    shutil.copytree(BASE,FROZEN)
    updated={}
    for name in ("rewards.py","office_env.py","train.py","test_bounded_rewards.py"):
        rel=REL/"experiments/simba_reward_20260930"/name
        shutil.copy2(REPO/rel,FROZEN/rel);updated[str(rel)]=sha(FROZEN/rel)
    protocol=dict(created_utc=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),source_commit=commit,
        source=str(SRC),base_source=str(BASE),overlay_sha256=updated,driver_sha256=sha(Path(__file__)),
        classification="post-hoc reward repair development; not independent confirmation or main replacement",
        intervention="bounded per-substep training tracking error e2/(.12^2+e2), consistent bounded failure continuation; raw metrics untouched",
        unchanged="actor48/action7, task, physics, gate, WBC/filter, peak/smooth/time/terminal costs, official network and normalizers",
        gamma=.9995,entropy_coef=-2.,initial_temperature=.01,warmup_std=.02,warmup_steps=5000,utd=2,
        target_steps=30000,lr_schedule_steps=100000,train_cutoff_utc=CUTOFF,
        from_scratch=True,seeds=[61001,61002],control_source=str(OLD),
        selection="largest common periodic checkpoint <=30000; never test-selected",
        manifest_sha256=sha(SRC/"experiments/simba_behavior_20261001/final_manifest.json"),
        entropy_early_stop_reason="User prioritized actual reward repair; four entropy workers received SIGUSR1 after all had periodic40k; supervisor preserves actual rc and autoeval")
    write(OUT/"PROTOCOL.json",protocol);write(FROZEN/"REPAIR_PROTOCOL.json",protocol)
    # No simulation may start until the four-slot predecessor has finished.
    while True:
        state=json.loads((OLD/"STATE.json").read_text())
        if (OLD/"FAILED.json").exists():raise RuntimeError("Predecessor failed; inspect before reallocating")
        if state["phase"]=="complete":
            for phase in ("TRAINING","EVALUATION"):
                statuses=json.loads((OLD/(phase+"_STATUS.json")).read_text())
                if any(r["returncode"]!=0 for r in statuses):raise RuntimeError("Predecessor returncode")
            break
        write(OUT/"STATE.json",dict(phase="waiting_for_predecessor",predecessor=state["phase"],running=[],updated_utc=time.time()))
        if time.time()>CUTOFF-900:raise RuntimeError("Insufficient remaining training budget; no overlapping launch")
        time.sleep(15)
    hook=SRC/"experiments/simba_reward_20260930/test_hooks_invariance.py"
    pool([dict(id="physical_noop",command=[PY,str(hook),"--output",str(OUT/"physical_noop")])],"invariance",1)
    valid=json.loads((OUT/"physical_noop/VALIDATION.json").read_text())
    if valid["status"]!="pass":raise RuntimeError("Hook changed physics")
    tasks=[]
    for seed in (61001,61002):
        rid="bounded_metric_seed"+str(seed)
        tasks.append(dict(id="train_"+rid,command=[PY,str(SRC/"experiments/simba_reward_20260930/train.py"),
            "--output",str(OUT/rid),"--reward","metric","--error-transform","bounded",
            "--seed",str(seed),"--steps","100000","--stop-after-step","30000","--wall-seconds","3000",
            "--checkpoint-every","10000","--gamma",".9995","--warmup-std",".02",
            "--entropy-coef","-2","--initial-temperature",".01","--terminal-objective","task_physical"]))
    pool(tasks,"training",2)
    specs=[]
    for setting,reward,base,prefix in (("bounded","metric",OUT,"bounded_metric"),
            ("original","metric",OLD,"metric"),("original","office_task",OLD,"office_task")):
        for seed in (61001,61002):
            specs.append(dict(setting=setting,reward=reward,seed=seed,id=setting+"_"+reward+"_seed"+str(seed),
                checkpoint_parent=str(base/(prefix+"_seed"+str(seed)))))
    sets=[{int(p.name.rsplit("_",1)[1]) for p in Path(s["checkpoint_parent"]).glob("checkpoint_step_*")
           if int(p.name.rsplit("_",1)[1])<=30000} for s in specs]
    common=set.intersection(*sets)
    if not common:raise RuntimeError("No common checkpoint; cannot compare unequal budgets")
    step=max(common);write(OUT/"COMMON_BUDGET.json",dict(step=step))
    protocol["evaluation_specs"]=specs;write(OUT/"PROTOCOL.json",protocol)
    (OUT/"evaluation").mkdir()
    tasks=[dict(id="eval_"+s["id"],command=[PY,str(SRC/"experiments/simba_behavior_20261001/evaluate_shared.py"),
        "--method","rl","--checkpoint",str(Path(s["checkpoint_parent"])/("checkpoint_step_%07d"%step)),
        "--manifest",str(SRC/"experiments/simba_behavior_20261001/final_manifest.json"),
        "--output",str(OUT/"evaluation"/s["id"])]) for s in specs]
    pool(tasks,"evaluation",4)
    report=REPO/REL/"experiments/simba_behavior_20261001/report_reward_repair.py"
    pool([dict(id="report",command=[PY,str(report),"--diagnostic",str(OUT)])],"report",1)
    write(OUT/"STATE.json",dict(phase="complete",common_step=step,updated_utc=time.time(),running=[]))
if __name__=="__main__":
    try:main()
    except Exception as e:
        if OUT.exists():write(OUT/"FAILED.json",dict(error=repr(e),utc=time.time()))
        raise
