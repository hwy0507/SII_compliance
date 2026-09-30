"""Independent reference-controller revisions on a frozen panel48 protocol."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--base-output',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=3)
    parser.add_argument('--duration',type=float)
    parser.add_argument('--methods',nargs='+',choices=('impedance','admittance'),default=['impedance','admittance'])
    parser.add_argument('--first-fixture-only',action='store_true')
    parser.add_argument('--impedance-config',type=json.loads,default={})
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Choose a fresh output directory')
    root=Path(__file__).resolve().parents[1]
    protocol=json.loads((args.base_output/'protocol.json').read_text())
    if protocol['observation']!='proprio48':raise ValueError('Requires frozen48 protocol')
    fixtures=protocol['fixtures'][:1] if args.first_fixture_only else protocol['fixtures']
    configs={'admittance':dict(stiffness=95.,rot_stiffness=4.,mass=.55,inertia=.065,zeta=1.)}
    if 'impedance' in args.methods:
        from run_panel_impedance_reference_20260923 import ReferenceImpedanceConfig
        configs['impedance']=asdict(ReferenceImpedanceConfig(**args.impedance_config))
    args.output.mkdir(parents=True)
    manifest=dict(scope='development reference-controller revision; no tuning selection/test claim',
                  base_protocol_sha256=hashlib.sha256((args.base_output/'protocol.json').read_bytes()).hexdigest(),
                  fixture_list=fixtures, duration_override=args.duration, configurations=configs,
                  source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((root/'scripts').glob('*.py'))})
    (args.output/'protocol.json').write_text(json.dumps(manifest,indent=2))

    def run(method,fixture):
        jobdir=args.output/(method+'_reference')/str(fixture['seed'])
        jobdir.mkdir(parents=True)
        stem=jobdir/'rollout'/'rollout'
        old=json.loads((args.base_output/method/str(fixture['seed'])/'rollout.command.json').read_text())
        command=[sys.executable,str(root/'scripts'/f'run_panel_{method}_reference_20260923.py')]
        fields={old['argv'][i]:old['argv'][i+1] for i in range(2,len(old['argv']),2)}
        fields={k:v for k,v in fields.items() if not k.startswith('--classical-')}
        fields['--output']=str(stem)
        if args.duration is not None:fields['--duration']=str(args.duration)
        for key,value in fields.items():command.extend([key,value])
        prefix='--reference-' if method=='impedance' else '--classical-'
        for key,value in configs[method].items():command.extend([prefix+key.replace('_','-'),str(value)])
        environment=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                         MUJOCO_GL='egl',PANELS_ENABLED='1',UNIFIED_6D_TEACHER='1',
                         PRIMITIVE_RUNNER_PATH=str(root/'scripts/run_primitive_teacher_v7_20260917.py'),
                         CORE_VMC_CONFIG=json.dumps(protocol['vmc']),PANEL_CONFIG=json.dumps(old['panel']))
        (jobdir/'command.json').write_text(json.dumps(dict(argv=command,configuration=configs[method],
                 environment={k:environment[k] for k in ('PANELS_ENABLED','UNIFIED_6D_TEACHER','PRIMITIVE_RUNNER_PATH','CORE_VMC_CONFIG','PANEL_CONFIG')}),indent=2))
        with (jobdir/'run.log').open('w') as log:
            done=subprocess.run(command,cwd=root,env=environment,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
        if done.returncode or not stem.with_suffix('.json').exists():
            return dict(method=method+'_reference',fixture=fixture,execution_error=done.returncode,log=str(jobdir/'run.log'))
        result=json.loads(stem.with_suffix('.json').read_text())
        with np.load(stem.with_suffix('.npz')) as trace:
            delta=trace['position']-trace['target'];xyz=np.sqrt(np.mean(delta**2,axis=0))
            speed=np.linalg.norm(trace['twist'][:,:3],axis=1)
            assert trace['observation'].shape[1]==48
        contacts=result['panel_audit']['contacts'];external=[v for k,v in contacts.items() if k!='target_object_geom']
        upstream=any(set(v['bodies'])&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'} for v in external)
        return dict(method=method+'_reference',fixture=fixture,task_success=result['success'],
                    strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                    tracking_rmse_xyz_m=xyz.tolist(),tracking_rmse_3d_m=float(np.linalg.norm(xyz)),
                    control_step_applied_torque_peak_nm=result['peak_torque_nm'],speed_peak_25hz_mps=float(speed.max()),
                    speed_p95_25hz_mps=float(np.percentile(speed,95)),max_penetration_mm=1000*max(v['max_penetration_m'] for v in external),
                    peak_contact_force_n=max(v['peak_point_force_n'] for v in external),rod_contact_s=contacts['push_rod_geom']['duration_s'],
                    upstream=upstream,teacher_called=result['teacher_called'],result=str(stem.with_suffix('.json')))

    rows=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run,m,f) for m in args.methods for f in fixtures]
        for future in as_completed(futures):
            rows.append(future.result());(args.output/'results.json').write_text(json.dumps(rows,indent=2))
            print(json.dumps(dict(completed=len(rows),total=len(futures),last=rows[-1])),flush=True)
    (args.output/'FINAL_RESULT.json').write_text(json.dumps(dict(completed=len(rows),rows=rows),indent=2))


if __name__=='__main__':main()
