"""Paired supplemental progress-potential diagnostic, separate from campaign_03."""
from pathlib import Path
import json,os,subprocess,time,sys
ROOT=Path("/home/arm1/vmc_mujoco_runtime/reward_study_20260930")
OUT=ROOT/"progress_dense_diagnostic_04"
SRC=ROOT/"frozen_v4_progressdiag/code/mujoco_6d_vmc_benchmark"
PY=ROOT/"venv_gpu/bin/python"
EX=SRC/"experiments/simba_reward_20260930"
def write(name,obj):
 p=OUT/name;t=p.with_suffix(".tmp");t.write_text(json.dumps(obj,indent=2)+"\n");t.replace(p)
def pool(tasks,phase):
 pending=list(tasks);running=[];done=[];slots=["5,6","15,16","17,18"]; fourth=False
 while pending or running:
  if not fourth and (ROOT/"campaign_03/COMPLETE.json").exists():slots.append("7,8");fourth=True
  for item in list(running):
   rc=item["proc"].poll()
   if rc is not None:
    done.append(dict(id=item["id"],returncode=rc,elapsed_s=time.time()-item["start"],cmd=item["cmd"]))
    item["log"].close();slots.append(item["cpu"]);running.remove(item)
  while pending and slots:
   task=pending.pop(0);cpu=slots.pop(0);log=(OUT/"logs"/(task["id"]+".log")).open("w")
   env=dict(os.environ,STUDY_CANONICAL_ROOT=str(SRC),STUDY_DENSE_PROGRESS="1")
   proc=subprocess.Popen(["taskset","-c",cpu]+task["cmd"],env=env,stdout=log,stderr=subprocess.STDOUT)
   running.append(dict(**task,proc=proc,cpu=cpu,log=log,start=time.time()))
  write("STATE.json",dict(phase=phase,updated=time.time(),running=[dict(id=r["id"],pid=r["proc"].pid,cpu=r["cpu"]) for r in running],pending=[r["id"] for r in pending],completed=done))
  if pending or running:time.sleep(10)
 write(phase.upper()+"_STATUS.json",done)
 return done
def main():
 OUT.mkdir(exist_ok=False);(OUT/"logs").mkdir()
 specs=[dict(id=f"{reward}_seed{seed}",reward=reward,seed=seed) for seed in [41001,41002] for reward in ["office_task","metric"]]
 protocol=dict(role="post-primary training-design diagnostic; not independent confirmation",
   source=str(SRC),main_campaign=str(ROOT/"campaign_03"),steps=40000,utd=2,seeds=[41001,41002],
   variable="continuous pose/speed-aware potential shared by both rewards",dense_progress=True,
   environment_actor_filter_gate_unchanged=True,lr_schedule_budget=40000,
   selection="fixed common completed step; no validation selection",physics_dt_train=.0001,physics_dt_test=.00005,
   evaluation="same six already-known development fixtures; not a new heldout test",
   max_concurrent=4,wall_limit_train_s=3300,runs=specs)
 write("PROTOCOL.json",protocol)
 train=[]
 for s in specs:
  train.append(dict(id="train_"+s["id"],cmd=[str(PY),str(EX/"train.py"),"--output",str(OUT/s["id"]),"--reward",s["reward"],"--seed",str(s["seed"]),"--steps","40000","--wall-seconds","3300","--checkpoint-every","10000"]))
 status=pool(train,"training")
 if any(s["returncode"] for s in status):raise RuntimeError("Training failed; preserve logs")
 available=[]
 for s in specs:available.append({int(p.name.split("_")[-1]) for p in (OUT/s["id"]).glob("checkpoint_step_*")})
 common=max(set.intersection(*available));write("COMMON_BUDGET.json",{"step":common})
 evals=[]
 for s in specs:
  evals.append(dict(id="test_"+s["id"],cmd=[str(PY),str(EX/"evaluate.py"),"--checkpoint",str(OUT/s["id"]/f"checkpoint_step_{common:07d}"),"--manifest",str(EX/"test_manifest.json"),"--output",str(OUT/"test"/s["id"]),"--physics-dt","0.00005"]))
 status=pool(evals,"test")
 if any(s["returncode"] for s in status):raise RuntimeError("Evaluation failed; preserve logs")
 write("COMPLETE.json",dict(status="complete",common_step=common,time=time.time()))
 write("STATE.json",dict(phase="complete",updated=time.time(),running=[],pending=[],completed=status))
if __name__=="__main__":
 try:main()
 except BaseException as e:
  if OUT.exists():write("FAILED.json",dict(error=repr(e),time=time.time()))
  raise
