import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from flask_joint_planner import FlaskJointPlanner, FlaskPlannerConfig, JointSegment


def config(dof=2, **kwargs):
    base = dict(
        velocity_limits=np.full(dof, 3.0),
        acceleration_limits=np.full(dof, 10.0),
        joint_lower=np.full(dof, -1.0),
        joint_upper=np.full(dof, 1.0),
        steering_time=0.3,
        min_steering_time=0.05,
        max_steering_time=1.0,
        samples_per_segment=21,
        max_iterations=1000,
        goal_bias=0.2,
        seed=4,
    )
    base.update(kwargs)
    return FlaskPlannerConfig(**base)


def test_cubic_hermite_hits_flat_boundary_conditions():
    segment = JointSegment(np.zeros(2), np.array([0.2, -0.1]), np.array([0.8, -0.4]), np.array([-0.3, 0.25]), 0.75)
    q0, v0, _ = segment.sample(0.0)
    q1, v1, _ = segment.sample(segment.duration)
    np.testing.assert_allclose(q0, segment.q0)
    np.testing.assert_allclose(v0, segment.v0)
    np.testing.assert_allclose(q1, segment.q1)
    np.testing.assert_allclose(v1, segment.v1)


def test_direct_plan_is_dynamically_bounded_and_exact():
    planner = FlaskJointPlanner(config())
    trajectory = planner.plan(np.array([-0.7, -0.4]), np.array([0.6, 0.8]))
    assert trajectory is not None
    q, v = trajectory.goal
    np.testing.assert_allclose(q, [0.6, 0.8])
    np.testing.assert_allclose(v, np.zeros(2))
    _, _, velocity, acceleration = trajectory.sample_times(32)
    assert np.max(np.abs(velocity)) <= 3.0 + 1e-8
    assert np.max(np.abs(acceleration)) <= 10.0 + 1e-7


def test_sampling_tree_uses_collision_free_closed_form_edges():
    def collision(q):
        # A joint-space obstacle blocks the direct diagonal; the planner must
        # route around its upper side using multiple cubic edges.
        return abs(float(q[0]) - 0.5) < 0.15 and abs(float(q[1])) < 0.7

    planner = FlaskJointPlanner(config(), collision_fn=collision)
    trajectory = planner.plan(np.array([-0.8, -0.8]), np.array([0.8, 0.8]))
    assert trajectory is not None
    _, q, _, _ = trajectory.sample_times(30)
    assert not any(collision(sample) for sample in q)
    np.testing.assert_allclose(trajectory.goal[0], [0.8, 0.8])
