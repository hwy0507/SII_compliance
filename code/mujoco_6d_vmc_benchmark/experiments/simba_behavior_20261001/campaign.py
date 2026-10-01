"""Eight-hour bounded paired SimbaV2 campaign; no duplicate or hot-source runs."""
from pathlib import Path
from datetime import datetime
import hashlib,json,os,shutil,signal,subprocess,sys,time
REPO=Path("/home/arm1/SII_compliance_baseline")
STUDY=Path("/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001")
OLD=Path("/home/arm1/vmc_mujoco_runtime/reward_study_20260930")
REL=Path("code/mujoco_6d_vmc_benchmark")
EX=REL/"experiments/simba_behavior_20261001"
PY=OLD/"venv_gpu/bin/python"
OUT=STUDY/"campaign_01"
DEADLINE=datetime.fromisoformat("2026-10-01T13:41:00+00:00").timestamp()
CUTOFF=DEADLINE-4200
ESN=Path("/home/arm1/vmc_mujoco_runtime/SII_compliance_eval_2e37ddc/outputs/esn_office_joint_esn_delayed2_20260928/model_medium4_v1/best.npz")
ESN_HASH="9739b6644b7bcbc2f7c8e5bee87342482f5ee00c3f543b32604f4fbe7315b5cc"
def write(name,obj):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    q=p.with_suffix(p.suffix+".tmp");q.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n");q.replace(p)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def select_temperature():
    pilot=STUDY/"exploration_pilot_02"
    status=json.loads((pilot/"COMPLETE.json").read_text())
    if not status["successful"]:raise ValueError("Incomplete/failed pilot; do not silently select")
    scores=[]
    for label,value in (("standard_temperature",.01),("low_temperature",.0001)):
        rates=[];counts=[];runs=[]
        for reward in ("office_task","metric"):
            p=pilot/(reward+"_"+label)/"episode_summaries.jsonl"
            rows=[json.loads(x) for x in p.read_text().splitlines()]
            # Exclude episodes partly collected during shared warmup.
            rows=[r for r in rows if r["step"]-r["steps_in_episode"]>=5000]
            if not rows:raise ValueError("No post-warmup complete episode for pilot")
            grasp=sum(any(int(k)>=2 for k in r["metrics"]["stages"]) for r in rows)
            rates.append(grasp/len(rows));counts.append(grasp)
            runs.append(dict(reward=reward,episodes=len(rows),grasp=grasp,source=str(p),sha256=sha(p)))
        scores.append(dict(initial_temperature=value,min_grasp_fraction=min(rates),total_grasp=sum(counts),runs=runs))
    ranked=sorted(scores,key=lambda s:(s["min_grasp_fraction"],s["total_grasp"],s["initial_temperature"]),reverse=True)
    write("TEMPERATURE_SELECTION.json",dict(rule="training-only, worst reward grasp fraction; total count; standard on tie",candidates=scores,selected=ranked[0]["initial_temperature"]))
    return ranked[0]["initial_temperature"]

def pool(tasks,phase,train=False):
    pending=list(tasks);running=[];done=[];slots=["5,6","7,8","15,16","17,18"]
    while pending or running:
        for r in list(running):
            rc=r["proc"].poll()
            if rc is not None:
                r["log"].close();slots.append(r["cpu"]);running.remove(r)
                done.append(dict(id=r["id"],returncode=rc,cmd=r["cmd"],elapsed_s=time.time()-r["start"]))
        if train and time.time()>=CUTOFF:
            for r in running:
                if not r.get("stop_sent"):
                    r["proc"].send_signal(signal.SIGUSR1);r["stop_sent"]=True
            for t in pending:done.append(dict(id=t["id"],returncode=None,skipped="training cutoff"))
            pending.clear()
        while pending and slots:
            item=pending.pop(0);cpu=slots.pop(0);log=(OUT/"logs"/(item["id"]+".log")).open("w")
            env=dict(os.environ,STUDY_CANONICAL_ROOT=str(SRC),STUDY_DENSE_PROGRESS="1")
            proc=subprocess.Popen(["taskset","-c",cpu]+item["cmd"],env=env,stdout=log,stderr=subprocess.STDOUT)
            running.append(dict(**item,proc=proc,cpu=cpu,log=log,start=time.time()))
        write("STATE.json",dict(phase=phase,updated_utc=time.time(),deadline_utc=DEADLINE,
              running=[dict(id=r["id"],pid=r["proc"].pid,cpu=r["cpu"],stop_sent=r.get("stop_sent",False)) for r in running],
              pending=[t["id"] for t in pending],completed=done))
        if pending or running:time.sleep(15)
    write(phase.upper()+"_STATUS.json",done)
    return done

def main():
    global SRC
    OUT.mkdir(exist_ok=False);(OUT/"logs").mkdir()
    inv=json.loads((STUDY/"telemetry_invariance_02"/"VALIDATION.json").read_text())
    if inv["status"]!="pass":raise ValueError("Telemetry invariance not passed")
    if any(sha(Path(p))!=v for p,v in inv["source_sha256"].items()):raise ValueError("Telemetry source changed since test")
    initial_temperature=select_temperature()
    entropy=-.5
    if sha(ESN)!=ESN_HASH:raise ValueError("ESN pin mismatch")
    if time.time()>=CUTOFF:raise ValueError("Insufficient training window")
    frozen=STUDY/"frozen_main_01"
    shutil.copytree(STUDY/"frozen_pilot_01",frozen)
    # Preserve base tar/MANIFEST; a complete current-source overlay is separately hashed.
    for directory in ("scripts","experiments/simba_reward_20260930","experiments/simba_behavior_20261001"):
        for p in (REPO/REL/directory).glob("*"):
            if p.is_file() and p.suffix in (".py",".json",".md",".sh"):
                target=frozen/REL/directory/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    SRC=frozen/REL
    source_sha={str(p.relative_to(frozen)):sha(p) for p in frozen.rglob("*.py")}
    commit=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD"],text=True).strip()
    specs=[dict(id=reward+"_seed"+str(seed),reward=reward,seed=seed) for seed in (61001,61002,61003) for reward in ("office_task","metric")]
    protocol=dict(source=str(SRC),source_sha256=source_sha,commit=commit,main_inspected="3336864",
        classification="prospectively frozen parameter draws on previously seen office geometry; finite-budget baseline",
        start_utc=time.time(),deadline_utc=DEADLINE,training_cutoff_utc=CUTOFF,
        steps_per_run=100000,seeds=[61001,61002,61003],utd=2,gamma=.9995,entropy_coef=entropy,initial_temperature=initial_temperature,warmup_std=.02,
        warmup_steps=5000,train_dt=.0001,evaluation_dt=.00005,duration_s=55,
        training_terminal="literal placement_complete AND task_success AND physical_valid; required collision exposure is separate and cannot negate correct task completion",
        behavior="offline compliant event recovery/progress with stable placement separately reported; not an obstacle-clearance certificate",
        primary_selection="largest common periodic checkpoint among all six runs; no test selection",
        evaluation_manifest_sha256=sha(SRC/"experiments/simba_behavior_20261001/final_manifest.json"),
        esn_checkpoint=str(ESN),esn_sha256=ESN_HASH,esn_retraining=False,
        comparable_scope="same new fixtures/55s/model/action interface; ESN has teacher pretraining, RL from scratch. Budgets not equated across learning paradigms.",
        old_results_unchanged=True,runs=specs)
    write("PROTOCOL.json",protocol);(frozen/"FROZEN_PROTOCOL.json").write_text(json.dumps(protocol,indent=2)+"\n")
    train=[]
    for s in specs:
        cmd=[str(PY),str(SRC/"experiments/simba_reward_20260930/train.py"),"--output",str(OUT/s["id"]),
             "--reward",s["reward"],"--seed",str(s["seed"]),"--steps","100000","--wall-seconds","11500",
             "--checkpoint-every","10000","--gamma",".9995","--warmup-std",".02","--entropy-coef",str(entropy),"--terminal-objective","task_physical","--initial-temperature",str(initial_temperature)]
        train.append(dict(id="train_"+s["id"],cmd=cmd))
    status=pool(train,"training",train=True)
    if any(s.get("returncode")!=0 for s in status):raise RuntimeError("Training incomplete; retain all evidence and report partial budget")
    sets=[{int(p.name.rsplit("_",1)[1]) for p in (OUT/s["id"]).glob("checkpoint_step_*")} for s in specs]
    common_set=set.intersection(*sets)
    if not common_set:raise RuntimeError("No shared periodic checkpoint")
    common=max(common_set);write("COMMON_BUDGET.json",dict(step=common))
    tasks=[]
    for s in specs:
        tasks.append(dict(id="eval_"+s["id"],cmd=[str(PY),str(SRC/"experiments/simba_behavior_20261001/evaluate_shared.py"),
            "--method","rl","--checkpoint",str(OUT/s["id"]/f"checkpoint_step_{common:07d}"),
            "--manifest",str(SRC/"experiments/simba_behavior_20261001/final_manifest.json"),"--output",str(OUT/"evaluation"/s["id"])]))
    for method in ("esn","hybrid","zero"):
        cmd=[str(PY),str(SRC/"experiments/simba_behavior_20261001/evaluate_shared.py"),
             "--method",method,"--manifest",str(SRC/"experiments/simba_behavior_20261001/final_manifest.json"),
             "--output",str(OUT/"evaluation"/method)]
        if method!="zero":cmd+=["--checkpoint",str(ESN)]
        tasks.append(dict(id="eval_"+method,cmd=cmd))
    status=pool(tasks,"evaluation")
    if any(s["returncode"]!=0 for s in status):raise RuntimeError("Evaluation failed; no silent exclusions")
    write("COMPLETE.json",dict(status="complete",common_step=common,completed_utc=time.time(),deadline_utc=DEADLINE))
    write("STATE.json",dict(phase="complete",updated_utc=time.time(),running=[],pending=[]))
if __name__=="__main__":
    try:main()
    except BaseException as e:
        if OUT.exists():write("FAILED.json",dict(error=repr(e),time_utc=time.time()))
        raise
