import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_goal_reward_signal_20261016 import decompose


class RewardSignalTests(unittest.TestCase):
    def fixture(self):
        spec = dict(reward=dict(gamma=.9, progress_weight=5., mode='office_task',
            success_reward=20., failure_penalty=20.), agent_config=dict(gamma=.9, n_step=25),
            reward_variant='task_safety')
        row = dict(steps=2, episode=3, condition_id='train', step_before=10, return_value=13.8,
            result=dict(task_success=True, strict_success=False))
        logs = []
        for i, (phi, nxt, progress, task, safety) in enumerate(((.2,.4,.8,0.,0.), (.4,.5,-2.,20.,5.))):
            logs.append(dict(step=11+i, episode=3, terms=dict(current_potential=phi,
                next_potential=nxt, effective_next_potential=0. if i else nxt, progress=progress,
                task=task, safety_peak_cost=safety, final_reward=progress+task-safety,
                bounded_error_cost=.1, terminated=bool(i), success=bool(i), failure=False)))
        return row, logs, spec

    def test_task_success_with_strict_failure_is_not_relabelled(self):
        out = decompose(*self.fixture())
        self.assertAlmostEqual(out['discounted_components']['progress'], -1.)
        self.assertEqual(out['undiscounted_components']['safety_peak_cost'], -5.)
        self.assertFalse(out['result']['strict_success'])

    def test_missing_or_repeated_data_is_not_complete(self):
        row, logs, spec = self.fixture()
        self.assertEqual(decompose(row, logs[:1], spec)['status'], 'pending_log_flush')
        with self.assertRaises(ValueError): decompose(row, logs+logs, spec)
        with self.assertRaises(ValueError): decompose(row, logs[1:], spec)
        logs[1]['step'] = logs[0]['step']
        with self.assertRaises(ValueError): decompose(row, logs, spec)

    def test_incorrect_terminal_or_cost_sign_is_rejected(self):
        for key, value in [('progress', .25), ('final_reward', 23.), ('success', False)]:
            row, logs, spec = self.fixture()
            logs = copy.deepcopy(logs); logs[-1]['terms'][key] = value
            with self.assertRaises(ValueError): decompose(row, logs, spec)


if __name__ == '__main__': unittest.main()
