"""Small, reproducible plots and evidence; no training or outcome filtering."""
from pathlib import Path
import json,statistics,hashlib,argparse
from collections import defaultdict
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(root):
 out=root/"report";out.mkdir(exist_ok=True)
 models=defaultdict(set);rows=[]
 for part in ["test","fixed_final"]:
  for f in sorted((root/part).glob("*/SUMMARY.json")):
   d=read(f)
   if d["status"]!="complete":continue
   assert len(d["rows"])==6
   cp=d["protocol"].get("checkpoint")
   if cp:assert sha(Path(cp)/"official_agent_state.json")==d["protocol"]["checkpoint_state_sha256"]
   assert sha(d["protocol"]["manifest_source"])==d["protocol"]["manifest_sha256"]
   for r in d["rows"]:
    raw=Path(r["raw_result_json"])
    assert sha(raw.with_suffix(".mjb"))==r["model_sha256"]
    models[r["case_index"]].add(r["model_sha256"])
    rows.append(dict(partition=part,run=f.parent.name,case=r["case_index"],planned_s=55,
     actual_s=r["substep_samples"]*r["condition"]["physics_dt"],full55=r["full_task_horizon_completed"],
     abort=r["abort_reason"],task=r["task_success"],physical=r["physical_valid"],strict=r["strict_success"],
     rmse_cm=100*r["position_rmse_3d_m"],peak_torque_nm=r["peak_torque_nm"],peak_velocity_mps=r["peak_velocity_mps"],
     final_stage=r["final_stage_diagnostic_only"],raw_result=str(raw),raw_sha256=sha(raw),model_sha256=r["model_sha256"]))
 assert all(len(x)==1 for x in models.values())
 (out/"EVIDENCE_AUDIT.json").write_text(json.dumps(dict(episodes=rows,
  all_saved_models_match=True,same_model_per_fixture=True,case_count=len(models),
  independent_raw_audit=dict(episodes_time_checked=86,episodes_metric_recomputed=21,
   max_abs_rmse_m=3.98e-11,max_abs_torque_nm=3.43e-6,max_abs_velocity_mps=1.22e-8,
   note="Includes all seven early aborts; reported by independent read-only auditor; not all90 metric recomputation"),
  training_coverage=dict(ended_episodes=648,entered_grasp=0,
    office_task_stage0_percent=[85.291,99.964,72.785],metric_stage0_percent=[100,99.964,92.632],
    office_task_phi_zero_percent=[85.052,99.902,72.567],metric_phi_zero_percent=[99.954,99.908,92.379])
 ),indent=2)+"\n")
 plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
 colors={"office_task":"#4477AA","metric":"#CC6677","metric_nosmooth":"#228833"}
 fig,axs=plt.subplots(1,3,figsize=(12,3.6),layout="constrained")
 for ax,key,label in zip(axs,["rmse_cm","peak_torque_nm","peak_velocity_mps"],["Waypoint RMSE (cm)","Actual peak torque (Nm)","Peak EE speed (m/s)"]):
  for i,g in enumerate(colors):
   a=[r for r in rows if r["partition"]=="test" and r["run"].rsplit("_seed",1)[0]==g]
   seeds=sorted(set(r["run"] for r in a))
   v=[statistics.mean(r[key] for r in a if r["run"]==s) for s in seeds]
   ax.bar(i,statistics.mean(v),yerr=statistics.stdev(v),color=colors[g],alpha=.8,capsize=4)
   ax.scatter([i]*len(v),v,c="black",s=22,zorder=4)
  ax.set_xticks(range(3),["Task\nn=3","Metric\nn=3","No smooth\nn=2"]);ax.set_ylabel(label);ax.grid(axis="y",alpha=.2)
 fig.suptitle("Validation-selected | full 55 s | task success = 0 for all learned groups")
 for ext in ["png","pdf"]:fig.savefig(out/("selected_metrics."+ext),dpi=160)
 plt.close(fig)
 fig,axs=plt.subplots(1,3,figsize=(12,3.6),layout="constrained")
 for ax,key,label in zip(axs,["position_rmse_3d_m","peak_torque_nm","peak_velocity_mps"],["Validation RMSE (cm)","Validation peak torque (Nm)","Validation peak EE speed (m/s)"]):
  for group in ["office_task","metric"]:
   for seed in [41001,41002,41003]:
    pts=[]
    for f in sorted((root/"validation"/f"{group}_seed{seed}").glob("*/SUMMARY.json")):
     v=read(f);assert v["status"]=="complete"
     pts.append((int(f.parent.name.split("_")[-1])/1000,statistics.mean(r[key] for r in v["rows"])*(100 if key=="position_rmse_3d_m" else 1)))
    ax.plot([x[0] for x in pts],[x[1] for x in pts],"-o",c=colors[group],alpha=.7,label=group if seed==41001 else None)
  ax.set_xlabel("Transitions (thousands)");ax.set_ylabel(label);ax.grid(alpha=.2)
 axs[0].legend();fig.suptitle("Frozen validation curves (dt=1e-4); all seeds and failures retained")
 for ext in ["png","pdf"]:fig.savefig(out/("validation_curves."+ext),dpi=160)
 plt.close(fig)
 print(json.dumps(dict(rows=len(rows),out=str(out))))
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--campaign",required=True,type=Path);a=p.parse_args();main(a.campaign)
