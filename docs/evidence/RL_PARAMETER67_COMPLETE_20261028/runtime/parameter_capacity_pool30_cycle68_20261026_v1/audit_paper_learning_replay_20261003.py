"""Reproduce saved learning replays; separate synthetic and physical histories.

This is a development-data diagnostic, never a task-success or generalization
score. It does not fit, alter, select or deploy a checkpoint.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now
from current_student_policy_20260921 import load_current


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--names',nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    assert not a.output.exists()
    data=root/'recovery035_data/training_data.npz';metadata=json.loads((data.parent/'DATA_COMPLETE.json').read_text())
    digest=sha(data);assert digest==metadata['training_data_sha256']
    with np.load(data) as z:
        observation=z['observation'];episode=z['episode'];train=z['train'];target=z['requested_teacher_action']
    masks=dict(synthetic_training=(episode<48)&train,synthetic_identity_holdout=~train,
               native_successful_teacher=episode==48,local_failed_teacher=episode==49,counterfactual_student=episode>=50)
    rows=[]
    for name in a.names:
        path=root/name;meta=json.loads((path/'TRAINING_COMPLETE.json').read_text());checkpoint=path/'checkpoint.npz'
        assert meta.get('training_data_sha256',meta.get('data_sha256'))==digest
        assert sha(checkpoint)==meta['checkpoint_sha256']
        actor=load_current(checkpoint);previous=None;predictions=[]
        for eid,obs in zip(episode,observation):
            if eid!=previous:actor.reset();previous=eid
            predictions.append(actor.act(obs))
        predictions=np.asarray(predictions)
        with np.load(path/'exported_replay.npz') as z:
            np.testing.assert_array_equal(z['episode'],episode)
            maximum=float(np.max(abs(predictions-z['prediction'])))
            np.testing.assert_allclose(predictions,z['prediction'],rtol=0,atol=1e-10)
        error=predictions-target
        row=dict(name=name,seed=meta['seed'],checkpoint_sha256=sha(checkpoint),
                 metadata_sha256=sha(path/'TRAINING_COMPLETE.json'),exported_replay_sha256=sha(path/'exported_replay.npz'),
                 reproduced_max_abs=maximum,learned_parameters=meta.get('trainable_readout_coefficients',meta.get('trainable_parameters')),
                 partitions={key:dict(samples=int(mask.sum()),requested_action_mse=float(np.mean(error[mask]**2)),
                    mean_error_by_action=error[mask].mean(0).tolist()) for key,mask in masks.items()})
        rows.append(row)
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),training_data_sha256=digest,
        rows=rows,lineage=metadata['lineage'],samples=len(observation),
        limitations='Recorded development/synthetic histories only. Physical-history labels include successful and failed teachers plus explicit counterfactuals. Low action MSE is not closed-loop placement or compliance evidence. No final-condition data or post-test tuning.'))
    print(json.dumps(dict(models=len(rows),samples_per_model=len(observation),maximum_replay_error=max(r['reproduced_max_abs'] for r in rows))))


if __name__=='__main__':main()
