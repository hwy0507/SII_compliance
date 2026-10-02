"""Finite export of completed pinned office transfers; no physics integration."""
import json,subprocess,sys,time
from pathlib import Path
from render_clips import RENDERER
HERE=Path(__file__).resolve().parent
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
IDS=["direct_metric_74001","direct_office_task_74001","fixed_admittance","fixed_impedance","fixed_vmc","parameter_admittance","parameter_impedance","parameter_vmc","direct_metric_74002","direct_office_task_74002","zero"]
END=1790944591-180
def main():
    logs=ROOT/"office_bridge/media_export01";logs.mkdir(exist_ok=False);done={};failures=[]
    while time.time()<END and len(done)<len(IDS):
        ready=[]
        for identity in IDS:
            folder=ROOT/"office_bridge/transfer01"/identity
            if identity in done or not (folder/"EXECUTION.json").exists():continue
            if json.loads((folder/"EXECUTION.json").read_text())["status"]!="complete":continue
            if (folder/"media/manifest.json").exists():done[identity]="previously_rendered";continue
            ready.append((identity,folder))
        if not ready:time.sleep(5);continue
        identity,folder=ready[0]
        commands=[[sys.executable,str(RENDERER),"--rollout",str(folder/"rollout"),"--output",str(folder/"media"),"--label",identity.replace("_"," ")+" | 1x full-run metrics","--stride","1","--fps","25","--gif-stride","5","--contact-closeup"],
                  [sys.executable,str(HERE/"render_clips.py"),"--prefix",str(folder/"rollout"),"--label",identity.replace("_"," ")]]
        rc=0
        with (logs/(identity+".log")).open("w") as log:
            for command in commands:
                try:rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=max(1,min(600,END-time.time()))).returncode
                except subprocess.TimeoutExpired:rc=124
                if rc:break
        done[identity]="complete" if rc==0 else "failed"
        if rc:failures.append(dict(id=identity,returncode=rc))
        (logs/"STATE.json").write_text(json.dumps(dict(done=done,failures=failures),indent=2))
        subprocess.run([sys.executable,str(HERE/"gallery.py")],check=True)
        print(json.dumps(dict(id=identity,status=done[identity])),flush=True)
    (logs/"COMPLETE.json").write_text(json.dumps(dict(done=done,failures=failures,missing=[i for i in IDS if i not in done]),indent=2))
if __name__=="__main__":main()
