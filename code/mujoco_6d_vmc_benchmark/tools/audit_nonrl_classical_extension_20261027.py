"""Read-only independent saved-telemetry audit; never simulates or trains.

The final mode requires all180 identities. Progress mode audits only complete
classical episodes in a snapshot and cannot issue final comparison approval.
Native classical actor/servo reconstruction is deliberately not claimed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np


def read(p): return json.loads(p.read_text())


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def require(ok, message):
    if not ok: raise ValueError(message)


def near(actual, expected, label, atol=1e-8):
    if actual is None or expected is None:
        require(actual is expected,label)
    else:
        np.testing.assert_allclose(actual,expected,rtol=3e-7,atol=atol,err_msg=label)


def check_manifest(root, expected):
    for name, digest in expected.items():require(sha(root/name)==digest,'Source drift: '+str(root/name))


def audit_row(row, root, model, condition, filter_class, config_class, learned):
    run=Path(row['run']); result=read(run/'rollout.json'); audit=read(run/'AUDIT.json')
    state=read(run/'execution.json')
    require(state['status']=='complete','Unfinished worker')
    for filename,key in [('AUDIT.json','audit_sha256'),('rollout.npz','trace_sha256'),
        ('rollout.mjb','model_sha256'),('execution.json','execution_sha256'),
        ('execution_chain.npz','chain_sha256'),('rollout_metrics/substep_metrics.npz','substep_metrics_sha256'),
        ('research_substeps.npz','research_substeps_sha256')]:
        require(sha(run/filename)==row[key],'Episode hash mismatch: '+str(run/filename))
    require(row['model_sha256']==read(root/'PROTOCOL.json')['formal_model_sha256'],'Wrong world')
    require(state['mujoco']=='3.11.0','Wrong physics interpreter')
    require(result['physics_resolution']['base_dt_s']==5e-5,'Changed physics dt')
    require(all(result['arguments'][k]==v for k,v in condition['overrides'].items()),'Wrong condition overrides')
    require(state['config']==model['config'] and read(run/'config.json')==model['config'],'Changed controller config')
    require(sha(run/'config.json')==state['config_sha256'],'Config hash mismatch')
    frozen=root/'physics_source'
    check_manifest(frozen,state['source_sha256'])
    if learned:
        require(sha(run/'checkpoint.npz')==model['checkpoint_sha256']==state['checkpoint_sha256'],'Checkpoint drift')
        require(audit['actor_replay_performed'] and audit['action_replay_max_abs']==0.,'Original learned actor replay missing')
    else:
        require(audit['actor_replay_performed'] is False,'Mislabelled classical actor replay')
        require(audit['parameter_source_sha256']==model['parameter_source_sha256'],'Classical source registration mismatch')
        check_manifest(run/'parameter_source',model['parameter_source_sha256'])
        require(state['runtime_provenance']['parameter_prior']['center']==model['config']['parameters'],'Executed parameters differ')
    with np.load(run/'rollout.npz') as z:
        time=z['time']; action=z['applied_action']; obs=z['observation']
    require(action.shape==(len(time),7) and obs.shape==(len(time),48),'Policy trace shape')
    near(np.diff(time),.04,'Policy clock')
    if not learned:
        with np.load(run/'baseline_policy.npz') as p:
            np.testing.assert_array_equal(p['action'],action)
            np.testing.assert_array_equal(p['observation'],obs)
    filt=filter_class(config_class(maximum_linear_yield_mps=.32))
    replay=[filt.filter(a,.04) for a in action]
    with np.load(run/'execution_chain.npz') as chain:
        np.testing.assert_array_equal(action,chain['requested_action'])
        for field,attr in [('clipped_action','raw_action_clipped'),('yield_twist','cartesian_yield_twist'),('wbc_scale','wbc_scale')]:
            np.testing.assert_array_equal(chain[field],np.asarray([getattr(x,attr) for x in replay]))
    del replay
    with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
        dt=z['dt']; torque=z['qfrc_actuator'].astype(float)
        error=z['error'].astype(float); twist=z['twist'].astype(float); physical_time=z['time']
    require(all(np.isfinite(x).all() for x in (dt,torque,error,twist,physical_time)),'Nonfinite telemetry')
    require(np.all(dt>0) and np.all(np.diff(physical_time)>0),'Invalid substep clock')
    near(dt,5e-5,'Frozen integration step',atol=1e-12)
    duration=float(dt.sum());peak=float(np.abs(torque).max())
    rmse=float(np.sqrt(np.sum(np.square(error)*dt[:,None])/duration)*1000)
    speed=float(np.linalg.norm(twist[:,:3],axis=1).max())
    near(duration,row['duration_s'],'Duration');near(peak,row['peak_torque_nm'],'Torque')
    near(rmse,audit['rmse_mm'],'RMSE');near(speed,audit['peak_speed_mps'],'Speed')
    del error,twist,physical_time
    with np.load(run/'research_substeps.npz') as z:
        human=z['contact_force_sum'][:,2].astype(float)
        ext=z['external_penetration_m'];edge=z['edge_penetration_m']
    require(len(human)==len(dt)==len(ext)==len(edge),'Telemetry alignment')
    require(all(np.isfinite(x).all() for x in (human,ext,edge)),'Nonfinite contact telemetry')
    peak_penetration=float(max(ext.max(),edge.max())*1000)
    near(float(ext.max()*1000),audit['penetration_mm'],'External penetration')
    near(float(edge.max()*1000),audit['edge_penetration_mm'],'Edge penetration')
    full=result['abort_reason'] is None and len(time)==1375
    require(result['full_task_horizon_completed']==full,'Horizon gate mismatch')
    if full:near(duration,55.,'Full55-second horizon')
    # Same frozen planned-hand-corner reducer, using saved hold/lift telemetry.
    # This verifies the reducer; it does not reconstruct contact-supported hold
    # from a new physics rollout or claim independent full-physics replay.
    require(result['success_definition'].startswith('planned-hand-corner-v1'),'Unregistered gate')
    task=bool(full and result['placement_hold_s']>=.5 and result['max_lift_m']>.10)
    strict=bool(task and result['abort_reason'] is None and ext.max()<=.0002 and edge.max()<=.0002)
    require(task==row['task_success']==audit['task_success']==result['task_success'],'Task reducer mismatch')
    require(strict==row['strict_success']==audit['strict_success']==result['strict_success'],'Strict reducer mismatch')
    finish=None
    if task:
        hold=result['placement_hold_s']; n=int(round(hold/.04))
        require(13<=n<=len(time),'Invalid success hold duration')
        finish=float(time[-1] - n*.04 + 13*.04)
    near(finish,row['completion_time_s'],'Completion time',atol=3e-8)
    physical_model=mujoco.MjModel.from_binary_path(str(run/'rollout.mjb'))
    limits=np.abs(physical_model.actuator_ctrlrange[:7,1]);threshold=limits*.5
    np.testing.assert_array_equal(threshold,[43.5]*4+[6]*3)
    contact=human>.05
    good=np.all(np.abs(torque[:,:7])<=threshold*(1+1e-6),axis=1)
    contact_s=float(dt[contact].sum());good_s=float(dt[contact & good].sum())
    ratio=good_s/contact_s if contact_s else None
    c=row['comfort']
    near(contact_s,c['human_contact_duration_s'],'Contact denominator')
    near(ratio,c['human_comfort_torque_compliance'],'Comfort fraction')
    near(peak_penetration,c['max_penetration_mm'],'Penetration aggregate')
    near(np.abs(torque[:,:7]).max(axis=0),c['peak_torque_by_joint_nm'],'Per-joint torque')
    violation=bool(peak_penetration>.2+1e-12 or np.any(np.abs(torque[:,:7])>limits*(1+1e-6)) or result['abort_reason'])
    require(violation==c['machine_safety_violation'],'Machine-safety classification')
    return dict(method=row['method'],condition=row['condition'],run=str(run),
                source_hashes={k:v for k,v in row.items() if k.endswith('_sha256')},
                physical_substeps=len(dt),duration_s=duration,
                task_success=task,strict_success=strict,completion_time_s=finish,rmse_mm=rmse,
                peak_torque_nm=peak,peak_speed_mps=speed,max_penetration_mm=peak_penetration,
                contact_duration_s=contact_s,comfort_ratio=ratio,common_filter_replay_max_abs=0.,
                actor_scope='Existing verified learned actor replay receipt' if learned else 'Policy trace consistency only; no independent classical actor replay',
                machine_safety_violation=violation)


def audit(root,progress,include_learned=False,condition_id=None):
    reg=read(root/'REGISTRATION.json');state=read(root/'execution.json')
    if not progress:require(state['status']=='complete','Final audit requires complete72, not a running/partial matrix')
    require(sha(root/'REGISTRATION.json')==state['registration_sha256'],'Registration changed')
    for name,key in [('MODEL_LOCK.json','models_sha256'),('PROTOCOL.json','protocol_sha256'),
                     ('CONDITIONS.json','conditions_sha256'),('LEARNED_ORIGINAL_REPORT.json','learned_report_sha256')]:
        require(sha(root/name)==reg[key],'Registered file changed')
    for directory,key in [('physics_source','physics_source_sha256'),('coordinator','coordinator_sha256'),('configs','config_sha256')]:
        check_manifest(root/directory,reg[key])
    parent=Path(reg['parent'])
    require(sha(parent/'MODEL_LOCK.json')==reg['parent_model_lock_sha256'],'Parent model lock changed')
    require(sha(parent/'REPORT.json')==reg['learned_report_sha256'],'Parent report changed')
    models={m['name']:m for m in read(root/'MODEL_LOCK.json')['models']}
    learned={m['name']:m for m in read(parent/'MODEL_LOCK.json')['models']}
    conditions={c['id']:c for c in read(root/'CONDITIONS.json')['conditions']}
    for m in models.values():check_manifest(Path(m['parameter_source']),m['parameter_source_sha256'])
    require(len(models)==6 and len(learned)==9 and len(conditions)==12,'Wrong matrix dimensions')
    require(sha(parent/'CONDITIONS.json')==reg['conditions_sha256'],'Different learned/classical conditions')
    sys.path.insert(0,str(root/'physics_source/scripts'))
    from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig
    complete={e['name'] for e in state['evaluation'] if e['status']=='complete'}
    partial=read(root/'PARTIAL_ROWS.json')['rows'] if (root/'PARTIAL_ROWS.json').exists() else []
    new=[r for r in partial if r['method']+'__'+r['condition'] in complete]
    require(len(new)==len(complete),'Missing completed classical receipts')
    if condition_id is not None:
        require(progress and not include_learned,'Condition mode is classical progress only')
        require(condition_id in conditions,'Unknown condition')
        new=[r for r in new if r['condition']==condition_id]
        require(len(new)==6 and {r['method'] for r in new}==set(models),'Condition audit requires all6 classical episodes complete')
    rows=new if progress and not include_learned else read(parent/'REPORT.json')['rows']+new
    ids={(r['method'],r['condition']) for r in rows}
    require(len(ids)==len(rows),'Duplicate episode receipts')
    if not progress:
        expected={(m,c) for m in list(models)+list(learned) for c in conditions}
        require(ids==expected and len(rows)==180,'Incomplete180 grid')
    checked=[]
    for r in rows:
        model=(learned if r['method'] in learned else models)[r['method']]
        checked.append(audit_row(r,root,model,conditions[r['condition']],VelocityResidualActionFilter,
                                 VelocityResidualSafetyConfig,r['method'] in learned))
    out=dict(status='progress_saved_physics_audit_passed' if progress else 'final180_saved_physics_audit_passed',
        created_utc=datetime.now(timezone.utc).isoformat(),auditor_sha256=sha(Path(__file__)),
        root=str(root),model_lock_sha256=sha(root/'MODEL_LOCK.json'),
        registration_sha256=sha(root/'REGISTRATION.json'),classical_completed=len(new),
        audited_episodes=len(checked),physical_substeps=sum(r['physical_substeps'] for r in checked),rows=checked,
        limitations=['No new physics or independent classical actor/servo replay.',
                    'Task reducer checked from saved hold/lift; no independent reconstruction of all placement-contact geometry.',
                    'Learned actor replay inherited from matching original audit receipt; public filter freshly replayed.'])
    if condition_id is not None:
        out.update(status='completed_classical_condition_audit_passed_not_final',condition=condition_id)
    if not progress:
        report=read(root/'REPORT.json')
        require(sha(root/'REPORT.json')==state['report_sha256'],'Final report hash mismatch')
        reported={(r['method'],r['condition']):r for r in report['rows']}
        require(set(reported)==ids,'Final report missing identities')
        times=[r['completion_time_s'] for r in checked if r['task_success']]
        tref=min(times) if times else None
        near(tref,report['t_ref_s'],'GlobalTask reference')
        for r in checked:
            item=reported[r['method'],r['condition']]
            near(tref/max(tref,r['completion_time_s']) if r['task_success'] else None,
                 item['spt_task_conditional'],'Per-episode conditionalSPT')
        for m in report['methods']+report['learned_family_pooled']:
            group=[r for r in checked if r['method']==m['method'] or r['method'].startswith(m['method']+'_s')]
            good=[r for r in group if r['task_success']]
            require(m['episodes']==len(group) and m['task_success']==len(good)==m['spt_task_conditional_n'],'Success denominator')
            require(m['strict_success']==sum(r['strict_success'] for r in group),'Strict denominator')
            near(float(np.mean([tref/max(tref,r['completion_time_s']) for r in good])) if good else None,
                 m['spt_task_conditional_mean'],'Conditional mean')
            near(float(np.mean([r['completion_time_s'] for r in good])) if good else None,
                 m['completion_time_mean_s_task'],'Completion mean')
            near(float(np.mean([r['peak_torque_nm'] for r in group])),m['peak_torque_mean_nm'],'Torque mean')
            near(max(r['peak_torque_nm'] for r in group),m['peak_torque_worst_nm'],'Torque worst')
            total=sum(r['contact_duration_s'] for r in group)
            ratio=sum((r['comfort_ratio'] or 0)*r['contact_duration_s'] for r in group)/total if total else None
            near(ratio,m['human_comfort_torque_compliance_contact_time_weighted'],'Pooled contact ratio')
            near(float(np.mean([r['machine_safety_violation'] for r in group])),m['machine_safety_violation_rate'],'Safety rate')
        out.update(report_sha256=sha(root/'REPORT.json'),t_ref_s=tref)
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--progress',action='store_true')
    p.add_argument('--include-learned',action='store_true',help='Also audit all original108 during progress; still not final approval')
    p.add_argument('--condition',help='Progress only: require and audit all6 classical episodes for one condition')
    a=p.parse_args();require(not a.output.exists(),'Never overwrite audit receipts')
    result=audit(a.root.resolve(),a.progress,a.include_learned,a.condition)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))
