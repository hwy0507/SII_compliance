#!/usr/bin/env python3
"""Paper-MPC nominal-controller compliance benchmark (branch experiment).

Replaces the nominal WBC with the faithful reimplementation of the paper
system's one-step quadratic velocity controller (``paper_mpc_wbc.py``), then
evaluates three perturbation scenarios x compliance methods:

Scenarios:
  rod   - the standard rail-impact fixtures (4 severities)
  ball  - the same fixtures with the spherical impactor
  board - rod parked; a static inclined wooden board across the lift path
          (the rising arm strikes the tilted face mid-lift)

Methods:
  none  - paper MPC alone (no compliance layer)
  esn / mlp   - the previously trained torque-residual students, zero-shot
  vmc_k<b>_s<s> - the torque-mode spring-carriage VMC, stiffness/budget sweep

Metrics per rollout: task success, at-grasp tracking error, peak torque,
peak impactor/board contact force, and post-impact recovery time (first
return below 10 mm of the pose error after the first contact).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_benchmark import TORQUE_LIMITS  # noqa: E402
from run_grasp_impact_benchmark import PickLiftCarryReference  # noqa: E402
from vmc_compliance_baseline import (  # noqa: E402
    SpringCarriageConfig,
    SpringCarriageVMC,
    load_controller,
)
from vmc_torque_baseline import VMCTorqueBaseline  # noqa: E402
from wbc_velocity_residual_env import (  # noqa: E402
    PandaWBCVelocityResidualEnv,
    VelocityResidualFixture,
    default_velocity_residual_fixtures,
)

RL_DT = 0.04
RECOVERY_THRESHOLD_M = 0.010
SEED = 20260819


def robot_geom_ids(model) -> set[int]:
    """All geoms belonging to the arm/hand (names carry the robot prefixes)."""

    import mujoco

    ids = set()
    for gid in range(model.ngeom):
        name = mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, gid)
        if name and (name.startswith("fr3_") or name.startswith("hand")):
            ids.add(gid)
    return ids


def contact_peak_force(env, obstacle_geoms: set[int], robot_geoms: set[int]) -> float:
    """Peak normal contact force between obstacle and robot geoms this step."""

    import mujoco

    peak = 0.0
    for cid in range(int(env.data.ncon)):
        contact = env.data.contact[cid]
        pair = {int(contact.geom1), int(contact.geom2)}
        if pair & obstacle_geoms and pair & robot_geobs_cache:
            wrench = np.zeros(6)
            mujoco.mj_contactForce(env.model, env.data, cid, wrench)
            peak = max(peak, float(np.linalg.norm(wrench[:3])))
    return peak


def run_rollout(
    menagerie: Path,
    fixture: VelocityResidualFixture,
    *,
    impactor_kind: str,
    controller,
    lift_board: bool = False,
    residual_scale: float = 0.03,
    verbose_name: str = "",
) -> dict:
    kwargs = dict(
        menagerie=menagerie, fan_ye_model_npz=None, fan_ye_train_summary_json=None,
        observation_mode="direct_esn", rod_enabled=True, seed=SEED, robot="fr3",
        execution_mode="torque_residual", residual_torque_scale=residual_scale,
        wbc_backend="paper_mpc", fixtures=(fixture,),
    )
    if lift_board:
        kwargs["lift_board_tilt_deg"] = 30.0
    env = PandaWBCVelocityResidualEnv(**kwargs)
    import mujoco

    global robot_geobs_cache
    robot_geobs_cache = robot_geom_ids(env.model)
    obstacle_geoms = {env._rod_geom_id}
    if lift_board:
        board_id = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_GEOM, "lift_board")
        if board_id >= 0:
            obstacle_geoms.add(board_id)
    env.reset(seed=SEED, options={"fixture_index": 0})
    if controller is not None and hasattr(controller, "reset"):
        controller.reset()

    log = []
    done = False
    info: dict = {}
    step = 0
    board_peak = 0.0
    impact_t = None
    while not done:
        d = env.diagnostics()
        t = step * RL_DT
        pos_err = float(np.linalg.norm(d["wbc_pose_error"][:3]))
        step_force = contact_peak_force(env, obstacle_geoms, robot_geobs_cache)
        board_peak = max(board_peak, step_force)
        if impact_t is None and step_force > 1.0:
            impact_t = t
        log.append((t, pos_err))
        if controller is None:
            action = np.zeros(7)
        else:
            if hasattr(controller, "baseline") and hasattr(controller, "residual_torque_limits"):
                act = controller.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    hand_jacobian=d.get("hand_jacobian"),
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            else:
                act = controller.act(
                    d["joint_position"], d["joint_velocity"], d["nominal_twist"],
                    pose_error=d["wbc_pose_error"], twist_error=d["wbc_twist_error"])
            action = act.bounded_filter_action
        _, _, done, _, info = env.step(action)
        step += 1

    grasp_idx = min(range(len(log)), key=lambda i: abs(log[i][0] - fixture.grasp_time_s))
    at_grasp = log[grasp_idx][1]
    recovery_s = None
    if impact_t is not None:
        peak_err = max(e for tt, e in log if tt >= impact_t)
        for tt, e in log:
            if tt > impact_t and e < RECOVERY_THRESHOLD_M:
                recovery_s = tt - impact_t
                break
    result = dict(
        name=verbose_name,
        scenario=impactor_kind,
        task_success=bool(info.get("task_success", False)),
        peak_torque_nm=float(info.get("peak_torque_nm", np.nan)),
        obstacle_force_n=float(board_peak if impactor_kind == "board"
                               else info.get("peak_contact_force_n", np.nan)),
        impact_time_s=impact_t,
        recovery_s=recovery_s,
        at_grasp_err_mm=at_grasp * 1000.0,
        peak_postimpact_err_mm=(peak_err * 1000.0) if impact_t is not None else None,
        hard_limit=bool(info.get("hard_torque_limit", False)),
    )
    env.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--esn", type=Path, default=None)
    parser.add_argument("--mlp", type=Path, default=None)
    parser.add_argument("--vmc-config", type=Path, default=None,
                        help="saved stable VMC npz (base config for the sweep)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--phase", type=str, default="all",
                        choices=("baseline", "students", "vmc", "all"))
    args = parser.parse_args()

    base_fixtures = default_velocity_residual_fixtures()
    scenarios = {}
    for i, fx in enumerate(base_fixtures):
        scenarios[f"rod_fx{i}"] = ("rod", fx, False)
        scenarios[f"ball_fx{i}"] = ("ball", replace(fx, impactor_type="ball"), False)
    for i in (0, 2):
        fx = base_fixtures[i]
        scenarios[f"board_fx{i}"] = (
            "board", replace(fx, rod_start_time_s=99.0), True)

    results = []
    t0 = time.time()
    if args.phase in ("baseline", "all"):
        for name, (kind, fx, lift) in scenarios.items():
            r = run_rollout(args.menagerie, fx, impactor_kind=kind, controller=None,
                            lift_board=lift, verbose_name=f"none/{name}")
            results.append(r)
            print(f"[{time.time()-t0:6.1f}s] {r['name']}: success={r['task_success']} "
                  f"peakT={r['peak_torque_nm']:.1f} force={r['obstacle_force_n']:.1f} "
                  f"rec={r['recovery_s']}", flush=True)
        args.out.write_text(json.dumps(results, indent=1))
        print("baseline phase done", flush=True)

    if args.phase in ("students", "all"):
        for tag, path in (("esn", args.esn), ("mlp", args.mlp)):
            if path is None:
                continue
            controller = load_controller(path)
            for name, (kind, fx, lift) in scenarios.items():
                r = run_rollout(args.menagerie, fx, impactor_kind=kind,
                                controller=controller, lift_board=lift,
                                verbose_name=f"{tag}/{name}")
                results.append(r)
                print(f"[{time.time()-t0:6.1f}s] {r['name']}: success={r['task_success']} "
                      f"peakT={r['peak_torque_nm']:.1f} force={r['obstacle_force_n']:.1f} "
                      f"rec={r['recovery_s']}", flush=True)
        args.out.write_text(json.dumps(results, indent=1))
        print("students phase done", flush=True)

    if args.phase in ("vmc", "all"):
        if args.vmc_config is not None:
            base_vmc = VMCTorqueBaseline.from_npz(args.vmc_config)
            base_cfg = base_vmc.config
        else:
            base_cfg = SpringCarriageConfig(
                k_translation_base=2.2, k_rotation_base=0.18)
        sweep_k = (1.5, 2.2, 3.2, 4.6)
        sweep_budget = (0.02, 0.03, 0.05)
        # Stage 1: sweep on one mid-severity fixture per scenario.
        probe = {"rod": "rod_fx2", "ball": "ball_fx2", "board": "board_fx2"}
        best: dict[str, tuple[float, dict]] = {}
        for kind, probe_name in probe.items():
            fx_kind, fx, lift = scenarios[probe_name]
            for k in sweep_k:
                for budget in sweep_budget:
                    cfg = replace(base_cfg, k_translation_base=k,
                                  k_rotation_base=base_cfg.k_rotation_base * k / base_cfg.k_translation_base)
                    ctrl = VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget)
                    r = run_rollout(args.menagerie, fx, impactor_kind=kind,
                                    controller=ctrl, lift_board=lift,
                                    residual_scale=budget,
                                    verbose_name=f"vmc_k{k}_s{budget}/{probe_name}")
                    results.append(r)
                    score = (1 if r["task_success"] else 0, -(r["at_grasp_err_mm"] or 999))
                    key = f"k{k}_s{budget}"
                    if kind not in best or score > best[kind][0]:
                        best[kind] = (score, dict(k=k, budget=budget))
                    print(f"[{time.time()-t0:6.1f}s] {r['name']}: success={r['task_success']} "
                          f"atGrasp={r['at_grasp_err_mm']:.1f}mm force={r['obstacle_force_n']:.1f} "
                          f"rec={r['recovery_s']}", flush=True)
        # Stage 2: best config per scenario across all its fixtures.
        for name, (kind, fx, lift) in scenarios.items():
            if kind not in best:
                continue
            k, budget = best[kind][1]["k"], best[kind][1]["budget"]
            cfg = replace(base_cfg, k_translation_base=k,
                          k_rotation_base=base_cfg.k_rotation_base * k / base_cfg.k_translation_base)
            ctrl = VMCTorqueBaseline(cfg, TORQUE_LIMITS * budget)
            if f"vmc_best/{name}" not in {r["name"] for r in results}:
                r = run_rollout(args.menagerie, fx, impactor_kind=kind,
                                controller=ctrl, lift_board=lift,
                                residual_scale=budget, verbose_name=f"vmc_best/{name}")
                results.append(r)
                print(f"[{time.time()-t0:6.1f}s] {r['name']}: success={r['task_success']} "
                      f"peakT={r['peak_torque_nm']:.1f} force={r['obstacle_force_n']:.1f} "
                      f"rec={r['recovery_s']}", flush=True)
        best_dump = {k: v[1] for k, v in best.items()}
        (args.out.parent / "vmc_best_configs.json").write_text(json.dumps(best_dump, indent=1))
        args.out.write_text(json.dumps(results, indent=1))
        print("vmc phase done; best:", best_dump, flush=True)


robot_geobs_cache: set[int] = set()


if __name__ == "__main__":
    main()
