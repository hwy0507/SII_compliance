"""Audit already-completed locked validation episodes, without simulation.

Requires an explicitly supplied locked-bank hash. Each NPZ is materialized and
closed before opening another. Does not dispatch validation or alter selection.
"""
import argparse
import ast
from datetime import datetime, timezone
import gc
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import sys
import time

import numpy as np

from teacher_bank_asset_audit_20260930 import sha

LOCK_VERIFICATION_SCOPE = ('Checks caller-supplied bank hash, completion marker, contiguous full search '
    'history, anchor counts and selected-record identity. Does not independently reconstruct candidate '
    'ranking or certify optimizer selection; terminal selection audit is separate.')
DURATION_SCOPE = ('Frozen v10 evaluator appends its record after env.step, then tests abort conditions. '
    'env.step executes all 10 servo intervals per 0.04 s action without an early break; each servo '
    'interval completes its physical substeps. Therefore terminal, returncode=0 episodes can abort '
    'only at a policy boundary. Exceptions during a physical substep are infrastructure failures, '
    'excluded before raw data are read. This is specific to this frozen contract, not a general '
    'claim that physical aborts must always occur at policy boundaries.')


def read(path):
    value=json.loads(Path(path).read_text())
    json.dumps(value,allow_nan=False)
    return value


def load_columns(path,keys=None):
    with np.load(path,allow_pickle=False) as archive:
        return {key:archive[key] for key in (archive.files if keys is None else keys)}


def complete_execution(folder):
    """Only execution metadata may be read until the terminal state is known."""
    path=folder/'execution.json'
    if not path.exists():return None,'not_executed'
    execution=read(path)
    if execution.get('status')!='completed' or execution.get('returncode')!=0:
        return None,'not_successfully_completed:'+str(execution.get('status'))
    return execution,None


def parse_initial_intersections(log):
    """Recognize the frozen explicit geometry rejection, never generic failure."""
    prefix='ValueError: Initial rigid body intersections: '
    lines=log.strip().splitlines()
    if not lines or not lines[-1].startswith(prefix) or 'in audit_initial' not in log:
        return None
    pairs=json.loads(lines[-1][len(prefix):])
    if (not isinstance(pairs,list) or not pairs or any(
            not isinstance(r.get('pair'),list) or len(r['pair'])!=2
            or not np.isfinite(r.get('depth_mm',float('nan'))) or r['depth_mm']<=.01 for r in pairs)):
        raise ValueError('Malformed initial intersection evidence')
    return pairs


def verify_request(root,request,execution,fixture,method,selected):
    if (request['fixture']!=fixture or request['method']!=method or request['phase']!='validation'
            or request['x']!=selected['x'] or request['plan_sha256']!=sha(root/'plan.json')
            or execution['plan_sha256']!=request['plan_sha256']):raise ValueError('Locked validation request mismatch')
    from teacher_bank_design_20260930 import decode,digest
    from teacher_bank_classical_20260930 import decode as classical_decode
    expected=decode(request['x']) if method=='vmc' else classical_decode(request['x'],method)
    if request['teacher']!=expected:raise ValueError('Controller config differs from locked x')
    if digest(fixture['active_physical_parameters'])!=fixture['physical_config_sha256']:
        raise ValueError('Fixture physical config hash mismatch')


def invalid_initial_scene(root,folder,fixture,method,selected):
    """Read terminal failure metadata; preserve it without fabricating metrics."""
    path=folder/'execution.json'
    if not path.is_file():return None
    execution=read(path)
    if execution.get('status')!='failed' or execution.get('returncode')!=1:return None
    log_path=folder/'run.log'
    if not log_path.is_file():return None
    log=log_path.read_text();pairs=parse_initial_intersections(log)
    if pairs is None:return None
    before=sha(path)
    request=read(folder/'request.json')
    verify_request(root,request,execution,fixture,method,selected)
    command=read(folder/'command.json')
    if command['fixture']!=fixture or command['teacher']!=request['teacher']:
        raise ValueError('Rejected-scene command does not bind to request')
    if any(folder.glob('rollout*')) or any((folder/name).exists() for name in
           ('teacher_internal.npz','execution_chain.npz','impedance_servo.npz')):
        raise ValueError('Unexpected dynamic/model evidence alongside pre-integration rejection')
    exposure=load_columns(folder/'exposure.npz')
    if (float(exposure['terminal_time_s'])!=0 or json.loads(str(exposure['fixture_json']))!=fixture
            or any(len(exposure[k]) for k in ('time','dt','contact_runs','person_physics'))):
        raise ValueError('Nonempty or mismatched initial-rejection exposure')
    source=root/'source/scripts/validate_office_apparatus_v5_20260917.py'
    tree=ast.parse(source.read_text())
    run=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run')
    calls=[n for n in ast.walk(run) if isinstance(n,ast.Call)]
    guard=next(n.lineno for n in calls if isinstance(n.func,ast.Name) and n.func.id=='audit_initial')
    steps=[n.lineno for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr in ('step','mj_step','mj_step1','mj_step2')]
    if not steps or guard>=min(steps):raise ValueError('Initial guard is not before evaluator integration')
    if 'in audit_initial' not in log or str(root/'source/scripts/office_task_v4_20260917.py') not in log:
        raise ValueError('Initial-rejection traceback differs from frozen source')
    if sha(path)!=before:raise ValueError('Failed execution changed during review')
    evidence=('execution.json','request.json','command.json','run.log','exposure.npz')
    return dict(folder=str(folder),status='invalid_initial_scene',fixture_id=fixture['id'],
        category=fixture['category'],method=method,seed=fixture['seed'],execution=execution,
        controller_coordinates=request['x'],selected_search_candidate=selected['index'],
        physical_config_sha256=fixture['physical_config_sha256'],initial_intersections=pairs,
        maximum_initial_overlap_mm=max(r['depth_mm'] for r in pairs),
        failure_reasons=['invalid_initial_scene'],metrics=None,eligible=False,
        raw_sha256={name:sha(folder/name) for name in evidence},
        preintegration_evidence=dict(evaluator_source_sha256=sha(source),
            original_audit_initial_line=guard,adapted_relative_line=guard-run.lineno+1,
            first_evaluator_step_line=min(steps),exposure_terminal_time_s=0.,
            scope='Frozen source ordering plus actual audit_initial traceback and empty exposure; no independent runtime step counter or dynamic rerun.'),
        comparison_scope='Retained scene-generation rejection, not a controller physical-gate failure; excluded from trajectory metric means, included in planned-case accounting.')


def verify_lock(root,bank_hash):
    if sha(root/'teacher_bank.json')!=bank_hash:raise ValueError('Locked bank hash mismatch')
    if not (root/'anchor_feasibility.json').is_file():raise ValueError('Search completion / lock marker absent')
    plan,bank=read(root/'plan.json'),read(root/'teacher_bank.json')
    for category in plan['categories']:
        for method in plan['methods']:
            key=category+'/'+method
            history=read(root/'search'/key/'history.json')
            if [r['index'] for r in history]!=list(range(plan['search_candidates_per_category'])):
                raise ValueError('Search history incomplete: '+key)
            selected=bank[key]
            if len(selected)!=1:raise ValueError('Expected one locked candidate per method/category')
            row=selected[0]
            if row['index'] not in range(len(history)) or any(row[k]!=v for k,v in history[row['index']].items()):
                raise ValueError('Selected bank record differs from completed search history')
            if any(h['total']!=len(plan['anchor_indices']) for h in history):
                raise ValueError('Incomplete search anchor history')
    return plan,bank


def audit_duration(action_count,actual_duration,planned_duration,abort_reason):
    """Apply the frozen complete-policy-step abort contract, retaining failures."""
    np.testing.assert_allclose(actual_duration,action_count*.04,rtol=0,atol=1e-6,
        err_msg='Frozen v10 permits successful process termination only after whole policy steps')
    full=abs(actual_duration-planned_duration)<1e-6
    if not full and not abort_reason:raise ValueError('Unexplained truncated episode')
    return dict(physical_horizon_duration_recorded=full,
        full_task_horizon_completed=full and not bool(abort_reason),scope=DURATION_SCOPE)


def physical_metrics(path,plan):
    data=load_columns(path,('time','dt','error','qfrc_actuator','twist'))
    for key,value in data.items():
        if not np.isfinite(value).all():raise ValueError('Nonfinite physical '+key)
    dt=data['dt'].astype(float)
    n=len(dt)
    if not n or np.any(dt<=0):raise ValueError('Empty or invalid physical trace')
    if (data['error'].shape!=(n,3) or data['qfrc_actuator'].shape!=(n,7)
            or data['twist'].shape!=(n,6) or data['time'].shape!=(n,)):
        raise ValueError('Physical trace shape mismatch')
    np.testing.assert_allclose(dt,plan['dt'],rtol=0,atol=1e-12)
    np.testing.assert_allclose(data['time'],np.cumsum(dt),rtol=0,atol=1e-7)
    error=data['error'].astype(float)
    measured=dict(rmse_m=float(np.sqrt(np.sum(np.einsum('ij,ij->i',error,error)*dt)/dt.sum())),
        peak_torque_nm=float(np.max(np.abs(data['qfrc_actuator']))),
        peak_speed_mps=float(np.max(np.linalg.norm(data['twist'][:,:3].astype(float),axis=1))),
        physical_samples=n,actual_duration_s=float(dt.sum()),
        scope='Independent reductions over archived physical-substep stage-waypoint error, actual generalized actuator torque, and translational endpoint twist; RMSE is not smooth global-path tracking.')
    return measured,data


def action_replay(folder,request,physics,runner):
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from teacher_bank_classical_20260930 import replay_admittance,replay_impedance
    data=load_columns(folder/'rollout.npz',('observation','applied_action','neuron_qpos','qpos','qvel','neuron_time','time'))
    alignment=runner.audit_observation_alignment(data)
    internal=load_columns(folder/'teacher_internal.npz')
    chain=load_columns(folder/'execution_chain.npz')
    for arrays in (data,internal,chain):
        if any(not np.isfinite(v).all() for v in arrays.values()):raise ValueError('Nonfinite action evidence')
    method=request['method']
    safety=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    actor=StableReadoutTeacher(**request['teacher']) if method=='vmc' else None
    maximum=0.
    execution_binding=None
    scope='VMC estimated-wrench input, virtual state, raw action and shared filter replay'
    if method=='admittance':
        replay=replay_admittance(request['teacher'],runner.column_rows(internal))
        maximum=replay['max_abs'];scope=replay['scope']
    elif method=='impedance':
        servo=load_columns(folder/'impedance_servo.npz')
        replay=replay_impedance(request['teacher'],runner.column_rows(servo),safety)
        maximum=replay['max_abs'];scope=replay['scope']
        import mujoco
        model=mujoco.MjModel.from_binary_path(str(folder/'rollout.mjb'))
        mapping=runner.direct_arm_mapping(model)
        del model
        execution_binding=dict(mapping=mapping,**runner.audit_impedance_execution(servo,physics))
        del servo
    filt,label_filter=VelocityResidualActionFilter(safety),VelocityResidualActionFilter(safety)
    observations=data['observation'];count=len(observations)
    if observations.shape!=(count,48) or any(len(a['request'])!=count for a in (internal,chain)):
        raise ValueError('canonical48D action lengths disagree')
    for i,obs in enumerate(observations):
        action=actor.act(obs[39:45]) if actor else internal['request'][i]
        out=filt.filter(action,.04)
        units=np.r_[[safety.maximum_linear_yield_mps]*3,[safety.maximum_angular_yield_radps]*3]
        label=np.r_[(1-out.wbc_scale)/(1-safety.minimum_wbc_scale),out.cartesian_yield_twist/units]
        second=label_filter.filter(chain['filtered_action'][i],.04)
        pairs=[(action,internal['request'][i]),(action,chain['request'][i]),(action,data['applied_action'][i]),
            (label,chain['filtered_action'][i]),(out.cartesian_yield_twist,chain['yield_twist'][i]),
            (out.wbc_scale,chain['wbc_scale'][i]),(.04,chain['filter_dt'][i]),
            (second.cartesian_yield_twist,out.cartesian_yield_twist),(second.wbc_scale,out.wbc_scale)]
        if actor:pairs.extend([(actor.offset,internal['offset'][i]),(actor.velocity,internal['velocity'][i]),
                                (actor.filtered,internal['filtered_wrench'][i])])
        for left,right in pairs:
            left,right=np.asarray(left),np.asarray(right)
            if left.shape!=right.shape:raise ValueError('Action/state replay shape mismatch')
            maximum=max(maximum,float(np.max(abs(left-right))))
    if maximum>1e-10:raise ValueError('Action/state/filter replay mismatch')
    return dict(max_abs=maximum,scope=scope,action_count=count,observation_alignment=alignment,
        executed_torque_binding=execution_binding,
        semantics=dict(raw_request='teacher_internal.request = execution_chain.request = rollout.applied_action (despite its field name)',
            filtered_action='execution_chain.filtered_action encodes filtered WBC scale/yield twist; is not motor torque',
            actual_execution='substep_metrics.qfrc_actuator is actual physical generalized actuator torque',
            impedance='action7 is zero; actual torque comes from impedance_servo applied_torque after motor limiter',
            vmc_admittance_limitation='Motor torque metrics are independently measured; complete FK/WBC/dynamics reconstruction from action7 is not performed.'))


def audit_case(root,folder,fixture,method,selected,plan,runner):
    execution,skip=complete_execution(folder)
    if skip:
        invalid=invalid_initial_scene(root,folder,fixture,method,selected)
        return invalid or dict(folder=str(folder),status='skipped',reason=skip)
    before=sha(folder/'execution.json')
    request,audit,meta=map(read,(folder/'request.json',folder/'audit.json',folder/'rollout.json'))
    verify_request(root,request,execution,fixture,method,selected)
    if (audit['fixture_id']!=fixture['id'] or audit['split']!='validation' or audit['method']!=method
            or not isinstance(audit['eligible'],bool)):raise ValueError('Audit identity mismatch')
    hashes={}
    for name,expected in audit['files_sha256'].items():
        path=(folder/name).resolve()
        if folder.resolve() not in path.parents:raise ValueError('Raw evidence path escapes case')
        hashes[name]=sha(path)
        if hashes[name]!=expected:raise ValueError('Raw evidence hash mismatch: '+name)
    if hashes.get('rollout.mjb')!=audit['model_sha256']:raise ValueError('MJB identity mismatch')
    measured,physics=physical_metrics(folder/'rollout_metrics/substep_metrics.npz',plan)
    for key in ('rmse_m','peak_torque_nm','peak_speed_mps'):
        np.testing.assert_allclose(measured[key],audit[key],rtol=2e-7,atol=1e-8)
    replay=action_replay(folder,request,physics,runner)
    from wbc_velocity_residual_core import TORQUE_LIMITS_NM,VelocityResidualSafetyConfig
    torque=physics['qfrc_actuator'].astype(float)
    safety=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    amplitude=float(np.max(abs(torque)/TORQUE_LIMITS_NM))
    slew=float(np.max(abs(np.diff(torque,axis=0))/(np.asarray(safety.maximum_torque_rate_nmps)*.004))) if len(torque)>1 else 0.
    np.testing.assert_allclose([amplitude,slew],[audit['torque_ratio'],audit['torque_slew_ratio']],rtol=2e-7,atol=1e-8)
    del torque
    duration_audit=audit_duration(replay['action_count'],measured['actual_duration_s'],
                                  plan['duration_s'],meta.get('abort_reason'))
    exposure=load_columns(folder/'exposure.npz')
    binding=runner.audit_exposure_physics_binding(exposure,physics,fixture)
    del exposure,physics
    from teacher_bank_exposure_20260930 import audit_saved
    exposure_gate=audit_saved(folder/'exposure.npz',fixture)
    if exposure_gate!=audit['exposure']:raise ValueError('Exposure replay mismatch')
    if audit['penetration_mm']!=meta['stats']['max_external_penetration_m']*1000:
        raise ValueError('Penetration metadata mismatch')
    if sha(folder/'execution.json')!=before:raise ValueError('Execution changed during review')
    return dict(folder=str(folder),status='audited',eligible=audit['eligible'],failure_reasons=audit['failure_reasons'],
        fixture_id=fixture['id'],category=fixture['category'],method=method,seed=fixture['seed'],
        controller_config=request['teacher'],controller_coordinates=request['x'],
        selected_search_candidate=selected['index'],physical_config_sha256=fixture['physical_config_sha256'],
        model_sha256=audit['model_sha256'],raw_sha256=hashes,audit_sha256=sha(folder/'audit.json'),
        execution_sha256=before,execution=execution,metrics=measured,
        full_task_horizon_completed=duration_audit['full_task_horizon_completed'],duration_audit=duration_audit,
        replay=replay,exposure_binding=binding,exposure_replay=exposure_gate,
        actuator_limits=dict(amplitude_ratio=amplitude,slew_ratio=slew,servo_period_s=.004),
        penetration=dict(mm=audit['penetration_mm'],independently_recomputed=False,
            scope='Audit/rollout metadata, no complete physical-substep contact-distance trace'),
        evaluator_flags={k:v for k,v in meta.items() if isinstance(v,bool)},abort_reason=meta.get('abort_reason'))


def paired_groups(rows,methods):
    result=[]
    for fixture in sorted({r['fixture_id'] for r in rows if r['status']=='audited'}):
        cases=[r for r in rows if r.get('fixture_id')==fixture and r['status']=='audited']
        if len({r['method'] for r in cases})!=len(cases):raise ValueError('Duplicate paired method')
        hashes={r['model_sha256'] for r in cases}
        if len(hashes)!=1:raise ValueError('Paired validation models differ: '+fixture)
        result.append(dict(fixture_id=fixture,complete=set(r['method'] for r in cases)==set(methods),
            methods=[r['method'] for r in cases],model_sha256=next(iter(hashes))))
    return result


def main():
    started_utc=datetime.now(timezone.utc).isoformat()
    started_monotonic=time.monotonic()
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--locked-bank-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,output=args.root.resolve(),args.output.resolve()
    if output.exists() or output==root or root in output.parents:raise ValueError('Require new external output directory')
    plan,bank=verify_lock(root,args.locked_bank_sha256)
    if sha(root/'fixtures.json')!=plan['fixtures_sha256']:raise ValueError('Fixture manifest mismatch')
    for name,digest in plan['sources'].items():
        if sha(root/'source'/name)!=digest:raise ValueError('Frozen source drift: '+name)
    fixtures=read(root/'fixtures.json')
    sys.path.insert(0,str(root/'source/tools'));sys.path.insert(0,str(root/'source/scripts'))
    import mujoco
    if mujoco.__version__!=plan['mujoco_version']:raise ValueError('Replay MuJoCo version differs')
    def forbidden(*unused,**kwargs):raise RuntimeError('No dynamic MuJoCo allowed in validation audit')
    for name in ('mj_step','mj_step1','mj_step2'):setattr(mujoco,name,forbidden)
    spec=importlib.util.spec_from_file_location('frozen_validation_audit_runner',root/'source/tools/teacher_bank_rollout_20260930.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    rows=[]
    output.mkdir(parents=True)
    for category in plan['categories']:
        subset=[f for f in fixtures if f['split']=='validation' and f['category']==category]
        for index in plan['validation_indices']:
            fixture=subset[index]
            for method in plan['methods']:
                folder=root/f'validation/{fixture["id"]}/{method}'
                try:
                    row=audit_case(root,folder,fixture,method,bank[category+'/'+method][0],plan,runner)
                except Exception as error:
                    row=dict(folder=str(folder),fixture_id=fixture['id'],method=method,category=category,
                        status='audit_failed',error_type=type(error).__name__,reason=str(error))
                rows.append(row)
                print(json.dumps(dict(fixture=fixture['id'],method=method,status=row['status'])),flush=True)
                gc.collect()
    paired=paired_groups(rows,plan['methods'])
    if sha(root/'teacher_bank.json')!=args.locked_bank_sha256:raise ValueError('Locked bank changed during review')
    report=dict(scope='Independent read-only audit of predeclared locked validation subset; retained failures, skipped incomplete episodes. No tuning or simulation; no success claims beyond completed paired cases.',
        root=str(root),locked_bank_sha256=args.locked_bank_sha256,plan_sha256=sha(root/'plan.json'),
        lock_verification_scope=LOCK_VERIFICATION_SCOPE,
        frozen_source_sha256=plan['sources'],script_sha256=sha(Path(__file__)),python=sys.executable,
        audit_execution=dict(argv=[sys.executable,*sys.argv],cwd=str(Path.cwd()),
            hostname=platform.node(),machine=platform.machine(),platform=platform.platform(),
            python_version=platform.python_version(),numpy_version=np.__version__,
            mujoco_version=mujoco.__version__,started_utc=started_utc,
            audit_finished_utc=datetime.now(timezone.utc).isoformat(),
            audit_elapsed_s=time.monotonic()-started_monotonic,
            timestamp_scope='In-process audit start through report assembly, not process exit.',
            thread_environment={k:os.environ.get(k) for k in
                ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS')},
            integration_guard=['mj_step','mj_step1','mj_step2']),
        planned_cases=len(plan['categories'])*len(plan['validation_indices'])*len(plan['methods']),
        audited_cases=sum(r['status']=='audited' for r in rows),
        invalid_initial_scene_cases=sum(r['status']=='invalid_initial_scene' for r in rows),
        paired_fixtures=paired,cases=rows,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')


if __name__=='__main__':main()
