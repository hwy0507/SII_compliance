"""Align saved pre-impact MLP actions, filter output and first gate crossings."""
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEV = ROOT / 'outputs/contact_yield_recovery_student_development_20261030_v7'
FIT = ROOT / 'outputs/contact_yield_recovery_retrain_20261030_v7'
DEST = ROOT.parents[1] / 'docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_V7_PREIMPACT_TIMELINE_20261031.json'
SEEDS = (2026102801, 2026102802, 2026102803)
SNAPSHOTS = (4.64, 4.68, 4.72, 4.76, 4.80)
LIMIT_M = .0002


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    if DEST.exists():
        raise FileExistsError(f'Preserve prior evidence: {DEST}')
    review = read(DEV / 'REVIEW.json')
    metadata = read(FIT / 'data/DATA_COMPLETE.json')
    assert review['status'] == 'verified_fixed27_development_diagnosis'
    assert review['no_final_test_performed'] is True
    assert metadata['training_data_sha256'] == 'd771433db06103edb3e33264b8040d059c4df6fb19faa66043f458c61457f42a'

    loaded = {}
    for seed in SEEDS:
        folder = DEV / 'episodes' / f'rod_00__special_mlp_scratch_s{seed}' / 'rod'
        with np.load(folder / 'trajectory.npz', allow_pickle=False) as z:
            trajectory = {key: z[key].copy() for key in ('time', 'qpos', 'qvel', 'action')}
        with np.load(folder / 'filter.npz', allow_pickle=False) as z:
            filtered = {key: z[key].copy() for key in ('twist', 'scale', 'dt')}
        with np.load(folder / 'substeps.npz', allow_pickle=False) as z:
            substeps = {key: z[key].copy() for key in (
                'time', 'external_penetration_m', 'joint_velocity', 'torque', 'disturbance_force_n')}
        assert trajectory['qpos'].shape == (500, 18)
        assert trajectory['qvel'].shape == (500, 17)
        assert trajectory['action'].shape == filtered['twist'].shape[:1] + (7,)
        assert substeps['time'].shape == substeps['external_penetration_m'].shape == (400000,)
        crossings = np.flatnonzero(substeps['external_penetration_m'] > LIMIT_M)
        first = None
        if len(crossings):
            i = int(crossings[0])
            first = dict(index=i, time_s=float(substeps['time'][i]),
                         penetration_m=float(substeps['external_penetration_m'][i]))
        loaded[seed] = (folder, trajectory, filtered, substeps, first)

    baseline = loaded[SEEDS[0]]
    baseline_t = baseline[1]['time']
    rows = []
    for seed in SEEDS:
        folder, trajectory, filtered, substeps, first = loaded[seed]
        times, qpos, qvel, action = (trajectory[k] for k in ('time', 'qpos', 'qvel', 'action'))
        baseline_traj, baseline_filter = baseline[1], baseline[2]
        snapshots = []
        for target in SNAPSHOTS:
            i = int(np.argmin(np.abs(times - target)))
            bi = int(np.argmin(np.abs(baseline_t - times[i])))
            time_s = float(times[i])
            event_relation = ('before_first_crossing' if first is None or time_s < first['time_s']
                              else 'at_or_after_first_crossing')
            snapshots.append(dict(
                requested_time_s=target, saved_time_s=time_s,
                relation_to_first_crossing=event_relation,
                robot_qpos=qpos[i, :7].tolist(),
                robot_qvel=qvel[i, :7].tolist(),
                requested_action=action[i].tolist(),
                filtered_twist=filtered['twist'][i].tolist(),
                filter_scale=float(filtered['scale'][i]),
                delta_from_passing_mlp01=dict(
                    robot_qpos_l2=float(np.linalg.norm(qpos[i, :7]-baseline_traj['qpos'][bi, :7])),
                    robot_qvel_l2=float(np.linalg.norm(qvel[i, :7]-baseline_traj['qvel'][bi, :7])),
                    requested_action_l2=float(np.linalg.norm(action[i]-baseline_traj['action'][bi])),
                    filtered_twist_l2=float(np.linalg.norm(
                        filtered['twist'][i]-baseline_filter['twist'][bi])))))
        event = None
        if first is not None:
            i = first['index']
            event = dict(**first,
                         joint_velocity=substeps['joint_velocity'][i].tolist(),
                         joint_torque=substeps['torque'][i].tolist(),
                         disturbance_force_n=float(substeps['disturbance_force_n'][i]))
        metric_path = folder.parent / 'METRICS.json'
        metric = read(metric_path)
        rows.append(dict(
            seed=seed, task_success=metric['task_success'],
            strict_success=metric['strict_success'],
            machine_compliant=metric['machine_compliant'],
            maximum_external_penetration_m=metric['max_external_penetration_m'],
            first_gate_crossing=event, snapshots=snapshots,
            input_hashes=dict(trajectory_sha256=sha(folder/'trajectory.npz'),
                              filter_sha256=sha(folder/'filter.npz'),
                              substeps_sha256=sha(folder/'substeps.npz'),
                              metrics_sha256=sha(metric_path))))

    result = dict(
        schema='sii-contact-yield-v7-preimpact-timeline-v1',
        status='complete_saved_substep_timeline_alignment',
        dataset_sha256=metadata['training_data_sha256'],
        development_review_sha256=sha(DEV/'REVIEW.json'),
        analyzer_sha256=sha(Path(__file__)),
        penetration_limit_m=LIMIT_M,
        comparison='Each failing MLP is compared with the passing MLP seed01 at the closest saved 40 ms actor timestamp.',
        qpos_qvel='Indices 0..6 are FR3 joints 1..7 under the registered model joint map.',
        rows=rows,
        limitations=[
            'The passing seed is a descriptive reference, not a paired counterfactual because initial qpos/qvel differ slightly.',
            'The first-crossing state is from saved substep summaries; no MuJoCo re-integration was performed.',
            'A 40 ms actor interval can hide faster state changes; saved substep files contain velocity, torque, penetration and disturbance force, not full qpos.',
            'The comparison identifies timing and association, not a unique causal action channel.',
            'Only registered rod_00 development trajectories were read; no physics, fitting, model selection, gate change, or final108 access.'],
        new_physics_steps=0, new_optimizer_updates=0)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                               allow_nan=False) + '\n')
    print(DEST)
    for row in rows:
        print(row['seed'], 'Task/Strict', row['task_success'], row['strict_success'],
              'first crossing', row['first_gate_crossing'])
        for item in row['snapshots']:
            print(item['saved_time_s'], item['relation_to_first_crossing'],
                  item['delta_from_passing_mlp01'])


if __name__ == '__main__':
    main()
