"""Audit observation/action, physical pairing and frozen evaluation contracts."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
def audit(catalog,output):
    cat=json.loads(catalog.read_text());rows=[];models=[];pair={};launches={}
    for entry in cat["models"]:
        parent=Path(entry["output"])
        if not (parent/"PROTOCOL.json").exists():
            models.append(dict(id=entry["id"],status="not_started"));continue
        protocol=json.loads((parent/"PROTOCOL.json").read_text())
        assert protocol["split"]==cat["split"] and protocol["deterministic"] and protocol["save_substeps"]
        assert len(protocol["fixtures"])==cat["planned_per_model"]
        actual=json.loads((parent/"ROWS.json").read_text()) if (parent/"ROWS.json").exists() else []
        assert len({r["fixture_id"] for r in actual})==len(actual)
        assert all(r["fixture_id"] in protocol["fixtures"] for r in actual)
        complete=(parent/"COMPLETE.json").exists()
        if complete:
            receipt=json.loads((parent/"COMPLETE.json").read_text())
            assert len(actual)==len(protocol["fixtures"])==receipt["completed"]
            if protocol["checkpoint"]:assert receipt["normalizers_unchanged"] is True
        for result in actual:
            if result.get("initial_state_rejected"):
                rows.append(dict(model=entry["id"],fixture=result["fixture_id"],status="initial_state_rejected"));continue
            episode=Path(result["evaluation_output"]);z=np.load(episode/"control.npz");obs=z["observation"];action=z["action"];times=z["time"]
            assert obs.shape==(len(times),48) and action.shape==(len(times),7)
            assert np.isfinite(obs).all() and np.isfinite(action).all() and np.max(abs(action))<=1.000001
            assert len(times)==result["steps"]
            timing=float(np.max(abs(np.diff(times)-.04))) if len(times)>1 else 0.
            assert timing<1e-8
            model_hash=hashlib.sha256((episode/"model.mjb").read_bytes()).hexdigest()
            assert model_hash==result["model_sha256"]
            pairs=pair.setdefault(result["fixture_id"],set());pairs.add((model_hash,result.get("physical_hash")))
            assert len(pairs)==1
            original=json.loads((episode/"original.json").read_text())
            launch=original.get("ball_launch_state")
            if launch:launches.setdefault(result["fixture_id"],[]).append(dict(model=entry["id"],launch=launch))
            rows.append(dict(model=entry["id"],fixture=result["fixture_id"],status="verified",samples=len(times),observation_dimension=48,output_action_dimension=7,maximum_abs_action=float(abs(action).max()),maximum_actor_interval_error_s=timing,model_sha256=model_hash))
        models.append(dict(id=entry["id"],completed=len(actual),planned=len(protocol["fixtures"]),status="complete" if complete else "running",checkpoint=protocol["checkpoint"],normalization_hash=protocol["normalization_hash"]))
    launch_comparison={}
    for fixture,items in launches.items():
        positions=np.array([v["launch"]["launch_position_m"] for v in items]);velocities=np.array([v["launch"]["launch_velocity_mps"] for v in items]);times=np.array([v["launch"]["time_s"] for v in items])
        launch_comparison[fixture]=dict(records=items,launch_time_range_s=[float(times.min()),float(times.max())],maximum_position_difference_from_first_m=float(np.linalg.norm(positions-positions[0],axis=1).max()),maximum_velocity_difference_from_first_mps=float(np.linalg.norm(velocities-velocities[0],axis=1).max()),same_exogenous_launch=bool(np.max(abs(positions-positions[0]))<1e-9 and np.max(abs(velocities-velocities[0]))<1e-9 and np.ptp(times)<1e-9))
    result=dict(ball_launch_comparison=launch_comparison,catalog=str(catalog),models=models,rows=rows,verified_episodes=sum(r["status"]=="verified" for r in rows),paired_fixture_count=len(pair),scope="Checks saved actor inputs/common normalized output commands and shared model/fixture identity, not identical exogenous impact states. Legacy ball launch depends on actual hand/task state; launch differences are reported. Torque/speed statistics are independently audited from native substeps. Partial models remain explicitly partial.")
    output.parent.mkdir(exist_ok=True,parents=True);output.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(verified=result["verified_episodes"],paired_fixtures=len(pair),completed_models=sum(m["status"]=="complete" for m in models))))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--catalog",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();audit(a.catalog,a.output)
