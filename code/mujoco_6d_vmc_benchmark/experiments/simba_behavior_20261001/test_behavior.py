"""Synthetic counterexamples for read-only behavior evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]/"scripts"))
from behavior_evaluate import evaluate, evaluate_file
from behavior_telemetry_20261001 import BehaviorTelemetry

RAW = dict(contact_required=["rod"], physical_valid=True,
           full_task_horizon_completed=True, execution_complete=True,
           abort_reason=None, task_success=False, placement_complete=False)


def trace(mode="slide"):
    rec = BehaviorTelemetry()
    normal = np.array([0., 0., 2.])
    force = np.array([0., 0., 1.])
    for k in range(1, 1501):
        t = k*.004
        u = np.clip((t-.1)/1., 0., 1.)
        p = np.array([.03*u, 0., .5])
        direction = np.array([1., 0., 0.])
        if mode == "stuck":
            p[0] = 0.
        elif mode == "normal":
            p = np.array([0., 0., .5+.03*u])
            direction = np.array([0., 0., 1.])
        elif mode == "roundtrip":
            p[0] = .03*np.sin(np.pi*u)
        contact = .1 <= t <= 1.1
        obs = "rod"
        vel = np.zeros(6)
        reference = p.copy()
        if mode == "impact":
            contact = .1 <= t < .104
            obs = "ball"
            p[0] = .03 if .1 <= t < .3 else 0.
            reference = np.array([0., 0., .5])
        elif mode == "unrecovered":
            contact = .1 <= t < .104
            obs = "ball"
            p[0] = .03 if t >= .1 else 0.
            reference = np.array([0., 0., .5])
        elif mode == "nodeparture":
            contact = .1 <= t < .104
            obs = "ball"
            p[0] = 0.
            reference = np.array([0., 0., .5])
        cs = [dict(obstacle_id=obs, force_world=force, normal_world=normal,
                   obstacle_position=np.zeros(3), robot_position=p,
                   robot_part="hand")] if contact else []
        rec.sample(time=t, dt=.004, hand_position=p, hand_rotation=np.eye(3),
            hand_twist=vel, reference_position=reference, reference_rotation=np.eye(3),
            task_direction=direction, route_progress_m=float(p @ direction),
            contacts=cs, stage=4, object_position=[.5, 0., .425])
    assert np.array_equal(normal, [0., 0., 2.]), "logger changed caller array"
    return rec.arrays()


class BehaviorTests(unittest.TestCase):
    def test_slide_without_placement_passes(self):
        result = evaluate(RAW, trace())
        self.assertTrue(result["compliant_progress_success"])
        self.assertTrue(result["strict_compliant_progress_success"])
        self.assertFalse(result["placement_success"])

    def test_stuck_stage_carry_does_not_pass(self):
        raw = dict(RAW, final_task_stage="carry", max_lift_m=.4)
        self.assertFalse(evaluate(raw, trace("stuck"))["compliant_progress_success"])

    def test_pure_normal_displacement_does_not_pass(self):
        self.assertFalse(evaluate(RAW, trace("normal"))["compliant_progress_success"])

    def test_roundtrip_does_not_pass(self):
        self.assertFalse(evaluate(RAW, trace("roundtrip"))["compliant_progress_success"])

    def test_missing_telemetry_is_unknown(self):
        self.assertIsNone(evaluate(RAW)["compliant_progress_success"])

    def test_missing_progress_is_unknown(self):
        z = trace()
        z["route_progress_m"][:] = np.nan
        self.assertIsNone(evaluate(RAW, z)["compliant_progress_success"])

    def test_cannot_drop_required_cup(self):
        raw = dict(RAW, contact_required=["rod", "cup"])
        with self.assertRaises(ValueError):
            evaluate(raw, trace(), required_contacts=["rod"])
        result = evaluate(raw, trace())
        self.assertFalse(result["compliant_progress_success"])
        self.assertEqual(result["event_results"][1]["status"], "not_exposed")

    def test_impact_recovery(self):
        r = evaluate(dict(RAW, contact_required=["ball"]), trace("impact"))
        self.assertTrue(r["compliant_progress_success"])
        ep = r["event_results"][0]["episodes"][0]
        self.assertGreaterEqual(ep["recovery_start_s"], ep["end_s"])
        self.assertLess(ep["recovery_time_s"], 1.)

    def test_no_departure_is_not_fake_recovery(self):
        r = evaluate(dict(RAW, contact_required=["ball"]), trace("nodeparture"))
        self.assertIsNone(r["compliant_progress_success"])
        self.assertTrue(r["event_results"][0]["episodes"][0]["disturbance_rejected"])

    def test_impact_unrecovered_fails(self):
        r = evaluate(dict(RAW, contact_required=["ball"]), trace("unrecovered"))
        self.assertFalse(r["compliant_progress_success"])

    def test_reference_switch_cannot_fake_recovery(self):
        z = trace("unrecovered")
        use = z["time"] >= .3
        z["reference_position"][use, 0] = .03
        z["position_error_m"][use] = 0.
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        self.assertIsNone(r["compliant_progress_success"])

    def test_rotational_reference_switch_does_not_fake_recovery(self):
        z = trace("nodeparture")
        use = z["time"] >= .1
        rot = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
        z["hand_rotation"][use] = rot
        z["rotation_error_rad"][use] = np.pi/2
        z["reference_rotation"][z["time"] >= .3] = rot
        z["rotation_error_rad"][z["time"] >= .3] = 0.
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        self.assertIsNone(r["compliant_progress_success"])

    def test_second_ball_impact_censors_first(self):
        z = trace("impact")
        i = int(np.searchsorted(z["time"], .204))
        z["contact_duration"][i, 0] = .004
        z["contact_first"][i, 0] = z["time"][i]-.004
        z["contact_last"][i, 0] = z["time"][i]
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        first = r["event_results"][0]["episodes"][0]
        self.assertEqual(first["impact_settled_recovery"]["reason"], "competing_contact")
        self.assertIsNone(first["success"])

    def test_overlap_contact_confounds_impact(self):
        z = trace("impact")
        z["obstacle_ids"] = np.array(["ball", "person_hand"])
        for k in list(z):
            if k.startswith("contact_"):
                z[k] = np.concatenate([z[k], z[k].copy()], axis=1)
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        self.assertIsNone(r["compliant_progress_success"])

    def test_waypoint_onward_motion_passes_progress_branch(self):
        z = trace("impact")
        t = z["time"]
        move = t >= .4
        z["hand_position"][move, 0] = .04*np.clip((t[move]-.4)/.4, 0, 1)
        z["reference_position"][move, 0] = .04
        z["route_progress_m"] = z["hand_position"][:, 0].copy()
        z["position_error_m"] = np.linalg.norm(z["hand_position"]-z["reference_position"], axis=1)
        z["hand_twist"][(t >= .4) & (t < .8), 0] = .1
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        first = r["event_results"][0]["episodes"][0]
        self.assertTrue(first["impact_progress_success"])
        self.assertIsNone(first["impact_settled_recovery_success"])
        self.assertTrue(r["compliant_progress_success"])

    def test_reference_or_precontact_attainment_without_motion_not_progress(self):
        z = trace("nodeparture")
        z["reference_position"][z["time"] >= .3, 0] = .04
        r = evaluate(dict(RAW, contact_required=["ball"]), z)
        first = r["event_results"][0]["episodes"][0]
        self.assertFalse(first["impact_progress_success"])
        self.assertIsNone(r["compliant_progress_success"])

    def test_body_switch_is_unknown(self):
        z = trace()
        z["contact_parts"][100:200, 0] = "fr3_link7"
        self.assertIsNone(evaluate(RAW, z)["compliant_progress_success"])

    def test_physics_and_drop_remain_separate(self):
        z = trace()
        r = evaluate(dict(RAW, physical_valid=False), z)
        self.assertTrue(r["compliant_progress_success"])
        self.assertFalse(r["strict_compliant_progress_success"])
        z["object_position"][100:200, 2] = .6
        z["object_position"][200:, 2] = .3
        r = evaluate(RAW, z)
        self.assertTrue(r["object_drop"]["observed_drop"])
        self.assertFalse(r["strict_compliant_progress_success"])

    def test_logger_counts_activity_once_per_substep(self):
        rec = BehaviorTelemetry()
        cs = [dict(obstacle_id="rod", force_world=[0, 0, 1],
                   normal_world=[0, 0, 1], obstacle_position=[0, 0, 0],
                   robot_position=[0, 0, .5], robot_part="hand")]*2
        for i in range(40):
            rec.sample(time=(i+1)*.0001, dt=.0001,
                hand_position=[0, 0, .5], hand_rotation=np.eye(3),
                hand_twist=np.zeros(6), reference_position=[0, 0, .5],
                reference_rotation=np.eye(3), task_direction=[1, 0, 0], contacts=cs)
        z = rec.arrays()
        self.assertEqual(len(z["time"]), 1)
        self.assertAlmostEqual(z["contact_duration"][0, 0], .004)
        self.assertAlmostEqual(z["contact_impulse"][0, 0], .008)
        self.assertAlmostEqual(z["contact_peak"][0, 0], 2.)

    def test_file_wrapper_and_serialization(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/"raw.json").write_text(json.dumps(RAW))
            np.savez_compressed(p/"trace.npz", **trace())
            r = evaluate_file(p/"raw.json", p/"trace.npz")
            json.dumps(r, allow_nan=False)
            self.assertTrue(r["compliant_progress_success"])


if __name__ == "__main__":
    unittest.main()
