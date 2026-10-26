"""Check unclipped training slowdown does not alter bounded deployment/export."""
import tempfile
from pathlib import Path
import unittest

import numpy as np
import torch

from train_office_mlp_rnn_20261002 import Network
from office_mlp_rnn_20261002 import OfficeMLPRNN


class NeuralContract(unittest.TestCase):
    def setUp(self):
        torch.set_default_dtype(torch.float64)
        torch.set_num_threads(1)

    def test_negative_slowdown_retains_training_gradient(self):
        model = Network('mlp',18,123)
        with torch.no_grad():
            model.core.weight.fill_(.1)
            model.head.weight[0].fill_(-.1)
        x=torch.ones(1,3,18)
        model.raw_slowdown_loss=True
        raw=model(x)[0]
        self.assertLess(float(raw[0,0,0].detach()),0)
        (raw[...,0]-.2).square().mean().backward()
        self.assertGreater(float(model.head.weight.grad[0].abs().sum()),0)
        model.eval()
        np.testing.assert_array_equal(model(x)[0][...,0].detach().numpy(),np.zeros((1,3)))

    def test_export_parity_and_state_reset(self):
        fields=np.array([*range(14,17),*range(20,23),*range(26,29),*range(39,48)])
        obs=np.random.default_rng(321).normal(0,.2,(100,48))
        features=np.c_[obs[:,fields],abs(obs[:,fields])]
        for kind in ['mlp','rnn']:
            model=Network(kind,36,123); model.raw_slowdown_loss=True; model.eval()
            expected=model(torch.from_numpy(features)[None])[0][0].detach().numpy()
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'checkpoint.npz'
                np.savez_compressed(path,**model.export(fields,np.ones(18),True))
                actor=OfficeMLPRNN(path)
                result=np.array([actor.act(o) for o in obs])
                np.testing.assert_allclose(result,expected,atol=1e-12,rtol=1e-12)
                actor.reset()
                np.testing.assert_array_equal(np.array([actor.act(o) for o in obs]),result)
            model.raw_slowdown_loss=False
            np.testing.assert_array_equal(model(torch.from_numpy(features)[None])[0][0].detach().numpy(),expected)


if __name__=='__main__':unittest.main()
