"""Posthoc configuration audit; never uses performance to choose a fixture/model."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from canonical48_rl_env_20260923 import save_json, sha


def audit(output, assets):
    rows = {}
    for split, directory in [('train','train_rod'),('validation','validation_front')]:
        historical = json.loads((assets/directory/'rollout.json').read_text())
        for policy in ('zero','ppo'):
            path = output/'eval'/split/policy/'episode_00000'/'rollout.json'
            current = json.loads(path.read_text())
            argument_differences = {k:dict(historical=v,current=current['arguments'].get(k))
                for k,v in historical['arguments'].items() if v!=current['arguments'].get(k)}
            expected_argument_changes = {'output','menagerie','model'}
            static_keys = ('nq','nv','nu','native_ccd_enabled','physical_panels','contact_names','initial_overlap')
            checks = dict(arguments_only_expected_changes=set(argument_differences)<=expected_argument_changes,
                scene_equal=historical['scene']==current['scene'],
                controller_config_equal=historical['controller_6d_config']==current['controller_6d_config'],
                physics_timestep_equal=historical['simulation_timestep_s']==current['simulation_timestep_s'],
                **{f'panel_audit_{k}_equal':historical['panel_audit'].get(k)==current['panel_audit'].get(k)
                   for k in static_keys})
            h_contract,c_contract=historical['experiment_contract'],current['experiment_contract']
            for key in ('persistent_rod','lift_goal_z_m','lift_nominal_scale'):
                checks[f'{key}_equal']=h_contract[key]==c_contract[key]
            restored_panel = dict(h_contract['panel_config'],rod_height_m=historical['scene']['push_height'])
            checks['panel_config_only_explicit_height_restoration']=restored_panel==c_contract['panel_config']
            rows[f'{split}/{policy}']=dict(checks=checks,passed=all(checks.values()),
                argument_differences=argument_differences,
                original_observation_contract=historical['contract'],current_observation_contract=current['contract'],
                original_reference=h_contract['reference'],current_reference=c_contract['reference'],
                historical_result_sha256=sha(assets/directory/'rollout.json'),current_result_sha256=sha(path))
    report = dict(rows=rows,all_checks_passed=all(r['passed'] for r in rows.values()),
        historical_runtime_byte_equivalence_proven=False,
        historical_wbc_safety_solver_full_config_available=False,
        limitations='Historical raw source rollouts used contact45 before canonical48 data conversion. Current runtime constructs48 causally. Static config agreement is not historical dynamics parity.')
    save_json(output/'RECONSTRUCTION_AUDIT.json',report)
    if not report['all_checks_passed']:
        raise AssertionError('Unexpected reconstructed configuration drift')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--assets',type=Path,default=ROOT/'outputs/canonical_rl_assets_20260923')
    args=parser.parse_args()
    print(json.dumps(audit(args.output,args.assets),indent=2))
