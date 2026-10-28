"""PRIVILEGED OFFLINE DIAGNOSTIC, never a deployable controller or ESN score.

After physical contact is present in the last completed substep, use its
normal and robot Jacobian to maximize instantaneous separating acceleration
over the motor box. Compare original slew limits with a deliberately
unphysical instantaneous torque jump. Neither uses pre-impact knowledge.
This greedy local oracle is NOT a global optimal-control certificate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import validate_office_apparatus_v5_20260917 as evaluator


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--mode', choices=('parity', 'oracle_slew', 'oracle_instant'), required=True)
    args = p.parse_args()
    original_make, original_step = evaluator.make, mujoco.mj_step
    owner, rows = {}, []

    def make(flags):
        env, task, spec = original_make(flags)
        m, d = env.model, env.data
        owner.update(env=env, first=True, previous=d.ctrl[:7].copy(), nominal=d.ctrl[:7].copy(),
                     mass=np.zeros((m.nv, m.nv)), jp=np.zeros((3, m.nv)), jr=np.zeros((3, m.nv)),
                     ball=mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'office_v5_ball_geom'),
                     robot=set(env._push_audit_robot_geom_ids))
        original_physics = env._physics_step

        def physics(t):
            owner['first'] = True
            return original_physics(t)
        env._physics_step = physics
        return env, task, spec

    def step(m, d, *a, **kw):
        if not owner or d is not owner['env'].data:
            return original_step(m, d, *a, **kw)
        env = owner['env']
        if owner['first']:
            owner['nominal'] = d.ctrl[:7].copy()
            owner['first'] = False
            if not rows:
                owner['previous'] = d.ctrl[:7].copy()
        contacts = []
        for contact in d.contact[:d.ncon]:
            g1, g2 = int(contact.geom1), int(contact.geom2)
            if contact.dist > 0:
                continue
            if g1 == owner['ball'] and g2 in owner['robot']:
                contacts.append((contact, g2, 1.))
            elif g2 == owner['ball'] and g1 in owner['robot']:
                contacts.append((contact, g1, -1.))
        coefficient, normal = np.zeros(7), np.zeros(3)
        target = owner['nominal'].copy()
        if contacts:
            contact, geom, sign = min(contacts, key=lambda item: item[0].dist)
            normal = sign * contact.frame.reshape(3, 3)[0].copy()
            mujoco.mj_fullM(m, d, owner['mass'])
            mujoco.mj_jac(m, d, owner['jp'], owner['jr'], contact.pos, int(m.geom_bodyid[geom]))
            # The first seven motors have unit gear on the first seven DOFs
            # in this frozen robot; assert this rather than infer other robots.
            np.testing.assert_array_equal(m.actuator_gear[:7, 0], np.ones(7))
            coefficient = np.linalg.solve(owner['mass'], normal @ owner['jp'])[:7]
            target = np.where(coefficient >= 0., env.torque_limits, -env.torque_limits)
        previous = owner['previous'].copy()
        if args.mode == 'oracle_slew':
            limit = env.safety_config.maximum_torque_rate_nmps * m.opt.timestep
            d.ctrl[:7] = np.clip(previous + np.clip(target - previous, -limit, limit),
                                 -env.torque_limits, env.torque_limits)
        elif args.mode == 'oracle_instant':
            d.ctrl[:7] = np.clip(target, -env.torque_limits, env.torque_limits)
        command = d.ctrl[:7].copy()
        owner['previous'] = command
        result = original_step(m, d, *a, **kw)
        rows.append((float(d.time), bool(contacts), command, owner['nominal'].copy(),
                     (command - previous) / m.opt.timestep, coefficient, normal))
        return result

    evaluator.make, mujoco.mj_step = make, step
    try:
        evaluator.run(argparse.Namespace(output=args.output, render=False, events='ball', task='pick_place',
            seed=2026092702, variant=-2, duration=6.2, dt=.0000015625, ball_speed=1.85,
            person_stroke=.22, rod_stroke=.24, esn_model=None, esn_mode='shadow',
            disable_selector_pulse=False, teacher='none', physics_probe_s=.08))
    finally:
        evaluator.make, mujoco.mj_step = original_make, original_step
    columns = ('time', 'contact_available', 'command', 'nominal_command', 'command_rate',
               'separation_acceleration_per_torque', 'normal_away_from_ball')
    trace = args.output.parent / 'oracle_substeps.npz'
    arrays = {key: np.asarray([row[i] for row in rows]) for i, key in enumerate(columns)}
    np.savez_compressed(trace, **arrays)
    active = np.flatnonzero(arrays['contact_available'])
    rates = np.max(np.abs(arrays['command_rate']), axis=0)
    bounds = np.array([700., 700., 700., 700., 160., 160., 160.])
    if args.mode == 'oracle_slew':
        assert np.all(rates <= bounds + 1e-6)
    result = json.loads(args.output.with_suffix('.json').read_text())
    assert not result['task_success'] and not result['full_task_horizon_completed']
    manifest = dict(purpose=__doc__, mode=args.mode, deployed_policy_candidate=False,
                    privileged_contact_truth_in_diagnostic=args.mode != 'parity',
                    additional_sensor_in_proposed_ESN=False, short_probe_never_task_success=True,
                    sensing_time='last completed physical substep only, no prediction/pre-impact action',
                    first_truth_available_after_completed_step_s=float(arrays['time'][active[0]] - .0000015625) if len(active) else None,
                    torque_amplitude_bounds_obeyed=bool(np.all(np.abs(arrays['command']) <= owner['env'].torque_limits + 1e-10)),
                    original_torque_slew_bounds_obeyed=bool(np.all(rates <= bounds + 1e-6)),
                    max_command_rate_nmps=rates.tolist(), penetration_mm=result['stats']['max_external_penetration_m'] * 1000,
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    raw_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
                    result_sha256=hashlib.sha256(args.output.with_suffix('.json').read_bytes()).hexdigest(),
                    limits='Greedy maximum local normal acceleration, not global optimum or proof of impossibility. Instant mode violates actuator slew and cannot qualify as an in-scope controller.')
    (args.output.parent / 'oracle_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
