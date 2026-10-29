"""Bounded teacher-only progress recovery along the observed 3D path."""
import numpy as np

from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher

VERSION = 'bounded_vertical_stage_progress_v1'


class VerticalStageProgressTeacher(VerticalAwareCrossTrackTeacher):
    """Add path-tangent speed only under measured opposition and lag.

    Inputs are the existing canonical48 command, measured twist, path direction,
    and estimated wrench. No stage, clock, object geometry, or success flag is
    used. The velocity correction is teacher-only and remains action-filtered.
    """

    def __init__(self, config):
        super().__init__(config)
        progress = config.get('path_progress_recovery')
        required = {'version', 'gain', 'maximum_speed_mps', 'opposition_threshold_n', 'deficit_scale_mps'}
        if not isinstance(progress, dict) or set(progress) != required or progress['version'] != VERSION:
            raise ValueError('Explicit complete 3D progress recovery configuration required')
        if not all(np.isfinite(progress[k]) and progress[k] > 0 for k in required - {'version'}):
            raise ValueError('Finite positive progress recovery constants required')
        if progress['gain'] > 2.0 or progress['maximum_speed_mps'] > 0.02:
            raise ValueError('Prospective bounded teacher envelope exceeded')
        self.path_progress = dict(progress)
        self.last_progress_velocity_mps = 0.0

    def reset(self):
        super().reset()
        self.last_progress_velocity_mps = 0.0

    def act(self, wrench_world, dt=.04):
        action = super().act(wrench_world, dt)
        obs = self.observation
        c = self.path_progress
        direction = np.asarray(obs[45:48], dtype=float)
        norm = float(np.linalg.norm(direction))
        self.last_progress_velocity_mps = 0.0
        if norm <= 1e-12:
            return action
        direction /= norm
        command = np.asarray(obs[14:17], dtype=float)
        measured = np.asarray(obs[26:29], dtype=float)
        desired_speed = float(command @ direction)
        actual_speed = float(measured @ direction)
        opposition = max(0.0, -float(np.asarray(wrench_world, dtype=float)[:3] @ direction)
                         - c['opposition_threshold_n'])
        load_gate = float(np.clip(opposition / c['opposition_threshold_n'], 0.0, 1.0))
        intent_gate = float(np.clip(desired_speed / c['deficit_scale_mps'], 0.0, 1.0))
        deficit = max(0.0, desired_speed - actual_speed)
        velocity = min(c['maximum_speed_mps'], c['gain'] * deficit)
        velocity *= load_gate * intent_gate
        self.last_progress_velocity_mps = float(velocity)
        action[1:4] = np.clip(action[1:4] + velocity * direction / .32, -1.0, 1.0)
        return action
