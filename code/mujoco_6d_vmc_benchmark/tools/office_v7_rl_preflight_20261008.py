"""Checkpoint loading and immutable action replay before any new v7 physics."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from research72_rl_actor_replay_20261004 import read,sha,normalization_hash,run_replay
from research72_checkpoint_20261003 import checkpoint_hashes

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--family",required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    c=next(x for x in read(a.root/"MODEL_MANIFEST.json")["candidates"] if x["family"]==a.family)
    rl=c["adapted_rl"]
    assert sha(rl["manifest"])==rl["manifest_sha256"]
    manifest=read(rl["manifest"]); cp=Path(rl["checkpoint"])
    assert checkpoint_hashes(cp)==manifest["hashes"]
    sys.path.insert(0,rl["parameter_source"])
    from official_parameter_agent import OfficialParameterAgent
    cfg=read(cp/"official_agent_state.json");config=cfg["config"];utd=cfg["utd"]
    agent=OfficialParameterAgent(seed=config["seed"],total_steps=int(config["learning_rate_decay_step"])//utd,
         utd=utd,gamma=config["gamma"],entropy_coef=config["temp_target_entropy_coef"],
         initial_temperature=config["temp_initial_value"],action_dimension=config["action_dimension"])
    agent.load(cp)
    history=Path("/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149")
    runs=list((history/"final_evaluation_v1").glob("queue_*/"+c["name"]+"__heldout_000"))
    assert len(runs)==1
    evidence=run_replay(agent,runs[0],manifest,config["action_dimension"])
    import jax,os
    result=dict(status="complete",family=a.family,candidate=c["name"],
                devices=[str(x) for x in jax.devices()],jax_platforms=os.environ.get("JAX_PLATFORMS"),
                checkpoint_manifest_sha256=sha(rl["manifest"]),evidence=evidence,
                physics_steps=0,gradient_updates=0,normalization_sha256=normalization_hash(agent))
    a.output.write_text(json.dumps(result,indent=2)+"\n")

if __name__=="__main__":main()

