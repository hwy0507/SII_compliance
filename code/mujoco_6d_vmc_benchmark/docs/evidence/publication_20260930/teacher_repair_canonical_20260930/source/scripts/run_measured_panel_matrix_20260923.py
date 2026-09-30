"""Replay frozen panel jobs with one common physical-substep instrumentation."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


METHODS=('vmc','impedance','admittance','mlp','esn','impedance_k300_reference',
         'impedance_k900_reference','admittance_r2_reference')
ABLATIONS={'esn_no_x_yield':('esn','no_x_yield','policy'),
           'esn_lowpass_025':('esn','lowpass_025','policy'),
           'mlp_lowpass_025':('mlp','lowpass_025','policy'),
           'vmc_lowpass_025':('vmc','lowpass_025','teacher')}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--base-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--workers',type=int,default=4)
    p.add_argument('--methods',nargs='+',choices=(*METHODS,*ABLATIONS),default=list(METHODS))
    p.add_argument('--ablation-seed',type=int,default=9301)
    p.add_argument('--duration',type=float)
    p.add_argument('--first-fixture-only',action='store_true')
    p.add_argument('--disable-audit',action='store_true')
    args=p.parse_args()
    if not 1<=args.workers<=4:raise ValueError('Use one to four server workers')
    if args.output.exists():raise FileExistsError('Fresh output required')
    args.output.mkdir(parents=True)
    root=Path(__file__).resolve().parents[1]
    protocol=json.loads((args.base_root/'panel_matched48/protocol.json').read_text())
    fixtures=protocol['fixtures'][:1] if args.first_fixture_only else protocol['fixtures']
    plans=[]
    for method in args.methods:
        for fixture in fixtures:
            if method in ABLATIONS and fixture['seed']!=args.ablation_seed:continue
            seed=str(fixture['seed'])
            base_method=ABLATIONS[method][0] if method in ABLATIONS else method
            if base_method in METHODS[:5]:
                old_path=args.base_root/'panel_matched48'/base_method/seed/'rollout.command.json'
            else:
                folder,old_method={'impedance_k300_reference':('panel_reference48','impedance_reference'),
                    'impedance_k900_reference':('panel_reference_k900_48','impedance_reference'),
                    'admittance_r2_reference':('panel_reference48_r2','admittance_reference')}[method]
                old_path=args.base_root/folder/old_method/seed/'command.json'
            old=json.loads(old_path.read_text())
            fields={old['argv'][i]:old['argv'][i+1] for i in range(2,len(old['argv']),2)}
            jobdir=args.output/method/seed
            fields['--output']=str(jobdir/'rollout/rollout')
            if args.duration is not None:fields['--duration']=str(args.duration)
            command=[sys.executable,str(root/'scripts/run_with_substep_metrics_20260923.py'),
                     '--runner',str(root/'scripts'/Path(old['argv'][1]).name),
                     '--metrics-output',str(jobdir/'metrics')]
            if args.disable_audit:command+=['--disable-audit']
            if method in ABLATIONS:
                _,function,kind=ABLATIONS[method]
                command += ['--'+kind+'-transform','panel_policy_ablations_20260923:'+function]
            command+=['--']
            for key,value in fields.items():command+=[key,value]
            panel=old.get('panel') or json.loads(old['environment']['PANEL_CONFIG'])
            environment=dict(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',
                MUJOCO_GL='egl',PANELS_ENABLED='1',UNIFIED_6D_TEACHER='1',
                PRIMITIVE_RUNNER_PATH=str(root/'scripts/run_primitive_teacher_v7_20260917.py'),
                CORE_VMC_CONFIG=json.dumps(protocol['vmc']),PANEL_CONFIG=json.dumps(panel))
            plans.append(dict(method=method,fixture=fixture,argv=command,environment=environment,
                         source_command=str(old_path),source_command_sha256=hashlib.sha256(old_path.read_bytes()).hexdigest()))
    manifest=dict(scope='read-only instrumentation rerun of frozen development conditions; no parameter selection',
                  methods=args.methods,fixtures=fixtures,models=protocol['models'],audit_enabled=not args.disable_audit,
                  source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted((root/'scripts').glob('*.py'))},jobs=plans)
    (args.output/'protocol.json').write_text(json.dumps(manifest,indent=2))

    def run(plan):
        jobdir=args.output/plan['method']/str(plan['fixture']['seed']);jobdir.mkdir(parents=True)
        (jobdir/'command.json').write_text(json.dumps(plan,indent=2))
        try:
            with (jobdir/'run.log').open('w') as log:
                done=subprocess.run(plan['argv'],cwd=root,env=dict(os.environ,**plan['environment']),
                                    stdout=log,stderr=subprocess.STDOUT,timeout=1800)
            row=dict(method=plan['method'],fixture=plan['fixture'],returncode=done.returncode)
            result_path=jobdir/'rollout/rollout.json';metric_path=jobdir/'metrics/audit_manifest.json'
            if result_path.exists():
                result=json.loads(result_path.read_text())
                contacts=result['panel_audit']['contacts']
                upstream=any(set(v['bodies'])&{'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'}
                             for k,v in contacts.items() if k!='target_object_geom')
                row.update(task_success=result['success'],strict_success=bool(result.get('accepted_panel_demo') and not upstream),
                           rod_contact_s=contacts['push_rod_geom']['duration_s'],result=str(result_path))
            if metric_path.exists():
                measured=json.loads(metric_path.read_text())
                row.update(wall_s=measured['wall_s'],metrics=measured['episodes'],audit_error=measured['error'])
            return row
        except subprocess.TimeoutExpired:
            return dict(method=plan['method'],fixture=plan['fixture'],returncode='timeout')
    rows=[]
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run,j) for j in plans]):
            row=future.result();rows.append(row)
            (args.output/'results.json').write_text(json.dumps(rows,indent=2,allow_nan=False))
            print(json.dumps(dict(completed=len(rows),total=len(plans),method=row['method'],seed=row['fixture']['seed'],
                                  returncode=row['returncode'],strict_success=row.get('strict_success'))),flush=True)
    (args.output/'FINAL_RESULT.json').write_text(json.dumps(dict(completed=len(rows),rows=rows),indent=2,allow_nan=False))


if __name__=='__main__':main()
