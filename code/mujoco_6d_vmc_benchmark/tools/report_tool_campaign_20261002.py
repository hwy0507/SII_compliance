"""Read completed rows only; independently recompute three physical metrics."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha,write,now,EXPECTED_MJB
from run_benchmark import CONTROL_DT,TORQUE_LIMITS
from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--batch',help='Explicit immediate child containing physical runs; startup/training records remain separate')
    args=p.parse_args();rows=[];pending=[];verified_sources=set()
    if args.batch and (Path(args.batch).name!=args.batch or args.batch in ('.','..')):
        raise ValueError('Batch must be an immediate child directory name')
    paths=(args.root/args.batch).glob('*/execution.json') if args.batch else args.root.glob('*/*/execution.json')
    for state_path in sorted(paths):
        run=state_path.parent;state=json.loads(state_path.read_text())
        recovered=(run/'RECOVERY_AUDIT.json').is_file()
        if (state.get('status')!='complete' and not recovered) or not (run/'AUDIT.json').exists():
            pending.append(dict(run=str(run),status=state.get('status')));continue
        summary=json.loads((run/'rollout.json').read_text());row=json.loads((run/'AUDIT.json').read_text())
        source_root=run.parent/'source'
        source_key=(str(source_root),tuple(sorted(state['source_sha256'].items())))
        if source_key not in verified_sources:
            for relative,digest in state['source_sha256'].items():
                if sha(source_root/relative)!=digest:raise ValueError('Frozen source differs: '+str(source_root/relative))
            verified_sources.add(source_key)
        row['frozen_source_hashes_verified']=True
        config=state.get('action_filter_config')
        if config is None:
            constructor=run.parent/'source/scripts/run_contact_transfer_20260916.py'
            assert sha(constructor)==state['source_sha256']['scripts/run_contact_transfer_20260916.py']
            assert 'safety_config=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)' in constructor.read_text()
            config=asdict(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
            row['filter_config_provenance']='Reconstructed from hash-verified frozen constructor for older metadata; full chain replay required'
        else:row['filter_config_provenance']='Recorded execution configuration; full chain replay required'
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            dt=z['dt'].astype(float);error=z['error'].astype(float)
            for key in ('dt','error','twist','qfrc_actuator'):
                if not np.isfinite(z[key]).all():raise ValueError('Nonfinite physical samples: '+str(run))
            if np.any(dt<=0):raise ValueError('Nonpositive physical timestep')
            energy=np.sum(error**2,axis=1)*dt;speed=np.linalg.norm(z['twist'][:,:3].astype(float),axis=1)
            torque=np.max(np.abs(z['qfrc_actuator']),axis=1);time=np.cumsum(dt)
            values=[float(np.sqrt(energy.sum()/dt.sum())*1000),float(torque.max()),float(speed.max())]
            np.testing.assert_allclose(values,[row[k] for k in ['rmse_mm','peak_torque_nm','peak_speed_mps']],rtol=0,atol=1e-8)
            row.update(error_integral_m2_s=float(energy.sum()),peak_speed_time_s=float(time[np.argmax(speed)]),
                       peak_torque_time_s=float(time[np.argmax(torque)]))
            delta=np.abs(np.diff(z['qfrc_actuator'].astype(float),axis=0))
            rates=np.asarray(config['maximum_torque_rate_nmps'])
            peak_delta=delta.max(0)
            valid=bool(np.all(peak_delta<=rates*CONTROL_DT+2e-5) and np.all(np.max(abs(z['qfrc_actuator']),axis=0)<=TORQUE_LIMITS+1e-5))
            if not valid:raise ValueError('Actuator bound/slew failed: '+str(run))
            changes=np.flatnonzero(np.any(delta>1e-5,axis=1))+1
            if len(changes)>1 and np.min(np.diff(changes))<round(CONTROL_DT/float(dt[0])):
                raise ValueError('Unexpected torque updates between 4ms servo periods')
            row.update(actuator_amplitude_and_command_slew_valid=True,
                       command_torque_rate_peak_nmps=(peak_delta/CONTROL_DT).tolist(),
                       slew_semantics='Torque-command changes divided by frozen 4ms servo update, not by 100us zero-order-hold physical sampling')
        with np.load(run/'execution_chain.npz') as z:
            filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(**config))
            for a,y,s in zip(z['requested_action'],z['yield_twist'],z['wbc_scale']):
                f=filt.filter(a,.04);np.testing.assert_array_equal(f.cartesian_yield_twist,y)
                if f.wbc_scale!=s:raise ValueError('Common filter replay mismatch')
            row['common_filter_replay_max_abs']=0.
        assert sha(run/'rollout.mjb')==row['model_sha256']==summary['model_sha256']==EXPECTED_MJB
        assert sha(run/'rollout.npz')==row['trace_sha256']
        assert sha(run/'config.json')==state['config_sha256']
        assert sha(run/'execution_chain.npz')==row['chain_sha256']
        assert sha(run/'rollout_metrics/substep_metrics.npz')==row['metrics_sha256']
        if state.get('checkpoint_sha256'):
            assert sha(run/'checkpoint.npz')==state['checkpoint_sha256']
        contact_path=run/'independent_contacts.npz'
        row['independent_contact_sidecar_available']=contact_path.exists()
        if contact_path.exists():
            with np.load(contact_path) as z:
                values=[float(z[k].max()*1000) for k in ('external_penetration_m','edge_penetration_m')]
                if not all(np.isfinite(z[k]).all() for k in z.files):raise ValueError('Nonfinite contact sidecar')
                assert len(z['time'])==len(dt)
            np.testing.assert_allclose(values,[row['penetration_mm'],row['edge_penetration_mm']],rtol=0,atol=1e-10)
            assert sha(contact_path)==state['independent_contact_audit']['sha256']
            row['independent_contact_sidecar_verified']=True
        row.update(run=str(run.resolve()),checkpoint_sha256=state.get('checkpoint_sha256'),config=state['config'],
                   audit_sha256=sha(run/'AUDIT.json'),completed_utc=state.get('ended_utc'),
                   metadata_write_recovery=recovered,
                   failure_reason=None if row['task_success'] else 'No stable released placement; terminal stage '+row['stage'],
                   contact_events=summary['stats']['events'],
                   unexpected_edge=summary['stats']['unexpected_edge'],
                   rod_longest_run=summary['stats'].get('contact_diagnostics',{}).get('rod_longest_run'))
        rows.append(row)
    valid=[r for r in rows if r['strict_success']]
    pareto=[r['run'] for r in valid if not any(
        s['rmse_mm']<=r['rmse_mm'] and s['peak_torque_nm']<=r['peak_torque_nm'] and
        (s['rmse_mm']<r['rmse_mm'] or s['peak_torque_nm']<r['peak_torque_nm']) for s in valid)]
    write(args.output,dict(created_utc=now(),rows=rows,pending=pending,strict_pareto_rmse_torque=pareto,
                          selected_batch=args.batch,source_sha256=sha(Path(__file__)),
                          limitation='Fixed seen-world development; unfinished/failed rows are retained; speed remains a safety/report quantity, not a positive reward'))
    print(json.dumps(dict(completed=len(rows),pending=len(pending),task=sum(r['task_success'] for r in rows),strict=len(valid)),indent=2))

if __name__=='__main__':main()
