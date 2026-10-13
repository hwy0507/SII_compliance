"""Audit motor-compensation candidate against its exact common-runtime baseline."""
import hashlib
import json
from pathlib import Path
import tarfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'outputs/original_esn_rod_opposition_20261013'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def summarize(path):
    result = read(path/'rollout.json')
    event = result['stats']['events'].get('rod')
    with np.load(path/'rollout.npz') as z, np.load(path/'execution_chain.npz') as c, np.load(path/'servo_tick_trace.npz') as s:
        t = z['neuron_time'].copy(); o = z['observation'].copy()
        data = dict(time=t, force=o[:,39:42].copy(), nominal=o[:,14:17].copy(),
            yield_velocity=c['yield_twist'][:,:3].copy(), measured=o[:,14:17]-o[:,26:29],
            raw=z['applied_action'][:,1:4].copy(), rod_peak=z['prior_contact_peak'][:,2].copy())
        recent = data['rod_peak'] > 0
        recent_contact = dict(frames=int(recent.sum()),
            caveat='Current observations/actions in frames whose preceding40ms contained rod contact; not simultaneous physical force samples',
            mean_nominal_mmps=(data['nominal'][recent].mean(0)*1000).tolist() if recent.any() else None,
            mean_filtered_esn_mmps=(data['yield_velocity'][recent].mean(0)*1000).tolist() if recent.any() else None,
            mean_measured_mmps=(data['measured'][recent].mean(0)*1000).tolist() if recent.any() else None,
            mean_estimated_force_n=data['force'][recent].mean(0).tolist() if recent.any() else None)
        windows = []
        intervals = [('fixed12_18',12.,18.)]
        if event and event['first_s'] is not None:
            intervals += [('rod_span',event['first_s'],event['last_s']),
                ('after_rod2_6',event['last_s']+2.,event['last_s']+6.)]
        for label, lo, hi in intervals:
            mask = (t>=lo-1e-7)&(t<hi-1e-7)
            smask = (s['time_s']>=lo-1e-7)&(s['time_s']<hi-1e-7)
            if mask.sum()<2 or smask.sum()<2:
                continue
            nominal = s['nominal_twist'][smask,:3]; residual = s['yield_twist'][smask,:3]
            measured = s['measured_twist'][smask,:3]
            windows.append(dict(name=label,start_s=lo,end_s=hi,policy_frames=int(mask.sum()),servo_frames=int(smask.sum()),
                nominal_mean_mmps=(nominal.mean(0)*1000).tolist(),
                residual_mean_mmps=(residual.mean(0)*1000).tolist(),
                measured_mean_mmps=(measured.mean(0)*1000).tolist(),
                nominal_vs_residual_x_opposition_fraction=float(np.mean(nominal[:,0]*residual[:,0]<0)),
                nominal_x_negative_fraction=float(np.mean(nominal[:,0]<0)),
                residual_x_negative_fraction=float(np.mean(residual[:,0]<0)),
                estimated_force_mean_n=o[mask,39:42].mean(0).tolist(),
                actual_velocity_step_rms_25hz_mmps=(np.sqrt(np.mean(np.diff(data['measured'][mask],axis=0)**2,axis=0))*1000).tolist(),
                actual_velocity_step_rms_250hz_mmps=(np.sqrt(np.mean(np.diff(measured,axis=0)**2,axis=0))*1000).tolist(),
                raw_x_sign_flips=int(np.sum(data['raw'][mask,0][1:]*data['raw'][mask,0][:-1]<0))))
    row = dict(task=result['task_success'],strict=result['strict_success'],stage=result['final_task_stage'],
        task_events=result['task_events'],rod=event,cup_valid=result['cup_valid'],
        metrics=result['metrics'],penetration_mm=result['stats']['max_external_penetration_m']*1000,
        windows=windows,recent_contact_bins=recent_contact,
        checkpoint_sha256=sha(path/'checkpoint.npz'),mjb_sha256=sha(path/'rollout.mjb'),
        trace_sha256=sha(path/'rollout.npz'),audit=read(path/'AUDIT.json'))
    e = read(path/'execution.json'); assert e['status']=='complete'
    with tarfile.open(path/'source_overlay.tar.gz') as archive:
        for name, expected in e['source_sha256'].items():
            assert hashlib.sha256(archive.extractfile(name).read()).hexdigest()==expected, name
    return row, data


def main():
    target = OUT/'COMPARISON.json'
    if target.exists():
        raise FileExistsError(target)
    paths = dict(baseline=ROOT/'outputs/original_esn_rod_tick_20261013/same_tick/episode',candidate=OUT/'episode')
    rows, data = {}, {}
    for key, path in paths.items():
        rows[key], data[key] = summarize(path)
    assert rows['baseline']['checkpoint_sha256']==rows['candidate']['checkpoint_sha256']
    assert rows['baseline']['mjb_sha256']==rows['candidate']['mjb_sha256']
    a,b = [read(p/'rollout.json') for p in paths.values()]
    for key in ('schedule','observer_settings','placement_destination','placement_support_geoms','physics_resolution','contact_required'):
        assert a[key]==b[key],key
    ea,eb = [read(p/'execution.json') for p in paths.values()]
    assert ea['action_filter_config']==eb['action_filter_config']
    for r in rows.values():
        assert r['audit']['feedback_tick_contract']['wrong_tick_fraction']==0
    value = dict(runs=rows,source_sha256=sha(Path(__file__)),
        limitations=['One paired old-layout trial; not generalization or a baseline ranking',
            'Rod-span windows include contact gaps; durations are reported independently',
            'Estimated force is not contact truth; command sum is not measured motion',
            'Lower velocity alone can reflect stalling; task completion and contact exposure remain required',
            'Model friction compensation is a new common servo option, not an ESN improvement or historical restoration'])
    target.write_text(json.dumps(value,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(4,1,figsize=(11,9),sharex=True,layout='constrained')
    for key,color in [('baseline','#bd6b29'),('candidate','#177eb1')]:
        d=data[key];t=d['time']
        axes[0].plot(t,d['rod_peak'],color=color,label=key,lw=.9)
        axes[1].plot(t,d['nominal'][:,0]*1000,color=color,label=key+' nominal',lw=1)
        axes[1].plot(t,d['yield_velocity'][:,0]*1000,color=color,label=key+' ESN filtered',lw=.8,ls='--')
        axes[2].plot(t,d['measured'][:,0]*1000,color=color,label=key,lw=.8)
        axes[3].plot(t,d['force'][:,0],color=color,label=key,lw=.8)
    for ax,label in zip(axes,['Rod peak / prior40ms (N)','Requested vx (mm/s)','Measured EE vx (mm/s)','Estimated Fx (N)']):
        ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(loc='upper right');ax.set_xlim(10,23)
    axes[-1].set_xlabel('Simulation time (s)')
    fig.suptitle('Frozen ESN: encoder-based motor friction candidate')
    fig.savefig(OUT/'rod_opposition.png',dpi=150);fig.savefig(OUT/'rod_opposition.pdf');plt.close(fig)
    for key,row in rows.items():
        print(key,json.dumps({k:row[k] for k in ('task','strict','stage','rod','windows')}))


if __name__=='__main__':
    main()
