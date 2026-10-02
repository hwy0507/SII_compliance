"""Finite foreground replay export for the current registered experiment window."""
import json,subprocess,sys,time
from pathlib import Path
from dispatch_evaluation import ROOT,LABELS
HERE=Path(__file__).resolve().parent
ORDER=["direct_metric_74001","direct_office_task_74001","zero","grid_admittance","grid_impedance","fixed_admittance","fixed_impedance","fixed_vmc","direct_metric_74002","direct_office_task_74002","parameter_admittance","parameter_impedance","parameter_vmc"]
END=1790944591-180
def main():
    logs=ROOT/"media_render01";logs.mkdir(exist_ok=False);done={};failures=[]
    while time.time()<END and len(done)<len(ORDER)*4:
        ready=[]
        for identity in ORDER:
            parent=ROOT/"final_reference01"/identity
            if not (parent/"ROWS.json").exists():continue
            rows=json.loads((parent/"ROWS.json").read_text())
            for row in rows:
                key=identity+"/"+row["fixture_id"]
                if key in done:continue
                if row.get("initial_state_rejected"):
                    done[key]="initial_state_rejected";continue
                ready.append((identity,row,key))
        if not ready:time.sleep(5);continue
        identity,row,key=ready[0];episode=Path(row["evaluation_output"]);label=LABELS[identity]
        protocol=json.loads((episode.parent/"PROTOCOL.json").read_text())
        if protocol.get("checkpoint"):label+=" @ "+Path(protocol["checkpoint"]).name
        command=[sys.executable,str(HERE/"render.py"),str(episode),"--label",label]
        with (logs/(key.replace("/","_")+".log")).open("w") as log:
            try:rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=min(600,max(1,END-time.time()))).returncode
            except subprocess.TimeoutExpired:rc=124
        done[key]="complete" if rc==0 else "failed"
        if rc:failures.append(dict(episode=str(episode),returncode=rc))
        (logs/"STATE.json").write_text(json.dumps(dict(done=done,failures=failures),indent=2))
        entries=[]
        for name in ORDER:
            parent=ROOT/"final_reference01"/name
            if not list(parent.glob("*/media/RENDER.json")):continue
            label=LABELS[name]
            if (parent/"PROTOCOL.json").exists():
                pr=json.loads((parent/"PROTOCOL.json").read_text())
                if pr.get("checkpoint"):label+=" @ "+Path(pr["checkpoint"]).name
            entries.append(dict(id="final_"+name,label=label,path=str(parent),group="final_development"))
        catalog=dict(status="最终 checkpoint 开发回放：已生成 "+str(sum(v=="complete" for v in done.values()))+"/52 个原始展示条件视频；固定测试成绩另见结果页。",entries=entries)
        (ROOT/"FINAL_MEDIA_CATALOG.json").write_text(json.dumps(catalog,ensure_ascii=False,indent=2))
        if entries:subprocess.run([sys.executable,str(HERE/"gallery.py"),"--catalog",str(ROOT/"FINAL_MEDIA_CATALOG.json")],check=True)
        print(json.dumps(dict(episode=key,status=done[key],completed=sum(v=="complete" for v in done.values()))),flush=True)
    (logs/"COMPLETE.json").write_text(json.dumps(dict(finished_epoch=time.time(),rendered=sum(v=="complete" for v in done.values()),failed=failures,missing=52-len(done)),indent=2))
if __name__=="__main__":main()
