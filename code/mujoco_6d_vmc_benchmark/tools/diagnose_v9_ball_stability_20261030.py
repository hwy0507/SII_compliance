"""Compare completed development ball failures and successes; no fitting/tests."""
import argparse
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current
from review_v9_paired_scene_closure_20261029 import verify_qualification
from run_video_reference_coverage_20261029 import make_actor


def teacher_predictions(config,observations):
    actor=make_actor(config);result=[]
    for observation in observations:
        actor.observe(observation);result.append(actor.act(observation[39:45],.04))
    return np.asarray(result)


def summarize(label,folder):
    q=verify_qualification(folder,sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
    legacy=read(folder/'legacy.json')
    with np.load(folder/'legacy.npz',allow_pickle=False) as z:
        time=z['time'].copy();stage=z['stage'].copy();position=z['object_position'].copy()
        error=np.linalg.norm(z['position']-z['target'],axis=1)
    with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
        np.testing.assert_array_equal(time,z['time']);observations=z['observation'].copy();actions=z['action'].copy()
    config=read(folder/'teacher.json');predictions=teacher_predictions(config,observations)
    if (folder/'student_checkpoint.npz').exists():
        actor=load_current(folder/'student_checkpoint.npz');actor.reset()
        replay=np.asarray([actor.act(o) for o in observations]);np.testing.assert_array_equal(replay,actions)
    else:np.testing.assert_array_equal(predictions,actions)
    speed=np.linalg.norm(np.diff(position,axis=0)/.04,axis=1)
    lift=float(position[-1,2]-.425);motion=float(speed[-9:].max())
    checks=dict(lift=lift>.10,payload_motion=motion<.02,tracking_error=float(error[-10:].mean())<.015,
        valid_physics=not legacy['invalid_physics'],no_upstream=not legacy['upstream_contact'],terminal_stage=int(stage[-1])==5,cup_stable=legacy['cup_stable'])
    assert all(checks.values())==legacy['success']
    tail=time>=time[-1]-5
    return dict(label=label,folder=str(folder),task_success=q['task_success'],qualified=q['status']=='qualified',
        original_task_checks=checks,last10_payload_motion_max_mps=motion,last10_tracking_error_mean_m=float(error[-10:].mean()),
        tail5_requested_residual_rms=float(np.sqrt(np.mean(actions[tail,1:]**2))),
        tail5_counterfactual_teacher_residual_rms=float(np.sqrt(np.mean(predictions[tail,1:]**2))),
        tail5_counterfactual_action_mse=float(np.mean((actions[tail]-predictions[tail])**2)),
        saturation_fraction=float(np.mean(np.any(np.abs(actions[:,1:])>=.999,axis=1))),
        first_observation=observations[0].tolist(),model_sha256=sha(folder/'scene.mjb'),
        input_hashes={name:sha(folder/name)for name in ['trajectory.npz','legacy.npz','legacy.json','teacher.json','DEMONSTRATION_QUALIFICATION.json']})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    plan=read(ROOT/'outputs/special_scene_direction_collection_20261029_v9/COLLECTION_PLAN.json')
    teacher={i:Path(next(e['folder']for e in plan['episodes']if e['id']=='ball_'+i))for i in ('00','09')}
    paired=ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5'
    common=ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/evaluations'
    groups=[dict(identity='ball_00',split='train',episodes=[('teacher',teacher['00']),('rnn_seed01_failed',paired/'ball_00_rnn_scratch/ball'),('mlp_seed01_passed',paired/'ball_00_mlp_scratch/ball')]),
        dict(identity='ball_09',split='validation',episodes=[('teacher',teacher['09']),('esn_seed01_rank2_failed',common/'esn_ridge_s2026102801_rank2/ball_09/ball'),('esn_seed02_rank1_passed',common/'esn_ridge_s2026102802_rank1/ball_09/ball')])]
    rows=[]
    for group in groups:
        summaries=[summarize(label,folder)for label,folder in group['episodes']]
        for s in summaries[1:]:
            assert s['model_sha256']==summaries[0]['model_sha256']
            np.testing.assert_array_equal(s['first_observation'],summaries[0]['first_observation'])
        rows.append(dict(identity=group['identity'],split=group['split'],same_initial_canonical48_and_mjb=True,episodes=summaries))
    write(a.output,dict(status='development_stability_comparison_no_new_physics',source_sha256=sha(Path(__file__)),groups=rows,
        limitations=['Counterfactual teacher acts on saved student history without dynamics execution; neither recovery proof nor training labels.',
            'Histories differ after the shared initial state; cross-history MSE is not a common-input accuracy ranking.',
            'Original task/safety gates retained. Training/validation cases only; no new final test or fitting.',
            'Passing one seed does not prove all seeds or whole matrix repaired.']))
    print([(g['identity'],[(s['label'],s['qualified'],s['last10_payload_motion_max_mps'],s['tail5_counterfactual_action_mse'])for s in g['episodes']])for g in rows])


if __name__=='__main__':main()
