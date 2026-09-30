"""Fast trainer integration check with fake physics and the real official agent.

This validates 5000-step warmup, nested update logging, statistics, checkpoint
and replay plumbing. It is NOT a physical Office performance experiment.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import train


class FakeOffice:
    def __init__(self, root, rewarder, duration, physics_dt):
        self.root=Path(root); self.root.mkdir(parents=True)
        self.duration=duration; self.physics_dt=physics_dt
        self.episode=0; self.worker=None
    def reset(self,seed,options):
        self.episode+=1; self.k=0
        return np.zeros(48,dtype=np.float32), {"interval":{"potential":0.}}
    def step_raw(self,action):
        self.k+=1; done=self.k>=1375
        obs=np.full(48, .001*np.sin(self.k),dtype=np.float32)
        iv=dict(elapsed_s=.04,error_cost=0.,peak_torque_ratio=0.,
                peak_torque_nm_per_joint=[0.]*7,max_position_error_m=0.,
                substeps=400,time_s=self.k*.04,stage=0,potential=0.,
                task_complete_before_interval=False)
        info={"interval":iv}
        if done:
            info["evaluation"]=dict(strict_success=False,task_success=False,
                physical_valid=True,placement_complete=False,abort_reason=None,
                final_task_stage="approach",metrics={},stats={"events":{}})
        return obs,done,info
    def close(self):
        pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    train.OfficeEnv=FakeOffice
    train.train(SimpleNamespace(output=args.output,reward="metric",seed=73,
        steps=5001,duration=55.,physics_dt=.0001,gamma=.995,utd=2,smooth=.005,
        wall_seconds=300.,checkpoint_every=10000,resume=None))
    result=json.loads((args.output/"COMPLETE.json").read_text())
    assert result["steps"]==5001,result
    assert result["updates"]==4,result
    progress=json.loads((args.output/"progress.json").read_text())
    assert progress["last_update"],"real update metrics should be logged"
    assert all(np.isfinite(v) for v in progress["last_update"].values())
    state=json.loads((args.output/"checkpoint_final"/"runner_state.json").read_text())
    assert state["replay"]["count"]==5001
    assert state["pending_transition"] is not None
    print("PASS real SimbaV2 trainer update/checkpoint with fake physical stepping",result)

if __name__=="__main__": main()
