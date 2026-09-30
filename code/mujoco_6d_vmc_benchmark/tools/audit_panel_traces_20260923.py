"""Recompute sampled metrics and stage summaries from frozen rollout traces."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def audit(root: Path, final: dict) -> list[dict]:
    rows = []
    for row in final['rows']:
        if 'execution_error' in row:
            rows.append(dict(method=row['method'], fixture=row['fixture'], execution_error=row['execution_error']))
            continue
        candidates = [root / row['method'] / str(row['fixture']['seed']) / 'rollout.npz']
        if len({r['method'] for r in final['rows']}) == 1:
            candidates.append(root / str(row['fixture']['seed']) / 'rollout.npz')
        existing = [p for p in candidates if p.exists()]
        if len(existing) != 1:
            raise ValueError(f'Missing or ambiguous trace for {row["method"]}/{row["fixture"]["seed"]}')
        source = existing[0]
        with np.load(source, allow_pickle=False) as z:
            time, stage = z['time'], z['stage']
            error = z['position'] - z['target']
            speed = np.linalg.norm(z['twist'][:, :3], axis=1)
            torque = z['torque']
        if not len(time) or any(not np.isfinite(x).all() for x in (time, stage, error, speed, torque)):
            raise ValueError(f'Empty/nonfinite trace: {source}')
        if len(time) > 1 and not np.allclose(np.diff(time), .04, atol=1e-8, rtol=0):
            raise ValueError(f'Unexpected sample spacing: {source}')

        def window(mask):
            if not np.any(mask):
                return None
            xyz = np.sqrt(np.mean(error[mask] ** 2, axis=0))
            return dict(samples=int(mask.sum()), start_s=float(time[mask][0]), end_s=float(time[mask][-1]),
                        rmse_3d_m=float(np.linalg.norm(xyz)), rmse_xyz_m=xyz.tolist(),
                        speed_peak_25hz_mps=float(speed[mask].max()),
                        speed_p95_25hz_mps=float(np.percentile(speed[mask], 95)),
                        actuator_torque_peak_25hz_nm=float(np.abs(torque[mask]).max()))

        whole = window(np.ones(len(time), dtype=bool))
        if not np.isclose(whole['rmse_3d_m'], row['tracking_rmse_3d_m'], atol=1e-12, rtol=0):
            raise ValueError(f'RMSE differs from reported result: {source}')
        if not np.isclose(whole['speed_peak_25hz_mps'], row['speed_peak_25hz_mps'], atol=1e-12, rtol=0):
            raise ValueError(f'Speed differs from reported result: {source}')
        rows.append(dict(method=row['method'], fixture=row['fixture'], trace=str(source),
                         trace_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                         whole=whole,
                         stages={str(int(s)): window(stage == s) for s in np.unique(stage)},
                         final_stage=int(stage[-1]),
                         actual_actuator_peak_is_sampled=True))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--traces', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = audit(args.traces, json.loads(args.result.read_text()))
    result = dict(scope='25 Hz recorded samples; not a reconstruction of unsaved physics substeps',
                  stage_names={'0': 'approach', '1': 'align to grasp', '2': 'close gripper', '3': 'loaded lift'},
                  rows=rows, result_sha256=hashlib.sha256(args.result.read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(f'Verified {len(rows)} rollout traces and generated per-stage metrics')


if __name__ == '__main__':
    main()
