"""Aggregate the pinned office transfer without selecting policies from its scores."""
import argparse,csv,hashlib,json
from pathlib import Path
MODEL_SHA="b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1"
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
SOURCE=Path("/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/tool_contact_20261002/v5_esn_full")
def build(output):
    names=["zero"]+[p+c for c in ["admittance","impedance","vmc"] for p in ["fixed_","parameter_"]]+[f"direct_{r}_{s}" for r in ["metric","office_task"] for s in [74001,74002]]
    rows=[];missing=[]
    for identity in names+["source_esn_reference"]:
        path=SOURCE if identity=="source_esn_reference" else ROOT/"office_bridge/transfer01"/identity
        prefix="esn_combined_v4" if identity=="source_esn_reference" else "rollout"
        summary_path=path/(prefix+".json")
        if not summary_path.exists():
            missing.append(dict(id=identity,path=str(path),status="started_without_final_summary" if path.exists() else "not_started"));continue
        s=json.loads(summary_path.read_text());m=s["metrics"];actual=hashlib.sha256((path/(prefix+".mjb")).read_bytes()).hexdigest()
        if actual!=MODEL_SHA or s["model_sha256"]!=MODEL_SHA:raise ValueError("Mismatched office model: "+identity)
        execution_path=path/"EXECUTION.json"
        execution=json.loads(execution_path.read_text()) if execution_path.exists() else {}
        row=dict(id=identity,source=str(path),method_role="historical_reference_different_training_exposure" if identity=="source_esn_reference" else "primitive_to_office_transfer",
            task=bool(s["task_success"]),strict=bool(s["strict_success"]),physical_valid=bool(s["physical_valid"]),full_horizon=bool(s["full_task_horizon_completed"]),
            duration_s=float(s["metrics"]["samples"])*float(s["arguments"]["dt"]),stage=s["final_task_stage"],rmse_mm=m["position_rmse_3d_m"]*1000,
            peak_torque_nm=m["generalized_actuator_torque_peak_nm"],peak_speed_mps=m["linear_speed_peak_mps"],external_penetration_mm=s["stats"]["max_external_penetration_m"]*1000,
            max_lift_m=s.get("max_payload_lift_m"),abort_reason=s.get("abort_reason"),model_sha256=actual,success_definition=s["success_definition"],
            events=s["stats"]["events"],edge_stats=s["stats"].get("unexpected_edge"),task_events=s["task_events"],
            execution_status=execution.get("status","source_archive"),policy=s.get("baseline_policy"))
        rows.append(row)
    output.mkdir(parents=True,exist_ok=True)
    result=dict(main="7cd5f4b7ac0a3056df76ac62bc690ded0724b104",model_sha256=MODEL_SHA,rows=rows,missing=missing,
        limitations=["One fixed composite development condition at dt=1e-4; no estimate of generalization or formal dt=5e-5 result.",
        "Source ESN is a historical reference with different training exposure; this is not an equal-data learning comparison.",
        "All-event zero is not the no-disturbance feasibility control.",
        "Contact exposure is diagnostic and does not change the inherited office task/strict gate.",
        "Fixed parameters are transferred unified BO-derived priors, not an office-specific BO optimum.",
        "Compare full-horizon metric rows; low error while stalled does not establish task success."])
    (output/"SUMMARY.json").write_text(json.dumps(result,indent=2,allow_nan=False))
    columns=["id","method_role","task","strict","physical_valid","full_horizon","duration_s","stage","rmse_mm","peak_torque_nm","peak_speed_mps","external_penetration_mm"]
    with (output/"EPISODES.csv").open("w") as f:
        writer=csv.DictWriter(f,fieldnames=columns);writer.writeheader();writer.writerows([{k:r[k] for k in columns} for r in rows])
    lines=["# Pinned office transfer", "", "| Method | Task | Strict | Full 55 s | Final stage | RMSE mm | Torque Nm | Speed m/s | External penetration mm |","|---|---|---|---|---|---:|---:|---:|---:|"]
    for r in rows:
        lines.append("| "+r["id"]+" | "+" | ".join(str(r[k]) for k in ["task","strict","full_horizon","stage"])+" | "+" | ".join(f"{r[k]:.3f}" for k in ["rmse_mm","peak_torque_nm","peak_speed_mps","external_penetration_mm"])+" |")
    lines+=["", "Unfinished models: "+(", ".join(r["id"] for r in missing) or "none")+".", "", *["- "+x for x in result["limitations"]]]
    (output/"SUMMARY.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(dict(completed=len(rows),missing=len(missing),output=str(output))))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args();build(a.output)
