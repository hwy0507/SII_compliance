"""Read-only timing/exposure diagnostics on completed public identities only.

Contact truth is used for offline analysis, never for actor or imitation targets.
These are associations; short-latency impacts do not alone prove unavoidability.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import sys
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now,ParameterTeacher


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--public-phase',type=Path,help='A registered public development phase, never final')
    p.add_argument('--condition',help='Require every registered candidate on this public identity')
    p.add_argument('--counterfactual-teacher',action='store_true',
        help='Diagnostic only: query original teacher on student observations; never actual-execution labels')
    p.add_argument('--readout-decomposition',action='store_true',
        help='Replay fixed-feature readout contributions at the queried contact frames, without fitting')
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
    assert bool(a.public_phase)==bool(a.condition)
    assert not a.counterfactual_teacher or a.public_phase
    assert not a.readout_decomposition or a.counterfactual_teacher
    teacher_config=None
    if a.counterfactual_teacher:
        assert sha(a.root/'teacher.json')==json.loads((a.root/'PROTOCOL.json').read_text())['teacher_config_sha256']
        teacher_config=json.loads((a.root/'teacher.json').read_text())
    if a.public_phase:
        spec=json.loads((a.public_phase/'SPECIFICATION.json').read_text())
        assert spec['protocol_sha256']==sha(a.root/'PROTOCOL.json')
        assert sha(a.root/'CONDITIONS.json')==json.loads((a.root/'PROTOCOL.json').read_text())['condition_file_sha256']
        public=json.loads((a.root/'CONDITIONS.json').read_text())['conditions']
        assert a.condition in {c['id'] for c in public if c['role']=='development'}
        assert a.condition in spec['conditions']
        paths=sorted(a.public_phase.glob(f'queue_*/*__{a.condition}/AUDIT.json'))
        expected={c['name']+'__'+a.condition for c in spec['candidates']}
        assert {path.parent.name for path in paths}==expected, 'Wait for every registered model, including failures'
    else:
        paths=sorted((a.root/'teacher_bank').glob('queue_*/train_*/AUDIT.json'))
        assert len(paths)==32
    assert all(json.loads((path.parent/'execution.json').read_text())['status']=='complete' for path in paths)
    out.mkdir(parents=True,exist_ok=False);rows=[]
    shutil.copy2(__file__,out/Path(__file__).name)
    for path in paths:
        run=path.parent;audit=json.loads(path.read_text());state=json.loads((run/'execution.json').read_text())
        assert state['status']=='complete' and state['runtime_provenance']['data_role']==('development' if a.public_phase else 'train')
        assert sha(run/'rollout.npz')==audit['trace_sha256']
        with np.load(run/'research_substeps.npz') as z:
            force=z['contact_force_sum'][:,5].copy();pen=z['external_penetration_m'].copy()
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            time=z['time'].copy();velocity=z['twist'][:,:3].copy()
        active=np.flatnonzero(force>.05);peak=int(np.argmax(pen))
        row=dict(condition_id=run.name,task=audit['task_success'],strict=audit['strict_success'],
            worst_pair=audit['worst_pair'],max_external_penetration_mm=float(pen[peak]*1000),
            peak_penetration_time_s=float(time[peak]),pillar_peak_force_n=float(force.max()),
            pillar_exposed=bool(len(active)),source_run=str(run),trace_sha256=audit['trace_sha256'],
            physics_sha256=sha(run/'research_substeps.npz'),metrics_sha256=audit['metrics_sha256'])
        if len(active):
            first=int(active[0]);t0=float(time[first]);window=(time>=max(0,t0-.04))&(time<=t0)
            with np.load(run/'rollout.npz') as z:
                clock=z['neuron_time'].copy();obs=z['observation'].copy();requests=z['applied_action'].copy()
            with np.load(run/'execution_chain.npz') as z:filtered=z['filtered_action'].copy()
            before=max(0,int(np.searchsorted(clock,t0,side='right')-1));after=np.flatnonzero((clock>=t0)&(clock<=t0+.16))
            row.update(first_pillar_contact_s=t0,hand_peak_speed_last40ms_mps=float(np.linalg.norm(velocity[window],axis=1).max(initial=0.)),
                previous_actor_time_s=float(clock[before]),time_since_actor_s=t0-float(clock[before]),
                precontact_estimated_wrench=obs[before,39:45].tolist(),precontact_request=requests[before].tolist(),
                precontact_filtered_action=filtered[before].tolist(),postcontact_actor_times_s=clock[after].tolist(),
                postcontact_estimated_wrench=obs[after,39:45].tolist(),postcontact_requests=requests[after].tolist(),
                peak_penetration_relative_to_first_pillar_s=float(time[peak]-t0),
                pillar_p95_active_force_n=float(np.percentile(force[active],95)))
            if teacher_config is not None:
                teacher=ParameterTeacher(teacher_config);queries=[]
                for observation in obs:
                    teacher.observe(observation);queries.append(teacher.act(observation[39:45]))
                queries=np.asarray(queries)
                at_peak=max(0,int(np.searchsorted(clock,time[peak],side='right')-1))
                selected=np.unique(np.r_[before,after,at_peak]).astype(int)
                row['counterfactual_teacher_query']=dict(
                    actual_execution=False,used_as_training_labels=False,
                    teacher_config_sha256=sha(a.root/'teacher.json'),
                    actor_times_s=clock[selected].tolist(),last_actor_before_peak_index=int(at_peak),
                    selected_actor_indices=selected.tolist(),estimated_wrench=obs[selected,39:45].tolist(),
                    position_error=obs[selected,20:23].tolist(),
                    student_requested_action=requests[selected].tolist(),
                    original_teacher_requested_action=queries[selected].tolist(),
                    student_filtered_action=filtered[selected].tolist(),
                    interpretation='Original teacher recurrent state replayed on actual student observations; hypothetical requests, not executed labels or proof of superior physical outcome.')
                if a.readout_decomposition:
                    with np.load(run/'checkpoint.npz') as checkpoint:
                        contract=str(checkpoint['contract'])
                    from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
                    from office_context_network_20261003 import OfficeContextNetwork
                    if contract in (OfficeVMCMemoryESN.contract,OfficeContextNetwork.contract):
                        model=(OfficeVMCMemoryESN if contract==OfficeVMCMemoryESN.contract else OfficeContextNetwork)(run/'checkpoint.npz')
                        actor=getattr(model,'core',model)
                        assert not actor.nonlinear and not actor.axis_separable and actor.weights.shape in ((424,7),(552,7))
                        assert actor.readout_activation=='clipped_linear' and actor.output_gain==1.
                        groups={'current_signed_load':slice(0,6),'signed_state':slice(6,134),
                                'current_absolute_load':slice(134,140),'absolute_state':slice(140,268),
                                'current_load_context':slice(268,412),'direct_context_forbidden':slice(412,424)}
                        if getattr(actor,'state_context_readout_w',None) is not None:
                            assert actor.weights.shape==(552,7)
                            groups.update(state_current_context=slice(412,540),direct_context_forbidden=slice(540,552))
                        decomposition=[];maximum=0.
                        for index,observation in enumerate(obs):
                            features=actor.features(observation);raw=features@actor.weights
                            prediction=np.clip(raw,-1.,1.);prediction[0]=np.clip(raw[0],0.,1.)
                            maximum=max(maximum,float(np.max(np.abs(prediction-requests[index]))))
                            if index in selected:
                                parts={key:(features[sl]@actor.weights[sl]).tolist() for key,sl in groups.items()}
                                np.testing.assert_allclose(np.sum(list(parts.values()),axis=0),raw,rtol=0,atol=1e-11)
                                decomposition.append(dict(actor_index=index,time_s=float(clock[index]),
                                    raw_before_clipping=raw.tolist(),contributions=parts,
                                    state_norm=float(np.linalg.norm(actor.state))))
                        assert maximum<1e-10
                        row['readout_decomposition']=dict(frames=decomposition,replay_max_abs=maximum,
                            checkpoint_sha256=sha(run/'checkpoint.npz'),
                            caveat='Algebraic feature contributions, not independent causal interventions; correlated features and cancellation are possible.')
        rows.append(row)
    assert len(rows)==len(paths)
    result=dict(completed_utc=now(),source_sha256=sha(Path(__file__)),rows=rows,
        count=len(rows),task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),
        failed_worst_pairs=dict(Counter(str(r['worst_pair']) for r in rows if not r['strict'])),
        data_role='development' if a.public_phase else 'train',
        public_condition=a.condition,phase=str(a.public_phase) if a.public_phase else None,
        limitations='Public identities only; hand speed is not link7 normal approach speed. Aggregate external peak may belong to another contact than first pillar. Timing association is not a causal impossibility proof. No diagnostics fed to actor or training labels.')
    write(out/'DIAGNOSTICS.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))


if __name__=='__main__':main()
