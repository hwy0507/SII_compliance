import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compare_published_complete_cycles_20261025 import complete_rows, paired_summary


class CompleteCycleComparisonTests(unittest.TestCase):
    def setUp(self):
        self.expected={'a':'passive_corner','b':'active_long'}
        self.rows=[dict(condition=c, category=t, cycle=6, reward=-25.,
            reward_terms={'terminal':-25.}, task_success=False, strict_success=False,
            final_task_stage='carry', abort_reason=None) for c,t in self.expected.items()]
        self.report=dict(cycle=6,optimizer_updates_performed=0,methods={'direct':dict(
            boundary='complete_condition_cycle',network_state_unchanged=True,episodes=self.rows)})

    def test_pairs_by_condition_not_completion_order_and_retains_failures(self):
        before=complete_rows(self.report,'direct',6,self.expected)
        self.rows.reverse()
        self.rows[0].update(reward=25.,reward_terms={'terminal':25.},task_success=True,strict_success=True)
        # Freeze the actual old rows before constructing the changed report.
        before={c:dict(r, reward=-25.,reward_terms={'terminal':-25.},task_success=False,
                        strict_success=False) for c,r in before.items()}
        after=complete_rows(self.report,'direct',6,self.expected)
        result=paired_summary(before,after)
        self.assertEqual(result['count'],2)
        self.assertEqual(result['paired_reward_delta_mean'],25.)
        self.assertEqual(result['gained_strict'],['b'])
        self.assertEqual(result['after_failure_stages'],{'carry':1})

    def test_duplicate_cannot_replace_missing_condition(self):
        self.rows[1]=copy.deepcopy(self.rows[0])
        with self.assertRaisesRegex(ValueError,'condition cohort'):
            complete_rows(self.report,'direct',6,self.expected)

    def test_partial_checkpoint_and_wrong_cycle_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'exact read-only'):
            complete_rows(self.report,'direct',7,self.expected)
        self.report['methods']['direct']['boundary']='partial_episode_valid_replay_reset_environment_on_resume'
        with self.assertRaisesRegex(ValueError,'complete immutable'):
            complete_rows(self.report,'direct',6,self.expected)

    def test_invalid_success_and_unreconstructed_reward_rejected(self):
        self.rows[0]['strict_success']=True
        with self.assertRaisesRegex(ValueError,'Strict success'):
            complete_rows(self.report,'direct',6,self.expected)
        self.rows[0]['strict_success']=False
        self.rows[0]['reward']=0.
        with self.assertRaisesRegex(ValueError,'component reconstruction'):
            complete_rows(self.report,'direct',6,self.expected)


if __name__=='__main__':unittest.main()
