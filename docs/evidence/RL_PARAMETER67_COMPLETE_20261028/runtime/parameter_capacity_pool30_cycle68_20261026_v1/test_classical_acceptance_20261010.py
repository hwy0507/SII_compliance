"""Ensure diagnostic geometry changes cannot silently become benchmark changes."""
import unittest
from pathlib import Path
import mujoco
import numpy as np
from classical_acceptance_20261010 import disable_obstacles, DISABLED_NAMES, rank_candidates, read
from strengthen_classical_local_20261010 import candidates
from finish_evidence_archive_20261010 import transfer_source, source_matches, destination


MODEL = Path(__file__).resolve().parents[1]/'outputs/baseline_local_rl_20261009/runtime/v6/construction/rollout.mjb'


class FixtureTest(unittest.TestCase):
    def test_frozen_and_events_off_have_identical_binary(self):
        for fixture in ('frozen', 'events_off'):
            m = mujoco.MjModel.from_binary_path(str(MODEL))
            before = self.bytes(m)
            self.assertEqual(disable_obstacles(m, fixture), [])
            self.assertEqual(before, self.bytes(m))

    def bytes(self, model):
        data = np.empty(mujoco.mj_sizeModel(model), np.uint8)
        mujoco.mj_saveModel(model, None, data)
        return data.tobytes()

    def test_only_registered_masks_change_and_are_reversible(self):
        for fixture in ('clear', 'edge_only', 'active_only'):
            m = mujoco.MjModel.from_binary_path(str(MODEL))
            before = self.bytes(m)
            changes = disable_obstacles(m, fixture)
            expected = set(DISABLED_NAMES)
            if fixture == 'edge_only':
                expected.remove('office_v5_unexpected_edge')
            if fixture == 'active_only':
                expected -= set(DISABLED_NAMES[9:])
            self.assertEqual({c['name'] for c in changes}, expected)
            for c in changes:
                self.assertEqual(m.geom_contype[c['id']], 0)
                self.assertEqual(m.geom_conaffinity[c['id']], 0)
                m.geom_contype[c['id']] = c['original_contype']
                m.geom_conaffinity[c['id']] = c['original_conaffinity']
            self.assertEqual(before, self.bytes(m), 'Mass, friction, supports, robot and limits must remain byte-identical')

    def test_support_and_payload_remain_collidable(self):
        m = mujoco.MjModel.from_binary_path(str(MODEL))
        protected = ['office_desk_top', 'office_v5_corner_top', 'target_object_geom', 'office_floor']
        before = [(m.geom(name).contype.copy(), m.geom(name).conaffinity.copy()) for name in protected]
        disable_obstacles(m, 'clear')
        for name, (ct, ca) in zip(protected, before):
            np.testing.assert_array_equal(m.geom(name).contype, ct)
            np.testing.assert_array_equal(m.geom(name).conaffinity, ca)
            self.assertTrue(np.any(ct) or np.any(ca))


class SearchTest(unittest.TestCase):
    def test_equal_budget_and_all_original_bounds(self):
        priors=read(MODEL.parents[2]/'history/parameter_v2/PRIORS.json')['methods']
        choices=candidates(priors)
        self.assertEqual(len(choices),27)
        self.assertEqual(len({c['name'] for c in choices}),27)
        for method, prior in priors.items():
            rows=[c for c in choices if c['controller']==method]
            self.assertEqual(len(rows),9)
            self.assertEqual(rows[0]['parameters'],prior['center'])
            for c in rows:
                self.assertTrue(all(lo<=x<=hi for x,(lo,hi) in zip(c['parameters'],prior['bounds'])))

    def test_actual_task_beats_stage_or_smaller_distance_failure(self):
        choices=[dict(name=m+str(i),controller=m,parameters=[]) for m in ('vmc','admittance','impedance') for i in (0,1)]
        reg=dict(candidates=choices,screen_conditions=['a','b'])
        rows=[]
        for c in choices:
            success=c['name'].endswith('1')
            for condition in ('a','b'):
                rows.append(dict(status='complete',job=dict(candidate=c['name'],condition_id=condition),audit=dict(
                    strict_success=False,task_success=success,full_horizon=True,
                    placement_error_xy_m=.02 if success else .001,penetration_mm=.3,rmse_mm=30.,peak_torque_nm=40.)))
        ranks=rank_candidates(reg,rows)
        self.assertTrue(all(v[0]['candidate']['name'].endswith('1') for v in ranks.values()))
        with self.assertRaises(AssertionError):rank_candidates(reg,rows[:-1])
        rows[0]['status']='failed_preserved'
        with self.assertRaises(AssertionError):rank_candidates(reg,rows)


class ArchiveTest(unittest.TestCase):
    def test_sender_cwd_is_used(self):
        self.assertEqual(transfer_source('outputs/run/', '/tmp/producer'), Path('/tmp/producer/outputs/run'))
        self.assertEqual(transfer_source('/tmp/actual/run', '/tmp/other'), Path('/tmp/actual/run'))
        self.assertTrue(source_matches('outputs/run/', '/tmp/producer', '/tmp/producer/outputs/run'))
        self.assertTrue(source_matches('outputs/run/', '/tmp/producer/outputs/run', '/tmp/producer/outputs/run'))
        self.assertFalse(source_matches('outputs/other/', '/tmp/producer/outputs/run', '/tmp/producer/outputs/run'))
        self.assertFalse(source_matches('/tmp/wrong/run', '/tmp/producer/outputs/run', '/tmp/producer/outputs/run'))

    def test_archive_names_are_not_paths(self):
        for name in ('rl_evidence_phase1_setup_20261010','classical_readiness_20261010'):
            self.assertTrue(destination(name).endswith('/'+name))
        for name in ('../classical_run','classical_a/../b','classical_a;whoami','/classical_a','classical_a b','classical_'):
            with self.assertRaises(ValueError):destination(name)


if __name__ == '__main__':
    unittest.main()
