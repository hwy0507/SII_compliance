"""Review all 18 development closures without fitting or inventing test metrics.

Teacher-on-student-history predictions are counterfactual actor outputs, not
physical teacher rollouts and never training labels. Keep failures visible.
"""
import argparse
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current
from review_special_regression_controls_20261028 import error_summary
from run_video_reference_coverage_20261029 import make_actor


def verify_qualification(folder, digest):
    p = folder/'DEMONSTRATION_QUALIFICATION.json'
    assert sha(p) == digest
    qualification = read(p)
    for name, expected in qualification['input_hashes'].items():
        assert sha(folder/name) == expected, str(folder/name)
    return qualification


def load_trajectory(folder):
    with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
        obs, act, time = (z[k].copy() for k in ('observation', 'action', 'time'))
    assert obs.shape == (len(time), 48) and act.shape == (len(time), 7)
    assert np.isfinite(obs).all() and np.isfinite(act).all()
    return obs, act, time


def review(root, output):
    assert not output.exists(), 'Preserve previous reviews'
    reg, state = read(root/'REGISTRATION.json'), read(root/'execution.json')
    assert state['status'] == 'complete_pending_review'
    assert len(state['rows']) == reg['maximum_episodes'] == len(reg['cases']) == 18
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    assert reg['wrapper'] == 'run_video_reference_coverage_20261029.py'
    for name, digest in reg['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    rows = []
    for case, receipt in zip(reg['cases'], state['rows']):
        assert case['id'] == receipt['id'] and receipt['returncode'] == 0
        folder = root/case['id']/case['scene']
        teacher_folder = Path(case['teacher_reference'])
        student_q = verify_qualification(folder, receipt['qualification_sha256'])
        teacher_q = verify_qualification(teacher_folder, case['qualification_sha256'])
        execution = read(folder/'execution.json')
        baseline_execution = read(teacher_folder/'execution.json')
        assert sha(teacher_folder/'execution.json') == case['teacher_execution_sha256']
        assert execution['model_sha256'] == baseline_execution['model_sha256'] == case['physics_model_sha256']
        assert execution['filter_config'] == baseline_execution['filter_config']
        assert sha(folder/'teacher.json') == case['config_sha256']
        assert sha(folder/'student_checkpoint.npz') == case['model']['checkpoint_sha256']
        for name, value in case['parameters'].items():
            assert execution['experiment_environment'][name] == str(value)
            assert baseline_execution['experiment_environment'][name] == str(value)
        obs, act, time = load_trajectory(folder)
        teacher_obs, teacher_act, teacher_time = load_trajectory(teacher_folder)
        model = load_current(folder/'student_checkpoint.npz')
        model.reset()
        replay = np.asarray([model.act(o) for o in obs])
        np.testing.assert_array_equal(replay, act)
        model.reset()
        imitation = np.asarray([model.act(o) for o in teacher_obs])
        teacher = make_actor(read(folder/'teacher.json'))
        teacher_predictions = []
        for o in obs:
            teacher.observe(o)
            teacher_predictions.append(teacher.act(o[39:45], .04))
        row = dict(id=case['id'], scene=case['scene'], split=case['split'],
            family=case['model']['family'], seed=case['model']['seed'],
            task_success=student_q['task_success'], development_safety_valid=student_q['safety_valid'],
            scene_behavior_valid=student_q['scene_contact_valid'],
            development_qualified=student_q['status'] == 'qualified',
            teacher_task_success=teacher_q['task_success'], teacher_qualified=teacher_q['status'] == 'qualified',
            student_metrics=student_q['metrics'], teacher_metrics=teacher_q['metrics'],
            student_on_teacher_history=error_summary(imitation, teacher_act, teacher_time),
            teacher_counterfactual_on_student_history=error_summary(np.asarray(teacher_predictions), act, time),
            residual_saturation_fraction=float(np.mean(np.any(np.abs(act[:, 1:]) >= .999, axis=1))),
            checkpoint_sha256=sha(folder/'student_checkpoint.npz'), trajectory_sha256=sha(folder/'trajectory.npz'),
            qualification_sha256=receipt['qualification_sha256'],
            teacher_trajectory_sha256=sha(teacher_folder/'trajectory.npz'))
        if case['scene'] == 'rod':
            row['rod_behavior'] = read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
            row['teacher_rod_behavior'] = read(teacher_folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        rows.append(row)
    groups = []
    for family in ('esn_ridge', 'rnn_scratch', 'mlp_scratch'):
        for split in ('train', 'validation'):
            group = [r for r in rows if r['family'] == family and r['split'] == split]
            assert len(group) == 3
            groups.append(dict(family=family, split=split, episodes=len(group),
                task_success=sum(r['task_success'] for r in group),
                development_qualified=sum(r['development_qualified'] for r in group),
                peak_torque_mean_nm=float(np.mean([max(r['student_metrics']['peak_torque_nm']) for r in group]))))
    result = dict(schema='sii-v9-paired-scene-closure-review-v1', status='complete_development_review',
        created_utc=datetime.now(timezone.utc).isoformat(), rows=rows, groups=groups,
        registration_sha256=sha(root/'REGISTRATION.json'), execution_sha256=sha(root/'execution.json'),
        reviewer_sha256=sha(Path(__file__)),
        limitations=['These are train and previously selected validation identities, not unseen tests.',
            'Original scene tasks differ from the office placement task. Development safety/qualification is not frozen office Strict.',
            'No completion-hold telemetry is inferred from final success; no SPT is fabricated.',
            'Disturbance comfort proxy is not measured human comfort; no-contact remains null.',
            'Counterfactual teacher actions are not dynamically executed actions or labels for fitting.'])
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, result)
    print(groups)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    review(a.root.resolve(), a.output.resolve())
