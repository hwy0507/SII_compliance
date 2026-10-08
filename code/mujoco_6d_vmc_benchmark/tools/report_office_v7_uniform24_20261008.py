"""Audit and report only the locked new office-v7 16 x 24 cohort."""
import argparse
import json
import math
from pathlib import Path
import statistics
import hashlib
from collections import Counter
import subprocess
import time
LABELS = {"esn":"ESN", "matched_rnn":"Matched RNN", "matched_mlp":"Matched MLP",
          "ordinary_rnn":"Ordinary RNN", "ordinary_mlp":"Ordinary MLP",
          "memoryless":"Memoryless", "classical_vmc":"Classical VMC",
          "classical_admittance":"Classical admittance", "classical_impedance":"Classical impedance",
          "parameter_vmc":"RL parameter VMC", "parameter_admittance":"RL parameter admittance",
          "parameter_impedance":"RL parameter impedance", "direct_metric":"RL direct metric",
          "direct_office_task":"RL direct task", "enhanced_teacher":"Enhanced teacher", "nominal_zero":"Nominal zero"}

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wilson(success,n):
    if not n:return None
    z=1.959963984540054
    ph=success/n;denom=1+z*z/n
    mid=(ph+z*z/(2*n))/denom
    width=z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/denom
    return [0.0 if success == 0 else max(0.0, mid-width),
            1.0 if success == n else min(1.0, mid+width)]

def build(root):
    protocol=read(root/"PROTOCOL.json")
    conditions=read(root/"CONDITIONS.json")["conditions"]
    assert len(conditions)==24
    ids={d["id"] for d in conditions}
    assert len(ids)==24
    assert sha(root/"CONDITIONS.json")==protocol["condition_file_sha256"]
    candidates=read(root/"MODEL_MANIFEST.json")["candidates"]
    assert len(candidates)==16
    assert {c["family"] for c in candidates}==set(LABELS)
    assert sha(root/"MODEL_MANIFEST.json")==protocol["model_manifest_sha256"]
    rows=[];families=[]
    for c in candidates:
        family=c["family"];group=[]
        for condition in conditions:
            name=family+"__"+condition["id"]
            p=root/"episodes"/(name+".execution.json")
            r=dict(family=family,candidate=c["name"],condition_id=condition["id"],status="not_dispatched")
            if p.exists():
                d=read(p);r.update(status=d["status"],receipt=str(p))
                assert d["candidate"]==c["name"] and d["condition_id"]==condition["id"]
                if d["status"]=="complete":
                    run=root/"episodes"/name
                    assert sha(run/"AUDIT.json")==d["audit_sha256"]
                    assert sha(d["metrics"])==d["metrics_sha256"]
                    a=read(run/"AUDIT.json");m=read(d["metrics"])
                    assert a["model_sha256"]==protocol["formal_model_sha256"]
                    assert m["trace_sha256"]==d["trace_sha256"]==a["trace_sha256"]
                    actual=read(run/"execution.json")["arguments"]
                    assert all(actual[k]==v for k,v in condition["overrides"].items())
                    assert actual["dt"]==protocol["physics_dt_s"]
                    assert all(m[k]==a[k] for k in ("task_success","strict_success","full_horizon"))
                    assert not a["strict_success"] or (a["task_success"] and a["penetration_mm"]<=.2)
                    r.update(audit=a,metrics=m,receipt_sha256=sha(p),audit_sha256=d["audit_sha256"],
                             metrics_sha256=d["metrics_sha256"],trace_sha256=d["trace_sha256"])
                    group.append(r)
            rows.append(r)
        task=sum(r["audit"]["task_success"] for r in group)
        strict=sum(r["audit"]["strict_success"] for r in group)
        f=dict(family=family,label=LABELS[family],candidate=c["name"],planned=24,
               completed=len(group),pending=24-len(group),task=task,strict=strict,
               task_rate=task/24 if len(group)==24 else None,
               strict_rate=strict/24 if len(group)==24 else None,
               task_wilson95=wilson(task,24) if len(group)==24 else None,
               strict_wilson95=wilson(strict,24) if len(group)==24 else None,
               short=sum(not r["audit"]["full_horizon"] for r in group),
               failed_final_stages=dict(Counter(r["audit"]["stage"] for r in group
                                                if not r["audit"]["task_success"])),
               failures=[dict(condition_id=r["condition_id"],stage=r["audit"]["stage"],
                         abort_reason=r["audit"].get("abort_reason"),penetration_mm=r["audit"]["penetration_mm"])
                         for r in group if not r["audit"]["strict_success"]])
        for key in ("rmse_mm","peak_torque_nm","peak_speed_mps"):
            f[key]=statistics.fmean(r["metrics"][key] for r in group) if group else None
        f["max_penetration_mm"]=max((r["audit"]["penetration_mm"] for r in group),default=None)
        f["contacts"]={}
        for event in ("ball","human","rod","unknown_edge"):
            contacts=[r["metrics"]["contact"][event] for r in group]
            p95=[v["contact_p95_force_n"] for v in contacts if v["exposure"]]
            f["contacts"][event]=dict(exposed=sum(v["exposure"] for v in contacts),
                mean_contact_p95_n=statistics.fmean(p95) if p95 else None,
                mean_impulse_ns=statistics.fmean(v["impulse_ns"] for v in contacts if v["exposure"]) if p95 else None)
        f["recovery"]={}
        for event in ("ball","human","rod"):
            rec=[r["metrics"]["recovery"][event] for r in group]
            times=[v["settled_rejoin_time_s"] for v in rec if v["settled_rejoin_time_s"] is not None]
            f["recovery"][event]=dict(recovered=len(times),exposed=sum(v["exposed"] for v in rec),
                    conditional_mean_s=statistics.fmean(times) if times else None)
        families.append(f)
    return dict(complete=all(f["completed"]==24 for f in families),planned=384,
                completed=sum(f["completed"] for f in families),families=families,rows=rows,
                protocol_sha256=sha(root/"PROTOCOL.json"),model_manifest_sha256=sha(root/"MODEL_MANIFEST.json"),
                condition_file_sha256=sha(root/"CONDITIONS.json"),
                report_source_sha256=sha(__file__),
                interpretation="New office-v7 24 stratified conditions, fixed model per method. Not the old office-v6 matrix. No low-force superiority claim without exposure, task and safety.",
                root=str(root))

def markdown(report):
    lines=["# Office-v7: all methods on the same 24 combined conditions","",
           f"Completed audited episodes: {report['completed']}/384. Final rates are only defined once each row has all 24 outcomes.",
           "", "Formal dt=5e-5; horizon=55s; original gates and limits; no training on this cohort.",
           "Ball (active short), hand/rod (active long), pillar/thick corner (passive). Fixed binary geometry; randomized disturbance parameters.",
           "Task/Strict failures and early aborts stay in the denominator. Missing infrastructure results are pending, never physical zeros.",
           "", "|Method|Completed|Task|Strict|Short failures|RMSE mm|Peak torque Nm|Peak speed m/s|Max penetration mm|",
           "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def fmt(v):return "NA" if v is None else f"{v:.3f}"
    def rate(f,k):return f"{f[k]}/24 ({100*f[k]/24:.1f}%)" if f["completed"]==24 else f"{f[k]} observed; pending {f['pending']}"
    for f in report["families"]:
        lines.append("|"+"|".join([f["label"],f"{f['completed']}/24",rate(f,"task"),rate(f,"strict"),str(f["short"]),
                 *[fmt(f[k]) for k in ("rmse_mm","peak_torque_nm","peak_speed_mps","max_penetration_mm")]])+"|")
    lines+=["","## Contact exposure and force","",
            "|Method|Ball exposed|Hand exposed / P95 N|Rod exposed / P95 N|Corner exposed|",
            "|---|---:|---:|---:|---:|"]
    for f in report["families"]:
        c=f["contacts"]
        n=f["completed"]
        lines.append(f"|{f['label']}|{c['ball']['exposed']}/{n}|{c['human']['exposed']}/{n} / {fmt(c['human']['mean_contact_p95_n'])}|{c['rod']['exposed']}/{n} / {fmt(c['rod']['mean_contact_p95_n'])}|{c['unknown_edge']['exposed']}/{n}|")
    lines+=["","Per-episode maxima are averaged in torque/speed columns; penetration is the worst across all completed episodes. Contact P95 is averaged only over exposed episodes.",
            "Exposure denominators above are completed episodes, not the number of planned episodes. Aborted runs have shorter observation and are not evidence of reduced contact or better tracking.",
            "Wilson 95% intervals, raw pair identities, failures, recovery censoring and evidence hashes are in REPORT.json.",
            "Enhanced teacher is a reference row; actor information scope and controller design must be reported separately from learned-policy comparisons.",
            "", "Server evidence: arm1@192.168.31.70:"+report["root"],
            "Protocol SHA256: "+report["protocol_sha256"],""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--wait-unit",help="Wait for this existing finite campaign service; never launch simulations")
    a=p.parse_args()
    if a.wait_unit:
        last_count=None
        while True:
            result=subprocess.run(["systemctl","--user","is-active",a.wait_unit],
                                  text=True,capture_output=True)
            if result.returncode not in (0,3,4):
                raise RuntimeError(result.stderr or result.stdout)
            if result.stdout.strip() not in ("active","activating","deactivating"):
                break
            counts=Counter(read(path)["status"] for path in
                           (a.root/"episodes").glob("*.execution.json"))
            if counts!=last_count:
                print(json.dumps(dict(episode_statuses=dict(counts),planned=384)),flush=True)
                last_count=counts
            time.sleep(20)
    a.output.mkdir(parents=True,exist_ok=False)
    r=build(a.root.resolve())
    (a.output/"REPORT.json").write_text(json.dumps(r,indent=2,allow_nan=False)+"\n")
    (a.output/"REPORT.md").write_text(markdown(r))
    print(json.dumps(dict(complete=r["complete"],completed=r["completed"],planned=384)))
    if a.wait_unit and not r["complete"]:
        raise SystemExit("Campaign stopped incomplete; partial report retained; no physical zeros invented")

if __name__=="__main__":main()
