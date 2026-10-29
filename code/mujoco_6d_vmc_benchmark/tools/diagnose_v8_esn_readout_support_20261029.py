"""Attribute frozen ESN readouts and measure train-only ridge design support.

The already inspected successful teacher history is diagnostic only. No
checkpoint fitting, selection, synthetic labels or physical simulation.
Grouped raw readouts are additive identities, not causal interventions.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_v8_matched_teacher_history_20261029 import RUNTIME, frozen_actor
from prepare_special_frozen_test_20261028 import manifest


def summary(values):
    a = np.asarray(values)
    assert a.size and np.isfinite(a).all()
    return dict(minimum=float(a.min()), median=float(np.median(a)),
                p95=float(np.quantile(a, .95)), maximum=float(a.max()),
                mean=float(a.mean()))


def feature_groups(actor):
    n, c = actor.w.shape[0], actor.context_dimension
    assert actor.context_inputs and actor.absolute_inputs and c == 12
    assert actor.readout_order == 1 and not actor.nonlinear
    assert actor.state_context_readout_w is not None
    assert actor.readout_activation == 'clipped_linear' and actor.output_gain == 1
    assert not actor.axis_separable and np.count_nonzero(actor.weights[-c:]) == 0
    sizes = [('current_load', 6), ('reservoir_state', n),
             ('absolute_load', 6), ('absolute_state', n),
             ('load_context', 12*c), ('state_context', n), ('context_only', c)]
    groups, start = [], 0
    for name, size in sizes:
        groups.append((name, start, start+size))
        start += size
    assert start == actor.weights.shape[0]
    return groups


def features(actor, observation, episode):
    actor.reset()
    previous = None
    rows = []
    for obs, eid in zip(observation, episode):
        if eid != previous:
            actor.reset()
            previous = eid
        rows.append(actor.features(obs))
    return np.asarray(rows)


def readouts(x, actor, groups):
    parts = np.stack([x[:, start:end] @ actor.weights[start:end]
                      for _, start, end in groups], axis=1)
    raw = x @ actor.weights
    np.testing.assert_allclose(parts.sum(axis=1), raw, rtol=1e-11, atol=1e-12)
    prediction = np.clip(raw, -1, 1)
    prediction[:, 0] = np.clip(raw[:, 0], 0, 1)
    return parts, raw, prediction


def describe(parts, raw, prediction, target, leverage, train_p95):
    return dict(frames=len(raw), action_mse=float(np.mean((prediction-target)**2)),
                raw_group_rms_by_channel=np.sqrt(np.mean(parts**2, axis=0)).tolist(),
                raw_group_max_abs_by_channel=np.abs(parts).max(axis=0).tolist(),
                raw_rms_by_channel=np.sqrt(np.mean(raw**2, axis=0)).tolist(),
                clipped_fraction_by_channel=np.mean(raw != prediction, axis=0).tolist(),
                ridge_design_leverage=summary(leverage),
                leverage_over_train_p95_fraction=float(np.mean(leverage > train_p95)))


def run(output):
    assert not output.exists(), 'Preserve earlier diagnostic'
    training = ROOT/'outputs/special_scene_retrain_20261029_v8'
    prior = ROOT/'outputs/nonrl_v8_matched_teacher_history_20261029_v2'
    preparation = ROOT/'outputs/special_scene_frozen108_preparation_20261029_v8'
    lock_path, data_path = training/'MODEL_LOCK.json', training/'data/training_data.npz'
    lock, matched = read(lock_path), read(prior/'REVIEW.json')
    assert sha(data_path) == lock['training_data_sha256']
    assert sha(prior/'PREDICTIONS.npz') == matched['prediction_sha256']
    assert manifest(RUNTIME) == read(preparation/'REGISTRATION.json')['physics_source_sha256']
    for name, digest in matched['input_hashes'].items():
        assert sha(Path(name)) == digest, name
    for name, digest in matched['source_hashes'].items():
        assert sha(Path(name)) == digest, name
    with np.load(data_path, allow_pickle=False) as z:
        train = z['train'].astype(bool)
        assert np.all(z['importance'][train] == 1)
        obs, target, episode = [z[k][train].copy() for k in
                               ('observation', 'requested_teacher_action', 'episode')]
    assert len(obs) == 12600 and len(np.unique(episode)) == 24
    with np.load(prior/'PREDICTIONS.npz', allow_pickle=False) as z:
        query, qt, stage, time = [z[k].copy() for k in
                                 ('observation', 'teacher_action', 'stage', 'time')]
        previous = {m['name']: z[m['name']].copy() for m in lock['models'] if m['family']=='esn_ridge'}
    arrays, rows = dict(stage=stage, time=time), []
    for model in lock['models']:
        if model['family'] != 'esn_ridge':
            continue
        assert sha(Path(model['checkpoint'])) == model['checkpoint_sha256']
        assert sha(Path(model['metadata'])) == model['metadata_sha256']
        info = read(Path(model['metadata']))
        actor = frozen_actor(model)
        groups = feature_groups(actor)
        x = features(actor, obs, episode)
        q = features(actor, query, np.zeros(len(query), dtype=int))
        xp, xr, prediction = readouts(x, actor, groups)
        qp, qr, qprediction = readouts(q, actor, groups)
        with np.load(Path(model['checkpoint']).with_name('exported_replay.npz'), allow_pickle=False) as z:
            np.testing.assert_allclose(prediction, z['prediction'][train], rtol=0, atol=1e-12)
        np.testing.assert_allclose(qprediction, previous[model['name']], rtol=0, atol=1e-12)
        # This is the original training normalizer and regularizer; test/query
        # frames never enter the Gram matrix or change any model coefficient.
        norm = np.maximum(x[:, :-12].std(axis=0), .005)
        design, qdesign = x[:, :-12]/norm, q[:, :-12]/norm
        ridge = info['selected']['ridge']
        assert ridge > 0
        gram = design.T@design + ridge*np.eye(design.shape[1])
        chol = np.linalg.cholesky(gram)
        projection = solve_triangular(chol, design.T, lower=True)
        leverage = np.sum(projection**2, axis=0)
        qprojection = solve_triangular(chol, qdesign.T, lower=True)
        qleverage = np.sum(qprojection**2, axis=0)
        # Independent linear solve checks both train and query quadratic forms.
        checked = []
        for label, d, lv in [('train', design, leverage), ('teacher_history', qdesign, qleverage)]:
            for i in sorted({0, len(d)//2, len(d)-1, int(np.argmax(lv))}):
                exact = float(d[i] @ np.linalg.solve(gram, d[i]))
                np.testing.assert_allclose(lv[i], exact, rtol=1e-6, atol=1e-9)
                checked.append(dict(domain=label, frame=i, quadratic_form=exact, cholesky=float(lv[i])))
        p95 = float(np.quantile(leverage, .95))
        rows.append(dict(name=model['name'], seed=model['seed'], ridge=ridge,
            feature_groups=[dict(name=n, start=a, end=b) for n,a,b in groups],
            train=describe(xp,xr,prediction,target,leverage,p95),
            teacher_history=describe(qp,qr,qprediction,qt,qleverage,p95),
            stages=[dict(stage=int(s), **describe(qp[stage==s], qr[stage==s], qprediction[stage==s],
                         qt[stage==s], qleverage[stage==s], p95)) for s in sorted(set(stage.tolist()))],
            independent_quadratic_checks=checked,
            checkpoint_sha256=model['checkpoint_sha256'], metadata_sha256=model['metadata_sha256']))
        prefix = str(model['seed'])
        arrays.update({prefix+'_train_parts':xp, prefix+'_train_raw':xr,
            prefix+'_train_leverage':leverage, prefix+'_teacher_parts':qp,
            prefix+'_teacher_raw':qr, prefix+'_teacher_leverage':qleverage})
    assert len(rows) == 3
    output.mkdir(parents=True)
    np.savez_compressed(output/'READOUT_ARRAYS.npz', **arrays)
    with np.load(output/'READOUT_ARRAYS.npz', allow_pickle=False) as z:
        for k,v in arrays.items():
            np.testing.assert_array_equal(z[k],v)
    result = dict(status='frozen_esn_readout_support_diagnostic',
        created_utc=datetime.now(timezone.utc).isoformat(), rows=rows,
        input_hashes={str(p):sha(p) for p in (lock_path,data_path,prior/'REVIEW.json',prior/'PREDICTIONS.npz',
                                            preparation/'REGISTRATION.json')},
        source_hashes={str(p):sha(p) for p in (Path(__file__),
            ROOT/'tools/diagnose_v8_matched_teacher_history_20261029.py',
            RUNTIME/'scripts/office_vmc_memory_esn_20260927.py')},
        arrays_sha256=sha(output/'READOUT_ARRAYS.npz'),
        formula='h(x)=(x/train_std) @ (X_train.T@X_train + ridge*I)^-1 @ (x/train_std). '
                'train_std has the original .005 floor. Context-only zero columns excluded.',
        limitation='Previously inspected teacher condition000, not unseen. Raw additive contributions before clipping '
            'are not causal group removals. Leverage is train-design support, not calibrated uncertainty or a new gate. '
            'No fitting, checkpoint selection, new physical trajectory or evidence of closed-loop repair.')
    write(output/'REVIEW.json', result)
    for row in rows:
        print(row['seed'], 'train leverage', row['train']['ridge_design_leverage'],
              'teacher leverage', row['teacher_history']['ridge_design_leverage'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output.resolve())
