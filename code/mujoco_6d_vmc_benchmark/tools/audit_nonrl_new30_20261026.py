"""Independently verify new30 training coverage, validation and final physics.

--progress audits only completed fits from one coordinator snapshot. It never
selects a partial-grid winner or reports a partial physics matrix as final.
--replay-completed additionally checks completed candidates on the six existing
selection identities; it does not expose new conditions or change model choice.
Without --progress, all75 fit processes/108 hyperparameter candidates, nine
locked models and108 physical episodes are required.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path

import numpy as np

from run_nonrl_spt_matrix_20261025 import read, sha, now, completion_time


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def equal_number(actual, expected, label):
    if actual is None or expected is None:
        require(actual is expected, label)
    else:
        require(math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), label)


def actor_class(root, family):
    name = 'office_vmc_memory_esn_20260927' if family == 'esn' else 'office_mlp_rnn_20261002'
    spec = importlib.util.spec_from_file_location('audit_'+name, root/'physics_source/scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.OfficeVMCMemoryESN if family == 'esn' else module.OfficeMLPRNN


def replay_validation(root, family, checkpoint, obs, ep, train, target):
    actor=actor_class(root,family)(checkpoint)
    per_episode=[]; squared_error=0.; count=0
    for e in np.unique(ep[~train]):
        ids=np.flatnonzero(ep==e)
        require(not train[ids].any(),'Validation history includes training frames')
        actor.reset(); pred=np.asarray([actor.act(o) for o in obs[ids]])
        se=float(np.sum((pred-target[ids])**2));squared_error+=se;count+=target[ids].size
        per_episode.append(dict(episode=int(e),frames=len(ids),action_mse=se/target[ids].size))
    return dict(validation_mse=squared_error/count,episodes=per_episode)


def audit(root, progress, replay_completed=False):
    reg = read(root/'REGISTRATION.json')
    state_bytes = (root/'execution.json').read_bytes()
    state = json.loads(state_bytes)
    require(reg['schema'] == 'sii-nonrl-new30-20261026-v1', 'Wrong experiment schema')
    require(state['registration_sha256'] == sha(root/'REGISTRATION.json'), 'Registration mismatch')
    require(reg['data_sha256'] == sha(root/'data/training_data.npz'), 'Dataset changed')
    require(reg['metadata_sha256'] == sha(root/'data/DATA_COMPLETE.json'), 'Data provenance changed')
    require(reg['condition_sha256'] == sha(root/'CONDITIONS.json'), 'Conditions changed')
    require(reg['protocol_sha256'] == sha(root/'PROTOCOL.json'), 'Protocol changed')
    for directory, key in [('source','source_sha256'),('physics_source','physics_source_sha256')]:
        for relative,digest in reg[key].items():
            require(sha(root/directory/relative) == digest, f'Source changed: {directory}/{relative}')
    meta = read(root/'data/DATA_COMPLETE.json')
    require(meta['episodes']==30 and meta['training_identities']==24 and meta['validation_identities']==6, 'Data split declaration')
    require({r['parent_episode'] for r in meta['lineage']} == set(range(25,55)), 'Old25 or unknown histories included')
    with np.load(root/'data/training_data.npz') as z:
        obs,ep,train,target=[z[k].copy() for k in ['observation','episode','train','requested_teacher_action']]
        require(z['physical_execution'].all() and np.all(z['importance']==1), 'Real uniform-weight demonstrations required')
    require(obs.shape==(41250,48) and target.shape==(41250,7), 'Unexpected dataset shapes')
    require(len(np.unique(ep[train]))==24 and len(np.unique(ep[~train]))==6 and train.sum()==33000, 'Actual split mismatch')
    require(not set(ep[train]).intersection(ep[~train]), 'Identity leakage')
    training_ids=set(np.unique(ep[train]))
    fits = [f for f in state['fits'] if f['status']=='complete']
    require(len({f['name'] for f in fits}) == len(fits), 'Duplicate fit records')
    rows=[]
    neural_grid=list(itertools.product(reg['neural_grid']['learning_rate'],reg['neural_grid']['weight_decay']))
    seen_neural=set()
    schedules={}
    for f in fits:
        directory=Path(f['output']); m=read(directory/'TRAINING_COMPLETE.json')
        require(f['metadata_sha256']==sha(directory/'TRAINING_COMPLETE.json'),'Fit metadata changed')
        require(sha(directory/'checkpoint.npz')==m['checkpoint_sha256'],'Fit checkpoint changed')
        require(read(directory/'execution.json')['status']=='complete','Fit is not actually complete')
        require(f['seed'] in reg['seeds'] and m['seed']==f['seed'],'Fit seed mismatch')
        if f['family']=='esn':
            require(m['training_data_sha256']==reg['data_sha256'],'ESN data mismatch')
            grid={(c['rho'],c['input_gain'],c['ridge']) for c in m['candidates']}
            expected={(r,g,l) for r in reg['esn_grid']['rho'] for g in reg['esn_grid']['input_gain'] for l in reg['esn_grid']['ridge']}
            require(grid==expected and len(m['candidates'])==12,'Incomplete ESN search')
            for c in m['candidates']:
                require(sha(directory/(c['name']+'.npz'))==c['checkpoint_sha256'],'ESN candidate checkpoint changed')
            best=min(m['candidates'],key=lambda c:(c['holdout_mse'],c['name']))
            require(m['selected']==best and m['checkpoint_sha256']==best['checkpoint_sha256'],'Wrong ESN selection')
            score=best['holdout_mse']
        else:
            require(f['family'] in ('rnn','mlp') and m['kind']==f['family'], 'Neural family mismatch')
            pair=(m['learning_rate'],m['weight_decay'])
            require(pair in neural_grid, 'Unregistered neural hyperparameters')
            require(f['name']==f'{f["family"]}_s{f["seed"]}_candidate{neural_grid.index(pair):02d}', 'Candidate identity mismatch')
            key=(f['family'],f['seed'],*pair)
            require(key not in seen_neural, 'Duplicate neural hyperparameters')
            seen_neural.add(key)
            require(m['data_sha256']==reg['data_sha256'] and m['metadata_sha256']==reg['metadata_sha256'],'Neural data mismatch')
            require(m['updates']==m['selected_update']==reg['neural_updates'],'Nonterminal checkpoint or incomplete training')
            require(m['checkpoint_selection']=='final' and m['parent_checkpoint_sha256'] is None,'Unexpected selection/warm start')
            require(m['action_delta_weight']==0 and m['drift_weight']==0 and m['global_loss'] and m['raw_slowdown_loss'],'Training options mismatch')
            require(m['lr_schedule']=='cosine' and m['precision']=='float64' and m['target']=='requested','Training contract mismatch')
            require(m['batch_size']==8 and m['tbptt_steps']==64 and m['width']==128 and m['absolute_inputs'], 'Neural architecture/batch mismatch')
            require(m['unused_field_isolation_pass'] and m['zero_input_equilibrium_pass'], 'Neural input contract failed')
            require(sha(directory/'schedule.json')==m['schedule_sha256'],'Training schedule changed')
            if m['schedule_sha256'] not in schedules:
                schedule=read(directory/'schedule.json')
                require(len(schedule)==reg['neural_updates'], 'Schedule length mismatch')
                require(all(set(item[1]).issubset(training_ids) for item in schedule), 'Validation identities used by optimizer')
                schedules[m['schedule_sha256']]=True
            require(sha(directory/'exported_replay.npz')==m['exported_replay_sha256'],'Export replay changed')
            require(m['numpy_torch_max_abs']<=5e-5,'Failed neural export parity')
            score=m['groups']['real_identity_validation']['action_mse']
        require(np.isfinite(score),'Nonfinite score')
        rows.append(dict(name=f['name'],family=f['family'],seed=f['seed'],validation_mse=score,
                         checkpoint_sha256=m['checkpoint_sha256'],metadata_sha256=f['metadata_sha256']))
    result=dict(status='verified_training_progress_not_final',created_utc=now(),root=str(root),
                execution_status_at_snapshot=state['status'],current_at_snapshot=state.get('current'),
                execution_snapshot_sha256=hashlib.sha256(state_bytes).hexdigest(),
                registration_sha256=sha(root/'REGISTRATION.json'),source_sha256=sha(Path(__file__)),
                complete_fit_processes=len(fits),complete_by_family=dict(Counter(f['family'] for f in fits)),
                expected_fit_processes=75,expected_hyperparameter_candidates=108,completed_fits=rows,
                verified_source_files=len(reg['source_sha256'])+len(reg['physics_source_sha256']))
    if progress:
        if replay_completed:
            result['completed_candidate_validation_replay']=[]
            for row in rows:
                replay=replay_validation(root,row['family'],root/'learning'/row['name']/'checkpoint.npz',obs,ep,train,target)
                equal_number(replay['validation_mse'],row['validation_mse'],'Completed candidate validation mismatch')
                result['completed_candidate_validation_replay'].append(dict(name=row['name'],**replay))
            result['replay_scope']='Completed candidates only, same six model-selection identities. No partial-grid model selection or new-condition exposure.'
        return result
    require(state['status']=='complete' and len(fits)==75,'Training/evaluation not yet complete')
    require(Counter(f['family'] for f in fits)=={'esn':3,'rnn':36,'mlp':36},'Training coverage mismatch')
    require(seen_neural=={(family,seed,*pair) for family in ('rnn','mlp') for seed in reg['seeds'] for pair in neural_grid}, 'Incomplete neural grid')
    lock=read(root/'MODEL_LOCK.json'); report=read(root/'REPORT.json')
    require(lock['status']=='frozen' and len(lock['models'])==9,'Model lock incomplete')
    require(state['model_lock_sha256']==report['model_lock_sha256']==sha(root/'MODEL_LOCK.json'),'Model lock changed')
    require(state['report_sha256']==sha(root/'REPORT.json') and report['status']=='complete','Report mismatch')
    require(report['registration_sha256']==sha(root/'REGISTRATION.json'),'Report provenance mismatch')
    validation=[]
    models={m['name']:m for m in lock['models']}
    require(set(models)=={f'{f}_s{s}' for f in reg['families'] for s in reg['seeds']},'Model grid mismatch')
    for model in models.values():
        choices=[r for r in rows if r['family']==model['family'] and r['seed']==model['seed']]
        best=min(choices,key=lambda r:(r['validation_mse'],r['name']))
        require(best['name']==model['selected_trial'] and best['checkpoint_sha256']==model['checkpoint_sha256'],'Wrong locked selection')
        require(sha(Path(model['checkpoint']))==model['checkpoint_sha256'],'Locked checkpoint changed')
        replay=replay_validation(root,model['family'],model['checkpoint'],obs,ep,train,target)
        equal_number(replay['validation_mse'],model['validation_mse'],'Independent deployment validation MSE mismatch')
        validation.append(dict(method=model['name'],**replay))
    conditions={c['id']:c for c in read(root/'CONDITIONS.json')['conditions']}
    physics=report['rows']
    require(len(physics)==108 and {(r['method'],r['condition']) for r in physics}==set((m,c) for m in models for c in conditions),'Incomplete/duplicate physical grid')
    qualified=[r['completion_time_s'] for r in physics if r['task_success'] and r['strict_success']]
    require(all(t is not None and math.isfinite(t) and t>0 for t in qualified),'Invalid completion time')
    ref=min(qualified) if qualified else None;equal_number(ref,report['t_ref_s'],'Wrong global T_ref')
    supplement=[];verified_sources=set()
    for r in physics:
        run=Path(r['run']);m=models[r['method']]
        for key,file in [('audit_sha256','AUDIT.json'),('trace_sha256','rollout.npz'),('execution_sha256','execution.json'),
                         ('model_sha256','rollout.mjb'),('chain_sha256','execution_chain.npz'),
                         ('substep_metrics_sha256','rollout_metrics/substep_metrics.npz'),('research_substeps_sha256','research_substeps.npz')]:
            require(sha(run/file)==r[key],f'Physical hash mismatch:{run}/{file}')
        require(sha(root/'metrics'/f'{r["method"]}__{r["condition"]}.json')==r['metric_sha256'],'Metric hash mismatch')
        receipt=read(run/'execution.json'); audit_row=read(run/'AUDIT.json')
        require(receipt['status']=='complete','Physical worker incomplete')
        require(receipt['checkpoint_sha256']==m['checkpoint_sha256']==sha(run/'checkpoint.npz'),'Wrong physical checkpoint')
        require(sha(root/'configs'/f'{r["method"]}__{r["condition"]}.json')==receipt['config_sha256'],'Physical config mismatch')
        require(receipt['runtime_provenance']['research_condition']==conditions[r['condition']],'Physical condition mismatch')
        require(receipt['runtime_provenance']['physics_dt_s']==5e-5,'Wrong physics dt')
        require(receipt['python']==reg['simulation_python'] and receipt['mujoco']=='3.11.0', 'Wrong physics runtime')
        require(r['model_sha256']==read(root/'PROTOCOL.json')['formal_model_sha256'], 'Wrong frozen MJB')
        require(audit_row['actor_replay_performed'] and audit_row['action_replay_max_abs']==0 and audit_row['common_filter_replay_max_abs']==0,'Replay audit failed')
        require(r['task_success']==audit_row['task_success'] and r['strict_success']==audit_row['strict_success'],'Success flags mismatch')
        for relative,digest in receipt['source_sha256'].items():
            if (relative,digest) not in verified_sources:
                require(sha(root/'physics_source'/relative)==digest,'Physical execution source mismatch')
                verified_sources.add((relative,digest))
        equal_number(completion_time(run),r['completion_time_s'],'Completion extraction mismatch')
        expected=ref/max(r['completion_time_s'],ref) if ref is not None and r['task_success'] and r['strict_success'] else 0.
        equal_number(expected,r['spt'],'SPT mismatch')
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            dt=z['dt'];torque=np.abs(z['qfrc_actuator'][:,:7]).astype(float)
        with np.load(run/'research_substeps.npz') as z:
            force=z['contact_force_sum'][:,2].astype(float)
            penetration=1000*np.maximum(z['external_penetration_m'],z['edge_penetration_m'])
        require(len(dt)==len(force)==len(torque) and len(dt)>0,'Substep alignment')
        require(np.isfinite(torque).all() and np.isfinite(force).all() and np.allclose(dt,5e-5,rtol=0,atol=1e-12),'Invalid substep telemetry')
        threshold=np.array([43.5]*4+[6.]*3);contact=force>.05
        within=np.all(torque<=threshold*(1+1e-6),axis=1)
        duration=float(dt[contact].sum());compliance=float(dt[contact&within].sum()/duration) if duration else None
        equal_number(duration,r['comfort']['human_contact_duration_s'],'Contact duration mismatch')
        equal_number(compliance,r['comfort']['human_comfort_torque_compliance'],'Contact compliance mismatch')
        equal_number(float(torque.max()),r['peak_torque_nm'],'Raw peak torque mismatch')
        equal_number(float(penetration.max()),r['comfort']['max_penetration_mm'],'Penetration mismatch')
        require(np.isfinite(penetration).all(), 'Nonfinite penetration telemetry')
        reasons=[]
        if penetration.max()>.2+1e-12:reasons.append('penetration_gt_0.2mm')
        if np.max(torque/(2*threshold))>1+1e-6:reasons.append('actuator_torque_gt_limit')
        summary=read(run/'rollout.json')
        if summary.get('abort_reason'):reasons.append('episode_abort:'+summary['abort_reason'])
        require(reasons==r['comfort']['machine_safety_violation_reasons'] and bool(reasons)==r['comfort']['machine_safety_violation'], 'Machine safety classification mismatch')
        supplement.append(dict(method=r['method'],condition=r['condition'],substeps=len(dt),
            human_force_peak_n=float(force.max()),human_contact_impulse_ns=float(np.sum(force[contact]*dt[contact])),
            comfort_exceed_duration_s=float(dt[contact&~within].sum()),
            comfort_excess_integral_nm_s_by_joint=(np.maximum(torque[contact]-threshold,0)*dt[contact,None]).sum(0).tolist(),
            failure_stage=audit_row.get('stage') if not r['task_success'] else None,abort_reason=audit_row.get('abort_reason')))
    methods={m['method']:m for m in report['methods']}
    require(len(report['methods'])==9 and set(methods)==set(models), 'Aggregate method coverage mismatch')
    for name,method in methods.items():
        group=[r for r in physics if r['method']==name]
        duration=sum(r['comfort']['human_contact_duration_s'] for r in group)
        compliant=sum((r['comfort']['human_comfort_torque_compliance'] or 0)*r['comfort']['human_contact_duration_s'] for r in group)
        expected=dict(episodes=12,task_success=sum(r['task_success'] for r in group),
            strict_success=sum(r['strict_success'] for r in group),spt_mean=float(np.mean([r['spt'] for r in group])),
            peak_torque_mean_nm=float(np.mean([r['peak_torque_nm'] for r in group])),
            human_comfort_torque_compliance_contact_time_weighted=compliant/duration if duration else None,
            machine_safety_violation_rate=sum(r['comfort']['machine_safety_violation'] for r in group)/12)
        for key,value in expected.items():equal_number(method[key],value,f'Method aggregate mismatch: {name}/{key}')
    for family,stats in report['family_summary'].items():
        for key,stat in stats.items():
            values=[methods[f'{family}_s{seed}'][key]/12 if key in ('task_success','strict_success') else methods[f'{family}_s{seed}'][key] for seed in sorted(reg['seeds'])]
            require(len(stat['per_seed'])==3, 'Missing replicate statistics')
            for actual,expected in zip(stat['per_seed'],values):equal_number(actual,expected,'Per-seed aggregate mismatch')
            finite=all(v is not None for v in values)
            equal_number(stat['mean'],float(np.mean(values)) if finite else None,'Family mean mismatch')
            equal_number(stat['sample_sd'],float(np.std(values,ddof=1)) if finite else None,'Family sample SD mismatch')
    result.update(status='final_audit_passed',validation_replay=validation,verified_physical_episodes=108,
                  report_sha256=sha(root/'REPORT.json'),model_lock_sha256=sha(root/'MODEL_LOCK.json'),
                  t_ref_s=ref,contact_supplement=supplement,
                  limitation='Final validation MSE reuses model-selection identities;12 prospective conditions are independent closed-loop evaluation. No broad-world superiority claim.')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--progress',action='store_true')
    p.add_argument('--replay-completed',action='store_true')
    a=p.parse_args();require(not a.output.exists(),'Never overwrite an audit')
    require(not a.replay_completed or a.progress,'--replay-completed requires --progress')
    result=audit(a.root.resolve(),a.progress,a.replay_completed)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['completed_fits','contact_supplement','validation_replay','completed_candidate_validation_replay']},ensure_ascii=False))


if __name__=='__main__':main()
