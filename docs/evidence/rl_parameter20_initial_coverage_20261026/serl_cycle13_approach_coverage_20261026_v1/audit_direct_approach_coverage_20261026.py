"""Read-only approach coverage and discounted reward decomposition of formal13.

Uses existing physical journals and sampled rollout telemetry, never new physics,
reward/actor changes, demonstration injection, or optimizer updates. Logged pose
errors use the current waypoint after task.update; threshold overlap below is
not an independent reconstruction of the task state machine or dwell gate.
"""
from pathlib import Path
import argparse
import collections
import hashlib
import json
import os
import sys
import time


def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main(args):
    os.sched_setaffinity(0, {52})
    import numpy as np
    B = args.base
    source = B/'runtime/source_train17_clock/source'
    sys.path.insert(0, str(source/'tools'))
    from spt_rl_reward_20261025 import SPTReward, CONFIG
    reg = json.loads(args.registration.read_text())
    assert reg['new_physics'] == reg['optimizer_updates'] == 0
    assert reg['direct_cycle'] == 13 and reg['parameter_cycle'] == 18
    for ref in reg['sources']:
        assert sha(ref['path']) == ref['sha256']
    episodes = []; inputs = []
    sets = [('direct',13,'serl_multistep_batch65536_cycle13_20261026_v1/direct')]
    sets += [(m,18,f'parameter_batch65536_cycle18_20261026_v1/{m}/train') for m in ['impedance','admittance','vmc']]
    for method, cycle, path in sets:
        run = B/'runs'/path
        rows = [json.loads(l) for l in (run/'episodes.jsonl').read_text().splitlines()]
        assert len(rows) == 30 and {r['cycle'] for r in rows} == {cycle}
        for row in rows:
            folder = Path(row['episode_path']); raw = folder/'rollout.npz'
            terminal_path = folder/'TERMINAL.json'; terminal = json.loads(terminal_path.read_text())
            with np.load(raw, allow_pickle=False) as x:
                stage = x['stage']; mask = stage == 0
                assert len(stage) == row['steps'] == 1375
                pe = x['task_position_error_m'][mask]; re = x['task_rotation_error_rad'][mask]; speed = x['task_speed_mps'][mask]
                assert len(pe) and all(np.isfinite(a).all() for a in [pe,re,speed])
                position = pe < .012; rotation = re < .12; slow = speed < .025
                overlap = position & rotation & slow
                longest = current = 0
                for flag in overlap:
                    current = current+1 if flag else 0; longest = max(current,longest)
                a = x['applied_action'][mask]
                result = dict(method=method,condition=row['condition'],cycle=cycle,task=row['task_success'],strict=row['strict_success'],final_stage=terminal['result']['final_task_stage'],approach_rows=int(mask.sum()),position_min_m=float(pe.min()),rotation_min_rad=float(re.min()),position_median_m=float(np.median(pe)),rotation_median_rad=float(np.median(re)),speed_median_mps=float(np.median(speed)),position_threshold_fraction=float(position.mean()),rotation_threshold_fraction=float(rotation.mean()),speed_threshold_fraction=float(slow.mean()),joint_threshold_fraction=float(overlap.mean()),longest_sampled_overlap_rows=longest,public0_mean=float(a[:,0].mean()),translation_residual_abs_mean=float(np.abs(a[:,1:4]).mean()),rotation_residual_abs_mean=float(np.abs(a[:,4:]).mean()))
                if method=='direct':assert np.all(stage==0)
            if method == 'direct':
                journal_path=folder/'actor_intervals.jsonl';journal=[json.loads(l) for l in journal_path.read_text().splitlines()]
                assert len(journal)==1375
                reward=SPTReward();discounted=collections.defaultdict(float);undiscounted=collections.defaultdict(float)
                phi=np.array([j['payload_potential'] for j in journal]+[terminal['payload_potential']])
                for i,j in enumerate(journal):
                    done=i==len(journal)-1;nxt=terminal if done else journal[i+1]
                    value,terms=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=done,task_success=False,strict_success=False)
                    for k in ['progress','occupancy','time','comfort_torque','contact_force','torque_slew','penetration','peak_torque','terminal','failure_tail']:
                        undiscounted[k]+=terms[k];discounted[k]+=CONFIG['gamma']**i*terms[k]
                assert abs(sum(undiscounted.values())-row['reward'])<1e-8
                assert abs(discounted['progress']+5*phi[0])<1e-10
                result.update(phi_initial=float(phi[0]),phi_max=float(phi.max()),phi_final=float(phi[-1]),phi_mean=float(phi.mean()),discounted_terms=dict(discounted),undiscounted_terms=dict(undiscounted),discounted_return=sum(discounted.values()),pbrs_telescoping_error=abs(discounted['progress']+5*phi[0]))
                inputs.append(dict(path=str(journal_path),sha256=sha(journal_path)))
            inputs.extend([dict(path=str(raw),sha256=sha(raw)),dict(path=str(terminal_path),sha256=sha(terminal_path))]);episodes.append(result)
    summaries={}
    for method,_,_ in sets:
        rows=[r for r in episodes if r['method']==method]
        numeric=['approach_rows','position_min_m','rotation_min_rad','position_median_m','rotation_median_rad','speed_median_mps','position_threshold_fraction','rotation_threshold_fraction','speed_threshold_fraction','joint_threshold_fraction','longest_sampled_overlap_rows','public0_mean','translation_residual_abs_mean','rotation_residual_abs_mean']
        summary={k:float(np.mean([r[k] for r in rows])) for k in numeric}
        summary.update(conditions=30,task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),final_stages=dict(collections.Counter(r['final_stage'] for r in rows)))
        if method=='direct':
            summary['discounted_terms_mean']={k:float(np.mean([r['discounted_terms'][k] for r in rows])) for k in rows[0]['discounted_terms']}
            summary['potential']={k:float(np.mean([r[k] for r in rows])) for k in ['phi_initial','phi_max','phi_final','phi_mean']}
        summaries[method]=summary
    report=dict(passed=True,time=time.time(),summaries=summaries,episodes=episodes,inputs=inputs,new_physics=0,optimizer_updates=0,weights_saved=False,limitation='Descriptive30-condition full-cycle audit. Parameter18 and Direct13 differ in policy/history, not a causal control. Waypoint errors are logged after task.update; sampled threshold overlap is not exact readiness/dwell replay. Discounted PBRS telescopes for complete failure, but occupancy remains potential-dependent; this does not mean the entire reward is constant or that changing frozen reward is authorized.',convergence_claim=False)
    (args.output/'REVIEW.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['base','registration','output']:p.add_argument('--'+name,type=Path,required=True)
    main(p.parse_args())
