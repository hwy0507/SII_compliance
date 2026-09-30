"""Targeted, compute-efficient recovery search for the held table corner.

The broad unified search established that every failure is the same stage-4
stall.  This script reuses those completed anchor traces, searches only the
identified force-to-tangential-slide subspace, and advances only strict anchor
successes to the four held-out physical fixtures.  It never changes the task,
success gate, observation contract, or controller family.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import numpy as np


os.environ.setdefault("UNIFIED_6D_CAMPAIGN", "unified_6d_table_targeted_20260921")
os.environ.setdefault("UNIFIED_6D_WORKERS", "16")
os.environ.setdefault("UNIFIED_6D_SCENES", "table_corner")

import search_unified_6d_teacher_20260921 as search


SOURCE = search.ROOT / "outputs" / "unified_6d_table_recovery_search_20260921" / "state.json"
COUNT = int(os.environ.get("TABLE_TARGETED_COUNT", "32"))
SURVIVORS = int(os.environ.get("TABLE_TARGETED_SURVIVORS", "6"))
SEED = 20260921 + 917


def latin_hypercube(count: int, dimensions: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    values = np.empty((count, dimensions), dtype=float)
    for column in range(dimensions):
        values[:, column] = (rng.permutation(count) + rng.random(count)) / count
    return values


def log_lerp(lo: float, hi: float, u: float) -> float:
    return float(np.exp(np.log(lo) + float(u) * np.log(hi / lo)))


def candidates() -> list[tuple[str, dict]]:
    state = json.loads(SOURCE.read_text())
    source_rows = [
        row for row in state["rows"]
        if row.get("scene") == "table_corner"
        and row.get("fixture") == "t_anchor"
        and not row.get("error")
        and row.get("physical_valid")
    ]
    # Endpoint accuracy is the relevant continuous diagnostic because every
    # source row reached exactly the same stage and none passed the hard gate.
    parents = sorted(
        source_rows,
        key=lambda row: (row.get("final_stage", 0) != 4,
                         row.get("endpoint_error_m", 9.0),
                         -row.get("progress", -999.0)),
    )[:6]
    if not parents:
        raise RuntimeError("No physically valid recovery-search parents")

    lhs = latin_hypercube(COUNT, 12, SEED)
    output: list[tuple[str, dict]] = []
    for index, u in enumerate(lhs):
        parent = copy.deepcopy(parents[index % len(parents)]["config"])
        k = np.asarray(parent["stiffness_6d"], dtype=float)
        b = np.asarray(parent["damping_6d"], dtype=float)
        mass = np.asarray(parent["mass_6d"], dtype=float)

        # Strong translational anisotropy is intentional: with a positive
        # virtual-frame pitch, an apron-normal load produces a tangential
        # component that can lift/slide link 6/7 around the rigid edge.
        k[0] = log_lerp(20.0, 110.0, u[0])
        k[2] = log_lerp(700.0, 2200.0, u[1])
        k[1] *= log_lerp(0.65, 1.45, u[2])
        k[3:] *= log_lerp(0.65, 1.55, u[3])
        parent["stiffness_6d"] = k.tolist()

        # Preserve damping near the broad-search stable region while allowing
        # faster recovery after the edge is cleared.
        b[0] = log_lerp(24.0, 58.0, u[4])
        b[2] = log_lerp(38.0, 92.0, u[5])
        parent["damping_6d"] = b.tolist()
        mass[0] = log_lerp(0.38, 0.72, u[6])
        mass[2] = log_lerp(0.62, 1.08, u[7])
        parent["mass_6d"] = mass.tolist()

        deadband = np.asarray(parent["deadband_6d"], dtype=float)
        deadband[0] = log_lerp(0.22, 0.85, u[8])
        deadband[2] = log_lerp(0.75, 1.65, u[9])
        parent["deadband_6d"] = deadband.tolist()

        pitch = 0.38 + 0.64 * float(u[10])
        roll = -0.24 + 0.48 * float(u[11])
        # Cycle yaw independently so wrist/link orientation is explored
        # without spending another random dimension.
        yaw = (-0.35, -0.12, 0.12, 0.35)[index % 4]
        parent["axis_rotation_rpy"] = [roll, pitch, yaw]
        parent["offset_tracking_gain_6d"] = (0.85, 1.15, 1.55, 2.10)[(index // 4) % 4]
        parent["filter_tau"] = (0.010, 0.018, 0.030, 0.048)[(index // 16) % 4]
        parent["velocity_limit_6d"] = [.10, .10, .16, .50, .50, .60]
        parent["action_limit_6d"] = [(.14, .18, .22, .26)[index % 4], .20,
                                     (.24, .30, .36, .42)[(index // 4) % 4],
                                     .70, .70, .70]
        output.append((f"targeted_{index:02d}", parent))
    return output


def main() -> None:
    search.OUT.mkdir(parents=True, exist_ok=True)
    fixture = search.FIXTURES["table_corner"][0]
    configs = {"table_corner": candidates()}
    rows: list[dict] = []
    protocol = {
        "version": "table_corner_targeted_6d_20260921",
        "source_state": str(SOURCE),
        "workers": search.WORKERS,
        "count": COUNT,
        "strict_task_and_physics_gate_unchanged": True,
        "search_subspace": [
            "positive virtual-frame pitch",
            "Kx/Kz anisotropy",
            "x/z damping and mass",
            "x/z wrench deadband",
            "x/z action limit",
            "offset tracking gain",
            "roll/yaw wrist clearance",
        ],
        "observation": "48D proprioception including complete 6D wrench",
        "action": "7D VMC action",
        "fixtures": search.FIXTURES,
    }
    (search.OUT / "protocol.json").write_text(json.dumps(protocol, indent=2))
    search.execute(
        [("table_corner", fixture, name, cfg) for name, cfg in configs["table_corner"]],
        rows, configs, "targeted_anchor",
    )

    feasible = sorted(
        [row for row in rows if row.get("accepted")],
        key=lambda row: row["score"],
    )[:SURVIVORS]
    fixture_jobs = [
        ("table_corner", held_out, row["candidate"], row["config"])
        for row in feasible
        for held_out in search.FIXTURES["table_corner"][1:]
    ]
    search.execute(fixture_jobs, rows, configs, "targeted_fixture_evaluation")

    accepted = [row for row in rows if row.get("accepted")]
    summary = {
        "complete": True,
        "rows": len(rows),
        "accepted": len(accepted),
        "anchor_accepted": len(feasible),
        "physical_fixtures": len({row["fixture_hash"] for row in accepted}),
        "parameter_groups": len({row["config_hash"] for row in accepted}),
        "selected_anchor_candidates": [row["candidate"] for row in feasible],
        "pareto": [
            {key: row[key] for key in (
                "fixture", "candidate", "config_hash", "score",
                "trajectory_rmse_after_contact_m", "endpoint_error_m",
                "peak_force_n", "peak_torque_nm", "speed_p95_mps",
                "max_penetration_m", "trace", "result",
            )}
            for row in search.pareto(accepted)
        ] if accepted else [],
        "contract": "proprio48_action7_6d_v1",
        "student_training_started": False,
        "office_data_used": False,
    }
    (search.OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    search.save_state(rows, configs, "complete")
    (search.OUT / "COMPLETE.json").write_text(json.dumps({"complete": True}, indent=2))
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
