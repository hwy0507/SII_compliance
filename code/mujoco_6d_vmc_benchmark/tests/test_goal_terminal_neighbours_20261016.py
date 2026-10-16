from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from diagnose_goal_terminal_neighbours_20261016 import terminal_neighbours


class TerminalNeighboursTests(unittest.TestCase):
    def test_identical_inputs_keep_terminal_difference_and_episode_boundaries(self):
        obs=np.zeros((20,48));action=np.zeros((20,5));reward=np.zeros(20);done=np.zeros(20)
        done[[9,19]]=1;reward[[9,19]]=-20
        result=terminal_neighbours(obs,action,reward,done,n_step=3,gamma=.9,dt=.04)
        self.assertEqual(result['pair_count'],6)
        for row in result['pairs']:
            self.assertLessEqual(row['episode_begin'],row['earlier_index'])
            self.assertGreaterEqual(row['earlier_to_end_steps'],6)
            self.assertEqual(row['joint_rms'],0.)
            self.assertAlmostEqual(row['query_reward_n'],-20*.9**row['query_to_end_steps'])
            self.assertEqual(row['earlier_reward_n'],0.)
            self.assertEqual(row['query_bootstrap_mask'],0)
            self.assertEqual(row['earlier_bootstrap_mask'],1)

    def test_neighbours_use_action_as_well_as_observation(self):
        obs=np.zeros((10,48));act=np.zeros((10,1));act[0]=1;act[7:]=1
        done=np.zeros(10);done[-1]=1
        result=terminal_neighbours(obs,act,np.zeros(10),done,n_step=3,gamma=.9,dt=.04)
        self.assertTrue(all(row['earlier_index']==0 for row in result['pairs']))

    def test_short_episode_is_reported_and_incomplete_replay_rejected(self):
        obs=np.zeros((4,48));act=np.zeros((4,1));done=np.zeros(4);done[-1]=1
        result=terminal_neighbours(obs,act,np.zeros(4),done,n_step=3,gamma=.9,dt=.04)
        self.assertEqual(result['pair_count'],0);self.assertEqual(len(result['skipped_episodes']),1)
        done[-1]=0
        with self.assertRaises(ValueError):terminal_neighbours(obs,act,np.zeros(4),done,n_step=3,gamma=.9,dt=.04)


if __name__=='__main__':unittest.main()
