"""Read-only contact-response sensitivity on cloned states; no truth feedback."""
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original_sample = evaluator.EpisodeMetrics.sample
    thresholds = [1e-6, 1e-4, 1.9e-4]
    rows, states = [], []

    def sample(metric):
        original_sample(metric)
        if len(rows) == len(thresholds):
            return
        env = metric.env
        m, live = env.model, env.data
        ball_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'office_v5_ball_geom')
        hand_geom = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_GEOM, 'hand_collision')
        pairs = [c for c in live.contact[:live.ncon] if {int(c.geom1), int(c.geom2)} == {ball_geom, hand_geom}]
        if not pairs or -min(c.dist for c in pairs) < thresholds[len(rows)]:
            return
        # All additional forward solves use separate data. Never modify live.
        frozen = mujoco.MjData(m)
        mujoco.mj_copyData(frozen, m, live)
        mujoco.mj_forward(m, frozen)
        pairs = [c for c in frozen.contact[:frozen.ncon] if {int(c.geom1), int(c.geom2)} == {ball_geom, hand_geom}]
        c = min(pairs, key=lambda value: value.dist)
        sign = 1. if int(c.geom2) == hand_geom else -1.
        normal = sign * c.frame.reshape(3, 3)[0].copy()
        jhand, jball, rotational = (np.zeros((3, m.nv)) for _ in range(3))
        mujoco.mj_jac(m, frozen, jhand, rotational, c.pos, int(m.geom_bodyid[hand_geom]))
        mujoco.mj_jac(m, frozen, jball, rotational, c.pos, int(m.geom_bodyid[ball_geom]))
        relative = normal @ (jhand - jball)
        mass = np.zeros((m.nv, m.nv))
        mujoco.mj_fullM(m, frozen, mass)
        np.testing.assert_array_equal(m.actuator_gear[:7, 0], 1.)
        np.testing.assert_array_equal(m.jnt_dofadr[m.actuator_trnid[:7, 0]], np.arange(7))
        gradient = np.linalg.solve(mass, relative)[:7]
        nominal = frozen.ctrl[:7].copy()
        best_box = np.where(gradient >= 0., env.torque_limits, -env.torque_limits)
        trials = []
        for label, torque in [('nominal', nominal), ('max_separation_box', best_box), ('min_separation_box', -best_box)]:
            data = mujoco.MjData(m)
            mujoco.mj_copyData(data, m, frozen)
            data.ctrl[:7] = torque
            mujoco.mj_forward(m, data)
            predicted = float(gradient @ (torque - nominal))
            actual = float(relative @ (data.qacc - frozen.qacc))
            smooth = float(relative @ (data.qacc_smooth - frozen.qacc_smooth))
            force = np.zeros(6)
            match = next(i for i, contact in enumerate(data.contact[:data.ncon])
                         if {int(contact.geom1), int(contact.geom2)} == {ball_geom, hand_geom})
            mujoco.mj_contactForce(m, data, match, force)
            trials.append(dict(label=label, torque_nm=torque.tolist(),
                               free_mass_prediction_delta_acceleration_mps2=predicted,
                               unconstrained_solve_delta_acceleration_mps2=smooth,
                               constrained_solve_delta_acceleration_mps2=actual,
                               constrained_over_free_ratio=actual / predicted if abs(predicted) > 1e-10 else None,
                               contact_force_local=force.tolist()))
        states.append(dict(qpos=frozen.qpos.copy(), qvel=frozen.qvel.copy(), ctrl=frozen.ctrl.copy(),
                           qfrc_applied=frozen.qfrc_applied.copy(), mocap_pos=frozen.mocap_pos.copy(),
                           mocap_quat=frozen.mocap_quat.copy(), relative_jacobian=relative, motor_gradient=gradient))
        address = c.efc_address
        rows.append(dict(time_s=float(frozen.time), threshold_m=thresholds[len(rows)], actual_depth_m=-float(c.dist),
                         normal_away_from_ball=normal.tolist(), solref=c.solref.tolist(), solimp=c.solimp.tolist(),
                         efc_KBIP=frozen.efc_KBIP[address].tolist(), trials=trials))

    evaluator.EpisodeMetrics.sample = sample
    try:
        evaluator.run(argparse.Namespace(output=args.output, render=False, events='ball', task='pick_place',
            seed=2026092702, variant=-2, duration=6.2, dt=.0000015625, ball_speed=1.85,
            person_stroke=.22, rod_stroke=.24, esn_model=None, esn_mode='shadow',
            disable_selector_pulse=False, teacher='none', physics_probe_s=.08))
    finally:
        evaluator.EpisodeMetrics.sample = original_sample
    assert len(rows) == 3
    state_path = args.output.parent / 'response_states.npz'
    np.savez_compressed(state_path, **{key: np.array([state[key] for state in states]) for key in states[0]})
    report = dict(purpose=__doc__, truth_enters_live_controller=False, live_trajectory_should_match_parity=True,
                  rows=rows, source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  state_sha256=hashlib.sha256(state_path.read_bytes()).hexdigest(),
                  caveats=['Cloned-state instantaneous sensitivity is not a controller or full-horizon control bound.',
                           'Positive solref and near-unit constraint impedance can suppress free-acceleration changes; coupling and friction also matter.',
                           'This does not authorize changing contact parameters or safety thresholds.'])
    (args.output.parent / 'contact_response.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
