"""Protect replay/RNG semantics when moving sample gathers to a device."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np
import torch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from published_replay_device_cache_20261025 import DeviceReplayCache
from train_published_compliance_20261025 import Replay


class DeviceReplayTests(unittest.TestCase):
    def check_device(self,device):
        for dim,obs in ((5,49),(7,48),(7,49)):
            a=Replay(dim,obs,17,capacity=17)
            b=Replay(dim,obs,17,capacity=17)
            cache=DeviceReplayCache(b,device)
            rng=np.random.default_rng(23)
            def sample(count):
                expected,actual=a.sample(count),cache.sample(count)
                for key,value in expected.items():
                    np.testing.assert_array_equal(value,actual[key].cpu().numpy())
                self.assertEqual(a.rng.bit_generator.state,b.rng.bit_generator.state)
            for i in range(60):
                row={k:rng.normal(size=v.shape[1]).astype(np.float32)
                     for k,v in a.arrays.items() if k!='masks'}
                a.add(**row);cache.add(**row)
                if i>=4:sample(32)
            self.assertEqual((a.cursor,a.size),(b.cursor,b.size))
            for key in a.arrays:
                np.testing.assert_array_equal(a.arrays[key],b.arrays[key])
            state=copy.deepcopy(a.state_dict())
            state['arrays']['masks'][:]=0
            state['arrays']['masks'][-1]=1
            a.load_state_dict(copy.deepcopy(state));cache.load_state_dict(copy.deepcopy(state))
            for _ in range(8):sample(1)

    def test_cpu_wrap_resume_and_rejection_rng(self):
        self.check_device('cpu')

    @unittest.skipUnless(torch.cuda.is_available(),'CUDA unavailable')
    def test_cuda_wrap_resume_and_rejection_rng(self):
        self.check_device('cuda:0')


if __name__=='__main__':
    unittest.main()
