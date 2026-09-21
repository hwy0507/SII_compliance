"""Run the frozen ESN in the existing office development world, no tuning."""
import json
import os
from pathlib import Path
import runpy
import sys
os.environ.setdefault('MUJOCO_GL','egl')
import mujoco
import numpy as np
import audited_velocity_env as backend
import contact_transfer_student_20260916 as student_module
from esn128_action7_20260918 import ESN128Action7
from run_benchmark import body_twist


def main():
    output=Path(sys.argv[sys.argv.index('--output')+1])
    revision=os.environ.get('OFFICE_RECOVERY_SCENE')
    if revision=='5':
        from office_recovery_scene_v5_20260918 import install
        install()
    elif revision=='4':
        from office_recovery_scene_v4_20260918 import install
        install()
    elif revision=='3':
        from office_recovery_scene_v3_20260918 import install
        install()
    elif revision=='2':
        from office_recovery_scene_v2_20260918 import install
        install()
    elif revision=='1':
        from office_recovery_scene_20260918 import install
        install()
    student_module.TransferStudent=ESN128Action7
    original_step=backend.PandaWBCVelocityResidualEnv.step
    original_close=backend.PandaWBCVelocityResidualEnv.close
    rows=[]
    def step(self,action):
        config=self.safety_config
        np.testing.assert_allclose([config.minimum_wbc_scale,config.maximum_linear_yield_mps,
                                   config.maximum_angular_yield_radps],[.2,.32,.6],atol=1e-12)
        m,d=self.model,self.data
        command=self._wbc_command(0.)
        reference=command.target_position_m.copy()
        result=original_step(self,action)
        rows.append(dict(time=float(d.time),position=d.xpos[self._hand_id].copy(),target=reference,
            twist=body_twist(m,d,self._hand_id),torque=d.qfrc_actuator[:7].copy(),action=np.asarray(action).copy()))
        if len(rows)%25==0:
            progress=dict(time_s=float(d.time),stage=int(self.reference.index),
                position_error_m=float(np.linalg.norm(rows[-1]['position']-reference)),
                speed_mps=float(np.linalg.norm(rows[-1]['twist'][:3])),
                residual_mps=float(.32*np.linalg.norm(action[1:4])))
            tmp=output.with_suffix('.progress.tmp');tmp.write_text(json.dumps(progress));tmp.replace(output.with_suffix('.progress.json'))
        return result
    def close(self):
        if self.model is not None:
            mujoco.mj_saveLastXML(str(output.with_suffix('.xml')),self.model)
        return original_close(self)
    backend.PandaWBCVelocityResidualEnv.step=step
    backend.PandaWBCVelocityResidualEnv.close=close
    runner=Path(__file__).with_name('validate_office_apparatus_v5_20260917.py')
    if os.environ.get('EVALUATION_STOP_AFTER_SUCCESS')=='1':
        import ast
        tree=ast.parse(runner.read_text());changed=0
        for func in tree.body:
            if isinstance(func,ast.FunctionDef) and func.name=='run':
                for loop in func.body:
                    if isinstance(loop,ast.For) and isinstance(loop.target,ast.Name) and loop.target.id=='_':
                        loop.body.append(ast.parse("if a.task=='pick_place' and placement_hold>=1. and release_truth and max_lift>.10 and np.linalg.norm(d.xpos[env._hand_id]-task.goals[-1])<.015 and sum(d.qpos[task.fingers])>.075: break").body[0]);changed+=1
        if changed!=1:raise RuntimeError('Could not identify evaluation loop')
        ast.fix_missing_locations(tree)
        exec(compile(tree,str(runner),'exec'),{'__name__':'__main__','__file__':str(runner)})
    else:
        runpy.run_path(str(runner),run_name='__main__')
    result=json.loads(output.with_suffix('.json').read_text())
    a={k:np.asarray([r[k] for r in rows]) for k in rows[0]}
    np.savez_compressed(output.with_name(output.name+'_metrics.npz'),**a)
    events=result['stats']['events'];first=min((e['first_s'] for e in events.values()),default=0.)
    window=a['time']>=first;speed=np.linalg.norm(a['twist'][:,:3],axis=1)
    metrics=dict(tracking_rmse_after_contact_m=float(np.sqrt(np.mean(np.sum((a['position'][window]-a['target'][window])**2,axis=1)))),
        speed_p95_mps=float(np.percentile(speed,95)),peak_speed_mps=float(speed.max()),
        acceleration_p95_mps2=float(np.percentile(np.linalg.norm(np.diff(a['twist'][:,:3],axis=0)/.04,axis=1),95)),
        peak_motor_torque_nm=result['stats']['peak_motor_torque_nm'],
        peak_contact_force_n=max((e['peak_n'] for e in events.values()),default=0.))
    result.update(purpose='frozen_ESN_source_BC_to_office_development_evaluation',
        controller='ESN 128 reservoir + 128 hidden readout + 7 outputs; shared WBC and task supervisor',
        metrics=metrics,weights_changed=False,office_used_for_selection=False,
        task_success=bool(result['placement_complete'] and result['physical_valid']),
        note='Office v5 development layouts; not final blind generalization test. The existing rigid office ball differs from the soft-shell training ball.')
    if revision in ('1','2','3','4','5'):
        import hashlib
        name=f'office_recovery_scene_v{revision}_20260918.py' if revision!='1' else 'office_recovery_scene_20260918.py'
        result['development_scene_revision']=name
        result['source_sha256'][name]=hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
    result['evaluator_stops_after_confirmed_success']=os.environ.get('EVALUATION_STOP_AFTER_SUCCESS')=='1'
    output.with_suffix('.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(output=str(output),success=result['task_success'],metrics=metrics)),flush=True)


if __name__=='__main__':main()
