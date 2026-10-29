"""Finite development data-collection operator, never a deployed student policy.

Both controllers observe the same canonical48 history. A registered number of
student actions is followed by executed teacher actions. Pre-handoff teacher
outputs remain counterfactual and must not be called executed demonstrations.
The schedule is collector metadata, not an additional student/teacher input.
"""
import numpy as np
from current_student_policy_20260921 import load_current
from run_video_reference_coverage_20261029 import make_actor as make_base_actor


class DevelopmentTeacherHandoff:
    def __init__(self, config, checkpoint, student_steps):
        if isinstance(student_steps, bool) or not isinstance(student_steps, int) or student_steps < 0:
            raise ValueError('Register a nonnegative integer student-prefix length')
        self.teacher = make_base_actor(config)
        self.student = load_current(checkpoint)
        self.student_steps = student_steps
        self.reset()

    def reset(self):
        self.teacher.reset()
        self.student.reset()
        self.index = 0
        self.pending = None
        self.last_teacher_action = None
        self.last_student_action = None
        self.last_behavior_role = None

    def observe(self, observation):
        if self.pending is not None:
            raise RuntimeError('One observe and one act per physical actor step')
        obs = np.asarray(observation, dtype=float)
        if obs.shape != (48,) or not np.isfinite(obs).all():
            raise ValueError('Expected finite canonical48 only')
        self.pending = obs.copy()
        self.teacher.observe(obs.copy())

    def act(self, wrench, dt=.04):
        if dt != .04:
            raise ValueError('Frozen 25-Hz actor clock required')
        if self.pending is None:
            raise RuntimeError('Observe each actual history once before acting')
        np.testing.assert_array_equal(wrench, self.pending[39:45])
        teacher = np.asarray(self.teacher.act(np.asarray(wrench).copy(), dt), dtype=float)
        student = np.asarray(self.student.act(self.pending.copy()), dtype=float)
        if teacher.shape != (7,) or student.shape != (7,) or not np.isfinite(teacher).all() or not np.isfinite(student).all():
            raise ValueError('Expected finite unfiltered action7')
        self.last_teacher_action = teacher.copy()
        self.last_student_action = student.copy()
        self.last_behavior_role = 'student_prefix' if self.index < self.student_steps else 'executed_teacher_suffix'
        result = student if self.index < self.student_steps else teacher
        self.index += 1
        self.pending = None
        return result.copy()
