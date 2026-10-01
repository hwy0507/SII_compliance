"""Read-only audit of reward scale and action coverage in the frozen main batch."""
import argparse, hashlib, json, math, statistics
from pathlib import Path
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def stats(v):
    return dict(n=len(v), minimum=min(v), median=statistics.median(v), maximum=max(v)) if v else dict(n=0)
def audit(root):
    rows=[]
    for mode in ("office_task","metric"):
        for seed in (61001,61002,61003):
            run=root/f"{mode}_seed{seed}"
            path=run/"episode_summaries.jsonl"
            episodes=[json.loads(x) for x in path.read_text().splitlines()]
            post=[r for r in episodes if r["step"]-r["steps_in_episode"]>=5000]
            full=[r for r in post if not r["abort_reason"]]
            early=[r for r in post if r["abort_reason"]]
            prog=json.loads((run/"progress.json").read_text())
            bins={k:dict(n=0,action_ss=0.,linear_ss=0.,slowdown_sum=0.,stage_counts={})
                  for k in ("warmup","learning")}
            # Scan original traces; include only warmup and last 5000 steps.
            with (run/"control_audit.jsonl").open() as f:
                for line in f:
                    r=json.loads(line); step=r["step"]
                    if 5000<=step<95000: continue
                    b=bins["warmup" if step<5000 else "learning"]
                    a=r["requested_action"]; iv=r["interval"]; actual=iv["filtered_action_physical"]
                    b["n"]+=1;b["action_ss"]+=sum(x*x for x in a)
                    b["linear_ss"]+=sum(x*x for x in actual[1:4]);b["slowdown_sum"]+=actual[0]
                    key=str(iv["stage"]);b["stage_counts"][key]=b["stage_counts"].get(key,0)+1
            for b in bins.values():
                n=b["n"]
                b["requested_action_rms_per_component"]=math.sqrt(b.pop("action_ss")/(7*n))
                b["filtered_linear_residual_rms_mps"]=math.sqrt(b.pop("linear_ss")/n)
                b["mean_wbc_scale"]=b.pop("slowdown_sum")/n
            stages={}
            for r in post: stages[r["final_stage"]]=stages.get(r["final_stage"],0)+1
            rows.append(dict(mode=mode,seed=seed,source_summary_sha256=sha(path),
                postwarmup_ended=len(post),full=len(full),early=len(early),final_stages=stages,
                full_terms={k:stats([r["reward_terms"][k] for r in full]) for k in
                    ("task","progress","error","peak_torque","time","smooth")},
                failure_continuation=stats([r["reward_terms"]["failure_continuation"] for r in early]),
                normalizers=prog["normalizers"],action_windows=bins))
    return dict(classification="post-hoc implementation diagnostic; no causal correction experiment",
                campaign=str(root),rows=rows,
                limitations=["Action stage counts are not actual object-grasp evidence.",
                    "Reward denominator is observed; it does not prove a unique cause of learning failure.",
                    "Raw evaluation RMSE/torque/speed and the frozen training data are not modified."])
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--campaign",type=Path,required=True)
    a=p.parse_args();result=audit(a.campaign)
    out=a.campaign/"report"/"REWARD_SCALE_AUDIT.json"
    out.write_text(json.dumps(result,indent=2)+"\n")
    for r in result["rows"]:
        print(json.dumps(r))
