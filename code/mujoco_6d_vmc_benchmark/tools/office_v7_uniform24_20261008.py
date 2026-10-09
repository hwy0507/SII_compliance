"""Register and execute a new, paired office-v7 24-condition cohort.

No training or result-based model/condition selection. Historical rollouts and
source trees are read-only. Infrastructure failures stop the queue, remain on
disk, and require an explicit new attempt; physical failures count in /24.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys

HISTORY = Path("/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149")
V6 = Path("/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002")
PARAMETER = Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02")
MENAGERIE = Path("/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie")
if os.environ.get('SII_LOCAL_RUNTIME'):
    _local = Path(os.environ['SII_LOCAL_RUNTIME']).resolve(strict=True)
    V6 = _local/'v6'
    MENAGERIE = _local/'menagerie'
FAMILIES = ("esn", "matched_rnn", "matched_mlp", "ordinary_rnn", "ordinary_mlp",
            "memoryless", "classical_vmc", "classical_admittance", "classical_impedance",
            "parameter_vmc", "parameter_admittance", "parameter_impedance",
            "direct_metric", "direct_office_task", "enhanced_teacher", "nominal_zero")
FORMAL = "d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3"
BASE = "bebb6331707228f7bf84fd4925611243cf2c442e"

def now():
    return datetime.now(timezone.utc).isoformat()

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def write(p, value):
    p = Path(p)
    tmp = p.with_suffix(p.suffix+".tmp")
    tmp.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")
    tmp.replace(p)

def environment(source):
    sys.path.insert(0, str(source/"tools"))
    from run_paper_final_validation_20261003 import ENV
    return {**ENV, "SII_SOURCE_BASE_COMMIT": BASE, "MUJOCO_MENAGERIE_PATH": str(MENAGERIE)}

def managed(source, command, label):
    return ["systemd-run", "--user", "--wait", "--pipe", "--collect",
            "--unit="+label, "--property=MemoryMax=3G", "--property=MemorySwapMax=0",
            "--working-directory="+str(source)] + [
                "--setenv="+k+"="+v for k,v in environment(source).items()] + command

def condition_rows():
    rng = random.Random(2026100824)
    # Stratified marginal coverage, generated once without any policy outcomes.
    bounds = dict(ball_speed=(1.305,1.595), person_start=(4.,5.),
                  rod_start=(13.5,14.5), person_stroke=(.18,.22),
                  rod_stroke=(.2115,.2585), rod_hold=(4.5,5.5))
    columns = {}
    for key,(lo,hi) in bounds.items():
        v = [round(lo+(hi-lo)*(i+rng.random())/24,6) for i in range(24)]
        rng.shuffle(v)
        columns[key]=v
    rows=[]
    for i in range(24):
        values = {k:v[i] for k,v in columns.items()}
        values.update(ball_launch_time_s=2., interaction_schedule="legacy",
                      events="all", duration=55., seed=2026091751,
                      planned_hand_corner=True, unexpected_edge=True,
                      combined_thick_corner_pillar_v4=True, allow_lateral_rejoin=True)
        assert values["rod_start"]-values["person_start"]-7. >= 1.5
        rows.append(dict(id=f"office_v7_24_{i:03d}", role="development", overrides=values))
    return rows,bounds

def prepare(root):
    root.mkdir(parents=True,exist_ok=False)
    source=root/"source"
    frozen=HISTORY/"final_evaluation_v1/queue_0/source"
    for folder in ("scripts","tools","assets"):
        shutil.copytree(frozen/folder,source/folder,
                        ignore=shutil.ignore_patterns("__pycache__","*.pyc"))
    for name in ("office_v7_worker_20261008.py", Path(__file__).name,
                 "office_v7_rl_preflight_20261008.py"):
        shutil.copy2(Path(__file__).with_name(name),source/"tools"/name)
    lock_path=HISTORY/"final_transition_v1/MODEL_LOCK.json"
    report_path=HISTORY/"final_delivery_v1/comparison/REPORT.json"
    lock=read(lock_path); report=read(report_path)
    chosen=[]
    for family in FAMILIES:
        name=report["families"][family]["models"][0]
        candidate=next(x for x in lock["candidates"] if x["name"]==name)
        chosen.append(dict(candidate,family=family))
        if candidate.get("checkpoint"):
            assert sha(candidate["checkpoint"])==candidate["checkpoint_sha256"]
    conditions,bounds=condition_rows()
    write(root/"CONDITIONS.json",dict(schema="sii-office-v7-conditions-v1",conditions=conditions))
    write(root/"MODEL_MANIFEST.json",dict(candidates=chosen,original_lock=str(lock_path),
         original_lock_sha256=sha(lock_path), selection="same first frozen model as prior uniform24 table"))
    hashes={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob("*")) if p.is_file()}
    write(root/"SOURCE_HASHES.json",hashes)
    write(root/"PROTOCOL.json",dict(schema="sii-office-v7-sequential-v1",registered_utc=now(),
        authorization="2026-10-08 user: every method on 24 combined scenes and repair RL",
        scene="office-v7-sequential-24",physics_dt_s=.00005,duration_s=55.,
        formal_model_sha256=FORMAL,condition_file_sha256=sha(root/"CONDITIONS.json"),
        model_manifest_sha256=sha(root/"MODEL_MANIFEST.json"),source_manifest_sha256=sha(root/"SOURCE_HASHES.json"),
        source_base_commit=BASE,condition_sampler_seed=2026100824,environment_seed=2026091751,
        conditions=24,methods=16,expected=384,distribution=bounds,
        actor_contract="unchanged canonical48/action7; estimated proprioceptive loads and reference-relative fields",
        categories={"passive":"fixed pillar/thick corner", "active_short":"ball at 2s",
                    "active_long":"person then rod; >=1.5s separation between commanded motions"},
        model_selection="No fitting. Same 16 first frozen family models as uniform24, replacing the older v7 pilot lock explicitly.",
        comparison="New paired development/generalization assessment; never reuses office-v6 outcomes.",
        gates="unchanged task/strict, external penetration <=0.2mm; physical short failures stay in /24",
        resources="Spark <=4 simulators, one thread and MemoryMax=3GiB per worker",
        missing="Infrastructure failure remains pending, never counted as physical task failure"))
    (root/"episodes").mkdir()
    (root/"preflight").mkdir()
    (root/"analysis").mkdir()
    write(root/"execution.json",dict(status="registered",registered_utc=now(),expected=384))
    return source

def preflight(root):
    source=root/"source";candidates=read(root/"MODEL_MANIFEST.json")["candidates"]
    for c in candidates:
        if not c.get("adapted_rl"):continue
        out=root/"preflight"/(c["family"]+".json")
        if out.exists():
            assert read(out)["status"]=="complete"
            continue
        command=[sys.executable,str(source/"tools/office_v7_rl_preflight_20261008.py"),
                 "--root",str(root),"--family",c["family"],"--output",str(out)]
        with out.with_suffix(".log").open("x") as f:
            rc=subprocess.run(managed(source,command,"sii-v724-pre-"+c["family"].replace("_","-")),stdout=f,stderr=subprocess.STDOUT).returncode
        if rc:raise RuntimeError("RL preflight failed, retained: "+c["family"])
    write(root/"PREFLIGHT_COMPLETE.json",dict(status="complete",ended_utc=now(),
          evidence={p.name:sha(p) for p in (root/"preflight").glob("*.json")}))

def command_for(root,c,d,run,config):
    source=root/"source"
    kind="adapted_rl" if c.get("adapted_rl") else "nominal" if c.get("nominal") else "classical" if c.get("controller") else "office"
    command=[sys.executable,str(source/"tools/office_v7_worker_20261008.py"),
         "--research-protocol",str(root/"PROTOCOL.json"),"--protocol-sha256",sha(root/"PROTOCOL.json"),
         "--research-condition",d["id"],"--worker-kind",kind,"--v6-input",str(V6),
         "--reference",str(V6/"esn_original_v2/rollout.json"),"--config",str(config),
         "--output",str(run),"--contact-audit","--physics-dt","0.00005"]
    if c.get("adapted_rl"):
        rl=c["adapted_rl"]
        command+=["--agent-checkpoint",rl["checkpoint"],"--checkpoint-manifest",rl["manifest"],
                  "--parameter-source",rl["parameter_source"]]
        if rl.get("controller"):command+=["--controller",rl["controller"]]
    elif c.get("controller"):
        command+=["--controller",c["controller"],"--parameter-source",str(PARAMETER)]
    elif c.get("checkpoint"):command+=["--checkpoint",c["checkpoint"]]
    return command

def one(root,c,d):
    source=root/"source";name=c["family"]+"__"+d["id"]
    run=root/"episodes"/name; receipt=root/"episodes"/(name+".execution.json")
    if receipt.exists():
        old=read(receipt)
        if old.get("status")=="complete":
            assert sha(run/"AUDIT.json")==old["audit_sha256"]
            assert sha(run/"rollout.npz")==old["trace_sha256"]
            return old
        raise RuntimeError("Preserve incomplete attempt; inspect before retry: "+name)
    config=root/"episodes"/(name+".config.json");write(config,c.get("config",{}))
    command=command_for(root,c,d,run,config)
    row=dict(name=name,family=c["family"],candidate=c["name"],condition_id=d["id"],
             started_utc=now(),status="running",command=command)
    write(receipt,row)
    with (root/"episodes"/(name+".log")).open("x") as f:
        rc=subprocess.run(managed(source,command,"sii-v724-"+name.replace("_","-")),stdout=f,stderr=subprocess.STDOUT).returncode
    row.update(returncode=rc,ended_utc=now())
    if rc:
        row["status"]="infrastructure_failure_preserved";write(receipt,row)
        raise RuntimeError("worker failed: "+name)
    audit=read(run/"AUDIT.json");actual=read(run/"execution.json")["arguments"]
    for key,value in d["overrides"].items():
        assert actual[key]==value,(name,key,actual[key],value)
    assert audit["model_sha256"]==FORMAL
    metric=root/"analysis"/(name+".json")
    cmd=[sys.executable,str(source/"tools/paper_metrics_20261002.py"),"--run",str(run),"--output",str(metric)]
    with (root/"analysis"/(name+".log")).open("x") as f:
        rc=subprocess.run(managed(source,cmd,"sii-v724-audit-"+name.replace("_","-")),stdout=f,stderr=subprocess.STDOUT).returncode
    if rc:
        row["status"]="independent_audit_failed_preserved";write(receipt,row)
        raise RuntimeError("audit failed: "+name)
    metrics=read(metric)
    for key in ("rmse_mm","peak_torque_nm","peak_speed_mps"):
        assert abs(metrics[key]-audit[key])<1e-4,(name,key)
    row.update(status="complete",audit=audit,audit_sha256=sha(run/"AUDIT.json"),
               trace_sha256=sha(run/"rollout.npz"),metrics=str(metric),metrics_sha256=sha(metric))
    write(receipt,row)
    return row

def summarize(root):
    rows=[read(p) for p in sorted((root/"episodes").glob("*.execution.json"))]
    families=[]
    expected_ids={d["id"] for d in read(root/"CONDITIONS.json")["conditions"]}
    for family in FAMILIES:
        rr=[r for r in rows if r["family"]==family and r["status"]=="complete"]
        assert len({r["condition_id"] for r in rr})==len(rr)
        assert {r["condition_id"] for r in rr}<=expected_ids
        aa=[r["audit"] for r in rr]
        f=dict(family=family,planned=24,completed=len(rr),pending=24-len(rr),
               task=sum(a["task_success"] for a in aa),strict=sum(a["strict_success"] for a in aa),
               short=sum(not a["full_horizon"] for a in aa))
        for key in ("rmse_mm","peak_torque_nm","peak_speed_mps","penetration_mm"):
            f[key]=statistics.fmean(a[key] for a in aa) if aa else None
        if len(rr)==24:
            f.update(task_rate=f["task"]/24,strict_rate=f["strict"]/24)
        families.append(f)
    summary=dict(created_utc=now(),expected=384,completed=sum(f["completed"] for f in families),
                 families=families,rows=rows,protocol_sha256=sha(root/"PROTOCOL.json"))
    write(root/"SUMMARY.json",summary)
    return summary

def execute(root):
    assert read(root/"PREFLIGHT_COMPLETE.json")["status"]=="complete"
    protocol=read(root/"PROTOCOL.json")
    for file,key in (("CONDITIONS.json","condition_file_sha256"),("MODEL_MANIFEST.json","model_manifest_sha256"),("SOURCE_HASHES.json","source_manifest_sha256")):
        assert sha(root/file)==protocol[key]
    for rel,h in read(root/"SOURCE_HASHES.json").items():assert sha(root/"source"/rel)==h,rel
    candidates=read(root/"MODEL_MANIFEST.json")["candidates"]
    conditions=read(root/"CONDITIONS.json")["conditions"]
    # RL appears first in the first wave to catch restore/runtime errors early.
    candidates=sorted(candidates,key=lambda c:not bool(c.get("adapted_rl")))
    planned=[(c,d) for d in conditions for c in candidates]
    write(root/"execution.json",dict(status="running",started_utc=now(),expected=len(planned)))
    def queue(index):
        for c,d in planned[index::4]:
            one(root,c,d)
        return index
    failures=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(queue,i) for i in range(4)]
        for future in futures:
            try:future.result()
            except Exception as exc:failures.append(repr(exc))
    s=summarize(root)
    write(root/"execution.json",dict(status="complete" if s["completed"]==384 else "incomplete_preserved",
         ended_utc=now(),expected=384,completed=s["completed"],errors=failures))
    if failures:raise RuntimeError(failures)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--phase",choices=("prepare","preflight","run","summary"),required=True)
    a=p.parse_args();root=a.root.resolve()
    if a.phase=="prepare":prepare(root);return
    with (root/".coordinator.lock").open("a") as f:
        fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if a.phase=="preflight":preflight(root)
        elif a.phase=="run":execute(root)
        else:summarize(root)

if __name__=="__main__":main()
