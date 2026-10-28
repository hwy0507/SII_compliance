"""Read-only diagnosis of a frozen rollout. No dynamics or policy modification."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import mujoco

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    run = ROOT / 'outputs/original_esn_old_office_transfer_20261013/episode_v2'
    out = ROOT / 'outputs/original_esn_old_office_chatter_20261013_v3'
    out.mkdir(exist_ok=False)
    execution = json.loads((run / 'execution.json').read_text())
    assert sha(ROOT/'scripts/office_vmc_memory_esn_20260927.py') == execution['source_sha256']['scripts/office_vmc_memory_esn_20260927.py']
    z = np.load(run/'rollout.npz'); c = np.load(run/'execution_chain.npz')
    t = z['neuron_time']; obs = z['observation']; nominal = obs[:,14:17]
    actual = nominal-obs[:,26:29]; raw = c['requested_action'][:,1:4]*.32
    filtered = c['yield_twist'][:,:3]
    policy = OfficeVMCMemoryESN(run/'checkpoint.npz')
    features = np.array([policy.features(o) for o in obs])
    logits = features @ policy.weights
    prediction = np.clip(logits,-1,1); prediction[:,0] = np.clip(logits[:,0],0,1)
    np.testing.assert_allclose(prediction,c['requested_action'],rtol=0,atol=2e-12)
    # Exact additive attribution of pre-clipping linear readout; not physical ablations.
    blocks = {'current_wrench':np.r_[0:6,134:140],
              'reservoir':np.r_[6:134,140:268],
              'current_wrench_context':np.arange(268,412),
              'reservoir_context':np.arange(412,540),
              'direct_context':np.arange(540,552)}
    contributions = {k:features[:,idx]@policy.weights[idx] for k,idx in blocks.items()}
    context_names = ['nominal_x','nominal_y','nominal_z','velocity_error_x','velocity_error_y',
        'velocity_error_z','direction_x','direction_y','direction_z','position_error_x','position_error_y','position_error_z']
    cross_by_context = (features[:,268:412]*policy.weights[268:412,1]).reshape(-1,12,12).sum(1)
    np.testing.assert_allclose(sum(contributions.values()),logits,rtol=0,atol=1e-11)
    # Replay instantaneous wrench mapping to check for least-squares rank switches.
    model = mujoco.MjModel.from_binary_path(str(run/'rollout.mjb')); data=mujoco.MjData(model)
    hand = mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'hand')
    jp=np.zeros((3,model.nv)); jr=jp.copy(); ranks=[]; wrench=[]; ratios=[]
    for q,load in zip(z['neuron_qpos'],obs[:,32:39]):
        data.qpos[:]=q; mujoco.mj_kinematics(model,data); mujoco.mj_comPos(model,data)
        mujoco.mj_jacBody(model,data,jp,jr,hand)
        J=np.vstack((jp,jr))[:,:7]; s=np.linalg.svd(J.T,compute_uv=False)
        ranks.append(int(np.sum(s>.03*s[0]))); ratios.append(float(s[-1]/s[0]))
        wrench.append(np.linalg.lstsq(J.T,load,rcond=.03)[0])
    wrench_error=float(np.max(np.abs(np.array(wrench)-obs[:,39:45])))
    # Saved post-integration qpos does not retain the live Jacobian cache from
    # the preceding dynamics evaluation. Record mismatch, not exact replay.
    windows=[]
    for lo,hi in [(8,10.24),(10.24,11.48),(11.48,16.68),(16.72,22.68),(24.12,28.36),(30,40)]:
        mask=(t>=lo-1e-7)&(t<hi-1e-7)
        def step_rms(a): return np.sqrt(np.mean(np.diff(a[mask],axis=0)**2,axis=0)).tolist()
        def spectrum(a):
            x=a[mask,0]; x=x-x.mean(); power=np.abs(np.fft.rfft(x*np.hanning(len(x))))**2
            freq=np.fft.rfftfreq(len(x),.04); power[0]=0
            return dict(dominant_hz=float(freq[power.argmax()]), fraction_above_5hz=float(power[freq>5].sum()/power.sum()))
        windows.append(dict(start_s=lo,end_s=hi,frames=int(mask.sum()),stages=np.unique(z['stage'][mask]).tolist(),
            requested_xyz_step_rms_mps=step_rms(raw),filtered_xyz_step_rms_mps=step_rms(filtered),
            measured_xyz_step_rms_mps=step_rms(actual),nominal_xyz_step_rms_mps=step_rms(nominal),
            requested_axis_saturation_fraction=np.mean(np.abs(raw[mask])>=.32-1e-8,axis=0).tolist(),
            raw_x_sign_flips=int(np.sum(raw[mask,0][1:]*raw[mask,0][:-1]<0)),
            filtered_axis_slew_fraction=np.mean(np.isclose(np.abs(np.diff(filtered[mask],axis=0)),.048,atol=1e-8),axis=0).tolist(),
            wrench_xyz_step_rms_n=step_rms(obs[:,39:42]),
            nominal_xyz_range_mps=np.ptp(nominal[mask],axis=0).tolist(),
            position_error_xyz_mean_m=obs[mask,20:23].mean(0).tolist(),
            position_context_clipped_fraction=np.mean(np.abs(obs[mask,20:23]/.08)>=4,axis=0).tolist(),
            prior_hand_rod_peak_n=np.max(z['prior_contact_peak'][mask,1:3],axis=0).tolist(),
            prior_all_contact_peak_n=np.max(z['prior_contact_peak'][mask],axis=0).tolist(),
            requested_x_spectrum=spectrum(raw),filtered_x_spectrum=spectrum(filtered),
            measured_x_spectrum=spectrum(actual),
            x_wrench_context_step_rms_by_context=dict(zip(context_names,step_rms(cross_by_context))),
            x_readout_step_rms_by_block={k:float(np.sqrt(np.mean(np.diff(v[mask,1])**2))) for k,v in contributions.items()}))
    sample=(t>=13-1e-7)&(t<13.4-1e-7)
    rows=[dict(t=float(t[i]),nominal_x_mps=float(nominal[i,0]),request_x_mps=float(raw[i,0]),
        filtered_x_mps=float(filtered[i,0]),actual_x_mps=float(actual[i,0]),estimated_wrench=obs[i,39:45].tolist(),
        raw_x_readout=float(logits[i,1]),x_readout_blocks={k:float(v[i,1]) for k,v in contributions.items()},
        x_wrench_context_by_context=dict(zip(context_names,cross_by_context[i].tolist()))) for i in np.flatnonzero(sample)]
    result=dict(physics_rerun=False,policy_changed=False,source_sha256=sha(__file__),
        input_sha256={n:sha(run/n) for n in ('rollout.npz','execution_chain.npz','checkpoint.npz','rollout.json','execution.json')},
        runtime_source_sha256=execution['source_sha256']['scripts/office_vmc_memory_esn_20260927.py'],
        exact_readout_replay_tolerance=2e-12,wrench_mapping_replay_max_abs=wrench_error,
        wrench_mapping_exact_replay=False,
        wrench_mapping_ranks=sorted(set(ranks)),minimum_singular_ratio=min(ratios),
        selector_pulse_frames=int(z['selector_pulse_active'].sum()),windows=windows,example_13s=rows,
        limitations=['Readout blocks are additive pre-clipping contributions, not independent causes.',
          'No counterfactual dynamics: cannot uniquely separate estimator, learned readout, memory and contact feedback.',
          '25Hz spectrum does not describe all physics-step vibration.',
          'Saturation threshold is the existing 0.32 m/s bound, not a new gate.',
          'No teacher-distribution comparison; distribution shift remains a hypothesis.'])
    (out/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2)+'\n')
    np.savez_compressed(out/'diagnostic_channels.npz',time=t,nominal=nominal,raw=raw,filtered=filtered,actual=actual,
        estimated_wrench=obs[:,39:45],scale=c['wbc_scale'],prior_contacts=z['prior_contact_peak'],logits=logits)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axs=plt.subplots(4,1,figsize=(12,10),sharex=True,layout='constrained')
    for j,name in [(1,'Hand'),(2,'Rod')]:axs[0].plot(t,z['prior_contact_peak'][:,j],label=name,lw=1)
    axs[0].set_ylabel('Prior 40 ms\ncontact peak (N)');axs[0].set_yscale('symlog',linthresh=1)
    for a,label in [(nominal,'Nominal x'),(raw,'ESN requested x'),(filtered,'Filtered x')]:axs[1].plot(t,a[:,0]*1000,label=label,lw=1)
    axs[1].set_ylabel('World-x command\n(mm/s)')
    for j,name in enumerate('xyz'):axs[2].plot(t,actual[:,j]*1000,label=f'Measured {name}',lw=1)
    axs[2].set_ylabel('Measured EE\nvelocity (mm/s)')
    for j,name in enumerate('xyz'):axs[3].plot(t,obs[:,39+j],label=f'Estimated F{name}',lw=1)
    axs[3].set_ylabel('Estimated wrench\nforce (N)');axs[3].set_xlabel('Simulation time (s)')
    for ax in axs:
        ax.axvline(11.482,color='black',ls=':',lw=1);ax.axvline(16.663,color='black',ls=':',lw=1)
        ax.set_xlim(10.5,22.5);ax.grid(alpha=.2);ax.legend(loc='upper right',ncol=3,fontsize=8)
    fig.suptitle('Frozen original ESN / old cup-pillar office: contact ends, command chatter persists')
    fig.savefig(out/'chatter.png',dpi=160);fig.savefig(out/'chatter.pdf');plt.close(fig)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
