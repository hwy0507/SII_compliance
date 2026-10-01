"""Read-only audit of legacy ESN summaries; no success inferred without traces."""
import hashlib,json
from pathlib import Path
from behavior_gates import evaluate_behavior
ROOT=Path("/home/arm1/vmc_mujoco_runtime/SII_compliance_eval_2e37ddc")
OUT=ROOT/"outputs/behavior_success_audit_20261001"
NAMES=["delayed_ball_formal_reference","combined_v4_development","corner_only_formal_reference"]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name in NAMES:
        path=ROOT/"outputs/overnight_esn_combined_campaign_20260928"/name/"rollout.json"
        raw=json.loads(path.read_text())
        rows.append(dict(name=name,source=str(path),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         original_required=raw.get("contact_required"),
                         gates=evaluate_behavior(raw)))
    report=dict(classification="posthoc legacy evidence audit; not new evaluation",
                supersedes="uncommitted 20260930 stage-plus-lift draft; that predicate was invalid",
                definition="Exposure, final stage and full runtime do not establish recovery after contact.",
                rows=rows)
    (OUT/"BEHAVIOR_SUCCESS_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    lines=["# Legacy ESN temporal-evidence audit","",
           "All three behavior outcomes are unassessed: original continuous trajectories are absent from this Spark mirror.",
           "Original contact_required is retained, including the cup in combined_contact_v2.",
           "Combined carry at 9.68 s precedes pillar contact at 12.9168 s, which continues to 55 s.",
           "This cannot establish pillar clearance or post-pillar recovery. No thresholds were relaxed.","",
           "| Case | Behavior | Exposure | Physical | Old placement |",
           "|---|---|---|---|---|"]
    for row in rows:
        g=row["gates"]
        lines.append(f"| {row['name']} | unknown | {g['interaction_exposure_valid']} | {g['physical_valid']} | {g['legacy_placement_completion']} |")
    (OUT/"BEHAVIOR_SUCCESS_AUDIT.md").write_text("\n".join(lines)+"\n")
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
