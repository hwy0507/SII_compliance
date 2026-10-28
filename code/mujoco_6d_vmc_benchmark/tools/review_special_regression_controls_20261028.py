"""Audit complete matched controls and quantify offline imitation drift.

Teacher predictions on student observations are diagnostic counterfactuals,
not executed actions or training labels. This review never fits a model.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import read, sha, write
from current_student_policy_20260921 import load_current
from optimize_tool_contact_20261002 import ParameterTeacher


def error_summary(prediction, target, time):
    error = prediction-target
    windows = []
    for start in np.arange(0, float(time[-1]), 2.):
        ids = (time > start) & (time <= start+2.+1e-8)
        if ids.any():
            windows.append(dict(start_s=float(start), end_s=float(start+2.),
                                mse=float(np.mean(error[ids]**2)),
                                max_abs=float(np.max(np.abs(error[ids])))))
    return dict(mse=float(np.mean(error**2)), max_abs=float(np.max(np.abs(error))),
                channel_rmse=np.sqrt(np.mean(error**2, axis=0)).tolist(), windows=windows)


def review(root, output):
    if output.exists():
        raise FileExistsError(output)
    reg, state = read(root/'REGISTRATION.json'), read(root/'execution.json')
    assert state['status'] == 'complete_pending_review'
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    assert len(state['episodes']) == reg['maximum_episodes'] == 10
    source = Path(__file__).resolve().parents[1]
    for name, digest in reg['source_sha256'].items():
        assert sha(source/name) == digest, name
    rows = []
    for case, receipt in zip(reg['cases'], state['episodes']):
        assert case['id'] == receipt['id'] and receipt['returncode'] == 0
        if case['kind'] == 'office':
            folder = root/case['id']
            assert sha(folder/'AUDIT.json') == receipt['audit_sha256']
            audit = read(folder/'AUDIT.json')
            rows.append(dict(id=case['id'], audit=audit, audit_sha256=receipt['audit_sha256']))
            continue
        folder = root/case['id']/case['scene']
        qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
        assert sha(folder/'DEMONSTRATION_QUALIFICATION.json') == receipt['qualification_sha256']
        for name, digest in qualification['input_hashes'].items():
            assert sha(folder/name) == digest, str(folder/name)
        execution = read(folder/'execution.json')
        assert execution['model_sha256'] == case['expected_model_sha256']
        assert execution['filter_config']['maximum_linear_yield_mps'] == .32
        row = dict(id=case['id'], qualification=qualification,
                   qualification_sha256=receipt['qualification_sha256'],
                   model_sha256=execution['model_sha256'])
        if case['model']:
            teacher_folder = root/(case['scene']+'_teacher')/case['scene']
            with np.load(teacher_folder/'trajectory.npz', allow_pickle=False) as z:
                obs, act, time = (z[k].copy() for k in ('observation', 'action', 'time'))
            model = load_current(folder/'student_checkpoint.npz')
            model.reset()
            prediction = np.asarray([model.act(o) for o in obs])
            row['student_on_new_teacher_history'] = error_summary(prediction, act, time)
            with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
                obs, act, time = (z[k].copy() for k in ('observation', 'action', 'time'))
            teacher = ParameterTeacher(read(folder/'teacher.json'))
            teacher.reset()
            expected = []
            for o in obs:
                teacher.observe(o)
                expected.append(teacher.act(o[39:45], .04))
            row['teacher_counterfactual_on_student_history'] = error_summary(np.asarray(expected), act, time)
            with np.load(Path(case['baseline'])/'trajectory.npz', allow_pickle=False) as z:
                old_obs, old_act, old_time = (z[k].copy() for k in ('observation', 'action', 'time'))
            model.reset()
            pred = np.asarray([model.act(o) for o in old_obs])
            row['student_on_original_training_history'] = error_summary(pred, old_act, old_time)
            row['baseline_trajectory_sha256'] = sha(Path(case['baseline'])/'trajectory.npz')
            row['checkpoint_sha256'] = sha(folder/'student_checkpoint.npz')
            assert row['checkpoint_sha256'] == case['model']['checkpoint_sha256']
        if case['scene'] == 'rod':
            row['rod_behavior'] = read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        rows.append(row)
    first, second = rows[:2]
    assert first['audit']['model_sha256'] == second['audit']['model_sha256']
    commands = [c['command'] for c in reg['cases'][:2]]
    assert commands[0] == commands[1]
    assert reg['cases'][0]['kind'] == reg['cases'][1]['kind'] == 'office'
    result = dict(schema='sii-complete-regression-control-review-v1',
                  registration_sha256=sha(root/'REGISTRATION.json'),
                  execution_sha256=sha(root/'execution.json'),
                  review_source_sha256=sha(Path(__file__)), rows=rows,
                  office_pair_same_registered_command=True,
                  limitations='One identity per scene and one already-inspected office condition, not the final108 or unseen generalization. New corner teacher uses corrected scale, old ESN was fitted on mixed scales. Counterfactual teacher-on-student predictions are not physical teacher actions and never enter training.')
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, result)
    print(json.dumps([dict(id=r['id'], task=r.get('audit',r.get('qualification',{}))['task_success'],
                           new_history_mse=r.get('student_on_new_teacher_history',{}).get('mse'),
                           original_history_mse=r.get('student_on_original_training_history',{}).get('mse')) for r in rows], indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    review(a.root.resolve(), a.output.resolve())
