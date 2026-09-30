"""Independent replay and physical-metric audit for balanced DAgger5."""
import argparse, hashlib, json, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(ROOT / 'scripts'))
    from current_student_policy_20260921 import load_current
    rows = []
    for folder in sorted(ROOT.glob('results/dagger5_balanced_*')):
        rp, tp, mp = folder/'rollout.json', folder/'rollout.npz', folder/'rollout_metrics'/'substep_metrics.npz'
        if not (rp.exists() and tp.exists() and mp.exists()):
            continue
        result = json.loads(rp.read_text())
        actor = load_current(args.model)
        with np.load(tp, allow_pickle=False) as trace:
            actions = np.asarray([actor.act(obs) for obs in trace['observation']])
            saved = trace['applied_action']
            action_error = float(np.max(np.abs(actions - saved)))
            saved_state = trace['reservoir_state']
            actor = load_current(args.model)
            replay_state = []
            for obs in trace['observation']:
                actor.act(obs)
                replay_state.append(actor.obj.state.copy())
            state_error = float(np.max(np.abs(np.asarray(replay_state) - saved_state)))
            steps = len(actions)
        with np.load(mp, allow_pickle=False) as metrics:
            dt = metrics['dt'].astype(np.float64)
            err = metrics['error'].astype(np.float64)
            rmse = float(np.sqrt(np.sum(err * err * dt[:, None]) / dt.sum()))
            speed = float(np.max(np.linalg.norm(metrics['twist'][:, :3], axis=1)))
            torque = float(np.max(np.abs(metrics['qfrc_actuator'])))
        np.testing.assert_allclose([rmse, speed, torque],
            [result['metrics']['position_rmse_3d_m'], result['metrics']['linear_speed_peak_mps'], result['metrics']['generalized_actuator_torque_peak_nm']],
            rtol=2e-7, atol=1e-8)
        if action_error >= 1e-10 or state_error >= 1e-10:
            raise AssertionError(f'replay mismatch: {folder}')
        rows.append(dict(case=folder.name, task=bool(result['task_success']), strict=bool(result['strict_success']),
            waypoint_rmse_mm=1000*rmse, peak_torque_nm=torque, peak_speed_mps=speed,
            penetration_mm=1000*result['stats']['max_external_penetration_m'],
            replay_max_abs=action_error, state_replay_max_abs=state_error, steps=steps,
            source_sha256=result['source_sha256'], files_sha256={str(p.relative_to(folder)): sha(p) for p in sorted(folder.rglob('*')) if p.is_file()}))
    report = dict(candidate_sha256=sha(args.model), episodes=len(rows), task_successes=sum(r['task'] for r in rows),
        strict_successes=sum(r['strict'] for r in rows), rows=rows,
        caveats=['Development dt=1e-4 only; no formal dt=5e-5 result.', 'Pure ESN, hybrid_vmc_blend=0; canonical48D actor input.', 'No gate, environment, actuator limit, or failure filtering changed.'])
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output/'ESN_JOINT_AUDIT.json').write_text(json.dumps(report, indent=2)+'\n')
    lines=['# Balanced DAgger5 ESN audit','', '| case | task | strict | RMSE mm | peak torque Nm | peak speed m/s | penetration mm | action replay | state replay |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['case']} | {r['task']} | {r['strict']} | {r['waypoint_rmse_mm']:.3f} | {r['peak_torque_nm']:.3f} | {r['peak_speed_mps']:.6f} | {r['penetration_mm']:.6f} | {r['replay_max_abs']:.1e} | {r['state_replay_max_abs']:.1e} |")
    lines += ['', f"Task {report['task_successes']}/{report['episodes']}; strict {report['strict_successes']}/{report['episodes']}.", 'Independent action/reservoir replay and physical substep recomputation passed.']
    (args.output/'ESN_JOINT_RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('\n'.join(lines))

if __name__ == '__main__':
    main()
