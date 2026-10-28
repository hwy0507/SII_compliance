"""Diagnose completed ESNs on all24 training histories while neural fits run.

No student dynamics, refitting, validation diagnostics, or checkpoint selection.
Uses each already-completed ESN search's original selected checkpoint. Replay
with the frozen evaluation actor distinguishes export errors from fit residuals.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import math
from pathlib import Path

import numpy as np

from audit_special_scene_fits_20261028 import load_class
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_repaired_student_closures_20261029 import error_stats, teacher_replay


def stats(prediction, target):
    result = error_stats(prediction, target)
    if len(target):
        # Independent scalar summation checks the vectorized aggregate.
        scalar = math.fsum(float(v)**2 for v in (prediction-target).flat)/target.size
        assert math.isclose(scalar, result['mse'], rel_tol=1e-12, abs_tol=1e-20)
        result['teacher_channel_rms'] = np.sqrt(np.mean(target**2, axis=0)).tolist()
        result['channel_max_abs'] = np.max(np.abs(prediction-target), axis=0).tolist()
    return result


def time_windows(time):
    # Integrator timestamp drift can make30.0s slightly larger than30 and
    # otherwise produce a spurious one-frame30-32s tail. Partition the verified
    # 40ms samples by index, exactly once, into50-frame diagnostic windows.
    np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=1e-8)
    np.testing.assert_allclose(time[0], .04, rtol=0, atol=1e-8)
    windows = {}
    index = np.arange(len(time))
    for start in range(0, len(time), 50):
        end = min(start+50, len(time))
        windows[f'time_{start*.04:g}_{end*.04:g}s'] = (index >= start) & (index < end)
    assert np.all(np.sum(list(windows.values()), axis=0) == 1)
    return windows


def audit(training, preparation, output):
    assert not output.exists(), 'Preserve prior diagnostic receipts'
    prep = read(preparation)
    assert Path(prep['training']) == training
    state = read(training/'execution.json')
    metadata = read(training/'data/DATA_COMPLETE.json')
    dataset_sha = sha(training/'data/training_data.npz')
    assert dataset_sha == metadata['training_data_sha256']
    source = read(training/'FITTING_SOURCE.json')
    for name, digest in source['source_hashes'].items():
        assert sha(training/'fitting_source'/name) == digest, name
    frozen = Path(prep['physics_source'])
    actor_name = 'scripts/office_vmc_memory_esn_20260927.py'
    assert sha(frozen/actor_name) == prep['physics_source_sha256'][actor_name]
    for name in ('tools/optimize_tool_contact_20261002.py',):
        assert sha(ROOT/name) == prep['source_sha256'][name]
    for name, digest in prep['source_sha256'].items():
        if name.startswith('scripts/'):
            assert sha(ROOT/name) == digest
    actor_class = load_class(frozen, 'office_vmc_memory_esn_20260927.py', 'OfficeVMCMemoryESN')
    with np.load(training/'data/training_data.npz', allow_pickle=False) as z:
        obs, target, episode, train = (z[k].copy() for k in (
            'observation', 'requested_teacher_action', 'episode', 'train'))
    lineage = [r for r in metadata['lineage'] if r['split'] == 'train']
    assert Counter(r['scene'] for r in lineage) == Counter(rod=8, ball=8, corner=8)
    assert set(episode[train]) == {r['episode'] for r in lineage}
    assert not set(episode[train]) & set(episode[~train])
    histories = {}
    inputs = {str(training/'data/DATA_COMPLETE.json'): sha(training/'data/DATA_COMPLETE.json'),
              str(training/'data/training_data.npz'): dataset_sha,
              str(preparation): sha(preparation), str(frozen/actor_name): sha(frozen/actor_name)}
    for row in lineage:
        folder = Path(row['folder'])
        for name, digest in row['hashes'].items():
            assert sha(folder/name) == digest, str(folder/name)
            inputs[str(folder/name)] = digest
        ids = np.flatnonzero(episode == row['episode'])
        assert len(ids) == row['frames'] and train[ids].all()
        with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
            np.testing.assert_array_equal(obs[ids], z['observation'])
            np.testing.assert_array_equal(target[ids], z['action'])
            time = z['time'].copy()
        assert np.all(np.isfinite(time))
        np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=1e-8)
        teacher, activation = teacher_replay(read(folder/'teacher.json'), obs[ids])
        np.testing.assert_array_equal(teacher, target[ids])
        windows = time_windows(time)
        windows['recovery_over_half_descriptive'] = activation > .5
        windows['remaining_recovery'] = activation <= .5
        if row['scene'] == 'rod':
            path = folder/'ROD_YIELD_REJOIN_AUDIT_V3.json'
            rod = read(path)
            assert rod['status'] == 'passed'
            for name, digest in rod['hashes'].items():
                path_to_check = ROOT/'tools'/name if name.endswith('.py') else folder/name
                assert sha(path_to_check) == digest
            inputs[str(path)] = sha(path)
            for name, start, end in (
                ('contact_to_pass', rod['hand_contact_first_s'], rod['pass_s']),
                ('pass_to_rejoin', rod['pass_s'], rod['rejoin_confirmed_s']),
                ('rejoin_to_withdrawal', rod['rejoin_confirmed_s'], rod['retract_start_s'])):
                windows[name] = (time >= start-1e-8) & (time <= end+1e-8)
        histories[row['id']] = (row, ids, windows)
    fits = [r for r in state['fits'] if r['family'] == 'esn_ridge']
    assert len(fits) == 3 and {r['seed'] for r in fits} == {2026102801, 2026102802, 2026102803}
    results = []
    for fit in fits:
        assert fit['status'] == 'complete'
        folder = Path(fit['output'])
        info = read(folder/'TRAINING_COMPLETE.json')
        assert info['training_data_sha256'] == dataset_sha
        assert sha(folder/'TRAINING_COMPLETE.json') == fit['metadata_sha256']
        assert sha(folder/'checkpoint.npz') == fit['checkpoint_sha256'] == info['checkpoint_sha256']
        for name, digest in info['source_sha256'].items():
            assert source['source_hashes'][name] == digest
        for name in ('checkpoint.npz', 'TRAINING_COMPLETE.json', 'exported_replay.npz'):
            inputs[str(folder/name)] = sha(folder/name)
        with np.load(folder/'exported_replay.npz', allow_pickle=False) as z:
            np.testing.assert_array_equal(z['episode'], episode)
            prediction = z['prediction'].copy()
        assert prediction.shape == target.shape and np.isfinite(prediction).all()
        actor = actor_class(folder/'checkpoint.npz')
        rows = []
        for identity, (row, ids, windows) in histories.items():
            actor.reset()
            replay = np.asarray([actor.act(o) for o in obs[ids]])
            np.testing.assert_array_equal(replay, prediction[ids])
            rows.append(dict(id=identity, scene=row['scene'], **stats(replay, target[ids]),
                             windows={k:stats(replay[m], target[ids][m]) for k,m in windows.items()}))
        scene_stats = {}
        for scene in ('rod', 'ball', 'corner'):
            ids = np.concatenate([ids for row,ids,_ in histories.values() if row['scene'] == scene])
            scene_stats[scene] = stats(prediction[ids], target[ids])
        results.append(dict(seed=fit['seed'], checkpoint_sha256=fit['checkpoint_sha256'],
                            training_frozen_actor_exact_replay=True, scenes=scene_stats, histories=rows))
    for name, digest in inputs.items():
        assert sha(Path(name)) == digest, 'Input changed while auditing: '+name
    sources = [Path(__file__), ROOT/'tools/audit_special_scene_fits_20261028.py',
               ROOT/'tools/review_repaired_student_closures_20261029.py',
               ROOT/'tools/collect_special_scene_actions_20261028.py',
               ROOT/'tools/optimize_tool_contact_20261002.py']
    output.parent.mkdir(parents=True, exist_ok=True)
    result = dict(status='training_history_diagnostic_complete_not_closed_loop',
        created_utc=datetime.now(timezone.utc).isoformat(), models=results,
        training_identities=24, training_frames=int(train.sum()),
        teacher_exact_replay_all24=True, input_sha256=inputs,
        source_sha256={str(p):sha(p) for p in sources},
        channels=['slowdown','translation_x','translation_y','translation_z','rotation_x','rotation_y','rotation_z'],
        units='Dimensionless requested actions before the common filter, not joint torque or actual velocity.',
        limitation='Training histories only; ESN checkpoints already chosen by their original searches. '
        'No refit, checkpoint reselection, neural comparison, validation diagnostics or student dynamics. '
        'Two-second windows and recovery>.5 are descriptive. Low imitation loss does not prove closed-loop '
        'stability, Task/Strict success, or repair of the final matrix. All75/full9 audit and18/108 remain required.')
    write(output, result)
    print(result['status'], 'models', len(results), 'train histories', len(lineage))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--training', type=Path, required=True)
    p.add_argument('--preparation', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    audit(a.training.resolve(), a.preparation.resolve(), a.output.resolve())
