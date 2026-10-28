"""Audit a same-tick control fix and diagnose impact memory without new physics."""
import hashlib,json,sys,tarfile
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
OUT=ROOT/'outputs/original_esn_rod_tick_20261013'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def summarize(path):
    result=read(path/'rollout.json')
    with np.load(path/'rollout.npz') as z:
        o=z['observation'].copy();t=z['neuron_time'].copy();actual=o[:,14:17]-o[:,26:29]
        actions=z['applied_action'].copy();states=z['reservoir_state'].copy();contacts=z['prior_contact_peak'].copy()
    windows=[]
    event=result['stats']['events'].get('rod');first=event['first_s'];last=event['last_s']
    for label,lo,hi in [('before_rod',max(0,first-2),first),('rod_first_2s',first,first+2),
                      ('after_rod_0_2s',last+.04,last+2.04),('after_rod_2_6s',last+2.04,last+6.04),('fixed_12_18s',12,18)]:
        m=(t>=lo-1e-7)&(t<hi-1e-7)
        windows.append(dict(window=label,start_s=lo,end_s=hi,frames=int(m.sum()),
            actual_xyz_step_rms_mmps=(1000*np.sqrt(np.mean(np.diff(actual[m],axis=0)**2,axis=0))).tolist(),
            raw_x_sign_flips=int(np.sum(actions[m,1][1:]*actions[m,1][:-1]<0)),
            raw_x_saturation_fraction=float(np.mean(abs(actions[m,1])>=1-1e-8)),
            estimated_wrench_rms=np.sqrt(np.mean(o[m,39:45]**2,axis=0)).tolist(),
            state_norm_mean=float(np.linalg.norm(states[m],axis=1).mean()),
            diagnosed_contact_peak_n=contacts[m].max(0).tolist()))
    checkpoint=path/'checkpoint.npz'
    if not checkpoint.exists():checkpoint=ROOT/'outputs/paired_baseline_development_20261012_v2/checkpoints/esn.npz'
    policy=OfficeVMCMemoryESN(checkpoint)
    index=int(np.searchsorted(t,last+.04));alternative=OfficeVMCMemoryESN(checkpoint)
    difference=[];state_difference=[];force_sensitivity=[]
    probe=OfficeVMCMemoryESN(checkpoint)
    for i,obs in enumerate(o):
        previous=policy.state.copy()
        action=policy.act(obs)
        np.testing.assert_array_equal(action,actions[i]);np.testing.assert_array_equal(policy.state,states[i])
        perturb=obs.copy();perturb[39]+=.001;probe.state=previous.copy()
        plus=float((probe.features(perturb)@probe.weights)[1])
        perturb[39]-=.002;probe.state=previous.copy()
        minus=float((probe.features(perturb)@probe.weights)[1])
        force_sensitivity.append((plus-minus)*.32/.002)
        if i>=index:
            alt=alternative.act(obs)
            difference.append(float(abs(alt-action).max()));state_difference.append(float(abs(alternative.state-policy.state).max()))
    difference=np.array(difference)
    suffix=np.maximum.accumulate(difference[::-1])[::-1]
    below=np.flatnonzero(suffix<1e-4)
    memory=dict(offline_only=True,physical_controller_never_reset=True,
        replay_start_s=float(t[index]),
        caveat='Both replays consume the SAME recorded observations; this tests memory dependence, not closed-loop reset recovery',
        initial_action_difference=float(difference[0]),final_action_difference=float(difference[-1]),
        final_state_difference=float(state_difference[-1]),
        suffix_action_difference_below_1e_4_after_s=float(t[index+below[0]]-t[index]) if len(below) else None)
    gain=np.array(force_sensitivity)
    for w in windows:
        mask=(t>=w['start_s']-1e-7)&(t<w['end_s']-1e-7)
        w['local_preclip_vx_Fx_sensitivity']=dict(median_mps_per_n=float(np.median(gain[mask])),
            min_mps_per_n=float(gain[mask].min()),max_mps_per_n=float(gain[mask].max()),
            negative_fraction=float(np.mean(gain[mask]<0)),
            caveat='Finite difference of next preclip readout at frozen preceding reservoir state, other observation fields fixed; not a physical intervention or stability proof')
    return dict(task=result['task_success'],strict=result['strict_success'],stage=result['final_task_stage'],
        events=result['task_events'],metrics=result['metrics'],penetration_mm=result['stats']['max_external_penetration_m']*1000,
        rod=event,cup_valid=result['cup_valid'],windows=windows,offline_memory_test=memory,
        hashes={name:sha(path/name) for name in ('rollout.json','rollout.npz','rollout.mjb')},checkpoint_sha256=sha(checkpoint)),dict(t=t,obs=o,actual=actual,actions=actions,states=states,contacts=contacts)

def main():
    target=OUT/'ROD_ANALYSIS.json'
    if target.exists():raise FileExistsError(target)
    paths=dict(native=ROOT/'outputs/paired_baseline_development_20261012_v2/episodes/esn__repair_development_002',
        historical=ROOT/'outputs/original_esn_continuous_reference_20261013/episode',
        lagged=OUT/'lagged/episode',same_tick=OUT/'same_tick/episode')
    rows={};arrays={}
    for label,path in paths.items():rows[label],arrays[label]=summarize(path)
    assert len({row['checkpoint_sha256'] for row in rows.values()})==1
    for label in ('lagged','same_tick'):
        e=read(paths[label]/'execution.json');assert e['status']=='complete'
        with tarfile.open(paths[label]/'source_overlay.tar.gz') as tar:
            for name,value in e['source_sha256'].items():assert hashlib.sha256(tar.extractfile(name).read()).hexdigest()==value
        rows[label]['audit']=read(paths[label]/'AUDIT.json')
    es=[read(paths[k]/'execution.json') for k in ('lagged','same_tick')]
    assert es[0]['action_filter_config']==es[1]['action_filter_config']
    meta=[read(paths[k]/'rollout.json') for k in ('lagged','same_tick')]
    for key in ('placement_destination','placement_support_geoms','schedule','observer_settings','contact_required','physics_resolution'):
        assert meta[0][key]==meta[1][key],key
    assert rows['lagged']['hashes']['rollout.mjb']==rows['same_tick']['hashes']['rollout.mjb']==rows['historical']['hashes']['rollout.mjb']
    # The instrumented control must reproduce the earlier uninstrumented run.
    replay={}
    with np.load(paths['historical']/'rollout.npz') as a,np.load(paths['lagged']/'rollout.npz') as b:
        for key in ('time','qpos','qvel','observation','applied_action','reservoir_state'):
            replay[key]=float(abs(a[key]-b[key]).max());np.testing.assert_array_equal(a[key],b[key])
    value=dict(runs=rows,source_sha256=sha(Path(__file__)),historical_instrumentation_exact_reproduction=replay,
        correction_only='Same-tick feedback scale latch, with existing residual/limits/reference unchanged',
        limitations=['One old-layout pair, not generalization or baseline ranking',
            'Native is a different route/posture and schedule, not a matched physical comparison',
            'Same-clock/event-aligned windows still have different contact exposure',
            'Offline cold-state replay is diagnostic only; no deployed state resets',
            'Physics dt5e-5 does not make a failed task or unsafe rollout a passed result'])
    target.write_text(json.dumps(value,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(4,1,figsize=(11,9),sharex=True,layout='constrained')
    for label,color in [('lagged','#c97730'),('same_tick','#157eab')]:
        d=arrays[label];t=d['t'];first=rows[label]['rod']['first_s'];last=rows[label]['rod']['last_s']
        axes[0].plot(t,d['contacts'][:,2],color=color,label=label,lw=1)
        axes[1].plot(t,d['obs'][:,39],color=color,label=label,lw=1)
        axes[2].plot(t,d['actions'][:,1]*320,color=color,label=label,lw=.8)
        axes[3].plot(t,d['actual'][:,0]*1000,color=color,label=label,lw=.8)
        for ax in axes:ax.axvline(first,color=color,ls=':',alpha=.6);ax.axvline(last,color=color,ls='--',alpha=.6)
    labels=['Rod peak / prior40ms (N)','Estimated Fx (N)','ESN request x (mm/s)','Measured EE vx (mm/s)']
    for ax,label in zip(axes,labels):ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(loc='upper right');ax.set_xlim(8,23)
    axes[-1].set_xlabel('Simulation time (s); dotted=first rod contact, dashed=last')
    fig.suptitle('Frozen ESN: only common feedback-scale timing changed')
    fig.savefig(OUT/'rod_timing.png',dpi=150);fig.savefig(OUT/'rod_timing.pdf');plt.close(fig)
    for label,r in rows.items():
        print(label,json.dumps({k:r[k] for k in ('task','strict','stage','rod','offline_memory_test')}))
        print('fixed12-18',r['windows'][-1])

if __name__=='__main__':main()
