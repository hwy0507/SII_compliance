"""Read-only implementation probes and frozen-run evidence; no robot steps/training.

The output is a diagnostic, not a repaired-controller performance evaluation.
Use --root with the immutable office-v7 uniform24 server directory for receipts.
"""
import argparse
import ast
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--source-root', type=Path,
                        default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve()
    sys.path[:0] = [str(source/'scripts'), str(source/'tools')]
    from vmc_teacher_stable_readout_20260930 import StableReadoutTeacher
    from wbc_velocity_residual_core import VelocityResidualSafetyConfig, VelocityResidualActionFilter
    from run_panel_impedance_reference_20260923 import MovingEquilibrium, ReferenceImpedanceConfig
    files = [source/'scripts'/name for name in (
        'vmc_teacher_stable_readout_20260930.py', 'run_vmc_6d_constrained_push_20260918.py',
        'wbc_velocity_residual_core.py', 'run_panel_impedance_reference_20260923.py')]
    out = dict(scope='Algebra/recorded trajectories only; zero new physics steps or gradient updates',
               source_sha256={str(f): sha(f) for f in files}, auditor_sha256=sha(__file__),
               created_utc=datetime.now(timezone.utc).isoformat(), host=platform.node(),
               python=sys.executable, python_version=platform.python_version(), numpy_version=np.__version__)

    safety = VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)
    if args.root:
        execution_path = args.root/'episodes/classical_vmc__office_v7_24_000/execution.json'
        execution = json.loads(execution_path.read_text())
        safety = VelocityResidualSafetyConfig(**execution['action_filter_config'])
        out['vmc_execution_sha256'] = sha(execution_path)
        out['actual_action_filter_config'] = execution['action_filter_config']
        for path in files:
            assert sha(path) == execution['source_sha256'][str(path.relative_to(source))]
    units = np.r_[np.full(3, safety.maximum_linear_yield_mps),
                  np.full(3, safety.maximum_angular_yield_radps)]
    actor = StableReadoutTeacher(velocity_weight=.5)
    requested = actor.act(np.array([1., 1., 1., .1, .1, .1]), .04)
    physical_readout = actor.R6 @ (actor.velocity_weight*actor.velocity + actor.offset_gain*actor.offset)
    filtered = VelocityResidualActionFilter(safety).filter(requested, .04)
    assert not filtered.slew_limited and np.max(np.abs(requested)) < 1
    ratio = filtered.cartesian_yield_twist / physical_readout
    np.testing.assert_allclose(ratio, [2., 2., 1.6, 1., 1., 1.], atol=1e-12)
    out['vmc_units_probe'] = dict(encoder_units=actor.action_limits.tolist(), decoder_units=units.tolist(),
        virtual_physical_readout=physical_readout.tolist(), decoded_filtered_twist=filtered.cartesian_yield_twist.tolist(),
        ratio=ratio.tolist(), slew_limited=False, interpretation='Confirmed physical readout normalization mismatch; closed-loop harm not established by this probe')

    integrator = MovingEquilibrium(ReferenceImpedanceConfig())
    rotation = np.eye(3)
    integrator.update(np.zeros(3), rotation, np.zeros(6), .004)
    integrator.position = np.array([.04, 0., 0.])
    before = integrator.position.copy()
    # At the travel bound, an orthogonal command is fully suppressed by the
    # scalar conditional integration. This reproduces a limitation, not a robot.
    for _ in range(250):
        integrator.update(np.zeros(3), rotation, np.array([0., .05, 0., 0., 0., 0.]), .004)
    displacement = integrator.position-before
    assert np.linalg.norm(displacement) < 1e-6
    out['impedance_bound_probe'] = dict(duration_s=1., nominal_tangential_speed_mps=.05,
        position_bound_m=.04, actual_reference_displacement_m=displacement.tolist(),
        interpretation='Scalar anti-windup can stall tangential reference at travel bound; diagnostic only')

    if args.root:
        root = args.root.resolve()
        out['root'] = str(root)
        out['protocol_sha256'] = sha(root/'PROTOCOL.json')
        report = json.loads((root/'report_final/REPORT.json').read_text())
        assert report['complete'] and report['completed'] == 384
        out['final_report_sha256'] = sha(root/'report_final/REPORT.json')
        param = root/'episodes/classical_vmc__office_v7_24_000/parameter_source'
        controller_source = (param/'controllers.py').read_text()
        out['controller_source_sha256'] = sha(param/'controllers.py')
        tree = ast.parse(controller_source)
        torque = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'torque')
        reads_command = any(isinstance(n, ast.Name) and n.id == 'joint_velocity_command' and isinstance(n.ctx, ast.Load) for n in ast.walk(torque))
        assert not reads_command
        out['impedance_ignores_limited_joint_command'] = dict(confirmed=True,
            interpretation='Native Cartesian torque backend still uses torque box/slew; upstream joint speed/acceleration command limiter is not consumed')
        sys.path.insert(0, str(param))
        from controllers import ParameterController
        prior = json.loads((param/'PRIORS.json').read_text())['methods']['vmc']
        baseline = ParameterController(SimpleNamespace(), 'vmc', prior)
        np.testing.assert_array_equal(baseline.actor.action_limits, actor.action_limits)
        out['vmc_units_probe']['actual_parameter_controller_defaults_verified'] = True
        out['impedance_recorded_anchors'] = []
        for family in ('classical_impedance', 'parameter_impedance'):
            run = root/'episodes'/(family+'__office_v7_24_000')
            with np.load(run/'impedance_servo.npz') as trace:
                v = trace['values']; tail = v[v[:, 0] >= v[-1, 0]-5]
                med = np.median(tail, axis=0)
                cap = float(np.mean(np.linalg.norm(tail[:, 1:4], axis=1) >= .04-1e-8))
            with np.load(run/'rollout.npz') as trace:
                obs = trace['observation'][-125:]
                error = float(np.median(np.linalg.norm(obs[:, 20:23], axis=1))*1000)
                nominal = float(np.median(np.linalg.norm(obs[:, 14:17], axis=1))*1000)
                speed = float(np.median(np.linalg.norm(obs[:, 14:17]-obs[:, 26:29], axis=1))*1000)
                zero_action = bool(np.all(trace['applied_action'] == 0))
            out['impedance_recorded_anchors'].append(dict(family=family, condition_id='office_v7_24_000',
                anchor_selection='first registered condition, no outcome selection',
                statistics='Last 125 actor observations (5 seconds), medians; not physical-substep RMSE',
                tail_spring_bound_fraction=cap, tail_position_error_mm=error,
                tail_nominal_speed_mm_s=nominal, tail_actual_speed_mm_s=speed,
                median_spring_error6=med[1:7].tolist(), median_residual_joint_torque_nm=med[13:20].tolist(),
                common_action7_identically_zero=zero_action,
                evidence_sha256={f:sha(run/f) for f in ('impedance_servo.npz','rollout.npz','execution.json')}))

        import mujoco
        model = mujoco.MjModel.from_binary_path(str(root/'episodes/classical_impedance__office_v7_24_000/rollout.mjb'))
        payload = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, 'target_object')
        out['model'] = dict(frictionloss_nm=model.dof_frictionloss[:7].tolist(),
                            payload_mass_kg=float(model.body_mass[payload]),
                            sha256=sha(root/'episodes/classical_impedance__office_v7_24_000/rollout.mjb'))

        out['rl_training'] = []
        for family in ('parameter_vmc','parameter_admittance','parameter_impedance','direct_metric','direct_office_task'):
            cpfile = root/'episodes'/(family+'__office_v7_24_000')/'ADAPTED_RL_CHECKPOINT.json'
            cp = json.loads(cpfile.read_text()); path = Path(cp['checkpoint'])
            agent = json.loads((path/'official_agent_state.json').read_text())
            current = path.parent; rows = []; chain = []; hashes = {}
            while True:
                execution = json.loads((current/'execution.json').read_text())
                rows.extend(execution['rows'])
                chain.append(dict(path=str(current), cumulative_steps=execution['steps'], segment_episodes=len(execution['rows'])))
                hashes[str(current/'execution.json')] = sha(current/'execution.json')
                if not execution.get('resumed_from'):
                    initial = json.loads((current/'PROTOCOL.json').read_text())
                    break
                current = Path(execution['resumed_from']['checkpoint']).parent
            assert len({r['run'] for r in rows}) == len(rows)
            assert sum(r['steps'] for r in rows) == agent['interactions'] == agent['reward_samples']
            successes = sum(bool(r['result']['task_success']) for r in rows)
            strict = sum(bool(r['result']['strict_success']) for r in rows)
            replay_path = path/'office_replay.npz'
            with np.load(replay_path) as z:
                terminal_count = int(z['terminated'].sum())
                assert terminal_count == len(rows) and len(z['reward']) == agent['interactions']
                truncated = int(z['truncated'].sum())
            out['rl_training'].append(dict(family=family, checkpoint=str(path),
                interactions=agent['interactions'], updates=agent['updates'], episodes=len(rows),
                task_successes=successes, strict_successes=strict,
                short_episodes=sum(not r['result']['full_task_horizon_completed'] for r in rows),
                replay_terminals=terminal_count, replay_truncated=truncated,
                initialization=initial['initialization'], teacher_labels_used=initial['teacher_labels_used'],
                warmup_steps=initial['warmup_steps'], chain=chain,
                checkpoint_manifest_sha256=sha(cpfile), replay_sha256=sha(replay_path), segment_execution_sha256=hashes))
        # Freeze evidence hashes after read-only probes; do not mutate policies.
        assert out['controller_source_sha256'] == sha(param/'controllers.py')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(out, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(out, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
