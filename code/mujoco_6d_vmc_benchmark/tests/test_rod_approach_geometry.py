from __future__ import annotations

import numpy as np

from run_rod_perturbation_benchmark import ROD_APPROACH_SIDES, rod_approach_geometry


def test_all_axis_aligned_geometries_have_orthogonal_rod_and_motion_axes() -> None:
    assert set(ROD_APPROACH_SIDES) == {"negative_x", "positive_x", "negative_y", "positive_y", "negative_z", "positive_z"}
    for side in ROD_APPROACH_SIDES:
        geometry = rod_approach_geometry(side, 0.54)
        assert np.isclose(np.linalg.norm(geometry.slide_axis_world), 1.0)
        assert np.isclose(np.linalg.norm(geometry.rod_long_axis_world), 1.0)
        assert np.isclose(np.dot(geometry.slide_axis_world, geometry.rod_long_axis_world), 0.0)


def test_existing_lateral_geometry_is_preserved_exactly() -> None:
    negative = rod_approach_geometry("negative_y", 0.54)
    positive = rod_approach_geometry("positive_y", 0.54)
    assert negative.support_position_m == (0.55, -0.20, 0.54)
    assert positive.support_position_m == (0.55, 0.20, 0.54)
    assert negative.slide_axis_world == (0.0, 1.0, 0.0)
    assert positive.slide_axis_world == (0.0, -1.0, 0.0)


def test_vertical_supports_are_physically_mirrored_about_interaction_plane() -> None:
    negative = rod_approach_geometry("negative_z", 0.54)
    positive = rod_approach_geometry("positive_z", 0.54)
    assert np.isclose(negative.support_position_m[2], 0.40)
    assert np.isclose(positive.support_position_m[2], 0.68)
    assert negative.slide_axis_world == (0.0, 0.0, 1.0)
    assert positive.slide_axis_world == (0.0, 0.0, -1.0)
    assert negative.rod_long_axis_world == (0.0, 1.0, 0.0)
    assert positive.rod_long_axis_world == (0.0, 1.0, 0.0)
