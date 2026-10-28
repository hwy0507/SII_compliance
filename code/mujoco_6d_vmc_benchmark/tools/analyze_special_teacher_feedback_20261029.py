"""Read-only diagnosis on completed training identities, never test labels.

Save exact actor replay, late-motion spectra, action conversion gains and
actual saved curves. Frequency/co-variation is descriptive, not causality.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from intent_recovery_teacher_20261029 import make_teacher


def spectrum(values):
    x = np.asarray(values, dtype=float)
    x = (x-x.mean())*np.hanning(len(x))
    power = np.abs(np.fft.rfft(x))**2
    frequencies = np.fft.rfftfreq(len(x), .04)
    index = 1+int(np.argmax(power[1:]))
    return dict(peak_frequency_hz=float(frequencies[index]), peak_bin_fraction=float(power[index]/max(power[1:].sum(),1e-30)))


def analyze(output):
    assert not output.exists()
    sources = [
        ('original_075', 'special_teacher_midpoint_20261028_v1', 'v075_avg1_'),
        ('equilibrium_015', 'special_intent_equilibrium_20261029_v1', 'equilibrium_'),
        ('equilibrium_030', 'special_equilibrium_intent030_20261029_v1', 'intent030_'),
    ]
    rows, curves = [], {}
    for label, folder, prefix in sources:
        for identity in ('ball_00', 'ball_01', 'ball_04'):
            path = ROOT/'outputs'/folder/(prefix+identity)/'ball'
            q, execution = read(path/'DEMONSTRATION_QUALIFICATION.json'), read(path/'execution.json')
            assert execution['status'] == 'complete'
            for name, digest in q['input_hashes'].items():
                assert sha(path/name) == digest
            config = read(path/'teacher.json')
            actor = make_teacher(config)
            with np.load(path/'trajectory.npz',allow_pickle=False) as z, np.load(path/'legacy.npz',allow_pickle=False) as legacy, np.load(path/'filter.npz',allow_pickle=False) as filt:
                obs, actions, times = z['observation'], z['action'], z['time']
                pred, base, memory, offset, velocity = [], [], [], [], []
                for o in obs:
                    actor.observe(o)
                    pred.append(actor.act(o[39:45]))
                    residual = actor.velocity_weight*actor.velocity+actor.offset_gain*actor.offset
                    base.append(np.clip(actor.R6@residual/actor.action_limits,-1,1)*actor.channel_gain[1:])
                    memory.append(actor.recovery_memory)
                    offset.append(actor.offset.copy()); velocity.append(actor.velocity.copy())
                np.testing.assert_array_equal(pred, actions)
                np.testing.assert_array_equal(filt['request'], actions)
                speed = np.linalg.norm(np.diff(legacy['object_position'],axis=0)/.04,axis=1)
                base = np.asarray(base)
                horizontal = np.minimum(1,np.linalg.norm(obs[:,45:47],axis=1))
                activation = np.array(memory)*horizontal**2
                base_contribution = (1-activation)*base[:,2]
                recovery_contribution = actions[:,3]-base_contribution
                tail = slice(-250,None)
                row = dict(setting=label, identity=identity, qualified=q['status']=='qualified',
                    sources={name:sha(path/name) for name in ('trajectory.npz','legacy.npz','filter.npz','teacher.json','DEMONSTRATION_QUALIFICATION.json')},
                    source_folder=str(path), actor_replay_max_abs=0.,
                    last9_speed_max_mps=float(speed[-9:].max()),
                    last250_speed_rms_mps=float(np.sqrt(np.mean(speed[-250:]**2))),
                    last250_z_action_std=float(actions[tail,3].std()),
                    last250_wrench_z_std_n=float(obs[tail,41].std()),
                    last250_base_z_std=float(base_contribution[tail].std()),
                    last250_recovery_z_std=float(recovery_contribution[tail].std()),
                    last250_z_action_spectrum=spectrum(actions[tail,3]),
                    last250_object_z_spectrum=spectrum(legacy['object_position'][tail,2]),
                    teacher_action_limits=actor.action_limits.tolist(),
                    common_yield_limits=[.32,.32,.32,.6,.6,.6],
                    base_unsaturated_component_gain=(np.array([.32,.32,.32,.6,.6,.6])/actor.action_limits).tolist(),
                    gain_interpretation='Pre-filter component conversion relative to virtual velocity+offset readout, not actual end-effector velocity. Could be historical tuning; not by itself proof of an implementation bug.')
                rows.append(row)
                if identity=='ball_01':
                    curves[label] = dict(time=times.copy(), speed=speed.copy(), action=actions[:,3].copy(),
                        base=base_contribution.copy(), recovery=recovery_contribution.copy(),
                        yield_z=filt['twist'][:,2].copy(), wrench_z=obs[:,41].copy())
    output.mkdir(parents=True)
    fig, axes = plt.subplots(3,3,figsize=(13,8),sharex=True)
    for j,(label,curve) in enumerate(curves.items()):
        axes[0,j].plot(curve['time'][1:],curve['speed'],lw=1)
        axes[0,j].axhline(.02,color='red',ls='--',lw=.8,label='original tail speed limit')
        axes[0,j].set_title(label+' / train ball01')
        axes[1,j].plot(curve['time'],curve['base'],label='base contribution',lw=.9)
        axes[1,j].plot(curve['time'],curve['recovery'],label='recovery contribution',lw=.9)
        axes[1,j].plot(curve['time'],curve['action'],label='requested z action',lw=.9,alpha=.7)
        axes[2,j].plot(curve['time'],curve['wrench_z'],label='estimated wrench z',lw=.9)
        for ax in axes[:,j]:
            ax.set_xlim(20,30);ax.grid(alpha=.2)
        axes[2,j].set_xlabel('Saved physical time (s)')
    axes[0,0].set_ylabel('Object speed (m/s)')
    axes[1,0].set_ylabel('Normalized requested z action')
    axes[2,0].set_ylabel('Estimated wrench z (N)')
    axes[0,0].legend(fontsize=7);axes[1,0].legend(fontsize=7)
    fig.suptitle('Actual completed training trajectories; no counterfactual physics / no student result')
    fig.tight_layout();fig.savefig(output/'actual_ball01_feedback.png',dpi=160);plt.close(fig)
    result = dict(status='complete',rows=rows,source_sha256=sha(Path(__file__)),
        plot_sha256=sha(output/'actual_ball01_feedback.png'),
        interpretation='All nine completed training traces retained. Last-window qualification is distinct from whole-tail stability; dominant frequencies are descriptive only. Virtual readout has anisotropic pre-filter gains 2/2/1.6, which warrants a separate controller-normalization control without changing the common filter.')
    write(output/'DIAGNOSIS.json',result)
    print([(r['setting'],r['identity'],r['qualified'],r['last9_speed_max_mps'],r['last250_z_action_spectrum']) for r in rows])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();analyze(a.output.resolve())
