"""Predeclared final potential-reward PPO six fixtures plus one zero replay."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
import os
from pathlib import Path
import sys
import time
import traceback
import zipfile
import numpy as np
from run_ppo_matched_validation_20260924 import run_job,sha,save

ROOT=Path(__file__).resolve().parents[1]
METHOD='ppo_potential8192'


def make_job(args,row,method):
    seed=row['fixture']['seed'];job=args.output/method/str(seed);stem=job/'rollout/rollout'
    original=row['command'];params=list(original[original.index('--')+1:])
    params[params.index('--output')+1]=str(stem)
    if '--model' in params:raise ValueError('Reference must be nominal VMC')
    runner=ROOT/'scripts'/('run_panel_zero_20260924.py' if method=='zero' else 'run_panel_ppo_20260923.py')
    if method==METHOD:params.extend(['--model',str(args.pilot/'ppo_final.zip'),'--ppo-normalizer',str(args.pilot/'vecnormalize_train_only.pkl')])
    return dict(method=method,fixture=row['fixture'],job=str(job),result=str(stem.with_suffix('.json')),
        command=[sys.executable,str(ROOT/'scripts/run_with_substep_metrics_20260923.py'),
            '--runner',str(runner),'--metrics-output',str(job/'metrics'),'--',*params],
        environment=dict(row['environment'],PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py')),
        expected_mjb_sha256=row['model_mjb_sha256'],reference_result=row['result'],reference_result_sha256=row['result_sha256'])


def zero_replay(original,current):
    checks=[]
    old_files={str(p.relative_to(original)) for p in original.rglob('*.npz')}
    new_files={str(p.relative_to(current)) for p in current.rglob('*.npz')}
    if old_files!=new_files:raise ValueError('Zero raw archive files differ')
    for name in sorted(old_files):
        with np.load(original/name,allow_pickle=False) as first,np.load(current/name,allow_pickle=False) as second:
            if first.files!=second.files:raise ValueError('Zero archive keys differ')
            for key in first.files:
                a,b=first[key],second[key]
                if a.dtype.kind in 'fciu' and not (np.isfinite(a).all() and np.isfinite(b).all()):raise ValueError('Nonfinite zero replay')
                if not np.array_equal(a,b):raise ValueError(f'Zero trajectory drift:{name}:{key}')
                checks.append(dict(file=name,key=key,shape=list(a.shape),exact=True))
    mjb=[sha(p/'rollout/rollout.mjb') for p in (original,current)]
    if mjb[0]!=mjb[1]:raise ValueError('Zero MJB drift')
    values=[json.loads((p/'rollout/rollout.json').read_text()) for p in (original,current)]
    original_differences=[k for k in values[0] if values[0][k]!=values[1][k]]
    for value in values:
        for key in ('pairs','robot_geoms','robot_bodies','other_contacts'):
            value['contact'][key]=sorted(value['contact'][key],key=lambda x:json.dumps(x,sort_keys=True))
    for key in values[0]:
        if key!='arguments' and values[0][key]!=values[1][key]:raise ValueError(f'Zero result drift:{key}')
    arg_diff=[k for k in values[0]['arguments'] if values[0]['arguments'][k]!=values[1]['arguments'][k]]
    if set(arg_diff)!={'output'}:raise ValueError(f'Zero arguments drift:{arg_diff}')
    return dict(passed=True,all_numeric_arrays_finite=True,arrays=checks,mjb_sha256=mjb[0],
        original_json_differences=original_differences,argument_differences=arg_diff,
        original_result_sha256=sha(original/'rollout/rollout.json'))


def main():
    p=argparse.ArgumentParser()
    for name in ('baseline-results','baseline-source','pilot','parity','freeze','old-evaluation','output'):
        p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();freeze=json.loads(args.freeze.read_text())
    for name,expected in freeze['files'].items():
        if sha(args.pilot/name)!=expected:raise ValueError('Frozen final artifact changed:'+name)
    complete=json.loads((args.pilot/'COMPLETE.json').read_text())
    train=json.loads((args.pilot/'manifest.json').read_text())
    if complete['status']!='complete' or complete['reward_version']!='push4_gate_potential_v1':raise ValueError('Not completed potential experiment')
    if train['training']['timesteps']!=8192:raise ValueError('Wrong training budget')
    with zipfile.ZipFile(args.pilot/'ppo_final.zip') as archive:
        if json.loads(archive.read('data'))['num_timesteps']!=8192:raise ValueError('Not final8192 model')
    model_hash=sha(args.pilot/'ppo_final.zip');norm_hash=sha(args.pilot/'vecnormalize_train_only.pkl')
    if complete['checkpoint_sha256']!=model_hash:raise ValueError('COMPLETE model differs')
    parity=json.loads(args.parity.read_text())
    if not parity['passed'] or parity['checkpoint_sha256']!=model_hash or parity['normalizer_sha256']!=norm_hash:raise ValueError('Offline parity missing')
    source={str(f.relative_to(args.baseline_source)):sha(f) for f in args.baseline_source.rglob('*.py')}
    if any(sha(ROOT/f)!=h for f,h in source.items()):raise ValueError('Baseline source changed')
    vmc=sorted([r for r in json.loads(args.baseline_results.read_text())['rows'] if r['candidate']['family']=='vmc'],key=lambda r:r['fixture']['seed'])
    if [r['fixture']['seed'] for r in vmc]!=list(range(9400,9406)):raise ValueError('Wrong fixtures')
    if any(sha(r['result'])!=r['result_sha256'] for r in vmc):raise ValueError('Reference drift')
    old=json.loads((args.old_evaluation/'FINAL_RESULT.json').read_text())['rows']
    zero=[r for r in old if r['method']=='zero']
    if sorted(r['fixture']['seed'] for r in zero)!=list(range(9400,9406)):raise ValueError('Original zero rows missing')
    if any(sha(r['result'])!=r['result_sha256'] for r in zero):raise ValueError('Original zero result drift')
    args.output.mkdir(parents=True,exist_ok=False)
    jobs=[make_job(args,vmc[0],METHOD),make_job(args,vmc[0],'zero')]+[make_job(args,row,METHOD) for row in vmc[1:]]
    manifest=dict(method=METHOD,jobs=jobs,workers=2,checkpoint_sha256=model_hash,normalizer_sha256=norm_hash,
        training_steps=8192,selection='Only fixed final8192; no validation selection',reward_version=complete['reward_version'],
        actor_privileged_fields=[],critic_privileged_fields=[],freeze=freeze,baseline_source_hashes=source,
        source_sha256={str(f.relative_to(ROOT)):sha(f) for f in ROOT.rglob('*.py')},
        reused_zero=zero,preflight='model/zero9400 then exact original zero raw replay, then five remaining model jobs',
        started_unix=time.time(),pid=os.getpid())
    save(args.output/'protocol.json',manifest);rows=[]
    def record(row):
        rows.append(row);save(args.output/'results.json',rows)
        save(args.output/'status.json',dict(status='running',completed=len(rows),total=7,pid=os.getpid()))
        print(json.dumps(dict(completed=len(rows),method=row['method'],seed=row['fixture']['seed'],task=row.get('task_success'),gate=row.get('strict_success'),error=row.get('execution_error'))),flush=True)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            for row in pool.map(run_job,jobs[:2]):record(row)
        if any('execution_error' in r for r in rows):raise RuntimeError('9400 preflight execution failed')
        replay=zero_replay(args.old_evaluation/'zero/9400',args.output/'zero/9400')
        save(args.output/'ZERO_REPLAY_PARITY.json',replay)
        save(args.output/'PREFLIGHT_PASSED.json',dict(passed=True,jobs=2,zero_replay_exact=True))
        with ThreadPoolExecutor(max_workers=2) as pool:
            for future in as_completed([pool.submit(run_job,job) for job in jobs[2:]]):record(future.result())
        if any(sha(ROOT/f)!=h for f,h in manifest['source_sha256'].items()):raise RuntimeError('Source changed')
        if any(sha(args.pilot/n)!=h for n,h in freeze['files'].items()):raise RuntimeError('Model artifacts changed')
        errors=sum('execution_error' in r for r in rows)
        save(args.output/'FINAL_RESULT.json',dict(rows=rows,reused_zero=zero,execution_errors=errors))
        if errors:raise RuntimeError('Execution errors retained')
        save(args.output/'COMPLETE.json',dict(status='complete',episodes=7,model_episodes=6,
            task=sum(r['task_success'] for r in rows if r['method']==METHOD),
            gate=sum(r['strict_success'] for r in rows if r['method']==METHOD),
            zero_replay_exact=True,source_snapshot_unchanged=True,elapsed_s=time.time()-manifest['started_unix']))
        save(args.output/'status.json',dict(status='complete',completed=7,total=7,pid=os.getpid()))
    except BaseException as error:
        save(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=len(rows)));raise


if __name__=='__main__':main()
