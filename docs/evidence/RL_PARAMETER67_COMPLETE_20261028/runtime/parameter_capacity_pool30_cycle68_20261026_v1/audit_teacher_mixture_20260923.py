"""Streaming, train-only teacher-mixture and history-support audit; no simulation.

Sampling is fixed before inspecting outcomes: first 12 SHA256(id)-ordered push
episodes per physical fixture. Full manifest metadata is counted separately.
Nearest-neighbour distances are descriptive, not calibrated OOD probabilities.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(path, root):
    path = Path(path)
    return path if path.is_absolute() else root / path


def sequence(actor, obs):
    actor.reset()
    features, predictions = [], []
    for o in obs:
        predictions.append(actor.act(o))
        features.append(np.r_[np.clip((o-actor.mean)/actor.std, -12, 12)*actor.input_mask, actor.state])
    features = (np.asarray(features)-actor.head['fmean'])/actor.head['fstd']
    return features, np.asarray(predictions)


def nearest(query, bank, labels, ids, k=10):
    # Bounded query chunks avoid an episode-by-bank-by-feature tensor.
    best_ids, best_dist, best_labels = [], [], []
    for q in query:
        dist = np.mean((bank-q)**2, axis=1)**.5
        ix = np.argsort(dist)[:k]
        best_ids.append([ids[int(i)] for i in ix])
        best_dist.append(dist[ix].tolist())
        best_labels.append(labels[ix, 1].tolist())
    return dict(distance_rms=np.asarray(best_dist).mean(0).tolist(),
                neighbour_x_action_mean=float(np.mean(best_labels)),
                neighbour_x_negative_fraction=float(np.mean(np.asarray(best_labels)<-.01)),
                neighbour_x_positive_fraction=float(np.mean(np.asarray(best_labels)>.01)),
                nearest_episode_ids=best_ids, nearest_x_labels=best_labels)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bank', type=Path, required=True)
    p.add_argument('--esn', type=Path, required=True)
    p.add_argument('--campaign', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    manifest = json.loads((args.bank/'manifest.json').read_text())
    rows = [r for r in manifest['train'] if r['scene']=='push']
    grouped = defaultdict(list)
    for r in rows:
        grouped[r['physical_fixture']].append(r)
    selected = [r for fixture in sorted(grouped) for r in sorted(grouped[fixture],
                key=lambda x: hashlib.sha256(x['id'].encode()).hexdigest())[:12]]
    counts = defaultdict(Counter)
    metadata_missing = []
    for row in rows:
        source = resolve(row['source_result'], ROOT)
        if not source.exists():
            metadata_missing.append(row['id']); continue
        result = json.loads(source.read_text())
        arguments = result.get('arguments', {})
        for key in ('event_stage', 'nominal_speed', 'dt'):
            counts[key][str(arguments.get(key))] += 1
        counts['fixture'][row['physical_fixture']] += 1
    actor = ESN128Proprio48Action7.load(args.esn)
    configs, reports, feature_bank, label_bank, sample_ids = [], [], [], [], []
    for row in selected:
        with np.load(resolve(row['trace'], args.bank), allow_pickle=False) as z:
            obs, labels = z['observation'], z['teacher_action']
        config = json.loads(resolve(row['source_search_result'], ROOT).read_text())['config']
        configs.append(config)
        teacher = SixDVirtualDynamics(config)
        replay = np.stack([teacher.act(o[39:45], .04) for o in obs])
        features, pred = sequence(actor, obs)
        ix = np.arange(0, len(obs), 5)
        feature_bank.append(features[ix]); label_bank.append(labels[ix])
        sample_ids.extend([row['id']]*len(ix))
        stable = obs[-25:, 39]
        reports.append(dict(id=row['id'], fixture=row['physical_fixture'],
            trace_sha256=digest(resolve(row['trace'], args.bank)),
            config=config, samples=len(obs),
            teacher_replay_max_error=float(np.max(np.abs(replay-labels))),
            esn_action_mae=np.mean(np.abs(pred-labels),axis=0).tolist(),
            tail_estimated_fx_mean=float(stable.mean()), tail_estimated_fx_std=float(stable.std()),
            tail_label_action_mean=labels[-25:].mean(0).tolist(),
            tail_esn_action_mean=pred[-25:].mean(0).tolist(),
            normalized_observation_max=float(np.max(np.abs((obs-actor.mean)/actor.std))),
            readout_feature_abs_p99=np.quantile(np.abs(features),.99,axis=0).tolist()))
    bank = np.concatenate(feature_bank); labels = np.concatenate(label_bank)
    # Cross-episode training reference, never matching the same episode to itself.
    reference = []
    ids = np.asarray(sample_ids)
    for row, features in zip(selected, feature_bank):
        mask = ids != row['id']
        reference.append(nearest(features[-5:], bank[mask], labels[mask], ids[mask], k=1)['distance_rms'][0])
    queries = {}
    for method in ('vmc','mlp','esn','esn_lowpass_025','mlp_lowpass_025'):
        path = args.campaign/method/'9301'/'rollout'/'rollout.npz'
        with np.load(path, allow_pickle=False) as z:
            obs = z['observation']
        features, pred = sequence(actor, obs)
        tail_means = []
        for config in configs:
            teacher = SixDVirtualDynamics(config)
            actions = np.stack([teacher.act(o[39:45], .04) for o in obs])
            tail_means.append(actions[-25:].mean(0))
        means = np.asarray(tail_means)
        queries[method] = dict(trace_sha256=digest(path),
            tail_esn_mean=pred[-25:].mean(0).tolist(),
            tail_wrench_mean=obs[-25:,39:45].mean(0).tolist(),
            teacher_config_tail_action_means=means.tolist(),
            teacher_config_tail_x_min_median_max=np.quantile(means[:,1],[0,.5,1]).tolist(),
            teacher_config_tail_x_positive_count=int(np.sum(means[:,1]>.01)),
            teacher_config_tail_x_negative_count=int(np.sum(means[:,1]<-.01)),
            nearest_readout_features=nearest(features[-25:],bank,labels,sample_ids),
            nearest_normalized_observations=nearest(features[-25:,:48],bank[:,:48],labels,sample_ids),
            tail_readout_feature_abs_max=float(np.max(np.abs(features[-25:]))))
    result = dict(scope='train-only deterministic subset, offline fixed visited histories; no new simulation or checkpoint selection',
        manifest_sha256=digest(args.bank/'manifest.json'), checkpoint_sha256=digest(args.esn),
        sample_rule='12 SHA256(id)-sorted episodes per push training physical fixture',
        train_push_episodes=len(rows), train_parameter_groups=len({r['parameter_group'] for r in rows}),
        metadata_counts={k:dict(v) for k,v in counts.items()}, metadata_missing=metadata_missing,
        sampled_episodes=len(selected), sampled_feature_rows=len(bank),
        feature_metric='RMS Euclidean distance in deployed head-normalized 176D features; 48D prefix is head-normalized current observation',
        cross_episode_train_nearest_distance_quantiles=np.quantile(reference,[0,.5,.9,1]).tolist(),
        episodes=reports, queries=queries,
        caveats=['Parameter mixture alone does not prove contradictory labels or a cause of task failure.',
                 'Same-state teacher replays condition on the same wrench history but do not create alternative closed-loop trajectories.',
                 'Nearest neighbours may have different histories and parameters; their label dispersion is descriptive.',
                 'Training-distance reference uses only a deterministic subset and no held-out calibration.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(sampled=len(selected), max_teacher_replay_error=max(r['teacher_replay_max_error'] for r in reports),
                         queries={k:v['teacher_config_tail_x_min_median_max'] for k,v in queries.items()})))


if __name__ == '__main__':
    main()
