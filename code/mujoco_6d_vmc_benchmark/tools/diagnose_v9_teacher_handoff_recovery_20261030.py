"""Saved actual teacher suffix diagnostics; no physics integration or fitting."""
import argparse
from pathlib import Path
import mujoco
import numpy as np
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_v9_paired_scene_closure_20261029 import verify_qualification


def summarize(folder):
    review=read(folder/'HANDOFF_REVIEW.json');receipt=read(folder/'HANDOFF_EXECUTION.json')
    q=verify_qualification(folder,review['qualification_sha256'])
    assert sha(folder/'HANDOFF_EXECUTION.json')==review['handoff_execution_sha256']
    assert sha(folder/'INDEPENDENT_AUDIT.json')==review['independent_audit_sha256']
    for name,digest in receipt['input_hashes'].items():assert sha(folder/name)==digest,name
    rod=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json');prefix=receipt['student_steps'];handoff_s=prefix*.04
    with np.load(folder/'trajectory.npz') as z:saved={k:z[k].copy() for k in z.files}
    with np.load(folder/'substeps.npz') as z:sub={k:z[k].copy() for k in z.files}
    with np.load(folder/'legacy.npz') as z:target=z['target'].copy();np.testing.assert_array_equal(z['time'],saved['time'])
    with np.load(folder/'handoff_actions.npz') as z:label={k:z[k].copy() for k in z.files}
    assert receipt['completed_steps']==len(saved['time'])==500
    np.testing.assert_array_equal(saved['action'][prefix:],label['teacher'][prefix:])
    dt=sub['dt'];time=sub['time'];penetration=sub['external_penetration_m']
    before=time<=handoff_s+1e-8;after=~before
    max_before=float(np.max(penetration[before]));max_after=float(np.max(penetration[after]))
    bad=np.flatnonzero(penetration>.0002)
    first_violation=float(time[bad[0]]) if len(bad) else None
    m=mujoco.MjModel.from_binary_path(str(folder/'scene.mjb'));d=mujoco.MjData(m)
    hand=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'hand')
    if hand<0:hand=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_BODY,'fr3_hand')
    assert hand>=0
    obs=saved['observation'];t=saved['time']
    at=min(len(t)-1,int(np.searchsorted(t,rod['hand_contact_first_s'])))
    direction=obs[at,45:48].copy();direction/=max(np.linalg.norm(direction),1e-12)
    positions=[]
    for i,ts in enumerate(t):
        for key in ('qpos','qvel','ctrl','mocap_pos','mocap_quat'):getattr(d,key)[:]=saved[key][i]
        d.time=float(ts);mujoco.mj_forward(m,d);positions.append(d.xpos[hand].copy())
    error=np.asarray(positions)-target;transverse=error-(error@direction)[:,None]*direction
    tube=np.linalg.norm(transverse,axis=1)
    window=(np.arange(len(t))>=prefix)&(t>=rod['pass_s'])&(t<rod['retract_start_s']) if rod['pass_s'] is not None else np.zeros(len(t),dtype=bool)
    recovery=None
    if window.any():
        best=np.flatnonzero(window)[np.argmin(tube[window])]
        recovery=dict(best_transverse_error_m=float(tube[best]),best_time_s=float(t[best]),
            best_transverse_xyz_m=transverse[best].tolist(),samples_within5mm=int(np.sum(tube[window]<=.005)),
            max_abs_executed_teacher_lateral_y_action=float(np.max(np.abs(saved['action'][window,2]))),
            max_abs_canonical_y_reference_error_m=float(np.max(np.abs(obs[window,21]))))
    names=['HANDOFF_REVIEW.json','HANDOFF_EXECUTION.json','DEMONSTRATION_QUALIFICATION.json',
        'ROD_YIELD_REJOIN_AUDIT_V3.json','trajectory.npz','substeps.npz','legacy.npz']
    return dict(folder=str(folder),handoff_s=handoff_s,qualified=review['qualified'],task=q['task_success'],
        safety=q['safety_valid'],behavior=q['scene_contact_valid'],rod_checks=rod['checks'],
        pass_s=rod['pass_s'],rejoin_s=rod['rejoin_confirmed_s'],retract_start_s=rod['retract_start_s'],
        prefix_max_penetration_m=max_before,teacher_suffix_max_penetration_m=max_after,
        first_penetration_over02mm_s=first_violation,
        violation_already_in_student_prefix=first_violation is not None and first_violation<=handoff_s+1e-8,
        post_pass_actual_teacher_window=recovery,source_sha256=sha(Path(__file__)),
        input_hashes={n:sha(folder/n) for n in names},
        limitations='Observed suffix on this actual history. First-pass interval does not recheck held/gap each sample; original rod audit decides behavior. Prefix safety violations cannot be attributed to later teacher actions. No integration/test/fitting.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    base=ROOT/'outputs/nonrl_v9_teacher_handoff_probes_20261030_v1'
    state=read(base/'HANDOFF.json');assert state['status']=='two_probes_complete_pending_data_repair_decision'
    rows=[summarize(base/('rod00_prefix'+str(n))/'rod') for n in (175,275)]
    write(a.output,dict(status='actual_suffix_saved_state_diagnosis',rows=rows,
        campaign_sha256=sha(base/'HANDOFF.json'),no_new_physics=True,no_test_or_fit=True))
    print([(r['handoff_s'],r['qualified'],r['prefix_max_penetration_m'],r['teacher_suffix_max_penetration_m'],r['post_pass_actual_teacher_window']) for r in rows])
