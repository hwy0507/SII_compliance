"""Audit the completed ten-ball block and diagnose training-only tail motion.

All original qualification outcomes are preserved. Validation gets only the
original terminal-gate recomputation; training curves and control-component
statistics inform any subsequent, separately registered teacher experiment.
"""
import argparse
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, validate, write
from optimize_tool_contact_20261002 import ParameterTeacher
from review_repaired_student_closures_20261029 import history, qualification


def audit(collection, output):
    assert not output.exists()
    plan = validate(collection/'COLLECTION_PLAN.json')
    progress = read(collection/'COLLECTION_PROGRESS.json')
    entries = [e for e in plan['episodes'] if e['scene']=='ball']
    assert len(entries)==10 and Counter(e['split'] for e in entries)==Counter(train=8, validation=2)
    completed = {r['id']:r for r in progress['episodes']}
    assert all(e['id'] in completed for e in entries), 'Full ten-ball block required'
    rows, arrays = [], {}
    for entry in entries:
        folder = Path(entry['folder'])
        q = qualification(folder)
        e, legacy = read(folder/'execution.json'), read(folder/'legacy.json')
        assert completed[entry['id']]['status']==q['status'] and completed[entry['id']]['returncode']==0
        assert e['collection_plan_sha256']==sha(collection/'COLLECTION_PLAN.json')
        obs, action, time = history(folder)
        with np.load(folder/'legacy.npz', allow_pickle=False) as trace:
            position, target, obj = [trace[n].copy() for n in ('position','target','object_position')]
        speed = np.linalg.norm(np.diff(obj,axis=0)/.04,axis=1)
        error = np.linalg.norm(position-target,axis=1)
        lift = float(obj[-1,2]-.425)
        motion = float(speed[-9:].max())
        terminal_checks = dict(lift_over_10cm=lift>.10, last9_speed_under_002=motion<.02,
            mean_last10_error_under_15mm=float(error[-10:].mean())<.015,
            valid_physics=not legacy['invalid_physics'], no_upstream_contact=not legacy['upstream_contact'],
            final_stage=legacy['final_stage']==5)
        # These registered ball conditions have no cup. No generic cup gate is dropped.
        assert legacy['cup_initial_position'] is None and legacy['cup_safe'] and legacy['cup_stable']
        assert all(terminal_checks.values())==legacy['success']==q['task_success']
        assert (terminal_checks['lift_over_10cm'] and terminal_checks['last9_speed_under_002'])==legacy['grasp_lift_success']
        row = dict(id=entry['id'], split=entry['split'], qualification=q['status'],
            task_success=q['task_success'], safety_valid=q['safety_valid'], contact_valid=q['scene_contact_valid'],
            terminal_checks=terminal_checks, lift_m=lift, last9_speed_max_mps=motion,
            mean_last10_error_m=float(error[-10:].mean()),
            inputs={n:sha(folder/n) for n in ('execution.json','trajectory.npz','legacy.npz','legacy.json',
                'teacher.json','DEMONSTRATION_QUALIFICATION.json','INDEPENDENT_AUDIT.json')})
        if entry['split']=='train':
            actor = ParameterTeacher(read(folder/'teacher.json'))
            components = []
            for o, expected in zip(obs, action):
                actor.observe(o); actual = actor.act(o[39:45])
                np.testing.assert_array_equal(actual, expected)
                activation=actor.recovery_memory*min(1.,np.linalg.norm(o[45:47]))**2
                base_z=actor.raw_action[3]*actor.channel_gain[3]
                assert actor.velocity_weight==1., 'This decomposition binds the actual full-velocity teacher'
                base=(1-activation)*base_z
                components.append([activation,base,actual[3]-base,actual[3],o[22],o[16]-o[28],o[41]])
            component=np.asarray(components)
            row.update(last250_speed_rms_mps=float(np.sqrt(np.mean(speed[-250:]**2))),
                last250_speed_max_mps=float(speed[-250:].max()),
                last250_component_std=component[-250:].std(axis=0).tolist(),
                exact_actor_replay=True)
            arrays[entry['id']+'_time']=time
            arrays[entry['id']+'_speed']=speed
            arrays[entry['id']+'_components']=component
        rows.append(row)
    ranked=sorted((r for r in rows if r['split']=='train'),key=lambda r:(-r['last250_speed_rms_mps'],r['id']))
    output.mkdir(parents=True)
    np.savez_compressed(output/'training_curves.npz',**arrays)
    fig,axes=plt.subplots(2,1,figsize=(11,7),layout='constrained')
    for row in rows:
        if row['split']!='train':continue
        key=row['id'];t=arrays[key+'_time']
        axes[0].plot(t[1:],arrays[key+'_speed'],label=key,lw=1)
    axes[0].axhline(.02,color='black',ls='--',label='original terminal-window speed criterion')
    axes[0].set_ylabel('Object speed (m/s)');axes[0].legend(ncol=3,fontsize=8)
    key=ranked[0]['id'];c=arrays[key+'_components'];t=arrays[key+'_time']
    for j,label in ((1,'base contribution'),(2,'recovery contribution'),(3,'requested z action')):
        axes[1].plot(t,c[:,j],label=label,lw=1)
    axes[1].set_ylabel('Normalized z action');axes[1].legend(fontsize=8)
    axes[1].set_title(key+' = highest last250 speed RMS among 8 training identities')
    for ax in axes:
        ax.set_xlim(20,30);ax.set_xlabel('Saved physical time (s)');ax.grid(alpha=.2)
    fig.suptitle('Actual teacher training traces: '+collection.name+'\n'
                 'Terminal acceptance is not whole-tail stability')
    fig.savefig(output/'training_ball_tail.png',dpi=160);plt.close(fig)
    result=dict(status='all10_gate_recomputed_failures_preserved',rows=rows,
        training_tail_rms_rank=[r['id'] for r in ranked],
        component_columns=['recovery_activation','base_z_contribution','recovery_z_contribution',
                           'requested_z_action','reference_minus_hand_z_m','actual_hand_z_mps','estimated_force_z_n'],
        plan_sha256=sha(collection/'COLLECTION_PLAN.json'),source_sha256=sha(Path(__file__)),
        helper_sha256=sha(ROOT/'tools/review_repaired_student_closures_20261029.py'),
        actor_sha256=sha(ROOT/'tools/optimize_tool_contact_20261002.py'),
        array_sha256=sha(output/'training_curves.npz'),plot_sha256=sha(output/'training_ball_tail.png'),
        limitation='Original terminal gate only on validation, no validation curves or parameter ranking. '
        'Training last250 speed ranking is post-hoc diagnostic, not a new qualification gate or proof of damping causality. '
        'No physics, fitting, source modification or removal of failures. Not a complete30 certificate.')
    write(output/'REVIEW.json',result)
    print([(r['id'],r['qualification'],r['last9_speed_max_mps']) for r in rows])
    print('training_tail_rms_rank',result['training_tail_rms_rank'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--collection',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();audit(args.collection.resolve(),args.output.resolve())
