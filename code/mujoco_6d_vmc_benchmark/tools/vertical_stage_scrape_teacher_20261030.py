"""Teacher-only contact-yield latch plus bounded 3D path progress."""
import numpy as np

from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher

VERSION = 'contact_yield_then_bounded_path_progress_v1'


class VerticalStageScrapeTeacher(VerticalAwareCrossTrackTeacher):
    """Continue commanded path motion only after sensed contact and yielding.

    The latch uses canonical48 transverse tracking error and estimated wrench.
    It does not read task phase, object geometry, clock, or success state.
    The added action remains teacher-only and passes through the common filter.
    """

    def __init__(self, config):
        super().__init__(config)
        c = config.get('contact_yield_progress')
        required = {'version', 'yield_force_threshold_n', 'yield_excursion_m', 'gain',
                    'maximum_speed_mps', 'deficit_scale_mps', 'memory_attack_s', 'memory_release_s'}
        if not isinstance(c, dict) or set(c) != required or c['version'] != VERSION:
            raise ValueError('Explicit complete contact-yield progress configuration required')
        if not all(np.isfinite(c[k]) and c[k] > 0 for k in required - {'version'}):
            raise ValueError('Finite positive contact-yield recovery constants required')
        if c['gain'] > 2.0 or c['maximum_speed_mps'] > 0.02 or c['yield_excursion_m'] < .004:
            raise ValueError('Prospective bounded teacher envelope exceeded')
        self.contact_yield_progress = dict(c)
        self.contact_anchor = None
        self.yield_seen = False
        self.progress_activation = 0.0
        self.last_progress_velocity_mps = 0.0

    def reset(self):
        super().reset()
        self.contact_anchor = None
        self.yield_seen = False
        self.progress_activation = 0.0
        self.last_progress_velocity_mps = 0.0

    def act(self, wrench_world, dt=.04):
        action = super().act(wrench_world, dt)
        obs = self.observation
        c = self.contact_yield_progress
        direction = np.asarray(obs[45:48], dtype=float)
        direction_norm = float(np.linalg.norm(direction))
        self.last_progress_velocity_mps = 0.0
        if direction_norm <= 1e-12:
            return action
        direction /= direction_norm
        projection = np.eye(3) - np.outer(direction, direction)
        cross_error = projection @ np.asarray(obs[20:23], dtype=float)
        force = np.asarray(wrench_world, dtype=float)[:3]
        cross_force = projection @ force
        load = float(np.linalg.norm(cross_force))

        if self.contact_anchor is None and load >= c['yield_force_threshold_n']:
            self.contact_anchor = cross_error.copy()
        if self.contact_anchor is not None and not self.yield_seen:
            self.yield_seen = float(np.linalg.norm(cross_error - self.contact_anchor)) >= c['yield_excursion_m']

        if self.yield_seen:
            target = float(np.clip((load - c['yield_force_threshold_n']) /
                                   c['yield_force_threshold_n'], 0.0, 1.0))
            tau = c['memory_attack_s'] if target > self.progress_activation else c['memory_release_s']
            self.progress_activation += (1.0 - np.exp(-dt / tau)) * (target - self.progress_activation)

            command = np.asarray(obs[14:17], dtype=float)
            measured = np.asarray(obs[26:29], dtype=float)
            desired_speed = float(command @ direction)
            actual_speed = float(measured @ direction)
            deficit = max(0.0, desired_speed - actual_speed)
            intent = float(np.clip(desired_speed / c['deficit_scale_mps'], 0.0, 1.0))
            velocity = min(c['maximum_speed_mps'], c['gain'] * deficit)
            velocity *= self.progress_activation * intent
            self.last_progress_velocity_mps = float(velocity)
            action[1:4] = np.clip(action[1:4] + velocity * direction / .32, -1.0, 1.0)
        return action
