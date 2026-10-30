"""Read-only, saved-trajectory diagnosis; never fits or integrates physics.

Raw observation envelopes are descriptive, not a causal/OOD certificate.
In particular joint channels 0/2/6 are not used by this ESN encoder.
"""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

DATA_SHA = '120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407'
USED = np.r_[14:17, 20:23, 26:29, 39:48]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def first(t, mask):
    ids = np.flatnonzero(mask)
    return float(t[ids[0]]) if len(ids) else None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--training', type=Path, required=True)
    p.add_argument('--regression', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists(), 'Do not overwrite diagnostic evidence'
    dataset = a.training/'data/training_data.npz'
    assert sha(dataset) == DATA_SHA, 'Only the current v9 data are admissible'
    with np.load(dataset, allow_pickle=False) as z:
        obs, ep, train = (z[k].copy() for k in ('observation', 'episode', 'train'))
    assert int(train.sum()) == 12600 and len(np.unique(ep[train])) == 24
    source = a.regression/'source/scripts/office_vmc_memory_esn_20260927.py'
    spec = importlib.util.spec_from_file_location('frozen_v9_actor', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    execution_path = a.regression/'execution.json'
    execution_bytes = execution_path.read_bytes()
    execution = json.loads(execution_bytes)
    model_lock = json.loads((a.regression/'INPUT_MODEL_LOCK.json').read_text())
    # One already inspected condition, paired across all three model seeds.
    rows = [r for r in execution['results'] if r['condition'].endswith('_000')]
    assert len(rows) == 9
    lo, hi = obs[train].min(0), obs[train].max(0)
    envelopes = {}
    results = []
    for row in rows:
        trace = Path(row['run'])/'rollout.npz'
        assert sha(trace) == row['trace_sha256']
        with np.load(trace, allow_pickle=False) as z:
            o, t, act, stage, err = (z[k].copy() for k in (
                'observation', 'time', 'applied_action', 'stage', 'task_position_error_m'))
            saved_requested = z['esn_action'].copy()
        outside = (o < lo-1e-9) | (o > hi+1e-9)
        saturated = np.any(np.abs(act) >= .999, axis=1)
        item = dict(method=row['method'], condition=row['condition'], trace_sha256=sha(trace),
            task=row['task_success'], strict=row['strict_success'],
            initial_raw_outside_channels=np.flatnonzero(outside[0]).tolist(),
            raw_envelope_outside_fraction=float(outside.any(1).mean()),
            esn_encoder_input_envelope_outside_fraction=float(outside[:, USED].any(1).mean()),
            first_applied_saturation_s=first(t, saturated),
            applied_saturation_fraction=float(saturated.mean()),
            first_tracking_error_gt_50mm_s=first(t, err > .05),
            stages=[dict(stage=int(s), start_s=float(t[stage == s][0]),
                duration_sampled_s=float(np.count_nonzero(stage == s)*.04),
                position_error_rmse_mm=float(np.sqrt(np.mean(err[stage == s]**2))*1000),
                max_position_error_mm=float(np.max(err[stage == s])*1000)) for s in np.unique(stage)])
        if '_esn_' in row['method']:
            checkpoint = a.regression/'checkpoints'/(row['method']+'.npz')
            actor = module.OfficeVMCMemoryESN(checkpoint)
            locked = next(m for m in model_lock['models'] if m['name'] == row['method'])
            assert sha(checkpoint) == locked['checkpoint_sha256']
            feats = []
            previous = None
            for eid, ob in zip(ep[train], obs[train]):
                if eid != previous:
                    actor.reset()
                    previous = eid
                feats.append(actor.features(ob))
            x = np.asarray(feats)
            active = np.any(actor.weights != 0, axis=1)
            flo, fhi = x[:, active].min(0), x[:, active].max(0)
            norm = np.maximum(x[:, active].std(0), .005)
            actor.reset()
            fx = np.asarray([actor.features(ob) for ob in o])
            raw = fx@actor.weights
            prediction = np.clip(raw, -1, 1)
            prediction[:, 0] = np.clip(raw[:, 0], 0, 1)
            replay_error = float(np.max(np.abs(prediction-saved_requested)))
            assert replay_error < 1e-10, replay_error
            excess = np.maximum(flo-fx[:, active], fx[:, active]-fhi)/norm
            excess = np.maximum(excess, 0).max(1)
            raw_sat = np.any(np.abs(raw[:, 1:]) >= 1, axis=1)
            item.update(checkpoint_sha256=sha(checkpoint), actor_replay_max_abs=replay_error,
                first_raw_residual_saturation_s=first(t, raw_sat),
                first_active_feature_envelope_excess_1std_s=first(t, excess > 1),
                first_active_feature_envelope_excess_5std_s=first(t, excess > 5),
                initial_active_feature_excess_std=float(excess[0]),
                max_active_feature_excess_std=float(excess.max()),
                raw_residual_max_abs=float(np.abs(raw[:, 1:]).max()),
                raw_slowdown_range=[float(raw[:, 0].min()), float(raw[:, 0].max())])
            envelopes[row['method']] = dict(active_features=int(active.sum()),
                train_raw_action_range_per_channel=np.stack(((x@actor.weights).min(0), (x@actor.weights).max(0))).tolist())
        results.append(item)
    out = dict(schema='sii-v9-saved-closed-loop-support-v1', created_utc=datetime.now(timezone.utc).isoformat(),
        status='diagnostic_only_no_refit_no_physics_no_model_selection',
        execution_snapshot_completed=execution['completed'],
        execution_snapshot_sha256=hashlib.sha256(execution_bytes).hexdigest(),
        dataset_sha256=DATA_SHA, training_frames=int(train.sum()),
        actor_source_sha256=sha(source), diagnostic_source_sha256=sha(Path(__file__)),
        esn_encoder_used_raw_channels=USED.tolist(),
        caveats=['Envelope exceedance is not a multivariate support or causal certificate.',
                 'Teacher labels are unavailable on student states; error here is task tracking error, not imitation loss.',
                 'Only completed condition 000 is inspected; no final method ranking.',
                 'Initial out-of-range joints 0/2/6 do not directly enter this ESN.'],
        train_envelopes=envelopes, rows=results)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(a.output), sha256=sha(a.output), rows=len(results))))


if __name__ == '__main__':
    main()
