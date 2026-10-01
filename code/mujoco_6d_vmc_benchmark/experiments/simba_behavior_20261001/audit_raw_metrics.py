"""Independently recompute metrics from completed evaluations; never run physics."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def recompute(z):
    dt = np.asarray(z['dt'], dtype=np.float64)
    error = np.asarray(z['error'], dtype=np.float64)
    velocity = np.asarray(z['twist'][:, :3], dtype=np.float64)
    torque = np.asarray(z['qfrc_actuator'], dtype=np.float64)
    times = np.asarray(z['time'], dtype=np.float64)
    arrays = (dt, error, velocity, torque, times)
    if not len(dt) or any(len(a) != len(dt) or not np.isfinite(a).all() for a in arrays):
        raise ValueError('empty, nonfinite or inconsistent raw arrays')
    if not np.all(dt > 0) or not np.allclose(np.diff(times, prepend=0.), dt, atol=1e-8, rtol=1e-6):
        raise ValueError('invalid physical time progression')
    return dict(position_rmse_3d_m=float(np.sqrt(np.sum(np.sum(error**2, axis=1)*dt)/dt.sum())),
                generalized_actuator_torque_peak_nm=float(np.abs(torque).max()),
                linear_speed_peak_mps=float(np.linalg.norm(velocity, axis=1).max()),
                generalized_actuator_torque_peak_by_joint_nm=np.abs(torque).max(axis=0).tolist(),
                duration_s=float(dt.sum()), samples=len(dt),
                full55=bool(abs(float(dt.sum())-55.) < 1e-6))


def audit(campaign):
    rows, skipped = [], []
    tolerances = dict(position_rmse_3d_m=1e-6, generalized_actuator_torque_peak_nm=1e-4,
                      linear_speed_peak_mps=1e-6)
    summaries = sorted((campaign/'evaluation').glob('*/SUMMARY.json'))
    for summary in summaries:
        s = json.loads(summary.read_text())
        if s.get('status') != 'complete':
            skipped.append(str(summary))
            continue
        for source in s['rows']:
            raw_path = Path(source['raw_result'])
            raw = json.loads(raw_path.read_text())
            npz = raw_path.parent/(raw_path.stem+'_metrics')/'substep_metrics.npz'
            row = dict(run=summary.parent.name, case=source['case']['id'], raw=str(raw_path),
                       physical_valid=raw.get('physical_valid'), abort_reason=raw.get('abort_reason'))
            try:
                with np.load(npz, allow_pickle=False) as z:
                    values = recompute(z)
                metric = raw['metrics']
                delta = {k: abs(values[k]-float(metric[k])) for k in tolerances}
                joint_delta = float(np.max(np.abs(np.array(values['generalized_actuator_torque_peak_by_joint_nm'])-
                    np.array(metric['generalized_actuator_torque_peak_by_joint_nm']))))
                ok = (all(delta[k] <= tolerances[k] for k in tolerances) and joint_delta <= 1e-4
                      and values['samples'] == metric['samples']
                      and values['full55'] == bool(raw['full_task_horizon_completed']))
                row.update(pass_audit=ok, recomputed=values, absolute_difference=delta,
                           max_joint_torque_difference_nm=joint_delta, raw_sha256=sha(raw_path),
                           substep_sha256=sha(npz))
            except (KeyError, ValueError, OSError) as exc:
                row.update(pass_audit=False, error=str(exc))
            rows.append(row)
    return dict(created_utc=datetime.now(timezone.utc).isoformat(), campaign=str(campaign),
                scope='completed evaluation summaries only; physics validity is separate from metric agreement',
                all54_present=len(rows)==54 and not skipped, rows_audited=len(rows),
                all_observed_pass=bool(rows) and all(r['pass_audit'] for r in rows),
                skipped_incomplete=skipped, tolerances=tolerances, rows=rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.campaign)
    output = args.campaign/'report'/'RAW_METRICS_AUDIT.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'rows'}))
    raise SystemExit(0 if result['all_observed_pass'] else 2)
