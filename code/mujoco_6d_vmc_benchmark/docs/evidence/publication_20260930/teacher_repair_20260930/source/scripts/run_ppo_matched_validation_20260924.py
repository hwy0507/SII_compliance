"""Frozen PPO8192 + zero on existing six validation fixtures; no selection."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
MODEL_HASH='611323476636c3a398bc465b11c4bf51c0dc6fab280fe9067c7babc66901f16e'
NORM_HASH='55fe4881e585d5f48dff32cf467a07ba29c2576a48654bf33516990866366b56'
UPSTREAM={'fr3_link0','fr3_link1','fr3_link2','fr3_link3','fr3_link4'}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def make_job(args,row,method):
    seed=row['fixture']['seed'];job=args.output/method/str(seed);stem=job/'rollout'/'rollout'
    original=row['command'];params=list(original[original.index('--')+1:])
    params[params.index('--output')+1]=str(stem)
    if '--model' in params:raise ValueError('Reference must be VMC without learned model')
    runner=ROOT/'scripts'/('run_panel_ppo_20260923.py' if method=='ppo8192' else 'run_panel_zero_20260924.py')
    if method=='ppo8192':params.extend(['--model',str(args.model),'--ppo-normalizer',str(args.normalizer)])
    command=[sys.executable,str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),
        '--runner',str(runner),'--metrics-output',str(job/'metrics'),'--',*params]
    environment=dict(row['environment'],PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'))
    return dict(method=method,fixture=row['fixture'],command=command,environment=environment,
        job=str(job),result=str(stem.with_suffix('.json')),expected_mjb_sha256=row['model_mjb_sha256'],
        reference_result=row['result'],reference_result_sha256=row['result_sha256'])


def run_job(record):
    record=dict(record);job=Path(record['job']);job.mkdir(parents=True,exist_ok=False)
    save(job/'command.json',record);started=time.time()
    env=dict(os.environ)
    for key in list(env):
        if key.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or key=='SKIP_MODEL_ARCHIVE':
            env.pop(key)
    env.update(record['environment'],OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='egl')
    try:
        with (job/'run.log').open('w') as log:
            process=subprocess.run(record['command'],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
        if process.returncode:raise RuntimeError(f'Runner exit {process.returncode}')
        path=Path(record['result']);result=json.loads(path.read_text())
        metrics=json.loads((job/'metrics/audit_manifest.json').read_text())
        if metrics['error'] or not metrics['enabled'] or len(metrics['episodes'])!=1:
            raise ValueError('Physical measurement missing or errored')
        physical=metrics['episodes'][0]
        with np.load(path.with_suffix('.npz'),allow_pickle=False) as trace:
            obs,action=trace['observation'],trace['action'];samples=len(action)
            if obs.shape!=(samples,48) or action.shape!=(samples,7) or not np.isfinite(obs).all() or not np.isfinite(action).all():
                raise ValueError('Invalid actor observation/action trace')
            if result['teacher_called'] or result['student_mixture']!=0:raise ValueError('Unexpected teacher intervention')
            if record['method']=='zero' and np.any(action):raise ValueError('Zero reference emitted nonzero action')
            rmse=float(np.sqrt(np.mean(np.sum((trace['position']-trace['target'])**2,axis=1))))
        full=samples==600
        if not full and not result['invalid_physics']:raise ValueError('Unexplained partial episode')
        expected=round(result['duration_s']/physical['timestep_s'])
        if physical['samples']!=expected:raise ValueError('Missing physical samples')
        model_hash=sha(path.with_suffix('.mjb'))
        if model_hash!=record['expected_mjb_sha256']:raise ValueError('Compiled model differs from existing matched fixture')
        contacts=result['panel_audit']['contacts'];external=[v for k,v in contacts.items() if k!='target_object_geom']
        upstream=any(set(v['bodies']) & UPSTREAM for v in external)
        reference=json.loads(Path(record['reference_result']).read_text())
        fields=('scene','controller_6d_config','experiment_contract','simulation_timestep_s')
        if any(result[k]!=reference[k] for k in fields):raise ValueError('Shared physics/task configuration drift')
        record.update(task_success=bool(result['success']),strict_success=bool(result.get('accepted_panel_demo') and not upstream),
            invalid_physics=bool(result['invalid_physics']),upstream=upstream,completed_24s=full,
            safety_terminated_early=bool(not full and result['invalid_physics']),actor_samples=samples,
            tracking_rmse_25hz_m=rmse,tracking_rmse_substep_m=physical['position_rmse_3d_m'],
            actuator_torque_peak_nm=physical['generalized_actuator_torque_peak_nm'],
            linear_speed_peak_substep_mps=physical['linear_speed_peak_mps'],physical=physical,
            endpoint_error_m=result['endpoint_error_m'],final_stage=result['final_stage'],
            max_penetration_mm=1000*max(v['max_penetration_m'] for v in external),
            rod_contact_s=contacts['push_rod_geom']['duration_s'],model_mjb_sha256=model_hash,
            result_sha256=sha(path),shared_configuration_equal=True)
    except Exception as error:
        record.update(execution_error=repr(error),traceback=traceback.format_exc())
    record['elapsed_s']=time.time()-started
    save(job/'result.json',record);return record


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--baseline-results',type=Path,required=True)
    parser.add_argument('--baseline-source',type=Path,required=True)
    parser.add_argument('--model',type=Path,required=True)
    parser.add_argument('--normalizer',type=Path,required=True)
    parser.add_argument('--parity',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if not 1<=args.workers<=4:raise ValueError('Workers must be1..4')
    if sha(args.model)!=MODEL_HASH or sha(args.normalizer)!=NORM_HASH:raise ValueError('Wrong frozen final model/normalizer')
    parity=json.loads(args.parity.read_text())
    if not parity['passed'] or parity['checkpoint_sha256']!=MODEL_HASH or parity['normalizer_sha256']!=NORM_HASH:
        raise ValueError('Final checkpoint deployment parity not verified')
    source_check={str(p.relative_to(args.baseline_source)):dict(expected=sha(p),actual=sha(ROOT/p.relative_to(args.baseline_source)))
        for p in args.baseline_source.rglob('*.py')}
    if any(v['expected']!=v['actual'] for v in source_check.values()):raise ValueError('Baseline source files changed')
    old=json.loads(args.baseline_results.read_text())['rows']
    vmc=sorted([r for r in old if r['candidate']['family']=='vmc'],key=lambda r:r['fixture']['seed'])
    if [r['fixture']['seed'] for r in vmc]!=list(range(9400,9406)):raise ValueError('Expected six frozen validation fixtures')
    if any(sha(r['result'])!=r['result_sha256'] for r in vmc):raise ValueError('Reference results changed')
    args.output.mkdir(parents=True,exist_ok=False)
    jobs=[make_job(args,row,method) for row in vmc for method in ('ppo8192','zero')]
    manifest=dict(scope='DGX matched deployment evaluation, not equal-data/equal-budget training comparison',
        checkpoint_sha256=MODEL_HASH,normalizer_sha256=NORM_HASH,training_steps=8192,
        training_fixture='one canonical rod train episode configuration; one seed; no demonstrations',
        model_selection='fixed final8192; no evaluation selection',actor_privileged_fields=[],critic_privileged_fields=[],
        checkpoint=str(args.model),normalizer=str(args.normalizer),jobs=jobs,workers=args.workers,
        baseline_results_sha256=sha(args.baseline_results),source_equivalence=source_check,
        new_source_sha256={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.py')},
        gates='Unchanged accepted_panel_demo AND no external upstream contact; all safety failures retained',
        metrics='Identical physics_substep_metrics wrapper and original task; partial invalid retained and flagged',
        preflight='Run PPO+zero9400 first; require exact reference MJB and shared configuration before remaining10',
        started_unix=time.time(),pid=os.getpid())
    save(args.output/'protocol.json',manifest);rows=[]
    def record(row):
        rows.append(row);save(args.output/'results.json',rows)
        save(args.output/'status.json',dict(status='running',completed=len(rows),total=12,pid=os.getpid(),
            latest=dict(method=row['method'],seed=row['fixture']['seed'],execution_error=row.get('execution_error'))))
        print(json.dumps(dict(completed=len(rows),method=row['method'],seed=row['fixture']['seed'],
            task=row.get('task_success'),gate=row.get('strict_success'),error=row.get('execution_error'))),flush=True)
    try:
        for job in jobs[:2]:record(run_job(job))
        if any('execution_error' in r for r in rows):raise RuntimeError('9400 preflight failed; remaining10 not launched')
        save(args.output/'PREFLIGHT_PASSED.json',dict(jobs=2,model_hash=rows[0]['model_mjb_sha256'],
            shared_configuration_equal=True))
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures=[pool.submit(run_job,job) for job in jobs[2:]]
            for future in as_completed(futures):record(future.result())
        changed=[p for p,h in manifest['new_source_sha256'].items() if sha(ROOT/p)!=h]
        if changed:raise RuntimeError(f'Source snapshot changed: {changed}')
        errors=sum('execution_error' in r for r in rows)
        save(args.output/'FINAL_RESULT.json',dict(rows=rows,execution_errors=errors))
        if errors:raise RuntimeError(f'{errors} execution errors retained')
        save(args.output/'COMPLETE.json',dict(status='complete',episodes=len(rows),
            task={m:sum(r['task_success'] for r in rows if r['method']==m) for m in ('ppo8192','zero')},
            gate={m:sum(r['strict_success'] for r in rows if r['method']==m) for m in ('ppo8192','zero')},
            all_model_hashes_match=True,source_snapshot_unchanged=True,elapsed_s=time.time()-manifest['started_unix']))
        save(args.output/'status.json',dict(status='complete',completed=12,total=12,pid=os.getpid()))
    except Exception as error:
        save(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(rows)))
        raise


if __name__=='__main__':main()
