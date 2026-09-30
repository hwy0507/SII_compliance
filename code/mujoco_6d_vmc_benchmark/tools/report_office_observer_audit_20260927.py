"""Validate unchanged trajectories and summarize observer calibration evidence."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]


def main():
    base=ROOT/'outputs/esn_office_observer_audit_20260927';rows=[]
    for condition in ('original','hard'):
        case=base/'results'/f'r34_{condition}_observer'
        reference=ROOT/'outputs/esn_office_r34_stress_20260927/results'/f'r34_{condition}'
        audit=json.loads((case/'observer_audit.json').read_text())
        result=json.loads((case/'rollout.json').read_text())
        old=json.loads((reference/'rollout.json').read_text())
        assert result['model_sha256']==old['model_sha256']
        assert result['source_sha256']==old['source_sha256']
        with np.load(case/'rollout.npz') as now,np.load(reference/'rollout.npz') as prior:
            assert set(now.files)==set(prior.files)
            for key in now.files:np.testing.assert_array_equal(now[key],prior[key],err_msg=key)
            observations=now['observation'];stage=now['stage'];time=now['time']
        with np.load(case/'observer_truth_sidecar.npz') as truth:
            np.testing.assert_allclose(truth['time'][:-1],time-.04,atol=1e-8,rtol=0)
            np.testing.assert_allclose(truth['estimated'][:-1],observations[:,32:39],atol=1e-10,rtol=0)
            wrench_error=observations[:,39:45]-truth['contact_wrench'][:-1]
            by_stage={}
            for index in sorted(set(stage)):
                mask=stage==index
                by_stage[str(index)]=dict(samples=int(mask.sum()),
                    force_error_norm_rmse_n=float(np.sqrt(np.mean(np.sum(wrench_error[mask,:3]**2,axis=1)))),
                    moment_error_norm_rmse_nm=float(np.sqrt(np.mean(np.sum(wrench_error[mask,3:]**2,axis=1)))),
                    force_bias_n=wrench_error[mask,:3].mean(axis=0).tolist())
        rows.append(dict(condition=condition,all_saved_trajectory_arrays_exact_match=True,
            task=result['task_success'],strict=result['strict_success'],
            observer_reconstruction_max_abs_nm=audit['observer_reconstruction_max_abs_nm'],
            physical_substep_joint_audit=audit['bins'],policy_sample_wrench_error=by_stage,
            hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                    (case/'observer_audit.json',case/'observer_truth_sidecar.npz',case/'rollout.json',case/'rollout.npz')}))
    report=dict(complete=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),rows=rows,
                caveats=['Contact truth includes carried payload.',
                         'Truth is offline audit only; equivalence does not authorize truth as an actor input.',
                         'Force inference is a least-squares equivalent tool wrench, not contact localization.',
                         'Stage labels index post-step saved state while observations precede the step; one transition sample can straddle stages.',
                         'RMSE decomposition terms are correlated; do not add their magnitudes.'])
    (base/'OBSERVER_AUDIT_RESULTS.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Pure-proprioception observer audit','',
           'Both full logged trajectories match the frozen R34 results exactly. Truth is offline only.','',
           '| Condition | Stage | Joint error RMS norm Nm | Dynamics term Nm | Friction term Nm | Equivalent force error RMS N |',
           '|---|---|---:|---:|---:|---:|']
    for row in rows:
        for index,wrench in row['policy_sample_wrench_error'].items():
            joint=row['physical_substep_joint_audit']['stage_'+index]
            values=[np.linalg.norm(joint[key]) for key in ('error_rmse_nm','dynamics_rmse_nm','friction_rmse_nm')]
            lines.append(f"| {row['condition']} | {index} | {values[0]:.6f} | {values[1]:.6f} | {values[2]:.6f} | {wrench['force_error_norm_rmse_n']:.6f} |")
    lines+=['',*report['caveats']]
    (base/'OBSERVER_AUDIT_RESULTS.md').write_text('\n'.join(lines)+'\n');print('\n'.join(lines))


if __name__=='__main__':main()
