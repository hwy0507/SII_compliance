"""Synthetic stall/progress diagnostic of frozen memory, never training data.

A causal input intervention tests whether a load-triggered state persists while
motion is stalled, then decays when progress resumes. It does not simulate a
physically realizable robot/contact trajectory or establish task superiority.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from optimize_tool_contact_20261002 import ParameterTeacher,ROOT,sha,write,now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--learning',type=Path,required=True)
    p.add_argument('--teacher-config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--data',type=Path)
    p.add_argument('--metadata',type=Path)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    fitted=json.loads((a.learning/'execution.json').read_text());assert fitted['status']=='complete'
    teacher_config=json.loads(a.teacher_config.read_text())
    sources=[Path(__file__),ROOT/'tools/optimize_tool_contact_20261002.py',
             ROOT/'scripts/office_vmc_memory_esn_20260927.py',ROOT/'scripts/vmc_teacher_stable_readout_20260930.py']
    hashes={str(s.relative_to(ROOT)):sha(s) for s in sources}
    state=dict(status='running',started_utc=now(),argv=sys.argv,source_sha256=hashes,physics_steps=0,training_updates=0)
    write(out/'execution.json',state)
    try:
        traces={};rows=[]
        models=[m for m in fitted['rows'] if m['family'] in ('esn','memoryless')]
        for branch in ('continued_stall','motion_progress','intent_removed'):
            obs=np.zeros((275,48));obs[:,14]=.03;obs[:,26]=.03;obs[:,45]=1.
            obs[:25,39]=-4.
            if branch=='motion_progress':obs[25:,26]=0.
            if branch=='intent_removed':obs[25:,14]=0.;obs[25:,26]=0.
            teacher=ParameterTeacher(teacher_config);teacher_actions=[];teacher_memory=[]
            for o in obs:
                teacher.observe(o);teacher_actions.append(teacher.act(o[39:45]));teacher_memory.append(teacher.recovery_memory)
            teacher_actions=np.asarray(teacher_actions);teacher_memory=np.asarray(teacher_memory)
            traces[branch+'_observation']=obs;traces[branch+'_teacher_action']=teacher_actions
            traces[branch+'_teacher_recovery_memory']=teacher_memory
            for m in models:
                checkpoint=a.learning/m['name']/'checkpoint.npz';assert sha(checkpoint)==m['checkpoint_sha256']
                actor=OfficeVMCMemoryESN(checkpoint);actions=[];reservoir=[]
                for o in obs:actions.append(actor.act(o));reservoir.append(actor.state.copy())
                actions=np.asarray(actions);reservoir=np.asarray(reservoir)
                assert np.isfinite(actions).all() and np.isfinite(reservoir).all()
                prefix=branch+'__'+m['name'];traces[prefix+'_action']=actions;traces[prefix+'_state']=reservoir
                norm=np.linalg.norm(reservoir,axis=1)
                rows.append(dict(branch=branch,name=m['name'],family=m['family'],checkpoint_sha256=sha(checkpoint),
                    teacher_memory_after_load=float(teacher_memory[24]),teacher_memory_final=float(teacher_memory[-1]),
                    reservoir_norm_after_load=float(norm[24]),reservoir_norm_final=float(norm[-1]),
                    reservoir_norm_retention=float(norm[-1]/norm[24]) if norm[24]>0 else None,
                    final_2s_mean_teacher_action=teacher_actions[-50:].mean(0).tolist(),
                    final_2s_mean_student_action=actions[-50:].mean(0).tolist(),
                    final_2s_requested_action_mse=float(np.mean((actions[-50:]-teacher_actions[-50:])**2))))
        np.savez_compressed(out/'synthetic_traces.npz',**traces)
        result=dict(completed_utc=now(),source_sha256=hashes,teacher_config_sha256=sha(a.teacher_config),
            trace_sha256=sha(out/'synthetic_traces.npz'),rows=rows,
            input='1s opposing estimated load while commanded speed30mm/s and actual speed0; then10s zero estimated load with stalled/progress/no-intent branches.',
            data_role='synthetic mechanism probe only; not a demonstration, development condition or physical rollout',
            limitations=['These observations need not be dynamically realizable; no contact/state consistency is asserted.',
                'Teacher state retention and ESN forgetting are mechanistic diagnostics, not proof of a real failure cause.',
                'Do not add these traces to imitation data or report their error as task performance.',
                'No new candidate fitted, checkpoint modified, budget expanded or sealed history read.'])
        if a.data is not None:
            assert a.metadata is not None
            metadata=json.loads(a.metadata.read_text());assert sha(a.data)==metadata['training_data_sha256']
            assert all(r['data_role'] in ('train','imitation_validation') for r in metadata['lineage'])
            with np.load(a.data) as z:
                observations=z['observation'].copy();episode=z['episode'].copy();train=z['train'].astype(bool)
                target=z['requested_teacher_action'].copy()
            memories=np.zeros(len(episode));replayed=np.zeros_like(target)
            for eid in np.unique(episode):
                teacher=ParameterTeacher(teacher_config)
                for i in np.flatnonzero(episode==eid):
                    o=observations[i];teacher.observe(o);replayed[i]=teacher.act(o[39:45]);memories[i]=teacher.recovery_memory
            maximum=float(np.max(np.abs(replayed-target)))
            assert maximum<1e-12,'Teacher replay differs from the actual requested labels'
            force_norm=np.linalg.norm(observations[:,39:42],axis=1)
            evidence=[]
            for role,mask in [('train',train),('imitation_validation',~train)]:
                for threshold in (.05,.5,1.):
                    selected=mask&(force_norm<threshold)&(memories>.5)
                    evidence.append(dict(role=role,estimated_force_threshold_n=threshold,
                        recovery_memory_threshold=.5,frames=int(selected.sum()),seconds=float(.04*selected.sum()),
                        identities=int(len(np.unique(episode[selected])))))
            result['real_history_coverage']=dict(data_sha256=sha(a.data),metadata_sha256=sha(a.metadata),
                exact_teacher_replay_max_abs=maximum,rows=evidence,
                interpretation='Estimated linear load magnitude and reconstructed causal teacher memory only. These counts do not establish ESN closed-loop failure or physical contact absence.')
        write(out/'MECHANISM.json',result)
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        state.update(status='complete',models=len(models),branches=3,trace_sha256=result['trace_sha256'])
        print(json.dumps({k:v for k,v in state.items() if k not in ('source_sha256','argv')}))
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
