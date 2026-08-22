"""Offline geometry audit for the fixed pre-grasp board in the dual-phase task.

This is deliberately a *scene-calibration* utility, not a policy or a
training environment.  For each static board candidate, it runs the identical
zero-residual WBC rollout and records who touched each board.  Candidates that
start in contact, hit the target object, or only collide with an unintended
link can therefore never be mistaken for a valid pre-grasp compliance case.
"""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import mujoco
import numpy as np

from wbc_velocity_residual_env import PandaWBCVelocityResidualEnv, VelocityResidualFixture


def board_contacts(env: PandaWBCVelocityResidualEnv, board_id: int) -> list[str]:
    assert env.data is not None and env.model is not None
    partners: set[str] = set()
    for index in range(env.data.ncon):
        contact = env.data.contact[index]
        if board_id not in (int(contact.geom1), int(contact.geom2)):
            continue
        other = int(contact.geom2) if int(contact.geom1) == board_id else int(contact.geom1)
        name = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_GEOM, other)
        if name is None:
            body_id = int(env.model.geom_bodyid[other])
            body = mujoco.mj_id2name(env.model, mujoco.mjtObj.mjOBJ_BODY, body_id)
            partners.add(f"{body or 'unnamed_body'}/geom_{other}")
        else:
            partners.add(name)
    return sorted(partners)


def run_candidate(
    menagerie: Path, x: float, y: float, z: float,
    half_extents: tuple[float, float, float], seed: int,
) -> dict[str, object]:
    fixture = VelocityResidualFixture(0.170, 0.541, 99.0, grasp_time_s=2.4)
    env = PandaWBCVelocityResidualEnv(
        menagerie, None, None, "direct_esn", rod_enabled=False, robot="fr3", seed=seed,
        execution_mode="torque_residual", residual_torque_scale=0.02,
        wbc_backend="paper_mpc", fixtures=(fixture,), lift_board_tilt_deg=15.0,
        lift_board_contact_mode="dual_phase_longitudinal",
    )
    env.reset(seed=seed, options={"fixture_index": 0})
    assert env.model is not None and env.data is not None
    pre_id = env._dual_board_geom_ids["pregrasp_board"]
    # This one-time mutation occurs strictly before the first physics step and
    # is equivalent to rebuilding the same fixed world geom for every trial.
    env.model.geom_pos[pre_id] = np.array([x, y, z])
    env.model.geom_quat[pre_id] = np.array([1.0, 0.0, 0.0, 0.0])
    env.model.geom_size[pre_id] = np.asarray(half_extents)
    mujoco.mj_forward(env.model, env.data)
    initial = board_contacts(env, pre_id)
    if initial:
        return {
            "x": x, "y": y, "z": z, "half_extents_m": half_extents,
            "initial_contacts": initial, "accepted": False,
        }
    done = False
    info: dict[str, object] = {}
    while not done:
        _, _, terminated, truncated, info = env.step(np.zeros(7, dtype=np.float32))
        done = bool(terminated or truncated)
    pre = dict(info["dual_board_metrics"]["pregrasp_board"])
    post = dict(info["dual_board_metrics"]["postgrasp_board"])
    pre_partners = set(pre["contact_geom_names"])
    invalid_pre = {"target_object_geom", "table", "rod_geom"}
    pre_time = pre["first_contact_s"]
    # `target_lift_at_first_contact_m` is recorded from the free object pose;
    # this confirms the pre contact happens before an actual lift.
    accepted = bool(
        pre["contact"]
        and pre_time is not None and float(pre_time) < fixture.grasp_time_s
        and bool(pre["hand_body_contact"] or pre["link7_body_contact"])
        and not bool(pre_partners & invalid_pre)
        and float(info["final_target_lift_m"]) > 0.12
        and post["contact"]
        and post["first_contact_s"] is not None
        and float(post["first_contact_s"]) > fixture.grasp_time_s
        and float(post["target_lift_at_first_contact_m"] or 0.0) > 0.08
    )
    return {
        "x": x, "y": y, "z": z, "half_extents_m": half_extents,
        "initial_contacts": initial, "pregrasp": pre, "postgrasp": post,
        "final_target_lift_m": info["final_target_lift_m"],
        "final_hand_target_distance_m": info["final_hand_target_distance_m"],
        "task_success": info["task_success"], "accepted": accepted,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--menagerie", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--scan-profile", choices=("edge_position", "edge_size"), default="edge_position",
    )
    args = parser.parse_args()
    # Narrow horizontal shelves: broad enough to yield a repeatable face
    # contact, but short enough not to envelop the block or the whole wrist.
    if args.scan_profile == "edge_position":
        specs = [
            (x, y, z, (0.025, 0.025, 0.008))
            for x, y, z in product(
                (0.550, 0.570),
                (0.050, 0.070, 0.090, 0.110),
                (0.540, 0.560, 0.580, 0.600),
            )
        ]
    else:
        specs = [
            (0.550, 0.050, 0.540, (half_x, half_y, 0.008))
            for half_x, half_y in product((0.050, 0.080, 0.120, 0.160), (0.020, 0.025, 0.030))
        ]
    results = [
        run_candidate(args.menagerie, x, y, z, half_extents, args.seed)
        for x, y, z, half_extents in specs
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2), encoding="utf-8")
    for result in results:
        pre = result.get("pregrasp", {})
        print(json.dumps({
            "x": result["x"], "y": result["y"], "z": result["z"],
            "half_extents_m": result["half_extents_m"],
            "initial": result["initial_contacts"],
            "pre_t": pre.get("first_contact_s"), "pre_partners": pre.get("contact_geom_names"),
            "lift": result.get("final_target_lift_m"), "accepted": result["accepted"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()
