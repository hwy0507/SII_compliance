"""Account for actual executed training, including discarded recovery tails."""
import argparse, datetime, hashlib, json
from pathlib import Path
ROOT = Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")

def segment(path):
    log = path / "episodes.jsonl"
    rows = [json.loads(line) for line in log.read_text().splitlines() if line.strip()]
    receipt = path / "COMPLETE.json"
    return dict(path=str(path), episode_log_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
        completed_episodes=len(rows),
        physical_action_intervals=sum(row["episode_steps"] for row in rows),
        simulated_seconds=sum(row["duration_s"] for row in rows),
        scene_counts={name: sum(row["scene"] == name for row in rows)
                      for name in ["ball", "push", "corner", "table_corner"]},
        first_counter=rows[0]["step"], last_counter=rows[-1]["step"],
        completion=json.loads(receipt.read_text()) if receipt.exists() else None,
        failure_files=[str(p) for p in sorted(path.rglob("ERROR.txt"))])

def build(output):
    entries = []
    for reward in ["metric", "office_task"]:
        for seed in [74001, 74002]:
            paths = ([ROOT / "campaign01" / f"{reward}_seed{seed}"] if seed == 74001 else [])
            paths += [ROOT / "campaign02" / f"{reward}_seed{seed}"]
            parts = [segment(path) for path in paths]
            assert parts[-1]["completion"] is not None
            exposure = sum(p["physical_action_intervals"] for p in parts)
            counter = parts[-1]["completion"]["step"]
            entries.append(dict(id=f"direct_{reward}_{seed}", seed=seed, segments=parts,
                selected_checkpoint_step=60000, final_learning_counter=counter,
                physical_action_intervals=exposure, discarded_tail_intervals=exposure-counter,
                physical_seconds=sum(p["simulated_seconds"] for p in parts),
                recovery="Agent, replay and RNG restored at 20000; live environment was restarted, not an exact simulator continuation." if seed == 74001 else None))
    lock = json.loads((ROOT / "PARAMETER_CHECKPOINT_LOCK.json").read_text())
    for controller in ["admittance", "impedance", "vmc"]:
        part = segment(ROOT / "parameter_rl/campaign01" / f"{controller}_seed75001")
        assert part["completion"] is not None
        assert part["physical_action_intervals"] == part["completion"]["step"]
        entries.append(dict(id="parameter_"+controller, seed=75001, segments=[part],
            selected_checkpoint_step=lock["selected_step"],
            final_learning_counter=part["completion"]["step"],
            physical_action_intervals=part["physical_action_intervals"], discarded_tail_intervals=0,
            physical_seconds=part["simulated_seconds"], recovery=None))
    result = dict(generated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        training_complete=True, runs=entries,
        scope="Counts completed physical interaction intervals from every retained training segment. Evaluation/reference/office rollouts are separate and never added to training.",
        caveats=["Periodic checkpoints can fall inside an episode; final physical exposure exceeds the selected checkpoint.",
            "Original negative-number CLI failures occurred before launching the next simulator; retained ERROR files are not successful episodes.",
            "Classical search has its separately registered 96 executed candidate-condition episodes; original BO prior exposure and historical ESN data are different and not equal-data training.",
            "4096 fixture definitions are sampled condition metadata, not 4096 executed trajectories."])
    output.write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps([{k:v for k,v in row.items() if k not in ["segments", "recovery"]} for row in entries]))
if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT/"PHYSICAL_EXPOSURE_FINAL.json")
    build(parser.parse_args().output)
