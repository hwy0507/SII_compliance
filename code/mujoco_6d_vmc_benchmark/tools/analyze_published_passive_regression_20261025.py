"""Read-only comparison of one observed training success and later same-case failures.

Does not infer a fixed successful checkpoint, causality, or independent safety
acceptance from changing-policy training rollouts. No physics or updates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from diagnose_published_value_bound_20261025 import audit_episode


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(args):
    p=json.loads(args.registration.read_text())
    if sha(__file__)!=p['source_sha256']:raise ValueError('Source drift')
    results={};series={};models=set();plans=set();fixtures=set()
    for entry in p['episodes']:
        root=Path(entry['path'])
        for name,expected in entry['files'].items():
            if sha(root/name)!=expected:raise ValueError('Frozen episode changed')
        transitions=Path(entry['transitions'])
        if sha(transitions)!=entry['transitions_sha256']:raise ValueError('Transition snapshot changed')
        rows=[json.loads(line) for line in transitions.read_text().splitlines()]
        if len(rows)!=1375 or any(r['cycle']!=entry['cycle'] or r['condition']!=p['condition'] for r in rows):
            raise ValueError('Incomplete or wrong training episode')
        audit=audit_episode(rows,.9995,5.)
        outcome=json.loads((root/'rollout.json').read_text());terminal=json.loads((root/'TERMINAL.json').read_text())
        adapter=json.loads((root/'ADAPTER.json').read_text())
        if outcome['abort_reason'] or not outcome['full_task_horizon_completed'] or not outcome['physical_valid']:
            raise ValueError('Expected valid full-horizon observational cases')
        model=sha(root/'rollout.mjb');models.add(model);plans.add(sha(root/'rollout.plan.json'))
        fixtures.add(adapter['fixture']['physical_config_sha256'])
        if model!=outcome['model_sha256'] or model!=terminal['model_sha256']:
            raise ValueError('Model receipt mismatch')
        if adapter['arguments']['dt']!=.00005:raise ValueError('Physics dt changed')
        intervals=[json.loads(line) for line in (root/'actor_intervals.jsonl').read_text().splitlines()]
        if len(intervals)!=1375:raise ValueError('Missing actor interval')
        action=np.array([r['action'] for r in intervals]);context=np.array([r['context'] for r in rows])
        arrays=np.load(root/'rollout.npz')
        time=arrays['time'];hand=arrays['hand'];payload=arrays['object_position'];potential=np.array([r['reward_terms']['next_potential'] for r in rows])
        if action.shape!=(1375,7) or arrays['observation'].shape!=(1375,48):raise ValueError('Actor contract changed')
        if not np.allclose(np.diff(time),.04,rtol=0,atol=1e-7):raise ValueError('Sampling period changed')
        numeric=('progress','occupancy','time','comfort_torque','contact_force','torque_slew','penetration','peak_torque','terminal','failure_tail','completion_efficiency')
        terms={k:sum(r['reward_terms'][k] for r in rows) for k in numeric}
        reward=sum(r['reward'] for r in rows)
        if not np.isclose(sum(terms.values()),reward,rtol=0,atol=1e-8):raise ValueError('Episode reward mismatch')
        stage_durations={};events=[dict(stage='approach',time_s=0.)]+outcome['task_events']
        for i,event in enumerate(events):
            end=events[i+1]['time_s'] if i+1<len(events) else 55.
            stage_durations[event['stage']]=stage_durations.get(event['stage'],0.)+end-event['time_s']
        result=dict(cycle=entry['cycle'],reward=reward,reward_terms=terms,task_success=outcome['task_success'],
            strict_success=outcome['strict_success'],completion_time_s=terminal['completion_time_s'],
            final_task_stage=outcome['final_task_stage'],task_events=outcome['task_events'],stage_durations_s=stage_durations,
            max_lift_m=outcome['max_lift_m'],placement_error_xy_m=outcome['placement_error_xy_m'],
            final_potential=float(potential[-1]),maximum_potential=float(potential.max()),discounted_reward=audit,
            context_mean=float(context.mean()),context_min=float(context.min()),context_max=float(context.max()),
            command_mean=action.mean(axis=0).tolist(),command_mean_first10s=action[time<=10].mean(axis=0).tolist(),
            model_sha256=model,plan_sha256=sha(root/'rollout.plan.json'),actor_input_dimension=48,control_dt_s=.04)
        results[str(entry['cycle'])]=result;series[entry['cycle']]=(time,potential,action,hand,payload)
    if len(models)!=1 or len(plans)!=1 or len(fixtures)!=1:raise ValueError('Physical case or nominal plan changed')
    args.output.mkdir(exist_ok=False)
    report=dict(registration_sha256=sha(args.registration),condition=p['condition'],methods=results,
        identical_model_plan_fixture=True,new_physics=0,optimizer_updates=0,
        limitation='Single condition selected because it had observed training success; changing policies and stochastic actions, no causal or fixed-policy comparison. Worker success receipts are not a fresh independent acceptance audit.')
    (args.output/'ANALYSIS.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for cycle,(time,potential,action,hand,payload) in series.items():
        label=f'cycle{cycle}'
        axes[0,0].plot(time,potential,label=label)
        axes[0,1].plot(time,payload[:,2],label=label)
        axes[1,0].plot(time,np.linalg.norm(payload[:,:2]-np.array([.69,-.31]),axis=1),label=label)
        axes[1,1].plot(time,action[:,0],alpha=.7,label=label)
    for ax,title in zip(axes.flat,['Payload shaping potential','Payload height (m)','Payload XY distance to placement (m)','Mixed direct slowdown command, before common filter']):
        ax.set_title(title);ax.set_xlabel('Time (s)');ax.legend();ax.grid(alpha=.2)
    fig.suptitle('Same passive0900 training condition: selected historical success and later failures')
    fig.savefig(args.output/'passive_regression.png',dpi=160);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
