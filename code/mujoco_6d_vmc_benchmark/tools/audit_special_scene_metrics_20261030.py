"""Hash-bound special-scene telemetry audit; development previews stay labelled."""
import argparse
from pathlib import Path

import numpy as np

from audit_special_terminal_trace_20261029 import audit
from collect_special_scene_actions_20261028 import read, sha, write
from review_v9_paired_scene_closure_20261029 import verify_qualification
from special_scene_metrics_20261030 import completion_time


def episode(folder, method, condition):
    digest = sha(folder/'DEMONSTRATION_QUALIFICATION.json')
    q = verify_qualification(folder,digest)
    terminal = audit(folder)
    execution = read(folder/'execution.json')
    with np.load(folder/'substeps.npz',allow_pickle=False) as archive:
        raw = {k:archive[k].copy() for k in archive.files}
    assert raw['torque'].shape == raw['joint_velocity'].shape == (execution['substeps'],7)
    assert execution['substeps'] == execution['steps']*800
    assert execution['physics_dt_s'] == .00005
    assert all(np.isfinite(v).all() for v in raw.values()), 'Nonfinite telemetry requires explicit failed-episode handling'
    np.testing.assert_array_equal(raw['dt'],np.full(execution['substeps'],.00005))
    limits = np.asarray(execution['actuator_torque_limits_nm'])
    np.testing.assert_array_equal(limits,[87,87,87,87,12,12,12])
    peak = np.max(np.abs(raw['torque']),axis=0)
    np.testing.assert_array_equal(peak,q['metrics']['peak_torque_nm'])
    penetration = float(np.max(raw['external_penetration_m']))
    assert penetration == q['metrics']['max_external_penetration_m']
    machine = (execution['status']=='complete' and penetration<=.0002 and np.all(peak<=limits+1e-8))
    task = bool(q['task_success'])
    finish = completion_time(terminal['time'],terminal['terminal_gate']) if task else None
    assert not task or finish is not None, 'Original Task success lacks the preregistered sampled hold; preserve audit failure'
    contact = raw['disturbance_force_n']>.05
    # Static corner contact is not a human comfort proxy; only rod/ball are
    # labelled disturbance-contact proxies, never measured human comfort.
    if execution['scene']=='corner':
        contact[:] = False
    comfortable = np.all(np.abs(raw['torque'])<=.5*limits,axis=1)
    actor = read(folder/'INDEPENDENT_AUDIT.json')
    assert actor['status']=='passed', 'Actor replay infrastructure defect must be resolved separately'
    assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==digest
    return dict(method=method,condition=condition,scene=execution['scene'],task_success=task,
        strict_success=bool(task and machine and q['safety_valid'] and q['scene_contact_valid']),
        completion_time_s=finish,peak_torque_nm=float(peak.max()),peak_joint_torque_nm=peak.tolist(),
        peak_joint_velocity_radps=np.max(np.abs(raw['joint_velocity']),axis=0).tolist(),
        max_external_penetration_m=penetration,machine_compliant=bool(machine),human_contact_s=None,
        human_comfort=None,proxy_contact_s=float(np.sum(raw['dt'][contact])),
        proxy_below_threshold_s=float(np.sum(raw['dt'][contact & comfortable])),
        qualification_sha256=digest,terminal_trace_hashes=terminal['hashes'],
        completion_semantics='Final uninterrupted terminal suffix, confirmed at its 13th 25-Hz sample; 0.48s sampled span. No substep terminal-hold claim.',
        strict_semantics='special-scene task AND frozen safety AND required scenario contact/rod behavior; not office-placement Strict')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--method',required=True)
    p.add_argument('--condition',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    write(a.output,dict(status='development_preview_not_final_test',auditor_sha256=sha(Path(__file__)),
        row=episode(a.folder.resolve(),a.method,a.condition),final_test_performed=False))
