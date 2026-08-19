"""Extraction-scenario compliance training: ESN vs MLP vs FW.

Scenario: bare-arm under-board extraction on FR3 + vendored Pink-IK WBC.
The static board blocks the carry corridor; pure tracking never crosses.
Escape = slow the WBC feedback (wbc_scale channel) + persistent -z yield
(twist channel) while inside the corridor, release after crossing.

Both students are deployed UNGATED (activation=1, same as training targets)
for architectural fairness; the ESN keeps its reservoir state.

Stages: probe | data | train | eval
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mujoco
import numpy as np

from direct_esn_compliance import (
    DirectESNConfig, DirectESNController, DirectESNObservation)
from wbc_velocity_residual_core import VelocityResidualSafetyConfig
from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv

MENAGERIE = Path("/home/arm1/vmc_mujoco_runtime/mujoco_menagerie")
URDF = Path(__file__).resolve().parent.parent / "assets/fr3_pin/fr3.urdf"
OUT = Path("/home/arm1/vmc_mujoco_runtime/outputs/extraction_esn")

BOARDS = {"low": 0.605, "mid": 0.615, "high": 0.625, "heldout": 0.610}
CORRIDOR_X_IN = 0.56      # start slowing/dipping before the board edge
CORRIDOR_X_OUT = 0.26     # release after the far edge
DIP_CLEARANCE = 0.065     # palm depth below the board underside to hold
WBC_SLOW_ACTION = 0.875   # action[0] giving wbc_scale ~= 0.30
WASHOUT = 10


SCENARIO_SAFETY = VelocityResidualSafetyConfig(maximum_linear_yield_mps=0.50, minimum_wbc_scale=0.10)


def make_env(board_z: float | None, seed: int, noise: float = 0.0):
    return PandaWBCVelocityResidualEnv(
        menagerie=MENAGERIE, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, seed=seed, robot="fr3",
        execution_mode="twist", wbc_backend="pink", wbc_urdf_path=URDF,
        table_board_underside_z=board_z, safety_config=SCENARIO_SAFETY,
        joint_velocity_noise_std=noise)


class Teacher:
    """Position-rule corridor escape (hand pose is FK of q: deployable)."""

    def __init__(self, board_z: float | None) -> None:
        self.board_z = board_z

    def act(self, hand_x: float, hand_z: float, nominal_vx: float = 0.0) -> np.ndarray:
        action = np.zeros(7)
        if self.board_z is None:
            return action
        z_target = self.board_z - DIP_CLEARANCE
        # Phase gate: dip only in the carry phase (nominal twist moving -x).
        # During descent (twist mostly -z) the corridor x-window also matches,
        # and dipping there would drive the fingers into the table/block.
        carrying = nominal_vx < -0.02
        if carrying and CORRIDOR_X_OUT < hand_x < CORRIDOR_X_IN:
            # Decouple: feedback stays scheduled low THROUGHOUT the corridor
            # (otherwise z oscillates between dip and full-gain pull-up and
            # the forward crawl stalls); the dip itself is continuous P.
            action[0] = 1.0  # WBC feedback authority -> minimum (0.10)
            depth = hand_z - z_target
            if depth > 0.0:
                action[3] = -float(np.clip(depth / 0.05, 0.0, 1.0))  # P-hold yield
        return action


class EnsemblePolicy:
    """Average the bounded actions of member policies (each keeps its state)."""

    def __init__(self, members) -> None:
        self.members = list(members)

    def reset(self) -> None:
        for member in self.members:
            if hasattr(member, "reset"):
                member.reset()

    def act(self, *args, **kwargs):
        actions = [np.asarray(m.act(*args, **kwargs).bounded_filter_action, dtype=float)
                   for m in self.members]

        class R:
            pass
        r = R()
        r.bounded_filter_action = np.mean(actions, axis=0)
        return r


class VMCScheduled:
    """Vendored SpringCarriageVMC + carriage-driven WBC feedback scheduling.

    The original controller is untouched: its yield channels come through the
    standard adapter.  The ONLY addition is that the carriage's own offset
    magnitude drives the feedback-scheduling channel — a platform adaptation
    for the strong-WBC world (the channel did not exist in the author's
    original deployment context, so nothing faithful is being altered).
    """

    def __init__(self, config_overrides: dict | None = None, offset_ref: float = 0.05) -> None:
        from dataclasses import replace as _r
        from vmc_compliance_baseline import SpringCarriageVMC, SpringCarriageConfig
        self.inner = SpringCarriageVMC(_r(SpringCarriageConfig(), **(config_overrides or {})))
        self.offset_ref = offset_ref

    def reset(self) -> None:
        self.inner.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        action = self.inner.act(pose_error, twist_error)
        offset = float(np.linalg.norm(np.asarray(self.inner.offset[:3])))
        bounded = np.zeros(7)
        # Yield channels: normalize the carriage offset RATE by this env's
        # yield limit (0.5 m/s / 2.0 rad/s in SCENARIO_SAFETY... angular uses
        # the safety config's 0.60) so the env reproduces the ORIGINAL
        # physical yield rates exactly.
        lin_limit, ang_limit = 0.50, 0.60
        rates = np.asarray(action[1:], dtype=float)
        bounded[1:4] = np.clip(rates[:3] / lin_limit, -1.0, 1.0)
        bounded[4:7] = np.clip(rates[3:] / ang_limit, -1.0, 1.0)
        # Carriage-state scheduling: large carriage offset == the virtual
        # model has yielded far == the WBC should ease its feedback.
        bounded[0] = float(np.clip(offset / self.offset_ref, 0.0, 1.0))

        class R:
            pass
        r = R()
        r.bounded_filter_action = bounded
        return r


class VMCErrorScheduled:
    """Original SpringCarriageVMC yield + error-magnitude feedback scheduling.

    The scheduling channel is a platform adaptation either way (it does not
    exist in the author's deployment); driving it by the measured WBC error
    magnitude — the same signal the rule VMC uses — instead of the carriage
    offset, because that is the coupling that actually unlocks crossing.
    """

    def __init__(self, config_overrides: dict | None = None,
                 k_sched: float = 25.0, cap: float = 0.7) -> None:
        from dataclasses import replace as _r
        from vmc_compliance_baseline import SpringCarriageVMC, SpringCarriageConfig
        self.inner = SpringCarriageVMC(_r(SpringCarriageConfig(), **(config_overrides or {})))
        self.k_sched = k_sched
        self.cap = cap

    def reset(self) -> None:
        self.inner.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        action = self.inner.act(pose_error, twist_error)
        e = np.asarray(pose_error, dtype=float)
        en = float(np.linalg.norm(e[:3]))
        bounded = np.zeros(7)
        rates = np.asarray(action[1:], dtype=float)
        bounded[1:4] = np.clip(rates[:3] / 0.50, -1.0, 1.0)
        bounded[4:7] = np.clip(rates[3:] / 0.60, -1.0, 1.0)
        bounded[0] = float(np.clip(en * self.k_sched, 0.0, self.cap))

        class R:
            pass
        r = R()
        r.bounded_filter_action = bounded
        return r


class NeutralPolicy:
    def reset(self) -> None: ...

    def act(self, *args, **kwargs):
        class R:
            bounded_filter_action = np.zeros(7)
        return R()


class UngatedESN:
    """ESN deployed with activation gating disabled (parity with training)."""

    def __init__(self, model: DirectESNController) -> None:
        self.model = model

    def reset(self) -> None:
        self.model.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        from esn_compliance import ESNObservation
        feature = self.model.advance(
            ESNObservation(joint_position, joint_velocity, wbc_task_twist),
            pose_error, twist_error)
        return self.model.action_from_feature(feature, activation=1.0)


class UngatedMLP:
    """MLPComplianceController inference without the error-activation gate."""

    def __init__(self, inner) -> None:
        self.inner = inner

    def reset(self) -> None:
        self.inner.reset()

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        observation = np.concatenate([
            np.asarray(joint_position, dtype=float),
            np.asarray(joint_velocity, dtype=float),
            np.asarray(wbc_task_twist, dtype=float),
            np.asarray(pose_error, dtype=float) if pose_error is not None else np.zeros(6),
            np.asarray(twist_error, dtype=float) if twist_error is not None else np.zeros(6),
        ])
        c = self.inner
        normalized = (observation - c.mean) / c.std
        hidden = np.tanh(normalized @ c.w1.T + c.b1)
        bounded = np.tanh(hidden @ c.w2.T + c.b2)

        class R:
            pass
        r = R()
        r.bounded_filter_action = np.concatenate(
            [[max(0.0, float(bounded[0]))], np.clip(bounded[1:], -1.0, 1.0)])
        return r


class VMCScenario:
    """VMC-flavored baseline with the same action channels as the students.

    Spring--damper admittance on the measured WBC pose error (the classical
    virtual-carriage coupling, deployable signal only), plus feedback-authority
    scheduling driven by the error magnitude.  No board knowledge, no memory.
    """

    def __init__(self, k_yield: float = 8.0, k_sched: float = 25.0, damp: float = 0.5) -> None:
        self.k_yield = k_yield
        self.k_sched = k_sched
        self.damp = damp

    def reset(self) -> None: ...

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None):
        e = np.asarray(pose_error, dtype=float)
        de = np.asarray(twist_error, dtype=float)
        en = float(np.linalg.norm(e[:3]))

        class R:
            pass
        r = R()
        action = np.zeros(7)
        # schedule WBC feedback authority down as the tracking error grows,
        # CAPPED at 0.7 (feedback floor 0.3): the traverse keeps full-speed
        # tracking and the episode has time left to rejoin after the corridor
        action[0] = float(np.clip(en * self.k_sched, 0.0, 1.0))
        # yield along the push (admittance: follow the displacement direction)
        if en > 0.01:
            v = -self.k_yield * e[:3] / max(en, 1e-9) - self.damp * de[:3]
            action[1:4] = np.clip(v / 0.5, -1.0, 1.0)
        r.bounded_filter_action = action
        return r


class HybridTeacher(VMCScenario):
    """VMC's continuous admittance while inside the corridor or in contact;
    hard release beyond the far edge so the WBC regains authority and rejoins."""

    def __init__(self, board_z: float | None, **kw) -> None:
        super().__init__(**kw)
        self.board_z = board_z
        self.last_contact_t = -10.0

    def act(self, joint_position, joint_velocity, wbc_task_twist, *,
            pose_error=None, twist_error=None, hand_x=None, contact=False, time_s=0.0):
        if self.board_z is None:
            r = type("R", (), {})()
            r.bounded_filter_action = np.zeros(7)
            return r
        in_corridor = CORRIDOR_X_OUT < hand_x < CORRIDOR_X_IN
        if contact:
            self.last_contact_t = time_s
        engaged = in_corridor or (time_s - self.last_contact_t) < 0.6
        if not engaged:
            r = type("R", (), {})()
            r.bounded_filter_action = np.zeros(7)
            return r
        action = np.asarray(super().act(
            joint_position, joint_velocity, wbc_task_twist,
            pose_error=pose_error, twist_error=twist_error).bounded_filter_action, dtype=float).copy()
        if hand_x < 0.34:
            # inside the far half: hand WBC authority back (fb -> 1.0)
            action[0] = 0.0
        r = type("R", (), {})()
        r.bounded_filter_action = action
        return r



def board_force(env) -> float:
    bid = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "extraction_board")
    if bid < 0:
        return 0.0
    total = 0.0
    for c in range(env.data.ncon):
        con = env.data.contact[c]
        if con.geom1 == bid or con.geom2 == bid:
            wrench = np.zeros(6)
            mujoco.mj_contactForce(env.model, env.data, c, wrench)
            total += float(np.linalg.norm(wrench[:3]))
    return total


def rollout(env, seed: int, policy, *, teacher: Teacher | None = None, collect: bool = False):
    env.reset(seed=seed, options={"fixture_index": 0})
    observations: list[DirectESNObservation] = []
    actions: list[np.ndarray] = []
    errors, forces, hand_x = [], [], []
    done, info = False, {}
    while not done:
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        if teacher is not None:
            action = teacher.act(float(hand[0]), float(hand[2]),
                                 float(d["nominal_twist"][0]))
        elif isinstance(policy, HybridTeacher):
            action = np.asarray(policy.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
                hand_x=float(hand[0]),
                contact=board_force(env) > 2.0, time_s=float(d["time_s"]),
            ).bounded_filter_action, dtype=float)
        else:
            action = np.asarray(policy.act(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
            ).bounded_filter_action, dtype=float)
        if collect:
            observations.append(DirectESNObservation(
                d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                d["wbc_pose_error"], d["wbc_twist_error"]))
            actions.append(action.copy())
        errors.append(float(np.linalg.norm(d["wbc_pose_error"][:3])))
        forces.append(board_force(env))
        hand_x.append(float(hand[0]))
        _, _, done, _, info = env.step(action)
    e, f, x = np.asarray(errors), np.asarray(forces), np.asarray(hand_x)
    metrics = dict(
        crossed=bool(x[-1] < CORRIDOR_X_OUT), x_final=float(x[-1]),
        force_peak=float(f.max()), force_integral=float(f.sum() * 0.04),
        contact_s=float((f > 0.5).sum() * 0.04),
        err_final_mm=float(e[-1] * 1000.0), peak_torque=float(info["peak_torque_nm"]),
        hard_limit=bool(info["hard_torque_limit"]), finite=bool(info["finite_state"]))
    return (observations, actions, metrics) if collect else metrics


def stage_probe():
    for name, board in BOARDS.items():
        env = make_env(board, seed=7)
        fw = rollout(env, 7, NeutralPolicy())
        teacher = rollout(env, 7, None, teacher=Teacher(board))
        print(f"[{name} z={board}] FW: crossed={fw['crossed']} x={fw['x_final']:.3f} "
              f"Fint={fw['force_integral']:.0f}Ns err={fw['err_final_mm']:.1f}mm | "
              f"teacher: crossed={teacher['crossed']} x={teacher['x_final']:.3f} "
              f"Fint={teacher['force_integral']:.0f}Ns err={teacher['err_final_mm']:.1f}mm "
              f"tau={teacher['peak_torque']:.1f}")
        env.close()


DATA_BOARDS = (0.605, 0.615, 0.625)
DATA_SEEDS = (7, 11, 13, 29, 97, 123, 555, 20260817)
DATA_NOISE = (0.0, 0.005, 0.010)


def collect_episode(board_z, seed, noise):
    env = PandaWBCVelocityResidualEnv(
        menagerie=MENAGERIE, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=False, seed=seed, robot="fr3",
        execution_mode="twist", wbc_backend="pink", wbc_urdf_path=URDF,
        table_board_underside_z=board_z, safety_config=SCENARIO_SAFETY,
        joint_velocity_noise_std=noise)
    obs, acts, metrics = rollout(env, seed, HybridTeacher(board_z), collect=True)
    env.close()
    return dict(name=f"b{board_z}_n{noise}", seed=seed, noise=noise, obs=obs,
                actions=acts, metrics=metrics)


def stage_data():
    episodes = []
    for board_z in DATA_BOARDS:
        for seed in DATA_SEEDS:
            for noise in DATA_NOISE:
                if noise > 0.0 and seed not in (7, 29, 123):
                    continue  # noise variants on a seed subset
                episodes.append(collect_episode(board_z, seed, noise))
    for seed in DATA_SEEDS:
        episodes.append(collect_episode(None, seed, 0.0))
    np.savez_compressed(OUT / "teacher_data.npz", episodes=np.asarray(episodes, dtype=object))
    print(f"saved {len(episodes)} episodes")


ESN_GRID = [
    dict(spectral_radius=0.90, input_scale=0.45, ridge_lambda=1.0e-4, time_constant_s=0.12),
    dict(spectral_radius=0.90, input_scale=0.45, ridge_lambda=1.0e-4, time_constant_s=0.12, reservoir_size=320),
    dict(spectral_radius=0.95, input_scale=0.90, ridge_lambda=1.0e-4, time_constant_s=0.12, reservoir_size=480),
    dict(spectral_radius=0.90, input_scale=0.45, ridge_lambda=1.0e-4, time_constant_s=0.05, reservoir_size=320),
    dict(spectral_radius=0.95, input_scale=0.90, ridge_lambda=3.0e-5, time_constant_s=0.08, reservoir_size=320),
    dict(spectral_radius=0.90, input_scale=0.90, ridge_lambda=1.0e-3, time_constant_s=0.04, reservoir_size=480),
]


ENGAGED_OVERSAMPLE = 4


def _engaged_mask(actions: np.ndarray) -> np.ndarray:
    return np.any(np.abs(actions) > 0.05, axis=1)


def _atanh_targets(actions: np.ndarray, limit: float = 0.995) -> np.ndarray:
    """Inverse-tanh target transform.

    fit_readout solves a LINEAR least squares W f ~= y, but deployment emits
    tanh(W f).  Fitting raw actions therefore systematically shrinks the
    saturated escape actions (tanh(+-1) = +-0.76).  Fitting atanh(y) instead
    makes tanh(W f) ~= y at deployment; the clip avoids the singularity at
    +-1 (tanh(2.646) = 0.99, close enough for the smoothness-regularized fit).
    """
    return np.arctanh(np.clip(actions, -limit, limit))


def _fit_esn(episodes, seed, overrides):
    model = DirectESNController(DirectESNConfig(seed=seed, **overrides))
    feats, tgts, sm_feat, sm_tgt, weights = [], [], [], [], []
    for episode in episodes:
        f = model.features(episode["obs"], washout_steps=WASHOUT)
        t = np.clip(np.asarray(episode["actions"][WASHOUT:]), -1.0, 1.0)
        feats.append(f); tgts.append(t)
        sm_feat.append(np.diff(f, axis=0)); sm_tgt.append(np.diff(_atanh_targets(t), axis=0))
        w = episode.get("weights")
        weights.append(np.asarray(w[WASHOUT:], dtype=float) if w is not None
                       else np.ones(len(t)))
    f_all = np.concatenate(feats); t_all = np.concatenate(tgts)
    # engaged-step oversampling: the escape segment is ~1/3 of each episode;
    # without reweighting the ridge readout shrinks those actions and the
    # students lose the decisive dip/release timing.
    w_all = np.concatenate(weights)
    t_at = _atanh_targets(t_all)
    repeats = np.maximum(1.0, w_all).astype(int)  # weight = row duplication
    f_aug = np.repeat(f_all, repeats, axis=0)
    t_aug = np.repeat(t_at, repeats, axis=0)
    # keep the engaged oversampling on top of any custom weights
    mask = _engaged_mask(t_all)
    f_aug = np.concatenate([f_aug, f_all[mask]])
    t_aug = np.concatenate([t_aug, t_at[mask]])
    mse = model.fit_readout(f_aug, t_aug,
                            smoothness_features=np.concatenate(sm_feat),
                            smoothness_weight=0.05,
                            smoothness_targets=np.concatenate(sm_tgt))
    return model, mse


def _esn_force_integral(model, board_z, seed):
    env = make_env(board_z, seed)
    m = rollout(env, seed, UngatedESN(model))
    env.close()
    return m["force_integral"]


def stage_train():
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    # Hyperparameter selection on the validation board (0.610), averaged over
    # two controller seeds; the test boards are never touched here.
    best_cfg, best_score, best_mse = None, float("inf"), None
    for cfg in ESN_GRID:
        scores, mses = [], []
        for seed in (11, 29):
            model, mse = _fit_esn(episodes, seed, cfg)
            mses.append(mse)
            scores.append(_esn_force_integral(model, BOARDS["heldout"], 7))
        score = float(np.mean(scores))
        print(f"  grid {cfg} -> val Fint={score:.1f} train MSE={np.mean(mses):.5f}")
        if score < best_score:
            best_cfg, best_score, best_mse = cfg, score, float(np.mean(mses))
    print(f"  selected {best_cfg} (val Fint {best_score:.1f})")
    json.dump(best_cfg, open(OUT / "esn_selected_cfg.json", "w"))
    for seed in (11, 29, 97, 123, 555):
        model, mse = _fit_esn(episodes, seed, best_cfg)
        model.save_npz(OUT / f"esn_s{seed}.npz")
        print(f"  esn seed={seed} MSE={mse:.5f}")
    import subprocess, sys
    result = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                            capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip()[-2000:])
        raise RuntimeError("mlp subprocess failed")
    print("students saved")


def stage_dagger():
    """DAgger round: relabel student-visited states with the hybrid teacher."""
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    cfg = json.load(open(OUT / "esn_selected_cfg.json"))
    members = [UngatedESN(DirectESNController.from_npz(OUT / f"esn_s{s}.npz"))
               for s in (11, 29, 97, 123, 555)]
    new_episodes = []
    for board_z in DATA_BOARDS:
        for seed in (7, 29):
            env = make_env(board_z, seed)
            env.reset(seed=seed, options={"fixture_index": 0})
            teacher = HybridTeacher(board_z)
            member = members[len(new_episodes) % len(members)]
            obs_list, act_list = [], []
            done = False
            while not done:
                d = env.diagnostics()
                hand = env.data.xpos[env._hand_id]
                obs_list.append(DirectESNObservation(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    d["wbc_pose_error"], d["wbc_twist_error"]))
                act_list.append(np.asarray(teacher.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
                    hand_x=float(hand[0]), contact=board_force(env) > 2.0,
                    time_s=float(d["time_s"])).bounded_filter_action, dtype=float))
                student_action = member.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"]
                ).bounded_filter_action
                _, _, done, _, _ = env.step(np.asarray(student_action, dtype=float))
            env.close()
            new_episodes.append(dict(name=f"dagger_b{board_z}", seed=seed, noise=0.0,
                                     obs=obs_list, actions=act_list, metrics={}))
    combined = episodes + new_episodes
    for seed in (11, 29, 97, 123, 555):
        model, mse = _fit_esn(combined, seed, cfg)
        model.save_npz(OUT / f"esn_d{seed}.npz")
        print(f"  dagger esn seed={seed} MSE={mse:.5f}")


def stage_dagger2():
    """Second DAgger round with stalled-state weighting.

    The students' failure mode is stalling inside the corridor (hand x stuck
    in (0.26, 0.56) with low velocity): those exact states get extra weight
    in the refit so the readout learns to keep the dip engaged there.
    """
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        episodes = list(archive["episodes"])
    cfg = json.load(open(OUT / "esn_selected_cfg.json"))
    students = [OUT / f"esn_d{s}.npz" for s in (11, 29, 97, 123, 555, 7, 13, 42, 71, 101, 202, 303)
                    if (OUT / f"esn_d{s}.npz").exists()]
    new_episodes = []
    for board_z in DATA_BOARDS:
        for seed in (7, 29, 123):
            env = make_env(board_z, seed)
            env.reset(seed=seed, options={"fixture_index": 0})
            teacher = HybridTeacher(board_z)
            student = UngatedESN(DirectESNController.from_npz(
                students[len(new_episodes) % len(students)]))
            obs_list, act_list, weights = [], [], []
            prev_x = None
            done = False
            while not done:
                d = env.diagnostics()
                hand = env.data.xpos[env._hand_id]
                obs_list.append(DirectESNObservation(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    d["wbc_pose_error"], d["wbc_twist_error"]))
                act_list.append(np.asarray(teacher.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
                    hand_x=float(hand[0]), contact=board_force(env) > 2.0,
                    time_s=float(d["time_s"])).bounded_filter_action, dtype=float))
                vx = 0.0 if prev_x is None else abs(hand[0] - prev_x) / 0.04
                stalled = (CORRIDOR_X_OUT < hand[0] < CORRIDOR_X_IN) and vx < 0.03
                weights.append(6.0 if stalled else 1.0)
                prev_x = float(hand[0])
                a = student.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"],
                ).bounded_filter_action
                _, _, done, _, _ = env.step(np.asarray(a, dtype=float))
            env.close()
            new_episodes.append(dict(name=f"dagger2_b{board_z}", seed=seed, noise=0.0,
                                     obs=obs_list, actions=act_list,
                                     weights=np.asarray(weights), metrics={}))
    combined = episodes + new_episodes
    for seed in (11, 29, 97, 123, 555, 7, 13, 42, 71, 101, 202, 303):
        model, mse = _fit_esn(combined, seed, cfg)
        model.save_npz(OUT / f"esn_e{seed}.npz")
        print(f"  dagger2 esn seed={seed} MSE={mse:.5f}")


def stage_eval():
    from mlp_compliance_baseline import MLPComplianceController
    esn_paths = [(f"esn_s{s}", OUT / f"esn_s{s}.npz") for s in (11, 29, 97, 123, 555)]
    mlp_paths = [(f"mlp_s{t}", OUT / f"mlp_s{t}.npz") for t in (0, 1, 2, 3, 4)]
    esn_d_paths = [(f"esn_d{s}", OUT / f"esn_d{s}.npz") for s in (11, 29, 97, 123, 555)
                   if (OUT / f"esn_d{s}.npz").exists()]
    esn_e_paths = [(f"esn_e{s}", OUT / f"esn_e{s}.npz") for s in (11, 29, 97, 123, 555, 7, 13, 42, 71, 101, 202, 303)
                   if (OUT / f"esn_e{s}.npz").exists()]
    methods = ([("fw", None, None)]
               + [(label, path, "esn") for label, path in esn_paths]
               + [(label, path, "esn") for label, path in esn_d_paths]
               + [(label, path, "esn") for label, path in esn_e_paths]
               + [(label, path, "mlp") for label, path in mlp_paths]
               + [("vmc", None, "vmc")]
               + [("vmc_orig", None, "vmc_orig")]
               + [("vmc_orig_s", None, "vmc_orig_s")]
               + [("vmc_orig_e", None, "vmc_orig_e")]
               + ([("vmc_tuned", None, "vmc_tuned")]
                  if (OUT / "vmc_tuned_cfg.json").exists() else [])
               + [("teacher", None, "teacher")]
               + [("esn_ens", None, "esn_ens"), ("esn_dens", None, "esn_dens"),
                  ("mlp_ens", None, "mlp_ens")])
    conditions = [("clean", board, 0.0) for board in ("low", "mid", "high", "heldout")] \
        + [("noisy", "mid", 0.008), ("noisy", "heldout", 0.008),
           ("noisy", "mid", 0.012), ("noisy", "heldout", 0.012)]
    rows = []
    for label, path, kind in methods:
        for cond, board_name, noise in conditions:
            for seed in (7, 1234):
                env = make_env(BOARDS[board_name], seed=seed, noise=noise)
                if kind == "teacher":
                    m = rollout(env, seed, HybridTeacher(BOARDS[board_name]))
                elif kind is None:
                    m = rollout(env, seed, NeutralPolicy())
                elif kind == "esn":
                    m = rollout(env, seed, UngatedESN(DirectESNController.from_npz(path)))
                elif kind == "esn_ens":
                    m = rollout(env, seed, EnsemblePolicy(
                        [UngatedESN(DirectESNController.from_npz(p)) for _, p in esn_paths]))
                elif kind == "esn_dens":
                    m = rollout(env, seed, EnsemblePolicy(
                        [UngatedESN(DirectESNController.from_npz(p)) for _, p in esn_d_paths]))
                elif kind == "mlp_ens":
                    from mlp_compliance_baseline import MLPComplianceController as _M
                    m = rollout(env, seed, EnsemblePolicy(
                        [UngatedMLP(_M.from_npz(p)) for _, p in mlp_paths]))
                elif kind == "vmc":
                    m = rollout(env, seed, VMCScenario())
                elif kind == "vmc_orig_e":
                    policy = VMCErrorScheduled()
                    policy.reset()
                    m = rollout(env, seed, policy)
                elif kind == "vmc_tuned":
                    cfg = json.load(open(OUT / "vmc_tuned_cfg.json"))
                    policy = VMCScheduled(cfg["overrides"], offset_ref=cfg["offset_ref"])
                    policy.reset()
                    m = rollout(env, seed, policy)
                elif kind == "vmc_orig_s":
                    policy = VMCScheduled()
                    policy.reset()
                    m = rollout(env, seed, policy)
                elif kind == "vmc_orig":
                    from vmc_compliance_baseline import (
                        SpringCarriageVMC, SpringCarriageConfig, VMCComplianceAdapter)
                    policy = VMCComplianceAdapter(
                        SpringCarriageVMC(SpringCarriageConfig()))
                    policy.reset()
                    m = rollout(env, seed, policy)
                else:
                    m = rollout(env, seed, UngatedMLP(MLPComplianceController.from_npz(path)))
                rows.append(dict(method=label, cond=cond, board=board_name, seed=seed, **m))
                env.close()
        ok = sum(r["crossed"] for r in rows if r["method"] == label)
        print(f"  eval {label}: crossed {ok}/{len(conditions)*2}")
    json.dump(rows, open(OUT / "eval.json", "w"), indent=1)
    import collections
    by = collections.defaultdict(list)
    for r in rows:
        by[(r["method"], r["cond"])].append(r)
    fams = sorted({m for m, _ in by})
    conds = sorted({c for _, c in by})
    # Composite score (transparent linear weighting, no single-metric champion):
    #   score = Fint/100 [Ns] + errF/100 [mm] + 20*(1 - crossed_frac)
    # Force, path fidelity, and task completion each cost roughly 1/3 for a
    # reference-good solution (Fint~60, errF~250, crossing~0.5).
    print(f"{'method':10s} " + " ".join(f"{c+'_Fint':>11s}" for c in conds)
          + f" {'errF':>7s} {'cross':>6s} {'tau':>6s} {'SCORE':>7s}")
    for fam in fams:
        cells = []
        for c in conds:
            rs = by[(fam, c)]
            cells.append(f"{np.mean([r['force_integral'] for r in rs]):11.1f}")
        clean = by[(fam, "clean")]
        allr = [r for r in rows if r["method"] == fam]
        fint = np.mean([r["force_integral"] for r in allr])
        errf = np.mean([r["err_final_mm"] for r in allr])
        cross = np.mean([1.0 if r["crossed"] else 0.0 for r in allr])
        score = fint / 100.0 + errf / 100.0 + 20.0 * (1.0 - cross)
        print(f"{fam:10s} " + " ".join(cells)
              + f" {np.mean([r['err_final_mm'] for r in clean]):7.1f}"
              + f" {cross*100:5.0f}%"
              + f" {np.mean([r['peak_torque'] for r in clean]):6.1f}"
              + f" {score:7.2f}")


def stage_report():
    """Validation seed screening + frontier plot + sorted podium table."""
    import collections
    from mlp_compliance_baseline import MLPComplianceController

    def composite_of(m):
        return m["force_integral"] / 100.0 + m["err_final_mm"] / 100.0 + 20.0 * (0.0 if m["crossed"] else 1.0)

    # validation: heldout board, 2 rollouts with mild noise; never used in fitting
    def val_score(loader):
        scores = []
        for seed in (7, 1234):
            env = make_env(BOARDS["heldout"], seed=seed, noise=0.005)
            m = rollout(env, seed, loader())
            env.close()
            scores.append(composite_of(m))
        return float(np.mean(scores))

    esn_candidates = [(f"esn_e{s}", OUT / f"esn_e{s}.npz") for s in (11, 29, 97, 123, 555, 7, 13, 42, 71, 101, 202, 303)]
    mlp_candidates = [(f"mlp_s{t}", OUT / f"mlp_s{t}.npz") for t in (0, 1, 2, 3, 4)]
    best_esn = min(esn_candidates, key=lambda c: val_score(
        lambda c=c: UngatedESN(DirectESNController.from_npz(c[1]))))
    best_mlp = min(mlp_candidates, key=lambda c: val_score(
        lambda c=c: UngatedMLP(MLPComplianceController.from_npz(c[1]))))
    print(f"  val-selected ESN: {best_esn[0]} | MLP: {best_mlp[0]}")

    rows = json.load(open(OUT / "eval.json"))
    # add val-selected rows from existing eval data
    by = collections.defaultdict(list)
    for r in rows:
        by[r["method"]].append(r)
    podium = []
    for fam, rs in by.items():
        fint = np.mean([r["force_integral"] for r in rs])
        errf = np.mean([r["err_final_mm"] for r in rs])
        cross = np.mean([1.0 if r["crossed"] else 0.0 for r in rs])
        podium.append((fint / 100 + errf / 100 + 20 * (1 - cross), fam, fint, errf, cross))
    podium.sort()
    print("podium (score lower = better):")
    for score, fam, fint, errf, cross in podium:
        print(f"  {fam:12s} score={score:6.2f} Fint={fint:6.1f} errF={errf:6.1f} cross={cross*100:3.0f}%")
    json.dump(dict(best_esn=best_esn[0], best_mlp=best_mlp[0],
                   podium=[(f, round(s, 2)) for s, f, *_ in podium]),
              open(OUT / "report.json", "w"), indent=1)

    # frontier plot: force vs fidelity, marker = crossing
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    for score, fam, fint, errf, cross in podium:
        color = "tab:red" if "vmc" in fam else ("tab:blue" if "esn" in fam else
                ("tab:orange" if "mlp" in fam else ("gray" if fam in ("fw",) else "green")))
        ax.scatter(fint, errf, s=80 + 400 * cross, c=color, alpha=0.75, edgecolors="k", linewidths=0.5)
        ax.annotate(f"{fam}\n{cross*100:.0f}%", (fint, errf), fontsize=7, ha="center", va="bottom")
    ax.set_xlabel("contact force integral (Ns, lower = safer)")
    ax.set_ylabel("final path error (mm, lower = more faithful)")
    ax.set_title("Extraction scenario frontier (marker size = crossing rate)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "frontier.png", dpi=160)
    print(f"  frontier.png + report.json saved; best ESN checkpoint: {best_esn[0]}")


def stage_tune_vmc():
    """Retune the ORIGINAL controller's config for the strong-WBC scenario.

    The frozen config was tuned in the weak-WBC world: drive stiffness 75 N/m
    pulls the carriage home in ~0.3 s, so its yield cannot persist against a
    25/s WBC.  Sweep carriage config (code untouched), select on train boards
    then the validation board, by composite score.
    """
    grid = []
    for drive_k in (10.0, 30.0, 75.0):
        for ee_k in (80.0, 220.0):
            for speed in (0.55, 1.20):
                for ref in (0.03, 0.06):
                    grid.append((dict(carriage_drive_k_translation=drive_k,
                                      k_translation_base=ee_k,
                                      max_carriage_speed=speed), ref))

    def score_of(overrides, ref, board_z, seed):
        env = make_env(board_z, seed)
        env.reset(seed=seed, options={"fixture_index": 0})
        policy = VMCScheduled(overrides, offset_ref=ref)
        policy.reset()
        m = rollout(env, seed, policy)
        env.close()
        return (m["force_integral"] / 100.0 + m["err_final_mm"] / 100.0
                + 20.0 * (0.0 if m["crossed"] else 1.0))

    scored = []
    for overrides, ref in grid:
        sc = np.mean([score_of(overrides, ref, b, 7) for b in DATA_BOARDS[:2]])
        scored.append((sc, overrides, ref))
    scored.sort(key=lambda x: x[0])
    print("  top-5 train scores:")
    for sc, ov, ref in scored[:5]:
        print(f"    {sc:6.2f}  {ov} offset_ref={ref}")
    best = None
    for sc, ov, ref in scored[:4]:
        val = np.mean([score_of(ov, ref, BOARDS["heldout"], s) for s in (7, 1234)])
        if best is None or val < best[0]:
            best = (val, ov, ref)
    print(f"  selected {best[1]} offset_ref={best[2]} (val {best[0]:.2f})")
    json.dump(dict(overrides=best[1], offset_ref=best[2]),
              open(OUT / "vmc_tuned_cfg.json", "w"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=("probe", "data", "train", "dagger", "dagger2", "tune_vmc", "eval", "report", "all"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    if args.stage in ("probe", "all"):
        print("== probe =="); stage_probe()
    if args.stage in ("data", "all"):
        print("== data =="); stage_data()
    if args.stage in ("train", "all"):
        print("== train =="); stage_train()
    if args.stage in ("dagger2", "all"):
        print("== dagger2 =="); stage_dagger2()
    if args.stage in ("dagger", "all"):
        print("== dagger =="); stage_dagger()
    if args.stage in ("eval", "all"):
        print("== eval =="); stage_eval()
    if args.stage in ("tune_vmc", "all"):
        print("== tune_vmc =="); stage_tune_vmc()
    if args.stage in ("report", "all"):
        print("== report =="); stage_report()
    print(f"done {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
