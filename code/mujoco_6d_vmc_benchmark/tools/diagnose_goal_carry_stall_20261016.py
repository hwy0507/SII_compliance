"""Diagnose closed TRAINING carry traces, without simulation or final acceptance.

Use the previous post-step hand position with the current pre-step observation.
This is waypoint/gate bookkeeping, not a controller causality experiment.
The planner updates BEFORE recording this observation: a reached intermediate
waypoint may already have been replaced. Zero sampled readiness alone is not
evidence of zero waypoint progress.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np


SUPPORTED_SOURCE = {
    'scripts/office_task_v4_20260917.py': '255ce3443ecfb46d4e88797f3b5bb78a864c089e395c097aa86e203533852d0f',
    'scripts/planned_hand_corner_20261002.py': '60fc1bc868a04e5a8e27c887b91a9ba4ffeaed6cd073379be589780d59fcabd5',
    'scripts/validate_office_apparatus_v5_20260917.py': '76ed25f77c7c32452121382b1f5a766f1b553af62802a1afb7000b3bd029ebe0',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def summarize(values):
    return dict(min=np.min(values, axis=0).tolist(),
                median=np.median(values, axis=0).tolist(),
                max=np.max(values, axis=0).tolist())


def waypoint_evidence(hand_before, error, route, lateral_rejoin):
    target = hand_before + error
    distances = np.linalg.norm(target[:, None, :] - route[None, :, :], axis=2)
    cursor = distances.argmin(axis=1)
    residual = distances.min(axis=1)
    if not np.all(residual < 1e-8):
        raise ValueError('Pre/post alignment or reference target differs from frozen route')
    radius_ready = np.linalg.norm(error, axis=1) < .012
    plane_ready = np.zeros(len(cursor), dtype=bool)
    forward = np.full(len(cursor), np.nan)
    lateral = forward.copy()
    for i, j in enumerate(cursor):
        if 0 < j < len(route)-1:
            tangent = route[j] - route[j-1]
            length = np.linalg.norm(tangent)
            if length > 1e-8:
                tangent /= length
                displacement = -error[i]
                forward[i] = displacement @ tangent
                lateral[i] = np.linalg.norm(displacement-forward[i]*tangent)
                plane_ready[i] = lateral_rejoin and forward[i] >= 0 and lateral[i] < .08
    finite = np.isfinite(forward)
    indices, counts = np.unique(cursor, return_counts=True)
    return dict(cursor_counts={str(int(k)): int(v) for k, v in zip(indices, counts)},
                cursor_first=int(cursor[0]), cursor_last=int(cursor[-1]),
                observed_cursor_increases=int((np.diff(cursor)>0).sum()),
                observed_cursor_decreases=int((np.diff(cursor)<0).sum()),
                sampled_cursor_unchanged=bool(np.all(cursor==cursor[0])),
                route_length=len(route), target_match_max_m=float(residual.max()),
                radius_ready_count=int(radius_ready.sum()),
                rejoin_plane_ready_count=int(plane_ready.sum()),
                position_or_rejoin_ready_count=int((radius_ready | plane_ready).sum()),
                forward_m=summarize(forward[finite]) if finite.any() else None,
                lateral_m=summarize(lateral[finite]) if finite.any() else None)


def diagnose(episode, tail_seconds=10.):
    episode = Path(episode)
    execution = json.loads((episode/'execution.json').read_text())
    if any(execution['source_sha256'].get(k) != v for k, v in SUPPORTED_SOURCE.items()):
        raise ValueError('Unsupported planner/gate/observation source version')
    audit = json.loads((episode/'AUDIT.json').read_text())
    if not execution.get('ended_utc') or not audit.get('training') or not audit.get('full_horizon'):
        raise ValueError('Only closed full-horizon training episodes supported')
    plan = json.loads((episode/'rollout.plan.json').read_text())
    with np.load(episode/'rollout.npz', allow_pickle=False) as z:
        # row i observation is BEFORE its action, hand[i] is AFTER it.
        mask = z['neuron_time'][1:] >= z['time'][-1]-tail_seconds-1e-8
        if not mask.any() or not np.all(z['stage'][1:][mask] == 4):
            raise ValueError('Tail must remain in carry')
        if not np.allclose(z['neuron_time'][1:], z['time'][:-1], atol=1e-8, rtol=0):
            raise ValueError('Trace time alignment mismatch')
        error = z['observation'][1:, 20:23][mask]
        if not np.allclose(np.linalg.norm(error, axis=1),
                           z['task_position_error_m'][1:][mask], atol=1e-10, rtol=0):
            raise ValueError('Canonical observation/error scalar mismatch')
        route = np.array([r['hand'] for r in plan['routes']['4']])
        result = waypoint_evidence(z['hand'][:-1][mask], error, route,
                                   plan['allow_lateral_rejoin'])
        result.update(samples=int(mask.sum()),
                      observation_order='After planner update, before action/physics; reached intermediate waypoint may already be replaced.',
                      readiness_scope='Sampled current target only; zero readiness does not imply zero progress. Intermediate waypoint advancement uses position/rejoin and rotation, without the final-stage speed/dwell requirement.',
                      position_error_m=summarize(np.linalg.norm(error, axis=1)),
                      rotation_error_rad=summarize(z['task_rotation_error_rad'][1:][mask]),
                      speed_mps=summarize(z['task_speed_mps'][1:][mask]),
                      task_ready_s=summarize(z['task_ready_s'][1:][mask]),
                      rotation_ready_count=int((z['task_rotation_error_rad'][1:][mask] < .12).sum()),
                      speed_ready_count=int((z['task_speed_mps'][1:][mask] < .025).sum()))
    with np.load(episode/'parameter_actions.npz', allow_pickle=False) as z:
        result['applied_parameters'] = summarize(z['parameters'][1:][mask])
        result['energy_scale'] = summarize(z['energy_scale'][1:][mask])
    names = ['execution.json', 'AUDIT.json', 'rollout.npz', 'rollout.plan.json',
             'parameter_actions.npz', 'CONTROLLER_FULLRANGE.json']
    return dict(episode=str(episode.resolve()), tail_seconds=tail_seconds,
                input_sha256={name: sha(episode/name) for name in names},
                native_training_audit=audit, evidence=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = dict(schema='sii-goal-training-carry-diagnostic-v1',
                   created_utc=datetime.now(timezone.utc).isoformat(),
                   scope='Closed training traces only; no final acceptance or physics replay',
                   limitations=['25Hz samples do not prove every physics substep gate state.',
                                'Planner updates precede observations; zero sampled readiness cannot establish no waypoint advancement.',
                                'Waypoint blockage does not establish controller cause or a successful fix.',
                                'Do not relax the frozen gate based on this diagnostic.'],
                   script_sha256=sha(__file__), episodes=[diagnose(p) for p in args.episode])
    with args.output.open('x') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(receipt, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
