"""Same-identity rod rejoin margins: teacher, passing MLP and three failures.

Saved-state mj_forward only; frozen gate/source and initial-state checks.
No fitting, no test histories, no counterfactual dynamics claims.
"""
import argparse
from pathlib import Path

import mujoco
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current
from run_video_reference_coverage_20261029 import make_actor
from review_v9_paired_scene_closure_20261029 import verify_qualification


def summarize(label,folder):
    names=('trajectory.npz','legacy.npz','legacy.json','scene.mjb','teacher.json',
           'DEMONSTRATION_QUALIFICATION.json','ROD_YIELD_REJOIN_AUDIT_V3.json')
    before={n:sha(folder/n) for n in names}
    q=verify_qualification(folder,before['DEMONSTRATION_QUALIFICATION.json'])
    rod=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
    assert rod['hashes']['audit_rod_yield_rejoin_v3_20261028.py']==sha(ROOT/'tools/audit_rod_yield_rejoin_v3_20261028.py')
    for n,h in rod['hashes'].items():
        if n!='audit_rod_yield_rejoin_v3_20261028.py':assert sha(folder/n)==h
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
        saved={k:z[k] for k in z.files}
    with np.load(folder/'legacy.npz',allow_pickle=False) as z:
        target=z['target'].copy();np.testing.assert_array_equal(z['time'],saved['time'])
    observations=saved['observation'];actions=saved['action'];time=saved['time']
    if (folder/'student_checkpoint.npz').exists():
        actor=load_current(folder/'student_checkpoint.npz');actor.reset()
        np.testing.assert_array_equal(np.asarray([actor.act(o) for o in observations]),actions)
    else:
        actor=make_actor(read(folder/'teacher.json'));pred=[]
        for o in observations:actor.observe(o);pred.append(actor.act(o[39:45],.04))
        np.testing.assert_array_equal(pred,actions)
    model=mujoco.MjModel.from_binary_path(str(folder/'scene.mjb'));data=mujoco.MjData(model)
    hand=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
    if hand<0:hand=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'fr3_hand')
    assert hand>=0
    i=min(len(time)-1,int(np.searchsorted(time,rod['hand_contact_first_s'])))
    direction=observations[i,45:48].copy();direction/=max(np.linalg.norm(direction),1e-12)
    positions=[]
    for i,t in enumerate(time):
        for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):getattr(data,key)[:]=saved[key][i]
        data.time=float(t);mujoco.mj_forward(model,data);positions.append(data.xpos[hand].copy())
    error=np.asarray(positions)-target
    transverse=error-(error@direction)[:,None]*direction
    tube=np.linalg.norm(transverse,axis=1)
    assert rod['pass_s'] is not None
    mask=(time>=rod['pass_s'])&(time<rod['retract_start_s'])
    assert mask.any()
    best=np.flatnonzero(mask)[int(np.argmin(tube[mask]))]
    assert before=={n:sha(folder/n) for n in names}
    return dict(label=label,folder=str(folder),qualified=q['status']=='qualified',
        task_success=q['task_success'],safety_valid=q['safety_valid'],scene_behavior_valid=q['scene_contact_valid'],
        frozen_behavior_checks=rod['checks'],pass_s=rod['pass_s'],rejoin_confirmed_s=rod['rejoin_confirmed_s'],
        retract_start_s=rod['retract_start_s'],post_first_pass_hold_window_s=float(time[mask][-1]-time[mask][0]),
        # This diagnostic interval does not recheck held/crossing/gap each
        # sample; only the original rod audit decides behavior qualification.
        best_transverse_error_m=float(tube[best]),best_time_s=float(time[best]),
        best_transverse_xyz_m=transverse[best].tolist(),
        post_first_pass_samples_within_5mm=int(np.sum(tube[mask]<=.005)),
        max_external_penetration_m=q['metrics']['max_external_penetration_m'],
        saturation_fraction=float(np.mean(np.any(np.abs(actions[:,1:])>=.999,axis=1))),
        first_observation=observations[0].tolist(),model_sha256=before['scene.mjb'],input_hashes=before)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    plan=read(ROOT/'outputs/special_scene_direction_collection_20261029_v9/COLLECTION_PLAN.json')
    teacher=Path(next(e['folder'] for e in plan['episodes'] if e['id']=='rod_00'))
    base=ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3'
    folders=[('teacher',teacher),('mlp_seed01_rank1_passed',ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5/rod_00_mlp_scratch/rod')]
    for rank in (1,2,3):
        folders.append(('mlp_seed02_rank'+str(rank)+'_failed',base/'evaluations'/('mlp_scratch_s2026102802_rank'+str(rank))/'rod_00/rod'))
    rows=[summarize(label,folder) for label,folder in folders]
    for row in rows[1:]:
        assert row['model_sha256']==rows[0]['model_sha256']
        np.testing.assert_array_equal(row['first_observation'],rows[0]['first_observation'])
    write(a.output,dict(status='same_identity_development_rejoin_diagnosis_no_physics',rows=rows,
        same_initial_canonical48_and_mjb=True,source_sha256=sha(Path(__file__)),
        limitations=['Five different closed-loop histories; not a common-input accuracy ranking.',
            'Tube error is against the original nominal target and hand body, as in the frozen audit.',
            'The interval after first crossing is diagnostic, not a replacement for per-sample behavior gating.',
            'No dynamics integration/fitting/test access; does not prove recovery on failed student histories.']))
    print([(r['label'],r['qualified'],r['best_transverse_error_m'],r['post_first_pass_samples_within_5mm']) for r in rows])
