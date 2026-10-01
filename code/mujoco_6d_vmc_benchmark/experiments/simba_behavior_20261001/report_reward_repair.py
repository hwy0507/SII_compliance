"""Explicit six-policy x six-case audit for the bounded reward repair."""
import argparse,json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from audit_raw_metrics import audit
from report_campaign import sha,METRICS
def build(root):
    p=json.loads((root/"PROTOCOL.json").read_text())
    step=json.loads((root/"COMMON_BUDGET.json").read_text())["step"]
    errors=[];pending=[];rows=[];models=defaultdict(dict);checks=[]
    specs=p["evaluation_specs"]
    assert len(specs)==6
    for spec in specs:
        folder=root/"evaluation"/spec["id"]
        f=folder/"SUMMARY.json"
        if not f.exists() or json.loads(f.read_text())["status"]!="complete":
            pending.append(spec["id"]);continue
        s=json.loads(f.read_text());ep=json.loads((folder/"PROTOCOL.json").read_text())
        cp=Path(ep["checkpoint"]);expected=Path(spec["checkpoint_parent"])/("checkpoint_step_%07d"%step)
        cfg=json.loads((cp/"official_agent_state.json").read_text())["config"]
        runner=json.loads((cp/"runner_state.json").read_text())
        reward=runner["run_definition"]["reward"]
        transform="bounded" if spec["setting"]=="bounded" else "quadratic"
        c=dict(checkpoint=cp==expected,step=runner["step"]==step,seed=cfg["seed"]==spec["seed"],
               entropy=cfg["temp_target_entropy_coef"]==-2.,lr_schedule=cfg["learning_rate_decay_step"]==200000,
               reward=reward["mode"]==spec["reward"],transform=reward.get("error_transform","quadratic")==transform,
               manifest=ep["manifest_sha256"]==p["manifest_sha256"],dt=ep["physics_dt"]==.00005,
               horizon=ep["duration_s"]==55,method=ep["method"]=="rl",
               normalizer=s["normalizers_before"]==s["normalizers_after"] and s["normalizers_before"] is not None,
               cases=len(s["rows"])==len(ep["cases"])==6,
               model_weights=bool(ep["checkpoint_sha256"]) and all(
                   sha(Path(k) if Path(k).is_absolute() else cp/k)==h for k,h in ep["checkpoint_sha256"].items()))
        checks.append(dict(id=spec["id"],checks=c))
        errors.extend(spec["id"]+": "+k for k,v in c.items() if not v)
        for i,r in enumerate(s["rows"]):
            rawpath=Path(r["raw_result"]);raw=json.loads(rawpath.read_text())
            case=r["case"]
            if case!=ep["cases"][i]:errors.append(spec["id"]+": case order")
            for k in ("seed","variant","ball_speed","person_stroke","rod_stroke"):
                if raw["arguments"][k]!=case[k]:errors.append(spec["id"]+": "+k)
            if raw["arguments"]["dt"]!=.00005 or raw["arguments"]["duration"]!=55:errors.append("raw timing")
            if raw["metrics"]!=r["metrics"]:errors.append("metrics differ")
            model=sha(rawpath.with_suffix(".mjb"))
            if model!=raw["model_sha256"]:errors.append("model file hash")
            models[case["id"]][spec["id"]]=model
            b=r["behavior"]
            if not set(raw["contact_required"]).issubset(b["required_contacts"]):errors.append("removed contact requirement")
            e=dict(run=spec["id"],setting=spec["setting"],reward=spec["reward"],seed=spec["seed"],
                raw=str(rawpath),case=case,physical=raw["physical_valid"],full55=raw["full_task_horizon_completed"],
                placement=raw["placement_complete"],task=raw["task_success"],stage=raw["final_task_stage"],
                abort=raw["abort_reason"],events=b["event_results"],max_lift_m=raw["stats"].get("max_lift_m"),
                grasp_caution="stage/lift alone is not verified continuous grasp")
            e.update({k:raw["metrics"][source]*scale for k,(source,scale) in METRICS.items()});rows.append(e)
    for case,model in models.items():
        if len(set(model.values()))!=1:errors.append(case+": physical model mismatch")
    raw_audit=audit(root);raw_audit.pop("all54_present",None)
    raw_audit["expected_rows"]=36
    raw_audit["complete_expected_matrix"]=len(raw_audit["rows"])==36 and not raw_audit["skipped_incomplete"]
    if raw_audit["rows_audited"] and not raw_audit["all_observed_pass"]:errors.append("raw metric audit")
    groups=[]
    for setting,reward in (("bounded","metric"),("original","metric"),("original","office_task")):
        rr=[r for r in rows if r["setting"]==setting and r["reward"]==reward]
        seeds=sorted({r["seed"] for r in rr});metrics={}
        for k in METRICS:
            means=[float(np.mean([r[k] for r in rr if r["seed"]==seed])) for seed in seeds]
            metrics[k]=dict(mean=float(np.mean(means)) if means else None,
                sd=float(np.std(means,ddof=1)) if len(means)>1 else None,seed_means=means,seeds=seeds)
        groups.append(dict(setting=setting,reward=reward,n=len(rr),metrics=metrics,
            full55=sum(r["full55"] for r in rr),physical=sum(r["physical"] for r in rr),
            placement=sum(r["placement"] for r in rr),task=sum(r["task"] for r in rr),
            stages=dict(Counter(r["stage"] for r in rr))))
    complete=len(rows)==36 and not pending and raw_audit["complete_expected_matrix"]
    result=dict(status="complete" if complete else "partial",common_step=step,errors=errors,pending=pending,
        classification=p["classification"],groups=groups,rows=rows,checks=checks,raw_audit=raw_audit,
        model_hashes=dict(models),complete_full55=complete and not errors and all(r["full55"] for r in rows))
    out=root/"report";out.mkdir(exist_ok=True)
    (out/"SUMMARY.json").write_text(json.dumps(result,indent=2)+"\n")
    lines=["# 有界指标奖励修复：独立开发对照","",f"共同step={step}；完成{len(rows)}/36；状态{result['status']}。",
        "","两训练seed，均使用entropy=-2；原任务/原指标控制复用低熵实验同step。不是主100k结果或独立确认。",
        "新跟踪训练成本e²/(.12²+e²)，保留原始RMSE/峰矩/峰速。阶段不是抓持成功证据。","",
        "| 版本 | reward | n | 55s | physical | task | placement | RMSE cm | Nm | m/s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for g in groups:
        v=[("pending" if g["metrics"][k]["mean"] is None else str(g["metrics"][k]["mean"])+" ± "+str(g["metrics"][k]["sd"])) for k in METRICS]
        lines.append("| "+" | ".join(map(str,[g["setting"],g["reward"],g["n"],g["full55"],g["physical"],g["task"],g["placement"],*v]))+" |")
    lines+=["","任何提前结束均保留，混合时长均值仅描述，不做55s统一排名。","",
            f"审计错误={errors}；pending={pending}。",""]
    for g in groups:lines.append(f"- {g['setting']}/{g['reward']}阶段诊断：{g['stages']}")
    (out/"REPORT.md").write_text("\n".join(lines)+"\n")
    return result
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--diagnostic",type=Path,required=True)
    r=build(p.parse_args().diagnostic)
    print(json.dumps(dict(status=r["status"],rows=len(r["rows"]),errors=r["errors"])))
    raise SystemExit(2 if r["errors"] else 0)
