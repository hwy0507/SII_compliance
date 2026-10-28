"""Check saved ESN ridge solutions against the original train-only equations.

Reconstructs sufficient statistics but does not solve, refit, or change models.
This is an algebra/export check, not a closed-loop stability certificate.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from audit_special_scene_fits_20261028 import load_class
from collect_special_scene_actions_20261028 import ROOT, read, sha, write


def audit(training, history_review, output):
    assert not output.exists()
    history = read(history_review)
    assert history['status'] == 'training_history_diagnostic_complete_not_closed_loop'
    for name, digest in history['input_sha256'].items():
        assert sha(Path(name)) == digest
    for name, digest in history['source_sha256'].items():
        assert sha(Path(name)) == digest
    metadata = read(training/'data/DATA_COMPLETE.json')
    assert sha(training/'data/training_data.npz') == metadata['training_data_sha256']
    source = training/'fitting_source'
    frozen = read(training/'FITTING_SOURCE.json')
    for name, digest in frozen['source_hashes'].items():
        assert sha(source/name) == digest
    actor_class = load_class(source, 'office_vmc_memory_esn_20260927.py', 'OfficeVMCMemoryESN')
    with np.load(training/'data/training_data.npz', allow_pickle=False) as z:
        obs, target, episode, train = (z[k].copy() for k in (
            'observation', 'requested_teacher_action', 'episode', 'train'))
        assert np.all(z['importance'][train] == 1)
    assert len(np.unique(episode[train])) == 24
    rows = []
    for model in history['models']:
        folder = training/f"learning/esn_ridge_s{model['seed']}"
        checkpoint = folder/'checkpoint.npz'
        assert sha(checkpoint) == model['checkpoint_sha256']
        info = read(folder/'TRAINING_COMPLETE.json')
        assert info['temporal_readout_loss']['delta_weight'] == 0
        assert info['temporal_readout_loss']['integral_weight'] == 0
        actor = actor_class(checkpoint)
        assert actor.context_dimension == 12
        assert np.all(actor.weights[-12:] == 0)
        features = []
        previous = None
        for eid, o in zip(episode[train], obs[train]):
            if eid != previous:
                actor.reset()
                previous = eid
            features.append(actor.features(o))
        x = np.asarray(features)[:, :-12]
        norm = np.maximum(x.std(axis=0), .005)
        design = x/norm
        coefficients = actor.weights[:-12]*norm[:, None]
        ridge = info['selected']['ridge']
        gram = design.T@design + ridge*np.eye(design.shape[1])
        rhs = design.T@target[train]
        residual = gram@coefficients-rhs
        relative = np.linalg.norm(residual)/max(np.linalg.norm(rhs), 1e-30)
        assert np.isfinite(relative) and relative < 1e-9
        raw = x@actor.weights[:-12]
        clipped = np.clip(raw, -1, 1)
        clipped[:, 0] = np.clip(raw[:, 0], 0, 1)
        with np.load(folder/'exported_replay.npz', allow_pickle=False) as z:
            expected = z['prediction'][train]
        error = float(np.max(np.abs(clipped-expected)))
        assert error < 1e-12
        rows.append(dict(seed=model['seed'], ridge=ridge, train_frames=len(x),
            features=x.shape[1], checkpoint_sha256=sha(checkpoint),
            relative_normal_equation_residual=float(relative),
            max_abs_normal_equation_residual=float(np.abs(residual).max()),
            reconstructed_export_max_abs=error,
            clipped_fraction_per_channel=np.mean(clipped != raw, axis=0).tolist()))
    result = dict(status='saved_ridge_equations_verified_no_refit', rows=rows,
        created_utc=datetime.now(timezone.utc).isoformat(), history_review_sha256=sha(history_review),
        training_data_sha256=metadata['training_data_sha256'],
        source_sha256={str(p):sha(p) for p in (Path(__file__),
            ROOT/'tools/audit_special_scene_fits_20261028.py',
            ROOT/'tools/collect_special_scene_actions_20261028.py')},
        limitation='Train-only normal equations of the registered unweighted ridge objective. '
        'No solve/refit/selection or student dynamics. Does not prove optimal representation, '
        'adequate coverage, closed-loop stability, or repaired final evaluation matrix.')
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, result)
    print(result['status'], rows)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training', type=Path, required=True)
    p.add_argument('--history-review', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    audit(a.training.resolve(), a.history_review.resolve(), a.output.resolve())
