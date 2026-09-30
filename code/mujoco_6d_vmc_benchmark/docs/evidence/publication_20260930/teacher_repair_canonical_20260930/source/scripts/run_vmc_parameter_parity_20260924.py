"""Two24s nominal VMC/zero-parameter VMC episodes, fixed train fixture only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
REQUIRED_ROLLOUT_FIELDS=['time','observation','action','teacher_force','stage','position','target','force',
    'twist','object_position','torque','cup_shift','cup_tilt','slide_memory','cup_position','ball_position','ball_velocity']
RESULT_LABEL_EXCLUSIONS=['controller','teacher_called','arguments']


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def save(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run_job(job):
    path=Path(job['directory']);path.mkdir(parents=True,exist_ok=False);save(path/'command.json',job)
    env=dict(os.environ)
    for key in list(env):
        if key.startswith(('PUSH_','PANEL_','CORE_VMC_','UNIFIED_','VMC_MODEL_CACHE_')) or key=='SKIP_MODEL_ARCHIVE':env.pop(key)
    env.update(job['environment'],OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',MUJOCO_GL='egl')
    with (path/'runner.log').open('w') as log:
        done=subprocess.run(job['command'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=1200)
    if done.returncode:raise RuntimeError(f"{job['method']} failed{done.returncode}; log retained")
    return json.loads((path/'rollout.json').read_text())


def equal_arrays(a,b,name):
    if a.shape!=b.shape:raise AssertionError(f'{name} shape mismatch')
    equal=np.array_equal(a,b,equal_nan=True) if a.dtype.kind in 'fc' else np.array_equal(a,b)
    if not equal:raise AssertionError(f'{name} differs; physics mismatch cannot be excluded after execution')
    return dict(equal=True,shape=list(a.shape),max_abs_error=float(np.max(np.abs(a-b))) if a.dtype.kind in 'fiu' and a.size else None)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--training-fixture',type=Path,required=True)
    parser.add_argument('--menagerie',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    command=json.loads((args.training_fixture/'command.json').read_text())
    historical=json.loads((args.training_fixture/'rollout.json').read_text())
    params=dict(historical['arguments'],duration=24.,menagerie=str(args.menagerie),mixture=0.,model=None,render=False)
    environment={k:command['environment'][k] for k in ('CORE_VMC_CONFIG','PANEL_CONFIG','PANELS_ENABLED')}
    panel=json.loads(environment['PANEL_CONFIG']);panel['rod_height_m']=historical['scene']['push_height']
    environment.update(PANEL_CONFIG=json.dumps(panel),UNIFIED_6D_TEACHER='1',
        PRIMITIVE_RUNNER_PATH=str(ROOT/'scripts/run_primitive_teacher_v7_20260917.py'))
    jobs=[]
    for method,runner in [('nominal_vmc','run_panel_push_20260920.py'),('zero_parameter','run_panel_vmc_zero_parameter_20260924.py')]:
        path=args.output/method;values=dict(params,output=str(path/'rollout'))
        argv=[sys.executable,str(ROOT/'scripts'/runner)]
        for key,value in values.items():
            if value is None or value is False:continue
            argv.extend(['--'+key.replace('_','-')] if value is True else ['--'+key.replace('_','-'),str(value)])
        jobs.append(dict(method=method,directory=str(path),command=argv,environment=environment))
    protocol=dict(scope='Train fixture push_00000 only; interface equivalence, not learned RL results',
        jobs=jobs,workers=2,parameter_action_dim=6,execution_action_dim=7,observation_dim=48,
        nominal_configuration_origin=str(args.training_fixture),
        source_hashes={str(p.relative_to(ROOT)):sha(p) for p in ROOT.rglob('*.py')},
        historical_command_sha256=sha(args.training_fixture/'command.json'),
        equivalence_required_rollout_fields=REQUIRED_ROLLOUT_FIELDS,
        teacher_action_rule='A.teacher_action == B.action; B.teacher_action all zero by policy-only logging branch',
        result_label_exclusions=RESULT_LABEL_EXCLUSIONS,
        allowed_argument_differences=['output','model'],
        physics_states='all keys exact',contact_samples='all keys exact',compiled_model='SHA256 exact',
        parameter_trace='all parameter requests/logscale zero; K/D exactly nominal throughout; action equals B rollout',
        actor_privileged_fields=[],policy='constant zero parameter6 from reset, not zero action7',
        pid=os.getpid(),started_unix=time.time())
    save(args.output/'protocol.json',protocol)
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run_job,jobs))
        a_path,b_path=[args.output/m for m in ('nominal_vmc','zero_parameter')]
        arrays={}
        with np.load(a_path/'rollout.npz',allow_pickle=False) as a,np.load(b_path/'rollout.npz',allow_pickle=False) as b:
            if set(a.files)!=set(REQUIRED_ROLLOUT_FIELDS+['teacher_action']) or set(b.files)!=set(a.files):
                raise AssertionError('Original rollout fields changed')
            if a['observation'].shape!=(600,48):raise AssertionError('Full24s interface proof not completed')
            for key in REQUIRED_ROLLOUT_FIELDS:arrays['rollout:'+key]=equal_arrays(a[key],b[key],key)
            arrays['A.teacher_action=B.action']=equal_arrays(a['teacher_action'],b['action'],'teacher policy output')
            if np.any(b['teacher_action']):raise AssertionError('Policy branch teacher logging not zero')
            b_action=b['action'].copy();b_obs=b['observation'].copy()
        for file in ('physics_states.npz','contact_samples.npz'):
            with np.load(a_path/file,allow_pickle=False) as a,np.load(b_path/file,allow_pickle=False) as b:
                if a.files!=b.files:raise AssertionError('Physics/contact field mismatch')
                for key in a.files:arrays[file+':'+key]=equal_arrays(a[key],b[key],file+key)
        model_hash=sha(a_path/'rollout.mjb')
        if sha(b_path/'rollout.mjb')!=model_hash:raise AssertionError('MJB differs')
        nominal=json.loads(environment['CORE_VMC_CONFIG'])
        with np.load(b_path/'vmc_parameter_trace.npz',allow_pickle=False) as parameter:
            if parameter['parameter_request'].shape!=(600,6) or np.any(parameter['parameter_request']) or np.any(parameter['log_scale']):
                raise AssertionError('Not zero parameters from reset')
            arrays['parameter_action']=equal_arrays(parameter['action'],b_action,'parameter execution')
            arrays['parameter_observation']=equal_arrays(parameter['observation'],b_obs,'parameter observation')
            for field,cfg in [('stiffness','stiffness_6d'),('damping','damping_6d')]:
                arrays[field]=equal_arrays(parameter[field],np.tile(nominal[cfg],(600,1)),field)
        first,second=results
        if not first['teacher_called'] or second['teacher_called']:raise AssertionError('Wrong teacher branches')
        if set(first)!=set(second):raise AssertionError('Result fields changed')
        different=[key for key in first if key not in RESULT_LABEL_EXCLUSIONS and first[key]!=second[key]]
        if different:raise AssertionError(f'Result dynamics/audit differ:{different}')
        arg_diff=[key for key in first['arguments'] if first['arguments'][key]!=second['arguments'][key]]
        if set(arg_diff)!={'output','model'}:raise AssertionError(f'Unexpected argument drift{arg_diff}')
        changed=[p for p,h in protocol['source_hashes'].items() if sha(ROOT/p)!=h]
        if changed:raise AssertionError('Snapshot source changed')
        summary=dict(status='complete',passed=True,episodes=2,samples_per_episode=600,arrays=arrays,
            model_mjb_sha256=model_hash,source_snapshot_unchanged=True,
            task_success=first['success'],accepted_panel_demo=first['accepted_panel_demo'],
            teacher_branch_metadata_differences_explained=True,
            learned_policy=False,elapsed_s=time.time()-protocol['started_unix'])
        save(args.output/'COMPLETE.json',summary);print(json.dumps(summary),flush=True)
    except BaseException as error:
        import traceback
        save(args.output/'FAILED.json',dict(error=repr(error),traceback=traceback.format_exc()))
        raise


if __name__=='__main__':main()
