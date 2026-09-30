"""Exact episode-boundary resume invariant: fake dynamics, real official agent.
4 uninterrupted steps vs 2 steps + saved boundary + 2 resumed steps.
This is a software test, not an Office baseline performance result.
"""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import jax
import train
from official_agent import OfficialOfficeAgent


class TwoStepOffice:
    def __init__(self,root,rewarder,duration,physics_dt):
        self.root=Path(root);self.root.mkdir(parents=True)
        self.episode=0;self.worker=None
    def reset(self,seed,options):
        self.episode+=1;self.k=0;self.worker=True
        self.rng=np.random.default_rng(seed)
        self.obs=self.rng.normal(0,.1,48).astype(np.float32)
        return self.obs.copy(),{"interval":{"potential":.1}}
    def step_raw(self,action):
        self.k+=1;done=self.k==2
        self.obs=self.obs+np.float32(.001*np.sum(action))
        error=float(np.linalg.norm(self.obs[:3]))*.1
        iv=dict(elapsed_s=.04,error_cost=.04/.08*(error/.12)**2,
            peak_torque_ratio=.2,peak_torque_nm_per_joint=[1.]*7,
            max_position_error_m=error,substeps=400,
            time_s=self.k*.04,stage=0,potential=.1+.1*self.k,
            task_complete_before_interval=False)
        info={"interval":iv}
        if done:
            self.worker=None
            info["evaluation"]=dict(strict_success=False,task_success=False,
                physical_valid=True,placement_complete=False,abort_reason=None,
                final_task_stage="approach",metrics={},stats={"events":{}})
        return self.obs.copy(),done,info
    def close(self):
        self.worker=None


def args(output,resume=None,stop=None):
    return SimpleNamespace(output=output,reward="metric",seed=993,
        steps=4,duration=.08,physics_dt=.0001,gamma=.995,utd=2,smooth=.005,
        wall_seconds=600.,checkpoint_every=2,resume=resume,stop_after_step=stop)


def rows(path):
    return [json.loads(x) for x in path.read_text().splitlines()]


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    train.OfficeEnv=TwoStepOffice
    train.WARMUP_STEPS=1
    full=a.output/"full";first=a.output/"first";resumed=a.output/"resumed"
    train.train(args(full))
    train.train(args(first,stop=2))
    boundary=first/"checkpoint_boundary_0000002"
    assert boundary.exists()
    boundary_state=json.loads((boundary/"runner_state.json").read_text())
    assert boundary_state["mid_episode"] is False
    assert boundary_state["pending_transition"]["terminated"] is True
    train.train(args(resumed,resume=boundary))
    full_rows=rows(full/"control_audit.jsonl")
    split_rows=rows(first/"control_audit.jsonl")+rows(resumed/"control_audit.jsonl")
    assert full_rows==split_rows,"action/reward/interval sequence differs"
    fcp=full/"checkpoint_final";rcp=resumed/"checkpoint_final"
    with np.load(fcp/"replay.npz") as x,np.load(rcp/"replay.npz") as y:
        for key in x.files:np.testing.assert_array_equal(x[key],y[key])
    fs=json.loads((fcp/"runner_state.json").read_text())
    rs=json.loads((rcp/"runner_state.json").read_text())
    for key in ("step","episode_index","exploration_rng","replay","pending_transition","reward_state"):
        assert fs[key]==rs[key],key
    agent1=OfficialOfficeAgent(993,4,utd=2,gamma=.995);agent1.load(fcp)
    agent2=OfficialOfficeAgent(993,4,utd=2,gamma=.995);agent2.load(rcp)
    leaf_count=0
    for name in ("_actor","_critic","_target_critic","_temperature"):
        l1=jax.tree_util.tree_leaves(getattr(agent1.raw_agent,name))
        l2=jax.tree_util.tree_leaves(getattr(agent2.raw_agent,name))
        assert len(l1)==len(l2)
        for x,y in zip(l1,l2):
            np.testing.assert_array_equal(np.asarray(x),np.asarray(y))
            leaf_count+=1
    assert agent1.diagnostics()==agent2.diagnostics()
    np.testing.assert_array_equal(np.asarray(agent1.raw_agent._rng),np.asarray(agent2.raw_agent._rng))
    # Mid-episode checkpoints must be explicitly rejected, never silently reset.
    mid=a.output/"mid"
    train.train(args(mid,stop=1))
    try:
        train.train(args(a.output/"must_reject",resume=mid/"checkpoint_final"))
    except ValueError as error:
        assert "Mid-episode" in str(error)
    else:
        raise AssertionError("Mid-episode checkpoint accepted")
    validation=dict(status="passed",kind="fake_physics_real_official_agent_resume",
        uninterrupted_steps=4,split_steps=[2,2],updates=agent1.updates,
        parameter_optimizer_leaves_identical=leaf_count,
        actions_rewards_replay_normalizers_rng_identical=True,
        pending_terminal_consumed_exactly_once=True,mid_episode_rejected=True)
    (a.output/"VALIDATION.json").write_text(json.dumps(validation,indent=2)+"\n")
    print(json.dumps(validation,indent=2))


if __name__=="__main__":
    main()
