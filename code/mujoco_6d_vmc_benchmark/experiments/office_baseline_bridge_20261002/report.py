"""Independent office metric audit and event/parameter diagnostics from saved data."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
def audit(prefix,output):
    summary=json.loads(prefix.with_suffix('.json').read_text())
    with np.load(prefix.parent/(prefix.name+'_metrics/substep_metrics.npz')) as raw:
        t=raw['time'];dt=raw['dt'];error=raw['error'].astype(float);twist=raw['twist'].astype(float);torque=raw['qfrc_actuator'].astype(float);stage=raw['stage']
    assert all(np.isfinite(v).all() for v in [t,dt,error,twist,torque])
    model_hash=hashlib.sha256(prefix.with_suffix('.mjb').read_bytes()).hexdigest()
    assert model_hash==summary['model_sha256']
    values=dict(position_rmse_3d_m=float(np.sqrt(np.sum(error**2*dt[:,None])/dt.sum())),generalized_actuator_torque_peak_nm=float(abs(torque).max()),linear_speed_peak_mps=float(np.linalg.norm(twist[:,:3],axis=1).max()))
    differences={k:abs(v-summary['metrics'][k]) for k,v in values.items()}
    assert differences['position_rmse_3d_m']<1e-5 and differences['generalized_actuator_torque_peak_nm']<1e-5 and differences['linear_speed_peak_mps']<1e-7,differences
    windows={}
    for name,start,end in [('ball_and_early_task',2.,3.),('human',3.,10.),('rod',12.,25.5),('late_task',25.5,55.)]:
        mask=(t>start)&(t<=end+1e-8)
        if not mask.any():windows[name]=None;continue
        windows[name]=dict(duration_s=float(dt[mask].sum()),rmse_mm=float(np.sqrt(np.sum(error[mask]**2*dt[mask,None])/dt[mask].sum())*1000),peak_torque_nm=float(abs(torque[mask]).max()),peak_speed_mps=float(np.linalg.norm(twist[mask,:3],axis=1).max()),stage_min=int(stage[mask].min()),stage_max=int(stage[mask].max()))
    output.mkdir(parents=True,exist_ok=True)
    result=dict(source=str(prefix),model_sha256=model_hash,task_success=summary['task_success'],strict_success=summary['strict_success'],full_horizon=summary['full_task_horizon_completed'],stage=summary['final_task_stage'],duration_s=float(dt.sum()),native_substeps=len(dt),recomputed_metrics=values,absolute_error_vs_online= differences,external_penetration_m_from_online_contacts=summary['stats']['max_external_penetration_m'],abort_reason=summary['abort_reason'],contacts=summary['stats']['events'],windows=windows,limitations=['Fixed event windows are diagnostic, not contact admission or a replacement task gate.','Window displacement includes nominal task motion; it is not a causal compliance response without a paired no-event control.','All-event nominal baseline still has disturbances and unknown edge; it is not the clear-task feasibility control.','Native raw metric vectors use float32, online accumulators float64; the audit uses declared numerical tolerances.'])
    (output/'OFFICE_AUDIT.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    # Physical-time bins keep extrema instead of skipping a short force/velocity peak.
    bins=np.floor((t-1e-9)/.04).astype(int);starts=np.r_[0,np.flatnonzero(np.diff(bins))+1];ends=np.r_[starts[1:]-1,len(t)-1]
    times=t[ends]
    series=[np.linalg.norm(error,axis=1)*1000,np.linalg.norm(twist[:,:3],axis=1),abs(torque).max(axis=1)]
    fig,axes=plt.subplots(4,1,figsize=(11,9),sharex=True,layout='constrained')
    for ax,y,label in zip(axes[:3],series,['Position error (mm)','Hand speed (m/s)','Peak joint torque (Nm)']):
        ax.plot(times,np.maximum.reduceat(y,starts),lw=1.,color='#286a87');ax.set_ylabel(label)
    axes[3].step(t[::400],stage[::400],where='post',color='#a16239');axes[3].set_ylabel('Task stage');axes[3].set_xlabel('Physical time (s)')
    for ax in axes:
        ax.axvline(2,color='#a53c3c',ls=':',alpha=.7)
        ax.axvspan(3,10,color='#d8ad51',alpha=.12);ax.axvspan(12,25.5,color='#69a89d',alpha=.12);ax.grid(alpha=.18)
    fig.suptitle(f'{summary.get("controller","Office")}\nTask={summary["task_success"]}, strict={summary["strict_success"]}; first three panels use 40 ms maxima')
    fig.savefig(output/'office_diagnostics.png',dpi=160);fig.savefig(output/'office_diagnostics.pdf');plt.close(fig)
    params=prefix.parent/'parameter_actions.npz'
    if params.exists():
        z=np.load(params);trace=np.load(prefix.with_suffix('.npz'));time=trace['neuron_time'];pri=np.asarray(summary['baseline_policy']['parameters']['prior']);keys=summary['baseline_policy']['parameters']['parameter_keys']
        assert len(time)==len(z['parameters'])
        fig,ax=plt.subplots(2,1,figsize=(11,6),sharex=True,layout='constrained')
        for i,key in enumerate(keys):ax[0].plot(time,z['parameters'][:,i]/pri[i],label=key,lw=1.)
        ax[0].axhline(1,color='0.4',ls='--',lw=.8);ax[0].set_ylabel('Parameter / shared prior');ax[0].legend(ncol=3,fontsize=8)
        ax[1].plot(time,z['tank'],color='#306f86');ax[1].axhline(.08,color='#a54444',ls='--');ax[1].set_ylabel('Local budget (J)');ax[1].set_xlabel('Physical time (s)')
        for a in ax:a.grid(alpha=.2)
        fig.suptitle('Online parameter adaptation; local storage budget is not a global passivity certificate')
        fig.savefig(output/'parameter_diagnostics.png',dpi=160);fig.savefig(output/'parameter_diagnostics.pdf');plt.close(fig)
    print(json.dumps(dict(output=str(output),task=result['task_success'],strict=result['strict_success'],duration=result['duration_s'],metric_errors=differences)))
def main():
    p=argparse.ArgumentParser();p.add_argument('--prefix',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.prefix,a.output)
if __name__=='__main__':main()
