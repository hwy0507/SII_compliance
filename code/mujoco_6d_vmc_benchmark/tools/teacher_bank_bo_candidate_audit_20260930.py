"""Offline, training-only explanation of frozen active_short VMC c05 acquisition.

No dynamics, validation, candidate generation for execution, or source mutation.
The acquisition is reconstructed from its original five-observation prefix.
"""
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import resource
import sys

import numpy as np
import scipy


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def columns(path):
    # Each compressed column is materialized once; never repeatedly index an NpzFile.
    with np.load(path, allow_pickle=False) as archive:
        return {key: archive[key] for key in archive.files}


def trace_stats(value):
    value = np.asarray(value, float)
    diff = np.diff(value, axis=0)
    return dict(rms=float(np.sqrt(np.mean(value ** 2))),
                max_abs=float(np.max(np.abs(value))),
                step_delta_rms=float(np.sqrt(np.mean(diff ** 2))) if len(diff) else 0.)


def episode(path):
    audit, rollout, request = (read(path / f) for f in ('audit.json', 'rollout.json', 'request.json'))
    if audit['split'] != 'train' or request['phase'] != 'search':
        raise ValueError('Only original search training anchors are authorized')
    r, teacher, chain = (columns(path / f) for f in ('rollout.npz', 'teacher_internal.npz', 'execution_chain.npz'))
    files = {name: sha(path / name) for name in audit['files_sha256']}
    mismatch = [name for name, digest in files.items() if digest != audit['files_sha256'][name]]
    if mismatch:
        raise ValueError(f'Frozen raw hashes differ: {mismatch}')
    stages = {}
    for stage in np.unique(r['stage']):
        mask = r['stage'] == stage
        position, rotation, speed = (r[k][mask] for k in ('task_position_error_m', 'task_rotation_error_rad', 'task_speed_mps'))
        stages[str(int(stage))] = dict(
            samples=int(mask.sum()), first_post_step_s=float(r['time'][mask][0]),
            last_post_step_s=float(r['time'][mask][-1]),
            position_median_m=float(np.median(position)), position_max_m=float(position.max()),
            rotation_median_rad=float(np.median(rotation)), rotation_max_rad=float(rotation.max()),
            speed_median_mps=float(np.median(speed)), speed_max_mps=float(speed.max()),
            position_gate_failed_fraction=float(np.mean(position >= .012)),
            rotation_gate_failed_fraction=float(np.mean(rotation >= .12)),
            speed_gate_failed_fraction=float(np.mean(speed >= .025)),
            kinematic_gate_all_met_fraction=float(np.mean((position < .012) & (rotation < .12) & (speed < .025))),
            logged_ready_max_s=float(r['task_ready_s'][mask].max()),
            action=trace_stats(teacher['request'][mask]),
            filtered_action=trace_stats(chain['filtered_action'][mask]),
            yield_twist=trace_stats(chain['yield_twist'][mask]),
            physical_stage_summary=rollout['metrics']['stages'].get(str(int(stage))))
    # Last ten seconds contain no stage transition for these nine rollouts.
    tail = r['time'] >= r['time'][-1] - 10
    result = {k: audit[k] for k in ('eligible', 'failure_reasons', 'task', 'strict', 'contact',
               'rmse_m', 'peak_torque_nm', 'peak_speed_mps', 'penetration_mm', 'action_delta_rms',
               'completion_proxy_retreat_s', 'score', 'replay_max_abs', 'model_sha256', 'fixture_id')}
    result.update(final_stage=rollout['final_task_stage'], release_supported=rollout['release_supported'],
                  placement_complete=rollout['placement_complete'], max_lift_m=rollout['max_lift_m'],
                  abort_reason=rollout['abort_reason'], task_events=rollout['task_events'],
                  contact_evidence=audit['exposure'], event_stats=rollout['stats']['events'],
                  stages=stages, request_config=request['teacher'], seed=request['fixture']['seed'],
                  fixture_physical_sha256=request['fixture']['physical_config_sha256'],
                  last10s_action=trace_stats(teacher['request'][tail]),
                  last10s_filtered_action=trace_stats(chain['filtered_action'][tail]),
                  last10s_offset=trace_stats(teacher['offset'][tail]),
                  last10s_velocity=trace_stats(teacher['velocity'][tail]),
                  last10s_wbc_scale_range=[float(chain['wbc_scale'][tail].min()), float(chain['wbc_scale'][tail].max())],
                  final_hand=r['hand'][-1].tolist(), final_object_position=r['object_position'][-1].tolist(),
                  final_retreat_distance_m=float(np.linalg.norm(r['hand'][-1] - [.560, -.330, .670])),
                  final_destination_xy_distance_m=float(np.linalg.norm(r['object_position'][-1, :2] - np.asarray(rollout['placement_destination'])[:2])),
                  raw_hashes_verified=True, files_sha256=files, audit_sha256=sha(path / 'audit.json'),
                  rollout_trace_caveat='Stage and post-state are logged after physics; task error/ready fields were sampled pre-step. Transition samples must not be interpreted as exact gate evaluation replay. Contact support and load-transfer truth are not reconstructed here.')
    return result


def acquisition(design, history, decision):
    prefix = history[:5]
    seed = design.SEED + 100 + 5  # active_short category index 1, candidate 5
    pool = design.qmc.LatinHypercube(7, seed=seed).random(512)
    x = np.asarray([row['x'] for row in prefix])
    mean, std = design.posterior(x, [row['constraint'] for row in prefix], pool)
    feasible = [row for row in prefix if row['constraint'] <= 0]
    om, os = design.posterior([row['x'] for row in feasible], [row['score'] for row in feasible], pool)
    delta = min(row['score'] for row in feasible) - om
    z = delta / os
    ei = delta * design.ndtr(z) + os * np.exp(-z*z/2) / np.sqrt(2*np.pi)
    probability = design.ndtr(-mean/std)
    value = probability * (ei + .01 * os)
    distance = np.min(np.linalg.norm(pool[:, None] - x[None, :], axis=2), axis=1)
    value[distance < 1e-6] = -np.inf
    chosen = int(np.argmax(value))
    expected = np.asarray(decision['x'])
    exact = np.array_equal(expected, pool[chosen]) and np.array_equal(expected, design.propose(prefix, seed))
    if not exact:
        raise ValueError('Actual frozen candidate acquisition did not reproduce exactly')
    def describe(i):
        return dict(pool_index=int(i), x=pool[i].tolist(), constraint_mean=float(mean[i]),
                    constraint_std=float(std[i]), p_feasible=float(probability[i]),
                    objective_mean=float(om[i]), objective_std=float(os[i]), ei=float(ei[i]),
                    exploration_bonus=float(.01 * os[i]), acquisition=float(value[i]),
                    nearest_history_distance=float(distance[i]),
                    distance_to_c03=float(np.linalg.norm(pool[i] - x[3])),
                    distance_to_c04=float(np.linalg.norm(pool[i] - x[4])))
    return dict(seed=seed, history_count=5, feasible_history_count=len(feasible), pool_size=512,
                decision_reproduced_exactly=exact, selected=describe(chosen),
                top5=[describe(int(i)) for i in np.argsort(value)[-5:][::-1]],
                p_feasible_pool_range=[float(probability.min()), float(probability.max())],
                history_prefix=prefix,
                constraint_semantics='Categorical failure-count/label-count proxy, not measured physical violation magnitude.',
                limitation='Two feasible objective observations are insufficient to infer broad safe-region knowledge; one failed exploratory proposal is not evidence that BO generally fails.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError('Refusing to overwrite independent evidence')
    resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    sys.dont_write_bytecode = True
    source_manifest = read(args.run / 'source/archive_manifest.json')
    source_hashes = {name: sha(args.run / 'source' / name) for name in source_manifest}
    if source_hashes != source_manifest:
        raise ValueError('Frozen source manifest differs from actual source files')
    source = args.run / 'source/tools/teacher_bank_design_20260930.py'
    spec = importlib.util.spec_from_file_location('frozen_design', source)
    design = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(design)
    search = args.run / 'search/active_short/vmc'
    history = read(search / 'history.json')
    decision = read(search / 'c05/decision.json')
    report = dict(scope=__doc__, run=str(args.run.resolve()), host=platform.node(),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__),
                  script_sha256=sha(__file__), design_source_sha256=sha(source),
                  source_hashes_verified=True, source_files_sha256=source_hashes,
                  source_manifest_sha256=sha(args.run / 'source/archive_manifest.json'),
                  history_sha256=sha(search / 'history.json'), decision_sha256=sha(search / 'c05/decision.json'),
                  acquisition=acquisition(design, history, decision), candidates={}, no_dynamic_steps=True,
                  validation_read=False, causal_intervention_performed=False,
                  metric_provenance='Physical-substep RMSE, peak torque and peak speed are copied from existing frozen audit/rollout summaries; their raw files are hash-verified, but these three metrics are not independently recomputed in this diagnostic report.',
                  score_semantics='Frozen score=RMSE/0.05 + 0.3*torque_ratio + 0.1*retreat_time_proxy/55. Action delta RMS is a diagnostic, not part of this score. No rule or bank selection is changed.')
    for index in (3, 4, 5):
        candidate = f'c{index:02d}'
        config = design.decode(history[index]['x'])
        episodes = {str(anchor): episode(search / candidate / str(anchor)) for anchor in (0, 337, 671)}
        if any(item['request_config'] != config for item in episodes.values()):
            raise ValueError('Decoded controller differs from actual execution request')
        report['candidates'][candidate] = dict(history=history[index], decoded=config, episodes=episodes)
    report['paired_fixture_and_model_identity_verified'] = all(
        len({report['candidates'][c]['episodes'][str(a)][key] for c in ('c03', 'c04', 'c05')}) == 1
        for a in (0, 337, 671) for key in ('model_sha256', 'fixture_physical_sha256', 'seed'))
    report['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output), peak_rss_kib=report['peak_rss_kib'])))


if __name__ == '__main__':
    main()
