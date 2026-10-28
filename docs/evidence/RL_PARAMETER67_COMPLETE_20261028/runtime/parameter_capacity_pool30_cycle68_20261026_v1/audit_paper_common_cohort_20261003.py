"""Verify same world, initial observation and physics code across full cohorts."""
import argparse,json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now

COMMON_ARGUMENTS=('seed','duration','dt','ball_speed','ball_launch_time_s','person_stroke','rod_stroke',
    'person_start','rod_start','rod_hold','events','task','corner_placement','planned_hand_corner','unexpected_edge',
    'allow_lateral_rejoin','observer_friction_velocity_scale','interaction_schedule','tool_contact')
PHYSICS_FILES=('fr3_scene.py','wbc_velocity_residual_env.py','wbc_velocity_residual_core.py',
    'run_contact_transfer_20260916.py','fixed_panda_wbc.py','office_task_v4_20260917.py','run_benchmark.py')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--phases',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    rows=[];reference=None;initial=None
    for phase in a.phases:
        batch=json.loads((phase/'execution.json').read_text());assert batch['status']=='complete'
        for entry in batch['rows']:
            run=phase/entry['name'];record=json.loads((run/'execution.json').read_text())
            result=json.loads((run/'rollout.json').read_text());assert record['status']=='complete'
            common={k:result['arguments'].get(k) for k in COMMON_ARGUMENTS}
            hashes={k:record['source_sha256']['scripts/'+k] for k in PHYSICS_FILES}
            for key,digest in hashes.items():assert sha(phase/'source/scripts'/key)==digest
            binary=sha(run/'rollout.mjb');assert binary==result['model_sha256']
            with np.load(run/'rollout.npz') as z:obs=z['observation'][0].copy()
            row=dict(run=str(run.resolve()),common_arguments=common,physics_source_sha256=hashes,
                     model_sha256=binary,python=record['python'],host=record['host'],mujoco=record['mujoco'],
                     execution_sha256=sha(run/'execution.json'),trace_sha256=sha(run/'rollout.npz'),
                     task_success=result['task_success'],strict_success=result['strict_success'],
                     full_horizon=result['full_task_horizon_completed'],abort_reason=result.get('abort_reason'))
            signature={k:row[k] for k in ('common_arguments','physics_source_sha256','model_sha256','python','host','mujoco')}
            if reference is None:reference=signature;initial=obs
            assert signature==reference, 'Common cohort mismatch: '+str(run)
            np.testing.assert_array_equal(obs,initial)
            row['initial_observation_exact_match']=True;rows.append(row)
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),rows=rows,common=reference,
        initial_observation=initial.tolist(),passed=True,
        limitation='Checks common numerical runtime and task configuration. Does not equalize training exposure or guarantee matching contacts after policies diverge; failures and aborts retained.'))
    print(json.dumps(dict(rows=len(rows),passed=True)))

if __name__=='__main__':main()
