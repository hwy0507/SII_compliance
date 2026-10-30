"""Completed train00 paired prefix only; no fitting or physical integration."""
import json
from pathlib import Path
import numpy as np
from current_student_policy_20260921 import load_current
from run_video_reference_coverage_20261029 import make_actor, sha

ROOT = Path.cwd()
RUN = ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5'
registration = json.loads((RUN/'REGISTRATION.json').read_text())
state_bytes = (RUN/'execution.json').read_bytes()
state = json.loads(state_bytes)
result = []
for case in registration['cases']:
    receipt = next((r for r in state['rows'] if r['id'] == case['id']), None)
    if not receipt or 'qualification_sha256' not in receipt or case['identity'] != 'rod_00':
        continue
    folder = RUN/case['id']/case['scene']
    teacher_folder = Path(case['teacher_reference'])
    assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == receipt['qualification_sha256']
    q = json.loads((folder/'DEMONSTRATION_QUALIFICATION.json').read_text())
    for name, digest in q['input_hashes'].items():assert sha(folder/name) == digest
    with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
        obs, action, time = (z[k].copy() for k in ('observation', 'action', 'time'))
    with np.load(teacher_folder/'trajectory.npz', allow_pickle=False) as z:
        reference, labels = (z[k].copy() for k in ('observation', 'action'))
    policy = load_current(folder/'student_checkpoint.npz')
    replay = np.asarray([policy.act(o) for o in obs])
    np.testing.assert_array_equal(replay, action)
    policy.reset()
    on_teacher = np.asarray([policy.act(o) for o in reference])
    def expert(history):
        actor = make_actor(json.loads((folder/'teacher.json').read_text()))
        values = []
        for o in history:
            actor.observe(o)
            values.append(actor.act(o[39:45], .04))
        return np.asarray(values)
    teacher_replay = expert(reference)
    np.testing.assert_array_equal(teacher_replay, labels)
    counterfactual = expert(obs)
    disagreement = np.max(np.abs(counterfactual[:, 1:]-action[:, 1:]), axis=1)
    first = lambda mask: float(time[np.flatnonzero(mask)[0]]) if np.any(mask) else None
    execution = json.loads((folder/'execution.json').read_text())
    result.append(dict(id=case['id'], family=case['model']['family'], split=case['split'],
        same_mjb=execution['model_sha256'] == case['physics_model_sha256'],
        initial_observation_max_abs_difference=float(np.max(np.abs(obs[0]-reference[0]))),
        teacher_replay_max_abs=0., student_replay_max_abs=0.,
        student_on_teacher_history_mse=float(np.mean((on_teacher-labels)**2)),
        teacher_counterfactual_on_student_history_mse=float(np.mean((counterfactual-action)**2)),
        first_residual_disagreement_gt_0p1_s=first(disagreement > .1),
        first_residual_disagreement_gt_0p5_s=first(disagreement > .5),
        first_requested_residual_saturation_s=first(np.any(np.abs(action[:,1:]) >= .999, axis=1)),
        requested_residual_saturation_fraction=float(np.mean(np.any(np.abs(action[:,1:]) >= .999, axis=1))),
        task_success=q['task_success'], development_safety_valid=q['safety_valid'],
        development_contact_valid=q['scene_contact_valid'],
        trajectory_sha256=sha(folder/'trajectory.npz'), qualification_sha256=receipt['qualification_sha256'],
        checkpoint_sha256=sha(folder/'student_checkpoint.npz')))
assert result
output = Path(__file__).with_name('PAIRED_PREFIX_ANALYSIS.json')
assert not output.exists()
output.write_text(json.dumps(dict(status='completed_train00_prefix_diagnostic_only',
    snapshot_completed_qualified_rows=sum('qualification_sha256' in r for r in state['rows']),
    registration_sha256=sha(RUN/'REGISTRATION.json'), source_sha256=sha(Path(__file__)),
    caveats=['This is an incomplete 18-case development prefix, not a final comparison.',
             'Counterfactual teacher output is not a physical recovery proof or training label.',
             'Different student histories: counterfactual MSE is not a common-input method ranking.'],
    rows=result), indent=2)+'\n')
print(json.dumps(result, indent=2))
