"""Check diagnostic partitioning, not the pending complete18 review or dynamics."""
import ast
import math
from pathlib import Path

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_repaired_student_closures_20261029 import diagnostic_windows, history, review


def check(time, action):
    # Known nonconstant errors expose duplicated or omitted boundary samples.
    delta = np.arange(action.size, dtype=float).reshape(action.shape) / action.size
    prediction = action + delta
    windows = diagnostic_windows(time, prediction, action)
    coverage = np.zeros(len(time), dtype=int)
    for w in windows:
        start, end = w['start_index'], w['end_index_exclusive']
        coverage[start:end] += 1
        residual = prediction[start:end] - action[start:end]
        mse = math.fsum(float(x)**2 for x in residual.flat) / residual.size
        assert math.isclose(mse, w['mse'], rel_tol=1e-12, abs_tol=1e-20)
        assert w['frames'] == end - start
    assert np.all(coverage == 1)
    assert len(windows) == math.ceil(len(time) / 50)
    assert windows[-1]['end_s'] == len(time) * .04
    return dict(frames=len(time), windows=len(windows), tail_frames=windows[-1]['frames'],
                end_s=windows[-1]['end_s'], exactly_once=True, scalar_mse_checked=True)


def main():
    output = ROOT/'outputs/special_scene_closure_window_checks_20261029_v8/REVIEW.json'
    assert not output.exists(), 'Preserve receipts'
    old = ROOT.parent.parent/'docs/evidence/NONRL_INTENT_RECOVERY_20261029/V8_CLOSURE_REVIEWER_BEFORE_WINDOW_FIX.py'
    current = ROOT/'tools/review_repaired_student_closures_20261029.py'
    trees = [ast.parse(p.read_text()) for p in (old, current)]
    for name in ('error_stats', 'history', 'teacher_replay', 'qualification'):
        nodes = [next(n for n in t.body if isinstance(n, ast.FunctionDef) and n.name == name) for t in trees]
        assert ast.dump(nodes[0]) == ast.dump(nodes[1]), name
    synthetic = []
    for n in (500, 750, 325):
        for drift in (0., 1e-9, -1e-9):
            time = np.arange(1, n+1) * .04 + np.linspace(0, drift, n)
            synthetic.append(dict(drift=drift, **check(time, np.zeros((n, 7)))))
    rejected = []
    for label, time in (('empty', np.array([])), ('wrong_origin', np.arange(50)*.04),
                        ('wrong_dt', np.arange(1,51)*.05), ('nonfinite', np.array([np.nan]))):
        try:
            diagnostic_windows(time, np.zeros((len(time),7)), np.zeros((len(time),7)))
        except AssertionError:
            rejected.append(label)
        else:
            raise AssertionError(label)
    training = ROOT/'outputs/special_scene_retrain_20261029_v8'
    metadata = read(training/'data/DATA_COMPLETE.json')
    actual = []
    for entry in metadata['lineage']:
        if entry['split'] != 'train':
            continue
        folder = Path(entry['folder'])
        _, action, time = history(folder)
        actual.append(dict(id=entry['id'], trajectory_sha256=sha(folder/'trajectory.npz'),
                           **check(time, action)))
    assert len(actual) == 24
    root = ROOT/'outputs/special_scene_student_closure_20261029_v8'
    assert not (root/'execution.json').exists(), 'Only exercise unstarted18 guard here'
    try:
        review(root, output)
    except AssertionError as exc:
        assert str(exc) == 'Original18 have not started'
    else:
        raise AssertionError('Unstarted18 accepted')
    assert not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    write(output, dict(status='partition_checks_passed_complete18_pending', synthetic=synthetic,
        actual_training_histories=actual, rejected=rejected, unchanged_shared_helpers=True,
        incomplete18_rejected_without_output=True, old_reviewer_sha256=sha(old),
        reviewer_sha256=sha(current), check_source_sha256=sha(Path(__file__)),
        initial_attempt_failure='All arithmetic checks passed but receipt write failed because parent '
            'directory did not exist; no receipt or model changes. Added parent mkdir and reran checks.',
        limitation='Synthetic errors test arithmetic only. Actual training timestamps/actions check '
                   'partitioning; no fitting, student dynamics, validation diagnosis or full18 positive path.'))
    print(output)


if __name__ == '__main__':
    main()
