import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from goal_rl_credit_adapter_20261016 import check_credit_migration, migrated_replay_metadata
from rl_goal_stage_20261016 import validate_training_job, worker_command


class GoalStageTests(unittest.TestCase):
    def test_migration_only_changes_credit_horizon(self):
        old = dict(n_step=1, gamma=.9995, action_dimension=7, learning_rate_init=1e-4)
        new = dict(old, n_step=25)
        check_credit_migration(old, new)
        for mutation in (dict(new, gamma=.99), dict(new, action_dimension=5),
                         dict(new, n_step=5), dict(new, learning_rate_init=.001)):
            with self.assertRaises(ValueError):
                check_credit_migration(old, mutation)

    def test_raw_replay_metadata_is_not_relabelled_or_mutated(self):
        old = dict(count=30, capacity=100, sha256='raw_hash', rng_state={'state': 7})
        backup = deepcopy(old)
        result = migrated_replay_metadata(old, 30, .9995)
        self.assertEqual(old, backup)
        self.assertEqual(result['sha256'], 'raw_hash')
        self.assertEqual(result['last_terminal'], 29)
        self.assertEqual(result['n_step'], 25)
        with self.assertRaises(ValueError):
            migrated_replay_metadata(old, 31, .9995)
        with self.assertRaises(ValueError):
            migrated_replay_metadata(result, 30, .9995)

    def test_worker_uses_hard_limits_and_explicit_stage_authority(self):
        reg = dict(runtime='/runtime', python='/venv/python', source='/frozen', parent_root='/parent',
                   parameter_source='/parameter', optimizer_schedule_steps=1000000, run_root='/new')
        job = dict(unit='job', output='/new/direct', seed=10, limit=61531, reward='office_task',
                   reward_variant='task_safety', hp='direct_explore', controller=None, checkpoint='/old/cp')
        cmd = worker_command(reg, job)
        for item in ('--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--setenv=SII_RL_UTD=1',
                     '--goal-registration', '/new/REGISTRATION.json', '--stop-at-step', '61531', '/old/cp'):
            self.assertIn(item, cmd)
        self.assertNotIn('--controller', cmd)
        job.update(controller='impedance', checkpoint=None)
        cmd = worker_command(reg, job)
        self.assertIn('--controller', cmd)
        self.assertNotIn('--resume-checkpoint', cmd)

    def test_job_validation_rejects_budget_and_reward_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            args = argparse.Namespace(goal_registration=root/'REGISTRATION.json', root=root/'parent',
                steps=1000000, output=root/'out', parameter_source=root/'parameter', controller=None,
                reward='office_task', reward_variant='task_safety', hyperparameter_id='direct_explore',
                seed=1, stop_at_step=61531, resume_checkpoint=root/'checkpoint')
            import platform
            reg = dict(schema='sii-rl-persistent-goal-stage-v1', compute_host=platform.node(),
                parent_root=str(args.root), parent_protocol_sha256='hash', server_compute=False,
                acceptance_allowed=False, optimizer_schedule_steps=1000000, parameter_source=str(args.parameter_source),
                new_interactions_per_family=11000, jobs=[dict(output=str(args.output), controller=None,
                    reward='office_task', reward_variant='task_safety', hp='direct_explore', seed=1,
                    limit=61531, inherited_steps=50531, checkpoint=str(args.resume_checkpoint))])
            args.goal_registration.write_text(json.dumps(reg))
            proto = {'budgets': {'rl_steps_per_family_seed': 1000000}}
            validate_training_job(args, proto, 'hash')
            args.stop_at_step += 1
            with self.assertRaises(AssertionError):
                validate_training_job(args, proto, 'hash')
            args.stop_at_step -= 1
            args.reward_variant = 'original'
            with self.assertRaises(AssertionError):
                validate_training_job(args, proto, 'hash')


if __name__ == '__main__':
    unittest.main()
