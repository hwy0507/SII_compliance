"""Audit reference/input/runtime compatibility without modifying any policy."""
import ast
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def stats(o):
    e=o[:,20:23]
    return dict(frames=len(o),position_abs_max_xyz_m=np.abs(e).max(0).tolist(),
        position_norm_quantiles_50_95_100_m=np.quantile(np.linalg.norm(e,axis=1),[.5,.95,1]).tolist(),
        position_y_feature_saturation_fraction=float(np.mean(np.abs(e[:,1])>=.32)))
def function_ast(p,name):
    return ast.dump(next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)

def main():
    old=ROOT/'outputs/original_esn_old_office_transfer_20261013/episode_v2'
    previous=ROOT/'outputs/paired_baseline_development_20261012_v2'
    data=ROOT/'outputs/research72_20261003_1149/demonstrations_refined_v1/training_data.npz'
    meta=ROOT/'outputs/research72_20261003_1149/context_readout_refit_v1/readout_refit_esn_2026100301/TRAINING_COMPLETE.json'
    assert sha(data)==read(meta)['training_data_sha256']
    assert sha(old/'checkpoint.npz')==read(meta)['checkpoint_sha256']==sha(previous/'checkpoints/esn.npz')
    out=ROOT/'outputs/original_esn_transfer_contract_20261013';out.mkdir(exist_ok=False)
    z=np.load(data); train=z['train'];rows={role:stats(z['observation'][mask]) for role,mask in [('train',train),('validation',~train)]}
    original=[]
    for p in sorted((previous/'episodes').glob('esn__*/rollout.npz')):
        q=np.load(p);a=read(p.parent/'AUDIT.json');assert sha(p)==a['trace_sha256']
        original.append(dict(condition=p.parent.name,sha256=sha(p),**stats(q['observation'])))
    q=np.load(old/'rollout.npz');rows['old_office_full']=stats(q['observation'])
    m=(q['neuron_time']>=11.48-1e-7)&(q['neuron_time']<16.68-1e-7)
    rows['old_office_rod_window']=stats(q['observation'][m])
    eold=read(old/'execution.json');eprev=read(previous/'episodes/esn__repair_development_000/execution.json')
    source={}
    for name in ('validate_office_apparatus_v5_20260917.py','audited_velocity_env.py','wbc_velocity_residual_core.py',
                 'haptic_vmc_teacher_20260916.py','office_task_v4_20260917.py','fixed_panda_wbc.py'):
        key='scripts/'+name
        source[key]=dict(old=eold['source_sha256'][key],previous=eprev['source_sha256'][key])
        assert source[key]['old']==source[key]['previous']==sha(ROOT/key)
    same_filter=eold['action_filter_config']==eprev['action_filter_config'];assert same_filter
    models=[mujoco.MjModel.from_binary_path(str(p)) for p in (old/'rollout.mjb',previous/'episodes/esn__repair_development_000/rollout.mjb')]
    joint_maps=[[(mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_JOINT,j),int(m.jnt_qposadr[j]),int(m.jnt_dofadr[j])) for j in range(7)] for m in models]
    assert joint_maps[0]==joint_maps[1]
    parity={f:bool(np.array_equal(getattr(models[0],f)[:7],getattr(models[1],f)[:7])) for f in
        ('dof_damping','dof_frictionloss','dof_armature','actuator_gainprm','actuator_biasprm','actuator_gear','actuator_ctrlrange','actuator_forcerange')}
    assert all(parity.values())
    from_paths=[previous/'source/scripts/current_student_policy_20260921.py',ROOT/'scripts/current_student_policy_20260921.py']
    # Adapter changed only to accept extra unrelated contracts; don't falsely claim identical file hashes.
    import difflib
    adapter_diff=''.join(difflib.unified_diff(from_paths[0].read_text().splitlines(True),from_paths[1].read_text().splitlines(True)))
    (out/'adapter_diff.txt').write_text(adapter_diff)
    shared_frame=read(old/'rollout.json');previous_frame=read(previous/'episodes/esn__repair_development_000/rollout.json')
    value=dict(physics_rerun=False,policy_modified=False,training_data_sha256=sha(data),metadata_sha256=sha(meta),
        checkpoint_sha256=sha(old/'checkpoint.npz'),script_sha256=sha(Path(__file__)),
        observation_stats=rows,all_eight_original=original,same_common_filter=same_filter,
        common_runtime_source_parity=source,arm_joint_map=joint_maps[0],arm_parameter_parity=parity,
        adapter_diff_sha256=sha(out/'adapter_diff.txt'),
        observation_formula='q7,dq7,command6,target-minus-hand pose error6,command-minus-measured twist6,estimated load7,wrench6,direction3',
        old_planned_hand_corner=shared_frame['arguments']['planned_hand_corner'],
        previous_planned_hand_corner=previous_frame['arguments']['planned_hand_corner'],
        old_policy_hz=shared_frame['neural_logging']['policy_hz'],previous_policy_hz=previous_frame['neural_logging']['policy_hz'],
        findings=['Old wrapper explicitly disables planned_hand_corner, selecting PickPlaceTask far phase endpoint.',
          'PlannedCornerTask updates goals to local path waypoints; same observation formula now sees different reference horizon.',
          'Training y error range and all eight original deployments differ sharply from old-office transfer.',
          'This is a demonstrated reference-contract mismatch; full causal responsibility requires a separately registered frozen-weight closed-loop comparison.',
          'No input rescaling, zeroing, new smoothing, checkpoint edit or physics rerun was performed.'])
    (out/'CONTRACT_AUDIT.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(value,indent=2))

if __name__=='__main__':main()
