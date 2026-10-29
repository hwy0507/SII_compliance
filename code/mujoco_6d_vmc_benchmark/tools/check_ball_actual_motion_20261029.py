"""Hand-computable motion checks; never used as physical demonstrations."""
import json
import argparse
import math
from pathlib import Path
import numpy as np

from describe_ball_actual_motion_20261029 import describe, sha


def check():
    time = .04*np.arange(1, 7)
    stage = np.array([3, 3, 4, 4, 5, 5])
    hand = np.array([[0, 0, .6], [0, 0, .6], [.02, 0, .6],
                     [.08, 0, .6], [.04, 0, .6], [0, 0, .6]])
    obj = hand - [0, 0, .1]
    target = np.array([[0, 0, .6], [0, 0, .6], [.085, 0, .6],
                       [.085, 0, .6], [0, 0, .6], [0, 0, .6]])
    rows = describe(time, stage, hand, obj, target)
    assert rows[0] == dict(stage=0, name='approach', frames=0, reached=False)
    carry, recovery = rows[2:]
    np.testing.assert_allclose(carry['commanded_goal_displacement_m'], [.085, 0, 0], atol=1e-14)
    np.testing.assert_allclose(carry['object_displacement_m'], [.08, 0, 0], atol=1e-14)
    np.testing.assert_allclose(carry['relative_position_drift_max_m'], 0, atol=1e-14)
    np.testing.assert_allclose(recovery['object_projection_on_goal_displacement_m'], .08, atol=1e-14)
    stationary = np.repeat(obj[:1], 6, axis=0)
    missing_carry = describe(time, stage, hand, stationary, target)[2]
    assert missing_carry['object_projection_on_goal_displacement_m'] == 0
    np.testing.assert_allclose(missing_carry['relative_position_drift_max_m'], .08, atol=1e-14)
    reversed_obj = obj.copy(); reversed_obj[:, 0] *= -1
    reverse = describe(time, stage, hand, reversed_obj, target)[2]
    np.testing.assert_allclose(reverse['object_projection_on_goal_displacement_m'], -.08, atol=1e-14)
    rejected = []
    for name, bad_time, bad_stage, bad_obj in (
        ('clock', time+.001, stage, obj),
        ('stage_reversal', time, np.array([3, 3, 4, 3, 5, 5]), obj),
        ('nonfinite', time, stage, obj*np.nan),
        ('shape', time, stage, obj[:-1]),
    ):
        try:
            describe(bad_time, bad_stage, hand, bad_obj, target)
        except (ValueError, AssertionError):
            rejected.append(name)
        else:
            raise AssertionError(name)
    return dict(status='passed', hand_calculated_cases=['co_motion', 'stationary_object', 'reversed_object', 'unreached_stage'],
                malformed_traces_rejected=rejected,
                limitation='Synthetic arithmetic checks only; no physical success certification')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--actual', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    result = check()
    result['source_sha256'] = sha(Path(__file__))
    result['descriptor_sha256'] = sha(Path(__file__).with_name('describe_ball_actual_motion_20261029.py'))
    if args.actual:
        actual = json.loads(args.actual.read_text())
        count = 0
        for row in actual['rows']:
            path = Path(row['folder'])/'legacy.npz'
            assert sha(path) == row['input_sha256']['legacy.npz']
            with np.load(path, allow_pickle=False) as z:
                stages = z['stage'].tolist()
                hand, obj, target = (z[key].tolist() for key in ('position', 'object_position', 'target'))
                for phase in row['phases']:
                    indices = [i for i, s in enumerate(stages) if s == phase['stage']]
                    assert len(indices) == phase['frames']
                    if not indices:
                        continue
                    first, last = indices[0], indices[-1]
                    anchor = max(0, first-1)
                    h = [hand[last][i]-hand[anchor][i] for i in range(3)]
                    o = [obj[last][i]-obj[anchor][i] for i in range(3)]
                    np.testing.assert_allclose(phase['hand_displacement_m'], h, rtol=0, atol=1e-14)
                    np.testing.assert_allclose(phase['object_displacement_m'], o, rtol=0, atol=1e-14)
                    initial_relative = [obj[anchor][i]-hand[anchor][i] for i in range(3)]
                    drift = max(math.dist([obj[j][i]-hand[j][i] for i in range(3)], initial_relative)
                                for j in range(anchor,last+1))
                    assert math.isclose(drift, phase['relative_position_drift_max_m'], rel_tol=1e-12, abs_tol=1e-14)
                    if first:
                        delta = [target[first][i]-target[anchor][i] for i in range(3)]
                        length = math.sqrt(sum(v*v for v in delta))
                        if length > 1e-12:
                            projection = math.fsum(o[i]*delta[i]/length for i in range(3))
                            assert math.isclose(projection, phase['object_projection_on_goal_displacement_m'], rel_tol=1e-12, abs_tol=1e-14)
                    count += 1
        result.update(actual_report_sha256=sha(args.actual), actual_phases_scalar_checked=count)
    if args.output:
        with args.output.open('x') as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write('\n')
    print(json.dumps(result))
