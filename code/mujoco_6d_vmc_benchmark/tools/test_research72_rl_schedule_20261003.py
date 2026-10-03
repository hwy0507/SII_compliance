"""Scheduling/receipt tests only; no physics, JAX learning or heldout reads."""
from contextlib import nullcontext
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import research72_rl_campaign_20261003 as campaign
from research72_rl_schedule_20261003 import active_campaign, closure, dispatch_plan, LIMITS, AMENDMENT, sha


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class SchedulingTests(unittest.TestCase):
    def test_initial_coverage_precedes_longer_segments(self):
        jobs = [{'name': str(i)} for i in range(5)]
        plan = dispatch_plan(jobs, 'round_robin_cumulative_boundaries')
        self.assertEqual([j['name'] for j, _, _ in plan[:5]], [str(i) for i in range(5)])
        self.assertEqual([limit for _, _, limit in plan[:5]], [5500]*5)
        self.assertEqual(len(plan), 25)
        for job in jobs:
            self.assertEqual([n for j, _, n in plan if j == job], list(LIMITS))

    def test_deadline_closure_requires_every_model(self):
        self.assertEqual(closure([{}, {'latest_manifest': 'a'}], False)['status'], 'deadline_no_new_dispatch')
        result = closure([{'latest_manifest': 'a'}, {'latest_manifest': 'b'}], False)
        self.assertEqual(result['status'], 'complete')
        self.assertFalse(result['all_requested_segments_dispatched'])
        self.assertEqual(result['dispatch_stop_reason'], 'development_deadline')

    def test_amendment_cannot_hide_an_already_dispatched_cohort(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(active_campaign(root), root/'rl_office_adaptation_v1')
            write(root/'PROTOCOL.json', {'budget_caps': {'rl_adaptation_steps_per_family_seed': 80000}})
            old = root/'rl_office_adaptation_v1'
            write(old/'execution.json', {'status': 'waiting_for_predecessor'})
            receipt = root/'change.json'
            write(receipt, dict(status='complete', old_receipts_preserved=True,
                stopped_physics_processes=0, old_rl_physics_episodes=0))
            write(root/AMENDMENT, dict(protocol_sha256=sha(root/'PROTOCOL.json'),
                scope='outcome_independent_round_robin_rl_dispatch', cumulative_step_boundaries=list(LIMITS),
                active_campaign='rl_office_adaptation_v2', superseded_campaign=old.name,
                superseded_execution_sha256=sha(old/'execution.json'),
                supersession_receipt=str(receipt), supersession_receipt_sha256=sha(receipt)))
            self.assertEqual(active_campaign(root), root/'rl_office_adaptation_v2')
            write(old/'queue_0/execution.json', {'status': 'running'})
            with self.assertRaisesRegex(AssertionError, 'already dispatched'):
                active_campaign(root)

    def test_real_queue_joins_every_parent_and_counts_only_new_steps(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); out = root/'rl'; out.mkdir()
            jobs = [dict(name=f'job{i}', family='synthetic', seed=i, reward='metric', controller=None)
                    for i in range(15)]
            write(out/'SPECIFICATION.json', dict(jobs=jobs, development_deadline_utc='2100-01-01T00:00:00+00:00',
                dispatch_schedule='round_robin_cumulative_boundaries', ipc_probe_receipt='synthetic'))
            calls = []
            def train(command, **kwargs):
                output = Path(command[command.index('--output')+1])
                limit = int(command[command.index('--stop-at-step')+1]); steps = limit//1375*1375
                inherited = 0
                if '--resume-checkpoint' in command:
                    parent = Path(command[command.index('--resume-checkpoint')+1])
                    prior = json.loads((parent.parent/'execution.json').read_text())
                    inherited = prior['steps']
                    self.assertEqual(parent.parent.parent, output.parent)
                self.assertEqual(command[command.index('--steps')+1], '80000')
                write(output/'PROTOCOL.json', {'synthetic': True})
                write(output/'execution.json', dict(status='complete', steps=steps, episodes=steps//1375,
                    new_segment_steps=steps-inherited, updates=2*max(0, steps-5000),
                    checkpoint_rows=[dict(path=str(output/'checkpoint'), step=steps, hashes={})]))
                calls.append((output.parent.name, limit))
                return SimpleNamespace(returncode=0)
            with patch.object(campaign, 'simulation_slot', return_value=nullcontext({'synthetic': True})), \
                 patch.object(campaign.subprocess, 'run', side_effect=train), \
                 patch.object(campaign, 'checkpoint_hashes', return_value={}):
                campaign.queue(root, out, 0)
            result = json.loads((out/'queue_0/execution.json').read_text())
            self.assertEqual(result['status'], 'complete')
            self.assertTrue(result['all_requested_segments_dispatched'])
            self.assertEqual([n for _, n in calls[:5]], [5500]*5)
            self.assertEqual(len(calls), 25)
            for row in result['rows']:
                self.assertEqual(len(row['segments']), 5)
                self.assertEqual(sum(s['new_segment_steps'] for s in row['segments']), 79750)
                self.assertEqual(row['segments'][-1]['cumulative_steps'], 79750)


if __name__ == '__main__':
    unittest.main()
