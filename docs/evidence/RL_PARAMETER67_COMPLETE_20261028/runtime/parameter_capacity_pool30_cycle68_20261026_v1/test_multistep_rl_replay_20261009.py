import tempfile
from pathlib import Path
import unittest
import numpy as np
from multistep_rl_replay_20261009 import MultiStepReplay
from research72_train_rl_20261003 import Replay


def add(replay,reward,done=False):
    i=replay.count
    replay.add(observation=np.full(48,i),action=np.full(7,i/10),reward=reward,
        terminated=float(done),truncated=0.,next_observation=np.full(48,i+1))


class MultiStepTests(unittest.TestCase):
    def test_one_step_matches_existing_replay_and_rng(self):
        old=Replay(10,7,10);new=MultiStepReplay(10,7,10,n_step=1,gamma=.9)
        for reward in [1.,2.,3.]:add(old,reward);add(new,reward)
        for k,v in old.sample(8).items():
            # Sampling once only: retain matching RNG state for all keys.
            if k=='observation':sample=new.sample(8)
            np.testing.assert_array_equal(v,sample[k])

    def test_terminal_stops_window_and_preserves_last_observation(self):
        replay=MultiStepReplay(10,7,10,n_step=3,gamma=.5)
        add(replay,1);add(replay,2,True);add(replay,100)
        self.assertEqual(replay.valid_count,2)
        batch=replay.at([0,1])
        np.testing.assert_array_equal(batch['reward'],[2,2])
        np.testing.assert_array_equal(batch['terminated'],[1,1])
        np.testing.assert_array_equal(batch['next_observation'],np.full((2,48),2))

    def test_full_window_bootstrap_and_no_unfinished_tail(self):
        replay=MultiStepReplay(10,7,10,n_step=3,gamma=.5)
        add(replay,1);add(replay,2);self.assertEqual(replay.valid_count,0)
        add(replay,4);self.assertEqual(replay.valid_count,1)
        self.assertEqual(replay.at([0])['reward'][0],3)
        self.assertEqual(replay.at([0])['terminated'][0],0)
        with self.assertRaises(AssertionError):replay.at([1])

    def test_checkpoint_reproduces_sampling(self):
        replay=MultiStepReplay(10,7,10,n_step=3,gamma=.9)
        add(replay,1);add(replay,2,True)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'replay.npz';meta=replay.save(path)
            other=MultiStepReplay(10,7,999,n_step=3,gamma=.9);other.restore(path,meta)
            original=replay.sample(20);restored=other.sample(20)
            for k,v in original.items():np.testing.assert_array_equal(v,restored[k])


if __name__=='__main__':unittest.main()
