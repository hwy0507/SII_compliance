"""Bounded handoff from pilot to source-checked training and final evaluation."""
from pathlib import Path
from datetime import datetime
import argparse,json,os,subprocess,time
STUDY=Path("/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001")
REPO=Path("/home/arm1/SII_compliance_baseline")
HERE=Path(__file__).resolve().parent
PY=Path("/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python")
def state(**kw):
    p=STUDY/"BOOTSTRAP_STATE.json";q=p.with_suffix(".tmp")
    q.write_text(json.dumps(dict(updated_utc=time.time(),pid=os.getpid(),**kw),indent=2)+"\n");q.replace(p)
def invoke(name,cmd):
    with (STUDY/(name+".log")).open("w") as log:
        proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
        state(phase=name,command=cmd,child_pid=proc.pid)
        rc=proc.wait()
    if rc:raise RuntimeError(f"{name} returncode={rc}")
def main():
    p=argparse.ArgumentParser();p.add_argument("--expected-commit",required=True);a=p.parse_args()
    state(phase="waiting_pilot_02",expected_commit=a.expected_commit)
    while not (STUDY/"exploration_pilot_02/COMPLETE.json").exists():
        if time.time()>datetime.fromisoformat("2026-10-01T12:31:00+00:00").timestamp():
            raise RuntimeError("Pilot incomplete at training cutoff")
        time.sleep(15)
    if not json.loads((STUDY/"exploration_pilot_02/COMPLETE.json").read_text())["successful"]:
        raise RuntimeError("Pilot02 failed")
    commit=subprocess.check_output(["git","-C",str(REPO),"rev-parse","HEAD"],text=True).strip()
    if commit!=a.expected_commit:raise RuntimeError("Unexpected source commit")
    subprocess.run(["git","-C",str(REPO),"diff","--quiet","HEAD","--","code/mujoco_6d_vmc_benchmark"],check=True)
    invoke("telemetry_invariance_02",[str(PY),str(HERE/"test_telemetry_invariance.py"),"--output",str(STUDY/"telemetry_invariance_02")])
    invoke("main_campaign_supervisor",[str(PY),str(HERE/"campaign.py")])
    invoke("main_campaign_report",[str(PY),str(HERE/"report_campaign.py"),"--campaign",str(STUDY/"campaign_01"),"--sensitivity"])
    state(phase="complete",commit=commit,report=str(STUDY/"campaign_01/report/REPORT.md"))
if __name__=="__main__":
    try:main()
    except BaseException as e:
        state(phase="failed",error=repr(e));raise
