"""Independent raw person-contact segmentation for c05 versus c00 train 0."""
import argparse
import gc
import importlib.util
import json
from pathlib import Path
import resource
import sys

import numpy as np

from teacher_bank_validation_audit_20260930 import (read,load_columns,complete_execution,
    physical_metrics,action_replay,audit_duration,sha)


def independent_runs(raw,fixture):
    """Segment true consecutive physical samples; never bridge gaps or withdraw."""
    raw=np.asarray(raw,dtype=float)
    if raw.ndim!=2 or raw.shape[1]!=6 or not np.isfinite(raw).all():
        raise ValueError('Invalid complete person physical trace')
    if not len(raw) or np.any(raw[:,1]<=0) or np.any(raw[:,2]<0):
        raise ValueError('Missing or invalid physical samples')
    np.testing.assert_allclose(raw[1:,0],raw[:-1,0]+raw[:-1,1],rtol=0,atol=1e-8)
    axis=np.asarray(fixture['axis'],dtype=float)
    if axis.shape!=(3,) or not np.isfinite(axis).all() or np.linalg.norm(axis)<1e-12:
        raise ValueError('Invalid apparatus axis')
    axis=axis/np.linalg.norm(axis)
    start=fixture['start_s'];end=start+fixture['press_s']+fixture['hold_s']
    mask=(raw[:,2]>.05)&(raw[:,0]>=start-1e-9)&(raw[:,0]+raw[:,1]<=end+1e-9)
    changes=np.diff(np.r_[False,mask,False].astype(np.int8))
    starts=np.flatnonzero(changes==1);ends=np.flatnonzero(changes==-1)
    rows=[];detail=[]
    for first,stop in zip(starts,ends):
        run=raw[first:stop]
        delta=run[:,3:]-run[0,3:]
        axial=delta@axis
        signed=-axial
        duration=float(run[:,1].sum())
        displacement=float(max(0.,signed.max()))
        rows.append([float(run[0,0]),float(run[-1,0]+run[-1,1]),duration,
            float(np.linalg.norm(delta-axial[:,None]*axis,axis=1).max()),
            float(np.linalg.norm(delta,axis=1).max()),float(max(0.,delta[:,2].max())),
            float(run[:,2].max()),displacement])
        detail.append(dict(index=len(rows)-1,first_physical_index=int(first),stop_physical_index=int(stop),
            samples=len(run),min_force_n=float(run[:,2].min()),peak_force_n=float(run[:,2].max()),
            impulse_ns=float(np.sum(run[:,2]*run[:,1])),
            duration_margin_s=duration-.4,signed_yield_margin_m=displacement-.01,
            minimum_force_margin_n=float(run[:,2].min())-.05,
            qualified=bool(duration>.4+1e-12 and displacement>=.01)))
    return np.asarray(rows,dtype=float).reshape(-1,8),detail


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    root,output=args.run.resolve(),args.output.resolve()
    if output.exists() or output==root or root in output.parents:raise ValueError('New external directory required')
    plan=read(root/'plan.json')
    for name,digest in plan['sources'].items():
        if sha(root/'source'/name)!=digest:raise ValueError('Frozen source drift')
    if sha(root/'fixtures.json')!=plan['fixtures_sha256']:raise ValueError('Fixture manifest drift')
    sys.path.insert(0,str(root/'source/tools'));sys.path.insert(0,str(root/'source/scripts'))
    import mujoco
    if mujoco.__version__!=plan['mujoco_version']:raise ValueError('MuJoCo version mismatch')
    def forbidden(*unused,**kwargs):raise RuntimeError('No dynamics permitted')
    for name in ('mj_step','mj_step1','mj_step2'):setattr(mujoco,name,forbidden)
    spec=importlib.util.spec_from_file_location('frozen_person_runner',root/'source/tools/teacher_bank_rollout_20260930.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    from teacher_bank_design_20260930 import decode,digest
    from teacher_bank_exposure_20260930 import audit_saved
    cases={};paired=None
    output.mkdir(parents=True)
    for candidate in ('c00','c05'):
        folder=root/f'search/active_long/vmc/{candidate}/0'
        execution,skip=complete_execution(folder)
        if skip:raise ValueError('Completed training case required: '+skip)
        request,audit,meta=map(read,(folder/'request.json',folder/'audit.json',folder/'rollout.json'))
        audit_hash=sha(folder/'audit.json');execution_hash=sha(folder/'execution.json')
        fixture=request['fixture'];decision=read(folder.parent/'decision.json')
        if (fixture['category']!='active_long' or fixture['apparatus']!='person' or fixture['split']!='train'
                or request['method']!='vmc' or request['phase']!='search' or request['x']!=decision['x']
                or request['teacher']!=decode(request['x']) or request['plan_sha256']!=sha(root/'plan.json')
                or execution['plan_sha256']!=request['plan_sha256']):raise ValueError('Training request binding mismatch')
        if digest(fixture['active_physical_parameters'])!=fixture['physical_config_sha256']:
            raise ValueError('Physical config digest mismatch')
        hashes={name:sha(folder/name) for name in audit['files_sha256']}
        if hashes!=audit['files_sha256']:raise ValueError('Raw trace hash mismatch')
        if hashes['rollout.mjb']!=audit['model_sha256']:raise ValueError('MJB mismatch')
        identity=(fixture,audit['model_sha256'])
        if paired is not None and identity!=paired:raise ValueError('Unpaired c00/c05 environments')
        paired=identity
        measured,physics=physical_metrics(folder/'rollout_metrics/substep_metrics.npz',plan)
        for key in ('rmse_m','peak_torque_nm','peak_speed_mps'):
            np.testing.assert_allclose(measured[key],audit[key],rtol=2e-7,atol=1e-8)
        replay=action_replay(folder,request,physics,runner)
        duration=audit_duration(replay['action_count'],measured['actual_duration_s'],plan['duration_s'],meta.get('abort_reason'))
        arrays=load_columns(folder/'exposure.npz')
        binding=runner.audit_exposure_physics_binding(arrays,physics,fixture)
        raw=arrays['person_physics']
        runs,details=independent_runs(raw,fixture)
        np.testing.assert_allclose(runs,arrays['person_window_runs'],rtol=0,atol=1e-10)
        qualified=[r['index'] for r in details if r['qualified']]
        if qualified!=audit['exposure']['diagnostics']['accepted_run_indices']:
            raise ValueError('Independent accepted runs differ from original audit')
        frozen_exposure=audit_saved(folder/'exposure.npz',fixture)
        if frozen_exposure!=audit['exposure']:raise ValueError('Frozen exposure replay mismatch')
        press_start=fixture['start_s'];retract=press_start+fixture['press_s']+fixture['hold_s']
        window=(raw[:,0]>=press_start-1e-9)&(raw[:,0]+raw[:,1]<=retract+1e-9)
        loads=dict(full_episode_peak_n=float(raw[:,2].max()),full_episode_impulse_ns=float(np.sum(raw[:,1]*raw[:,2])),
            press_hold_peak_n=float(raw[window,2].max()),press_hold_impulse_ns=float(np.sum(raw[window,1]*raw[window,2])),
            scope='Independent aggregation of saved every-substep person force; simulator-derived contact force, not new dynamic reconstruction')
        penetration=meta['stats']['max_external_penetration_m']*1000
        if penetration!=audit['penetration_mm']:raise ValueError('Penetration metadata disagreement')
        if candidate=='c05' and not (qualified and audit['eligible'] and all(meta[k] for k in
                ('task_success','strict_success','placement_complete','release_supported','physical_valid'))):
            raise ValueError('Claimed c05 successful task/exposure not supported')
        if sha(folder/'audit.json')!=audit_hash or sha(folder/'execution.json')!=execution_hash:
            raise ValueError('Original completed metadata changed')
        np.savez_compressed(output/(candidate+'_independent_person_runs.npz'),runs=runs)
        cases[candidate]=dict(folder=str(folder),fixture=fixture,decision=decision,controller=request['teacher'],
            raw_sha256=hashes,audit_sha256=audit_hash,execution_sha256=execution_hash,execution=execution,
            original_eligible=audit['eligible'],original_failure_reasons=audit['failure_reasons'],
            metrics=measured,duration=duration,replay=replay,physical_exposure_binding=binding,
            independent_person_run_count=len(runs),qualified_run_indices=qualified,
            qualified_runs=[dict(values=runs[i].tolist(),**details[i]) for i in qualified],
            max_signed_push_m=float(runs[:,7].max()),longest_window_contact_s=float(runs[:,2].max()),
            full_runs_array_file=candidate+'_independent_person_runs.npz',contact_load=loads,
            evaluator_person_event=meta['stats']['events']['person_hand'],
            penetration=dict(external_mm=penetration,safety_margin_mm=.2-penetration,independently_recomputed=False,
                reason='No full physical-substep contact-distance trace; preserved evaluator maximum only'),
            evaluator_booleans={k:v for k,v in meta.items() if isinstance(v,bool)},task_events=meta['task_events'],
            abort_reason=meta.get('abort_reason'),frozen_exposure_audit=frozen_exposure)
        print(json.dumps(dict(candidate=candidate,eligible=audit['eligible'],qualified_runs=qualified,
            max_signed_push_m=cases[candidate]['max_signed_push_m'],peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)),flush=True)
        del arrays,raw,physics,runs,details
        gc.collect()
    report=dict(scope='One matched training hand-push condition: c05 vs c00, not validation or generalization. No thresholds changed.',
        contact_rule='Only complete physical intervals in press/hold, force >0.05N; a single uninterrupted run >0.4s and signed displacement along -axis >=0.01m. Origin resets at every gap; withdraw excluded.',
        caveat='Signed movement under contact is kinematic evidence; no no-push counterfactual, no causal separation from nominal motion. Margin reports are not robustness certifications.',
        source_run=str(root),plan_sha256=sha(root/'plan.json'),frozen_source_sha256=plan['sources'],
        script_sha256=sha(Path(__file__)),helper_sha256=sha(Path(__file__).with_name('teacher_bank_validation_audit_20260930.py')),
        cases=cases,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    (output/'review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    (output/'files_sha256.json').write_text(json.dumps({p.name:sha(p) for p in output.iterdir() if p.is_file()},indent=2)+'\n')
    print(json.dumps(dict(output=str(output),review_sha256=sha(output/'review.json'))))


if __name__=='__main__':main()
