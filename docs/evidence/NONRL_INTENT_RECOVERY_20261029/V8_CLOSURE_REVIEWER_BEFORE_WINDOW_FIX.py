"""Review all18 paired real-scene student closures, preserving every failure.

Separates exported-actor correctness, imitation on teacher histories, and
teacher counterfactuals on student histories. No fitting or physical rollout.
The latter counterfactual is not an executed teacher trajectory or a label
for further fitting. Validation diagnostics never select another checkpoint.
"""
import argparse
from collections import Counter
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current
from optimize_tool_contact_20261002 import ParameterTeacher


def error_stats(prediction, target):
    assert prediction.shape == target.shape and target.ndim == 2 and target.shape[1] == 7
    assert np.isfinite(prediction).all() and np.isfinite(target).all()
    if not len(target):
        return dict(frames=0, mse=None, channel_rmse=None, channel_bias=None, max_abs=None)
    delta = prediction - target
    return dict(frames=len(target), mse=float(np.mean(delta**2)),
                channel_rmse=np.sqrt(np.mean(delta**2, axis=0)).tolist(),
                channel_bias=delta.mean(axis=0).tolist(), max_abs=float(np.abs(delta).max()))


def history(folder):
    with np.load(folder/'trajectory.npz', allow_pickle=False) as z:
        obs, action, time = (z[k].copy() for k in ('observation', 'action', 'time'))
    assert obs.shape == (len(action), 48) and action.shape == (len(time), 7) and len(time)
    assert np.isfinite(obs).all() and np.isfinite(action).all() and np.isfinite(time).all()
    np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=1e-8)
    return obs, action, time


def teacher_replay(config, observations):
    teacher = ParameterTeacher(config)
    teacher.reset()
    actions, activation = [], []
    for obs in observations:
        teacher.observe(obs)
        actions.append(teacher.act(obs[39:45], .04))
        activation.append(teacher.recovery_memory * min(1., np.linalg.norm(obs[45:47]))**2)
    return np.asarray(actions), np.asarray(activation)


def qualification(folder):
    q = read(folder/'DEMONSTRATION_QUALIFICATION.json')
    for name, digest in q['input_hashes'].items():
        assert sha(folder/name) == digest, str(folder/name)
    audit = read(folder/'INDEPENDENT_AUDIT.json')
    assert audit['status'] == 'passed'
    for name, digest in audit['input_hashes'].items():
        assert sha(folder/name) == digest, str(folder/name)
    return q


def review(root, output):
    assert not output.exists(), 'Preserve existing review'
    # Reject before opening model/output files when the original18 are unfinished.
    assert (root/'execution.json').exists(), 'Original18 have not started'
    state = read(root/'execution.json')
    assert state['status'] == 'complete_pending_review', 'Original18 incomplete'
    prep, reg = read(root/'PREPARATION.json'), read(root/'REGISTRATION.json')
    assert reg['schema'] == 'sii-repaired-student-scene-closure-v1'
    assert state['registration_sha256'] == sha(root/'REGISTRATION.json')
    assert reg['preparation_sha256'] == sha(root/'PREPARATION.json')
    assert reg['fit_audit_sha256'] == sha(root/'FIT_AUDIT.json')
    fit = read(root/'FIT_AUDIT.json')
    assert fit['status'] == 'passed'
    training = Path(prep['training'])
    assert sha(training/'MODEL_LOCK.json') == reg['model_lock_sha256'] == fit['model_lock_sha256']
    models = read(training/'MODEL_LOCK.json')['models']
    for name, digest in prep['source_sha256'].items():
        assert sha(ROOT/name) == digest, name
    for name, digest in reg['config_sha256'].items():
        assert sha(Path(name)) == digest, name
    assert len(reg['cases']) == len(state['episodes']) == reg['maximum_episodes'] == 18
    expected = Counter((e['id'], f) for e in prep['identities'] for f in prep['families'])
    assert Counter((c['identity'], c['model']['family']) for c in reg['cases']) == expected
    identities = {e['id']: e for e in prep['identities']}
    rows = []
    for case, receipt in zip(reg['cases'], state['episodes']):
        assert receipt['id'] == case['id'] and receipt['returncode'] == 0
        assert case['model'] in models and case['model']['seed'] == prep['model_seed']
        entry = identities[case['identity']]
        assert all(case[k] == entry[k] for k in ('scene', 'split', 'seed', 'scene_parameters'))
        student_folder = root/case['id']/case['scene']
        teacher_folder = Path(reg['teacher_references'][case['identity']]['folder'])
        assert teacher_folder == Path(case['baseline'])
        assert teacher_folder == Path(entry['folder'])
        tq, sq = qualification(teacher_folder), qualification(student_folder)
        assert tq['status'] == 'qualified'
        assert sha(teacher_folder/'DEMONSTRATION_QUALIFICATION.json') == reg['teacher_references'][case['identity']]['qualification_sha256']
        assert sha(student_folder/'DEMONSTRATION_QUALIFICATION.json') == receipt['qualification_sha256']
        te, se = read(teacher_folder/'execution.json'), read(student_folder/'execution.json')
        assert sha(teacher_folder/'execution.json') == case['baseline_execution_sha256']
        assert te['status'] == se['status'] == 'complete'
        assert te['controller_role'] == 'teacher' and se['controller_role'] == 'student_diagnostic'
        assert te['model_sha256'] == se['model_sha256'] == case['expected_model_sha256']
        assert te['filter_config'] == se['filter_config']
        assert te['physics_dt_s'] == se['physics_dt_s'] == .00005
        for key, value in case['scene_parameters'].items():
            assert te['experiment_environment'][key] == se['experiment_environment'][key] == str(value)
        assert te['experiment_environment']['VMC_SCENE_SEED'] == se['experiment_environment']['VMC_SCENE_SEED'] == str(case['seed'])
        assert sha(teacher_folder/'teacher.json') == sha(student_folder/'teacher.json')
        checkpoint = student_folder/'student_checkpoint.npz'
        assert sha(checkpoint) == case['model']['checkpoint_sha256']
        tobs, taction, ttime = history(teacher_folder)
        sobs, saction, stime = history(student_folder)
        config = read(teacher_folder/'teacher.json')
        tpred, activation = teacher_replay(config, tobs)
        np.testing.assert_array_equal(tpred, taction)
        actor = load_current(checkpoint)
        actor.reset()
        sactual = np.asarray([actor.act(o) for o in sobs])
        np.testing.assert_array_equal(sactual, saction)
        actor.reset()
        imitation = np.asarray([actor.act(o) for o in tobs])
        counterfactual, _ = teacher_replay(config, sobs)
        windows = []
        for start in np.arange(0, float(ttime[-1]), 2.):
            mask = (ttime > start) & (ttime <= start + 2. + 1e-8)
            if mask.any():
                windows.append(dict(start_s=float(start), end_s=float(start+2.),
                                    **error_stats(imitation[mask], taction[mask])))
        active = activation > .5
        row = dict(id=case['id'], scene=case['scene'], split=case['split'],
            family=case['model']['family'], teacher_qualification=tq, student_qualification=sq,
            teacher_and_student_exact_actor_replay=True,
            teacher_history_imitation=error_stats(imitation, taction),
            teacher_history_windows=windows,
            teacher_history_recovery_over_half=error_stats(imitation[active], taction[active]),
            teacher_history_remaining=error_stats(imitation[~active], taction[~active]),
            counterfactual_teacher_on_student_history=error_stats(counterfactual, saction),
            teacher_frames=len(tobs), student_frames=len(sobs),
            checkpoint_sha256=sha(checkpoint),
            source_hashes={label:{name:sha(folder/name) for name in ('trajectory.npz','execution.json',
                'DEMONSTRATION_QUALIFICATION.json','INDEPENDENT_AUDIT.json','teacher.json')}
                for label,folder in (('teacher',teacher_folder),('student',student_folder))})
        if case['scene'] == 'rod':
            row['student_rod_behavior'] = read(student_folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
            for name, digest in row['student_rod_behavior']['hashes'].items():
                path = ROOT/'tools'/name if name.endswith('.py') else student_folder/name
                assert sha(path) == digest, str(path)
        rows.append(row)
    result = dict(status='complete18_diagnostics_not_success_certification', rows=rows,
        qualified_students=sum(r['student_qualification']['status']=='qualified' for r in rows),
        registration_sha256=sha(root/'REGISTRATION.json'), execution_sha256=sha(root/'execution.json'),
        fit_audit_sha256=sha(root/'FIT_AUDIT.json'), reviewer_sha256=sha(Path(__file__)),
        limitation='All18 are training00/validation08 development identities, not final108 or unseen data. '
        'No new simulation, fitting, model selection or gate change. The .5 recovery split and 2s windows '
        'are descriptive, not acceptance gates. Teacher predictions on student histories are counterfactual '
        'and cannot establish physical outcomes or a causal attribution. Every student failure is retained.')
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, result)
    print(result['status'], 'qualified', result['qualified_students'], '/18')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    review(args.root.resolve(), args.output.resolve())
