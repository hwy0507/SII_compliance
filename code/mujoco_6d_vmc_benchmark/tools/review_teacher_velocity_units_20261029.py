"""Compare completed, paired teacher controls using saved physical traces.

No fitting or new simulation. Keep the original last-nine speed gate distinct
from the broader ten-second stability diagnostic. Office is development
regression, not an unseen test and never an imitation-label source.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from intent_recovery_teacher_20261029 import make_teacher


def main(output):
    assert not output.exists()
    parents = [ROOT/'outputs'/name for name in (
        'special_equilibrium_intent030_20261029_v1',
        'special_teacher_velocity_units_20261029_v1')]
    reviews = [read(p/'REVIEW.json') for p in parents]
    regs = [read(p/'REGISTRATION.json') for p in parents]
    configs = [read(Path(r['cases'][0]['config'])) for r in regs]
    expected = dict(configs[0], options=dict(configs[0].get('options', {}),
                                         action_limit_6d=[.32,.32,.32,.6,.6,.6]))
    assert expected == configs[1], 'Unexpected additional teacher change'
    rows, office_rows = [], []
    fig, axes = plt.subplots(3, 2, figsize=(11, 8), sharex=True)
    for j, (parent, review, reg) in enumerate(zip(parents, reviews, regs)):
        assert review['execution_sha256'] == sha(parent/'execution.json')
        assert review['registration_sha256'] == sha(parent/'REGISTRATION.json')
        for i, identity in enumerate(('ball_00','ball_01','ball_04')):
            case = next(c for c in reg['cases'] if c.get('identity') == identity)
            other = next(c for c in regs[1-j]['cases'] if c.get('identity') == identity)
            for key in ('seed','scene_parameters','expected_model_sha256'):
                assert case[key] == other[key]
            folder = parent/case['id']/'ball'
            q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            for name, digest in q['input_hashes'].items():
                assert sha(folder/name) == digest
            with np.load(folder/'legacy.npz',allow_pickle=False) as legacy, np.load(folder/'trajectory.npz',allow_pickle=False) as trace:
                actor = make_teacher(configs[j])
                predictions = []
                for observation in trace['observation']:
                    actor.observe(observation)
                    predictions.append(actor.act(observation[39:45]))
                np.testing.assert_array_equal(predictions, trace['action'])
                time = trace['time'].copy()
                # MuJoCo accumulates 800 floating-point 50us steps per sample.
                # This tolerance is <1e-6 physics substeps, not a gate change.
                np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=2e-11)
                speed = np.linalg.norm(np.diff(legacy['object_position'],axis=0)/.04,axis=1)
                metric = dict(setting=('before','matched_normalization')[j],identity=identity,
                    qualification=q['status'],actor_replay_max_abs=0.,
                    original_tail_speed_max_mps=float(speed[-9:].max()),
                    last10s_speed_rms_mps=float(np.sqrt(np.mean(speed[-250:]**2))),
                    last10s_speed_max_mps=float(speed[-250:].max()),
                    trajectory_sha256=sha(folder/'trajectory.npz'),legacy_sha256=sha(folder/'legacy.npz'),
                    qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
                stored = next(r for r in review['rows'] if r['id']==case['id'])
                assert metric['original_tail_speed_max_mps']==stored['tail_object_speed_max_mps']
                rows.append(metric)
                ax=axes[i,j]
                ax.plot(time[1:],speed,lw=.85)
                ax.axhline(.02,color='red',ls='--',lw=.8)
                ax.axvspan(time[-10],time[-1],color='green',alpha=.13)
                ax.set_xlim(20,30);ax.set_ylim(bottom=0);ax.grid(alpha=.2)
                ax.set_title(f"{identity} / {metric['setting']} / {q['status']}",fontsize=9)
                ax.set_ylabel('Object speed (m/s)')
                if i==2: ax.set_xlabel('Saved physical time (s)')
        case = next(c for c in reg['cases'] if c['kind']=='office')
        folder = parent/case['id']
        audit = read(folder/'AUDIT.json')
        assert sha(folder/'rollout.npz')==audit['trace_sha256']
        assert sha(folder/'execution_chain.npz')==audit['chain_sha256']
        assert audit['full_horizon']
        with np.load(folder/'rollout.npz',allow_pickle=False) as trace, np.load(folder/'teacher_internal.npz',allow_pickle=False) as internal, np.load(folder/'execution_chain.npz',allow_pickle=False) as chain:
            actor=make_teacher(configs[j])
            predictions, components=[] , []
            for observation in trace['observation']:
                actor.observe(observation)
                predictions.append(actor.act(observation[39:45]))
                residual=actor.R6@(actor.velocity_weight*actor.velocity+actor.offset_gain*actor.offset)
                base=np.clip(residual/actor.action_limits,-1,1)*actor.channel_gain[1:]
                components.append((actor.recovery_activation,actor.recovery_intent,base[2]))
            np.testing.assert_array_equal(predictions,internal['requested_action'])
            np.testing.assert_array_equal(predictions,chain['requested_action'])
            tail=slice(-250,None)
            observation=trace['observation'][tail]
            decomposition=np.asarray(components)[tail]
            gate_position=trace['task_position_error_m'][tail]<.012
            gate_rotation=trace['task_rotation_error_rad'][tail]<.12
            gate_speed=trace['task_speed_mps'][tail]<.025
            office_rows.append(dict(setting=('before','matched_normalization')[j],
                task=audit['task_success'],strict=audit['strict_success'],stage=audit['stage'],
                actor_replay_max_abs=0.,audit_sha256=sha(folder/'AUDIT.json'),
                last250_pose_error_mean=observation[:,20:26].mean(0).tolist(),
                last250_nominal_linear_velocity_mean=observation[:,14:17].mean(0).tolist(),
                last250_estimated_wrench_mean=observation[:,39:45].mean(0).tolist(),
                last250_recovery_activation_mean=float(decomposition[:,0].mean()),
                last250_recovery_intent_mean=float(decomposition[:,1].mean()),
                last250_base_z_action_mean=float(decomposition[:,2].mean()),
                last250_filtered_yield_twist_mean=chain['yield_twist'][tail].mean(0).tolist(),
                last250_position_gate_fraction=float(gate_position.mean()),
                last250_rotation_gate_fraction=float(gate_rotation.mean()),
                last250_speed_gate_fraction=float(gate_speed.mean()),
                last250_three_kinematic_gates_fraction=float((gate_position&gate_rotation&gate_speed).mean()),
                limitation='Kinematic marginals are descriptive, not the complete carry or final Task/Strict gate. Saved office observations are never fitting labels.'))
    for i in range(3):
        maximum=max(ax.get_ylim()[1] for ax in axes[i])
        for ax in axes[i]: ax.set_ylim(0,maximum)
    fig.suptitle('Paired full physics: last 10 s shown; green = original qualification window\nTeacher normalization only; no student training or unseen-test claim',fontsize=11)
    fig.tight_layout()
    output.mkdir(parents=True)
    fig.savefig(output/'paired_ball_speed.png',dpi=160);plt.close(fig)
    write(output/'REVIEW.json',dict(status='complete',rows=rows,office_rows=office_rows,
        source_sha256=sha(Path(__file__)),
        parent_reviews={str(p):sha(p/'REVIEW.json') for p in parents},
        plot_sha256=sha(output/'paired_ball_speed.png'),
        all_six_qualified=reviews[1]['all_six_qualified'],
        limitation='Only this finite paired control; does not establish global stability or repair of ESN and the108 matrix. Original end-window qualification is not whole-tail stability.'))
    print(rows,office_rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args().output.resolve())
