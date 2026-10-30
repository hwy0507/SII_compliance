"""Algebraic controls for teacher-only 3D progress recovery."""
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher
from vertical_stage_progress_teacher_20261030 import VerticalStageProgressTeacher


def run():
    config = json.loads((ROOT / 'outputs/special_scene_vertical_aware_collection_20261030_v2/teacher.json').read_text())
    config['path_progress_recovery'] = dict(version='bounded_vertical_stage_progress_v1', gain=1.0,
        maximum_speed_mps=.02, opposition_threshold_n=.5, deficit_scale_mps=.02)
    obs = np.zeros(48)
    obs[14:17] = [0, 0, .06]
    obs[26:29] = [0, 0, .02]
    obs[45:48] = [0, 0, 1]
    wrench = np.array([0, 0, -2, 0, 0, 0.])
    base = VerticalAwareCrossTrackTeacher(config)
    progress = VerticalStageProgressTeacher(config)
    base.observe(obs); progress.observe(obs)
    reference = base.act(wrench.copy(), .04)
    actual = progress.act(wrench.copy(), .04)
    expected_speed = .02
    np.testing.assert_allclose(actual[1:4] - reference[1:4], [0, 0, expected_speed/.32], atol=1e-12)
    assert progress.last_progress_velocity_mps == expected_speed

    for direction, measured, force, expected in (
        ([0, 0, 1], [0, 0, .06], [0, 0, -2], 0.),
        ([0, 0, 1], [0, 0, .02], [0, 0, 0], 0.),
        ([0, 0, 0], [0, 0, 0], [0, 0, -2], 0.),
        ([1, 0, 0], [0, 0, 0], [-2, 0, 0], .02),
        ([1, 0, 0], [0, 0, 0], [2, 0, 0], 0.),
    ):
        obs[45:48] = direction; obs[26:29] = measured
        obs[14:17] = np.asarray(direction, dtype=float) * .06
        progress.reset(); progress.observe(obs)
        progress.act(np.asarray(force + [0, 0, 0.], dtype=float), .04)
        assert abs(progress.last_progress_velocity_mps - expected) <= 1e-12
    print('vertical, horizontal, no-intent, no-opposition and cap controls passed')


if __name__ == '__main__':
    run()
