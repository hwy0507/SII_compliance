"""Report the closed occupancy/control pair without rerunning simulation.

The occupancy arm uses a different training reward, so its total return is
never ranked against the control return.  The report compares native physical
metrics and also separates the added occupancy cost from the unchanged base
reward.  It is evidence for stage selection only; it is not final acceptance.
"""
from datetime import datetime, timezone
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

BENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BENCH / "tools"))
from report_goal_tracking_pair_20261016 import report
from screen_goal_rl_convergence_20261016 import collect


def digest(path):
    return hashlib.file_digest(Path(path).open("rb"), "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def closed(run):
    state = read(Path(run) / "execution.json")
    assert state["status"] == "complete" and state["steps"] == 44000
    rows = state["rows"]
    assert len(rows) == 32 and all(r.get("ended_utc") for r in rows)
    assert all(r["step_after"] - r["step_before"] == r["steps"] for r in rows)
    return state, rows


def reward_breakdown(run, rows):
    log = {}
    for line in (Path(run) / "training.jsonl").read_text().splitlines():
        entry = json.loads(line)
        log.setdefault(entry["episode"], []).append(entry)
    assert [int(e["step"]) for values in log.values() for e in values] == list(range(1, 44001))
    result = []
    for row in rows:
        entries = log[row["episode"]]
        terms = [entry["terms"] for entry in entries]
        assert len(terms) == row["steps"]
        for term in terms:
            assert all(math.isfinite(float(v)) for v in term.values()
                       if isinstance(v, (int, float)))
        added = sum(t.get("payload_occupancy", 0.0)
                    + t.get("payload_occupancy_failure_continuation", 0.0)
                    for t in terms)
        final = sum(t["final_reward"] for t in terms)
        # ``reward`` is the reducer output before the shared physical-slew
        # deduction; include that unchanged deduction in the counterfactual
        # base so only the occupancy treatment is removed.
        base = sum(t["reward"] + t.get("physical_slew", 0.0)
                   + t.get("physical_slew_failure_continuation", 0.0)
                   for t in terms)
        assert abs(final - row["return_value"]) < 1e-9
        assert abs(final - base - added) < 2e-8
        result.append(dict(episode=row["episode"], condition_id=row["condition_id"],
                           return_value=row["return_value"], base_return=base,
                           occupancy_added_return=added, final_return=final))
    return result


def parameter_summary(run, rows):
    summaries = []
    for row in rows:
        trace = read(Path(row["run"]) / "parameter_trace.json")
        raw = [r["raw_action"] for r in trace]
        applied = [r["applied_parameters"] for r in trace]
        scales = [r["energy_scale"] for r in trace]
        assert len(raw) == len(applied) == len(scales) == row["steps"]
        summaries.append(dict(episode=row["episode"],
                              raw_action_std=[statistics.pstdev(x) for x in zip(*raw)],
                              applied_parameter_std=[statistics.pstdev(x) for x in zip(*applied)],
                              energy_scale_min=min(scales), energy_scale_max=max(scales)))
    return summaries


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    out = args.output.resolve()
    assert not out.exists()
    reg = read(root / "REGISTRATION.json")
    assert reg["experiment_kind"] == "fresh_parameter_occupancy_pilot"
    control_state, control_rows = closed(root / "impedance_control")
    occupancy_state, occupancy_rows = closed(root / "impedance_occupancy")
    assert [r["condition_id"] for r in control_rows] == [r["condition_id"] for r in occupancy_rows]
    for row in control_rows + occupancy_rows:
        audit = read(Path(row["run"]) / "AUDIT.json")
        assert digest(Path(row["run"]) / "AUDIT.json") == row["audit_sha256"]
        assert digest(Path(row["run"]) / "rollout.npz") == row["trace_sha256"]
        assert audit["task_success"] is False and audit["strict_success"] is False
        receipt = root / ("impedance_control" if row in control_rows else "impedance_occupancy") \
            / "storage_receipts" / Path(row["run"]).name / "VERIFIED.json"
        assert receipt.exists()
    pair = report(root)
    screen = collect(root)
    control_rewards = [r["return_value"] for r in control_rows]
    occupancy_rewards = reward_breakdown(root / "impedance_occupancy", occupancy_rows)
    base_rewards = [r["base_return"] for r in occupancy_rewards]
    added_rewards = [r["occupancy_added_return"] for r in occupancy_rewards]
    paired_base_delta = [b - c for b, c in zip(base_rewards, control_rewards)]
    result = dict(
        observed_utc=datetime.now(timezone.utc).isoformat(),
        root=str(root), registration_sha256=digest(root / "REGISTRATION.json"),
        control_execution_sha256=digest(root / "impedance_control" / "execution.json"),
        occupancy_execution_sha256=digest(root / "impedance_occupancy" / "execution.json"),
        control_steps=control_state["steps"], occupancy_steps=occupancy_state["steps"],
        control_updates=control_state["updates"], occupancy_updates=occupancy_state["updates"],
        control_summary=dict(episodes=32, task=0, strict=0, joint=0,
                             mean_return=statistics.fmean(control_rewards),
                             return_std=statistics.pstdev(control_rewards)),
        occupancy_summary=dict(episodes=32, task=0, strict=0, joint=0,
                               mean_return=statistics.fmean([r["return_value"] for r in occupancy_rows]),
                               return_std=statistics.pstdev([r["return_value"] for r in occupancy_rows]),
                               mean_base_return=statistics.fmean(base_rewards),
                               mean_added_occupancy_return=statistics.fmean(added_rewards),
                               mean_paired_base_delta=statistics.fmean(paired_base_delta)),
        paired_native_metrics=pair["comparison"]["by_phase"],
        parameter_summary=parameter_summary(root / "impedance_occupancy", occupancy_rows),
        training_screen=screen,
        simulation=False, gradient_updates=0, independent_physical_replay=False,
        acceptance=False, convergence=False,
        limitation="The two arms share identities and exposure but use different training rewards; total returns are not ranked. Native physical metrics and unchanged base reward are descriptive. All 64 failed episodes remain retained; this pilot does not satisfy the four-family convergence screen or final acceptance.")
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"control": result["control_summary"],
                      "occupancy": result["occupancy_summary"],
                      "learned_native": result["paired_native_metrics"]["learned"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
