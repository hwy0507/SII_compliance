"""Describe recovery exposure in all24 train identities after collection ends.

Validation identities are counted and hash-checked for lineage, never used in
these tuning diagnostics. Exact actor replay and saved actions are evidence;
exposure statistics are descriptive and do not prove student learnability.
"""
import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT,read,sha,validate,write
from optimize_tool_contact_20261002 import ParameterTeacher


def runs(mask):
    lengths=[]; current=0
    for flag in mask:
        if flag: current+=1
        elif current:
            lengths.append(current);current=0
    if current: lengths.append(current)
    return lengths


def audit(collection, output):
    assert not output.exists()
    plan_path=collection/'COLLECTION_PLAN.json'
    plan=validate(plan_path);state=read(collection/'COLLECTION_PROGRESS.json')
    assert state['status']=='qualified_complete', 'Require complete qualified30; no partial coverage conclusion'
    assert state['plan_sha256']==sha(plan_path)
    assert len(state['episodes'])==len(plan['episodes'])==30
    rows=[]; excluded=[]; vectors={}
    for entry,receipt in zip(plan['episodes'],state['episodes']):
        assert entry['id']==receipt['id'] and receipt['status']=='qualified' and receipt['returncode']==0
        folder=Path(entry['folder']);q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert q['status']=='qualified'
        for name,digest in q['input_hashes'].items(): assert sha(folder/name)==digest,name
        execution=read(folder/'execution.json')
        assert execution['collection_plan_sha256']==sha(plan_path)
        assert execution['collection_identity']==entry['id']
        assert execution['teacher_config_sha256']==plan['teacher_config_sha256']
        if entry['split']=='validation':
            excluded.append(entry['id']);continue
        assert entry['split']=='train'
        actor=ParameterTeacher(read(folder/'teacher.json'));values=[]
        with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
            assert z['observation'].shape==(len(z['action']),48)
            np.testing.assert_allclose(np.diff(z['time']),.04,rtol=0,atol=1e-8)
            for obs,action in zip(z['observation'],z['action']):
                actor.observe(obs);np.testing.assert_array_equal(actor.act(obs[39:45]),action)
                norm=float(np.linalg.norm(obs[45:47]));h=min(1.,norm);direction=obs[45:47]/max(norm,1e-12)
                values.append([actor.recovery_memory,actor.recovery_memory*h*h,h,
                    obs[22],obs[16],obs[14:16]@direction,(obs[14:16]-obs[26:28])@direction,
                    -obs[39:41]@direction])
        a=np.asarray(values);vectors[entry['id']]=a;mask=a[:,1]>.5;lengths=runs(mask)
        rows.append(dict(id=entry['id'],scene=entry['scene'],frames=len(a),
            activation_over_half_frames=int(mask.sum()),activation_over_half_run_lengths_frames=lengths,
            longest_activation_over_half_s=max(lengths,default=0)*.04,
            mean=a.mean(0).tolist(),minimum=a.min(0).tolist(),maximum=a.max(0).tolist(),
            exact_actor_replay=True,trajectory_sha256=sha(folder/'trajectory.npz'),
            qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json')))
    assert len(rows)==24 and len(excluded)==6
    assert Counter(r['scene'] for r in rows)==Counter(rod=8,ball=8,corner=8)
    output.mkdir(parents=True)
    np.savez_compressed(output/'training_recovery.npz',**vectors)
    result=dict(status='complete_train_only',collection=str(collection),
        plan_sha256=sha(plan_path),progress_sha256=sha(collection/'COLLECTION_PROGRESS.json'),
        teacher_sha256=plan['teacher_config_sha256'],rows=rows,excluded_validation_identities=excluded,
        columns=['recovery_memory','activation','horizontal_path_weight','reference_minus_hand_z_m',
                 'nominal_z_mps','nominal_path_mps','actual_path_mps','estimated_opposing_force_n'],
        per_scene={scene:dict(frames=sum(r['frames'] for r in rows if r['scene']==scene),
            activation_over_half_frames=sum(r['activation_over_half_frames'] for r in rows if r['scene']==scene),
            longest_activation_over_half_s=max(r['longest_activation_over_half_s'] for r in rows if r['scene']==scene))
            for scene in ('rod','ball','corner')},
        array_sha256=sha(output/'training_recovery.npz'),source_sha256=sha(Path(__file__)),
        actor_source_sha256=sha(ROOT/'tools/optimize_tool_contact_20261002.py'),
        limitation='Descriptive .5 activation threshold, not a task/qualification gate. No simulation, fitting, validation tuning or input additions. Marginal exposure is not sufficient joint coverage or a causal learning diagnosis.')
    write(output/'REVIEW.json',result);print(result['per_scene'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--collection',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();audit(a.collection.resolve(),a.output.resolve())
