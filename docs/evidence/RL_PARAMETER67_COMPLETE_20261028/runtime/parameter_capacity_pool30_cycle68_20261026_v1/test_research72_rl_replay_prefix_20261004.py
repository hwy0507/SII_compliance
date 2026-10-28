import unittest
import numpy as np
from research72_rl_replay_prefix_20261004 import compare_buffers


class PrefixTests(unittest.TestCase):
    def fixture(self,dimension=7):
        rng=np.random.default_rng(17)
        child={k:rng.normal(size=(9,*shape)).astype(np.float32) for k,shape in
            dict(observation=(48,),next_observation=(48,),action=(dimension,),reward=(),terminated=(),truncated=()).items()}
        child['action']=np.clip(child['action'],-1,1)
        child['terminated'][:]=0;child['terminated'][[2,5,8]]=1;child['truncated'][:]=0
        return {k:v[:3].copy() for k,v in child.items()},child

    def test_real_prefix_shape_for_both_interfaces(self):
        for dimension in (5,7):
            parent,child=self.fixture(dimension)
            self.assertEqual(compare_buffers(parent,child,3,9,dimension)['appended_transitions'],6)

    def test_inherited_action_or_reward_mutation_rejected(self):
        for key in ('action','reward','observation','terminated'):
            parent,child=self.fixture();child[key][0]+=1
            with self.assertRaises(AssertionError):compare_buffers(parent,child,3,9,7)

    def test_incomplete_or_invalid_new_boundary_rejected(self):
        for key,value in (('terminated',0),('action',2),('reward',float('nan'))):
            parent,child=self.fixture();child[key][-1]=value
            with self.assertRaises(AssertionError):compare_buffers(parent,child,3,9,7)


if __name__=='__main__':unittest.main()
