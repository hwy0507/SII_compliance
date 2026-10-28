"""Train-only counterfactual reward audit; no learning or policy selection.

Separate original Task completion from a continuous penalty for exceeding the
UNCHANGED .2mm external penetration gate. This is a proposed training objective,
not an evaluation change or proof that RL will learn. Research-only physical
channels never enter the canonical48 actor. All failures remain in the census.
"""
import argparse
from pathlib import Path
import math
import sys
import numpy as np
from office_v7_uniform24_20261008 import read,write,sha,now

GATE_M=.0002
SAFETY_WEIGHT=20.


def safety_potential(penetration_m):
    if not math.isfinite(penetration_m) or penetration_m < 0:
        raise ValueError('Invalid physical penetration')
    excess=max(0.,penetration_m/GATE_M-1.)
    return excess/(1.+excess)


def terminal_task_adjustment(task,strict):
    assert not strict or task
    # Original terminal is +20 for Task AND Strict, -20 otherwise.
    # Proposed terminal is +20 for Task, -20 otherwise. Safety is separate.
    return 40. if task and not strict else 0.


def inspect(segment):
    from inspect_local_rl_progress_20261009 import objective_information
    old=objective_information(segment)
    state=read(segment/'execution.json');spec=read(segment/'PROTOCOL.json')
    assert spec['reward']['mode']=='office_task'
    root=segment.parent;protocol=read(root/'PROTOCOL.json')
    conditions=read(root/'CONDITIONS.json')['conditions']
    train={c['id'] for c in conditions if c['role']=='train'}
    assert all(r['condition_id'] in train for r in state['rows'])
    gamma=spec['reward']['gamma'];episodes=[]
    for row,oldrow in zip(state['rows'],old['episodes'],strict=True):
        run=Path(row['run']);audit=read(run/'AUDIT.json')
        assert sha(run/'rollout.npz')==row['trace_sha256']
        assert sha(run/'AUDIT.json')==row['audit_sha256']
        research_path=run/'research_substeps.npz'
        assert sha(research_path)==read(run/'research_channels.json')['telemetry_sha256']
        with np.load(research_path) as data:p=data['external_penetration_m'].copy()
        assert np.isfinite(p).all() and np.min(p)>=0
        np.testing.assert_allclose(1000*p.max(),audit['penetration_mm'],rtol=1e-8,atol=1e-8)
        ivs=read(run/'RL_INTERVALS.json');assert ivs[0] is None
        assert len(ivs)==row['steps']+1
        offset=0;peak=0.;discounted=0.;undiscounted=0.;elapsed=0.
        for index,iv in enumerate(ivs[1:]):
            end=offset+iv['substeps'];maximum=max(peak,float(p[offset:end].max()))
            penalty=SAFETY_WEIGHT*(safety_potential(maximum)-safety_potential(peak))
            assert penalty>=0
            discounted+=gamma**index*penalty;undiscounted+=penalty
            peak=maximum;offset=end;elapsed+=iv['elapsed_s']
        assert offset==len(p)
        # Early failure cannot improve the return by avoiding future safety
        # exposure. A conservative remaining peak budget is charged at terminal.
        remaining=(SAFETY_WEIGHT*(1.-safety_potential(peak))
                   if elapsed<protocol['duration_s']-1e-7 else 0.)
        discount=gamma**(row['steps']-1)
        adjustment=terminal_task_adjustment(oldrow['task'],oldrow['strict'])
        proposed=oldrow['discounted_return']+discount*(adjustment-remaining)-discounted
        episodes.append(dict(condition=row['condition_id'],episode=row['episode'],steps=row['steps'],
            group=('random_warmup' if row['step_after']<=spec['warmup_steps'] else
                   'learned_behavior' if row['step_before']>=spec['warmup_steps'] else 'mixed'),
            task=oldrow['task'],strict=oldrow['strict'],stage=audit['stage'],
            physical_seconds=elapsed,penetration_mm=1000*peak,
            original_discounted_return=oldrow['discounted_return'],
            proposed_discounted_return=proposed,terminal_task_adjustment=adjustment,
            proposed_safety_cost_undiscounted=undiscounted,early_failure_safety_continuation=remaining,
            trace_sha256=row['trace_sha256'],research_sha256=sha(research_path),
            intervals_sha256=sha(run/'RL_INTERVALS.json')))
    return dict(segment=str(segment),training_protocol_sha256=sha(segment/'PROTOCOL.json'),
        execution_sha256=sha(segment/'execution.json'),episodes=episodes,
        old_return_std=float(np.std([e['original_discounted_return'] for e in episodes])),
        proposed_return_std=float(np.std([e['proposed_discounted_return'] for e in episodes])))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    roots=[a.root/'direct_office_task_smoke',a.root/'direct_office_task_segment011k']
    result=dict(created_utc=now(),source_sha256=sha(__file__),new_physics_steps=0,
        new_gradient_updates=0,development_or_final_reads=0,actor_input_changes=False,
        proposal=dict(task_terminal_success=20,task_terminal_failure=-20,
            safety_weight=SAFETY_WEIGHT,external_gate_m=GATE_M,
            safety_cost='20 * increments of excess/(1+excess), excess=max(0,pmax/.0002-1)',
            remainder='At early termination charge unused worst-case safety peak budget',
            shaping='Original potential-based shaping, time cost and terminal cancellation unchanged'),
        limitation='Counterfactual returns of existing behavior only. Not a trained policy, '
            'no convergence or causal improvement claim; task success still separate from strict success.',
        segments=[inspect(path) for path in roots])
    write(a.output,result)
    for row in result['segments']:
        print(Path(row['segment']).name,'return std',row['old_return_std'],'->',row['proposed_return_std'])


if __name__=='__main__':main()
