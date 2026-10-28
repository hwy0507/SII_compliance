"""Describe recovery activation on five training controls and office regression.

No fitting or simulator: replay actual canonical observations, require exact
actions, and retain descriptive state ranges. Marginal overlap cannot prove
joint distribution coverage or student learnability.
"""
import argparse
from pathlib import Path
import numpy as np

from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from optimize_tool_contact_20261002 import ParameterTeacher


def audit(root,output):
    assert not output.exists()
    reg,state=read(root/'REGISTRATION.json'),read(root/'execution.json')
    assert state['status']=='complete_pending_review'
    assert state['registration_sha256']==sha(root/'REGISTRATION.json')
    rows=[]
    for case in reg['cases']:
        actor=ParameterTeacher(read(Path(case['config'])))
        values=[]
        folder=root/case['id']
        if case['kind']=='scene':
            path=folder/case['scene']/'trajectory.npz'
            with np.load(path,allow_pickle=False) as data:
                obs,actions=data['observation'],data['action']
            sources={str(path):sha(path)}
        else:
            with np.load(folder/'rollout.npz',allow_pickle=False) as data:
                obs=data['observation']
            with np.load(folder/'execution_chain.npz',allow_pickle=False) as data:
                actions=data['requested_action']
            sources={str(folder/n):sha(folder/n) for n in ('rollout.npz','execution_chain.npz')}
        assert len(obs)==len(actions)
        for observation,expected in zip(obs,actions):
            actor.observe(observation)
            np.testing.assert_array_equal(actor.act(observation[39:45]),expected)
            norm=float(np.linalg.norm(observation[45:47]))
            horizontal=min(1.,norm)
            direction=observation[45:47]/max(norm,1e-12)
            values.append([actor.recovery_memory,actor.recovery_memory*horizontal**2,
                horizontal,observation[22],observation[16],
                observation[14:16]@direction,(observation[14:16]-observation[26:28])@direction,
                -observation[39:41]@direction])
        a=np.asarray(values)
        rows.append(dict(id=case['id'],kind=case['kind'],frames=len(a),
            exact_actor_replay=True,nonzero_memory_frames=int(np.count_nonzero(a[:,0])),
            activation_over_half_frames=int(np.count_nonzero(a[:,1]>.5)),
            mean=a.mean(0).tolist(),minimum=a.min(0).tolist(),maximum=a.max(0).tolist(),inputs=sources))
    result=dict(rows=rows,columns=['memory','activation','horizontal_path_weight','reference_minus_hand_z_m',
        'nominal_z_mps','nominal_path_mps','actual_path_mps','estimated_opposing_force_n'],
        registration_sha256=sha(root/'REGISTRATION.json'),source_sha256=sha(Path(__file__)),
        actor_source_sha256=sha(ROOT/'tools/optimize_tool_contact_20261002.py'),
        limitation='Five training controls only, not qualified30 or validation. Office is inspected regression, never labels. No physics, fitting, joint-coverage or learnability guarantee.')
    write(output,result)
    for row in rows: print(row['id'],row['nonzero_memory_frames'],row['activation_over_half_frames'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();audit(a.root.resolve(),a.output.resolve())
