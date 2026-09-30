"""Train-only diagnostics and original VMC control for the reconstructed rod fixture."""
from __future__ import annotations
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import numpy as np
import psutil
from canonical48_rl_env_20260923 import load_fixture_specs,runtime_argv,save_json,sha,reward_from_transition,evaluation_summary


def trace_diagnostics(folder, terminal=True):
    with np.load(folder/'actor_trace.npz',allow_pickle=False) as data:
        obs,actions,phase=(data[k].copy() for k in ('observation','action','phase_reward_metadata'))
    result=json.loads((folder/'rollout.json').read_text()) if terminal else None
    totals={}
    phase_totals={}
    for t,action in enumerate(actions):
        last=t==len(actions)-1
        next_obs=obs[t] if last else obs[t+1]
        next_phase=result['final_stage'] if last and result else phase[t] if last else phase[t+1]
        reward,terms=reward_from_transition(next_obs,action,actions[t-1] if t else np.zeros(7),
            next_phase-phase[t],result if last else None)
        for key,value in terms.items():
            totals[key]=totals.get(key,0.)+value
        key=str(int(phase[t]))
        phase_totals[key]=phase_totals.get(key,0.)+reward
    return dict(samples=len(actions),reward_terms=totals,reward_total=sum(totals.values()),
        reward_by_phase=phase_totals,phase_counts={str(int(p)):int(np.sum(phase==p)) for p in np.unique(phase)},
        slowdown_mean=float(actions[:,0].mean()),slowdown_zero_fraction=float(np.mean(actions[:,0]==0)),
        slowdown_one_fraction=float(np.mean(actions[:,0]==1)),
        action_mean=actions.mean(axis=0),action_std=actions.std(axis=0),
        final_48d_pose_error=obs[-1,20:26],final_estimated_force_norm=float(np.linalg.norm(obs[-1,39:42])),
        task_success=result['success'] if result else None,
        final_stage=result['final_stage'] if result else None,
        terminal_shaping_uses_last_actor_observation=True,
        final_shaping_observation_age_s=.04,
        final_terminal_labels_from_post_last_physics_step=True)


def run_vmc(spec,assets,output):
    output.mkdir(parents=True,exist_ok=False)
    argv=runtime_argv(spec,output/'rollout',assets/'menagerie')
    index=argv.index('--model')
    del argv[index:index+2]
    env=dict(os.environ)
    for key in list(env):
        if key.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')):
            del env[key]
    env.update({k:spec['command']['environment'][k] for k in ('PANEL_CONFIG','CORE_VMC_CONFIG','PANELS_ENABLED')})
    panel=json.loads(env['PANEL_CONFIG']);panel['rod_height_m']=spec['historical_scene']['push_height']
    env.update(PANEL_CONFIG=json.dumps(panel),UNIFIED_6D_TEACHER='1',
        PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'),
        SKIP_MODEL_ARCHIVE='1',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    command=[sys.executable,str(ROOT/'scripts/run_panel_push_20260920.py'),*argv]
    save_json(output/'command.json',dict(argv=command,environment={k:env[k] for k in (
        'PANEL_CONFIG','CORE_VMC_CONFIG','PANELS_ENABLED','UNIFIED_6D_TEACHER','PRIMITIVE_RUNNER_PATH')},
        source_row=spec['row'],source_sha256=sha(ROOT/'scripts/run_panel_push_20260920.py'),
        policy='original six-D VMC; model argument absent; no action override'))
    start=time.time();peak_rss=0.
    with (output/'runner.log').open('w') as log:
        process=subprocess.Popen(command,env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        try:
            while process.poll() is None:
                rss=psutil.Process(process.pid).memory_info().rss/2**30
                peak_rss=max(peak_rss,rss)
                if rss>7 or psutil.virtual_memory().available<2.5*2**30:
                    raise MemoryError('VMC resource guard')
                if time.time()-start>900:
                    raise TimeoutError('VMC control exceeded15 minutes')
                time.sleep(.5)
            if process.returncode:
                raise RuntimeError(f'VMC control exit {process.returncode}')
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:process.kill();process.wait()
    result=json.loads((output/'rollout.json').read_text())
    if not result['teacher_called'] or result['contract']!='proprio48_action7_6d_v1':
        raise AssertionError('VMC call/contract incorrect')
    if result['scene']!=spec['historical_scene'] or result['panel_audit']['physical_panels']!=spec['historical_physical_panels']:
        raise AssertionError('VMC fixture configuration changed')
    return dict(**evaluation_summary(result,spec),elapsed_s=time.time()-start,peak_rss_gib=peak_rss,
        teacher_called=result['teacher_called'],source_row=spec['row'])


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--pilot',type=Path,default=ROOT/'outputs/canonical48_ppo_pilot_20260923_r1')
    parser.add_argument('--assets',type=Path,default=ROOT/'outputs/canonical_rl_assets_20260923')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
    args.output=args.output.resolve();args.output.mkdir(parents=True,exist_ok=False)
    specs,_=load_fixture_specs(args.assets)
    report=dict(scope='train rod only; no new validation-dependent design decisions',
        traces={key:trace_diagnostics(args.pilot/folder) for key,folder in (
            ('train_stochastic','train/episode_00000'),('zero','eval/train/zero/episode_00000'),
            ('ppo640_deterministic','eval/train/ppo/episode_00000'))},
        initial_slowdown=dict(gaussian_mean_at_zero_normalized_observation=0.,
            gaussian_std=math.exp(-2),clip_lower_probability=.5,
            expected_clipped_mean=math.exp(-2)/math.sqrt(2*math.pi),
            upper_clip_probability_negligible=True,
            interpretation='SB3 Gaussian plus Box clipping is standard; zero is no slowdown. Positive half-normal initial slowdown is an action-parameterization bias, not a bridge mismatch.'),
        transition_review=dict(nonterminal='reward uses next published48 observation after previous action physics and next task.update',
            terminal='post-step task/safety outcome; shaping reuses last actor observation40ms old, no terminal bootstrap',
            actor_privileged_fields=[],critic_privileged_fields=[],
            dense_shaping_present=True,terminal_success_signal_sparse=True,
            finite_horizon='24s evaluation endpoint is task terminal, deliberately terminated=True',
            reward_version_changed=False))
    save_json(args.output/'diagnosis.json',report)
    report['vmc_control']=run_vmc(specs['train'],args.assets,args.output/'vmc_control')
    save_json(args.output/'diagnosis.json',report)
    save_json(args.output/'COMPLETE.json',dict(status='complete',vmc=report['vmc_control']))


if __name__=='__main__':main()
