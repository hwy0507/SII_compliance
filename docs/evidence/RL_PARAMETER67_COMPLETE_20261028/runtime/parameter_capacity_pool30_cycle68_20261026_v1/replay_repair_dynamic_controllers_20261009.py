"""Chronological VMC/admittance state/action replay using actual public metadata.

Unlike the parameter-shield audit, virtual offsets and velocities are recomputed
from zero, not supplied from logs. Cartesian admittance uses the robot's known
kinematics and archived nominal WBC configuration; no contact/event state and
no dynamics stepping. Optional state-only scope is reported explicitly.
"""
import argparse
import copy
from dataclasses import replace
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--admittance-state-only', action='store_true',
        help='Explicitly exclude Cartesian nominal-WBC action reconstruction')
    args = p.parse_args()
    assert not args.output.exists()
    sys.path[:0] = [str(args.parameter_source), str(Path(__file__).resolve().parents[1]/'scripts')]
    from controllers import ParameterController
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig
    repair = read(args.run/'CONTROLLER_REPAIR.json')
    method = repair['controller']
    assert method in ('vmc','admittance')
    prior = copy.deepcopy(read(args.parameter_source/'PRIORS.json')['methods'][method])
    prior['center'] = repair['prior']
    actual = read(args.run/'execution.json')['action_filter_config']
    safety = replace(VelocityResidualSafetyConfig(),
        maximum_linear_yield_mps=actual['maximum_linear_yield_mps'],
        maximum_angular_yield_radps=actual['maximum_angular_yield_radps'])
    # VMC and the legacy joint-reference mapping need no kinematic queries.
    env = SimpleNamespace(safety_config=safety, model=None, data=None, _hand_id=None,
        fixed_wbc=SimpleNamespace(waypoints=[]))
    trace = read(args.run/'parameter_trace.json')
    errors = {k:0. for k in ('offset','velocity','action','parameters','energy')}
    cartesian = method == 'admittance' and repair['reference_mapping'] == 'original BO controller reference mapping'
    state_only = cartesian and args.admittance_state_only
    if state_only:
        errors.pop('action')
    extra_files = []
    wrench_error = None
    with np.load(args.run/'baseline_policy.npz') as policy:
        obs = policy['observation']
        action = policy['action']
        raw = policy['raw_action'] if 'raw_action' in policy else np.zeros((len(obs),prior['action_dimension']))
        assert len(trace) == len(obs) == len(action) == len(raw)
        if cartesian and not state_only:
            import mujoco
            from fixed_panda_wbc import FixedBasePandaWBCConfig
            from run_contact_transfer_20260916 import ScaledReferenceWBC
            from run_benchmark import body_jacobian
            from haptic_vmc_teacher_20260916 import equivalent_tool_wrench
            model_path = args.run/'rollout.mjb'
            assert sha(model_path) == read(args.run/'AUDIT.json')['model_sha256']
            model = mujoco.MjModel.from_binary_path(str(model_path))
            assert model.opt.integrator in (mujoco.mjtIntegrator.mjINT_EULER,
                mujoco.mjtIntegrator.mjINT_IMPLICIT,mujoco.mjtIntegrator.mjINT_IMPLICITFAST)
            data = mujoco.MjData(model)
            hand = mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
            assert hand >= 0
            speed = read(args.run/'rollout.json')['fixture']['nominal_speed']
            env = SimpleNamespace(safety_config=safety,model=model,data=data,_hand_id=hand,
                fixed_wbc=ScaledReferenceWBC(model,hand,obs[0,:7],FixedBasePandaWBCConfig(
                    position_feedback_gain=2.5*12/13,orientation_feedback_gain=2.3,
                    max_linear_speed_mps=speed,max_angular_speed_radps=.5,nullspace_posture_gain=.1)))
            wrench_error = 0.
            extra_files.extend([model_path,args.run/'rollout.json'])
        if method == 'admittance' and not cartesian:
            assert repair['reference_mapping'] == 'joint-WBC offset-to-twist gains [5,5,5,3,3,3]'
        actor = ParameterController(env, method, prior)
        if method == 'vmc':
            np.testing.assert_array_equal(actor.actor.action_limits,repair['physical_action_units'])
        for index,(o,request,expected,record) in enumerate(zip(obs,raw,action,trace)):
            if cartesian and not state_only:
                # Match retained pre-integration kinematic fields and current
                # encoder q, as the real WBC does after mj_step.
                data.qpos[:7] = o[:7] - (model.opt.timestep*o[7:14] if index else 0.)
                mujoco.mj_kinematics(model,data)
                mujoco.mj_comPos(model,data)
                data.qpos[:7] = o[:7]
                data.qvel[:7] = o[7:14]
                reconstructed = equivalent_tool_wrench(body_jacobian(model,data,hand),o[32:39])
                wrench_error = max(wrench_error,float(np.max(abs(reconstructed-o[39:45]))))
                np.testing.assert_allclose(reconstructed,o[39:45],rtol=1e-10,atol=1e-10)
            offset,velocity = actor.storage_state()
            values = {'offset':offset-np.asarray(record['offset']), 'velocity':velocity-np.asarray(record['velocity'])}
            if state_only:
                theta = actor.shield.update(request,offset,velocity)
                actor.apply(theta)
                # Same equivalent_tool_wrench(J, estimated_joint_load) is
                # already recorded in canonical48[39:45] by the evaluator.
                actor.actor.state.advance(o[39:45],.04)
            else:
                prediction = actor.act(o,request)
                values['action'] = prediction-expected
            values.update(parameters=actor.shield.theta-np.asarray(record['applied_parameters']),
                energy=actor.shield.energy-record['energy_after_j'])
            for key,value in values.items(): errors[key] = max(errors[key],float(np.max(abs(value))))
        raw_range = [float(raw.min()),float(raw.max())]
    assert max(errors.values()) < 1e-10, errors
    write(args.output,dict(status='passed',created_utc=now(),method=method,steps=len(trace),
        max_abs=errors, raw_parameter_action_range=raw_range, physics_steps=0,
        action_output_compared=not state_only,cartesian_nominal_wbc_reconstructed=cartesian and not state_only,
        kinematic_wrench_reconstruction_max_abs=wrench_error,
        scope='Recomputed virtual dynamics/shield from zero and canonical48/raw parameters. Full Cartesian mode uses known robot kinematics/shared WBC with archived fixture speed. State-only mode excludes WBC output. No mj_step/contact truth; not a passivity or task-success proof.',
        hashes={str(p):sha(p) for p in [args.run/'baseline_policy.npz',args.run/'parameter_trace.json',
            args.run/'CONTROLLER_REPAIR.json',args.parameter_source/'controllers.py',
            args.parameter_source/'controllers_legacy.py',args.parameter_source/'baseline_repair_controllers_20261008.py',Path(__file__),*extra_files]}))
    print(method, len(trace), raw_range, errors, flush=True)


if __name__ == '__main__': main()
