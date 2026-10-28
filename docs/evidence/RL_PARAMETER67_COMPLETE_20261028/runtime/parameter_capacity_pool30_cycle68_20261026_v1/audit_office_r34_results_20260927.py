"""Independently replay R34 and recompute time-weighted physical metrics."""
import hashlib
import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--campaign',default='outputs/esn_office_r34_stress_20260927')
    p.add_argument('--model',default='outputs/esn_office_resolved_stress_20260927/r34_half_gain/model.npz')
    p.add_argument('--plan',default='configs/esn_office_r34_stress_20260927.json')
    p.add_argument('--stem',default='R34_INDEPENDENT_AUDIT')
    args=p.parse_args()
    base = ROOT / args.campaign
    model = ROOT / args.model
    plan = ROOT / args.plan
    rows = []
    for job in json.loads(plan.read_text())['jobs']:
        folder = base / 'results' / job['id']
        result = json.loads((folder / 'rollout.json').read_text())
        assert result['neural_logging']['model_sha256'] == digest(model)
        assert result['model_sha256'] == digest(folder / 'rollout.mjb')
        actor = OfficeVMCMemoryESN(model)
        reset_actor = OfficeVMCMemoryESN(model)
        with np.load(folder / 'rollout.npz') as trace:
            actions, reset_actions, states = [], [], []
            for obs in trace['observation']:
                actions.append(actor.act(obs))
                states.append(actor.state.copy())
                reset_actor.reset()
                reset_actions.append(reset_actor.act(obs))
            actions = np.asarray(actions)
            action_error = float(np.max(np.abs(actions - trace['applied_action'])))
            state_error = float(np.max(np.abs(np.asarray(states) - trace['reservoir_state'])))
            assert action_error < 1e-10 and state_error < 1e-10
            memory_difference = float(np.sqrt(np.mean((actions - reset_actions) ** 2)))
        with np.load(folder / 'rollout_metrics/substep_metrics.npz') as raw:
            dt = raw['dt']
            error = raw['error'].astype(np.float64)
            rmse = float(np.sqrt(np.sum(error * error * dt[:, None]) / dt.sum()))
            speed = float(np.max(np.linalg.norm(raw['twist'][:, :3].astype(np.float64), axis=1)))
            torque = float(np.max(np.abs(raw['qfrc_actuator'])))
            assert abs(float(dt.sum()) - 55.) < 1e-7
            assert np.isfinite(error).all()
        recorded = result['metrics']
        np.testing.assert_allclose(
            [rmse, speed, torque],
            [recorded['position_rmse_3d_m'], recorded['linear_speed_peak_mps'],
             recorded['generalized_actuator_torque_peak_nm']], rtol=2e-7, atol=1e-8)
        rows.append(dict(case=job['id'], task=result['task_success'], strict=result['strict_success'],
                         action_replay_max_abs=action_error, reservoir_replay_max_abs=state_error,
                         offline_reset_action_rmse=memory_difference,
                         independent_rmse_m=rmse, independent_speed_peak_mps=speed,
                         independent_torque_peak_nm=torque,
                         files_sha256={str(p.relative_to(folder)): digest(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    report = dict(all_passed=True, episodes=len(rows), checkpoint_sha256=digest(model),
                  source_sha256=digest(Path(__file__)), plan_sha256=digest(plan), rows=rows,
                  memory_caveat='Reset comparison replays fixed observations offline. It establishes history-dependent actions, not a closed-loop benefit or a new task success rate.')
    (base / (args.stem+'.json')).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
    for row in rows:
        print(row['case'], 'replay_error', row['action_replay_max_abs'],
              'offline_memory_action_rmse', row['offline_reset_action_rmse'])


if __name__ == '__main__':
    main()
