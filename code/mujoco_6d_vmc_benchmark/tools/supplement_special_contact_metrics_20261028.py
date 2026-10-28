"""Read-only contact diagnostics required by the evaluation standard.

Run after the complete108 saved-evidence audit. Adds contact force and torque
excess integrals, without changing success, SPT, comfort or machine gates.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np
from prepare_special_frozen_test_20261028 import read, require, sha, write


def contact_integrals(run, row):
    require(sha(run/'rollout_metrics/substep_metrics.npz') == row['substep_metrics_sha256']
            and sha(run/'research_substeps.npz') == row['research_substeps_sha256'], 'Raw evidence changed')
    with np.load(run/'rollout_metrics/substep_metrics.npz', allow_pickle=False) as z:
        dt = z['dt'].astype(float)
        torque = np.abs(z['qfrc_actuator'][:, :7].astype(float))
    with np.load(run/'research_substeps.npz', allow_pickle=False) as z:
        force = z['contact_force_sum'][:, 2].astype(float)
    require(torque.shape == (len(dt),7) and force.shape == dt.shape, 'Substep alignment mismatch')
    require(np.isfinite(dt).all() and np.isfinite(torque).all() and np.isfinite(force).all(), 'Nonfinite evidence')
    require(np.allclose(dt, .00005, rtol=0, atol=1e-12), 'Wrong physical dt')
    threshold = np.asarray(row['comfort']['comfort_threshold_nm'], dtype=float)
    np.testing.assert_array_equal(threshold, [43.5]*4+[6.]*3)
    require(row['comfort']['human_force_threshold_n'] == .05, 'Changed contact threshold')
    contact = force > .05
    duration = float(dt[contact].sum())
    require(np.isclose(duration, row['comfort']['human_contact_duration_s'], rtol=1e-12, atol=1e-12), 'Contact duration mismatch')
    if not duration:
        require(row['comfort']['human_comfort_torque_compliance'] is None, 'No-contact comfort must be NA')
        return dict(contact_duration_s=0., contact_force_peak_n=None, contact_impulse_ns=None,
                    comfort_exceed_duration_s=None, excess_torque_integral_by_joint_nm_s=None,
                    max_joint_excess_integral_nm_s=None)
    contact_torque = torque[contact]
    time = dt[contact]
    exceeds = np.any(contact_torque > threshold*(1+1e-6), axis=1)
    exceeded = float(time[exceeds].sum())
    require(np.isclose(1-exceeded/duration, row['comfort']['human_comfort_torque_compliance'],
                       rtol=1e-10, atol=1e-10), 'Comfort denominator mismatch')
    excess = np.maximum(contact_torque-threshold, 0.)
    return dict(contact_duration_s=duration, contact_force_peak_n=float(force[contact].max()),
                contact_impulse_ns=float(np.sum(force[contact]*time)), comfort_exceed_duration_s=exceeded,
                excess_torque_integral_by_joint_nm_s=np.sum(excess*time[:,None], axis=0).tolist(),
                max_joint_excess_integral_nm_s=float(np.sum(excess.max(axis=1)*time)))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    require(not a.output.exists(), 'Preserve previous supplements')
    audit = read(a.audit)
    require(audit['status'] == 'frozen108_saved_evidence_audit_passed'
            and audit['verified_episodes'] == 108, 'Complete108 audit required')
    plan = read(Path(audit['preparation'])/'REGISTRATION.json')
    root = Path(plan['evaluation'])
    require(sha(root/'REPORT.json') == audit['report_sha256'], 'Changed report')
    require(sha(root/'INPUT_MODEL_LOCK.json') == audit['model_lock_sha256'], 'Changed model lock')
    report = read(root/'REPORT.json')
    require(report['status'] == 'complete' and len(report['rows']) == 108, 'Incomplete matrix')
    rows = []
    for row in report['rows']:
        expected = root/'evaluation'/(row['method']+'__'+row['condition'])
        require(Path(row['run']) == expected, 'Wrong episode source')
        rows.append(dict(method=row['method'], condition=row['condition'], **contact_integrals(expected,row)))
    methods = {}
    for name in sorted({r['method'] for r in rows}):
        all_rows = [r for r in rows if r['method']==name]
        contacted = [r for r in all_rows if r['contact_duration_s'] > 0]
        methods[name] = dict(episodes=len(all_rows), contact_episodes=len(contacted),
            contact_duration_s_total=sum(r['contact_duration_s'] for r in all_rows),
            contact_force_peak_n_max=max((r['contact_force_peak_n'] for r in contacted),default=None),
            contact_impulse_ns_total=sum(r['contact_impulse_ns'] for r in contacted) if contacted else None,
            comfort_exceed_duration_s_total=sum(r['comfort_exceed_duration_s'] for r in contacted) if contacted else None,
            excess_torque_integral_by_joint_nm_s_total=np.sum([r['excess_torque_integral_by_joint_nm_s'] for r in contacted],axis=0).tolist() if contacted else None,
            max_joint_excess_integral_nm_s_total=sum(r['max_joint_excess_integral_nm_s'] for r in contacted) if contacted else None)
    result = dict(status='complete108_contact_diagnostics', created_utc=datetime.now(timezone.utc).isoformat(),
        audit_sha256=sha(a.audit), report_sha256=audit['report_sha256'], script_sha256=sha(Path(__file__)),
        definitions=dict(contact='human_robot_sum > 0.05N; dt=5e-5',
            excess_by_joint='integral_contact max(abs(tau_j)-comfort_threshold_j,0) dt',
            max_joint_excess='integral_contact max_j max(abs(tau_j)-comfort_threshold_j,0) dt',
            exceed_duration='any joint > threshold*(1+1e-6), matching frozen comfort tolerance'),
        rows=rows, methods=methods,
        limitation='Descriptive saved-substep diagnostics; no new gate, no dynamics reintegration or human comfort calibration. No-contact measures stay NA. Original six metrics unchanged.')
    write(a.output,result)
    print(json.dumps(dict(status=result['status'],episodes=len(rows),output=str(a.output))))


if __name__ == '__main__':
    main()
