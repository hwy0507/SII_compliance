"""Lock the largest common completed periodic checkpoint available by the deadline."""
import hashlib,json,re,time
from pathlib import Path
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")
DEADLINE=1790941200.0
def main():
    output=ROOT/"PARAMETER_CHECKPOINT_LOCK.json"
    if output.exists():print(output.read_text());return
    if time.time()<DEADLINE:raise RuntimeError("Registered training deadline has not arrived")
    candidates={};records={}
    for c in ["admittance","impedance","vmc"]:
        run=ROOT/"parameter_rl/campaign01"/(c+"_seed75001")
        if not (run/"COMPLETE.json").exists():raise RuntimeError("Wait for finite episode/checkpoint writes to finish: "+c)
        records[c]=json.loads((run/"COMPLETE.json").read_text());available={}
        for p in run.glob("checkpoint_*"):
            if not re.fullmatch(r"checkpoint_\d{7}",p.name) or not (p/"official_agent_state.json").exists():continue
            files=[v for v in p.rglob("*") if v.is_file()]
            latest=max(v.stat().st_mtime for v in files)
            if latest<=DEADLINE:available[int(p.name.split("_")[1])]=dict(path=str(p),latest_file_mtime=latest)
        candidates[c]=available
    common=sorted(set.intersection(*(set(v) for v in candidates.values())))
    if not common:raise RuntimeError("No common eligible periodic checkpoint")
    step=max(common);selected={}
    for c,v in candidates.items():
        item=dict(v[step]);p=Path(item["path"])
        item["inference_sha256"]={str(f.relative_to(p)):hashlib.sha256(f.read_bytes()).hexdigest() for f in p.rglob("*") if f.is_file() and f.name!="replay.npz"}
        selected[c]=item
    result=dict(locked_epoch=time.time(),training_deadline_epoch=DEADLINE,selected_step=step,rule="Largest common completed periodic checkpoint with all saved file mtimes <= registered training deadline; no test/validation scores",eligible_steps={c:sorted(v) for c,v in candidates.items()},selected=selected,training_completion=records)
    output.write_text(json.dumps(result,indent=2));print(json.dumps(dict(step=step,eligible=result["eligible_steps"],output=str(output)),indent=2))
if __name__=="__main__":main()
