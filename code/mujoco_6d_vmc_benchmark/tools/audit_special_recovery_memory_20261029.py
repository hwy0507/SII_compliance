"""Describe teacher/ESN recovery on all24 real training histories.

No new physics, synthetic tails, model selection or fitting. Near-zero load is
a dimensionless descriptive threshold on the actor's existing wrench scale,
not a contact or success gate. All scenes and seeds are retained.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from audit_special_scene_fits_20261028 import load_class
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_repaired_student_closures_20261029 import teacher_replay


def audit(training, preparation, prior_review, output):
    assert not output.exists()
    prior = read(prior_review)
    assert prior['status'] == 'training_history_diagnostic_complete_not_closed_loop'
    for name, digest in {**prior['input_sha256'], **prior['source_sha256']}.items():
        assert sha(Path(name)) == digest, name
    prep = read(preparation)
    assert Path(prep['training']) == training
    frozen = Path(prep['physics_source'])
    actor_file = frozen/'scripts/office_vmc_memory_esn_20260927.py'
    assert sha(actor_file) == prep['physics_source_sha256']['scripts/office_vmc_memory_esn_20260927.py']
    actor_class = load_class(frozen, actor_file.name, 'OfficeVMCMemoryESN')
    actors, model_rows = {}, []
    for model in prior['models']:
        checkpoint = training/f"learning/esn_ridge_s{model['seed']}/checkpoint.npz"
        assert sha(checkpoint) == model['checkpoint_sha256']
        actor = actor_class(checkpoint)
        assert actor.context_gate_w is None
        with np.load(checkpoint, allow_pickle=False) as z:
            assert 'state_delta_readout' not in z.files or not bool(z['state_delta_readout'])
        assert np.all(actor.weights[-actor.context_dimension:] == 0)
        np.testing.assert_array_equal(actor.scale, [8, 8, 8, 1, 1, 1])
        actors[model['seed']] = actor
        model_rows.append(dict(seed=model['seed'], checkpoint_sha256=sha(checkpoint),
            nominal_leak_timescales_s=np.unique(-.04/np.log1p(-actor.leak)).tolist(),
            direct_context_readout_zero=True, context_dependent_leak=False))
    meta = read(training/'data/DATA_COMPLETE.json')
    lineage = [r for r in meta['lineage'] if r['split'] == 'train']
    assert len(lineage) == 24 and set(r['id'] for r in lineage) == set(meta['training_identities'])
    rows = []
    for row in lineage:
        folder = Path(row['folder'])
        assert sha(folder/'trajectory.npz') == row['hashes']['trajectory.npz']
        with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
            obs, target, time = (z[k].copy() for k in ('observation','action','time'))
        np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=1e-8)
        teacher, activation = teacher_replay(read(folder/'teacher.json'), obs)
        np.testing.assert_array_equal(teacher, target)
        tail = np.arange(len(time)-50, len(time))
        load = np.max(np.abs(obs[:,39:45]/np.array([8,8,8,1,1,1])), axis=1)
        thresholds = {}
        for threshold in (1e-4, 1e-6, 1e-8):
            significant = np.flatnonzero(load > threshold)
            last = int(significant[-1]) if len(significant) else None
            thresholds[str(threshold)] = dict(last_above_threshold_sample=last,
                tail_near_zero_frames=int(np.sum(load[tail] <= threshold)),
                final_continuous_near_zero_duration_s=float((len(time)-1-last)*.04) if last is not None else float(len(time)*.04))
        predictions = []
        for seed, actor in actors.items():
            actor.reset()
            predicted, state_norm = [], []
            for observation in obs:
                predicted.append(actor.act(observation))
                state_norm.append(float(np.linalg.norm(actor.state)))
            predicted = np.asarray(predicted)
            delta = predicted[tail,3]-target[tail,3]
            # Cross-check against the independently verified full-history export.
            fit = training/f'learning/esn_ridge_s{seed}'
            with np.load(fit/'exported_replay.npz', allow_pickle=False) as z:
                expected = z['prediction'][z['episode'] == row['episode']]
            np.testing.assert_array_equal(predicted, expected)
            predictions.append(dict(seed=seed,
                tail_z_mean=float(predicted[tail,3].mean()),
                tail_z_bias=float(delta.mean()), tail_z_rmse=float(np.sqrt(np.mean(delta**2))),
                reservoir_norm_at_tail_start=state_norm[int(tail[0])], reservoir_norm_at_end=state_norm[-1]))
        rows.append(dict(id=row['id'], scene=row['scene'], split=row['split'],
            frames=len(time), tail_frames=50, tail_time_first_s=float(time[tail[0]]), tail_time_last_s=float(time[-1]),
            tail_scaled_wrench_max=float(load[tail].max()), near_zero_thresholds=thresholds,
            tail_teacher_z_mean=float(target[tail,3].mean()), tail_teacher_z_rms=float(np.sqrt(np.mean(target[tail,3]**2))),
            tail_teacher_recovery_activation_mean=float(activation[tail].mean()),
            tail_teacher_recovery_activation_min=float(activation[tail].min()),
            predictions=predictions))
    for name, digest in prior['input_sha256'].items():
        assert sha(Path(name)) == digest
    result = dict(status='all24_train_recovery_memory_diagnostic_no_refit',
        created_utc=datetime.now(timezone.utc).isoformat(), rows=rows, models=model_rows,
        prior_review=str(prior_review), prior_review_sha256=sha(prior_review),
        preparation_sha256=sha(preparation), teacher_config_sha256=meta['teacher_config_sha256'],
        dataset_sha256=meta['training_data_sha256'], source_sha256={str(p):sha(p) for p in (
            Path(__file__), ROOT/'tools/review_repaired_student_closures_20261029.py',
            ROOT/'tools/optimize_tool_contact_20261002.py', actor_file)},
        units='Normalized requested action before the common filter. Load=max(abs(estimated_wrench/[8N,8N,8N,1Nm,1Nm,1Nm])).',
        limitation='All24 training histories and all3 completed ESNs; no validation/test trajectories, '
        'synthetic extension, refit, checkpoint selection, or physical integration. Near-zero thresholds '
        'are descriptive sensitivity checks, not contact/task gates. Nominal neuron timescales are not '
        'the recurrent network effective memory. Sustained teacher recovery with small estimated load '
        'and student action bias is evidence of an imitation mismatch, not proof of closed-loop failure '
        'or proof that changing memory will improve it. Actual18 and108 remain required.')
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output,result)
    print(result['status'],len(rows))


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('training','preparation','prior-review','output'):
        p.add_argument('--'+name, type=Path, required=True)
    a=p.parse_args()
    audit(a.training.resolve(),a.preparation.resolve(),a.prior_review.resolve(),a.output.resolve())
