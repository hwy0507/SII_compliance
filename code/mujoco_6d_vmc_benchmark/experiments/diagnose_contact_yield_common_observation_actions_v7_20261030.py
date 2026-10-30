"""Replay all locked v7 actors on the same saved rod observations.

This is an offline counterfactual action comparison: it performs no MuJoCo
integration, fitting, reselection, or access to the isolated final test set.
"""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from current_student_policy_20260921 import load_current
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig

FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
DEV = ROOT / 'outputs/contact_yield_recovery_student_development_20261030_v7'
EVIDENCE = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029'
DEST = EVIDENCE / 'CONTACT_YIELD_COMMON_OBSERVATION_ACTIONS_V7_20261030_V3.json'
FAMILIES = ('esn_ridge', 'rnn_scratch', 'mlp_scratch')
SEEDS = (2026102801, 2026102802, 2026102803)
WINDOWS = ((0., 4.4), (4.4, 4.72), (4.72, 5.), (5., 8.),
           (8., 12.76), (12.76, 20.))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def model_key(model):
    return f"{model['family']}_s{model['seed']}"


def window_summary(values, times, start, end):
    mask = (times >= start) & (times < end)
    selected = values[mask]
    if not len(selected):
        return dict(start_s=start, end_s=end, frames=0)
    return dict(start_s=start, end_s=end, frames=int(mask.sum()),
                rms=float(np.sqrt(np.mean(selected ** 2))),
                mean_abs=float(np.mean(np.abs(selected))),
                max_abs=float(np.max(np.abs(selected))))


def channel_rms(values, times, start, end):
    mask = (times >= start) & (times < end)
    selected = values[mask]
    if not len(selected):
        return []
    return np.sqrt(np.mean(selected ** 2, axis=0)).tolist()


def filtered_trace(actions, config, dts):
    config = {key: np.asarray(value) if isinstance(value, list) else value
              for key, value in config.items()}
    filt = VelocityResidualActionFilter(VelocityResidualSafetyConfig(**config))
    twists, scales, clipped, saturated, limited = [], [], [], [], []
    for action, dt in zip(actions, dts):
        result = filt.filter(action, float(dt))
        twists.append(result.cartesian_yield_twist.copy())
        scales.append(result.wbc_scale)
        clipped.append(result.raw_action_clipped.copy())
        saturated.append(result.amplitude_saturated)
        limited.append(result.slew_limited)
    return dict(twist=np.asarray(twists), scale=np.asarray(scales),
                clipped=np.asarray(clipped), saturated=np.asarray(saturated),
                slew_limited=np.asarray(limited))


def main():
    assert not DEST.exists(), 'Preserve any earlier evidence; use a new versioned receipt.'
    fit_exec = read(FIT / 'execution.json')
    audit = read(FIT / 'FIT_AUDIT.json')
    lock = read(FIT / 'MODEL_LOCK.json')
    data_meta = read(FIT / 'data/DATA_COMPLETE.json')
    reg = read(DEV / 'REGISTRATION.json')
    execution = read(DEV / 'execution.json')
    review = read(DEV / 'REVIEW.json')
    assert fit_exec['status'] == 'complete' and len(fit_exec['fits']) == 75
    assert audit['status'] == 'passed' and lock['status'] == 'frozen'
    assert len(lock['models']) == 9 and data_meta['training_data_sha256'] == lock['training_data_sha256']
    assert reg['models'] == lock['models']
    assert execution['status'] == 'complete_development_diagnosis_pending_review'
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['no_final_test_performed'] is True
    models = {model_key(m): m for m in lock['models']}
    assert len(models) == 9
    loaded = {}
    for key, model in models.items():
        path = Path(model['checkpoint'])
        assert sha(path) == model['checkpoint_sha256']
        assert sha(Path(model['metadata'])) == model['metadata_sha256']
        loaded[key] = load_current(path)

    rows = []
    for family in FAMILIES:
        for seed in SEEDS:
            case_id = f'rod_00__special_{family}_s{seed}'
            folder = DEV / 'episodes' / case_id / 'rod'
            trajectory_path = folder / 'trajectory.npz'
            execution_path = folder / 'execution.json'
            filter_path = folder / 'filter.npz'
            episode_exec = read(execution_path)
            metric = read(folder.parent / 'METRICS.json')
            with np.load(trajectory_path, allow_pickle=False) as tape:
                observations = tape['observation'].copy()
                saved_action = tape['action'].copy()
                times = tape['time'].copy()
            with np.load(filter_path, allow_pickle=False) as tape:
                saved_filter = {name: tape[name].copy() for name in tape.files}
            dts = saved_filter['dt']
            assert observations.shape == (500, 48) and saved_action.shape == (500, 7)
            assert len(times) == len(dts) == len(observations)
            assert sha(trajectory_path) == next(
                r['input_hashes']['trajectory_sha256'] for r in read(EVIDENCE / 'CONTACT_YIELD_MLP_ROD_SUPPORT_DIAGNOSIS_V7_20261030.json')['rows']
                if r['case_id'] == case_id)

            actions, filtered = {}, {}
            for key, actor in loaded.items():
                actor.reset()
                actions[key] = np.asarray([actor.act(obs) for obs in observations])
                filtered[key] = filtered_trace(actions[key], episode_exec['filter_config'], dts)
            source_key = model_key(next(m for m in lock['models']
                                        if m['name'] == episode_exec['model_name'])) if 'model_name' in episode_exec else None
            if source_key is None:
                source_key = f"{family}_s{seed}"
            assert episode_exec['student_checkpoint_sha256'] == models[source_key]['checkpoint_sha256']
            np.testing.assert_array_equal(actions[source_key], saved_action)
            np.testing.assert_array_equal(filtered[source_key]['clipped'], saved_filter['clipped'])
            np.testing.assert_array_equal(filtered[source_key]['twist'], saved_filter['twist'])
            np.testing.assert_array_equal(filtered[source_key]['scale'], saved_filter['scale'])

            comparisons = []
            for key in models:
                delta = actions[key] - saved_action
                filter_delta = filtered[key]['twist'] - filtered[source_key]['twist']
                comparisons.append(dict(
                    actor=key,
                    is_source_actor=(key == source_key),
                    action_windows=[window_summary(delta, times, a, b) for a, b in WINDOWS],
                    action_channel_rms_by_window=[channel_rms(delta, times, a, b) for a, b in WINDOWS],
                    filtered_twist_windows=[window_summary(filter_delta, times, a, b) for a, b in WINDOWS],
                    filtered_twist_channel_rms_by_window=[channel_rms(filter_delta, times, a, b) for a, b in WINDOWS],
                    full_trace_action_rms=float(np.sqrt(np.mean(delta ** 2))),
                    full_trace_action_max_abs=float(np.max(np.abs(delta))),
                    full_trace_filtered_twist_rms=float(np.sqrt(np.mean(filter_delta ** 2))),
                    saturated_steps=int(filtered[key]['saturated'].sum()),
                    slew_limited_steps=int(filtered[key]['slew_limited'].sum())))

            pairwise = []
            for left_index, left in enumerate(models):
                for right in list(models)[left_index + 1:]:
                    action_delta = actions[left] - actions[right]
                    twist_delta = filtered[left]['twist'] - filtered[right]['twist']
                    pairwise.append(dict(
                        left=left, right=right,
                        action_rms=float(np.sqrt(np.mean(action_delta ** 2))),
                        action_max_abs=float(np.max(np.abs(action_delta))),
                        action_channel_rms_by_window=[channel_rms(action_delta, times, a, b) for a, b in WINDOWS],
                        filtered_twist_rms=float(np.sqrt(np.mean(twist_delta ** 2))),
                        windows=[window_summary(action_delta, times, a, b) for a, b in WINDOWS]))
            rows.append(dict(
                case_id=case_id, task_success=metric['task_success'],
                strict_success=metric['strict_success'],
                machine_compliant=metric['machine_compliant'],
                max_external_penetration_m=metric['max_external_penetration_m'],
                hand_contact_first_s=read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')['hand_contact_first_s'],
                pass_s=read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')['pass_s'],
                rejoin_confirmed_s=read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')['rejoin_confirmed_s'],
                retract_start_s=read(folder / 'ROD_YIELD_REJOIN_AUDIT_V3.json')['retract_start_s'],
                source_actor=source_key,
                hashes=dict(trajectory_sha256=sha(trajectory_path),
                            execution_sha256=sha(execution_path), filter_sha256=sha(filter_path)),
                comparisons_to_source=comparisons, pairwise=pairwise))

    result = dict(
        schema='sii-contact-yield-common-observation-actions-v7-v2',
        status='complete_saved_common_observation_action_filter_replay',
        dataset_sha256=lock['training_data_sha256'],
        fit_execution_sha256=sha(FIT / 'execution.json'),
        fit_audit_sha256=sha(FIT / 'FIT_AUDIT.json'),
        model_lock_sha256=sha(FIT / 'MODEL_LOCK.json'),
        development_registration_sha256=sha(DEV / 'REGISTRATION.json'),
        development_execution_sha256=sha(DEV / 'execution.json'),
        development_review_sha256=sha(DEV / 'REVIEW.json'),
        analyzer_sha256=sha(Path(__file__)),
        actors=list(models), rows=rows,
        method='For each saved rod00 observation tape, reset and sequentially advance every locked model on the identical observation sequence; then independently replay each resulting request through the episode’s recorded unchanged filter configuration and dt sequence.',
        limitations=[
            'This is an offline counterfactual action comparison on nine saved train00 development trajectories, not a physical counterfactual rollout.',
            'The observations were generated by each source actor; shared-input action differences do not establish which action caused the observed penetration.',
            'Recurrent actors are reset at the beginning of each trajectory and advanced in time order.',
            'No MuJoCo steps, fitting, model selection, training-data changes, gate changes, or final-test access occurred.',
            'Saved filter outputs are recomputed from the frozen filter configuration; this analysis does not apply commands to physics.'],
        new_physics_steps=0, new_optimizer_updates=0, final_test_accessed=False)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(DEST)
    print('rows', len(rows), 'models', len(models), 'pairwise comparisons', sum(len(r['pairwise']) for r in rows))
    for row in rows:
        failing = [x for x in row['comparisons_to_source'] if x['actor'].startswith('mlp_scratch')]
        print(row['case_id'], 'Task/Strict', row['task_success'], row['strict_success'],
              'penetration_mm', round(row['max_external_penetration_m'] * 1000, 4),
              'action_rms_vs_source', [(x['actor'], round(x['full_trace_action_rms'], 5)) for x in failing])


if __name__ == '__main__':
    main()
