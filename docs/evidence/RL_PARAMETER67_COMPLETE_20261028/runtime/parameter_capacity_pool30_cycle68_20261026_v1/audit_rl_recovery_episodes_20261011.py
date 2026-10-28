"""Verify completed recovery episodes while learners keep running, no physics."""
import argparse
from pathlib import Path
import numpy as np
from office_v7_uniform24_20261008 import read, write, sha, now
from inspect_local_rl_progress_20261009 import inspect


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--names',nargs='+',default=['direct_office_task','parameter_impedance'],
                   help='Exact registered methods to inspect; defaults preserve the original two-lane audit')
    args=p.parse_args();assert not args.output.exists()
    registration=read(args.run_root/'REGISTRATION.json')
    protocol=read(Path(registration['parent_root'])/'PROTOCOL.json')
    reports=[]
    assert len(args.names)==len(set(args.names))
    assert set(args.names)<={j['name'] for j in registration['jobs']}
    for name in args.names:
        segment=args.run_root/(name+'_step165000')
        report=inspect(segment)
        assert report['episodes'], 'Wait for a fully saved first episode: '+name
        assert report['steps']>report['inherited_steps']
        assert report['complete_optimizer_rows_through_snapshot']>0
        original=read(segment/'execution.json')
        for row in report['episodes']:
            entry=next(r for r in original['rows'] if r['episode']==row['episode'])
            run=Path(entry['run']);audit=read(run/'AUDIT.json')
            assert sha(run/'rollout.npz')==entry['trace_sha256']==audit['trace_sha256']
            assert sha(run/'execution_chain.npz')==audit['chain_sha256']
            assert sha(run/'rollout.mjb')==audit['model_sha256']==protocol['formal_model_sha256']
            assert audit['training_policy_trace_consistency_max_abs']==0
            assert audit['common_filter_replay_max_abs']==0
            metrics=run/'rollout_metrics/substep_metrics.npz'
            assert sha(metrics)==audit['metrics_sha256']
            with np.load(metrics,allow_pickle=False) as data:
                dt=data['dt'].astype(float)
                np.testing.assert_allclose(dt,protocol['physics_dt_s'],rtol=0,atol=1e-12)
                error=data['error'].astype(float)
                rmse=1000*float(np.sqrt(np.sum(dt[:,None]*error**2)/dt.sum()))
                speed=float(np.linalg.norm(data['twist'][:,:3].astype(float),axis=1).max())
                torque=float(np.abs(data['qfrc_actuator'].astype(float)).max())
            np.testing.assert_allclose([rmse,torque,speed],
                [audit['rmse_mm'],audit['peak_torque_nm'],audit['peak_speed_mps']],rtol=1e-6,atol=1e-6)
            np.testing.assert_allclose(dt.sum(),audit['physical_seconds'],rtol=0,atol=1e-7)
            row['independent_metrics_passed']=True
            row['physical_steps']=len(dt)
        reports.append(report)
    value=dict(status='passed',created_utc=now(),registration_sha256=sha(args.run_root/'REGISTRATION.json'),
        source_sha256=sha(__file__),segments=reports,new_physics_steps=0,gradient_updates=0,final_test_reads=0,
        limitation='Training behavior audit, not frozen-policy development or convergence; no fixed actor replay claimed while weights update.')
    write(args.output,value)
    for report in reports:
        print(Path(report['segment']).name,report['steps'],len(report['episodes']),report['groups'])


if __name__=='__main__':main()
