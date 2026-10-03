"""Exercise the full metric extractor on synthetic short/complete histories."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from paper_metrics_20261002 import measure, sha


class CensorTests(unittest.TestCase):
    def make_run(self, end):
        temp = tempfile.TemporaryDirectory(prefix='sii-metric-censor-')
        self.addCleanup(temp.cleanup)
        root = Path(temp.name); (root/'rollout_metrics').mkdir()
        time = np.arange(1, round(end/.01)+1)*.01
        n = len(time); dt = np.full(n,.01)
        np.savez(root/'rollout_metrics/substep_metrics.npz',time=time,dt=dt,
                 error=np.zeros((n,3)),twist=np.zeros((n,6)),
                 qfrc_actuator=np.zeros((n,7)),stage=np.zeros(n))
        force = np.zeros((n,6))
        force[(time>=.25)&(time<=.3),1] = 1
        force[(time>=1.1)&(time<=1.5),2] = 1
        np.savez(root/'research_substeps.npz',contact_force_sum=force,
                 hand_position=np.zeros((n,3)),reference_position=np.zeros((n,3)),
                 route_cursor=np.zeros(n),dq=np.zeros((n,7)))
        (root/'rollout.mjb').write_bytes(b'SYNTHETIC - not a model')
        (root/'rollout.npz').write_bytes(b'SYNTHETIC - not a rollout')
        documents = {
            'research_channels.json':dict(telemetry_sha256=sha(root/'research_substeps.npz'),
                force_columns=['all','ball','human','rod','edge','pillar']),
            'execution.json':dict(runtime_provenance=dict(model_sha256=sha(root/'rollout.mjb'))),
            'rollout.json':dict(arguments=dict(person_start=1.,rod_start=10.,rod_hold=6.),
                ball_launch_time_s=.2,task_success=False,strict_success=False,
                full_task_horizon_completed=end==55.,abort_reason='synthetic_short' if end<55 else None,
                final_task_stage='carry',placement_error_xy_m=.1)}
        for name,d in documents.items():
            (root/name).write_text(json.dumps(d))
        return root

    def test_abort_during_push_has_no_post_unload_observation(self):
        result = measure(self.make_run(2.))
        human = result['recovery']['human']
        self.assertTrue(human['exposed'])
        self.assertTrue(human['right_censored'])
        self.assertIsNone(human['settled_rejoin_time_s'])
        self.assertEqual(human['censor_s'],2.)
        self.assertEqual(human['observation_window_s'],0.)

    def test_ball_followup_truncated_by_actual_end(self):
        ball = measure(self.make_run(.4))['recovery']['ball']
        self.assertAlmostEqual(ball['observation_window_s'],.1)
        self.assertEqual(ball['planned_censor_s'],1.)
        self.assertTrue(ball['right_censored'])

    def test_complete_history_retains_scheduled_window(self):
        result = measure(self.make_run(55.))
        self.assertEqual(result['recovery']['human']['censor_s'],10.)
        self.assertEqual(result['recovery']['human']['observation_window_s'],2.)
        self.assertAlmostEqual(result['recovery']['ball']['observation_window_s'],.7)
        self.assertFalse(result['contact']['pillar']['exposure'])
        self.assertIsNone(result['contact']['pillar']['contact_p95_force_n'])

    def test_late_human_contact_preserved_without_changing_event_metrics(self):
        root = self.make_run(55.)
        before = measure(root)
        with np.load(root/'research_substeps.npz') as data:
            values = {k: data[k].copy() for k in data.files}
        # Ten 10 ms samples well outside the human push window [1,8].
        values['contact_force_sum'][2000:2010, 2] = 4.
        values['contact_force_sum'][:, 0] = values['contact_force_sum'][:, 1:4].sum(axis=1)
        np.savez(root/'research_substeps.npz', **values)
        path = root/'research_channels.json'; channels = json.loads(path.read_text())
        channels['telemetry_sha256'] = sha(root/'research_substeps.npz')
        path.write_text(json.dumps(channels))
        after = measure(root)
        self.assertEqual(before['contact'], after['contact'])
        self.assertEqual(before['recovery'], after['recovery'])
        extra = after['supplemental_contact']
        late = extra['outside_event_window']['human']
        self.assertTrue(late['exposure'])
        self.assertAlmostEqual(late['contact_duration_s'], .1)
        self.assertAlmostEqual(late['impulse_ns'], .4)
        self.assertEqual(late['peak_force_n'], 4.)
        self.assertAlmostEqual(extra['whole_observed_horizon']['human']['impulse_ns'],
                               after['contact']['human']['impulse_ns']+.4)
        self.assertNotIn('external_robot', extra['outside_event_window'])

    def test_short_history_supplement_has_no_invented_future(self):
        extra = measure(self.make_run(2.))['supplemental_contact']
        self.assertAlmostEqual(extra['whole_observed_horizon']['human']['observed_duration_s'],2.)
        self.assertFalse(extra['outside_event_window']['human']['exposure'])
        self.assertIsNone(extra['outside_event_window']['human']['contact_p95_force_n'])


if __name__ == '__main__':
    unittest.main()
