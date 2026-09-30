"""Paired from-scratch official SimbaV2 reward experiment, isolated on Spark."""
from __future__ import annotations
import argparse, dataclasses, hashlib, json, os, signal, sys, time
from pathlib import Path
import numpy as np
from office_env import OfficeEnv, ROOT
from rewards import RewardConfig, OfficeReward, IntervalMetrics
from official_agent import OfficialOfficeAgent, WARMUP_STEPS, BATCH_SIZE

def clean(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,Path):return str(x)
    raise TypeError(type(x).__name__)
def dump(path,value):
    path=Path(path);tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,indent=2,default=clean,allow_nan=False)+"\n");tmp.replace(path)

class Replay:
    def __init__(self,capacity,seed):
        self.capacity=capacity;self.count=0;self.rng=np.random.default_rng(seed)
        self.data={k:np.empty((capacity,)+shape,np.float32) for k,shape in
          dict(observation=(48,),action=(7,),reward=(),terminated=(),truncated=(),next_observation=(48,)).items()}
    def add(self,**row):
        i=self.count%self.capacity
        for k,v in row.items():self.data[k][i]=v
        self.count+=1
    def sample(self,n):
        idx=self.rng.integers(0,min(self.count,self.capacity),n)
        return {k:v[idx] for k,v in self.data.items()}
    def save(self,path):
        n=min(self.count,self.capacity)
        np.savez(path,**{k:v[:n] for k,v in self.data.items()})
        return dict(count=self.count,capacity=self.capacity,rng=self.rng.bit_generator.state)
    def load(self,path,state):
        if int(state["capacity"])!=self.capacity:
            raise ValueError("Replay capacity changed; exact resume requires original total step budget")
        count=int(state["count"]);n=min(count,self.capacity)
        if count<0:raise ValueError("Negative replay count")
        with np.load(path,allow_pickle=False) as saved:
            if set(saved.files)!=set(self.data):raise ValueError("Replay schema mismatch")
            for key,array in self.data.items():
                value=saved[key]
                if value.shape!=(n,)+array.shape[1:]:raise ValueError("Replay shape mismatch: "+key)
                array[:n]=value
        self.count=count
        self.rng.bit_generator.state=state["rng"]

def fixture(seed,episode):
    rng=np.random.default_rng(seed+100003*episode)
    variants=(-4,-3,-2,-1);events=("all","all","ball","person","rod")
    return dict(seed=int(seed+100003*episode),variant=variants[episode%4],events=events[episode%5],
        ball_speed=float(rng.uniform(1.35,1.95)),person_stroke=float(rng.uniform(.16,.23)),
        rod_stroke=float(rng.uniform(.19,.24)))

def train(a):
    resume_path=Path(a.resume).resolve() if getattr(a,"resume",None) else None
    resume_state=json.loads((resume_path/"runner_state.json").read_text()) if resume_path else None
    if resume_state is not None:
        if resume_state.get("resume_format_version")!=1:
            raise ValueError("Unsupported checkpoint resume format")
        if resume_state.get("mid_episode",True):
            raise ValueError("Mid-episode checkpoint cannot be resumed exactly: choose checkpoint_boundary_*; simulator state was not saved")
        if int(resume_state["step"])>=a.steps:
            raise ValueError("--steps is the original total budget, and must exceed restored step")
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    config=RewardConfig(mode=a.reward,horizon_s=a.duration,gamma=a.gamma,smooth_weight=a.smooth)
    rewarder=OfficeReward(config)
    agent=OfficialOfficeAgent(a.seed,a.steps,utd=a.utd,gamma=a.gamma)
    replay=Replay(max(a.steps,10000),a.seed+53)
    exploration=np.random.default_rng(a.seed+71)
    env=OfficeEnv(out/"episodes",rewarder,duration=a.duration,physics_dt=a.physics_dt)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"scripts").glob("*.py")}
    run_definition=dict(seed=a.seed,total_step_budget=a.steps,reward=config.to_dict(),
        utd=a.utd,physics_dt=a.physics_dt,warmup_steps=WARMUP_STEPS,
        train_variants=[-4,-3,-2,-1],train_event_cycle=["all","all","ball","person","rod"])
    if resume_state is not None:
        if resume_state.get("run_definition")!=run_definition:
            raise ValueError("Resume protocol differs; retain original seed, total steps, reward, UTD, dt and warmup")
        if resume_state.get("source_sha256")!=hashes:
            raise ValueError("Runtime source changed; exact resume rejected")
        agent.load(resume_path)
        replay.load(resume_path/"replay.npz",resume_state["replay"])
        exploration.bit_generator.state=resume_state["exploration_rng"]
        env.episode=int(resume_state["env_episode_index"])
    dump(out/"PROTOCOL.json",dict(
        name="official_simbav2_office_reward_comparison_20260930",seed=a.seed,total_step_budget=a.steps,
        actor="raw proprio48 only; no task stage, clock, contact truth or obstacle geometry",
        action="canonical tanh [-1,1]^7: slowdown + world Cartesian twist residual",
        additional_rl_only_safety_envelope=False,teacher=False,vmc=False,bc=False,from_scratch=resume_state is None,
        resumed_from=str(resume_path) if resume_path else None,resume_mode="episode_boundary_exact" if resume_path else None,
        observation_and_reward_normalization="official running statistics; training only",
        reward=config.to_dict(),agent=agent.config,utd=a.utd,initial_random_steps=WARMUP_STEPS,
        train_physics_dt=a.physics_dt,formal_evaluation_physics_dt=.00005,duration_s=a.duration,
        reference="current PickPlaceTask stage waypoint; no continuous sigma path",
        error="all physical substeps; contact intervals retained; no clipping",
        actual_torque="completed mj_step qfrc_actuator[:7], normalized by env.torque_limits",
        peak_speed="all-substep norm(J(q_post) dq_post) diagnostic/safety; no positive reward",
        terminal="55s finite-horizon or existing validator abort; strict_success gate unchanged",
        timeout_is_true_terminal=True,variable_episode_lengths=True,
        equivalence_caveat="variable horizons break RMSE ranking equivalence; discount breaks final peak-square equivalence",
        success_gate="result.strict_success; task_success also reported separately",
        previous_action_reset=[0.]*7,train_variants=[-4,-3,-2,-1],train_event_cycle=["all","all","ball","person","rod"],
        fixture_rule="seed + 100003*episode; no hidden +101*variant",
        scene="main 38caf31 combined_thick_corner_pillar_v4, corner placement, delayed ball2/person3/rod7 hold6",
        main_commit="38caf3152282df4963435bb65c11c93a1e4fffa5",
        source_sha256=hashes,max_wall_seconds=a.wall_seconds,
        checkpoint_selection="fixed step validation only; test not used to update or select",
        budget_caveat="finite compute-budget experiment; no guaranteed convergence claim"))
    started=time.monotonic()
    episode=int(resume_state["episode_index"]) if resume_state else 0
    step=int(resume_state["step"]) if resume_state else 0
    previous=resume_state["pending_transition"] if resume_state else None
    start_step=step
    next_boundary_checkpoint=(step//a.checkpoint_every+1)*a.checkpoint_every
    episode_return=0.;terms_sum={};episode_start_step=0;last_metrics={}
    stop_requested=False
    def stop_handler(*_):
        nonlocal stop_requested
        stop_requested=True
    signal.signal(signal.SIGUSR1,stop_handler)
    signal.signal(signal.SIGTERM,stop_handler)
    def reset():
        nonlocal obs,phi,episode_return,terms_sum,episode_start_step
        f=fixture(a.seed,episode)
        obs,info=env.reset(seed=f.pop("seed"),options=f)
        rewarder.reset();phi=info["interval"]["potential"]
        episode_return=0.;terms_sum={};episode_start_step=step
    def checkpoint(label):
        cp=out/label;agent.save(cp)
        replay_state=replay.save(cp/"replay.npz")
        dump(cp/"runner_state.json",dict(step=step,episode_index=episode,
            exploration_rng=exploration.bit_generator.state,replay=replay_state,
            pending_transition=previous,env_episode_index=env.episode,
            mid_episode=env.worker is not None,
            resume_format_version=1,run_definition=run_definition,source_sha256=hashes,
            resume_semantics="exact resume only at episode boundary; mid-episode checkpoints rejected",
            reward_state=vars(rewarder) | {"config":config.to_dict()}))
    reset()
    rows_file=out/"episode_summaries.jsonl"
    trace=(out/"control_audit.jsonl").open("w")
    try:
        while step<a.steps:
            policy_action=agent.sample_action(obs,previous_transition=previous,training=True)
            previous=None
            action=exploration.uniform(-1,1,7).astype(np.float32) if step<WARMUP_STEPS else policy_action
            next_obs,done,info=env.step_raw(action)
            iv=info["interval"]
            interval=IntervalMetrics(**{f.name:iv[f.name] for f in dataclasses.fields(IntervalMetrics)})
            result=info.get("evaluation")
            success=bool(result["strict_success"]) if done else False
            reason=(("strict_success" if success else result.get("abort_reason") or "finite_horizon_timeout")
                    if done else None)
            reward,terms=rewarder(interval,action,current_potential=phi,next_potential=iv["potential"],
                terminated=done,success=success,failure=done and not success,terminal_reason=reason,task_complete_before_interval=iv["task_complete_before_interval"])
            trace.write(json.dumps(dict(step=step,episode=episode,interval=iv,
                requested_action=action, reward=reward,reward_terms=terms),default=clean)+"\n")
            episode_return+=reward
            for k in ("task","progress","error","peak_torque","time","smooth","failure_continuation"):
                terms_sum[k]=terms_sum.get(k,0.)+terms[k]
            replay.add(observation=obs,action=action,reward=reward,terminated=float(done),
                truncated=0.,next_observation=next_obs)
            previous=dict(reward=reward,terminated=done,truncated=False)
            obs=next_obs;phi=iv["potential"];step+=1
            if step>=WARMUP_STEPS:
                for _ in range(a.utd):
                    m=agent.update(replay.sample(BATCH_SIZE))
                last_metrics={k:float(v) for k,v in m.items() if np.isscalar(v) and np.isfinite(v)}
            if done:
                row=dict(episode=episode,step=step,steps_in_episode=step-episode_start_step,
                    fixture=fixture(a.seed,episode),episode_return=episode_return,reward_terms=terms_sum,
                    task_success=bool(result["task_success"]),strict_success=success,
                    physical_valid=bool(result["physical_valid"]),placement_complete=bool(result["placement_complete"]),
                    final_stage=result["final_task_stage"],metrics=result["metrics"],
                    events=result["stats"]["events"],abort_reason=result["abort_reason"],
                    error_cost_total=rewarder.error_cost_total,actual_peak_torque_ratio=rewarder.peak_torque_ratio)
                with rows_file.open("a") as f:f.write(json.dumps(row,default=clean)+"\n")
                episode+=1
            if step%100==0 or done:
                trace.flush()
                dump(out/"progress.json",dict(status="training",step=step,updates=agent.updates,
                    episodes=episode,elapsed_s=time.monotonic()-started,
                    steps_per_s=(step-start_step)/max(1,time.monotonic()-started),
                    last_reward_terms=terms_sum,last_update=last_metrics,normalizers=agent.diagnostics()))
            if step%a.checkpoint_every==0:checkpoint(f"checkpoint_step_{step:07d}")
            if done and step>=next_boundary_checkpoint:
                checkpoint(f"checkpoint_boundary_{step:07d}")
                next_boundary_checkpoint=(step//a.checkpoint_every+1)*a.checkpoint_every
            if stop_requested or time.monotonic()-started>=a.wall_seconds or step>=a.steps or (getattr(a,"stop_after_step",None) is not None and step>=a.stop_after_step):
                checkpoint("checkpoint_final")
                dump(out/"COMPLETE.json",dict(status="step_budget_complete" if step>=a.steps else "wall_budget_checkpoint",
                    steps=step,updates=agent.updates,episodes=episode,elapsed_s=time.monotonic()-started,
                    convergence_claim=False,checkpoint="checkpoint_final"))
                break
            if done:reset()
    finally:
        trace.close();env.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--resume",type=Path,help="Resume only an episode-boundary checkpoint into a new output directory")
    p.add_argument("--stop-after-step",type=int,help="Optional absolute early checkpoint step; keeps original total-step learning-rate schedule")
    p.add_argument("--reward",choices=["office_task","metric","task_only"],required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--steps",type=int,default=100000)
    p.add_argument("--duration",type=float,default=55.)
    p.add_argument("--physics-dt",type=float,default=.0001)
    p.add_argument("--gamma",type=float,default=.995)
    p.add_argument("--utd",type=int,default=2)
    p.add_argument("--smooth",type=float,default=.005)
    p.add_argument("--wall-seconds",type=float,default=18000)
    p.add_argument("--checkpoint-every",type=int,default=10000)
    train(p.parse_args())
