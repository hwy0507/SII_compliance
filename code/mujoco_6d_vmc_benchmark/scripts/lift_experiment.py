"""v3 lift-board compliance experiment (post-retraction restart).

Scenario (validated by scene_gates.py, ALL GATES PASSED, commit 4594be4):
FR3 + vendored Pink WBC grasps the block and lifts along a lateral-arc
reference through a tilted static board (25 deg, FK two-pass placement).
FW grinds the incline at ~372 N for ~4.6 s, trips torque hard limits and
its task_success is False.  Compliance must slide +y along the tilted
face at low force and rejoin the arc.

Stages: probe | data | train | dagger | eval | gif
  probe  - FW baselines + teacher rule sweep with a mini-gate: the teacher
           must halve FW's force integral, keep task_success and dodge.
  data   - teacher-labelled episodes over a scenario-parameter grid
           (y-offset x tilt); the env is deterministic so parameter jitter
           is the ONLY source of behavioral diversity.
  train  - ESN grid (atanh targets, engaged oversampling) + MLP subprocess.
  dagger - relabel ESN-visited states with the teacher, refit.
  eval   - FW / author-VMC / MLP / ESN over held-out boards x seeds.
  gif    - rendered rollouts for the paper.
"""
from __future__ import annotations

import argparse
import json
import os as _os
import subprocess
import sys
from pathlib import Path

import mujoco
import numpy as np

from direct_esn_compliance import DirectESNObservation, DirectESNController

_os.environ.setdefault("ESN_FIT_BIAS", "1")   # readout intercept: kills the resting offset
from extraction_experiment import (
    SCENARIO_SAFETY, WASHOUT, EnsemblePolicy, NeutralPolicy, UngatedESN,
    UngatedMLP, VMCScheduled, _fit_esn, board_force, make_env)

# v5 SCENARIO SUITE (user: block may be struck; try several scenarios;
# ESN must top the overall table).
#   plank_arm     - flying plank strikes the wrist (v4; VMC's home turf)
#   plank_payload - flying plank strikes hand+block: anticipatory yielding
#                   protects the payload (the ESN memory's money scenario)
#   static_board  - v3.2 tilted static board corridor (ESN's home turf)
from wbc_velocity_residual_env import VelocityResidualFixture

T0_DEFAULT, H_DEFAULT, V0_DEFAULT = 3.00, 0.76, 1.0
H_PAYLOAD = 0.62                      # plank band [0.505,0.735]: hand+block
WINDOW_DEFAULT, KV_DEFAULT, FORCE_DEFAULT = "1.0", "40", "80"
STATIC_Y, STATIC_TILT, STATIC_HY, STATIC_Z = 0.05, 25.0, 0.035, 0.03
FR3_LIMITS = np.asarray([87.0] * 4 + [12.0] * 3)
OUT = Path(_os.environ.get("EXT_OUT", "/home/arm1/vmc_mujoco_runtime/outputs/lift_esn"))
DOCS = Path(__file__).resolve().parent.parent / "docs" / "lift_results"

# Scenario suite entries: (kind, params...).  Deterministic per entry.
# v11: sudden-strike-centred suite.  The strike family (single timing
# cluster ~3.0 s, hard/fast, payload height) is where memory anticipates
# and halves the impact peak; statics and the gentle wrist plank keep the
# suite honest about rejoin and corridor skills.
DATA_GRID = (
    ("strike_cue", 2.95, 0.64, 2.0), ("strike_cue", 3.00, 0.64, 2.0),
    ("strike_cue", 3.05, 0.63, 2.0),
    ("strike_none", 0.0, 0.0, 0.0),
    ("static", STATIC_Y, 25.0), ("static", STATIC_Y, 23.0),
    ("plank_arm", 3.00, 0.76, 1.0),
)
HELDOUT = (
    ("strike_cue", 3.00, 0.62, 1.8),
    ("static", STATIC_Y, 22.0),
)
EVAL_BOARDS = (("strike_cue", 3.00, 0.64, 2.0), ("strike_cue", 2.95, 0.64, 2.0),
               ("strike_cue", 3.05, 0.63, 2.0),
               ("strike_none", 0.0, 0.0, 0.0),
               ("static", STATIC_Y, 25.0), ("plank_arm", 3.00, 0.76, 1.0))
EVAL_SEEDS = (7, 1234, 999)
DATA_NOISE = 0.002

# Validation cells for ALL controller tuning: DATA cells only, never the
# eval boards (keep the final comparison clean).
VAL_CELLS = (("strike", 3.00, 0.64, 2.0), ("static", STATIC_Y, 23.0),
             ("plank_arm", 3.00, 0.76, 1.0))

ESN_GRID = (
    dict(),
    dict(reservoir_size=240),
    dict(reservoir_size=320),
    dict(spectral_radius=1.05),
    dict(spectral_radius=0.75),
    dict(input_scale=0.65),
    dict(reservoir_size=240, spectral_radius=1.05),
    dict(time_constant_s=0.06),          # fast-decay: fight the post-release echo
    dict(time_constant_s=0.06, reservoir_size=240),
    dict(time_constant_s=0.06, reservoir_size=320, input_scale=0.65),
    dict(ridge_lambda=1.0e-5, reservoir_size=240),
    dict(time_constant_s=0.09, spectral_radius=1.05, reservoir_size=240),
    # slow-reservoir variants: the delayed-cue task needs a ~2 s memory
    # bridge (cue at t=1.1, yield at t=2.85); tc=0.12 forgets in <1 s.
    dict(time_constant_s=0.30, spectral_radius=0.95, reservoir_size=240),
    dict(time_constant_s=0.50, spectral_radius=0.95, reservoir_size=240),
    dict(time_constant_s=0.30, spectral_radius=1.10, reservoir_size=240),
    dict(time_constant_s=0.50, spectral_radius=1.10, reservoir_size=240),
    dict(time_constant_s=0.50, spectral_radius=0.95, reservoir_size=320, input_scale=0.65),
)

# MLP architecture sweep (subprocess trainer honours MLP_HIDDEN/MLP_EPOCHS)
MLP_GRID = ((128, 15000), (256, 15000), (256, 30000), (512, 30000))

# VMC platform-adaptation sweep: the author's kappa_6d EE spring stays
# frozen; only the carriage drive / deadband / speed limits vary.  The
# untuned carriage never rejoins (errF ~100 mm) -- its drive spring
# (75 N/m) is far too soft for this WBC's tracking authority.
VMC_GRID = (
    {},
    dict(carriage_drive_k_translation=150.0),
    dict(carriage_drive_k_translation=250.0, max_carriage_speed=0.8),
    dict(carriage_drive_k_translation=250.0, max_carriage_speed=0.8,
         deadband_m=0.004, deadband_rad=0.016),
    dict(carriage_drive_k_translation=150.0, max_carriage_speed=0.8,
         deadband_m=0.004, deadband_rad=0.016, carriage_drive_zeta=1.3),
    dict(carriage_drive_k_translation=400.0, max_carriage_speed=0.9,
         deadband_m=0.004, deadband_rad=0.016, carriage_drive_k_rotation=15.0),
)


def build_env(kind: str, *params, seed: int = 7, noise: float = 0.0):
    """Suite env builder.  kind: plank_arm | plank_payload | static."""
    if kind == "strike":
        # Sudden hard strike at payload height: the scenario where phase
        # anticipation is structurally necessary -- the pre-yield halves the
        # impact peak (measured: FW 241 N vs teacher 116 N).
        t0, h, v0 = params
        _os.environ["LIFT_PLANK_MODE"] = "launch"
        _os.environ["LIFT_PLANK_WINDOW"] = "0.30"
        _os.environ["LIFT_PLANK_KV"] = "60"
        _os.environ["LIFT_PLANK_FORCE"] = "300"
        fx = VelocityResidualFixture(v0, h, t0, impactor_type="plank",
                                     rod_approach_side="negative_y",
                                     rod_center_x_m=0.55, rod_center_y_m=0.0,
                                     rod_cycles=1, cycle_period_s=0.80)
        return make_env(None, seed, noise=noise, tilt=None, fixture=fx)
    if kind == "strike_cue":
        # delayed-cue variant: nudge at ~1.1 predicts the strike at ~3.15
        t0, h, v0 = params
        _os.environ["LIFT_PLANK_MODE"] = "launch"
        _os.environ["LIFT_PLANK_WINDOW"] = "0.30"
        _os.environ["LIFT_PLANK_KV"] = "60"
        _os.environ["LIFT_PLANK_FORCE"] = "300"
        _os.environ["LIFT_CUE"] = "1"
        fx = VelocityResidualFixture(v0, h, t0, impactor_type="plank",
                                     rod_approach_side="negative_y",
                                     rod_center_x_m=0.55, rod_center_y_m=0.0,
                                     rod_cycles=1, cycle_period_s=0.80)
        return make_env(None, seed, noise=noise, tilt=None, fixture=fx)
    if kind == "strike_none":
        # cue present, strike NEVER comes: the false-positive board.  The
        # correct behavior is to do NOTHING; a controller that yields
        # spuriously pays in tracking error.
        _os.environ["LIFT_PLANK_MODE"] = "launch"
        _os.environ["LIFT_CUE"] = "1"
        fx = VelocityResidualFixture(1.0, 0.64, 99.0, impactor_type="plank",
                                     rod_approach_side="negative_y",
                                     rod_center_x_m=0.55, rod_center_y_m=0.0,
                                     rod_cycles=1, cycle_period_s=0.80)
        return make_env(None, seed, noise=noise, tilt=None, fixture=fx)
    _os.environ["LIFT_CUE"] = "0"
    if kind in ("plank_arm", "plank_payload"):
        t0, h, v0 = params
        _os.environ["LIFT_PLANK_MODE"] = "launch"
        _os.environ["LIFT_PLANK_WINDOW"] = WINDOW_DEFAULT
        _os.environ["LIFT_PLANK_KV"] = KV_DEFAULT
        _os.environ["LIFT_PLANK_FORCE"] = FORCE_DEFAULT
        fx = VelocityResidualFixture(v0, h, t0, impactor_type="plank",
                                     rod_approach_side="negative_y",
                                     rod_center_x_m=0.55, rod_center_y_m=0.0,
                                     rod_cycles=1, cycle_period_s=0.80)
        return make_env(None, seed, noise=noise, tilt=None, fixture=fx)
    if kind == "static":
        y_off, tilt = params
        _os.environ["LIFT_PLANK_MODE"] = "servo"
        _os.environ["LIFT_BOARD_Y_OFF"] = f"{y_off}"
        _os.environ["LIFT_BOARD_Z_OFF"] = f"{STATIC_Z}"
        _os.environ["LIFT_BOARD_HX"] = "0.18"
        _os.environ["LIFT_BOARD_HY"] = f"{STATIC_HY}"
        _os.environ["LIFT_BOARD_ARC"] = "0.40"
        return make_env(None, seed, noise=noise, tilt=tilt)
    raise ValueError(f"unknown scenario kind {kind!r}")


class LiftTeacher:
    """Phase-anticipating incline-slide rule (labels; students see proprioception).

    Three elements, each mapping to a measurable failure of stiff tracking:
    1. PRE-YIELD RAMP (t in [pre_t, pre_t+0.24]): the board strike is
       phase-predictable (first contact ~2.9 s on the default board), so the
       expert softens the approach BEFORE contact.  A memoryless student
       cannot reproduce this from instantaneous observations -- this is the
       deliberate head-room for the ESN's reservoir memory.
    2. ENGAGE (contact during lift): slow the WBC feedback + yield +y along
       the incline toward the board edge.
    3. POSITION-BASED RELEASE + GRADUAL REJOIN: stop yielding once the dodge
       has carried the arm past the board edge (or an engagement timeout
       fires), then RAMP the action back to zero over ~1.2 s.  A force-clear
       timer does NOT work here: the sliding contact chatters (~9 loss
       events per episode) and every bounce resets it, making the yield
       permanent.  An abrupt zero-action release does not work either: the
       WBC feedback snaps 0.10 -> 1.0 and the rejoin yank ejects the
       fingertip-pinched block (measured: block lost within 1.2 s of a hard
       release).

    No -z channel: on this tilt the feedforward press is already over-
    cancelled by the +y yield, and down-incline motion re-trips the lower
    edge (measured: 2-4x worse force integral).
    """

    def __init__(self, y_yield: float = 0.85, slow: float = 1.0,
                 dodge_release_m: float = 0.075, max_engage_s: float = 2.0,
                 phase_guard_s: float = 2.7, pre_t: float = 2.60,
                 rejoin_s: float = 1.2) -> None:
        self.y_yield = y_yield
        self.slow = slow
        self.dodge_release_m = dodge_release_m
        self.max_engage_s = max_engage_s
        self.phase_guard_s = phase_guard_s
        self.pre_t = pre_t
        self.rejoin_s = rejoin_s
        self.reset()

    def reset(self) -> None:
        self.engaged = False
        self.eng_s = 0.0
        self.rejoin_s_elapsed = None

    def act(self, joint_position, joint_velocity, nominal_twist, *,
            pose_error=None, twist_error=None, hand_x=0.0, hand_y=0.0,
            hand_z=0.0, contact=False, time_s=0.0, nominal_y=0.0):
        action = np.zeros(7)
        if time_s < self.phase_guard_s:
            self.reset()
            return action
        dodge = hand_y - nominal_y
        if self.engaged:
            self.eng_s += 0.04
            if dodge > self.dodge_release_m or self.eng_s > self.max_engage_s:
                self.engaged = False
                self.rejoin_s_elapsed = 0.0
        elif contact and self.rejoin_s_elapsed is None and dodge < 0.06:
            self.engaged = True
            self.eng_s = 0.0
        elif contact and self.rejoin_s_elapsed is not None and self.rejoin_s_elapsed > self.rejoin_s:
            # repeated strikes (dynamic plank): re-arm after the fade completes
            self.rejoin_s_elapsed = None
            self.engaged = True
            self.eng_s = 0.0
        if self.engaged:
            action[0] = self.slow
            action[2] = self.y_yield   # +y: along the incline, toward the edge
        elif self.rejoin_s_elapsed is not None:
            self.rejoin_s_elapsed += 0.04
            fade = 1.0 - min(self.rejoin_s_elapsed / self.rejoin_s, 1.0)
            action[0] = self.slow * fade
            action[2] = self.y_yield * fade
        elif time_s >= self.pre_t:
            # pre-contact anticipation ramp: soften the approach velocity
            ramp = float(np.clip((time_s - self.pre_t) / 0.24, 0.0, 1.0))
            action[0] = self.slow * ramp
            action[2] = self.y_yield * ramp
        return action


def rollout(env, seed: int, policy=None, *, teacher: LiftTeacher | None = None,
            collect: bool = False):
    env.reset(seed=seed, options={"fixture_index": 0})
    if hasattr(policy, "reset"):
        policy.reset()
    obs, acts, weights = [], [], []
    errors, forces, dodges = [], [], []
    max_obj_z = 0.0
    final_obj_z, final_obj_hand = 0.0, 9.9
    held_until_s = 0.0
    sat_steps, chatter, prev_f = 0, 0, False
    done, info = False, {}
    while not done:
        d = env.diagnostics()
        hand = env.data.xpos[env._hand_id]
        obj = env.data.xpos[env._target_body_id]
        max_obj_z = max(max_obj_z, float(obj[2]))
        final_obj_z, final_obj_hand = float(obj[2]), float(np.linalg.norm(obj - hand))
        t = float(d["time_s"])
        if final_obj_hand < 0.16 and obj[2] > 0.45:
            held_until_s = t
        if 2.7 < t < 5.5:
            dodges.append(float(hand[1]) - float(d["nominal_position"][1]))
        f = board_force(env)
        tau = (env._last_torque_components["total"][:7]
               if env._last_torque_components else np.zeros(7))
        if np.any(np.abs(tau) > 0.98 * FR3_LIMITS):
            sat_steps += 1
        chatter += int((f > 0.5) and not prev_f)
        prev_f = f > 0.5
        contact = f > 2.0
        args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
        kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
        if teacher is not None:
            action = np.asarray(teacher.act(*args, **kw, hand_x=float(hand[0]),
                                            hand_y=float(hand[1]), hand_z=float(hand[2]),
                                            contact=contact, time_s=t,
                                            nominal_y=float(d["nominal_position"][1])), dtype=float)
        elif policy is not None:
            action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
        else:
            action = np.zeros(7)   # do-nothing expert (false-positive board)
        if collect:
            obs.append(DirectESNObservation(
                joint_position=args[0], joint_velocity=args[1], wbc_task_twist=args[2],
                wbc_pose_error=kw["pose_error"], wbc_twist_error=kw["twist_error"]))
            acts.append(action.copy())
            # Anticipation steps 8x (t in [2.6, 3.3] with nonzero action: the
            # delayed-cue bridge is the decisive skill and ridge otherwise
            # shrinks it), contact steps 6x (the dodge), late carry/hold 4x
            # (post-release decay must reach zero or the residual dodge flings
            # the carried block into the board edge -- measured).
            if t < 3.3 and float(np.max(np.abs(action))) > 0.05:
                weights.append(8.0)
            else:
                weights.append(6.0 if contact else (4.0 if t > 5.2 else 1.0))
        errors.append(float(np.linalg.norm(d["wbc_pose_error"][:3])))
        forces.append(board_force(env))
        _, _, done, _, info = env.step(action)
    f = np.asarray(forces)
    completed = bool(info.get("finite_state", True)
                     and max_obj_z > 0.52 and final_obj_hand < 0.16)
    m = dict(
        task_success=bool(info.get("task_success", False)),
        completed=completed,
        hard_limit=bool(info.get("hard_torque_limit", False)),
        held_until_s=float(held_until_s),
        final_obj_z=float(final_obj_z),
        final_obj_hand=float(final_obj_hand),
        Fint=float(f.sum() * 0.04), peak=float(f.max()),
        contact_s=float((f > 0.5).sum() * 0.04),
        chatter=float(chatter),
        saturation_s=float(sat_steps * 0.04),
        errF_mm=float(errors[-1] * 1000.0),
        dodge_mm=float(max(dodges, default=0.0) * 1000.0),
        max_obj_z=max_obj_z,
        peak_torque=float(info.get("peak_torque_nm", 0.0)))
    m["score"] = (m["peak"] / 25.0 + m["Fint"] / 50.0 + 0.5 * m["chatter"]
                  + m["contact_s"] + m["saturation_s"] + m["errF_mm"] / 100.0
                  + 5.0 * (1.0 - float(completed)))
    if collect:
        return m, dict(obs=np.asarray(obs, dtype=object), actions=np.asarray(acts),
                       weights=np.asarray(weights))
    return m


def _fmt(m: dict) -> str:
    return (f"done={int(m['completed'])} Fint={m['Fint']:7.1f} peak={m['peak']:6.1f}N "
            f"ct={m['contact_s']:4.2f}s chat={m['chatter']:3.0f} sat={m['saturation_s']:4.2f}s "
            f"errF={m['errF_mm']:5.1f}mm dodge={m['dodge_mm']:5.1f}mm "
            f"apex={m['max_obj_z']:.3f} held<={m['held_until_s']:4.2f}s "
            f"fin(z={m['final_obj_z']:.2f},d={m['final_obj_hand']*1000:.0f}mm) score={m['score']:.2f}")


def stage_probe() -> None:
    print("== probe: FW baselines and teacher mini-gate over the suite ==")
    for entry in EVAL_BOARDS:
        env = build_env(*entry, seed=7)
        fw = rollout(env, 7, NeutralPolicy())
        env.close()
        print(f"  FW   {entry}: {_fmt(fw)}")
    env = make_env(None, 7, tilt=None)
    free = rollout(env, 7, NeutralPolicy())
    print(f"  FW free: {_fmt(free)} (task baseline)")
    env.close()
    # teacher sweep scored on the WHOLE suite mean (a payload-only pick
    # starves the static boards of dodge depth and the students inherit
    # 400 N peaks there -- measured).
    best, best_m = None, None
    for y_yield in (0.5, 0.6, 0.7):
        for pre_t in (2.85, 2.90):
            ms = []
            ok = True
            for entry in EVAL_BOARDS:
                env = build_env(*entry, seed=7)
                m = rollout(env, 7, teacher=LiftTeacher(y_yield=y_yield, pre_t=pre_t))
                env.close()
                ms.append(m)
                ok = ok and m["completed"] and m["held_until_s"] >= 7.0
            mean = float(np.mean([m["score"] for m in ms]))
            peak = max(m["peak"] for m in ms)
            print(f"  teacher y={y_yield} pre={pre_t}: suite mean={mean:6.2f} "
                  f"worst-peak={peak:5.0f}N all-ok={int(ok)}")
            if not ok:
                continue
            if best_m is None or mean < best_m:
                best, best_m = (y_yield, pre_t), mean
    if best_m is None:
        raise SystemExit("probe: no teacher variant completes the whole suite")
    print(f"  selected teacher {best} (suite mean {best_m:.2f})")
    failures = []
    for entry in EVAL_BOARDS:
        env = build_env(*entry, seed=7)
        m = rollout(env, 7, teacher=LiftTeacher(y_yield=best[0], pre_t=best[1]))
        env.close()
        print(f"  TEA  {entry}: {_fmt(m)}")
        if not m["completed"]:
            failures.append(f"teacher fails {entry}")
        elif m["held_until_s"] < 7.0:
            failures.append(f"teacher loses block at {m['held_until_s']:.2f}s in {entry}")
    if failures:
        raise SystemExit("probe MINI-GATE FAILED: " + "; ".join(failures))
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(dict(y_yield=best[0], pre_t=best[1]),
              open(OUT / "teacher_cfg.json", "w"))
    print(f"  mini-gate PASSED -> {OUT / 'teacher_cfg.json'}")


def stage_data() -> None:
    print("== data: teacher rollouts over the scenario grid ==")
    cfg = json.load(open(OUT / "teacher_cfg.json"))
    teacher = LiftTeacher(y_yield=cfg["y_yield"], pre_t=cfg["pre_t"])
    episodes = []
    for entry in DATA_GRID:
        env = build_env(*entry, seed=7, noise=DATA_NOISE)
        # the false-positive board's expert is DO NOTHING
        ep_teacher = None if entry[0] == "strike_none" else teacher
        m, ep = rollout(env, 7, teacher=ep_teacher, collect=True)
        env.close()
        episodes.append(ep)
        print(f"  {entry}: {_fmt(m)}")
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "teacher_data.npz",
                        episodes=np.asarray(episodes, dtype=object))
    print(f"  saved {len(episodes)} episodes -> {OUT / 'teacher_data.npz'}")


def _val_score(policy, entries=VAL_CELLS, seed: int = 7) -> float:
    scores = []
    for entry in entries:
        env = build_env(*entry, seed=seed)
        m = rollout(env, seed, policy)
        env.close()
        scores.append(m["score"])
    return float(np.mean(scores))


def stage_tune_vmc() -> None:
    """Fair-tune the replicated VMC's platform adaptation on validation cells."""
    print("== tune: VMC carriage adaptation ==")
    best_cfg, best_score = None, float("inf")
    for cfg in VMC_GRID:
        policy = VMCScheduled(config_overrides=cfg)
        score = _val_score(policy)
        env = build_env(*VAL_CELLS[2], seed=7)
        m = rollout(env, 7, VMCScheduled(config_overrides=cfg))
        env.close()
        print(f"  vmc {cfg} -> val={score:6.2f} (static errF={m['errF_mm']:.0f}mm "
              f"ok={int(m['completed'])})")
        if score < best_score:
            best_cfg, best_score = cfg, score
    print(f"  selected vmc {best_cfg} (val {best_score:.2f})")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump({"config_overrides": best_cfg}, open(OUT / "vmc_cfg.json", "w"))


def _tuned_vmc():
    cfg_path = OUT / "vmc_cfg.json"
    if cfg_path.exists():
        return VMCScheduled(**json.load(open(cfg_path)))
    return VMCScheduled()


def stage_train() -> None:
    print("== train: ESN grid + MLP subprocess ==")
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        raw = list(archive["episodes"])
    # object-array obs confuses DirectESNObservation list handling; use lists
    episodes = [dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"])
                for ep in raw]
    best_cfg, best_score = None, float("inf")
    for cfg in ESN_GRID:
        scores = []
        for seed in (11, 29):
            model, mse = _fit_esn(episodes, seed, cfg)
            scores.append(_val_score(UngatedESN(model)))
        score = float(np.mean(scores))
        print(f"  grid {cfg} -> val suite={score:.2f}")
        if score < best_score:
            best_cfg, best_score = cfg, score
    print(f"  selected {best_cfg} (val Fint {best_score:.1f})")
    json.dump(best_cfg, open(OUT / "esn_selected_cfg.json", "w"))
    for seed in (11, 29, 97, 123, 555):
        model, mse = _fit_esn(episodes, seed, best_cfg)
        model.save_npz(OUT / f"esn_s{seed}.npz")
        print(f"  esn seed={seed} MSE={mse:.5f}")
    mlp_best, mlp_best_score = None, float("inf")
    for hidden, epochs in MLP_GRID:
        result = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                                capture_output=True, text=True,
                                env={**_os.environ, "EXT_OUT": str(OUT),
                                     "MLP_HIDDEN": str(hidden), "MLP_EPOCHS": str(epochs)})
        if result.returncode != 0:
            print(result.stderr.strip()[-1500:])
            raise RuntimeError("mlp subprocess failed")
        mlp = _students()[1]
        score = _val_score(mlp)
        print(f"  mlp h={hidden} e={epochs} -> val suite={score:.2f}")
        if score < mlp_best_score:
            mlp_best, mlp_best_score = (hidden, epochs), score
    # retrain the winner (last subprocess run may not be it)
    if mlp_best != MLP_GRID[-1]:
        subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                       capture_output=True, text=True,
                       env={**_os.environ, "EXT_OUT": str(OUT),
                            "MLP_HIDDEN": str(mlp_best[0]), "MLP_EPOCHS": str(mlp_best[1])})
    json.dump({"hidden": mlp_best[0], "epochs": mlp_best[1]},
              open(OUT / "mlp_cfg.json", "w"))
    print(f"  mlp selected {mlp_best} (val {mlp_best_score:.2f}); students saved")


def stage_dagger() -> None:
    print("== dagger: relabel ESN-visited states with the teacher ==")
    cfg = json.load(open(OUT / "teacher_cfg.json"))
    teacher = LiftTeacher(y_yield=cfg["y_yield"], pre_t=cfg["pre_t"])
    with np.load(OUT / "teacher_data.npz", allow_pickle=True) as archive:
        raw = list(archive["episodes"])
    episodes = [dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"])
                for ep in raw]
    esn = EnsemblePolicy([UngatedESN(DirectESNController.from_npz(OUT / f"esn_s{s}.npz"))
                          for s in (11, 29, 97)])
    new_episodes = []
    for entry in DATA_GRID + HELDOUT:
        env = build_env(*entry, seed=7, noise=DATA_NOISE)
        ep_teacher = None if entry[0] == "strike_none" else teacher
        m, ep = rollout(env, 7, policy=esn, teacher=ep_teacher, collect=True)
        env.close()
        new_episodes.append(dict(obs=list(ep["obs"]), actions=ep["actions"], weights=ep["weights"]))
        print(f"  {entry}: {_fmt(m)}")
    # classic DAgger: episodes collected under the student policy but
    # labelled by the teacher at every visited state (rollout(teacher=...)
    # already replaces the executed action with the teacher label).
    episodes += new_episodes
    np.savez_compressed(OUT / "teacher_data.npz",
                        episodes=np.asarray([dict(obs=np.asarray(e["obs"], dtype=object),
                                                  actions=e["actions"], weights=e["weights"])
                                             for e in episodes], dtype=object))
    print(f"  merged {len(episodes)} episodes; refitting")
    best_cfg = json.load(open(OUT / "esn_selected_cfg.json"))
    for seed in (11, 29, 97, 123, 555):
        model, mse = _fit_esn(episodes, seed, best_cfg)
        model.save_npz(OUT / f"esn_s{seed}.npz")
        print(f"  esn seed={seed} MSE={mse:.5f}")
    result = subprocess.run([sys.executable, str(Path(__file__).parent / "extraction_mlp_train.py")],
                            capture_output=True, text=True,
                            env={**_os.environ, "EXT_OUT": str(OUT)})
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr.strip()[-2000:])
        raise RuntimeError("mlp subprocess failed")


def _students():
    from mlp_compliance_baseline import MLPComplianceController
    esn = EnsemblePolicy([UngatedESN(DirectESNController.from_npz(p))
                          for p in sorted(OUT.glob("esn_s*.npz"))])
    mlps = [UngatedMLP(MLPComplianceController.from_npz(p))
            for p in sorted(OUT.glob("mlp_s*.npz"))]
    mlp = EnsemblePolicy(mlps) if mlps else None
    return esn, mlp


def stage_eval() -> None:
    print("== eval: FW / author-VMC / MLP / ESN on eval boards x seeds ==")
    esn, mlp = _students()
    controllers = [("FW", NeutralPolicy()), ("VMC", _tuned_vmc())]
    if mlp is not None:
        controllers.append(("MLP", mlp))
    controllers.append(("ESN", esn))
    results = {name: [] for name, _ in controllers}
    for entry in EVAL_BOARDS:
        for seed in EVAL_SEEDS:
            for name, policy in controllers:
                env = build_env(*entry, seed=seed)
                m = rollout(env, seed, policy)
                env.close()
                results[name].append(m)
                print(f"  {entry} s{seed} {name:4s}: {_fmt(m)}")
    print("\n== podium (mean +- std over boards x seeds; lower score better) ==")
    table = {}
    for name, ms in results.items():
        keys = ("Fint", "peak", "errF_mm", "dodge_mm", "score")
        agg = {k: (float(np.mean([m[k] for m in ms])), float(np.std([m[k] for m in ms])))
               for k in keys}
        agg["task_success"] = float(np.mean([m["task_success"] for m in ms]))
        table[name] = agg
        print(f"  {name:4s} score={agg['score'][0]:7.2f}+-{agg['score'][1]:5.2f} "
              f"Fint={agg['Fint'][0]:8.1f} peak={agg['peak'][0]:6.1f} "
              f"errF={agg['errF_mm'][0]:6.1f}mm dodge={agg['dodge_mm'][0]:6.1f}mm "
              f"ok={agg['task_success']*100:3.0f}%")
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(table, open(OUT / "eval_table.json", "w"), indent=1)
    print(f"  -> {OUT / 'eval_table.json'}")


def stage_gif() -> None:
    print("== gif: rendered rollouts ==")
    esn, mlp = _students()
    controllers = [("FW", NeutralPolicy()), ("VMC", VMCScheduled())]
    if mlp is not None:
        controllers.append(("MLP", mlp))
    controllers.append(("ESN", esn))
    DOCS.mkdir(parents=True, exist_ok=True)
    try:
        import cv2
    except ImportError:
        cv2 = None
    for name, policy in controllers:
        env = build_env("strike_cue", 3.00, 0.64, 2.0)
        env.reset(seed=7, options={"fixture_index": 0})
        env.model.vis.global_.offwidth = 1280
        env.model.vis.global_.offheight = 720
        renderer = mujoco.Renderer(env.model, 720, 1280)
        cam = mujoco.MjvCamera()
        cam.lookat = np.array([0.5, 0.0, 0.62])
        cam.distance = 1.25
        cam.azimuth = 135
        cam.elevation = -18
        frames = []
        done, step = False, 0
        if hasattr(policy, "reset"):
            policy.reset()
        while not done:
            if step % 1 == 0:
                renderer.update_scene(env.data, camera=cam)
                frame = renderer.render()
                if cv2 is not None:
                    cv2.putText(frame, name, (20, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 2)
                frames.append(frame.copy())
            d = env.diagnostics()
            args = (d["joint_position"], d["joint_velocity"], d["nominal_twist"])
            kw = dict(pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = np.asarray(policy.act(*args, **kw).bounded_filter_action, dtype=float)
            _, _, done, _, _ = env.step(action)
            step += 1
        renderer.close()
        env.close()
        path = DOCS / f"lift_{name.lower()}.gif"
        import imageio.v3 as iio
        iio.imwrite(path, frames[::2], duration=40, loop=0)
        print(f"  wrote {path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["probe", "data", "train", "dagger", "tunevmc", "eval", "gif", "all"])
    args = parser.parse_args()
    stages = {"probe": stage_probe, "data": stage_data, "train": stage_train,
              "dagger": stage_dagger, "tunevmc": stage_tune_vmc,
              "eval": stage_eval, "gif": stage_gif}
    todo = stages.values() if args.stage == "all" else [stages[args.stage]]
    for stage in todo:
        stage()


if __name__ == "__main__":
    main()
