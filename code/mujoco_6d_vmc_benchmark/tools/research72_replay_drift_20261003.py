"""Independent action-filter/integration diagnostics on imitation validation.

These are open-loop teacher-observation proxies, not simulated position errors
or closed-loop task results. No fitting, test history, or new physics is used.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


def read(p):
    return json.loads(p.read_text())


def filtered(actions):
    filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
    values=[filt.filter(action,.04) for action in actions]
    return np.asarray([v.cartesian_yield_twist for v in values]),np.asarray([v.wbc_scale for v in values])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',type=Path,required=True)
    p.add_argument('--metadata',type=Path,required=True)
    p.add_argument('--learning',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    state=read(a.learning/'execution.json');assert state['status']=='complete'
    meta=read(a.metadata);assert sha(a.data)==meta['training_data_sha256']
    with np.load(a.data) as z:
        episode=z['episode'].copy();train=z['train'].copy().astype(bool)
        target=z['requested_teacher_action'].copy()
        actual_twist=z['executed_yield_twist'].copy();actual_scale=z['executed_wbc_scale'].copy()
    ids=np.unique(episode[~train]);assert len(ids)==6
    references={}
    for eid in ids:
        indices=np.flatnonzero(episode==eid)
        assert len(indices)==1375 and not train[indices].any()
        lineage=next(row for row in meta['lineage'] if row['episode']==int(eid))
        assert lineage['data_role']=='imitation_validation'
        twist,scale=filtered(target[indices])
        np.testing.assert_array_equal(twist,actual_twist[indices])
        np.testing.assert_array_equal(scale,actual_scale[indices])
        references[int(eid)]=(indices,twist,scale,lineage['condition_id'])
    rows=[]
    for model in state['rows']:
        directory=a.learning/model['name'];cp=directory/'checkpoint.npz'
        assert sha(cp)==model['checkpoint_sha256']
        assert sha(directory/'TRAINING_COMPLETE.json')==model['training_metadata_sha256']
        replay=directory/'exported_replay.npz'
        with np.load(replay) as z:
            np.testing.assert_array_equal(z['episode'],episode)
            prediction=z['prediction'].copy()
        assert prediction.shape==target.shape and np.isfinite(prediction).all()
        episodes=[]
        for indices,teacher_twist,teacher_scale,condition in references.values():
            twist,scale=filtered(prediction[indices])
            drift=np.cumsum((twist[:,:3]-teacher_twist[:,:3])*.04,axis=0)
            episodes.append(dict(condition_id=condition,
                requested_action_mse=float(np.mean((prediction[indices]-target[indices])**2)),
                filtered_linear_velocity_rmse_mps=float(np.sqrt(np.mean(np.sum((twist[:,:3]-teacher_twist[:,:3])**2,axis=1)))),
                open_loop_integrated_residual_error_final_mm=(1000*drift[-1]).tolist(),
                open_loop_integrated_residual_error_peak_mm=float(1000*np.linalg.norm(drift,axis=1).max()),
                open_loop_integrated_residual_error_rms_mm=float(1000*np.sqrt(np.mean(np.sum(drift**2,axis=1)))),
                wbc_scale_absolute_difference_s=float(.04*np.abs(scale-teacher_scale).sum())))
        rows.append(dict(name=model['name'],family=model['family'],checkpoint_sha256=sha(cp),
            exported_replay_sha256=sha(replay),episodes=episodes))
    result=dict(completed_utc=now(),source_sha256=sha(Path(__file__)),
        data_sha256=sha(a.data),learning_execution_sha256=sha(a.learning/'execution.json'),
        metadata_sha256=sha(a.metadata),models=len(rows),identities=6,rows=rows,
        filtering='Same common filter and 40ms action interval, reset once per full identity; teacher executed target arrays independently reproduced.',
        interpretation='Residual-velocity integral under teacher observations only. Ignores closed-loop state changes, nominal-reference adaptation, contact mechanics and integration constraints. Not actual RMSE, placement drift or task success.',
        use='Diagnose systematic action bias and memory/temporal loss; no final-test history or tuning is performed here.')
    write(out/'REPLAY_DRIFT.json',result)
    print(json.dumps(dict(models=len(rows),validation_identities=6,physics_steps=0)))


if __name__=='__main__':
    main()
