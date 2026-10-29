"""Algebraic controls for contact-before-progress teacher behavior."""
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher
from vertical_stage_scrape_teacher_20261030 import VerticalStageScrapeTeacher


def run():
    config = json.loads((ROOT / 'outputs/special_scene_vertical_aware_collection_20261030_v2/teacher.json').read_text())
    config['contact_yield_progress'] = dict(version='contact_yield_then_bounded_path_progress_v1',
        yield_force_threshold_n=1.0, yield_excursion_m=.004, gain=1.0,
        maximum_speed_mps=.02, deficit_scale_mps=.02, memory_attack_s=.08, memory_release_s=.5)
    obs = np.zeros(48); obs[14:17] = [0, 0, .06]; obs[26:29] = [0, 0, .02]
    obs[45:48] = [0, 0, 1]; obs[20:23] = [0, 0, 0]
    teacher = VerticalStageScrapeTeacher(config)

    def act(wrench, error):
        obs[20:23] = error
        teacher.observe(obs.copy())
        return teacher.act(np.asarray(wrench, dtype=float), .04)

    act([0, 0, 0, 0, 0, 0], [0, 0, 0])
    assert teacher.contact_anchor is None and not teacher.yield_seen and teacher.last_progress_velocity_mps == 0
    act([0, 0, 0, 0, 0, 0], [0, 0, 0])
    assert teacher.last_progress_velocity_mps == 0

    act([2, 0, 0, 0, 0, 0], [0, 0, 0])
    assert teacher.contact_anchor is not None and not teacher.yield_seen
    act([2, 0, 0, 0, 0, 0], [.005, 0, 0])
    assert teacher.yield_seen and teacher.last_progress_velocity_mps > 0
    assert teacher.last_progress_velocity_mps <= .02
    assert teacher.progress_activation > 0

    teacher.reset()
    assert teacher.contact_anchor is None and not teacher.yield_seen and teacher.progress_activation == 0
    act([0, 0, 0, 0, 0, 0], [0, 0, 0])
    assert teacher.last_progress_velocity_mps == 0
    print('no-contact, contact-before-yield, post-yield bounded progress and reset controls passed')


if __name__ == '__main__':
    run()
