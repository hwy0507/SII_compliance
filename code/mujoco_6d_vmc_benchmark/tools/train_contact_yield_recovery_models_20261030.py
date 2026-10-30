"""Fair ESN/RNN/MLP retraining on the new three-scene VMC dataset."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


SEEDS = [2026102801, 2026102802, 2026102803]
RATES = [1e-4, 3e-4, 1e-3, 3e-3]
DECAYS = [0.0, 1e-5, 1e-4]
UPDATES = 32000


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path):
    return json.loads(path.read_text())


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def freeze_fitting_source(root: Path) -> dict:
    """Bind all candidates to one isolated source tree before the first fit."""
    benchmark = Path(__file__).resolve().parents[1]
    destination = root / 'fitting_source'
    receipt = root / 'FITTING_SOURCE.json'
    if not receipt.exists():
        if destination.exists():
            raise FileExistsError('Incomplete fitting snapshot; inspect before recovery')
        sources = list((benchmark / 'scripts').glob('*.py')) + [
            benchmark / 'tools' / name for name in (
            'train_contact_yield_recovery_models_20261030.py',
            'train_contact_yield_recovery_neural_20261030.py',
                'train_paper_context_esn_20261003.py',
                'train_office_mlp_rnn_20261002.py',
                'optimize_tool_contact_20261002.py')]
        hashes = {str(p.relative_to(benchmark)): sha(p) for p in sources}
        for source in sources:
            target = destination / source.relative_to(benchmark)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        manifest = dict(schema='sii-special-frozen-fitting-source-v1',
                        created_utc=now(), source_hashes=hashes,
                        base_commit=subprocess.check_output(
                            ['git', 'rev-parse', 'HEAD'], cwd=benchmark, text=True).strip(),
                        note='Content hashes identify executed bytes; base commit does not imply a clean worktree.')
        write(receipt, manifest)
    manifest = read(receipt)
    for name, digest in manifest['source_hashes'].items():
        if sha(destination / name) != digest:
            raise ValueError(f'Fitting snapshot changed: {name}')
    if sha(Path(__file__)) != manifest['source_hashes']['tools/train_contact_yield_recovery_models_20261030.py']:
        raise ValueError('Coordinator differs from registered fitting source')
    return manifest


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--run", action="store_true")
    args = p.parse_args()
    root = args.root.resolve()
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    if memory == 'max' or int(memory)>3*1024**3 or (cg/'memory.swap.max').read_text().strip()!='0':
        raise RuntimeError('Actual cgroup MemoryMax<=3GiB and swap=0 required')
    compute_lock=(Path(__file__).resolve().parents[1]/'outputs/.local-rl-compute.lock').open('a')
    fcntl.flock(compute_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if not args.run:
        raise SystemExit("use --run")
    if not root.exists() or not (root / "data" / "DATA_COMPLETE.json").exists():
        raise FileNotFoundError(root)
    state_path = root / "execution.json"
    state = read(state_path) if state_path.exists() else {"status": "prepared", "fits": []}
    if state.get("status") not in ("prepared", "dataset_complete", "training", "failed_preserved"):
        raise RuntimeError(f"refusing to resume state {state.get('status')}")
    data = root / "data" / "training_data.npz"
    state.setdefault("fits", [])
    metadata = root / "data" / "DATA_COMPLETE.json"
    expected = read(metadata)["training_data_sha256"]
    dataset_meta=read(metadata)
    schema=dataset_meta.get('schema')
    if dataset_meta.get('qualified_episodes')!=30:
        raise RuntimeError('Require 30 qualified real-special-scene identities')
    if schema=='sii-vmc-special-scenes-recovery-augmented-v1' and dataset_meta.get('augmentation_round') in (None, 2):
        expected_population=(36, 30, 6, 30, 19500, 1480, 18020)
    elif schema=='sii-vmc-special-scenes-recovery-augmented-v3' and dataset_meta.get('augmentation_round')==3:
        expected_population=(38, 32, 6, 32, 20500, 1707, 18793)
    else:
        raise RuntimeError(f'Unsupported recovery dataset schema/round: {schema}/{dataset_meta.get("augmentation_round")}')
    episodes, train_episodes, validation_episodes, expected_train_ids, frames, zero_weight, positive_weight=expected_population
    if (dataset_meta.get('episodes'), len([r for r in dataset_meta['lineage'] if r['split']=='train']),
            len([r for r in dataset_meta['lineage'] if r['split']=='validation']),
            dataset_meta.get('frames'), dataset_meta.get('zero_weight_warmup_frames')) != (
            episodes, train_episodes, validation_episodes, frames, zero_weight):
        raise RuntimeError('Dataset metadata population/lineage mismatch')
    with np.load(data, allow_pickle=False) as z:
        episode, train, importance = z['episode'].copy(), z['train'].copy(), z['importance'].copy()
        if not z['physical_execution'].all():
            raise RuntimeError('Nonphysical demonstration row in training data')
    if (len(episode)!=frames or len(np.unique(episode[train]))!=expected_train_ids
            or len(np.unique(episode[~train]))!=validation_episodes
            or int((importance==0).sum())!=zero_weight
            or int((importance>0).sum())!=positive_weight
            or int((importance<0).sum())!=0):
        raise RuntimeError('Dataset arrays disagree with registered population/weights')
    if sha(data) != expected:
        raise RuntimeError("dataset hash mismatch")
    registration = read(root / 'REGISTRATION.json')
    if (registration['seeds'] != SEEDS or registration['candidates_per_family_seed'] != 12
            or registration['neural_updates'] != UPDATES
            or registration['neural_grid'] != dict(learning_rate=RATES, weight_decay=DECAYS)
            or registration['esn_grid'] != dict(rho=[.5,.8], input_gain=[.08,.25,.6], ridge=[.001,.1])):
        raise ValueError('Training budget differs from dataset registration')
    if state['fits'] and not (root / 'FITTING_SOURCE.json').exists():
        raise ValueError('Cannot introduce a new snapshot into an existing unfrozen fit')
    fitting_source = freeze_fitting_source(root)
    frozen = root / 'fitting_source'
    tools = frozen / 'tools'
    provenance = {name: sha(root / name) for name in (
        'data/training_data.npz', 'data/DATA_COMPLETE.json', 'REGISTRATION.json', 'FITTING_SOURCE.json')}
    if state.get('fitting_input_hashes', provenance) != provenance:
        raise ValueError('Fitting inputs changed after launch')
    # The frozen fitting environment contains torch; the MuJoCo collection
    # environment intentionally does not. Both inherit the real cgroup limits.
    python = str(Path(__file__).resolve().parents[4] / ".venv-rl" / "bin" / "python")
    if not Path(python).exists():
        raise FileNotFoundError(python)
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               SII_MEMORY_MAX_BYTES=str(3 * 1024**3),
               PYTHONPATH=str(frozen / 'scripts') + ':' + str(tools),
               SII_SOURCE_BASE_COMMIT=fitting_source['base_commit'])
    data_args = ["--data", str(data), "--metadata", str(metadata)]
    jobs = []
    for seed in SEEDS:
        jobs.append((f"esn_ridge_s{seed}", "esn_ridge", seed,
                     [python, str(tools / "train_paper_context_esn_20261003.py"), *data_args,
                      "--seed", str(seed), "--state-context-readout"]))
    for rate, decay in itertools.product(RATES, DECAYS):
        candidate = list(itertools.product(RATES, DECAYS)).index((rate, decay))
        for seed in SEEDS:
            for family, kind in (("rnn_scratch", "rnn"), ("mlp_scratch", "mlp")):
                name = f"{family}_s{seed}_candidate{candidate:02d}"
                jobs.append((name, family, seed,
                             [python, str(tools / "train_contact_yield_recovery_neural_20261030.py"), *data_args,
                              "--kind", kind, "--seed", str(seed), "--target", "requested",
                              "--absolute-inputs", "--precision", "float64", "--updates", str(UPDATES),
                              "--learning-rate", str(rate), "--weight-decay", str(decay),
                              "--action-delta-weight", "0", "--lr-schedule", "cosine",
                              "--global-loss", "--raw-slowdown-loss", "--selection", "final"]))
    state.update(status="training", started_utc=state.get("started_utc", now()), host=os.uname().nodename,
                 data_sha256=expected, expected_jobs=len(jobs), fitting_input_hashes=provenance)
    write(state_path, state)
    completed = {x["name"] for x in state.get("fits", []) if x.get("status") == "complete"}
    try:
        for name, family, seed, command in jobs:
            freeze_fitting_source(root)
            if any(sha(root / name) != digest for name, digest in provenance.items()):
                raise ValueError('Fitting input changed at candidate boundary')
            if name in completed:
                row = next(r for r in state['fits'] if r['name'] == name and r['status'] == 'complete')
                if (sha(Path(row['output']) / 'checkpoint.npz') != row['checkpoint_sha256']
                        or sha(Path(row['output']) / 'TRAINING_COMPLETE.json') != row['metadata_sha256']):
                    raise ValueError(f'Completed fit changed: {name}')
                continue
            if (root/'STOP_REQUESTED').exists():
                state.update(status='stopped_at_candidate_boundary',ended_utc=now())
                write(state_path,state)
                return
            out = root / "learning" / name
            log = root / "logs" / f"{name}.log"
            out.parent.mkdir(parents=True, exist_ok=True); log.parent.mkdir(parents=True, exist_ok=True)
            row = {"name": name, "family": family, "seed": seed, "output": str(out), "status": "running", "started_utc": now(),
                   "command": command + ["--output", str(out)]}
            state["current"] = name; state["fits"].append(row); write(state_path, state)
            start = time.monotonic()
            if out.exists():
                raise FileExistsError(f'Preserve incomplete fit; explicit recovery required: {out}')
            with log.open("x") as stream:
                result = subprocess.run(command + ["--output", str(out)], stdout=stream, stderr=subprocess.STDOUT, env=env,pass_fds=(compute_lock.fileno(),))
            if result.returncode != 0:
                row.update(status="failed_preserved", returncode=result.returncode, ended_utc=now())
                write(state_path, state)
                raise RuntimeError(f"trainer failed: {name}; log={log}")
            complete = out / "TRAINING_COMPLETE.json"
            if not complete.exists():
                raise RuntimeError(f"missing training metadata: {name}")
            meta = read(complete)
            if meta.get("training_data_sha256",meta.get("data_sha256")) != expected:
                raise RuntimeError(f"trainer lineage mismatch: {name}")
            freeze_fitting_source(root)
            if any(sha(root / item) != digest for item, digest in provenance.items()):
                raise ValueError('Fitting input changed during candidate')
            for item, digest in meta['source_sha256'].items():
                if fitting_source['source_hashes'].get(item) != digest:
                    raise ValueError(f'Candidate used unregistered source: {item}')
            row.update(status="complete", ended_utc=now(), wall_seconds=time.monotonic() - start,
                       metadata_sha256=sha(complete), checkpoint_sha256=sha(out / "checkpoint.npz"))
            write(state_path, state)
        # Model selection is validation-only and occurs after every candidate
        # has finished.  ESN internally screens its registered 12 fixed grids.
        selected = []
        for seed in SEEDS:
            for family in ("esn_ridge", "rnn_scratch", "mlp_scratch"):
                fits = [r for r in state["fits"] if r["seed"] == seed and r["family"] == family and r["status"] == "complete"]
                if family == "esn_ridge":
                    if len(fits) != 1: raise RuntimeError(f"incomplete ESN fits for seed {seed}")
                elif len(fits) != len(RATES) * len(DECAYS):
                    raise RuntimeError(f"incomplete neural grid: {family} seed {seed}")
                scored = []
                for fit in fits:
                    meta = read(Path(fit["output"]) / "TRAINING_COMPLETE.json")
                    score = (meta["selected"]["holdout_mse"] if family == "esn_ridge"
                             else meta["groups"]["real_identity_validation"]["action_mse"])
                    scored.append((float(score), fit["name"], fit, meta))
                score, name, fit, meta = min(scored, key=lambda x: (x[0], x[1]))
                cp = Path(fit["output"]) / "checkpoint.npz"
                selected.append({"name": f"special_{family}_s{seed}", "family": family, "seed": seed,
                                 "validation_mse": score, "selected_trial": name,
                                 "checkpoint": str(cp), "checkpoint_sha256": sha(cp),
                                 "metadata": str(Path(fit["output"]) / "TRAINING_COMPLETE.json"),
                                 "metadata_sha256": sha(Path(fit["output"]) / "TRAINING_COMPLETE.json"),
                                 "trainable_parameters": int(meta.get("trainable_parameters", meta.get("trainable_readout_coefficients", 0))),
                                 "worker_kind": "office", "config": {}})
        lock = {"schema": "sii-nonrl-special-scene-model-lock-v1", "status": "frozen",
                "created_utc": now(), "training_data_sha256": expected,
                "selection": "minimum requested-action MSE on the same six registered validation identities (two per scene); no office test selection",
                "budget": {"candidates_per_family_seed":12,"neural_updates_per_candidate":UPDATES,
                           "note":"Equal candidate count, not equal FLOPs/parameter count; finite neural budget is not a convergence claim"},
                "models": selected}
        write(root / "MODEL_LOCK.json", lock)
        state.update(status="complete", ended_utc=now(), model_lock_sha256=sha(root / "MODEL_LOCK.json"), selected=selected)
        write(state_path, state)
        print(json.dumps({"status": "complete", "root": str(root), "models": selected}, indent=2))
    except BaseException as exc:
        state.update(status="failed_preserved", error=repr(exc), ended_utc=now())
        write(state_path, state)
        raise


if __name__ == "__main__":
    main()
