"""Fresh matched panel-push VMC/impedance/admittance development matrix."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--menagerie', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--unified48', action='store_true')
    parser.add_argument('--mlp', type=Path)
    parser.add_argument('--esn', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Use a fresh output directory')
    args.output.mkdir(parents=True)
    root = Path(__file__).resolve().parents[1]
    reference = json.loads(args.reference.read_text())['arguments']
    panel = dict(layout='raised_hand_rim', pad_bottom_z=.55, pad_top_z=.71,
                 pad_lower_y=-.15, pad_upper_y=-.085, front_inner_x=.595,
                 back_inner_x=.500, pad_thickness=.015, end_effector_only=False,
                 rod_height_m=.58, workstation=True)
    vmc = dict(stiffness_6d=[520,360,1400,12,10,14], damping_6d=[32,27,62,3,2.7,3.3],
               mass_6d=[.5,.5,.8,.06,.06,.08], wrench_limit_6d=[35,35,50,3,3,3],
               deadband_6d=[.2,.2,.2,.03,.03,.03], velocity_limit_6d=[.12,.12,.16,.55,.55,.65],
               offset_limit_6d=[.18,.18,.18,.35,.35,.35], action_limit_6d=[.16,.16,.2,.6,.6,.6],
               offset_tracking_gain_6d=1.4, filter_tau=.04, axis_rotation_rpy=[.35,0,-.25])
    fixtures = [dict(seed=9300, push_angle=-.15, push_height=.575, payload_mass=.085),
                dict(seed=9301, push_angle=-.05, push_height=.580, payload_mass=.100),
                dict(seed=9302, push_angle=.10, push_height=.585, payload_mass=.115)]
    models = {name:path for name,path in [('mlp',args.mlp),('esn',args.esn)] if path is not None}
    if models and not args.unified48:
        raise ValueError('Current matched checkpoints require --unified48')
    manifest = dict(scope='fresh paired development panel-push; no historical score reuse',
                    observation='proprio48' if args.unified48 else 'contact45',
                    models={name:dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                            for name,path in models.items()},
                    fixtures=fixtures, panel=panel, vmc=vmc, reference=reference,
                    source_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted((root/'scripts').glob('*.py'))})
    (args.output/'protocol.json').write_text(json.dumps(manifest, indent=2))

    def run(method, fixture):
        stem = args.output / method / str(fixture['seed']) / 'rollout'
        stem.parent.mkdir(parents=True)
        params = {k:v for k,v in reference.items() if v is not None and k not in
                  ('output','render','settle_only','model')}
        params.update(fixture, scene='push', event_stage='loaded_lift', duration=24.,
                      menagerie=str(args.menagerie), teacher_profile='memory',
                      teacher_force_source='estimated', mixture=0.)
        classical = method in ('impedance','admittance')
        filename = 'run_panel_classical_adapter_20260923.py' if classical else 'run_panel_push_20260920.py'
        command = [sys.executable, str(root/'scripts'/filename), '--output', str(stem)]
        if classical:
            command += ['--classical-controller', method]
        elif method in models:
            command += ['--model', str(models[method])]
        if method == 'admittance':
            command += ['--classical-stiffness','95','--classical-rot-stiffness','4',
                        '--classical-mass','.55','--classical-inertia','.065']
        for key, value in params.items():
            command += ['--'+key.replace('_','-'), str(value)]
        env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1',
                   MUJOCO_GL='egl', PANELS_ENABLED='1', UNIFIED_6D_TEACHER='1' if args.unified48 else '0',
                   PRIMITIVE_RUNNER_PATH=str(root/'scripts/run_primitive_teacher_v7_20260917.py'),
                   CORE_VMC_CONFIG=json.dumps(vmc), PANEL_CONFIG=json.dumps(dict(panel, rod_height_m=fixture['push_height'])))
        (stem.with_suffix('.command.json')).write_text(json.dumps(dict(argv=command, panel=json.loads(env['PANEL_CONFIG'])), indent=2))
        with stem.with_suffix('.log').open('w') as log:
            completed = subprocess.run(command, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        if completed.returncode or not stem.with_suffix('.json').exists():
            return dict(method=method, fixture=fixture, execution_error=completed.returncode)
        result = json.loads(stem.with_suffix('.json').read_text())
        with np.load(stem.with_suffix('.npz'), allow_pickle=False) as trace:
            delta = trace['position'] - trace['target']
            speed = np.linalg.norm(trace['twist'][:,:3], axis=1)
            rmse_xyz = np.sqrt(np.mean(delta**2, axis=0))
        contacts = result['panel_audit']['contacts']
        external = [v for k,v in contacts.items() if k != 'target_object_geom']
        penetration = max(v['max_penetration_m'] for v in external)
        upstream = any(set(v['bodies']) & {'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external)
        return dict(method=method, fixture=fixture, task_success=result['success'],
                    panel_accepted=result.get('accepted_panel_demo',False),
                    strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                    tracking_rmse_xyz_m=rmse_xyz.tolist(), tracking_rmse_3d_m=float(np.linalg.norm(rmse_xyz)),
                    control_step_applied_torque_peak_nm=result['peak_torque_nm'],
                    speed_peak_25hz_mps=float(speed.max()), speed_p95_25hz_mps=float(np.percentile(speed,95)),
                    max_penetration_mm=1000*penetration,
                    peak_contact_force_n=max(v['peak_point_force_n'] for v in external),
                    rod_contact_s=contacts['push_rod_geom']['duration_s'], upstream=upstream,
                    teacher_called=result['teacher_called'], result=str(stem.with_suffix('.json')))

    rows=[]
    methods = ['vmc','impedance','admittance',*models]
    total = len(methods)*len(fixtures)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run,m,f) for m in methods for f in fixtures]
        for future in as_completed(futures):
            rows.append(future.result())
            (args.output/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps(dict(completed=len(rows),total=total,last=rows[-1])),flush=True)
    (args.output/'FINAL_RESULT.json').write_text(json.dumps(dict(completed=len(rows),rows=rows),indent=2))


if __name__ == '__main__':
    main()
